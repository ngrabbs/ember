#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
/* Values match the shared wire dictionary. Configuration is latched at boot. */
enum {IP_GROUND_TEST=1,IP_FLIGHT=2};
enum {IP_BOOT,IP_STARTUP,IP_COMMISSIONING,IP_SAFE,IP_NOMINAL};
enum {IP_CLI_DEBUG,IP_CLI_TELEM,IP_UMB_DEBUG,IP_UMB_TELEM,IP_UHF_TELEM,IP_LTE_TELEM,IP_OUTPUT_COUNT};
static const char *const ip_modes[]={"BOOT","STARTUP","COMMISSIONING","SAFE","NOMINAL"};
static const char *const ip_outputs[]={"cli_debug","cli_telem","umb_debug","umb_telem","uhf_telem","lte_telem"};
typedef struct {uint8_t configuration,mode,outputs;const char *reason;} ip_state;
static inline void ip_init(ip_state *s,uint8_t configuration){
    *s=(ip_state){.configuration=configuration,.mode=IP_BOOT,.reason="RESET"};
}
static inline void ip_finish_boot(ip_state *s,bool essential_ok,bool history_valid,bool startup_incomplete){
    s->outputs=0;
    if(s->configuration==IP_GROUND_TEST){s->mode=IP_SAFE;s->reason=essential_ok?"GROUND_TEST_DEFAULT":"ESSENTIAL_CHECK_FAILED";}
    else if(s->configuration!=IP_FLIGHT){s->mode=IP_SAFE;s->reason="INVALID_CONFIGURATION";}
    else if(!essential_ok || !history_valid){s->mode=IP_SAFE;s->reason=!essential_ok?"ESSENTIAL_CHECK_FAILED":"HISTORY_UNAVAILABLE";}
    else {s->mode=startup_incomplete?IP_STARTUP:IP_SAFE;s->reason=startup_incomplete?"INITIAL_STARTUP":"FLIGHT_REBOOT";}
}
static inline bool ip_test(const ip_state *s){return s->configuration==IP_GROUND_TEST && s->mode>=IP_STARTUP && s->mode<=IP_NOMINAL;}
static inline bool ip_enabled(const ip_state *s,unsigned channel){
    return channel<IP_OUTPUT_COUNT && ip_test(s) && (s->outputs&(1u<<channel));
}
static inline const char *ip_set_output(ip_state *s,unsigned channel,bool on){
    if(channel>=IP_OUTPUT_COUNT)return "UNKNOWN_OUTPUT";
    if(on && !ip_test(s))return s->mode==IP_BOOT?"BOOT_IN_PROGRESS":"FLIGHT_ROUTINE_STUB";
    if(on)s->outputs|=(uint8_t)(1u<<channel);else s->outputs&=(uint8_t)~(1u<<channel);
    return NULL;
}
static inline const char *ip_mode(ip_state *s,unsigned mode){
    if(mode>IP_NOMINAL || mode==IP_BOOT)return "INVALID_MODE_USE_RESET_FOR_BOOT";
    if(s->configuration!=IP_GROUND_TEST && mode!=IP_SAFE)return "FLIGHT_ROUTINE_STUB";
    s->mode=(uint8_t)mode;s->outputs=0;
    s->reason=s->configuration==IP_GROUND_TEST?(mode==IP_SAFE?"GROUND_SAFE_COMMAND":"GROUND_SIMULATION_COMMAND"):"GROUND_SAFE_COMMAND";
    return NULL;
}
