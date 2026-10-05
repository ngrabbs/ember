# Message protocols

[System guide](../README.md)

The lab has implemented wire contracts; the mission application and flight
transport definitions remain drafts.

| Need | Owning reference |
|---|---|
| Bench packet IDs, fields, CRC, transactions and results | [EMBER bench v1](ember_bench_v1.md), generated from [dictionary.json](../../ground/ember/dictionary.json) |
| Real EPS readout, quality and native/wrapper provenance | [EPS POWER_STATUS v1](eps_power_status_v1.md) |
| Mission command validation and dispatch intent | [Command draft](command.md) |
| Mission telemetry field groups and framing intent | [Telemetry draft](telemetry.md) |
| Operator use of implemented commands | [User guides](../../docs/user/README.md) |

Transport roles are defined in the [bus architecture](../interfaces/board_to_board.md).
