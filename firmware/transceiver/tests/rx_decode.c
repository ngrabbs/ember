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
 /* A CRC-valid non-EMBER payload is accepted by the transparent RF link,
  * while legacy native-only capture rejects the same frame. */
 uint8_t opaque[]={0x1a,0xcf,0xfc,0x1d,3,0,0,0,19,0,3,0xff,0x42,0,0,0,0,0};
 bp32(opaque+14,bp_crc32(opaque+4,10));
 memset(&lane,0,sizeof(lane));
 unsigned found=0;
 for(unsigned i=0;i<sizeof(opaque);i++)for(int bit=7;bit>=0;bit--)
  found+=rd_bit_impl(&lane,(opaque[i]>>bit)&1,&r,false);
 assert(found==1 && r.sequence==19 && r.size==3 && !memcmp(r.packet,opaque+11,3));
 memset(&lane,0,sizeof(lane));
 for(unsigned i=0;i<sizeof(opaque);i++)for(int bit=7;bit>=0;bit--)
  assert(!rd_bit(&lane,(opaque[i]>>bit)&1,&r));
 opaque[17]^=1;memset(&lane,0,sizeof(lane));
 for(unsigned i=0;i<sizeof(opaque);i++)for(int bit=7;bit>=0;bit--)
  assert(!rd_bit_impl(&lane,(opaque[i]>>bit)&1,&r,false));
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
