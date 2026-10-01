# Payload Hardware

## Layout

- `design/`: payload design concepts and constraints
- `kicad/`: payload board source files — the Altium project converted to KiCad 10
- `altium/`, `altium-carlos/`: local-only Altium sources — **not tracked**
- `bringup/`: validation plans and logs
- `releases/`: build-ready release packages

## Board source status

`kicad/cubesat_orin_nano_carrier` is the converted Jetson Orin Nano carrier:
87 footprints, a flat 4-page schematic (root + `Cameras`, `M2_USB_UART`,
`SODIMM_Power`), 650 track segments — mostly the PCIe escape from J1. Board
design in this repo is KiCad-only per
[`hardware/conventions/kicad_jlcpcb_design_rules.md`](../conventions/kicad_jlcpcb_design_rules.md);
the Altium trees are kept locally as the conversion source and are ignored by
git (see the Altium block in the root `.gitignore`).

## Mechanical — CSKB / PC/104 envelope

The outline, mounting holes and H1/H2 positions are held **identical** to
`AMSAT/sdrb/hardware/pcb-variants/sdrb-cskb`, which is the reference that was
corrected to spec. Geometry is that board's Edge.Cuts translated by
`(+14.6103, -16.3164)` mm into this board's frame, so the two match exactly.

- Outline: 24 primitives, one closed loop, every endpoint used exactly twice,
  **95.8850 x 90.1800 mm**. X is exactly the CSK Slot1 profile; Y is 0.010 mm
  over the spec's 90.170, matching the reference.
- Mounting holes, inset from the nearest edges:

  | | left | right | top | bottom |
  | --- | --- | --- | --- | --- |
  | MH1 | 90.8050 | **5.0800** | **5.0900** | 85.0900 |
  | MH2 | **5.0800** | 90.8050 | 7.6300 | 82.5500 |
  | MH3 | **5.0800** | 90.8050 | 81.2900 | 8.8900 |
  | MH4 | 90.8050 | **5.0800** | 85.1000 | **5.0800** |

- CSKB connectors: H1 pin 1 at `(113.2136, 136.1236)`, H2 pin 1 at
  `(108.1336, 136.1236)`, both rotation -90. Pad rows sit **5.0800 / 7.6200 /
  10.1600 / 12.7000 mm** from the left board edge — the same four values as the
  reference. H1 to H2 pitch is 5.08 mm (0.2").

A bad outline fails silently — KiCad falls back to the bounding box and fab
output loses the notches. Re-run the closed-loop check after any outline edit.
