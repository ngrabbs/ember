# EPS Rev B completion ledger

Updated 2026-10-24. The operator authorizes completing the integrated EPS schematic and a new four-layer Rev B PCB using the existing outline as the starting geometry. Final stackup, clearances and usable height require mechanical review. Rev A remains a preserved fabrication/bring-up baseline.

Completion requires one connected, reviewable design. Isolated studies establish circuit evidence but do not constitute an integrated EPS. Hardware acceptance follows the design and has separate exit criteria.

ERC retains6 documented errors (3 unfinished MCU pins and3 prior intentional pin-type joins), plus2 inherited switched-VTref warnings under unchanged settings. Earlier checkpoint counts below are historical; no complete EPS, PCB or hardware acceptance is implied.

| Block | Current authority and evidence | Remaining design work |
|---|---|---|
| 5 V regulation | — | Actual startup/load model, cold capacitor bounds and thermal placement. Internal 5V0_RECOVERY_REG feeds the attached barrier; shared +5V exists only downstream. |
| Solar/source and 5 V containment | [Latch and survival checkpoint](rev_b_5v_latch_and_mosfet_survival.md); all 83 protection parts integrated as two unique sheets, with MCU fault/reset links verified | Resolve 5 V LTC4364 accuracy coverage and conditional hot linear SOA; complete charger/source boundaries. VIN_CHG now feeds SYS_PWR_PERMITTED through the real charger input FET and shunt; battery/RBF fixtures and charger-to-pack containment remain open. |
| Essential 3.3 V | — | — |
| Charger and temperature | — | — |
| Battery protection | BQ40Z50RSMR-R2 is integrated as a unique 2S pack sheet: common-drain CHG/DSG pair, 2 mΩ shunt/filters, BSS84 precharge, reverse-port clamp, separate TS1/TS2 harness and provisional ISO1540 bus. All 33 BQ pins and 34 complete added/expanded net sets are checked; [commissioning manifest](rev_b_bms_commissioning_manifest.json) records unapproved limits | Resolve [DSG gate stress during short circuit](rev_b_bms_gate_stress_candidate.md), coupled cutoff/hot SOA, [isolated-supply startup, leakage and gauging acceptance](rev_b_bms_isolated_supply_integration.md). The new supply replaces the former shared-positive ISO1540 path in the development schematic. Secondary protection, pack fuse, configuration/thresholds, sensor assembly and autonomous fault/recovery acceptance remain open. Native connectivity is not full pack protection acceptance. |
| RBF and deployment cutoff | — | Select mechanism/harness and source switch circuits; demonstrate bidirectional cutoff, open-harness default, inrush and depleted-pack recovery. ZX10C10A01 is a concrete contact candidate, with minimum-load/resistance documentation and mechanics still unresolved |
| Controller and CAN A/B | — | — |
| Managed loads and stack | — | — |
| PCB and mechanics | — | — |
| Release review | Per-block netlists/ERC/renders | Full hierarchy checks, pin/package/BOM reconciliation, back-power/fault matrix, independent review and assembly outputs |

## Design sequence

The stock source-pin stack and five drain aliases are preserved; library, live and saved-board geometry agree. Internal concave fillets, default reference placement and assembly/thermal qualification remain explicit review items. That package checkpoint added no real charger circuit; the subsequent charger integration now uses it. No real PCB placement was added.

The [Rev B root](../rev_b/eps_rev_b.kicad_pro) now includes unique Charger PowerPath and 2S pack-protection sheets with Controller, CAN, Essential 3V3, Recovery 5V converter, Solar source protection and Recovery rail protection. The BMS-stage graph contains 233 unique physical parts and 133 nets (115 functional), with 648 unique physical ref.pin endpoints. All 187 previous physical UUIDs and 359 earlier symbol objects remain, except five explicitly corrected resistor TCR fields documented in the [metadata correction](rev_b_passive_metadata_correction.md). ERC retains 11 unfinished MCU pin errors and three deliberate datasheet-derived output joins, with no warnings. Resolve BMS gate stress and bus-power measurement, then hardware source isolation, stack interfaces and managed battery distribution. PROTECTED_PACK remains distinct from BATT_PERMITTED across the missing RBF stage. Shared startup, charger/filter behavior and pack-fault containment remain open. Retain historical studies; review the complete schematic before PCB synchronization. The current 243-part area budget still omits unfinished blocks.

It preserves all 233 preceding physical parts and 451 symbol objects. At that historical checkpoint ERC is12 errors (nine unfinished MCU pins and the same three intentional output joins),zero warnings. Use its verifier at its recorded basis; the isolated-supply checkpoint supersedes it for the current root. The UART interface has separate electrical and actual rendered-sheet evidence, with stock power-unit field collisions and S03/S11 tool limitations still explicit. The ADuM5028 construction rules and green review enclosure are now approved, conditional on remaining electrical checks; approval alone does not integrate isolated power or close the BMS measurement error.

Checkpoint verifiers enforce their recorded commit and protected-source scope. Older package/integration checks are historical and intentionally reject later authorized source changes; reproduce them at their recorded commit. The BMS-integration verifier is the historical 233-part checkpoint; use the isolated-BMS-integration verifier for the current development root. The 61 Git-tracked charger-checkpoint artifacts are frozen against b9d0724; ignored editor history, previews, locks and PRL/DS_Store files are not byte-frozen acceptance artifacts.

## Hardware acceptance inputs

Physical Rev A thermistor continuity and fitted values remain unknown. Final design ratings also need measured COMMS/IHU/payload idle, peak and inrush currents, solar source/harness limits, accepted cell specification and pack temperatures, and quantified holder/upper-board clearances. The operator confirms the May export; its local STEP omits the holder/cells, which are visible in the separate Onshape assembly. Development assumptions can support analysis and layout exploration; they do not establish these inputs.

The release remains open until source cutoff/back-power, charging and sensor faults, autonomous pack protection, A-to-B bus recovery, controlled startup, transient response, thermal behavior and mechanical clearance meet recorded limits. Flight acceptance additionally depends on the selected dispenser/launch requirements and environmental qualification.

## Isolated BMS supply, 2026-10-24

The preferred development circuit is permitted essential +3V3 → UCC33020RAQR in **5.0 V mode (SEL=VCC)** → LT3014IS5#TRPBF → `3V3_BMS_ISO`, feeding only ISO1540 side 2 and its two pullups. At this earlier candidate checkpoint, the EPS remained at243 parts/137 nets and the supply was not integrated. The subsequent development integration below supersedes that source state; gauging and electrical qualification remain open.

The user approved the exact [UCC construction rules](rev_b_bms_ucc33020_library_rules.md). It retains the green review marker, corner-shape deviation and unsupported library-display/metadata defaults. All477 byte-frozen baseline files remain unchanged; a separate append-only check preserves every previous review-library symbol. Neither fixture is a functioning supply or production PCB placement.

Its documented reverse-output protection addresses the earlier TLV767 discharge concern for the stated scenario; leakage, PVT and complete system faults are separate. These remain calculation-aid estimates, without arbitrary prebias, repeated UVLO or coupled essential-source proof. TDK CGA3E2X7R1H153K080AA is selected for the15 nF/50 V high-frequency bypasses.

Before electrical/PCB release, complete exact bulk-capacitor effective/ESR envelopes, primary current/inrush and branch-fault containment, startup sequencing and remaining temperature/fault bounds. The later development drawing proceeds under the explicit [integration contract](rev_b_bms_isolated_supply_integration.md), without waiving these acceptance gates. The proposed supply does not yet establish BMS communication during an essential-rail brownout. Keep source cutoff, pack protection and firmware bus recovery independent of successful telemetry.

ADuM5028 construction approval still stands, but its conditional startup/dynamic gate has not passed and no ADuM part was authored. The UCC approval covers library construction and disposable verification; it does not waive electrical integration checks or constitute final custom-part review.

## Independent low-voltage branches, 2026-10-24

The custom symbol's bottom-pin spacing was revised within the agreed functional layout so its exact Value is readable. This library work does not select or integrate CAN/BMS branch circuits. Existing CAN A/B210 kΩ limit calculations remain historical candidates.

Its concrete development bank candidate uses eight/three/one TDK CGA5L1X7R1H106K160AC10 µF parts at primary/isolated5 V/LDO output respectively, conditional on stated tolerance/temperature/aging/bias assumptions. A separate115 kΩ BMS-primary RILIM candidate screens to202.81–266.30 mA and gives more ideal charging margin than the CAN setting. Actual reset/control ownership, source interaction, startup, initial short response, capacitor qualification and thermal/pulse behavior remain open. This study added no real EPS branch; its243-part/137-net source state is historical and is superseded by the integration below.

Twenty-five passive-discharge/feed sensitivities show that clearing the TPS latch cannot be equated with fully power-cycling the UCC/LDO banks. The2 s hold, all-path leakage bounds and reset behavior remain unqualified. At that read-only checkpoint no GPIO was assigned; the subsequent development integration now wires PD0/PD3 with the documented startup restrictions.

All197 protected native files remain unchanged. It also identifies protected+5V as an unselected primary-source alternative to compare against the essential3V3 burst/fault burden; neither source option had integration release at that read-only checkpoint. The later contract selects essential3V3 for development drawing; electrical/PCB release remains open.

## Isolated supply integrated development checkpoint

Its 32 physical additions bring the full root to 275 parts/146 nets/754 endpoints across11 sheets. Only U201.8/R218.1/R219.1/C210.1 migrate from shared+3V3 to3V3_BMS_ISO; system and raw returns remain distinct. This removes that shared-positive schematic connection; residual leakage, calibration and full gauging acceptance remain separate. PD3 enables/resets the primary branch, PD0 reads its diagnostic fault, and both require the documented UCPD startup handling.

The 3V3 burst case reaches a 3.0936 V minimum under its imposed load/source; the initial short reaches 2.605 A before limiting. These are model results, not guaranteed source/fault bounds. Coupled UCC startup/prebias, all-path power-off feeds, healthy CAN survival, PVT, pulse/thermal/EMC and mechanical acceptance remain open. It still omits five old placeholders, unfinished blocks and mechanical exclusions; it is not a placement/fit pass.

Full-hierarchy electrical checks and actual rendered-sheet inspection are separate evidence. The current 10 ERC errors are seven unfinished MCU pins plus the three earlier intentional output joins, with 0 warnings. Existing S03/S11/tool field/pagination limits and custom-part review markers remain; no complete policy or fabrication pass is claimed. Physical RBF/deployment source cutoff, essential3V3 fault containment, charger-to-pack OV, managed loads, remaining interfaces and the authorized PCB stage still require work.

## CAN branch development integration

Each TCAN VCC/VIO and its existing local capacitor bank now use a separate TPS2553DBVR-1 /1 Ω branch. Existing TXD/STB pullups stay on the essential MCU side of new signal resistors; RXD gains a defined pullup. All275 previous physical UUIDs/metadata and524 old symbol objects are retained, with only two documented power-symbol Value changes.

Separate stock SN74LVC1G14DBVR inverters reuse PB9/PD1's standby commands for branch control: HIGH/default disables and requests latch reset; LOW powers normal operation. No new GPIOs are allocated. FAULT diagnostics are bench test points; disabled channels have no CAN wake reception. Both channels are enabled after initialization under the [integration contract](rev_b_can_branch_integration.md). The canonical CSKB record now explicitly includes EPS on the unchanged A/B pins; legacy stack I2C/alert reconciliation remains pending.

Two additional nominal independent-reset runs leave B powered while A's EN is toggled; imposed inverter/GPIO behavior is not a manufacturer inverter dynamic model. The earlier six coupled runs still show the pre-resistor TPS-OUT fault weakness, and moving that resistor upstream is not accepted. Healthy-channel survival, initial short response, shared-source startup, PVT, logic timing and off-state leakage/discharge remain electrical gates. S03/S11/field-anchor and pagination limits remain explicit. No real PCB synchronization occurred.

## RBF retained-power refinement, 2026-10-24

Separate22 µF battery and163.77 µF system banks use a25 mΩ BATFET proxy; this is an intermediate two-node experiment, not the complete charger/source startup model. Added100 kΩ common-source and bias bleeds reduce late residual voltage. N-channel common-source body diodes do not intentionally feed the internal node from external drains; leakage and partial-power limits still require guarantees. The datasheet supports unequal VIN/VOUT during shutdown but does not validate this adapted sense connection or arbitrary pin-current limits.

All202 tracked native files remain unchanged; no RBF circuit or mechanism is selected. Exact contacts/harness, all-condition leakage, full stage-resolved startup, hot MOSFET SOA and repeated actuation remain integration gates. The current305-part graph's capacitor membership/MPN/value/tolerance/pins independently match the earlier inventory. Corrected reversed-device drain mapping, raw hashes, completed logs, interpolated plotting tables and actual plot inspection are retained separately from schematic evidence.

## Stack geometry decisions and peer mismatch,2026-10-24

The operator confirms16 mm clear facing-surface gap and chooses to preserve existing EMBER5.08 mm H1/H2 center spacing. Canonical mechanical documentation is updated; board sources are unchanged. Exact −37 endpoint representation, upper-board thickness, mating-depth tolerances, paired-body/courtyard clearance and mounting-hole alignment remain open.

The actual COMMS board CAN pins do not match the canonical stack allocation. Preserve EPS's canonical H1.51/52/H2.49/50 assignments; record the required peer electrical revision without modifying COMMS under this EPS-only change. Mechanical matching is not electrical bus-recovery evidence.

## Physical SWD integrated development checkpoint

TMUX1511 switches SWDIO, SWCLK, NRST and target VTref; an independent TPS3839 supply qualifier preserves debugger access under MCU reset without firmware. All304 other physical parts retain exact UUIDs/metadata; three internal debug nets intentionally migrate to global scope.

Electrical evidence is separate from actual inspection of13 full pages and16 details. ERC is10 errors/2 warnings; no type/severity weakening or added exclusions. The current static screen includes STM32 internal pulls, giving only21.70 mV of clock-high margin at the minimum specified probe VOH. Actual probe loading, rapid/slow brownout, injection, ESD, timing and service-cable clearance remain open. The earlier package-only calculations and native-source freeze are historical and deliberately superseded by the integrated stage. No real PCB synchronization or layout occurred.

## Essential3V3 controller construction checkpoint

Final20-object pad mapping and mask geometry pass, and the actual part images are inspected. Full manufacturer-page visual acceptance remains open; the part is not integrated into the318-part root. Eight unmodified typical-macro bias tests favor LTC4368 over LTC4365 for gate drive. Complete connected-circuit supply/fault, capacitor/magnetic, timing and SOA checks remain the next selection gate. The main EPS graph, PCB and all five earlier custom symbols are preserved.

Two completed connected LTC4368/CSD18543 experiments expose a further selection failure: the0.2→2A step falls to2.563/2.602V for50/1mΩ imposed source resistance. Improved late-window voltage does not cure the transient deficit. This connected topology remains unselected and no native circuit was integrated. The archived results bind original raw/model hashes and inspected plotting data separately from package/fixture ERC evidence.

The later250ms/1mΩ load step also fails the3V screen (2.79881V minimum), despite 6.448–6.464V gate drive before the step; its400ms run completes. The early80ms pair also included an ongoing gate ramp. Both conditions are retained explicitly, without calling the early window steady state.

## Essential3V3 filter/source boundary refinement

A low-DCR2.2µH guard with640µF imposed effective protected capacitance improves the load-step minimum to3.10377V; a negative-gate clamp also removes modeled controller/FET rating excursions. These are development directions, not native integration release. The308A failed-buck magnetic sensitivity makes upstream branch current limiting and its local stored energy the next required boundary. Evaluate the stock TPS26630RGE without assuming its nominal current limit bounds the first short-circuit pulse. Exact bank/diode/guard, drive/delay, source/magnetic, thermal/SOA and source-page visual gates remain open. The318-part main graph and all218 tracked native files are preserved.

It does not select or integrate a limiter. The protected peak remains below 3.4 V in four completed late Gear cases, but input current reaches 161.6 A, the imposed buck-inductor current reaches 227.9 A, and an ideal direct input short reaches 824.8 A. Hot SOA, physically bounded first-pulse energy and low-input drive remain unresolved; LTC4231's low-input model gate voltage disagrees with its datasheet range. Failed and startup-invalid attempts are retained separately. TPS26630 programming calculations, actual stock symbol/footprint limitations, encrypted-model limitations and preserved local input capacitance are recorded. This is an engineering evidence checkpoint with no new native integration, ERC, sheet-render or PCB acceptance claim.

## Four rail measurements integrated,2026-10-24

PA0/PA1/PA4/PA5 now measure SYS_PWR_PERMITTED, protected+5V, essential+3V3 and BATT_PERMITTED through a dedicated TPS3839-qualified TMUX1511. All10 nF filters precede the switch;47 kΩ MCU-side bleeds load the divider and are included in the verified transfer. SYS/battery inputs are coarse diagnostic paths; BMS measurements remain authoritative for cell protection. Calibration/reference accuracy, switch/ADC dynamics, injection and brownout remain qualification gates. No autonomous protection depends on these samples.

Whole-root electrical checks preserve all318 prior physical parts and verify15 added net sets and173 functional-net classes. ERC is6 errors/2 inherited warnings; PB15/PD2/PB8 remain genuinely unfinished. All14 pages and18 details were inspected by the design owner; root separately inspected the new sheet, channel/supply/controller details and manufacturer ADC connection figure. Nine sideways new resistor references were corrected using stock horizontal orientations, without UUID/metadata/net changes. S11 field-API and inherited root filename-anchor limitations remain explicit. No PCB synchronization occurred.

Controller IN also exceeds its36 V recommended operating ceiling in that model. This does not release the input limiter, magnetic, clamp or hot-SOA design. The remaining power/protection and mechanical work above is unchanged.

## Root filename presentation repair, 2026-10-24

Exact hierarchy and whole-root XML are preserved; all229
other native files are unchanged. Fresh ERC remains6 errors/2 warnings across
345 parts/14 sheets. Actual root-page and caption-detail inspection is separate
from electrical evidence. Historical field-tool limitations above remain true
for those checkpoints; this repair proves sheet-field positioning, without
closing component S11 or other design/qualification gates.

## Telemetry native-field presentation, 2026-10-24

Redundant annotation substitutes are removed.
Actual final page, all-channel and every-passive detail inspection is separate
from the unchanged whole-root XML/ERC evidence. All229 other native files are
preserved. This is the current345-part/14-sheet presentation source state;
earlier checkpoint verifiers remain frozen at their recorded commits. Other
sheets' S11 issues and all electrical/mechanical/PCB/qualification gates remain.

## Payload helper-drive comparison, 2026-10-24

A 180 ohm drain-resistor sensitivity reduces helper current to about73–75mA
but extends proxy-gate discharge to about1–2us; it is not selected. Coupled
CSD18543 attempts expose numerical failures/warnings and supply no survival
acceptance. Actual DRV loading, hot SOA and reverse interruption remain open.
All230 tracked native files match ac4a4b9; the EPS and 49-part managed-feed
candidate counts remain unchanged. No new library approval or PCB work occurs.
