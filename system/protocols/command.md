# Command protocol

[System guide](../README.md) · [Data interfaces](../interfaces/data_interfaces.md)

Application meanings are owned by the merged
[operations dictionaries](../../docs/architecture/operations/Ground_Operations_Command_Telemetry/README.md).
The [bench v1 contract](ember_bench_v1.md) defines the initial host codec.
Flight framing and authorization remain unresolved; see the
[coordination note](../ground_station/dustin_followup.md).

**Legacy flight draft below; use bench v1 for the lab implementation.**

Proposed fields: **version byte → command ID → target subsystem → argument length →
arguments → sequence counter → CRC**. Remaining field widths, byte order, CRC parameters,
and concrete command IDs remain unspecified.

## Acceptance and execution

1. Comms decodes the uplink and forwards commands to IHU, the acceptance authority.
2. IHU requires a valid CRC and known schema; unknown commands return an explicit error.
3. Distinguish transport delivery from IHU acceptance ACK/NACK and execution
   results. A timeout means the outcome is unknown. Draft 0.2 uses manual resend
   after status verification for state-changing commands; automatic retries
   are not enabled. Correlation and duplicate/reset rules need final definition.
4. Dispatch over the destination's [documented transport](../interfaces/board_to_board.md).
   Record safety-critical mode changes in the event log.

## Safe mode

Keep a minimal command set available; defer or reject nonessential commands.
Recovery commands require an explicitly verified acknowledgment path. The concrete
safe-mode command set remains open; see the [operations draft](../../docs/architecture/operations/README.md).
