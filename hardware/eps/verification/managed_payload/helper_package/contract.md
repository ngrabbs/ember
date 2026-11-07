# Stock helper/reference package fixture boundary

2026-10-24. Root owns this bounded disposable verification. Read the full
repository schematic policy, net naming, AGENTS.md and managed-feed contract.
Author only `fixture/payload_stock_check.{kicad_pro,kicad_sch,kicad_pcb}` through
Konnect; preserve every219 native path in `frozen_baseline.json`. No real EPS
mutation, library construction, fictional circuit connectivity or PCB sync.

ANSI B, one page, two intentionally unconnected symbols: Q1
`Transistor_FET:T2N7002AK`, exact proposed orderable `T2N7002AK,LM`, at
(101.6,101.6); U1 `Reference_Voltage:LM4040DBZ-2.5`, actual
`LM4040CEM3-2.5/NOPB`, at(228.6,101.6). Both use unchanged stock
`Package_TO_SOT_SMD:SOT-23`. Board placements Q1 at(50,50),U1 at(65,50),front,
rotation0. Preserve generic package Value if closed-board property updates
are unsupported and explicitly record it; reference, schematic MPN and this
table identify the package instances. Do not imply BOM/placement-file readiness.

Use exact MFG P/N, Manufacturer, PackageSize, Datasheet, Description and Review
properties. Value may display the exact MPN once instead of duplicating it.
Visible annotations identify a package-mapping fixture with no functioning
circuit. No no-connect markers or flags to hide genuine unwired fixture pins.

| Part | Physical lead/function | Symbol pin/type | Stock pad XY mm |
| --- | --- | --- | --- |
| Q1 | 1 Gate | 1 G/input | −0.9375,−0.95 |
| Q1 | 2 Source | 2 S/passive | −0.9375,+0.95 |
| Q1 | 3 Drain | 3 D/passive | +0.9375,0 |
| U1 | 1 Cathode | 1 K/passive | −0.9375,−0.95 |
| U1 | 2 Anode | 2 A/passive | −0.9375,+0.95 |
| U1 | 3 NC, float or anode per manufacturer | 3 NC/no_connect, floating here | +0.9375,0 |

All pad coordinates are front/component view,Y down. Each package has three
leads, three separate symbol pins and three numbered copper/paste/mask pads,
without EP, drills or duplicate numbers. Pads1.475×0.60mm,roundrect ratio0.25.
Toshiba's datasheet top view has1/2 along bottom and3 above; rotate that drawing
90° clockwise to match the stock footprint orientation. LM4040 DBZ top view
has1/2 on one side and3 opposite; reconcile the actual rendered key/numbering.
The SOT23 footprint is an IPC library land, not a claim of exact manufacturer
recommended lands. For Q1 reserve a full4.0×3.5mm placement rectangle because
the notched stock courtyard leaves only0.20mm to maximum body width. U1's
full maximum/mold-flash envelope and assembly land acceptance remain separate.

Primary pin sources actually rendered/inspected: Toshiba T2N7002AK datasheet
2026-04-14 pp1/2/5/6, and TI LM4040 SNOS633N DBZ p3 (plus pin functions p4).
Use exact table maps; symbol/footprint names alone are not evidence. No source
file is copied/rewritten by ordinary text tools. Query library, saved symbol
fields/pins and actual placed board pads. Compare counts, full number
multiplicities, XY,size,radius,layers,rotation and drills. Render/inspect actual
schematic page/detail and copper/paste/fab/courtyard board details. A numbered
overlay must be labelled as query-derived, not native artwork. Run CLI ERC and
netlist without suppressions; explain the unconnected fixture errors. Freeze
evidence hashes and report native preservation independently of pin mapping.

Electrical selection remains conditional: Toshiba specifies17pF maximum Ciss
at VDS10V,VGS0,25°C; that test point does not bound the whole gate trajectory,
temperature or routing. Use10pF imposed stray and2× Ciss sensitivity (44pF
total) to screen remaining drive margin, not as a qualified maximum. The3V
TPS DRV minimum still requires valid loading and full-temperature sink/timing
acceptance. This fixture is no MOSFET survival or clamp-circuit acceptance.
