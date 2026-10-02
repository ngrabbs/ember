#include <assert.h>
#include "Arduino.h"
uint32_t test_time=0;int test_reset=-1;HardwareSerial Serial(9);
#include "../../firmware/walter_lte_bench/src/main.cpp"
#include "../../firmware/can_feather_bench/power_packet.h"
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
    setup();assert(state==OFF && test_reset==LOW);
    auto p=request(UL_HELLO);receive(p);assert(returned().type==UL_HELLO_ACK);
    p=request(UL_RF_WINDOW);p.size=4;ul_p32(p.payload,120);receive(p);
    assert(returned().type==UL_RF_WINDOW_ACK && state==BOOT_WAIT && test_reset==HIGH);
    uint32_t initial=deadline;receive(p);assert(returned().payload[0]==UL_ERR_BUSY && deadline==initial);
    test_time=12000;poll_modem(test_time);assert(at_busy && state==CONFIGURE);
    for(unsigned i=0;i<8;++i)ok();assert(state==REGISTER && !at_busy);
    poll_modem(test_time);ok("\r\n+CEREG: 2,1\r\n\r\nOK\r\n");assert(state==SOCKET_CONFIG);
    ok();assert(state==SOCKET_OPEN);ok();assert(state==READY);
    auto query=request(UL_LINK_STATUS);receive(query);auto health=returned();
    assert(health.type==UL_LINK_STATUS_ACK && health.size==16 && health.payload[0]==READY && health.payload[3]==1);
    p=request(UL_SEND_PACKET);ltc4162_raw_t raw={};raw.telemetry_status=1;raw.vbat=21071;
    p.size=power_packet(p.payload,&raw,77,1,456,1);receive(p);
    assert(state==SEND && send_pending && !payload_sent);
    auto other=p;other.request=11;receive(other);assert(returned().payload[0]==UL_ERR_BUSY);
    modem.output.clear();ok("\r\n> ");assert(payload_sent && modem.output==std::string((char*)p.payload,p.size));
    ok();auto ack=returned();assert(ack.type==UL_MODEM_ACCEPTED && ack.request==p.request && ack.origin==99);
    assert(ack.size==p.size && !memcmp(ack.payload,p.payload,p.size) && accepted==1 && state==READY);
    receive(other);assert(send_pending);test_time=deadline;poll_modem(test_time);
    auto failure=returned();assert(failure.type==UL_ERROR && failure.payload[0]==UL_ERR_MODEM_UNKNOWN);
    assert(state==OFF && test_reset==LOW && !send_pending);
    receive(p);assert(returned().payload[0]==UL_ERR_NOT_READY);
    p=request(UL_RF_WINDOW);p.size=4;ul_p32(p.payload,30);receive(p);returned();
    test_time+=12000;poll_modem(test_time);test_time+=6001;poll_modem(test_time);
    assert(state==OFF && test_reset==LOW);return 0;
}
