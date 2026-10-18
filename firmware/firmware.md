# Firmware applications

| Application | Source and build guide | Runtime |
|---|---|---|
| IHU | [IHU firmware](ihu/README.md) | FreeRTOS 11.2.0 + Pico SDK candidate, IHU CAN Feather; target/output `ihu` |
| Walter MCU | [Walter MCU firmware](walter_mcu/README.md) | Pico SDK, LTE CAN Feather; target/output `walter_mcu` |
| Transceiver | [Transceiver firmware](transceiver/README.md) | Pico SDK, original Pico UHF transceiver |
| Walter | [Walter firmware](walter/README.md) | ESP32-S3, UART-controlled LTE-M modem |
| Payload | [Payload firmware](payload/README.md) | Payload Pi service |

Use the [IHU console guide](../docs/user/ihu-can-console.md) for commands,
[mode/output policy](../docs/architecture/operations/04-ihu-runtime-policy.md)
for implemented behavior, and [system interfaces](../system/README.md) for
protocol contracts. Full flight routines remain inactive stubs.

The earlier FreeRTOS applications, vendored kernel and legacy-only build/test
support were removed. They remain available in
[Git history](https://github.com/ngrabbs/ember/tree/e133cf204a10ed47e703e5e5a81f17a4241268de/firmware).
The shared LTC4162 register header remains because the active IHU uses it.

Shared dependencies:

- [`comms_transport`](comms_transport/README.md): CAN fragmentation, UART framing,
  correlation/discovery and the MCP25625 driver used across the active applications.
- [`shared/pico_can`](shared/pico_can/README.md): common CAN Feather board profile
  and build identity/dictionary configuration; each application owns its version.
- `shared/ltc4162_registers.h`: generated EPS register definitions used by IHU.
- [`shared/ember_protocol`](shared/ember_protocol/README.md): portable command engine
  linked by IHU and host tests.

The standalone USB endpoint, UART-only Feather/Walter diagnostics and `common`
placeholder were removed. Walter's active source is now under `walter`; use
PlatformIO environment `walter` and a fresh build directory after this move.
