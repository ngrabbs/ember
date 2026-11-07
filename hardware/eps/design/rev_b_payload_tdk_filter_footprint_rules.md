# TDK payload filter footprint construction proposal

2026-10-24. Construction approved by the user: “Approve TDK filter footprint construction”. Completed disposable evidence is in [the package checkpoint](../verification/managed_payload/tdk_filter_package/README.md). The custom review marker remains; assembly/circuit qualification is separate. For C1405/C1406 only, exact
TDK CGA3E2C0G1H102J080AA, 1 nF/5%/50 V/C0G, 0603. No new symbol is needed:
retain stock `Device:C`, two interchangeable passive terminals, physical
pad 1 left/pad 2 right in front view. No polarized behavior or pin key is
invented. Approval covers construction and disposable verification only.

Source: [TDK exact product page](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA3E2C0G1H102J080AA).
The live product page, second gallery drawing and reflow range table were
actually inspected. Retained screenshot:
[manufacturer land diagram](../verification/managed_payload/passive_selection/TDK_lands_browser.png).
PA is the inner gap, PB horizontal pad length, PC vertical pad width; all
three reflow recommendations span 0.60..0.80 mm. Choose their 0.70 mm midpoint.
The queried stock C_0603_1608Metric has 0.90 × 0.95 mm pads and 0.65 mm gap:
gap is within the range, pad length/width are outside it. Do not relabel the
stock footprint as an exact TDK pattern or change the global library.

## Project footprint boundary

Add `C_0603_TDK_CGA3_PA0.70_PB0.70_PC0.70_REVIEW` to the existing portable
project `Ember_Charger_BMS_Review` footprint library, resolved through Konnect.
Preserve every prior library object/table and real EPS source. Use one mutation
owner. All native authoring, registration, placement and changes via Konnect.

Two numbered SMD roundrect copper pads at (−0.70,0)/(+0.70,0) mm,
size 0.70 × 0.70 mm, radius 0.05 mm (`roundrect_rratio=1/14`), rotation 0;
F.Cu/F.Paste/F.Mask, no drills. Copper inner gap 0.70 mm, outer X±1.05 mm.
Paste apertures equal copper; stencil thickness/process remain unqualified.

Two blank-number F.Mask-only apertures at the same centers, 0.80 × 0.80 mm,
radius 0.10 mm (`roundrect_rratio=1/8`), implement a chosen +0.05 mm mask
opening through the supported authoring API. This is a design choice, not a
TDK mask specification. Require exactly four raw pads: electrical numbers
1/2 once each and two blank mask-only pads. Two copper regions, two paste
regions, two effective mask openings; nominal mask web 0.60 mm. Verify saved
project/footprint margins and actual mask union; no unexamined inherited
expansion. Do not claim pad dictionary size proves these counts.

F.Fab nominal body 1.60 × 0.80 mm, 0.10 mm outline; identical end-terminal
indications are optional. F.CrtYd closed rectangle X±1.35/Y±0.70 mm,
0.05 mm stroke/no fill: 0.25 mm beyond explicit mask X±1.10 and at least
0.25 mm beyond maximum 1.70 × 0.90 mm body. Maximum component height is
0.90 mm. Re-evaluate height/placement in the real board mechanical assembly.
F.SilkS short top/bottom strokes clear of mask; no polarity/pin-1 triangle.
Use readable reference/value fields; no unverified 3D model. Description and
tags name the exact selected part, dimensions and review status.

## Acceptance

Create a new disposable symbol/board fixture through Konnect. Use exact
MFG P/N/Manufacturer/PackageSize/Tolerance/Voltage/Dielectric fields and S11
presentation. Retain a visible green CUSTOM FOOTPRINT — REVIEW REQUIRED
callout; the stock capacitor symbol itself is unchanged. Do not claim its
body is green or use DNP/ERC changes as review markers.

Query library and saved instance fields, two symbol pins, all four raw pads,
numbers, XY, dimensions, radii, layers, rotation and drills. Compare copper,
paste, effective mask, body and courtyard against these rules, including saved
mask defaults. Place/save and read back the disposable board through the
supported live or closed-board workflow; record the actual source mode.
Export and actually inspect page/detail schematic and copper/paste/mask/fab/
courtyard/numbered board views. Distinguish query-derived overlays from native
artwork. Run CLI netlist/ERC without hiding genuine unwired fixture pins.
Record native preservation and source/render hashes separately from electrical
results. Keep the footprint out of the real design while mapping, mask or
orientation is ambiguous. Assembly process, filter response and qualification
remain separate gates after package construction.
