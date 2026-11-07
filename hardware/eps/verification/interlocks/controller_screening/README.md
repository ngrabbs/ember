# RBF model diagnostics and controller screening

2026-10-23. **Experimental evidence only; no RBF circuit selected or implemented.**
This follows the [failed P-channel gate studies](../gate_screening/README.md).
The 28 cases here completed in LTspice 26.0.2. That establishes that waveforms
exist, not that the circuit or MOSFET safe operating area is accepted.

## Isolated P-channel model diagnosis

Three tests with the unmodified Vishay SUD50P08-25L model completed: one-device
DC, common-source pair DC and one-device transient. At an 8.4 V supply, 10 Ω
load and −8.4 V gate/source, the DC outputs are 8.38221 V and 8.36450 V,
respectively. The transient output is 8.38221 V at 4 ms, then 0.598114 V at 9 ms
as the 100 µF output capacitor discharges. This narrows the previous failure:
the model can converge in isolated tests. The four earlier complete gate-circuit
runs remain unsuccessful; these new runs do not establish their inrush,
cutoff, leakage or SOA.

## Experimental N-channel controller application

The other 25 cases use the installed unmodified LTC4367 macro and IRLR2908
VDMOS model. The controller is powered from a diode OR of the two switch ports
**through the hardware permission contact**, with an isolated 100 nF bias
reservoir. UV and SHDN follow the permission node. Two common-source MOSFETs
block either direction while off. A 100 nF gate-to-ground capacitor slows turn-on;
1 MΩ connects gate to source. Generic diodes and the generic contact model are
unselected assumptions, not BOM items.

**Material application deviation:** controller VOUT senses the MOSFET common
source, rather than the external load terminal. This is a study adaptation for
bidirectional source isolation, not a claim to reproduce the manufacturer's
reference circuit. No missing controller symbol or footprint was authored.

| Case | Minimum controller VOUT sense | Finding |
|---|---:|---|
| Direct sense, 8.4 V battery | −0.920289 V | Reject: below −0.3 V absolute minimum |
| Diode-isolated sense, battery | −0.448323 V | Reject: diode alone does not fix undershoot |
| 100 nF on common source | −0.609783 V | Reject |
| 220 nF on common source | −0.399642 V | Reject |
| 1 µF on common source, battery / 5 V / reverse | approximately −2.54 µV | Does not violate that limit in these runs |
| 0.8 µF, battery at −40 °C / +85 °C | −2.97 µV / −0.011137 V | Temperature/model sensitivity only |
| 0.8 µF, 4.5 V battery | approximately −2.54 µV | Model starts; output at 450 ms is 4.46062 V |
| 0.8 µF, 1 A / 0.1 A limited solar | approximately −2.54 µV | Model starts under the stated passive load |
| Stiff 60 V hot-plug, direct sense | −2.05570 V | Reject; harness ringing also drives MOSFET VDS above 80 V |
| 60 V, 1 A limited source, contact open, 1 µF | approximately −2.54 µV | Inhibited only; does not qualify arbitrary 60 V hot-plug |

The 0.8 µF tests represent an illustrative 20% reduction from 1 µF, **not** a
selected capacitor's guaranteed effective capacitance across voltage, temperature
and ageing. Their maximum absolute gate/source stress is about 9.4131 V; no
80 V VDS violation was found in those six cases. Model temperature settings do
not establish controller process corners or hot linear SOA. The 1 A solar case
has about 0.216 J of integrated positive dissipation in M1 over the run; energy
alone is not an SOA criterion.

Permission bounce has two approximately 1 ms pulses before stable permission at
100 ms. It is one illustrative waveform. Battery and reverse-battery are
separate tests with the source on opposite ports; they do not connect a battery
directly to a higher-voltage solar source. Each actual source needs its own
reviewed barrier and complete PowerPath analysis.

## Fixture boundaries and interpretation

Battery feed: 50 mΩ, 1 µH harness, 1 µF input capacitor, 1 µs source rise and
10 Ω load with 142.7 µF nominal downstream capacitance. The large total source
current spike at initial connection largely charges the upstream input capacitor;
use recorded MOSFET currents to distinguish it from passed-load inrush.
Solar feed: behavioral 0..1 A or 0..0.1 A source, 1 µH harness, 1 µF input,
1 kΩ load and 390.8 µF nominal downstream capacitance. These capacitances are
provisional study sums, not a frozen integrated EPS budget. No regulator startup
or constant-power load is represented.

For solar decks, I(Vsource) measures the open-circuit-voltage control source,
**not** the PV supply current; the log's `peak_current=0` is not a current-limit
result. For the solar cases, output voltage remaining at 700 ms is consistent
with the passive load's capacitor discharge time; it does not by itself prove
continued conduction or satisfy a discharge-time requirement.

Remaining acceptance includes actual contact/harness selection, source limits,
capacitance/ESR/ESL corners, partial-power pin currents and power sequencing,
off-state leakage/back-power, inrush and linear SOA at temperature, abrupt loss
of either source, repeated actuation and actual integrated load behavior. In
particular, charging the internal source capacitor and removing controller bias
can leave VOUT positive while VIN falls; this adaptation needs a documented
permitted pin-power relationship. The controller power domain must satisfy the
RBF boundary without introducing an unreviewed always-powered raw-bus circuit.

## Reproduction and evidence

[Results](results.json) include raw/log hashes, extrema, sampled output voltages,
MOSFET currents and integrated positive dissipation. [Model hashes](model_hashes.json)
identify the actual unmodified inputs; model files and large raw outputs remain
outside Git. Portable decks substitute `${LTSPICE_LIBRARY}` and `${PMOS_MODEL}`.
The saved logs substitute directory paths and normalize trailing blank lines; original log hashes are recorded
separately. Several runs needed normal Gmin/source stepping to obtain an operating
point; completion does not imply every run used direct Newton convergence.

Run `rerun.py --output /absolute/new-directory --pmos-model /absolute/sud50p08.lib`
with Python 3; output must be a new external directory. Use repeated `--case`
arguments for a subset. Then use the bundled Python with NumPy:
`analyze.py --controller-raw /absolute/new-directory --pmos-raw /absolute/new-directory --output /absolute/results.json`.
Use the same repeated `--case` selections with the analyzer after a subset run. The analyzer also accepts the original separate scratch directories. It verifies
completed logs and reads actual raw points rather than accepting log measures
alone. Three selected portable decks were rerun successfully; [repeat evidence](portable_rerun.json) records agreement within 100 µV for the selected voltage observations. Process termination is bounded to 45 seconds per serial run.

Sources: [LTC4367 Rev D, absolute ratings p.2](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4367.pdf),
[Vishay SUD50P08 datasheet](https://www.vishay.com/docs/73443/sud50p08.pdf),
[unmodified P-channel model archive](https://www.vishay.com/docs/77820/sud50p08.zip).
The controller's −0.3 V VOUT absolute minimum is a failure threshold, not an
operating target. No KiCad sources changed in this study; no new schematic or
board render was produced.
