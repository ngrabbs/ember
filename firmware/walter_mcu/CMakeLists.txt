cmake_minimum_required(VERSION 3.13)
if(NOT PICO_SDK_PATH)
    set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
endif()
set(PICO_BOARD ember_can_feather)
list(APPEND PICO_BOARD_HEADER_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/../shared/pico_can/boards)
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(walter_mcu C CXX ASM)
set(CMAKE_C_STANDARD 11)
include(../shared/pico_can/configure.cmake)
add_executable(walter_mcu main.c ../comms_transport/mcp25625.c)
target_include_directories(walter_mcu PRIVATE
    ../comms_transport ${CMAKE_CURRENT_BINARY_DIR}/generated ${CMAKE_CURRENT_BINARY_DIR})
target_compile_options(walter_mcu PRIVATE -Wall -Wextra -Werror)
target_link_libraries(walter_mcu pico_stdlib pico_unique_id pico_rand hardware_uart hardware_spi)
pico_enable_stdio_usb(walter_mcu 1)
pico_enable_stdio_uart(walter_mcu 0)
target_compile_definitions(walter_mcu PRIVATE
    PICO_STDIO_USB_STDOUT_TIMEOUT_US=20000
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0)
pico_set_program_name(walter_mcu "walter_mcu")
pico_set_program_version(walter_mcu "${FW_VERSION}")
pico_add_extra_outputs(walter_mcu)
