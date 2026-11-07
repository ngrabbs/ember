# BMS integration development checkpoint

Basis: `b9d0724b1f56e508d3fbec67cd0b472d1073022f`, KiCad CLI 10.0.0. The new ANSI B **2S pack protection** child adds the BQ40Z50RSMR-R2 core, common-drain CHG/DSG pair, precharge path, cell/shunt filters, two external NTC interfaces, seven-contact sense harness and provisional ISO1540 SMBus interface. This is a reviewable development circuit, not commissioned pack protection or fabrication qualification.

## Electrical evidence

`verify_bms.py` passes **233 physical parts / 133 nets / 115 functional nets / 648 unique physical ref.pin endpoints**. It checks all 33 BQ physical pins, every new passive/FET/connector/testpoint terminal, 34 declared whole-net sets, reference uniqueness before dictionary conversion, all 451 symbol annotations and the complete baseline graph union. All 187 prior physical UUIDs and all 359 prior symbol objects remain; the only prior metadata exceptions are the authorized TCR corrections on R601/R610/R612/R614/R621 from 25 to 100 ppm/K. `tcr_correction.json` proves their field-only graph preservation.

Fresh `eps_rev_b.xml`, `erc.json` and nine-page `eps_rev_b.pdf` were exported after the final presentation repair. No annotation warning was emitted. ERC retains **14 errors / 0 warnings**: 11 unfinished MCU pins, the inherited U300.25/U300.26 SW power-output pair, and the intentional BQ FUSE.25-to-BTP.15 / FUSE.25-to-#FLG0202 raw-return pairs. Electrical pin types were preserved; no artificial no-connects or exclusions were added.

`geometry.json` checks all wire endpoints and all 260 queried physical/power/flag pin anchors on the 1.27 mm grid. BMS: 182 segments, zero connected fourways, 14 unconnected crossings; controller: 82 segments, zero connected fourways, 22 unconnected crossings. No queried pin lies on a branch. `class_membership.json` proves exactly one intended class for each actual functional net. The three inherited `/Controller/REC5_*` / `/Controller/SRC_FAULT` patterns remain unmatched orphans because native pattern deletion is not exposed.

`BATT_RAW`, `CELL1_RAW`, downward `GND_BMS_RAW`, `BMS_FET_DRAIN` and `PROTECTED_PACK` remain distinct. R200 is the intended metal connection between raw return and system GND. **PROTECTED_PACK is before the absent physical RBF and is not joined to BATT_PERMITTED.** Existing BATT_PERMITTED, VIN_CHG and SYS_PWR_PERMITTED endpoint sets are unchanged. Flags describe actual external raw-cell fixtures, passive filtering or internal PBI energy paths; they do not bypass protection.

## Part and physical-map evidence

The accepted project BQ symbol/land and CSD18543Q3A lands retain bright-green **CUSTOM — REVIEW REQUIRED** callouts. No new custom library was authored. `fields_readback.json` and `bom.csv` record all 46 new physical parts, including controller R111/R112. The BOM is a review output, not an assembly release.

`verify_parts.py`, `parts_readback.json` and `parts_physical_map.csv` check five stock candidates in a separate saved disposable schematic and actual PCB: ISO1540DR, BM07B-GHS-TBT(LF)(SN), BSS84-7-F, BAT46W-7-F and DMN62D2U-7. All **25 raw pad objects = 23 electrical symbol pins + two floating mechanical MP objects** are checked before unique-key conversion. Dimensions, coordinates, layers, radii, no-drill properties and saved instances agree. The fixture was closed before final hashes; its project normalized to KiCad meta version 3. Locks, PRL and GUI caches are excluded.

Stock lands are documented deviations from manufacturer recommendations: ISO1540 SOIC pads are 1.95 × 0.6 mm at X ±2.475 mm versus TI's 1.55 × 0.6 mm at ±2.7 mm; JST GH signal pads are 0.6 × 1.7 mm versus the reference 0.6 × 1.35 ±0.1 mm. JST's front-mount drawing is rotated 180 degrees in the stock footprint. Diodes drawings identify physical G/S/D positions; the stock numeric G1/S2/D3 mapping is checked by those positions, not an invented printed numeric key. These checks establish development identity, not solder-process or temperature qualification.

Manufacturer drawings actually inspected: TI BQ SLUSCS4C Rev C Figures 9-1/9-2/9-12/9-13 and electrical table 7.18; TI ISO1540 SLLSEB6F pin/application/land figures; JST eGH pages 2–3; Diodes BSS84 DS30149 Rev 27, BAT46W DS30044 Rev 20 and DMN62D2U DS44892 Rev 3. Precision resistors use Vishay TNPW document 28758 Rev 10-Apr-2026 **0.110 W general P70**; 10 MΩ CRCW uses document 20035 Rev 14-Apr-2026, 5%, 200 ppm/K, standard 0.10 W P70. CRCW1206 HP code K is 100 ppm/K.

## Actual rendered inspection

All nine full-sheet PNGs were opened and inspected, separately from electrical checks. Changed-sheet details opened: `bms_power`, `bms_ic`, `bms_cell_filters`, `bms_shunt`, `bms_bus`, `bms_harness`, `bms_top_note`, `controller_bus`, `controller_bms_notes` and `recovery_bms_note`. The final controller and BMS full pages were reopened after repair. The controller allocation note no longer overlaps the SWD note, the BMS boundary note clears the upper frame, the BAT-filter flag clears the power-name text, and the charger-alert branch clears both new SMBus label glyphs.

Final five-part disposable symbol/copper/numbered-fab full views and details were also opened. Tiny numbered fab overlays cross body strokes; numeric pad readback is checked independently. Inherited visible-field/pagination limitations remain. S11 styling is not satisfied merely by metadata: the exposed API cannot set the required custom-field presentation. S03 native severity persistence is unsupported. Generic `batch_delete(uuids)` was tested on a new `/tmp` text-only disposable and **does support free text**; delete/re-add was then used for the two new annotations. No dedicated free-text move/edit API exists. Older contradictory absence notes remain visibly superseded by dated corrections, rather than carrying authority.

## Explicit engineering gates

- Q201 output-short VGS may exceed its ±20 V absolute rating: the BQ drive can approach VBAT + 12 V while PACK collapses. Q203 does not contain this case. Gate clamp, coupled cutoff and hot SOA remain open; no survival claim is made.
- Q203 DMN62D2U-7 uses **S2=PROTECTED_PACK, D3=DSG main gate, G1 through 1 kΩ to system GND**. The parent-owned `verification/bms/reverse_clamp` diagnostic supports development selection only; its typical model and assumed negative BQ drive do not qualify hotplug or temperature protection.
- Shared-positive ISO1540 power with distinct returns creates up to **8.42 mA state-dependent shunt-current offset**, potentially reversing the idle-current sign. Gauging is not accepted; isolated power remains unresolved. See the parent-owned BMS bus screening record. This is not whole-board galvanically isolated power.
- Local SMBus is 100 kbit/s, conditional on ≤40 pF side 1 / ≤200 pF side 2 and both supplies ≥3 V for 1 ms before polling. Reserve 13.8 mA IC plus 3.431 mA pullups. Static margins do not prove transient or power-off behavior.
- C203 requires ≥2.2 µF effective capacitance; its bias/temperature minimum and BAT hold-up/diode leakage are unverified. The 10 MΩ gate pulls retain TI's driver-test load; hot leakage and turn-off remain open.
- The 300 Ω precharge path has an illustrative ≤28.9 mA / approximately 0.246 W bound at 8.526 V and minimum resistance 295.05 Ω. Its 0.75 W P70 rating assumes thermal resistance ≤110 K/W; pulse/SOA/cold acceptance is open. 8.526 V is a sizing case, not an approved pack threshold.
- The 2 mΩ shunt, TS1/TS2 cell-temperature configuration, disabled TS3/TS4/display/PTC/PRES paths, permanent-failure policy, current calibration, NTC harness, pack thermal construction and commissioning manifest remain unqualified. No firmware/program image was generated.
- Physical RBF, charger-to-pack 35 V failed-short containment, shared startup/source-energy limits, autonomous 3V3 OV protection and CAN branch fault containment remain open.

## Reproduce and scope

From the repository root run `python3 hardware/eps/verification/rev_b/bms_integration/verify_bms.py`. To deliberately regenerate read-only CLI outputs first, run `refresh_exports.py`; it records exact commands, stdout/stderr, version and hierarchy hashes. `native_source_sha256.json` prevents stale exports from outliving native edits. `changed_paths.json` lists the exact six modified and four added protected files. The guard compares against b9d0724 and also works after commit.

The original broad baseline capture is retained, but only **61 Git-tracked charger checkpoint artifacts** are asserted byte-identical to both b9d0724 and the current worktree. The 34 ignored GUI/history files are reported separately; only a Finder `.DS_Store` change and a removed stale lock differ. No historical source, library or real PCB was changed. No real integrated PCB synchronization was performed.
