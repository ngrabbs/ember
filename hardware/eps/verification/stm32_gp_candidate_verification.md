# STM32G0B1KET6 GP candidate verification

2026-10-04. Draft symbol created through Konnect in `hardware/eps/libraries/Ember_EPS_Candidates.kicad_sym`. It is registered only in the disposable validation project, not the EPS project. The first draft remains as a superseded geometry trial; use `STM32G0B1KET6_GP_DRAFT_v2` for continued validation.

Manufacturer: STMicroelectronics. Exact candidate: STM32G0B1KET6, GP LQFP32. Authority: [DS13560 Rev 6](https://www.st.com/resource/en/datasheet/stm32g0b1ke.pdf), Figure 3 (printed p.36), Figures 39–40 and Table 82 (pp.126–129). Symbol ID: `Ember_EPS_Candidates:STM32G0B1KET6_GP_DRAFT_v2`. Current candidate footprint: `Ember_EPS_Candidates:ST_LQFP32_7x7mm_P0.8mm_DRAFT`. The original generic footprint is retained only as a comparison instance.

The symbol and disposable placed instance both read back 32 unique pins. A disposable board footprint reads back 32 unique front-side pads. No exposed pad, duplicate pad, or mechanical hole is present in this LQFP32 package. All 32 pin functions were compared with the intended manufacturer-derived GP allocation. Pin-1 marker is at upper left; top/component view numbering runs counterclockwise, down the left side, across the bottom, up the right side, and across the top. The current custom footprint is the disposable U5 at (48,25) mm. Local pad coordinates below subtract that placement, with +X right and +Y down.

| Physical lead | Function / symbol name | Symbol type | Footprint pad | Local X / Y mm | View / direction | Authority |
|---|---|---|---|---|---|---|
| 1 | PB9 | bidirectional | 1 | -4.300 / -2.800 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 2 | PC14 | bidirectional | 2 | -4.300 / -2.000 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 3 | PC15 | bidirectional | 3 | -4.300 / -1.200 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 4 | VDD/VDDA | power_in | 4 | -4.300 / -0.400 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 5 | VSS/VSSA | power_in | 5 | -4.300 / 0.400 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 6 | PF2/NRST | bidirectional | 6 | -4.300 / 1.200 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 7 | PA0 | bidirectional | 7 | -4.300 / 2.000 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 8 | PA1 | bidirectional | 8 | -4.300 / 2.800 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 9 | PA2 | bidirectional | 9 | -2.800 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 10 | PA3 | bidirectional | 10 | -2.000 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 11 | PA4 | bidirectional | 11 | -1.200 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 12 | PA5 | bidirectional | 12 | -0.400 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 13 | PA6 | bidirectional | 13 | 0.400 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 14 | PA7 | bidirectional | 14 | 1.200 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 15 | PB0 | bidirectional | 15 | 2.000 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 16 | PB1 | bidirectional | 16 | 2.800 / 4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 17 | PB15 | bidirectional | 17 | 4.300 / 2.800 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 18 | PA8 | bidirectional | 18 | 4.300 / 2.000 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 19 | PA9 | bidirectional | 19 | 4.300 / 1.200 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 20 | VDDIO2 | power_in | 20 | 4.300 / 0.400 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 21 | PA10 | bidirectional | 21 | 4.300 / -0.400 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 22 | PA11/PA9 | bidirectional | 22 | 4.300 / -1.200 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 23 | PA12/PA10 | bidirectional | 23 | 4.300 / -2.000 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 24 | PA13 | bidirectional | 24 | 4.300 / -2.800 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 25 | PA14/BOOT0 | bidirectional | 25 | 2.800 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 26 | PD0 | bidirectional | 26 | 2.000 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 27 | PD1 | bidirectional | 27 | 1.200 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 28 | PD2 | bidirectional | 28 | 0.400 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 29 | PD3 | bidirectional | 29 | -0.400 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 30 | PB6 | bidirectional | 30 | -1.200 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 31 | PB7 | bidirectional | 31 | -2.000 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |
| 32 | PB8 | bidirectional | 32 | -2.800 / -4.300 | Top; CCW from upper-left key | Figure 3 p.36; package pp.126–129 |

The disposable schematic was rendered and visually inspected after moving supply pins to avoid the part-name overlap. The footprint export was rendered and inspected for front-side orientation, key marker, body outline and courtyard. The footprint centers show 0.8 mm pitch and the fabrication body is nominally 7 × 7 mm, consistent with the package authority. The 2026-10-04 IPC-2581 export closes the missing pad-size evidence: all 32 package pins use 1.50 × 0.50 mm rounded rectangles (swapped on top/bottom rows), radius 0.125 mm. Pad centers remain 4.175 mm from the body center, giving inner/outer radial edges of 3.425/4.925 mm. ST's example land pattern on p.129 uses 1.20 × 0.45 mm lands with inner/outer row distances 7.4/9.8 mm, corresponding to center offset 4.3 mm. The generic lands extend 0.275 mm farther inward and are 0.05 mm wider; that difference does not by itself prove incompatibility, but the final assembly land-pattern choice needs justification. Copper, mask and paste primitives are exported on their respective layers; assembly tolerance and mask/stencil settings remain open. Export: `/Users/nick/Documents/ChatGPT/EMBER/eps-rev-b-study/package-check-2026-10-04/controller_packages-ipc2581.xml`. Its Y coordinates are inverted relative to the KiCad coordinate table above.

**Verdict: INCOMPLETE package acceptance.** This draft is suitable for continued disposable validation, not real Rev B placement. The symbol library also has an empty default Footprint field; the disposable schematic instance has the explicit candidate footprint assigned. Complete library metadata/default assignment and the assembly land-pattern decision before acceptance. Alternate-function/remap and reset-state requirements remain in the controller specification.

[Raw readback evidence](evidence/2026-10-04_corrected_mcu_candidate.json). Scratch project: `/Users/nick/Documents/ChatGPT/EMBER/eps-rev-b-study/package-check-2026-10-04/package_check.kicad_pro`. No existing EPS schematic or board was edited, and no electrical operation, MCU firmware or final board fit was tested.

## Manufacturer pattern update — 2026-10-04

A custom ST-reference land pattern was created through Konnect and assigned to the scratch schematic instance. Figure 40 was independently rechecked through ST’s [DS13560 Rev6 family datasheet](https://www.st.com/resource/en/datasheet/stm32g0b1vb.pdf), p.129, when the KE URL timed out. The current 32 pads are rectangular, 1.20 × 0.45 mm, center offset 4.3 mm, pitch 0.8 mm. All 32 numbers, centers and dimensions passed comparison with the saved IPC-2581 readback; GenCAD independently exports the instance. Body/fab outline 7 × 7 mm; courtyard ±5.15 mm; top-left pin-1 silk dot at (-4.1,-4.1), front-side orientation. The MCU image was inspected after creation. This closes the earlier generic-land-pattern selection issue; the preceding generic geometry paragraph remains historical comparison evidence. Default symbol-library footprint metadata is still empty; the placed scratch instance is explicitly assigned. Full production acceptance and electrical support remain incomplete.
