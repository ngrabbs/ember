# Firmware applications

| Application | Source and build guide | Runtime |
|---|---|---|
| IHU | [IHU firmware](ihu/README.md) | Pico SDK, IHU CAN Feather; target/output `ihu` |
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

For new telemetry, follow the [developer walkthrough](../docs/architecture/telemetry_data_flow.md).
See [firmware research](../docs/research/firmware_references.md) for RTOS background.

## Current bench builds

Checked 2026-11-14 against `main` at `f2788aa`. Use the version and source
commit together when recording a test. The `main` versions are the merged
source baseline. Use the bench column to identify which features and test
results apply to the hardware.

| Firmware | Version on `main` | Bench identity and purpose |
|---|---|---|
| [IHU](ihu/CHANGELOG.md) | 0.14.1 | **Live: 0.26.0 · `af0925a`.** The USB console reported a clean build. This is the startup and UHF demo build for scheduled telemetry, GPS, and coordination of payload fire checks. |
| [Transceiver](transceiver/CHANGELOG.md) | 0.34.0 | **Running commit unconfirmed.** The November 5 flash record identifies 0.37.2 at `14243dc`, used for the bench UHF link. The November 12 receive experiments share version 0.37.2. The November 14 sweep logs verify restoration of the pre-sweep image without identifying its commit. |
| [Payload](payload/CHANGELOG.md) | 0.2.0 | **Running version unconfirmed.** The October 17 Yamcs identity is 0.1.0 at `c6be5ab`. A later boot reported payload status without a version. The 0.7.0 branch adds capture GPS evidence for the live camera fire-check workflow. |

The IHU identity came from the m75q USB console. Transceiver restore evidence
is on m75q under `~/work/tx-sweep-20261114/`. The documented payload SSH
address currently reaches the SatNOGS host.

## Shared dependencies

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
