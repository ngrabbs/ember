# U8 ADL5602 identity and pin-map audit

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


Reviewed 2026-09-09. **Pin mapping accepted; amplifier bias/layout and thermal acceptance remain open.**

Manufacturer: Analog Devices. Exact part: **ADL5602ARKZ-R7**, package RK-3, three-lead SOT-89. Existing LCSC C496494 resolves to that MPN. Sources: [ADI Rev. A datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/ADL5602.pdf), pp. 8, 12, 15; [LCSC listing](https://www.lcsc.com/product-detail/C496494.html). Manufacturer diagrams were visually inspected in the browser.

KiCad symbol: `RF_Amplifier:ADL5610`, deliberately reused for its compatible three-pin map. The library name does not authorize an ADL5610 purchasing substitution. Value/MPN, manufacturer, description and datasheet fields now explicitly identify ADL5602 on both schematic and PCB. Footprint: `Package_TO_SOT_SMD:SOT-89-3`.

## Physical lead reconciliation

Coordinates are library-local millimeters, component-side top view at 0°; negative Y is upward. Starting at the upper-left input lead in ADI Figure 2, the left-side leads run downward 1 → 2 → 3. Figure 21 rotates this top view so leads read left-to-right along the bottom; its separately labeled bottom view is not used to number PCB pads.

| Physical lead | Function | Symbol pin / name / type | Footprint pad | Local X,Y mm | Evidence / view |
|---|---|---|---|---|---|
| 1 | RFIN | 1 / blank / input | 1 | −1.950, −1.500 | ADI p.8 Fig.2/Table4; top view, upper-left |
| 2 | GND | 2 / GND / power_in | 2 | −1.8625, 0 | ADI p.8; top view, middle-left |
| 3 | RFOUT and DC bias | 3 / blank / output | 3 | −1.950, +1.500 | ADI p.8; top view, lower-left |
| Exposed paddle/tab (2) | GND, internally tied to 2 | Same pin 2 | Same custom pad 2 | Pad union bounds X −2.600…+2.000, Y −0.8665…+0.8665 | ADI p.8 note; top view, body/tab |

Three electrical symbol pins and three logical footprint pads represent three leads plus the shared ground paddle. Pad 2 is a continuous custom copper polygon, not merely its small anchor rectangle. The 1.5 mm lead pitch and 3.0 mm input-to-output spacing agree with the package drawing. The generic footprint differs from ADI's recommended thermal land pattern; thermal-via coverage and assembly acceptance are separate open checks.

## Verification

- Konnect search found no ADL5602 symbol; queried the existing ADL5610 symbol and stock SOT-89 footprint.
- Created independent disposable schematic and PCB placements. Inspected both renders and native pad geometry; no mirror, reversed lead, missing tab or accidental duplicate was found.
- Actual U8: pad 1 `TX_437`, pad 2 `GND`, pad 3 `Net-(C84-Pad1)`. Native placed pad geometry matches the library translated to (148.0136,139.8436), without rotation.
- Updated metadata through Konnect (schematic) and native KiCad field APIs (PCB). Exported component fields verify the MPN and datasheet. The standalone TX export's nine emitted nets are identical before/after, but the known hierarchy/export limitation means this is not a new full-design ERC pass.
- All 691 copper items and all 141 footprint positions/pad nets are unchanged. RF class assignments remain present. No routing or circuit-value change was made in this audit.

## Required amplifier work before routing release

1. Resolve L15's actual part (existing C337958, 220 nH/0805). ADI's reference circuit uses 470 nH plus 68 pF, 1.2 nF and 1 µF supply bypassing. The present C71/C76 are 100 nF/10 µF. A difference alone does not prove failure; qualify RF impedance, current, DC resistance and bypass parasitics, or adopt a verified reference network.
2. Move/arrange the bias tee near U8 before completing RFOUT→C84. Current RFOUT and L15 output-pad centers are about 16 mm apart. Review two isolated old RFOUT vias, then route over continuous L2 ground. C84 is also a tuned filter coupling capacitor; do not replace its 3.9 pF value with the reference circuit's coupling value without redesigning the filter.
3. Check ground-tab stitching and heat removal. At 5 V the datasheet gives 89 mA typical, 106 mA maximum supply current under its stated test conditions, and about 0.45 W typical dissipation. The old 60 mA assumption is inadequate.
4. Recompute the complete EPS rail budget, including temperature/tolerances, RX load, Pico operating state and the switch circuitry; verify supply continuity and drop. Do not treat the old “<300 mA total” note as validated.
