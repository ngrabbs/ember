# Payload power-control contract and 5 V monitor screening

2026-10-04. Continues the [power architecture](power_architecture.md).
IHU shutdown semantics below are accepted by the user. The hardware structure
is a design proposal; no new control circuitry has been placed in the carrier.

## Control ownership

In stack mode, IHU's `PAYLOAD_EN` grants operation while high and immediately
removes hardware permission while low. Normal session stops begin over CAN:
stop captures, finish processing/storage writes, request Linux shutdown, then
complete the module power-down handshake. IHU retains permission during that
process and removes it after shutdown acknowledgement. That acknowledgement
must mean the payload domain has shut down, rather than merely that the stop
command was received. CAN loss, stop timeouts and retry limits need defined
firmware policy. An emergency kill may interrupt SD writes.

Bench mode is sampled and latched at supervisor startup. It supplies local
permission for qualified standalone power. Moving a live jumper cannot change
the mode. Flight assembly must prevent accidental bench bypass; this jumper
is not the spacecraft inhibit mechanism.

Keep IHU permission, MCU converter request, MCU module-arm pulse, hardware
voltage qualification and Linux application readiness as separate signals.
Electrical permission alone does not permit camera triggers.

## Hardware structure

Use an always-on, asynchronously cleared run latch. A fresh MCU arm edge sets
it only after source, permission and voltage checks. A fault clears it without
executing STM32 code. Clearing takes priority over an arm edge.

| Signal / function | Required behavior |
| --- | --- |
| `MAIN_BUCK_EN` | AON valid AND selected source valid AND mode permission AND MCU main request AND MCU alive; external default low |
| `5V_WINDOW_OK` | Independently measure at SODIMM VDD_IN and local module ground; monitor powered from AON |
| Run-latch asynchronous clear | Any AON/source/permission loss, main-request removal, 5 V fault or translated module shutdown request |
| Run-latch arm | Fresh edge after complete qualification and discharge; stale high MCU output cannot rearm |
| `POWER_EN` | Run latch through a module-compatible level interface; default off including partial power |
| Module-facing carrier I/O | Enabled only while run latch is set AND module `SYS_RESET_N` is released |
| Camera triggers | Additionally require application ready, cameras armed and an active session; stop immediately on stop/fault |

Do not gate `MAIN_BUCK_EN` directly with its own `5V_WINDOW_OK`: at startup
the 5 V supply is absent, creating a deadlock. Converter startup and module
startup need separate gates. A stuck MCU output must not defeat the IHU hard
kill or module shutdown path.

The module clears its internal SHUTDOWN_REQ latch when POWER_EN goes low.
A combinational AND of MCU run request and SHUTDOWN_REQ could therefore
restart it as soon as the request clears. The external run latch stays off
until a new deliberate arm edge. Firmware must also verify discharged rails
and a minimum off interval before that edge. Bench automatic boot applies at
initial qualified power-up; fault recovery uses bounded retries.

During normal shutdown, keep main 5 V available for the module's shutdown
sequence. Jetson asserts SHUTDOWN_REQ, hardware removes POWER_EN, and the
module controls SYS_RESET_N. Remove the converter after shutdown/discharge
criteria. An IHU hard kill removes converter and module permission immediately,
subject to actual gate delays and stored rail energy.

This latch is an operating interlock, not complete overvoltage protection.
POWER_EN low does not physically disconnect VDD_IN. A buck high-side failure
can expose the module to input voltage; monitor response, output isolation/
clamping and allowable transient energy require a separate design. Loss of a
source has no guaranteed SD-write hold-up.

## Module timing and interfaces

The local NVIDIA design guide, section 6.1, requires the carrier to respond
to module shutdown as soon as possible. It also requires module-facing carrier
3.3 V off within 1.5 ms of SYS_RESET assertion and carrier 1.8 V off within
4 ms. These are load-voltage decay limits, not merely buck-disable deadlines.
Include bulk capacitance, load, leakage and backfeeding in discharge tests.
Do not externally assert SYS_RESET_N during power-down; the module owns that
part of the sequence. Confirm against the current guide for the exact module
before circuit release.

SHUTDOWN_REQ is open drain with a module-side pull-up to VDD_IN. Do not connect
it directly to a non-5-V-tolerant AON input. Likewise, do not assume 3.3 V logic
directly satisfies POWER_EN. Select the actual level interfaces and verify
partial-power behavior. The old +1V8_MOD name does not establish an exported
module supply.

The current downloaded guide is **DG-10931-001_v1.5, February 2026**; see
[run_latch.md](run_latch.md) for the updated startup contract. It removes the
older 400 ms interval and prohibits module-input current limiting that blocks
reverse current. Reconcile proposed module isolation accordingly. Old Nano
compatibility remains separate.

## Voltage-monitor screening

Target steady VDD_IN within 4.75–5.25 V at the connector, including regulator
error, resistor tolerance, input leakage, wiring drop and sensing error.
Calculate fault and recovery thresholds plus worst-case regulator startup.
Hysteresis can make a seemingly suitable monitor prevent startup.

| Candidate | Findings | Disposition |
| --- | --- | --- |
| TPS3702CX50DDCR | Nominal 4.80 V UV / 5.20 V OV in narrow setting; ±0.9% accuracy leaves only 6.8 mV UV and 3.2 mV OV external-error margin. Direct SENSE needs feedthrough protection. Stock symbol gives ordinary output types for its open-drain outputs. | Do not accept as the present interlock. |
| TPS3700DDCR | Falling UV sense can be 387 mV, rising can be 404 mV. Setting worst falling trip at 4.75 V implies possible restart at 4.959 V before divider/leakage error. | Startup margin against the 4.988 V regulator proposal unproven. |
| TPS3703 | Available suffixes matter; nominal UV percentage is asymmetric. Do not infer an available 5 V / ±3% option from the naming chart. | No accepted exact variant. |
| TPS37044BJOFDDFR | Adjustable 0.8 V channels have ±4% windows and ±1% accuracy. A single centered channel consumes nearly all the module window before divider error. Two offset channels may narrow the intersection. | Alternative needing complete hysteresis/startup analysis. |
| TLV6710DDCR | Defined falling UV and rising OV thresholds; external dividers reduce feedthrough at sense inputs. Local database lists C2863066, Extended; cached stock is not purchasing evidence. | Useful comparison; passives below are not accepted. |

TLV6710 screen: separate 110 kΩ/10 kΩ UV and 119 kΩ/10 kΩ OV dividers,
assumed 0.1%, with ±25 nA input bias.
`Vin = Vth × (1 + Rt/Rb) + Ibias × Rt`.

| Boundary | Worst-case DC range |
| --- | --- |
| Falling UV fault | 4.7525–4.8476 V |
| Rising UV recovery / initial startup | 4.7885–4.9678 V |
| Rising OV fault | 5.1089–5.2113 V |
| Falling OV recovery | 4.9801–5.1725 V |

UV leaves only 2.5 mV additional margin, and the upper startup corner is close
to the proposed 4.988 V nominal output. These dividers are **not accepted**,
despite fitting the nominal module range. A 120 kΩ OV top resistor exceeds
5.25 V at its upper corner; 119 kΩ is used only for comparison.

The LMR51460 reference's 0.792–0.808 V limits are specified at 25°C in the
table, not as a guaranteed full-temperature ±1% bound. Feedback leakage and
sense location also matter. Resolve the full output envelope before selecting
a monitor or changing the feedback divider. Evaluate a tighter reference/
comparator circuit if integrated monitors cannot supply adequate margins.

TLV6710 propagation/startup figures are typical, not guaranteed maximum
bounds. Include sense filtering in fault-response tests. Divider attenuation
keeps a 15.75 V feedthrough below approximately 1.315 V at UV sense in the
resistor-only screen. Verify powered/unpowered limits and the full fault
envelope rather than inferring system survival from that number.

## Verification and implementation boundary

Follow-up: [precision_monitor.md](precision_monitor.md) recommends
REF3425IDBVR plus LM2903BIDR, with independently set UV/OV thresholds and
an allocated DC budget that has positive margins. Its corner calculation
passes; physical pin-map acceptance and disposable circuit placement are
complete with checked exports/ERC. Bench validation remains. The scratch buck divider now uses 10 kΩ / 1.91 kΩ at the same ratio.
The integrated-monitor screens above remain as rejected alternatives.

Run [power_control_study.py](power_control_study.py) with Python 3. It checks
20 ideal sequence scenarios and 4,096 steady input combinations: startup
without 5 V, stale MCU arm, shutdown release, source/IHU loss, AON reset,
graceful stop and I/O qualification. It verifies specified digital intent,
not physical gate timing, asynchronous races, rail decay or SD integrity.

The [run-latch study](run_latch.md) now selects exact latch/gates and AON
reset supervisor, with accepted physical maps and exported topology. Select
level interfaces, AON supply and discharge switches next. Accept their
manufacturer pin-to-symbol-to-footprint maps before Konnect placement.
Implement full power/control sheets under one schematic owner, then verify
exports, ERC and renders. The regulator scratch study remains unchanged;
the complete carrier is not fabrication-ready.

## Sources

- [NVIDIA Orin design guide v1.5](Jetson_Orin_Design_Guide_DG-10931-001_v1.5.pdf), printed pages 17–20, section 6.1.
- [TPS3702 datasheet](https://www.ti.com/lit/ds/symlink/tps3702.pdf), SBVS251A, sections 6.5 / 7.3.
- [TPS3700 datasheet](https://www.ti.com/lit/ds/symlink/tps3700.pdf), SBVS187G, electrical characteristics.
- [TPS3703 datasheet](https://www.ti.com/lit/ds/symlink/tps3703.pdf), SBVS249B, threshold table / orderables.
- [TPS3704 datasheet](https://www.ti.com/lit/ds/symlink/tps3704.pdf), SNVSBZ2E, tables 4-1 / 9-2 and sections 6.5 / 8.1.2.
- [TLV6710 datasheet](https://www.ti.com/lit/ds/symlink/tlv6710.pdf), SNVSAV4B, sections 7.5–7.6.
- [LMR51460-Q1 datasheet](https://www.ti.com/lit/ds/symlink/lmr51460-q1.pdf), SLUSFR3, electrical characteristics.
