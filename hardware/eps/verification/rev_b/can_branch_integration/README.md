# CAN A/B branch integration — development checkpoint

Basis: `2d1ff31`, project `hardware/eps/rev_b/eps_rev_b.kicad_pro`.
Contract: `design/rev_b_can_branch_integration.md`; electrical screens remain in
`verification/controller_rev_b/branch_control_screen` and `coupled_branch_screen`.
This checkpoint implements the drawing; it does not qualify shared-rail fault
survival, PVT, timing, thermal operation, arbitrary shorts or flight hardware.

## Electrical and preservation evidence

The unmodified whole-hierarchy KiCad 10 CLI export is `eps_rev_b.xml`:
**305 physical parts, 166 nets (150 functional), 826 unique physical endpoints**.
The 30 additions use R1100–R1119, U1100–U1103, C1100–C1103 and TP1100/1101.
`verify_integration.py` constructs and compares the entire expected graph from
`before.xml`, including all new terminals and every existing net. It rejects raw
duplicate references and endpoints before dictionary conversion.

Each TPS2553DBVR-1 has 210k ILIM, a post-switch 1 ohm resistor, local bypass,
100k EN pulldown, FAULT bench testpoint and 10k output bleed. A shared-rail
SN74LVC1G14DBVR drives EN through 1k. STB HIGH/default turns the channel OFF;
STB LOW enables normal operation. A disabled channel cannot wake from CAN.
FAULT has no MCU diagnostic allocation. The provisional startup/reset wait is
20 ms; complete discharge and reliable reset through all off feeds remain gates.

Only the ten old VCC/VIO/capacitor positive terminals move to `3V3_CANA/B`.
The six TCAN signal terminals move behind new 1k series resistors. Existing
R101–R104 pullups remain shared +3V3 on the MCU side; each RXD gains a shared
47k MCU-side pullup. CAN H/L, connectors and termination remain exact.
Full endpoint sets are in `endpoint_contract.csv`; all 22 new IC pins have
queried/saved name/type maps in `package_pin_map.csv`. Passive and testpoint
terminals are included in the full 72-new-pin graph contract.

All **275 previous physical UUIDs and exported metadata** remain exact. All
**524 old native symbol objects** remain exact except the explicitly authorized
Values of #PWR0112 / #PWR0117 (+3V3 to 3V3_CANA/B). There are 582 current
symbol/unit objects with unique annotations. Controller source is byte-preserved.
The only current-main protected changes are root schematic/project and CAN
interfaces, plus the new `can_branch_power.kicad_sch`. No PCB synchronization or
new library authoring occurred. The independent inverter fixture is separately
frozen under `verification/controller_rev_b/can_branch_parts`.

The baseline preserves 1,365 unique portable source/evidence files, including
200 other protected files, all five preexisting untracked progress files and
the accepted inverter package artifacts. Category counts overlap; the verifier
deduplicates them. Portable scope excludes 26 package `.history` entries and one
older local-history PCB snapshot previously imported into the baseline; these
27 local runtime files remain untouched and are not acceptance prerequisites.
The package manifest now binds 37 actual CAD/source/review artifacts. Tracked
`.gitignore` files remain legitimate frozen evidence. Caches, embedded `.git`,
locks, PRL and backup runtime state are excluded by path-aware filters.
The protected-path guard works before and after committing
this checkpoint, and the current source hashes bind all CLI/visual evidence.

Fresh `erc.json`: **10 errors, 0 warnings**, unchanged: seven genuinely unfinished
MCU pins (7/8/11/12/17/28/32), and three previous intentional pin-type conflicts
(charger same-IC SW25/SW26 outputs, BMS FUSE25 versus raw-source flag, and
BMS unused BTP_INT15/FUSE25 ties). No pin types,
exclusions or unrelated NC flags were weakened. Each inverter physical NC1 has
the legitimate datasheet NC flag. See `erc_classified.json` for exact items.
CLI stdout/stderr and commands are preserved in `cli_checks.json`; the XML is
not enriched or postprocessed. Fontconfig diagnostics are distinct from ERC.

All 18 new functional nets have one persisted class each, and all 150 actual
functional nets match exactly one class. The three inherited orphan patterns
`/Controller/REC5_RESET`, `/Controller/REC5_FAULT`, `/Controller/SRC_FAULT`
match no current net and are retained because no supported pattern-delete API
exists. `class_membership.json` and `netclass_readback.json` record this.

## Actual rendered inspection

All **12 full pages and 14 details** were opened and inspected; image hashes and
source binding are in `visual_review.json`. The PDF is the actual 12-page root
export. Changed views: `can_branch_power.png`, `can_interfaces.png`,
`eps_rev_b.png`, `branch_a_detail.png`, `branch_b_detail.png`,
`can_a_signals_detail.png`, `can_b_signals_detail.png`, `root_branch_tile.png`.
The new signal resistors/pulls, supply boundaries, inverter NCs, review markers,
FAULT bench paths and control polarity are legible.

Geometry checks include all queried power/ground/flag anchors and raw saved
segments: **zero connected fourways and zero pin/branch anchors** on all sheets.
The new branch page has zero unconnected crossings. The CAN interface page has
four unconnected crossings (the RX pull verticals over TX/STB); no dots, wire
endpoints or labels occur at these crossings. Existing crossings are enumerated
in `geometry.json`. Wire/pin anchors are on the 1.27 mm electrical grid.

This is not a whole-policy presentation PASS. S11 custom fields are saved and
checked, but required per-instance field positioning/font/visibility APIs remain
limited; readable adjacent family/rating blocks supplement them. TPS Value/pin5
anchors remain close, with separate legible glyphs; stock pin names are preserved.
The supported green callout alternative marks custom TPS symbols; body graphics
are not claimed green. Inherited root sheet filename anchors remain detached
from some old boxes (S06); individual child PNG pagination reports 1/1 while the
root PDF has 12 pages (S04). S03 fourway severity cannot be persisted through the
exposed API, so explicit geometry checks remain necessary. Prior unrelated
annotations and their dated corrections are preserved.

## Physical package and remaining gates

The TI inverter stock five-lead contact map passed independent saved/live board
verification before real placement. Its generic HandSoldering footprint is not
the exact TI land; the stock courtyard has only 0.025 mm worst-flash Y margin.
Later placement must reserve at least **4.76 x 4.05 mm**, including package flash
and 0.25 mm clearance. Package/assembly/mechanical qualification remains open.

The conditional screen's RXD high margin is about 68 mV; inverter thresholds use
adjacent discrete supply rows and do not establish continuous 3.3 V/PVT limits.
Nominal imposed-load reset/fault simulations are not guaranteed initial-short
response, healthy-channel survival, source/TPS-OUT fault containment, thermal
performance or complete off-state discharge. Shared +3V3/GND/MCU/clock remain
common paths. RBF, autonomous essential-3V3 OV containment, source/pack failed-short
containment, commissioning, and the earlier system qualification gates remain open.

Reproduce: run `verify_integration.py` with the bundled Python runtime. Fresh
read-only exports can be regenerated by `refresh_exports.py`; re-render and
inspect if native sources change. Historical verifiers/artifacts stay frozen.

## Independent root review

After the explicit native write freeze, fresh independent CLI component/net
blocks matched this checkpoint exactly. A separate semantic verifier checked
all275 old physical metadata records,16 allowed terminal migrations, every new
branch resistor/MPN/rating, all72 added endpoints,150 actual persisted class
matches and the unchanged ERC signature/exclusions. Root also opened all12 full
pages and14 details. Evidence and commands are in
`../../controller_rev_b/branch_control_screen/root_review.json`; the fresh raw
netlist is retained in the new CAN-stage fit inventory. The actual PDF first
root page also shows Id12/12, so the12-page count is not coherent-pagination
acceptance. The protected-delta report is sorted to remain stable across commit.
