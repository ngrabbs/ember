# 5 V recovery closure and receiving-board handoff

2026-10-23. Complements the [converter design](rev_b_5v_recovery_design.md); this record separates resolved design choices from integration and physical acceptance. Existing stack interfaces remain unchanged.

## Confirmed startup behavior

The operator confirms COMMS has a TX power switch that defaults off, and no other power controls. Its receive/control circuitry therefore belongs to the unavoidable startup load; it cannot be held off by a nonexistent EPS permission input. The IHU schematic is not yet complete. Record local sequencing requirements there before its power design is implemented.

Keep shared `+5V` available for recovery and start the converter autonomously. Do not insert a shared-rail switch merely to defer loads that can be controlled locally. Keep the COMMS TX switch off throughout startup. Recovery receive must not require a command from an unpowered IHU, and EPS must not drive IHU-owned `COMMS_EN`/`PAYLOAD_EN` pins.

**IHU schematic requirements:**

1. Power the minimum boot/control circuitry directly from the essential supply it actually requires. Allocate its unavoidable input capacitance and startup draw with COMMS; do not assume an entire IHU can be switched off and still issue a recovery command.
2. Put substantial nonessential 5 V loads behind local default-off switches/enables. Require hardware supply-good qualification and a settling delay before software can admit them. The hardware condition vetoes an MCU-high GPIO during brownout/reset.
3. Sense the rails locally. No EPS PG signal is currently allocated on the canonical stack; an EPS-local `REC5_PG` label is not an off-board interface. A new wire requires a separate pin/interface allocation.
4. Qualify 3.3 V if the receiving logic needs it, along with 5 V. Assert the veto on a failed rail and restart the delay after recovery. Check the switch-enable logic during the supervisor's own power-up, supply absence, and the interval in which its output is undefined.
5. Limit branch capacitance and ramp current. Discharging a local branch must not discharge the essential shared rail or backfeed it through signal interfaces. Do not use a delayed enable alone as an overcurrent limiter.

A [TPS3808G50DBVR](https://www.ti.com/lit/ds/symlink/tps3808.pdf) is a **candidate for local IHU undervoltage/settling supervision**, not an EPS-installed switch or an overvoltage protector. Its nominal 4.65 V threshold must be reconciled with IHU minimum voltage and hysteresis. CT open gives a specified 12–28 ms release delay, rather than a guaranteed 20 ms. Its open-drain RESET needs a pull-up and a fail-off switch interface; it cannot directly be assumed to provide an active-high default-low enable while unpowered. Complete that interface in the IHU schematic. A higher rail threshold may be necessary; the selected package name does not freeze that choice.

## Proposed measurable startup allocation

These are engineering allocations to check against actual boards, not accepted measured loads:

| Quantity | Proposed development allocation |
|---|---:|
| EPS output bank, high-capacitance case | 500 µF |
| Additional directly connected stack capacitance | 100 µF total |
| Unavoidable startup load | 0.5 A total on 5 V |
| Deferred load admission | After local rail qualification and hardware delay |
| Deferred plus essential steady load | Within provisional shared 2 A budget |

At 5.08 V and a 2.5 ms ramp, 600 µF draws approximately 1.219 A; adding 0.5 A gives 1.719 A versus the drift-inclusive slow-limit sensitivity of 2.369 A. This arithmetic leaves about 0.65 A but does not guarantee dynamic startup or the low-VIN inductor limit. The slow-limit-only maximum additional capacitance would be about 420 µF; the proposed 100 µF allocation deliberately reserves margin. Constant-power receivers can draw more current during a slow ramp: measure their actual behavior rather than substituting their rated 5 V current.

Test COMMS receive startup with TX off before admitting TX. IHU boot must be possible under the same low-energy condition. After settling, enable one substantial branch at a time, control its slew, and verify the recovery path stays alive. Keep battery protection limits separate from converter UVLO.

## Source-voltage decision

The converter's 35 V development input ceiling remains conditional on a completed upstream protector. It does not increase the LTC4162 operating limit. The [source study](rev_b_source_voltage_and_fault_budget.md) has only a **typical** cold 4S Voc of 32.164 V; supplier spread, AM0, actual temperature and transients are still unbounded.

An additional [TPS2663 Rev G](https://www.ti.com/lit/ds/symlink/tps2663.pdf) comparison rejects a tempting integrated-cutoff shortcut. For divider multiplier `k = 1 + Rtop/Rbottom`:

- Worst-case reconnect at 32.164 V requires `k > 32.164 / 1.09 = 29.508`.
- Worst-case cutoff no later than 35 V requires `k < 35 / 1.224 = 28.595`.
- There is no overlap even before resistor drift, leakage, detection delay and overshoot. The fixed internal cutoff can reach 35.4 V, which also fails this ceiling.

This is a threshold-window rejection, not a statement that the device is generally unsuitable. Its 35 V maximum clamp variants leave no operating overshoot margin to the charger's 35 V boundary. Likewise, a 23/24 V eFuse on the 5 V rail cannot be assumed to survive a failed converter passing a 35 V source.

The next source-circuit selection must provide separately controlled trip/reconnect thresholds or qualified voltage clamping, with a default-off gate stage, bias inside the RBF boundary, proven fault energy, and battery handover. A monitor alone is not the gate circuit. Specify maximum source current/slew and effective protected-node capacitance to evaluate `ΔV = I × delay / C`; do not turn a typical delay or a bounded-PV calculation into protection against a stiff bench-source step. Retain LM5177 as the alternative if the TPS input boundary cannot be established. Charger protection is still necessary with either converter.

An additional [LT4363 Rev C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf), pp. 11–12, and [LTC4364 Rev B](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf), pp. 13–15, check prevents another shortcut: their linear surge-clamp operation starts a fault timer and eventually disconnects a persistent overvoltage. Setting a clamp below normal cold-array Voc therefore does not automatically provide continuous cold-solar startup; repeated cutoff/cooldown or restart inhibition can remain. A larger timer does not establish continuous MOSFET SOA. These are comparison candidates only, with no native circuit or component selection made. The complete source problem still requires either a feasible precise threshold window or explicitly continuous-rated conditioning and fault coordination.

## Temperature, components and physical acceptance

The operator selected **−40 to +85 °C only for electronics component screening**. Actual electronics/baseplate temperature and the battery operating limits remain open. At an assumed 85 °C board reference, the converter's 125 °C operating junction ceiling leaves 40 K. Attributing the entire 1.86 W stage-loss sensitivity to the IC would require an effective heat path of at most 21.5 K/W; this conservative allocation is not a die-loss or vacuum temperature prediction. TI's EVM thermal metrics depend on its specified copper/board construction.

Exact development MPNs now exist for every converter component. All seven signal resistors use Vishay TNPW0603, 0.1%, 25 ppm/K; R6/R8 reuse TNPW060310K0BEEA. Codes are constructed from [Vishay document 28758, 10-Apr-2026](https://www.vishay.com/docs/28758/tnpw_e3.pdf), pp. 3–4; ordering/lot confirmation remains open. Their 0.11 W general-mode P70 rating needs temperature derating. The worst divider resistor is approximately 15.3 mW at 35 V. R4 retains its separate 1 W/50 ppm/K rating from the [Bourns CRF data](https://www.bourns.com/docs/product-datasheets/crf.pdf). The shunt TCR is specified over +25 to +125 °C; extending it to −40 °C in the screening calculation is a sensitivity, not a cold-resistance guarantee.

C17 is [GRM31C5C1H753JA01L](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM31C5C1H753JA01-01A-EN_PDF_CERAMICCAPACITORSMD), 75 nF, 5%, 50 V, C0G, 1206. C18 is [GRM1885C1H301JA01D](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM1885C1H301JA01-01A-EN_PDF_CERAMICCAPACITORSMD), 300 pF, 5%, 50 V, C0G, 0603. This removes X7R DC-bias uncertainty from the compensation pair. The cold extension of the small C0G temperature term in the calculation is conservative sensitivity; it does not expand a published guarantee. C3–C6 and C9–C12 still require full TDK bias/temperature/aging data; the accessible TI EVM BOM establishes part identity, not effective capacitance.

The [Coilcraft XAL7070-682MEC](https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xal/xal7070/xal7070-682/) replaces the initial 10 µH choice to respect TI's recommended effective-inductance ceiling. The 6.8 µH part's 12.8 A saturation figure is typical at 25 °C and 30% L loss; 6.8 A RMS is a reference for 20 °C rise. Neither is a guaranteed hot fault-current rating. The installed XAL7070 footprint is a candidate pending direct mechanical-drawing inspection; current download access did not provide that drawing.

[EEHZK1V101XP](https://industrial.panasonic.com/ww/products/pt/hybrid-aluminum/models/EEHZK1V101XP) is **6.3 mm diameter × 7.7 mm nominal height**, not 5.8 mm tall. [EEHZA1H680P](https://industrial.panasonic.com/ww/products/pt/hybrid-aluminum/models/EEHZA1H680P) is 8 mm × 10.2 mm nominal. The 16 mm standoff leaves nominal height room, but assembly tolerance, vent requirements, the opposing PCB and vacuum/material suitability still need review. A generic same-diameter footprint is not automatically Panasonic's recommended pattern.

## Exit evidence still required

| Work item | Completion evidence |
|---|---|
| Native component identity | Fresh CLI BOM/netlist contains every selected MPN and required field; no silent batch-field omissions |
| Package construction | Approved Panasonic land patterns, polarity, maximum-body courtyard and actual query-back/render checks; full IC stencil review remains separate |
| Receiving boards | COMMS direct-load/current/capacitance measurements; IHU local switch and supervisor circuit with no boot dependency |
| Source and rail faults | Complete autonomous source OV and independent 5 V containment circuits; worst-case trip/reset, delay, SOA, peak voltage and recovery |
| Dynamic qualification | 4.5 V cold start, 5 V transition region, high VIN, source handover, prebias, branch admission and shorts; actual multibranch loop gain and cold transient measurements |
| Environment and CAD | Qualified heat path/temperatures and EMI; supported S11 visible-field presentation under the repository policy |

None of the physical tests above has run. These design corrections narrow the remaining work; they do not make the supply a fabrication-ready or flight-qualified design.
