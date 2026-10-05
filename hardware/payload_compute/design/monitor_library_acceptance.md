# Voltage-monitor library acceptance

2026-10-04. PASS for electrical pin maps and package lands of the two exact
parts below. This is not circuit qualification or fabrication readiness.
The disposable project is [payload_monitor_acceptance](validation/payload_monitor_acceptance/payload_monitor_acceptance.kicad_pro).

## REF3425IDBVR

Texas Instruments, DBV/SOT-23-6. [REF34 datasheet](https://www.ti.com/lit/ds/symlink/ref34.pdf),
SBAS804G, April 2026: p.4 top-view pin figure/table; PDF pp.26–28 package,
land and stencil drawings, DBV0006A, 4214840/G, August 2024.
Custom symbol is required because the part was absent from the active library.
Default and placed footprint: `EMBER_Payload:TI_DBV0006A_SOT23_6`.

Every row uses top/component view: pin 1 upper left, counterclockwise down
the left side then up the right. X/Y are footprint-local mm, Y down.

| Lead | Function | Symbol pin/name/type | Pad | X/Y mm |
| --- | --- | --- | --- | --- |
| 1 | Ground force | 1 / GND_F / power_in | 1 | -1.30 / -0.95 |
| 2 | Ground sense | 2 / GND_S / power_in | 2 | -1.30 / 0 |
| 3 | Enable | 3 / EN / input | 3 | -1.30 / 0.95 |
| 4 | Supply | 4 / IN / power_in | 4 | 1.30 / 0.95 |
| 5 | Output sense | 5 / OUT_S / input | 5 | 1.30 / 0 |
| 6 | Output force | 6 / OUT_F / power_out | 6 | 1.30 / -0.95 |

Six physical leads, six symbol pins, six electrical pads; no EP, duplicates,
mechanical or paste-only pads. Each land is 1.10×0.60 mm, pitch 0.95 mm,
row spacing 2.60 mm, rounded radius 0.05 mm, front copper/paste/mask, no drill.
Fab body 1.6×2.9 mm, upper-left chamfer and silk dot identify pin 1.
Courtyard includes both body and lands with >=0.25 mm clearance.
Use this enabled six-lead variant; REF3425T has different pin functions.

## LM2903BIDR

Texas Instruments, D/SOIC-8. [LM393/LM2903 datasheet](https://www.ti.com/lit/ds/symlink/lm393.pdf),
SLCS005AH, April 2025: p.3 top-view figure/table; PDF pp.43–45 package,
land and stencil drawings, D0008A, 4214825/C, February 2019.
Stock `Comparator:LM2903` matches all leads and open-collector output types.
Its placed value/MPN is LM2903BIDR; its generic library default footprint is
blank, so explicitly assign `EMBER_Payload:TI_D0008A_SOIC_8` to every unit.

Every row uses top/component view: pin 1 upper left, counterclockwise down
the left side then up the right. X/Y are footprint-local mm, Y down.

| Lead | Function | Symbol pin/name/type | Pad | X/Y mm |
| --- | --- | --- | --- | --- |
| 1 | Comparator A output | 1 / unnamed / open_collector | 1 | -2.70 / -1.905 |
| 2 | Comparator A negative | 2 / - / input | 2 | -2.70 / -0.635 |
| 3 | Comparator A positive | 3 / + / input | 3 | -2.70 / 0.635 |
| 4 | Ground | 4 / V- / power_in | 4 | -2.70 / 1.905 |
| 5 | Comparator B positive | 5 / + / input | 5 | 2.70 / 1.905 |
| 6 | Comparator B negative | 6 / - / input | 6 | 2.70 / 0.635 |
| 7 | Comparator B output | 7 / unnamed / open_collector | 7 | 2.70 / -0.635 |
| 8 | Supply | 8 / V+ / power_in | 8 | 2.70 / -1.905 |

Eight physical leads, eight symbol pins over three units, eight electrical
pads; no EP, duplicates, mechanical or paste-only pads. Each land is
1.55×0.60 mm, pitch 1.27 mm, row spacing 5.40 mm, rounded radius 0.05 mm,
front copper/paste/mask, no drill. Fab body 3.9×4.9 mm; upper-left chamfer
and silk dot identify pin 1. Courtyard includes body and lands at >=0.25 mm.

## Acceptance evidence and limits

Queried both symbols and footprints, placed/read back disposable schematic
instances, placed both footprints at rotation zero on front copper, and
checked all 14 live pad positions against their library coordinates.
Inspected manufacturer land drawings, disposable schematic render and
enlarged board render. Corrected generated courtyards to include package
bodies, then refreshed live instances through a reviewed Konnect plan.

The [library evidence](validation/payload_monitor_acceptance/payload_monitor_acceptance-library-evidence.json)
contains original pin/pad/instance queries; the
[accepted-evidence file](validation/payload_monitor_acceptance/payload_monitor_acceptance-accepted-library-evidence.json)
contains final queries and courtyard graphics after refresh. Pad coordinates
are unchanged. The reference symbol drawing was widened to keep its fields
clear of pin numbers; physical numbering/functions are unchanged and rechecked.
The [board detail](validation/payload_monitor_acceptance/payload_monitor_acceptance-footprints-detail.png)
shows orientation and keys. Scratch reference labels are illustrative and
need final silkscreen positioning during carrier layout. No 3D model is
claimed. Passive MPN/footprint acceptance and full circuit validation are
separate. The custom reference's default footprint was explicitly applied
to its placed instance because placement did not copy that field.
