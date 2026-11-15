#pragma once
#include "uhf_startup_link.h"

enum uhf_startup_stage { UHF_STARTUP_LOCAL, UHF_STARTUP_EPS, UHF_STARTUP_PROBE, UHF_STARTUP_WAIT, UHF_STARTUP_BEACON, UHF_STARTUP_ACTIVATE, UHF_STARTUP_ACTIVE, UHF_STARTUP_LISTEN, UHF_STARTUP_FAILED };
static struct {
    enum uhf_startup_stage stage;
    uint32_t since,radio_boot,last_send,last_rx,stop_at,last_log,last_heartbeat,tx_at,tx_id,last_up;
    bool heartbeat_enabled,antenna,probe_sent,stop_pending,usb,tx_pending;
    bool banner_shown;
    unsigned count,shown;
    struct {uint32_t at;const char *line;} events[24];
} uhf_startup;

enum {
    UHF_STARTUP_TELEMETRY_DEFAULT_ENABLED=false,
    UHF_STARTUP_TELEMETRY_DEFAULT_SET=W_UHF_TELEMETRY_SET_BASIC,
    UHF_STARTUP_LISTEN_DEFAULT_S=540,
    UHF_STARTUP_TELEMETRY_DEFAULT_S=60,
    UHF_STARTUP_TELEMETRY_MIN_S=5,
    UHF_STARTUP_PHASE_MAX_S=3600,
    UHF_STARTUP_PAYLOAD_TIMEOUT_MS=750,
};
static struct {
    bool enabled,report_pending;
    uint16_t listen_seconds,telemetry_seconds;
    uint32_t started;
    uint8_t packet_set;
    unsigned next_packet;
} uhf_startup_schedule;

static struct {
    bool ready;
    uint32_t cycle,sampled;
    gps_result result;
} uhf_startup_gps;

static void uhf_startup_gps_complete(const gps_result *gps,uint32_t sampled){
    if(!uhf_startup_schedule.enabled || uhf_startup_schedule.started!=uhf_startup_gps.cycle ||
       uhf_startup_schedule.next_packet!=8)return;
    uhf_startup_gps.result=*gps;
    uhf_startup_gps.sampled=sampled;
    uhf_startup_gps.ready=true;
}

static size_t uhf_startup_gps_packet(uint8_t *packet){
    const size_t size=W_PAYLOAD+W_SIZE_GPS_STATUS+2;
    _Static_assert(W_PAYLOAD+W_SIZE_GPS_STATUS+2<=BD_PACKET_MAX,"GPS packet exceeds RF link limit");
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_GPS_STATUS,W_SIZE_GPS_STATUS);
    ul_p32(packet+W_UPTIME_MS,uhf_startup_gps.sampled);
    uint8_t *p=packet+W_PAYLOAD;
    const gps_result *gps=&uhf_startup_gps.result;
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
} uhf_startup_poll;

static void uhf_startup_poll_stop(void){
    if(!uhf_startup_poll.active)return;
    target_index=uhf_startup_poll.target;
    peer=uhf_startup_poll.peer;
    pending.active=false;
    output.active=false;
    uhf_startup_poll.active=false;
}

static void uhf_startup_poll_start(uint8_t node,uint8_t request){
    if(pending.active || output.active)return;
    uhf_startup_poll.active=true;
    uhf_startup_poll.valid=false;
    uhf_startup_poll.target=target_index;
    uhf_startup_poll.peer=peer;
    uhf_startup_poll.request=request;
    target_index=node;
    peer=node==DR_COMMS_INDEX?uhf_startup.radio_boot:0;
    memset(&fragments,0,sizeof(fragments));
    submit(peer?request:UL_HELLO,NULL,0);
}

static void uhf_startup_poll_receive(const ul_packet *reply){
    bool hello=pending.packet.type==UL_HELLO;
    uint32_t previous=matched;
    receive(reply);
    if(pending.active)return;
    if(matched!=previous){
        if(hello){
            submit(uhf_startup_poll.request,NULL,0);
            if(pending.active)return;
        }else{
            memcpy(uhf_startup_poll.report,reply->payload,reply->size);
            uhf_startup_poll.valid=true;
        }
    }
    uhf_startup_poll_stop();
}

static size_t uhf_startup_payload_status_packet(uint8_t *packet){
    const size_t size=W_PAYLOAD+W_SIZE_PAYLOAD_STATUS+2;
    _Static_assert(W_PAYLOAD+W_SIZE_PAYLOAD_STATUS+2<=BD_PACKET_MAX,"Payload packet exceeds RF link limit");
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_PAYLOAD_STATUS,W_SIZE_PAYLOAD_STATUS);
    uint8_t *p=packet+W_PAYLOAD;
    const uint8_t *report=uhf_startup_poll.report;
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
} uhf_startup_firmware[]={
    {DR_COMMS_INDEX,UL_FIRMWARE_INFO,W_ID_COMMS_FIRMWARE,W_SIZE_COMMS_FIRMWARE},
    {DR_PAYLOAD_INDEX,UL_FIRMWARE_INFO,W_ID_PAYLOAD_FIRMWARE,W_SIZE_PAYLOAD_FIRMWARE},
    {DR_LTE_INDEX,UL_FIRMWARE_INFO,W_ID_LTE_CAN_FIRMWARE,W_SIZE_LTE_CAN_FIRMWARE},
    {DR_LTE_INDEX,CF_MODEM_FIRMWARE,W_ID_LTE_MODEM_FIRMWARE,W_SIZE_LTE_MODEM_FIRMWARE},
};
enum {UHF_STARTUP_FIRMWARE_START=10, UHF_STARTUP_FULL_STEPS=UHF_STARTUP_FIRMWARE_START+2*sizeof(uhf_startup_firmware)/sizeof(uhf_startup_firmware[0])};

static size_t uhf_startup_firmware_packet(uint8_t *packet,unsigned index){
    unsigned id=uhf_startup_firmware[index].id;
    size_t payload=uhf_startup_firmware[index].size;
    size_t size=W_PAYLOAD+payload+2;
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,id,payload);
    uint8_t *fields=packet+W_PAYLOAD;
    const uint8_t *identity=uhf_startup_poll.report;
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

static cf_reader uhf_startup_up;
static uint8_t uhf_startup_response[BD_PACKET_MAX];
static size_t uhf_startup_response_size;
static uint32_t uhf_startup_uplinks,uhf_startup_replies,uhf_startup_tx_ok,uhf_startup_drops;

static bool uhf_startup_store_response(const uint8_t *p,size_t n){
    if(uhf_startup_response_size || n>sizeof(uhf_startup_response))return false;
    memcpy(uhf_startup_response,p,n);
    uhf_startup_response_size=n;
    ++uhf_startup_replies;
    return true;
}

static bool uhf_startup_command_reply(const uint8_t *p,size_t n,void *unused){
    const uint8_t *request=unused;
    bool status_request=ul_u16(request+8)==W_ID_REQUEST_STATUS;
    if(status_request && p[W_KIND]==W_KINDS_TELEMETRY && ul_u16(p+8)==W_ID_SYSTEM_STATUS){
        if(uhf_startup_response_size)return false;
        uhf_startup_response_size=status_packet(uhf_startup_response,request);++uhf_startup_replies;
        return true;
    }
    if(n!=43 || p[W_KIND]!=W_KINDS_RESPONSE)return false;
    unsigned stage=p[W_PAYLOAD+W_COMMAND_RESPONSE_STAGE];
    if(stage==W_STAGE_ACCEPTED || (status_request && stage==W_STAGE_COMPLETED))return true;
    return uhf_startup_store_response(p,n);
}
static void uhf_startup_send_faults(const ul_packet *request) {
    const size_t size = W_PAYLOAD + W_SIZE_IHU_FAULTS + 2;
    _Static_assert(W_PAYLOAD + W_SIZE_IHU_FAULTS + 2 <= BD_PACKET_MAX,
                   "IHU fault history exceeds RF link limit");
    const unsigned stride = W_IHU_FAULTS_FAULT2_CODE - W_IHU_FAULTS_FAULT1_CODE;
    _Static_assert(W_SIZE_IHU_FAULTS == W_IHU_FAULTS_FAULT1_CODE +
                   IHU_FAULT_CAPACITY * (1 + sizeof(uint32_t)),
                   "IHU fault history layout does not match the ring");
    uint8_t *packet = uhf_startup_response;
    cdh_header(packet, size, request, W_KINDS_TELEMETRY, W_ID_IHU_FAULTS, W_SIZE_IHU_FAULTS);
    uint8_t *fields = packet + W_PAYLOAD;
    unsigned count = fault_count < IHU_FAULT_CAPACITY ? fault_count : IHU_FAULT_CAPACITY;
    fields[W_IHU_FAULTS_PAYLOAD_VERSION] = 1;
    fields[W_IHU_FAULTS_COUNT] = count;
    ul_p32(fields + W_IHU_FAULTS_TOTAL, fault_count);
    for (unsigned i = 0; i < count; ++i) {
        unsigned slot = (fault_count - count + i) % IHU_FAULT_CAPACITY;
        fields[W_IHU_FAULTS_FAULT1_CODE + i * stride] = faults[slot].code;
        ul_p32(fields + W_IHU_FAULTS_FAULT1_UPTIME_MS + i * stride, faults[slot].at);
    }
    ul_p16(packet + size - 2, ul_crc(packet, size - 2));
    uhf_startup_response_size = size;
    ++uhf_startup_replies;
}
static bool uhf_startup_ack_setting(const ul_packet *request,uint32_t value){
    ul_packet reply={.version=1,.type=UP_RESULT,.sender=boot,.origin=request->sender,
        .request=request->request,.size=43};
    cdh_header(reply.payload,43,request,W_KINDS_RESPONSE,W_ID_COMMAND_RESPONSE,11);
    ul_p16(reply.payload+30,ul_u16(request->payload+W_MESSAGE_ID));
    reply.payload[32]=W_STAGE_COMPLETED;
    ul_p32(reply.payload+37,value);
    return cdh_send(&reply);
}
static size_t uhf_startup_schedule_packet(uint8_t *packet,uint32_t now){
    const size_t size=W_PAYLOAD+W_SIZE_UHF_SCHEDULE_STATUS+2;
    cdh_header(packet,size,NULL,W_KINDS_TELEMETRY,W_ID_UHF_SCHEDULE_STATUS,W_SIZE_UHF_SCHEDULE_STATUS);
    ul_p32(packet+W_UPTIME_MS,now);
    uint8_t *fields=packet+W_PAYLOAD;
    fields[W_UHF_SCHEDULE_STATUS_ENABLED]=uhf_startup_schedule.enabled;
    fields[W_UHF_SCHEDULE_STATUS_TELEMETRY_SET]=uhf_startup_schedule.packet_set;
    ul_p16(fields+W_UHF_SCHEDULE_STATUS_LISTEN_SECONDS,uhf_startup_schedule.listen_seconds);
    ul_p16(fields+W_UHF_SCHEDULE_STATUS_TELEMETRY_SECONDS,uhf_startup_schedule.telemetry_seconds);
    uint32_t cycle=(uhf_startup_schedule.listen_seconds+uhf_startup_schedule.telemetry_seconds)*1000u;
    ul_p32(fields+W_UHF_SCHEDULE_STATUS_CYCLE_OFFSET_MS,
           uhf_startup_schedule.enabled?(now-uhf_startup_schedule.started)%cycle:0);
    ul_p16(packet+size-2,ul_crc(packet,size-2));
    return size;
}

static void uhf_startup_restart_schedule(uint32_t now){
    uhf_startup_schedule.started=now;
    uhf_startup_schedule.next_packet=0;
    uhf_startup_poll.valid=false;
    uhf_startup_gps.ready=false;
}
static void uhf_startup_set_output(const ul_packet *request,uint32_t now){
    const uint8_t *wire=request->payload;
    uint8_t enabled=wire[W_PAYLOAD];
    if(enabled>1){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(ul_u16(wire+W_MESSAGE_ID)==W_ID_SET_HEARTBEAT){
        if(enabled && uhf_startup_schedule.enabled){
            cdh_error(request,W_STAGE_REJECTED,W_REASON_MODE_NOT_ALLOWED);
            return;
        }
        if(uhf_startup_ack_setting(request,enabled)){
            if(enabled && !uhf_startup.heartbeat_enabled)uhf_startup.last_heartbeat=now;
            uhf_startup.heartbeat_enabled=enabled;
        }
        return;
    }
    if(uhf_startup_ack_setting(request,enabled)){
        if(enabled && !uhf_startup_schedule.enabled)uhf_startup_restart_schedule(now);
        uhf_startup_schedule.enabled=enabled;
        uhf_startup_schedule.report_pending=true;
        if(enabled)uhf_startup.heartbeat_enabled=false;
    }
}
static void uhf_startup_set_schedule(const ul_packet *request,uint32_t now){
    const uint8_t *args=request->payload+W_PAYLOAD;
    uint16_t listen=ul_u16(args),telem=ul_u16(args+2);
    if(!listen || listen>UHF_STARTUP_PHASE_MAX_S || telem<UHF_STARTUP_TELEMETRY_MIN_S || telem>UHF_STARTUP_PHASE_MAX_S){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(uhf_startup_ack_setting(request,ul_u32(args)) &&
       (listen!=uhf_startup_schedule.listen_seconds || telem!=uhf_startup_schedule.telemetry_seconds)){
        uhf_startup_schedule.listen_seconds=listen;
        uhf_startup_schedule.telemetry_seconds=telem;
        uhf_startup_schedule.report_pending=true;
        uhf_startup_restart_schedule(now);
    }
}
static void uhf_startup_set_packet_set(const ul_packet *request,uint32_t now){
    uint8_t set=request->payload[W_PAYLOAD];
    if(set!=W_UHF_TELEMETRY_SET_BASIC && set!=W_UHF_TELEMETRY_SET_FULL){
        cdh_error(request,W_STAGE_REJECTED,W_REASON_INVALID_PARAMETER);
        return;
    }
    if(uhf_startup_ack_setting(request,set) && set!=uhf_startup_schedule.packet_set){
        uhf_startup_schedule.packet_set=set;
        uhf_startup_schedule.report_pending=true;
        uhf_startup_restart_schedule(now);
    }
}
static void uhf_startup_uplink(const cf_frame *f,uint32_t now){
    static ul_packet p;
    if(!cf_feed(&uhf_startup_up,f,BD_UP_ID,now))return;
    if(!bd_packet(&uhf_startup_up,&p,uhf_startup.radio_boot,boot) || p.request<=uhf_startup.last_up)return;
    uhf_startup.last_up=p.request;++uhf_startup_uplinks;
    if(p.size<32 || uhf_startup_response_size || fire_uplink.active || cdh.active){++uhf_startup_drops;return;}
    uhf_startup_poll_stop();
    unsigned id=ul_u16(p.payload+W_MESSAGE_ID);
    if((id==W_ID_SET_HEARTBEAT || id==W_ID_SET_UHF_TELEMETRY) && up_native_args(p.payload,p.size,1)){
        uhf_startup_set_output(&p,now);return;
    }
    if(id==W_ID_SET_UHF_TELEMETRY_SCHEDULE && up_native_args(p.payload,p.size,4)){
        uhf_startup_set_schedule(&p,now);return;
    }
    if(id==W_ID_SET_UHF_TELEMETRY_SET && up_native_args(p.payload,p.size,1)){
        uhf_startup_set_packet_set(&p,now);return;
    }
    if (id == W_ID_REQUEST_IHU_FAULTS && up_native_args(p.payload, p.size, 0)) {
        uhf_startup_send_faults(&p);
        return;
    }
    if(up_native_cdh(p.payload,p.size)){cdh_receive(&p);return;}
    if(up_native_fire(p.payload,p.size)){
        if(output.active || pending.active){cdh_error(&p,W_STAGE_REJECTED,W_REASON_BUSY);return;}
        uplink_start_fire(&p);
        return;
    }
    if(!up_native_ping(p.payload,p.size) && !up_native_status(p.payload,p.size)){++uhf_startup_drops;return;}
    ember_command(&uplink_engine,p.payload,p.size,now,uhf_startup_command_reply,p.payload);
    if(id==W_ID_REQUEST_STATUS && uhf_startup_response_size)uhf_startup_schedule.report_pending=true;
}
static bool uhf_startup_queue_packet(const uint8_t *p,size_t n,uint32_t now){
    static ul_packet packet;
    if(!n || n>BD_PACKET_MAX || uhf_startup.tx_id==UINT32_MAX)return false;
    packet=(ul_packet){.version=1,.type=BD_PACKET,.sender=boot,.origin=uhf_startup.radio_boot,
        .request=++uhf_startup.tx_id,.size=(uint16_t)n};
    memcpy(packet.payload,p,n);
    if(!queue(&packet))return false;
    output.route=BD_DOWN_ID;uhf_startup.tx_at=now;uhf_startup.tx_pending=true;
    return true;
}
static void uhf_startup_history(bool reply) {
    for(unsigned i=0;i<uhf_startup.count;i++)
        ihu_printf(reply,"STARTUP t_ms=%" PRIu32 " %s\n",uhf_startup.events[i].at,uhf_startup.events[i].line);
}
static void uhf_startup_event(const char *line) {
    uint32_t now=now_ms();
    if(uhf_startup.count<sizeof(uhf_startup.events)/sizeof(uhf_startup.events[0])){
        unsigned i=uhf_startup.count++;
        uhf_startup.events[i].at=now;uhf_startup.events[i].line=line;
    }
}
static void uhf_startup_stage(enum uhf_startup_stage stage,uint32_t now) {
    uhf_startup.stage=stage;uhf_startup.since=now;
}
static void uhf_startup_fail(const char *reason) {
    if(uhf_startup.stage==UHF_STARTUP_FAILED)return;
    uint32_t now=now_ms();
    uhf_startup_event(reason);
    uhf_startup_event("SAFE: outputs off; no automatic retry");
    policy.mode=IP_SAFE;policy.reason=reason;policy.outputs=0;
    output.active=false;uhf_startup_response_size=0;uhf_startup.tx_pending=false;
    pending.active=false;cdh.active=false;uhf_startup_schedule.enabled=false;
    if(fire_uplink.active)fire_restore();
    uhf_startup_poll_stop();
    uhf_startup.stop_pending=uhf_startup.radio_boot!=0;uhf_startup.stop_at=now;
    uhf_startup_stage(UHF_STARTUP_FAILED,now);
}
static bool uhf_startup_send(unsigned id,uint32_t radio_boot) {
    cf_frame f=bd_frame(id,boot,radio_boot);
    return ihu_can_send(&can,&f);
}
static void uhf_startup_receive(const cf_frame *f,uint32_t now) {
    if(uhf_startup.stage==UHF_STARTUP_ACTIVE){
        if(f->id==BD_UP_ID){uhf_startup_uplink(f,now);return;}
        if((fire_uplink.active || uhf_startup_poll.active) && pending.active && f->id==RX_ID){
            ul_packet reply;
            if(cf_feed(&fragments,f,RX_ID,now) && up_envelope(&fragments,&reply) &&
               reply.origin==boot && reply.request==pending.packet.request){
                if(uhf_startup_poll.active)uhf_startup_poll_receive(&reply);
                else receive(&reply);
            }
            return;
        }
        if((f->id==BD_TX_OK || f->id==BD_TX_FAILED) && uhf_startup.tx_pending &&
           bd_matches(f,uhf_startup.tx_id,uhf_startup.radio_boot)){
            if(f->id==BD_TX_FAILED)uhf_startup_fail("UHF packet TX... FAILED");
            else {uhf_startup.tx_pending=false;uhf_startup.last_rx=now;++uhf_startup_tx_ok;
                dr_seen(&devices[DR_COMMS_INDEX],now,uhf_startup.radio_boot);}
            return;
        }
    }
    if(f->size!=8 || ul_u32(f->data)!=boot)return;
    uint32_t sender=ul_u32(f->data+4);
    if(f->id==BD_READY && uhf_startup.stage==UHF_STARTUP_PROBE && uhf_startup.probe_sent &&
       sender && (uint32_t)(now-uhf_startup.since)<12000){
        uhf_startup.radio_boot=sender;
        uhf_startup_event("Checking UHF transceiver... PASSED (CAN startup handshake, TX off)");
        policy.mode=IP_STARTUP;policy.reason="UHF_STARTUP_RELEASE_TIMERS";
        uhf_startup_event("SAFE -> STARTUP");
        uhf_startup_event("Release switches A and B released [SIMULATED]");
        uhf_startup_event("Antenna release timer 10 s; radio silence timer 15 s [GROUND_TEST]");
        uhf_startup_stage(UHF_STARTUP_WAIT,now);
    }
    if(!sender || sender!=uhf_startup.radio_boot)return;
    if(f->id==BD_FAILED)uhf_startup_fail("UHF transceiver... FAILED (stopped or radio fault)");
    if(f->id==BD_RX && uhf_startup.stage==UHF_STARTUP_BEACON &&
       (uint32_t)(now-uhf_startup.since)<BD_CW_LIMIT_MS+2000){
        uhf_startup_event("CW beacon complete; transmitter muted");
        uhf_startup_event("Checking UHF receive readiness... PASSED");
#if IHU_BOOT_RX_ONLY
        policy.mode=IP_NOMINAL;policy.reason="UHF_STARTUP_RX_ONLY";policy.outputs=0;
        uhf_startup_event("COMMISSIONING -> NOMINAL: UHF LISTEN ONLY");
        uhf_startup_stage(UHF_STARTUP_LISTEN,now);
#else
        uhf_startup_event("Enabling UHF LINK_ACTIVE...");
        uhf_startup_stage(UHF_STARTUP_ACTIVATE,now);uhf_startup.last_send=now-200;
#endif
        uhf_startup.last_rx=now;
    }
    if(f->id==BD_LINKED && uhf_startup.stage==UHF_STARTUP_ACTIVATE){
        policy.mode=IP_NOMINAL;policy.reason="UHF_STARTUP_LINK_ACTIVE";policy.outputs=0;
        uhf_startup_event("COMMISSIONING -> NOMINAL: UHF LINK_ACTIVE");
        uhf_startup_stage(UHF_STARTUP_ACTIVE,now);
        uhf_startup.last_heartbeat=now;
    }
    if((f->id==BD_LINKED && uhf_startup.stage==UHF_STARTUP_ACTIVE) ||
       (f->id==BD_RX && uhf_startup.stage==UHF_STARTUP_LISTEN)){
        uhf_startup.last_rx=now;
        dr_seen(&devices[DR_COMMS_INDEX],now,uhf_startup.radio_boot);
    }
}
static void boot_banner(void) {
    ihu_printf(false,
        "\n"
        "  =============== EMBER IHU | firmware %s ===============\n"
        "  Spacecraft housekeeping, telemetry, and commanding\n"
        "  Profile       GROUND_TEST / UHF\n"
        "  Startup       SAFE -> STARTUP -> COMMISSIONING -> NOMINAL\n"
        "  Radio         CW boot beacon, then %s after successful startup\n"
        "  Defaults      All output flags off | UHF heartbeat off\n"
        "  UHF schedule  %s | %s | %u s listen / %u s telemetry\n"
        "  Console       help | startup | status | radio | outputs\n"
        "\n",
        FW_VERSION, IHU_BOOT_RX_ONLY ? "RX_ONLY" : "LINK_ACTIVE",
        UHF_STARTUP_TELEMETRY_DEFAULT_ENABLED ? "ON" : "OFF",
        UHF_STARTUP_TELEMETRY_DEFAULT_SET==W_UHF_TELEMETRY_SET_BASIC ? "BASIC" : "FULL",
        (unsigned)UHF_STARTUP_LISTEN_DEFAULT_S, (unsigned)UHF_STARTUP_TELEMETRY_DEFAULT_S);
}
static void uhf_startup_step(void) {
    uint32_t now=now_ms();
    bool live=stdio_usb_connected();
    if(live && !uhf_startup.usb){
        uhf_startup.banner_shown=false;
        uhf_startup.shown=0;
    }
    if(live && (uint32_t)(now-uhf_startup.last_log)>=20){
        if(!uhf_startup.banner_shown){
            boot_banner();
            uhf_startup.banner_shown=true;
            uhf_startup.last_log=now;
        }else if(uhf_startup.shown<uhf_startup.count){
            unsigned i=uhf_startup.shown++;
            uhf_startup.last_log=now;
            ihu_printf(false,"STARTUP t_ms=%" PRIu32 " %s\n",uhf_startup.events[i].at,uhf_startup.events[i].line);
        }
    }
    uhf_startup.usb=live;
    ihu_can_poll_tx(&can,now);
    bool local_ok=can.ready && !(ihu_can_register(0x0e)&0xe0) && !ihu_can_register(0x2d);
    if(uhf_startup.stage!=UHF_STARTUP_FAILED && !local_ok)uhf_startup_fail("Checking local CAN controller... FAILED");
    if(uhf_startup.stage!=UHF_STARTUP_FAILED && uhf_startup.stage!=UHF_STARTUP_LOCAL &&
       ((housekeeping.attempted && !housekeeping.valid) ||
        (housekeeping.valid && (uint32_t)(now-housekeeping.sampled)>6500)))
        uhf_startup_fail("Checking EPS telemetry... FAILED (invalid or stale)");
    uint32_t elapsed=now-uhf_startup.since;
    switch(uhf_startup.stage){
    case UHF_STARTUP_LOCAL:
        uhf_startup_event("Checking local CAN controller... PASSED");
        uhf_startup_event("Checking EPS telemetry...");
        uhf_startup_stage(UHF_STARTUP_EPS,now);
        break;
    case UHF_STARTUP_EPS:
        if(housekeeping.valid){
            uhf_startup_event("Checking EPS telemetry... PASSED (valid register read)");
            uhf_startup_event("Checking UHF transceiver...");
            uhf_startup_stage(UHF_STARTUP_PROBE,now);
        }else if(elapsed>=7000)uhf_startup_fail("Checking EPS telemetry... FAILED (timeout)");
        break;
    case UHF_STARTUP_PROBE:
        if(elapsed>=12000)uhf_startup_fail("Checking UHF transceiver... FAILED (no startup READY)");
        else if(!uhf_startup.probe_sent || (uint32_t)(now-uhf_startup.last_send)>=500){
            if(!can.pending && uhf_startup_send(BD_PROBE,0)){
                uhf_startup.probe_sent=true;uhf_startup.last_send=now;
            }
        }
        break;
    case UHF_STARTUP_WAIT:
        if(elapsed>=BD_ANTENNA_MS && !uhf_startup.antenna){
            uhf_startup.antenna=true;
            uhf_startup_event("Antenna release timer expired - deploying antenna [SIMULATED]");
        }
        if(elapsed>=BD_SILENCE_MS){
            uhf_startup_event("Radio silence timer expired [GROUND_TEST]");
            policy.mode=IP_COMMISSIONING;policy.reason="UHF_STARTUP_BEACON_AND_RX";
            uhf_startup_event("STARTUP -> COMMISSIONING");
            uhf_startup_event("Checking antenna deployment result... PASSED [SIMULATED]");
            uhf_startup_event("Requesting initial CW beacon: KI5YNG - EMBER BOOT");
            /* Mark admission before send. No retry after a possibly delivered request. */
            uhf_startup_stage(UHF_STARTUP_BEACON,now);uhf_startup.last_send=now;
            if(!uhf_startup_send(BD_FIRE,uhf_startup.radio_boot))uhf_startup_fail("CW request... FAILED (submission)");
        }
        break;
    case UHF_STARTUP_BEACON:
        if(elapsed>=BD_CW_LIMIT_MS+2000)uhf_startup_fail("CW/RX completion... FAILED (timeout; outcome unknown)");
        else if((uint32_t)(now-uhf_startup.last_send)>=BD_KEEP_PERIOD_MS && !can.pending &&
                uhf_startup_send(BD_KEEP,uhf_startup.radio_boot))uhf_startup.last_send=now;
        break;
    case UHF_STARTUP_ACTIVATE:
        if(elapsed>=2000)uhf_startup_fail("UHF LINK_ACTIVE... FAILED (no acknowledgement)");
        else if((uint32_t)(now-uhf_startup.last_send)>=200 && !can.pending &&
                uhf_startup_send(BD_LINK,uhf_startup.radio_boot))uhf_startup.last_send=now;
        break;
    case UHF_STARTUP_ACTIVE:
        if((uint32_t)(now-uhf_startup.last_rx)>=BD_RX_TIMEOUT_MS)
            uhf_startup_fail("UHF LINK_ACTIVE... FAILED (status timeout)");
        else if(uhf_startup.tx_pending && (uint32_t)(now-uhf_startup.tx_at)>=BD_TX_TIMEOUT_MS)
            uhf_startup_fail("UHF packet TX... FAILED (outcome unknown; no retry)");
        else if((uint32_t)(now-uhf_startup.last_send)>=BD_KEEP_PERIOD_MS && !can.pending &&
                uhf_startup_send(BD_KEEP,uhf_startup.radio_boot))uhf_startup.last_send=now;
        break;
    case UHF_STARTUP_LISTEN:
        if((uint32_t)(now-uhf_startup.last_rx)>=BD_RX_TIMEOUT_MS)
            uhf_startup_fail("UHF receive readiness... FAILED (status timeout)");
        break;
    case UHF_STARTUP_FAILED:
        if(uhf_startup.stop_pending &&
           ((uint32_t)(now-uhf_startup.stop_at)>=1000 ||
            (local_ok && !can.pending && uhf_startup_send(BD_STOP,uhf_startup.radio_boot))))
            uhf_startup.stop_pending=false;
        break;
    }
    if(uhf_startup.stage!=UHF_STARTUP_FAILED && !sensor_job.active && (uint32_t)(now-housekeeping.last)>=5000){
        housekeeping.last=now;
        (void)request_sensor(SENSOR_HEALTH,0,false);
    }
}
static void uhf_startup_schedule_pump(uint32_t now){
    if(!uhf_startup_schedule.enabled)return;
    uint32_t listen_ms=(uint32_t)uhf_startup_schedule.listen_seconds*1000;
    uint32_t cycle_ms=listen_ms+(uint32_t)uhf_startup_schedule.telemetry_seconds*1000;
    uint32_t elapsed=now-uhf_startup_schedule.started;
    if(elapsed>=cycle_ms){
        elapsed%=cycle_ms;
        uhf_startup_restart_schedule(now-elapsed);
    }
    /* Leave time for the admitted burst to finish before the listen phase. */
    unsigned count=uhf_startup_schedule.packet_set==W_UHF_TELEMETRY_SET_FULL?UHF_STARTUP_FULL_STEPS+1:3;
    if(elapsed<listen_ms || cycle_ms-elapsed<=BD_TX_TIMEOUT_MS || uhf_startup_schedule.next_packet>=count)return;
    if(uhf_startup_schedule.next_packet==7){
        if(cycle_ms-elapsed<=BD_TX_TIMEOUT_MS+2500 || sensor_job.active ||
           now-housekeeping.last>=3500)return;
        uhf_startup_gps.cycle=uhf_startup_schedule.started;
        ++uhf_startup_schedule.next_packet;
        if(!request_sensor(SENSOR_GPS_TELEMETRY,0,false))--uhf_startup_schedule.next_packet;
        return;
    }
    if(uhf_startup_schedule.next_packet==8 && !uhf_startup_gps.ready)return;
    _Static_assert(W_PAYLOAD+W_SIZE_POWER_STATUS+2<=BD_PACKET_MAX,"EPS packet exceeds RF link limit");
    _Static_assert(W_PAYLOAD+W_SIZE_DEVICE_STATUS+2<=BD_PACKET_MAX,"Device packet exceeds RF link limit");
    uint8_t packet[BD_PACKET_MAX];
    size_t size;
    unsigned step=uhf_startup_schedule.next_packet++;
    if(step==count-1){
        size=uhf_startup_schedule_packet(packet,now);
        if(!uhf_startup_queue_packet(packet,size,now))uhf_startup_fail("UHF schedule report queue... FAILED");
        return;
    }
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
        if(cycle_ms-elapsed>BD_TX_TIMEOUT_MS+2*UHF_STARTUP_PAYLOAD_TIMEOUT_MS)
            uhf_startup_poll_start(DR_PAYLOAD_INDEX,PL_STATUS);
        return;
    case 6:
        if(!uhf_startup_poll.valid)return;
        size=uhf_startup_payload_status_packet(packet);
        break;
    case 8:
        size=uhf_startup_gps_packet(packet);
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
        unsigned offset=step-UHF_STARTUP_FIRMWARE_START;
        unsigned index=offset/2;
        if(!(offset%2)){
            uhf_startup_poll.valid=false;
            if(cycle_ms-elapsed>BD_TX_TIMEOUT_MS+2*UHF_STARTUP_PAYLOAD_TIMEOUT_MS)
                uhf_startup_poll_start(uhf_startup_firmware[index].node,uhf_startup_firmware[index].request);
            return;
        }
        if(!uhf_startup_poll.valid)return;
        size=uhf_startup_firmware_packet(packet,index);
        break;
    }
    }
    if(!uhf_startup_queue_packet(packet,size,now))uhf_startup_fail("UHF telemetry queue... FAILED");
}
static void uhf_startup_link_pump(uint32_t now){
    if(uhf_startup.stage!=UHF_STARTUP_ACTIVE)return;
    cf_expire(&uhf_startup_up,now);
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
    if(uhf_startup_poll.active && (!pending.active || now-pending.started>=UHF_STARTUP_PAYLOAD_TIMEOUT_MS))
        uhf_startup_poll_stop();
    cdh_pump(now);
    bool due=uhf_startup.heartbeat_enabled && (uint32_t)(now-uhf_startup.last_heartbeat)>=BD_HEARTBEAT_MS;
    if(due)uhf_startup.last_heartbeat=now; /* No catch-up burst. */
    if(!uhf_startup.tx_pending && !output.active){
        if(uhf_startup_response_size){
            if(!uhf_startup_queue_packet(uhf_startup_response,uhf_startup_response_size,now))
                uhf_startup_fail("UHF reply queue... FAILED");
            uhf_startup_response_size=0;
        }else if(!uhf_startup_up.active && !fire_uplink.active && !uhf_startup_poll.active && !cdh.active){
            if(uhf_startup_schedule.report_pending){
                uint8_t packet[W_PAYLOAD+W_SIZE_UHF_SCHEDULE_STATUS+2];
                size_t size=uhf_startup_schedule_packet(packet,now);
                uhf_startup_schedule.report_pending=false;
                if(!uhf_startup_queue_packet(packet,size,now))uhf_startup_fail("UHF schedule report queue... FAILED");
            }else if(uhf_startup_schedule.enabled)uhf_startup_schedule_pump(now);
            else if(due){
                uint8_t p[W_PAYLOAD+W_SIZE_HEARTBEAT+2];
                size_t n=health_packet(p,false,boot,telemetry_sequence++,now,BD_HEARTBEAT_MS,
                    uplink_engine.accepted,uplink_engine.rejected,policy.mode,policy.configuration);
                if(!uhf_startup_queue_packet(p,n,now))uhf_startup_fail("UHF heartbeat queue... FAILED");
            }
        }
    }
    if(uhf_startup.stage==UHF_STARTUP_ACTIVE)pump_tx(now);
}
