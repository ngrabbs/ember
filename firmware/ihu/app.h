#pragma once
#include <stdbool.h>
/* Only the application task calls these entry points. */
void ihu_app_init(void);
void ihu_app_command(const char *line);
void ihu_app_step(bool scheduled);
