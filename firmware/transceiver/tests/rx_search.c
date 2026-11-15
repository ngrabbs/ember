/* Regression runner for retained real ADC samples; never dispatches a command. */
#include <assert.h>
#include <stdio.h>
#include "../rx_decode.h"
static unsigned probes,limit;
static bool bounded(void){return ++probes<=limit;}
int main(int argc,char **argv){
 assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
 static uint16_t samples[32768];assert(fread(samples,2,32768,f)==32768);fclose(f);
 rd_result first={0},second={0};limit=3;
 assert(rd_decode(samples,32768,&first,bounded));
 unsigned initial=probes;probes=0;limit=1;
 assert(rd_decode(samples,32768,&second,bounded));
 assert(first.size==second.size && !memcmp(first.packet,second.packet,first.size));
 printf("PASS: CRC-valid captured command at %uHz in %u candidates; cached reacquisition in %u\n",
        first.frequency,initial,probes);
}
