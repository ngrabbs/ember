# Rev B controller native development study

2026-10-23. **Controller support rebuild is reviewable; integrated EPS schematic acceptance remains open.** Sole CAD mutation owner used Konnect 0.11.1 / KiCad 10.0.0. No existing EPS, converter, protection, library or PCB source was changed. No commit was created by this build agent.

Project: [controller_rev_b.kicad_pro](../../../studies/controller_rev_b/controller_rev_b.kicad_pro). Both root and linked CAN child use ANSI B landscape. Candidate libraries resolve through portable `${KIPRJMOD}/../../libraries/…` tables. The automatically created blank PCB is excluded from the schematic deliverable; it has no layout work.

## Corrected MCU identity

The earlier custom symbol named `STM32G0B1KET6_GP_DRAFT_v2` actually carries the **N** variant physical map. Current [ST DS13560 Rev 6, Figure 3, p.36](https://www.st.com/resource/en/datasheet/stm32g0b1ke.pdf) shows the difference:

| Physical pin | GP STM32G0B1KET6 | Selected N STM32G0B1KET6N |
|---|---|---|
| 17 | PB2 | PB15 |
| 20 | PC6 | VDDIO2 |
| 26 | PA15 | PD0 |
| 27 | PB3 | PD1 |
| 28 | PB4 | PD2 |
| 29 | PB5 | PD3 |

The user selected STM32G0B1KET6N. U1 now uses installed stock `MCU_ST_STM32G0:STM32G0B1KETxN`, exact instance MFG P/N STM32G0B1KET6N, and the existing manufacturer-pattern ST LQFP32 footprint. All 32 physical pins and all 32 unique SMD pads were checked. The stock symbol labels both supply pins VDD; the schematic note and PinMap field explicitly identify pin20 as VDDIO2. No new custom symbol was authored. See [stock readback](stock_n_symbol.json), [pad readback](mcu_n_footprint.json), and [disposable render](mcu_n_detail.png).

PA11/PA12 CAN A pads are in the N variant's VDDIO2 domain. VDDIO2 stays on the same essential +3V3 as VDD: ST p.17 prohibits VDDIO2 without valid VDD. C4 increased from the old optional 1uF to 4.7uF, following the 100nF + 4.7uF VDDIO2 decoupling in Figure15. Effective capacitance and startup remain qualification items. USB and LSE are not used; PA11/PA12 remap, UCPD reset state, BOOT0 options, errata and CubeMX confirmation remain open.

## Implemented boundary

27 physical parts: MCU, two TCAN3413DRs, ECS-3225MV-160-BN-TR, 13 capacitors, five selected startup pullups, two unselected DNP termination options, and three logical connector placeholders. All original reference designators and the original 17 functional endpoint sets are retained. Local power/ground bars, bypassing, reset, oscillator enable/HSE, CAN pullups/termination and SWD topology are drawn with actual wires. Six MCU-to-CAN logic signals use global labels because they cross the actual sheets. Other signals use local labels; +3V3/GND retain legacy interface names.

Selected capacitor metadata: 100nF GRM188R72A104KA35D (0603,100V,X7R,10%); 1uF GRM21BR71C105KA01L (0805,16V,X7R,10%); 4.7uF GRM21BR71A475KE51L (0805,10V,X7R,10%). Startup pullups use TNPW060310K0BEEA (10k,0.1%,25ppm/K,0.11W general P70). Procurement and effective-capacitance acceptance remain open. Primary references: [Murata100n](https://www.murata.com/products/productdetail?partno=GRM188R72A104KA35%23), [Murata1u](https://www.murata.com/en-us/products/productdetail?partno=GRM21BR71C105KA01%23), [Murata4.7u](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM21BR71A475KE51-01A.pdf), [Vishay TNPW](https://www.vishay.com/docs/28758/tnpw_e3.pdf).

New approved board-local allocations are PA6=REC5_RESET, PA7=REC5_FAULT, PC15=SRC_FAULT. These are local named stubs until the protection sheets actually join the project. The existing protection-side 47k pullups and Q107 reset interface are not duplicated. Reset remains a 2ms pulse subject to >=10s cooldown and rail qualification; it does not bypass protection or authorize a power cycle. PD3 remains physically unconnected and reserved: BMS BTP must not connect directly to 3.3V logic. BMS status is to be polled through the separately designed isolated SMBus. No EPS drive was added to IHU-owned COMMS_EN/PAYLOAD_EN or canonical EPS_ALERT_N.

J1 is logical SWD access only: 1VTref sense,2SWDIO,3SWCLK,4NRST,5GND. J2/J3 are logical CAN subsets, not full stack connectors. Intended mapping remains CAN_H/L H1.51/52 and CAN_B_H/L H2.49/50. Canonical EPS-node authority still needs coordinated integration. J1–J3 have no selected MPN/footprint. R7/R8 have a Population=DNP field and explicit notes; native DNP flag setting is unavailable. Their sustained fault power/package/MPN remain unselected. External CAN TVS remains unselected under the previous candidate's open coordination review.

Both transceivers still share essential +3V3, GND, MCU and clock. A branch supply short can remove both channels. Exact per-transceiver current limiting/isolation is not selected or drawn. [TI TCAN3413 Rev A](https://www.ti.com/lit/ds/symlink/tcan3413.pdf) p.20 distinguishes VCC/VIO UVLO states and describes low leakage with both supplies off. The table does not establish arbitrary failed-pin isolation. A future isolated branch must review VCC, VIO, TXD/STB pullups, MCU input injection and sequencing together. CAN B is bus-path recovery, not independent controller redundancy.

## Electrical evidence

[verify_controller.py](verify_controller.py) checks fresh full-hierarchy CLI XML plus Konnect readbacks. [verified.json](verified.json), [endpoint CSV](endpoint_sets.csv), [field readback](fields_readback.json), [BOM](bom.csv), [CLI XML](controller.xml).

- Original17 endpoint sets match the scratch export exactly after resolving new sheet prefixes.
- Three new GPIO sets match U1.13/U1.14/U1.3. No extra named-net shorts.
- All27 references,22 selected parts' metadata and five deliberately unselected placeholders read back.
- All32 MCU pins/32 pads match the N variant. All20 named nets have persisted exact class assignments, separately separating CAN bus and MCU logic.
- 121 wire segments are orthogonal/on1.27mm grid. Independent geometry checks found zero four-way intersections and zero component/power pin anchors at branch junctions.
- Fresh [CLI ERC](erc.json): **18 errors,3 warnings**. Errors are16 unfinished MCU pins and2 undriven supply/return nets because the upstream essential source is absent. Warnings are the3 isolated protection-interface stubs. No fake NC/power flags or exclusions suppress these findings.
- Remaining MCU pins:7,8,9,10,11,12,17,18,19,21,26,28,29,30,31,32. They cover ADC conditioning,Uart,charger/pack interfaces,interlock/payload request and reserves.

Class numerical values are Konnect defaults, not accepted fabrication rules, current widths or differential impedance. CAN H/L legacy names are preserved; native _P/_N recognition is not claimed. Board matching is absent because no PCB synchronization occurred.

## Actual rendered-sheet inspection

[Two-sheet PDF](controller_rev_b.pdf), [root page](controller_rev_b.png), [CAN page](can_interfaces.png), [MCU/SWD detail](controller_detail.png), [clock/reset detail](clock_reset_detail.png), [CAN A detail](can_a_detail.png), [CAN B detail](can_b_detail.png). Both complete pages and all four details were opened and inspected. Actual label-to-MCU overlaps, oscillator-value/supply overlap and SWD-value/ground-wire overlap were corrected through Konnect, then re-rendered and inspected. Signals, exposed stubs, local support topology and bus separation are readable. Ratings-field rendering is explicitly not accepted below.

The root and child are connected in the native hierarchy. However **pagination is blocked**: Konnect reports childpage2, but fresh CLI PDF prints Id2/2 on both root and child. Calling renumber_sheet_pages retained this behavior. No exposed root page-number/title-block setter can repair it. S04 page dimensions/hierarchy are verified; coherent printed numbering remains open.

## Policy and integration blocks

- **S03:** fresh ERC explicitly lists four_way_junction among ignored_checks. Exposed APIs cannot persist native ERC rule severity. run_erc.severity is only an output filter; save_project_config is Konnect JSON. Geometric checking does not substitute for the required Error setting.
- **S11:** required custom field values persist, but edit_schematic_component lacks custom-field visibility,font,size,position/justification setters. Rendered orientation-aware Arial rating blocks are not verified/passed. Connector and termination placeholders independently block complete metadata acceptance. [Capability evidence](api_capability_audit.json).
- Printed root/child numbering remains a Konnect hierarchy limitation described above.
- Full EPS integration, exact physical debug/stack connectors, termination/TVS, CAN supply branch isolation, ADC networks, UART, charger I2C, isolated retained-domain SMBus, essential3.3V stage, protection linking and firmware startup/bench qualification remain open.

## Essential-buck draft inventory

Read-only inspection of the latest scratch LMR51635XDDCR stage found10 physical parts/six named nets. Only U1 has a footprint; nine passives remain without footprint/complete selected metadata. C5/C6 are requirements `>=47u eff`, not orderable capacitors. L1 is5.6u with a proposed XAL6060 reference. The draft starts autonomously with EN tied to SYS_PWR_PERMITTED and preserves +3V3, but uses A4, local-label supply input and several zero-wire power/ground anchors. It is not policy-ready. [Actual scratch render](essential_buck_scratch.png), [inventory](essential_buck_scratch_inventory.json). Next promotion requires physical input/output capacitor/inductor selection, effective-C/startup/UVLO/thermal checks, then a separately verified B-sheet rebuild linked into the integrated root. It was not copied into this study.

All native files were created/edited via Konnect. The original scratch projects and previously tracked native designs/libraries are unchanged.


S08 status: existing custom TCAN/ECS symbols were reused without green body/markers. Original construction approval coverage remains unresolved; no S08 full-policy pass is claimed. Vishay 28758 Rev10-Apr-2026 p2 rates TNPW0603 general operation0.11W P70/125C film;0.21W requires advanced175C film operation and is not the selected rating.
