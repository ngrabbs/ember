#include <assert.h>
#include <stdio.h>
#include "can_fragment.h"
int main(void) {
    cf_reader r={0};cf_frame f;uint8_t wire[UL_WIRE_MAX];
    for(unsigned n=1;n<=UL_WIRE_MAX;++n) {
        for(unsigned i=0;i<n;++i)wire[i]=(uint8_t)i;
        unsigned count=(n+3)/4;
        for(unsigned i=0;i<count;++i) {
            assert(cf_fragment(wire,n,CF_IHU_ID,123,i,&f));
            assert(cf_feed(&r,&f,CF_IHU_ID,i)==(i+1==count));
        }
        assert(r.used==n && !memcmp(r.wire,wire,n));
    }
    assert(!cf_fragment(wire,UL_WIRE_MAX+1,CF_IHU_ID,1,0,&f));
    assert(cf_fragment(wire,240,CF_IHU_ID,2,0,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,0));
    assert(cf_fragment(wire,240,CF_IHU_ID,2,2,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,1));assert(!r.active);
    assert(cf_fragment(wire,240,CF_IHU_ID,2,0,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,2));
    assert(!cf_feed(&r,&f,CF_IHU_ID,3));assert(!r.active); // Duplicate START aborts.
    assert(!cf_feed(&r,&f,CF_COMMS_ID,3));assert(!r.active); // Wrong route ignored.
    assert(cf_fragment(wire,240,CF_IHU_ID,2,0,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,UINT32_MAX-200));
    cf_expire(&r,300);assert(!r.active && r.timeouts==1);
    assert(cf_fragment(wire,8,CF_IHU_ID,3,0,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,301));
    assert(cf_fragment(wire,8,CF_IHU_ID,4,1,&f));assert(!cf_feed(&r,&f,CF_IHU_ID,302));assert(!r.active);
    assert(cf_fragment(wire,3,CF_IHU_ID,5,0,&f));assert(cf_feed(&r,&f,CF_IHU_ID,303));
    f.data[0]=0x20;assert(!cf_feed(&r,&f,CF_IHU_ID,304));
    f.size=9;assert(!cf_feed(&r,&f,CF_IHU_ID,305));
    // Envelope integrity and identity across real fragmentation and reassembly.
    ul_packet source={0},decoded;source.version=1;source.type=CF_CHAIN;
    source.sender=0x12345678;source.origin=source.sender;source.request=0x10203;
    for(unsigned size=1;size<=240;++size) {
        source.size=(uint16_t)size;for(unsigned i=0;i<size;++i)source.payload[i]=(uint8_t)i;
        size_t length=ul_encode(&source,wire);unsigned frames=(unsigned)((length+3)/4);
        for(unsigned i=0;i<frames;++i) {
            assert(cf_fragment(wire,length,CF_IHU_ID,(uint16_t)source.request,i,&f));
            assert(cf_feed(&r,&f,CF_IHU_ID,400+i)==(i+1==frames));
        }
        ul_reader parser={0};bool complete=false;
        for(size_t i=0;i<r.used;++i)if(ul_feed(&parser,r.wire[i],500,&decoded))complete=true;
        assert(complete && decoded.sender==source.sender && decoded.origin==source.origin);
        assert(decoded.request==source.request && decoded.type==CF_CHAIN && decoded.size==size);
        assert(!memcmp(decoded.payload,source.payload,size));
    }
    puts("PASS CAN: 263 bounds, missing/duplicate/token/route, timeout/wrap, recovery");
}
