# Payload compute: schematic-start baseline

2026-10-04 baseline; capture started 2026-10-05. **Prototype schematic capture is underway.** Architecture,
ownership, interfaces and implementation order are defined below. This does
not mean that every component is qualified, that three synchronized Jetson
cameras work, or that the board is ready for layout, fabrication or flight.
The real schematic must resolve exact parts and physical maps sheet by sheet;
unaccepted packages must not be placed by copying a generic pin assignment.

The purpose of this milestone is to stop extending disposable studies as a
prerequisite for every real sheet. We have enough to capture the board now,
while keeping explicit release gates for untested hardware and software.

## Captured stages

The new [payload_compute_rev_next project](../kicad/payload_compute_rev_next/payload_compute_rev_next.kicad_pro)
contains the real root hierarchy, AON regulator, reset/run-control core,
three independent limited/reverse-blocking bootstrap feeds, startup mode
sampling, immutable one-hot source choice, live IHU permission and external
watchdog/reset qualification.
[Stage evidence and open interfaces](../kicad/payload_compute_rev_next/README.md)
record bounded verification for each stage. Coordinated connector/fuse/TVS
entry protection, USB PD negotiation, raw-source/main-bus voltage qualification,
main admissions and physical buck/Jetson enable interfaces are still unbuilt.
Stage3 choice outputs identify the committed source; `SOURCE_OK_AON` remains
an uncaptured qualification boundary, so source choice cannot enable main power
on its own.
The [bootstrap input and restart contract](bootstrap_input_contract.md) defines
initial USB current, reduced-startup limits and complete-power-loss recovery.
The converted carrier and disposable studies remain intact.

The [stage3 six-sheet review PDF](../kicad/payload_compute_rev_next/payload_compute_rev_next-stage3.pdf)
shows the captured mode/source/watchdog circuits. Exported-gate checks cover
all 256 mode/source/permission combinations; open future interfaces and
conditional electrical qualification remain recorded in the project evidence.

## Baseline and authority

Target the SD-equipped Orin Nano devkit module first, fixed regulated 5 V
VDD_IN, three InnoMaker IMX296RAW cameras with 750/770/780 nm filters,
removable M.2 Key-E Wi-Fi, ground fan/spreader and CSKB envelope. Exact module
SKU, camera revisions and Wi-Fi card still require inventory. Legacy Nano
compatibility is a separate variant check; it is not a generic drop-in or
SD-boot guarantee for every bare Nano module.

IHU owns observation windows, location/time context, resource permission and
normal session stops. STM32 owns CAN, bounded scheduling, power sequencing,
watchdogs and hardware trigger timing. Jetson owns camera configuration,
three-frame acquisition, processing, SD retention and the web interface.
CAN normal stop retains PAYLOAD_EN until verified off. PAYLOAD_EN low removes
hardware permission immediately, including with hung firmware.

Use [the revised carrier pin plan](payload_carrier_pinmap.md),
[supervisor/control contract](supervisor_interfaces.md),
[source and enable implementation](source_hardware.md), and
[camera/bench validation](camera_and_bench.md). The former May pin map is
retained as historical documentation; it cannot override this baseline.
Canonical H1/H2 pin numbers remain in the system CSKB map.

## Board blocks and capture order

| Sheet | Contents | Work required during capture |
|---|---|---|
| Root | Power domains and hierarchical interface overview | Explicit domain names; no generic +3V3 joining stack/AON/camera power |
| 01 Stack and lab connectors | H1/H2, battery-range bench feed, mode jumper, fan/trigger connectors | Exact connector mating-view maps and current/clearance budgets |
| 02 USB-C PD | Power-only USB-C receptacle, STUSB4500, NVM access, status | CC/ESD/VBUS circuitry, programmed/read-back 5/9/15 V profiles, contract qualification |
| 03 Entry and bootstrap | Entry fuse/transient/reversal protection, independent limited AON feeds, OR and AON buck | Coordinated protection and USB attach budget; branch short and reverse-leakage analysis |
| 04 Source and run control | Immutable source lock, mode receiver, raw windows, main eFuses, watchdog, run latch | Revised EN interface, safe defaults, no startup dependency loop |
| 05 Payload regulators | Main 5 V, independent peripheral 3.3 V, local 1.8 V, branch isolation/discharge | Exact passives; main-buck reverse-current requirement; rail decay and monitor margins |
| 06 Supervisor and telemetry | STM32G0B1VET6, two CAN paths, UART, local I2C, voltage/current/temperature sensing | Accept 100-lead map, implement pin reservations and partial-power-safe inputs |
| 07 Jetson | 260-pin socket, VDD_IN bypass, POWER_EN, reset/shutdown receivers, recovery USB | Exact module and socket map; boot straps; no direct stack control/I2C connection |
| 08 Cameras | Three independent CSI ports, camera I2C switch, three power/trigger/strobe branches | Exact FFC/harness maps; driver lane/polarity/device-tree contract |
| 09 Bench peripherals and debug | M.2, fan, SWD, two consoles, status indicators and shutdown button | Exact socket/fan maps; default cooling and back-power checks |

Keep existing carrier copper as a mechanical/routing reference. Do not update
its PCB from a partially rebuilt schematic: old refdes/UUID links and escaped
traces could otherwise attach to different circuits. Capture in a separate
next-revision project and migrate checked mechanical geometry later through
Konnect. No real carrier source or PCB copper was changed by this analysis.

## Parts baseline

| Function | Part / choice | Acceptance status |
|---|---|---|
| Main 5 V buck | LMR51460SQDRRRQ1 | Physical map and standalone circuit checked; thermal/dropout/load qualification open |
| AON 3.3 V | LMR36506R3RPER, RT to VCC, 1 MHz | Prototype map/circuit checked; modified lands and common stencil need assembly qualification |
| Main input switches | TPS259470LRPWR, separate USB/bench/stack paths | Physical map checked; old MOSFET clamp fixture is not the integration baseline |
| AON reset | TPS3808G33DBVR | Physical map and standalone latch study checked |
| Logic / latches | Accepted SN74LVC1G10/11DBVR, SN74LVC1G74DCUR, SN74LVC1G373DBVR | Use verified maps; verify every new combination and power domain |
| Main 5 V window | REF3425IDBVR + LM2903BIDR on main 5 V | Maps/circuit/DC allocation checked |
| Raw windows / coarse logic receivers | TPS3700DDCR | DDC physical map and mode/IHU circuit captured; raw-window circuits still unbuilt |
| Supervisor | STM32G0B1VET6, LQFP100 | Functional pin plan checked; exact 100-lead map not yet accepted |
| CAN transceivers | Two TCAN334GDR, 3.3 V | Standby plus shutdown selected; exact map and electrical checks required |
| External watchdog | TPS3431SDRBR | DRB physical map and reset/ready circuit captured; dynamic/partial-power qualification pending |
| PD controller | STUSB4500QTR | Architecture selected; package/circuit/NVM acceptance required |
| Peripheral 3.3 V buck | LMR51430XFDDCR, 500 kHz FPWM | 3 A class gives allocation headroom; exact map/passives/thermal checks required |
| Local 1.8 V | TPS7A2018PDBVR candidate, fed from local peripheral 3.3 V | Exact orderable and interface/discharge budget to accept during capture |
| UART translation | SN74AXC2T245RSWR candidate, explicit direction and OE | Partial-power architecture chosen; RSW package and loading to accept |
| Camera trigger / strobe | Three 3.3–5 V current-capable trigger branches and optocoupler return receivers | Exact camera revision and safe idle/current/timing to accept; no 1.8 V XTR assumption |
| Camera I2C selection | PCA9546APWR candidate | Separate bus channels; exact map/reset/pullups to accept |
| Main-bus energy monitor | INA228DGSR candidate + Kelvin 10 mΩ shunt | Measurement boundary defined; exact map/shunt rating/accuracy to accept |
| Temperature | NTC ADC input near buck; Jetson die temperature over UART | Calibration and flight thermal solution open |

Candidates are not an accepted BOM. Current JLC stock, assembly capability,
minimum orders and substitutions must be checked before layout/BOM release.
New parts may need adjustment as their exact circuit and package evidence are
accepted; their functional boundaries are fixed here.

## Gates after schematic start

| Gate | Required evidence |
|---|---|
| Place each package-sensitive part | Exact MPN lead-to-symbol-to-pad map, query-back and disposable visual acceptance |
| Finish each sheet | Complete boundary interfaces, real netlist, direct ERC, pin/wire/short checks and readable render |
| Start production PCB layout | Full schematic connectivity/ERC review; reconciled pinmux, power budgets, connector/current and discharge designs |
| Release prototype fabrication | Full PCB DRC/DFM, stackup/high-speed rules, thermal/current review and assembly/stencil/BOM acceptance |
| Accept payload function | Single, dual, then triple Jetson acquisition; hardware-trigger driver work; measured exposure/frame association; validated detection pipeline |
| Accept portable student kit | Exact bank/cable/card/fan; boot/workload/PD traces; AP fallback; shutdown and fault tests |
| Release flight design | Launch isolation covers raw stack/AON and alternate feeds; exact flight thermal construction; environmental and mission validation |

The unknown exact module/card/camera revisions do not stop capture of the
accepted power/control core. They do stop connector/module variant acceptance
and any claim of complete compatibility. Bench tests require access to the
loaned devkit and cameras; this analysis does not substitute invented results.

## Immediate engineering decisions

- USB lab target remains 15 V / 3 A. Five volts is supervision/negotiation
  only. No NVMe and no onboard USB-to-UART IC are added.
- Begin bring-up in a conservative 7 W Jetson configuration. Retain the 15 W
  design/load case, but do not enable it automatically until boot/load/current
  limits are qualified. Boot peaks are not bounded by that software setting.
- Keep the 6.0–8.4 V nominal feed requirement. Low-end operation remains a
  dropout/loaded-input test gate; initial raw UV allocation may inhibit startup
  around 6.2 V. A USB-C bank is the preferred full student-lab feed.
- Allocate a hardware watchdog, three camera strobe returns and independent
  debug ports now. LQFP100 avoids exhausting a 64-pin supervisor's I/O.
- No direct IHU-to-Jetson I2C or sleep wire. Use CAN-to-STM32-to-Jetson UART;
  the allocated stack sleep input is reserved/monitored, with SC7 disabled in
  the first software baseline.
- Report INVALID, CLEAR or DETECTED; failed capture never becomes a negative
  wildfire report. Raw images remain on SD/Wi-Fi; CAN image transfer is disabled
  in the first baseline.

Reproduce the planning checks with `python3 design/schematic_start_study.py`.
These are architecture/DC/resource checks, not netlist verification of a
finished board. Existing circuit fixtures retain their own evidence/checks.

## Verification of this planning milestone

The [planning results](schematic_start_results.json) reproduce raw-voltage
corner ranges, static eFuse-enable margins, source-current allocations, MCU
pin/ADC uniqueness and image size. Seven saved fixture checkers passed against
their exported evidence (main buck, precision monitor, run latch, bench sampler,
permission logic, AON buck and historical admission clamp). Boundary ERC findings
remain explicitly accounted for in those isolated fixtures; these checks are
not a fresh full-carrier ERC or an acceptance of the revised integrated circuit.

Peripheral discharge remains a substantial design task: with 220 µF effective
capacitance, an ideal RC path needs at most 2.43 Ω to bring 3.3 V to an example
0.2 V target in 1.5 ms. Regulator turn-off delay, capacitance variation, residual
feeds and resistor/switch pulse energy reduce the available margin. The example
0.2 V endpoint is a planning assumption; accept the actual endpoint and timing
against the module design guide during that sheet's capture. Do not rely on an
unsized internal quick-output-discharge function.

Schematic start needed no further architectural decision from the user. The
new project root and accepted AON/reset/control core are now captured; next accept
and complete each new circuit/package in the order above. Driver tests,
module inventory and flight thermal/inhibit work can proceed alongside capture,
with their release gates retained.
