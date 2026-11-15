#pragma once
#include "uhf_startup_link.h"
#include "radio_config.h"
#include "firmware_info.h"
#include "boot_morse.h"
#include "hardware/sync.h"
#include "hardware/dma.h"

static bd_radio uhf_startup_radio;
static bool uhf_startup_abort,uhf_startup_fire,uhf_startup_listen,uhf_startup_link,uhf_startup_tx_pending;
static uint32_t uhf_startup_last_tx,uhf_startup_uplink_id;
static uint8_t uhf_startup_can_error;
static const char *uhf_startup_fault="startup_or_radio";
static cf_reader uhf_startup_down;
static ul_packet uhf_startup_tx;
static uint32_t uhf_startup_keep_ms;
static uint64_t uhf_startup_cw_deadline,uhf_startup_decode_deadline;

static bool uhf_startup_reply(unsigned id) {
    cf_frame f=bd_frame(id,uhf_startup_radio.token,responder_boot);
    return can_send_frame(&f,time_us_64()+50000);
}
static void uhf_startup_identity(const cf_frame *frame,uint32_t now){
    static cf_reader reader;
    ul_packet request;
    if(!cf_feed(&reader,frame,CF_IHU_ID,now) ||
       !up_envelope(&reader,&request) || request.version!=1 ||
       request.sender!=uhf_startup_radio.token || request.origin!=uhf_startup_radio.token ||
       request.type!=UL_FIRMWARE_INFO || request.size)return;
    request.type=UL_FIRMWARE_INFO_ACK;
    request.sender=responder_boot;
    request.size=FI_SIZE;
    fi_payload(request.payload,responder_boot,now);
    uint8_t wire[UL_WIRE_MAX];
    size_t size=ul_encode(&request,wire);
    if(size)(void)hello_send(wire,size,request.request,time_us_64()+50000);
}

static void uhf_startup_config_reply(uint32_t request){
    ul_packet report={.version=1,.type=BD_CONFIG,.sender=responder_boot,
        .origin=uhf_startup_radio.token,.request=request,.size=RADIO_CONFIG_SIZE};
    uint8_t *data=report.payload;
    data[0]=RADIO_CONFIG_SCHEMA;
    data[1]=RADIO_PROFILE_DBPSK_1200_V3;
    data[2]=RADIO_PROFILE_DBPSK_1200_V3;
    data[3]=RADIO_PROFILE_DBPSK_1200_V3;
    data[4]=uhf_startup_link?RADIO_BEHAVIOR_LINK_ACTIVE:RADIO_BEHAVIOR_RX_ONLY;
    /* Nominal RF targets of the compiled Si5351 RX and TX clock profiles. */
    radio_config_profile(data+RADIO_CONFIG_DEFAULT,435000000u,437000000u,BPSK_BAUD);
    memcpy(data+RADIO_CONFIG_ACTIVE,data+RADIO_CONFIG_DEFAULT,
           RADIO_CONFIG_ACTIVE-RADIO_CONFIG_DEFAULT);
    ul_p32(data+RADIO_CONFIG_BOOT,responder_boot);
    uint8_t wire[UL_WIRE_MAX];
    size_t size=ul_encode(&report,wire);
    uint64_t deadline=time_us_64()+75000;
    for(unsigned i=0;i*CF_CHUNK<size;i++){
        cf_frame f;
        if(!cf_fragment(wire,size,BD_CONFIG_REPLY,(uint16_t)request,i,&f) ||
           !can_send_frame(&f,deadline))return;
        sleep_ms(2);
    }
}

static bool uhf_startup_radio_poll(bool keying) {
    if(uhf_startup_link && (uint32_t)((uint32_t)(time_us_64()/1000)-uhf_startup_keep_ms)>=BD_KEEP_TIMEOUT_MS){
        uhf_startup_fault="keepalive_expired";return false;
    }
    if(can_read(14,0x0e)&0xe0){uhf_startup_fault="can_mode";return false;}
    uhf_startup_can_error=can_read(14,0x2d);
    if(uhf_startup_can_error){uhf_startup_fault="can_error";return false;}
    uint8_t flags=can_read(14,0x2c);
    for(unsigned b=0;b<2;b++){
        if(!(flags&(1u<<b)))continue;
        uint8_t tx[15]={3,b?0x71:0x61},rx[15];
        gpio_put(14,false);sleep_us(2);spi_write_read_blocking(spi0,tx,rx,15);sleep_us(2);gpio_put(14,true);
        can_modify(0x2c,(uint8_t)(1u<<b),0);
        uint8_t *d=rx+2;
        if((d[1]&0x18) || (d[4]&0x40) || (d[4]&15)>8)continue;
        cf_frame f={.id=(uint16_t)((d[0]<<3)|(d[1]>>5)),.size=d[4]&15},reply;
        memcpy(f.data,d+5,f.size);
        if(f.id==BD_STOP && bd_matches(&f,uhf_startup_radio.token,responder_boot)){
            gpio_put(10,false);uhf_startup_abort=true;uhf_startup_fault="ihu_stop";return false;
        }
        if(f.id==BD_KEEP && uhf_startup_radio.spent && bd_matches(&f,uhf_startup_radio.token,responder_boot))
            uhf_startup_keep_ms=(uint32_t)(time_us_64()/1000);
        if(keying)continue;
        if(uhf_startup_listen && f.id==BD_CONFIG_QUERY && f.size==8 &&
           ul_u32(f.data)==uhf_startup_radio.token && ul_u32(f.data+4)){
            uhf_startup_config_reply(ul_u32(f.data+4));
            continue;
        }
        if(uhf_startup_link && f.id==CF_IHU_ID){
            uhf_startup_identity(&f,(uint32_t)(time_us_64()/1000));
            continue;
        }
        if(uhf_startup_listen && f.id==BD_LINK && bd_matches(&f,uhf_startup_radio.token,responder_boot)){
            if(!uhf_startup_link){uhf_startup_link=true;uhf_startup_keep_ms=(uint32_t)(time_us_64()/1000);}
            if(!uhf_startup_reply(BD_LINKED))return false;
        }
        if(uhf_startup_link && f.id==BD_DOWN_ID &&
           cf_feed(&uhf_startup_down,&f,BD_DOWN_ID,(uint32_t)(time_us_64()/1000))){
            static ul_packet candidate;
            if(!uhf_startup_tx_pending && bd_packet(&uhf_startup_down,&candidate,uhf_startup_radio.token,responder_boot) &&
               candidate.request>uhf_startup_last_tx){
                uhf_startup_tx=candidate;uhf_startup_last_tx=candidate.request;uhf_startup_tx_pending=true;
            }
        } /* No blocking reply transmissions during marks. */
        if(dr_respond(&f,DR_COMMS_NODE,responder_boot,&reply)){
            (void)can_send_frame(&reply,time_us_64()+50000);continue;
        }
        if(f.size!=8)continue;
        uint32_t now=(uint32_t)(time_us_64()/1000);
        if(f.id==BD_PROBE && !ul_u32(f.data+4) && !uhf_startup_radio.spent &&
           bd_arm(&uhf_startup_radio,ul_u32(f.data),now)){
            if(!rx_stop())return false;
            (void)uhf_startup_reply(BD_READY);
        }
        if(f.id==BD_FIRE && bd_matches(&f,uhf_startup_radio.token,responder_boot) &&
           bd_take(&uhf_startup_radio,now)){uhf_startup_keep_ms=now;uhf_startup_fire=true;}
    }
    return !uhf_startup_abort;
}
static bool uhf_startup_cw_continue(void) {
    return !clock_deadline_fired && time_us_64()<uhf_startup_cw_deadline &&
           getchar_timeout_us(0)<0 &&
           (uint32_t)((uint32_t)(time_us_64()/1000)-uhf_startup_keep_ms)<BD_KEEP_TIMEOUT_MS && uhf_startup_radio_poll(true);
}
static bool uhf_startup_morse_segment(bool mark,unsigned units) {
    if(!uhf_startup_cw_continue())return false;
    gpio_put(10,false);
    if(!clock_write(3,mark?0xfe:0xff,true))return false;
    if(mark){
        uint8_t status;
        if(!clock_read(0,&status) || (status&0xa8) || !uhf_startup_cw_continue())return false;
        uint32_t irq=save_and_disable_interrupts();
        if(!clock_deadline_fired && time_us_64()<uhf_startup_cw_deadline)gpio_put(10,true);
        restore_interrupts(irq);
    }
    uint64_t end=time_us_64()+units*BOOT_CW_UNIT_US;
    while(time_us_64()<end){
        if(!uhf_startup_cw_continue()){gpio_put(10,false);return false;}
        sleep_us(500);
    }
    gpio_put(10,false);
    return uhf_startup_cw_continue();
}
static bool uhf_startup_emit(uint64_t deadline) {
    uhf_startup_cw_deadline=deadline;
    return boot_morse(uhf_startup_morse_segment);
}
static bool uhf_startup_rx_healthy(void){
    uint8_t enabled,status;
    return clock_read(3,&enabled) && enabled==0xfd && clock_read(0,&status) && !(status&0xa8);
}

/* DMA keeps sampling while the decoder reads its independent snapshot.
 * Overlap exceeds the ground gateway's modulated uplink length. */
enum {
    UHF_STARTUP_DMA_SAMPLES=16384, UHF_STARTUP_WINDOW_SAMPLES=32768,
    UHF_STARTUP_OVERLAP_SAMPLES=7680,
    UHF_STARTUP_WINDOW_STEP=UHF_STARTUP_WINDOW_SAMPLES-UHF_STARTUP_OVERLAP_SAMPLES
};
static int uhf_startup_dma;
static uint16_t uhf_startup_dma_ring[UHF_STARTUP_DMA_SAMPLES] __attribute__((aligned(32768)));
static uint16_t uhf_startup_history_samples[UHF_STARTUP_WINDOW_SAMPLES];
static bool uhf_startup_adc_running;
static uint32_t uhf_startup_adc_copied,uhf_startup_adc_next;
static uint64_t uhf_startup_adc_epoch_us,uhf_startup_adc_start_us,uhf_startup_adc_end_us;
static unsigned uhf_startup_rx_window;
static unsigned uhf_startup_adc_samples;
static rd_result uhf_startup_last_forwarded;
static unsigned uhf_startup_last_forwarded_window;

static void uhf_startup_adc_stop(void){
    if(!uhf_startup_adc_running)return;
    adc_run(false);
    dma_channel_abort((unsigned)uhf_startup_dma);
    adc_fifo_drain();
    uhf_startup_adc_running=false;
}

static void uhf_startup_adc_start(void){
    adc_fifo_drain();
    adc_hw->fcs |= ADC_FCS_OVER_BITS;
    dma_channel_config c=dma_channel_get_default_config((unsigned)uhf_startup_dma);
    channel_config_set_transfer_data_size(&c,DMA_SIZE_16);
    channel_config_set_read_increment(&c,false);
    channel_config_set_write_increment(&c,true);
    channel_config_set_ring(&c,true,15);
    channel_config_set_dreq(&c,DREQ_ADC);
    uhf_startup_adc_copied=0;
    uhf_startup_adc_next=UHF_STARTUP_WINDOW_SAMPLES;
    dma_channel_configure((unsigned)uhf_startup_dma,&c,uhf_startup_dma_ring,&adc_hw->fifo,UINT32_MAX,true);
    uhf_startup_adc_epoch_us=time_us_64();
    uhf_startup_adc_running=true;
    adc_run(true);
}

static bool uhf_startup_adc_collect(void){
    uint32_t produced=UINT32_MAX-dma_hw->ch[uhf_startup_dma].transfer_count;
    if(produced-uhf_startup_adc_copied>=UHF_STARTUP_DMA_SAMPLES || (adc_hw->fcs&ADC_FCS_OVER_BITS)){
        uhf_startup_fault="adc_overrun";
        uhf_startup_abort=true;
        return false;
    }
    /* Stop at the snapshot boundary. Remaining samples stay in the DMA ring. */
    if(produced>uhf_startup_adc_next)produced=uhf_startup_adc_next;
    __compiler_memory_barrier();
    while(uhf_startup_adc_copied<produced){
        uint32_t i=uhf_startup_adc_copied++;
        uhf_startup_history_samples[i&(UHF_STARTUP_WINDOW_SAMPLES-1)]=uhf_startup_dma_ring[i&(UHF_STARTUP_DMA_SAMPLES-1)];
    }
    return true;
}

static bool uhf_startup_decode_continue(void){
    return !uhf_startup_abort && time_us_64()<uhf_startup_decode_deadline &&
           getchar_timeout_us(0)<0 && uhf_startup_radio_poll(false) &&
           !uhf_startup_tx_pending && uhf_startup_adc_collect();
}

static bool uhf_startup_capture(void){
    uhf_startup_adc_samples=0;
    if(!uhf_startup_adc_running)uhf_startup_adc_start();
    uint64_t deadline=time_us_64()+4300000;
    while(!uhf_startup_tx_pending){
        if(time_us_64()>=deadline || getchar_timeout_us(0)>=0 ||
           !uhf_startup_radio_poll(false) || !uhf_startup_adc_collect())return false;
        if(uhf_startup_adc_copied==uhf_startup_adc_next)break;
        sleep_us(300);
    }
    if(uhf_startup_tx_pending)return true;
    uint32_t first=uhf_startup_adc_next-UHF_STARTUP_WINDOW_SAMPLES;
    unsigned offset=first&(UHF_STARTUP_WINDOW_SAMPLES-1);
    unsigned tail=UHF_STARTUP_WINDOW_SAMPLES-offset;
    memcpy(rx_samples,uhf_startup_history_samples+offset,tail*sizeof(rx_samples[0]));
    memcpy(rx_samples+tail,uhf_startup_history_samples,offset*sizeof(rx_samples[0]));
    uhf_startup_adc_start_us=uhf_startup_adc_epoch_us+(uint64_t)first*125;
    uhf_startup_adc_end_us=uhf_startup_adc_epoch_us+(uint64_t)uhf_startup_adc_next*125;
    uhf_startup_adc_samples=UHF_STARTUP_WINDOW_SAMPLES;
    uhf_startup_adc_next+=UHF_STARTUP_WINDOW_STEP;
    return true;
}
/* USB diagnostics share this loop with the two hardware CAN RX buffers. */
static bool uhf_startup_write_log(const char *line, int length) {
    for(int offset=0;offset<length;offset+=16){
        if(!uhf_startup_radio_poll(false))return false;
        int count=length-offset;
        if(count>16)count=16;
        (void)stdio_put_string(line+offset,count,false,true);
    }
    return uhf_startup_radio_poll(false);
}

/* Report amplitude in ADC counts, with 16 ms peak-to-peak blocks to expose
 * a short burst inside the longer DMA window. Block statistics include noise. */
static bool uhf_startup_log_rx(const rd_result *result,uint64_t decode_end,const char *forward){
    unsigned min=4095,max=0,clipped=0,quiet=4095,peak=0,peak_block=0;
    for(unsigned start=0;start<uhf_startup_adc_samples;start+=128){
        if(start%2048==0 && !uhf_startup_radio_poll(false))return false;
        unsigned lo=4095,hi=0,end=start+128;
        if(end>uhf_startup_adc_samples)end=uhf_startup_adc_samples;
        for(unsigned i=start;i<end;++i){
            unsigned sample=rx_samples[i];
            if(sample<lo)lo=sample;
            if(sample>hi)hi=sample;
            if(sample==0 || sample>=4095)++clipped;
        }
        if(lo<min)min=lo;
        if(hi>max)max=hi;
        unsigned span=hi-lo;
        if(span<quiet)quiet=span;
        if(span>peak){peak=span;peak_block=start/128;}
    }
    char line[352];
    int length=snprintf(line,sizeof(line),"[rx_diag] window=%u adc_start_ms=%lu adc_end_ms=%lu samples=%u min=%u max=%u "
           "clip=%u block_pp_min=%u block_pp_max=%u peak_offset_ms=%u "
           "decode_end_ms=%lu sync=%u bad_header=%u crc_bad=%u crc_ok=%u "
           "if_hz=%u seq=%lu can=%s\n",
           ++uhf_startup_rx_window,(unsigned long)(uhf_startup_adc_start_us/1000),
           (unsigned long)(uhf_startup_adc_end_us/1000),uhf_startup_adc_samples,min,max,clipped,
           quiet,peak,peak_block*16,(unsigned long)(decode_end/1000),
           result->sync_hits,result->header_rejects,result->crc_failures,result->crc_passes,
           result->frequency,(unsigned long)result->sequence,forward);
    return uhf_startup_write_log(line,length>=(int)sizeof(line)?(int)sizeof(line)-1:length);
}
static bool uhf_startup_forward(const rd_result *decoded){
    static ul_packet p;
    static uint8_t wire[UL_WIRE_MAX];
    if(decoded->size>BD_PACKET_MAX || uhf_startup_uplink_id==UINT32_MAX)return true;
    p=(ul_packet){.version=1,.type=BD_PACKET,.sender=responder_boot,.origin=uhf_startup_radio.token,
        .request=++uhf_startup_uplink_id,.size=(uint16_t)decoded->size};
    memcpy(p.payload,decoded->packet,p.size);
    size_t n=ul_encode(&p,wire);
    if(!n)return false;
    for(unsigned i=0;i*CF_CHUNK<n;i++){
        cf_frame f;
        if(!cf_fragment(wire,n,BD_UP_ID,(uint16_t)p.request,i,&f) ||
           !can_send_frame(&f,time_us_64()+50000) || !uhf_startup_radio_poll(false))return false;
        sleep_ms(2);
    }
    return true;
}
/* Reuse the verified clock preparation/mute path, with CAN kept live for
 * stop and keepalive during each bounded BPSK packet. */
static bool uhf_startup_bpsk(uint64_t deadline){
    uint64_t start=time_us_64();
    bool phase=false;
    for(unsigned i=0;i<packet_frame_size*8u;i++){
        uint64_t due=start+(uint64_t)i*1000000/BPSK_BAUD;
        while(time_us_64()<due)if(clock_deadline_fired)return false;
        uint64_t now=time_us_64();
        if(now>due+150 || now>=deadline || clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
        phase^=(packet_frame[i/8]>>(7-i%8))&1;
        gpio_put(16,phase);
        if(!uhf_startup_radio_poll(true))return false;
    }
    uint64_t end=start+(uint64_t)packet_frame_size*8u*1000000/BPSK_BAUD;
    while(time_us_64()<end)if(clock_deadline_fired)return false;
    return time_us_64()<deadline && !clock_deadline_fired;
}
static bool uhf_startup_tx_permitted(void){return uhf_startup_radio_poll(true);}
static bool uhf_startup_transmit(void){
    uint32_t request=uhf_startup_tx.request;
    uhf_startup_tx_pending=false;
    packet_frame_size=bridge_frame(packet_frame,uhf_startup_tx.payload,uhf_startup_tx.size,request);
    bool sent=packet_frame_size && clock_window_impl(true,false,uhf_startup_bpsk,1,0,uhf_startup_tx_permitted);
    bool rx=sent && rx_start(true) && uhf_startup_rx_healthy();
    cf_frame report=bd_frame(rx?BD_TX_OK:BD_TX_FAILED,request,responder_boot);
    bool reported=can_send_frame(&report,time_us_64()+50000);
    char line[112];
    int length=snprintf(line,sizeof(line),"[uhf_startup] TX request=%lu sent=%u RX_READY=%u ground_ack=0\n",
           (unsigned long)request,sent,rx);
    bool logged=uhf_startup_write_log(line,length>=(int)sizeof(line)?(int)sizeof(line)-1:length);
    return reported && rx && logged;
}
static void uhf_startup_radio_run(bool can_ok) {
    printf("[uhf_startup] CONDUCTED ONLY; generic packet link; ordinary console RF paths disabled\n");
    if(!can_ok || !rx_stop())goto failed;
    uhf_startup_dma=dma_claim_unused_channel(false);
    if(uhf_startup_dma<0)goto failed;
    adc_fifo_setup(true,true,1,true,false);
    adc_set_clkdiv(5999.0f);
    for(;;){
        if(getchar_timeout_us(0)>=0 || !uhf_startup_radio_poll(false))goto failed;
        if(uhf_startup_fire){
            uhf_startup_fire=false;
            printf("[uhf_startup] CW begin nominal_hz=437000000 wpm=%u text=%s\n",BOOT_CW_WPM,BOOT_CW_TEXT);
            if(!clock_window_impl(true,false,uhf_startup_emit,1,BD_CW_LIMIT_MS,uhf_startup_tx_permitted) ||
               !rx_start(true) || !uhf_startup_rx_healthy())goto failed;
            uhf_startup_listen=true;
            printf("[uhf_startup] CW complete; RX_READY TX=0 dispatch=0\n");
            if(!uhf_startup_reply(BD_RX))goto failed;
        }
        if(uhf_startup_listen){
            if(uhf_startup_tx_pending){
                uhf_startup_adc_stop();
                if(!uhf_startup_transmit())goto failed;
                continue;
            }
            if(!uhf_startup_capture() || !uhf_startup_rx_healthy())goto failed;
            if(uhf_startup_tx_pending)continue;
            rd_result result={0};
            uhf_startup_decode_deadline=time_us_64()+3000000;
            const char *forward="not_attempted";
            bool decoded=!uhf_startup_tx_pending &&
                rd_decode_impl(rx_samples,32768,&result,uhf_startup_decode_continue,false);
            uint64_t decode_end=time_us_64();
            if(decoded){
                printf("[uhf_startup] RX sequence=%lu bytes=%u forward=%u\n",
                       (unsigned long)result.sequence,(unsigned)result.size,uhf_startup_link);
                if(!uhf_startup_link)forward="link_disabled";
                else if(result.size>BD_PACKET_MAX || uhf_startup_uplink_id==UINT32_MAX)
                    forward="skipped";
                else if(uhf_startup_last_forwarded_window==uhf_startup_rx_window &&
                        result.sequence==uhf_startup_last_forwarded.sequence &&
                        result.size==uhf_startup_last_forwarded.size &&
                        !memcmp(result.packet,uhf_startup_last_forwarded.packet,result.size)){
                    forward="overlap_duplicate";
                }else if(!uhf_startup_forward(&result)){
                    (void)uhf_startup_log_rx(&result,decode_end,"failed");
                    goto failed;
                }else{
                    forward="sent";
                    uhf_startup_last_forwarded=result;
                    uhf_startup_last_forwarded_window=uhf_startup_rx_window+1;
                }
            }
            if(uhf_startup_abort || !uhf_startup_radio_poll(false) || !uhf_startup_rx_healthy() ||
               !uhf_startup_reply(uhf_startup_link?BD_LINKED:BD_RX))goto failed;
            if(!uhf_startup_log_rx(&result,decode_end,forward))goto failed;
        }else sleep_ms(1);
    }
failed:
    uhf_startup_adc_stop();
    uhf_startup_radio.spent=true;
    bool muted=rx_stop();
    if(can_ok && uhf_startup_radio.token)(void)uhf_startup_reply(BD_FAILED);
    printf("[uhf_startup] SAFE reason=%s can_eflg=%02x clock_shutdown_verified=%u; reset both boards for a new run\n",
           uhf_startup_fault,uhf_startup_can_error,muted);
    for(;;)sleep_ms(100);
}
