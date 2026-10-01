# System interfaces and integration

[Documentation home](../docs/README.md)

Use these documents when two subsystems must agree. The **CSKB pin map is
canonical**; protocol layouts, timing targets, and integration gates remain drafts
unless explicitly marked otherwise. Allocation does not imply implementation.

| Need | Reference |
|---|---|
| Connector pin, signal name, or board direction | [CSKB pin map](interfaces/cskb_pinmap.md) |
| Connector part or stack spacing | [CSKB mechanical reference](interfaces/cskb_mechanical.md) |
| Which bus to use | [Board-to-board architecture](interfaces/board_to_board.md) |
| IHU/comms ownership, signals, and timing | [IHU–comms interface](interfaces/comms_to_ihu.md) |
| Power rails and load boundaries | [Power interfaces](interfaces/power_interfaces.md) |
| Data ownership and buffering | [Data interfaces](interfaces/data_interfaces.md) |
| Command acceptance and acknowledgments | [Command protocol](protocols/command.md) |
| Telemetry fields and error checks | [Telemetry protocol](protocols/telemetry.md) |
| Bring-up order and gates | [Integration plan](integration/integration_plan.md) |
| Integrated verification coverage | [System tests](integration/system_tests.md) |

For spacecraft behavior, use the [operations draft](../docs/architecture/operations/README.md).
Board implementation belongs in [hardware](../docs/architecture/hardware_overview.md);
shared assignments belong here.
