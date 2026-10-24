# Isolated bus-power comparison: read-only physical/source review

2026-10-24, basis `74441cb6fe011e806f72eb0dc7af6b852b2e4f81`. No native/library/disposable project was authored or changed. The [UCC construction proposal](../../../design/rev_b_bms_ucc33020_library_rules.md) is **not approved**; neither UCC33020 nor TLV767 is accepted for real circuit placement by this review. Historical UART/BMS fixtures and verifiers remain untouched.

## Primary source and actual image inspection

Both PDFs downloaded directly from TI with curl; exact URLs, identities, byte counts and SHA-256 are in `sources.json`. Full downloads remain `/tmp/ember-ucc33020.pdf` and `/tmp/ember-tlv767.pdf`. Source figures here were rendered with pypdfium2 at 2× scale and actually opened, separately from text extraction. UCC pages inspected: 4, 6, 7, 8, 23, 24, 25, 26, 29, 34–36; TLV pages: 3, 4, 6, 22, 37–39. The saved subset covers pin maps, specifications, application and package/land/paste. No native instance/render acceptance has run.

UCC identity: SLUSFK4A Rev A May 2025; ordering addendum 7-Nov-2025; RAQ0012C drawing 4230399/A 01/2024. TLV identity: SLVSE84D Rev D July 2021; current appended DRV0006A drawing 4222173/C 11/2025. A recent appended mechanical drawing does not change the electrical-revision identity.

## Electrical findings for root's comparison

- UCC 3.0–5.5 V recommended input. At 3.3 V ±10%, recommended 5 V output power is 0.5 W at 25–85°C, 0.35 W at 105°C and 0.2 W at 125°C. Do not substitute the 1 W headline, or the 140 mA/25°C characterization point, for the recommended 3.3 V operating envelope.
- UCC p7 has ±4% output accuracy across 3.0–5.5 V input. At exactly 3.3 V and 0–140 mA it lists 4.85/5/5.15 V min/typ/max. Line regulation 12 mV/V max applies 3.0–3.6 V at 50 mA; load regulation 0.4% max applies 3.3 V, 0–100 mA. Avoid unreviewed double-counting of overlapping accuracy specifications.
- UCC ripple is 50 mV typical / **75 mV maximum**, but specifically at 25°C, 3.3 V input, 50 mA output, 20 MHz bandwidth and the stated capacitor network; specified by design, not production tested. This is not a whole-temperature/noise/transient guarantee.
- UCC disabled current **180 µA max** at 3.3/5 V; enabled 5 V-output no-load current 7 mA typ / 15 mA max (5.5 V-output no-load max 18 mA). Full load at 3.3 V, 140 mA output, 25°C: 390/415/450 mA min/typ/max input. Efficiency 50% is typical at 3.3 V/100 mA. Input current at the actual ~10 mA isolated load is not guaranteed by that efficiency row.
- EN rising threshold 2.1 V max, falling 0.8 V min, input current 10 µA max; fault output ≤0.5 V with the specified ≥18 kΩ resistor. Fault pulse 200 µs typical. EN and SEL have weak internal pulldowns but must be intentionally driven/strapped. SEL=VCC selects 5 V; SEL=GNDS selects 5.5 V. SEL is sampled below the secondary 2.7 V UVLO point, then latched. No explicit prebiased-start guarantee was found.
- Soft-start begins with stepped duty cycle, limits duty while secondary output is below 2.7 V, and faults if regulation is not reached after the described 16 ms timeout. Output UV/OV and thermal faults shut down and retry after the described 160 ms interval. Timing prose is not an independently bounded system guarantee. Input UV/OV recovery resumes immediately when its threshold is crossed rather than waiting for that timer.
- For 5 V mode, output OVP rising threshold is **5.45 V typical / 5.5 V max**, not a guaranteed lower bound. The OV clamp is described as keeping the converter within absolute maximum conditions before shutdown. No separate quantified dynamic peak clamp limit or prebiased restart bound was found; do not infer complete external-load containment.
- Typical application: input 15 nF + 10 µF; output 15 nF + 22 µF, low ESR/ESL and close to the pins. The TI calculator is recommended for capacitor/load choices to avoid overpower mode; nominal values alone do not establish effective capacitance or coupled startup acceptance. No ferrites are mandatory in this reference. Heat leaves through ground terminals; no central thermal pad.
- TLV76733: 3.3 V ±1% over specified load/temperature; p6 accuracy row has ≥1 mA load and the table's input/headroom conditions. Fixed-output IQ is 60 µA typ / 95 µA max. DRV dropout max 1.4 V at 1 A; low-load dropout plots do not provide an independent guaranteed lower-load bound. CIN recommended 1 µF; COUT nominal 1–220 µF, ≥0.5 µF effective for stability, ESR 2–500 mΩ. Evaluate actual selected capacitor and input trough/headroom together.
- TLV reverse output-to-input current is **not limited** and can damage the device. VOUT/SNS absolute limit is min(VIN+0.3 V,18 V). Input collapse with stored output charge or externally biased output needs explicit treatment. The 1.2 mA typical disabled output pulldown is not an approved large-cap discharge/reverse-current solution. LDO EN ≥1.2 V enables, ≤0.4 V disables; it has an internal pullup. Its soft start is typical 500 µs and not full fault containment.

The later 5.5 V-mode comparison would strap SEL to GNDS: full-input ±4% implies 5.28 V minimum, giving more LDO headroom than 5 V mode. The numeric recommended-power table is explicitly for 5.0 V output; 5.5 V operating-area graphs are typical, not a new numeric guaranteed table. Whole-temperature input-current, ripple, dropout and startup gates remain open.

TLV p20 Figure 9-1 was separately rendered/opened: the external Schottky has **cathode IN / anode OUT**, diverting reverse current around the regulator into the input reservoir; it does not block reverse current or isolate the upstream load. `Device:D_Schottky` readback confirms pin1 K / pin2 A. The already physically accepted BAT46W-7-F with stock `Diode_SMD:D_SOD-123` is an available comparison candidate, not an accepted protective selection. Current Diodes DS30044 Rev20-2, November2023, specifies VF ≤0.45 V at10mA/25°C, 150mA continuous, 750mA/10ms surge; this cannot by itself guarantee TLV's VIN+0.3V absolute constraint, particularly with a hard-clamped input. Review actual stored energy/current/temperature and alternate reverse isolation before selecting it. Source: https://www.diodes.com/assets/Datasheets/BAT46W.pdf ; local `/tmp/ember-bat46w.pdf`.

## Physical maps and stock readback

UCC has twelve logical contacts, six isolated small lands plus two connected three-contact ground combs: **eight continuous metal regions**, no NCs, no central EP and no mechanical pads. See proposed per-lead table and explicit decomposition. Configured footprint searches `RAQ`, `VSON-12`, `UCC33` returned zero. The isolated positive supply would feed only ISO1540 side 2 and its pullups; system and raw returns remain connected only through the existing shunt. This physical proposal does not resolve electrical selection.

`check_decomposition.py` is an ordinary numerical proposal screen, not CAD authoring. Its 1 µm raster/0.5° arc sampling compares a nominal R0.05-filleted TI comb with the rounded-rectangle union: 0.004248 mm² combined symmetric-difference area, differing pixels within 0.043 mm per coordinate of a sharp corner. Conservative resolution bound 0.052 mm. `decomposition.png` was opened: yellow is common area, green is ideal fillet area absent from the proposed union. Native geometry and aperture exports must be checked anew after approval. All extra mask apertures must be blank; their union with numbered copper pads' base F.Mask must be verified, rather than counted as isolated numbered openings.

TLV stock `Regulator_Linear:TLV76733DRVx` query saved in `tlv767_symbol.json`; proposed unchanged stock no-via footprint `Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` in `tlv767_footprint.json`. This is a possible stock assignment rather than new custom authoring. The symbol default instead uses the thermal-via variant; selecting the no-via alternative would be deliberate and require the disposable gate.

| TI physical lead/function | Stock symbol/type | Stock front X/Y mm |
|---|---|---|
| 1 OUT | 1 OUT / power_out | −0.8875 / −0.65 |
| 2 SNS | 2 SNS / input | −0.8875 / 0 |
| 3 GND | 3 GND / power_in | −0.8875 / +0.65 |
| 4 EN | 4 EN / input | +0.8875 / +0.65 |
| 5 GND | 5 GND / passive, stacked with 3 | +0.8875 / 0 |
| 6 IN | 6 IN / power_in | +0.8875 / −0.65 |
| EP7 ground/thermal pad | 7 PAD / passive | 0 / 0 |

TI p3 top view: 1 upper left, 1–3 down left and 4–6 up right; stock orientation agrees. Preserve stacked 3/5 semantics and wire EP7 to the selected return. Seven electrical pins; no NCs or mechanical-only contacts. The no-via footprint raw count is **9 = 7 copper objects + 2 blank paste-only objects**, zero drills. Copper lead pads 1–6 are 0.375 ×0.40 mm roundrect ratio0.25; EP7 is 1.0 ×1.6 mm F.Cu/F.Mask; two paste windows 0.81 ×0.64 mm at Y±0.4. The default via variant instead has 12 raw objects including two plated drills and backside copper, not nine.

**Stock-land deviation:** TI current p38 recommends contacts 0.45 ×0.30 mm at X±0.975; stock uses 0.375 ×0.40 at ±0.8875. EP nominal 1×1.6 matches. TI p39 stencil gives 88% EP coverage; stock windows have 64.8% rectangular area before corner rounding. Stock mask expansion and complete assembly/courtyard acceptance are not established by pad queries. These are documented stock alternatives, not an exact TI land/stencil claim. No stock geometry has been modified. Actual disposable placement, saved/live full-object checks and render acceptance remain **NOT RUN**, pending electrical choice.
