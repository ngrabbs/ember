#include <assert.h>
#include "hello.h"
static size_t run(ul_packet *p, uint16_t token, uint8_t *wire) {
    cf_reader f={0}; f.used=ul_encode(p,f.wire);f.token=token;
    uint32_t request=0;
    return hello_response(&f,42,wire,&request);
}
int main(void) {
    ul_packet in={.version=1,.type=UL_HELLO,.sender=123,.origin=123,.request=7};
    uint8_t wire[UL_WIRE_MAX];size_t n=run(&in,7,wire);assert(n);
    ul_reader r={0};ul_packet out;unsigned count=0;
    for(size_t i=0;i<n;i++)if(ul_feed(&r,wire[i],0,&out))count++;
    assert(count==1&&out.type==UL_HELLO_ACK&&out.sender==42&&out.origin==123&&out.request==7&&!out.size);
    assert(!run(&in,8,wire));
    in.version=2;assert(!run(&in,7,wire));in.version=1;
    in.type=UL_ECHO;assert(!run(&in,7,wire));in.type=UL_HELLO;
    in.origin=456;assert(!run(&in,7,wire));in.origin=123;
    in.size=1;assert(!run(&in,7,wire));in.size=0;
    cf_reader f={0};f.token=7;f.used=ul_encode(&in,f.wire);f.wire[5]^=1;
    uint32_t request;assert(!hello_response(&f,42,wire,&request));
    f.used=ul_encode(&in,f.wire);f.wire[f.used++]=1;
    assert(!hello_response(&f,42,wire,&request));
    return 0;
}
