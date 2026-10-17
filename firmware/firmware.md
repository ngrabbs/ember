# Firmware applications

| Application | Source and build guide | Runtime |
|---|---|---|
| IHU | [IHU firmware](ihu/README.md) | Pico SDK, CAN Feather; also builds the LTE CAN Feather role |
| COMMS | [COMMS firmware](comms/README.md) | Pico SDK, original Pico UHF transceiver |
| Payload | [Payload firmware](payload/README.md) | Payload Pi service |

Use the [IHU console guide](../docs/user/ihu-can-console.md) for commands,
[mode/output policy](../docs/architecture/operations/04-ihu-runtime-policy.md)
for implemented behavior, and [system interfaces](../system/README.md) for
protocol contracts. Full flight routines remain inactive stubs.

The earlier FreeRTOS applications, vendored kernel and legacy-only build/test
support were removed. They remain available in
[Git history](https://github.com/ngrabbs/ember/tree/e133cf204a10ed47e703e5e5a81f17a4241268de/firmware).
The shared LTC4162 register header remains because the active IHU uses it.
