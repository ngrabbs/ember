# Independent 5 V monitor and output-voltage budget

2026-10-04. Circuit implemented in a disposable study after exact package
acceptance. This closes an allocated **DC design budget**, not measured performance
or the complete overvoltage/transient protection design. Continues the
[power-control contract](power_control.md).

## Recommended implementation

Use **REF3425IDBVR**, 2.5 V reference (local database C187836), and
**LM2903BIDR**, dual comparator, SOIC-8 (C2869804). Both are TI parts listed
as Extended in Konnect's local JLCPCB database. Recheck current supply and
assembly eligibility before BOM release. LM393B's industrial version stops at
85°C; use LM2903B for the -40..125°C component screening range. This range is
not an established flight thermal envelope.

Power the reference from always-on 3.3 V. Connect its force/sense pins as the
manufacturer specifies, enable it with AON power, and use 100 nF input bypass
and an output capacitance within its specified 0.1–10 µF stable range. Start
with 1 µF effective at 2.5 V; exact capacitor remains to select.

Power the comparator from the protected selected input bus, with 100 nF
local bypass. Its guaranteed offset specifications require at least 5 V;
hardware source qualification must inhibit module operation outside the
qualified range. Initial USB bootstrap does not authorize Jetson operation.
Avoid powering this comparator from 3.3 V: its common-mode limit would
exclude the 2.5 V reference. At comparator supply >=5 V, the reference fits
the worst-case supply-minus-2-V common-mode limit.

Use independent dividers from Kelvin-sensed module VDD_IN to local module
ground, rather than from the buck's switching loop:

| Comparator | Top / bottom | Input polarity | Nominal trip |
| --- | --- | --- | --- |
| UV | 9.31 kΩ / 10 kΩ | Divided rail to IN+, reference to IN− | 4.8275 V |
| OV | 10.7 kΩ / 10 kΩ | Reference to IN+, divided rail to IN− | 5.1750 V |

Both comparator outputs pull low on fault. Pull up to AON 3.3 V, initially
10 kΩ. A 550 mV maximum low output at <=4 mA over temperature is compatible
with a receiver having an appropriate low-input limit; accept the exact
receiver and pull-up circuit before wiring. The outputs may form a wired
fault signal because they are open collector. Keep correct symbol pin types.

Use **0.1% resistors with <=10 ppm/°C TCR** for these dividers. Exact passive
MPNs have not been accepted. Do not substitute common 1%/100 ppm resistors.

The external run latch supplies fault memory. No comparator positive-feedback
hysteresis is included in this first proposal: once either output detects a
fault, the run latch stays cleared despite comparator recovery. Startup must
qualify stable monitor outputs before issuing a fresh arm edge. Noise can
still cause nuisance shutdowns; measure it and size any sense filter using
the fault-delay budget. Do not add large capacitors just to suppress faults.

## Worst-case DC budget

Run [precision_monitor_study.py](precision_monitor_study.py). Each threshold
uses all 64 corners of reference, comparator offset, divider tolerance, bias
and module-referred sensing error.

| Contribution | Bound used | Basis |
| --- | --- | --- |
| Reference total error | ±0.20% | Allocated limit: ±0.05% initial, 6 ppm/°C ×165°C box-method span =0.099%, line/load contribution, plus remaining assembly/aging reserve |
| Each resistor | ±0.30% | 0.1% initial +10 ppm/°C ×165°C =0.265%, rounded up independently |
| Comparator offset | ±4 mV | LM2903B D/SOIC full-temperature limit; DGK/VSSOP has a different bound |
| Comparator bias | ±50 nA magnitude | Conservative symmetric screen of the full-temperature input-bias limit |
| Sensing/layout error | ±10 mV at module | Allocated PCB/ground/filter error; must be demonstrated |

Reference reflow shift, long-term drift and thermal hysteresis are not all
guaranteed maximum specifications. The ±0.20% allocation must be verified
after assembly and over qualification conditions; it is not claimed as an
unconditional REF3425 lifetime guarantee. Reject or rework units outside the
budget. Adding another consumer to the reference requires redoing load/error
and startup analysis.

| Result | Bound |
| --- | --- |
| UV falling fault / rising recovery (no added hysteresis) | 4.7858–4.8694 V |
| OV rising fault / falling recovery (no added hysteresis) | 5.1299–5.2203 V |
| Required healthy module voltage, steady | 4.91–5.09 V |
| Additional allowed ripple/transient departure from steady | ±20 mV |
| Resulting required healthy dynamic envelope | 4.89–5.11 V |
| Worst UV guard above 4.75 V module limit | 35.8 mV |
| Worst OV guard below 5.25 V module limit | 29.7 mV |
| Healthy dynamic margin from UV / OV fault corners | 20.6 / 19.9 mV |

The no-hysteresis assumption excludes any unspecified intrinsic comparator
effects; the sensing reserve and physical threshold test must cover these.
These guards are **voltage margins**, not proof that a fast fault is interrupted
before crossing a module limit. Comparator response depends on overdrive,
filters add delay, and stored/through-fault energy remains separate.

## Main regulator refinement

The scratch LMR51460 feedback divider is now **10 kΩ / 1.91 kΩ**, replacing
100 kΩ / 19.1 kΩ through Konnect. The ratio retains 4.9885 V nominal. At the
100 nA maximum feedback-leakage magnitude, its output contribution decreases
from 10 mV to 1 mV. Divider current increases from about 42 µA to 419 µA
(approximately 2.1 mW at 5 V), a small cost relative to the payload load.
Exact resistor parts/TCR still need acceptance.

Use the required 4.91–5.09 V steady envelope as an acceptance gate for the
complete regulator at the module connector. The datasheet's reference limits
are specified at 25°C, so full-temperature regulation remains unresolved.
Kelvin feedback can compensate output-copper drop if routed according to
TI's feedback-layout guidance; AGND/PGND connection and sense-return errors
must be included. A room-temperature passing measurement cannot close the
full operating envelope.

Before accepting the regulator, measure source extremes, minimum loaded
battery voltage after protection/harness losses, startup, load steps, fan/
camera/Wi-Fi switching and temperature. The ±20 mV dynamic allowance is a
design requirement, not the earlier rough 0.2 V capacitor-sizing allowance.
That earlier capacitor estimate is now insufficient as evidence: size and
test the complete network for this tighter limit. If the converter cannot
meet the budget, revise regulation/decoupling or threshold design together.

## Startup, fault containment and acceptance gates

Reference settling is listed as typical, not a guaranteed maximum. Keep the
run latch hardware-cleared through AON/source startup, then qualify reference
health and monitor status before arming. Do not rely solely on a fixed delay
copied from a typical settling-time figure. Reference collapse while main 5 V
is present should assert OV in this polarity arrangement; verify actual
power-up, power-down and partially powered behavior on the bench.

The comparator's input ratings permit inputs above its own supply within
the datasheet limits. Supplying it from the selected bus also keeps normal
and buck-feedthrough sense voltages below that bus. Verify complete absolute
maximum, common-mode and source-collapse cases before accepting protection.
This is not permission to expose Jetson to feedthrough. Choose output
isolation/clamping and prove response/energy containment separately.

The [physical pin maps and package lands](monitor_library_acceptance.md) are
accepted for both exact ICs. The [bounded monitor study](validation/payload_monitor_acceptance/README.md)
is placed/wired, rendered and checked: zero ERC errors/warnings, no unconnected
pins, floating wire endpoints, named-net shorts or heuristic orphans. Its eight
exported nets match the intended topology. This is evidence of correct design
connections, not physical threshold/timing qualification. Passive MPNs are pending.

Next: complete the AON reset, run latch and level interfaces before integrating
power sheets into the carrier. Preserve the accepted CAN graceful-stop and
PAYLOAD_EN immediate-kill contract; no automatic rearm after a hardware fault.

## Manufacturer sources

- [REF34 datasheet](https://www.ti.com/lit/ds/symlink/ref34.pdf), SBAS804G, April 2026, sections 5, 6.5, 7 and 9.
- [LM2903B/LM393 family datasheet](https://www.ti.com/lit/ds/symlink/lm393.pdf), SLCS005AH, April 2025, sections 5.6, 7 and 8.
- [LMR51460-Q1 datasheet](https://www.ti.com/lit/ds/symlink/lmr51460-q1.pdf), SLUSFR3, feedback electrical characteristics and layout guidance.
