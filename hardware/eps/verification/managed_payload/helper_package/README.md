# Stock helper and reference package verification

2026-10-24. Root-owned disposable fixture, authored only through Konnect.
The real EPS remains at its 345-part, 14-sheet checkpoint. No real circuit or
library was changed. `verify_fixture.py` checks all 219 frozen native paths,
the two stock symbol maps, saved sourcing fields, six placed pads and CLI
exports. Native read-only inspection is limited to pad geometry and field
visibility omitted by the query/export APIs.

Electrical/structural evidence: Q1 T2N7002AK,LM is G1/S2/D3; U1
LM4040CEM3-2.5/NOPB is K1/A2/NC3. Both unchanged stock SOT-23 footprints have
three separate 1.475 × 0.60 mm roundrect pads, ratio 0.25, no drills, with
copper/paste/mask membership. `physical_map.csv` records front-view coordinates.
The saved NC3 exists despite being hidden in U1's stock graphic; it is floating
as permitted by TI. The fixture is deliberately unwired: CLI ERC reports five
unconnected pins and one undriven gate, all errors, with no suppressions added.
Generic fixture project defaults retain ignored checks listed in `erc.json`;
this is not a full schematic-policy or circuit/ERC pass.

Actual visual inspection was performed separately: `symbols.png` at page
scale, both `*_detail.png` images, combined board details, all five layers in
`layers_review.png`, and `numbered_copper.png`. Reference, exact selected MPN
and pin numbers are readable; comments identify the simplified MOSFET glyph
and hidden NC. The number overlay is derived from saved pad queries, not native
artwork. Fabrication layers retain generic **SOT-23** board Values because
closed-board property editing is unsupported; these are not assembly exports.

Primary manufacturer images inspected: Toshiba T2N7002AK 2026-04-14 pp1/2/5/6
(pin diagram, electrical table, capacitance curve and package), TI LM4040
SNOS633N DBZ top view p3 and pin table p4. Toshiba's top drawing rotates 90°
clockwise into the stock pad orientation. Sources and hashes are in the parent
`sources.json`; the unchanged stock library query is retained here.

This accepts pin/pad mapping only. For Q1 reserve a full 4.0 × 3.5 mm rectangle:
the stock notched courtyard gives only 0.20 mm to its maximum body width.
U1's maximum mold-flash envelope/courtyard and assembly acceptance of both
generic land patterns remain open. The fixture does not prove helper drive,
reverse interruption, reference startup, solder-process acceptance or MOSFET
survival. Re-run the verifier from the repository root with Python 3.
