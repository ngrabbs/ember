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
