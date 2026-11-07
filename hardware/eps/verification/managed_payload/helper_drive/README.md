# Payload helper-drive comparison

2026-10-24. **Retain T2N7002AK,LM provisionally. No replacement or added resistor
is released for integration by this study.** All 230 tracked native files match
`ac4a4b9`; the actual EPS remains 345 parts / 186 nets / 933 endpoints / 14 sheets.
Electrical analysis and actual plot/source-image inspection are separate from
schematic/ERC review; this packet made no CAD changes.

The SSM3K15AMFV alternative offers a 2.5 V on-resistance specification, but its
13.5 pF input capacitance is **typical**, not a maximum. Its pulse-current rating
is 400 mA. T2N7002AK specifies 17 pF maximum at its listed test point and 760 mA
pulses of at most 10 us / 1% duty, at the stated datasheet conditions. Neither
part has a guaranteed complete cold/hot switching trajectory here. The selected
T2N's on-resistance at the TPS minimum 3 V drive remains an open guarantee.
Sources: [Toshiba SSM3K15AMFV](https://toshiba.semicon-storage.com/info/SSM3K15AMFV_datasheet_en_20140301.pdf?did=2565&prodName=SSM3K15AMFV),
[T2N7002AK](https://toshiba.semicon-storage.com/info/T2N7002AK_datasheet_en_20150401.pdf?did=29712&prodName=T2N7002AK),
[TI TPS2663 SLVSE94G](https://www.ti.com/lit/ds/symlink/tps2663.pdf).

## Completed helper-only experiment

`gate_bench.py` executes the installed, unmodified encrypted Toshiba LTspice
models normally; it never decrypts or modifies their contents. Both models use
D/G/S simulator terminal order, independently of physical lead numbering.
The manufacturer's SSM symbol file's generic model terminal numbers must not
be used as physical package numbers. No SSM KiCad part was authored/placed.

There are 24 cases: two helpers, requested model temperatures of -40/25/85 C,
direct connection (0.001 ohm numerical resistor) or a 180 ohm drain-resistor
sensitivity, and imposed 2/4 nF main-gate loads. Two 1 ns maximum-step repeats
compare with the 2 ns cases. All 26 reach 30 us without simulator warnings.
Peak current changes by 0.90% / 0.54% in the two finer-step comparisons; this
is a limited numerical check, not a convergence or PVT proof.

The bench precharges the capacitor to 14 V, disconnects that fixture source,
retains 23 uA bias / 800 kohm bleed, then applies an imposed 3 V drive through
10 ohms, with 10 pF routing capacitance. There is no TPS2663 driver model.
The 2/4 nF loads are sensitivity values, not guaranteed nonlinear CSD18543
capacitance/charge envelopes. Its published 14.5 nC maximum total charge is at
10 V, 30 V drain and 12 A, not this 14 V capacitor bench.

| Helper | Drain path | Peak current across cases | Time for proxy gate below 1 V |
| --- | --- | --- | --- |
| T2N7002AK | Direct | 317–442 mA | 0.093–0.223 us |
| T2N7002AK | 180 ohm sensitivity | 73.9–74.8 mA | 0.988–1.967 us |
| SSM3K15AMFV | Direct | 269–349 mA | 0.105–0.216 us |
| SSM3K15AMFV | 180 ohm sensitivity | 72.6–74.6 mA | 0.979–1.956 us |

The 1 V marker is a diagnostic, **not guaranteed main-FET cutoff**. The resistor
reduces helper stress by moving dissipation into itself and slows discharge;
its effect on reverse charge and the main FET is unresolved. Therefore it is
not added to the 49-part candidate or passive manifest. The alternative does
not establish a guaranteed capacitance bound or sufficient pulse margin to
justify replacing the already verified T2N package.

Positive driver charge divided by 3 V gives about 67 pF for T2N and 59 pF for
SSM in this benchmark. That diagnostic includes dynamic gate/drain interaction;
it is **not Ciss**, and cannot be substituted into TI's 50 pF test condition as
an automatic pass/fail. Conversely, the imposed ideal drive does not prove
TI's minimum level or maximum delay under the actual load. Full-temperature
DRV loading/timing remains open.

## Coupled attempts and survival gate

Nine earlier coupled attempts are preserved separately: one completed UIC pilot,
three completed runs with tolerance-relaxation warnings, four failed runs and
one terminal timeout. The CSD18543 model struggles around zero drain voltage;
a raw peak of 1.417 A includes an approximately 4e-18 s excursion. Such spikes
and warned/failed traces do not establish physical current or survival bounds.
`coupled_attempts.json` records the actual statuses. No simulation remains live.
`coupled_probe.py` reports saved attempts by default; `--execute` is an explicit
exploratory rerun, not a recommended qualification command.

Close this gate using the complete real driver and source path: measure
IN_SYS-referenced DRV/B_GATE, both MOSFET Vgs/Vds and reverse current during
source collapse and recovery, with actual capacitance/harness bounds. Compare
the direct helper and resistor option at the intended temperature/current
corners, including stored inductive energy, main-FET hot linear SOA, helper
pulse duty, brownout and repeated actuation. The remaining source bounds,
firmware retry budget and thermal boundary must be established first. Neither
the capacitor benchmark nor the current coupled macro proves those conditions.

## Evidence and reproduction

`gate_results.json`, `gate_summary.csv`, completed decks/CSV and compressed
original logs retain numeric evidence. `models.json` binds installed vendor
files; raw/model files stay external. `log_archive.json` binds original and
compressed bytes. `analyze.py` validates the full raw hashes, produces summary
and plot, and checks all native sources against `ac4a4b9`. It needs NumPy and
Matplotlib; the local isolated analysis environment uses Python 3.12,
NumPy 2.3.5 and Matplotlib 3.11.2. `gate_bench.py` additionally needs installed
LTspice 26.0.2 and the named Toshiba models. `verify_archive.py` checks portable
evidence without simulation/model installation. Earlier source/native checkpoint
verifiers remain scoped to their recorded commits.

The actual comparison plot and Toshiba source pages 1/2/4 were opened and
inspected. `visual_review.json` records that scope. This is not a schematic
render, package acceptance, complete protection design or hardware/flight
qualification.
