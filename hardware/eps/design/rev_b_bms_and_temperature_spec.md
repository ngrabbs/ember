# EPS Rev B battery protection and temperature specification

Draft dated 2026-10-03. Use BQ40Z50-R2 as the circuit and configuration reference for an autonomous 2S pack protector, with two independent cell-temperature sensors. Retain a third, electrically separate sensor for LTC4162 charge qualification. This document defines implementation requirements and simulator tests; it does not freeze production parts, numerical protection limits or pack acceptance. Rev A charging remains unresolved until the damaged circuit is inspected.

[Architecture plan](rev_b_plan.md) · [Source isolation](rev_b_source_isolation_study.md) · [Rev A bench evidence](../../../system/ground_station/eps_bench_setup.md)

## Protection circuit allocation

The raw pack domain contains the BMS, its cell filters, shunt and charge/discharge protection FET drive. It stays connected to the cells while RBF interrupts downstream spacecraft functions. Put high-side protection FETs between raw battery positive and the protected pack port; the separate RBF battery-isolation pair follows that port. Keep precharge and any secondary-protection circuitry within the reviewed reference arrangement.

Use three raw cell nodes: pack bottom, series midpoint and pack top. Provide filtered inputs to the BMS and implement the selected device's exact 2S connection scheme for unused cell inputs. Never leave them floating or copy a generic four-cell reference unchanged. Program and verify 2S configuration before normal operation; define commissioning power and connection order so the device does not enter an unintended shutdown state during setup. The [TI datasheet](https://www.ti.com/lit/ds/symlink/bq40z50-r2.pdf), §§8.3.5.4 and 9.2, is the circuit authority.

The BMS shunt must measure the complete battery current in both directions. Place its Kelvin connections and ground references so USB, debug, cell-sense returns or structure connections cannot bypass it. Keep the LTC4162 charge-current shunt separate. Audit every connection across the retained-power boundary; local SMBus and BTP status require power-off isolation before reaching the STM32 domain.

Compare 5 mΩ and 10 mΩ BMS shunts against the selected comparator thresholds, measurement accuracy and peak currents. At an illustrative 6 A, they drop 30 mV and 60 mV and dissipate 0.18 W and 0.36 W respectively. These are engineering sizing cases, not approved current ratings. Select tolerance, temperature coefficient, pulse capability and thermal margin together with fault settings.

Use the reference's internal balancing first for evaluation. It is limited to 10 mA: correcting an illustrative 100 mAh group mismatch takes at least 10 hours of actual balancing time, before restrictions and inefficiency. Demonstrate that this is adequate for the characterized pack; add external balancing only if justified. Equal voltage is not proof of matched capacity or health.

Secondary protection and any electrically triggered fuse remain explicit design decisions. Begin reversible fault tests with a simulator and an appropriately configured development fixture. Review permanent-failure actions before enabling them; do not discover an irreversible fuse response while experimenting with a real pack.

## Sensor allocation and harness

| Sensor | Electrical destination | Proposed location and purpose |
|---|---|---|
| Charger NTC | LTC4162 NTC network | A thermally representative cell surface identified through pack testing; independently qualifies charging. |
| Group 1 NTC | BMS TS1 | Cell surface in the lower series group; battery protection and telemetry. |
| Group 2 NTC | BMS TS2 | Cell surface in the upper series group; battery protection and telemetry. |
| Optional future sensors | BMS TS3/TS4 | Reserve for uncovered cell hot/cold spots or protection-FET temperature after thermal testing. |

Attach sensors with electrical insulation, retained thermal contact and strain relief. Define attachment materials and qualification with the mechanical design. A detached sensor that still reads ambient temperature is an important failure case. Test both cells in each parallel group before concluding that one sensor covers the group. Keep the charger sensor and one BMS sensor nearby enough to evaluate agreement, while preserving separate wiring and bias circuits.

Retain XT30 for main power provisionally. Three cell-sense nodes plus three separate two-wire NTCs require nine signal contacts before optional sensors or spares. This is a contact-count requirement, not a final connector pinout or connector selection. Prefer dedicated NTC return conductors to their respective quiet sensing references rather than returning through the high-current power cable. Do not accidentally join charger ground to a cell-side reference across a current shunt through the harness.

Choose a keyed, retained sensing connector and document pack assembly, polarity, mating order and sense-wire fault protection. Verify filters and protection against balancing currents, measurement errors and shorts between adjacent cell nodes. No raw cell-sense pin may power downstream electronics around RBF.

## LTC4162 thermistor network

Implement the network independently of MCU firmware:

```text
LTC4162 NTCBIAS pin 9 -- 10 kΩ bias resistor -- NTC pin 10
                                                    |
                                              Charger NTC
                                                    |
                                             Quiet analog GND
```

Use a 10 kΩ at 25 °C NTC as the baseline, with a matching bias resistor of 1% or better and a curve consistent with the charger's 3490 K reference model. The [LTC4162-L datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf), pin descriptions and temperature-qualification section, specifies 1.2 V measurement excitation and the matching-resistor arrangement. A different curve requires calculated changes and verification. Freeze a mechanically suitable sensor MPN, resistance table, tolerance and lead/attachment construction before routing.

The following resistor substitutions use the ideal constant-beta model, `R(T) = 10 kΩ × exp[3490 × (1/T − 1/298.15)]`, with kelvin temperatures. They are approximate test targets, not a manufacturer's resistance table or final JEITA thresholds.

| Simulated temperature | Approximate resistance | NTC voltage while 1.2 V bias is active |
|---|---|---|
| 0 °C | 29.2 kΩ | 0.894 V |
| 10 °C | 18.6 kΩ | 0.780 V |
| 25 °C | 10.0 kΩ | 0.600 V |
| 40 °C | 5.71 kΩ | 0.436 V |
| 45 °C | 4.79 kΩ | 0.389 V |
| 60 °C | 2.92 kΩ | 0.271 V |

Measure the pulsed bias with an appropriate capture method; a static meter reading during inactive bias is not evidence of failure. Keep test points at NTCBIAS, NTC and analog return. Read back actual JEITA configuration and ADC validity alongside measurements. Normal firmware must not disable qualification or install a dummy-temperature bypass.

## BMS temperature configuration

The BMS has its own thermistor excitation and conversion model. Its [datasheet](https://www.ti.com/lit/ds/symlink/bq40z50-r2.pdf), §9.2.2.3.4, specifies 10 kΩ sensors with internal nominal 18 kΩ pull-ups. Do not copy the charger divider onto TS inputs or assume equal nominal resistance means equal temperature conversion. Select the BMS sensor curve and calibration model together.

The [R2 technical reference manual](https://www.ti.com/lit/ug/sluubk0b/sluubk0b.pdf), temperature-protection, open-thermistor and temperature-configuration sections, documents these relevant behaviors: TS2 defaults to FET reporting; enabled cell sensors use the minimum for cold protection and maximum for hot protection; host temperature injection can bypass TS sensing; open-sensor detection also depends on internal-temperature comparison and delay. These details require explicit readback and fault testing.

| Configuration item | Required implementation outcome |
|---|---|
| TS1/TS2 enable and mode | Both enabled as cell-temperature inputs. Confirm TS2 is changed from its FET default. |
| TS3/TS4 | Disable when unused and connect unused pins as instructed by the selected datasheet. Revise configuration if populated later. |
| Internal temperature | Report separately; do not let PCB temperature substitute for pack sensors. |
| Host-written cell temperature | Disabled in normal operation. Protection must remain independent of STM32 availability. |
| Thermal protections | Configure charge and discharge hot/cold limits, delays and recovery hysteresis from accepted cell limits and thermal uncertainty. |
| Open/short sensor response | Required outcome is charging inhibited without a host command. Verify actual device response over warm and cold conditions; add independent circuitry or change the implementation if coverage is inadequate. |
| Permanent-failure actions | Explicitly review latch, FET and fuse behavior for each enabled fault. Record recovery/service policy. |

An open sensor can look like extreme cold and a short like extreme heat. Do not rely only on an implausibility comparison with the MCU or on the named open-thermistor flag. Verify the resulting charge FET state and actual current. Keep thermal fault indications distinct from stale/unavailable SMBus telemetry.

## Threshold ownership and commissioning

LTC4162 owns normal charge regulation and its independent NTC qualification. BMS owns cell protection, including individual-cell voltage and battery current limits. EPS requests lower charge/current or load states within that envelope; it cannot override protection. A BMS charging recommendation over SMBus is not automatically executed by the standalone LTC4162.

Do not freeze numerical cutoffs from example circuits or the repository's informal cell summaries. Obtain the applicable MJ1 specification and pack acceptance requirements, then account for sensor accuracy, cell-to-sensor gradient, ADC error, timing and current overshoot. Normal charger limits should avoid repeatedly hitting BMS protection. A pack-voltage limit alone cannot detect one group overcharging while the other remains low.

Maintain a versioned configuration manifest containing device/firmware identity, cell count, chemistry profile, sensor models, protection thresholds/delays, balancing rules, wake/sleep behavior, permanent-failure actions and sealing policy. Calibration covers both group voltages, signed current and both temperatures. Read back configuration after programming and after a power cycle. Gauging accuracy still requires pack characterization and learning; initial state of charge is not acceptance evidence.

## Simulator verification sequence

1. Assemble and verify both temperature networks before testing real charging. With a safe simulated 2S pack, substitute valid, open and short resistance states into each input individually.
2. Verify that each BMS cell sensor can independently inhibit charging while the charger NTC remains valid. Repeat with STM32 held in reset and with SMBus unavailable. Repeat open-sensor tests with a cold BMS PCB to expose internal-temperature comparison limitations.
3. Verify charger NTC pause independently while the BMS permits charging. Capture bias waveform, NTC conversion, JEITA region, charger state, current and configuration readback.
4. Sweep individual group voltage and charge/discharge current to verify programmed trips and recovery. Measure current through partial protection states; do not infer full isolation from a CHG/DSG status bit.
5. Integrate RBF source isolation and test recovery after permitted battery cutoffs without the STM32. Verify sensor harness removal cannot leave charging enabled and no recovery path bypasses RBF.
6. After simulator acceptance, calibrate real sensors against a reference thermometer and characterize mounting gradients and pack operating modes under a controlled test plan.

Final evidence must show electrical fault response, retained configuration, autonomous operation and physical temperature coverage. This specification makes the next schematic pass concrete; it does not establish those results.
