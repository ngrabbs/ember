#pragma once
#include "rf_queue.h"
static rq_state rf_queue;
static bool rf_bus_open(void) {
    if(!configuration_mode(can_read(14,0x0e),can_read(14,0x0f)))return false;
    if(can_read(14,0x2a)!=0 || can_read(14,0x29)!=0xf0 || can_read(14,0x28)!=0x86)return false;
    can_write(14,0x2c,0);can_write(14,0x2d,0);can_write(14,0x60,0x64);
    can_write(14,0x30,0);can_write(14,0x40,0);can_write(14,0x50,0);
    if(!can_mode(14,0))return false;
    gpio_put(2,false);return true;
}
static bool rf_bus_close(void) {
    gpio_put(2,true);return can_mode(14,0x80);
}
static bool rf_reply_send(const ul_packet *request,uint8_t type,uint8_t status) {
    static ul_packet reply;static uint8_t wire[UL_WIRE_MAX];
    uhf_reply(request,responder_boot,type,status,&reply);
    size_t size=ul_encode(&reply,wire);
    return size && hello_send(wire,size,request->request,time_us_64()+500000);
}
/* g: collect for 10s, then send at most four queued frames, then stop.
 * CAN is quiesced during RF; no reception or automatic retry during draining. */
static bool rf_service(void) {
    static cf_reader f;static ul_reader reader;static ul_packet in;
    static uint8_t native[BPSK_NATIVE_MAX];
    memset(&f,0,sizeof(f));bool abort=false,ok=true;
    if(!rf_bus_open())return false;
    uint64_t end=time_us_64()+10000000;
    printf("[uhf] COLLECT max10s capacity=4; any console byte cancels; then bounded drain\n");
    while(time_us_64()<end) {
        if(getchar_timeout_us(0)>=0){abort=true;break;}
        if((can_read(14,0x0e)&0xe0)!=0 || can_read(14,0x2d)){ok=false;break;}
        uint8_t flags=can_read(14,0x2c);
        for(unsigned buffer=0;buffer<2;buffer++) {
            if(!(flags&(1u<<buffer)))continue;
            uint8_t base=buffer?0x71:0x61,tx[15]={3,base},rx[15];
            gpio_put(14,false);sleep_us(2);spi_write_read_blocking(spi0,tx,rx,15);sleep_us(2);gpio_put(14,true);
            can_modify(0x2c,(uint8_t)(1u<<buffer),0);uint8_t *d=rx+2;
            if((d[1]&0x18) || (d[4]&0x40) || (d[4]&15)>8)continue;
            cf_frame frame={.id=(uint16_t)((d[0]<<3)|(d[1]>>5)),.size=d[4]&15};memcpy(frame.data,d+5,frame.size);
            if(!cf_feed(&f,&frame,CF_IHU_ID,(uint32_t)(time_us_64()/1000)))continue;
            memset(&reader,0,sizeof(reader));unsigned count=0;
            for(size_t i=0;i<f.used;i++)if(ul_feed(&reader,f.wire[i],0,&in))count++;
            if(count!=1 || reader.used || reader.discard || reader.crc_errors || reader.framing_errors ||
               reader.format_errors || reader.overflows || in.version!=1 || !in.sender ||
               in.origin!=in.sender || (uint16_t)in.request!=f.token)continue;
            if(in.type==UL_HELLO && !in.size) {
                static uint8_t wire[UL_WIRE_MAX];uint32_t request;
                size_t size=hello_response(&f,responder_boot,wire,&request);
                if(!size || !hello_send(wire,size,request,time_us_64()+500000)){ok=false;break;}
                continue;
            }
            if(in.type!=CF_UHF_SEND)continue;
            size_t size;uint32_t request;uint8_t status=UHF_INVALID,type=CF_UHF_REJECTED;
            if(bridge_telemetry_type(&f,native,&size,&request,true))type=rq_admit(&rf_queue,&in,&status);
            printf("[uhf] admission request=%lu type=%02X status=%u queued=%u\n",(unsigned long)in.request,type,status,rf_queue.count);
            if(!rf_reply_send(&in,type,status)){ok=false;break;}
        }
        if(!ok)break;
        sleep_ms(1);
    }
    if(can_read(14,0x2d))ok=false;
    if(!rf_bus_close())ok=false;
    printf("[uhf] DRAIN queued=%u abort=%u bus_ok=%u\n",rf_queue.count,abort,ok);
    while(rf_queue.count) {
        rq_item *item=&rf_queue.items[0];uint8_t result=UHF_CANCELLED;
        if(!abort && ok) {
            packet_frame_size=bridge_frame(packet_frame,item->packet.payload,item->packet.size,item->packet.request);
            printf("[uhf] packet request=%lu packet_hex=",(unsigned long)item->packet.request);
            for(unsigned i=0;i<item->packet.size;i++)printf("%02x",item->packet.payload[i]);
            printf("\n");
            bool sent=packet_frame_size && clock_window_drive(true,false,bpsk_emit,1);
            result=sent?UHF_OK:UHF_FAILED;if(!sent)abort=true;
        }
        bool delivered=false;
        if(ok && rf_bus_open()) {
            delivered=rf_reply_send(&item->packet,CF_UHF_RESULT,result);
            if(!rf_bus_close())ok=false;
        } else ok=false;
        printf("[uhf] result request=%lu status=%u reply_sent=%u ground_ack=0\n",(unsigned long)item->packet.request,result,delivered);
        rq_finish(&rf_queue,result);
        if(!delivered)abort=true;
        sleep_ms(20);
    }
    gpio_put(10,false);gpio_put(16,false);gpio_put(2,true);
    printf("[uhf] STOP queued=0 TX=0\n");return rf_bus_close() && ok;
}
