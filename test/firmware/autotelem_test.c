#include <assert.h>
#include <stdio.h>
#include "autotelem.h"

int main(void) {
    at_state s={0};
    assert(at_poll(&s,UINT32_MAX,true)==AT_NONE); /* Disabled at boot. */
    assert(!at_enable(&s,0,0) && !at_enable(&s,4,0) && !at_enable(&s,3601,0));
    assert(!s.enabled);
    assert(at_enable(&s,AT_DEFAULT_SECONDS,1000));
    assert(s.period_ms==20000 && s.next_ms==21000);
    assert(at_poll(&s,20999,true)==AT_NONE);
    assert(at_poll(&s,21000,true)==AT_READ && s.due==1 && s.next_ms==41000);
    assert(at_poll(&s,41000,false)==AT_SKIP && s.skipped==1);
    assert(at_poll(&s,41001,true)==AT_NONE); /* No queued retry when idle. */
    assert(at_poll(&s,100000,true)==AT_READ && s.next_ms==120000);
    assert(at_poll(&s,100000,true)==AT_NONE); /* No catch-up burst. */
    at_disable(&s);assert(at_poll(&s,120000,true)==AT_NONE);
    assert(at_enable(&s,5,UINT32_MAX-2000));
    assert(s.next_ms==2999 && at_poll(&s,UINT32_MAX,true)==AT_NONE);
    assert(at_poll(&s,2998,true)==AT_NONE && at_poll(&s,2999,true)==AT_READ);
    assert(at_enable(&s,3600,3000) && s.period_ms==3600000);
    assert(at_poll(&s,3000,true)==AT_NONE); /* Re-enable starts a fresh period. */
    uint32_t deadline=s.next_ms;
    assert(!at_enable(&s,UINT32_MAX,0) && s.enabled && s.next_ms==deadline);
    puts("autotelem: boot-off, bounds, cadence, busy skip, no catch-up, disable and wrap PASS");
}
