# Recovery protection circuit selection

## 2026-10-23 bank correction and new coupled checks

The upstream converter bank is now **five EEHZA1H680P 68 µF / 50 V hybrids plus eight CGA5L1X7R1H106K160AC 10 µF / 50 V ceramics**. It replaces the previous 35 V / 25 V bank; C16 remains 100 nF / 50 V. Nominal capacitance is 420 µF, initial high tolerance is 496 µF, and the endurance-plus-tolerance sensitivity is 618.4 µF plus C16. Use a **650 µF upstream development allocation**, with staged charging of the downstream bank; the earlier 500 µF arithmetic is historical. Cold/bias/endurance bounds remain subject to manufacturer data and measurements.

The [current bank analysis and acceptance gaps](../verification/protection/bank/README.md) and [34-part native BOM/render evidence](../verification/protection/bank/native/README.md) supersede the earlier bank-specific BOM and screenshots. Existing endpoint names and the PCB are unchanged. The subsequent [latch and MOSFET follow-up](rev_b_5v_latch_and_mosfet_survival.md) installs the bleeder/timing/feedback correction and source slew limiter. Its 83-part BOM, current renders and screening supersede the original protection timer/divider values below. Guaranteed hot SOA, low-VCC accuracy and physical qualification remain open.


2026-10-23. Complete **development circuits** selected and built as an isolated
study. This advances the [architecture checkpoint](rev_b_5v_recovery_fault_containment.md);
it does not qualify MOSFET survival, integrate the circuits into Rev B, or release
a board for fabrication. The fabricated Rev A and recovery converter study are unchanged.

## Selected functions and parts

The source barrier uses **LTC4364HDE-2#PBF** with autonomous restart. The shared
5 V barrier uses **LTC4364HDE-1#PBF** with latch-off and a deliberate hardware
reset input from independently powered EPS control. Both have common-source
back-to-back N-channel MOSFETs, analog output clamping, current limiting and a
stress timer. Their operation does not require firmware.

The selected hardware values, complete pin maps, capacitor populations and
native-build boundary are in the [circuit contract](../verification/protection/native_build_contract.md).
The [executable circuit generator](../verification/protection/run_protection.py)
includes those hardware networks plus clearly separated simulation fixtures.
Fixture voltage sources, leakage/reference injections, parasitic lumping and
ideal loads are not schematic components.

| Function | Source barrier | Shared 5 V barrier |
|---|---|---|
| Input/output | `SOLAR_PERMITTED` → `VIN_CHG` | `5V0_RECOVERY_REG` → existing `+5V` |
| Pass/reverse FET | One IRLR2908TRPBF each | Three IRLR2908TRPBF in parallel per function |
| FB divider | 25.8 kΩ / 1 kΩ; nominal 33.5 V | 3.20 kΩ / 1 kΩ; nominal 5.25 V |
| Sense resistance | 20 mΩ, CRF1206-FZ-R020ELF development identity | Same |
| Timer | 100 nF C0G | 220 pF C0G |
| Gate slew | 1 nF C0G, series 2.2 kΩ to ground | 68 nF C0G, series 2.2 kΩ to ground |
| UV divider | 50 kΩ / 10 kΩ, 10 nF filter | 20 kΩ / 10 kΩ |
| Startup/retry inhibit | 27.8 kΩ / 1 kΩ, 1 nF; nominal 36 V | OV grounded; latch-off variant |
| Input conditioning | DC-blocked 1 Ω / ≥2 µF snubber, SMBJ60A | XAL1510-472MED, ≥2.5 µH effective; ≥2 µF local input capacitance; SMBJ36A |
| Bias | 100 Ω, 1N4148W, ≥4.7 µF effective isolated reservoir | 100 Ω, 100 nF |
| Protected output bank | 68 µF hybrid + 3 × 10 µF ceramic nominal | 2 × 100 µF hybrid + 8 × 22 µF ceramic nominal |

All power FETs are 80 V / ±16 V DPAK devices with physical 1 G / 2 D-tab / 3 S.
Use [Infineon's exact IRLR2908 datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlr2908-datasheet-en.pdf),
including its linear SOA; the switching-current and avalanche ratings do not
establish survival in a surge-stopper application. Parallel FETs reduce normal
loss; equal sharing in linear operation is not accepted as a safety assumption.

Each controller drives its pass gates through 4.7 kΩ. An MMBT3906LT1G PNP has
emitter at the pass gates, base at HGATE and collector returned through 100 Ω
to COMMON. A 1N4148W from HGATE anode to gate cathode protects its reverse BE
junction. This buffer preserves slow startup but speeds turnoff when the
controller uses its weak shutdown pull-down. Both gate functions have
**Littelfuse SMBJ8.5A**, cathode gate/anode COMMON. Gate-slew and timer
capacitors use 100 V C0G parts; gate-to-ground voltage exceeds a 50 V rating
during the high-source sensitivity cases.

The source snubber is **CRCW12061R00FKEAHP** in series with four
GRM32ER72A225KA35L capacitors to ground. Its minimum effective capacitance is
2 µF through 60 V. The same capacitor population supplies the rail's local
input bank. Four more provide the source's diode-isolated VCC reservoir;
that bank requires ≥4.7 µF through 9–35 V. These are acceptance requirements,
not established Murata DC-bias guarantees. Pulse 100 Ω resistors are
CRCW1206100RFKEAHP. Divider resistors are TNPW0603, 0.1%, 25 ppm/K. Exact ordering codes are
constructed from verified manufacturer rules and persisted in the native BOM;
procurement confirmation remains open.

The [Littelfuse SMBJ family](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf)
identities are deliberate. The source **60 V** TVS must tolerate a persistent
60 V input without acting as a DC shunt. Its full-current clamp specification
exceeds 80 V, so it does **not** independently guarantee protection of the
80 V parts. The bounded source network and RC damping must establish the
actual peak. The rail's **36 V** TVS absorbs inductor turnoff pulses at PIN;
it is not the 5 V clamp and must not be asked to absorb sustained bus power.

## Restart, startup and power budget

Converter feedback and its original output bank stay **upstream** of the rail
barrier. Connecting feedback to disconnected `+5V` would be unsafe. Naming
`5V0_RECOVERY_REG` is local to this new study; existing converter wiring has
not yet been migrated.

COMMS TX remains default off. IHU must default its heavy loads off and qualify
its own local rail before enabling them. Unavoidable startup load is allocated
≤0.5 A; the full provisional 2 A load comes later. Return to that state after
a trip. The modeled maximum downstream bank is 551.2 µF, including the
100 µF external allocation. Local minimums are 112 µF bulk at ≤0.4 Ω cold
ESR, plus 48 µF ceramic at low ESR. Physical data and measurements must close
both minimum and maximum bank bounds.

`REC5_RESET` drives an MMBT3904LT1G through 47 kΩ with a 100 kΩ base-emitter
pull-down. A deliberate 2 ms pulse pulls UV low. It does not bypass clamp or
current limits; do not retry indefinitely. The independent control domain's
own 3.3 V protection and reset policy remain open. FLT pull-ups are 47 kΩ to
that domain. ENOUT and SHDN are intentionally unused; an external ENOUT
pull-up can produce a false indication at low output voltage.

At 2 A, a conservative development drop allocation is 20 mΩ shunt + 10 mΩ
guard inductor + two banks of 30 mΩ FETs divided by three, multiplied by a
hot-resistance sensitivity. With 1.5× FET resistance, this is about 120 mV;
at the converter's 4.919254 V lower corner it leaves approximately 4.799 V
before stack wiring. With 2× it leaves about 4.779 V. The hot multiplier is
not a guaranteed manufacturer maximum. Consumer minimum voltage, wiring
loss and actual case temperature must be accepted before claiming headroom.
The final XAL1510-472MED replaces XAL1010-472MED after the modeled guard
current reached about 30 A, above the smaller part's 25.4 A typical 30% loss
reference. The [larger part](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal1510/xal1510-472/)
has a 39 A typical reference, 3.8 mΩ maximum DCR at 25 °C and a
15.4 × 16.4 × 10 mm body. It still needs hot magnetic qualification. The
unchanged simulation uses 2.5 µH / 10 mΩ as explicit conservative development
requirements, not a generated nonlinear magnetic model.
The 16 mm top standoff accommodates the nominal inductor height, but complete
2D/3D fit is still open; six DPAKs and these capacitor banks are substantial.

## Transient and survival checks

Saved results and reproduction instructions are in the
[verification record](../verification/protection/README.md). They use LTspice
26.0.2 with installed ADI models, explicit capacitor ESR/ESL, low-input startup,
slow OV, converter LC faults, a low-impedance input/output bridge, output and
input shorts, prebias, deliberate reset, cold/hot sensitivities and persistent
source faults. A finite charged-reservoir bridge is separate from a stiff
35 V source fixture. Neither fixture proves that every internal converter
failure path is represented.

Important rejected arrangements are retained as evidence:

- A delayed cutoff without the additional rail inductor exceeded 5.5 V.
- A slow gate capacitor without the PNP discharge buffer left a long linear
  tail and much larger pass-FET energy.
- The earlier source gate/bias arrangement repeatedly ramped into a weak PV
  short. Diode-isolated bias, the smaller source gate capacitor and OV retry
  inhibition removed that high-dissipation behavior in the stated fixtures.
- A small 12 V gate zener model allowed >16 V VGS during a source short.
- The undamped source-input model reached about 115 V. A 36 V input TVS
  suppressed that pulse but was rejected because it dissipated tens of watts
  during a persistent 60 V source fault. The selected DC-blocked RC network
  and 60 V TVS avoid that DC failure mechanism.

Do not use a single joule limit for MOSFET acceptance. Check both devices'
actual VDS, VGS, current direction, pulse duration, repetition, SOA trajectory
and initial case temperature. The analysis reports pass and reverse device
energies separately and includes the PNP, shunt and TVS stresses. Its Foster
thermal comparison uses an intentionally conservative hand-read envelope of
the IRLR2908 transient thermal curve, with **the entire parallel pass bank's
power assigned to one FET**. It is not a manufacturer electrothermal or
hotspot model and assumes a fixed case temperature.

Package inductance matters: the zero-package-inductance source-short model
produces about 162 A reverse-channel/body pulse, exceeding the 150 A pulsed
body-diode rating. With the datasheet's typical 4.5 nH drain / 7.5 nH source
inductances, the modeled pulse is about 41 A and internal gate peaks remain
below 11 V. **This is a sensitivity, not permission to disregard the 162 A
case.** Minimum actual loop/package inductance, diode recovery, shunt pulse
capacity, measured waveforms and hot SOA must close before survival is
accepted. Do not label a typical-model simulation “MOSFET qualified.”

## Remaining acceptance gates

1. Accept actual solar voltage/current, local reservoir and harness bounds.
   Development uses ≤1 A PV current, ≤1 µF upstream reservoir and ≤1 µH
   harness, with 60 V abnormal-source tests. This is unrelated to the estimated
   2 A 5 V load; that estimate does not establish PV fault current.
2. Confirm [LTC4364](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4364-1-4364-2.pdf)
   FB accuracy and dynamics at 5–12 V VCC. Its cited FB accuracy row covers
   12–80 V. Resistor/reference sensitivities below 12 V are **not** a guaranteed
   extension of that specification. OV hysteresis also lacks a guaranteed
   bound sufficient to close cold reconnect by calculation alone.
3. Accept allowable receiving-board peak voltage/duration. The 5.5 V ceiling
   is provisional, not a COMMS/IHU absolute-maximum approval.
4. Obtain effective capacitor/ESR data, inductor minimum L through fault
   current and temperature, TVS dynamic/leakage data, shunt pulse curves,
   PNP corners and resistor pulse acceptance. The inductor's typical saturation
   current is not a guaranteed minimum inductance curve.
5. Perform limited-energy bench faults, low-battery startup, absent-battery
   operation, handover, reset repetition and cold/hot measurements. Actual
   pack protection, RBF permission wiring, 3.3 V containment, branch fuses and
   a protector's own short failure remain separate system work.
   The previously observed upstream bank overstress prompted the installed
   50 V bank correction documented at the top of this record. New fixtures
   include the actual converter shunt and individual capacitor branches;
   their numerical results supersede the old bank-specific peaks. Effective
   capacitance, pulse ratings and arbitrary stiff-source faults remain open.
6. Complete native schematic presentation, final component sourcing, physical
   fit and integration. S11 visible Arial/orientation-aware fields remain
   limited by the exposed Konnect API; metadata does not count as compliance.
   S03 four-way-junction ERC severity persistence is also API-blocked; the
   separate geometry check passes but does not satisfy that settings gate.
   Export page IDs remain inconsistent despite a verified attached hierarchy.

The component-screening range remains −40…+85 °C. Neither the electronics nor
the battery assembly has a qualified operating-temperature range yet.
