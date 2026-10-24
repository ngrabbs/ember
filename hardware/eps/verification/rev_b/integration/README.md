# Integrated EPS Rev B — controller checkpoint

2026-10-23. [Native project](../../../rev_b/eps_rev_b.kicad_pro), new B root plus unique Controller and CAN interfaces children. This begins the integrated schematic; it does not imply the remaining EPS power/interlock/BMS/charger circuit exists. No PCB synchronization, custom part construction or historical-study mutation occurred.

## Method and crosswalk

Konnect duplicate_sheet was tested only in `/tmp/ember_integration_probe_20261023`. Its immediate child copy has new UUIDs and can be independently renamed; its nested child still refers to the original deep.kicad_sch. The exported disposable hierarchy reports annotation errors. Therefore it is not a verified recursive project clone. add_hierarchical_sheet links existing files and patches their instances, which would alter historical evidence. [Probe findings](disposable_probe.json).

The new project was created through Konnect. Both unique child sheets were attached before placing parts, so the new eps_rev_b instance paths were established first. Components, complete metadata, exact footprints, transformed positions, 121 local wire segments and 25 labels were then rebuilt through Konnect from readback/exported blueprints. No protected source was copied or text patched. Existing approved library parts were reused through portable `${KIPRJMOD}/../libraries/` tables.

[Reference crosswalk](reference_crosswalk.csv) records all 27 physical references and 21 power symbols, old/new sheets and UUIDs. U1→U100, U2→U101, U3→U102; capacitors/resistors/connectors/oscillator occupy the same 100 block. No PWR_FLAG existed in the source controller, and none was added. Future ranges reserve 200 BMS, 300 charger, 400 essential 3V3, 500 recovery 5V and 600 protection. [Endpoint crosswalk](endpoint_crosswalk.csv) records exact full-path net translation, not basename-only comparison. Later blocks require their own complete reference and net crosswalk before attachment; independent outputs/ground domains must not merge implicitly.

## Electrical evidence

Run `python3 hardware/eps/verification/rev_b/integration/verify_integration.py` from the repository. [Result](verified.json): all **36 mapped net endpoint sets match** the accepted controller study, including 20 functional nets and 16 unfinished MCU singleton nets. All 27 physical parts preserve exact library identity, value, footprint, datasheet and every exported metadata field. All 18 historical project/schematic/table files in the prebuild checkpoint retain their SHA256. [Blueprint](rebuild_blueprint.json), [readback](readback.json), [fields](fields_readback.json), [netlist](eps_rev_b.xml), [BOM](bom.csv).

Fresh full-root KiCad10 CLI ERC: **18 errors, 3 warnings**. Sixteen errors are unfinished MCU pins; two identify the absent essential source/return. Three isolated labels are REC5_RESET, REC5_FAULT and SRC_FAULT, which remain local until the actual protection sheets participate. No flags/NCs hide these interfaces. GPIO, BMS isolation, charger, ADCs, UART, interlock/payload request, supply fault containment, physical connectors and bus protection remain unfinished. J100/J101/J102 and R106/R107 are the same five unselected placeholders; custom MFG fields do not imply physical selection. R106/R107 Population=DNP is metadata only, not native DNP state.

Geometry independently confirms 57 Controller and 64 CAN H/V wire segments on the 1.27 mm grid, zero four-way intersections and no pin/power anchors on branches. Six persisted classes assign all 20 functional nets with exact full names. Their default numerical geometry is not a qualified PCB rule. Canonical CAN_H/L, CAN_B_H/L, legacy +3V3/GND and all existing logical signal names are preserved. CAN A/B logic remains global between the two participating children. New CAN branch circuitry is not installed.

## Actual visual inspection

[Root PNG](eps_rev_b.png), [Controller PNG](controller.png), [CAN PNG](can_interfaces.png) and [three-page PDF](eps_rev_b.pdf) were opened and inspected. [Controller detail](controller_detail_280.png), [CAN A detail](can_interfaces_detail_80.png), [CAN B detail](can_interfaces_detail_1120.png) were also inspected. Native circuits remain readable, support parts are locally wired, supply/ground orientations are correct, external labels clear the MCU and each other, and no text/wire/body collisions were observed. The notes explicitly identify reserved PD3 and prohibit direct BTP logic connection. The root has room for subsequent functional sheets.

Policy gates remain open: S03 four-way ERC severity defaults ignored and no exposed API persists the required Error; S08 reused TCAN/ECS review marking requires resolution of original construction approval; S11 saved values do not implement required field visibility/font/position; logical connectors and termination parts are unselected. Root page metadata also remains wrong: root render prints Id3/3; child standalone renders print1/1. The hierarchy API knows children2/3, but no root instance-page setter is exposed. All three B pages export in correct order in the full PDF. This is recorded as an S04 API limitation, not silently accepted pagination.

The auto-created blank eps_rev_b.kicad_pcb and runtime .kicad_prl are excluded by the project .gitignore. The PCB stage has not begun.
