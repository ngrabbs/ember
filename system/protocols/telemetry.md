# Telemetry protocol

Use the [bench v1 dictionary](ember_bench_v1.md) for initial lab packets.
The live `ember` Yamcs instance uses that subset alongside the upstream
`myproject` demonstration. The flight proposal below is not yet reconciled.

[System guide](../README.md) · [Data interfaces](../interfaces/data_interfaces.md)

Application meanings are owned by the merged
[operations dictionaries](../../docs/architecture/operations/Ground_Operations_Command_Telemetry/README.md).
The framing proposals below remain unresolved; see the
[coordination note](../ground_station/dustin_followup.md).

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

The FreeRTOS IHU–COMMS application has an I2C status/ping jumper link. The
separate CAN Feather bench implements packet forwarding, with native EPS
telemetry delivery recorded over Walter LTE-M. SDRB UHF is a separate local
workstream whose source/configuration is not included in this branch. Production
application integration and CAN A/B remain open; see the
[integration checklist](../interfaces/comms_walter.md). COMMS owns external
link framing. Apply link-level packet checksums, an end-to-end
payload CRC, and a sequence counter for drops/reordering.

**Versioning proposal:** a semantic schema version in the header, with compatible
extensions using TLV or reserved fields. The original “version byte” framing
and semantic-version representation need reconciliation; neither encoding nor
extension policy is finalized.
