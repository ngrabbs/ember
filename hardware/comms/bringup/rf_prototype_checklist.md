# Comms prototype RF qualification worksheet

Status: NOT EXECUTED. This worksheet does not approve fabrication or certify RF performance.

## New capacitor sensitivity result

FH specifies the installed 0402CG3R9C500NT end capacitors as 3.9 pF ±0.25 pF (C0G, 50 V, 0402). [Manufacturer specification](https://fhcomp.com/en/product_info/?prod_code=0402CG3R9C500NT).

The analysis varied both end capacitors together through 3.65, 3.90 and 4.15 pF, with the previously verified Coilcraft 10 nH model and routed-line network. Coupling capacitors remain ideal 1.6 pF; shunt capacitors remain exact nominal values. Added capacitor/ground parasitics are zero for this separate sensitivity slice.

| Shunt value | TX output loss at 437 MHz across end-cap sweep |
|---|---:|
| Current 9.1 pF | 2.374–2.915 dB |
| Candidate 8.2 pF | 1.634–1.796 dB |
| Candidate 7.5 pF | 1.563–1.608 dB |

7.5 pF remains the preferred test candidate. These are model results, not measurements or full tolerance bounds. Opposite-sign end-cap errors, inductor/shunt/coupling tolerance, active loading and PCB parasitics are not included. All 72 sampled filter/frequency results passed the passive power-balance check. Reproduce with `../design/analysis/rf_end_cap_sensitivity.py OUTPUT_DIRECTORY`; raw results are in `../design/analysis/rf_end_cap_sensitivity.json`.

## Record before testing

- Board revision/serial and actual stackup: __________
- Instruments, calibration date and calibration planes: __________
- Supply voltage/current limits and installed component variants: __________
- Required occupied bandwidth, allowable filter loss, return loss, rejection frequencies/limits, TX power and RX sensitivity: __________
- Baseline 9.1 pF C526972: YAGEO CC0402BRNPO9BN9R1, identified in the sourcing record; verify live stock and exact RF model.
- Exact orderable 7.5/8.2 pF tuning parts and tolerances: unresolved; do not reuse the 9.1 pF supplier code.

The system targets above must be defined before assigning PASS/FAIL. The sweep below is for characterization, not an invented product specification.

## 1. Passive filters

Measure unpowered, with active and bias branches isolated as described in `../design/analysis/rf_vendor_model_followup.md`. Verify isolation against the actual schematic and assembly before connecting the VNA. Retain the filter end capacitors. Calibrate or de-embed the temporary launches to the filter ports; a long flying ground lead becomes part of the measurement.

Sweep 350–550 MHz, recording S11, S21 and S22, then record explicit 435 and 437 MHz points. Measure additional out-of-band points against the eventual rejection requirement and within the instrument's calibrated range.

| Filter | Paired tuning capacitors | Baseline | Intermediate | Preferred candidate |
|---|---|---|---|---|
| RX input | C56/C64 | 9.1 pF | 8.2 pF | 7.5 pF |
| TX preselector | C96/C100 | 9.1 pF | 8.2 pF | 7.5 pF |
| TX output | C87/C92 | 9.1 pF | 8.2 pF | 7.5 pF |
| LO | C90/C95 | 9.1 pF | 8.2 pF | 7.5 pF |

Change one filter's pair at a time. Save the baseline before rework. Record peak frequency, loss and both return losses at the operating frequency, bandwidth and required rejection. Preserve raw .s2p files; use names such as BOARD_TX-output_7p5_CONFIG_DATE.s2p. Fill the companion CSV with measured values; empty cells mean unmeasured.

## 2. Amplifiers and bias isolation

Restore the intended circuit. Verify rails and quiescent current before applying RF. With correctly terminated ports, measure U8/U9 gain and supply current at the intended operating frequencies and levels. Check for oscillation with no input and across the intended operating states. Account for instrument attenuation, DC blocking and maximum input ratings.

For L16, measure RF leakage onto the supply and check gain/stability under bias. Record supply current and heating. The selected 0805HP-221XJRC has not satisfied the historical >1.5 GHz SRF target; its assembled suitability remains an explicit open qualification item. Do not mark it accepted from ideal reactance alone.

## 3. Single-antenna switch and complete signal paths

Confirm U11 routes the one J9 antenna to RX and TX in the intended control states. Measure path loss and inactive-port leakage at low power first. Verify control timing during transitions, then test intended TX power with appropriate attenuation and termination. Record any RX exposure during TX; compare with the actual receiver input limits.

Measure LO drive at U10 under its actual loading and compare against the mixer's specified operating requirement. Measure transmitter output power and unwanted emissions with calibrated attenuation. Measure receiver sensitivity using the agreed modulation, bandwidth and error criterion. A passive-filter VNA result cannot substitute for these checks.

## Closeout

- [ ] Actual instrument availability recorded.
- [ ] Performance budgets and exact tuning parts resolved.
- [ ] Passive baseline and candidates measured, raw data saved.
- [ ] Amplifier, choke and single-antenna switching qualification completed.
- [ ] Complete TX/RX performance measured against defined requirements.
- [ ] Selected values/MPNs synchronized into schematic and PCB, with native ERC/DRC/net parity rerun.

No component values or PCB geometry changed in this analysis pass. Last verified PCB state remains 0 active errors, 1 accepted header-silkscreen warning and 0 unrouted connections. RF qualification is still open.
