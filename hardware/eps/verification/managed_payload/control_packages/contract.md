# Managed-feed stock control/protection package fixture

Root owns this bounded Konnect-only mutation. Preserve all227 baseline native
files. Author only the three new fixture/control_check project files. No real
EPS circuit, PCB, project setting, registration or library mutation. Read root
AGENTS.md, complete schematic policy/net naming, managed-feed contract and the
Konnect/library/schematic skills. ANSI B; deliberately unwired pin-map fixture.

| Ref | Exact selected MPN | Stock symbol | Stock footprint |
| --- | --- | --- | --- |
| U1 | TPS26630RGER | Power_Management:TPS26630RGE | Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm |
| U2 | SN74HCS08PWR | 74xx:74LS08, all5units | Package_SO:TSSOP-14_4.4x5mm_P0.65mm |
| U3 | 74HC74PW,118 | 74xx:74HC74, all3units | sameTSSOP14 |
| U4 | SN74LVC2G08DCUR | 74xGxx:74LVC2G08, all3units | Package_SO:VSSOP-8_2.3x2mm_P0.5mm |
| U5 | SN74LVC1G32DBVR | 74xGxx:74LVC1G32 | Package_TO_SOT_SMD:SOT-23-5_HandSoldering |
| D1 | BAS116H,115 | Device:D_Small | Diode_SMD:D_SOD-123F |

The prior exact TPS3839K33DBZR SWD package checkpoint and SN74LVC1G14DBVR CAN
package checkpoint remain reusable; do not duplicate them or change their parts.
TPS3700 remains outside this fixture and construction approval is still pending.

All68 physical leads, including EP25 and six eFuse NC contacts, must match
manufacturer functions and stock symbol types. Preserve PGOOD16's generic
output-type limitation (actual OD) explicitly. U2 requires actual HCS MPN,
Description and datasheet plus the visible warning 'Schmitt inputs — HCS part
required'; do not imply an LS08 may be fitted. Retain exact MFG P/N,
Manufacturer, PackageSize and Review fields; display exact MPN once through
Value where it already matches. No new custom symbol or physical part.

Use the eFuse footprint WITHOUT embedded vias. Its stock default ThermalVias
version has9×0.20mm drills below the configured0.30mm minimum. The selected
no-via version has29rawobjects:25numbered electrical pads and4blank paste-only
windows. No thermal-via/PCB thermal design is thereby complete. Peripheral
pads and paste coverage differ from TI's example; quantify them and retain
assembly/thermal acceptance open. Never deduplicate raw pad counts first.

Component-front/Ydown coordinates: TI pin diagrams and land patterns are top
views. RGE outline's underside diagram must be mirrored vertically to reconcile
with the top view; do not rotate it blindly. HC74 p3PW map is already top;
its p14mechanical view rotates90°clockwise into the stock orientation. BAS116H
p1bar is K1; its p5mechanical view rotates90°counterclockwise into stock1left.
TI PW/DCU/DBV top views require no rotation into the selected stock footprints.

Full layout reservations, not native courtyard edits: U1=5.26×5.26mm,
U2/U3=7.70×5.90mm, U4=4.56×2.90mm, U5=4.76×4.05mm, D1=4.40×2.30mm.
These account for selected pads and worst body/flash; retain stock notched
courtyard shortfalls explicitly. Heights1.0/1.2/1.2/0.9/1.45/1.2mm respectively.
Recheck actual source limits and mask/clearance geometry before real placement.

Plan one page: U1(76.2,101.6); D1(76.2,190.5). U2units1/2/3 at
(190.5,69.85)/(266.7,69.85)/(342.9,69.85); units4/5 at
(190.5,120.65)/(266.7,120.65). U3units1/2/3 at
(342.9,120.65)/(190.5,177.8)/(266.7,177.8). U4units1/2/3 at
(342.9,177.8)/(190.5,233.68)/(266.7,233.68). U5 was moved after render inspection to(342.9,210.82), clear of the title block.
Board row placements U1(50,50),U2(65,50),U3(80,50),U4(95,50),U5(110,50),
D1(125,50), allfront/rotation0. Exact sourcing comes from schematic metadata;
closed-board generic package Values must be recorded if editing unsupported.

Query library and saved-instance pins/fields, all raw board pads, coordinates,
sizes/radii/layers/rotations/drills. Full lead/function table in physical_map.csv.
CLI XML/ERC without fake NC/flags or severity changes; explain unwired-pin
errors, stock hidden NC and intentional IN/OUT/GND stacked pins. Inspect actual
page/detail renders and board copper/paste/mask/fab/courtyard/numbered views.
Overlays are query-derived, not native artwork. Preserve every prior native hash
and record source/render hashes; electrical and rendered evidence separately.
No circuit timing, reverse blocking, cutoff, SOA or flight acceptance follows.

Presentation repair: the separate existing local Konnect build exposes guarded
field-position tools through a real stdio MCP connection. Its runtime schema,
binary hash, dry-run/apply responses and exact before/after item snapshots are
recorded here. Only field presentation changed after the OR placement fix;
full metadata, pins, UUIDs, instances and CLI connectivity are compared. No
client configuration change, source patch, direct native write or new symbol
variant was needed. Old cached-tool limitations remain historical records.
