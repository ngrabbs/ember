# U10 ADE-1+ pin and package audit

Reviewed 2026-09-09. Electrical lead mapping and solder-land geometry accepted. Stale schematic editor state has been discarded with user authorization; 3D/stack-height acceptance remains open.

Manufacturer: Mini-Circuits. Exact part: ADE-1+ (RoHS suffix +), CD636 package. Sources visually inspected in the browser: [ADE-1+ datasheet](https://www.minicircuits.com/pdfs/ADE-1+.pdf), page 1; [CD family mechanical drawing](https://www.minicircuits.com/case_style/CD636.pdf), page 1; [98-PL052 mounting configuration](https://www.minicircuits.com/pcb/98-pl052.pdf), page 1, revision C dated 12/01/06. The datasheet revision was not transcribed from its small footer; use the accessed manufacturer document, not the prior ADE-6 datasheet. The mechanical drawing explicitly covers CD541/CD542/CD636/CD637.

Existing symbol: RF_Mixer:ADE-6, used as a pin-compatible stand-in. Existing footprint: RF_Mini-Circuits:Mini-Circuits_CD542_LandPatternPL-052. The shared drawing confirms that CD542 and CD636 have the same lead pitch and land dimensions; their case heights differ. No renumbering or copper replacement is required for the ADE-1+ lead map.

The case drawing shows the index dot on the component body adjacent to lead 1, bottom-left in that drawing, with 1–2–3 across the lower edge and 6–5–4 across the upper edge. This is the indexed component view, not a mirrored solder-side view. Rotating that indexed drawing 90 degrees clockwise puts lead 1 at the footprint's upper-left. The PL052 mounting drawing likewise marks the unit index at lead 1 and corroborates the land orientation.

| Physical lead | Function | Symbol pin/name/type | Primary footprint pad | Local X,Y mm | Evidence |
|---|---|---|---|---|---|
| 1 | Ground | 1 / GND / power_in | 1 | -2.54,-2.54 | Index-adjacent lead; datasheet and CD drawing |
| 2 | IF | 2 / IF / output | 2 | -2.54,0 | Next along indexed row |
| 3 | RF | 3 / RF / input | 3 | -2.54,+2.54 | End of indexed row |
| 4 | Ground | 4 / GND / passive | 4 | +2.54,+2.54 | Opposite lead 3 |
| 5 | Ground | 5 / GND / passive | 5 | +2.54,0 | Opposite lead 2 |
| 6 | LO | 6 / LO / input | 6 | +2.54,-2.54 | Opposite lead 1 |

Six physical leads map to six logical pad numbers. The footprint has 17 pad objects: six primary SMD lands, eight plated ground stitching holes and three additional ground-copper shapes. These extra ground objects are intentional PL052 features, not extra physical device leads. Symbol grounds 1/4/5 are stacked at one schematic location; all three electrical pins were verified by tool readback. The symbol's input/output types describe a schematic convention for a passive mixer, not additional supply pins.

Primary lands are 2.54 × 1.651 mm; along-row pitch is 2.54 mm and opposing row-center separation is 5.08 mm. The mechanical drawing's suggested land span is 7.62 mm, consistent with these lands. Every placed pad's number, geometry, layer set and position matches the stock footprint translated to U10's current origin. The footprint's 0.508 mm ground holes correspond to the PL052 drawing. That drawing's 0.064-inch RF trace width is for its stated Rogers stackup; it must not replace this project's independently derived 0.358 mm microstrip width.

## Verification and metadata

Queried the stock symbol and footprint through Konnect. Created disposable symbol and PCB placements and inspected both rendered outputs. All 17 placed pads match the library, and actual nets are 1/4/5=GND, 2=Net-(U10-IF), 3=Net-(U10-RF), 6=Net-(U10-LO).

Corrected the saved schematic and PCB metadata to ADE-1+, Mini-Circuits, CD636, correct datasheet URL and 0.5–500 MHz RF/LO range with +7 dBm nominal LO drive. Added the audit reference and 4.11 mm maximum package-height field. PCB verification proves all 689 copper items and all 141 footprint positions/pad nets unchanged. See `u10_identity_validation.json`.

The Schematic Editor was subsequently found open on RF_Switch with an unsaved marker. The user confirmed they had made no changes and authorized discarding that stale editor state. The editor was closed with Discard Changes, and all saved schematic files were verified unchanged against the snapshot. Saved U10 metadata was reread through Konnect. This reconciliation does not constitute a fresh full ERC or a schematic-to-PCB update.

## Remaining checks

- The linked STEP model is Mini-Circuits_CD542.step. CD542 height is 2.84 mm max; CD636 is 4.11 mm max. Preserve the accepted XY land pattern, but replace/verify the 3D representation and use 4.11 mm for mechanical clearance. Current 3D-model clearance is not accepted.
- Layout/mixer-port routing and ground transitions remain open. Verify LO amplitude at the mixer, termination, conversion loss and filter response under actual operating conditions.
- RX input chain to place: C55 → L12/C56 → C60 → L13/C64 → C67 → U9. C56/L12/C60/L13/C64/C67 remain in the unplaced group. U9 output couples through C75 to U10 RF and takes DC bias through L16. This pass did not move or route these parts.
