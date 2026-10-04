#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct { int unused; } i2c_inst_t;
int i2c_write_timeout_us(i2c_inst_t *, uint8_t, const uint8_t *, size_t, bool, uint32_t);
int i2c_read_timeout_us(i2c_inst_t *, uint8_t, uint8_t *, size_t, bool, uint32_t);
