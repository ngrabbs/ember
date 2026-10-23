# EPS Rev B 5 V recovery supply

2026-10-23. **Electrical development baseline drafted; final design acceptance remains open.** Prefer evaluating **TPS552872RYQR** as the integrated alternative to LM5177 plus four external FETs. It removes the external low-gate-voltage selection problem and does not need an MCU command or an already-running output for startup. This is conditional on the protected source envelope and qualification below; it is not a frozen production BOM or a demonstrated 2 A rail rating.

[Native study](../studies/recovery_5v/recovery_5v.kicad_sch) · [Development BOM](../studies/recovery_5v/development_bom.csv) · [Analysis script](../verification/recovery_5v_analysis.py) · [Calculated cases](../verification/evidence/2026-10-23_recovery_5v_analysis.json) · [Connectivity verification](../verification/evidence/2026-10-23_recovery_5v_verified.json)

## Decision and operating boundary

Preserve the selected recovery behavior: regulated `+5V` with the pack at the provisional 5 V floor. Use **4.5 V at the converter** as the development sensitivity for source-path losses, not as a measured path drop or approved battery cutoff. The shared stack distribution budget is provisionally 2 A; actual recovery, transmit, startup and other board loads remain unmeasured. Do not require the EPS MCU to enable its own recovery supplies.

The converter sits downstream of the proposed hardware RBF/deployment and source-OV circuits. `SYS_PWR_PERMITTED` is the existing variable source interface. It may rise well above pack voltage because of charger PowerPath operation. The design study uses a **35 V protected input ceiling**. The TPS device has less input-voltage margin than the 60 V LM5177: it cannot substitute for solar protection. Prove the actual local VIN peak remains within its operating rating, including cutoff delay, handover and ringing. Do not use absolute maximum as an operating allowance. Retain LM5177 as the fallback if this protected envelope cannot be established; no accepted source maximum or cutoff circuit is silently changed.

The integrated converter was compared with LTC3115-2, whose advertised 2 A capability applies in step-down operation; its low-input 5 V capability is lower. It does not establish the present 2 A development case.

## Circuit baseline

Manufacturer sources: [TI TPS552872 SLVSHG1, August 2023](https://www.ti.com/lit/ds/symlink/tps552872.pdf), §§5, 7.3, 8.2.2 and RYQ0021A drawing; [TI EVM SLVUCS0, July 2023](https://www.ti.com/lit/ug/slvucs0/slvucs0.pdf), schematic p. 4 and BOM pp. 7–8. The application schematic, loop equations and package land drawing were rendered and inspected. This adapts the EVM organization to 5 V / 400 kHz; its 12 V / 2 MHz compensation is not copied.

| Function | Development choice | Disposition |
|---|---|---|
| Converter | TPS552872RYQR, four integrated switches | Conditional development selection; custom review marker remains |
| Startup/bias | EXTVCC intentionally floating selects internal LDO | No external auxiliary supply or output-fed startup loop; internal bias drops below its nominal value at low input |
| Light-load mode | MODE wired low; DITH/SYNC wired low | PFM, no dithering; measure COMMS receive noise before accepting |
| Frequency | R3 = 49.3 kΩ | Nominal 400 kHz; 360 kHz analysis is a sensitivity, not a guaranteed corner specification |
| UVLO | R1/R2 = 39.2 kΩ / 16.9 kΩ, 0.1%, 25 ppm/K | Calculated rising interval 3.969–4.198 V including resistor temperature sensitivity, below 4.5 V development input |
| Feedback | R5/R6 = 31.6 kΩ / 10 kΩ, 0.1%, 25 ppm/K | Nominal 4.992 V after shunt; static sensitivity 4.919–5.075 V including reference, resistors/TCR, FB leakage and residual CDC current |
| Output current sense | R4 = 20 mΩ, 1%, CRF1206-FZ-R020ELF | Slow current-limit sensitivity 2.369–2.635 A including 50 ppm/K shunt drift; 0.08 W at 2 A. Not an input inrush limiter or guaranteed short-circuit ceiling |
| Inductor | L1 = 6.8 µH; XAL7070-682MEC | Initial maximum 8.16 µH stays below TI's 10 µH recommended ceiling; published saturation is typical and hot fault-current acceptance remains open |
| Input bypass | Three 10 µF / 50 V ceramics, 100 nF / 50 V, 68 µF / 50 V hybrid bulk | Manufacturer EVM part references in BOM; bias, ripple, source impedance and inrush remain to be qualified |
| Output bank | Four 22 µF / 25 V ceramics plus three 100 µF / 35 V hybrid references, 100 nF bypass | 388 µF nominal; expanded analysis sweeps 160–500 µF effective. Nominal sum is not a guaranteed cold/bias capacitance |
| Internal-bias bypass | 10 µF / 50 V reference | Must retain the required effective capacitance; not an exported spacecraft supply |
| Bootstrap | Two 100 nF / 50 V GCM188L81H104KA57D references | Each wired between its BOOT and SW pins |
| Compensation | 3.74 kΩ / 75 nF series branch, parallel 300 pF | TNPW06033K74BEEA, GRM31C5C1H753JA01L (1206 C0G), GRM1885C1H301JA01D (0603 C0G); loop qualification remains open |
| Power good | PG with 10 kΩ pull-up to independent essential `+3V3` | Status/load-release boundary only; 3.3 V absence does not prevent converter startup |

The optional CC output and cable-droop compensation output are intentionally unconnected. Output capacitors attach before the current-sense resistor; feedback and ISN observe `+5V` after it. The distinct upstream node is `5V0_RECOVERY_RAW`. The nominal internal LDO node is `5V2_RECOVERY_BIAS`; that name is not a promise of 5.2 V at depleted input. Existing `+5V`, `+3V3` and ground interface names are preserved.

## Sizing and startup findings

At nominal 2 A, allowing the shunt drop requires about 10.08 W before the shunt. At 4.5 V input this is **2.49–2.64 A** using assumed 90–85% efficiency; the upper feedback-voltage corner increases the 85% case to approximately 2.68 A. This leaves calculation margin to the published average-current limit but does not prove the limit or efficiency at depleted input and temperature. The largest nominal-voltage modeled peak is about 3.57 A with the smaller inductor; short-circuit/inrush peaks are a separate test. The inductor's maximum current-limit and temperature behavior is not closed by a typical saturation figure.

The initial 10 µH ±20% candidate could reach 12 µH, above the manufacturer's recommended 10 µH maximum effective inductance. The revised 6.8 µH choice reaches 8.16 µH at initial high tolerance. An illustrative 20% low tolerance plus 30% magnetic roll-off gives 3.808 µH, above the 3.33 µH inner-loop minimum calculated at 360 kHz. This roll-off is a sensitivity, not a guaranteed hot-current curve. A 4.7 µH nominal part with the same reductions would not retain that margin.

The expanded analytical model covers 768 cases: load 0.5/2 A, input 4.5/6/8.4/35 V, capacitance 160/500 µF, ESR 2/50/267 mΩ, inductance 3.808/8.16 µH, and resistor/compensation-capacitor tolerance sensitivities. Estimated crossover is 0.96–5.54 kHz; minimum estimated phase margin is 62.7°. It approximates the current-mode plant and error amplifier, including the shunt's small load-side effect. It excludes switching/sample delay, current-limit dynamics, PFM and buck-boost transition operation. The hybrid and ceramic branches have different ESR/frequency behavior; a lumped ESR sweep cannot qualify the physical bank. No transient or switching simulation has run.

For a hypothetical 1.9 A load step, 25 µs unsupported interval and 10 mΩ ESR, 220 µF gives about 0.235 V droop. The actual load slew and permitted droop remain to be verified. Loss sensitivities at 2 A total approximately 1.20–1.86 W, including the shunt; these are assumed-efficiency budgets, not a die-loss or vacuum thermal prediction.

The user selected **−40 to +85 °C for component screening**, leaving operating-temperature qualification open. The ZK catalog gives a D8 cold/endurance ESR bound of 0.8 Ω per capacitor: three parallel parts alone correspond to 267 mΩ, above the old 50 mΩ model limit. A deliberately conservative 160 µF/267 mΩ lumped step gives about 0.804 V droop in the same 1.9 A/25 µs example. That does not predict the ceramic-assisted bank, but prevents accepting cold transient performance from the earlier calculation. Finish the actual multibranch impedance model and measurements before retaining or replacing these hybrid parts.

Charging 388 µF to 5 V in the minimum nominally specified ramp interval requires about 0.776 A of capacitor current. Adding a simultaneous 2 A load can exceed the slow current-limit minimum. **Keep heavy and constant-power loads disconnected until PG and startup have settled.** PG is provided, but the downstream hardware permission/delay circuit and actual receiving-board startup behavior are not implemented or qualified in this study. A provisional 0.5 A recovery load is a test case, not a measured COMMS requirement. Do not solve this dependency with a command from an unpowered IHU. Verify startup with initially discharged output and from a prebiased rail.

See the [startup and IHU handoff](rev_b_5v_recovery_closure.md) for the newly recorded COMMS TX switch, directly powered recovery load, proposed capacitance/current allocations, and hardware delay requirements. No shared-rail switch or new stack pin is silently introduced.

The internal output overvoltage feature is not a 5.5 V spacecraft-rail protector. Independent protection against feedback failure or a shorted power switch remains part of the system fault-containment review. Likewise, PFM reverse-current behavior is not an all-source RBF isolation barrier.

## Native design and verification

The new project is an isolated, editable **ANSI B development study**, with one functional schematic sheet. Its PCB contains only the disposable U1 package comparison authorized for library verification; it is not synchronized to the circuit, placed, routed or ready for fabrication. Rev A and existing controller sources were not modified. Project library tables use portable `${KIPRJMOD}` paths.

**Electrical evidence:** all 16 functional net endpoint sets match the intended circuit; the three intentional NC pins are separately checked. Direct KiCad 10 ERC: **0 errors, 0 warnings**. Konnect reports no floating wire endpoints, unconnected required pins, merged nets or orphan items. Fresh queried wire geometry contains no connected four-way endpoints or collinear overlapping segments. Exact POWER/ANALOG_CONTROL assignments are checked against the saved schematic net names. Their inherited widths/clearances are not accepted routing or current-carrying constraints. The available API did not set the four-way ERC severity; geometry was checked explicitly.

**Physical identity:** 21 symbol functions match the manufacturer table. The custom footprint has 21 unique electrical numbers and 23 pad objects because central pad 9 is formed from three overlapping lands. Top/component-side orientation, pin-1 key, dimensions, layers and lack of drills were queried back and inspected in actual exports. See [readback](../verification/evidence/2026-10-23_recovery_5v_readback.json), [fresh geometry](../verification/evidence/2026-10-23_recovery_5v_geometry.json), and the project IPC-2581 comparison. Stencil segmentation and thermal implementation are not accepted by this check.

The CLI report records ignored checks for single global labels, four-way junctions, simulation models, and footprint filters. These inherited settings were not changed to obtain the result. Four-way geometry and the custom package map were checked separately; no SPICE-model verification is claimed. No individual ERC violation is excluded in the report.

**Visual evidence:** the actual schematic page and controller/power/compensation details were inspected, and label/wire conflicts corrected. The user approved the bright-green CUSTOM review callout alternative on 2026-10-23. Body graphics themselves are not green. Full S11 presentation acceptance is **blocked by the exposed field API**: it cannot set/verify the required visible Arial parameter blocks and orientation-aware field effects. Individual component edits now persist the exact development MPNs and metadata; the previous batch operation had silently omitted passive fields, and the previous blank BOM was not valid metadata evidence. Fresh CLI export is the verification authority. Metadata, a BOM export and a readable circuit do not constitute an S11 pass.

## Remaining closure gates and bench sequence

| Gate | Required evidence |
|---|---|
| Source boundary | Accepted cold-array envelope and autonomous cutoff; local VIN stays within operating limit during fault/handover/ringing. Keep the 768 mm² reservation until actual placement proves otherwise |
| Exact assembly BOM | Exact development MPNs selected; finish bulk land-pattern verification and all package maps, capacitor bias/temperature/aging and inductor hot fault margin. Hybrid bulk references are bench choices, not flight-qualified selections |
| Startup and load release | Start at 4.5 V input with output discharged, recovery load and separately delayed 2 A load. Record PG, VCC, both SW nodes, inductor current and output. Characterize current-limited-source recovery and UVLO rising/falling behavior |
| Regulation and stability | Sweep 4.5–35 V with intermediate 5 V transition region, 0/0.5/2 A loads, load steps, prebias, PFM behavior and source handover. Measure loop gain/phase on the real LC bank |
| Fault containment | Short/open feedback, output short/hiccup, externally driven output, local input overshoot, RBF insertion and removed-source backfeed. Define protection rather than assuming converter shutdown provides it |
| Thermal and environment | Establish actual ambient/baseplate envelope and vacuum heat path; validate loss, junction temperature, hybrid-cap suitability, 16 mm stack clearance and EMI/COMMS reception |
| CAD acceptance | Complete supported S11 field presentation, full package/stencil review, hierarchy integration and repeated electrical/visual checks after edits |

Use current-limited sources and simulated pack conditions for initial tests; provisional converter thresholds do not define the BMS/cell limits. Bench results are **not run**. The recovery architecture and candidate circuit have advanced; calling the complete supply closed would overstate the evidence.
