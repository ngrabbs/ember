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
| Stack data | IHU–comms SPI plus housekeeping I2C and control/status signals |
| Future control | CAN A/B assigned for Iteration 2 in the system pin map; allocation does not imply board implementation |

The low-power ADL5602 TX architecture is selected; a 1–2 W redesign is outside
this baseline. Actual antenna power, spectral purity, receive performance, and
mismatch tolerance need measurement.

**Unresolved component work:** U9 replacement, its L16 bias network, D15 protection,
and J9 mechanical acceptance. TQP3M9036 is a U9 candidate only; do not describe it
as installed. Filter tuning candidates likewise remain unapplied.

Use the [TX](tx_chain.md), [RX](rx_chain.md), and
[antenna](single_antenna_integration.md) pages for circuit boundaries, and the
[canonical CSKB map](../../../system/interfaces/cskb_pinmap.md) for stack pins.
The [verification index](../verification/README.md) distinguishes earlier check
results from work still needed before release.
