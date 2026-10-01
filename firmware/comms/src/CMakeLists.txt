# Comms board application binary.
#
# Layout:
#   src/main.c               entry point + task creation
#   src/config/pinmap.h      board pin assignments (see schematic_guide.md rev 0.9)
#   src/tasks/*.{c,h}        FreeRTOS task implementations
#   ../drivers/*.{c,h}       chip drivers, shared with the standalone
#                            bench apps that also live in ../drivers/
#   ../../shared/*.h         wire protocols shared with firmware/ihu

set(COMMS_DRIVERS_DIR ${CMAKE_CURRENT_LIST_DIR}/../drivers)
set(EMBER_SHARED_DIR ${CMAKE_CURRENT_LIST_DIR}/../../shared)

add_executable(${ProjectName}
    main.c
    tasks/selftest_task.c
    tasks/hk_slave_task.c
    tasks/console_task.c
    tasks/blink_task.c
    ${COMMS_DRIVERS_DIR}/si5351a.c
)

# Stdio on BOTH transports — the SDK fans printf out to every enabled
# driver, so the same boot report lands on whichever one you have hooked
# up, and on both at once if you have both.
#
#   USB CDC  — the Pico module's own micro-USB, which the schematic guide
#              calls the primary programming and debug interface for the
#              prototype. Enumerates as /dev/ttyACM0.
#   UART0    — GP0 (TX) / GP1 (RX), 115200 8N1. Unassigned on the comms
#              schematic and brought out on the spare GPIO header, so it
#              stays available on the populated board and keeps working
#              when USB is busy re-flashing or the host has dropped it.
#              adapter RX <- GP0 (pin 1), TX -> GP1 (pin 2), GND <-> GND
#
# The IHU runs UART-only because TinyUSB wants a FreeRTOS-aware config to
# avoid deadlocking during scheduler start. That is handled here: the
# kernel config sets configSUPPORT_PICO_SYNC_INTEROP and
# configSUPPORT_PICO_TIME_INTEROP, which is what the SDK needs to drive
# the TinyUSB device task from FreeRTOS, and nothing prints from an ISR.
pico_enable_stdio_usb(${ProjectName} 1)
pico_enable_stdio_uart(${ProjectName} 1)

# Cap how long a USB write may stall.
#
# pico_stdio_usb's writer busy-spins on tud_task() — it does not yield —
# for up to PICO_STDIO_USB_STDOUT_TIMEOUT_US whenever the CDC buffer is
# full and the host is not draining it. That is a host-not-listening
# case, which on a satellite is the normal case. At the SDK default of
# 500 ms per stalled 64-byte chunk, a board sitting with an enumerated
# but idle port spends most of its time in that spin, starving every
# lower-priority task.
#
# 100 ms is still far more than a real terminal needs to accept a chunk,
# and it bounds the damage when nothing is listening. The real fix for
# the TX path is not to printf from it at all.
target_compile_definitions(${ProjectName} PRIVATE
    PICO_STDIO_USB_STDOUT_TIMEOUT_US=100000
)

target_include_directories(${ProjectName} PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${COMMS_DRIVERS_DIR}
    ${EMBER_SHARED_DIR}       # comms_hk_proto.h — shared with firmware/ihu
    ${CMAKE_SOURCE_DIR}            # makes FreeRTOSConfig.h visible to the kernel
)

target_link_libraries(${ProjectName}
    pico_stdlib
    pico_unique_id          # board id in the boot banner
    hardware_i2c            # Si5351A (master) + IHU housekeeping link (slave)
    pico_i2c_slave          # IRQ-driven I2C slave for the housekeeping link
    hardware_spi            # IHU link; pins declared in pinmap.h, not yet driven
    hardware_gpio
    hardware_adc            # RX baseband DC bias check
    hardware_watchdog       # reset-reason reporting
    FreeRTOS-Kernel-Heap4
)

# Generate .uf2, .bin, .hex, .elf, .map alongside the binary.
pico_add_extra_outputs(${ProjectName})
