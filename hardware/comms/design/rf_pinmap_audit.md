# PSA4-5043+ pin-map repair record

2026-09-09. Implemented through Konnect; not a fabrication release.

Manufacturer PSA4-5043+ datasheet: https://www.minicircuits.com/pdfs/PSA4-5043+.pdf
Manufacturer package drawing: 98-MMM Rev L, sheet 2, suggested land pattern; reviewed in manufacturer PDF mirrored at https://img.eecart.com/dev/file/part/spec/PSA4-5043%2B-Mini%20Circuits.pdf (page 28).

Component-side pattern rotated 90 degrees clockwise from the drawing. Coordinates in millimetres relative to footprint origin:

| Pad | Function | X | Y | Width | Height |
|---|---|---:|---:|---:|---:|
| 1 | RF OUT/DC | -1.10 | -0.65 | 0.95 | 0.50 |
| 2 | GND | -1.10 | 0.50 | 0.95 | 0.80 |
| 3 | RF IN | 1.10 | 0.65 | 0.95 | 0.50 |
| 4 | GND | 1.10 | -0.65 | 0.95 | 0.50 |

Four SMD pads, front copper/paste/mask; no drilled or duplicate pads. Pin 1 marker at upper left. Custom symbol and footprint placed in a disposable project, rendered, and four pad identities/positions read back. Both U9 grounds verified in exported project netlist. Input/output wires adapted to new symbol endpoints.

Pending acceptance: main PCB integration and clearance checks; reference text placement; final RF connectivity audit. Symbol library has no default footprint field; the U9 instance has the explicit custom footprint assigned. No 3D model supplied. Q3/Q4 exact manufacturer pin mapping is still unresolved and is not covered by this record.

## Hottech Q3/Q4 acceptance — 2026-09-09

Source: manufacturer Hottech 2SC3356, four-page document (no revision printed), pages 1 and 3, linked from C193010: https://www.lcsc.com/datasheet/C193010.pdf . Exact selected manufacturer is Guangdong Hottech, MPN 2SC3356, SOT-23. R25 is the S gain-bin marking, not a verified ordering suffix.

The page-1 perspective shows the package from the component side and identifies each physical B/E/C lead; its adjacent planar drawing has C on the single-lead side, B lower-left and E lower-right. It does not print numeric lead IDs. Rotating that component-side pattern 90 degrees clockwise maps the physical functions to the following KiCad pad numbers (numbers are the chosen library association, not a claim that the manufacturer printed them):

| Physical lead in manufacturer view | Symbol pin/name/type | Footprint pad | X/Y mm | Evidence |
|---|---|---|---|---|
| Bottom-left B | 1/B/input | 1 | -0.9375/-0.95 | p1 component-side view, rotated 90° clockwise |
| Bottom-right E | 2/E/passive | 2 | -0.9375/+0.95 | p1 component-side view, rotated 90° clockwise |
| Top single C | 3/C/passive | 3 | +0.9375/0 | p1 component-side view, rotated 90° clockwise |

Library symbol Transistor_BJT:Q_NPN_BEC; footprint Package_TO_SOT_SMD:SOT-23. Three physical leads, three symbol pins, three SMD pads; no duplicate or mechanical pads. Standard footprint has a larger land area than the manufacturer reference-only suggestion; 1.90 mm paired-lead pitch matches. Disposable placement/readback confirms all three pad positions and front copper/paste/mask layers. Render inspection confirms component-side orientation, pin-1 chamfer/marker, courtyard and land pattern. Symbol query confirms pin types and locations. Main schematic symbol functional endpoints are unchanged; numbers corrected.

Verification: wire queries confirm Q3 collector 3 on L17/C81, base 1 on C73/R27; Q4 collector 3 on L18/C85, base 1 on C83/R33. Native exported netlist confirms both emitter pins 2 on GND and both collector pins 3 off GND. Main PCB remains to be synchronized and DRC-checked. No blanket interchangeability with other manufacturers is accepted.


## U7 — TI SN74LVC1G86DBVR (accepted schematic package assignment)

Source: https://www.ti.com/lit/ds/symlink/sn74lvc1g86.pdf , SCES222R, Figure 4-1, DBV five-pin SOT-23 **top view**. Pin 1 is upper-left; walk down the left edge then up the right edge: 1=A, 2=B, 3=GND, 4=Y, 5=VCC. Stock 74xGxx:74LVC1G86 returns five corresponding pins (1/2 input, 4 output, 3/5 power input). Stock Package_TO_SOT_SMD:SOT-23-5 has five front SMD pads at local coordinates 1=(-1.1375,-0.95), 2=(-1.1375,0), 3=(-1.1375,0.95), 4=(1.1375,0.95), 5=(1.1375,-0.95). No duplicate/missing/mechanical pads, no mirroring. Scratch U3 symbol and footprint placed, queried and rendered; upper-left pin-1 silk triangle and fab chamfer agree with datasheet. Main U7 readback and XML export confirm footprint and exact MPN. Acceptance covers package/pin mapping; it does not qualify 145MHz RF operation.

## C58/C59 — Panasonic EEHZA1V470P (accepted schematic package assignment)

Primary sources: https://industrial.panasonic.com/content/data/CP/PDF/news2014/en/VH_E.pdf , PDF page 22 (ZA-9, exact part) and page 13 (land pattern); current part identity also confirmed at https://na.industrial.panasonic.com/products/capacitors/aluminum-electrolytic-capacitors/series/79/model/122 . 47uF, 35V, polarized hybrid aluminum electrolytic, size D, diameter 6.3mm, height 5.8mm. Terminal-side package drawing shows negative at the square end, positive at chamfered end; top marking identifies negative side. Two terminals only; manufacturer uses polarity rather than numeric lead labels. Our logical mapping is 1=positive, 2=negative. Front footprint view rotates the terminal axis to put positive/chamfered end left. Symmetry across that axis makes the orthogonal mirror immaterial to these two terminal positions; polarity is explicitly preserved.

Searched existing library first: CP_Elec_6.3x5.8 uses Nichicon-style pads 3.5x1.6mm with 1.9mm gap. Created Ember_RF:CP_Elec_Panasonic_D_6.3x5.8 to match Panasonic's size-D recommendation exactly: rectangular pads 3.2x1.6mm, centers +/-2.5mm on X, gap 1.8mm. Pad 1 left positive; pad 2 right negative. Front Cu/Paste/Mask only. Body/fab base 6.6mm with positive-end chamfers and diameter 6.3mm circle; courtyard +/-4.35mm X and +/-3.65mm Y includes body tolerance and 0.25mm margin. Positive silk mark clear of pads. No 3D model assigned.

Scratch C1 polarized symbol and C2 custom footprint placed, queried and rendered. Two symbol pins and two pads match; no duplicates or mechanical-only pads. Generator initially made pad-envelope-only courtyard; corrected via MCP before acceptance to include the full body. Main C58/C59 replacement preserves both pin endpoints exactly. Export after replacement confirms C58.1=+5V, C59.1=+3V3, C58.2=C59.2=GND. Values and LCSC C178639 preserved, exact manufacturer/MPN/voltage recorded. Main power schematic render visually checked. Main-board placement/routing and native library availability remain open.


## U5 — Microchip MCP6022-I/SN

Accepted SOIC-8 footprint assignment based on the existing prototype BOM in design/schematic_guide.md. Source: https://ww1.microchip.com/downloads/en/DeviceDoc/20001685E.pdf , DS20001685E (2017), p.1 package pinout and p.51 ordering suffix SN=8-lead SOIC. Top/component view with notch above; pin 1 upper left, counterclockwise lead numbering. Symbol Amplifier_Operational:MCP6022; footprint Package_SO:SOIC-8_3.9x4.9mm_P1.27mm. Eight physical leads, eight electrical symbol pins across units A/B/C, eight front SMD pads, no duplicate or mechanical-only pads. Stock pad dimensions 1.95x0.6mm, 1.27mm pitch, front Cu/Mask/Paste.

| Lead | Function | Symbol pin/type | Footprint pad | Local X/Y mm | View |
|---|---|---|---|---|---|
| 1 | OUT A | 1 output | 1 | -2.475/-1.905 | top, counterclockwise from notch |
| 2 | IN A- | 2 input | 2 | -2.475/-0.635 | top, counterclockwise from notch |
| 3 | IN A+ | 3 input | 3 | -2.475/0.635 | top, counterclockwise from notch |
| 4 | VSS | 4 power_in | 4 | -2.475/1.905 | top, counterclockwise from notch |
| 5 | IN B+ | 5 input | 5 | 2.475/1.905 | top, counterclockwise from notch |
| 6 | IN B- | 6 input | 6 | 2.475/0.635 | top, counterclockwise from notch |
| 7 | OUT B | 7 output | 7 | 2.475/-0.635 | top, counterclockwise from notch |
| 8 | VDD | 8 power_in | 8 | 2.475/-1.905 | top, counterclockwise from notch |

Scratch U4 A/B/C placed and pin locations queried; footprint U4 queried with all eight pad positions and layer sets. Schematic/board renders inspected: pad-1 triangle and fab chamfer upper left, correct lead ordering, no mirror reversal. Main U5 edit/readback confirms footprint on all three units and exact manufacturer/MPN. This is package acceptance, not a new baseband performance qualification.

## J8 — optional unpopulated header

User specifies an unpopulated through-hole header for future use, no exact purchased part. Selected stock Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical, 20 pads at 2.54mm pitch. Native DNP flag enabled and verified in assembly CSV preview and exported XML. Board inclusion retained. No manufacturer-specific or mating-part acceptance claimed; check the actual future header/cable orientation if populated. Cleared old Samtec purchasing field to avoid unintended ordering.

## Connector footprint completion — 2026-09-09

- [x] J6/J7 assigned project-local Samtec ESQ-120-14-G-S single-row 20-pin footprints; H3/H4 assigned ESQ-126-39-G-D double-row 52-pin footprints. Exact MPN/manufacturer/datasheet recorded; Samtec MPN removed from misleading LCSC field on J6/J7.
- [x] Scratch readback verified all 72 unique pad numbers, coordinates, symbol pin sets, 2.54 mm pitch, 1.02 mm drills and 1.8 mm lands. Top render inspected. Detailed acceptance in design/samtec_pad_audit.md.
- [x] Fresh export has no blank component footprints; named connectivity unchanged, J8 DNP preserved.
- [ ] Confirm connector physical side, rotation and origins against mating boards. Samtec mating-face numbering is distinct from the project's schematic pin diagram; do not mirror the footprint merely to match that diagram. Verify opposite Pico row orientations and stack compatibility before routing. Final reference/silkscreen placement remains open.
- [ ] New PCB dry-run passes missing-footprint preflight but reports 15 reference identity conflicts: C1, C2, C3, C4, C5, C6, C7, R1, R2, R3, R4, Y1, Y2, L12, L13. It classifies 107 footprints as board-only. These are not accepted deletions or a validated mapping; reconcile against full native connectivity before any update.
- [ ] CLI export still contains only 35 nets; native baseline contains 176. This discrepancy remains a synchronization blocker. No main PCB changes applied.

## User clarification — three identical DNP headers

J6/J7/J8 all use Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical. Supersedes J6/J7 Samtec socket selection above; purchasing fields cleared and all three assembly notes specify DNP. J8 native DNP flag remains set. J6/J7 native DNP checkboxes still require setting: desktop control timed out twice and current Konnect component editing does not expose that flag. Main PCB still awaiting synchronization.

## CSKB sockets placed for top-side assembly

- [x] User confirmed socket bodies above PCB, pins below; EPS B.Cu assignment was a placement mistake and not the intended assembly reference. H3/H4 remain on F.Cu.
- [x] Custom ESQ footprint updated through Konnect to CSKB logical numbering, odd-left/even-right in zero-rotation top view. This is an unkeyed socket with interface-defined numbering; distinguish from Samtec polarization-position numbers. No schematic bus pins or pad net assignments were changed. Earlier audit's generic Samtec mating-position convention is superseded for these CSKB instances.
- [x] H3/H4 refreshed using reviewed Konnect plan and placed at (111.9436,104.3736)/(106.8636,104.3736), both 180 degrees. Separation 5.08 mm. H4 restores original numbered-pad coordinates; H3 shifts its original hole grid +0.04 mm in X to match EPS. All 104 pad coordinates and net assignments verified. Top copper/silk export inspected.
- [x] Zones refilled and board saved. DRC now 631 errors, 273 warnings, 140 unconnected items (904 violations total). Placement/routing and silkscreen cleanup remain; not fab-ready.
- Scratch-board Add API failed during validation; no scratch-board acceptance claimed. Acceptance here uses library-tool readback, reviewed live refresh, all-pad live position/net checks, and rendered board inspection.
