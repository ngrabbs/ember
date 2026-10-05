# October 4 transceiver preview release

Fresh saved design reviewed, exported and uploaded October 4, 2026. **INCOMPLETE for unconditional production release; complete for the user-authorized draft quote/preview.** No order placed or paid.

## Current JLCPCB candidate

- New cart item **transceiver-preview-gerbers_Y24**, PCB prototype **Y24-9381059A**, assembly **SMT026100461688-9381059A**. Older Y23 remains in cart and is superseded.
- [Draft assembly preview](https://cart.jlcpcb.com/smt-order/?pcbFileNo=ccda5725e3f04ffebf3d45dc1c2eb2b8).
- Quote **$287.01** before shipping/tax: PCB $59.73 + Economic assembly $227.28. Five PCBs, two top assembled. All 144 placements selected; 56 exact LCSC part numbers matched without substitutions. Stock is not reserved.
- Contract observed in the current portal: four layers, 1.6mm, JLC04161H-7628, outer 1oz / inner 0.5oz, green mask / white silk, ENIG 1u", plugged vias, full flying-probe PCB test, no separate stencil order. Detected outline 95.97 x 90.18mm.
- Explicit impedance service **±10% (±5ohm at values <=50ohm)** selected, $33.08. This replaces the older draft's uncertain impedance service selection. RF construction is 0.358mm top traces referenced to L2 GND, 0.2104mm dielectric, nominal 1.1mm coplanar clearance.
- Production-file and parts-placement confirmation enabled; placement auto-confirm disabled. Prototype product description: research/education development board.
- Fabrication remark requests 50ohm controlled impedance, J9's five **finished 0.84 +/-0.05mm soldered PTHs**, and preservation of PC104 holes. J9 is not press-fit.

## Fresh design evidence

Source hashes are in `evidence/source-hashes.json`. Board SHA256: `e969c80d28f62171bb6eb9b52046d4ef295c5c81170a37aa8faf685d421b0742`.

- Native editor ERC: **0 errors**, two intentional MCP25625 library-copy warnings, four ignored tests explicitly listed in `evidence/native-erc.rpt`.
- Direct saved-board DRC: **0 errors, 0 unconnected**, one known fixed-H1/H2 silk warning. Konnect manufacturing validator reports READY only within its limited DRC/DFM scope.
- Independent eight-sheet review: [report](../../verification/review_20261004_final/independent-review.md). CLI ERC is unreliable for this hierarchy and is not used as release authority.
- Exact pin identity has one discrepancy: R39 terminals were reversed during schematic redraw. Both designs have the same nonpolar 100k resistor between the same nodes. Explicitly interchanging only R39.1/.2 produces **zero electrical connectivity mismatches**. This is documented equivalence, not an exact parity pass. Reconcile before future schematic-to-PCB synchronization.
- All analog/RF/clock traces remain on top; 1,020 track segments comprise 836 top and 184 bottom, none on inner layers. Inner Gerber fill regions are GND only. Rendered planes remain broad beneath the RF area with normal via/pad antipads, no signal-routing splits. This is geometric inspection, not EM qualification.

## Accepted exports and preview

`transceiver-preview-gerbers.zip` contains freshly generated 11 Gerber layers (four copper, two mask, two silk, two paste, outline), PTH/NPTH drill files and job file. All are nonempty. There are 456 plated drill hits: 271 x0.30mm, 8 x0.508mm, 5 x0.84mm, 64 x1.00mm, 104 x1.02mm, 4 x3.18mm. No NPTH hits are required. Outline has 24 connected line/arc elements with closed endpoints. Top/bottom, inner layers and paste were rendered and inspected in `preview/`.

`assembly/BOM.csv` and `assembly/CPL.csv` each cover 144 top placements. BOM uses embedded LCSC fields and MPN where present. Hand assembly/DNP/testpoint exclusions are listed in `evidence/assembly-exclusions.json`; headers and Pico remain user assembled. Placement coordinates and native rotations are unchanged from the prior reviewed candidate. JLC import initially deselected twenty C1525 capacitors; all twenty were explicitly selected, leaving all144 checked.

The same verified portal rotation corrections were reapplied: clockwise90 U1/U4/U5/U10/U11/Y2;180 U7/U8/U9/U12/U13/U14/Q3/Q4/Y1. Native CPL remains raw KiCad orientation; portal corrections belong to this draft. U1 and Y2 pin-one alignment visually checked; U15 pin-one marker remains upper-right, but its portal model is generic. Preview snapshots and quote/cart evidence are retained.

## Remaining before manufacturing approval

- Vendor CAM acceptance of exact RF construction/50ohm requirement and J9 finished-hole tolerance/soldering process.
- Vendor placement confirmation, particularly U15 RPW0010A custom pad/paste geometry and LED/diode polarity. These requests were saved in assembly remarks; a generic preview model cannot certify them.
- Recheck availability at checkout; priced/matched inventory is not a reservation. No silent substitutes permitted.
- Prototype bench qualification remains power-source margin, startup/protection/thermal behavior, CAN operation, and RF tuning/output spectrum/receiver performance. Current clean design-rule results do not certify radio performance.

Current authority: JLCPCB quote/assembly portal retrieved October4,2026; saved snapshots `evidence/jlc-bom.txt`, `jlc-quote.txt`, and `jlc-cart.txt`. Artifact hashes and sizes are in `manifest.json`. Previous releases are historical.
