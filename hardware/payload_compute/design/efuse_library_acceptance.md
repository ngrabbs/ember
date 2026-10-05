# TPS259470LRPWR package acceptance

2026-10-04. **Accepted for the physical pin map and documented prototype land
pattern only.** No main-input branch is wired in this disposable project.
Default-off admission, current limit, thermal behavior, inrush and system
protection remain separate design work.

Manufacturer: Texas Instruments. Exact orderable MPN: TPS259470LRPWR;
RPW = 10-lead VQFN-HR, R = reel. The L variant latches off on faults;
the 470 variant provides adjustable OVLO, active current limit, AUXOFF and FLT.
Source: [TI datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
SLVSFC9C, revised May 2026. Pin drawing/function table pp. 5–6;
land/stencil examples PDF pp. 73–74, drawing 4225183/A, August 2019.
Library search returned no stock TPS25947 symbol or RPW footprint.

Symbol: `EMBER_Payload:TPS259470LRPWR`.
Footprint: `EMBER_Payload:TI_RPW0010A_VQFN-HR-10_2x2mm`.
Coordinates below are footprint-local millimetres, +Y down.
Walk from keyed upper-left lead 1 down the left side, through the two internal
power bars, then up the right side. All rows use the manufacturer's top view;
there is no bottom-view mirror. Pads 5 and 6 are distinct electrical leads,
not an exposed ground pad. There is no lead 11.

| Physical lead | Function | Symbol pin / name / type | Footprint pad centres X / Y | View / direction | Evidence |
|---|---|---|---|---|---|
| 1 | Enable / UVLO | 1 / EN/UVLO / input | 1: −0.900 / −0.700; −0.725 / −0.875 | Top, CCW from upper-left key | p. 5 fig. 5-1/table 5-1; PDF p. 73 |
| 2 | OVLO | 2 / OVLO / input | 2: −0.900 / −0.225 | Top, CCW from key | Same |
| 3 | Auxiliary control | 3 / AUXOFF / open_collector | 3: −0.900 / +0.225 | Top, CCW from key | Same |
| 4 | Active-low fault | 4 / ~FLT / open_collector | 4: −0.900 / +0.700; −0.725 / +0.875 | Top, CCW from key | Same |
| 5 | Power input | 5 / IN / power_in | 5: −0.250 / 0 | Top, left internal bar | Same |
| 6 | Power output | 6 / OUT / power_out | 6: +0.250 / 0 | Top, right internal bar | Same |
| 7 | Slew capacitor | 7 / DVDT / passive | 7: +0.900 / +0.700; +0.725 / +0.875 | Top, CCW from key | Same |
| 8 | Ground | 8 / GND / power_in | 8: +0.900 / +0.225 | Top, CCW from key | Same |
| 9 | Current limit / monitor | 9 / ILM / passive | 9: +0.900 / −0.225 | Top, CCW from key | pp. 5–6; PDF p. 73 |
| 10 | Overcurrent timer | 10 / ITIMER / passive | 10: +0.900 / −0.700; +0.725 / −0.875 | Top, CCW from key | pp. 5–6; PDF p. 73 |

## Land and stencil implementation

The ten physical leads correspond to ten symbol pins and ten logical copper
pad numbers. Four L-shaped corner leads each use two overlapping primitives
with the same number: **14 numbered copper/mask primitives**, four intentional
duplicates. Twelve additional unnumbered paste-only primitives give 26 total
pad objects. No mechanical holes or additional electrical pad are present.

Normal leads: 0.600 × 0.250 mm. Corner horizontal arms:
0.600 × 0.300 mm; vertical arms: 0.250 × 0.650 mm. IN/OUT bars:
0.300 × 2.400 mm. All individual roundrects have 0.050 mm corner radius.
The union of two rounded rectangles leaves a square concave L corner instead
of TI's rounded concave corner. This is an intentional local deviation from
the example land pattern, bounded within 0.050 mm of that corner; lead numbering,
outer extents, minimum separation and contact areas are preserved. It is not
claimed to be an exact copy of TI's contour.

Paste follows TI's **0.100 mm stencil example**: four normal full-size
openings; each corner uses 0.600 × 0.275 mm and 0.225 × 0.650 mm overlapping
arms, with centres at X=±0.900/Y=±0.6875 and X=±0.7125/Y=±0.875.
The arm overlap describes one aperture per corner. Each power bar has two
0.280 × 1.060 mm windows centred at Y=±0.630, leaving a 0.200 mm central gap.
There are twelve connected paste apertures. Do not generate another default
full-bar paste opening. Stencil thickness and paste release still require
assembly-house review when the board is released.
The LMR36506 package example uses a 0.125 mm stencil. A single assembled PCB
needs a deliberate common-stencil choice and adjusted apertures or an accepted
stepped stencil; these two manufacturer examples must not be combined as
though their quoted area coverage also proved equal paste volume.

F.Fab is a 2 × 2 mm body with upper-left chamfer. Silkscreen has an upper-left
dot and two clear outline sides. Courtyard ±1.650 mm encloses pads and markers;
it exceeds the required 0.250 mm clearance from pad extrema.

## Evidence and limits

[Disposable project and renders](validation/payload_input_acceptance/README.md)
include MCP library queries, schematic pin/field readback, closed-board pad
readback, exported netlist, copper/package render and separate paste render.
Every lead/function, instance coordinate and layer set was compared with the
table; all ten physical leads are represented. The first symbol render showed
overlapping vertical pin names; the final horizontal-pin layout corrected it
and was rendered and read back again. The final body text is readable.

`validation/check_input_package.py` checks the saved evidence against this
manufacturer map, deliberate duplicate counts, lead separation, stencil window
sizes and disposable instance placement. This package-only fixture is
intentionally unwired; ERC would report unconnected pins and is not circuit
acceptance. KiCad is closed, so all modifications are saved Konnect file writes;
there is no pending live-editor save.

The accepted package does not establish AUXOFF as a complete source-health
indicator. Refer to [source selection](source_selection.md) for the additional
feedback and default-off enable requirements.
