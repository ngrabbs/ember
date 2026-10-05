# System integration plan

[System guide](../README.md) · [System tests](system_tests.md)

**Status: integration plan updated 2026-10-04; bench demonstrations and future
gates are separate.** Single-bus CAN is the selected implemented bench packet
transport. SPI is an older hardware allocation, not a prerequisite for CAN.

| Work | Recorded evidence | Remaining gate |
|---|---|---|
| EPS standalone | [Rev A bring-up](../../hardware/eps/bringup/phase1_validation.md) | Complete power/protection/load acceptance; Rev B work is a separate design workstream |
| IHU–EPS I2C | [UART/Yamcs validation](../ground_station/eps_yamcs_setup.md); [CAN Feather EPS reads](../../firmware/can_feather_bench/README.md) | Sense resistor verification, thermistor setup, bus stress and recovery |
| Command/response bench | [USB endpoint validation](../ground_station/usb_validation.md) | Integrate flight command authorization/dispatch into the actual IHU application |
| IHU–COMMS CAN | [Single-bus Feather transport](../../firmware/can_feather_bench/README.md) | Production runtime integration, reset/fault recovery and sustained traffic |
| Native EPS downlink | [LTE evidence](../../ground/lte/README.md) | Reliability/endurance, calibrated RF performance, UHF integration and operational recovery |
| Command uplink over RF | No implemented Yamcs LTE/UHF telecommand link | Define, implement and validate reception, authorization, dispatch and correlated results |
| Payload and CAN A/B | Proposed architecture | Multi-node arbitration, failed-node containment and independently qualified failover |

Recorded results apply only to their stated hardware/software configurations.
Before executing a new gate, define conditions and measurable limits in
[system tests](system_tests.md), then record results in the [test workspace](../../test/README.md).
The [bus plan](../interfaces/board_to_board.md) owns transport roles.
