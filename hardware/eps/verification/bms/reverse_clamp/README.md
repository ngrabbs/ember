# BMS reverse-connection clamp screening

2026-10-24. **Development selection: DMN62D2U-7 with a 1 kΩ gate-to-system-ground resistor. Full reverse-fault protection is not yet accepted.** The native package gate is recorded separately in the BMS integration checkpoint. This study makes no KiCad mutations.

## Topology and source

The root reviewer and schematic owner independently inspected a high-resolution crop of TI BQ40Z50-R2 SLUSCS4C Figure 9-13, printed page 38. Q4's source (lead 2) connects to PACK+, drain (lead 3) to the main DSG FET gate, and gate (lead 1) through a resistor to CHGND, the system return. Its body diode points from PACK+ toward the main DSG gate. **Do not reverse drain and source.** Normal BQ off-state drive is specified relative to PACK+, not system ground; §7.18 specifies ±0.4 V. The small grounded-gate NMOS begins pulling the DSG gate toward its source when the pack port becomes negative. No added raw-cell LDO or positive gate-bias supply is used.

[Diodes DMN62D2U DS44892 Rev 3, March 2025](https://www.diodes.com/datasheet/download/DMN62D2U.pdf) supplies the exact single-SOT23 ordering code, top-view functional layout and package drawing. Its 60 V drain and ±20 V gate ratings address the preliminary voltage screen; the low threshold is 0.5–1.0 V at 250 µA **at 25 °C**, and on-resistance is specified at 1.8 V. This does not guarantee a complete clamp response at a threshold voltage. The root actually viewed pages 1, 2 and 6. The body-diode-current table has an apparent unit typo (390 A); this study does not use that entry as a current rating.

The [unmodified primary model](https://www.diodes.com/spice/download/5027/DMN62D2U.spice.txt) is external to Git. [Source hashes](sources.json) identify the actual retrieved PDF/model inputs. The manufacturer's model notice limits accuracy of its named key parameters to 25 °C. Temperature sweeps below are diagnostics, not guaranteed cold/hot corners.

## Isolated fixture

The port is forced from −8.526 to +8.526 V. A behavioral off-driver source is `max(V(port),0)+0.4 V`, feeding the main gate through 5.1 kΩ; a 10 MΩ resistor joins main gate and port. The positive-port expression applies the published worst positive off offset. Holding the negative-port driver at +0.4 V is an **explicit fixture assumption**, not a BQ macro-model or a specification for operation below the PACK pin's absolute limit. The full protected PACK-pin network still needs its own check. The actual current-shunt reference offset is not represented in these nine fixtures.

Two injected gate-current polarities of ±10 µA test ground-resistor sensitivity. Six DC sweeps cover −40, +25 and +85 °C. Three 25 °C transients force port reversal and restoration with 1 ns, 1 µs and 100 µs edges. The transient fixture uses illustrative main-FET capacitances of 2 nF gate/source and 100 pF gate/drain, a stiff 8.526 V drain source and 10 ns maximum time step. It omits the actual main-FET channel, battery/source impedance, BQ drive dynamics, port network and layout inductance. It therefore cannot calculate main-FET current, energy or SOA.

## Findings and interpretation

All nine final 1 kΩ cases complete in LTspice. The largest modeled positive main-FET off VGS is 1.44925 V in the −40 °C/adverse-current DC case. The 1 ns transient reaches 1.29803 V. Small-clamp gate/source stress stays within approximately ±8.536 V in these fixtures. [Results](results.json) include all actual waveform extrema, point counts and raw/log hashes. [Portable decks](decks/) and normalized logs are retained.

The prior 10 kΩ comparison used the same correct orientation and off-drive expression: its corresponding maxima were 1.53920 V and 1.56437 V. Reducing the resistor lowers the assumed leakage offset from 100 mV to 10 mV and improves dynamic gate control. This is a documented deviation from TI's reference 10 kΩ. It does not introduce an intentional DC power path through an ideal MOS gate; actual leakage and abnormal clamp currents remain budget items. The [10 kΩ comparison results](comparison_10k.json) are not native hardware, and only the final 1 kΩ decks are selected here. Reproduce the comparison with `--gate-resistance 10k`.

The CSD18543Q3A's 1.5 V minimum threshold is a preliminary **screen**, not a hard safe-off boundary or an SOA limit. A typical model result below it cannot establish process/temperature margin. Closure requires an actual coupled BQ/main-FET model or bounded drive behavior, both source polarities, positive on-drive and restoration, leakage/threshold/capacitance corners, protected pin stresses, inductive paths, current/energy and hot linear SOA. Neither this clamp nor the BMS protects a 35 V failed-short charger path by itself.

An initial exploratory fixture incorrectly held the off driver at absolute zero at positive PACK voltage. A subsequent low-resolution source misreading briefly reversed Q4 in a second exploratory fixture. Both were rejected before native Q4 placement; their outputs are excluded from the selected results. The final orientation and off-reference above were independently reconciled against the actual source image.

## Reproduction

With the bundled Python/NumPy and LTspice installed, run:

```sh
python3 rerun.py --model /absolute/DMN62D2U.spice.txt --output /absolute/new-directory
```

The output directory must not exist. Each serial subprocess is bounded to 45 seconds. The script checks completed logs, axis endpoints and actual waveform data, then writes results in that directory. Use `--analyze-existing --output /absolute/run-directory` to inspect existing raw files. Models and large raw outputs remain outside Git. The logs retain the manufacturer level-3 model width warning; its unmodified model uses SPICE default TNOM = 27 °C, with the listed analysis temperatures applied. Native electrical checks and actual rendered-sheet inspection are separate from this model evidence.
