# Command Protocol

## Scope

Define uplink command packet format, parsing behavior, and safety checks.

## Provisional Packet Model

- Version byte
- Command ID
- Target subsystem ID
- Argument length
- Arguments
- Sequence counter
- CRC

## Validation Policy (Provisional)

- IHU is authority for command acceptance/rejection decisions
- Commands require valid CRC and known schema version
- Unknown command IDs are rejected with explicit error code

## Command Acknowledgment Model

- Immediate transport ACK/NACK for packet validity
- Execution ACK with status code after command handling completes
- Timeout handling with bounded retries

## Transport Mapping

- Uplink commands are decoded by comms and forwarded to IHU
- IHU dispatches inter-board commands over SPI and/or CAN by destination
- Safety-critical mode-change commands are mirrored in event log

## Safe-Mode Command Handling

- Minimal command set remains active in safe mode
- Non-essential commands are deferred or rejected while in safe mode
- Recovery commands require explicit ACK path verification
