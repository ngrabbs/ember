# Comms design overview

[Design guide](README.md) · [Open work](../TODO.md)

**Documented baseline:** 437 MHz BPSK transmitter, 435 MHz receiver, half duplex
through one UHF antenna at J9. The RP2040 controls the radio and exchanges commands
and telemetry with the IHU. This summary consolidates existing design records;
it does not claim fresh circuit verification or measured RF acceptance.

| Function | Documented implementation |
|---|---|
| Clock | Si5351A; CLK0 near 145.67 MHz for TX, CLK1 near 145 MHz for RX LO; tripling reaches UHF |
| TX | XOR BPSK → transistor tripler → filter → ADL5602 → output filter |
| RX | Input filter → PSA4-5043+ LNA → ADE-1+ mixer → MCP6022 baseband → RP2040 ADC |
| Antenna | PE4259 switch, common-port DC block and bidirectional ESD protection |
| Power | Stack +5V/+3V3; local 3.0 V switch supply |
| Stack data | CAN A/B through two MCP25625 controllers; shared Pico SPI0 master with separate CS/IRQ/reset/standby |
| Layout status | Routing complete; DRC 0 errors / 0 unconnected; firmware port and final fabrication checks remain open |

The low-power ADL5602 TX architecture is selected; a 1–2 W redesign is outside
this baseline. Actual antenna power, spectral purity, receive performance, and
mismatch tolerance need measurement.

**Prototype parts selected:** L16 0805HP-221XGRC / C40877572, D15
PESD5V0F1BLD,315 / C478204, J9 Molex 734151471 / C588477. J9 clearance is
confirmed. Retain the audited PSA4-5043+ at U9; October 3 live stock makes the
TQP3M9036 replacement unnecessary. [Acceptance and operating limits](../verification/components/prototype_parts_2026-10-03.md)
retain L16 stability/bias and D15 RF-voltage checks for bench bring-up.
Filter tuning candidates remain unapplied.

Use the [TX](tx_chain.md), [RX](rx_chain.md), and
[antenna](single_antenna_integration.md) pages for circuit boundaries, and the
[canonical CSKB map](../../../system/interfaces/cskb_pinmap.md) for stack pins.
The [verification index](../verification/README.md) distinguishes earlier check
results from work still needed before release.
