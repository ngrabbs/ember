#include <assert.h>
#include <stdio.h>
#include "uart_link.h"
static bool decode(ul_reader *r,const uint8_t *wire,size_t n,uint32_t now,ul_packet *p) {
    bool found=false;
    for(size_t i=0;i<n;++i)if(ul_feed(r,wire[i],now,p))found=true;
    return found;
}
int main(void) {
    assert(ul_crc((const uint8_t *)"123456789",9)==0x29b1);
    ul_packet p={0},out,reply;p.version=1;p.type=UL_ECHO;p.sender=0x11223344;p.origin=p.sender;p.request=7;
    uint8_t wire[UL_WIRE_MAX];ul_reader r={0};
    for(unsigned pattern=0;pattern<3;++pattern)for(unsigned n=1;n<=UL_PAYLOAD_MAX;++n) {
        p.size=(uint16_t)n;
        for(unsigned i=0;i<n;++i)p.payload[i]=pattern==0?0:pattern==1?0x55:(uint8_t)i;
        size_t w=ul_encode(&p,wire);assert(w<=UL_WIRE_MAX);
        assert(decode(&r,wire,w,1,&out));assert(out.size==n && !memcmp(out.payload,p.payload,n));
        ul_reply(&out,0xaabbccdd,&reply);assert(reply.type==UL_ECHO_ACK && reply.sender==0xaabbccdd);
        assert(reply.origin==p.sender && reply.request==7 && reply.size==n && !memcmp(reply.payload,p.payload,n));
    }
    // Literal independently calculated HELLO frame, including zeros in integers.
    const uint8_t hello[]={0xd,0x45,0x55,0x1,0x1,0x11,0x22,0x33,0x44,0x11,0x22,0x33,0x44,0x1,0x1,0x2,0x7,0x1,0x3,0x53,0x8b,0x0};
    ul_packet literal=p;literal.type=UL_HELLO;literal.size=0;
    assert(ul_encode(&literal,wire)==sizeof(hello) && !memcmp(wire,hello,sizeof(hello)));
    assert(decode(&r,hello,sizeof(hello),1,&out));
    assert(out.type==UL_HELLO && out.sender==0x11223344 && out.origin==0x11223344 && out.request==7 && !out.size);
    p.size=240;for(unsigned i=0;i<240;++i)p.payload[i]=0x55;
    size_t w=ul_encode(&p,wire);wire[6]^=1;
    assert(!decode(&r,wire,w,2,&out));assert(r.crc_errors==1);
    const uint8_t malformed[]={5,1,2,0};assert(!decode(&r,malformed,sizeof(malformed),3,&out));assert(r.framing_errors==1);
    for(unsigned i=0;i<UL_ENCODED_MAX+1;++i)assert(!ul_feed(&r,1,4,&out));
    assert(r.overflows==1);assert(!ul_feed(&r,0,4,&out));
    w=ul_encode(&p,wire);assert(decode(&r,wire,w,5,&out));
    assert(!decode(&r,wire,5,6,&out));ul_expire(&r,256);assert(r.gaps==1 && r.discard);
    assert(!decode(&r,wire+5,w-5,257,&out));assert(decode(&r,wire,w,258,&out));
    // Unsigned timer wrap and recovery after a truncated frame.
    assert(!decode(&r,wire,5,UINT32_MAX-100,&out));ul_expire(&r,150);assert(r.gaps==2);
    assert(!ul_feed(&r,0,150,&out));assert(decode(&r,wire,w,151,&out));
    p.version=2;ul_reply(&p,8,&reply);assert(reply.type==UL_ERROR && reply.payload[0]==UL_ERR_VERSION);
    p.version=1;p.type=0x33;ul_reply(&p,8,&reply);assert(reply.payload[0]==UL_ERR_TYPE);
    p.type=UL_ECHO;p.origin=9;ul_reply(&p,8,&reply);assert(reply.payload[0]==UL_ERR_REQUEST);
    p.origin=p.sender;p.size=0;ul_reply(&p,8,&reply);assert(reply.payload[0]==UL_ERR_PAYLOAD);
    p.type=UL_HELLO;ul_reply(&p,8,&reply);assert(reply.type==UL_HELLO_ACK && !reply.size);
    p.size=241;assert(!ul_encode(&p,wire));p.size=0;p.sender=0;assert(!ul_encode(&p,wire));
    // COBS 254-byte nonzero run must produce an ff block and round trip.
    uint8_t raw[260],encoded[262],decoded[260];memset(raw,0x66,sizeof(raw));
    size_t encoded_size=ul_cobs_encode(raw,sizeof(raw),encoded);assert(encoded[0]==255);
    assert(ul_cobs_decode(encoded,encoded_size,decoded)==sizeof(raw));assert(!memcmp(raw,decoded,sizeof(raw)));
    puts("PASS: 720 payload patterns/sizes, CRC, COBS ff, malformed, overflow, gap/wrap, rejection, recovery");
}
