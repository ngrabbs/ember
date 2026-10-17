# Walter MCU firmware

This application runs on the **Adafruit RP2040 CAN Bus Feather on the LTE
board**. It receives IHU requests over CAN and controls Walter's ESP32-S3
application over framed UART. Walter's own firmware lives in
[`firmware/walter`](../walter/README.md); the IHU lives in
[`firmware/ihu`](../ihu/README.md), and UHF uses
[`firmware/transceiver`](../transceiver/README.md).

```text
IHU (ihu) -- CAN --> LTE Feather (walter_mcu) -- UART --> Walter (walter)
```

## Build and identity

From the repository root, with Pico SDK and ARM GCC available:

```sh
cmake -S firmware/walter_mcu -B build/walter_mcu -DPICO_SDK_PATH="$PICO_SDK_PATH" \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build build/walter_mcu --target walter_mcu -j4
# build/walter_mcu/walter_mcu.uf2
# build/walter_mcu/walter_mcu.elf
```

CMake project, target, program name and artifact basename are all `walter_mcu`.
USB `version`/`status` reports `role=WALTER_MCU`, version, source SHA, dirty flag
and boot identity. This application owns its VERSION file; the source split
retains 0.14.1 from the former combined project. There is no ROLE_IHU build
switch and no IHU source dependency. Start with a fresh build directory.

The former `ember_comms_can_bench.uf2` was this Feather's image and reported
`LTE_CAN_MCU`. Historical deployments/evidence retain those names. Verify the
physical board's USB unique ID before flashing; Raspberry Pi Pico USB product
names alone do not distinguish the Feathers. This source split does not flash
or change the deployed firmware.

## Transport and startup

- CAN remains 500 kbit/s: requests `0x720`, replies `0x721`; presence node 3
  answers on `0x703`. CAN enters normal mode at boot when initialization succeeds.
- UART0 GPIO0 TX / GPIO1 RX stays 115200 8N1 with no hardware flow control.
  See [transport wiring/history](../../system/interfaces/comms_walter.md).
- Requests retain boot/request correlation, payload validation, one active
  UART chain, bounded timeouts and no automatic retry. Walter HELLO precedes
  the operation when its boot identity is unknown.
- Services include diagnostic echo, native packet echo, firmware identity,
  modem firmware identity, bounded RF window, LTE packet submission, link
  status and diagnostics. Modem acceptance does not establish ground receipt.
- Boot starts no RF window or periodic telemetry. The IHU retains its existing
  LTE output permission and explicit command flow (`hello lte`, `lte status`,
  `lte firmware`, `lte modem firmware`, `lte N`, `heartbeat lte`, etc.). CAN
  message types and telemetry dictionary names retain their LTE names.

## USB diagnostics

`help`, `version`, `status`, `selftest`, `normal`, `hello`, and `ping N`
(`N=1..240`) are the existing case-sensitive console commands. `selftest` is
local MCP loopback; `normal` restores normal CAN mode. The USB HELLO/ping
request behavior is retained from the former combined application; operational
LTE requests originate on IHU. Forwarding CAN/UART traffic does not require a USB console connection.

Shared protocols and MCP25625 driver live in
[`comms_transport`](../comms_transport/README.md); shared board/identity build
support lives in [`shared/pico_can`](../shared/pico_can/README.md).
