# 5 V recovery source protection and fault containment

2026-10-23. Engineering decision record and calculation checkpoint; **protection is not implemented or qualified**. Complements the [converter](rev_b_5v_recovery_design.md), [closure record](rev_b_5v_recovery_closure.md) and [source envelope](rev_b_source_voltage_and_fault_budget.md). Existing native circuitry and external interface names are unchanged.

## Architecture to carry forward

Use two independent hardware barriers. Solar protection sits after the RBF/deployment isolation and before the charger/PowerPath. A separate clamp/disconnect stage sits between the recovery converter and shared `+5V`. The second stage protects against a failed converter, including a power-switch short; source protection alone cannot prevent a permitted 35 V source reaching a nominal 5 V load.

```text
solar blocking → RBF/deployment isolation → SOLAR_PERMITTED
    → autonomous source barrier → VIN_CHG / PowerPath
battery → independent pack protection / RBF isolation → PowerPath
    → SYS_PWR_PERMITTED → recovery converter and its local output bank
    → independent 5 V clamp/disconnect → existing shared +5V
```

Keep the converter feedback and its minimum required output bank upstream of the new barrier. Sensing shared `+5V` through an opened barrier would make the converter increase its output while disconnected. In the eventual native integration, give the presently regulated internal node a new local name and retain `+5V` on the downstream stack interface; verify every changed endpoint. Do not move the entire output bank downstream without redoing loop/startup analysis. Protected-side capacitance must have an explicit minimum as well as an inrush maximum; the current 100 µF external allocation is only a maximum.

Both barriers operate without MCU firmware, IHU commands, or the rail they disconnect. Bias belongs upstream of the respective barrier and inside the RBF boundary. Include off-state reverse current, stored energy and control-line backfeed. A single pass MOSFET body diode is not bidirectional isolation. Retain a reverse-blocking function where an input short could discharge the stack or battery through it; the existing face diodes do not prove isolation at every internal node.

## Source window: static feasibility improved, dynamic acceptance open

The [TPS3760-Q1 Rev B](https://www.ti.com/lit/ds/symlink/tps3760-q1.pdf), tables 4-1, 6.5 and 6.6, identifies **TPS3760E012DYYRQ1** as the adjustable OV, 2% hysteresis, active-low open-drain, **non-latching** variant. A candidate 412 kΩ / 10 kΩ divider gives:

| Calculated quantity | Interval |
|---|---:|
| OV assertion | 33.210–34.314 V |
| Falling-voltage reconnect | 32.535–33.639 V |
| Minimum reconnect margin above typical cold Voc | 0.371 V |
| Margin from latest static trip to 35 V | 0.686 V |

The [script](../verification/recovery_5v_fault_analysis.py) includes independent 0.1% resistor error, 25 ppm/K across 65 K, ±100 nA sense-current sensitivity, reference error and hysteresis error. Use a conservative signed leakage interval. This resolves the earlier *static* hysteresis-window rejection for this candidate. It does not turn typical 32.164 V cold Voc into a guaranteed array maximum. An accepted normal source above 32.535 V would invalidate worst-case reconnect with this divider.

Do not use the monitor alone as a source protector. Its 17 µs maximum detect figure applies at **20% threshold overdrive**, not a small excursion near 35 V. The driver, MOSFET discharge, harness ringing and hot-plug behavior consume additional margin. The startup output also requires explicit fail-off circuitry; an open-drain pull-up is not by itself proof of safe startup.

[TPS4810-Q1 Rev C](https://www.ti.com/lit/ds/symlink/tps4810-q1.pdf) is a gate-stage candidate: 3.5–95 V operation, charge pump, separate drivers for common-source back-to-back N-channel FETs and optional short-circuit interruption. Its INP pins permit high-voltage control, but the complete pull-up, supply qualification, slew control and default-off circuit remains to be designed. Short-circuit interruption is not regulated current limiting. Do not borrow its typical peak gate current or short-circuit response as guaranteed bounds for arbitrary FETs. This option remains the low-quiescent-current comparison, rather than a selected complete source circuit.

## Clamp followed by disconnect: preferred containment function

Carry forward a **fast analog clamp with timed disconnection**, rather than approving a delayed monitor-only rail cutoff. Compare LT4363 with LTC4364 where active reverse-current blocking is required. These remain circuit candidates, not installed parts.

[LT4363 Rev C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf), pp. 3–4 and 11–15, provides output voltage/current regulation, a stress-dependent timer and latch-off (-1) or automatic retry (-2). At low input it needs a logic-level pass FET. Its published fast response uses specific test steps; gate slew capacitance affects fault response. The table's default VCC is 12 V, so application-wide accuracy/dynamics cannot be inferred solely from these figures.

For comparison, [LTC4364 Rev B](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf), pp. 3–5 and 14–16, adds an independently controlled ideal-diode FET. Its FB accuracy row explicitly covers VCC = 12–80 V. The proposed 5 V application therefore needs low-input confirmation, especially a slow fault rise through 5–12 V. This is a selection gate, not a reason to silently extend the specification.

LT4363 table-condition calculations illustrate the available margins:

| Function | Candidate divider | Nominal clamp | Calculated interval |
|---|---|---:|---:|
| Source ceiling | 25.3 kΩ / 1 kΩ | 33.533 V | 32.684–34.388 V |
| Independent rail ceiling | 3.12 kΩ / 1 kΩ | 5.253 V | 5.126–5.380 V |

These are **sensitivity calculations at the cited table conditions**, including resistor drift and ±1 µA FB leakage. They are not application guarantees or final resistor selections. The source setting lies above typical cold Voc and could avoid continuous normal clamping, unlike a clamp below normal cold Voc. Only 0.520 V separates its minimum from that typical value. Supplier spread, AM0 and the actual thermal envelope can consume it. A persistent abnormal input must time out; do not size the FET for unproven continuous linear dissipation. Any source retry-inhibit threshold must also permit cold reconnect.

On the rail, the existing regulator's calculated 5.074753 V upper corner leaves only **51.7 mV** to minimum clamp. Maximum clamp leaves **119.5 mV** to a **provisional 5.5 V design ceiling**. Neither consumer acceptance of 5.5 V nor those dynamic margins is established. Wiring drop, regulator load release and protector input-bias effects must be included before freezing these numbers. Increasing clamp voltage to hide nuisance trips spends the fault overshoot margin.

## Fault energy and timing acceptance

The converter input's nominal 68 µF bulk stores 41.65 mJ at 35 V; nominal 30 µF ceramic adds 18.38 mJ before bias correction. Cutting off upstream solar does not remove this local energy. Battery and PowerPath replenishment must be evaluated separately.

A reproducible ideal lossless LC sensitivity uses 35 V, 3.808 µH and 160 µF, initially at 5.074753 V with zero inductor current. If a fault leaves the path conducting, it crosses 5.380 V after about 3.53 µs and reaches about 5.578 V one microsecond later. This is **not a predicted or worst-case fault waveform**: resistance, initial load current, saturation, semiconductor topology and parasitics are omitted. It demonstrates why a static threshold plus a headline delay cannot establish containment. A real short across a converter input/output bypassing the inductor needs a separate, potentially faster test.

At a 35 V fault input and 5.25 V clamp, a pass FET dissipates 59.5 W at 2 A or 89.25 W at 3 A. A 1 ms interval represents 59.5–89.25 mJ; 5 ms represents 297.5–446.25 mJ. These are **stress allocations, not accepted current limits or timer settings**. Select the pass FET from its linear safe-operating-area curve at the actual initial temperature, gate drive and pulse/repetition conditions. A large switching-current or avalanche rating is insufficient. Include initial transient stress before the timer starts and capacitor charging after restart. Choose the timer after this check, and verify normal startup does not expire it.

## Fault and restart policy

| Condition | Required behavior |
|---|---|
| Solar overvoltage | Clamp/cut solar without disabling a healthy battery path; restart autonomously after a safe source and cooldown. Do not require an already powered IHU. |
| Converter OV or pass-through | Independent clamp limits the shared rail, then disconnects and retains a fault. Disable the converter as an additional action; its EN is not the containment barrier. |
| Persistent shared 5 V short | Bounded current/energy followed by disconnection; do not reset-loop the shared rail indefinitely. Coordinate with local branch limits. |
| Input short or prebiased output | Reverse-blocking function prevents uncontrolled discharge/backfeed. Verify powered and unpowered controls. |
| RBF insertion / permission loss | Hardware removes both sources and active protector bias; control/telemetry must not keep the stage powered. |
| Faulted protector itself | Record residual exposure; two functions do not establish tolerance of every protector/controller short. No single-fault-tolerant claim is made. |

Recommend latched 5 V OV containment with bounded, deliberate reset from an independently alive EPS control domain. Recovery must not depend solely on the IHU/COMMS powered by the disconnected rail. Hardware voltage/current limits remain active during reset; software cannot bypass them. A reset method and retry budget remain to be implemented. The future 3.3 V protection must be reviewed before claiming that control domain survives a common-source fault. COMMS TX remains default off and IHU heavy-load sequencing remains local; the barrier is for faults, not a command-required boot dependency.

## Next implementation gates

1. Establish accepted array voltage/current/slew and bench-source limits, and downstream allowable peak voltage/duration. Use bounded engineering envelopes for development; retain the distinction from accepted flight limits.
2. Resolve low-input clamp accuracy, reverse-blocking topology, default-off startup and timer behavior. Select complete source and rail circuits, not merely monitor ICs. Registered-library searches found neither LT4363 nor TPS3760; no new custom component has been authored.
3. Select and verify the pass FETs, shunts, timer, gate network, upstream/downstream capacitance and reset interface. New missing-part construction follows repository S08 before native authoring.
4. Build through Konnect, then verify connectivity/ERC and actual rendered sheets separately. No native protection circuit, ERC result or protection render is claimed by this checkpoint.
5. Test limited-energy hot plug, cold open-circuit startup, absent/depleted battery, handover, slow/fast OV, converter feedback failure, actual switch-short paths, prebias, input/output shorts and reset repetition. Measure voltage at charger and receiving-board pins, gate waveforms, current and FET temperature; include high-temperature initial SOA. Do not perform these tests on the lithium pack as a substitute for a controlled source fixture.

The [saved calculation results](../verification/evidence/2026-10-23_recovery_5v_fault_analysis.json) reproduce the stated static feasibility cases; the calculation assertions pass. Dynamic containment, component selection and physical tests remain open. This record neither closes the 5 V recovery design nor authorizes fabrication.
