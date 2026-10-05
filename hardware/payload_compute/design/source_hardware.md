# Source hardware for the real schematic

2026-10-04. Integration baseline; exact new packages/circuits must be accepted
during capture. This supersedes the PMV16XNR clamp as the preferred interface.
The previous clamp fixture and its conditional DC checks are retained as
evidence of that experiment, not presented as the new circuit.

## Enable without a raw-biased MOSFET

Use an AON-powered SN74LVC1G11DBVR output through 4.7 kΩ / 1% series
resistance into eFuse EN, with 10 kΩ / 1% EN-to-ground. No raw-input pull-up
or raw UV divider is attached to EN. Inputs require qualified branch admission,
AON reset release and the branch's raw hardware voltage validity. The source
decoder also includes mode/source lock, one-hot selection and watchdog/MCU
readiness. Separate raw voltage-window detectors provide UV qualification.

At the valid AON supply, the gate's full-temperature VOH≥2.4 V allocation
gives EN≥1.621 V including 0.1 µA eFuse leakage. VOL≤0.4 V gives EN≤0.274 V,
below the 0.45 V minimum shutdown threshold. With AON at zero, 10 µA gate
Ioff plus 0.1 µA eFuse leakage gives EN≤0.102 V. These are calculable static
margins without assuming a MOSFET's leakage at nonzero VGS. Output load is
under 0.24 mA, within the gate's stated drive conditions.

This does not prove behavior at every intermediate AON voltage or for fast
raw steps. Require scope/SPICE checks of cold attach, slow/fast AON collapse,
detach, negative input and gate injection. Keep EN capacitance small or omit
it initially; qualify any added filter against fault reset and shutdown delay.
Record the existing eFuse latch-off/reset behavior; a new grant does not
automatically clear every input fault. AON reset must suppress grants even if
comparator outputs float at low supply.

Retain the raw OVLO divider as independent eFuse overvoltage protection.
USB UV now comes from a TPS3700DDCR hardware detector powered by AON.
For each raw source, tie the detector's two open-drain outputs together with
an AON pull-up to form RAW_WINDOW_OK. OUTA sinks for undervoltage, OUTB sinks
for overvoltage. Its 450 µs maximum startup is shorter than the reset
supervisor's 12 ms minimum release delay; still check actual sequencing.

| Branch | UV top / bottom | UV rising allocation | OV top / bottom | OV rising allocation |
|---|---|---|---|---|
| USB | 324 kΩ / 10 kΩ | 13.142–13.580 V | 402 kΩ / 10 kΩ | 16.210–16.753 V |
| Bench and stack | 143 kΩ / 10 kΩ | 6.021–6.220 V | 215 kΩ / 10 kΩ | 8.854–9.148 V |

[Reproducible rising and falling ranges](schematic_start_results.json) are
produced by `schematic_start_study.py`.

Ranges use TPS3700 396–404 mV thresholds, ±25 nA input-current allocation
and a ±0.3% total resistor allocation (initial tolerance plus temperature).
Use its separately specified 387–400 mV falling thresholds for hysteresis
calculations; do not subtract the typical 5.5 mV as a guaranteed value.
The battery UV choice is deliberately conservative for the 5 V buck's input
headroom. Nominal 6.0 V operation is still a requirement to investigate, not
a promise of startup at 6.0 V after path drops. Revisit the divider only with
loaded-input/dropout and EPS threshold evidence.

These input windows are coarse power-valid guards. Keep main-5-V precision
monitoring separate. Set SOURCE_OK only after independently valid raw input,
selected-bus voltage, completed inrush, clear faults and operating-profile
qualification. AUXOFF/FLT or the enable command alone cannot substitute.
Provide raw presence sensing that detects a USB 5 V cable even though its
main path is ineligible, so two attached lab sources inhibit startup.

## Immutable startup source choice

Implement three SN74LVC1G373DBVR request latches, one SN74LVC1G74DCUR
SOURCE_LOCKED flip-flop, one-hot decoding and mode/raw/contract gates.
These packages already have accepted physical maps. Each request defaults
low. Before locking, latch enable is high only while AON reset is released
and SOURCE_LOCKED is low. Main admissions are always blocked while unlocked.

The MCU chooses one eligible source, holds all request data stable, then
pulses SOURCE_LOCK_CLK with D tied high. CLR_N is AON reset only. SOURCE_LOCKED
closes the three request latches. Ordinary MCU reset changes requests/alive
but cannot change their stored choice or SOURCE_LOCKED. Decoding rejects
000 and every multi-hot encoding. No alternate input automatically takes
over when the selected input fails. The separate run latch still requires
new qualification and a fresh arm edge after a fault.

Reserve 1 ms data setup/hold around a 1 ms source-lock pulse for first firmware;
verify actual latch/decoder races and asynchronous reset. Source selection
may wait while inputs conflict, before any choice is locked. Once locked,
changing feeds requires an AON power cycle. IHU permission gates downstream
flight operation, not the creation of the AON supply.

The mode jumper is also sampled once. Replace the old unresolved Schmitt
threshold assumption with a fixed-threshold receiver option: TPS3700 on AON,
filtered active-low jumper voltage on INB and a non-inverting OUTB receiver
into the sampler. The applied jumper grounds BENCH_JUMPER_N; a 10 kΩ AON
pull-up defines open as flight mode. OUTB releases high for the grounded
bench input and sinks low for the open/high input. The
other comparator can receive IHU PAYLOAD_EN on INA through a 10 kΩ / 5.1 kΩ
divider. A 3.0 V high then exceeds 0.99 V at the sense input; a 0.4 V low
stays below 0.137 V. Both are well separated from 0.387–0.404 V thresholds.
The divider also defines low when IHU is missing. Check module/IHU ground
offsets and startup, and accept this new package before placing it.

Stage 3 capture uses a firmware-timed mode-lock pulse after at least 20 ms
from clean reset release and at least 10 ms stable BENCH_LATCHED, rather than
sampling automatically at reset release. The 1 kΩ / 100 nF filter is a
prototype allocation requiring jumper-bounce and supply-ramp qualification.
PF3 is allocated to MODE_LOCK_CLK; PC9 can read the transparent BENCH_LATCHED
signal before locking. AON reset alone clears the mode/source locks.
Ordinary MCU reset must inhibit readiness without reopening either latch.

Choice outputs must include reset, committed mode/source locks, exactly one
stored request and the correct mode: USB/bench in bench mode, stack in flight
mode. MODE_PERMISSION additionally requires live IHU permission for stack.
The [ideal 256-case contract check](stage3_control_contract_study.py) records
these requirements; actual exported gate connectivity must independently
implement them. A choice is not SOURCE_OK: raw presence/windows, PD contract,
selected-bus/inrush/fault qualification remain separate hardware owners.

Open-drain detector/watchdog/reset lines need edge conditioning before
ordinary CMOS inputs. Stage 3 uses near-rail Schmitt receivers as a conditional
prototype choice; discrete supply-point threshold tables are not interpolated
into a guaranteed full AON threshold envelope. Check full-rail levels, bias,
fanout, actual edges and supply ramps before hardware acceptance. The watchdog
EN input needs a separately budgeted low level of at most 0.25 V; the reset
supervisor's generic 0.4 V output-low bound does not establish that margin.

## Independent bootstrap paths

Keep one protected/limited bootstrap branch per raw source before each
default-off main switch. Reverse-isolate those branches before the common
LMR36506 supply. A main switch cannot protect a branch bypassing it.
Use coordinated entry protection upstream of both branches. The next capture
selects TPS26600PWPR on all three bootstrap branches, with native active OR
and a nominal 118 kΩ ±1% current-limit resistor, keeping its upper resistance
below the recommended 120 kΩ maximum. Its 4.2 V operating minimum
allows initial USB 5 V without an added Schottky drop. Exact package acceptance,
thresholds and startup behavior belong to the captured stage evidence; the
part selection alone does not qualify the complete inlet.

The STUSB4500 powers itself from receptacle VBUS. The MCU is not required to
negotiate the initial full profile. USB 5 V bootstrap must stay within actual
advertised/negotiated current. Treat the previous 0.250 W reduced-startup
allocation as a ceiling to verify, and target 0.200 W to add margin. Recompute
the current budget using the captured native-OR circuit and its actual drop,
including PD/protection/indicator overhead. CAN paths remain in standby/shutdown until
the full profile is established. A main-path current setting cannot enforce
that bootstrap budget. The [bootstrap input and restart contract](bootstrap_input_contract.md)
defines the qualified C-to-C source, reduced-startup allocation, whole-inlet
capacitance budget and recovery after complete AON loss.

For all entry paths, coordinate fuse energy, reverse polarity, TVS dynamic
clamp and IC input/absolute limits with wiring and capacitor ratings. This
cannot be closed by naming a TVS standoff voltage. Include the actual source
impedance and source fault current. Bootstrap reverse leakage must not power
an absent source or defeat flight launch isolation.

## Limits and control crossings

The existing USB 1.65 kΩ limit screen has a 1.798 A minimum, which does not
cover the 15 W lab case with 20% load allowance at 14.25 V/85% efficiency
(2.187 A). It does cover the equivalent 7 W lab arithmetic case (1.394 A),
but neither case proves boot transients. Likewise the 750 Ω battery limit
minimum 3.956 A falls below the 15 W flight allowance at 6 V (4.253 A).
Use conservative bring-up loads, include configurable limit-resistor options,
and qualify or revise input protection before enabling the 15 W profile.
Never infer safe connector current from the converter's 6 A rating.

Regulator EN interfaces also need partial-power checks. LMR51430 specifies
EN relative to VIN; LMR51460 discourages applying EN when VIN is zero.
Do not copy an AON output directly onto every converter EN. Provide
bus-domain isolation/local bias as needed, hardware bus-invalid suppression,
and verify absent-input and discharge trajectories before sheet acceptance.
Main and peripheral output switching/discharge must meet the module's rail
decay requirements without limiting reverse current at module VDD_IN.

Sources: [TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf),
[SN74LVC1G11](https://www.ti.com/lit/ds/symlink/sn74lvc1g11.pdf),
[TPS25947](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
[TPS2660](https://www.ti.com/lit/ds/symlink/tps2660.pdf),
[LMR51430](https://www.ti.com/lit/ds/symlink/lmr51430.pdf), and
[LMR51460-Q1](https://www.ti.com/lit/ds/symlink/lmr51460-q1.pdf).
