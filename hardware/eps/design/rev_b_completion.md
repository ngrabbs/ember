# EPS Rev B completion ledger

2026-10-23. The operator authorizes completing the integrated EPS schematic and a new four-layer Rev B PCB using the existing outline as the starting geometry. Final stackup, clearances and usable height require mechanical review. Rev A remains a preserved fabrication/bring-up baseline.

Completion requires one connected, reviewable design. Isolated studies establish circuit evidence but do not constitute an integrated EPS. Hardware acceptance follows the design and has separate exit criteria.

| Block | Current authority and evidence | Remaining design work |
|---|---|---|
| 5 V regulation | [Recovery study](rev_b_5v_recovery_closure.md), TPS552872, current 50 V bank | Integrate source and output protection, actual startup/load model, cold capacitor bounds and thermal placement |
| Solar/source and 5 V containment | [Latch and survival checkpoint](rev_b_5v_latch_and_mosfet_survival.md), 83-part two-sheet protection study | Resolve 5 V LTC4364 accuracy coverage and conditional hot linear SOA; integrate with charger/source boundaries |
| Essential 3.3 V | [Buck draft](../verification/essential_buck_stage_draft.md), LMR51635 | Select exact passives, UVLO and fault containment; verify startup, current budget and load response |
| Charger and temperature | [BMS/temperature specification](rev_b_bms_and_temperature_spec.md) and damaged Rev A audit | Rebuild LTC4162 reference circuit with verified 2S straps, PowerPath FETs/shunts and three separate pack sensors; freeze configuration and sensor assembly |
| Battery protection | BQ40Z50 functional reference | Select current family/order code, complete 2S circuit, FETs, precharge, secondary protection, retained bus isolation and commissioning manifest |
| RBF and deployment cutoff | [Source-isolation study](rev_b_source_isolation_study.md) | Select mechanism/harness and passive source switch circuits; demonstrate bidirectional cutoff, open-harness default, inrush and depleted-pack recovery |
| Controller and CAN A/B | [Controller evidence](../verification/controller_can_interface_draft.md), corrected STM32G0B1 GP map | Bring native source into tracked project, update GPIO budget for recovery protection, finish interfaces/defaults and independent transceiver branch containment |
| Managed loads and stack | [Architecture authority](rev_b_plan.md), canonical H1/H2 pin map | EPS payload VBAT switch, permission expiry and default-off local loads; preserve IHU control ownership and shared essential rails |
| PCB and mechanics | Nominal 96 x 90 mm, 16 mm top standoff | Full BOM courtyard fit, actual outline/holes, battery/holder and RBF clearances, stackup/rules, placement/routing and DRC |
| Release review | Per-block netlists/ERC/renders | Full hierarchy checks, pin/package/BOM reconciliation, back-power/fault matrix, independent review and assembly outputs |

## Design sequence

Finish the controller and charger circuit definitions while retaining the existing recovery studies. Next close battery protection and hardware source isolation, then integrate regulation, stack interfaces and managed battery distribution. Review the complete schematic before PCB synchronization. Layout must use the actual full BOM; the earlier area estimates omit much of the subsequently added recovery protection.

## Hardware acceptance inputs

Physical Rev A thermistor continuity and fitted values remain unknown. Final design ratings also need measured COMMS/IHU/payload idle, peak and inrush currents, solar source/harness limits, accepted cell specification and pack temperatures, and current holder/upper-board geometry. Development assumptions can support analysis and layout exploration; they do not establish these inputs.

The release remains open until source cutoff/back-power, charging and sensor faults, autonomous pack protection, A-to-B bus recovery, controlled startup, transient response, thermal behavior and mechanical clearance meet recorded limits. Flight acceptance additionally depends on the selected dispenser/launch requirements and environmental qualification.
