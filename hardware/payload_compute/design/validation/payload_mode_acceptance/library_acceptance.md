# Bench-mode latch physical pin map

SN74LVC1G373DBVR: TI SCES528F (May 2017), pin diagram page 3,
DBV0006A drawing 4214840/G (08/2024). Source:
https://www.ti.com/lit/ds/symlink/sn74lvc1g373.pdf
Top view, pin 1 upper left; walk down left 1–3 then up right 4–6.
PCB coordinates are front placement, local mm with positive Y down.

| Lead | Function / symbol pin / type | Pad | x, y mm |
| --- | --- | --- | --- |
| 1 | LE / 1 / input | 1 | -1.30, -0.95 |
| 2 | GND / 2 / power_in | 2 | -1.30, 0 |
| 3 | D / 3 / input | 3 | -1.30, 0.95 |
| 4 | Q / 4 / tri_state | 4 | 1.30, 0.95 |
| 5 | VCC / 5 / power_in | 5 | 1.30, 0 |
| 6 | OE_N / 6 / input | 6 | 1.30, -0.95 |

Symbol `74xGxx:74LVC1G373`; footprint `EMBER_Payload:TI_DBV0006A_SOT23_6`.
Six physical leads, six symbol pins, six electrical pads; no duplicates,
exposed pads, mechanical pads or holes. Lands 1.10 × 0.60 mm, corner
radius 0.05 mm, zero-rotation SMD F.Cu/F.Mask/F.Paste; no drill.
Courtyard ±2.10 × ±1.70 mm. Fab chamfer and silk dot mark upper left.
No 3D model. Final reference silk placement is not accepted by this study.

Library and disposable instance query-back: `payload_mode_acceptance-library-evidence.json`.
Disposed footprint U2=(100,100), front, rotation 0, live IPC pad readback.
Symbol and package renders inspected before wiring. Accepted for bounded
study; sourcing, passives and hardware behavior remain unqualified.
Lock flip-flop and AND gate reuse the accepted maps in ../../latch_library_acceptance.md.

SN74LVC1G17DBVR: TI SCES351Y October 2025, top-view pin diagram p3,
DBV0005A land drawing 4214839/K August 2024. Source:
https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf
Same front-view numbering walk, 1–3 down left then 4–5 up right.

| Lead | Function / symbol pin / type | Pad | x, y mm |
| --- | --- | --- | --- |
| 1 | NC / 1 / no_connect | 1 | -1.30, -0.95 |
| 2 | A / 2 / input | 2 | -1.30, 0 |
| 3 | GND / 3 / power_in | 3 | -1.30, 0.95 |
| 4 | Y / 4 / output | 4 | 1.30, 0.95 |
| 5 | VCC / 5 / power_in | 5 | 1.30, -0.95 |

Five physical leads, five symbol pins including NC, five pads. Pad 1 is
intentionally electrically unconnected. No duplicated/mechanical/thermal pads.
Symbol `74xGxx:74LVC1G17`; footprint `EMBER_Payload:TI_DBV0005A_SOT23_5`.
Land size, radius, layers, courtyard and pin-1 key follow the six-lead DBV
geometry above, with no right-middle land. Live U4=(110,100), front rotation 0,
read back and rendered with U2 before wiring. No bottom/mating view involved.
