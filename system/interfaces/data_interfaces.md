# Data interfaces

[System guide](../README.md) · [Bus architecture](board_to_board.md)

**Status: ownership baseline; queue sizes and packet contracts are provisional.**
Comms forwards received commands to the IHU. IHU validates and routes them, then
assembles system state and payload data for downlink through comms.

| Owner | Responsibility |
|---|---|
| IHU | Command acceptance/sequencing, subsystem dispatch, system telemetry |
| COMMS MCU | Packet queues, Walter/UHF transport selection, uplink/downlink forwarding and local radio control |
| EPS | Charger and rail-health observability fields |
| Payload | Mission data and payload status |

Use I2C for implemented EPS housekeeping; alert GPIO behavior remains proposed.
The FreeRTOS IHU–COMMS I2C jumper link provides status/ping only. The separate
CAN Feather bench implements single-bus packet forwarding, including framed
COMMS–Walter UART exchanges. Production CAN A/B integration remains open.
SPI is an older hardware allocation. See the
[integration contract and checklist](comms_walter.md). Pin assignments live in the
[canonical map](cskb_pinmap.md).

| Provisional queue | Minimum target |
|---|---|
| IHU commands | 16 entries |
| IHU outbound telemetry | 32 frames |
| Comms TX | 16 frames, with priorities |

On overflow, drop lowest-priority telemetry first; never safety alerts.
**Open:** final schemas/versioning, traffic priority map, and the cross-board
timestamp authority. See the draft [command](../protocols/command.md) and
[telemetry](../protocols/telemetry.md) contracts.
