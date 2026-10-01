# RF component-model follow-up — 2026-09-09

**Outcome:** the Coilcraft model strengthens the case for tuning the filters below their current 9.1 pF shunt value. **7.5 pF is the preferred next test candidate**, with 8.2 pF retained as an intermediate option. Neither value has been applied to the schematic, PCB or purchasing fields. No new commit or push was made.

## What changed in the analysis

Inspected both pages of Coilcraft Document 158, revised 2026-04-29, including the circuit diagram and 0402HP-10N row. Replaced the ideal 10 nH model with the manufacturer's frequency-dependent equivalent circuit:

`Z = R2 + ((Rvar + jωL) || (R1 + 1/(jωC)))`, with `Rvar = k√f`.

Parameters are R1=4 Ω, R2=0.085 Ω, C=0.051 pF, L=10 nH, k=2.57×10⁻⁵ (f in Hz). At 435 MHz this gives approximately 0.625+j27.436 Ω, or Q≈43.9. The model topology and row were visually checked; the passive response was numerically checked across all four filter sweeps. These are typical component-model results, not guaranteed production limits. [Coilcraft model source](https://www.coilcraft.com/pdfs/spice_0402hp.pdf)

The routed-line network, 50 Ω source/load assumptions and component-terminal approximation are unchanged from the previous review. The model still excludes active-device loading, RF bias branches, coupling and an electromagnetic extraction of the PCB.

## Current values with the manufacturer inductor model

| Filter | Insertion loss at 435 MHz | Insertion loss at 437 MHz | Input return loss at 437 MHz |
|---|---:|---:|---:|
| RX input | 2.16 dB | 2.29 dB | 10.90 dB |
| TX preselector | 2.36 dB | 2.53 dB | 9.45 dB |
| TX output | 2.45 dB | 2.63 dB | 8.45 dB |
| RX LO | 2.17 dB | 2.30 dB | 10.48 dB |

These calculations use ideal capacitors and ground connections; they should not be mistaken for complete board predictions. RX loss before the LNA matters directly to the noise/sensitivity budget. Loss in the LO filter also needs to be included when checking actual drive at the mixer.

## Candidate values and uncertainty

Compared 9.1, 8.2 and 7.5 pF for both shunt capacitors in each filter, keeping the 10 nH inductors, 1.6 pF coupling and 3.9 pF end capacitors unchanged. The study uses four explicit assumptions:

| Scenario | Added capacitance per signal pad | Ground inductance per shunt branch | Capacitor ESL | Capacitor ESR |
|---|---:|---:|---:|---:|
| Manufacturer inductor only | 0 | 0 | 0 | 0 |
| Low parasitics | 0.03 pF | 0.1 nH | 0.1 nH | 0.03 Ω |
| Mid parasitics | 0.07 pF | 0.3 nH | 0.25 nH | 0.08 Ω |
| High parasitics | 0.12 pF | 0.6 nH | 0.4 nH | 0.15 Ω |

**These are illustrative sensitivity cases, not extracted board parameters, verified capacitor models, tolerance limits or statistical confidence bounds.** Ground branches are modeled independently; shared via inductance and mutual coupling are omitted. Effective dielectric constant remains an estimate of 3.3. No Monte Carlo yield claim is made.

Across those cases, calculated TX output-filter insertion loss at 437 MHz spans:

| Shunt value | Calculated range across cases |
|---|---:|
| Current 9.1 pF | 2.63–8.61 dB |
| Candidate 8.2 pF | 1.67–4.80 dB |
| Candidate 7.5 pF | 1.56–2.66 dB |

The 7.5 pF candidate also improves the other three filters across this study. It does not meet a proven worst-case acceptance criterion: for example the TX output filter's return loss still falls below 10 dB in the high-parasitic case. The ranges are deliberately not presented as expected actual-board performance.

## Exact tuning targets

| Filter | Change together during controlled tuning | Baseline | Candidate sequence |
|---|---|---:|---|
| RX input | C56, C64 | 9.1 pF | 8.2 pF, 7.5 pF |
| TX preselector | C96, C100 | 9.1 pF | 8.2 pF, 7.5 pF |
| TX output | C87, C92 | 9.1 pF | 8.2 pF, 7.5 pF |
| RX LO | C90, C95 | 9.1 pF | 8.2 pF, 7.5 pF |

Keep the baseline data before changing anything. Compare both input/output return loss and insertion loss across the intended band. A measured improvement is the basis for updating the default values and exact orderable parts in both schematic and PCB.

## Component-model gaps

The 3.9 pF ordering code resolves to FH **0402CG3R9C500NT**, and the 1.6 pF code resolves to Murata **GJM1555C1H1R6BB01D**. These supplier records establish purchasing identity, not their RF equivalent circuits. [FH ordering record](https://www.lcsc.com/product-detail/C1566.html), [Murata ordering record](https://www.lcsc.com/product-image/C161311.html).

A verified RF model for those exact capacitors has not been acquired. The exact 9.1 pF part behind C526972 could not be independently resolved in this pass; retain that as a procurement/model-data gap, not proof that the code is wrong. Do not reuse its ordering code for 7.5 or 8.2 pF.

L16 remains the previously selected **0805HP-221XJRC** prototype choke. Its exact frequency-dependent model under bias has not been obtained. This pass models the **10 nH filter inductors**, not L16. Its old >1.5 GHz SRF target and assembled isolation/stability qualification remain open.

## Measurement sequence

1. Characterize the passive filters before installing adjacent active parts, or otherwise isolate their ports. Keep the filter's own 3.9 pF end capacitors installed. Calibration/de-embedding must account for temporary coax/probe launches and lead lengths.
2. For RX input, omit U11/U9 during the isolated-filter measurement. For TX output, omit U8/U11 and L15 so the PA bias branch cannot load the input port. For TX preselector, also isolate the tripler's collector/bias/tank branches (Q3/L17/C81) and PA input. For LO, isolate Q4/L18/C85 and U10. Review the actual assembly state before removing anything; these are staged measurement configurations, not permanent DNP instructions.
3. Record S11, S21 and S22 for the 9.1 pF baseline and each candidate, including 435 and 437 MHz. Save raw Touchstone files with the assembly configuration and calibration plane. Choose final values against the agreed bandwidth, loss, return-loss and rejection budgets.
4. Restore the amplifier, switch and bias networks. Check supply current, gain, stability and RF leakage on supply nodes; then check mixer LO drive and complete transmitter spectrum. Use DC blocking and attenuation appropriate to the instruments and powered output levels.
5. Update the exact BOM entries and default schematic/PCB values only after corroboration, and rerun electrical/layout checks. Hardware acceptance cannot be completed using KiCad checks alone.

Available test equipment is still to be confirmed; this sequence can be adapted for a NanoVNA/VNA and whichever powered-RF instruments are available.

## Saved state and reproducibility

No KiCad source files were changed in this follow-up. The saved board retains the previous verified **0 errors, 1 intentional header-silkscreen warning, 0 unrouted connections**, with 181 nets matching. Those geometry checks were not rerun for an analysis-only change.

`rf_filter_vendor.py` accepts an exported inventory, output directory and optional JSON settings. `rf_vendor_model_validation.json` contains all 12 sensitivity cases and model checks. The paired 435/437 MHz runs report only the peak among sampled points, not a swept resonance frequency. See `rf_vendor_scenarios.json` for the exact scenario inputs.

**RF acceptance remains INCOMPLETE.** We now have a specific tuning hypothesis and measurement sequence, rather than sufficient evidence to approve a component-value change or fabrication release.
