#include <assert.h>
#include <stdio.h>
#include "../rx_ping.h"
static void finish(uint8_t *p){bp16(p+30,bp_crc16(p,30));}
static void expect(rp_cache *c,uint8_t *p,const char *status){assert(!strcmp(rp_check(c,p,32),status));}
int main(void){
 rp_cache c={0};uint8_t p[32]={0};
 bp16(p,0x1900);bp16(p+2,0xc001);bp16(p+4,25);p[6]=1;p[7]=0;bp16(p+8,1);p[10]=1;p[11]=2;
 bp32(p+12,0x52585031);bp32(p+16,1);bp32(p+20,0x52585453);finish(p);
 bp16(p+8,W_ID_PAYLOAD_FIRE_CHECK);finish(p);
 expect(&c,p,"PING_ACCEPTED");assert(c.used==1);
 bp16(p+8,W_ID_PING);finish(p);
 bp16(p+2,0xc002);finish(p);expect(&c,p,"PING_DUPLICATE");assert(c.used==1);
 p[11]=3;finish(p);expect(&c,p,"REJECT_ROUTE");p[11]=2;
 p[10]=3;finish(p);expect(&c,p,"REJECT_ROUTE");p[10]=1;
 bp16(p+8,48);finish(p);expect(&c,p,"REJECT_COMMAND");bp16(p+8,1);
 bp32(p+20,99);finish(p);expect(&c,p,"REJECT_TRANSACTION_CONFLICT");bp32(p+20,0x52585453);
 for(unsigned offset=12;offset<=20;offset+=4){uint32_t old=rd_u32(p+offset);bp32(p+offset,0);finish(p);expect(&c,p,"REJECT_IDENTITY");bp32(p+offset,old);}
 finish(p);p[31]^=1;expect(&c,p,"REJECT_FRAME");finish(p);
 assert(!strcmp(rp_check(&c,p,31),"REJECT_SIZE"));
 for(unsigned i=2;i<=16;i++){bp32(p+16,i);finish(p);expect(&c,p,"PING_ACCEPTED");}
 bp32(p+16,17);finish(p);expect(&c,p,"REJECT_CACHE_FULL");assert(c.used==16);
 bp32(p+16,1);finish(p);expect(&c,p,"PING_DUPLICATE");
 puts("PASS: PING route, shape, identity, CRC, duplicate, conflict, full-cache fail closed");
}
