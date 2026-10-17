#include <assert.h>
#include "rf_bridge.h"
static bool run(ul_packet *in,uint16_t token,uint8_t *out) {
    cf_reader f={0};f.token=token;f.used=ul_encode(in,f.wire);uint32_t request=0;
    size_t size=0;bool ok=bridge_telemetry_type(&f,out,&size,&request,in->type==CF_UHF_SEND);if(ok)assert(size==in->size);if(ok)assert(request==in->request);return ok;
}
int main(void) {
    uint8_t frame[BPSK_FRAME_MAX],out[BPSK_NATIVE_MAX];
    assert(bpsk_frame(frame,sizeof(frame),123,7,456));
    ul_packet in={.version=1,.type=CF_CHAIN,.sender=123,.origin=123,.request=19,.size=38};
    memcpy(in.payload,frame+43,38);in.payload[10]=2;bp16(in.payload+36,bp_crc16(in.payload,36));
    assert(run(&in,19,out));assert(!memcmp(out,in.payload,38));
    bridge_frame(frame,out,38,19);assert(!memcmp(frame+43,out,38));
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
    cf_reader f={0};f.token=19;f.used=ul_encode(&in,f.wire);f.wire[f.used++]=1;uint32_t request;size_t size;
    assert(!bridge_telemetry(&f,out,&size,&request));
    f.used=ul_encode(&in,f.wire);f.wire[5]^=1;assert(!bridge_telemetry(&f,out,&size,&request));
    const unsigned ids[]={W_ID_HEARTBEAT,W_ID_SYSTEM_STATUS,W_ID_POWER_STATUS,W_ID_COMM_STATUS,W_ID_LTE_CAN_FIRMWARE,W_ID_LTE_MODEM_FIRMWARE,W_ID_DEVICE_STATUS};
    const unsigned sizes[]={W_SIZE_HEARTBEAT,W_SIZE_SYSTEM_STATUS,W_SIZE_POWER_STATUS,W_SIZE_COMM_STATUS,W_SIZE_LTE_CAN_FIRMWARE,W_SIZE_LTE_MODEM_FIRMWARE,W_SIZE_DEVICE_STATUS};
    for(unsigned i=0;i<7;i++)for(unsigned type=0;type<3;type++) {
        in.type=type==2?CF_UHF_SEND:type?CF_SEND_PACKET:CF_CHAIN;in.size=W_PAYLOAD+sizes[i]+2;
        assert(in.size<=BPSK_NATIVE_MAX);
        memset(in.payload,0,in.size);bp16(in.payload,W_TM_IDENTITY);bp16(in.payload+2,0xc001);
        bp16(in.payload+4,in.size-7);in.payload[6]=1;in.payload[7]=1;
        bp16(in.payload+8,ids[i]);in.payload[10]=2;in.payload[11]=1;
        bp32(in.payload+20,in.sender);bp16(in.payload+28,sizes[i]);
        bp16(in.payload+in.size-2,bp_crc16(in.payload,in.size-2));
        assert(run(&in,19,out));assert(!memcmp(out,in.payload,in.size));
        size_t n=bridge_frame(frame,out,in.size,19);assert(n==in.size+63u);
        assert(n*8u*1000000ull/BPSK_BAUD<1500000);
        assert(!memcmp(frame+43,in.payload,in.size));
        assert(ul_u32(frame+43+in.size)==bp_crc32(frame+36,7+in.size));
        for(unsigned j=0;j<in.size;j++) {
            in.payload[j]^=1;assert(!run(&in,19,out));in.payload[j]^=1;
        }
        in.payload[12]=1;bp16(in.payload+in.size-2,bp_crc16(in.payload,in.size-2));
        assert(!run(&in,19,out));
    }
    assert(!bridge_frame(frame,out,BPSK_NATIVE_MAX+1,1));
    return 0;
}
