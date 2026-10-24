# Converter output-bank voltage correction — native evidence

2026-10-23. The existing `recovery_5v` development schematic now has a 50 V output bank. This is a bounded bank correction; converter/protection integration and complete coupled-loop acceptance remain open.

## Saved hardware

- C9–C12 and new C19–C22: eight 10 µF, 50 V, 10%, X7R **CGA5L1X7R1H106K160AC**, stock 1206 lands.
- C13–C15 and new C23–C24: five 68 µF, 50 V, 20% hybrid **EEHZA1H680P**, reusing the already-approved Panasonic F project land and positive-pad-1 map.
- C16 remains its original 100 nF / 50 V bypass, unchanged.
- All thirteen bank pin-1 endpoints are on **5V0_RECOVERY_RAW**, before R4; all pin-2 endpoints are on GND. Existing `+5V`, `+3V3`, `SYS_PWR_PERMITTED` and every other interface remain unchanged.

Nominal bulk-plus-ceramic bank is 420 µF, plus C16. The initial high-tolerance sum is 496 µF; **the endurance-plus-tolerance maximum used by the parent study is 618.4 µF plus C16**, against a 650 µF development allocation. Nominal values and arithmetic are not guaranteed cold/bias/aging capacitance. Effective branch capacitance, ESR, endurance, leakage, physical fit and pulse qualification remain open.

## Electrical evidence

[verify_bank.py](verify_bank.py) checks fresh [before.xml](before.xml) and [after.xml](after.xml), with [verified.json](verified.json) recording:

- **16 functional plus 3 intentional NC endpoint sets pass**. The only endpoint additions are C19–C24 pin 1 to RAW and pin 2 to GND.
- **34 physical parts**, increased from 28. All original 28 component UUIDs are preserved. The 21 unrelated component records, including C16, R4 and U1, are identical in the exported before/after data.
- Required bank MFG P/N, voltage, tolerance, dielectric, package and footprint fields match the exact selected parts.
- Saved POWER/ANALOG_CONTROL assignments still cover exactly all 16 functional nets; no project-setting mutation was needed.

[Direct KiCad CLI ERC](erc-cli.json): **0 errors, 0 warnings**. [Konnect readback](readback.json): zero floating wire ends, unconnected required pins, shorted named nets or orphan items. [Geometry check](geometry-check.json): no four-direction wire endpoints, collinear overlaps or off-grid wire endpoints. The inherited four-way-junction check is still ignored by native ERC; [the exposed-API limitation](../../native/erc-severity-api-limitation.json) remains separate from the geometry pass.

[Current BOM](development_bom.csv), [canonical netlist](after.net) and XML are the current bank evidence. Earlier study exports and historical verification files were retained.

## Actual visual inspection

The final [ANSI B full page](bank.png) and [bank/FB detail](bank-detail.png) were opened and inspected. The ceramic population occupies two rows and the five hybrids a third row. The hybrid feed bar was lowered one grid interval to 160.02 mm to separate it from the second row's GND text; FB's horizontal wire and local label moved from 180.34 to 184.15 mm. Real local wires, upward RAW supply symbols, downward grounds, polarity markings and exposed wire stubs are visible. The controller and all unrelated circuits retain their prior arrangement.

S11 visible Arial/orientation-aware parameter blocks remain **API-blocked**. Fresh exported metadata does not satisfy that presentation gate. Existing custom-symbol review marking and approved Panasonic construction status remain unchanged; no new custom symbol or footprint was created.

## Scope and checkpoint

Only `hardware/eps/studies/recovery_5v/recovery_5v.kicad_sch` changed among the existing project files. [Checkpoint evidence](checkpoint.json) records the clean pre-change Git commit/blob and confirms the PCB SHA-256 is unchanged. All KiCad mutations used Konnect 0.11.1 with KiCad CLI 10.0.0. No PCB, project, library, protection-project or interface mutation occurred; no commit was made.

The parent simulation work accepted this voltage correction independently of its remaining integrated LC crossings, low-FB load-release/latch behavior and physical qualification. This native report claims circuit/metadata/ERC/render verification only, not complete coupled-system or fabrication acceptance.
