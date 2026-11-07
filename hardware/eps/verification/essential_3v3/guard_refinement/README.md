# Essential 3V3 filter and fault-source refinement

2026-10-24, basis `490721c`. **A useful development direction, not a selected or integrated protection circuit.** Thirty completed LTspice experiments comprise22 current experiments and8 explicitly superseded fault-fixture diagnostics. All218 tracked native CAD/library/table files are byte-identical to the basis. The integrated EPS remains318 parts/175 nets/866 endpoints/13 sheets.

## What changed the design decision

The earlier10µH/192µF guard rings below3V under the imposed0.2→2A step. Increasing capacitance alone to768µF yields only3.00088V in the nominal model; that is insufficient design margin. The separate470µF/0.22Ω damping branch reaches2.96647V. Smaller inductance and a larger protected bulk bank with low guard resistance provide a better combined direction.

| Imposed guard / protected bank | Other assumptions | Minimum during250ms step |
| --- | --- | ---: |
|10µH /192µF|20mΩ guard,27°C|2.79879V|
|4.7µH /384µF|20mΩ guard,27°C|3.00688V|
|2.2µH /384µF|20mΩ guard,27°C|3.06620V|
|2.2µH /640µF|9mΩ guard,27°C,negative-gate diode|3.10377V|
|2.64µH /640µF|12mΩ guard,85°C model sensitivity|3.08658V|
|2.64µH /640µF|12mΩ guard,22.5mΩ output ESR,85°C|3.09584V|
|2.64µH /640µF|same ESR/resistance,−40°C|3.10616V|
|2.64µH /640µF|27°C,50mΩ source,22.5mΩ output ESR|3.03257V|

All ordinary cases use a3.232799V source and1mΩ source resistance unless stated. These are imposed source impedances, not an LMR51635 loop model. Output ESR can damp ringing; a higher ESR is not automatically the worst minimum-voltage case. Temperature commands exercise the installed models, not guaranteed process/temperature corners of both devices. The 640µF bank is imposed effective capacitance, not an already-qualified BOM.

An independent linear load-step calculation with0.059Ω fitted nominal path resistance agrees with all seven low-source-resistance first-sweep minima within0.258mV. Matrix-exponential and RK4 solutions of that linear model agree within2.4e−11 mixed-state units. This checks the LC mechanism and numerics; the resistance is fitted from the connected model and is not independent MOSFET qualification.

## Actual fault-model finding: negative gate excursion

The corrected finite-source fault fixtures insert a650µF bank precharged to35V through an imposed0.5µH failed-buck inductance and15.9mΩ resistance. A1A replenishing source remains. The good3.324392V source disconnects without being ramped to zero. A synthetic36V-class clamp at the post-guard FET drain uses `Dclamp 0 pin`, with44.2V breakdown/1.35Ω dynamic resistance. Neither its current/temperature behavior nor the0.5µH saturated inductance is guaranteed hardware data.

Without a separate negative-gate clamp, the model drives GATE below−40V and the60V CSD18543 pair reaches approximately62.5V VDS. A low protected-output peak therefore does **not** make that circuit acceptable. These samples exceed device ratings; their exact excursion magnitudes are not predictions of valid device operation.

Adding an imposed low-leakage diode from GND anode to GATE cathode improves that sensitivity. In the2.2µH/640µF case, controller GATE stays above−0.753V, Q1 reaches43.849V VDS, Q2 reaches6.357V, and the protected rail peaks at3.24241V under2A. With load removed before the fault, the protected rail peaks at3.33801V. A1µs versus2µs maximum-step repeat gives the same stored output peak, with8.8mV change in Q1 peak VDS. This is a typical-model observation with an imposed diode model, not acceptance of an exact diode or timing envelope.

The repeat captures18.18mA peak negative-gate clamp current but **308.26A in the failed-buck inductor**. That current invalidates treating the present buck magnetic as a known linear0.5µH element. It is the next architecture gate: evaluate current limiting ahead of the3V3 converter, with all post-limiter input capacitance and turn-on/short-circuit response included. Improving only the downstream LC network leaves this fault-energy path unresolved.

Port-power evidence uses real zero-volt drain-current sensors, not guessed internal model names. In the selected-direction experiment, Q1's positive terminal-energy integral is16.55mJ over0–250ms (including normal conduction), versus1.35µJ over the first fault millisecond. These include capacitive/storage power and are **not dissipated heat or SOA clearance**. Full trajectories, hot linear SOA, repetitive behavior and PCB thermal paths still need checking.

## Concrete part candidates and limits

[Coilcraft XEL6060-222MEC](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xel/xel6060/xel6060-222/) is a2.2µH±20% guard candidate with6.7mΩ maximum DCR at25°C. Its16A saturation reference and13.4A20°C-rise reference are distinct and do not specify the failed-buck magnetic. The9/12mΩ guard assumptions are sensitivities pending actual temperature/thermal and land checks. Registered XEL6060 footprint search returned zero; no custom part was constructed.

[Nichicon PCG0J102MCL1GS](https://www.nichicon.com/en-us/part/pcg0j102mcl1gs/492/) is a concrete1000µF/6.3V/10×8mm bulk candidate. The [PCG catalog](https://www.nichicon.com/getmedia/d303cae0-2fd4-4814-87a5-fb6c18f6da72/e-pcg.pdf) specifies±20% initial capacitance,18mΩ ESR for this code, and an endurance capacitance change within±20% of its defined initial value after restoration to20°C. Thus1000×0.8×0.8=640µF is a20°C bookkeeping sensitivity, **not a guaranteed combined cold/in-service minimum**. The1.25 impedance-temperature ratio is specified at100kHz;22.5mΩ is an imposed ESR sensitivity, not an all-frequency bank guarantee. Leakage, frequency behavior, reflow, radiation, vacuum and actual land/height clearances remain open. Stock `CP_Elec_10x7.7` exists but has not been declared manufacturer-equivalent.

[Nexperia BAS116](https://assets.nexperia.com/documents/data-sheet/BAS116.pdf) is a low-leakage negative-gate clamp candidate (80nA maximum reverse leakage at75V/150°C;1.1V maximum forward drop at50mA/25°C under the listed pulse conditions). The experiment's generic diode is **not** its vendor model and omits recovery. Registered BAS116 search returned zero; stock `Diode:BAV199DW` is another unreviewed search lead, not a substitution. No diode library authorization or construction is implied.

The [TI TPS2663 RevG](https://www.ti.com/lit/ds/symlink/tps2663.pdf) family merits an input-limiter study. Its4.5–60V operating range reaches the present low-input development boundary. Prefer evaluating the1× active-current-limit TPS26630 option before a variant intentionally permitting2× pulse current. A fresh search finds stock `Power_Management:TPS26630RGE` and related parts; no new library is currently needed for that investigation. Exact current/timing/dropout, local stored energy, autonomous recovery, thermal and source interaction remain open.

[ADI LTC4368 RevC](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4368.pdf) still does not establish the proposed complete3.3V drive envelope by interpolation. Its6µs tD(FAST) row uses2.2nF; its separate2µs comparator row specifies12V/50mV overdrive. [TI CSD18543](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf) lists1150pF maximum Ciss per FET at its test point; the sum of these test-point maxima is2.3nF and does not justify treating the actual nonlinear pair as a≤2.2nF controller fixture, before reviewing the real slew network. Do not assert a guaranteed6µs complete opening time for this circuit. CSD gate-leakage/resistance table conditions likewise do not establish hot guarantees. Manufacturer drawing-page pixel review remains open from the earlier library checkpoint; fresh retrieval did not resolve it.

## Evidence and reproduction

`run.py` creates external decks and runs unmodified installed LTC4368-1 and TI CSD18543 models, checking exact model hashes. `initial_sweep_run.py`, `diagnostic_handover_run.py`, `unclamped_gate_run.py` and `gate_clamp_initial_run.py` preserve the precise earlier driver versions. The initial four fault cases reversed the power clamp; four subsequent fault cases used the superseded good-source handover. `results.json` separates these eight diagnostics from22 current experiments. They are not silently relabeled as passed or overwritten. Failed attempts and model limits remain visible.

`decks/` preserves every portable circuit; `logs/` preserves completed logs with only runtime paths normalized. Original raw/model/log hashes are retained. Vendor semiconductor models and large raw files remain external. `archive.py` checks completed original raw data, extracts all-sample extrema and generates interpolated plotting CSVs; it requires NumPy/Matplotlib and the five external run directories. `linear_check.py` runs the independent sanity calculation. `verify.py` checks the portable evidence and native freeze without rerunning LTspice. Example current-case reproduction:

```
python3 run.py --output /absolute/new-run --ti-model-archive /absolute/TI-archive.zip --cases bulk640_esr_hot bulk640_esr_cold bulk640_source50m fault_bulk640_repeat
python3 linear_check.py --output /absolute/new-linear.json
python3 verify.py
```

The root actually opened both `load_comparison.png` and `gate_clamp_comparison.png`. This is inspection of simulation plots, separate from native schematic/PCB/ERC evidence. No new schematic was drawn or rendered; there is no new ERC or PCB-layout acceptance claim. Existing interface names, project settings, libraries, main schematic and board are preserved.

Archived portable decks retain generator whitespace, including trailing blanks from optional `.save` fields, to preserve their recorded hashes. Source scripts, JSON, Markdown and plotting CSVs are checked separately; no source or export is silently reformatted.
