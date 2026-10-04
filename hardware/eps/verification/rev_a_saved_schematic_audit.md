# EPS saved schematic and Rev A fabrication comparison

Audit dated 2026-10-03. The current saved EPS schematic is not an accepted electrical baseline for Rev B. A read-only KiCad netlist export exposes substantial connectivity gaps and differences from the Rev A fabrication BOM. These findings describe the saved design, not the hand-reworked physical board. Do not infer that the fabricated board has every exported gap.

**Verdict: INCOMPLETE.** Exported connectivity and schematic images were inspected, but formal Konnect ERC/short checks and candidate library pin-map acceptance could not run. The requested toolsets reported successful loading, while their callable tools remained absent from this session. No KiCad source or library was changed.

[Rev B implementation handoff](../design/rev_b_bom_and_schematic_checklist.md) · [Exported netlist](evidence/2026-10-03_saved_schematic/eps.xml) · [BOM/net comparison](evidence/2026-10-03_saved_schematic/comparison.json) · [Provenance and source hashes](evidence/2026-10-03_saved_schematic/provenance.json)

## Package and wire reconciliation — 2026-10-04

[Complete query evidence](evidence/2026-10-04_package_and_wire_readback.json) records the next readback pass. The symbol resolved by Konnect for `MCU_ST_STM32G0:STM32G0B1KETx` fails GP pin-map acceptance against ST DS13560 Rev 6, Figure 3, printed page 36. It reports pin 17 PB2 instead of PB15, pin 20 PC6 instead of VDDIO2, and pins 26–29 PA15/PB3/PB4/PB5 instead of PD0/PD1/PD2/PD3. A disposable schematic placed through Konnect and rendered through KiCad shows those same conflicting functions, so this is not merely a textual inspection-response mismatch. Native library content versus Konnect inheritance/resolution remains to be distinguished; this evidence establishes that the current Konnect placement path produces the wrong GP symbol. Reject this symbol for the proposed STM32G0B1KET6. Do not change the chosen MCU to fit a mislabeled symbol or substitute the N variant automatically. The installed N-suffixed symbol also requires independent acceptance; its name alone is not evidence.

The proposed manufacturer-derived GP pin allocation remains the intended allocation. Prepare a corrected project-owned symbol, then complete physical footprint lead joins and disposable schematic/board inspection before real placement. The footprint-info response for the candidate LQFP reports 32 pads and graphics but omits individual pad coordinates, despite the tool description; physical pad readback remains incomplete. TCAN3413 and ECS-3225 exact-symbol searches return no matches. Do not substitute another TCAN33x symbol on name similarity.

Wire reconciliation also qualifies the earlier NTC conclusion. At pin 9 the returned coordinate is (283.21, 135.89) mm and a wire endpoint is at the same coordinate within floating-point rounding. Pin 10 is at (283.21, 138.43) mm, exactly matching a returned wire endpoint. A trace-from-point call finds the pin-10 wire but still returns no named net. Thus `net: null` alone is not sufficient to claim an absent wire or prove the repair needed. The previous exported-netlist omissions remain unresolved against the wire inventory and rendered geometry. Investigate symbol transformation/import and exported connectivity before moving wires or increasing snapping tolerance.

Only the disposable package-check schematic was created and populated, through Konnect. The EPS project and its libraries remain unchanged.

## Konnect follow-up — 2026-10-04

The tool-loading workaround succeeded after restarting Codex. Direct Konnect schematic checks are now callable; the earlier tool-availability limitation below is historical. This follow-up was read-only and did not alter KiCad source or libraries. [Raw tool evidence](evidence/2026-10-04_konnect_checks.json) records complete responses.

- U1 pins 9 NTCBIAS and 10 NTC each return `net: null`, corroborating the exported thermistor connectivity gap.
- U2 returns connected VIN and GND only; RT, EN, SW, BST, SS and FB return `net: null`.
- Charger short scan reports zero shorts. This is limited to the charger sheet and does not establish intended connectivity or whole-design acceptance.
- A 0.05 mm near-miss dry run finds zero fixes. Do not apply automatic snapping as an assumed repair; this test does not identify the import failure mechanism.
- Hierarchical sheet-pin validation reports zero issues. A design lacking intended hierarchy interfaces can pass this matching check, so it does not resolve the separate sheet-local supply/bus nets.
- Root ERC returns 245 violations: 34 errors and 211 warnings. Rule counts are 8 power-pin-not-driven, 25 dangling wires, 1 unconnected pin, 77 footprint-library issues, 124 symbol-library issues, 5 isolated pin labels and 5 unconnected wire endpoints. Some power-input classifications may themselves require symbol correction; do not treat all as independent physical faults.

The ERC response contains coordinates and wire lengths inconsistent in scale with direct pin coordinates and the rendered schematic; retain the response as tool evidence but do not use its coordinates to target edits until report units/normalization are reconciled. The original exported connectivity remains stronger corroboration for the identified NTC and regulator gaps.

**Current verdict remains INCOMPLETE.** Package maps, whole-design short/connectivity coverage, PCB DRC and physical assembly reconciliation remain outstanding. The tool-discovery blocker is resolved for schematic work. PCB IPC is currently unconfigured and will be needed for live board operations.

## Inspection coverage

The root schematic export traversed `eps`, `Regulation` and `Solar_Charger`. It produced 77 component records and 18 connected nets. Component reference strings were unique in the XML, but KiCad reported annotation errors during export; their cause remains unresolved. Unique XML references do not clear that warning.

The charger and regulation SVG exports were rendered and visually inspected. They show wiring that is absent from the connectivity export at several IC pins. The visual drawing alone therefore cannot establish electrical connection. Direct pin-endpoint checks and ERC must resolve the discrepancy before reuse. Root SVG was exported but not visually accepted in this audit.

## Findings requiring resolution before reuse

| Finding | Export evidence | Required action |
|---|---|---|
| Thermistor qualification has no exported connection | U1 pins 9 `NTCBIAS` and 10 `NTC` are absent from all connected nets, despite a drawn header/resistor arrangement | Inspect actual saved pin/wire endpoints through Konnect; rebuild the verified bias/NTC network in Rev B. Physical Rev A damage still needs separate inspection. |
| Other charger pins are outside connected nets | U1 pins 5, 6, 8, 11, 16, 17, 21 and 22 are also absent | Classify each pin against its function; intentional unused SYNC differs from missing sense/drive/regulator wiring. Verify endpoints and device requirements rather than marking every absence identically. |
| Converter connectivity is incomplete in export | Each of U2/U3 has only VIN pin 3 and GND pin 4 represented; pins 1, 2, 5, 6, 7 and 8 are absent | Resolve RT, EN, SW, BST, FB and SS connectivity against the rendered circuit and device requirements. Do not reuse it as a connected converter. |
| PowerPath is split across sheet-local nets | `/Solar_Charger/VOUT_PP`, `/Regulation/VOUT_PP` and root `/VOUT_PP` are separate nets | Implement deliberate hierarchy/global connections under repository net naming; verify the charger actually feeds both buck VIN pins and the root test point. |
| Battery feed is split across sheets | Charger `/Solar_Charger/BATT_POS` is separate from root `/BATT_POS` feeding J10/J9 and H2.45/H2.46 | Resolve source-to-charger/stack connectivity; Rev B additionally requires the new protection/isolation boundaries. |
| I2C is split across sheets | Root `/I2C_SCL` contains H1.43 alone and `/I2C_SDA` contains H1.41 alone; charger pins 13/14 are on separate local nets | Reconcile Rev A interface evidence. For Rev B, keep the charger on the EPS-local bus and deliberately update stack ownership/semantics. |
| Reference assignments differ from fabrication | Release D1 is SS14; saved D1 is an LED. Release R1/R4 are current shunts; saved shunts are RS1/RS2 | Compare by circuit function and MPN, not reference alone. Reconcile design generations and physical assembly before carrying anything forward. |

These are critical baseline-reuse findings where required power/sense paths are not established. They are not a manufacturing-readiness verdict on the physical Rev A PCB. No DRC or copper-connectivity acceptance was performed.

## Baseline provenance investigation

Repository history and the fabrication archive show an Altium-to-KiCad conversion between the release artifacts and the current saved project. The release top-copper Gerber records `Altium Designer,26.5.0 (11)` as its generation software. ZIP entries carry 2026-04-25 timestamps; these are archive metadata, not a proven fabrication date.

The 2026-09-02 commit `d181fef` introduced the KiCad import and described the sheets as independent roots. Commit `e15b85f` explicitly records “attempt to convert altium to kicad, lost foot prints, not good”. Commit `344160a` then records hierarchy assembly, repair of symbol-to-footprint links, restoration of annotation after an attempted renumbering, and the duplicate J5/XT30 reassignment to J10. Its reported zero-warning PCB synchronization is a historical author statement about synchronization, not proof that power circuits were electrically verified.

Consequently, current KiCad reference assignments and exported connectivity cannot be treated as a direct record of the fabricated Rev A assembly. Conversion damage is a plausible contributor to the drawing/export disagreement; direct endpoint and ERC evidence is still needed to determine the mechanism. Do not infer that current missing netlist connections existed in the fabricated copper.

[History records and release hashes](evidence/2026-10-03_saved_schematic/baseline_history.json) preserve the evidence. Use the released Gerbers for fabricated geometry, the release BOM/CPL for recorded assembly, and the documented physical rework for deviations. Neither the old instructions nor the imported CAD overrides measured board connectivity.

## First bench investigation: thermistor path

The existing [bench record](../../../system/ground_station/eps_bench_setup.md) says no real thermistor was fitted and the substitute divider wiring remained unverified. Establish that path before another software bypass attempt:

1. With all sources disconnected, identify physical U1 pins 9 (NTCBIAS), 10 (NTC), their bias resistor, connector and analog return. Measure endpoint continuity, resistance and unintended bridges. Record photographs and the actual fitted resistor values against the fabrication assembly, not current refdes alone. The operator must supply these physical observations; none were obtained in this audit.
2. Reconstruct the divider on a controlled fixture first: NTCBIAS → matching 10 kΩ bias resistor → NTC node → 10 kΩ room-temperature substitute → quiet analog ground. Verify the physical chip pin map before board rework. This substitute is a diagnostic fixture, not a flight sensor or permission for unattended pack charging.
3. Capture the pulsed NTCBIAS and NTC waveforms together with ADC-valid, thermistor raw value, JEITA region, charger state/status and charger settings under normal firmware. The expected nominal divider ratio is one half while bias is active; use the temperature specification for other resistor cases.
4. If temperature qualification clears but charging remains absent, retain that result and investigate charge settings, individual group/pack voltage, current-sense connections and PowerPath behavior. A correct thermistor reading does not establish that charging must occur, especially near full battery voltage.

Record every physical repair separately from the saved-design reconciliation. No bench result or repair is claimed by this checklist.

## Fabrication BOM differences

The release CSV expands to 53 component references; the saved schematic has 77. There are 27 saved references absent from the release list, three release references absent from the saved list, and 36 shared references with different literal value/MPN strings. Some changes may be equivalent substitutions or documentation conventions; the comparison does not classify all 36 as electrical faults.

The release CPL contains 77 placements. Compared with the saved netlist, its reference-only differences are CPL-only `BT1, BT2, BT3, BT4, BT5, BT6, BT7, BT8, D2, D3, D4, TP6, TP7, TP8` and saved-only `C4, C40, D5, D6, J10, J5, J7, J9, R16, R17, R20, R21, RS1, RS2`; 38 common references have different literal comment/value strings. This shows that the 53-reference BOM is not the same inventory scope as the placement file. Counts alone cannot establish that the KiCad conversion matches the fabrication assembly.

The three absent release references are D2, D3 and D4. The saved schematic notes blocking diodes on the solar-face boards, so relocation is a hypothesis to reconcile, not a confirmed omission in the spacecraft. Newly listed connectors/test points also show that the release CSV is not a complete record of the current saved assembly.

U1 remains recorded as LTC4162EUFD-LADMTRPBF and U2/U3 as TPS62933FDRLR. This supports the current component-family baseline while leaving actual values, placement, connectivity and assembly acceptance unresolved. The comparison JSON preserves every changed string and each exported net member for follow-up.

## Rev B package mapping status

| Candidate | Manufacturer-side information already recorded | Remaining acceptance evidence |
|---|---|---|
| STM32G0B1KET6 | Proposed general-purpose LQFP32 allocation with 32 unique physical pin rows | Resolve exact existing symbol ID and footprint; join every pin to physical pad and coordinates; check drawing view and errata. |
| TCAN3413DR, two instances | Eight-pin SOIC function-to-net table in controller study | Read selected symbol and footprint through library tools; verify all eight joins, orientation and pad geometry. |
| ECS-3225MV-160-BN-TR | Manufacturer pad functions 1 enable, 2 ground, 3 output, 4 supply | Verify selected symbol/footprint pad coordinates and orientation against the package drawing. |

These are specification inputs, not accepted library maps. The [KiCad library skill](/Users/nick/.agents/skills/kicad-library/SKILL.md) requires readback using `get_symbol_info` and `get_footprint_info` and a complete physical-lead join before using package-sensitive parts. Those functions are unavailable here; no candidate symbol or footprint was created, selected as accepted, or placed.

## Next implementation actions

1. Restore callable Konnect schematic and library tools; run direct endpoint, short and ERC checks to resolve the drawing/export disagreement and annotation warning.
2. Preserve the fabricated baseline and identify the current schematic generation. Reconstruct verified circuits rather than copying apparently connected graphics.
3. Accept the MCU, transceiver and oscillator library maps and build the controller/CAN draft in a separate Rev B design through Konnect.
4. Close the power-circuit selections and simulator evidence from the existing specifications before a full schematic freeze.

The exported evidence is useful now, but neither saved connectivity nor package acceptance has passed the full review gate.
