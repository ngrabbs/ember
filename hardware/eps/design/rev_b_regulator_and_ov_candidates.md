# EPS Rev B regulator and solar cutoff candidates

Study dated 2026-10-04. The operator selected **preserving regulated 5 V for COMMS recovery down to the currently documented 5 V pack floor**. Carry forward a 3.3 V buck and a 5 V buck-boost stage. The pack floor is a provisional system requirement, not an accepted MJ1/BMS setting. Account for protection, harness and PowerPath drops when defining minimum converter input.

Leading development candidates are **LMR51635XDDCR for 3.3 V** and **LM5177DCPR for 5 V**. Solar OV selection remains open after checking cutoff hysteresis. No KiCad source changed and no complete power stage is accepted. [Voltage envelope](rev_b_source_voltage_and_fault_budget.md) · [BOM handoff](rev_b_bom_and_schematic_checklist.md) · [Calculation evidence](../verification/evidence/2026-10-04_regulator_ov_candidates.json)

The [subsequent sizing and fit checkpoint](rev_b_power_stage_sizing_and_fit.md) expands complete converter reservations to 1200 mm² and records the operator’s 16 mm top standoff. It checks illustrative 2 A rail cases, identifies inductor and low-gate-voltage constraints, and documents the LM5177 EVM’s 78.7 kΩ RT resistor for 400 kHz development. Complete stages remain unaccepted.

## Conversion choices

| Candidate | Manufacturer limits / configuration | EPS disposition |
|---|---|---|
| LMR51635XDDCR | 4.3–60 V input; 3.5 A class; 400 kHz PFM; SOT-23-THN DDC-6; 29 µA typical operating IQ | Leading 3.3 V candidate. Capacity and space are promising; actual shared-rail load and vacuum thermal path still determine acceptance. |
| LMR36520ADDAR | 4.2–65 V input; 2 A class; 400 kHz non-FPWM; HSOIC-8 with thermal pad | Alternative for a smaller accepted current requirement. Larger package and lower current class reduce its appeal for the present shared rail. |
| TPSM365R6 family | 65 V input, 0.6 A maximum output module | Consider only for an explicitly bounded local essential branch. Do not substitute it for the shared rail using the unmeasured 2 A battery estimate. |
| LM5177DCPR | Four-switch buck-boost controller; 3.5–60 V headline input; PSM option; 38-pin HTSSOP, 9.7 × 4.4 mm body | Leading 5 V candidate for the selected recovery requirement. Requires four external MOSFETs, inductor, sensing, compensation and passives. Its IC/package size is only part of the required area. |
| LM5176 | Four-switch buck-boost controller; 4.2–55 V input without external bias | Alternative if complete area, consumption or implementation favors it. No assumption that its example power stage is appropriate for EMBER. |

Primary references: [TI LMR516x5, SLUSF64B Rev B](https://www.ti.com/lit/ds/symlink/lmr51635.pdf), pages 3–5, 12–13 and 17–19; [TI LMR36520, SNVSBF0C Rev C](https://www.ti.com/lit/ds/symlink/lmr36520.pdf), pages 1, 3–5; [TI TPSM365R6 Rev C](https://www.ti.com/lit/ds/symlink/tpsm365r6.pdf); [TI LM5177, SNVSBU4F Rev F](https://www.ti.com/lit/ds/symlink/lm5177.pdf), pages 1, 7–10 and orderable addendum; [TI LM5176 Rev D](https://www.ti.com/lit/ds/symlink/lm5176.pdf).

The LMR51635's advertised maximum duty is 96%; its 400 kHz timing gives about 92% before frequency foldback. Even an ideal 96% duty requires 5/0.96 = 5.208 V to produce 5 V, before losses. Thus the 4.3 V minimum input rating does not imply regulated 5 V output at that input. A buck-only 5 V rail does not meet the selected recovery floor. Essential 5 V consumers stay supplied; nonessential 5 V branches are managed downstream.

For 3.3 V, 400 kHz prioritizes conversion loss over the smallest inductance. PFM improves light-load prospects but creates a variable switching spectrum. Test conducted/radiated noise against COMMS receive performance; compare FPWM only if the measured noise benefit justifies its power penalty. A direct RBF/deployment-permitted source starts the essential converter without an MCU enable dependency. Do not leave EN floating or let reset remove essential power.

Initial arithmetic examples, not a selected passive BOM:

- LMR51635 reference = 0.8 V. 31.8 kΩ top / 10.2 kΩ bottom gives approximately 3.294 V. Complete reference/resistor/leakage/drift analysis must meet the actual consumers' rail limits.
- A 5.6 µH inductor at 400 kHz and 35 V input gives approximately 1.334 A peak-to-peak ripple at 3.3 V by the ideal buck equation. Size saturation above the applicable maximum current limit, not just nominal load plus ripple. Effective output capacitance and compensation compatibility need their own check.
- A 5 V, 2 A output scenario at 90% assumed efficiency requires 2.222 A at a 5 V converter input. This is a sizing case, not a measured load or accepted efficiency. Simultaneous 3.3 V consumers add pack current.

For the LM5177, define autonomous startup, low-input MOSFET enhancement, PSM configuration, current limit, loop compensation and reverse-power behavior before placement. Its quoted 60 µA is a specific quiescent condition, not total switching or no-load spacecraft consumption. Keep BIAS and all sense/control paths inside the interlocked domain. Do not depend on an already-running 5 V rail to cold-start its own converter.

The retrieved LM5177 Rev F text contains apparent editorial discrepancies in §7.3.5–7.3.6 (LM51770 naming and frequency text inconsistent with the recommended 100–600 kHz table). Use the actual LM5177 limits and obtain clarification before relying on affected frequency-selection equations. This is an implementation gate, not a reason to assume the part has a 2.5 MHz capability.

## Solar cutoff comparison and restart constraint

The [ADI LTC4367 Rev D](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4367.pdf), pages 1, 3–4 and 12, provides a 2.5–60 V operating controller driving external back-to-back N-channel MOSFETs. The standard version waits about 32 ms before re-enabling; the -1 version about 500 µs. OV comparator limits are 492.5–507.5 mV; hysteresis is 20–32 mV. These scale to source volts through the divider.

Consider **only as a sensitivity case** a separate OV divider of 660 kΩ / 10 kΩ, both 0.1%, with ±10 nA leakage. Nominal trip is 33.5 V. Conservative independent corners give:

| Quantity | Calculated interval |
|---|---:|
| OV trip | 32.926–34.076 V |
| Reconnect after OV | 30.786–32.734 V |
| Headroom from maximum static trip to 35 V | 0.924 V |

The typical −40°C 4S Voc is 32.164 V. While that falls below the minimum trip in this example, it exceeds the minimum reconnect threshold. **Cold recovery following an OV event is therefore not guaranteed.** The interval also excludes resistor temperature drift, actual array maximum and dynamic overshoot. Reducing hysteresis by increasing the divider bottom resistance does not work: the threshold ratio fixes its source-voltage scaling. The faster -1 variant changes delay, not the required hysteresis window.

Do not accept this example as the circuit or force reconnection with MCU control. The LTC4367 remains a fast-cutoff comparison candidate, conditional on an acceptable restart window or revised source limits. Its 2 µs maximum fault propagation and 6 µs maximum gate-turn-off specifications have stated overdrive/load conditions; they are not a universal 8 µs guarantee for an arbitrary external FET pair. It does not provide current limiting or ideal-diode isolation during normal on-state conduction.

An alternative to evaluate is [ADI LTC2965](https://www.analog.com/media/en/technical-documentation/data-sheets/2965fc.pdf), a high-voltage monitor with separately programmable upper/lower reference inputs and selectable range. It can express the tighter trip/reset window needed here, but **is not a MOSFET driver or complete protection circuit**. Its monitor delay and weak output require a separately verified gate stage; do not connect it directly to a solar P-channel gate on name similarity. Compare the full circuit's fault energy, default-off startup and bias power with the fast-controller option. No monitor MPN/thresholds are frozen.

The autonomous OV circuit must remain downstream of hardware RBF isolation, with its monitor supplied from SOLAR_PERMITTED ahead of its fault switch. Protect LTC4162 VIN and all connected input/sense nodes, preserve battery handover, and prove that downstream VOUT sense/bias cannot cross the RBF boundary. The independent RBF mechanism remains effective regardless of monitor/controller failure or MCU state.

## Required implementation evidence

1. Measure/budget 3.3 V and essential/nonessential 5 V loads, then size each stage independently. Neither the user's battery-current estimate nor a controller part number establishes rail capacity.
2. Reserve complete buck-boost area in the single-board floorplan: controller, four FETs, inductor, shunts, capacitors, compensation, copper and heat path. If it does not fit, compare a smaller complete 5 V buck-boost implementation while preserving the selected recovery behavior.
3. Select and verify component pin maps, package land patterns and power-stage calculations through Konnect before placing a disposable circuit. No library acceptance or new ERC result is claimed here.
4. Resolve the OV trip/reset tolerance window against accepted cold/AM0 array limits, then evaluate FET turn-off, input ringing, capacitor bias derating and restart under limited-energy tests. A fast rising low-impedance bench-source fault is a separate case from normal photovoltaic operation.
5. Verify 5 V startup and regulation with the full pack-path drop at the lower recovery boundary, including source handover and shared-rail load steps. Confirm recovery receive operation and shed transmit/nonessential loads before BMS hard cutoff.

LMR51635 and LM5177 PDFs were downloaded outside the repository; relevant specification pages were rendered and inspected. The LTC4367/2965 specifications were checked through the manufacturer web documents; local ADI PDF download attempts failed, so no local rendered-page verification is claimed for those candidates. The JSON records sources and calculation assumptions. There are no bench or simulation qualification results in this checkpoint.
