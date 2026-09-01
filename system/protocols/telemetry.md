# Telemetry Protocol

## Scope

Define baseline telemetry framing, field mapping, and downlink transport.

## Provisional Frame Model

- Version byte
- Message type
- Source subsystem ID
- Sequence counter
- Payload length
- Payload
- CRC

## Transport Mapping (Provisional)

- RF downlink framing handled by communications subsystem
- Inter-board transport:
  - SPI for IHU <-> comms telemetry transfer
  - CAN for subsystem status broadcast in Iteration 2

## Field Groups

- EPS: rail voltages, battery state, charger status, thermal indicators
- Comms: TX/RX mode, queue depth, fault flags, RSSI-like receive metrics
- IHU: mode state, reset reason, watchdog events, uptime
- Payload: status and selected science/experiment metadata

## Error Control

- Link-level checksums on inter-board packets
- End-to-end CRC on telemetry frame payload
- Sequence counter to detect drops/reordering

## Versioning Strategy

- Semantic telemetry schema version in frame header
- Backward-compatible field extension by TLV or reserved-field policy
