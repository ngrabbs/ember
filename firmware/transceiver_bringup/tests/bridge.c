#include <assert.h>
#include "rf_bridge.h"
static bool run(ul_packet *in,uint16_t token,uint8_t *out) {
    cf_reader f={0};f.token=token;f.used=ul_encode(in,f.wire);uint32_t request=0;
    bool ok=bridge_heartbeat(&f,out,&request);if(ok)assert(request==in->request);return ok;
}
int main(void) {
    uint8_t frame[BPSK_FRAME_SIZE],out[38];
    assert(bpsk_frame(frame,sizeof(frame),123,7,456));
    ul_packet in={.version=1,.type=CF_CHAIN,.sender=123,.origin=123,.request=19,.size=38};
    memcpy(in.payload,frame+43,38);in.payload[10]=2;bp16(in.payload+36,bp_crc16(in.payload,36));
    assert(run(&in,19,out));assert(!memcmp(out,in.payload,38));
    bridge_frame(frame,out,19);assert(!memcmp(frame+43,out,38));
    assert(ul_u32(frame+37)==19 && ul_u32(frame+81)==bp_crc32(frame+36,45));
    assert(!run(&in,20,out));
    in.type=UL_ECHO;assert(!run(&in,19,out));in.type=CF_CHAIN;
    in.origin=124;assert(!run(&in,19,out));in.origin=123;
    in.version=2;assert(!run(&in,19,out));in.version=1;
    in.size=37;assert(!run(&in,19,out));in.size=38;
    /* Valid outer envelope must not bypass native CRC, identity, kind or source checks. */
    for(unsigned at=0;at<38;at++) {
        in.payload[at]^=1;assert(!run(&in,19,out));in.payload[at]^=1;
    }
    const unsigned fields[]={0,4,6,7,8,10,11,20,28};
    for(unsigned i=0;i<sizeof(fields)/sizeof(*fields);i++) {
        unsigned at=fields[i];uint8_t old=in.payload[at];in.payload[at]=0xff;
        bp16(in.payload+36,bp_crc16(in.payload,36));assert(!run(&in,19,out));
        in.payload[at]=old;bp16(in.payload+36,bp_crc16(in.payload,36));
    }
    cf_reader f={0};f.token=19;f.used=ul_encode(&in,f.wire);f.wire[f.used++]=1;uint32_t request;
    assert(!bridge_heartbeat(&f,out,&request));
    f.used=ul_encode(&in,f.wire);f.wire[5]^=1;assert(!bridge_heartbeat(&f,out,&request));
    return 0;
}
