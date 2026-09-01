cmake_minimum_required(VERSION 3.13)

# Project name — also used as the binary basename (ihu.uf2 etc.)
set(ProjectName ihu)

# FreeRTOS kernel lives as a git submodule under lib/FreeRTOS-Kernel.
# Run `git submodule update --init --recursive` from the repo root after cloning.
set(FREERTOS_KERNEL_PATH ${CMAKE_CURRENT_SOURCE_DIR}/lib/FreeRTOS-Kernel)

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
