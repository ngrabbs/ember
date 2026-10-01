cmake_minimum_required(VERSION 3.13)
if(NOT PICO_SDK_PATH)
    set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
endif()
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(ember_usb_bench C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
execute_process(COMMAND ${Python3_EXECUTABLE}
    ${CMAKE_CURRENT_SOURCE_DIR}/../../ground/ember/generate_c.py
    ${CMAKE_CURRENT_BINARY_DIR}/generated/wire.h
    RESULT_VARIABLE generated)
if(NOT generated EQUAL 0)
    message(FATAL_ERROR "Dictionary header generation failed")
endif()
add_executable(ember_usb_bench main.c protocol.c framing.c)
target_include_directories(ember_usb_bench PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/generated)
target_compile_options(ember_usb_bench PRIVATE -Wall -Wextra -Werror)
target_link_libraries(ember_usb_bench pico_stdlib pico_stdio_usb hardware_uart pico_rand)
pico_enable_stdio_usb(ember_usb_bench 1)
pico_enable_stdio_uart(ember_usb_bench 0)
target_compile_definitions(ember_usb_bench PRIVATE
    PICO_STDIO_USB_STDOUT_TIMEOUT_US=20000
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0)
pico_set_program_name(ember_usb_bench "EMBER USB Bench")
pico_set_program_version(ember_usb_bench "bench-v1")
pico_add_extra_outputs(ember_usb_bench)
