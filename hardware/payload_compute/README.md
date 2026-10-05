# Payload Hardware

## Layout

- `design/`: payload design concepts and constraints
- `kicad/`: payload board source files — the Altium project converted to KiCad 10
- `altium/`, `altium-carlos/`: local-only Altium sources — **not tracked**
- `bringup/`: validation plans and logs
- `releases/`: build-ready release packages

## Board source status

The [new prototype project](kicad/payload_compute_rev_next/payload_compute_rev_next.kicad_pro)
now contains the root hierarchy, AON supply, reset/run core, three limited
reverse-blocking bootstrap feeds, startup mode/source locks, live IHU
permission and external watchdog/reset qualification. Raw-source and main-bus
qualification, USB PD and main admissions remain upcoming capture stages.
The source-choice outputs do not yet establish safe power admission.
See [stage evidence and open boundaries](kicad/payload_compute_rev_next/README.md).
Review the [current six-sheet schematic PDF](kicad/payload_compute_rev_next/payload_compute_rev_next-stage3.pdf).

Use the [next-carrier schematic baseline](design/schematic_start.md):
power/source control, STM32 dual CAN, module/camera interfaces, debug and
portable-bench operation are defined for staged prototype capture. The
converted carrier remains a reference, not the accepted new circuit.

See the [preliminary power budget](design/power_budget.md) for input-power
estimates, proposed local rails, USB-C PD options, and measurement gates.
The [power architecture](design/power_architecture.md) develops the input
protection, regulator shortlist, USB bootstrap, source selection, and
sequencing behavior. It remains a circuit proposal pending detailed design.
The [eFuse package acceptance](design/efuse_library_acceptance.md) now records
all ten physical leads, a disposable placement and separate copper/stencil
renders. The [USB admission study](design/admission_control.md) now contains
a wired input circuit and raw-powered enable clamp. Its exported topology
passes; temperature, low-state leakage and ramps remain unqualified.
The [AON supply budget](design/aon_supply_budget.py) replaces the earlier ±2%
assumption with the preferred PFM regulator's asymmetric DC allocation;
startup and transient qualification remain open. The
[AON regulator study](design/aon_regulator.md) now has an accepted prototype
package map, a standalone schematic and zero-error/warning ERC. Both new
circuits remain outside the carrier.
The [component sizing study](design/power_component_sizing.md) adds regulator
passives, protection threshold corners, and separate USB/battery qualification
profiles, with a [reproducible calculator](design/power_sizing.py).
The [disposable 5 V circuit study](design/validation/payload_power_acceptance/README.md)
now has a schematic, render, exported topology, and zero-error/warning ERC.
The [regulator library acceptance record](design/lmr51460_library_acceptance.md)
documents corrected footprint geometry and passed library acceptance after
the local Konnect repair. This circuit has not been integrated into the carrier.
It recommends evaluating 15 V / 3 A PD for full lab operation; this supersedes
the earlier fixed-9-V proposal as the preferred candidate, pending acceptance
and validation. Regulator candidates are shortlisted; the battery bank and
final regulator qualification remain open.
The [power-control contract and monitor screening](design/power_control.md)
records the accepted IHU hard-kill semantics, a fault-cleared run latch,
module I/O discharge constraints and unresolved 5 V monitoring margins.
Its [executable study](design/power_control_study.py) checks ideal logic and
DC divider corners; it does not qualify the hardware timing.
The [precision monitor budget](design/precision_monitor.md) uses
REF3425IDBVR plus LM2903BIDR. Their [physical pin maps](design/monitor_library_acceptance.md)
are accepted, and the [disposable monitor circuit](design/validation/payload_monitor_acceptance/README.md)
has passed ERC and exact exported-connectivity checks. Its DC corners pass
the allocated limits; regulator transients, passive selection and hardware
timing still require qualification. The scratch feedback divider
uses 10 kΩ / 1.91 kΩ to reduce leakage error at the same nominal voltage.

The [run-latch/startup study](design/run_latch.md) now has an AON reset supervisor,
separate converter gates and a fault-cleared latch, with accepted package maps
and checked exported connectivity. Four upstream electrical boundaries remain
unimplemented and are recorded in ERC. Module level interfaces, bench-mode
sampling and rail discharge are the next circuit blocks. NVIDIA guide v1.5
supersedes the preliminary local startup timing evidence.

The [bench-mode sampler](design/bench_mode.md) now locks the physical jumper
until AON reset and preserves it through ordinary STM32 resets. Its disposable
schematic has checked connectivity and one declared external-reset ERC error.
PAYLOAD_EN is proposed as 3.3 V push-pull, default low, per the user selection;
the IHU receiver and mode/source permission logic now have a checked
standalone circuit study; source-admission hardware remains open.

The [IHU receiver and permission proposal](design/permission_control.md)
checks 512 combinations, includes both-source rejection and default-low IHU
reception, and preserves fresh-arm recovery. Its disposable KiCad schematic
is wired and its exported topology passes all 512 combinations. NAND package
acceptance is complete. ERC retains one external-reset error and two boundary
warnings. See the [study evidence](design/validation/payload_permission_acceptance/README.md).
The PCB is a package-validation scratch board; carrier integration is pending.

The [source-selection study](design/source_selection.md) now separates AON
bootstrap from the three default-off main paths, defines immutable startup
source choice and independent source-health feedback, and checks 32,768
admission combinations. It revises USB main UV/OV screens and identifies
the battery current-limit and bootstrap-budget gaps. Source switches, their
fail-off interfaces remain to be implemented. The new project's AON supply
and bootstrap feeds are captured; see the
[bootstrap input/restart contract](design/bootstrap_input_contract.md) and
[exact bootstrap package acceptance](design/bootstrap_library_acceptance.md).

### Payload compute requirements discussion — 2026-10-04

These requirements describe the next revision. The converted schematic and
PCB have not yet been updated or validated against them; older pin-map and
schematic-guide assumptions must be reconciled during implementation.

Accepted mission and operating requirements:

- Capture and retain three spectral images, process them onboard for wildfire
  detection, and report compact results to the IHU. Channels use 750, 770,
  and 780 nm filters. Capture cadence and regional observation windows remain
  experimental, with battery usage a principal constraint.
- Target the existing Jetson Orin Nano module and retain intended compatibility
  with the team's older Nano modules using separate software builds. Exact
  module identities, storage arrangements, and interface compatibility still
  require verification.
- Use microSD storage; do not add an NVMe SSD interface.
- Retain captures in a bounded rolling store: overwrite the oldest ordinary
  captures when needed and protect wildfire detections within a reserved
  storage budget. Reserve operating-system/free-space headroom. Define the
  protected-store-full behavior, quotas, and retention of raw/processed data
  before implementation; protected captures cannot grow without bound.
- Retain the three original raw frames and processing results for each stored
  capture, with JPEG previews for the bench web interface.
- Use the Koenig payload's three global-shutter cameras. Its current hardware
  documentation identifies InnoMaker CAM-IMX296RAW, which differs from the
  Raspberry Pi camera-board assumption in the existing carrier pin map.
  Confirm exact camera hardware before accepting connector or trigger wiring.
- All camera testing so far has used a Pi 4. The hardware-trigger attempt with
  the Arducam mux did not work. Simultaneous exposure and successful receipt
  of all three frames remain validation goals on the new carrier.
- Provide a removable M.2 Wi-Fi module for standalone bench operation and the
  Koenig web-interface workflow. Flight operation omits the Wi-Fi module.
- Preserve automatic Wi-Fi access-point fallback from the Koenig workflow:
  join a configured network when available; otherwise host an access point
  for laptop access without requiring command-line setup. Verify this behavior
  with the selected Wi-Fi card and each supported Jetson software image.
- Preserve mounting provisions and clearance for the ground-test fan and heat
  spreader. Provide the same mating fan interface as the Orin Nano devkit.
  NVIDIA's connector correction identifies ACES 50275-00471-003, four pins,
  1.25 mm pitch. Confirm physical mating, pin numbering, supply/current,
  PWM/tach electrical interfaces, and footprint before accepting a part.
  The compact flight thermal/mechanical arrangement remains unresolved;
  retaining a fan connector does not establish a flight cooling solution.
- Target JLCPCB fabrication. Assembly scope and exact parts remain open.

Accepted control and power architecture:

- Add an STM32 supervisor with two built-in CAN controllers and separate
  external transceivers for stack CAN A and CAN B. Exact MCU/package and
  failover behavior remain open; STM32G0B1 is an initial candidate only.
- IHU authorizes observation sessions and supplies capture parameters and
  schedules. STM32 generates scheduled hardware triggers after Jetson reports
  the cameras armed; also support a single-capture command. Sessions are
  bounded by duration and/or capture count.
- Jetson owns camera configuration, image acquisition, storage, processing,
  and the bench web interface. STM32 owns CAN communication, power sequencing,
  trigger timing, and watchdog recovery.
- Provide a standalone bench power connector for the nominal 6.0–8.4 V
  battery range. A 12 V adapter input is not required. Bench/stack source
  selection, protection, and local peripheral supplies remain to be designed.
- Provide a bench-mode jumper: with bench mode selected at startup, valid
  standalone power automatically boots Jetson and the web interface. Stack
  mode waits for IHU authorization. Define mode sampling and source selection
  so a fitted jumper cannot accidentally override flight controls.
- Keep the supervisor available while board power is present, with the Jetson
  and associated payload loads on a switched domain. Reconcile this with the
  existing direct PAYLOAD_EN-to-buck connection and stack-powered peripherals.
- Request graceful shutdown and allow image writes to finish before normal
  power removal. Normal stops use CAN while IHU retains permission;
  PAYLOAD_EN low is an immediate hardware kill and may interrupt SD writes.
  STM32 may power-cycle an unresponsive Jetson using bounded
  retries, report recovery events to IHU, and defer repeated-failure policy
  to IHU. Timeouts and retry counts remain open.

Student-lab power/access baseline:

- Preferred USB-C PD input: 15 V / 3 A through protected independent bootstrap
  and main paths, locally regulated to 5 V for Jetson. USB 5 V powers supervision
  only. Exact bank/cable qualification and actual attach/load budget remain open.
- The suggested Adafruit 4288 USB-A 5 V / 2.1 A bank is not selected for full
  payload operation. Do not parallel its outputs.
- A startup-sampled bench jumper enables automatic boot and Koenig Wi-Fi AP
  fallback. Provide ready/fault indication, web/button graceful stop, and no
  insufficient-power boot loop. Source choice locks until AON power cycle.
- STM32 owns two CAN paths, explicit-direction application UART, hardware
  trigger/strobe timing, power sequencing and independent watchdog recovery.
  Jetson and MCU have separate console access; MCU also has SWD.
- Camera trigger circuitry uses the exact InnoMaker optocoupler/header revision;
  triple Jetson acquisition and Jetson trigger driver support remain validation
  gates. Detailed contracts and open hardware gates are in the baseline above.

References: [Koenig hardware setup](https://github.com/ngrabbs/koenig_wildfire/blob/main/docs/hardware_setup.md),
[STM32G0B1 datasheet](https://www.st.com/resource/en/datasheet/stm32g0b1ve.pdf),
[STUSB4500 product information](https://www.st.com/en/interfaces-and-transceivers/stusb4500.html),
[Adafruit 4288 battery bank](https://www.adafruit.com/product/4288),
[NVIDIA fan connector correction](https://forums.developer.nvidia.com/t/clarification-on-developer-kit-fan-connector-type/313320),
and the [stack pin map](../../system/interfaces/cskb_pinmap.md).

`kicad/cubesat_orin_nano_carrier` is the converted Jetson Orin Nano carrier:
87 footprints, a flat 4-page schematic (root + `Cameras`, `M2_USB_UART`,
`SODIMM_Power`), 650 track segments — mostly the PCIe escape from J1. Board
design in this repo is KiCad-only per
[`hardware/conventions/kicad_jlcpcb_design_rules.md`](../conventions/kicad_jlcpcb_design_rules.md);
the Altium trees are kept locally as the conversion source and are ignored by
git (see the Altium block in the root `.gitignore`).

## Mechanical — CSKB / PC/104 envelope

The outline, mounting holes and H1/H2 positions are held **identical** to
`AMSAT/sdrb/hardware/pcb-variants/sdrb-cskb`, which is the reference that was
corrected to spec. Geometry is that board's Edge.Cuts translated by
`(+14.6103, -16.3164)` mm into this board's frame, so the two match exactly.

- Outline: 24 primitives, one closed loop, every endpoint used exactly twice,
  **95.8850 x 90.1800 mm**. X is exactly the CSK Slot1 profile; Y is 0.010 mm
  over the spec's 90.170, matching the reference.
- Mounting holes, inset from the nearest edges:

  | | left | right | top | bottom |
  | --- | --- | --- | --- | --- |
  | MH1 | 90.8050 | **5.0800** | **5.0900** | 85.0900 |
  | MH2 | **5.0800** | 90.8050 | 7.6300 | 82.5500 |
  | MH3 | **5.0800** | 90.8050 | 81.2900 | 8.8900 |
  | MH4 | 90.8050 | **5.0800** | 85.1000 | **5.0800** |

- CSKB connectors: H1 pin 1 at `(113.2136, 136.1236)`, H2 pin 1 at
  `(108.1336, 136.1236)`, both rotation -90. Pad rows sit **5.0800 / 7.6200 /
  10.1600 / 12.7000 mm** from the left board edge — the same four values as the
  reference. H1 to H2 pitch is 5.08 mm (0.2").

A bad outline fails silently — KiCad falls back to the bounding box and fab
output loses the notches. Re-run the closed-loop check after any outline edit.
