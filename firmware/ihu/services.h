#pragma once
#include <stdarg.h>
#include <stdio.h>
#include "mcp25625.h"
#include "gps.h"
#include "eps_diagnostics.h"
#include "../shared/ltc4162_registers.h"
enum ihu_sensor_op {IHU_SENSOR_READ_EPS, IHU_SENSOR_SET_ADC, IHU_SENSOR_READ_GPS, IHU_SENSOR_POLL_EPS};
typedef struct {
    ltc4162_raw_t raw;
    gps_result gps;
    bool ok,enable,health,between_gps_chunks;
    enum eps_error eps_error;
    uint8_t failed;
    uint16_t before,after;
    uint32_t sampled;
} ihu_sensor_result;
#ifdef IHU_HOST_TEST
/* Handler tests exercise the same application actor with deterministic I/O. */
#include "eps_readout.h"
#define ihu_can_init mcp_init
#define ihu_can_mode mcp_mode
#define ihu_can_send mcp_send
#define ihu_can_receive mcp_receive
#define ihu_can_poll_tx mcp_poll_tx
#define ihu_can_register mcp_register
static ihu_sensor_result host_sensor;
static bool host_sensor_ready,host_sensor_defer;
static inline bool ihu_sensor_submit(enum ihu_sensor_op op,bool enable){
    memset(&host_sensor,0,sizeof(host_sensor));host_sensor.enable=enable;
    if(op==IHU_SENSOR_READ_GPS)host_sensor.gps.status=GPS_NO_DATA;
    else if(op==IHU_SENSOR_SET_ADC)host_sensor.ok=eps_force_adc(enable,&host_sensor.before,&host_sensor.after);
    else {
        host_sensor.health=op==IHU_SENSOR_POLL_EPS;
        host_sensor.eps_error=eps_read(&host_sensor.raw,&host_sensor.failed);
        host_sensor.ok=host_sensor.eps_error==EPS_OK;
    }
    host_sensor.sampled=to_ms_since_boot(get_absolute_time());host_sensor_ready=true;return true;
}
static inline bool ihu_sensor_receive(ihu_sensor_result *r){
    if(!host_sensor_ready || host_sensor_defer)return false;
    *r=host_sensor;host_sensor_ready=false;return true;
}
static unsigned host_reboots;
static inline void ihu_reboot(void){++host_reboots;}
static inline void ihu_runtime_status(void){}
static inline void ihu_vprintf(bool reply,const char *fmt,va_list args){(void)reply;vprintf(fmt,args);}
#else
bool ihu_can_init(mcp_state *s);
bool ihu_can_mode(mcp_state *s,uint8_t mode);
bool ihu_can_send(mcp_state *s,const cf_frame *f);
bool ihu_can_receive(mcp_state *s,cf_frame *f);
void ihu_can_poll_tx(mcp_state *s,uint32_t now);
uint8_t ihu_can_register(uint8_t reg);
bool ihu_sensor_submit(enum ihu_sensor_op op,bool enable);
bool ihu_sensor_receive(ihu_sensor_result *r);
void ihu_vprintf(bool reply,const char *fmt,va_list args);
void ihu_runtime_status(void);
void ihu_reboot(void);
#endif
static inline void ihu_printf(bool reply,const char *fmt,...){
    va_list args;va_start(args,fmt);ihu_vprintf(reply,fmt,args);va_end(args);
}
