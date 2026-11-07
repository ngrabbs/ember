# Rail Telemetry development integration

Saved native checkpoint based on `2600a17`, under `design/rev_b_adc_frontend_integration.md`. Four switched, filtered divider channels measure SYS_PWR_PERMITTED, protected +5V, essential +3V3 and BATT_PERMITTED. U1300 is the existing approved TMUX1511PWR review symbol; U1301 is a separate TPS3839K33DBZR qualifier. All 10 nF C0G filters precede the switch; there is no deliberate MCU-side storage capacitor. This is a development schematic, not autonomous protection or accuracy/PVT acceptance.

Run with the bundled Python runtime (pypdf required):

```sh
python3 hardware/eps/verification/rev_b/adc_integration/verify_integration.py
python3 hardware/eps/verification/rev_b/adc_integration/hash_evidence.py --check
```

`refresh_exports.py` records unmodified KiCad CLI XML/ERC/PDF, commands and native-source hashes. No XML metadata enrichment is used. `readback.json`, `fields_writeback.json` and saved native properties corroborate complete per-instance metadata; get_schematic_component alone does not expose custom fields.

## Electrical and preservation evidence

`verify_integration.py` passes: **345 physical parts, 186 nets, 173 functional nets, 933 physical endpoints, 14 sheets**. Exact whole-net assertions cover every new terminal and all four MCU crossings. All **318 prior physical UUIDs/metadata**, **616 old symbol AST objects** and **1967 frozen files**, including the five preexisting user progress files, remain exact. The only protected changes are root hierarchy, controller, project netclass assignments and the new `rail_telemetry.kicad_sch`. No library or PCB changes occurred. `presentation_crosswalk.json` records the exact two authorized obsolete controller-note replacements; unrelated notes are retained.

Fresh ERC has **6 errors / 2 inherited warnings**: three genuinely unfinished MCU pins (PB15/PD2/PB8), three previously documented intentional joins and the two prior SWD bidirectional/power-flag warnings. No exclusions or pin-type weakening were added. `erc_classified.json` is asserted against the prior checkpoint minus precisely the four now-connected ADC pins.

All actual nets have one intended class. Fifteen patterns add the four global ADC nets, eight divider/switched segments, two upper-divider midpoints and CONTROL qualifier. Six inherited orphan patterns match no current net. New-sheet geometry: 80 wire segments, 92 queried pin anchors including power/ground, three unconnected crossings, zero connected fourways and zero pin-on-branch anchors. Controller: 88 segments, 76 anchors, 27 unconnected crossings, zero connected fourways/pin branches. Wire endpoints and anchors are on the 1.27 mm grid. Endpoint-on-crossing connectivity is included in the fourway test.

`package_pin_map.csv` verifies all 17 IC leads against unchanged accepted embedded symbols and transformed live queries. Stock footprint raw/unique counts are 14/3/2/2. Each of the 27 parts has explicit manufacturer/MPN/package/rating fields. TNPW0603 parts use 0.1%, 25 ppm/K, **0.110 W general P70**. C1300–1303 are TDK CGA3E2C0G1H103J080AA (10 nF, 5%, 50 V, C0G); local 100 nF bypasses reuse GRM188R72A104KA35D.

## Actual rendered inspection

All **14 full-page PNGs and 18 detail PNGs** listed and hash-bound in `visual_review.json` were actually opened and inspected. The complete hierarchical PDF is `eps_rev_b.pdf`; new page `rail_telemetry.png`, four channel details, `telemetry_supply_detail.png`, `controller_adc_detail.png` and `root_adc_tile.png` show the changed drawing. Earlier `resistor_orientation_trial.png` is intermediate evidence only.

The nine initially rotated resistor References were fixed through supported stock-symbol rotation/reset operations and short ground bends, preserving UUIDs, metadata and nets. All 19 new resistors now have upright References above body and centered Values; all six capacitor References are upright. `field_effects.json` is checked against the saved native properties. The title says **switched**, not galvanically isolated. The visible green CUSTOM—REVIEW REQUIRED callout is the approved body-color alternative; it does not claim green symbol bodies or qualification.

S11 remains partial: supported field tools do not provide full font/visibility/anchor styling; explicit parameter blocks aid review without claiming all policy presentation requirements. Existing root filename-field associations remain detached/misassociated because sheet-field anchors are unsupported. Native connected-fourway ERC severity cannot be set through the exposed API; the separate geometry gate checks it. Standalone pages retain their existing page counters; the actual root PDF contains 14 pages. Generic stock lands and recorded TMUX/TPS flash/clearance reservations remain layout/manufacturing gates.

## Sources and open acceptance

`sources.json` identifies manufacturer publications and access limits. The manufacturer-authored ST DS13560 Rev 6 PDF is archived from a distributor mirror and crosschecked against the official ST document. Actual pinout, ADC tables, idle/rearm requirement and Figure 29 connection pages were rendered and inspected (p36, 100–102, 106); p103 was rendered but is not claimed inspected. TI TMUX functional/application figures and Vishay general-power/order-code figures were actually viewed. TDK exact-product metadata was checked on its manufacturer page; direct catalog download failed, so no unavailable TDK PDF figure inspection is claimed.

The loaded divider gains, leakage, precharge, settling and imposed 60 V/6 V/3.6 V ceilings are conditional engineering screens in the root-owned ADC calculations. They do not establish arbitrary fault/brownout survival, reference accuracy, crosstalk or full-temperature performance. Firmware must configure analog/no pulls, apply the specified sampling/VDDA conditions, calibrate and rearm after long idle (>100 microseconds); a 10 Hz scan alone is insufficient. Wait/first-sample handling and actual PVT timing remain validation gates. Existing RBF, charger-to-pack fault, 3V3 OV, hot SOA, shared startup, commissioning and mechanical/layout gates remain open. No PCB synchronization or fabrication qualification was performed.

## Portable evidence

`baseline.json` records the exact frozen set and exclusions for root-owned concurrent analysis. `native_source_sha256.json` binds current native sources; the verifier checks those bytes before relying on exports. `evidence_sha256.json` covers portable current evidence and the four authorized native paths, excluding runtime `.history`, `.git`, lock/PRL/cache/backup state. It does not freeze volatile local history or imply root-owned concurrent evidence was modified by this agent.
