# Four rail measurement development screen

2026-10-24. Calculation authority for the [ADC integration contract](../../../design/rev_b_adc_frontend_integration.md). This packet proves conditional passive arithmetic, not an integrated circuit, absolute measurement accuracy or brownout qualification. A separate native integration packet records actual schematic state.

Each source feeds a divider and10 nF external filter **before** its TMUX1511 isolation channel. After the switch, a1 kΩ resistor leads to the MCU pin and47 kΩ ground bleed. The bleed deliberately loads the divider; firmware must use the loaded transfer below. Use the BMS for precision battery/cell telemetry and protection, because the high-voltage-tolerant diagnostic battery path trades ADC resolution for fault headroom.

| Source | U100 pin | Nominal ADC/source gain | Design input ceiling | Largest steady ADC voltage |
|---|---|---:|---:|---:|
| SYS_PWR_PERMITTED | 7 / PA0 | 0.03890593 | 60 V | 2.34645 V |
| +5V | 8 / PA1 | 0.28657488 | 6 V | 1.72607 V |
| +3V3 | 11 / PA4 | 0.44337950 | 3.6 V | 1.60097 V |
| BATT_PERMITTED | 12 / PA5 | 0.03890593 | 60 V | 2.34645 V |

The60 V sensitivities do not raise system operating ratings. Protected+5V/+3V3 measurements depend on their respective containment boundaries. No arbitrary coincident fault or failed divider is covered.

`calculate.py` sweeps independent resistor initial/temperature corners and switch resistance. It includes off-to-on connection of the precharged filter as an ideal passive step: every resulting ADC node remains below2.857 V, while every switch-open divider remains below3.6 V under the input ceilings. The maximum steady source impedance is8.625 kΩ; the conservative external-filter half-LSB settling sensitivity is0.903 ms. `independent_check.py` solves a conductance matrix and separately checks nominal settling, confirming the1 kΩ/47 kΩ network was not omitted from the transfer. Results are deterministic JSON, without vendor semiconductor models.

Use a dedicated supply qualifier and2 ms settling wait,160.5-cycle ADC sampling at≤35 MHz, analog/no-pull pin modes, ADC power-up calibration/regulator/reference startup and proper rearm after long idle. Initial scan rate is10 Hz. Reference/VREFINT calibration, ADC total error, switch charge injection, pad loading, supply collapse and all-path off-state behavior remain separate acceptance gates. Averaging does not remove ratio/reference/offset errors. The0.2 µA combined leakage calculation is a stated sensitivity, not a guarantee outside its test conditions.

At3.6 V reference, the coarse high-voltage channels have≈22.59 mV/LSB and≈146.84 mV error from6.5 ADC LSB alone. Their ratio error and reference uncertainty add separately; these channels must not be described as precision battery gauges. For the protected5 V and3.3 V channels the analogous ADC-only terms are≈19.94 mV and12.88 mV. Measuring the3.3 V rail against itself is ratiometric; use a verified reference to infer its absolute value.

Primary sources and exact component identities are in the integration contract. Root actually inspected the existing TMUX manufacturer p21/p23 images. ST source pages and native rendered sheets are recorded separately by the integration owner. These calculation scripts do not read or write native KiCad source.
