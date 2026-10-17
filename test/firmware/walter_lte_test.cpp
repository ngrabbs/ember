#include <assert.h>
#include "Arduino.h"
uint32_t test_time=0;int test_reset=-1;HardwareSerial Serial(9);
#include "../../firmware/walter_lte_bench/src/main.cpp"
#include "../../firmware/can_feather_bench/power_packet.h"
#include "../../firmware/can_feather_bench/health_packet.h"
static ul_packet request(uint8_t type) {
    ul_packet p={};p.version=1;p.type=type;p.sender=99;p.origin=99;p.request=10;return p;
}
static ul_packet returned(void) {
    ul_reader r={};ul_packet p={};bool found=false;
    for(uint8_t byte:comms.output)if(ul_feed(&r,byte,test_time,&p))found=true;
    comms.output.clear();assert(found);return p;
}
static void ok(const char *body="\r\nOK\r\n") {
    modem.input=body;poll_modem(test_time);
}
int main(void) {
    uint8_t registration=255;
    for(const char *text:{"+CEREG:2,1","+CEREG: 2, 1","+CEREG: 1,\"1234\",\"abcdef\",7"}) {
        assert(parse_cereg(text,&registration) && registration==1);
    }
    assert(parse_cereg("+CEREG:2,5",&registration) && registration==5);
    assert(parse_cereg("+CEREG: 2,2",&registration) && registration==2);
    assert(!parse_cereg("AT+CEREG?",&registration));
    assert(!parse_cereg("+CEREG: garbage",&registration));
    modem.input="\r\n+CEREG: 1,\"1234\",\"abcdef\",7\r\n";
    at("AT");assert(registered==1 && cereg_status==1);
    off();state=REGISTER;wait_until=100;deadline=1000;
    modem.input="\r\n+CEREG:5\r\n";poll_modem(0);
    assert(registered==1 && cereg_status==5 && !at_busy);
    poll_modem(0);assert(state==SOCKET_CONFIG && at_busy);
    off();
    setup();assert(state==OFF && test_reset==LOW);
    auto p=request(UL_HELLO);receive(p);assert(returned().type==UL_HELLO_ACK);
    p=request(UL_RF_WINDOW);p.size=4;ul_p32(p.payload,120);receive(p);
    assert(returned().type==UL_RF_WINDOW_ACK && state==BOOT_WAIT && test_reset==HIGH);
    uint32_t initial=deadline;receive(p);assert(returned().payload[0]==UL_ERR_BUSY && deadline==initial);
    test_time=12000;poll_modem(test_time);assert(at_busy && state==CONFIGURE);
    for(unsigned i=0;i<8;++i) { ok(); }
    assert(state==REGISTER && !at_busy);
    poll_modem(test_time);ok("\r\n+CEREG:2, 1\r\n\r\nOK\r\n");assert(state==SOCKET_CONFIG);
    ok();assert(state==SOCKET_OPEN);ok();assert(state==READY);
    auto query=request(UL_LINK_STATUS);receive(query);auto health=returned();
    assert(health.type==UL_LINK_STATUS_ACK && health.size==16 && health.payload[0]==READY && health.payload[3]==1);
    p=request(UL_SEND_PACKET);ltc4162_raw_t raw={};raw.telemetry_status=1;raw.vbat=21071;
    p.size=power_packet(p.payload,&raw,77,1,456,1);receive(p);
    assert(state==SEND && send_pending && !payload_sent);
    assert(modem.output.size()>=1 && modem.output.back()=='\r');
    assert(modem.output.find("AT+SQNSSENDEXT=1,128,0\r\n")==std::string::npos);
    auto other=p;other.request=11;receive(other);assert(returned().payload[0]==UL_ERR_BUSY);
    modem.output.clear();ok("\r\n> ");assert(payload_sent && modem.output==std::string((char*)p.payload,p.size));
    ok();auto ack=returned();assert(ack.type==UL_MODEM_ACCEPTED && ack.request==p.request && ack.origin==99);
    assert(ack.size==p.size && !memcmp(ack.payload,p.payload,p.size) && accepted==1 && state==READY);
    query=request(UL_LINK_DIAG);receive(query);health=returned();
    assert(health.type==UL_LINK_DIAG_ACK && health.size==LTE_DIAG_SIZE && health.payload[16]==1);
    assert(health.payload[18]==1 && (health.payload[23]&11)==11);
    // READY is stale after a queued registration-loss URC: no send AT command.
    modem.output.clear();modem.input="\r\n+CEREG:2,2\r\n";
    receive(other);assert(returned().payload[0]==UL_ERR_NOT_READY);
    assert(state==READY && !registered && !send_pending && modem.output.empty());
    // Bounded registration polling can make the next explicit send admissible.
    poll_modem(test_time);assert(at_busy && modem.output=="AT+CEREG?\r");
    modem.output.clear();receive(other);assert(returned().payload[0]==UL_ERR_NOT_READY);
    assert(at_busy && modem.output.empty());
    ok("\r\n+CEREG:2,1\r\n\r\nOK\r\n");assert(registered && !at_busy);
    receive(other);assert(send_pending);test_time=deadline;poll_modem(test_time);
    auto failure=returned();assert(failure.type==UL_ERROR && failure.payload[0]==UL_ERR_MODEM_UNKNOWN);
    assert(state==OFF && test_reset==LOW && !send_pending);
    receive(p);assert(returned().payload[0]==UL_ERR_NOT_READY);
    p=request(UL_RF_WINDOW);p.size=4;ul_p32(p.payload,30);receive(p);returned();
    test_time+=12000;poll_modem(test_time);test_time+=6001;poll_modem(test_time);
    assert(state==OFF && test_reset==LOW);
    query=request(UL_LINK_DIAG);receive(query);health=returned();
    assert(health.payload[21]==1 && health.payload[22]==CONFIGURE && (health.payload[23]&4));
    reset_diagnostic();state=READY;cereg_status=1;registered=1;deadline=test_time+40000;
    p=request(UL_SEND_PACKET);p.size=power_packet(p.payload,&raw,77,2,456,2);receive(p);
    ok("\r\n+CME ERROR: 173\r\n");assert(returned().payload[0]==UL_ERR_MODEM_REJECTED);
    receive(query);health=returned();assert(health.payload[0]==OFF && health.payload[18]==1 && health.payload[19]==1);
    assert(ul_u32(health.payload+24)==173 && health.payload[45]==2 && health.payload[21]==10 && health.payload[22]==SEND);
    assert(health.payload[44]==3 && !memcmp(health.payload+48,"173",3));
    reset_diagnostic();state=READY;cereg_status=1;registered=1;deadline=test_time+40000;receive(p);
    ok("\r\n+CEREG:2,2\r\n+CME ERROR: operation not allowed\r\n");returned();
    receive(query);health=returned();assert(health.payload[19]==2 && ul_u32(health.payload+32)==1);
    assert(health.payload[45]==3 && ul_u32(health.payload+24)==UINT32_MAX);
    assert(!strcmp((const char*)health.payload+48,"operation not allowed"));
    for(bool system:{false,true}) {
        reset_diagnostic();state=READY;cereg_status=1;registered=1;deadline=test_time+40000;
        p=request(UL_SEND_PACKET);p.request=20+(unsigned)system;
        p.size=health_packet(p.payload,system,77,3,456,0,42,3);
        receive(p);assert(send_pending && state==SEND);
        modem.output.clear();ok("\r\n> ");
        assert(modem.output==std::string((char*)p.payload,p.size));
        ok();auto reply=returned();assert(reply.type==UL_MODEM_ACCEPTED && reply.size==p.size);
        assert(!memcmp(reply.payload,p.payload,p.size));
    }
    return 0;
}
