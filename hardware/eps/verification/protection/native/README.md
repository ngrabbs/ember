# Native protection development study

**Historical 81-part export.** Use the [current 83-part latch/source-short evidence](../latch/native/README.md) for the revised circuit, BOM and actual renders.

2026-10-23. Isolated editable circuit study, not a fabrication release or a qualified protection system. All native writes used Konnect 0.11.1; verification used KiCad 10.0.0. No existing converter, controller, library or PCB was changed.

Open `hardware/eps/studies/recovery_protection/recovery_protection.kicad_pro`. The root source sheet links `recovery_rail_final.kicad_sch`; both use ANSI B landscape. Portable project footprint registration reuses the approved Panasonic D8/F review candidates. No new symbol or footprint was authored.

## Electrical evidence

- [Fresh XML](protection.xml), [KiCad netlist](protection.net), [assertions](verify_native.py), [result](verified.json): **40 complete endpoint sets pass**, comprising 36 connected nets and four intentional NC pins. There are 81 unique physical components: 38 source and 43 rail.
- Source Q1/Q2 use one IRLR2908TRPBF per pass/reverse function. Rail Q101–Q103/Q104–Q106 use three per function. All sources join COMMON; drains point to input and SENSE. Controller SOURCE observes COMMON. PNP emitter→GH, base→HGATE, collector→100Ω→COMMON is asserted explicitly.
- Final source damping: D5 SMBJ60A to ground; R13 CRCW12061R00FKEAHP 1Ω feeds C13–C16 GRM32ER72A225KA35L to ground. Effective snubber capacitance must remain ≥2µF through 60V. SMBJ60A's full-current 96.8V clamp does not guarantee 80V MOSFET survival; bounded RC/source analysis and physical qualification remain separate.
- Source D3/D4 and rail D103/D104 are SMBJ8.5A gate-to-COMMON clamps. Rail input D105 remains SMBJ36A. The rejected 12V gate zeners and source SMBJ36A are absent from the linked circuit.
- [Direct CLI ERC](erc-cli.json): **0 errors, 1 warning**. The single-pin local `REC5_RESET` external interface is intentionally outside MCU-allocation scope. It is not excluded. SHDN/ENOUT are NC on both controllers. Inherited ignored checks include four-way junctions, single global labels, simulation models and footprint filters; they were not changed to obtain this result. **S03 native severity persistence is BLOCKED_API:** no exposed Konnect schema can set `four_way_junction` to Error; `run_erc.severity` is only a report filter. [Capability evidence](erc-severity-api-limitation.json) records the inspected schemas. The separate geometry pass does not satisfy this setting requirement.
- [Source readback](final-readback-1.json) and [rail readback](final-readback-2.json): no floating wire endpoints, unconnected required pins, shorted named nets or orphan items. [Geometry check](geometry-check.json): no four-direction wire endpoints, collinear wire overlaps or off-grid wire endpoints. Unjoined rail gate/drain crossings remain separate in the exact exported endpoint sets.
- [Saved net classes](netclasses.json): 36 exact assignments in POWER/ANALOG_CONTROL match all connected schematic nets. The generated blank PCB has no synchronized nets; saved schematic-name patterns are checked against XML. API routing defaults (0.25mm width/0.2mm clearance) are not accepted current or fabrication rules.
- [BOM](development_bom.csv), [final resistor query-back](final-resistor-fields.json), and XML preserve exact development MFG P/N identities and all required passive parameter values. Eighteen TNPW0603 ordering codes use verified Vishay 28758 Rev10-Apr-2026 pp3–4 rules; procurement confirmation remains open. KEMET constructed codes also require procurement confirmation. Inductor L1 is **XAL1510-472MED**, 4.7µH, using stock `Inductor_SMD:L_Coilcraft_XAL1510-472`. [Final query-back](final-inductor-readback.json) verifies its two nonpolarized pads at (−5.3,0)/(+5.3,0), each 3.18×13.2mm. The [manufacturer specification](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal1510/xal1510-472/) lists 21A Irms/20°C rise, 29A/40°C rise, 39A typical 30% L drop at 25°C, and DCR 3.4mΩ typical/3.8mΩ maximum. Body size is 15.4×16.4×10mm; 10mm is below the 16mm standoff, but actual larger-area assembly fit and hot minimum-L qualification remain open. The analytical 2.5µH/10mΩ envelope is unchanged. The final XML and resistor readback supersede the earlier generic resistor-code fields in the geometry readbacks.

## Actual rendered-sheet inspection

[Source full page](source.png) and [rail full page](rail.png) were opened and inspected, followed by [source power](source-power.png), [source controller](source-controller.png), [source gate](source-gate.png), [source snubber](source-snubber.png), [rail power](rail-power.png), [rail controller](rail-controller.png), [rail gate](rail-gate.png), and [rail reset](rail-reset.png) details. The child box was moved clear of the title block; bank bars and timer capacitor references were separated from ground text. Local topology uses real green wires, upward named supplies and downward grounds. Remote gate/sense observations use justified local label connections.

Presentation acceptance is **incomplete**. S11 required visible Arial passive parameter blocks and IC MFG P/N field effects cannot be set/read back through the exposed API; persisted metadata is not a visibility pass. Export IDs remain inconsistent (root render 2/2, standalone child 1/1) despite saved child page 2 and a hierarchy renumber call. No supported root-page-number setter was exposed. The attached hierarchy and filenames are verified.

## Physical and qualification limits

[Stock query evidence](physical-query.json) records LTC4364 DE pins 1–15, DPAK 1G/2D+tab/3S, SOT23 1B/2E/3C, and diode K1/A2 joins. Panasonic mapping reuses previously approved project evidence. No PCB package placement/render was authorized; full disposable package-render acceptance is not claimed. Cold capacitance/ESR, capacitor bias/aging, shunt/snubber pulse, hot gate/TVS leakage, low-VCC clamp accuracy, MOSFET linear SOA/body-pulse/repetition and environment remain open in the parent analysis/design records. No bench test was run.

## Delivery exclusions

Only `recovery_protection.kicad_pro`, `recovery_protection.kicad_sch`, linked `recovery_rail_final.kicad_sch`, and `fp-lib-table` form the native deliverable.

The unlinked `recovery_rail.kicad_sch` is a rejected intermediate with duplicate references. Konnect explicit-UUID deletion also refused because its resolver found ambiguous references; it must not be integrated or staged. The automatically generated blank `recovery_protection.kicad_pcb` and local `recovery_protection.kicad_prl` are excluded. No native-file deletion workaround was used. No commit was made.
