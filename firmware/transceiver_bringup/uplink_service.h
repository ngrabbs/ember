#pragma once
#include "uplink_ping.h"
static uint8_t uplink_response[43];
static bool uplink_response_valid;
static uint64_t uplink_response_time;
static uint32_t uplink_request;
/* Runs only after RX clock shutdown, once per accepted PING. No retries. */
static bool uplink_forward(void){
 if(!uplink_pending)return true;
 uplink_pending=false;uplink_response_valid=false;
 if(!disable_clocks() || !rf_bus_open())return false;
 static ul_packet sent,reply;static cf_reader fragments;static uint8_t wire[UL_WIRE_MAX];
 memset(&sent,0,sizeof(sent));memset(&fragments,0,sizeof(fragments));
 sent.version=1;sent.type=UP_PING;sent.sender=sent.origin=responder_boot;sent.request=++uplink_request;
 sent.size=32;memcpy(sent.payload,uplink_ping,32);
 size_t size=ul_encode(&sent,wire);uint64_t end=time_us_64()+2000000;
 bool sent_ok=size!=0;
 for(unsigned i=0;sent_ok && i*CF_CHUNK<size;i++){
  cf_frame f;sent_ok=cf_fragment(wire,size,UP_REQUEST_ID,(uint16_t)sent.request,i,&f)&&can_send_frame(&f,end);
  sleep_ms(2);
 }
 printf("[uplink] forwarded=%u request=%lu retry=0 RF=0\n",sent_ok,(unsigned long)sent.request);
 while(sent_ok && time_us_64()<end){
  if(getchar_timeout_us(0)>=0)break;
  if(can_read(14,0x2d))break;
  uint8_t flags=can_read(14,0x2c);
  for(unsigned b=0;b<2;b++){
   if(!(flags&(1u<<b)))continue;
   uint8_t tx[15]={3,b?0x71:0x61},rx[15];
   gpio_put(14,false);sleep_us(2);spi_write_read_blocking(spi0,tx,rx,15);sleep_us(2);gpio_put(14,true);
   can_modify(0x2c,(uint8_t)(1u<<b),0);uint8_t *d=rx+2;
   if((d[1]&0x18)||(d[4]&0x40)||(d[4]&15)>8)continue;
   cf_frame f={.id=(uint16_t)((d[0]<<3)|(d[1]>>5)),.size=d[4]&15};memcpy(f.data,d+5,f.size);
   cf_frame discovery;
   if(dr_respond(&f,DR_COMMS_NODE,responder_boot,&discovery)){(void)can_send_frame(&discovery,end);continue;}
   if(cf_feed(&fragments,&f,UP_REPLY_ID,(uint32_t)(time_us_64()/1000)) &&
      up_envelope(&fragments,&reply) && up_completed(&reply,&sent)){
    memcpy(uplink_response,reply.payload,43);uplink_response_valid=true;uplink_response_time=time_us_64();
    printf("[uplink] IHU_COMPLETED boot=%lu response_hex=",(unsigned long)reply.sender);
    for(unsigned i=0;i<43;i++){printf("%02x",uplink_response[i]);}printf(" RF=0\n");
    return true;
   }
  }
  sleep_ms(1);
 }
 printf("[uplink] outcome=UNKNOWN_OR_TIMEOUT response_held=0 retry=0\n");
 return (can_read(14,0x0e)&0xe0)==0 && !can_read(14,0x2d);
}
/* Explicit console V only, one previously validated response, at most once. */
static bool uplink_transmit_response(void){
 if(!uplink_response_valid || time_us_64()-uplink_response_time>600000000){
  uplink_response_valid=false;printf("[uplink] NO_RF no_fresh_response\n");return true;
 }
 uplink_response_valid=false;
 if(!rf_bus_close())return false;
 packet_frame_size=bridge_frame(packet_frame,uplink_response,43,uplink_request);
 bool ok=packet_frame_size && clock_window_drive(true,false,bpsk_emit,1);
 printf("[uplink] response_RF_complete=%u retry=0 ground_ack=0\n",ok);
 return ok;
}

#include "auto_reply.h"
/* A: exactly one RX capture and at most one fresh IHU reply. RF lease is local. */
static bool uplink_auto_window(void){
 ar_lease lease;ar_start(&lease,time_us_64());
 uplink_response_valid=false;uplink_pending=false;
 printf("[auto_reply] BEGIN max20s max_replies=1 boot_resume=0\n");
 rx_test(true,true);
 bool fresh=uplink_pending,healthy=true;
 if(fresh)healthy=uplink_forward();
 bool allowed=ar_take(&lease,time_us_64(),fresh&&uplink_response_valid,healthy,getchar_timeout_us(0)>=0);
 bool ok=healthy;
 if(allowed)ok=uplink_transmit_response();
 else uplink_response_valid=false;
 printf("[auto_reply] END reply_attempted=%u ok=%u armed=0\n",allowed,ok);
 return ok;
}
