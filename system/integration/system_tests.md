# System tests

[System guide](../README.md) · [Integration plan](integration_plan.md)

**Draft coverage list.** Procedures, numerical acceptance limits, and evidence
links still need definition; these rows do not record passing tests.

| Area | Required coverage |
|---|---|
| Power/reset | Startup, brownout, reset-safe outputs, and recovery |
| Telemetry | Transport integrity and complete end-to-end delivery |
| Commands | Reception, validation, execution, and acknowledgment |
| I2C | Consistent EPS reads under bus stress |
| SPI | Framing errors and timeout/recovery under sustained transfer |
| CAN | Multi-node arbitration, node offline, fault confinement, and bus recovery |
| CAN A/B | Inject a fault on each bus and verify the defined failover behavior |
| Operations | Mode transitions, inhibited actions, and persistent state across resets |

Start operations testing with the [tabletop and bench checks](../../docs/architecture/operations/02-transition-table.md#first-tabletop-and-bench-checks).
Each executable test needs setup, stimulus, expected result, pass/fail limits,
and a result record in the [test workspace](../../test/README.md).
