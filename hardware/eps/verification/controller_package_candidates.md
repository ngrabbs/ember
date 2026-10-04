# Controller package candidates

2026-10-04. All library and scratch-project mutations used Konnect. The existing EPS schematic and board were not changed. These are disposable candidates, not accepted production parts.

## CAN A/B: Texas Instruments TCAN3413DR

Authority: [SLLSFS8A, Rev A, November 2023](https://www.ti.com/lit/ds/symlink/tcan3413.pdf), p.3 Figure 4-2 and Table 4-1; current appended D0008A package drawing 4214825/C, February 2019, PDF pp.42–44. The D package is SOIC-8 without an exposed pad. Symbol `Ember_EPS_Candidates:TCAN3413D_DRAFT`; current candidate footprint `Ember_EPS_Candidates:TI_D0008A_SOIC8_3.9x4.9mm_P1.27mm_DRAFT`. The original generic footprint remains a comparison only. DR is the reel order code. Pin 5 is VIO for this exact device; it must not be treated as the TCAN3414 shutdown input.

Every row uses top/component view, counterclockwise from the upper-left pin-1 key. Coordinates are local KiCad mm, +X right, +Y down, derived from the current custom comparison instance U4 at (48,9). Symbol/library readback and schematic instances U2/U3 match the following mapping.

| Physical lead | Function / symbol name | Symbol type | Footprint pad | Local X / Y mm | Evidence |
|---|---|---|---|---|---|
| 1 | TXD | input | 1 | -2.700 / -1.905 | p.3 Fig 4-2; U4 exported pad readback |
| 2 | GND | power_in | 2 | -2.700 / -0.635 | same |
| 3 | VCC | power_in | 3 | -2.700 / 0.635 | same |
| 4 | RXD | tri_state | 4 | -2.700 / 1.905 | same |
| 5 | VIO | power_in | 5 | 2.700 / 1.905 | same |
| 6 | CANL | bidirectional | 6 | 2.700 / 0.635 | same |
| 7 | CANH | bidirectional | 7 | 2.700 / -0.635 | same |
| 8 | STB | input | 8 | 2.700 / -1.905 | same |

Counts: 8 physical leads, 8 symbol pins, 8 unique electrical pads, no duplicates or mechanical holes. Front Cu/Mask/Paste layers; no assigned nets in this unwired test. IPC-2581 supplies the dimensions omitted by Konnect's pad query: 1.95 × 0.60 mm rounded rectangles, 0.15 mm corner radius, 1.27 mm pitch, 4.95 mm row-center spacing. TI's example uses 1.55 × 0.60 mm, 0.05 mm radius, 5.4 mm row spacing. Generic geometry is therefore not an exact reproduction; select and justify the assembly land pattern before acceptance. Disposable schematic and board renders show the correct upper-left key and direction.

## Clock: ECS ECS-3225MV-160-BN-TR

Authority: [ECS-3225MV Rev.2026](https://ecsxtal.com/store/pdf/ECS-3225MV.pdf), p.1 Figure 1 top/side/bottom views, pad-function table and Figure 2 land pattern; p.2 frequency code 160. Symbol `Ember_EPS_Candidates:ECS_3225MV_DRAFT`; custom footprint `Ember_EPS_Candidates:ECS_3225MV_3.2x2.5mm_DRAFT`.

The bottom view is mirrored relative to the top view. The chosen component/top view has pin 1 at lower left, then pin 2 lower right, pin 3 upper right, pin 4 upper left, counterclockwise. Local KiCad coordinates use +Y down. All rows are grounded in p.1 Figure 1 top view, the pad-function table and Figure 2; the placed custom footprint is independently present in the IPC-2581 export as Y2 (the schematic oscillator is Y1; these are comparison instances, not a synchronized PCB).

| Physical lead | Function / symbol name | Symbol type | Footprint pad | Local X / Y mm |
|---|---|---|---|---|
| 1 | Tri-state control / EN | input | 1 | -1.100 / 0.800 |
| 2 | GND | power_in | 2 | 1.100 / 0.800 |
| 3 | Output / OUT | tri_state | 3 | 1.100 / -0.800 |
| 4 | VDD | power_in | 4 | -1.100 / -0.800 |

Counts: 4 terminals, 4 symbol pins, 4 exported electrical pads, no duplicates or mechanical holes. The custom footprint follows ECS's suggested 1.40 × 1.20 mm rectangular lands with 2.20 × 1.60 mm center spacing. Body 3.2 × 2.5 mm; 0.25 mm courtyard allowance; front Cu/Mask/Paste. Library graphics and the disposable board render confirm a lower-left fabrication chamfer and pin-1 silk dot. The initial dot sat outside the rectangular courtyard. The library courtyard now extends to X=-2.8/+2.05 and Y=±1.65 mm, enclosing the dot; a fresh Y3 instance was placed and rendered after the edit. The older Y2 retains the original geometry as a comparison. No 3D model is assigned.

The installed Abracon ASE comparison footprint uses 1.30 × 1.10 mm rounded lands, 2.10 × 1.65 mm center spacing and 0.25 mm corner radius, so it was not assigned to the oscillator schematic instance. The custom candidate was assigned instead.

**Direct instance-pad query unavailable; independent export readback verified:** `place_component` reported Y2 saved successfully, and the independent IPC-2581 export contains Y2 and the correct four local pins/rectangular primitive. `get_component_pads(Y2)` nevertheless returns “Footprint 'Y2' not found.” Read-only reference-field inspection showed that this custom instance uses legacy `fp_text reference`, while the working stock instances use modern Reference properties. That is a plausible tool-reader limitation, not a demonstrated missing footprint. GenCAD additionally exports the same reference and four pins. The direct query remains unavailable; both independent exports serve as the instance readback evidence. No protected files were patched to alter this format.

## Status and evidence

**INCOMPLETE acceptance.** The custom symbols retain empty default Footprint/Description properties because the available create-symbol interface does not set them; explicit scratch instance assignments are present. The symbols' pin maps and current custom land geometry passed readback, but default library metadata and final assembly settings remain open. No electrical function, firmware failover, clock timing, final fit or assembly process was tested.

Scratch project: `/Users/nick/Documents/ChatGPT/EMBER/eps-rev-b-study/package-check-2026-10-04/package_check.kicad_pro`. Reviewed exports there: `controller_symbols.png`, `controller_packages.svg`, `controller_packages-detail.png`, `controller_packages-ipc2581.xml`. The board render contains page-frame overlays and comparison parts outside the original 20 × 20 mm test outline; it is a geometry test, not fabrication output. IPC-2581 Y coordinates are opposite KiCad's local Y convention; the tables above normalize them.

[Konnect readbacks](evidence/2026-10-04_controller_packages.json). The MCU geometry update is recorded in [its candidate verification](stm32_gp_candidate_verification.md).

## Manufacturer pattern and signal draft update — 2026-10-04

The new TI footprint follows the D0008A example: 1.55 × 0.60 mm rounded lands, radius 0.05 mm, row centers 5.4 mm and pitch 1.27 mm. All eight numbers, centers and dimensions passed IPC-2581 comparison. The current CAN table above describes this custom footprint; the earlier generic-geometry paragraph is historical comparison. Its courtyard includes body and pin-1 marker; top/bottom silk bars avoid the lands. The new MCU footprint follows ST Figure 40. Fresh custom oscillator Y3 carries the revised courtyard. All 44 unique electrical pads across U4/U5/Y3 passed numerical checks; no extra exposed/mechanical pad or drill is intended. All three individual renders were inspected for key, direction, body and courtyard. See [exported readback](evidence/2026-10-04_manufacturer_patterns_readback.json), [IPC-2581](evidence/2026-10-04_manufacturer_patterns-ipc2581.xml) and [GenCAD](evidence/2026-10-04_manufacturer_patterns.cad). Symbol-library defaults remain unassigned; explicit scratch schematic footprints are current. Assembly mask/stencil settings remain to be set for the final board.

Seven named signal links now join the scratch MCU to both transceivers and the oscillator. The saved KiCad netlist contains exactly the intended two endpoints on each link: A RX U1.22/U2.4, A TX U1.23/U2.1, A STB U1.1/U2.8; B RX U1.15/U3.4, B TX U1.16/U3.1, B STB U1.27/U3.8; HSE U1.2/Y1.3. Konnect wire validation reports zero floating ends and zero shorted named nets. Render inspection confirms readable labels within the sheet. [Connectivity evidence](evidence/2026-10-04_controller_signal_links_verified.json).

**Electrical draft INCOMPLETE:** ERC reports 48 errors: 37 unconnected pins, 10 undriven power pins and one undriven oscillator-enable input. Power, reset, decoupling, pull-ups, CAN bus interfaces/protection and the remaining MCU interfaces are not yet implemented. No issue was hidden with no-connect flags or power flags. The package-test PCB is not synchronized to the signal schematic and is not a layout proposal. Next is the controller support circuit and bus interfaces.

## Controller support progress — 2026-10-04

[Controller support draft](../verification/controller_support_draft.md) now adds essential-supply connections, 13 capacitors, five startup pull-ups and the NRST capacitor. Eleven exported named nets passed exact endpoint comparison; wire and short checks passed. Current ERC is 26 errors, reflecting remaining interfaces and the absent source in the standalone sheet. The earlier 48-error signal-only result is historical. CAN symbol v3 and oscillator v2 improve ground-pin drawing placement while preserving package mapping.
