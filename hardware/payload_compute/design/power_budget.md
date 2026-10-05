# Payload compute preliminary power budget

Updated 2026-10-04. This study sizes the next payload carrier's power paths
for scheduled observations and simple student-lab operation. It does not
describe a measured board or accept the converted schematic for fabrication.

The provisional full lab load needs about 24.5 W at the board input in a
15 W Jetson power mode. A 9 V / 3 A USB-C source is marginal after reasonable
design margin. Prefer evaluating a 15 V / 3 A USB-C PD source for full lab use,
with a local regulated 5 V Jetson supply. The [schematic-start baseline](schematic_start.md) adopts 15 V / 3 A as
the preferred lab target; the exact bank/cable and measured load remain
unqualified. The separate battery/bench input remains nominally 6.0–8.4 V.

## Requirements and evidence

User decisions are recorded in the [payload README](../README.md): microSD,
three global-shutter spectral cameras, removable bench Wi-Fi, devkit-compatible
fan interface, STM32 dual-CAN supervision, scheduled hardware triggers, and
automatic bench startup selected by jumper. Flight Wi-Fi is omitted; flight
cooling and observation duty cycle remain open.

| Item | Evidence | Limit of the evidence |
| --- | --- | --- |
| Jetson power modes | NVIDIA documents 7/15 W modes and newer 25 W / MAXN SUPER configurations [1] | Mode budgets are not guaranteed instantaneous input-current limits. Exact modules and software configurations remain unidentified. |
| Jetson supply | Local DS-11105-001 v1.1, printed page 34: 4.75–5.25 V recommended when MODULE_ID is low [2] | Exact module applicability must be confirmed. Its 5 A entry is in the absolute-maximum table; do not treat it as an operating-current requirement or transient specification. |
| Camera input | InnoMaker lists 3.3 V on 15-pin connector pin 15 [3] | No whole-camera current rating was established from the documentation read. |
| Fan interface | Local carrier specification, printed page 25: GND, 5 V, tach, PWM [4] | Fan current/startup demand remains unknown. Connector MPN is corrected by NVIDIA separately [5]. |
| Existing main buck | Legacy schematic guide names TPS62933F; TI specifies 3 A continuous [6] | Documentation is not query-back evidence of the saved schematic. It has insufficient allocation if Jetson and fan share its output at the assumed loads. |
| Adafruit 4288 | Product page advertises 5 V USB-A outputs up to 2.1 A [7] | A single output at that rating provides 10.5 W. Shared/per-port simultaneous capacity is unclear. Not a USB-C PD source; do not parallel outputs. |

## Provisional load allocations

These numbers allocate design capacity; they are not expected averages,
measured maxima, or accepted device specifications. Replace each placeholder
with exact-part evidence and measurements before accepting regulator sizing.
The 15 W module row includes module-side storage activity for this estimate;
any additional carrier-mounted storage needs its own allocation.

| Load | Rail | Allocation | Status |
| --- | --- | ---: | --- |
| Jetson in a 15 W mode | 5 V | 15.000 W / 3.000 A equivalent | Published mode budget used as a planning case; input peaks unknown |
| Three cameras | 3.3 V | 2.475 W / 0.750 A total | Assumption: 0.250 A per camera, not a verified InnoMaker rating |
| M.2 Wi-Fi/BT card | 3.3 V | 2.500 W / 0.758 A | Placeholder; card identity and peak/inrush unknown |
| Ground-test fan | 5 V | 1.500 W / 0.300 A | Placeholder; exact fan rating and startup current unknown |
| STM32, two CAN transceivers, monitoring | Always-on 3.3 V | 0.350 W / 0.106 A | Placeholder; includes active-bus allowance, not a verified maximum |
| Camera control, translators, LEDs, auxiliary rails | Mixed, predominantly 3.3 V | 0.250 W | Placeholder; use an explicit rail-by-rail allocation during implementation |
| Total lab load | All regulated outputs | 22.075 W | Sum of the above |

Use an aggregate conversion efficiency of 90% for the first calculation and
85% as a sensitivity case. This includes the carrier converters/path losses
as a simplified model; it excludes losses inside a battery bank. Actual
efficiency depends on input voltage, rail load, topology, and temperature.

`P_input = sum(P_loads) / efficiency`

`I_input = P_input / V_at_board_input`

## Operating cases

| Case | Regulated loads | Input at 90% | Input at 85% | Input with 20% load margin at 90% |
| --- | ---: | ---: | ---: | ---: |
| Lab, Jetson 7 W mode, Wi-Fi and fan | 14.075 W | 15.64 W | 16.56 W | 18.77 W |
| Lab, Jetson 15 W mode, Wi-Fi and fan | 22.075 W | 24.53 W | 25.97 W | 29.43 W |
| Flight illustration, Jetson 15 W, no Wi-Fi or fan | 18.075 W | 20.08 W | 21.26 W | 24.10 W |
| Lab sensitivity, Jetson 25 W, Wi-Fi and fan | 32.075 W | 35.64 W | 37.74 W | 42.77 W |

The 20% margin is an engineering allowance, not a modeled startup waveform.
Passing this arithmetic does not prove transient stability. The flight case
assumes passive cooling and adds no other thermal-management load; no flight
thermal solution has been accepted. The 25 W case is sensitivity only, not a
promise that this carrier or the unidentified modules support that mode.

For the 15 W lab case at 90% efficiency:

| Voltage at board input | Calculated current |
| --- | ---: |
| 6.0 V | 4.09 A |
| 8.4 V | 2.92 A |
| 9.0 V | 2.73 A |
| 15.0 V | 1.64 A |

At 6 V the corresponding flight illustration is 3.35 A, rising to 3.54 A
at 85% efficiency. EPS, battery discharge limits, shared stack connector
contacts, harness resistance, and ground returns must support the actual
allocation. Two parallel power pins do not establish safe current capacity.

## Input recommendation

1. Retain the nominal 6.0–8.4 V battery/bench connector.
2. Evaluate a USB-C PD sink with a preferred fixed 15 V / 3 A contract for
   full lab operation. 45 W is source capacity, not continuous payload draw.
   Check the specific advertised output profile, not just headline wattage.
3. Evaluate a 9 V / 3 A contract for a qualified lower-power configuration.
   With the placeholder 15 W lab case it has only 2.47 W headroom at 90%
   efficiency and 1.03 W at 85%, before startup uncertainty. It does not meet
   the chosen 20% load-margin case. Do not advertise universal 9 V support.
4. Default USB 5 V may power PD negotiation/supervision through an appropriate
   supply path. Keep Jetson off unless a sufficient contract is established;
   show insufficient power instead of repeatedly attempting to boot.
5. Use protected source selection with reverse-current blocking for USB,
   bench, and stack feeds. Prefer a simple documented bench source choice;
   hot source switching is not a required feature. A bench-mode jumper
   selects behavior, not electrical source isolation.

Accepting 15 V requires checking the complete USB input path, capacitor and
switch ratings, converters, transients, and fault response. PD voltage must
never connect directly to the 5 V Jetson supply. STUSB4500 is a candidate for
autonomous negotiation with configurable profiles [8]; exact circuitry,
NVM provisioning, sourcing, and contract-status handling remain open.

The student workflow stays one USB-C cable, automatic startup in bench mode,
and Wi-Fi access-point fallback. Package one validated bank/cable combination
with the lab payload. Check low-load automatic shutoff and behavior when the
bank is recharged or another output is used. A physical shutdown button and
clear starting/ready/power-fault indicators remain proposed usability features.

## Proposed local power rails

| Rail | Preliminary capacity target | Purpose |
| --- | --- | --- |
| Always-on 3.3 V | 0.5 A | Supervisor, CAN, monitors; available with Jetson off |
| Switched regulated 5 V | 6 A class converter, thermally validated | Jetson and ground fan; about 3.3 A allocated in the 15 W lab case |
| Switched 3.3 V | 2 A continuous, thermally validated | Cameras, removable M.2 card, auxiliary logic; approximately 1.58 A if the miscellaneous allowance is placed here |
| Local 1.8 V | Size after translator/control allocation | Locally derived interface-reference rail where needed; verify the origin of the legacy +1V8_MOD net rather than assuming an exposed module supply |

Derive the switched 3.3 V rail directly from the selected input with a buck
if practical, so camera/Wi-Fi loading does not also consume the main 5 V
converter allocation. An LDO from 15 V to 3.3 V at this load would waste
roughly 18.5 W and is unsuitable. The always-on rail also needs a sensible
light-load loss budget.

The 6 A converter class is a proposed hardware-capacity target, not permission
to deliver 6 A to the module or use unrestricted compute modes. Determine
branch current limits from the exact module, connector, and transient data.
For the first lab image, evaluate an explicit 15 W software configuration;
do not rely on the installed image's default mode. Availability of a 25 W
setting does not make it approved for this board.

Validate low-battery operation using voltage at converter pins under load,
including source-selection and cable drops. Validate full-load temperature,
inductor saturation, capacitor effective capacitance, loop response, inrush,
soft start, and current-limit behavior. Main rail power-good should inform
sequencing. Camera/M.2 power and signal isolation must obey module reset and
power sequencing; the always-on STM32 must not drive an unpowered Jetson.

## Energy measurements for observation scheduling

Power ratings alone cannot choose the capture interval. Record input energy
through complete sessions, including boot, readiness, captures, processing,
idle time, storage writes, and graceful shutdown. Concurrent activities must
be counted once rather than adding separate overlapping energy estimates.

`E_session_Wh = integral(P_input_W * dt_seconds) / 3600`

Compare cold-start sessions with keeping Jetson ready between capture batches.
Measure supervisor-only power separately; do not equate the active 0.350 W
allocation with standby consumption. IHU can then schedule regional windows
using measured session energy and EPS reserve constraints.

## Validation before accepting parts

- Identify module, Wi-Fi card, fan, and camera hardware revisions. Obtain
  current ratings and module input/transient requirements.
- Measure boot and workload traces on the available devkits when accessible;
  label devkit measurements separately from final-carrier measurements.
- Measure each camera free-running and triggered, including startup. Measure
  all three acquiring together once the new capture path works.
- Exercise Wi-Fi association/AP startup, image download, and simultaneous
  capture/processing/storage. Exercise maximum fan command and fan startup.
- Load-test candidate regulators from battery-low and PD inputs. Use an
  oscilloscope to check 5 V droop at the module connector as well as average
  current/energy. Verify no unwanted CAN resets during load steps.
- Test PD negotiation failure, cable removal, bank depletion, low-load shutoff,
  restart behavior, and dual-source backfeed protection.
- Verify orderly power sequencing and graceful shutdown separately from
  watchdog-forced recovery. No hold-up energy for a sudden unplug is assumed.
- Reconcile stack input isolation with the existing documented RBF/deployment
  power-isolation gap [9]; acceptance of portable bench power does not resolve
  flight inhibit design.

## Sources

1. [NVIDIA power modes](https://docs.nvidia.com/jetson/archives/r36.4.4/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html)
   and [JetPack 6.2 power-mode changes](https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules/).
2. [Local Orin Nano datasheet](Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf), printed pages 25–27 and 34.
3. [InnoMaker camera hardware and trigger documentation](https://docs.inno-maker.com/home/mipi-cameras/imx296-mipi-cameras).
4. [Local devkit carrier specification](Jetson-Orin-Nano-DevKit-Carrier-Board-Specification_SP-11324-001_v1.3.pdf), printed page 25.
5. [NVIDIA fan connector correction](https://forums.developer.nvidia.com/t/clarification-on-developer-kit-fan-connector-type/313320).
6. [TI TPS62933F specification](https://www.ti.com/product/TPS62933F) and [legacy schematic guide](altium_payload_schematic_guide.md).
7. [Adafruit 4288 product specification](https://www.adafruit.com/product/4288).
8. [STUSB4500 controller specification](https://www.st.com/en/interfaces-and-transceivers/stusb4500.html).
9. [Canonical stack power and CAN allocation](../../../system/interfaces/cskb_pinmap.md).
