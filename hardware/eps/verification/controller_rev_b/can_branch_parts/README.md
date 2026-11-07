# CAN branch inverter: development contact-map acceptance

2026-10-24, pre-integration basis `2d1ff31`. **TI SN74LVC1G14DBVR** is accepted for development contact mapping with unchanged stock `74xGxx:SN74LVC1G14DBV` and `Package_TO_SOT_SMD:SOT-23-5_HandSoldering`. No custom component or real EPS placement is part of this package checkpoint.

Primary source: [TI SCES218AA, October2025](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf), local `sn74lvc1g14.pdf`, SHA256 `c21067b4f4119d0981fb2e8d73b987b0e661c86f7bb0ed161f23a4b599fd68a7`. Actual p3 pin figure, p4 function table, p7 electrical table, p12 application, p17 order table and p28–30 package/land/stencil images were opened and inspected. The DBV0005A drawing is4214839/K,08/2024. Exact ordering is DBVR,5leads,large3000reel,−40..125°C table range; this does not establish procurement/flight acceptance. The earlier Nexperia candidate was superseded before native placement by this accessible TI primary source.

**Map:** top/component view, pin1 upper-left, counterclockwise down the left row1/2/3 then right4/5. Leads are1NC,2A,3GND,4Y,5VCC. The stock symbol has five separate physical pins, including no-connect pin1; its A/Y graphical pins have blank names but exact numbers2/4. All five library, saved-board and live-after-save pad objects are counted before keyed comparisons. No duplicate, exposed, mechanical or drilled objects exist. `physical_map.csv` joins every lead to its symbol type and front pad coordinate.

The standard SOT-23-5 footprint was reviewed and not selected: its stepped courtyard leaves only0.175mm at the maximum-body corners. The selected hand-solder variant uses1.56×0.65mm pads atX±1.35,Y−0.95/0/+0.95 andR0.1625; TI's example uses1.10×0.60 atX±1.30,R0.05. Copper/paste/mask geometry therefore is **generic stock, not exact TI**. Its F.Fab outline1.8×3.1mm also differs from TI nominal1.6×2.9mm.

The stock rectangular courtyard isX±2.38,Y±1.8mm. It clears outer pads by at least0.25mm, and maximum body length3.05mm by0.275mm. But including TI's allowed0.25mm/side mold flash givesYhalf1.775mm and only0.025mm clearance. Development use is explicitly conditional on reserving **at least4.76×4.05mm** in later layout, including Yhalf2.025mm for the full flash envelope plus0.25mm clearance. The stock footprint was not modified. Pin1 silk marker extends beyond the stock courtyard; reference text also needs normal layout placement. No complete mechanical/assembly pass is claimed.

The new disposable board was opened through KiCad manager. Konnect confirmed exactly one open IPC board at the expected fixture path before placement; one U1 was placed and saved through Konnect. All five live positions/layers/net states match the saved instance/library. The actual saved board has0.05mm inherited mask margin, no footprint/pad override, and five corresponding mask apertures. Fab pad numbers come from the CLI's native sketch-pad overlay, not an invented label drawing.

**Electrical fixture check:** one native symbol, one genuine NC marker only on physical1, four functional pins intentionally unwired. Raw CLI ERC reports7errors (4unconnected,2power-not-driven,1input-not-driven),0warnings; no fake flags. This fixture does not test inverter logic or the proposed CAN supply circuit.

**Actual visual inspection:** `symbols.png`, `symbol_detail.png`, `board_copper.png`, `board_paste.png`, `board_mask.png`, `board_fab.png` and `board_silk.png` were opened and inspected. Pin1 key, CCW rows, five copper/paste/mask contacts, numbered fab and the generic courtyard agree with query-back. All source figures are under `source_figures/`. The saved board closed cleanly: the UI close returned an AX timeout, but Konnect confirmed zero open boards and no save/discard prompt appeared. Closed-editor pad-query AS_UNHANDLED is recorded; the required live-after-save query had already passed. Opening normalized only this new fixture's project to KiCad10 meta version3.

`verify_parts.py` checks every raw pad geometry/layer/no-drill, live/saved counts, symbol types/instance metadata, legitimate NC, IPC identity, source hash and exact preservation of 203 portable preexisting protected sources plus all five specified untracked progress artifacts. One local `.history` PCB snapshot was removed from the original 204-file preservation scope; it remains untouched locally. It is a pre-integration checkpoint: later explicitly authorized real CAN changes supersede the main-source freeze, while this fixture remains immutable. Its accepted geometry is reused by the separate integrated verifier; do not reinterpret its earlier preservation result as a claim that later main schematics stayed unchanged.

Portable manifests exclude `.history` / embedded `.git`, caches, locks, PRL and backup state, without deleting or staging those local files. The corrected package manifest contains 37 actual source/review artifacts instead of 63 entries (26 local history entries excluded). No CAD, physical map, source figure, query, render or electrical result changed. The recorded pre-integration preservation count was adjusted by scope only; its superseded main-source freeze was not rerun after real integration.

Run with the workspace Python runtime before real integration:

```sh
python3 hardware/eps/verification/controller_rev_b/can_branch_parts/verify_parts.py
```

Exact added protected files are only `disposable/can_branch_parts_check.kicad_sch`, `.kicad_pro` and `.kicad_pcb`. No vendor/global library changed. Electrical/PVT, Schmitt supply-range thresholds, signal timing, shared-source fault survival, mask/stencil/assembly and flight acceptance remain separate.
