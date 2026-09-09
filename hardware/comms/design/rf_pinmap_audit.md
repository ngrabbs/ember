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
