#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#define GPIO_OUT 1
#define GPIO_FUNC_I2C 3
#define PICO_ERROR_TIMEOUT -1
#define PICO_UNIQUE_BOARD_ID_SIZE_BYTES 8
#define i2c1 1
uint32_t get_absolute_time(void);
static inline uint32_t to_ms_since_boot(uint32_t t){return t;}
static inline bool stdio_usb_connected(void){return true;}
static inline void stdio_init_all(void){}
static inline void pico_get_unique_board_id_string(char *p,size_t n){if(n)*p=0;}
static inline uint32_t get_rand_32(void){return 123;}
static inline void gpio_init(int p){(void)p;}
static inline void gpio_set_dir(int p,int d){(void)p;(void)d;}
static inline void gpio_set_function(int p,int f){(void)p;(void)f;}
static inline void gpio_pull_up(int p){(void)p;}
static inline void gpio_put(int p,bool b){(void)p;(void)b;}
static inline void i2c_init(int p,int b){(void)p;(void)b;}
int i2c_write_timeout_us(int p,int a,const uint8_t*b,size_t n,bool s,int t);
int i2c_read_timeout_us(int p,int a,uint8_t*b,size_t n,bool s,int t);
int getchar_timeout_us(int timeout);
int putchar_raw(int ch);
static inline void tight_loop_contents(void){}
void watchdog_reboot(uint32_t pc,uint32_t sp,uint32_t delay);
void watchdog_update(void);
void watchdog_enable(uint32_t delay,bool debug);
typedef struct {uint32_t scratch[8];} mock_watchdog_hw;
extern mock_watchdog_hw mock_watchdog;
#define watchdog_hw (&mock_watchdog)
