# BMS SMBus boundary candidate

2026-10-23. ADUM1250ARZ-RL7 is an electrical candidate for the local pack-manager bus. It is **not accepted for native placement**: manufacturer pin/package figures and disposable symbol/footprint renders still need actual inspection. No CAD or library changes are made by this record.

## Boundary and power

BQ40Z50 VSS belongs to the raw-cell side of the current shunt; MCU/system GND belongs to PACK− on the other side. A direct ground connection bypasses the shunt. The proposed ADuM1250 uses side 1 for the STM32 and side 2 for the BMS. Both VDD pins receive the interlocked essential +3V3 positive supply. GND1 returns to system GND; GND2 returns to raw BMS VSS. Each supply gets a local 100 nF bypass to its own ground. Never join the ground pins or their capacitor returns.

The signal barrier avoids a direct ground wire across the shunt, but the common positive supply means the assembled circuit is **not a galvanically isolated power domain**. Side-2 supply and pull-up return currents pass through the shunt and must be included in current-measurement and power budgets. Do not add a raw-cell LDO: that would create an additional powered island during RBF. Only the reviewed pack protection domain may remain powered then.

Both bus pull-up domains come from the permitted +3V3 supply. BMS SMBD/SMBC are open-drain with internal pulldowns; unused BTP_INT is tied to BMS VSS. This avoids an intentional always-powered logic-high source. It does not establish every power-off leakage or external service path: review powered/unpowered endpoints, unequal supply ramps, all alternate feeds and the complete fixture. A grounded debug adapter must not bridge the shunt. Commissioning still needs the BMS's specified PACK+ wake source and verified 2S configuration.

## Electrical screening

Use 100 kbit/s initially. Four 3.9 kΩ pull-ups, each 0.1% and 25 ppm/K, are provisional. Their worst independent resistance excursion over 65 K is 3889.76–3910.24 Ω. The following calculations use the buck's static 3.23280–3.32439 V range, not its unqualified load-step envelope. A 6 A sizing case through a 2 mΩ, 1%, 50 ppm/K shunt gives up to ±12.159 mV reference offset when the TCR bound is assumed over 65 K; the shunt's cold guarantee remains open.

| Check | Conditional result |
|---|---|
| Side-2 supply, including reference offset | 3.22064–3.33655 V, within 3.0–5.5 V operation |
| Side-1 pull-up current at 0.9 V output low | At least 0.597 mA, above 0.5 mA minimum static loading |
| Side-2 pull-up current at 0.4 V output low | At most 0.755 mA, below BMS 1.5 mA sink test current |
| MCU output low to side-1 input low | 0.4 V maximum versus input requirement below 0.5 V; 100 mV static margin |
| Side-1 output low to MCU input | 0.9 V maximum versus 0.3 × 3.23280 V = 0.96984 V; only 69.84 mV static margin |
| BMS output low to side-2 input | 0.4 V maximum versus 0.3 × 3.22064 V = 0.96619 V; 566 mV static margin |
| Side-2 output low to BMS input | 0.4 V maximum versus 0.8 V input-low limit; 400 mV static margin |
| Supply allocation | Up to 3 mA per side at the published 3.3 V test point; reserve 6 mA plus bus pull-up currents, without calling this a guaranteed full-range current maximum |

At 3.0 V the conservative MCU input-low limit equals the isolator's 0.9 V maximum. That leaves no noise margin. The present buck step estimate can fall below 3.0 V, so this candidate does not close communication during large rail transients. Qualify the rail and define bus-reset/retry behavior; never interpret stale telemetry as a valid battery state.

Provisional total loading budgets are 100 pF on side 1 and 200 pF on side 2, including device, routing and fixture capacitance. The side-2 30–70% RC rise estimate is about 663 ns at 3910.24 Ω/200 pF, below 1 µs. ADI Table 10's side-1 100 kbit/s allowance scales from 771 pF at 1 kΩ to about 197 pF at this resistance. Those are screening calculations; measure both rise/fall times and account for propagation, clock stretching, SMBus timeouts and actual wiring. Do not extend these limits to 400 kbit/s or a shared stack bus.

Both supplies must reach the specified startup thresholds and wait at least 40 µs after both exceed 2.0 V, with the device's 3.0 V operating minimum also respected. UVLO behavior is not a guarantee of valid data at 2.5 V. Source qualification and MCU startup must allow the interface to settle before polling.

## Library query and acceptance remaining

The registered official symbol `Isolator:ADuM1250` has eight pins and the stock footprint `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`. Query-back on 2026-10-23 returned the following physical numbering. These are **library observations pending source-figure/render comparison**, not an accepted manufacturer map.

| Lead | Symbol name/type | Footprint pad center, mm |
|---|---|---|
| 1 | VDD1 / power_in | −2.475, −1.905 |
| 2 | SDA1 / bidirectional | −2.475, −0.635 |
| 3 | SCL1 / bidirectional | −2.475, +0.635 |
| 4 | GND1 / power_in | −2.475, +1.905 |
| 5 | GND2 / power_in | +2.475, +1.905 |
| 6 | SCL2 / bidirectional | +2.475, +0.635 |
| 7 | SDA2 / bidirectional | +2.475, −0.635 |
| 8 | VDD2 / power_in | +2.475, −1.905 |

The footprint's component-view/Y-down numbering is counterclockwise from the upper-left key; all eight pads are 1.95 × 0.60 mm SMD, no drill/EP or duplicate electrical pads. Its body is 3.9 × 4.9 mm, pitch 1.27 mm, and pin-1 silk/fab markers exist. Before real placement, independently compare the manufacturer's pin diagram and R-8 drawing, inspect a disposable schematic and board render, read back both instances and record all eight physical mapping rows. The official PDF text was accessible, but local PDF downloads timed out or failed and the web screenshot path did not provide an inspectable image. No source-diagram or disposable-render inspection is claimed here.

## Sources

- [ADI ADuM1250/1251 Rev L, September 2025](https://www.analog.com/media/en/technical-documentation/data-sheets/adum1250_1251.pdf), Tables 1, 5, 6 and 10, startup and application guidance, package/order information. The A-grade exact order code covers −40 to +105 °C; this is component screening, not pack qualification.
- [TI BQ40Z50-R2 SLUSCS4C](https://www.ti.com/lit/ds/symlink/bq40z50-r2.pdf), pin functions and §§7.11–7.12: SMBus levels, internal pulldowns and BTP limits.
- [ST DS13560 Rev 6](https://www.st.com/resource/en/datasheet/stm32g0b1ke.pdf), Tables 55 and 57: conservative input-low threshold and GPIO output-low limit. PA9/PA10 remain the local pack-manager bus allocation.
- [Native buck screening](../verification/essential_3v3/native/README.md) for the conditional static supply envelope and unresolved transient behavior.

## 2026-10-24 update: ISO1540DR selected for development integration

The ADuM1250 above is retained as the historical comparison. Use **ISO1540DR** for the next development schematic, conditional on the separate physical-map/disposable-render acceptance. TI's bidirectional clock channel supports target clock stretching; ISO1541 is not a substitute. The existing stock `Isolator:ISO1540` and `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` avoid a new custom part. Override the stock family datasheet link with the exact ISO1540 datasheet. This selection improves the MCU receive-low margin, at a higher current allocation and smaller side-1 capacitance budget.

Preserve the boundary above: VCC1/VCC2 and all pull-ups receive the permitted essential +3V3 positive supply, GND1 is system GND and GND2 is `GND_BMS_RAW`. Both local 100 nF bypasses return to their own domain. There is no additional always-powered logic supply. The common positive supply means this assembly does not provide galvanically isolated power; side-2 supply and pull-up currents return through the shunt. This design choice must be included in gauging calibration, load budgets and all powered/unpowered tests.

[TI SLLSEB6F Rev F](https://www.ti.com/lit/ds/symlink/iso1540.pdf), §§6.3, 6.9–6.12 and 8.2, is the electrical authority. The local primary PDF's actual pin-map, electrical-table, reference-application and land-pattern pages were viewed. The stock footprint is a generic alternative, not TI's exact example land: stock pads are 1.95 × 0.60 mm at X ±2.475 mm, whereas TI's example uses 1.55 × 0.60 mm at X ±2.7 mm. Both use 1.27 mm pitch. Record toe/heel coverage and saved-board inspection in the package acceptance before placement; do not describe the stock pattern as manufacturer-exact.

The [reproducible static screen](../verification/bms/bus_screening/calculate.py) and [results](../verification/bms/bus_screening/calculated.json) retain the earlier rail/shunt/temperature assumptions. They are conditional design calculations, not measured or simulated transient qualification.

| Check | ISO1540 result |
|---|---|
| Operation | Both sides 3.0–5.5 V; conditional side-2 range 3.22064–3.33655 V |
| MCU low into side 1 | 0.4 V versus minimum falling threshold 0.480 V: 80 mV margin |
| Side-1 low into MCU | 0.800 V versus 0.96984 V: 169.84 mV margin, versus 69.84 mV for the earlier candidate |
| BMS low into side 2 | 0.4 V versus 0.96619 V: 566 mV margin |
| Side-2 low into BMS | 0.4 V versus 0.8 V: 400 mV margin |
| Pull-ups | Four 3.9 kΩ, 0.1%, 25 ppm/K; ISO1 minimum low-state load 0.622 mA, ISO2 minimum 0.721 mA, BMS maximum 0.755 mA |
| Speed/loading | 100 kbit/s only; side 1 ≤40 pF and side 2 allocation ≤200 pF, including devices/routing/service fixture |
| RC rise estimate | 133 ns / 663 ns for side 1 / side 2, versus 1 µs screening limit |
| Static IC allocation at 3–3.6 V | Both lines low: 7.1 + 6.7 = 13.8 mA maximum; both high: 4.0 + 3.5 = 7.5 mA maximum, plus external pull-ups |

The upper bound for four pull-ups to zero volts is another 3.431 mA. This deliberately exceeds the current at the specified finite low levels. The static all-low total is approximately 17.23 mA, about 57.3 mW from a 3.32439 V source; switching/load-capacitance current is additional. The calculation also checks high-state margins using ISO input leakage 10 µA, BMS input leakage 1 µA and its minimum 0.7 MΩ pulldown; a provisional MCU input budget of 1 µA must be reconciled with the selected pin modes and complete ST limits. ISO input capacitance is 7 pF **typical**, not a guaranteed maximum. Neither loading budget is established by that number alone.

Define firmware startup as waiting at least 1 ms after both local supplies are valid at or above 3.0 V, then performing bus recovery and verifying BMS identity/configuration before accepting telemetry. This is a conservative proposed sequence, not a new datasheet guarantee: TI's UVLO recovery maximum is 151 µs under its stated test conditions. The UVLO maximum threshold of 2.9 V does not extend operation below 3.0 V. The buck's unqualified 2.987 V load-step estimate still falls outside the interface's operating range. Verify rail transients, unequal ramps, stuck-low recovery, SMBus timeouts, power-off leakage and service-adapter paths before closing this interface.

The physical numbering is 1 VCC1, 2 SDA1, 3 SCL1, 4 GND1, 5 GND2, 6 SCL2, 7 SDA2, 8 VCC2. Package acceptance and native integration evidence belong to the new BMS integration checkpoint; the historical ADuM table above is not that acceptance.

## Current-measurement gate found during integration

**The shared-positive supply is provisional and does not meet the complete-current measurement intent by itself.** In a steady battery-powered fixture, take actual battery discharge current as positive. Let `Iraw_bus` be the sum of ISO side-2 supply current and any side-2 pull-up current returning directly to `GND_BMS_RAW`. With other unmeasured retained-domain loads treated separately, KCL gives approximately `Ishunt = Ibattery − Iraw_bus`. The signal barrier does not create a metallic ground short, but the shared positive supply permits this measurement error. “Current returns through the shunt” must not be read as “the shunt measures all battery current correctly.”

Using the present static screen, side-2 IC current can be 6.7 mA in the published both-low condition; its two pull-ups add up to 1.716 mA under the deliberately conservative zero-volt upper bound. Thus the affected branch can shift measured current by roughly 8.42 mA in that fixture, before other leakage/reference loads. It is state-dependent. A single zero-current calibration cannot remove the active/idle difference, and near idle the apparent current can have the wrong sign. Do not accept fuel gauging or low-current charge/discharge decisions on this architecture without closing that error. Ampere-level fault settings need their own uncertainty review rather than inheriting a “negligible” assertion.

A permitted-supply **isolated DC/DC** feeding only VCC2 and its two pull-ups would remove the common-positive power path: primary VIN/GND use the system domain, secondary VOUT/return use the raw BMS domain, and no additional raw-cell supply remains powered during RBF. Evaluate startup, both supplies' valid ranges, power-off leakage, EMI, source budget and actual package area together. It is functional separation across the current-sense reference, not a claim of spacecraft safety isolation: the two ground domains remain intentionally joined through the current shunt.

Primary alternatives under review, with no native selection or new custom construction authorized by this note:

- [ADI ADuM5020/ADuM5028 Rev E](https://www.analog.com/media/en/technical-documentation/data-sheets/adum5020-5028.pdf), retrieved 2026-10-24. A -3 converter supports 3.3 V input/output. ADuM5028 offers an 8-lead wide package; however, no-load input current can reach 15 mA, and output/loading/ripple limits must be checked at this small bus load. A registered `ADuM502` symbol search returned none. It would retain ISO1540's better receive-low margin but add power and footprint costs.
- [ADI ADM3260 Rev G](https://www.analog.com/media/en/technical-documentation/data-sheets/ADM3260.pdf) integrates isolated I2C and isolated power in one 20-lead SSOP. A registered exact symbol search returned none. It could reduce part count, but its electrical limits must be screened independently; the earlier ADuM1250/ISO1540 calculations cannot be applied to it.

The development ISO1540 circuit may be drawn to make the retained boundary reviewable, with this deficiency explicitly noted. Its static level check and package map are separate from this unresolved power/current-measurement gate. Resolve this gate before final BMS acceptance or PCB release.

Follow-up screening rejects ADM3260 as a direct substitute with its normal power direction: its isolated output is side 1, whose specified low can be 0.85/0.90 V, exceeding the BMS 0.8 V input-low limit. Reversing the logical sides alone would put the power input on the raw reference and would not solve the shared-power problem. ADuM5028-3BRIZ feeding the existing ISO1540 side 2 remains the preferred isolated-power candidate to finish screening. Its supply/load/noise limits and source figures still require acceptance before library construction.
