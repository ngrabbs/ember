# Physical gate-clamp model evaluation

2026-10-24. **Nominal development evidence only. BZT52C15-7-F remains the preferred clamp candidate for further validation; no native clamps have been installed and the gate/SOA acceptance gate remains open.**

## Primary source and model integrity

The live [Diodes BZT52C15 page](https://www.diodes.com/part/view/BZT52C15) was read through the in-app browser, exposing the official [model download](https://www.diodes.com/spice/download/783/BZT52C15.spice.txt). This resolves the previous missing-primary-model issue; a secondary repository model was not used. Source hashes are in `sources.json`. The external original remains unchanged and is not redistributed.

LTspice rejects the original standalone hyphen and the `.ENDS` attached to the final model statement. `run_clamp.py` comments only that separator and starts `.ENDS` on a new line. It compares executable tokens before/after and checks both byte hashes. No device, node, numerical parameter or temperature coefficient changes. The original rejection is saved separately. This is an explicitly adapted primary model, not an unmodified-model success claim.

[PCN-2780](https://www.diodes.com/assets/PCN-Files/Diodes_PCN_2780_EOL.pdf), page 3, was actually rendered and inspected: the retired part is `BZT52C15-7-F-79`; `BZT52C15-7-F` is the listed active replacement. The family page's EOL link therefore does not establish discontinuation of the proposed order code. Other PCNs and purchase-time lifecycle checks remain part of sourcing.

TI [SLUA660A](https://www.ti.com/lit/an/slua660a/slua660a.pdf), page 11, was rendered and actually inspected. Its Figure 12 confirms the common-drain FET arrangement, gate resistors, gate-source off resistors and reverse-port transistor roles. It is an older family guide, not authority to replace the R2-specific pin map or component values. Its prose and drawing are not fully consistent on PACK/VCC support; retain the current R2 datasheet as authority.

## Static results and temperature limitation

The adapted model completed 10,001-point DC sweeps at −40, +25 and +85 °C.

| Temperature | Model voltage at 5 mA | Model leakage at 12 V |
|---|---:|---:|
| −40 °C | 14.737 V | 11.3 pA |
| +25 °C | 14.956 V | 21.7 pA |
| +85 °C | 15.155 V | 12.31 nA |

The model's +25-to-+85 °C average slope at 5 mA is only about **3.32 mV/K**. The [Diodes datasheet](https://www.diodes.com/datasheet/download/BZT52Cxx.pdf) lists **9.2–13.0 mV/K at 5 mA**. Thus the model does not establish the temperature behavior required for this design. It also represents nominal leakage, not a production maximum: the datasheet leakage limit is specified at 10.5 V, below the assumed 12 V normal boost. Do not infer guaranteed normal-on charge-pump loading at 12 V from these tiny nominal currents. No electrical parameter was adjusted to force a match.

## Nominal coupled comparison

Two 25 °C finite-transition cases include the real primary-model Q203 reverse transistor, its 1 kΩ gate return to system ground, and a 2 mΩ system-to-raw return shunt. Both use the exact TI main-FET model. The clamp case adds two independent adapted BZT52C15 models, each anode at its own main FET source and cathode at its gate. No shared-source connection or shunt bypass is introduced. Both cases reached the requested 3 ms endpoint.

The source, held 20.526 V drive command, 160 µs imposed delay, 100 µs command ramp, 80 mΩ/1 µH battery feed, snubbers and 1 mΩ fault resistor are sensitivity fixtures inherited from the prior study. The source includes the additional 1 mΩ short-switch resistance. There is still no BQ charge-pump/BAT reservoir model, precharge circuit, fuse, RBF or downstream charger. These are not measured pack bounds or selected fault settings. Convergence warnings remain recorded. The DMN62D2U model's temperature qualification is also limited, so the coupled comparison is kept at 25 °C.

| Result | Without added gate clamps | With two physical-model clamps |
|---|---:|---:|
| Peak DSG VGS | 20.214 V | 14.786 V |
| Peak CHG VGS | 18.912 V | 14.776 V |
| Peak discharge current | 81.84 A | 81.62 A |
| Peak DSG channel power | 725.6 W | 723.9 W |
| Post-fault positive DSG channel energy | 19.79 mJ | 19.95 mJ |
| Peak system-return offset | 163.7 mV | 163.3 mV |

The nominal clamp currents peak near 2.6 mA positive and about 50–55 mA negative, including model displacement/transient behavior. Those values require waveform and physical pulse checks; they are not accepted diode current ratings. The integrated clamp energy is about 2.7 µJ per branch. Nominal pre-fault current is about 22 pA per branch, which cannot substitute for worst-case leakage.

Including Q203 and the shunt removes the earlier large negative gate excursions in this particular fixture. Do not carry those earlier omitted-circuit excursions forward as predictions for the native circuit. The positive DSG excursion above its 20 V limit persists without added clamps. The clamp comparison strengthens the positive-clamp case, but substantial channel stress persists and is a separate SOA issue. No energy-to-avalanche-rating comparison establishes survival.

## Candidate comparison and next action

Nexperia [BZT52H-A18](https://assets.nexperia.com/documents/data-sheet/BZT52H_SER.pdf) offers a tighter 18 V selection and a leakage specification at 12.6 V, above the assumed normal boost. Its +85 °C first-order 5 mA upper screen is 19.14 V, leaving only 0.86 V below the FET limit before overshoot and self-heating. The B selection leaves still less margin. These are conditional temperature extrapolations, not dynamic clamp guarantees.

ST [ESDA14V2L](https://www.st.com/resource/en/datasheet/esdal.pdf) specifies leakage at 12 V and a lower breakdown range, but its 5 µA maximum leakage at 25 °C is a materially larger gate-pump load. Its shared-anode dual structure cannot protect both main FETs with one common return because the main sources differ. Two packages or another topology would be needed. Its primary model URL was found, but the local download failed; no ST model simulation or rendered datasheet inspection is claimed.

Continue with BZT52C15-7-F as the preferred **development candidate**, with two local independent gate/source branches. Before native integration, close its symbol/land identity and define a bounded normal-on leakage/drive margin over temperature. Resolve transient clamp voltage, negative pulse response and actual BQ turn-off behavior with a qualified model or pack-simulator measurements. Then assess the full cutoff trajectory against the MOSFET's temperature-dependent SOA and all BQ sense/power pin limits. This record does not freeze a production BOM, protection timing or flight rating.

Reproduce the DC study with `run_clamp.py --model ORIGINAL_MODEL --output NEW_DIRECTORY`. Reproduce the two coupled cases with `run_coupled.py --clamp-model ORIGINAL_MODEL --fet-model TI_MODEL --reverse-model DMN_MODEL --output NEW_DIRECTORY`. Inputs are hash-checked; run LTspice serially. Logs, complete-endpoint metrics and external raw hashes are saved; model files stay external.
