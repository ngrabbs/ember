#include "demo.h"
void demo_safe(demo_state *s, const char *reason) {
    s->policy.mode=IP_SAFE; s->policy.outputs=0; s->policy.reason=reason;
    s->released=s->antenna=s->rf=s->checkout=false;
}
void demo_init(demo_state *s, uint32_t now, bool a, bool b) {
    *s=(demo_state){.health=true,.raw={a,b},.stable={a,b},.changed={now,now}};
    ip_init(&s->policy,IP_GROUND_TEST);
    demo_safe(s,"DEMO_READY_INSTALL_BOTH_JUMPERS");
}
const char *demo_start(demo_state *s) {
    if(s->policy.mode!=IP_SAFE) return "ENTER_SAFE_FIRST";
    if(!s->health) return "SIMULATED_HEALTH_FAILED";
    if(s->raw[0] || s->raw[1] || s->stable[0] || s->stable[1]) return "INSTALL_BOTH_JUMPERS";
    s->released=s->antenna=s->rf=s->checkout=false;
    s->policy.mode=IP_STARTUP;s->policy.outputs=0;s->policy.reason="WAIT_RELEASE";
    return NULL;
}
void demo_health(demo_state *s,bool ok) {
    s->health=ok;
    if(!ok) demo_safe(s,"SIMULATED_HEALTH_FAILED");
}
void demo_tick(demo_state *s,uint32_t now,bool a,bool b) {
    const bool inputs[]={a,b};
    for(unsigned i=0;i<2;i++) {
        if(inputs[i]!=s->raw[i]) {s->raw[i]=inputs[i];s->changed[i]=now;}
        if((uint32_t)(now-s->changed[i])>=DEMO_DEBOUNCE_MS) s->stable[i]=s->raw[i];
    }
    /* Conservative immediate stop on closure; only release needs qualification. */
    if(s->released && (!a || !b)) {demo_safe(s,"RELEASE_SWITCH_REINSERTED");return;}
    if(s->policy.mode!=IP_STARTUP) return;
    if(!s->released && a && b && s->stable[0] && s->stable[1]) {
        s->released=true;s->release_ms=now;s->policy.reason="RELEASE_QUALIFIED_WAIT_TIMERS";
    }
    if(!s->released) return;
    uint32_t elapsed=now-s->release_ms;
    if(elapsed>=DEMO_ANTENNA_MS) s->antenna=true;
    if(elapsed>=DEMO_RF_MS) s->rf=true;
    if(s->antenna && s->rf) {
        s->policy.mode=IP_COMMISSIONING;s->policy.outputs=0;s->policy.reason="SIMULATED_STARTUP_COMPLETE";
    }
}
const char *demo_checkout(demo_state *s) {
    if(s->policy.mode!=IP_COMMISSIONING) return "COMMISSIONING_REQUIRED";
    if(!s->health || !s->released || !s->raw[0] || !s->raw[1]) return "DEMO_GATES_NOT_MET";
    s->checkout=true; return NULL;
}
const char *demo_approve(demo_state *s) {
    if(s->policy.mode!=IP_COMMISSIONING) return "COMMISSIONING_REQUIRED";
    if(!s->checkout) return "CHECKOUT_REQUIRED";
    if(!s->health || !s->released || !s->raw[0] || !s->raw[1]) return "DEMO_GATES_NOT_MET";
    s->policy.mode=IP_NOMINAL;s->policy.outputs=0;s->policy.reason="DEMO_GROUND_APPROVAL";
    return NULL;
}
