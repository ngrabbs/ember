#pragma once
#include "boot_demo_link.h"
#include "firmware_info.h"
#include "boot_morse.h"
#include "hardware/sync.h"
#include "hardware/dma.h"

static bd_radio demo_radio;
static bool demo_abort,demo_fire,demo_listen,demo_link,demo_tx_pending;
static uint32_t demo_last_tx,demo_uplink_id;
static uint8_t demo_can_error;
static const char *demo_fault="startup_or_radio";
static cf_reader demo_down;
static ul_packet demo_tx;
static uint32_t demo_keep_ms;
static uint64_t demo_cw_deadline,demo_decode_deadline;

static bool demo_reply(unsigned id) {
    cf_frame f=bd_frame(id,demo_radio.token,responder_boot);
    return can_send_frame(&f,time_us_64()+50000);
}
static void demo_identity(const cf_frame *frame,uint32_t now){
    static cf_reader reader;
    ul_packet request;
    if(!cf_feed(&reader,frame,CF_IHU_ID,now) ||
       !up_envelope(&reader,&request) || request.version!=1 ||
       request.sender!=demo_radio.token || request.origin!=demo_radio.token ||
       request.type!=UL_FIRMWARE_INFO || request.size)return;
    request.type=UL_FIRMWARE_INFO_ACK;
    request.sender=responder_boot;
    request.size=FI_SIZE;
    fi_payload(request.payload,responder_boot,now);
    uint8_t wire[UL_WIRE_MAX];
    size_t size=ul_encode(&request,wire);
    if(size)(void)hello_send(wire,size,request.request,time_us_64()+50000);
}

static bool demo_radio_poll(bool keying) {
    if(demo_link && (uint32_t)((uint32_t)(time_us_64()/1000)-demo_keep_ms)>=BD_KEEP_TIMEOUT_MS){
        demo_fault="keepalive_expired";return false;
    }
    if(can_read(14,0x0e)&0xe0){demo_fault="can_mode";return false;}
    demo_can_error=can_read(14,0x2d);
    if(demo_can_error){demo_fault="can_error";return false;}
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
        if(f.id==BD_STOP && bd_matches(&f,demo_radio.token,responder_boot)){
            gpio_put(10,false);demo_abort=true;demo_fault="ihu_stop";return false;
        }
        if(f.id==BD_KEEP && demo_radio.spent && bd_matches(&f,demo_radio.token,responder_boot))
            demo_keep_ms=(uint32_t)(time_us_64()/1000);
        if(keying)continue;
        if(demo_link && f.id==CF_IHU_ID){
            demo_identity(&f,(uint32_t)(time_us_64()/1000));
            continue;
        }
        if(demo_listen && f.id==BD_LINK && bd_matches(&f,demo_radio.token,responder_boot)){
            if(!demo_link){demo_link=true;demo_keep_ms=(uint32_t)(time_us_64()/1000);}
            if(!demo_reply(BD_LINKED))return false;
        }
        if(demo_link && f.id==BD_DOWN_ID &&
           cf_feed(&demo_down,&f,BD_DOWN_ID,(uint32_t)(time_us_64()/1000))){
            static ul_packet candidate;
            if(!demo_tx_pending && bd_packet(&demo_down,&candidate,demo_radio.token,responder_boot) &&
               candidate.request>demo_last_tx){
                demo_tx=candidate;demo_last_tx=candidate.request;demo_tx_pending=true;
            }
        } /* No blocking reply transmissions during marks. */
        if(dr_respond(&f,DR_COMMS_NODE,responder_boot,&reply)){
            (void)can_send_frame(&reply,time_us_64()+50000);continue;
        }
        if(f.size!=8)continue;
        uint32_t now=(uint32_t)(time_us_64()/1000);
        if(f.id==BD_PROBE && !ul_u32(f.data+4) && !demo_radio.spent &&
           bd_arm(&demo_radio,ul_u32(f.data),now)){
            if(!rx_stop())return false;
            (void)demo_reply(BD_READY);
        }
        if(f.id==BD_FIRE && bd_matches(&f,demo_radio.token,responder_boot) &&
           bd_take(&demo_radio,now)){demo_keep_ms=now;demo_fire=true;}
    }
    return !demo_abort;
}
static bool demo_cw_continue(void) {
    return !clock_deadline_fired && time_us_64()<demo_cw_deadline &&
           getchar_timeout_us(0)<0 &&
           (uint32_t)((uint32_t)(time_us_64()/1000)-demo_keep_ms)<BD_KEEP_TIMEOUT_MS && demo_radio_poll(true);
}
static bool demo_morse_segment(bool mark,unsigned units) {
    if(!demo_cw_continue())return false;
    gpio_put(10,false);
    if(!clock_write(3,mark?0xfe:0xff,true))return false;
    if(mark){
        uint8_t status;
        if(!clock_read(0,&status) || (status&0xa8) || !demo_cw_continue())return false;
        uint32_t irq=save_and_disable_interrupts();
        if(!clock_deadline_fired && time_us_64()<demo_cw_deadline)gpio_put(10,true);
        restore_interrupts(irq);
    }
    uint64_t end=time_us_64()+units*BOOT_CW_UNIT_US;
    while(time_us_64()<end){
        if(!demo_cw_continue()){gpio_put(10,false);return false;}
        sleep_us(500);
    }
    gpio_put(10,false);
    return demo_cw_continue();
}
static bool demo_emit(uint64_t deadline) {
    demo_cw_deadline=deadline;
    return boot_morse(demo_morse_segment);
}
static bool demo_rx_healthy(void){
    uint8_t enabled,status;
    return clock_read(3,&enabled) && enabled==0xfd && clock_read(0,&status) && !(status&0xa8);
}

/* DMA keeps sampling while the decoder reads its independent snapshot.
 * Overlap exceeds the ground gateway's modulated uplink length. */
enum {
    DEMO_DMA_SAMPLES=16384, DEMO_WINDOW_SAMPLES=32768,
    DEMO_OVERLAP_SAMPLES=7680,
    DEMO_WINDOW_STEP=DEMO_WINDOW_SAMPLES-DEMO_OVERLAP_SAMPLES
};
static int demo_dma;
static uint16_t demo_dma_ring[DEMO_DMA_SAMPLES] __attribute__((aligned(32768)));
static uint16_t demo_history_samples[DEMO_WINDOW_SAMPLES];
static bool demo_adc_running;
static uint32_t demo_adc_copied,demo_adc_next;
static uint64_t demo_adc_epoch_us,demo_adc_start_us,demo_adc_end_us;
static unsigned demo_rx_window;
static unsigned demo_adc_samples;
static rd_result demo_last_forwarded;
static unsigned demo_last_forwarded_window;

static void demo_adc_stop(void){
    if(!demo_adc_running)return;
    adc_run(false);
    dma_channel_abort((unsigned)demo_dma);
    adc_fifo_drain();
    demo_adc_running=false;
}

static void demo_adc_start(void){
    adc_fifo_drain();
    adc_hw->fcs |= ADC_FCS_OVER_BITS;
    dma_channel_config c=dma_channel_get_default_config((unsigned)demo_dma);
    channel_config_set_transfer_data_size(&c,DMA_SIZE_16);
    channel_config_set_read_increment(&c,false);
    channel_config_set_write_increment(&c,true);
    channel_config_set_ring(&c,true,15);
    channel_config_set_dreq(&c,DREQ_ADC);
    demo_adc_copied=0;
    demo_adc_next=DEMO_WINDOW_SAMPLES;
    dma_channel_configure((unsigned)demo_dma,&c,demo_dma_ring,&adc_hw->fifo,UINT32_MAX,true);
    demo_adc_epoch_us=time_us_64();
    demo_adc_running=true;
    adc_run(true);
}

static bool demo_adc_collect(void){
    uint32_t produced=UINT32_MAX-dma_hw->ch[demo_dma].transfer_count;
    if(produced-demo_adc_copied>=DEMO_DMA_SAMPLES || (adc_hw->fcs&ADC_FCS_OVER_BITS)){
        demo_fault="adc_overrun";
        demo_abort=true;
        return false;
    }
    /* Stop at the snapshot boundary. Remaining samples stay in the DMA ring. */
    if(produced>demo_adc_next)produced=demo_adc_next;
    __compiler_memory_barrier();
    while(demo_adc_copied<produced){
        uint32_t i=demo_adc_copied++;
        demo_history_samples[i&(DEMO_WINDOW_SAMPLES-1)]=demo_dma_ring[i&(DEMO_DMA_SAMPLES-1)];
    }
    return true;
}

static bool demo_decode_continue(void){
    return !demo_abort && time_us_64()<demo_decode_deadline &&
           getchar_timeout_us(0)<0 && demo_radio_poll(false) &&
           !demo_tx_pending && demo_adc_collect();
}

static bool demo_capture(void){
    demo_adc_samples=0;
    if(!demo_adc_running)demo_adc_start();
    uint64_t deadline=time_us_64()+4300000;
    while(!demo_tx_pending){
        if(time_us_64()>=deadline || getchar_timeout_us(0)>=0 ||
           !demo_radio_poll(false) || !demo_adc_collect())return false;
        if(demo_adc_copied==demo_adc_next)break;
        sleep_us(300);
    }
    if(demo_tx_pending)return true;
    uint32_t first=demo_adc_next-DEMO_WINDOW_SAMPLES;
    unsigned offset=first&(DEMO_WINDOW_SAMPLES-1);
    unsigned tail=DEMO_WINDOW_SAMPLES-offset;
    memcpy(rx_samples,demo_history_samples+offset,tail*sizeof(rx_samples[0]));
    memcpy(rx_samples+tail,demo_history_samples,offset*sizeof(rx_samples[0]));
    demo_adc_start_us=demo_adc_epoch_us+(uint64_t)first*125;
    demo_adc_end_us=demo_adc_epoch_us+(uint64_t)demo_adc_next*125;
    demo_adc_samples=DEMO_WINDOW_SAMPLES;
    demo_adc_next+=DEMO_WINDOW_STEP;
    return true;
}
/* USB diagnostics share this loop with the two hardware CAN RX buffers. */
static bool demo_write_log(const char *line, int length) {
    for(int offset=0;offset<length;offset+=16){
        if(!demo_radio_poll(false))return false;
        int count=length-offset;
        if(count>16)count=16;
        (void)stdio_put_string(line+offset,count,false,true);
    }
    return demo_radio_poll(false);
}

/* Report amplitude in ADC counts, with 16 ms peak-to-peak blocks to expose
 * a short burst inside the longer DMA window. Block statistics include noise. */
static bool demo_log_rx(const rd_result *result,uint64_t decode_end,const char *forward){
    unsigned min=4095,max=0,clipped=0,quiet=4095,peak=0,peak_block=0;
    for(unsigned start=0;start<demo_adc_samples;start+=128){
        if(start%2048==0 && !demo_radio_poll(false))return false;
        unsigned lo=4095,hi=0,end=start+128;
        if(end>demo_adc_samples)end=demo_adc_samples;
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
           ++demo_rx_window,(unsigned long)(demo_adc_start_us/1000),
           (unsigned long)(demo_adc_end_us/1000),demo_adc_samples,min,max,clipped,
           quiet,peak,peak_block*16,(unsigned long)(decode_end/1000),
           result->sync_hits,result->header_rejects,result->crc_failures,result->crc_passes,
           result->frequency,(unsigned long)result->sequence,forward);
    return demo_write_log(line,length>=(int)sizeof(line)?(int)sizeof(line)-1:length);
}
static bool demo_forward(const rd_result *decoded){
    static ul_packet p;
    static uint8_t wire[UL_WIRE_MAX];
    if(decoded->size>BD_PACKET_MAX || demo_uplink_id==UINT32_MAX)return true;
    p=(ul_packet){.version=1,.type=BD_PACKET,.sender=responder_boot,.origin=demo_radio.token,
        .request=++demo_uplink_id,.size=(uint16_t)decoded->size};
    memcpy(p.payload,decoded->packet,p.size);
    size_t n=ul_encode(&p,wire);
    if(!n)return false;
    for(unsigned i=0;i*CF_CHUNK<n;i++){
        cf_frame f;
        if(!cf_fragment(wire,n,BD_UP_ID,(uint16_t)p.request,i,&f) ||
           !can_send_frame(&f,time_us_64()+50000) || !demo_radio_poll(false))return false;
        sleep_ms(2);
    }
    return true;
}
/* Reuse the verified clock preparation/mute path, with CAN kept live for
 * stop and keepalive during each bounded BPSK packet. */
static bool demo_bpsk(uint64_t deadline){
    uint64_t start=time_us_64();
    bool phase=false;
    for(unsigned i=0;i<packet_frame_size*8u;i++){
        uint64_t due=start+(uint64_t)i*1000000/BPSK_BAUD;
        while(time_us_64()<due)if(clock_deadline_fired)return false;
        uint64_t now=time_us_64();
        if(now>due+150 || now>=deadline || clock_deadline_fired || getchar_timeout_us(0)>=0)return false;
        phase^=(packet_frame[i/8]>>(7-i%8))&1;
        gpio_put(16,phase);
        if(!demo_radio_poll(true))return false;
    }
    uint64_t end=start+(uint64_t)packet_frame_size*8u*1000000/BPSK_BAUD;
    while(time_us_64()<end)if(clock_deadline_fired)return false;
    return time_us_64()<deadline && !clock_deadline_fired;
}
static bool demo_tx_permitted(void){return demo_radio_poll(true);}
static bool demo_transmit(void){
    uint32_t request=demo_tx.request;
    demo_tx_pending=false;
    packet_frame_size=bridge_frame(packet_frame,demo_tx.payload,demo_tx.size,request);
    bool sent=packet_frame_size && clock_window_impl(true,false,demo_bpsk,1,0,demo_tx_permitted);
    bool rx=sent && rx_start(true) && demo_rx_healthy();
    cf_frame report=bd_frame(rx?BD_TX_OK:BD_TX_FAILED,request,responder_boot);
    bool reported=can_send_frame(&report,time_us_64()+50000);
    char line[112];
    int length=snprintf(line,sizeof(line),"[boot_demo] TX request=%lu sent=%u RX_READY=%u ground_ack=0\n",
           (unsigned long)request,sent,rx);
    bool logged=demo_write_log(line,length>=(int)sizeof(line)?(int)sizeof(line)-1:length);
    return reported && rx && logged;
}
static void demo_radio_run(bool can_ok) {
    printf("[boot_demo] CONDUCTED ONLY; generic packet link; ordinary console RF paths disabled\n");
    if(!can_ok || !rx_stop())goto failed;
    demo_dma=dma_claim_unused_channel(false);
    if(demo_dma<0)goto failed;
    adc_fifo_setup(true,true,1,true,false);
    adc_set_clkdiv(5999.0f);
    for(;;){
        if(getchar_timeout_us(0)>=0 || !demo_radio_poll(false))goto failed;
        if(demo_fire){
            demo_fire=false;
            printf("[boot_demo] CW begin nominal_hz=437000000 wpm=%u text=%s\n",BOOT_CW_WPM,BOOT_CW_TEXT);
            if(!clock_window_impl(true,false,demo_emit,1,BD_CW_LIMIT_MS,demo_tx_permitted) ||
               !rx_start(true) || !demo_rx_healthy())goto failed;
            demo_listen=true;
            printf("[boot_demo] CW complete; RX_READY TX=0 dispatch=0\n");
            if(!demo_reply(BD_RX))goto failed;
        }
        if(demo_listen){
            if(demo_tx_pending){
                demo_adc_stop();
                if(!demo_transmit())goto failed;
                continue;
            }
            if(!demo_capture() || !demo_rx_healthy())goto failed;
            if(demo_tx_pending)continue;
            rd_result result={0};
            demo_decode_deadline=time_us_64()+3000000;
            const char *forward="not_attempted";
            bool decoded=!demo_tx_pending &&
                rd_decode_impl(rx_samples,32768,&result,demo_decode_continue,false);
            uint64_t decode_end=time_us_64();
            if(decoded){
                printf("[boot_demo] RX sequence=%lu bytes=%u forward=%u\n",
                       (unsigned long)result.sequence,(unsigned)result.size,demo_link);
                if(!demo_link)forward="link_disabled";
                else if(result.size>BD_PACKET_MAX || demo_uplink_id==UINT32_MAX)
                    forward="skipped";
                else if(demo_last_forwarded_window==demo_rx_window &&
                        result.sequence==demo_last_forwarded.sequence &&
                        result.size==demo_last_forwarded.size &&
                        !memcmp(result.packet,demo_last_forwarded.packet,result.size)){
                    forward="overlap_duplicate";
                }else if(!demo_forward(&result)){
                    (void)demo_log_rx(&result,decode_end,"failed");
                    goto failed;
                }else{
                    forward="sent";
                    demo_last_forwarded=result;
                    demo_last_forwarded_window=demo_rx_window+1;
                }
            }
            if(demo_abort || !demo_radio_poll(false) || !demo_rx_healthy() ||
               !demo_reply(demo_link?BD_LINKED:BD_RX))goto failed;
            if(!demo_log_rx(&result,decode_end,forward))goto failed;
        }else sleep_ms(1);
    }
failed:
    demo_adc_stop();
    demo_radio.spent=true;
    bool muted=rx_stop();
    if(can_ok && demo_radio.token)(void)demo_reply(BD_FAILED);
    printf("[boot_demo] SAFE reason=%s can_eflg=%02x clock_shutdown_verified=%u; reset both boards for a new run\n",
           demo_fault,demo_can_error,muted);
    for(;;)sleep_ms(100);
}
