# Data interfaces

[System guide](../README.md) · [Bus architecture](board_to_board.md)

**Status: ownership baseline; queue sizes and packet contracts are provisional.**
Comms forwards received commands to the IHU. IHU validates and routes them, then
assembles system state and payload data for downlink through comms.

| Owner | Responsibility |
|---|---|
| IHU | Command acceptance/sequencing, subsystem dispatch, system telemetry |
| Comms | RF framing/modulation and uplink/downlink transport |
| EPS | Charger and rail-health observability fields |
| Payload | Mission data and payload status |

Use I2C and alert GPIO for EPS housekeeping, SPI for IHU–comms data, and planned
CAN A/B for Iteration 2 control/status. Pin assignments live in the
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
