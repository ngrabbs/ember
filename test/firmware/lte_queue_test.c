#include <assert.h>
#include "lte_queue.h"
int main(void) {
    lq_state q={0};uint8_t packet[128],status[16]={0};
    for(unsigned i=0;i<sizeof(packet);++i)packet[i]=(uint8_t)i;
    assert(!lq_push(&q,packet,241,0));
    for(unsigned i=0;i<4;++i) {packet[0]=(uint8_t)i;assert(lq_push(&q,packet,sizeof(packet),0xfffffff0));}
    assert(!lq_push(&q,packet,sizeof(packet),0xfffffff0) && q.full==1 && q.count==4);
    assert(!lq_poll(&q,0xfffffff0));q.enabled=true;
    assert(lq_poll(&q,0xfffffff0));assert(!lq_drop(&q));
    status[0]=6;ul_p32(status+4,120000);
    assert(!lq_status(&q,status,0xfffffff0)); // READY without registration
    assert(!lq_poll(&q,1000));assert(lq_poll(&q,2000));
    status[3]=1;ul_p32(status+4,15999);assert(!lq_status(&q,status,2000));
    assert(lq_poll(&q,4000));ul_p32(status+4,16000);assert(lq_status(&q,status,4000));
    assert(q.state==LQ_SEND && lq_front(&q)->attempts==1 && lq_front(&q)->bytes[0]==0);
    lq_result(&q,UL_ERR_NOT_READY,4000);assert(!lq_poll(&q,5999));assert(lq_poll(&q,6000));
    assert(lq_status(&q,status,6000));lq_result(&q,UL_ERR_BUSY,6000);
    assert(!lq_poll(&q,9999));assert(lq_poll(&q,10000));assert(lq_status(&q,status,10000));
    lq_result(&q,UL_ERR_NOT_READY,10000);assert(q.state==LQ_HELD && q.hold==LQ_HOLD_EXHAUSTED && q.count==4);
    assert(!lq_poll(&q,20000));assert(lq_drop(&q));
    assert(lq_front(&q)->bytes[0]==1);assert(lq_poll(&q,20000));assert(lq_status(&q,status,20000));
    lq_result(&q,UL_ERR_MODEM_UNKNOWN,20000);assert(q.hold==LQ_HOLD_UNKNOWN && q.count==3);
    assert(!lq_poll(&q,22000));assert(lq_drop(&q));
    assert(lq_poll(&q,23000));assert(lq_status(&q,status,23000));
    lq_result(&q,UL_ERR_MODEM_REJECTED,23000);assert(q.hold==LQ_HOLD_REJECTED && q.count==2);
    assert(lq_drop(&q));assert(lq_poll(&q,24000));assert(lq_status(&q,status,24000));
    lq_result(&q,0,24000);assert(q.count==0 && q.accepted==1 && q.state==LQ_IDLE);
    assert(lq_push(&q,packet,sizeof(packet),25000));assert(!lq_poll(&q,325000));
    assert(q.hold==LQ_HOLD_EXPIRED && q.count==1);assert(lq_drop(&q));
    return 0;
}
