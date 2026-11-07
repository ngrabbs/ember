# TPS3700 payload source-window library construction proposal

2026-10-24. **Awaiting explicit construction approval.** Proposes TI
TPS3700DDCR for a managed-payload feed source-window monitor powered from
essential +3V3. It selects no complete protection circuit, flight threshold or
source/current rating. Circuit integration remains conditional on the separate
electrical and sequencing checks. Existing approvals cover other parts only.

## Source and search

Primary [TI SBVS187G, February 2019](https://www.ti.com/lit/ds/symlink/tps3700.pdf):
physical pin map/functions p4; limits, thresholds/leakage and power-up behavior
pp5–7; reference window schematic Figure20 p16. Exact orderable part
**TPS3700DDCR**, DDC six-lead thin SOT, −40..125°C, large reel. Do not substitute
DSE WSON, Q1, R2 or another package by name similarity. The DSE pin map differs.

The [linked TI DDC0006A drawing](https://www.ti.com/lit/pdf/MPDS124I), drawing
4214841/E, August2024, supplies top-view outline p1, recommended lands/mask p2
and stencil p3. All five relevant pin/application/package page images were
opened and inspected on2026-10-24. Manufacturer drawings remain source
references; disposable views must show what Konnect actually created.

Fresh Konnect project-aware `TPS3700` search returns zero. Neither current
global nor project symbol table registers a `KiCadLib` nickname; its absence is
not a negative part search within that library. Official stock TSOT-23-6 and
SOT-23-6 both have six1.325×0.60mm lands at X=±1.1375, Y=−0.95/0/+0.95,
radius0.15. TI specifies1.10×0.60 at X=±1.35 with radius0.05. The stock
body-zone courtyard also has only0.175mm clearance to maximum1.75mm body
width. Propose an exact manufacturer-pattern project footprint; do not edit
vendor/global libraries or relabel the earlier DBV footprint as DDC.

## Native authoring boundary

Append one symbol `TPS3700DDCR_REVIEW` and one footprint
`TI_DDC0006A_TSOT23_6_TI_Land_REVIEW` to the existing portable
`Ember_Charger_BMS_Review` project library under `hardware/eps/rev_b/libraries/`.
Resolve its current registered files through supported tools; preserve all
existing symbol subtrees, footprints, registrations and prior native sources.
All changes through Konnect. No real EPS PCB synchronization/placement.

Use one rectangular unit: INA+ and INB− left, OUTA/OUTB right, VDD top, GND
bottom. All six pins visible and separate, with no implicit/hidden power or
stacked leads. Pin endpoints on1.27mm grid, preferably2.54mm vertical spacing;
expand body as needed for exact names and exposed wire stubs. Read actual
generated bounds and fields before wiring. Do not draw physical package lead
order as the schematic's functional arrangement.

All rows below use **top/component/front view**, pin1 upper left,
counterclockwise down left1–3, then up right4–6; footprint Y points down.
Coordinates in millimetres. No exposed pad or mechanical/electrical seventh pin.

| Physical lead | Symbol name/type | Pad | X | Y |
| --- | --- | --- | --- | --- |
| 1 | OUTA / open_collector | 1 | −1.35 | −0.95 |
| 2 | GND / power_in | 2 | −1.35 | 0 |
| 3 | INA+ / input | 3 | −1.35 | +0.95 |
| 4 | INB− / input | 4 | +1.35 | +0.95 |
| 5 | VDD / power_in | 5 | +1.35 | 0 |
| 6 | OUTB / open_collector | 6 | +1.35 | −0.95 |

Require Reference U, Value TPS3700DDCR, exact `MFG P/N=TPS3700DDCR`,
`Manufacturer=Texas Instruments`, `PackageSize=DDC0006A / TSOT-23-6`, source
Datasheet URL, exact project Footprint, description and review status. Preserve
canonical property names and source metadata. Show exact MFG P/N beside the
main unit without duplicate Value text. Read all library/disposable fields and
display settings back. Unsupported S11 default/field-font operations remain
explicit limitations, not passes inferred from a property dictionary.

## Review marker requiring approval

The symbol remains **CUSTOM — REVIEW REQUIRED**. Konnect's currently available
symbol authoring cannot set bright-green symbol-body graphics. Propose the same
alternative used for earlier approved parts: a visible bright-green `#00FF00`
enclosure/callout with the custom-review warning and construction authorization
status. Do not claim the symbol body itself is green, alter the global theme,
change pin types, or use DNP as a marker. Inspect the rendered result and retain
the marker until explicit review release.

## Exact footprint rules

- Six numbered SMD roundrect pads,1.10×0.60mm, radius0.05mm
  (`roundrect_rratio=1/12`), rotation0; F.Cu/F.Paste/F.Mask, no drills. Centers
  as above. Paste equals the six TI stencil apertures;0.125mm source stencil
  thickness is not production stencil qualification.
- Six additional **blank-number F.Mask-only** roundrect apertures,
  1.20×0.70mm, radius0.10mm (`roundrect_rratio=1/7`), same centers. Their union
  implements a chosen+0.05mm NSMD opening despite absent native margin API.
  TI's preferred NSMD note is0.07mm **MAX**, not MIN. Query inherited saved-board
  margins and inspect effective openings: require+0.05mm nominal; block mask
  acceptance if effective expansion exceeds0.07mm or cannot be established.
- Raw count12: six numbered copper/paste/base-mask and six blank mask-only;
  each electrical number1–6 once, blank count6. Six copper regions, six paste
  regions, six effective mask regions; no duplicate electrical numbers, vias,
  drills, center pad or extra contacts. Check full counters before converting
  to a number-keyed dictionary. Adjacent copper/paste gap0.35mm, mask web0.25mm.
- F.Fab nominal body1.60×2.90mm, upper-left pin1 chamfer,0.10mm stroke.
  F.CrtYd closed X=±2.20,Y=±2.10mm,0.05mm stroke, no fill. Outer copper X=±1.90
  and explicit mask±1.95 leave0.30/0.25mm respectively. Maximum body1.75×3.05mm
  and maximum1.1mm height from DDC drawing; courtyard retains additional margin.
- F.SilkS separated top/bottom strokes and a distinct pin1 marker,0.12mm
  strokes, no mask intersections. Keep fields readable and clear; record any
  unsupported placement operation. No unverified3D model or inferred paste
  shrink. Do not edit an existing footprint to implement this proposal.

## Acceptance after approval

Create a new disposable ANSI B symbol/PCB fixture through Konnect, separate from
every frozen checkpoint. Query exact library pin names/types/fields and all raw
footprint objects. Place and save both disposable instances; first establish
actual live/closed-board IPC identity. Requery library/live/saved pad counts,
number multiplicities, centers, sizes, radii, rotations, layers and drills.
Compare every lead to the table. Verify actual mask margin and union geometry.

Export and actually inspect schematic page/detail and board copper, paste,
mask, silk, courtyard and numbered fabrication views; distinguish overlays
from native artwork. Check top-view orientation and pin1, not counts alone.
Run independent CLI netlist/ERC, preserving genuine unwired fixture pins
instead of hiding them with no-connects/flags. Record before/after source hashes,
an exact old-source/library preservation guard, source references, readbacks,
render paths, inspected views and remaining limitations. Package acceptance
does not establish transient response, fault capture timing, current survival,
brownout or assembly/flight acceptance.
