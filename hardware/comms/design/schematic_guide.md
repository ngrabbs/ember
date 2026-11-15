# Comms schematic guide

**KiCad work policy:** read the [shared schematic policy](../../conventions/kicad_schematic_policy.md) before building, editing, or reviewing. It governs wiring, page layout, labels, field presentation, library reuse, net classes, and electrical/visual acceptance. Existing names and revision-specific examples below remain design records; they do not authorize automatic net renaming or override the policy.

[Design guide](README.md) · [KiCad project](../kicad/README.md)

This page is a sheet guide; the earlier step-by-step construction
instructions contained superseded VHF, package, and power assumptions.

| Sheet | Circuit | Reference |
|---|---|---|
| Overview | Project hierarchy and block summary | [Design overview](overview.md) |
| Clock Gen | Si5351A, crystal, clock outputs | [TX](tx_chain.md) / [RX](rx_chain.md) |
| TX Chain | BPSK, tripler, filters, ADL5602 | [TX chain](tx_chain.md) |
| RX Chain | UHF filter, LNA, ADE-1+, baseband | [RX chain](rx_chain.md) |
| Power | Stack rails and protection | — |
| Digital Control | RP2040, modulation/sampling and control | [Firmware roadmap](../../../firmware/README.md) |
| Connectors (legacy Sheet 7) | Stack, debug, and antenna interfaces | — |
| RF Switch | Shared antenna, protection, 3.0 V supply/buffer | [Single antenna](single_antenna_integration.md) |

## Rules and evidence

- Stack signals follow the canonical map; local signals follow
  [net-naming conventions](../../conventions/net_naming.md).
- Use the [shared fabrication/impedance rules](../../conventions/kicad_jlcpcb_design_rules.md)
  and [RF layout guide](rf_layout_guidelines.md).
- Verify native schematic connectivity before synchronizing the PCB. Prior tooling
  records identify a CLI/native hierarchy discrepancy; don't delete apparent
  orphan circuitry from a partial export.

Open annotation, substitution, sourcing, and validation work lives in
[TODO](../TODO.md). This cleanup changed documentation only, not the circuit.
