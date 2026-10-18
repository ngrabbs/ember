#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/watchdog.h"
#include "hardware/structs/watchdog.h"
#include "app.h"
#include "runtime.h"
#include "runtime_contract.h"
#include "services.h"
#include "eps_readout.h"

/* One core, one application actor. Workers never access application globals. */
typedef struct {bool mode;uint8_t wanted;cf_frame frame;} can_call;
typedef struct {bool ok;mcp_state state;} can_reply;
typedef struct {bool adc,enable;} sensor_call;
typedef struct {uint16_t size;char text[IHU_RECORD_SIZE];} usb_record;
typedef struct {mcp_state state;uint8_t registers[7];} can_snapshot;
static const uint8_t observed_registers[]={0x0e,0x2a,0x29,0x28,0x1c,0x1d,0x2d};
static can_snapshot snapshot;
static uint32_t progress[IHU_TASKS],idle_progress;
static uint32_t can_drops,reply_drops,log_drops,record_overflows,can_high,command_high;
static bool can_ready,sensor_ready,app_ready,schedule_due;
static ihu_controls controls;
static TaskHandle_t app_handle;
static QueueHandle_t can_calls,can_replies,can_frames,sensor_calls,sensor_results,commands,replies,logs;
#define STATIC_QUEUE(name,count,type) \
    static StaticQueue_t name##_control; \
    static uint8_t name##_storage[(count)*sizeof(type)]; \
    name=xQueueCreateStatic(count,sizeof(type),name##_storage,&name##_control); \
    configASSERT(name)
static uint32_t milliseconds(void){return to_ms_since_boot(get_absolute_time());}
static void checkin(unsigned who){taskENTER_CRITICAL();progress[who]=milliseconds();taskEXIT_CRITICAL();}
static void wake_app(void){if(app_handle)xTaskNotifyGive(app_handle);}
static void increment(uint32_t *p){taskENTER_CRITICAL();++*p;taskEXIT_CRITICAL();}
void ihu_runtime_panic(unsigned reason){
    watchdog_hw->scratch[0]=0x49485500u|reason;
    watchdog_reboot(0,0,10);
    for(;;)tight_loop_contents();
}
void vApplicationStackOverflowHook(TaskHandle_t task,char *name){(void)task;(void)name;ihu_runtime_panic(2);}
void vApplicationIdleHook(void){taskENTER_CRITICAL();idle_progress=milliseconds();taskEXIT_CRITICAL();}
static void copy_snapshot(mcp_state *s){taskENTER_CRITICAL();*s=snapshot.state;taskEXIT_CRITICAL();}
bool ihu_can_init(mcp_state *s){copy_snapshot(s);return s->ready;}
void ihu_can_poll_tx(mcp_state *s,uint32_t now){(void)now;copy_snapshot(s);}
uint8_t ihu_can_register(uint8_t reg){
    uint8_t value=0xff;
    taskENTER_CRITICAL();
    for(unsigned i=0;i<sizeof(observed_registers);i++)if(reg==observed_registers[i])value=snapshot.registers[i];
    taskEXIT_CRITICAL();return value;
}
static bool call_can(mcp_state *s,can_call *call){
    can_reply reply;
    /* Sole caller is the application actor; a missing completion is fatal,
     * never recycled into a later request with ambiguous identity. */
    if(xQueueSend(can_calls,call,0)!=pdPASS)ihu_runtime_panic(3);
    if(xQueueReceive(can_replies,&reply,pdMS_TO_TICKS(150))!=pdPASS)ihu_runtime_panic(4);
    *s=reply.state;return reply.ok;
}
bool ihu_can_mode(mcp_state *s,uint8_t mode){can_call call={.mode=true,.wanted=mode};return call_can(s,&call);}
bool ihu_can_send(mcp_state *s,const cf_frame *frame){can_call call={.frame=*frame};return call_can(s,&call);}
bool ihu_can_receive(mcp_state *s,cf_frame *frame){copy_snapshot(s);return xQueueReceive(can_frames,frame,0)==pdPASS;}
bool ihu_sensor_submit(bool adc,bool enable){sensor_call call={adc,enable};return xQueueSend(sensor_calls,&call,0)==pdPASS;}
bool ihu_sensor_receive(ihu_sensor_result *r){return xQueueReceive(sensor_results,r,0)==pdPASS;}

/* Only the application actor builds fragmented printf records. USB and workers
 * may enqueue already complete records through the independent queues. */
static usb_record building;
static bool building_reply,discard_record;
static void enqueue_record(const usb_record *r,bool reply){
    if(xQueueSend(reply?replies:logs,r,0)!=pdPASS)increment(reply?&reply_drops:&log_drops);
}
void ihu_vprintf(bool reply,const char *fmt,va_list args){
    char part[IHU_RECORD_SIZE]={0};int length=vsnprintf(part,sizeof(part),fmt,args);
    if(length<0 || (size_t)length>=sizeof(part)){discard_record=true;increment(&record_overflows);}
    for(size_t i=0;part[i] && i<sizeof(part)-1;i++){
        char ch=part[i];
        if(!building.size)building_reply=reply;
        if(!discard_record){
            if(building.size<sizeof(building.text)-1)building.text[building.size++]=ch;
            else {discard_record=true;increment(&record_overflows);}
        }
        if(ch=='\n'){
            if(!discard_record){building.text[building.size]=0;enqueue_record(&building,building_reply);}
            building.size=0;discard_record=false;
        }
    }
}
static void usb_error(const char *message){
    usb_record record={0};int n=snprintf(record.text,sizeof(record.text),"REJECT reason=%s\n",message);
    if(n>0 && (size_t)n<sizeof(record.text)){record.size=(uint16_t)n;enqueue_record(&record,true);}
}
static StaticTask_t task_control[IHU_TASKS];
static TaskHandle_t handles[IHU_TASKS];
static StackType_t supervisor_stack[512],can_stack[1024],app_stack[2048],sensor_stack[512],schedule_stack[256],usb_stack[1024];
void ihu_runtime_status(void){
    uint32_t dropped_rx,dropped_reply,dropped_log,overflows,high_rx,high_command;
    taskENTER_CRITICAL();dropped_rx=can_drops;dropped_reply=reply_drops;dropped_log=log_drops;
    overflows=record_overflows;high_rx=can_high;high_command=command_high;taskEXIT_CRITICAL();
    ihu_printf(true,"RTOS kernel=%s cores=1 preemptive=1 tick_hz=%u can_rx_drops=%" PRIu32 " reply_drops=%" PRIu32 " log_drops=%" PRIu32 " record_overflows=%" PRIu32 " can_rx_high=%" PRIu32 " command_high=%" PRIu32 " reset_reason=%08" PRIx32 "\n",
        tskKERNEL_VERSION_NUMBER,(unsigned)configTICK_RATE_HZ,dropped_rx,dropped_reply,dropped_log,overflows,high_rx,high_command,watchdog_hw->scratch[0]);
    for(unsigned i=0;i<IHU_TASKS;i++)ihu_printf(true,"RTOS_TASK id=%u stack_free_words=%u\n",i,(unsigned)uxTaskGetStackHighWaterMark(handles[i]));
}
static void publish_can(mcp_state *state){
    can_snapshot next={.state=*state};
    for(unsigned i=0;i<sizeof(observed_registers);i++)next.registers[i]=mcp_register(observed_registers[i]);
    taskENTER_CRITICAL();snapshot=next;taskEXIT_CRITICAL();
}
static void can_task(void *arg){
    (void)arg;mcp_state state;mcp_init(&state);
    if(state.ready)(void)mcp_mode(&state,0); /* Bounded startup only. */
    publish_can(&state);taskENTER_CRITICAL();can_ready=true;taskEXIT_CRITICAL();
    bool changing=false;uint8_t wanted=0;uint32_t started=0;
    for(;;){
        uint32_t now=milliseconds();cf_frame frame;can_call call;bool complete=false,ok=false;
        mcp_poll_tx(&state,now);
        for(unsigned i=0;i<16;i++){
            if(!mcp_receive(&state,&frame))break;
            if(xQueueSend(can_frames,&frame,0)!=pdPASS)increment(&can_drops);
            unsigned used=uxQueueMessagesWaiting(can_frames);
            taskENTER_CRITICAL();if(used>can_high)can_high=used;taskEXIT_CRITICAL();
            wake_app();
        }
        if(changing){
            if((mcp_register(0x0e)&0xe0)==wanted){complete=true;ok=true;changing=false;}
            else if((uint32_t)(now-started)>=100){state.ready=false;complete=true;changing=false;}
        } else if(xQueueReceive(can_calls,&call,0)==pdPASS){
            if(call.mode){
                wanted=call.wanted;changing=mcp_mode_begin(&state,wanted);started=now;
                if(!changing)complete=true;
            } else {ok=mcp_send(&state,&call.frame);complete=true;}
        }
        publish_can(&state);
        if(complete){can_reply reply={.ok=ok,.state=state};configASSERT(xQueueSend(can_replies,&reply,0)==pdPASS);}
        checkin(IHU_CAN);vTaskDelay(pdMS_TO_TICKS(1));
    }
}
static void sensor_task(void *arg){
    (void)arg;eps_bus_init();taskENTER_CRITICAL();sensor_ready=true;taskEXIT_CRITICAL();
    for(;;){
        sensor_call call;
        if(xQueueReceive(sensor_calls,&call,pdMS_TO_TICKS(100))==pdPASS){
            ihu_sensor_result r={.enable=call.enable};
            r.ok=call.adc?eps_force_adc(call.enable,&r.before,&r.after):eps_read(&r.raw,&r.failed);
            r.sampled=milliseconds();configASSERT(xQueueSend(sensor_results,&r,0)==pdPASS);wake_app();
        }
        checkin(IHU_SENSOR);
    }
}
static void run_urgent(uint32_t *cancel_before){
    ihu_controls copy;taskENTER_CRITICAL();copy=controls;controls.pending=0;taskEXIT_CRITICAL();
    static const char *const lines[]={"output cli_debug off","output cli_telem off","output umb_debug off","output umb_telem off","output uhf_telem off","output lte_telem off","uhf stop"};
    for(unsigned i=0;i<7;i++)if(copy.pending&(1u<<i)){
        ihu_app_command(lines[i]);if(copy.sequence[i]>*cancel_before)*cancel_before=copy.sequence[i];
    }
}
static void application_task(void *arg){
    (void)arg;uint32_t began=milliseconds();
    for(;;){
        bool ready;taskENTER_CRITICAL();ready=can_ready&&sensor_ready;taskEXIT_CRITICAL();
        if(ready)break;
        if((uint32_t)(milliseconds()-began)>1000)ihu_runtime_panic(5);
        checkin(IHU_APP);vTaskDelay(pdMS_TO_TICKS(1));
    }
    ihu_app_init();taskENTER_CRITICAL();app_ready=true;taskEXIT_CRITICAL();
    uint32_t cancel_before=0;
    for(;;){
        run_urgent(&cancel_before);
        ihu_command command;
        if(xQueueReceive(commands,&command,0)==pdPASS){
            if(command.sequence<cancel_before)usb_error("CANCELLED_BY_STOP");
            else ihu_app_command(command.line);
        }
        /* OFF is processed before collecting EPS results or advancing TX. */
        run_urgent(&cancel_before);
        bool due;taskENTER_CRITICAL();due=schedule_due;schedule_due=false;taskEXIT_CRITICAL();
        ihu_app_step(due);
        checkin(IHU_APP);
        if(uxQueueMessagesWaiting(commands)==0)(void)ulTaskNotifyTake(pdTRUE,pdMS_TO_TICKS(2));
        else vTaskDelay(pdMS_TO_TICKS(1));
    }
}
static void schedule_task(void *arg){
    (void)arg;TickType_t next=xTaskGetTickCount();
    for(;;){taskENTER_CRITICAL();schedule_due=true;taskEXIT_CRITICAL();wake_app();checkin(IHU_SCHEDULE);vTaskDelayUntil(&next,pdMS_TO_TICKS(2));}
}
static void submit_command(ihu_command *command){
    taskENTER_CRITICAL();bool numbered=ihu_number_command(&controls,command);taskEXIT_CRITICAL();
    if(!numbered){usb_error("COMMAND_SEQUENCE_EXHAUSTED");return;}
    if(ihu_urgent_index(command->line)<0 && xQueueSend(commands,command,0)!=pdPASS)usb_error("COMMAND_QUEUE_FULL");
    unsigned used=uxQueueMessagesWaiting(commands);
    taskENTER_CRITICAL();if(used>command_high)command_high=used;taskEXIT_CRITICAL();wake_app();
}
static void usb_task(void *arg){
    (void)arg;ihu_command command={0};size_t used=0;bool discard=false;
    usb_record outgoing={0};size_t sent=0;
    for(;;){
        for(unsigned i=0;i<40;i++){
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT)break;
            if(ch=='\r'||ch=='\n'){
                if(discard)usb_error("COMMAND_TOO_LONG");
                else if(used){command.line[used]=0;submit_command(&command);}
                used=0;discard=false;
            } else if(!discard){if(ch && used+1<sizeof(command.line))command.line[used++]=(char)ch;else discard=true;}
        }
        if(!outgoing.size){
            if(xQueueReceive(replies,&outgoing,0)!=pdPASS)(void)xQueueReceive(logs,&outgoing,0);
            sent=0;
        }
        if(outgoing.size){
            /* SDK stdio has a bounded timeout; one small chunk per wake limits
             * USB load. A complete record is never interleaved with another. */
            if(!stdio_usb_connected()){outgoing.size=0;}
            else {
                unsigned count=outgoing.size-sent;if(count>64)count=64;
                for(unsigned i=0;i<count;i++)putchar_raw(outgoing.text[sent++]);
                if(sent==outgoing.size)outgoing.size=0;
            }
        }
        checkin(IHU_USB);vTaskDelay(pdMS_TO_TICKS(1));
    }
}
static void supervisor_task(void *arg){
    (void)arg;uint32_t began=milliseconds();bool led=false;
    gpio_init(13);gpio_set_dir(13,GPIO_OUT);
    for(;;){
        uint32_t now=milliseconds(),seen[IHU_TASKS],idle;bool ready;
        checkin(IHU_SUPERVISOR);
        taskENTER_CRITICAL();memcpy(seen,progress,sizeof(seen));idle=idle_progress;ready=app_ready;taskEXIT_CRITICAL();
        bool healthy=ihu_progress_ok(now,seen,IHU_TASKS,2000) && (uint32_t)(now-idle)<=2000;
        if((uint32_t)(now-began)<1500 || (ready && healthy))watchdog_update();
        else ihu_runtime_panic(6);
        led=!led;gpio_put(13,led);vTaskDelay(pdMS_TO_TICKS(100));
    }
}
void ihu_runtime_start(void){
    stdio_init_all();
    STATIC_QUEUE(can_calls,1,can_call);STATIC_QUEUE(can_replies,1,can_reply);
    STATIC_QUEUE(can_frames,IHU_CAN_RX_QUEUE,cf_frame);
    STATIC_QUEUE(sensor_calls,1,sensor_call);STATIC_QUEUE(sensor_results,1,ihu_sensor_result);
    STATIC_QUEUE(commands,IHU_COMMAND_QUEUE,ihu_command);
    STATIC_QUEUE(replies,IHU_REPLY_QUEUE,usb_record);STATIC_QUEUE(logs,IHU_LOG_QUEUE,usb_record);
    handles[IHU_SUPERVISOR]=xTaskCreateStatic(supervisor_task,"supervisor",512,NULL,5,supervisor_stack,&task_control[IHU_SUPERVISOR]);
    handles[IHU_CAN]=xTaskCreateStatic(can_task,"can_service",1024,NULL,4,can_stack,&task_control[IHU_CAN]);
    handles[IHU_APP]=xTaskCreateStatic(application_task,"command_mode",2048,NULL,3,app_stack,&task_control[IHU_APP]);
    handles[IHU_SENSOR]=xTaskCreateStatic(sensor_task,"sensors",512,NULL,2,sensor_stack,&task_control[IHU_SENSOR]);
    handles[IHU_SCHEDULE]=xTaskCreateStatic(schedule_task,"schedule",256,NULL,2,schedule_stack,&task_control[IHU_SCHEDULE]);
    handles[IHU_USB]=xTaskCreateStatic(usb_task,"usb_console",1024,NULL,1,usb_stack,&task_control[IHU_USB]);
    app_handle=handles[IHU_APP];
    for(unsigned i=0;i<IHU_TASKS;i++)configASSERT(handles[i]);
    watchdog_enable(4000,true);
    vTaskStartScheduler();ihu_runtime_panic(7);
}
