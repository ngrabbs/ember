# Telemetry protocol

[System guide](../README.md) · [Data interfaces](../interfaces/data_interfaces.md)

**Draft: field groups and framing intent; encoding details pending.**

Proposed fields: **version byte → message type → source subsystem → sequence counter →
payload length → payload → CRC**. Remaining field widths, byte order, units, and CRC
parameters still need definition.

| Source | Field group |
|---|---|
| EPS | Rail voltages, battery state, charger status, thermal indicators |
| Comms | TX/RX mode, queue depth, faults, receive metrics such as RSSI |
| IHU | Mode, reset reason, watchdog events, uptime |
| Payload | Status and selected science/experiment metadata |

IHU–comms telemetry uses SPI; Iteration 2 CAN carries subsystem status.
Comms owns RF downlink framing. Apply link-level packet checksums, an end-to-end
payload CRC, and a sequence counter for drops/reordering.

**Versioning proposal:** a semantic schema version in the header, with compatible
extensions using TLV or reserved fields. The original “version byte” framing
and semantic-version representation need reconciliation; neither encoding nor
extension policy is finalized.
