#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "hardware/watchdog.h"
#include "FreeRTOS.h"
#include "task.h"
#include "demo.h"
#define SWITCH_A 14
#define SWITCH_B 15
#define HISTORY 32
static demo_state state;
static StaticTask_t task_buffer;
static StackType_t task_stack[2048];
static char history[HISTORY][160];
static unsigned history_count;
static uint32_t now_ms(void) {return to_ms_since_boot(get_absolute_time());}
static void event(const char *format,...) {
    char body[120];va_list args;va_start(args,format);vsnprintf(body,sizeof(body),format,args);va_end(args);
    unsigned slot=history_count%HISTORY;
    snprintf(history[slot],sizeof(history[slot]),"EVENT t_ms=%lu %s",(unsigned long)now_ms(),body);
    history_count++;
    if(stdio_usb_connected()) printf("%s\n",history[slot]);
}
static void version(void) {
    printf("FIRMWARE role=IHU_DEMO board=pico_rp2040 version=%s git=%s dirty=%d\n",DEMO_VERSION,DEMO_GIT,DEMO_DIRTY);
    printf("DEMO ONLY: USB console + GP14/GP15 inputs; all peers, deployment and RF are simulated.\n");
}
static void outputs(void) {
    printf("OUTPUTS cli_debug=%u cli_telem=%u umb_debug=0 umb_telem=0 uhf_telem=0 lte_telem=0\n",
        !!(state.policy.outputs&(1u<<IP_CLI_DEBUG)),!!(state.policy.outputs&(1u<<IP_CLI_TELEM)));
}
static void status(void) {
    uint32_t elapsed=state.released ? now_ms()-state.release_ms : 0;
    printf("MODE configuration=GROUND_TEST mode=%s simulated=1 reason=%s\n",ip_modes[state.policy.mode],state.policy.reason);
    printf("SWITCHES A=GP14 raw=%s stable=%s B=GP15 raw=%s stable=%s debounce_ms=%u\n",
        state.raw[0]?"RELEASED":"HELD",state.stable[0]?"RELEASED":"HELD",
        state.raw[1]?"RELEASED":"HELD",state.stable[1]?"RELEASED":"HELD",DEMO_DEBOUNCE_MS);
    printf("GATES simulated_health=%u release_qualified=%u antenna_simulated=%u rf_wait_complete=%u checkout=%u\n",
        state.health,state.released,state.antenna,state.rf,state.checkout);
    printf("DEMO_TIMERS elapsed_ms=%lu antenna_wait_ms=%u rf_wait_ms=%u persistence=NONE\n",
        (unsigned long)elapsed,DEMO_ANTENNA_MS,DEMO_RF_MS);
    outputs();
}
static void help(void) {
    printf("COMMANDS help | version | status | mode | outputs | rtos | history | reboot\n"
        "  demo start (or mode startup): both jumpers installed, health OK; wait for release\n"
        "  demo checkout: accept SIMULATED checkout in COMMISSIONING\n"
        "  demo approve (or mode nominal): guarded approval after checkout\n"
        "  mode safe: stop and clear progression; reinstall jumpers before restarting\n"
        "  demo health fail/ok: inject/clear simulated fault; clear stays SAFE\n"
        "  demo reset: restart this volatile scenario in SAFE without USB reconnect\n"
        "  output cli_debug on/off | output cli_telem on/off\n"
        "Pull BOTH jumpers, wait 10s antenna / 15s RF (DEMO TIMES), then checkout + approve.\n"
        "Reinsert EITHER jumper after release to enter SAFE. Other IHU commands are unavailable.\n");
}
static void replay(void) {
    printf("HISTORY last=%u retained_max=%u (RAM only; timestamps since boot)\n",history_count,HISTORY);
    unsigned first=history_count>HISTORY?history_count-HISTORY:0;
    for(unsigned i=first;i<history_count;i++) printf("%s\n",history[i%HISTORY]);
}
static void observe(const demo_state *before) {
    if(before->stable[0]!=state.stable[0] || before->stable[1]!=state.stable[1])
        event("SWITCHES qualified A=%s B=%s",state.stable[0]?"RELEASED":"HELD",state.stable[1]?"RELEASED":"HELD");
    if(!before->released && state.released) event("RELEASE qualified; independent DEMO waits start: antenna=10s RF=15s");
    if(!before->antenna && state.antenna) event("ANTENNA simulated completion; no actuator connected or driven");
    if(!before->rf && state.rf) event("RF demo wait complete; no radio connected or driven");
    if(before->policy.mode!=state.policy.mode)
        event("MODE %s -> %s reason=%s",ip_modes[before->policy.mode],ip_modes[state.policy.mode],state.policy.reason);
    if(before->policy.mode!=state.policy.mode || before->released!=state.released) status();
}
static void reset_scenario(void) {
    event("MODE -> BOOT reason=DEMO_SCENARIO_RESET");
    demo_init(&state,now_ms(),gpio_get(SWITCH_A),gpio_get(SWITCH_B));
    event("MODE BOOT -> SAFE reason=%s",state.policy.reason);
}
static void command(char *line) {
    demo_state before=state;const char *error=NULL;
    if(!strcmp(line,"help")) help();
    else if(!strcmp(line,"version")) version();
    else if(!strcmp(line,"status") || !strcmp(line,"mode")) status();
    else if(!strcmp(line,"outputs")) outputs();
    else if(!strcmp(line,"history")) replay();
    else if(!strcmp(line,"rtos")) printf("RTOS kernel=%s core=0 task=demo stack_free_words=%lu\n",tskKERNEL_VERSION_NUMBER,(unsigned long)uxTaskGetStackHighWaterMark(NULL));
    else if(!strcmp(line,"demo start") || !strcmp(line,"mode startup")) error=demo_start(&state);
    else if(!strcmp(line,"demo checkout")) {
        error=demo_checkout(&state);
        if(!error) event("CHECKOUT simulated checklist accepted; awaiting demo approve");
    }
    else if(!strcmp(line,"demo approve") || !strcmp(line,"mode nominal")) error=demo_approve(&state);
    else if(!strcmp(line,"mode safe")) demo_safe(&state,"GROUND_SAFE_COMMAND");
    else if(!strcmp(line,"demo health fail")) {demo_health(&state,false);event("HEALTH simulated fault injected");}
    else if(!strcmp(line,"demo health ok")) {demo_health(&state,true);event("HEALTH simulated healthy; no automatic recovery");}
    else if(!strcmp(line,"demo reset")) {reset_scenario();status();return;}
    else if(!strcmp(line,"reboot")) {printf("REBOOT scenario/history will be cleared; reconnect console\n");watchdog_reboot(0,0,100);return;}
    else if(!strncmp(line,"output ",7)) {
        char name[32],value[8],extra[2];int n=sscanf(line+7,"%31s %7s %1s",name,value,extra);
        if(n!=2 || (strcmp(value,"on") && strcmp(value,"off"))) error="USE_output_NAME_on_or_off";
        else if(strcmp(name,"cli_debug") && strcmp(name,"cli_telem")) error="DEMO_SUPPORTS_ONLY_cli_debug_AND_cli_telem";
        else {error=ip_set_output(&state.policy,!strcmp(name,"cli_debug")?IP_CLI_DEBUG:IP_CLI_TELEM,!strcmp(value,"on"));if(!error) outputs();}
    }
    else error="UNKNOWN_COMMAND_TYPE_help";
    if(error) printf("REJECT reason=%s\n",error);
    else printf("OK command=%s\n",line);
    observe(&before);
}
static void run(void *unused) {
    (void)unused;bool connected=false,discard=false;char line[96];unsigned used=0;
    uint32_t last_second=now_ms(),last_telem=now_ms();
    for(;;) {
        uint32_t now=now_ms();demo_state before=state;
        demo_tick(&state,now,gpio_get(SWITCH_A),gpio_get(SWITCH_B));
        bool live=stdio_usb_connected();
        /* Save transitions before replay, including events while the terminal was closed. */
        observe(&before);
        if(live && !connected) {version();replay();status();printf("Type help, then demo start with both jumpers installed.\n> ");}
        if(!live) {used=0;discard=false;}
        connected=live;
        for(unsigned i=0;live && i<32;i++) {
            int ch=getchar_timeout_us(0);if(ch==PICO_ERROR_TIMEOUT) break;
            if(ch=='\r' || ch=='\n') {
                if(discard) {printf("\nREJECT reason=LINE_TOO_LONG\n> ");discard=false;used=0;}
                else if(used) {line[used]=0;printf("\n");command(line);used=0;printf("> ");}
            } else if(ch==8 || ch==127) {if(!discard && used){used--;printf("\b \b");}}
            else if(ch>=32 && ch<=126 && !discard) {
                if(used<sizeof(line)-1) {line[used++]=(char)ch;putchar(ch);} else {discard=true;used=0;}
            }
        }
        if((uint32_t)(now-last_second)>=1000) {
            last_second=now;
            if(state.policy.mode==IP_STARTUP && state.released) {
                uint32_t elapsed=now-state.release_ms;
                printf("WAIT DEMO elapsed_s=%lu antenna_remaining_s=%lu rf_remaining_s=%lu\n",
                    (unsigned long)(elapsed/1000),(unsigned long)(elapsed>=DEMO_ANTENNA_MS?0:(DEMO_ANTENNA_MS-elapsed+999)/1000),
                    (unsigned long)(elapsed>=DEMO_RF_MS?0:(DEMO_RF_MS-elapsed+999)/1000));
            }
            if(ip_enabled(&state.policy,IP_CLI_DEBUG)) printf("DEBUG DEMO mode=%s health=%u release=%u checkout=%u\n",ip_modes[state.policy.mode],state.health,state.released,state.checkout);
            gpio_put(PICO_DEFAULT_LED_PIN,state.policy.mode==IP_NOMINAL || ((now/1000)%2));
        }
        if((uint32_t)(now-last_telem)>=5000) {last_telem=now;if(ip_enabled(&state.policy,IP_CLI_TELEM)) status();}
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
void ihu_runtime_panic(unsigned reason) {(void)reason;watchdog_reboot(0,0,10);for(;;) tight_loop_contents();}
void vApplicationStackOverflowHook(TaskHandle_t task,char *name) {(void)task;(void)name;ihu_runtime_panic(2);}
int main(void) {
    stdio_init_all();
    gpio_init(SWITCH_A);gpio_set_dir(SWITCH_A,GPIO_IN);gpio_pull_up(SWITCH_A);
    gpio_init(SWITCH_B);gpio_set_dir(SWITCH_B,GPIO_IN);gpio_pull_up(SWITCH_B);
    gpio_init(PICO_DEFAULT_LED_PIN);gpio_set_dir(PICO_DEFAULT_LED_PIN,GPIO_OUT);
    reset_scenario();
    xTaskCreateStatic(run,"demo",2048,NULL,2,task_stack,&task_buffer);
    vTaskStartScheduler();ihu_runtime_panic(3);
}
