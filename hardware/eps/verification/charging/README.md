# Charger thermistor analysis

2026-10-23. The development sensor candidate is **Semitec 103AT-2**, with three separate devices for LTC4162 charge qualification and BMS group-1/group-2 sensing. Its leaded construction permits a pack-mounted probe; insulation, extension-wire attachment, retention and vacuum-material acceptance remain assembly decisions. It is not a selected flight sensor assembly.

## Divider and conversion

Use a 10 kΩ bias resistor from LTC4162 pin 9 NTCBIAS to pin 10 NTC, with the charger sensor from NTC to the charger's quiet ground. Candidate bias part is TNPW060310K0BEEA, 0.1%, 25 ppm/K; its exact ordering/rating needs the normal library/BOM acceptance. Do not share either BMS sensor or its return/bias circuit with this divider. Charger-side return must not bypass the BMS current shunt.

For raw ADC code `c`, the circuit gives `c = 18191 × 1.2 × Rntc / (Rntc + Rbias)`, hence `Rntc = Rbias × c / (21829.2 − c)`. Reject invalid, open and short readings before converting to temperature. This equation agrees with the actual divider and the main explanation on printed p.21 of [LTC4162-L Rev A](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf). The inverted expression repeated in its register descriptions disagrees with that circuit and Table 6. The reproducible check agrees with the six Table 6 resistance/code pairs to within **0.012%** after published rounding.

With 10 kΩ at room temperature, expect about 0.6 V while the 1.2 V excitation is active, and raw code 10915. This is a pulsed measurement: inactive bias or stale ADC data must not be interpreted as a failed thermistor. Open sensing tends high; shorted sensing tends low. Actual charging inhibition and fault recovery must be verified with resistor substitution, valid telemetry and STM32 held in reset.

## Candidate curve and threshold sensitivity

The [Semitec AT catalog](https://www.semitec-global.com/uploads/2022/01/P12-13-AT-Thermistor.pdf), printed pp.12–13, provides the nominal 103AT resistance table and 1% resistance/beta tolerances. Both pages were rendered and inspected. The analysis interpolates log resistance against reciprocal absolute temperature rather than assuming a constant-beta curve equals the manufacturer's table.

Applying the original LTC4162 default end thresholds to this candidate gives nominal trips near **−0.79 and +60.77 °C**. Therefore it is not a drop-in way to establish a 0–60 °C charging window. Clearing `en_jeita` retains basic temperature cutoff; it does not bypass it. The proposed restricted development profile uses nominal breakpoints 5, 10, 35, 37, 39 and 40 °C. These are analysis inputs, **not approved cell limits or register programming instructions**.

Eight sensitivity corners combine sensor R25 ±1%, beta ±1%, bias initial ±0.1% and bias drift across −40 to +85 °C electronics screening. The proposed cold and hot endpoints then span about **4.49–5.49 °C** and **39.48–40.53 °C**. ADC error, table interpolation error, full R/T guarantees, sensor gradient/lag and mounting self-heating are outside this envelope. The BMS must provide independently configured protection before a host changes the charger profile; charger power-on defaults cannot depend on a successful STM32 boot for pack protection.

## Reproduce and integrate

Run `python3 hardware/eps/verification/charging/check_thermistor.py` from the repository root. It writes [results](thermistor_results.json), checks the independent ADI table anchors, divider monotonicity, room-temperature ratio and invalid-code rejection. It performs no hardware access or register writes.

The next native charger sheet must include physical pins 9/10 and their complete local wired divider, test points, verified 2S cell straps, DVCC tied to the local bus pull-up domain, and battery sensing entirely after hardware isolation. The BMS curve/coefficient configuration is a separate acceptance item. The hand-reworked Rev A thermistor fault still requires physical inspection; the current saved import cannot establish its copper connectivity.
