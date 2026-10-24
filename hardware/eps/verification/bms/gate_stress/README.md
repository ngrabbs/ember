# BMS gate/channel stress sensitivity

2026-10-24. **Development diagnostic; gate-clamp selection and MOSFET survival remain OPEN. No native circuit changes.**

The unmodified [TI CSD18543Q3A PSpice model](https://www.ti.com/lit/zip/slpm286), Final 1.00, runs in installed LTspice 26.0.2. Its declared terminals are drain/gate/source = 1/2/3. The external model hash and primary specification links are in `sources.json`; no manufacturer model is redistributed. A preliminary 0.1 V drain DC sweep completed (27 °C default), returning approximately 14.39 mΩ at 4.5 V gate and 10.40 mΩ at 10 V. This is a compatibility check, not measured or guaranteed part resistance.

## Circuit and limits

The test has the two common-drain main FET channels, 5.1 kΩ gate resistors, 10 MΩ gate-source resistors, 50 nF equivalent snubbers across the pair and port, an 8.526 V source with 80 mΩ/1 µH feed, and a 4.263 Ω normal load. The short adds 1 mΩ switch resistance plus a stated 10 mΩ or 1 mΩ fault resistor. These impedances are illustrative, not measured pack/harness bounds. Capacitance and ESR are nominal fixtures.

Both on commands are imposed stiff 20.526 V sources, representing a held BAT reservoir and a 12 V boost screening assumption. This is **not a BQ40Z50-R2 model**: the real BAT diode/reservoir, charge-pump impedance/current limit and supply collapse are absent. The 12 V datasheet entry includes an 18 V BAT test condition; applying it to this 2S transient is a stress assumption, not a guaranteed 2S waveform. CHG remains commanded on. DSG changes toward PACK + 0.4 V after an imposed 160 µs or 500 µs delay. These are sensitivity values, not selected protection settings or complete device timing bounds.

The `abrupt` profile changes the driver instantaneously. The `slewed_gear` profile adds a 100 µs command transition and Gear integration; this is an explicit different fixture, not a repair to TI's model or a fitted BQ driver. Device gate fall time is not the same as this command ramp. Model convergence warnings remain in the logs even when the requested endpoint is reached.

The optional clamp is a **hypothetical behavioral branch**, 16.38 V positive knee with 30 Ω slope, 0.9 V negative knee with 2 Ω slope, and 100 pF at each gate/source. It is not a BZT52C15 model, a tolerance envelope or guaranteed performance. The actual Q203 reverse-port transistor, precharge circuit, shunt/reference offset, separate BQ pin dynamics, cell chemistry, pack fuse, RBF and downstream charger are not included. This matrix cannot establish their interactions or complete fault containment. No gate-oxide destruction or self-heating model is present: traces beyond absolute ratings are outside an acceptable operating region, not predictions that the FET survives there.

## Results

Eighteen matrix cases were attempted. Six abrupt cases failed convergence or left incomplete binary output; their results are rejected. Two abrupt hot clamped cases reached 3 ms. All eight finite-transition cases and both lower-resistance short cases reached 3 ms. Repeated solver-warning text in failed logs is abbreviated with the original full log hash retained; failed binary files remain external and are not acceptance evidence.

| Finite-transition case | Unclamped DSG peak VGS | Hypothetical-clamped peak VGS | Peak discharge with clamp | DSG positive energy after fault, with clamp |
|---|---:|---:|---:|---:|
| 25 °C, 160 µs, 10 mΩ fault | 19.763 V | 16.403 V | 76.43 A | 17.53 mJ |
| 85 °C, 160 µs, 10 mΩ fault | 19.784 V | 16.403 V | 74.33 A | 20.16 mJ |
| 85 °C, 500 µs, 10 mΩ fault | 19.784 V | 16.403 V | 74.33 A | 43.80 mJ |
| 25 °C, 160 µs, 1 mΩ fault | 20.362 V | 16.404 V | 83.39 A | 20.69 mJ |

The lower-resistance unclamped fixture also produces large negative gate/source excursions (about −41 V DSG and −48 V CHG). Treat these as reasons to examine local negative clamping and inductive/driver behavior, not as trusted hardware waveforms: the fixture omissions, convergence warnings and absent gate breakdown matter. In the completed finite-transition clamped cases, peak DSG channel power remains roughly 599–747 W despite the lower VGS. A gate clamp addresses a different stress from channel heating.

The [TI datasheet](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf), SLPS633, p6, Figures 10–12, was rendered and actually inspected. Its single-pulse SOA, avalanche curves and case-temperature current graph are different limits. Integrated channel energy must **not** be compared directly with the 55 mJ single-avalanche rating, and these simulations do not establish an SOA pass. Electronics ambient screening at +85 °C also does not define actual FET case or junction temperature.

## Next design action

Continue with local positive/negative gate protection for both main FETs, while verifying real clamp leakage at normal boost, charge-pump loading, capacitance and turn-off behavior. Obtain a primary clamp model or characterize it; do not substitute a secondary-source model as manufacturer evidence. Then include Q203, the BAT supply/reservoir, shunt/reference motion and bounded pack/harness/source impedances in a coherent fault model. Select protection thresholds/delays together with current and SOA limits. Check actual gate, drain, sense and BQ pin waveforms on a current-limited pack simulator before hardware acceptance. A new clamp component is not yet selected or installed.

Reproduce serially with the bundled Python and external model:

```sh
python3 run_screen.py --model /absolute/CSD18543Q3A.LIB --output /new/abrupt-run
python3 run_screen.py --model /absolute/CSD18543Q3A.LIB --output /new/slewed-run --profile slewed_gear
python3 run_screen.py --model /absolute/CSD18543Q3A.LIB --output /new/short-run --profile slewed_gear --fault-milliohm 1 --only-temp 25 --only-delay 160u
```

Run only one LTspice batch at a time; exit code zero alone is insufficient. The runner requires a complete 3 ms binary endpoint and saves failed cases separately from completed results. Raw/executed deck hashes identify external run artifacts; portable decks and normalized logs are committed.
