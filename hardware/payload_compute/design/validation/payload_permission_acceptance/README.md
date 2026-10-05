# Permission-control circuit study

2026-10-04. **PASS for bounded schematic and NAND physical map**.
Carrier integration, source switching, physical timing and flight qualification
remain open. See [design and limitations](../../permission_control.md).

Nine gates, nine resistors (R9 deliberately omitted) and nine 100 nF bypass
capacitors are wired. [Schematic render](payload_permission_acceptance-final.png),
[exported netlist](payload_permission_acceptance.net),
[query/check evidence](payload_permission_acceptance-final-evidence.json),
[direct ERC](payload_permission_acceptance-erc.json).

Checked: 20 exported nets and 512 combinations evaluated from the actual saved
gate pins against independent requirements. No floating wire endpoints,
unconnected pins, shorts, orphan items or detected symbol overlaps.
The final image was inspected for labels, signal flow and page boundaries.

ERC has **one error and two warnings**, all explicit boundaries:
U9 pin 3 requires the external AON_RESET_N supervisor driver;
IHU_PAYLOAD_EN and AON_RESET_N are isolated labels in this study.
Pulldowns may satisfy ERC's drive heuristic; no result replaces actual external
drivers. AON power/ground flags are study assumptions.
AON_RESET_N uses the supervisor block's existing 10 kΩ pull-up, with no
10 kΩ pulldown/divider added here.

## SN74LVC1G10DBVR physical acceptance

Manufacturer Texas Instruments; exact MPN SN74LVC1G10DBVR, DBV six-lead SOT-23.
[Datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g10.pdf)
SCES486E, revised December 2013, p1 top-view function map;
PDF p24, DBV0006A land drawing 4214840/G 08/2024.
Symbol `74xGxx:74LVC1G10`;
footprint `EMBER_Payload:TI_DBV0006A_SOT23_6`.
Signal names in the stock symbol are blank; functions are reconciled by
the manufacturer's physical number.

Walk counterclockwise from upper-left lead 1 in top/component view.
Coordinates below are footprint-local mm, Y down.
Every row uses the p1 function map and p24 land drawing above.

| Lead / function | Symbol pin / name / type | Pad | X / Y mm | View / direction | Evidence |
|---|---|---|---|---|---|
| 1 / A | 1 / blank / input | 1 | -1.30 / -0.95 | top, counterclockwise from upper-left | p1 / p24 |
| 2 / GND | 2 / GND / power_in | 2 | -1.30 / 0 | top, counterclockwise | p1 / p24 |
| 3 / B | 3 / blank / input | 3 | -1.30 / 0.95 | top, counterclockwise | p1 / p24 |
| 4 / Y, NAND | 4 / blank / output | 4 | 1.30 / 0.95 | top, counterclockwise | p1 / p24 |
| 5 / VCC | 5 / VCC / power_in | 5 | 1.30 / 0 | top, counterclockwise | p1 / p24 |
| 6 / C | 6 / blank / input | 6 | 1.30 / -0.95 | top, counterclockwise | p1 / p24 |

Six physical leads / six symbol pins / six electrical pads.
Zero duplicates, thermal pads, mechanical-only pads or intentional omissions.
Each SMD land is 1.1 × 0.6 mm, radius 0.05 mm, zero rotation/no drill,
F.Cu/F.Paste/F.Mask. Courtyard ±2.1 × ±1.7 mm, F.Fab upper-left chamfer,
upper-left silkscreen pin-1 dot. No 3D model; solder-mask settings and
fabrication DFM remain carrier-level checks.

Disposable symbol U2 was queried/rendered; footprint U2 was placed
at (20,20) with 0° rotation on F.Cu after the user closed KiCad.
All six placed pad coordinates were read back through Konnect's file fallback
and match local positions plus that origin.
[Package render](payload_permission_acceptance-package-detail.png) and
[full SVG](payload_permission_acceptance-package.svg) were inspected against
the manufacturer drawings. The scratch PCB contains that package only and
has no routed circuit or manufacturing-readiness claim.

Earlier unwired draft exports are historical evidence superseded by the final
files above. Protected sources were mutated only by Konnect; successful atomic
mutations plus readback/export establish saved file state. The live save
command cannot run while KiCad is closed; there are no pending live changes.

## Recheck

From the payload_compute directory:

```sh
python3 design/permission_control_study.py
python3 design/validation/check_permission_study.py
```

These checks do not establish connector transient protection, source-switch
defaults/telemetry, asynchronous hazards, board loading, rail discharge timing
or Jetson compatibility.
