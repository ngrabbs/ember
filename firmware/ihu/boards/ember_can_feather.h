#ifndef EMBER_CAN_FEATHER_H
#define EMBER_CAN_FEATHER_H
// pico_cmake_set PICO_PLATFORM=rp2040
// Explicit CAN Feather mappings; SDK's ordinary Feather SPI/NeoPixel differ.
#define PICO_DEFAULT_UART 0
#define PICO_DEFAULT_UART_TX_PIN 0
#define PICO_DEFAULT_UART_RX_PIN 1
#define PICO_DEFAULT_LED_PIN 13
#define PICO_DEFAULT_WS2812_PIN 21
#define PICO_DEFAULT_SPI 1
#define PICO_DEFAULT_SPI_SCK_PIN 14
#define PICO_DEFAULT_SPI_TX_PIN 15
#define PICO_DEFAULT_SPI_RX_PIN 8
#include "boards/adafruit_feather_rp2040.h"
#endif
