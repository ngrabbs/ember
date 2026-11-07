# Board interfaces

[System guide](../README.md) · [Canonical CSKB pin map](cskb_pinmap.md)

Use the table to identify the link, then open its reference for wiring and
limits. The CubeSat Kit Bus (CSKB) pin map owns stack pin assignments.

| Endpoints | Bus or signal | What crosses it | Status and reference |
|---|---|---|---|
| IHU ↔ EPS charger | I²C | Charger measurements and status | Bench readout. [EPS telemetry walkthrough](../../docs/user/lte-eps-walkthrough.md) |
| IHU ↔ payload Pi | CAN A, 500 kbit/s | Payload commands, replies, and status | Single-bus bench. [Payload interface and commands](../../docs/user/payload.md) |
| IHU → UHF COMMS board | CAN A | Native telemetry for UHF downlink | Bounded bench run. [Recorded packet matches](../ground_station/evidence/uhf-flight-20261017/result.json) |
| IHU ↔ Walter MCU | Classic CAN, 500 kbit/s | Telemetry packets and transport status | Single-bus LTE bench. [Walter transport](comms_walter.md) |
| Walter MCU ↔ Walter modem | Framed UART | Send requests with native packets and modem replies | LTE bench. [UART contract and wiring](comms_walter.md) |
| EPS → stack and payload carrier | CSKB `+5V`, `+3V3`, `VBAT` | Regulated stack supplies and battery feed to the payload's local converter | Documented rail allocation. [Power interfaces](power_interfaces.md) |
| IHU ↔ COMMS | I²C jumper / CSKB SPI | I²C housekeeping and ping / SPI stack signals | Earlier configurations. I²C bench only, SPI allocated. [IHU–COMMS interface](comms_to_ihu.md) |
| IHU ↔ subsystem controllers | Redundant CAN A/B | Planned command, telemetry, and fault transport | Redundancy and failover open. [Bus architecture](board_to_board.md) |
| Stack boards | CSKB H1/H2 | Board-to-board power and signal connections | [Connector mechanics and spacing](cskb_mechanical.md) |

See [data ownership](data_interfaces.md) for who produces and consumes each
message. For radio links to the ground, use the [radio guide](../../docs/comms/README.md).
