# Isolated BMS supply development integration

Native basis: `f11ee84a0b302c72e44ec62f3172903e350f7f2a`; root-owned circuit authority: [integration specification](../../../design/rev_b_bms_isolated_supply_integration.md). This checkpoint adds the complete 32-part TPS2553DBVR-1 → UCC33020RAQR → LT3014IS5#TRPBF development circuit as one unique ANSI B child. It does not qualify the electrical design or release a PCB.

**Electrical verification:** fresh, unmodified KiCad CLI XML has **275 physical parts, 146 nets, 132 functional nets and 754 physical pin endpoints**. Exact whole-net comparisons cover all 81 new physical terminals, both MCU allocations, every existing net and the four migrated positives U201.8/R218.1/R219.1/C210.1. Only those four old terminals move from +3V3 to 3V3_BMS_ISO; all raw returns stay exact. PD3.29 commands EPS_BMS_PRI_EN; PD0.26 receives EPS_BMS_PRI_FAULT_N. All 243 earlier physical parts retain their UUIDs, values, footprints and exported fields.

Fresh ERC is **10 errors / 0 warnings**: seven genuinely unfinished MCU pins (7,8,11,12,17,28,32), the existing U300.25/.26 SW power-output conflict, U200.25 FUSE versus #FLG0202, and U200.15 BTP_INT versus U200.25. Types were preserved; no fake NC or exclusion hides a finding. See `erc_classified.json`. Fontconfig host diagnostics are captured separately in `cli_checks.json`; no annotation-error warning was emitted.

`verify_integration.py` checks raw component-reference uniqueness and raw endpoint uniqueness before dictionaries, exact graph union, all 23 IC pins/types, all new field values, old native symbol objects, all-symbol annotations, full-source hashes and an exact five-path protected Git guard that remains valid after commit. It byte-checks **1,257 frozen tracked CAD/evidence files** against both worktree and Git basis. All 472 previous symbol objects remain, with explicit exceptions: three existing power Values migrate to the isolated rail; #PWR0103 keeps its UUID/metadata and moves upward 2.54mm to clear the new FAULT label. The original HSE net label was re-created at its original position while arranging the new control route. No library, historical fixture or real PCB changes were made.

**Rendered inspection:** all eleven actual full-page PNGs and the six details below were opened and inspected. The whole-root PDF has eleven pages. New review callouts, named wire topology, MCU label clearance, LDO feedback label, raw-ground glyph, output print margin, capacitor groups and rating/open-gate notes were reviewed separately from connectivity.

- `primary_detail.png`: TPS, control/FAULT network, series resistor and primary reservoir feed.
- `isolation_detail.png`: all repeated UCC primary/secondary ground pins, SEL→VCC, HF bypasses and separated raw-ground label.
- `ldo_detail.png`: SHDN tie, divider, output capacitor and bleeder.
- `controller_control_detail.png`: PD0/PD3 links, C112 ground and HSE clearance.
- `bms_supply_migration_detail.png`: isolated positives and unchanged distinct return domains.
- `root_isolated_tile.png`: unique child and current development status.

Geometry checks cover **1,001 queried pin anchors**, including every power symbol and flag, on the 1.27mm grid. There are zero pin branch anchors and zero connected four-way intersections across the hierarchy. There are 76 unconnected crossings total, including three introduced on the controller route and one in the new TPS block. The connected test includes both explicit junctions and wire-endpoint-on-crossing connectivity. Every actual functional net has exactly one class match; four new rails are POWER, controls are CONTROL, ILIM/feedback are ANALOG_CONTROL. The three inherited unmatched /Controller protector patterns remain explicitly orphaned; the exposed API cannot delete native patterns.

The flag after R901 represents the actual TPS-driven passive-filter node. It adds no independent rail source. UCC secondary and LDO return to GND_BMS_RAW; the input branch returns to system GND. Only ISO1540 side2, its two pullups and local bypass are fed from 3V3_BMS_ISO. The former shared-positive gauging-current path is removed topologically; full gauging/calibration acceptance is still open.

Metadata is stored in native instances and independently checked in the raw XML/API readback. The batch edit API updates existing fields but does not create missing custom fields; the per-component API was used to create and read back every new manufacturer/rating field. The expected field contract is `expected_component_fields.json`, actual API fields are `metadata_api_readback.json`, and `fields_readback.json` comes from the unmodified CLI export.

Presentation policy is not fully passed. S03 native ERC-severity persistence, S11 custom-field display/font control and S04 child standalone-render pagination remain API limitations. S06 inherited root filename anchors still associate controller/CAN filenames poorly after historical sheet moves. U900's anchored Value is close to its bottom ILIM pin-number stroke; the supported reset-field-position dry run reports it already at the library anchor, with no arbitrary instance field-position API. Green **CUSTOM — REVIEW REQUIRED** callouts implement the approved alternative; symbol bodies are not claimed green. Re-linking the new child while moving its root tile retained an inactive earlier instance path in its new symbols; the active hierarchy exports once with unique annotations and no CLI annotation warning.

Remaining hardware gates include coupled UCC/LDO startup/prebias and repeated faults, unknown off-state feed paths, effective C/ESR/aging, weak-source/UVLO and essential-loop behavior, autonomous 3V3 OV containment, initial short surge / healthy CAN survival, hot/pulse/SOA, EMC, calibration and physical fit. The 2s LOW command is a discharge/latch-clear attempt, not a guaranteed full power cycle; an MCU reset releases default-on. UCPD dead-battery initialization and fresh-valid-telemetry recovery are requirements, not implemented firmware. Missing RBF still separates PROTECTED_PACK from BATT_PERMITTED.

Reproduce with the workspace Python runtime:

```sh
python3 hardware/eps/verification/rev_b/isolated_bms_integration/refresh_exports.py
python3 hardware/eps/verification/rev_b/isolated_bms_integration/verify_integration.py
```

Authoritative final artifacts are `eps_rev_b.xml`, `erc.json`, `eps_rev_b.pdf`, `verified.json`, `endpoint_contract.csv`, `package_pin_map.csv`, `reference_UUID_crosswalk.json`, `geometry.json`, `class_membership.json` and the eleven named sheet PNGs. `before.xml`, three before-text snapshots and `baseline.json` retain the initial boundary. `readback.json` is supplemented by the final controller/isolated readbacks. No real PCB synchronization was performed.

Exact native delta: modify `eps_rev_b.kicad_sch`, `eps_rev_b.kicad_pro`, `controller.kicad_sch`, `bms_protection.kicad_sch`; add `bms_isolated_power.kicad_sch`, all under `hardware/eps/rev_b/`. Other agent-owned additions are confined to this evidence directory; root-owned research/ledger/fit edits are outside its manifest.
