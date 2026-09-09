# Comms board — review and repair checklist

## Current RF progress — single antenna

- [x] U10 electrical pin/land-pattern audit: ADE-1+ CD636 shares the PL052 land geometry with the existing CD542 footprint; six leads and 17 intentional pad objects reconciled. PCB metadata corrected without geometry changes. See `design/u10_ade1_pinmap.md`.
- [x] Discard stale unsaved schematic-editor state with user authorization. All saved schematic files verified unchanged against the snapshot; schematic editor is closed.
- [ ] Replace/verify U10's CD542 3D model for CD636 height: 4.11 mm maximum, versus 2.84 mm for CD542. Electrical land-pattern acceptance does not establish stack-height clearance.

- [x] TX input filter: placed C98, rebuilt resonator connections, routed C101/TP14 to U8. Removed 39 old copper items and added 22; no new local DRC violations, no remaining unconnected items on the three routed RF nets, and 755/755 L2 ground samples passed. See `design/input_filter_routing_validation.json`.
- [x] Resolved TP13/C93 overlap and rebuilt TRIPLER_OUT entrance/probe routing; 200/200 ground samples passed and no local DRC violations remain. See `design/tx_entrance_validation.json`.
- [ ] Continue RX filter placement and U10 physical pin/footprint audit; C56/L12/C60/L13 remain off-board.

- [x] U8 ground stitching: four vias outside the solder land, connected by two direct copper straps. Retained copper, footprint positions and pad nets unchanged. See `design/u8_ground_validation.json`.

- [x] U8 output/bias routing: removed obsolete +5 V short at C84, moved L15/C71/C76, routed RFOUT and supply feeder. Saved-board geometry/net checks passed; 1,365 RF ground samples passed. See `design/u8_bias_routing_validation.json`.

- [x] Added and wired the PE4259 switch sheet: J9 → C102 → U11; RF1 → TX_OUT, RF2 → RX_IN. Added 3.0 V regulator, tolerant control buffer, decoupling and pull-downs.
- [x] Reused existing TX_ACTIVE on J6.14 / Pico GP10; GP22 stays spare. Verified the three IC package maps and disposable placements.
- [x] Pre-D15 native connectivity: 124 components / 181 nets / 433 nodes; all 401 previous nodes preserved. Native ERC: 0 active errors, 0 active warnings; existing 2 exclusions and 4 ignored checks remain.
- [x] Synchronized all 11 switch parts into the PCB and placed them near J9; moved C55/C94 beside the switch. Removed J5 and four obsolete TX/RX antenna feed segments. J9 is the sole antenna connector.
- [x] Checked final placement: no DRC violations involving the 13 placed RF parts (unconnected items remain). Preserved all other footprint positions and retained track geometry; only the intended TX_ACTIVE rename remains on existing copper.
- [x] Added D15 PESD5V0F1BRLD across ANT/GND, verified SOD-882D package, synchronized and placed beside J9. Native ERC remains 0 active errors/warnings with prior exclusions unchanged; RF sheet connectivity checks pass. See `design/antenna_esd_pinmap.md`.
- [ ] H3 remains open for common-port RF tuning, RF/power/control routing and bench ESD/VNA validation. Initial RF traces and local supply/control are routed; chain-side RF connections and wider power-network repairs remain.
- [x] Assigned ANT and Net-(U11-RFC) to the existing 0.358 mm RF class. Routed J9–C102–U11 and U11 branches to C94/C55. Added D15 and U11 ground vias, C106 bypass connection and ground via. Applied a top-layer pour-only keepout at least 1.1 mm from these RF trace edges.
- [ ] Validate J9 through-hole launch: sampled L2 ground is present under the routed RF centerlines except the approximately 1.1 mm connector antipad transition. Complete wider power-network repairs and chain-side RF routing, full-width return review and VNA/ESD testing.
- Latest PCB DRC after refill: **519 errors, 211 warnings, 118 unconnected items**. The board is not ready for fabrication; 16 legacy footprints still need reviewed cleanup.
- [ ] Resolve tooling's KiCad 10 top-level-sheet context mismatch. The project instance UUID differs from the root document UUID; native KiCad consistently uses the former. Do not assume this difference proves damaged schematic wiring.
- Evidence and exact circuit: `design/single_antenna_integration.md`, `design/rf_switch_pinmap.md`, `design/rf_switch_pcb_validation.json`.

- [x] Routed local U12 regulator/input-enable/output capacitor/bleeder, 3.0 V distribution to U11/U13, U13 control to U11/R36, and R35 to U13 input. Added local capacitor ground vias. All new copper passes DRC; native readback preserves all prior copper.
- [x] Routed incoming +5V from the existing supply via and TX_ACTIVE from J6.14 to the switch circuit on In2.Cu. Two new vias and all 16 segments retain correct nets after refill; no new copper violations.
- [ ] Place C56/L12 and the remaining RX input filter before extending C55. U8 pin mapping is audited; its bias parts, supply feeder and RFOUT-to-C84 route are placed/routed and locally checked. Four ground-tab stitching vias and two direct copper connections are installed and checked. Input filter and TX_437 are now routed and verified. TP13/C93 entrance overlap is resolved; board-specific thermal qualification remains open. The C84-output-to-C94 filter path is routed and checked. Existing board-wide +5V disconnections still require repair.

- [x] Removed obsolete TX filter C19/C20/C21/L6 and 17 reviewed trace segments. Placed C87/C89/C92 at the replacement filter locations. Saved native readback confirms exactly these removals/moves; all 685 retained copper items are unchanged. Routing remains incomplete.

- [x] Routed the C84 output through L19/C87, C89, L21/C92 and C94 to the switch. Rotated L19/L21 to align their signal pads, replaced obsolete fanouts with four short ground-via connections, and moved one local +3V0 crossing to B.Cu. Added top-pour clearance and cleaned six references. Saved readback: 26 new copper items with correct nets, 20 reviewed removals, all 665 retained copper items unchanged. No DRC violations involving the new copper or adjusted reference fields. L2 sampling at center, both trace edges, and ±0.6312 mm finds no gaps in 1,085 samples. RF bench/VNA validation remains open. See `design/tx_filter_routing_validation.json`.

## Prior checkpoint — before RF placement/routing

This checkpoint is historical; the current RF progress section above supersedes its counts.

- PCB synchronized using the full native schematic connectivity after repairing 86 footprint links. All 113 schematic references are present; 21 legacy footprints remain for reviewed cleanup.
- J6/J7/J8 are identical 1x20 through-hole headers, all DNP; their 60 numbered pads retain the original hole locations.
- H3/H4 socket bodies mount on top, tails below. CSKB logical numbering retained; 104 pad positions/nets checked, connector spacing corrected to 5.08 mm.
- U5 uses the selected SOIC-8 footprint; old U1 still remains and must be removed with its obsolete copper after placement review.
- Latest saved-board DRC after zone refill: **631 errors, 273 warnings, 140 unconnected items**. No fabrication release is implied.
- Next: RF placement, replacement alignment, legacy circuitry removal, rerouting, then fresh ERC/DRC and physical stack review. CLI/native schematic export discrepancy remains unresolved; use native connectivity for synchronization.


Baseline: 2026-09-09, ember `513365c`. Target: 437 MHz BPSK TX / 435 MHz RX, half-duplex, single UHF antenna. Checked means implemented **and verified**, not merely planned. Current design is not ready for fabrication.

## Critical — correct electrical identity before PCB synchronization

- [ ] **C0 — Hierarchy identity:** reconcile stale instance paths with the current root UUID; verify unnamed nets export correctly before interpreting remaining ERC findings.

- [ ] **C1 — U9 PSA4-5043+ pin map:** replace the SPF5189Z stand-in with an audited four-pin PSA4 symbol; RF IN=3, RF OUT/DC=1, GND=2/4. Verify SOT-343 physical pad mapping, grounding, saved connectivity and render.
- [x] **C2 — Q3/Q4 2SC3356 schematic pin maps:** confirmed Hottech C193010 package geometry; replaced simulation symbols with Q_NPN_BEC (B1/E2/C3). Verified base drive, collector tanks and grounded emitters. PCB pad-net synchronization remains P1/P2; no Renesas substitution allowed without a new audit.
- [ ] **C3 — RX collector tank:** corrected C82 to 100 nF supply bypass and C85 to 8.2 pF collector tank capacitance. C75 now 100 nF / 0402 per the existing coupling-cap plan; Q4 physical map and tank connectivity verified. Exact C85 C0G/NP0 purchasing part and RF component performance remain to verify.
- [x] **C4 — BPSK_DATA direction:** removed the output-side global alias. U7 pin 4 now connects to C73 on local RF_TX_BPSK_145; exported BPSK_DATA connects J7 pin 20, R25 pin 1 and TP12 pin 1, separately.

## High — finish the UHF schematic

- [ ] **H1 — LNA bias choke:** replace current L16=1 µH (old L14) with the specified 220 nH RF choke after verifying exact part, SRF, current rating and footprint.
- [ ] **H2 — RX LO drive:** finish LO amplifier and attenuation, and establish +7 dBm acceptance at the mixer LO port.
- [ ] **H3 — Antenna switching:** implement the selected SPDT, control/default RX state, compatible supply/control levels, antenna DC block and protection. Connect ANT, TX_OUT and RX_IN.
- [ ] **H4 — Footprints:** resolve remaining empty fields on J6/J7/H3/H4. Audit exact BOM and package selections.
- [x] **H5a — U8 identity:** verified ADL5602ARKZ-R7 lead map and exposed ground tab against the ADL5610 symbol and SOT-89 footprint; corrected schematic/PCB metadata. See `design/u8_adl5602_pinmap.md`.
- [x] **H5b — U10 identity:** ADE-1+ lead mapping, compatible ADE-6 symbol and CD636/PL052 land geometry verified; PCB metadata corrected. See `design/u10_ade1_pinmap.md`. Schematic-editor reconciliation is complete; 3D height remains open.
- [ ] **H5c — U8 bias and thermal layout:** L15 identified as Murata LQW2BASR22J00L; existing 220 nH retained pending RF bench qualification. Bias/bypass placement, supply feeder and RFOUT-to-C84 routing are complete and locally checked (see `design/u8_bias_routing.md`). Four 0.6/0.3 mm ground stitching vias and two 0.5 mm direct tab connections are installed and locally DRC-checked; all four contact filled L2 and bottom GND. Board-specific thermal and RF qualification remain open. Use 89 mA typical / 106 mA datasheet maximum under specified test conditions instead of the old 60 mA assumption; recalculate the full rail budget.
- [ ] **H6 — Schematic cleanup:** resolve 35 dangling-wire findings (UUID mapping: Clock_Gen 6, TX_Chain 7, RX_Chain 17, Power 2, Digital_Control 3; report incorrectly groups them under root); update obsolete VHF/clock notes and references. Rerun ERC without hiding unexplained errors.

## PCB — after schematic acceptance

- [ ] **P1 — Identity reconciliation:** map current schematic references/UUIDs to existing PCB footprints before applying an update. Baseline parity: 98 missing / 92 extra footprints, 33 net conflicts, 18 symbol mismatches, 10 field mismatches.
- [ ] **P2 — Synchronize:** rerun Konnect dry-run after preflight fixes; inspect all changes, then apply the exact accepted plan.
- [ ] **P3 — Electrical geometry:** inspect and repair reported shorts, 91 unconnected items, clearances and 6 outline findings.
- [ ] **P4 — Fab constraints:** fix via sizes/annular rings, padstacks, holes, mask bridges and track widths against the selected stackup/fab requirements.
- [ ] **P5 — RF layout:** reconcile RF netclass assignments; validate 50 Ω width, solid return plane, grounding/stitching, short RF paths and tuning-pad provisions.
- [ ] **P6 — Final checks:** refill zones; rerun ERC, DRC and schematic parity; audit ignored checks and complete independent RF/layout review.

## Bench validation

- [ ] Current-limited power and rail/ground continuity.
- [ ] Clock frequencies and XOR performance.
- [ ] TX output power/spurs; filter VNA measurements.
- [ ] RX LO power/spurs, LNA gain, mixer/baseband operation and sensitivity.
- [ ] T/R sequencing and TX-to-RX isolation.

## Verified setup and existing progress

- [x] Konnect 0.11.1 Codex guidance installed, server registered, live API connection verified.
- [x] Repository refreshed to `513365c`; reviewed KiCad files unchanged by pull.
- [x] Baseline checks recorded: ERC 37 errors/3 warnings; PCB 751 errors/312 warnings including 91 unconnected; 251 additional parity warnings.
- [x] UHF filter starting values identified in all four BPFs: 10 nH / 9.1 pF, 1.6 pF coupling, 3.9 pF I/O. **Topology and RF performance still need validation.**
- [x] TX tank L17=15 nH / C81=8.2 pF reaches Q3's symbol collector. **Physical transistor pin mapping still needs validation.**

## Work log

- 2026-09-09: Created this checklist from the initial review. Starting C1/C2 physical pin-map verification. No PCB synchronization applied; the preview failed with “KiCad netlist node is missing footprint.”

### First repair batch — 2026-09-09

- U9 replaced through Konnect with project-local Ember_RF:PSA4-5043+ symbol and PSA4-5043_MMM1362 footprint. Input pin 3 and output/DC pin 1 rewired; ground pins 2 and 4 both appear on GND in the exported netlist. Manufacturer land pattern implemented and exercised in a disposable PCB; pad positions and pin numbers read back. C1 remains open for final connectivity/field placement review and PCB integration. Library reference text needs placement cleanup on the actual PCB.
- C82/C85 values and LCSC fields exchanged to match bypass/tank functions. Removed stale 100 nF manufacturer part number from C85; exact 8.2 pF purchasing part remains to verify.
- C4 verified by fresh exported connectivity: output no longer aliases the GPIO data net.
- Fresh ERC: 37 errors / 3 warnings, unchanged from baseline; these electrical identity fixes do not resolve the existing root dangling wires or Q3/Q4 pin-type conflicts. ERC count alone does not establish RF correctness.
- Main PCB unchanged; no schematic-to-PCB update applied. Next: establish exact Q3/Q4 manufacturer pinout, finish C75 and missing footprints, then reconcile PCB identities before synchronization.

### Second repair batch — 2026-09-09

- Hottech C193010 was identified from its supplier-linked manufacturer datasheet; unlike the Renesas variant, its physical B/E placement matches the selected B1/E2/C3 footprint mapping. Q3/Q4 now explicitly identify Hottech and use Q_NPN_BEC. Scratch symbol/footprint rendering and pad query completed.
- Wire continuity verified: Q3 base→C73/R27, collector→L17/C81; Q4 base→C83/R33, collector→L18/C85; exported netlist confirms both pin-2 emitters on GND and pin-3 collectors off GND. U9 input→C67, output/DC→C75/L16 and both grounds also verified.
- C75 assigned 100 nF, C_0402_1005Metric, C1525 / CL05B104KO5NNNC, following the existing output coupling-cap plan. RF insertion loss still needs bench verification.
- ERC now 35 errors / 3 warnings. Important correction: “root-sheet dangling wires” was a report-location interpretation error. Root has zero electrical wires; UUID mapping locates all 35 findings on functional sheets. Do not delete these wires as decorative debris. Native report coordinates also differ by 100× from actual queried coordinates; use UUIDs and live query coordinates for repairs.
- Next work: trace these dangling findings and finish the 17 remaining empty footprint fields before reviewing a new PCB update preview. Main PCB remains unchanged.

### Third repair batch — 2026-09-09

- Assigned and read back R3/R4 to R_0402_1005Metric, matching existing C60485 / YAGEO RC0402JR-070RL. Assigned TP11–TP16 to 1 mm exposed test pads. Export verifies these eight assignments.
- Six empty footprint fields remain: U5, J6, J7, J8, H3, H4.
- **New C0 — repair hierarchy identity before trusting ERC/netlist.** Root UUID is 34355200-1bb0-4506-ab43-0e1897ffed50, while saved child symbol and sheet instance paths still begin c034ea61-6551-4f92-af2a-65337e5cc22a. All six child sheets are affected. This matches the failure mechanism in https://github.com/mixelpixx/Konnect/issues/29: unresolved instance paths suppress auto-named nets. It is not yet proven that all 35 wire findings disappear after repair. No wiring was removed or relabeled to mask this problem. Konnect dry-run near-miss checks found zero fixes on all five implicated functional sheets.
- Installed Konnect tools do not expose an in-place hierarchy-path repair. Need KiCad to reconcile/save hierarchy while preserving existing reference assignments, then export and compare every net before PCB synchronization.
- **C58/C59 purchasing identity:** C178639 is Panasonic EEHZA1V470P, a polarized hybrid electrolytic (47 µF, 35 V, 6.3 mm diameter / 5.8 mm height), not an unpolarized ceramic. C_US symbols replaced with C_Polarized_US; positive pin 1 confirmed on the supply rails and pin 2 on GND. Custom Panasonic size-D footprint accepted and assigned. Manufacturer datasheet via https://www.lcsc.com/datasheet/C178639.pdf . Verified against Panasonic primary-source package and land-pattern drawings.
- U7 C402161 resolves to TI SN74LVC1G86DBVR; DBV pin-map audit completed and SOT-23-5 assigned. U5 exact package choice and connector mechanical/mating maps remain open.
- PCB dry-run still refuses preflight: “KiCad netlist node is missing footprint.” Main PCB unchanged. Hierarchy repair is an additional blocker even after all footprints are assigned.

- Follow-up after native save: exported netlist remains 35 nets / 193 nodes; ERC remains 35 errors / 3 warnings. Saving alone did not reconcile the stale hierarchy paths. Konnect annotation only assigns missing reference numbers and does not repair hierarchy IDs; native hierarchy/annotation repair is still required.

### Native KiCad investigation — 2026-09-09

- User authorized native UI repair if annotation/save did not work. Annotation/save still yielded CLI 35 nets / 193 pin nodes and 35 errors / 3 warnings.
- Ran ERC inside the project Schematic Editor: **0 active errors, 5 active warnings, 2 existing exclusions**. Four ignored tests: global label appears once; four-way connection; SPICE model issue; footprint does not match filters. These settings were not changed. Two exclusions are stale transistor/PWR_FLAG pin-conflict markers and still require review.
- Native active warnings: isolated ANT, RX_IN, TX_OUT labels plus Ember_RF symbol/footprint libraries not present in the running editor configuration. Project tables exist on disk; resolve/reload the editor's library configuration before native PCB synchronization.
- Native KiCad netlist export contains **176 nets / 401 pin nodes**. It explicitly contains U9 input/output, Q3/Q4 base/collector and other previously omitted unnamed nets. The corrected RF connections agree with the earlier geometric checks. This native export is the current connectivity review evidence; CLI/Konnect automatic PCB synchronization remains blocked by the export discrepancy and nine missing footprints.
- **Correction to earlier diagnosis:** stale saved hierarchy paths are real, but they do not stop the native editor from forming nets. No proof yet that the 35 CLI dangling-wire findings are actual wiring defects. Do not repair/delete these wires based solely on that report. C0 remains open for reconciling native versus CLI behavior; native export provides a usable interim review path.
- Updated root title to “CubeSat Comms -- UHF/UHF Overview” and added title-block comment 9 “UHF/UHF revision in review - not for fabrication” to all sheets through the native Page Settings dialog. Forced native save did not resolve CLI export behavior. No references or wire geometry were changed in this investigation; main PCB unchanged.

## Follow-up repairs — 2026-09-09

- [x] U7: assigned Package_TO_SOT_SMD:SOT-23-5 after TI DBV top-view pin-map reconciliation and scratch placement/readback/render. Exact MPN SN74LVC1G86DBVR and manufacturer recorded. RF switching performance remains a bench-validation item.
- [x] C58/C59: corrected polarized symbols and assigned Ember_RF:CP_Elec_Panasonic_D_6.3x5.8. Panasonic EEHZA1V470P, 47uF/35V; pads 3.2x1.6mm, 1.8mm gap, positive pad 1. Scratch acceptance completed. Pin endpoints unchanged; exported C58.1=+5V, C59.1=+3V3, both pin 2=GND.
- [ ] Native library state: project symbol table visibly lists enabled Ember_RF at the correct path, and KiCad CLI successfully renders the library symbol. Native ERC nevertheless reported library not found and footprint library unavailable. Applied the native Symbol Libraries OK action to reload configuration; a subsequent native ERC rerun is still required. Do not mark resolved.
- The main PCB has not been synchronized or routed. Native/CLI connectivity disagreement remains unresolved; full native export remains the connectivity review reference. Latest CLI export is useful for component fields and these named supply nets only.

## After checkpoint fc6b76c — 2026-09-09

- [x] Native library loading resolved: applied both Symbol Libraries and Footprint Libraries settings, reopened schematic, and reran native ERC. No symbol/footprint library warnings remain. Latest native ERC: zero active errors, three isolated-label warnings (ANT/RX_IN/TX_OUT), two old transistor exclusions, four ignored tests unchanged.
- [x] U5 assigned Microchip MCP6022-I/SN / Package_SO:SOIC-8_3.9x4.9mm_P1.27mm, following schematic_guide.md prototype BOM. Audited all eight pins and three units in scratch project, queried pads and inspected renders. Main readback confirms all three units updated.
- [x] J8: user confirmed optional through-hole expansion header, unpopulated at fabrication/assembly. Native DNP flag saved and verified in CSV preview and XML property. Assigned standard Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical. Cleared copied Samtec purchasing field and added assembly note. Keep footprint on board; do not order/populate J8 in assembly BOM.
- Remaining blank footprints: J6/J7/H3/H4. J6/J7 specify ESQ-120-14-G-S; Samtec footprint drawing confirms 2.54mm pitch and 1.02mm holes. Audit mating orientation and envelope before assignment. J8 exact purchased part is intentionally unspecified because it is DNP.
- Named-net export comparison before/after confirms unchanged connectivity and only U5/J8 footprint identity changes. CLI still exports 35 nets; full native-versus-CLI discrepancy remains open. Native save normalized additional Power/TX/RX serialization and persisted symbol-table view settings in the project configuration; main PCB unchanged.

## Connector footprint completion — 2026-09-09

- [x] J6/J7 assigned project-local Samtec ESQ-120-14-G-S single-row 20-pin footprints; H3/H4 assigned ESQ-126-39-G-D double-row 52-pin footprints. Exact MPN/manufacturer/datasheet recorded; Samtec MPN removed from misleading LCSC field on J6/J7.
- [x] Scratch readback verified all 72 unique pad numbers, coordinates, symbol pin sets, 2.54 mm pitch, 1.02 mm drills and 1.8 mm lands. Top render inspected. Detailed acceptance in design/samtec_pad_audit.md.
- [x] Fresh export has no blank component footprints; named connectivity unchanged, J8 DNP preserved.
- [ ] Confirm connector physical side, rotation and origins against mating boards. Samtec mating-face numbering is distinct from the project's schematic pin diagram; do not mirror the footprint merely to match that diagram. Verify opposite Pico row orientations and stack compatibility before routing. Final reference/silkscreen placement remains open.
- [ ] New PCB dry-run passes missing-footprint preflight but reports 15 reference identity conflicts: C1, C2, C3, C4, C5, C6, C7, R1, R2, R3, R4, Y1, Y2, L12, L13. It classifies 107 footprints as board-only. These are not accepted deletions or a validated mapping; reconcile against full native connectivity before any update.
- [ ] CLI export still contains only 35 nets; native baseline contains 176. This discrepancy remains a synchronization blocker. No main PCB changes applied.

## User clarification — three identical DNP headers

J6/J7/J8 all use Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical. Supersedes J6/J7 Samtec socket selection above; purchasing fields cleared and all three assembly notes specify DNP. J8 native DNP flag remains set. J6/J7 native DNP checkboxes still require setting: desktop control timed out twice and current Konnect component editing does not expose that flag. Main PCB still awaiting synchronization.

## PCB identity investigation

Read-only UUID comparison found 86 unique candidate matches. PCB references changed after annotation: for example PCB C4 maps to schematic C2, C6 to C4, R1/R2 to R3/R4, and R3/R4 to R1/R2. Blind relinking by reference would be incorrect. Old PCB paths omit hierarchy prefixes. See design/pcb_identity_review.md for full candidate table; pad/net validation still required. Native desktop control remains unavailable (timeout), so J6/J7 DNP checkboxes and native update are pending.

## Desktop connection restored and DNP complete

- [x] Restarting KiCad restored native desktop control. J6/J7 native Do Not Populate flags enabled and saved. Fresh XML independently verifies J6/J7/J8 all DNP with identical PinHeader_1x20_P2.54mm_Vertical footprints. Cleared the bulk-edit/BOM filter.
- PCB identity candidate mappings and native/CLI netlist discrepancy still require resolution before applying an update.

## Live PCB connectivity reconciliation

- [x] Queried all 107 existing PCB footprints through live Konnect IPC. All mapped pad numbers exist in the native schematic connectivity export.
- [ ] Seven existing PCB net assignments span multiple current schematic nets: I2C_SCL, I2C_SDA, GND (Q3 collector), TRIPLER_OUT (Q3 base), old Q1 base (Q3 emitter), old U4 RF (U9 input/output and L16), BPSK_145 (data/output separation). Review affected copper and routing during synchronization; net-assignment comparison alone does not prove physical copper continuity.
- [ ] 21 unmatched footprints require classification; do not delete them automatically. Detailed list and affected pads in design/pcb_pad_reconciliation.md.
- No PCB mutation applied in this reconciliation.

## Unmatched footprints classified

All 21 classified by circuit role in design/unmatched_pcb_classification.md. U1→U5 has eight-pin electrical agreement but requires replacing the incorrect 10-pad footprint with SOIC-8. Three capacitor candidates identified; two series-inductor positions become coupling capacitors. RX input and LO filter blocks require topology-aware replacement. Preserve TP1/TP2 and J5 pending test-access/antenna-switch decisions. No PCB edits applied.

## Native update preview

Native preview with reference relinking OFF, footprint replacement ON, deletion OFF proposes 113 additions (all schematic parts), with 17 warnings and zero errors. It does not recover the preserved leaf UUIDs beneath changed hierarchy paths. Closed without applying. Zero preview errors is not a safe-update verdict. Explicit footprint linkage repair is required before synchronization; report in design/native_update_preview.txt.

## Footprint links repaired in working PCB

- [x] Applied and saved 86 preserved-UUID hierarchy links through native KiCad board API, after isolated-copy test. Compared saved board against native baseline: only paths changed; references, pads, tracks, zones and geometry identical. Native save omits solder-mask epsilon_r entries and empty zone_defaults even without edits; other stackup data unchanged.
- Native preview now recognizes existing parts and proposes 27 new footprints, rather than all 113. 21 warnings, zero errors; update not applied. See design/linked_update_preview.txt.

## Native PCB synchronization applied

- [x] Native update applied and saved with UUID matching, replacement enabled, deletion disabled. All 113 schematic references now exist, no duplicate references; PCB contains 134 footprints including 21 retained legacy items. J6/J7/J8 identical header footprints and native DNP flags verified.
- Native update finished with zero errors and three warnings: two old RX filter vias and Y1 pad 4 absent from symbol.
- U5 SOIC-8 added, but old U1 remains: attempted multi-unit U5 linkage was not recognized. Do not treat this as an in-place replacement. Review U5 placement and remove old U1 only with associated copper cleanup.
- Old L12/L13 preserved as LEGACY_L12/LEGACY_L13 to avoid collisions.
- DRC baseline after update: 1566 errors, 476 warnings, plus 171 unconnected items. New footprints are unplaced and legacy circuitry retained; this is an intermediate repair state, not fabrication-ready. Schematic parity not checked by this CLI run.
- Next: place new components and correct replacement footprint alignment, then remove obsolete circuitry and reroute changed nets.

## Header placement restored

- [x] J6/J7/J8 moved and rotated via live Konnect IPC so all 60 numbered pads exactly coincide with original J1/J2/J3 pad centers (zero measured deviation). DNP and identical header footprints retained. C58/C59 replacement pad centers already match their old pads exactly.
- [x] Zones refilled through IPC and board saved. DRC: 933 errors, 418 warnings, 154 unconnected items; total violations reduced from 2042 to 1351 after header alignment and zone refill. Not fabrication-ready.
- [ ] H3/H4 require explicit physical mating review: best rigid numbered-pad fit leaves 2.54 mm error, indicating swapped rows/mirrored numbering relative to old connector. Do not force alignment or silently swap net numbers.

## Stack connector mounting-side check

- EPS saved PCB uses B.Cu for H1/H2, while original and current comms use F.Cu for H1/H2→H3/H4. Their imported local pad coordinates are the same despite different mounting sides; this is insufficient evidence of physical mating compatibility.
- EPS H1 origin is x=113.2136 mm, H2 x=108.1336 mm (5.08 mm separation). Original comms H1 x=113.1736 mm, H2 x=108.1336 mm (5.04 mm separation). Both use y=136.1236 mm, -90 degrees. Comms also has a 0.04 mm inter-connector spacing discrepancy relative to EPS.
- Samtec Figure 4 mating-face numbering and the new library pattern were re-inspected. Do not renumber pads to conceal a mirrored mounting-side mismatch. Need stack drawing/physical assembly orientation to select the socket side and verify alignment; question sent to user. No H3/H4 geometry changes applied in this check.

## CSKB sockets placed for top-side assembly

- [x] User confirmed socket bodies above PCB, pins below; EPS B.Cu assignment was a placement mistake and not the intended assembly reference. H3/H4 remain on F.Cu.
- [x] Custom ESQ footprint updated through Konnect to CSKB logical numbering, odd-left/even-right in zero-rotation top view. This is an unkeyed socket with interface-defined numbering; distinguish from Samtec polarization-position numbers. No schematic bus pins or pad net assignments were changed. Earlier audit's generic Samtec mating-position convention is superseded for these CSKB instances.
- [x] H3/H4 refreshed using reviewed Konnect plan and placed at (111.9436,104.3736)/(106.8636,104.3736), both 180 degrees. Separation 5.08 mm. H4 restores original numbered-pad coordinates; H3 shifts its original hole grid +0.04 mm in X to match EPS. All 104 pad coordinates and net assignments verified. Top copper/silk export inspected.
- [x] Zones refilled and board saved. DRC now 631 errors, 273 warnings, 140 unconnected items (904 violations total). Placement/routing and silkscreen cleanup remain; not fab-ready.
- Scratch-board Add API failed during validation; no scratch-board acceptance claimed. Acceptance here uses library-tool readback, reviewed live refresh, all-pad live position/net checks, and rendered board inspection.

## Single-antenna requirement reaffirmed

J9 is the one shared UHF antenna connector; TX_OUT/RX_IN are internal SPDT branches. Legacy J5 is to be removed with old feed routing, not preserved as a second antenna. PE4259 six-pin symbol created and read back; switch is not yet placed/wired. Supply/control, DC blocking, protection, GPIO and footprint acceptance remain pending. See design/single_antenna_integration.md.

## RX input filter routing — 2026-09-09

- [x] Place and route C55 → C56/L12 → C60 → C64/L13 → C67 → U9 IN; check clearances and L2 return plane. Adjust adjacent bypass corridor; 107 unconnected items remain. See `design/rx_input_routing.md`.
- [x] Route U9 ground stitching, local bias supply and C75 output to U10 RF pin 3. See `design/u9_output_routing.md`; choke qualification and legacy bypass vias remain open.

## U9 output and bias routing — 2026-09-09

- [x] U9 pins 2/4 directly stitched to ground; C75 output coupling and L16 bias branch routed. Local C77/C79 bypass nodes joined to the existing +5 V feeder.
- [x] Remove obsolete +5 V branch intruding into U10 RF input and replace two obstructing legacy ground vias. DRC now 509 errors / 204 warnings / 102 unconnected items.
- [ ] Qualify or replace L16 for 435 MHz; 1 µH retained, not accepted for fabrication. Verify exact MPN, impedance/SRF, current and land pattern; do not rely on generic inductance-only SRF claims.
- [x] Replace four legacy bypass vias around C77/C79 and verify local routing. See `design/rx_bypass_cleanup.md`.
- [ ] Validate shared +5 V rail budget.

## RX bypass and L16 review — 2026-09-09

- [x] Clean C77/C79 bypass vias and dogbones: 501 errors / 202 warnings / 101 unconnected items; new copper locally clear.
- [x] Verify original DDY L16 data: typical SRF is 550 MHz, not the generic 200–400 MHz previously assumed.
- [ ] Resolve L16 exact part and land-pattern acceptance; Coilcraft 0805HP-221XJRC is a researched candidate, not an applied or qualified substitution. See `design/l16_choke_review.md`.

## L16 prototype part and footprint — 2026-09-09

- [x] Set L16 to Coilcraft 0805HP-221XJRC / 220 nH in schematic and PCB, with manufacturer-derived `Ember_RF:L_Coilcraft_0805HP` land pattern; clear obsolete LCSC ordering code. See `design/l16_footprint_acceptance.md`.
- [x] Adjust L16/C75 placement and six RF segments; DRC remains 501 errors / 202 warnings / 101 unconnected items.
- [ ] Resolve the old >1.5 GHz SRF target and perform biased RF impedance, gain, return-loss and stability measurements. Selected part has 930 MHz typical SRF; this is explicitly a prototype choice, not closure of that target or production qualification.
- [ ] Continue remaining mixer LO/IF routing and shared supply budget review.

## Mixer IF routing — 2026-09-09

- [x] Connect U10 IF, R34, C99 and RX_IF to TP15/R20; remove obsolete crossing power copper.
- [x] Verify retained copper, pad nets, live component positions, local DRC and L2 ground. Main DRC: **479 errors / 200 warnings / 98 unconnected**. See `design/mixer_if_routing.md` and `design/mixer_if_validation.json`.
- [ ] Place and route LO filter/driver to U10 pin 6; consolidate IF RF netclass assignment.
- [ ] Resolve remaining TP15/R20 placement/labels and board-wide DRC; qualify prototype L16 before fabrication.

## LO band-pass filter routing — 2026-09-09

- [x] Replace obsolete LO low-pass footprints and route C86/C90/L20/C91/C95/L22/C97 into U10 pin 6.
- [x] Reroute crossing RX_BASEBAND segment; verify new routing and L2 ground. Main DRC: **460 errors / 167 warnings / 87 unconnected**. See `design/lo_filter_routing.md` and `design/lo_filter_validation.json`.
- [x] Assign and verify RF netclasses for LO resonator nodes, U10 LO and U10 IF.
- [ ] Place and route Q4 input, collector/bias and supply/bypass network into C86; current filter input remains open.
- [ ] Remove redundant legacy drill overlaps near U10 pins 4/5; resolve U10/C57 courtyard issue and finish assembly-readable labels.
- [ ] Update superseded direct-LO bring-up procedure and validate complete UHF LO drive on the bench.

## Q4 LO tripler routing — 2026-09-09

- [x] Place/connect Q4, C83/R33, L18/C85 and C82; join collector to C86 and bypass to existing +5V feeder.
- [x] Verify local DRC/connectivity, retained copper and pad nets, live component pads and L2 ground. Main DRC: **451 errors / 166 warnings / 77 unconnected**. See `design/q4_lo_routing.md` and `design/q4_lo_routing_validation.json`.
- [x] Assign and verify Q4 base/collector RF netclasses.
- [ ] Resolve redundant ground drill overlaps near U10 pins 4/5 and U10/C57 placement conflict.
- [ ] Validate complete LO drive/spectrum and shared supply budget; finish remaining board-wide connectivity and assembly labeling.

## U10 ground/C57 clearance — 2026-09-09

- [x] Remove two redundant vias overlapping U10 footprint holes; verify retained plated-hole ground connections.
- [x] Move C57 clear of U10 and reroute its existing nets. Main DRC: **450 errors / 150 warnings / 77 unconnected**. See `design/u10_cleanup.md` and `design/u10_cleanup_validation.json`.
- [ ] Priority: repair pre-existing malformed/self-intersecting board outline causing 3D viewer warning; preserve mechanical dimensions.
- [ ] Resolve TP15/R20 and R20/R21 courtyard conflicts and TP15 silk clipping.
- [ ] Continue legacy RX copper cleanup, remaining connectivity and RF/supply qualification.

## Board outline repaired — 2026-09-09

- [x] Remove five nanometer-scale Edge.Cuts connector segments and join neighboring endpoints; preserve all arcs, component geometry and copper.
- [x] Clear all six invalid-outline DRC findings and verify the 3D viewer renders without its previous warning. Main DRC: **444 errors / 150 warnings / 77 unconnected**. See `design/outline_repair.md` and `design/outline_repair_validation.json`.
- [ ] Resolve TP15/R20/R21 courtyard conflicts, legacy RX copper and remaining connectivity.

## IF test-point spacing — 2026-09-09

- [x] Clear TP15/R20 and R20/R21 courtyard overlaps plus TP15 silk clipping; reroute RX_IF with 0.358 mm traces.
- [x] Verify live pad positions, unchanged nets/copper, local DRC and valid outline. Main DRC: **439 errors / 149 warnings / 77 unconnected**. See `design/if_spacing_cleanup.md` and `design/if_spacing_validation.json`.
- [ ] Clean obsolete RX filter remnants and remaining board-wide connectivity; continue RF and shared-supply qualification.

## Obsolete RX filter removed — 2026-09-09

- [x] Remove confirmed legacy C29/C30/C31/C32/L9/L10/L11 and 32 obsolete copper items; preserve all retained pad nets and copper.
- [x] Refill and verify RF ground, valid outline and saved-board DRC: **387 errors / 129 warnings / 69 unconnected**. See `design/legacy_rx_cleanup.md` and `design/legacy_rx_cleanup_validation.json`.
- [ ] Audit/remove legacy U1 against current U5 and resolve remaining unnamed/shorted copper around clock and baseband circuitry.
- [ ] Resolve J6/SPI and H3/ground clearances, remaining connectivity, supply budget and RF qualification.


## Clock restoration checkpoint

Restored the actual Si5351 Y2 to the former clock footprint location and removed the obsolete U1 identity. Swapped R1/R2 placement to match SCL/SDA, reversed C5/C66 to match supply and ground routing, and restored their ground dogbones. Connected crystal copper to XA/XB. Replaced Y1 Crystal_GND2 with Crystal_GND24, matching Abracon ABM8G pins 2/4 ground (https://abracon.com/Resonators/ABM8G.pdf). Y1 now records the selected 25 MHz part.

Moved C6/C7 outward and rebuilt their short connections; widened undersized clock tracks and ground escapes. Enlarged 95 vias to 0.60 mm with existing 0.30 mm drills.

Y2 standard 0.50 mm pitch / 0.35 mm pad width requires 0.15 mm pad clearance. Its pads carry a 0.15 mm local clearance; board manufacturing floor is 0.15 mm, while all five netclasses retain 0.20 mm clearance. Supported by the 1 oz process capabilities at https://jlcpcb.com/capabilities/pcb-capabilities . No DRC categories or individual errors were excluded.

Verified all unrelated footprint positions and all original pad net assignments (except corrected Y1.4) are unchanged. Clock signal clusters match schematic anchors. Power nets still encounter documented unrelated shorts elsewhere, so the board is not yet electrically clean.

Saved board DRC: 98 errors, 128 warnings, 51 unconnected items. Clock sheet ERC has zero violations.

## Latest routing cleanup — 2026-09-09

- [x] Complete remaining power, digital and receiver copper connections: saved board now has zero unconnected items.
- [x] Correct receiver DC bias with R38/R39, move C72 to VREF_RX, return R30 to VREF_RX; check named-net pad membership.
- [x] Check restored RF pour setback and 705 ground-reference samples.
- [x] User accepted H3/H4 courtyard overlap to preserve equal pin spacing; saved one pair-specific DRC exclusion with comment. Fresh saved-board DRC: zero active errors, 120 warnings, zero unconnected items.
- [x] Native schematic ERC: zero errors, one GND label naming warning, two existing exclusions/four ignored tests. Native netlist comparison: 181 nets, zero PCB connectivity mismatches.
- [ ] Correct old Sallen–Key text (unity gain/equal values gives Q=0.5) and new resistor field placement in native editor.
- [ ] Review remaining 120 DRC warnings; RF bench qualification and L16 prototype limitation remain open.

See design/remaining_layout_cleanup.md and design/remaining_layout_validation.json for the current saved-board evidence. No commit or push performed.
