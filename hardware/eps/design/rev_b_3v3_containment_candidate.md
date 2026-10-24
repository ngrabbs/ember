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
and symbols; no model has been changed or simulated for this boundary yet.

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
