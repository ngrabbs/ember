#include <assert.h>
#include <stdio.h>
#include "uplink_ping.h"
#include "payload_protocol.h"
int main(void){
 uint8_t raw[16]={2,2,2,0};ul_p32(raw+4,42);ul_p32(raw+12,1);
 assert(pl_fire_valid(raw,16,42));raw[0]=1;assert(!pl_fire_valid(raw,16,42));
 raw[0]=2;raw[2]=1;assert(!pl_fire_valid(raw,16,42));raw[2]=2;
 ul_packet sent={.version=1,.type=UP_PING,.sender=11,.origin=11,.request=7,.size=32};
 ul_p32(sent.payload+12,9);ul_p32(sent.payload+16,8);
 ul_packet reply={.version=1,.type=UP_RESULT,.sender=22,.origin=11,.request=7,.size=52};
 uint8_t *b=reply.payload;ul_p16(b,0x0901);ul_p16(b+2,0xc000);ul_p16(b+4,45);
 b[6]=1;b[7]=1;ul_p16(b+8,57);b[10]=2;b[11]=1;memcpy(b+12,sent.payload+12,8);
 ul_p32(b+20,22);ul_p16(b+28,20);b[30]=2;b[31]=2;b[32]=2;b[33]=2;
 ul_p32(b+38,42);ul_p32(b+46,1);ul_p16(b+50,ul_crc(b,50));assert(up_fire_completed(&reply,&sent));
 b[30]=1;ul_p16(b+50,ul_crc(b,50));assert(!up_fire_completed(&reply,&sent));
 b[30]=2;b[33]=1;ul_p16(b+50,ul_crc(b,50));assert(!up_fire_completed(&reply,&sent));
 puts("PASS: v2 UNKNOWN explicit, legacy binary preserved, no UNKNOWN stub or v1 acceptance");
}
