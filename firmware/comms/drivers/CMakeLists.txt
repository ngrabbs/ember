cmake_minimum_required(VERSION 3.13)

# Pull in Pico SDK (set PICO_SDK_PATH environment variable)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(si5351a_bringup C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(si5351a_bringup
    si5351a_bringup.c
    si5351a.c
)

target_link_libraries(si5351a_bringup
    pico_stdlib
    hardware_i2c
)

# Enable USB serial output (disable UART since we're using USB)
pico_enable_stdio_usb(si5351a_bringup 1)
pico_enable_stdio_uart(si5351a_bringup 0)

# Generate UF2 for drag-and-drop flashing
pico_add_extra_outputs(si5351a_bringup)
