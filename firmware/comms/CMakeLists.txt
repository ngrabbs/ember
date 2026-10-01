cmake_minimum_required(VERSION 3.13)

# Project name — also used as the binary basename (comms.uf2 etc.)
set(ProjectName comms)

# FreeRTOS kernel. The submodule currently lives under the IHU tree
# (firmware/ihu/lib/FreeRTOS-Kernel); both boards are RP2040 and run the
# same kernel version on purpose, so rather than carry a second checkout
# we point at that one by default.
#
# Override order:
#   1. -DFREERTOS_KERNEL_PATH=... or the FREERTOS_KERNEL_PATH env var
#   2. lib/FreeRTOS-Kernel here, if someone adds the submodule locally
#   3. ../ihu/lib/FreeRTOS-Kernel
if(NOT FREERTOS_KERNEL_PATH AND DEFINED ENV{FREERTOS_KERNEL_PATH})
    set(FREERTOS_KERNEL_PATH $ENV{FREERTOS_KERNEL_PATH})
endif()
if(NOT FREERTOS_KERNEL_PATH)
    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/lib/FreeRTOS-Kernel/CMakeLists.txt)
        set(FREERTOS_KERNEL_PATH ${CMAKE_CURRENT_SOURCE_DIR}/lib/FreeRTOS-Kernel)
    else()
        set(FREERTOS_KERNEL_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../ihu/lib/FreeRTOS-Kernel)
    endif()
endif()
get_filename_component(FREERTOS_KERNEL_PATH ${FREERTOS_KERNEL_PATH} ABSOLUTE)

if(NOT EXISTS ${FREERTOS_KERNEL_PATH}/CMakeLists.txt)
    message(FATAL_ERROR
        "FreeRTOS kernel not found at ${FREERTOS_KERNEL_PATH}.\n"
        "Run 'git submodule update --init --recursive' from the repo root, "
        "or pass -DFREERTOS_KERNEL_PATH=/path/to/FreeRTOS-Kernel.")
endif()
message(STATUS "FreeRTOS kernel: ${FREERTOS_KERNEL_PATH}")

# Pico SDK locator (uses PICO_SDK_PATH env var, or fetches from GitHub if
# PICO_SDK_FETCH_FROM_GIT=ON is also set).
include(pico_sdk_import.cmake)

# FreeRTOS RP2040 port — must be included before project() so port-specific
# toolchain settings are picked up.
include(${FREERTOS_KERNEL_PATH}/portable/ThirdParty/GCC/RP2040/FreeRTOS_Kernel_import.cmake)

project(${ProjectName} C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

# Application sources live under src/
add_subdirectory(src)
