# 50 V converter bank and coupled-protection follow-up

2026-10-23. Development checkpoint; not a fabrication release. The previous protection study exposed overvoltage of the converter's own output capacitors. That bank is now corrected in the native converter schematic. This record supersedes earlier bank-specific calculations, BOMs and images; the independent protection study itself remains unchanged.

## Installed bank

Five Panasonic EEHZA1H680P (68 µF / 50 V, F land) and eight TDK CGA5L1X7R1H106K160AC (10 µF / 50 V, 1206) replace the 35 V hybrids and 25 V ceramics. C16 stays 100 nF / 50 V. All thirteen positive terminals remain on `5V0_RECOVERY_RAW` before converter R4; negative terminals are GND. The [native report, current BOM and actual renders](native/README.md) record 34 physical parts, 16 functional plus 3 NC endpoint sets, CLI ERC 0 errors / 0 warnings, and unchanged PCB. Electrical verification and rendered-sheet inspection are separate evidence. S03 severity persistence and S11 presentation remain API-blocked.

The 420 µF nominal bank reaches 496 µF at initial high tolerance. Applying Panasonic's +30% endurance change to the +20% bulk tolerance gives 530.4 µF bulk, hence **618.4 µF plus C16**. Use a **650 µF development allocation**, pending actual temperature/bias/endurance acceptance. Applying the −30% endurance change and −20% initial bulk tolerance gives 190.4 µF at the specified measurement condition; the modeled 160 µF minimum leaves a further factor of 0.8403 for temperature. That factor is an acceptance requirement, not manufacturer proof of cold capacitance.

At 5.08 V / 2.5 ms, 650 µF needs 1.321 A; adding the 0.5 A startup allocation gives 1.821 A versus the 2.369 A slow-limit sensitivity. Charging the 623.2 µF downstream high-capacitance sensitivity simultaneously would instead need about 3.087 A including the load. Preserve staged downstream slew. The finite-current startup fixture passes, but it is not a TPS552872 switching/startup model.

## Reproducible transient evidence

[Generator](run_bank_checks.py), [cases](cases.json) and [numerical table](evidence/results.md) and [results/model/deck/raw hashes](evidence/results.json) extend the historical protection generator without changing it. LTspice 26.0.2 uses the locally installed ADI encrypted controller and typical IRLR2908 models; vendor files/raw waveforms are not redistributed. The model includes individual upstream capacitor branches, converter R4, the guard inductor and protected bank. Healthy regulation senses after R4; a failed converter cannot regulate. A second bridge placement bypasses R4. These are explicit fault fixtures, not arbitrary-source containment guarantees.

Run serially with Python/numpy and an installed LTspice library:

```sh
python3 hardware/eps/verification/protection/bank/run_bank_checks.py --work /absolute/scratch/directory
python3 hardware/eps/verification/protection/bank/analyze_impedance.py
python3 hardware/eps/verification/protection/bank/native/verify_bank.py
```

The upstream minimum-bank bridge reaches approximately **35.863 V**, below the new 50 V capacitor ratings; the slow-gate sensitivity is approximately 35.864 V. Finite 330 µF reservoir and shunt-bypass fixtures are also recorded. External drain/gate and provisional 5.5 V output checks pass for those fixtures. This does not establish capacitor pulse endurance, shunt survival or a guaranteed all-temperature voltage bound.

**New acceptance failure:** with the low-reference sensitivity and a 2 A to zero load release, the current 220 pF rail timer latches off; final output is about 4.570 V rather than recovering. The no-load case cannot assume the 0.5 A startup *upper allocation* is a minimum bleed load. This single case is explicitly an expected rejection in the harness: reproducing the failure does not accept the circuit.

Analysis-only discharge/timer candidates are retained in the cases/results. Both 100 Ω and 330 Ω bleeders prevent the tested latch with 10 nF timers; they draw approximately 0.25 W / 50 mA and 0.076 W / 15 mA respectively at 5 V. The longer 100 nF and 330 nF timer variants also pass that release but raise modeled total pass-bank fault energy to about 56 mJ and 175 mJ. The 100 Ω / 10 nF case reduces it to about 10.2 mJ; the 330 Ω / 10 nF case is about 9.74 mJ. **No bleeder or timer change is installed in the native protection study.** Shorter-timer candidates require startup/reset, output short, capacitance, threshold, component-tolerance and hot sharing/SOA checks before native selection. Model gate-pull/gate-charge behavior is typical, not a worst-case turn-off guarantee.

## Averaged impedance sensitivity

[Analysis](analyze_impedance.py) and [31,104 coupled cases plus 1,728 converter-only cases](evidence/impedance.json) include explicit capacitor ESR/ESL and series guard impedance. The extension retains TI's approximate output damping through an additional DC conductance; it is a development sensitivity model, not a validated multistage control model. Estimated minimum unity-crossing phase margin is 58.01° converter-only and 45.79° with the barrier. There are 140 coupled cases with multiple/rising unity crossings; minimum sampled `|1+L|` is 0.476. Multiple crossings alone do not establish instability or acceptance.

Analytic polynomial roots are saved for flagged cases. Some combinations produce positive roots at hundreds of MHz, far beyond this current-mode/RHP-zero approximation's useful bandwidth. These cannot be used as physical stability predictions or silently discarded to claim closed-loop qualification. The frequency model excludes switching/PFM, transition, constant-power receivers and nonlinear clamps. Preserve the existing 3.74 kΩ / 75 nF / 300 pF compensation pending a validated coupled model and bench impedance/load-step measurements.

## Physical acceptance still open

- Panasonic's 0.4 Ω per-part cold ESR limit is specified at 100 kHz after endurance; five parallel parts give 0.08 Ω at that condition. The loop calculation's frequency-independent ESR is only a sensitivity.
- TDK bias/temperature/aging minima and Panasonic all-temperature capacitance maxima/minima remain unaccepted; the 650 µF allocation is not a manufacturer maximum over every condition.
- Added capacitor area, leakage, ripple/pulse endurance, PCB fit and thermal behavior need acceptance. The 10.2 mm nominal hybrid height fits under the stated 16 mm standoff only before assembly/vent/opposing-board clearances are accounted for.
- IRLR2908 hot linear SOA/current sharing, reverse-body pulses, shunt pulse limits, TVS dynamics and guaranteed guard inductance through the modeled fault current remain open. A thermal convolution or typical model is not MOSFET survival proof.
- Low-VCC LTC4364 FB accuracy, consumer voltage/time limits, real source impedance/energy, coupled loop/startup and limited-energy bench faults remain required. Neither schematic is integrated into a flight EPS PCB.

Primary bank data: [Panasonic exact part](https://industrial.panasonic.com/ww/products/pt/hybrid-aluminum/models/EEHZA1H680P), [ZA series data, 2025-09-01](https://industrial.panasonic.com/cdbs/www-data/pdf/RDD0000/ABA0000C1221.pdf), [TDK exact part](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=CGA5L1X7R1H106K160AC), [TDK reference characteristics](https://product.tdk.com/info/en/documents/chara_sheet/CGA5L1X7R1H106K160AC.pdf). Reference graphs are not guaranteed bias minima; no inaccessible TDK graph is claimed as visually inspected.
