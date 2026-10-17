#include <stdio.h>
#include <assert.h>
#include "../rx_decode.h"
static bool cancel(void){return false;}
static void parser_checks(void){
 rd_result r={0};rd_lane lane={0};
 /* Reject a syntactically valid sync followed by an oversized frame header. */
 uint8_t bad[]={0x1a,0xcf,0xfc,0x1d,3,0,0,0,1,0xff,0xff};
 for(unsigned i=0;i<sizeof(bad);i++)for(int bit=7;bit>=0;bit--)assert(!rd_bit(&lane,(bad[i]>>bit)&1,&r));
 assert(!lane.collecting);
 static uint16_t flat[32768];for(unsigned i=0;i<32768;i++)flat[i]=2085;
 assert(!rd_decode(flat,32767,&r,NULL));
 assert(!rd_decode(flat,32768,&r,cancel));
}
int main(int argc,char **argv){
 parser_checks();
 assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
 static uint16_t samples[32768];assert(fread(samples,2,32768,f)==32768);fclose(f);
 rd_result r={0};bool ok=rd_decode(samples,32768,&r,NULL);
 if(ok){printf("sequence=%u frequency=%u hex=",r.sequence,r.frequency);for(unsigned i=0;i<r.size;i++)printf("%02x",r.packet[i]);puts("");}
 else puts("NO_PACKET");return 0;
}
