#include <assert.h>
#include "rf_queue.h"
#include "uhf_client.h"
int main(void) {
    rq_state q={0};uc_state client={0};uint8_t status;
    ul_packet p={.version=1,.type=CF_UHF_SEND,.sender=123,.origin=123,.request=1,.size=3,.payload={1,2,3}},r;
    assert(rq_admit(&q,&p,&status)==CF_UHF_ADMITTED && status==0 && q.count==1);
    assert(uc_start(&client,&p,456,0));
    uhf_reply(&p,456,CF_UHF_ADMITTED,0,&r);
    assert(uc_receive(&client,&r) && uc_count(&client)==1 && client.items[0].admitted);
    assert(rq_admit(&q,&p,&status)==CF_UHF_ADMITTED && q.count==1);
    p.type=CF_UHF_FIRMWARE;assert(rq_admit(&q,&p,&status)==CF_UHF_REJECTED && status==UHF_CONFLICT);p.type=CF_UHF_SEND;
    p.payload[0]^=1;assert(rq_admit(&q,&p,&status)==CF_UHF_REJECTED && status==UHF_CONFLICT);p.payload[0]^=1;
    for(unsigned i=2;i<=4;i++){p.request=i;assert(rq_admit(&q,&p,&status)==CF_UHF_ADMITTED);assert(uc_start(&client,&p,456,0));}
    p.request=5;assert(!uc_start(&client,&p,456,0));
    assert(rq_admit(&q,&p,&status)==CF_UHF_REJECTED && status==UHF_FULL && q.count==4);
    p.origin=124;assert(rq_admit(&q,&p,&status)==CF_UHF_REJECTED);p.origin=123;
    p.request=1;uhf_reply(&p,456,CF_UHF_RESULT,UHF_OK,&r);
    ul_packet bad=r;bad.sender++;assert(!uc_receive(&client,&bad));
    bad=r;bad.origin++;assert(!uc_receive(&client,&bad));
    bad=r;bad.request=99;assert(!uc_receive(&client,&bad));
    bad=r;bad.size--;assert(!uc_receive(&client,&bad));
    bad=r;bad.payload[4]^=1;assert(!uc_receive(&client,&bad));
    bad=r;bad.payload[1]=99;assert(!uc_receive(&client,&bad));
    assert(uc_receive(&client,&r) && uc_count(&client)==3);assert(!uc_receive(&client,&r));
    rq_finish(&q,UHF_OK);assert(q.items[0].packet.request==2);
    assert(rq_admit(&q,&p,&status)==CF_UHF_RESULT && status==UHF_OK && q.count==3);
    p.request=2;rq_finish(&q,UHF_FAILED);
    assert(rq_admit(&q,&p,&status)==CF_UHF_RESULT && status==UHF_FAILED);
    uhf_reply(&p,456,CF_UHF_RESULT,UHF_FAILED,&r);assert(uc_receive(&client,&r));
    p.request=3;rq_finish(&q,UHF_CANCELLED);
    assert(rq_admit(&q,&p,&status)==CF_UHF_RESULT && status==UHF_CANCELLED);
    uhf_reply(&p,456,CF_UHF_RESULT,UHF_CANCELLED,&r);assert(uc_receive(&client,&r));
    p.request=4;rq_finish(&q,UHF_CANCELLED);
    uhf_reply(&p,456,CF_UHF_REJECTED,UHF_FULL,&r);assert(uc_receive(&client,&r));assert(!uc_count(&client));
    for(unsigned i=5;i<20;i++){p.request=i;assert(rq_admit(&q,&p,&status)==CF_UHF_ADMITTED);rq_finish(&q,UHF_OK);}
    p.request=1;assert(rq_admit(&q,&p,&status)==CF_UHF_REJECTED && status==UHF_STALE);
    p.origin=p.sender=125;p.request=1;assert(rq_admit(&q,&p,&status)==CF_UHF_ADMITTED);
    assert(q.count==1 && q.history_count==0);
    p.request=22;assert(uc_start(&client,&p,456,0));
    uhf_reply(&p,456,CF_UHF_REJECTED,UHF_DISABLED,&r);
    bad=r;bad.payload[1]=UHF_FAILED;assert(!uc_receive(&client,&bad));
    assert(uc_receive(&client,&r) && !uc_count(&client));
    return 0;
}
