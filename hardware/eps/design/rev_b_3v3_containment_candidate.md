# Essential 3.3 V fault containment candidate

2026-10-24. Read-only screening for the remaining essential-rail fault
boundary; no native circuit is selected or integrated by this record.

The LMR51635 output can expose the MCU/CAN rail to its source if an internal
switch fails short. The existing output-bank rating does not protect the
lower-voltage logic. The barrier must work from the available 3.3 V rail,
without a running MCU, and account for source energy, stored inductor energy,
output capacitance, turn-off delay, start-up and reverse/back-power paths.

A registered stock-symbol search found `Power_Management:LTC4365TS8` and its
`-1` alternative, plus DFN versions. LTC4368 returned no registered symbol.
Prefer evaluating a stock package before proposing another custom library.
The installed LTspice library includes unmodified LTC4365/LTC4365-1 models
and symbols. The later development checkpoint below supersedes this initial pre-simulation state; vendor models remain unmodified.

[ADI LTC4365 Rev B](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4365.pdf)
specifies 2.5–34 V operation with protection to +60 V, adjustable 0.5 V
UV/OV comparisons, and an external pair of N-channel MOSFETs. The standard
part recovers after nominally 36 ms; the -1 version uses 1 ms. Its fault-delay
row specifies 2 µs maximum only at VIN=VOUT=12 V and 50 mV overdrive.
Do not apply that as a guaranteed delay at the EPS 3.3 V operating point.

This is a candidate for screening, not closure of the response-time or MOSFET
survival requirement. Begin by obtaining and inspecting the actual reference
figure, reconciling an exact industrial-grade order code and package map,
and checking low-voltage gate drive and fault behavior. The complete circuit
also needs an independently bounded current/energy path; voltage disconnection
alone does not establish current limiting or prevent downstream overshoot.
The shared CAN branch-containment problem remains separate.

Proceed only after current rail/load/source bounds and the proposed
threshold/guard network have been modeled together. Retain the existing
+3V3 interface name downstream; any newly separated converter-output net
requires an explicit documented migration and full endpoint crosswalk.

## 2026-10-24 quantified selection gate

The [protection-window checkpoint](../verification/essential_3v3/containment_window/README.md) now adds504 direct-step and240 two-filter linear fault cases, independently checked against closed-form/matrix-exponential solutions and a half-step repeat. This is not a controller or native integration pass. It identifies an additional mandatory change: current C404–C411 are25V parts exposed upstream of a downstream barrier; the fault-rated raw bank and stable feedback path must be included in the final circuit.

The unclamped58.8k/10k LTC4365 OV divider exceeds the5V sense-pin absolute maximum at the imposed35V source;60.4k/10k leaves only10.46mV from maximum trip to the3.6V working ceiling. Low-voltage gate drive, complete turn-off timing and sense-pin protection remain selection gates. Supplying an LTC4364 from permittedSYS alone does not cover its12V-minimum FB accuracy row during battery operation.

The two-filter comparison shows why existing L400 must be modeled rather than treating its output as an arbitrary stiff step. It also exposes fault-current sensitivities far beyond L400's published typical saturation reference. Carry forward coordinated raw-bank voltage rating, actual source/magnetic bounds, a tight autonomous sense/drive path, downstream guard and a real turn-off energy clamp as one design task. Do not integrate an isolated voltage switch as if it closed all of these paths. Existing+3V3 consumers and interface names remain unchanged.

## LTC4368 development continuation

The operator approved [LTC4368IMS-1 library construction](rev_b_ltc4368_library_rules.md). The [constructed package/gate checkpoint](../verification/essential_3v3/ltc4368_candidate/README.md) checks all ten pins and20 raw pad objects, preserves every previous symbol subtree, and demonstrates an exact0.04mm mask opening despite the disposable board's0.05mm inherited margin. Actual final part renders were inspected; manufacturer-page pixel inspection remains open because PDF/image retrieval did not succeed. No main circuit/PCB integration occurred.

Eight completed27°C forced-bias macro runs show only1.889V GATE−VOUT for LTC4365 at3.2328V/1µA gate load, versus6.412V for LTC4368-1. This favors evaluating LTC4368 with the CSD18543Q3A model, without claiming a guaranteed drive envelope. LTC4368's20V OV-pin rating removes the earlier LTC4365-specific sense-pin absolute-limit problem for the35V divider example. Raw-bank voltage rating, magnetic/source energy, clamp, actual low-voltage timing and MOSFET survival remain unresolved.

Two connected LTC4368/TI CSD18543 nominal runs fail the3V load-step screen:2.56334V minimum with50mΩ assumed source resistance and2.60192V with1mΩ, for an imposed0.2→2A step. Late-window voltage alone therefore does not release the barrier. The exact10µH/15mΩ/100nF slew-network experiment remains unselected; source dynamics, filter damping, gate headroom and fault-energy containment need coordinated redesign and verification.

The later250ms/1mΩ load step also fails the3V screen (2.79881V minimum), despite 6.448–6.464V gate drive before the step; its400ms run completes. The early80ms pair also included an ongoing gate ramp. Both conditions are retained explicitly, without calling the early window steady state.
