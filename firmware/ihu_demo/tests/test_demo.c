#include <assert.h>
#include <stdio.h>
#include "../demo.h"
static void release(demo_state *s,uint32_t now) {
    demo_tick(s,now,true,true);demo_tick(s,now+249,true,true);assert(!s->released);
    demo_tick(s,now+250,true,true);assert(s->released);
}
int main(void) {
    demo_state s;
    demo_init(&s,0,true,true);assert(s.policy.mode==IP_SAFE);assert(demo_start(&s));
    demo_tick(&s,1,false,false);demo_tick(&s,251,false,false);assert(!demo_start(&s));
    demo_tick(&s,300,true,false);demo_tick(&s,1000,true,false);assert(!s.released);
    demo_tick(&s,1001,false,false);demo_tick(&s,1251,false,false);
    release(&s,2000);assert(s.release_ms==2250);assert(demo_approve(&s));assert(demo_checkout(&s));
    demo_tick(&s,12249,true,true);assert(!s.antenna && !s.rf);
    demo_tick(&s,12250,true,true);assert(s.antenna && !s.rf && s.policy.mode==IP_STARTUP);
    demo_tick(&s,17249,true,true);assert(s.policy.mode==IP_STARTUP);
    demo_tick(&s,17250,true,true);assert(s.policy.mode==IP_COMMISSIONING);assert(demo_approve(&s));
    assert(!demo_checkout(&s));assert(!demo_approve(&s));assert(s.policy.mode==IP_NOMINAL);
    s.policy.outputs=63;demo_tick(&s,18000,false,true);assert(s.policy.mode==IP_SAFE && !s.policy.outputs && !s.released);
    demo_health(&s,false);assert(demo_start(&s));demo_health(&s,true);assert(s.policy.mode==IP_SAFE);
    /* Bounce must restart qualification; delayed ticks never shorten either wait. */
    demo_init(&s,0,false,false);assert(!demo_start(&s));
    demo_tick(&s,1,true,true);demo_tick(&s,200,false,true);demo_tick(&s,300,true,true);
    demo_tick(&s,549,true,true);assert(!s.released);demo_tick(&s,550,true,true);assert(s.released);
    demo_health(&s,false);assert(s.policy.mode==IP_SAFE && !s.checkout);
    /* A closing input cannot qualify release from its stale open debounce state. */
    demo_init(&s,0,false,false);assert(!demo_start(&s));
    demo_tick(&s,1,true,false);demo_tick(&s,251,true,false);
    demo_tick(&s,300,true,true);demo_tick(&s,550,false,true);assert(!s.released);
    /* NOMINAL still needs current health after checkout. */
    demo_init(&s,0,false,false);assert(!demo_start(&s));release(&s,1);
    demo_tick(&s,s.release_ms+15000,true,true);assert(!demo_checkout(&s));
    demo_health(&s,false);assert(demo_approve(&s));assert(!s.checkout);
    /* Unsigned millisecond wrap remains bounded at both debounce and waits. */
    uint32_t t=UINT32_MAX-100;
    demo_init(&s,t,false,false);assert(!demo_start(&s));release(&s,t+1);
    demo_tick(&s,s.release_ms+14999,true,true);assert(s.policy.mode==IP_STARTUP);
    demo_tick(&s,s.release_ms+15000,true,true);assert(s.policy.mode==IP_COMMISSIONING);
    demo_tick(&s,s.release_ms+15001,true,false);assert(s.policy.mode==IP_SAFE);
    /* Reboot does not restore progress or authorize an already-open harness. */
    demo_init(&s,0,true,true);assert(!s.released && !s.checkout && s.policy.mode==IP_SAFE);assert(demo_start(&s));
    puts("IHU demo state-machine tests passed");
}
