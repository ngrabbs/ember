#pragma once
#include "boot_demo_link.h"

enum demo_stage { DEMO_LOCAL, DEMO_EPS, DEMO_PROBE, DEMO_WAIT, DEMO_BEACON, DEMO_ACTIVATE, DEMO_ACTIVE, DEMO_LISTEN, DEMO_FAILED };
static struct {
    enum demo_stage stage;
    uint32_t since,radio_boot,last_send,last_rx,stop_at,last_log,last_heartbeat,tx_at,tx_id,last_up;
    bool heartbeat_enabled,antenna,probe_sent,stop_pending,usb,tx_pending;
    unsigned count,shown;
    struct {uint32_t at;const char *line;} events[24];
} startup_demo;

enum {
    DEMO_LISTEN_DEFAULT_S=540,
    DEMO_TELEMETRY_DEFAULT_S=60,
    DEMO_TELEMETRY_MIN_S=5,
    DEMO_PHASE_MAX_S=3600,
    DEMO_PAYLOAD_TIMEOUT_MS=750,
};
static struct {
    bool enabled;
    uint16_t listen_seconds,telemetry_seconds;
    uint32_t started;
    uint8_t packet_set;
    unsigned next_packet;
} demo_schedule;

static struct {
    bool ready;
    uint32_t cycle,sampled;
    gps_result result;
} demo_gps;

static void demo_gps_complete(const gps_result *gps,uint32_t sampled){
    if(!demo_schedule.enabled || demo_schedule.started!=demo_gps.cycle ||
       demo_schedule.next_packet!=8)return;
    demo_gps.result=*gps;
    demo_gps.sampled=sampled;
    demo_gps.ready=true;
}

static size_t demo_gps_packet(uint8_t *packet){
    const size_t size=W_PAYLOAD+W_SIZE_GPS_STATUS+2;
    _Static_assert(W_PAYLOAD+W_SIZE_GPS_STATUS+2<=BD_PACKET_MAX,"GPS packet exceeds RF link limit");
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_GPS_STATUS,W_SIZE_GPS_STATUS);
    ul_p32(packet+W_UPTIME_MS,demo_gps.sampled);
    uint8_t *p=packet+W_PAYLOAD;
    const gps_result *gps=&demo_gps.result;
    bool fix=gps->status==GPS_FIX;
    p[W_GPS_STATUS_STATUS]=gps->status;
    p[W_GPS_STATUS_SATELLITES]=gps->satellites;
    ul_p32(p+W_GPS_STATUS_LATITUDE_DEG,fix?(int32_t)(gps->latitude*1e7):INT32_MIN);
    ul_p32(p+W_GPS_STATUS_LONGITUDE_DEG,fix?(int32_t)(gps->longitude*1e7):INT32_MIN);
    ul_p32(p+W_GPS_STATUS_ALTITUDE_MSL_M,fix && gps->altitude_valid?(int32_t)(gps->altitude*1000):INT32_MIN);
    ul_p16(packet+size-2,ul_crc(packet,size-2));
    return size;
}

/* The optional poll borrows the CAN request slot until a reply or timeout. */
static struct {
    bool active,valid;
    uint8_t target, request;
    uint32_t peer;
    uint8_t report[FI_SIZE];
} demo_poll;

static void demo_poll_stop(void){
    if(!demo_poll.active)return;
    target_index=demo_poll.target;
    peer=demo_poll.peer;
    pending.active=false;
    output.active=false;
    demo_poll.active=false;
}

static void demo_poll_start(uint8_t node,uint8_t request){
    if(pending.active || output.active)return;
    demo_poll.active=true;
    demo_poll.valid=false;
    demo_poll.target=target_index;
    demo_poll.peer=peer;
    demo_poll.request=request;
    target_index=node;
    peer=node==DR_COMMS_INDEX?startup_demo.radio_boot:0;
    memset(&fragments,0,sizeof(fragments));
    submit(peer?request:UL_HELLO,NULL,0);
}

static void demo_poll_receive(const ul_packet *reply){
    bool hello=pending.packet.type==UL_HELLO;
    uint32_t previous=matched;
    receive(reply);
    if(pending.active)return;
    if(matched!=previous){
        if(hello){
            submit(demo_poll.request,NULL,0);
            if(pending.active)return;
        }else{
            memcpy(demo_poll.report,reply->payload,reply->size);
            demo_poll.valid=true;
        }
    }
    demo_poll_stop();
}

static size_t demo_payload_status_packet(uint8_t *packet){
    const size_t size=W_PAYLOAD+W_SIZE_PAYLOAD_STATUS+2;
    _Static_assert(W_PAYLOAD+W_SIZE_PAYLOAD_STATUS+2<=BD_PACKET_MAX,"Payload packet exceeds RF link limit");
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_PAYLOAD_STATUS,W_SIZE_PAYLOAD_STATUS);
    uint8_t *p=packet+W_PAYLOAD;
    const uint8_t *report=demo_poll.report;
    p[W_PAYLOAD_STATUS_PAYLOAD_VERSION]=report[0];
    p[W_PAYLOAD_STATUS_TRANSPORT]=W_PAYLOAD_TRANSPORT_IHU_NATIVE_RF;
    p[W_PAYLOAD_STATUS_REPORT_KIND]=W_PAYLOAD_REPORT_KIND_STATUS;
    p[W_PAYLOAD_STATUS_NODE]=report[1];
    p[W_PAYLOAD_STATUS_READY]=report[2];
    memcpy(p+W_PAYLOAD_STATUS_REPORTED_BOOT_ID,report+4,PL_REPORT_SIZE-4);
    ul_p16(packet+size-2,ul_crc(packet,size-2));
    return size;
}

/* Reuse the four firmware schemas already installed in Yamcs. */
static const struct {
    uint8_t node,request;
    uint16_t id,size;
} demo_firmware[]={
    {DR_COMMS_INDEX,UL_FIRMWARE_INFO,W_ID_COMMS_FIRMWARE,W_SIZE_COMMS_FIRMWARE},
    {DR_PAYLOAD_INDEX,UL_FIRMWARE_INFO,W_ID_PAYLOAD_FIRMWARE,W_SIZE_PAYLOAD_FIRMWARE},
    {DR_LTE_INDEX,UL_FIRMWARE_INFO,W_ID_LTE_CAN_FIRMWARE,W_SIZE_LTE_CAN_FIRMWARE},
    {DR_LTE_INDEX,CF_MODEM_FIRMWARE,W_ID_LTE_MODEM_FIRMWARE,W_SIZE_LTE_MODEM_FIRMWARE},
};
enum {DEMO_FIRMWARE_START=10, DEMO_FULL_STEPS=DEMO_FIRMWARE_START+2*sizeof(demo_firmware)/sizeof(demo_firmware[0])};

static size_t demo_firmware_packet(uint8_t *packet,unsigned index){
    unsigned id=demo_firmware[index].id;
    size_t payload=demo_firmware[index].size;
    size_t size=W_PAYLOAD+payload+2;
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,id,payload);
    uint8_t *fields=packet+W_PAYLOAD;
    const uint8_t *identity=demo_poll.report;
    if(id==W_ID_COMMS_FIRMWARE){
        packet[W_SOURCE]=W_ENDPOINTS_COMMS;
        ul_p32(packet+W_SOURCE_BOOT_ID,ul_u32(identity+24));
        ul_p32(packet+W_UPTIME_MS,ul_u32(identity+28));
        /* Keep the transceiver's existing header and payload layout. */
        memcpy(fields,identity,W_SIZE_COMMS_FIRMWARE);
    }else if(id==W_ID_PAYLOAD_FIRMWARE){
        fields[W_PAYLOAD_FIRMWARE_TRANSPORT]=W_PAYLOAD_TRANSPORT_IHU_NATIVE_RF;
        memcpy(fields+W_PAYLOAD_FIRMWARE_VERSION_MAJOR,identity,FI_SIZE);
    }else{
        memcpy(fields,identity,FI_SIZE);
    }
    ul_p16(packet+size-2,ul_crc(packet,size-2));
    return size;
}

static cf_reader demo_up;
static uint8_t demo_response[BD_PACKET_MAX];
static size_t demo_response_size;
static uint32_t demo_uplinks,demo_replies,demo_tx_ok,demo_drops;

static bool demo_store_response(const uint8_t *p,size_t n){
    if(demo_response_size || n>sizeof(demo_response))return false;
    memcpy(demo_response,p,n);
    demo_response_size=n;
    ++demo_replies;
    return true;
}

static bool demo_command_reply(const uint8_t *p,size_t n,void *unused){
    const uint8_t *request=unused;
    bool status_request=ul_u16(request+8)==W_ID_REQUEST_STATUS;
    if(status_request && p[W_KIND]==W_KINDS_TELEMETRY && ul_u16(p+8)==W_ID_SYSTEM_STATUS){
        if(demo_response_size)return false;
        demo_response_size=status_packet(demo_response,request);++demo_replies;
        return true;
    }
    if(n!=43 || p[W_KIND]!=W_KINDS_RESPONSE)return false;
    unsigned stage=p[W_PAYLOAD+W_COMMAND_RESPONSE_STAGE];
    if(stage==W_STAGE_ACCEPTED || (status_request && stage==W_STAGE_COMPLETED))return true;
    return demo_store_response(p,n);
}
static bool demo_ack_setting(const ul_packet *request,uint32_t value){
    ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,
        .request=request->request,.size=43};
    cdh_header(reply.payload,43,request,W_KINDS_RESPONSE,W_ID_COMMAND_RESPONSE,11);
    ul_p16(reply.payload+30,ul_u16(request->payload+W_MESSAGE_ID));
    reply.payload[32]=W_STAGE_COMPLETED;
    ul_p32(reply.payload+37,value);
    return cdh_send(&reply);
}
static void demo_restart_schedule(uint32_t now){
    demo_schedule.started=now;
    demo_schedule.next_packet=0;
    demo_poll.valid=false;
    demo_gps.ready=false;
}
static void demo_set_output(const ul_packet *request,uint32_t now){
    const uint8_t *wire=request->payload;
    uint8_t enabled=wire[W_PAYLOAD];
    if(enabled>1){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(ul_u16(wire+W_MESSAGE_ID)==W_ID_SET_HEARTBEAT){
        if(enabled && demo_schedule.enabled){
            cdh_error(request,W_STAGE_REJECTED,W_REASON_MODE_NOT_ALLOWED);
            return;
        }
        if(demo_ack_setting(request,enabled)){
            if(enabled && !startup_demo.heartbeat_enabled)startup_demo.last_heartbeat=now;
            startup_demo.heartbeat_enabled=enabled;
        }
        return;
    }
    if(demo_ack_setting(request,enabled)){
        if(enabled && !demo_schedule.enabled)demo_restart_schedule(now);
        demo_schedule.enabled=enabled;
        if(enabled)startup_demo.heartbeat_enabled=false;
    }
}
static void demo_set_schedule(const ul_packet *request,uint32_t now){
    const uint8_t *args=request->payload+W_PAYLOAD;
    uint16_t listen=ul_u16(args),telem=ul_u16(args+2);
    if(!listen || listen>DEMO_PHASE_MAX_S || telem<DEMO_TELEMETRY_MIN_S || telem>DEMO_PHASE_MAX_S){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(demo_ack_setting(request,ul_u32(args)) &&
       (listen!=demo_schedule.listen_seconds || telem!=demo_schedule.telemetry_seconds)){
        demo_schedule.listen_seconds=listen;
        demo_schedule.telemetry_seconds=telem;
        demo_restart_schedule(now);
    }
}
static void demo_set_packet_set(const ul_packet *request,uint32_t now){
    uint8_t set=request->payload[W_PAYLOAD];
    if(set!=W_UHF_TELEMETRY_SET_BASIC && set!=W_UHF_TELEMETRY_SET_FULL){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(demo_ack_setting(request,set) && set!=demo_schedule.packet_set){
        demo_schedule.packet_set=set;
        demo_restart_schedule(now);
    }
}
static void demo_uplink(const cf_frame *f,uint32_t now){
    static ul_packet p;
    if(!cf_feed(&demo_up,f,BD_UP_ID,now))return;
    if(!bd_packet(&demo_up,&p,startup_demo.radio_boot,boot) || p.request<=startup_demo.last_up)return;
    startup_demo.last_up=p.request;++demo_uplinks;
    if(p.size<32 || demo_response_size || fire_uplink.active || cdh.active){++demo_drops;return;}
    demo_poll_stop();
    unsigned id=ul_u16(p.payload+W_MESSAGE_ID);
    if((id==W_ID_SET_HEARTBEAT || id==W_ID_SET_UHF_TELEMETRY) && up_native_args(p.payload,p.size,1)){
        demo_set_output(&p,now);return;
    }
    if(id==W_ID_SET_UHF_TELEMETRY_SCHEDULE && up_native_args(p.payload,p.size,4)){
        demo_set_schedule(&p,now);return;
    }
    if(id==W_ID_SET_UHF_TELEMETRY_SET && up_native_args(p.payload,p.size,1)){
        demo_set_packet_set(&p,now);return;
    }
    if(up_native_cdh(p.payload,p.size)){cdh_receive(&p);return;}
    if(up_native_fire(p.payload,p.size)){
        if(output.active || pending.active){cdh_error(&p,W_STAGE_REJECTED,W_REASON_BUSY);return;}
        uplink_start_fire(&p);
        return;
    }
    if(!up_native_ping(p.payload,p.size) && !up_native_status(p.payload,p.size)){++demo_drops;return;}
    ember_command(&uplink_engine,p.payload,p.size,now,demo_command_reply,p.payload);
}
static bool demo_queue_packet(const uint8_t *p,size_t n,uint32_t now){
    static ul_packet packet;
    if(!n || n>BD_PACKET_MAX || startup_demo.tx_id==UINT32_MAX)return false;
    packet=(ul_packet){.version=1,.type=BD_PACKET,.sender=boot,.origin=startup_demo.radio_boot,
        .request=++startup_demo.tx_id,.size=(uint16_t)n};
    memcpy(packet.payload,p,n);
    if(!queue(&packet))return false;
    output.route=BD_DOWN_ID;startup_demo.tx_at=now;startup_demo.tx_pending=true;
    return true;
}
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
    output.active=false;demo_response_size=0;startup_demo.tx_pending=false;
    pending.active=false;cdh.active=false;demo_schedule.enabled=false;
    if(fire_uplink.active)fire_restore();
    demo_poll_stop();
    startup_demo.stop_pending=startup_demo.radio_boot!=0;startup_demo.stop_at=now;
    demo_stage(DEMO_FAILED,now);
}
static bool demo_send(unsigned id,uint32_t radio_boot) {
    cf_frame f=bd_frame(id,boot,radio_boot);
    return ihu_can_send(&can,&f);
}
static void demo_receive(const cf_frame *f,uint32_t now) {
    if(startup_demo.stage==DEMO_ACTIVE){
        if(f->id==BD_UP_ID){demo_uplink(f,now);return;}
        if((fire_uplink.active || demo_poll.active) && pending.active && f->id==RX_ID){
            ul_packet reply;
            if(cf_feed(&fragments,f,RX_ID,now) && up_envelope(&fragments,&reply) &&
               reply.origin==boot && reply.request==pending.packet.request){
                if(demo_poll.active)demo_poll_receive(&reply);
                else receive(&reply);
            }
            return;
        }
        if((f->id==BD_TX_OK || f->id==BD_TX_FAILED) && startup_demo.tx_pending &&
           bd_matches(f,startup_demo.tx_id,startup_demo.radio_boot)){
            if(f->id==BD_TX_FAILED)demo_fail("UHF packet TX... FAILED");
            else {startup_demo.tx_pending=false;startup_demo.last_rx=now;++demo_tx_ok;
                dr_seen(&devices[DR_COMMS_INDEX],now,startup_demo.radio_boot);}
            return;
        }
    }
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
#if IHU_BOOT_RX_ONLY
        policy.mode=IP_NOMINAL;policy.reason="DEMO_RX_ONLY";policy.outputs=0;
        demo_event("COMMISSIONING -> NOMINAL: UHF LISTEN ONLY");
        demo_stage(DEMO_LISTEN,now);
#else
        demo_event("Enabling UHF LINK_ACTIVE...");
        demo_stage(DEMO_ACTIVATE,now);startup_demo.last_send=now-200;
#endif
        startup_demo.last_rx=now;
    }
    if(f->id==BD_LINKED && startup_demo.stage==DEMO_ACTIVATE){
        policy.mode=IP_NOMINAL;policy.reason="DEMO_LINK_ACTIVE";policy.outputs=0;
        demo_event("COMMISSIONING -> NOMINAL: UHF LINK_ACTIVE");
        demo_stage(DEMO_ACTIVE,now);
        startup_demo.last_heartbeat=now;
    }
    if((f->id==BD_LINKED && startup_demo.stage==DEMO_ACTIVE) ||
       (f->id==BD_RX && startup_demo.stage==DEMO_LISTEN)){
        startup_demo.last_rx=now;
        dr_seen(&devices[DR_COMMS_INDEX],now,startup_demo.radio_boot);
    }
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
    case DEMO_ACTIVATE:
        if(elapsed>=2000)demo_fail("UHF LINK_ACTIVE... FAILED (no acknowledgement)");
        else if((uint32_t)(now-startup_demo.last_send)>=200 && !can.pending &&
                demo_send(BD_LINK,startup_demo.radio_boot))startup_demo.last_send=now;
        break;
    case DEMO_ACTIVE:
        if((uint32_t)(now-startup_demo.last_rx)>=BD_RX_TIMEOUT_MS)
            demo_fail("UHF LINK_ACTIVE... FAILED (status timeout)");
        else if(startup_demo.tx_pending && (uint32_t)(now-startup_demo.tx_at)>=BD_TX_TIMEOUT_MS)
            demo_fail("UHF packet TX... FAILED (outcome unknown; no retry)");
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
    if(startup_demo.stage!=DEMO_FAILED && !sensor_job.active && (uint32_t)(now-housekeeping.last)>=5000){
        housekeeping.last=now;
        (void)request_sensor(SENSOR_HEALTH,0,false);
    }
}
static void demo_schedule_pump(uint32_t now){
    if(!demo_schedule.enabled)return;
    uint32_t listen_ms=(uint32_t)demo_schedule.listen_seconds*1000;
    uint32_t cycle_ms=listen_ms+(uint32_t)demo_schedule.telemetry_seconds*1000;
    uint32_t elapsed=now-demo_schedule.started;
    if(elapsed>=cycle_ms){
        elapsed%=cycle_ms;
        demo_restart_schedule(now-elapsed);
    }
    /* Leave time for the admitted burst to finish before the listen phase. */
    unsigned count=demo_schedule.packet_set==W_UHF_TELEMETRY_SET_FULL?DEMO_FULL_STEPS:2;
    if(elapsed<listen_ms || cycle_ms-elapsed<=BD_TX_TIMEOUT_MS || demo_schedule.next_packet>=count)return;
    if(demo_schedule.next_packet==7){
        if(cycle_ms-elapsed<=BD_TX_TIMEOUT_MS+2500 || sensor_job.active ||
           now-housekeeping.last>=3500)return;
        demo_gps.cycle=demo_schedule.started;
        ++demo_schedule.next_packet;
        if(!request_sensor(SENSOR_GPS_TELEMETRY,0,false))--demo_schedule.next_packet;
        return;
    }
    if(demo_schedule.next_packet==8 && !demo_gps.ready)return;
    _Static_assert(W_PAYLOAD+W_SIZE_POWER_STATUS+2<=BD_PACKET_MAX,"EPS packet exceeds RF link limit");
    _Static_assert(W_PAYLOAD+W_SIZE_DEVICE_STATUS+2<=BD_PACKET_MAX,"Device packet exceeds RF link limit");
    uint8_t packet[BD_PACKET_MAX];
    size_t size;
    unsigned step=demo_schedule.next_packet++;
    switch(step){
    case 0:
        size=status_packet(packet,NULL);
        break;
    case 1:
        if(!housekeeping.valid)return;
        size=power_packet(packet,&housekeeping.eps,boot,telemetry_sequence++,housekeeping.sampled,++eps_readout_count);
        break;
    case 2:
        size=device_packet(packet,devices,true,boot,telemetry_sequence++,now);
        break;
    case 3:
        size=health_packet(packet,true,boot,telemetry_sequence++,now,cycle_ms,
            uplink_engine.accepted,uplink_engine.rejected,policy.mode,policy.configuration);
        break;
    case 4:
        size=health_packet(packet,false,boot,telemetry_sequence++,now,cycle_ms,
            uplink_engine.accepted,uplink_engine.rejected,policy.mode,policy.configuration);
        break;
    case 5:
        if(cycle_ms-elapsed>BD_TX_TIMEOUT_MS+2*DEMO_PAYLOAD_TIMEOUT_MS)
            demo_poll_start(DR_PAYLOAD_INDEX,PL_STATUS);
        return;
    case 6:
        if(!demo_poll.valid)return;
        size=demo_payload_status_packet(packet);
        break;
    case 8:
        size=demo_gps_packet(packet);
        break;
    case 9: {
        uint8_t identity[FI_SIZE];
        fi_payload(identity,boot,now);
        size=W_PAYLOAD+W_SIZE_IHU_FIRMWARE+2;
        cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_IHU_FIRMWARE,W_SIZE_IHU_FIRMWARE);
        memcpy(packet+W_PAYLOAD,identity,W_SIZE_IHU_FIRMWARE);
        ul_p16(packet+size-2,ul_crc(packet,size-2));
        break;
    }
    default: {
        unsigned offset=step-DEMO_FIRMWARE_START;
        unsigned index=offset/2;
        if(!(offset%2)){
            demo_poll.valid=false;
            if(cycle_ms-elapsed>BD_TX_TIMEOUT_MS+2*DEMO_PAYLOAD_TIMEOUT_MS)
                demo_poll_start(demo_firmware[index].node,demo_firmware[index].request);
            return;
        }
        if(!demo_poll.valid)return;
        size=demo_firmware_packet(packet,index);
        break;
    }
    }
    if(!demo_queue_packet(packet,size,now))demo_fail("UHF telemetry queue... FAILED");
}
static void demo_link_pump(uint32_t now){
    if(startup_demo.stage!=DEMO_ACTIVE)return;
    cf_expire(&demo_up,now);
    cf_expire(&fragments,now);
    if(fire_uplink.gps_waiting && !fire_uplink.gps_reading){
        if(now-fire_uplink.gps_since>=2000)fire_submit_gps(NULL);
        else if(!sensor_job.active && now-housekeeping.last<3500){
            fire_uplink.gps_reading=true;
            if(!request_sensor(SENSOR_FIRE_GPS,0,false))fire_submit_gps(NULL);
        }
    }
    now=now_ms();
    if(fire_uplink.active && !fire_uplink.gps_waiting && (!pending.active || (uint32_t)(now-pending.started)>=request_timeout_ms(pending.packet.type))){
        pending.active=false;
        output.active=false;
        fire_unavailable(0);
    }
    if(demo_poll.active && (!pending.active || now-pending.started>=DEMO_PAYLOAD_TIMEOUT_MS))
        demo_poll_stop();
    cdh_pump(now);
    bool due=startup_demo.heartbeat_enabled && (uint32_t)(now-startup_demo.last_heartbeat)>=BD_HEARTBEAT_MS;
    if(due)startup_demo.last_heartbeat=now; /* No catch-up burst. */
    if(!startup_demo.tx_pending && !output.active){
        if(demo_response_size){
            if(!demo_queue_packet(demo_response,demo_response_size,now))
                demo_fail("UHF reply queue... FAILED");
            demo_response_size=0;
        }else if(!demo_up.active && !fire_uplink.active && !demo_poll.active && !cdh.active){
            if(demo_schedule.enabled)demo_schedule_pump(now);
            else if(due){
                uint8_t p[W_PAYLOAD+W_SIZE_HEARTBEAT+2];
                size_t n=health_packet(p,false,boot,telemetry_sequence++,now,BD_HEARTBEAT_MS,
                    uplink_engine.accepted,uplink_engine.rejected,policy.mode,policy.configuration);
                if(!demo_queue_packet(p,n,now))demo_fail("UHF heartbeat queue... FAILED");
            }
        }
    }
    if(startup_demo.stage==DEMO_ACTIVE)pump_tx(now);
}
