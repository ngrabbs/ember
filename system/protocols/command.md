# Command protocol

[System guide](../README.md) · [Data interfaces](../interfaces/data_interfaces.md)

**Draft: packet model and handling policy; encoding details pending.**

Proposed fields: **version byte → command ID → target subsystem → argument length →
arguments → sequence counter → CRC**. Remaining field widths, byte order, CRC parameters,
and concrete command IDs remain unspecified.

## Acceptance and execution

1. Comms decodes the uplink and forwards commands to IHU, the acceptance authority.
2. IHU requires a valid CRC and known schema; unknown commands return an explicit error.
3. Return an immediate transport ACK/NACK for validity, then an execution ACK/status
   after handling. Use bounded retries on timeout; limits remain to be defined.
4. Dispatch over the destination's [documented transport](../interfaces/board_to_board.md).
   Record safety-critical mode changes in the event log.

## Safe mode

Keep a minimal command set available; defer or reject nonessential commands.
Recovery commands require an explicitly verified acknowledgment path. The concrete
safe-mode command set remains open; see the [operations draft](../../docs/architecture/operations/README.md).
