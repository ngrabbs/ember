#pragma once
#include "boot_demo_link.h"

enum demo_stage { DEMO_LOCAL, DEMO_EPS, DEMO_PROBE, DEMO_WAIT, DEMO_BEACON, DEMO_LISTEN, DEMO_FAILED };
static struct {
    enum demo_stage stage;
    uint32_t since,radio_boot,last_send,last_rx,stop_at,last_log;
    bool antenna,probe_sent,stop_pending,usb;
    unsigned count,shown;
    struct {uint32_t at;const char *line;} events[24];
} startup_demo;

static void demo_history(bool reply) {
    for(unsigned i=0;i<startup_demo.count;i++)
        ihu_printf(reply,"STARTUP t_ms=%" PRIu32 " %s\n",startup_demo.events[i].at,startup_demo.events[i].line);
}
static void demo_event(const char *line) {
    uint32_t now=now_ms();
    if(startup_demo.count<sizeof(startup_demo.events)/sizeof(startup_demo.events[0])){
        unsigned i=startup_demo.count++;
        startup_demo.events[i].at=now;startup_demo.events[i].line=line;
    }
}
static void demo_stage(enum demo_stage stage,uint32_t now) {
    startup_demo.stage=stage;startup_demo.since=now;
}
static void demo_fail(const char *reason) {
    if(startup_demo.stage==DEMO_FAILED)return;
    uint32_t now=now_ms();
    demo_event(reason);
    demo_event("SAFE: outputs off; no automatic retry");
    policy.mode=IP_SAFE;policy.reason=reason;policy.outputs=0;
    startup_demo.stop_pending=startup_demo.radio_boot!=0;startup_demo.stop_at=now;
    demo_stage(DEMO_FAILED,now);
}
static bool demo_send(unsigned id,uint32_t radio_boot) {
    cf_frame f=bd_frame(id,boot,radio_boot);
    return ihu_can_send(&can,&f);
}
static void demo_receive(const cf_frame *f,uint32_t now) {
    if(f->size!=8 || ul_u32(f->data)!=boot)return;
    uint32_t sender=ul_u32(f->data+4);
    if(f->id==BD_READY && startup_demo.stage==DEMO_PROBE && startup_demo.probe_sent &&
       sender && (uint32_t)(now-startup_demo.since)<12000){
        startup_demo.radio_boot=sender;
        demo_event("Checking UHF transceiver... PASSED (demo CAN handshake, TX off)");
        policy.mode=IP_STARTUP;policy.reason="DEMO_RELEASE_TIMERS";
        demo_event("SAFE -> STARTUP");
        demo_event("Release switches A and B released [SIMULATED]");
        demo_event("Antenna release timer 10 s; radio silence timer 15 s [DEMO]");
        demo_stage(DEMO_WAIT,now);
    }
    if(!sender || sender!=startup_demo.radio_boot)return;
    if(f->id==BD_FAILED)demo_fail("UHF transceiver... FAILED (stopped or radio fault)");
    if(f->id==BD_RX && startup_demo.stage==DEMO_BEACON &&
       (uint32_t)(now-startup_demo.since)<BD_CW_LIMIT_MS+2000){
        demo_event("CW beacon complete; transmitter muted");
        demo_event("Checking UHF receive readiness... PASSED");
        policy.mode=IP_NOMINAL;policy.reason="DEMO_RX_ONLY";policy.outputs=0;
        demo_event("COMMISSIONING -> NOMINAL: UHF LISTEN ONLY");
        demo_stage(DEMO_LISTEN,now);
    }
    if(f->id==BD_RX && startup_demo.stage==DEMO_LISTEN)startup_demo.last_rx=now;
}
static void demo_step(void) {
    uint32_t now=now_ms();
    bool live=stdio_usb_connected();
    if(live && !startup_demo.usb)startup_demo.shown=0;
    if(live && startup_demo.shown<startup_demo.count &&
       (uint32_t)(now-startup_demo.last_log)>=20){
        unsigned i=startup_demo.shown++;
        startup_demo.last_log=now;
        ihu_printf(false,"STARTUP t_ms=%" PRIu32 " %s\n",startup_demo.events[i].at,startup_demo.events[i].line);
    }
    startup_demo.usb=live;
    ihu_can_poll_tx(&can,now);
    bool local_ok=can.ready && !(ihu_can_register(0x0e)&0xe0) && !ihu_can_register(0x2d);
    if(startup_demo.stage!=DEMO_FAILED && !local_ok)demo_fail("Checking local CAN controller... FAILED");
    if(startup_demo.stage!=DEMO_FAILED && startup_demo.stage!=DEMO_LOCAL &&
       ((housekeeping.attempted && !housekeeping.valid) ||
        (housekeeping.valid && (uint32_t)(now-housekeeping.sampled)>6500)))
        demo_fail("Checking EPS telemetry... FAILED (invalid or stale)");
    uint32_t elapsed=now-startup_demo.since;
    switch(startup_demo.stage){
    case DEMO_LOCAL:
        demo_event("Checking local CAN controller... PASSED");
        demo_event("Checking EPS telemetry...");
        demo_stage(DEMO_EPS,now);
        break;
    case DEMO_EPS:
        if(housekeeping.valid){
            demo_event("Checking EPS telemetry... PASSED (valid register read)");
            demo_event("Checking UHF transceiver...");
            demo_stage(DEMO_PROBE,now);
        }else if(elapsed>=7000)demo_fail("Checking EPS telemetry... FAILED (timeout)");
        break;
    case DEMO_PROBE:
        if(elapsed>=12000)demo_fail("Checking UHF transceiver... FAILED (no demo READY)");
        else if(!startup_demo.probe_sent || (uint32_t)(now-startup_demo.last_send)>=500){
            if(!can.pending && demo_send(BD_PROBE,0)){
                startup_demo.probe_sent=true;startup_demo.last_send=now;
            }
        }
        break;
    case DEMO_WAIT:
        if(elapsed>=BD_ANTENNA_MS && !startup_demo.antenna){
            startup_demo.antenna=true;
            demo_event("Antenna release timer expired - deploying antenna [SIMULATED]");
        }
        if(elapsed>=BD_SILENCE_MS){
            demo_event("Radio silence timer expired [DEMO]");
            policy.mode=IP_COMMISSIONING;policy.reason="DEMO_BEACON_AND_RX";
            demo_event("STARTUP -> COMMISSIONING");
            demo_event("Checking antenna deployment result... PASSED [SIMULATED]");
            demo_event("Requesting initial CW beacon: KI5YNG - EMBER BOOT");
            /* Mark admission before send. No retry after a possibly delivered request. */
            demo_stage(DEMO_BEACON,now);startup_demo.last_send=now;
            if(!demo_send(BD_FIRE,startup_demo.radio_boot))demo_fail("CW request... FAILED (submission)");
        }
        break;
    case DEMO_BEACON:
        if(elapsed>=BD_CW_LIMIT_MS+2000)demo_fail("CW/RX completion... FAILED (timeout; outcome unknown)");
        else if((uint32_t)(now-startup_demo.last_send)>=BD_KEEP_PERIOD_MS && !can.pending &&
                demo_send(BD_KEEP,startup_demo.radio_boot))startup_demo.last_send=now;
        break;
    case DEMO_LISTEN:
        if((uint32_t)(now-startup_demo.last_rx)>=BD_RX_TIMEOUT_MS)
            demo_fail("UHF receive readiness... FAILED (status timeout)");
        break;
    case DEMO_FAILED:
        if(startup_demo.stop_pending &&
           ((uint32_t)(now-startup_demo.stop_at)>=1000 ||
            (local_ok && !can.pending && demo_send(BD_STOP,startup_demo.radio_boot))))
            startup_demo.stop_pending=false;
        break;
    }
    if(startup_demo.stage!=DEMO_FAILED)housekeeping_pump(now);
}
