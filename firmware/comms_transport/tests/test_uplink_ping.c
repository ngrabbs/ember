#include <assert.h>
#include <stdio.h>
#include "uplink_ping.h"
#include "protocol.h"
static ul_packet sent,reply;
static unsigned completed;
static bool emit(const uint8_t *p,size_t n,void *unused){
 (void)unused;
 if(p[32]!=2)return true;
 reply=(ul_packet){.version=1,.type=UP_RESULT,.sender=456,.origin=sent.sender,.request=sent.request,.size=(uint16_t)n};
 memcpy(reply.payload,p,n);completed++;return true;
}
int main(void){
 sent=(ul_packet){.version=1,.type=UP_PING,.sender=123,.origin=123,.request=1,.size=32};
 uint8_t *p=sent.payload;ul_p16(p,0x1900);ul_p16(p+2,0xc001);ul_p16(p+4,25);p[6]=1;ul_p16(p+8,1);p[10]=1;p[11]=2;
 ul_p32(p+12,7);ul_p32(p+16,9);ul_p32(p+20,111);ul_p16(p+30,ul_crc(p,30));assert(up_native_ping(p,32));
 uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&sent,wire);cf_reader f={0};bool done=false;
 for(unsigned i=0;i*CF_CHUNK<n;i++){cf_frame frame;assert(cf_fragment(wire,n,UP_REQUEST_ID,1,i,&frame));done=cf_feed(&f,&frame,UP_REQUEST_ID,i);}
 ul_packet decoded;assert(done&&up_envelope(&f,&decoded)&&!memcmp(decoded.payload,p,32));
 static ember_state engine;ember_init(&engine,456);ember_command(&engine,decoded.payload,decoded.size,100,emit,NULL);
 assert(completed==1&&engine.accepted==1&&up_completed(&reply,&sent));
 ember_command(&engine,decoded.payload,decoded.size,101,emit,NULL);assert(completed==2&&engine.accepted==1);
 reply.origin++;assert(!up_completed(&reply,&sent));reply.origin--;
 reply.request++;assert(!up_completed(&reply,&sent));reply.request--;
 reply.payload[41]^=1;assert(!up_completed(&reply,&sent));reply.payload[41]^=1;
 reply.payload[16]^=1;ul_p16(reply.payload+41,ul_crc(reply.payload,41));assert(!up_completed(&reply,&sent));
 p[11]=3;ul_p16(p+30,ul_crc(p,30));assert(!up_native_ping(p,32));p[11]=2;
 ul_p16(p+8,48);ul_p16(p+30,ul_crc(p,30));assert(!up_native_ping(p,32));
 /* New read-only status route accepts only its exact correlated snapshot. */
 p[11]=2;ul_p16(p+8,2);ul_p16(p+30,ul_crc(p,30));assert(up_native_status(p,32));
 reply=(ul_packet){.version=1,.type=UP_RESULT,.sender=456,.origin=sent.sender,.request=sent.request,.size=56};
 uint8_t *b=reply.payload;ul_p16(b,0x0901);ul_p16(b+2,0xc001);ul_p16(b+4,49);
 b[6]=1;b[7]=1;ul_p16(b+8,58);b[10]=2;b[11]=1;memcpy(b+12,p+12,8);
 ul_p32(b+20,456);ul_p16(b+28,24);b[30]=1;b[31]=3;b[32]=1;b[38]=1;
 ul_p16(b+54,ul_crc(b,54));assert(up_status_completed(&reply,&sent));
 b[16]^=1;ul_p16(b+54,ul_crc(b,54));assert(!up_status_completed(&reply,&sent));
 puts("PASS: fragmented PING, IHU engine completion, duplicate caching, reply correlation and rejection");
}
