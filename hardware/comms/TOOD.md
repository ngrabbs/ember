# Comms board — review and repair checklist

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
- [ ] **H4 — Footprints:** resolve remaining empty fields on U5/J6/J7/J8/H3/H4. Audit exact BOM and package selections.
- [ ] **H5 — Remaining RF identities:** audit U8 ADL5602 versus ADL5610 symbol and U10 ADE-1+ versus ADE-6 symbol.
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
