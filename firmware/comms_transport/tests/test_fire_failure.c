#include <assert.h>
#include <stdio.h>
#include "uplink_ping.h"
int main(void){
 ul_packet sent={.version=1,.type=UP_PING,.sender=123,.origin=123,.request=1,.size=32};
 uint8_t *p=sent.payload;ul_p16(p,0x1900);ul_p16(p+2,0xc001);ul_p16(p+4,25);p[6]=1;
 ul_p16(p+8,1028);p[10]=1;p[11]=2;ul_p32(p+12,7);ul_p32(p+16,9);ul_p32(p+20,111);
 ul_p16(p+30,ul_crc(p,30));assert(up_native_fire(p,32));
 ul_packet reply={.version=1,.type=UP_RESULT,.sender=456,.origin=123,.request=1,.size=43};
 p=reply.payload;ul_p16(p,0x0901);ul_p16(p+2,0xc001);ul_p16(p+4,36);p[6]=1;p[7]=2;
 ul_p16(p+8,49);p[10]=2;p[11]=1;memcpy(p+12,sent.payload+12,8);ul_p32(p+20,456);
 ul_p16(p+28,11);ul_p16(p+30,1028);p[32]=3;ul_p16(p+33,7);ul_p32(p+37,11);
 ul_p16(p+41,ul_crc(p,41));assert(up_fire_failed(&reply,&sent));assert(!up_fire_completed(&reply,&sent));
 reply.origin++;assert(!up_fire_failed(&reply,&sent));reply.origin--;
 p[16]^=1;ul_p16(p+41,ul_crc(p,41));assert(!up_fire_failed(&reply,&sent));p[16]^=1;
 p[32]=2;ul_p16(p+41,ul_crc(p,41));assert(!up_fire_failed(&reply,&sent));p[32]=3;
 ul_p16(p+41,ul_crc(p,41));p[42]^=1;assert(!up_fire_failed(&reply,&sent));
 puts("PASS: failure correlation, native CRC, stage validation and no false fire completion");
}
