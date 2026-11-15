# Comms KiCad project

[Comms home](../README.md) · [Open work](../TODO.md)

Open `transceiver.kicad_pro`. This is the current working all-UHF, single-antenna
project; the former “RX rebuild pending” description is superseded.

| File | Purpose |
|---|---|
| `transceiver.kicad_pro` | Project configuration |
| `transceiver.kicad_sch` and child sheets | Schematic hierarchy |
| `transceiver.kicad_pcb` | Board layout |
| `transceiver.kicad_dru` | Project design rules |
| `lib/`, `sym-lib-table`, `fp-lib-table` | Project symbols, footprints, and library registration |

These files remain tracked.

Follow the [schematic guide](../design/schematic_guide.md),
[shared design rules](../../conventions/kicad_jlcpcb_design_rules.md), and
[RF layout guidance](../design/rf_layout_guidelines.md). Use KiCad/Konnect for design
changes. Prior CLI/native export discrepancies require native connectivity checks
before synchronizing the board.

Fabrication outputs belong in [releases](../releases/README.md).
