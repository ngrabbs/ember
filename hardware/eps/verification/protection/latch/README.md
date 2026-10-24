# Latch correction and MOSFET survival evidence

2026-10-23. Current [design decisions, limitations and physical test contract](../../../design/rev_b_5v_latch_and_mosfet_survival.md). This supersedes the prior protection/bank timer-only candidate discussion. The native circuit has a 330 Ω bleeder, 100 nF rail timer, 10 nF rail gate-slew cap, 3.57 kΩ / 1.11 kΩ rail FB divider, 10 nF source timer and XAL1010 source slew inductor. **Development screening is not hot-SOA qualification.**

- [Rail cases](cases.json), [generator](run_latch.py), [rail results and hashes](evidence/results.json).
- [Source cases](source_cases.json), [generator](run_source.py), [source results and hashes](evidence/source_results.json).
- [Independent voltage/current/thermal extraction](check_survival.py), [survival results](evidence/survival.json).
- [Release voltage minima and final timer discharge](evidence/release_minima.json).
- [Numerical table](evidence/results.md), [waveforms](evidence/waveforms.png), [plot script](plot_results.py).
- [Native connectivity/BOM/ERC and actual rendered-sheet evidence](native/README.md).
- [Exploratory rejected records](evidence/rejected.json) retain earlier failures. Exact deck/raw hashes are authoritative for those historical fixtures; the final generators include subsequent fixture corrections.

The `accepted_` rail-case prefix identifies the selected **development** topology, not accepted flight hardware. All source cases with `guard_` include the installed source inductor. Unguarded source cases are comparisons; the hard input short must fail output and internal-gate checks. Abrupt repeated 2 A load cycling must fail the separate 4.75 V undershoot check while avoiding latch-off. These expected rejections are not silently counted as functioning hardware.

The longer cold no-load cases require both recovery and final timer discharge. This catches a latent latch that short output-only checks missed. The final 5.270 V divider balances healthy-regulator margin against the high-trip provisional 5.5 V output ceiling. Equivalent timing capacitances inject stated rate sensitivities; they are not native extra parts. The regulator emulator's shunt-drop correction has finite 1 kHz bandwidth to avoid an artificial negative-damping path; it does not qualify TPS552872 loop/startup behavior.

Run LTspice **serially**; the macOS batch application shares one process/runtime:

```sh
python3 hardware/eps/verification/protection/latch/run_latch.py --work /absolute/scratch/latch-checks
python3 hardware/eps/verification/protection/latch/run_source.py --work /absolute/scratch/source-timer-checks
python3 hardware/eps/verification/protection/latch/check_survival.py --rail-work /absolute/scratch/latch-checks --source-work /absolute/scratch/source-timer-checks
python3 hardware/eps/verification/protection/latch/native/verify_native.py
python3 hardware/eps/verification/protection/latch/native/verify_geometry.py
```

Python/numpy, LTspice 26.0.2 and its installed ADI/IRLR2908 models are required. Plotting additionally requires matplotlib. Vendor encrypted models and raw waveforms remain outside Git; generated deck/raw/model hashes record provenance. Native exports and electrical-versus-visual evidence are separate from SPICE. No bench test was run.

Controlled-load fixtures require both 5 ms ramps and 20 ms settling intervals; their floor check includes the first transition. Faster re-admission remains unqualified.
