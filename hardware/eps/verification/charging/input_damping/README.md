# Charger input damper: parts and coupled-source checkpoint

2026-10-23. **Development selection only; no CAD change or charger-loop acceptance.**
This replaces the unspecified 2.5 Ω / 150 µF example in the
[charger sizing checkpoint](../power_stage/README.md) with a concrete candidate
and records why simply adding it cannot close the complete input design.

## Circuit allocation

Use **AC05000002708JAC00**, 2.7 Ω / 5% axial wirewound, in series with a bank
of **three EEHZA1H680P**, 68 µF / 50 V hybrid capacitors in parallel. Connect
that entire series branch from VIN_CHG to system GND, after RBF/source protection
and before the charger INFET/input-current shunt. It is a shunt damping branch,
not a resistor in the main supply path. Preserve separate VIN_CHG and
SYS_PWR_PERMITTED until the actual charger PowerPath is implemented.

The resistor's ordering code, 5 W P40 / 4.7 W P70, negative wire TCR range,
18 mm × 7.5 mm maximum body, 0.8 ±0.03 mm leads and pulse plots were checked
in [Vishay 28730, Rev 05-Dec-2024](https://www.vishay.com/docs/28730/ac_ac-at_ac-ni.pdf),
pp.1–2, 5–8 and 10. The short-pulse energy plot provides substantial room over
this branch's calculated step energy; its plotted values are not a guaranteed
hot/repetitive pulse limit for the complete assembly. The resistor is not an
accepted fuse. Mounting/lead forming, thermal clearance to the pack and nearby
capacitors, footprint and vibration retention remain open. The searched 20 mm
stock axial footprint has only a 6.4 mm body width; do not call it an exact
AC05 footprint or silently use its smaller body envelope.

The capacitors reuse the already reviewed Panasonic F construction and exact
part identity from the converter/source banks. Panasonic's
[current ZA specification](https://industrial.panasonic.com/cdbs/www-data/pdf/RDD0000/ABA0000C1221.pdf)
(01-Sep-2025), pp.1–2, gives ±20% initial tolerance and ±30% endurance change
relative to initial measured capacitance. Three parts provide **204 µF nominal,
163.2–244.8 µF initial**, and **114.24–318.24 µF** as a combined
initial-tolerance/endurance sensitivity. Those endpoints do not guarantee cold
capacitance. Two 68 µF parts would reach only 76.16 µF at the same low
sensitivity. ESR is frequency/temperature dependent; the room-temperature
100 kHz maximum is not a 1–10 kHz cold bound.

[calculate.py](calculate.py) reproduces [calculations.json](calculations.json).
At 35 V, the high-capacitance sensitivity stores **194.9 mJ**. The illustrative
minimum-resistance sensitivity gives **480.1 W** initial resistor power for an
ideal stiff step. This is an RC pulse, not 480 W continuously. At 1 A through a
shorted capacitor, the resistor instead needs to tolerate up to approximately
**2.85 W continuously** under the resistance sensitivity. Actual source current
must be independently bounded; the charger input-current servo cannot establish
that ceiling. Resistor datasheet power and the 16 mm nominal standoff do not
establish safe temperatures or mechanical clearance in vacuum.

Two 5.1 Ω / 1 W pulse MELFs in parallel were considered and rejected as a
self-sufficient branch selection: at 1 A total, each dissipates **1.275 W even
at nominal resistance**. A short-pulse rating cannot replace the continuous
fault requirement. This does not exclude a separately protected compact branch,
but no such fuse/cutoff circuit is selected here.

## Coupled source-protector simulations

[run.py](run.py) uses the current guarded LTC4364 source-deck generator,
unmodified installed controller/FET models and the stated passive loads. Four
runs completed in LTspice 26.0.2; logs and raw data were read back. The damper
bank is 318.24 µF for these sensitivities, with 10 mΩ lumped ESR except the
cold case's 133 mΩ. These are explicit model inputs, not measured frequency
curves. [Results](transients.json) preserve conditions, model/generator hashes,
raw/deck/log hashes and observed rating checks.

| Fixture | Observed result |
|---|---|
| −40 °C startup, high source-bank and damper capacitance | Final VIN_CHG 32.0824 V; no modeled startup timer trip; damper peak 1.022 W |
| +85 °C, 60 V source fault, 1 A limited | VIN_CHG peak 34.6490 V; source disconnects; damper absorbs 13.25 mJ after the event |
| Damper capacitor short at 120 ms, 1 A source | Final VIN_CHG 2.7105 V; resistor still dissipates 2.699 W at 1.2 s; 2.914 J after the event |
| Same short, 0.3 A source | Final VIN_CHG 0.8132 V; resistor still dissipates 0.2430 W at 1.2 s |

All four runs stay below the checked 35 V output, 80 V MOSFET VDS and ±16 V
VGS limits in these models. This does not qualify hot linear SOA, body-diode
pulse current, actual capacitor-short energy/ESL, resistor pulse endurance or
the shared load behavior. The 361 W resistor peak in the short cases comes
from the charged source bank; current limitation of the solar source does not
eliminate stored-capacitor energy. The observed finite interval provides no
credit for fast autonomous clearing of a damper short. No complete charger,
MPPT input loop or regulator switching model is present.

Reproduce with the bundled Python/NumPy:
`run.py --work /absolute/scratch/damping --output /absolute/results.json`.
Runs are serial with a 45 s per-process timeout; identical completed decks may
be reused after interruption. Observation timeout alone is not a restart reason.
Portable saved decks/logs are included with trailing whitespace normalized; resolve `${LTSPICE_LIBRARY}` to the
installed model directory before direct LTspice use. Original raw outputs and
models remain outside Git. Saved logs replace local directory paths and trim
trailing blank lines; original log hashes are retained in the results.

## Input impedance remains a system gate

[LTC4162-L Rev A, pp.33–34](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf)
recommends a series RC shunt to moderate a solar panel's high impedance region
and explains the interaction with VOUT bypass capacitance. Figure 8 was actually
rendered and inspected. The proposed circuit preserves its branch organization
but changes values and sits behind the separate EMBER source protector. It is
not evidence that the complete modified input network follows the reference's
dynamic behavior.

The exported integrated design already has **98 µF nominal directly on VIN_CHG**
(C600, 68 µF; C601–C603, 10 µF each). The proposed charger/converter system bank
adds **142.7 µF nominal on the separate system node**. Adding this damper gives a
**444.7 µF nominal subtotal**, before guard/bias/bypass contributions and actual
operating-state/tolerance bounds. This supersedes a 150 µF example when sizing
solar-side startup; it does not authorize merging the two native nets.

A lumped impedance sensitivity makes the missing loop check concrete. The
2.7 Ω / 204 µF branch alone has |Z| = 2.81/2.71/2.70 Ω at 1/3/10 kHz.
Including the existing direct source bank changes those to approximately
**1.26/0.519/0.162 Ω**, with respective real parts **0.550/0.112/0.024 Ω**.
Thus the damper's resistor value is not the driving impedance of the combined
network. A further idealized conducting-PowerPath limit includes the system
bank and reduces impedance again. These calculations use nominal capacitance,
illustrative ESR, ideal wiring and no active control. They demonstrate that the
branch-alone argument is insufficient; they **do not prove instability**.

Before native implementation/freeze, reconcile direct source-bank capacitance,
INFET/current-sense placement and actual input-loop response. Review capacitor
partitioning or filtering as a complete source/charger network, rerunning the
source protection and source-inhibit checks after any change. No installed
LTC4162 macro was found in the LTspice library; do not substitute another part's
loop model as proof. Actual charger evaluation or an appropriate validated
control model is needed to establish margins, weak-light startup and MPPT
recovery. Existing source-bank parts and historical protection evidence remain
unchanged.
