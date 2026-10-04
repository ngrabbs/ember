# EPS Rev B provisional BOM and schematic checklist

Draft dated 2026-10-03. This is the implementation handoff for the planned single-board EPS revision. It separates proposed components from reference parts and unresolved circuit selections. It is not a complete assembly BOM or an order list. Quantities below cover functional blocks; supporting passives, protection, test points and connector mating parts must be added from the completed schematic.

[Architecture and decisions](rev_b_plan.md) · [Controller and CAN circuits](rev_b_pin_and_fit_study.md) · [Source isolation](rev_b_source_isolation_study.md) · [BMS and temperature](rev_b_bms_and_temperature_spec.md)

## Provisional component list

| Block | Quantity | Component or requirement | Selection status and remaining work |
|---|---|---|---|
| EPS MCU | 1 | STM32G0B1KET6, general-purpose LQFP32 | Proposed full MPN matching the chosen pinout. Confirm temperature grade, errata and complete pin configuration. Do not substitute the N pinout. [ST product authority](https://www.st.com/en/microcontrollers-microprocessors/stm32g0b1ke.html). |
| CAN transceivers | 2 | TCAN3413DR, SOIC-8 | Proposed A/B parts; verify physical package maps and essential-supply fault budget. |
| Clock | 1 | ECS-3225MV-160-BN-TR | Proposed 16 MHz CMOS oscillator; verify HSE electrical limits, temperature range and timing budget. |
| Pack manager | 1 | BQ40Z50 family, R2 circuit/configuration reference | Final orderable MPN and delivered/programmed firmware revision remain open. Do not infer the order code from the manual title. |
| BMS charge/discharge FETs | At least 2 | High-side N-channel parts compatible with selected BMS | Select gate-drive compatibility, hot resistance, current and transient capability from complete reference circuit. Parallel devices may change quantity. |
| BMS precharge | 1 circuit allowance | Reference-compatible FET/resistor network | Select only after recovery behavior and energy limits are defined. |
| BMS current shunt | 1 | Compare 5 mΩ and 10 mΩ Kelvin-sensed options | Rating, package and value await current/fault calculations. |
| BMS cell input filters | 1 set | Exact selected 2S reference implementation | Select resistor/capacitor values with balancing, connection transients and accuracy. |
| Secondary protection | 1 circuit allowance | Independent protection and fuse response as required | Acceptance requirement and exact implementation open; not assumed provided by the primary IC. |
| Pack-side harness fuse | 1 | Close to cells, upstream of main cable | Select current/time characteristics and coordinate wire, connector and PCB protection. |
| RBF battery isolation | 2 reference devices | Si7149DP P-channel pair | Reference only; finalize gate network, minimum drive, startup SOA, leakage and thermal margin. |
| RBF solar isolation | 2 reference devices | DMP6023LE P-channel pair | Reference only; production specification, cold voltage, gate clamp and transients unresolved. |
| Hardware interlocks | 1 RBF mechanism plus deployment mechanisms | Side-access pin, structurally supported contacts, independent gate permission loops | Select switch/pole count, bracket, guide, harness and dispenser interface. Physical mechanisms are not PCB footprint assumptions. |
| Main pack connector | 1 board-side plus mating pack assembly | Retain XT30 provisionally | Identify exact connector orientation/MPNs; check holder, soldering, retention and mating clearance. |
| Sense/NTC harness | 1 connector pair | At least 9 contacts for current three-sensor proposal | Keyed and retained; choose housing, contacts, wire and pinout. Optional sensors add contacts. |
| Charger NTC | 1 | 10 kΩ at 25 °C; curve compatible with charger model | Pack-mounted construction and MPN open; a chip reference sensor is not automatically a pack probe. |
| Charger bias resistor | 1 | 10 kΩ, 1% or better, low drift | Proposed value; finalize package/MPN and tolerance analysis with sensor. |
| BMS cell NTCs | 2 | 10 kΩ at 25 °C; model matched to BMS conversion | Separate from charger sensor; freeze curve, leads, mounting and calibration. |
| Retained charger | 1 | LTC4162EUFD-LADMTRPBF, as named in Rev A release BOM | Reuse candidate; verify exact ADI order-code notation, chemistry/2S configuration and assembled circuit. |
| Retained PowerPath FETs | 2 reference devices | FDMC8327L, Rev A release BOM | Reassess voltage/current/layout and exact physical maps. Additional RBF pairs do not replace these functions. |
| Buck stages | 2 | Higher-voltage replacements for TPS62933FDRLR, 3.3 V and 5 V | [Source study](rev_b_source_voltage_and_fault_budget.md) rejects unconditional 30 V reuse with 4S solar. Compare ≥42 V operating candidates, dropout, startup, light-load loss, current and thermal limits. Final MPNs open. |
| Solar OV isolation | 1 circuit allowance | Autonomous fault cutoff inside RBF boundary | Define trip tolerance/delay, unconditioned-input ratings, bias, SOA, battery handover and restart. Exact circuit/MPNs open. |
| Charger/input sense resistors | 2 reference devices | WSLP0805R0100FEA, Rev A release BOM | Verify actual fitted values and Kelvin routing. Do not assign Rev A references to new parts automatically. |
| Payload battery load switch | 1 circuit allowance | Downstream of battery source isolation, ahead of paired stack VBAT pins | Select ratings/inrush/fault response after payload current envelope; default off. |
| CAN support | 2 sets | Supply bypassing, STB/TXD pulls, bus protection, optional termination/filtering | Final MPNs and population from controller specification and network topology. Termination is conditional, not two mandatory fitted resistors. |
| MCU support | 1 set | Decoupling, reset/BOOT0, SWD, debug UART, rail sensing and isolated BMS interface | Complete from exact MCU/BMS requirements. No generic decoupling rule substitutes for all device-specific supply requirements. |
| Existing conversion passives | 3 stage sets | Charger and two buck inductors, capacitors and networks | Recalculate and reconcile actual CAD, BOM and assembly; do not copy the fabricated values as accepted designs. |

Payload auxiliary switching and COMMS TX switching belong on the consuming boards under the present proposal. They are cross-board work items, not extra EPS-resident BOM channels. Current estimates of three logical groups do not prove three independent physical EPS outputs exist.

## Power-stage reuse gate

The [Rev A release BOM](../releases/CubeSat_EPS_rev_A_BOM.csv) names LTC4162 and TPS62933F, rather than the older TPSM5D1806 overview. It establishes recorded fabrication parts, not measured performance or current assembly.

[TI's TPS6293x datasheet](https://www.ti.com/lit/ds/symlink/tps62933f.pdf) specifies a 30 V maximum operating input for TPS62933F. The charger permits a higher input, but PowerPath can expose downstream converters to solar-source voltage. Therefore set the accepted solar/PowerPath envelope from the weakest connected device and capacitor, including tolerance, cold open-circuit voltage and overshoot. Disabling a buck's EN does not remove voltage from its VIN pin. If coordinated input overvoltage protection cannot preserve adequate margin and operation, change the bucks or source conditioning before reuse.

Do not carry the failed main-input resistor workaround into Rev B as a selected damping circuit. Reconstruct the charger input network from its accepted reference and the actual panel/harness impedance. Review 5 V regulation at the lowest usable battery voltage as well as solar operation.

## Proposed schematic organization

| Sheet | Functional ownership | Required interfaces |
|---|---|---|
| Root and stack interface | Architecture, canonical stack connectors and domain notes | Existing rail/CAN pins; explicit IHU-owned controls; EPS-local measurements and alert semantics |
| Battery protection | Raw cell inputs, BMS, protection FETs, shunt, balancing, secondary protection | Raw pack/sense/NTCs, protected pack port, isolated SMBus/BTP |
| Hardware source isolation | Battery and solar MOSFET pairs, gate controls, transient handling | Structural RBF/deployment harness; protected and interlocked outputs |
| Charger and thermal qualification | LTC4162, its original PowerPath roles, charge/input shunts, NTC and MPPT network | Interlocked solar/battery, local charger I2C and alert, PowerPath output |
| Regulation and managed battery feed | Essential 3.3 V, 5 V, payload battery switch and rail sensing | Essential EPS/IHU/recovery loads; paired switched VBAT stack feed |
| Controller and dual CAN | MCU, oscillator, reset/debug, two transceivers | Independent A/B bus pairs, isolated BMS bus, local charger bus, default-off managed enables |

Sheet names describe an implementation organization; they do not create new nets or authorize connector pin changes. Follow repository net naming and design rules. Label source sides clearly to make any boundary bypass visible in the schematic.

## Schematic implementation checklist

- [ ] Preserve a recoverable Rev A baseline and keep the Rev B draft distinguishable from the fabricated project. Perform all KiCad source changes through Konnect.
- [ ] Export and reconcile saved Rev A connectivity/BOM with the release BOM and bench modifications. Resolve references, cell straps, thermistor disconnections and input damping before copying circuits.
- [ ] Accept physical pin/pad maps for every exact MPN/package, including MCU, BMS, FETs, transceivers, oscillator and connectors.
- [ ] Complete the BMS 2S connection/configuration manifest and choose protection/precharge/secondary circuits, with autonomous sensor fault behavior.
- [ ] Close source-switch gate networks and solar/PowerPath overvoltage envelope. Demonstrate permitted recovery without an MCU and no RBF bypass.
- [ ] Complete MCU power/reset/clock/BOOT0 and default-state design; confirm both FDCANs and debugging in the chosen package.
- [ ] Define local BMS bus isolation and verify its unpowered behavior, ground/shunt references and pull-up domains.
- [ ] Coordinate canonical interfaces: EPS as an A/B node, charger I2C ownership, protected/switched VBAT semantics, alert producer, payload and COMMS permissions. Preserve physical assignments unless an explicit new allocation is reviewed.
- [ ] Define payload shutdown evidence/order and local permission expiry. Preserve COMMS ground recovery within a measured energy budget.
- [ ] Complete continuous/peak/inrush/current limits and numerical fault settings. Populate real converter/passive ratings and harness/fuse coordination.
- [ ] Confirm actual courtyards, holder/structure clearance, component height and RBF travel before freezing board area or layer stackup.
- [ ] Save, export and inspect connectivity; run direct ERC, short/orphan checks and rendered-sheet inspection. Resolve power-off/back-feed findings and classify all remaining violations.

## Current handoff state

The [saved-schematic audit](../verification/rev_a_saved_schematic_audit.md) now records exported connectivity gaps, drawing/export disagreement and fabrication-BOM differences. Its verdict is INCOMPLETE: formal Konnect checks are now available and have run in part, while library pin-map acceptance remains incomplete. The installed MCU symbol fails GP mapping and must be corrected before use. Do not copy the saved power sheets as electrically accepted circuits.

The controller/CAN block has specific candidate parts, pin connections and calculated initial timing. The BMS, temperature and source-isolation blocks have functional specifications and acceptance tests. Their exact power components, fault settings and recovery evidence are still open. The complete BOM, mechanical fit, electrical verification and flight acceptance are not complete.

The exported audit and repository-history investigation are recorded. Next, resolve its connectivity and annotation findings through Konnect, reconcile the Altium fabrication release with physical rework, and accept candidate package maps before the controller/CAN schematic draft. Close the power-circuit selections alongside that work. Continue preparation without waiting for measurements that only the bench can supply, while leaving the affected ratings and thresholds explicitly unresolved.

## Controller package preparation — 2026-10-04

Konnect-created draft symbols now cover the corrected GP MCU, TCAN3413DR A/B transceivers and ECS-3225MV oscillator. Disposable schematic and board renders were inspected. IPC-2581 exports supplied individual pad dimensions missing from the direct queries; the oscillator now has an ECS-dimensioned custom candidate footprint. See [controller candidate evidence](../verification/controller_package_candidates.md) and [MCU evidence](../verification/stm32_gp_candidate_verification.md). Full acceptance remains open for default symbol metadata, MCU/CAN assembly land-pattern selection, oscillator marker/courtyard review and the custom-footprint instance-query discrepancy. No candidate is marked production accepted.

Manufacturer-pattern candidates and the seven controller/CAN/clock signal links are now present in the disposable project. All 44 custom pad numbers/centers/dimensions and all seven exported two-endpoint signal nets passed checks. The oscillator direct-query discrepancy has independent IPC-2581 and GenCAD coverage; its courtyard was corrected. Remaining work is symbol default metadata and controller support circuitry (power, reset, decoupling, pull-ups, bus interface/protection), followed by full ERC. Current partial-draft ERC remains 48 errors, documented rather than suppressed.

## Controller support progress — 2026-10-04

[Controller support draft](../verification/controller_support_draft.md) now adds essential-supply connections, 13 capacitors, five startup pull-ups and the NRST capacitor. Eleven exported named nets passed exact endpoint comparison; wire and short checks passed. Current ERC is 26 errors, reflecting remaining interfaces and the absent source in the standalone sheet. The earlier 48-error signal-only result is historical. CAN symbol v3 and oscillator v2 improve ground-pin drawing placement while preserving package mapping.
