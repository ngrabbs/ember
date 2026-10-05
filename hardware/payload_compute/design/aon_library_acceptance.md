# LMR36506R3RPER prototype package acceptance

2026-10-04. Physical lead/function map accepted for the bounded prototype
study after library queries, disposable placement, instance readback and
visual inspection. Land pattern uses documented engineering deviations;
common-stencil selection and assembly release remain pending.

Manufacturer: Texas Instruments. Exact MPN: LMR36506R3RPER, fixed 3.3 V
auto/PFM mode; RPE = 9-lead VQFN-HR; final R = reel.
Source: [TI datasheet](https://www.ti.com/lit/ds/symlink/lmr36506.pdf),
SNVSBB6C, January 2026. Top-view pin figure/table p. 4; package bottom-view
outline p. 44; land/stencil top views pp. 45–46, drawing 4227033/B, September
2023. No stock LMR36506 symbol or RPE footprint was found.

Symbol: `EMBER_Payload:LMR36506R3RPER`.
Footprint: `EMBER_Payload:TI_RPE0009B_VQFN-HR-9_2x2mm_Prototype`.
All following coordinates are top view, +Y down, relative to package centre.
Walk from upper-left key down leads 1–4, then up right-side leads 5–8;
lead 9 is the separate central ground bar. The p. 44 bottom view is reflected
vertically into this chosen top-view frame, consistent with p. 4 and p. 45.

| Lead | Function | Symbol number / name / type | Footprint pad centres X / Y (mm) | View / direction | Evidence |
|---|---|---|---|---|---|
| 1 | Frequency selection | 1 / RT / passive | 1: −0.825 / −0.738; −0.650 / −0.9125 | Top, CCW from upper-left key | p. 4 fig. 5-1/table 5-1; pp. 44–45 |
| 2 | Power good | 2 / PGOOD / open_collector | 2: −0.900 / −0.250 | Top, CCW from key | Same |
| 3 | Enable | 3 / EN/UVLO / input | 3: −0.900 / +0.250 | Top, CCW from key | Same |
| 4 | Input supply | 4 / VIN / power_in | 4: −0.850 / +0.738; −0.700 / +0.9125 | Top, CCW from key | Same; bottom-arm width is prototype choice |
| 5 | Switch node | 5 / SW / output | 5: +0.850 / +0.738; +0.700 / +0.9125 | Top, CCW from key | Same; bottom-arm width is prototype choice |
| 6 | Bootstrap capacitor | 6 / BOOT / passive | 6: +0.900 / +0.250 | Top, CCW from key | Same |
| 7 | Internal LDO | 7 / VCC / power_out | 7: +0.900 / −0.250 | Top, CCW from key | Same |
| 8 | Fixed-output sense | 8 / VOUT/BIAS / input | 8: +0.825 / −0.738; +0.650 / −0.9125 | Top, CCW from key | Same |
| 9 | Ground | 9 / GND / power_in | 9: 0 / −0.550 | Top, central bar | Same |

Nine physical electrical leads = nine symbol pins = nine logical copper pad
numbers. Four L leads have two overlapping same-number copper/mask primitives:
13 numbered copper primitives, four deliberate duplicates. Ten unnumbered
paste-only primitives bring the total to 23 objects. There is no lead 10,
mechanical hole or additional exposed pad.

## Prototype land pattern choices

Middle leads are 0.600 × 0.250 mm at X=±0.900, Y=±0.250. Central ground
bar is 0.350 × 1.300 mm, offset toward the keyed end as TI shows; do not
replace it with a centred ground rectangle.

Upper L horizontal arms are 0.750 × 0.225 mm and vertical arms
0.400 × 0.575 mm. Lower horizontal arms are 0.700 × 0.225 mm. The lower
vertical arms are deliberately specified as 0.400 × 0.575 mm at X=±0.700,
extending 0.050 mm farther outward than the 0.350 mm strip inferred from
TI's example contour. This chosen prototype dimension avoids treating an
unlabelled contour width as an exact manufacturer requirement. The copper
still covers the physical leads and preserves isolation. Every primitive
has R0.050 corners; their union has square concave corners. These deviations
are explicit engineering choices, not an exact reproduction of TI's contour.

Paste uses the p. 46 **0.125 mm stencil** basis: upper vertical arms shortened
to 0.500 mm at Y=−0.875; ground windows 0.350 × 0.550 mm at Y=−0.925 and
0.350 × 0.500 mm at Y=−0.175. Normal leads retain full paste; lower L paste
follows the chosen enlarged copper. TI's coverage percentages are not claimed
for this modified pattern. Fourteen paste primitives form ten connected
apertures. Reconcile paste volume with the eFuse's 0.100 mm example before
assembly; do not assume one stencil thickness satisfies both unchanged.

F.Fab is 2 × 2 mm with keyed chamfer; silk dot is upper-left; courtyard
±1.650 mm exceeds 0.250 mm from pad extrema. The disposable board is unconnected
at 20/20 mm. The [package fixture](validation/payload_aon_acceptance/README.md)
contains final query evidence and separate symbol/copper/paste renders.

This record proves the physical map and the specified prototype geometry,
not regulator startup, loop stability, converter efficiency, a common stencil,
flight suitability or fabrication readiness.
