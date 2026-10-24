# LT3014 isolated BMS post-regulator screen

2026-10-24. **Development selection evidence; not an integrated EPS or hardware acceptance result.** The prior TLV767/5.5 V screen remains historical. The preferred candidate is now permitted essential +3V3 → UCC33020RAQR in **5.0 V mode, SEL=VCC** → LT3014IS5#TRPBF → `3V3_BMS_ISO`, with all secondary returns on GND_BMS_RAW. Only ISO1540 side 2 and its two pullups use that output. Neither raw-cell power nor a conductor across the current shunt is added.

## Selection and static checks

The [LT3014 Rev D datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/3014fd.pdf) explicitly protects an output held up with its input grounded, intermediate or open, independently of SHDN. This removes the TLV767-specific need to qualify an external reverse-discharge diode. It does not make reverse leakage zero: the 4 µA maximum is specified at 25°C and VOUT=ADJ=1.22 V, and cannot be transferred to the 3.3 V/full-temperature application. I-grade is selected for the stated full −40 to +125°C guarantee, rather than relying on E-grade characterization assurance. The project's component-screening range remains −40 to +85°C; battery/environmental qualification remains open.

Run `python3 calculate.py` for the conditional DC calculations in [calculated.json](calculated.json). Top/bottom feedback resistors are 16.9 kΩ / 10.0 kΩ, 0.1%, 25 ppm/K. The full-range 1.18–1.26 V ADJ specification and independent ±0.2625% resistor excursion give approximately **3.164–3.401 V**; the upper value includes a 10 nA **25°C-only** bias-current sensitivity, not a full-temperature bias guarantee. Do not add the line/load maxima a second time to an accuracy row already spanning input and load. The divider draws at least 117.7 µA, meeting the 100 µA minimum electrical-table load without the TLV candidate's separate 3 kΩ bleeder. This leaves about 164 mV above ISO1540's operating minimum, and keeps the screened healthy supply within the 3–3.6 V window used for its current budget.

All-low ISO side-2 IC maximum, two pullups pessimistically pulled to zero and the divider total about 8.575 mA. Allocate 12 mA output provisionally and 1 mA regulator ground current using the larger 20 mA test-point maximum as a conservative lower-current budget assumption. The isolated stage allocation is then 13 mA / 67.6 mW at 5.2 V; LDO loss is approximately 29.6 mW at the screened corners. The 20 mA maximum dropout bound of 570 mV leaves about **829 mV** from a 4.8 V input after the output upper corner. This supports using the UCC's numerically specified 5 V mode instead of relying on a 5.5 V power-rating inference. The UCC 0.5 W table still covers only 25–85°C, so cold operation and complete startup remain gates.

Provisional feedback MPNs follow the already used Vishay TNPW0603 ordering convention: TNPW060316K9BEEA / TNPW060310K0BEEA, 0.1%, 25 ppm/K, general-mode P70=0.11 W subject to derating. Procurement/order confirmation remains open. The stock device pin/package/disposable review is recorded separately in [LT3014 candidate evidence](../lt3014_candidate/README.md). Source figures were actually inspected by the design owner; native fixture rendering is a separate gate from this analysis.

## Nominal model diagnostics

The model is the installed, unmodified ADI/Linear Technology `LT3014.lib` used by LTspice, SHA-256 `9757f56b9c8372a738c1e1cad8c36ac95318260c4bac1b6d3be75b045693c337`. It is not redistributed. [run_screen.py](run_screen.py) checks that hash, writes portable decks using `${LDO_MODEL}`, executes each case serially with a 45 s timeout, requires the completion log and checks that the raw trace reaches 120 ms. The model's eight **simulation** ports are OUT/ADJ/NC/GND/SHDN/NC/NC/IN; these are not the five physical lead numbers. Several model transistors are fixed at 27°C. A `.temp` sweep would not establish PVT qualification.

All five cases completed. They impose a 0→4.8 V, 1 ms source ramp, 3.5→8.5→3.5 mA synthetic load transitions in 1 µs, source collapse at 60 ms and restart at 80 ms. Load current is reduced below 3 V to avoid an unphysical constant-current sink driving an unpowered output negative. This is **not** an ISO1540 startup or UCC converter model.

| Effective output C / case | Minimum during rising load step | Maximum in active interval |
|---|---:|---:|
| 1 µF | 3.2428 V | 3.3248 V |
| 4.7 µF | 3.2609 V | 3.3091 V |
| 10 µF | 3.2662 V | 3.3044 V |
| 10 µF, initial-condition prebias | 3.2662 V | 3.3044 V |
| 10 µF, finite external prebias ramp | 3.2662 V | 3.3044 V |

The initial-condition case forces the output capacitor to 3.4 V at t=0 while model internal capacitances start uncharged. It produces a **−1.55 A model input impulse at ~20 ps**, with about 0.28 nC reverse charge in the first 10 ns. Retain this result; it is not evidence of a hardware ampere-scale reverse path or an accepted reverse-current limit. A separate finite-ramp case biases the output to about 3.396 V through a 1 Ω source before disconnecting it and ramping the input. Its first-5-ms modeled input minimum is about −5.2 µA. After imposed input collapse the model shows short current excursions of about −17.2 µA; do not relabel this as a datasheet maximum. The input monitor is separated from the 22 µF reservoir discharge so the capacitor's forced current is not mistaken for LDO reverse conduction.

The finite-prebias case dips below 3 V briefly while the external bias is removed before input startup. That interval is **not valid BMS communication**. Firmware must wait for supply settling, recover the bus and validate BMS identity/configuration as already required by the interface contract. Model restart success does not establish service continuity through shutdown.

[results.json](results.json), portable decks, normalized completion logs and decimated CSV traces are retained. Full raw data remain in `/tmp/ember-lt3014-screen-20261024-v3` with hashes in the results. [waveforms.pdf](waveforms.pdf) was plotted with ReportLab; all four rendered pages were actually opened and inspected, including startup/restart, rising/falling load transitions and finite prebias. Plot review and simulator numerical completion are separate from native schematic review.

## Remaining integration gates

Exact effective output capacitors (target ≥4.7 µF over bias/tolerance/temperature), UCC input/output capacitor network, essential-rail loaded current/inrush, cold UCC operation, repeated UVLO/prebiased converter restart, electrical full-temperature bias/leakage limits, circuit-fault containment, thermal/EMC and actual bus waveforms remain open. A 1 µF nominal model run is a sensitivity and does not replace the larger development capacitance target. No UCC custom library or real EPS circuit is authorized by this record. Its separate construction approval is still pending. The real EPS stays at 243 parts / 137 nets and the shunt measurement error remains unresolved until the isolated circuit is integrated and checked.
