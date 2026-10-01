#pragma once
#include <stdbool.h>
#define IHU_I2C0_LOCK_TIMEOUT_MS 1000
bool ihu_i2c0_lock(unsigned);
void ihu_i2c0_unlock(void);
