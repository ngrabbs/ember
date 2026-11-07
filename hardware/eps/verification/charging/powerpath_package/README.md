# CSD18543Q3A package acceptance

2026-10-24, baseline `2450670`. Construction was explicitly approved under
`hardware/eps/design/rev_b_charger_powerpath_footprint_rules.md`. The saved
footprint and disposable instances pass the physical mapping checks for
**development use under the approved rounded-rectangle decomposition**.
**CUSTOM FOOTPRINT — REVIEW REQUIRED** metadata/callouts remain. This is not
assembly, electrical/thermal, sourcing, fit or flight qualification.

## Physical and electrical evidence

The stock `Transistor_FET:CSD18543Q3A` is unchanged: five logical pins, with
source 1/2/3 stacked, gate 4 and drain 5. `physical_map.csv` has all nine physical
contact rows; drain terminals 5/6/7/8 and thermal region 9 intentionally alias
logical pad 5. The thermal region is drain, never ground. Exact MFG P/N is
`CSD18543Q3A` in the disposable schematic and board Value.

The new project-owned footprint is
`Ember_Charger_BMS_Review:TI_CSD18543Q3A_Q3A_Manufacturer`. It contains **30 raw
objects: nine numbered Cu/Mask objects, twelve unnumbered Paste-only objects
and nine unnumbered Mask-only objects**. There are five unique electrical
numbers, with five separate objects numbered 5 and four intentional number
repetitions. `all_objects.csv` records every saved object. Counter comparisons
and raw-list lengths retain all repeated numbers and blank objects; nothing is
hidden by a number-keyed dictionary. All sizes, positions, layers, radii,
zero rotations and no-drill states match the approved tables.

Authority is TI **SLPS633, December 2016**, printed pp.1/8/9/10. The top-view pin
figure and bottom-view mechanical drawing were reconciled with the front-side
copper/stencil views: pin 1 upper-left, counterclockwise; X right/Y down.
All four source figures were actually opened and inspected; paths and hashes
are in `source_manifest.json`.

The drain fingers overlap the central region by 0.100 mm nominally, leaving
at least a 0.050 mm full-height overlap despite their R0.05 corners. The drain
union is connected. Its outer projection is 0.635 mm beyond central X=1.215,
ending at X=1.850. The decomposition does **not** reproduce TI's internal
concave R0.05 arcs: the eight junction-corner differences remain localized
within 0.05 mm extents. This approved approximation is not described as an
exact TI copper outline. Manufacturing corner fidelity remains open.

TI p.9 requires at least 0.05 mm mask expansion. With no supported native
mask-margin setter, nine explicit blank Mask-only roundrects enlarge each
actual copper object's width/height by 0.10 mm and radius from 0.05 to 0.10 mm.
Their union supplies the minimum 0.05 mm expansion; actual mask/copper exports
were inspected. The scratch board's default mask clearance is also 0.05 mm.
No copper object has automatic Paste. The twelve separate paste apertures
implement the eight perimeter/four central TI pattern. Stencil thickness,
release behavior and via-in-pad processing remain unqualified.

`readback.json` contains library, stock-symbol, disposable symbol and saved
live PCB pad queries. Konnect confirmed the exact isolated scratch board
before placement, placed Q1 at (25,25) mm/front/zero rotation and saved it.
Read-only saved native geometry supplies sizes/types/radii/drills omitted by
the live pad-position API, tied to the PCB source hash in `saved_geometry.json`.
No routing, vias, zones or outline were added.

Fresh CLI XML proves the stock source-stack endpoint set {Q1.1,Q1.2,Q1.3},
plus isolated gate 4 and drain 5. ERC reports **four expected errors, zero
warnings**: three unconnected endpoints and one undriven input. This unwired
inspection fixture has no fake source flags or NC suppression; it is not an
operating circuit test.

## Actual rendered evidence

`symbol.png`/`symbol.pdf` and `symbol_detail.png` were opened and inspected.
The official symbol shows source 1; hidden stacked source 2/3 are retained by
query and XML. The exact part identity and green footprint-review callout are
visible. No custom symbol was authored.

Saved-board views were actually opened and inspected: `board_copper.png`,
`board_paste.png`, `board_mask.png`, `board_mask_copper.png`, `board_fab.png`
and `board_silk.png`. The continuous drain outline, twelve distinct paste
apertures, expanded mask, fab key and silk dot agree with the construction.
Root independently inspected the schematic detail and copper/paste/mask/fab/
silk views.

Two presentation limits are explicit: Konnect's default placed Reference Q1
crosses the central drain/mask in the silk view; the library outline and dot
are clear, but **the entire placed silkscreen is not accepted**. The exposed
`edit_component` operation cannot reposition fields. Fab sketch strokes also
obscure parts of tiny pad-number glyphs; all numeric mapping is corroborated
by the raw object checks. Production reference placement remains layout work.

## Reproduction and preserved scope

Run `python3 hardware/eps/verification/charging/powerpath_package/verify_package.py`
from the repository root. It verifies the mapping, all 30 raw objects, drain
continuity, mask expansion, stock symbol/metadata, CLI endpoint/ERC evidence,
exact five new protected source paths and source hashes. It also requires
**all 94 frozen integrated/native and prior charger/BMS evidence files** to
match the baseline. Those files are unchanged. The new scratch project was
normalized to KiCad 10 defaults when opened; it is isolated from prior studies.

Only one new `.kicad_mod`, the new scratch `.kicad_pro/.kicad_pcb/.kicad_sch`
and its portable `fp-lib-table` are protected-source additions. The existing
integrated library registration already resolves this `.pretty` directory;
no existing table or library definition was edited. The old historical
charger/BMS verifier's global added-path guard is preserved unchanged; this
new authorized boundary has its own scoped baseline.

`native_source_sha256.json`, `evidence_sha256.json` and `changed_files.txt`
record exact deliverables. Generated scratch PRL/lock/history and routine
logs are excluded. No real integrated circuit placement or production PCB synchronization was
performed. All later EPS protection and
charger/BMS circuit acceptance work remains separate.

Staged whitespace review preserves the exact generated bytes: the six
`board_*.svg` exports contain trailing spaces and the disposable
`powerpath_check.kicad_sch` contains one whitespace-only line. The remaining
staged files pass `git diff --cached --check`; no protected source or hashed
export was hand-normalized.
