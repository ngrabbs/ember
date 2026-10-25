# RBF source-boundary inventory and model disposition

2026-10-24. **Read-only engineering evidence. No source-cutoff circuit or contact assembly is selected, and no native CAD changes were made.** This refines the next integration boundary against the current 275-part graph; it does not close RBF, MOSFET survival or flight acceptance.

## Capacitor stages in the actual graph

[inventory.py](inventory.py) reads the exported isolated-BMS checkpoint and asserts each capacitor's two terminals, initial tolerance and exact MPN. [inventory.json](inventory.json) records its source hash and all member pins. Reproduce with `python3 hardware/eps/verification/interlocks/source_boundary_2026_10_24/inventory.py` from the repository root.

| Stage | Nominal µF | Initial-tolerance upper µF | Connection relevant to cutoff |
| --- | ---: | ---: | --- |
| BATT_PERMITTED | 20 | 22 | C304/C305, directly after the missing battery cutoff |
| SYS_PWR_PERMITTED | 142.7 | 163.77 | Behind charger battery/input PowerPath; includes converter input banks |
| VIN_CHG | 98.1 | 114.71 | Behind source protection, before charger input PowerPath |
| SRC_BIAS | 8.8 | 9.68 | Source-protection bias through its diode/resistor feed |
| SRC_SNUB | 8.8 | 9.68 | Behind R612, 1 Ω, on SRC_FILTERED after L600 |

The earlier battery fixture's 142.7 µF matches the present **system bank only**. It excludes the direct 20 µF battery bank. An illustrative sum of both is 162.7 µF nominal / 185.77 µF at initial tolerance upper, storing 5.914 / 6.752 mJ at the old 8.526 V study point. These are separate nodes joined by the charger BATFET, not an instruction to put one capacitor at its drain.

The four listed solar-side stages sum to 258.4 µF nominal / 297.84 µF at initial tolerance upper. If all were charged to an illustrative 35 V, their stored energy would be 0.15827 / 0.182427 J. This is a bookkeeping sensitivity, **not** their actual simultaneous startup voltage or MOSFET dissipation. The old 390.8 µF solar fixture is not the current graph's stage-by-stage model.

Retain L600, R612, the bias feed, source-protector FETs and charger PowerPath in the next startup model. Do not include regulated 3.3 V/5 V output banks by simply adding their microfarads at the input; their energy/current appears through converter startup and load behavior. Bias, temperature, ageing, ESR/ESL, wiring, active load, fault current and repeated-start bounds remain open. Initial tolerance upper is not a guaranteed all-condition capacitance maximum. Stored energy alone is not an SOA criterion.

## Three additional passive-model failures

[Failure records](failed_runs.json) preserve exact model, deck, raw and full-log hashes. Each process was terminated at its 45 s bound and has no completed-log marker. Original large logs/raws and models remain outside Git at the recorded paths. Portable decks preserve each tested circuit with an external model-path token.

| Fixture | Change from the earlier passive battery test | Last complete logged solver position |
| --- | --- | ---: |
| SUD common-source anchor | Add a real 1 MΩ common-source-to-ground resistor | approximately 50.056 ms |
| SQD common-source anchor | Same fixture, exact unmodified SQD50P08-25L_PS manufacturer macro | approximately 50.045 ms |
| SQD split gates/source capacitor | Add 100 Ω in each gate and 1 µF/1 Ω ESR common-source capacitance | approximately 261.473 ms |

The split-gate case progressed beyond the command's 200 ms release, but it still did not finish the 300 ms analysis. No extrema, cutoff time, inrush or SOA are accepted from any of these partial files. Neither changing the device nor adding damping has yet produced a usable complete passive-pair transient. The model failures do not prove that the physical circuit fails.

The SQD alternative has an official [Vishay datasheet](https://www.vishay.com/docs/72217/sqd50p08.pdf), Rev B, 30-Jul-2012: exact SQD50P08-25L-GE3, 80 V P-channel, ±20 V gate rating, maximum 31 mΩ at −4.5 V and 25 °C. This is a research candidate, not an accepted package, procurement decision, hot SOA or guaranteed drive at the depleted-pack terminal. No authoritative SUD end-of-life determination was obtained; no lifecycle claim is made.

## Contact candidate, with a concrete hold point

The [Honeywell ZX manufacturer document](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/switches/basic-switches/subminiature-basic-switches/zx-series/documents/sps-siot-micro-switch-zx-basic-product-sheet-004990-2-en-ciid-151139.pdf), Issue 3 / 004990, was inspected at actual pages 2–4. [Source hashes](sources.json) and the three page renders are retained. Page 2 decodes ZX10 as gold-plated contacts, C as 90 gf maximum pin-plunger force, 10 as straight solder terminals, A as pin plunger and 01 as SPDT. Page 4 explicitly lists **ZX10C10A01**. This makes it a concrete remote-harness candidate, rather than an invented combination of ordering codes.

Page 3 lists 0.1 A / 48 Vdc and 0.2 A / 60 Vdc for ZX10, and manufacturer operation −40 to +85 °C; the separate agency use-temperature note is 0 to +55 °C. These maximum ratings do not establish reliable switching at the gate network's microampere-to-milliampere load. The actual rendered table prints “100 Ohm max.” for switch resistance and “100 Ohm min.” for insulation resistance. Those implausible entries are a manufacturer-document ambiguity; **do not silently reinterpret them as mΩ/MΩ or use them as accepted limits**. Obtain the exact engineering drawing/contact specification and minimum-load guidance before circuit or procurement acceptance. A 60 V contact rating also does not cover arbitrary overshoot beyond 60 V.

Keep independent battery and solar dry-contact loops. A possible remote assembly uses two separately wired NC contacts per mechanical inhibit, so pressing the actuator opens both permission loops and an unplugged series harness inhibits power. Pole count, force/travel/overtravel, mounting and positive actuation, bounce, contamination, faulted harness behavior and thermal/vacuum suitability still require review. Two switches actuated by one mechanism do not establish independent hazard inhibits. No exact assembly, connector pinout, bracket or dispenser compatibility is selected here.

## Next circuit decision

Preserve the passive common-source pair as an unresolved candidate rather than integrating it on partial model evidence. The completed LTC4367 experiments remain separate evidence. Its VOUT pin participates in charge-pump power when sufficiently positive, so sensing the energized common-source node needs explicit retained-power/partial-power analysis when VIN is removed by the permission contact; it cannot be assumed to preserve the BMS-only retained-power boundary.

The next useful closure is a full circuit with stage-resolved startup, either a supported passive-device simulation or a properly bounded controller architecture, plus exact contact requirements and hot linear SOA. Continue independent EPS blocks while that boundary remains open. Electrical simulation and actual page inspection remain separate: this checkpoint inspects manufacturer pages, not new EPS schematic pages; the existing 11-sheet native graph is unchanged.

## Subsequent evidence

The [retained-power screen](../retained_power_2026_10_24/README.md) refines the LTC4367 concern with eight completed cases, explicit common-source/bias bleeds, two battery-side capacitor nodes and an independent check against the current305-part graph. It distinguishes the N-channel body-diode direction from the earlier passive P-channel candidate. It does not select a circuit, establish all-condition leakage, replace the charger with a qualified model, or close hot SOA. This original inventory and its275-part source hash remain historical evidence and are not rewritten.
