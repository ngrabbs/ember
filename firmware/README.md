# Firmware

Build and operating instructions live with each application.

| Application | Guide | Changelog |
|---|---|---|
| IHU | [IHU](ihu/README.md) | [IHU changes](ihu/CHANGELOG.md) |
| UHF transceiver | [Transceiver](transceiver/README.md) | [Transceiver changes](transceiver/CHANGELOG.md) |
| Camera payload | [Payload](payload/README.md) | [Payload changes](payload/CHANGELOG.md) |
| LTE CAN Feather | [Walter MCU](walter_mcu/README.md) | — |
| LTE-M modem | [Walter](walter/README.md) | — |

## Current bench builds

The [root hardware and firmware table](../README.md#hardware-and-firmware)
tracks bench and development versions. For the November 15 source commits and
verification details, see the [dated bench record](https://github.com/ngrabbs/ember/blob/a237f01e8fd64fa45ac621644caaa3f1656ca779/firmware/README.md#current-bench-builds).

## Shared code

- [Communications transport](comms_transport/README.md) covers CAN fragmentation, device discovery, and UART framing.
- [Pico CAN configuration](shared/pico_can/README.md) supplies the board profile and build identity setup.
- [EMBER command engine](shared/ember_protocol/README.md) handles native commands and results.
- [LTC4162 register definitions](shared/ltc4162_registers.h) support IHU charger readout.
