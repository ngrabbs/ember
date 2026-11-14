"""Run the real IHU demo actor with fake time/CAN and validate the wire and Morse."""
import pathlib
import subprocess
import tempfile
import unittest

from test_can_addressing import DRIVER, SDK
from generate_c import generate

ROOT = pathlib.Path(__file__).resolve().parents[2]
CHECKS = r'''
#include "boot_morse.h"
static unsigned units, marks;
static char symbols[80], text[32];
static unsigned ns, nt;
static void decode(void) {
    static const struct {char ch;const char *pattern;} codes[]={
        {'K',"-.-"},{'I',".."},{'5',"....."},{'Y',"-.--"},{'N',"-."},{'G',"--."},
        {'-',"-....-"},{'E',"."},{'M',"--"},{'B',"-..."},{'R',".-."},{'O',"---"},{'T',"-"}
    };
    for(unsigned i=0;i<sizeof(codes)/sizeof(codes[0]);i++){
        if(!strcmp(symbols,codes[i].pattern)){text[nt++]=codes[i].ch;ns=0;symbols[0]=0;return;}
    }
    assert(0);
}
static bool segment(bool mark,unsigned count){
    units+=count;
    if(mark){assert(count==1 || count==3);symbols[ns++]=count==1?'.':'-';symbols[ns]=0;++marks;}
    else if(count!=1){assert(count==3 || count==7);decode();if(count==7)text[nt++]=' ';}
    return true;
}
static void tick(uint32_t delta){
    fake_now+=delta;housekeeping.last=fake_now;housekeeping.sampled=fake_now;
    ihu_app_step(true);
}
static void start(void){
    memset(&startup_demo,0,sizeof(startup_demo));memset(&housekeeping,0,sizeof(housekeeping));
    memset(&demo_up,0,sizeof(demo_up));output.active=false;demo_response_size=0;
    ihu_app_init();assert(policy.mode==IP_SAFE && !policy.outputs);
    assert(!demo_schedule.enabled && demo_schedule.listen_seconds==540 && demo_schedule.telemetry_seconds==60);
    assert(demo_schedule.packet_set==W_UHF_TELEMETRY_SET_BASIC);
    housekeeping.attempted=housekeeping.valid=true;
    tick(1);tick(1);tick(1);
    assert(startup_demo.stage==DEMO_PROBE && last_frame.id==BD_PROBE);
}
static void inject(const ul_packet *p,unsigned route){
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(p,wire);
    for(unsigned i=0;i*CF_CHUNK<n;i++){
        cf_frame f;assert(cf_fragment(wire,n,route,(uint16_t)p->request,i,&f));
        demo_receive(&f,fake_now);
    }
}
static void request(ul_packet *p,unsigned cmd,unsigned arg_size,uint32_t arg){
    ++p->request;p->size=32+arg_size;
    ul_p16(p->payload+4,p->size-7);ul_p16(p->payload+8,cmd);
    ul_p32(p->payload+16,p->request);ul_p16(p->payload+28,arg_size);
    if(arg_size==1)p->payload[30]=arg;
    if(arg_size==4)ul_p32(p->payload+30,arg);
    ul_p16(p->payload+p->size-2,ul_crc(p->payload,p->size-2));
    inject(p,BD_UP_ID);
}
static void complete_reply(void){
    tick(1);assert(startup_demo.tx_pending && output.route==BD_DOWN_ID);
    while(output.active)tick(2);
    cf_frame f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
}
static unsigned queued_message(void){
    ul_reader reader={0};ul_packet packet={0};
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&packet);
    assert(packet.type==BD_PACKET && !ul_u32(packet.payload+12) && !ul_u32(packet.payload+16));
    return ul_u16(packet.payload+W_MESSAGE_ID);
}
static void gps_sentence(gps_reader *reader,const char *body,bool valid,gps_result *result){
    unsigned sum=0;
    for(const char *p=body;*p;p++)sum^=(unsigned char)*p;
    char sentence[83];
    snprintf(sentence,sizeof(sentence),"$%s*%02X\r\n",body,valid?sum:sum^1);
    bool received=false;
    for(const char *p=sentence;*p;p++)if(gps_feed(reader,*p,result))received=true;
    assert(received==valid);
}
int main(void){
    gps_reader gps={0};gps_result position={0};
    gps_sentence(&gps,"GNGGA,123519,4807.038,S,01131.000,W,1,08,0.9,545.4,M,46.9,M,,",true,&position);
    assert(position.status==GPS_FIX && position.satellites==8);
    assert(position.altitude_valid && position.altitude>545.39 && position.altitude<545.41);
    assert(position.latitude<-48.1172 && position.latitude>-48.1174);
    assert(position.longitude<-11.5166 && position.longitude>-11.5168);
    gps_sentence(&gps,"GPGGA,123519,,,,,0,00,99.99,,,,,,",false,&position);
    assert(position.status==GPS_FIX);
    gps_sentence(&gps,"GPGGA,123519,,,,,0,00,99.99,,,,,,",true,&position);
    assert(position.status==GPS_NO_FIX && position.satellites==0);
    assert(boot_morse(segment));decode();assert(!strcmp(text,"KI5YNG - EMBER BOOT"));
    assert(marks>30 && units*BOOT_CW_UNIT_US<BD_CW_LIMIT_MS*1000);
    bd_radio r={0};uint32_t t=UINT32_MAX-100;
    assert(bd_arm(&r,7,t));assert(!bd_arm(&r,8,t+1));assert(bd_arm(&r,7,t+500));
    assert(!bd_take(&r,t+14999));assert(bd_take(&r,t+15000));assert(!bd_take(&r,t+15001));
    assert(!bd_arm(&r,7,t+16000));r=(bd_radio){0};assert(bd_arm(&r,7,t));assert(!bd_take(&r,t+30000));
    start();
    command("mode nominal");assert(policy.mode==IP_SAFE);
    cf_frame f=bd_frame(BD_READY,boot+1,22);demo_receive(&f,fake_now);assert(policy.mode==IP_SAFE);
    f=bd_frame(BD_READY,boot,22);demo_receive(&f,fake_now);
    assert(policy.mode==IP_STARTUP && !startup_demo.antenna);
    tick(9999);assert(!startup_demo.antenna && last_frame.id==BD_PROBE);
    tick(1);assert(startup_demo.antenna && last_frame.id==BD_PROBE);
    tick(4999);assert(policy.mode==IP_STARTUP && last_frame.id==BD_PROBE);
    tick(1);assert(policy.mode==IP_COMMISSIONING && bd_matches(&last_frame,boot,22) && last_frame.id==BD_FIRE);
    assert(fires==1);
    tick(200);assert(last_frame.id==BD_KEEP && fires==1);
    f=bd_frame(BD_RX,boot,23);demo_receive(&f,fake_now);assert(policy.mode==IP_COMMISSIONING);
    f=bd_frame(BD_RX,boot,22);demo_receive(&f,fake_now);assert(policy.mode==IP_COMMISSIONING);
    tick(1);assert(last_frame.id==BD_LINK);
    f=bd_frame(BD_LINKED,boot,22);demo_receive(&f,fake_now);
    assert(policy.mode==IP_NOMINAL && startup_demo.stage==DEMO_ACTIVE && !policy.outputs);
    command("gps");
    tick(BD_HEARTBEAT_MS);
    assert(!startup_demo.heartbeat_enabled && !startup_demo.tx_pending);
    command("output uhf_telem on");assert(!policy.outputs);
    ul_packet uplink={.version=1,.type=BD_PACKET,.sender=22,.origin=boot,.request=1,.size=32};
    uint8_t *p=uplink.payload;
    ul_p16(p,0x1900);ul_p16(p+2,0xc001);ul_p16(p+4,25);p[6]=1;ul_p16(p+8,1);
    p[10]=1;p[11]=2;ul_p32(p+12,11);ul_p32(p+16,42);ul_p32(p+20,55);ul_p16(p+30,ul_crc(p,30));
    uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(&uplink,wire);
    for(unsigned i=0;i*CF_CHUNK<n;i++){
        assert(cf_fragment(wire,n,BD_UP_ID,1,i,&f));demo_receive(&f,fake_now);
    }
    assert(demo_uplinks==1 && demo_replies==1 && demo_response_size==43);
    tick(1);
    assert(output.route==BD_DOWN_ID && startup_demo.tx_pending && !demo_response_size);
    ul_reader reader={0};ul_packet reply={0};
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.type==BD_PACKET && reply.origin==22 && reply.size==43);
    assert(ul_u16(reply.payload+30)==1 && ul_u32(reply.payload+16)==42 && reply.payload[32]==2);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,reply.request,22);demo_receive(&f,fake_now);
    assert(!startup_demo.tx_pending && demo_tx_ok==1);
    uplink.request=2;ul_p16(p+8,W_ID_REQUEST_STATUS);ul_p32(p+16,43);ul_p16(p+30,ul_crc(p,30));
    n=ul_encode(&uplink,wire);
    for(unsigned i=0;i*CF_CHUNK<n;i++){
        assert(cf_fragment(wire,n,BD_UP_ID,2,i,&f));demo_receive(&f,fake_now);
    }
    assert(demo_uplinks==2 && demo_replies==2 && demo_response_size==56);
    assert(ul_u16(demo_response+8)==W_ID_IHU_STATUS && ul_u32(demo_response+16)==43);
    assert(demo_response[31]==IP_NOMINAL && demo_response[41] && demo_response[50]==DR_ONLINE);
    assert(ul_crc(demo_response,54)==ul_u16(demo_response+54));
    tick(1);while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);

    request(&uplink,W_ID_REQUEST_TELEMETRY,1,W_DATA_GROUP_SYSTEM);
    assert(demo_response_size==56 && ul_u16(demo_response+8)==W_ID_IHU_STATUS);
    complete_reply();
    request(&uplink,W_ID_STATUS_CAPTURE,0,0);
    assert(cdh.active && cdh.count==1 && !demo_response_size);
    for(unsigned i=0;i<4;i++)tick(1000);
    assert(cdh.valid && !cdh.active && output.route==BD_DOWN_ID);
    reader=(ul_reader){0};
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.size==120 && ul_u16(reply.payload+8)==W_ID_STATUS_RECORDS);
    uint32_t capture_id=ul_u32(reply.payload+34);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    request(&uplink,W_ID_STATUS_FETCH,4,capture_id);
    assert(demo_response_size==120 && !memcmp(demo_response+38,reply.payload+38,80));
    complete_reply();
    request(&uplink,W_ID_IHU_REBOOT,0,0);
    assert(demo_response_size==43 && demo_response[32]==W_STAGE_REJECTED);
    assert(ul_u16(demo_response+33)==W_REASON_MODE_NOT_ALLOWED && !reboot_scheduled);
    complete_reply();

    request(&uplink,W_ID_PAYLOAD_FIRE_CHECK,0,0);
    assert(pending.active && pending.packet.type==UL_HELLO && output.route==CF_PAYLOAD_REQUEST_ID);
    while(output.active)tick(2);
    ul_packet ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=44;
    inject(&ack,CF_PAYLOAD_REPLY_ID);
    for(unsigned i=0;i<21 && fire_uplink.gps_waiting;++i)tick(100);
    assert(pending.active && pending.packet.type==PL_FIRE_CHECK && pending.packet.size==PL_GPS_SIZE);
    while(output.active)tick(2);
    tick(10000);
    assert(pending.active && fire_uplink.active && !demo_response_size);
    ack=pending.packet;ack.type=PL_FIRE_RESULT;ack.sender=44;ack.size=PL_GPS_TAGGED_SIZE;
    memset(ack.payload,0,sizeof(ack.payload));
    ack.payload[0]=1;ack.payload[2]=1;ul_p32(ack.payload+4,44);ul_p32(ack.payload+12,1);
    inject(&ack,CF_PAYLOAD_REPLY_ID);
    assert(!pending.active && !fire_uplink.active && demo_response_size==71);
    assert(ul_u16(demo_response+8)==W_ID_PAYLOAD_FIRE_TAGGED && demo_response[32]==0);
    assert(ul_u32(demo_response+16)==uplink.request);
    complete_reply();

    request(&uplink,W_ID_PAYLOAD_FIRE_CHECK,0,0);
    assert(pending.active && fire_uplink.active);
    tick(4999);
    assert(pending.active && pending.packet.type==UL_HELLO);
    tick(1);
    assert(!pending.active && !fire_uplink.active && output.route==BD_DOWN_ID);
    reader=(ul_reader){0};
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.size==43 && reply.payload[32]==W_STAGE_EXECUTION_FAILED);
    assert(ul_u16(reply.payload+33)==W_REASON_NOT_AVAILABLE);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);

    request(&uplink,W_ID_SET_HEARTBEAT,1,2);
    assert(!startup_demo.heartbeat_enabled && demo_response[32]==W_STAGE_REJECTED);
    complete_reply();
    request(&uplink,W_ID_SET_HEARTBEAT,1,1);
    assert(startup_demo.heartbeat_enabled && demo_response[32]==W_STAGE_COMPLETED);
    complete_reply();
    request(&uplink,W_ID_SET_HEARTBEAT,1,0);
    assert(!startup_demo.heartbeat_enabled && demo_response[32]==W_STAGE_COMPLETED);
    complete_reply();
    tick(BD_HEARTBEAT_MS);
    assert(!startup_demo.tx_pending);
    request(&uplink,W_ID_SET_UHF_TELEMETRY_SCHEDULE,4,(5u<<16)|4);
    assert(demo_response[32]==W_STAGE_REJECTED && demo_schedule.listen_seconds==540);
    complete_reply();
    request(&uplink,W_ID_SET_UHF_TELEMETRY_SCHEDULE,4,(5u<<16)|10);
    assert(demo_response[32]==W_STAGE_COMPLETED && ul_u32(demo_response+37)==((5u<<16)|10));
    assert(!demo_schedule.enabled && demo_schedule.listen_seconds==5 && demo_schedule.telemetry_seconds==10);
    complete_reply();
    request(&uplink,W_ID_SET_UHF_TELEMETRY,1,1);
    assert(demo_schedule.enabled && !startup_demo.heartbeat_enabled);
    complete_reply();
    request(&uplink,W_ID_PING,0,0);
    assert(demo_response[32]==W_STAGE_COMPLETED);
    complete_reply();
    request(&uplink,W_ID_SET_HEARTBEAT,1,1);
    assert(demo_response[32]==W_STAGE_REJECTED && !startup_demo.heartbeat_enabled);
    complete_reply();
    tick(demo_schedule.started+4999-fake_now);
    assert(!startup_demo.tx_pending);
    tick(1);
    assert(startup_demo.tx_pending && queued_message()==W_ID_IHU_STATUS);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    tick(1);
    assert(startup_demo.tx_pending && queued_message()==W_ID_POWER_STATUS);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    tick(7000);
    assert(!startup_demo.tx_pending);
    tick(demo_schedule.started+15000-fake_now);
    assert(!startup_demo.tx_pending);
    f=bd_frame(BD_LINKED,boot,22);demo_receive(&f,fake_now);
    tick(5000);
    assert(startup_demo.tx_pending && queued_message()==W_ID_IHU_STATUS);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    request(&uplink,W_ID_SET_UHF_TELEMETRY_SET,1,2);
    assert(demo_response[32]==W_STAGE_REJECTED && demo_schedule.packet_set==W_UHF_TELEMETRY_SET_BASIC);
    complete_reply();
    request(&uplink,W_ID_SET_UHF_TELEMETRY_SET,1,W_UHF_TELEMETRY_SET_FULL);
    assert(demo_response[32]==W_STAGE_COMPLETED && demo_schedule.packet_set==W_UHF_TELEMETRY_SET_FULL);
    uint32_t full_started=demo_schedule.started;
    complete_reply();
    request(&uplink,W_ID_SET_UHF_TELEMETRY_SET,1,W_UHF_TELEMETRY_SET_FULL);
    assert(demo_schedule.started==full_started);
    complete_reply();
    tick(full_started+4999-fake_now);
    assert(!startup_demo.tx_pending);
    const unsigned full_packets[]={W_ID_IHU_STATUS,W_ID_POWER_STATUS,W_ID_DEVICE_STATUS,
                                   W_ID_SYSTEM_STATUS,W_ID_HEARTBEAT};
    for(unsigned i=0;i<sizeof(full_packets)/sizeof(full_packets[0]);i++){
        tick(1);
        assert(startup_demo.tx_pending && queued_message()==full_packets[i]);
        while(output.active)tick(2);
        f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    }
    tick(1);
    assert(!startup_demo.tx_pending);
    assert(demo_poll.active && pending.packet.type==UL_HELLO);
    while(output.active)tick(2);
    ack=pending.packet;ack.type=UL_HELLO_ACK;ack.sender=44;
    inject(&ack,CF_PAYLOAD_REPLY_ID);
    assert(pending.active && pending.packet.type==PL_STATUS);
    while(output.active)tick(2);
    ack=pending.packet;ack.type=PL_STATUS_ACK;ack.sender=44;ack.size=PL_REPORT_SIZE;
    ack.payload[0]=1;ack.payload[1]=4;ack.payload[2]=1;
    ul_p32(ack.payload+4,44);ul_p32(ack.payload+8,1234);
    inject(&ack,CF_PAYLOAD_REPLY_ID);
    assert(!demo_poll.active && !pending.active);
    tick(1);
    assert(startup_demo.tx_pending && queued_message()==W_ID_PAYLOAD_STATUS);
    memset(&reader,0,sizeof(reader));memset(&reply,0,sizeof(reply));
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.payload[W_PAYLOAD+W_PAYLOAD_STATUS_TRANSPORT]==W_PAYLOAD_TRANSPORT_IHU_NATIVE_RF);
    assert(ul_u32(reply.payload+W_PAYLOAD+W_PAYLOAD_STATUS_REPORTED_BOOT_ID)==44);
    assert(ul_u32(reply.payload+W_PAYLOAD+W_PAYLOAD_STATUS_REPORTED_UPTIME_MS)==1234);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    tick(1);assert(!startup_demo.tx_pending);

    tick(1);
    assert(startup_demo.tx_pending && queued_message()==W_ID_GPS_STATUS);
    memset(&reader,0,sizeof(reader));memset(&reply,0,sizeof(reply));
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.payload[W_PAYLOAD+W_GPS_STATUS_STATUS]==W_GPS_STATUS_NO_DATA);
    assert(ul_u32(reply.payload+W_PAYLOAD+W_GPS_STATUS_LATITUDE_DEG)==(uint32_t)INT32_MIN);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);
    tick(1);assert(!startup_demo.tx_pending);

    assert(demo_poll.active && pending.packet.type==UL_FIRMWARE_INFO);
    while(output.active)tick(2);
    ack=pending.packet;
    ack.type=UL_FIRMWARE_INFO_ACK;ack.sender=22;ack.size=FI_SIZE;
    ack.payload[0]=1;ul_p32(ack.payload+24,22);
    inject(&ack,CF_COMMS_ID);

    tick(1);

    assert(startup_demo.tx_pending && queued_message()==W_ID_COMMS_FIRMWARE);
    while(output.active)tick(2);
    f=bd_frame(BD_TX_OK,startup_demo.tx_id,22);demo_receive(&f,fake_now);

    /* A missing payload reply never creates a telemetry sample. */
    demo_schedule.next_packet=5;
    tick(1);assert(demo_poll.active);
    tick(DEMO_PAYLOAD_TIMEOUT_MS);
    assert(!demo_poll.active && !pending.active && !startup_demo.tx_pending);
    request(&uplink,W_ID_SET_UHF_TELEMETRY,1,0);
    assert(!demo_schedule.enabled && demo_schedule.listen_seconds==5 && demo_schedule.telemetry_seconds==10);
    complete_reply();
    tick(6000);
    assert(!startup_demo.tx_pending);
    request(&uplink,W_ID_SET_HEARTBEAT,1,1);
    complete_reply();

    tick(BD_HEARTBEAT_MS);
    memset(&reader,0,sizeof(reader));memset(&reply,0,sizeof(reply));
    for(size_t i=0;i<output.size;i++)ul_feed(&reader,output.wire[i],0,&reply);
    assert(reply.type==BD_PACKET && ul_u16(reply.payload+8)==W_ID_HEARTBEAT);
    tick(BD_TX_TIMEOUT_MS);tick(1);assert(policy.mode==IP_SAFE && last_frame.id==BD_STOP && fires==1);

    start();f=bd_frame(BD_READY,boot,22);demo_receive(&f,fake_now);
    housekeeping.valid=false;tick(15000);
    assert(policy.mode==IP_SAFE && fires==1 && last_frame.id==BD_STOP);

    start();f=bd_frame(BD_READY,boot,22);demo_receive(&f,fake_now);tick(15000);
    assert(fires==2);tick(BD_CW_LIMIT_MS+2000);tick(1);
    assert(policy.mode==IP_SAFE && last_frame.id==BD_STOP && fires==2);
    f=bd_frame(BD_RX,boot,22);demo_receive(&f,fake_now);assert(policy.mode==IP_SAFE);

    start();f=bd_frame(BD_READY,boot,22);demo_receive(&f,fake_now);
    command("mode safe");tick(15000);assert(policy.mode==IP_SAFE && fires==2);
    puts("BOOT_DEMO_PASS");
    return 0;
}
'''

class BootDemo(unittest.TestCase):
    def test_timed_actor_and_morse(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / "sdk.h").write_text(SDK)
            for name in ("pico/stdlib.h", "pico/stdio_usb.h", "pico/unique_id.h",
                         "pico/rand.h", "hardware/i2c.h"):
                f = p / name
                f.parent.mkdir(exist_ok=True)
                f.write_text('#include "sdk.h"\n')
            (p / "build_identity.h").write_text(
                '#define FW_VERSION "0.18.1"\n#define FW_MAJOR 0\n#define FW_MINOR 18\n'
                '#define FW_PATCH 1\n#define FW_DIRTY 0\n#define FW_GIT "host-test"\n')
            generate(p / "wire.h")
            driver = DRIVER.split("static ul_packet queued")[0].replace(
                "bool mcp_send(mcp_state*s,const cf_frame*f){(void)s;(void)f;return true;}",
                "static cf_frame last_frame;static unsigned fires;\n"
                "bool mcp_send(mcp_state*s,const cf_frame*f){(void)s;last_frame=*f;"
                "if(f->id==BD_FIRE)++fires;return true;}")
            source = p / "test.c"
            source.write_text(f'#include <assert.h>\n#include "{ROOT}/firmware/ihu/app.c"\n'
                              + driver + CHECKS)
            binary = p / "test"
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-DIHU_HOST_TEST", "-DIHU_BOOT_DEMO=1",
                            f"-I{p}", f"-I{ROOT}/firmware/comms_transport",
                            f"-I{ROOT}/firmware/transceiver", str(source),
                            str(ROOT / "firmware/shared/ember_protocol/protocol.c"),
                            "-o", str(binary)], check=True)
            output = subprocess.check_output([binary], text=True)
            self.assertIn("GPS status=NO_DATA", output)
            self.assertIn("BOOT_DEMO_PASS", output)
