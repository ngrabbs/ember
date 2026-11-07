# CSD18543Q3A PowerPath footprint construction rules

2026-10-24. **Construction authorized:** the user explicitly answered “Approve footprint construction” for this document, including drain aliases, TI paste apertures and disposable verification. This authorizes construction/review, not final qualification. Reuse the existing official
`Transistor_FET:CSD18543Q3A` symbol. Construct one project-owned manufacturer-land
footprint in `Ember_Charger_BMS_Review.pretty`; no new symbol or global-library
edit. Keep a visible `CUSTOM FOOTPRINT — REVIEW REQUIRED` instance field and
pending-review metadata until accepted.

Authority: [TI SLPS633, December 2016](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf),
pp.1, 8–10. The top-view pin figure, bottom-view package drawing, copper lands
and stencil drawing were rendered and actually inspected. Coordinates below
are front/component view, X right / Y down, millimeters, pin 1 upper-left.
The stock footprint targets a different NexFET reference and differs in land
centers, widths and paste apertures; it is not the exact TI pattern.

## Physical and logical mapping

The package has eight perimeter terminals and a drain thermal region numbered
9 in the mechanical drawing. The stock symbol has **five logical pin numbers**:
1/2/3 source, 4 gate and 5 common drain. Preserve that symbol; document all five
drain contact regions as intentional aliases of logical pin/pad 5.

| Physical terminal | Function | Symbol pin | Copper pad object center | Copper size |
|---|---|---|---|---|
| 1 | S | 1 | −1.550, −0.975 | 0.600 × 0.300 |
| 2 | S | 2 | −1.550, −0.325 | 0.600 × 0.300 |
| 3 | S | 3 | −1.550, +0.325 | 0.600 × 0.300 |
| 4 | G | 4 | −1.550, +0.975 | 0.600 × 0.300 |
| 5 | D | 5 | +1.4825, +0.975 | 0.735 × 0.300 |
| 6 | D | 5 | +1.4825, +0.325 | 0.735 × 0.300 |
| 7 | D | 5 | +1.4825, −0.325 | 0.735 × 0.300 |
| 8 | D | 5 | +1.4825, −0.975 | 0.735 × 0.300 |
| 9 thermal | D | 5 | +0.3275, 0 | 1.775 × 2.450 |

Use nine numbered front copper/mask objects, with 0.05 mm corner radius.
Five objects intentionally repeat electrical number 5; there are five unique
pad numbers and four intentional number repetitions. The right-hand finger
rectangles extend 0.100 mm inside the central region, so their union remains
continuous and preserves TI's external drain extents. Their right edge is +1.850;
TI's exposed finger length is 0.635 mm from the central edge at +1.215. This
rectangle decomposition is the explicit alternative to an unsupported custom
polygon pad. Inspect the rendered union for gaps/notches before acceptance.
No copper pad has automatic F.Paste; stencil apertures are separate objects.

The approved decomposition preserves a 0.100 mm nominal overlap and at least
0.050 mm full-height connection into each finger. It does not reproduce TI's
internal concave R0.05 arcs: those differences are localized within 0.05 mm
corner extents at the eight finger/central junction corners. Treat this as a
documented construction deviation, not an exact TI outline or a new permission
blocker. Manufacturing corner fidelity remains open.

## Paste, body and acceptance

Twelve unnumbered F.Paste-only pads implement TI p.10: eight perimeter apertures
0.600 × 0.300 mm at X = ±1.550 and Y = ±0.975/±0.325; four central apertures
0.705 × 1.125 mm at X = −0.2075/+0.6975 and Y = ±0.6625. Corners use 0.05 mm
radius. The half-micron center rounding reconciles the printed 0.208/0.663 mm
reference dimensions with the stated aperture edges and 0.905/1.325 mm spacing.
Final stencil thickness/process and via-in-pad treatment are not qualified.

TI p.9 requires solder-mask opening at least 0.05 mm beyond copper on all sides.
The exposed authoring tools have no mask-margin setter. Implement nine extra
**unnumbered F.Mask-only** roundrects at the nine copper centers, width/height
increased by 0.10 mm and corner radius 0.10 mm. Their union with the numbered
Cu/Mask objects provides the required minimum 0.05 mm expansion for the actual
decomposed copper. This implementation was authorized as a routine realization
of the manufacturer requirement. It creates **30 raw pad objects: nine copper,
twelve blank paste and nine blank mask**, still only five electrical numbers.
Do not collapse the repeated drain numbers or blank objects in verification.

Fab uses the maximum 3.10 × 3.25 mm molded body, with a clear pin-1 key; separately
account for the package's 3.50 mm maximum lead span. Courtyard extends at least
0.25 mm beyond all copper, body and marker envelopes. Keep silkscreen clear of
mask openings. No thermal vias, drills or board routing in this construction.
The thermal drain region must never be mistaken for a ground pad.

Read back every copper/paste object, including repeated numbers, dimensions,
coordinates, layers, radius and no-drill state. Compare all nine physical rows
and twelve apertures. Place disposable symbol/board instances through Konnect,
query them, save and inspect actual schematic and placed-board renders before
real use. Preserve the stock symbol's stacked source pins and exact MFG P/N;
record all drain aliases explicitly. The recorded approval authorizes construction
and review, not electrical/thermal, assembly, sourcing or flight acceptance.
