# System integration plan

[System guide](../README.md) · [System tests](system_tests.md)

**Draft sequence; gates are planned, not passed.**

| Order | Work | Gate |
|---|---|---|
| 1 | Validate EPS standalone | Board bring-up evidence |
| 2 | Integrate IHU–EPS I2C telemetry | A: reliable reads under nominal load |
| 3 | Integrate IHU–comms SPI | A: stable framing and recovery under nominal load |
| 4 | Close end-to-end command and telemetry loop over SPI | B: reliable command/response and downlink |
| 5 | Bring up CAN between IHU and comms | C: heartbeat and fault signaling |
| 6 | Add payload nodes; exercise CAN A/B | C: arbitration, failed-node behavior, and failover |

Before execution, define test conditions and measurable pass/fail limits in
[system tests](system_tests.md), then record results in the [test workspace](../../test/README.md).
Use the [bus plan](../interfaces/board_to_board.md) for iteration scope.
