#include <assert.h>
#include "uhf_run.h"
int main(void) {
    ur_state s={0};assert(ur_due(&s,1000,true)==-1);
    assert(!ur_start(&s,0,10,0));assert(!ur_start(&s,121,10,0));
    assert(!ur_start(&s,120,4,0));assert(!ur_start(&s,120,61,0));
    assert(ur_start(&s,120,10,100));assert(!ur_start(&s,120,10,100));
    unsigned packets=0;
    for(unsigned elapsed=0;elapsed<=120000;elapsed+=100) {
        int stage=ur_due(&s,100+elapsed,true);
        if(stage>=0){assert(stage==(int)(packets%4));ur_submitted(&s);packets++;}
    }
    assert(packets==48 && s.cycles==12 && s.state==UR_EXPIRED);
    assert(ur_due(&s,300000,true)==-1);
    assert(ur_start(&s,120,10,0));assert(ur_due(&s,0,false)==-1);
    assert(ur_due(&s,35000,true)==0);ur_submitted(&s);
    assert(ur_due(&s,35001,true)==1);ur_submitted(&s);
    assert(ur_due(&s,35002,true)==2);ur_submitted(&s);
    assert(ur_due(&s,35003,true)==3);ur_submitted(&s);
    assert(ur_due(&s,35004,true)==-1 && s.next==45000); /* No backlog. */
    ur_stop(&s,UR_STOPPED);assert(ur_due(&s,46000,true)==-1);
    assert(ur_start(&s,1,5,UINT32_MAX-499));
    assert(ur_due(&s,UINT32_MAX-499,true)==0);ur_submitted(&s);
    assert(ur_due(&s,501,true)==-1 && s.state==UR_EXPIRED);
    assert(ur_start(&s,120,10,0));ur_stop(&s,UR_FAULT);assert(ur_due(&s,0,true)==-1);
    assert(ur_start(&s,120,10,0));
    ur_link_snapshot(&s,1,3); /* Recovered link with historical errors. */
    assert(!ur_link_changed(&s,1,3));
    assert(ur_link_changed(&s,2,3));assert(ur_link_changed(&s,1,4));
    ur_stop(&s,UR_FAULT);assert(ur_start(&s,120,10,0));
    ur_link_snapshot(&s,2,4);assert(!ur_link_changed(&s,2,4));
    ur_link_snapshot(&s,UINT32_MAX,UINT32_MAX);
    assert(ur_link_changed(&s,0,UINT32_MAX));
    assert(ur_link_changed(&s,UINT32_MAX,0));
    return 0;
}
