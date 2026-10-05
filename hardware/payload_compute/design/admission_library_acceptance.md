# PMV16XNR enable-clamp physical map

2026-10-04. Accepted physical pin map for the prototype study; operating
temperature/ramp qualification is separate.

Nexperia PMV16XNR (PMV16XN device, R orderable reel suffix), TO-236AB/SOT23.
Manufacturer [product/orderable record](https://www.nexperia.com/product/PMV16XN)
and [datasheet](https://assets.nexperia.com/documents/data-sheet/PMV16XN.pdf),
PMV16XN v.1, 11 November 2014, copyright 2017. Pin functions p. 2 table 2;
package p. 10 fig. 18; reflow example p. 11 fig. 19.

Use stock `Transistor_FET:Q_NMOS_GSD` and `Package_TO_SOT_SMD:SOT-23`.
This is a verified assignment of a generic symbol, not an assumed generic
MOSFET pin order. Coordinates below are top/component view, +Y down. Rotate
the manufacturer's top outline 90° clockwise without reflecting: original
lower-left 1 becomes upper-left; original lower-right 2 becomes lower-left;
original upper-middle 3 becomes right-middle.

| Physical lead | Function | Symbol pin/name/type | Footprint pad / X/Y (mm) | View/direction | Evidence |
|---|---|---|---|---|---|
| 1 | Gate | 1 / G / input | 1 / −0.9375 / −0.950 | Top, 90° clockwise rotation, no mirror | p. 2 table 2; p. 10 fig. 18 |
| 2 | Source | 2 / S / passive | 2 / −0.9375 / +0.950 | Same; next along two-lead side | Same |
| 3 | Drain | 3 / D / passive | 3 / +0.9375 / 0 | Same; opposite single-lead side | Same |

Three physical leads = three symbol pins = three footprint pads. No duplicates,
exposed pad, mechanical hole or omitted electrical lead. Pads are 1.475 ×
0.600 mm roundrects on F.Cu/F.Mask/F.Paste. These are KiCad's larger generic
SOT23 lands, not the smaller exact Nexperia reflow example. They cover the
1.9 mm lead pitch and terminal envelope without joining leads; fab body
1.3 × 2.9 mm and keyed upper-left chamfer agree with the rotated package.
Silkscreen triangle identifies lead 1. Courtyard follows the component/pad
envelope; the footprint includes a standard SOT23 model.

[Disposable evidence](validation/payload_admission_acceptance/payload_admission_acceptance-package-evidence.json)
includes symbol and footprint query-back, placed schematic pins/properties,
and closed-board pads at 20/20 mm. Symbol and board renders were inspected:
G is left, D is above, S below in the symbol; physical lead 1 is upper-left in
the footprint. The body diode points from S toward D, matching the datasheet.

Only the map is accepted. The published IDSS/IGSS and 1.8 V RDS(on) maxima
used in the [conditional DC screen](admission_control.md) have 25°C test conditions; they do not
establish worst-case leakage or clamp resistance over flight temperatures.
