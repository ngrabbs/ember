# Run-latch library acceptance

2026-10-04. Accepted for this bounded disposable study only.
Exact ordered suffixes: TPS3808G33DBVR (DBV six leads),
SN74LVC1G11DBVR (DBV six leads), SN74LVC1G74DCUR (DCU eight leads).
Cached JLC codes C43698 / C22046 / C70285 are sourcing candidates, not
current purchasing/assembly acceptance.

Manufacturer pin diagrams are top views. PCB footprint coordinates below
are front/top placement, local mm with positive Y down. Pin 1 is upper left;
numbering runs down the left side, then up the right. No mirrored bottom-view
numbering is applied. All leads have one electrical pad; no exposed,
duplicate, mechanical or paste-only pads occur in these packages.

| MPN | Datasheet lead | Function | Symbol pin / type | Footprint pad | Local x, y mm |
| --- | --- | --- | --- | --- | --- |
| TPS3808G33DBVR | 1 | RESET_N | 1 / open_collector | 1 | -1.3, -0.95 |
| TPS3808G33DBVR | 2 | GND | 2 / power_in | 2 | -1.3, 0 |
| TPS3808G33DBVR | 3 | MR_N | 3 / input | 3 | -1.3, 0.95 |
| TPS3808G33DBVR | 4 | CT | 4 / input | 4 | 1.3, 0.95 |
| TPS3808G33DBVR | 5 | SENSE | 5 / input | 5 | 1.3, 0 |
| TPS3808G33DBVR | 6 | VDD | 6 / power_in | 6 | 1.3, -0.95 |
| SN74LVC1G11DBVR | 1 | A | 1 / input | 1 | -1.3, -0.95 |
| SN74LVC1G11DBVR | 2 | GND | 2 / power_in | 2 | -1.3, 0 |
| SN74LVC1G11DBVR | 3 | B | 3 / input | 3 | -1.3, 0.95 |
| SN74LVC1G11DBVR | 4 | Y | 4 / output | 4 | 1.3, 0.95 |
| SN74LVC1G11DBVR | 5 | VCC | 5 / power_in | 5 | 1.3, 0 |
| SN74LVC1G11DBVR | 6 | C | 6 / input | 6 | 1.3, -0.95 |
| SN74LVC1G74DCUR | 1 | CLK | 1 / input | 1 | -1.55, -0.75 |
| SN74LVC1G74DCUR | 2 | D | 2 / input | 2 | -1.55, -0.25 |
| SN74LVC1G74DCUR | 3 | Q_N | 3 / output | 3 | -1.55, 0.25 |
| SN74LVC1G74DCUR | 4 | GND | 4 / power_in | 4 | -1.55, 0.75 |
| SN74LVC1G74DCUR | 5 | Q | 5 / output | 5 | 1.55, 0.75 |
| SN74LVC1G74DCUR | 6 | CLR_N | 6 / input | 6 | 1.55, 0.25 |
| SN74LVC1G74DCUR | 7 | PRE_N | 7 / input | 7 | 1.55, -0.25 |
| SN74LVC1G74DCUR | 8 | VCC | 8 / power_in | 8 | 1.55, -0.75 |

TI TPS3808 SBVS050N pin map p4 and DBV0006A land drawing 4214840/G
08/2024; TI SN74LVC1G11 SCES487I pin map p3 (same DBV package);
TI SN74LVC1G74 SCES794G pin map p4 and DCU0008A land drawing
4225266/A 09/2014 are the source evidence. Datasheet links are in
[run_latch.md](run_latch.md).

The reset custom symbol corrects RESET_N to open collector. The gate stock
symbol has unnamed logic pins, reconciled above to manufacturer A/B/C/Y.
The latch is custom: positive Q is lead 5; inverted Q is lead 3. Do not use
a different 74-family package's numbering. PRE_N/CLR_N are active low,
CLK rising edge; simultaneous low preset and clear is excluded by tying preset high.

DBV footprint uses 1.10 × 0.60 mm lands, row centers x ±1.30 mm,
y -0.95/0/+0.95 mm. DCU uses 0.85 × 0.30 mm lands, row centers
x ±1.55 mm, y -0.75/-0.25/+0.25/+0.75 mm. All are zero-rotation SMD
round rectangles with 0.05 mm corner radius on F.Cu/F.Mask/F.Paste;
no drill. DCU courtyard is ±2.225 × ±1.25 mm, DBV ±2.10 × ±1.70 mm.
Fab outlines and upper-left silk dots establish pin-1 orientation. No 3D
model is supplied. Final silk/assembly placement remains a layout task.

[Disposable evidence](validation/payload_latch_acceptance/README.md) records
library queries, placed symbols and live IPC pads at U1=(100,100),
U2=(110,100), U5=(120,100), rotation 0. Renders were visually inspected.
The checker joins all 20 distinct package leads to symbol numbers, lands and
live pads, plus all five placed IC pin maps and exported circuit nets.
Library defaults were not copied by placement, so all five instance
footprints and MPN/LCSC fields were assigned explicitly through Konnect.
