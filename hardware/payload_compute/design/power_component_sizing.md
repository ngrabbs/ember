# Payload power component sizing

2026-10-04. Preliminary design values, not a qualified BOM or implemented
schematic. Continues the [power architecture](power_architecture.md).
Run `python3 hardware/payload_compute/design/power_sizing.py` from the repository
root to reproduce the numerical results. The calculator uses the standard library.

## Main regulator choice

Prefer **LMR51460SQDRRRQ1** for the next evaluation. TI's 6–36 V-input,
5 V / 6 A application example is a better starting point for the battery path
than the TPS56637 example beginning at 8 V. This does not establish dropout
performance at the module after cable, eFuse, copper, and connector drops.
Use the datasheet's recommended 4 V input minimum rather than assuming a
product-page summary establishes the operating envelope.

The existing SODIMM power sheet lists two TAJD107K020RNJ 100 µF capacitors,
five 10 µF and two 22 µF capacitors on the 5 V bank: approximately 294 µF
nominal before small bypass capacitors and module capacitance. This conflicts
with TPS56637's recommended 20–100 µF **effective** output-capacitance range.
Do not simply replace the legacy buck while retaining all passives. Reconcile
which capacitors remain, ESR, ceramic DC bias, tolerance, stability, startup,
and discharge. LMR51460 also requires this validation.

| Main 5 V item | Preliminary choice | Reason / remaining qualification |
| --- | --- | --- |
| Frequency | RT 34.8 kΩ, nominal 400 kHz | TI gives 345–455 kHz; explicit resistor avoids conflicting open/short RT wording |
| Feedback | 10 kΩ / 1.91 kΩ, 0.1% | 4.988 V nominal; tenfold lower resistance reduces the 100 nA feedback-leakage contribution to 1 mV; full-temperature error, TCR and sense location still required |
| Inductor | 4.7 µH | Screen RMS rating ≥7.55 A and Isat ≥12 A using 80% rating rule; exact MPN unselected |
| Output capacitance | Target ≥150 µF **effective** initially | Transient sizing below; total bank and stability must be checked together |
| Input capacitance | Two 10 µF, 50 V plus 100 nF, 50 V | Require ≥10 µF effective at maximum input; exact ceramic bias curves unselected |
| Bootstrap | 100 nF, ≥16 V | Connect BOOT to SW; not ground |
| Enable | Hardware default off | Input-valid qualification separate from coarse EN threshold |
| PG pull-up | 10 kΩ to supervisor 3.3 V | Electrical isolation/default behavior required when either domain is off |

At 15.75 V input, 4.7 µH and 6 A output, an extra frequency guard of
345 kHz ×0.9 gives 2.339 A peak-to-peak ripple, 7.169 A peak and 6.038 A RMS.
The additional 10% guard conservatively includes spread spectrum; it is not
a claim that TI guarantees this combined frequency limit. Inductor tolerance
and temperature remain additional corners. The 12 A Isat target also covers
the 9.6 A maximum tabulated high-side current-limit value with 80% derating;
TI notes closed-loop current-limit behavior can differ from production tests.

TI's transient estimate is C >3×ΔI/(f×ΔV). A 3 A step and 0.2 V allowance
at that guarded frequency gives 144.93 µF. This is a planning step size, not
measured Jetson demand. ESR, control response, wiring drop and reference error
also consume the module's 4.75–5.25 V voltage budget. A 6 A regulator rating
does not authorize a 6 A module load or overcome thermal derating.

Follow-up: the [precision monitor budget](precision_monitor.md) allocates
4.91–5.09 V steady at the module and only ±20 mV additional dynamic excursion.
The 0.2 V transient estimate above is historical sizing evidence, not proof
of meeting this tighter requirement. Applying the same rough formula at
20 mV gives about 1.45 mF effective capacitance for the assumed 3 A step.
That is not a recommendation to add this bank: validate actual load steps,
loop response, ESR/ESL, module decoupling, stability and board area before
choosing the network. The regulator and monitor must be qualified together.

## Input-protection dividers

TPS259470LRPWR uses separate EN/UVLO and OVLO dividers. Values below use
0.1% resistors, the datasheet's threshold min/max and ±0.1 µA pin leakage.
The corner calculation uses Vin = Vthreshold×(1+Rt/Rb)+Ileak×Rt.
These windows describe the input eFuse, not the regulated Jetson rail.

The [source-selection follow-up](source_selection.md) supersedes the USB
rows below for the main path: bootstrap is now separate, main UV screening
uses 1.00 MΩ / 100 kΩ and main OV uses 365 kΩ / 29.4 kΩ.
The old USB top resistors also fall below TI's 350 kΩ recommendation for
>5 V/reverse-exposed signal pull-ups. Keep the old calculations only as
historical screens; they are not current recommended input circuitry.

| Branch / threshold | Top / bottom | Rising window | Falling window |
| --- | --- | --- | --- |
| USB UV | 56.2 kΩ / 20 kΩ | 4.495–4.672 V | 4.088–4.264 V |
| USB OV | 250 kΩ / 20 kΩ | 15.916–16.566 V | 14.474–15.119 V |
| Battery/bench UV | 374 kΩ / 100 kΩ | 5.561–5.844 V | 5.055–5.336 V |
| Battery/bench OV | 665 kΩ / 100 kΩ | 8.968–9.439 V | 8.151–8.619 V |

The first battery UV proposal, 390 kΩ / 100 kΩ, could require 6.041 V to
restart at the worst corner, so it was rejected for a nominal 6 V input.
The revised divider admits supervision at 6 V; its low falling threshold
does **not** establish safe battery discharge or sufficient main-buck headroom.
EPS/IHU cutoff rules and loaded converter voltage must qualify main operation.
An OV fault may need source removal to recover, depending on latch behavior;
the wide falling threshold must not be mistaken for a precise restart point.

Use 4.7 nF on dVdt as a starting value: the typical equation gives
0.426 V/ms, approximately 35.25 ms to 15 V or 14.1 ms to 6 V. Actual ramp
limits and tolerances require checking. Hold the switched converters off
during input charging; compute inrush from all selected-bus capacitance.
Leave ITIMER open initially for minimum blanking rather than permitting long
overload intervals. Fault response and source current limits still need tests.

## Current and operating profiles

- USB screening value: RILM =1.30 kΩ gives 2.565 A nominal. An **assumed**
  ±15% limit error plus 1% resistor produces 2.158–2.979 A. This is only a
  screen: TI does not tabulate a guaranteed envelope at 1.30 kΩ, and overload
  timing can allow temporary higher current. Do not claim contract compliance
  from this interpolation. Obtain bounded limits or select a different
  protection implementation before release.
  Follow-up: TI explicitly advertises ±10% accuracy for ILIM >1 A on p.1.
  Using that stated accuracy and a **0.1%** 1.30 kΩ resistor gives a design
  screen of 2.306–2.824 A. The lab budget with 20% load allowance at 14.25 V
  and 85% efficiency is 2.187 A. This strengthens the steady-state design
  basis; the original conservative ±15%/1% screen remains in the calculator
  for comparison. Tabulated electrical-characteristic limits govern over
  a feature summary where they differ. Verify the selected setting across
  temperature and actual source/harness conditions before release. An upper
  steady-state threshold below 3 A still does not imply instantaneous USB
  contract compliance during blanking/short-circuit response.
- Battery/bench screening value: RILM =750 Ω, 0.1%, uses a tabulated point.
  Scaling for resistor tolerance gives approximately 3.956–4.845 A; verify
  the scaling and application behavior before treating those as final limits.
  The 5.5 A rating is not the same as the adjustable overload threshold.
- The 15 W flight estimate draws 3.544 A at 6 V and 85% efficiency without
  margin. The full lab estimate with 20% load margin draws **5.194 A**.
  Neither is automatically accepted over harness/temperature/startup corners.
- Begin battery/bench qualification with an Orin low-power profile represented
  by the 7 W budget case: approximately **3.312 A** at 6 V, 85% efficiency,
  and 20% load margin. Select the actual supported software mode by module
  and software version; a 7 W allocation does not limit boot transients.
- Full lab qualification uses 15 V / 3 A PD. Higher battery power remains a
  design gate; increase protection capacity if measurements require it.

At 5.194 A the eFuse's 45 mΩ maximum tabulated on-resistance alone implies
about 0.234 V drop and 1.21 W dissipation. At 3.312 A it implies 0.149 V and
0.494 W. This illustrates why an input voltage label alone cannot qualify
the low-battery corner. Connector and harness drops add to these estimates.

## Other rail starting values

| Rail | Preliminary values | Qualification still required |
| --- | --- | --- |
| Switched 3.3 V, TPS62933PDRLR | Nominal 500 kHz; 6.8 µH; feedback 31.2 kΩ / 10 kΩ (3.296 V); two 22 µF output ceramics; 100 nF bootstrap | Effective capacitance, stability, actual camera/Wi-Fi steps and inrush; inductor must cover IC current-limit corner, not only allocated load |
| Always-on 3.3 V, LMR36506RRPER | RT 40.2 kΩ, approximately 401 kHz; 33 µH; feedback 100 kΩ / 43.2 kΩ (3.315 V); 47 µF output; ≥4.7 µF effective input plus 100 nF; 100 nF bootstrap; 1 µF VCC | Frequency tolerance, effective capacitance, USB bootstrap startup/draw and current-limit/inductor selection |

Auxiliary ripple is approximately 0.767 A peak-to-peak at 15.75 V, 6.8 µH
and nominal 500 kHz. Always-on ripple is approximately 0.198 A at 33 µH
and nominal 400 kHz. These nominal-frequency calculations are starting
points, not completed tolerance analyses. VCC is an internal regulator node,
not an external supply for unrelated loads.

## Physical acceptance and implementation gates

LMR51460 uses DRR WSON-12: SW leads 1–3, BOOT 4, PG 5, RT 6,
FB 7, AGND 8, EN 9, VIN 10–12, exposed PGND pad 13 (top view).
Connect AGND to PGND at the prescribed small net tie. Do not merge away
repeated physical leads in a custom symbol or omit the exposed pad.

No matching stock symbol was found in the Konnect search. The stock footprint
`Package_SON:WSON-12-1EP_3x3mm_P0.5mm_EP1.5x2.5mm` cites TPS63710 and
has a nominal 1.5 mm exposed-pad width. LMR51460's DRR0012G/E land-pattern
drawings specify **1.3 ×2.5 mm**. It is not accepted for this part. The project-local replacement footprint
uses TI's specified dimensions and has been placed and rendered in a
disposable project. After the local Konnect repair, its full pad geometry,
live instance and default symbol footprint assignment pass query-back checks.
The scratch regulator circuit passes direct ERC with zero errors/warnings.
See the [library acceptance record](lmr51460_library_acceptance.md) for the
physical map and verified evidence. The carrier schematic and PCB are
unchanged; project-local libraries and registration tables have been added.

Before integration, complete the 5 V window monitor, fail-safe enable logic,
input selection hardware, USB current-control guarantee, surge clamp and
exact passives. Then validate minimum loaded input, boot/load transients,
voltage at the module, source faults, shutdown timing and thermal behavior.

## Primary references

- [LMR51460-Q1 datasheet](https://www.ti.com/lit/ds/symlink/lmr51460-q1.pdf), SLUSFR3 August 2024, pp. 3–6, 19–22, 31–33 and DRR0012E drawings.
- [TPS25947 datasheet](https://www.ti.com/lit/ds/symlink/tps25947.pdf), SLVSFC9C May 2026, electrical characteristics and design equations.
- [TPS56637 datasheet](https://www.ti.com/lit/ds/symlink/tps56637.pdf), output-capacitor selection and typical application.
- [TPS62933P datasheet](https://www.ti.com/lit/ds/symlink/tps62933p.pdf), component selection.
- [LMR36506 datasheet](https://www.ti.com/lit/ds/symlink/lmr36506.pdf), SNVSBB6C January 2026, adjustable feedback and Table 8-1.
- [Local Orin Nano datasheet](Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf), supply limits and sequencing.
