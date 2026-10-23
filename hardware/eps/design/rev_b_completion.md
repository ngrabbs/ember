# EPS Rev B completion ledger

2026-10-23. The operator authorizes completing the integrated EPS schematic and a new four-layer Rev B PCB using the existing outline as the starting geometry. Final stackup, clearances and usable height require mechanical review. Rev A remains a preserved fabrication/bring-up baseline.

Completion requires one connected, reviewable design. Isolated studies establish circuit evidence but do not constitute an integrated EPS. Hardware acceptance follows the design and has separate exit criteria.

| Block | Current authority and evidence | Remaining design work |
|---|---|---|
| 5 V regulation | [Recovery study](rev_b_5v_recovery_closure.md), TPS552872, current 50 V bank | Integrate source and output protection, actual startup/load model, cold capacitor bounds and thermal placement |
| Solar/source and 5 V containment | [Latch and survival checkpoint](rev_b_5v_latch_and_mosfet_survival.md), 83-part two-sheet protection study | Resolve 5 V LTC4364 accuracy coverage and conditional hot linear SOA; integrate with charger/source boundaries |
| Essential 3.3 V | [Integrated buck checkpoint](../verification/rev_b/buck_integration/README.md), LMR51635XDDCR; complete controller/buck union has 43 parts and 40 checked nets | Close UVLO/weak-source behavior and output fault containment; qualify effective capacitance, actual current steps, startup and thermal performance. External permitted-source flags are development fixture boundaries, not implemented RBF/charger hardware. The 2 A steady-load screening does not establish a 2 A fast-step rating. |
| Charger and temperature | [BMS/temperature specification](rev_b_bms_and_temperature_spec.md) and damaged Rev A audit | Rebuild LTC4162 reference circuit with verified 2S straps, PowerPath FETs/shunts and three separate pack sensors; freeze configuration and sensor assembly |
| Battery protection | BQ40Z50 functional reference | Select current family/order code, complete 2S circuit, FETs, precharge, secondary protection, retained bus isolation and commissioning manifest |
| RBF and deployment cutoff | [Source-isolation study](rev_b_source_isolation_study.md) | Select mechanism/harness and passive source switch circuits; demonstrate bidirectional cutoff, open-harness default, inrush and depleted-pack recovery |
| Controller and CAN A/B | [Rev B integrated controller checkpoint](../verification/rev_b/integration/README.md), corrected stock STM32G0B1KET6N, 20 functional nets plus 16 unfinished pin sets; 48 reference/UUID crosswalk entries | Finish ADC/local buses/stack/debug connector, independent transceiver branch containment and remaining integration errors; recovery GPIO allocation is recorded. [CAN branch screening](../verification/controller_rev_b/branch_selection/README.md) does not yet establish B survival during an A supply short. |
| Managed loads and stack | [Architecture authority](rev_b_plan.md), canonical H1/H2 pin map | EPS payload VBAT switch, permission expiry and default-off local loads; preserve IHU control ownership and shared essential rails |
| PCB and mechanics | Nominal 96 x 90 mm, 16 mm top standoff | Full BOM courtyard fit, actual outline/holes, battery/holder and RBF clearances, stackup/rules, placement/routing and DRC |
| Release review | Per-block netlists/ERC/renders | Full hierarchy checks, pin/package/BOM reconciliation, back-power/fault matrix, independent review and assembly outputs |

## Design sequence

The new [Rev B root](../rev_b/eps_rev_b.kicad_pro) now contains unique Controller, CAN and Essential 3V3 sheets rebuilt through Konnect with explicit reference and endpoint crosswalks; it is not the complete EPS. Integrate the reviewed 5 V regulation and protection blocks while finishing charger, battery protection and hardware source isolation, then add stack interfaces and managed battery distribution. Retain all historical studies. Review the complete schematic before PCB synchronization. Layout must use the actual full BOM; the earlier area estimates omit much of the subsequently added recovery protection.

## Hardware acceptance inputs

Physical Rev A thermistor continuity and fitted values remain unknown. Final design ratings also need measured COMMS/IHU/payload idle, peak and inrush currents, solar source/harness limits, accepted cell specification and pack temperatures, and current holder/upper-board geometry. Development assumptions can support analysis and layout exploration; they do not establish these inputs.

The release remains open until source cutoff/back-power, charging and sensor faults, autonomous pack protection, A-to-B bus recovery, controlled startup, transient response, thermal behavior and mechanical clearance meet recorded limits. Flight acceptance additionally depends on the selected dispenser/launch requirements and environmental qualification.
