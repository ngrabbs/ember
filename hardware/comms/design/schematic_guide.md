# Comms schematic guide

[Design guide](README.md) · [KiCad project](../kicad/README.md)

Use the saved KiCad project for component connectivity and the
[canonical CSKB pin map](../../../system/interfaces/cskb_pinmap.md) for shared
signals. This page is a sheet guide; the earlier step-by-step construction
instructions contained superseded VHF, package, and power assumptions.

| Sheet | Circuit | Reference |
|---|---|---|
| Overview | Project hierarchy and block summary | [Design overview](overview.md) |
| Clock Gen | Si5351A, crystal, clock outputs | [TX](tx_chain.md) / [RX](rx_chain.md) |
| TX Chain | BPSK, tripler, filters, ADL5602 | [TX chain](tx_chain.md) |
| RX Chain | UHF filter, LNA, ADE-1+, baseband | [RX chain](rx_chain.md) |
| Power | Stack rails and protection | [System power](../../../system/interfaces/power_interfaces.md) |
| Digital Control | RP2040, modulation/sampling and control | [Firmware roadmap](../../../firmware/firmware.md) |
| Connectors (legacy Sheet 7) | Stack, debug, and antenna interfaces | [CSKB pin map](../../../system/interfaces/cskb_pinmap.md) |
| RF Switch | Shared antenna, protection, 3.0 V supply/buffer | [Single antenna](single_antenna_integration.md) |

## Rules and evidence

- Stack signals follow the canonical map; local signals follow
  [net-naming conventions](../../conventions/net_naming.md).
- Use the [shared fabrication/impedance rules](../../conventions/kicad_jlcpcb_design_rules.md)
  and [RF layout guide](rf_layout_guidelines.md).
- Consult [component audits](../verification/README.md) for exact pin/package maps;
  accepted mapping does not establish RF performance or mechanical stack clearance.
- Verify native schematic connectivity before synchronizing the PCB. Prior tooling
  records identify a CLI/native hierarchy discrepancy; don't delete apparent
  orphan circuitry from a partial export.
- J6/J7/J8 remain identical DNP headers. H3/H4 are the board references for the
  stack sockets; use the [alignment record](../verification/components/cskb_alignment_verification.md)
  for their saved physical placement and the system map for logical assignments.

Open annotation, substitution, sourcing, and validation work lives in
[TODO](../TODO.md). This cleanup changed documentation only, not the circuit.
