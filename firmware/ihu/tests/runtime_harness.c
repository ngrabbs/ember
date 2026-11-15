/* Run the production application and task adapters on the real FreeRTOS POSIX
 * scheduler. Only Pico peripherals are mocked; this is not an ARM timing test. */
#include <assert.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include "../runtime.c"
#include "uhf_client.h"
mock_watchdog_hw mock_watchdog;
static bool stall_sensor,sensor_working,slow_host;
static unsigned feeds,frames_while_sampling,rf_packets;
static char input[8192],capture[65536];static size_t input_read,input_used,capture_used;
static uint32_t sensor_started,last_rx;
static cf_reader assembled;
static ul_packet response_packets[4];static unsigned response_in,response_out,response_fragment;
uint32_t get_absolute_time(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);static uint64_t origin;uint64_t now=(uint64_t)t.tv_sec*1000+t.tv_nsec/1000000;if(!origin)origin=now;return (uint32_t)(now-origin);}
void watchdog_reboot(uint32_t pc,uint32_t sp,uint32_t delay){(void)pc;(void)sp;(void)delay;_Exit(100+(int)(mock_watchdog.scratch[0]&255));}
void watchdog_enable(uint32_t delay,bool debug){assert(delay==4000&&debug);}
void watchdog_update(void){++feeds;}
int getchar_timeout_us(int timeout){(void)timeout;return input_read<input_used?(uint8_t)input[input_read++]:PICO_ERROR_TIMEOUT;}
int putchar_raw(int ch){if(slow_host)vTaskDelay(pdMS_TO_TICKS(3));assert(capture_used+1<sizeof(capture));capture[capture_used++]=(char)ch;capture[capture_used]=0;return ch;}
static void enter(const char *line){size_t n=strlen(line);taskENTER_CRITICAL();assert(input_used+n+1<sizeof(input));memcpy(input+input_used,line,n);input_used+=n;input[input_used++]='\n';taskEXIT_CRITICAL();}
static void wait_for(const char *text){
    uint32_t began=milliseconds();
    while(!strstr(capture,text)){if((uint32_t)(milliseconds()-began)>=1500){fprintf(stderr,"wanted: %s\ncapture: %s\n",text,capture);abort();}vTaskDelay(pdMS_TO_TICKS(2));}
}
bool mcp_init(mcp_state *s){memset(s,0,sizeof(*s));s->ready=true;return true;}
bool mcp_mode(mcp_state *s,uint8_t mode){(void)s;(void)mode;return true;}
bool mcp_mode_begin(mcp_state *s,uint8_t mode){(void)s;(void)mode;return true;}
uint8_t mcp_register(uint8_t reg){return reg==0x29?0xf0:reg==0x28?0x86:0;}
void mcp_poll_tx(mcp_state *s,uint32_t now){(void)now;s->pending=false;}
static void reply_packet(const ul_packet *p){assert(response_in-response_out<4);response_packets[response_in++%4]=*p;}
bool mcp_send(mcp_state *s,const cf_frame *f){
    s->pending=true;++s->tx_ok;
    if(cf_feed(&assembled,f,0x710,milliseconds())){
        ul_reader reader={0};ul_packet p={0};bool found=false;
        for(size_t i=0;i<assembled.used;i++)if(ul_feed(&reader,assembled.wire[i],milliseconds(),&p))found=true;
        assert(found);
        if(p.type==UL_HELLO){ul_packet r=p;r.type=UL_HELLO_ACK;r.sender=22;reply_packet(&r);}
        else if(uhf_is_request(p.type)){
            ++rf_packets;ul_packet r;uhf_reply(&p,22,CF_UHF_ADMITTED,UHF_OK,&r);reply_packet(&r);
            uhf_reply(&p,22,CF_UHF_RESULT,UHF_OK,&r);reply_packet(&r);
        }
    }
    return true;
}
bool mcp_receive(mcp_state *s,cf_frame *f){
    uint32_t now=milliseconds();if(now==last_rx)return false;last_rx=now;
    if(sensor_working)++frames_while_sampling;
    if(response_in!=response_out){
        ul_packet *r=&response_packets[response_out%4];uint8_t wire[UL_WIRE_MAX];size_t n=ul_encode(r,wire);
        assert(cf_fragment(wire,n,0x711,(uint16_t)r->request,response_fragment++,f));
        if(response_fragment*CF_CHUNK>=n){response_fragment=0;++response_out;}
    } else {*f=(cf_frame){.id=0x700,.size=0};}
    ++s->rx;return true;
}
int i2c_write_timeout_us(int p,int a,const uint8_t *b,size_t n,bool repeated,int timeout){
    (void)p;(void)a;(void)b;(void)n;(void)repeated;(void)timeout;
    sensor_working=true;sensor_started=milliseconds();
    if(stall_sensor)for(;;){ /* Tick preemption must keep CAN/supervisor alive. */ }
    while((uint32_t)(milliseconds()-sensor_started)<150){} /* SDK-style polling with IRQs enabled. */
    sensor_working=false;return -1;
}
int i2c_read_timeout_us(int p,int a,uint8_t*b,size_t n,bool stop,int timeout){(void)p;(void)a;(void)b;(void)n;(void)stop;(void)timeout;return -1;}
static void test_task(void *arg){
    (void)arg;vTaskDelay(pdMS_TO_TICKS(30));
    enter("status");wait_for("configuration=GROUND_TEST mode=SAFE");
    enter("hello transceiver");wait_for("CAN_HELLO_CONFIRMED");
    enter("output uhf_telem on");wait_for("uhf_telem=1");
    enter("uhf heartbeat");wait_for("RF_TX_COMPLETE");assert(rf_packets==1);
    taskENTER_CRITICAL();capture_used=0;capture[0]=0;taskEXIT_CRITICAL();
    enter("eps json");
    while(!sensor_working)vTaskDelay(pdMS_TO_TICKS(1));
    if(stall_sensor){for(;;)vTaskDelay(pdMS_TO_TICKS(100));}
    enter("output uhf_telem off");
    uint32_t start=milliseconds();
    while(!strstr(capture,"uhf_telem=0 lte_telem=0\n") || sensor_started==0){assert(milliseconds()-start<100);vTaskDelay(1);}
    assert(sensor_working); /* OFF does not wait for I2C completion. */
    vTaskDelay(pdMS_TO_TICKS(200));
    assert(frames_while_sampling>20 && can_drops==0);
    wait_for("EPS_READ outcome=FAILED");
    /* Backpressure all normal reply slots as well as normal command ingress.
     * The separate control mailbox/reply queue must still accept OFF. */
    slow_host=true;
    usb_record load={.size=5,.text="LOAD\n"};
    for(unsigned i=0;i<IHU_REPLY_QUEUE;i++)enqueue_record(&load,true);
    /* Fill normal ingress and ensure OFF cannot be starved by queued ONs. */
    for(unsigned i=0;i<12;i++){ihu_command c={0};strcpy(c.line,"output uhf_telem on");submit_command(&c);}
    ihu_command off={0};strcpy(off.line,"output uhf_telem off");submit_command(&off);
    vTaskDelay(pdMS_TO_TICKS(20));
    assert(controls.pending==0);slow_host=false;
    vTaskDelay(pdMS_TO_TICKS(80));
    assert(controls.pending==0 && command_high==IHU_COMMAND_QUEUE);
    wait_for("CANCELLED_BY_STOP");
    enter("uhf heartbeat");wait_for("REJECT reason=OUTPUT_DISABLED");assert(rf_packets==1);
    enter("rtos");wait_for("RTOS kernel=V11.2.0");
    vTaskDelay(pdMS_TO_TICKS(120));assert(feeds>=3);
    static const char pass[]="PASS: actual FreeRTOS scheduler, CAN during blocked EPS, OFF priority, saturated ingress, RF result, watchdog progress\n";
    (void)write(STDOUT_FILENO,pass,sizeof(pass)-1);_Exit(0);
}
int main(int argc,char **argv){
    ihu_controls safety={.next=UINT32_MAX};ihu_command c={0};
    assert(!ihu_number_command(&safety,&c) && safety.pending==0x7f);
    assert(ihu_urgent_index("output  uhf_telem off ")==4);
    assert(ihu_urgent_index("output uhf_telem on")==-1);
    uint32_t seen[]={UINT32_MAX-5,3};assert(ihu_progress_ok(10,seen,2,20));
    assert(!ihu_progress_ok(30,seen,2,20));
    (void)get_absolute_time();(void)argv;stall_sensor=argc>1;
    static StaticTask_t control;static StackType_t stack[4096];
    assert(xTaskCreateStatic(test_task,"test",4096,NULL,3,stack,&control));
    ihu_runtime_start();return 1;
}
