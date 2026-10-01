# IHU application binary.
#
# Layout:
#   src/main.c              entry point + task creation
#   src/config/pinmap.h     board pin assignments + chip config
#   src/config/i2c0_bus.*   shared housekeeping-bus lock (EPS + comms)
#   src/tasks/*.{c,h}       FreeRTOS task implementations
#   src/drivers/*.{c,h}     chip drivers — LTC4162 today, MR25H40/STWD100 later
#   src/cli/*.{c,h}         interactive command-line interface
#   ../../shared/*.h        wire protocols shared with firmware/comms

set(EMBER_SHARED_DIR ${CMAKE_CURRENT_LIST_DIR}/../../shared)

add_executable(${ProjectName}
    main.c
    tasks/console_task.c
    tasks/blink_task.c
    tasks/eps_monitor_task.c
    tasks/comms_monitor_task.c
    config/i2c0_bus.c
    drivers/ltc4162.c
    drivers/comms_link.c
    cli/cli.c
)

# Stdio over UART (GP0 TX, GP1 RX, 115200 8N1 by default).
#
# Use a USB-to-serial adapter:
#   adapter RX <- Pico GP0 (pin 1, TX)
#   adapter TX -> Pico GP1 (pin 2, RX)
#   adapter GND <-> Pico GND
#
# USB CDC stdio is intentionally disabled — TinyUSB needs a FreeRTOS-aware
# config and an OS abstraction to avoid deadlocks during scheduler start.
# We can revisit USB stdio in v0.2 once the rest of the stack is stable.
pico_enable_stdio_usb(${ProjectName} 0)
pico_enable_stdio_uart(${ProjectName} 1)

target_include_directories(${ProjectName} PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${EMBER_SHARED_DIR}            # comms_hk_proto.h — shared with firmware/comms
    ${CMAKE_SOURCE_DIR}            # makes FreeRTOSConfig.h visible to the kernel
)

target_link_libraries(${ProjectName}
    pico_stdlib
    hardware_i2c
    hardware_gpio
    hardware_watchdog       # cli 'reboot' command
    FreeRTOS-Kernel-Heap4
)

# Generate .uf2, .bin, .hex, .elf, .map alongside the binary.
pico_add_extra_outputs(${ProjectName})
