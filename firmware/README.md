# Firmware

Build and operating instructions live with each application.

| Application | Guide | Changelog |
|---|---|---|
| IHU | [IHU](ihu/README.md) | [IHU changes](ihu/CHANGELOG.md) |
| UHF transceiver | [Transceiver](transceiver/README.md) | [Transceiver changes](transceiver/CHANGELOG.md) |
| Camera payload | [Payload](payload/README.md) | [Payload changes](payload/CHANGELOG.md) |
| LTE CAN-to-UART bridge | [Walter MCU](walter_mcu/README.md) · Adafruit RP2040 CAN Bus Feather | — |
| LTE-M telemetry app | [Walter](walter/README.md) · ESP32-S3 on the Walter module | — |

## Current bench builds

The [root hardware and firmware table](../README.md#hardware-and-firmware)
tracks bench and development versions.

## Walter LTE bench

| Component | Source on `main` | Last recorded bench app | Role |
|---|---|---|---|
| [Walter MCU](walter_mcu/README.md) | [0.14.1](walter_mcu/VERSION) | 0.8.0 | Receives IHU requests on CAN and bridges them to Walter over UART. |
| [Walter](walter/README.md) | [0.3.0](walter/VERSION) | 0.3.0 | Controls the onboard Sequans modem and sends native telemetry over LTE-M. |

Bench versions come from the [root bench record](../README.md#hardware-and-firmware).
The Sequans modem has its own firmware. See the
[LTE inventory](../ground/lte/INVENTORY.md) for its recorded AT identity and the
[Walter guide](walter/README.md#how-lte-telemetry-reaches-yamcs) for the path to
Yamcs `lte-tm-in`.

## Shared code

- [Communications transport](comms_transport/README.md) covers CAN fragmentation, device discovery, and UART framing.
- [Pico CAN configuration](shared/pico_can/README.md) supplies the board profile and build identity setup.
- [EMBER command engine](shared/ember_protocol/README.md) handles native commands and results.
- [LTC4162 register definitions](shared/ltc4162_registers.h) support IHU charger readout.
