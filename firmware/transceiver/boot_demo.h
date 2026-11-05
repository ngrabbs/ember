#pragma once
#include "boot_demo_link.h"
#include "boot_morse.h"
#include "hardware/sync.h"

static bd_radio demo_radio;
static bool demo_abort,demo_fire,demo_listen;
static uint32_t demo_keep_ms;
static uint64_t demo_cw_deadline,demo_decode_deadline;

static bool demo_reply(unsigned id) {
    cf_frame f=bd_frame(id,demo_radio.token,responder_boot);
    return can_send_frame(&f,time_us_64()+50000);
}
static bool demo_radio_poll(bool keying) {
    if((can_read(14,0x0e)&0xe0) || can_read(14,0x2d))return false;
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
            gpio_put(10,false);demo_abort=true;return false;
        }
        if(f.id==BD_KEEP && demo_radio.spent && bd_matches(&f,demo_radio.token,responder_boot))
            demo_keep_ms=(uint32_t)(time_us_64()/1000);
        if(keying)continue; /* No blocking reply transmissions during marks. */
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
static bool demo_decode_continue(void) {
    return !demo_abort && time_us_64()<demo_decode_deadline &&
           getchar_timeout_us(0)<0 && demo_radio_poll(false);
}
static bool demo_rx_healthy(void){
    uint8_t enabled,status;
    return clock_read(3,&enabled) && enabled==0xfd && clock_read(0,&status) && !(status&0xa8);
}
static void demo_radio_run(bool can_ok) {
    printf("[boot_demo] CONDUCTED ONLY; normal RF TX and RF command dispatch disabled\n");
    if(!can_ok || !rx_stop())goto failed;
    for(;;){
        if(getchar_timeout_us(0)>=0 || !demo_radio_poll(false))goto failed;
        if(demo_fire){
            demo_fire=false;
            printf("[boot_demo] CW begin nominal_hz=437000000 wpm=%u text=%s\n",BOOT_CW_WPM,BOOT_CW_TEXT);
            if(!clock_window_impl(true,false,demo_emit,1,BD_CW_LIMIT_MS) ||
               !rx_start(true) || !demo_rx_healthy())goto failed;
            demo_listen=true;
            printf("[boot_demo] CW complete; RX_READY TX=0 dispatch=0\n");
            if(!demo_reply(BD_RX))goto failed;
        }
        if(demo_listen){
            /* RX stays enabled. Capture/decode are bounded and have acquisition gaps.
             * Do not forward packets into the command engine or send a reply. */
            rx_requested=32768;rx_late=0;
            if(!rx_capture() || !demo_radio_poll(false) || !demo_rx_healthy())goto failed;
            rd_result result={0};
            demo_decode_deadline=time_us_64()+3000000;
            if(!rx_late && rd_decode(rx_samples,rx_count,&result,demo_decode_continue))
                printf("[boot_demo] RX packet sequence=%lu bytes=%u mixer_hz=%u dispatch=0 TX=0\n",
                       (unsigned long)result.sequence,(unsigned)result.size,result.frequency);
            if(demo_abort || !demo_radio_poll(false) || !demo_rx_healthy() || !demo_reply(BD_RX))goto failed;
        }else sleep_ms(1);
    }
failed:
    demo_radio.spent=true;
    bool muted=rx_stop();
    if(can_ok && demo_radio.token)(void)demo_reply(BD_FAILED);
    printf("[boot_demo] SAFE stopped clock_shutdown_verified=%u; reset both boards for a new run\n",muted);
    for(;;)sleep_ms(100);
}
