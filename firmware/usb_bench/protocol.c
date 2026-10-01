#include "protocol.h"
#include <string.h>
_Static_assert(W_MAX_PACKET==240 && W_PAYLOAD==30, "Review framing for a changed wire profile");
_Static_assert(W_SIZE_COMMAND_RESPONSE<=18 && W_SIZE_COMM_STATUS<=18 &&
               W_SIZE_SYSTEM_STATUS<=18 && W_SIZE_HEARTBEAT<=18, "Increase cached report capacity");

static uint16_t u16(const uint8_t *p) { return (uint16_t)((p[0] << 8) | p[1]); }
static uint32_t u32(const uint8_t *p) { return ((uint32_t)u16(p) << 16) | u16(p+2); }
static void p16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)(v>>8); p[1]=(uint8_t)v; }
static void p32(uint8_t *p, uint32_t v) { p16(p,(uint16_t)(v>>16)); p16(p+2,(uint16_t)v); }
uint16_t ember_crc(const uint8_t *p, size_t n) {
    uint16_t crc=0xffff;
    for (size_t i=0;i<n;i++) {
        crc ^= (uint16_t)p[i]<<8;
        for (unsigned j=0;j<8;j++) crc=(uint16_t)((crc&0x8000)?(crc<<1)^0x1021:crc<<1);
    }
    return crc;
}
void ember_init(ember_state *s, uint32_t boot) {
    memset(s,0,sizeof(*s)); s->boot=boot?boot:1; s->period=W_PERIOD_DEFAULT;
}
static void emit(ember_state *s, const ember_report *r, uint32_t epoch, uint32_t transaction,
                 uint32_t uptime, ember_send_fn send, void *context) {
    uint8_t packet[W_MAX_PACKET]={0}; size_t n=W_PAYLOAD+r->size+2;
    p16(packet,W_TM_IDENTITY); p16(packet+2,(uint16_t)(0xc000|s->sequence));
    s->sequence=(uint16_t)((s->sequence+1)&0x3fff);
    p16(packet+4,(uint16_t)(n-7)); packet[W_SCHEMA_VERSION]=W_VERSION;
    packet[W_KIND]=r->kind; p16(packet+W_MESSAGE_ID,r->id);
    packet[W_SOURCE]=W_ENDPOINTS_IHU; packet[W_TARGET]=W_ENDPOINTS_GROUND;
    p32(packet+W_TRANSACTION_EPOCH,epoch); p32(packet+W_TRANSACTION_ID,transaction);
    p32(packet+W_SOURCE_BOOT_ID,s->boot); p32(packet+W_UPTIME_MS,uptime);
    p16(packet+W_PAYLOAD_LENGTH,r->size); memcpy(packet+W_PAYLOAD,r->payload,r->size);
    p16(packet+n-2,ember_crc(packet,n-2));
    if (send(packet,n,context)) s->tx++; else s->dropped++;
}
static ember_report response(uint16_t command, uint8_t stage, uint16_t reason,
                             uint16_t parameter, uint32_t value) {
    ember_report r={.kind=W_KINDS_RESPONSE,.id=W_ID_COMMAND_RESPONSE,.size=W_SIZE_COMMAND_RESPONSE};
    p16(r.payload+W_COMMAND_RESPONSE_COMMAND_ID,command);
    r.payload[W_COMMAND_RESPONSE_STAGE]=stage; p16(r.payload+W_COMMAND_RESPONSE_REASON,reason);
    p16(r.payload+W_COMMAND_RESPONSE_PARAMETER_ID,parameter); p32(r.payload+W_COMMAND_RESPONSE_VALUE,value);
    return r;
}
static ember_report telemetry(ember_state *s, uint16_t id) {
    ember_report r={.kind=W_KINDS_TELEMETRY,.id=id};
    if (id==W_ID_COMM_STATUS) {
        r.size=W_SIZE_COMM_STATUS;
        p32(r.payload+W_COMM_STATUS_RX_PACKETS,s->rx); p32(r.payload+W_COMM_STATUS_TX_PACKETS,s->tx);
        p32(r.payload+W_COMM_STATUS_CRC_ERRORS,s->crc_errors); p32(r.payload+W_COMM_STATUS_DROPPED_PACKETS,s->dropped);
        p16(r.payload+W_COMM_STATUS_RSSI_DBM,0x8000);
    } else if (id==W_ID_HEARTBEAT) {
        r.size=W_SIZE_HEARTBEAT;
        r.payload[W_HEARTBEAT_MODE]=W_MODE_SAFE;
        r.payload[W_HEARTBEAT_CONFIGURATION]=W_CONFIGURATION_GROUND_TEST;
        p32(r.payload+W_HEARTBEAT_TELEMETRY_PERIOD_MS,s->period);
    } else {
        r.size=W_SIZE_SYSTEM_STATUS;
        r.payload[W_SYSTEM_STATUS_MODE]=W_MODE_SAFE;
        r.payload[W_SYSTEM_STATUS_CONFIGURATION]=W_CONFIGURATION_GROUND_TEST;
        p32(r.payload+W_SYSTEM_STATUS_TELEMETRY_PERIOD_MS,s->period);
        p32(r.payload+W_SYSTEM_STATUS_ACCEPTED_COMMANDS,s->accepted);
        p32(r.payload+W_SYSTEM_STATUS_REJECTED_COMMANDS,s->rejected);
    }
    return r;
}
void ember_periodic(ember_state *s, uint32_t uptime, ember_send_fn send, void *context) {
    const uint16_t ids[]={W_ID_HEARTBEAT,W_ID_SYSTEM_STATUS,W_ID_COMM_STATUS};
    for (unsigned i=0;i<3;i++) { ember_report r=telemetry(s,ids[i]); emit(s,&r,0,0,uptime,send,context); }
}
void ember_command(ember_state *s, const uint8_t *p, size_t n, uint32_t uptime,
                   ember_send_fn send, void *context) {
    if (n<W_PAYLOAD+2 || n>W_MAX_PACKET || u16(p)!=W_TC_IDENTITY ||
        (u16(p+2)>>14)!=3 || (size_t)u16(p+4)+7!=n || p[W_SCHEMA_VERSION]!=W_VERSION ||
        p[W_KIND]!=W_KINDS_COMMAND || p[W_SOURCE]!=W_ENDPOINTS_GROUND || p[W_TARGET]!=W_ENDPOINTS_IHU ||
        !u32(p+W_TRANSACTION_EPOCH) || !u32(p+W_TRANSACTION_ID) || !u32(p+W_SOURCE_BOOT_ID) ||
        (size_t)u16(p+W_PAYLOAD_LENGTH)+W_PAYLOAD+2!=n) { s->dropped++; return; }
    if (ember_crc(p,n-2)!=u16(p+n-2)) { s->crc_errors++; s->dropped++; return; }
    uint16_t id=u16(p+W_MESSAGE_ID), size=u16(p+W_PAYLOAD_LENGTH);
    uint32_t epoch=u32(p+W_TRANSACTION_EPOCH), transaction=u32(p+W_TRANSACTION_ID);
    int expected=-1;
    if (id==W_ID_PING) expected=W_SIZE_PING;
    if (id==W_ID_REQUEST_STATUS) expected=W_SIZE_REQUEST_STATUS;
    if (id==W_ID_REQUEST_TELEMETRY) expected=W_SIZE_REQUEST_TELEMETRY;
    if (id==W_ID_SET_PARAMETER) expected=W_SIZE_SET_PARAMETER;
    if (expected>=0 && size!=(unsigned)expected) { s->dropped++; return; }
    s->rx++;
    for (unsigned i=0;i<64;i++) {
        ember_cache_entry *c=&s->cache[i];
        if (!c->valid || c->epoch!=epoch || c->transaction!=transaction) continue;
        if (c->command!=id || c->size!=size || memcmp(c->arguments,p+W_PAYLOAD,size)) {
            s->rejected++; ember_report r=response(id,W_STAGE_REJECTED,W_REASON_TRANSACTION_CONFLICT,0,0);
            emit(s,&r,epoch,transaction,uptime,send,context);
        } else for (unsigned j=0;j<c->count;j++) emit(s,&c->reports[j],epoch,transaction,uptime,send,context);
        return;
    }
    ember_cache_entry *c=&s->cache[s->next_cache]; s->next_cache=(s->next_cache+1)%64;
    memset(c,0,sizeof(*c)); c->valid=true; c->epoch=epoch; c->transaction=transaction;
    c->command=id; c->size=size; memcpy(c->arguments,p+W_PAYLOAD,size);
    uint16_t reason=W_REASON_NONE;
    const uint8_t *args=p+W_PAYLOAD;
    uint32_t value=0;
    if (expected<0) reason=W_REASON_UNKNOWN_COMMAND;
    else if (id==W_ID_REQUEST_TELEMETRY && args[0]!=W_DATA_GROUP_SYSTEM && args[0]!=W_DATA_GROUP_COMMS)
        reason=W_REASON_INVALID_PARAMETER;
    else if (id==W_ID_SET_PARAMETER) {
        value=u32(args+W_SET_PARAMETER_VALUE);
        if (u16(args+W_SET_PARAMETER_PARAMETER_ID)!=W_PARAMETER_ID_TELEMETRY_PERIOD ||
            value<W_PERIOD_MINIMUM || value>W_PERIOD_MAXIMUM) reason=W_REASON_INVALID_PARAMETER;
    }
    if (reason) { s->rejected++; c->reports[c->count++]=response(id,W_STAGE_REJECTED,reason,0,0); }
    else {
        s->accepted++; c->reports[c->count++]=response(id,W_STAGE_ACCEPTED,0,0,0);
        if (id==W_ID_SET_PARAMETER) s->period=value;
        if (id==W_ID_REQUEST_STATUS || id==W_ID_REQUEST_TELEMETRY)
            c->reports[c->count++]=telemetry(s,id==W_ID_REQUEST_STATUS || args[0]==W_DATA_GROUP_SYSTEM?
                                           W_ID_SYSTEM_STATUS:W_ID_COMM_STATUS);
        c->reports[c->count++]=response(id,W_STAGE_COMPLETED,0,id==W_ID_SET_PARAMETER?W_PARAMETER_ID_TELEMETRY_PERIOD:0,
                                      id==W_ID_SET_PARAMETER?s->period:0);
    }
    for (unsigned i=0;i<c->count;i++) emit(s,&c->reports[i],epoch,transaction,uptime,send,context);
}
