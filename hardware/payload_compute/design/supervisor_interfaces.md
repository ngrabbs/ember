# Supervisor, control and debug contract

2026-10-04. Schematic-start decisions. Numerical firmware settings below are
initial engineering defaults, configurable after measurement; they are not
accepted flight timing requirements or vendor boot deadlines.

## MCU and physical interfaces

Use STM32G0B1VET6 in LQFP100 for capture. The 512 KB family member has two
FDCAN controllers and leaves space for safety/status inputs, three strobe
returns and telemetry. [Functional pin reservations](supervisor_pin_plan.json)
assign 69 distinct GPIO/AF roles, including four optional ADC-isolation controls.
Seven direct ADC channels use PA4–PA7 and PB0–PB2; PC0–PC3 have no ADC
function on this MCU. Main-bus voltage comes from INA228, with an independent
digital validity receiver on PC3. VDDIO2 is powered from the same AON rail;
disable UCPD dead-battery pulldowns during initialization.
This is not a physical-lead map: validate every lead, supply domain (including
VDDIO2), symbol and footprint before placement. Keep HSE, reset, SWD and
optional LSE pins reserved. Begin with an external 8 MHz HSE, tolerance target
≤50 ppm over the qualified conditions; exact crystal/load parts need selection.
No battery-backed RTC is added. Loss of AON invalidates cached schedules/time.

| Interface | Baseline |
|---|---|
| Stack control | Classic CAN, 500 kbit/s, matching the existing EMBER bench baseline; FD disabled initially |
| CAN A | FDCAN1 PC4/PC5 AF3 → TCAN334GDR → H1.51/H1.52 |
| CAN B | FDCAN2 PB12/PB13 AF3 → separate TCAN334GDR → H2.49/H2.50 |
| Jetson application link | USART1 PA9/PA10 AF1, 115200 8N1 initially, translated to module UART0 pins 101/99 |
| MCU console | USART2 PA2/PA3 AF1, 3.3 V TX/RX/GND header, separate from application link |
| Jetson console | Module UART2 pins 236/238, 1.8-to-3.3 V translation, separate TX/RX/GND header |
| Local management I2C | I2C1 PB8/PB9 AF6, AON domain, 100 kHz initial rate |
| Camera edge generation | TIM2_CH1 PA0 AF2, one hardware edge source with three isolated branches |
| Camera strobe capture | TIM2_CH2 PA1, CH3 PB10, CH4 PB11, AF2; software shall not repurpose those channels |
| Fan control | MCU TIM3 PWM PB4 and tach capture PB5 AF1; Linux supplies temperature/request information over UART |
| Programming | Standard keyed Cortex SWD 10-pin 1.27 mm, VTref/GND/SWDIO/SWCLK/NRST; VTref senses AON and does not inject power |

Two CAN buses remain electrically independent. Provide separate optional
120 Ω termination footprints/jumpers, default DNP unless the payload is a
physical bus endpoint. Include protection footprints appropriate to the stack
common-mode/fault envelope; no isolated CAN supply is required for the first
common-ground prototype. Each TCAN334 uses separately controlled standby and
shutdown, biased inactive at MCU reset. Maintain recessive TXD defaults.
Its 3.0–3.6 V supply range fits the AON DC allocation. Validate unpowered bus
loading, wake behavior, active CAN current and connector/harness faults.

CAN A is primary. Keep B available for explicit failover; define command
deduplication by sender/session/sequence so retrying on B does not recapture,
rearm or restart a completed transaction. Bus-off is not a permission to
restart Jetson. A valid session has a duration/count bound and an IHU lease;
loss of the lease stops new triggers and requests a graceful stop. IHU may
hard-kill at any time. Do not allocate CAN IDs/APIDs until the system protocol
namespace is reconciled; the semantic contract below is independent of IDs.

No direct stack I2C link to Jetson. H1.41/43 are pass-through/NC on this new
payload revision unless a future AON-only housekeeping interface is explicitly
specified. Camera I2C, local AON management I2C and stack I2C are separate nets.
Candidate local 7-bit addresses: STUSB4500 0x28 (strap), INA228 0x40 (strap).
Check these against actual selected parts and buses before capture. The camera
switch uses its own Jetson camera bus; its address must be selected from the
complete camera/EEPROM map, not from these AON addresses.

## External watchdog and reset

Select TPS3431SDRBR for an independent MCU watchdog. SET1 high and CWD open
give a tabulated 1.36–1.84 s watchdog interval. Firmware produces a falling
WDI edge every 200 ms only after a healthy supervisor loop; no autonomous
timer/DMA toggling that continues after the control task hangs. WDO clears
payload permission in hardware and resets the MCU, while the separate source
lock retains its choice through ordinary MCU reset. New MCU readiness and a
fresh arm are required afterward.

EN and ENOUT must be included in the watchdog-valid function: disabling the
watchdog makes WDO high impedance, so WDO alone is not health. If a debug
disable provision is fitted, use a physical bench-only interlock that also
holds payload enables off. Flight assembly cannot bypass this through software.
Verify watchdog output levels, pull-ups, startup and reset pulse against the
MCU/gate loads before accepting its circuit.

The stage 3 implementation keeps SET1 high and CWD open, with a conditioned
AON reset driving EN. EN must not derive from the watchdog's own combined
fault/reset output, which would create disabling feedback. WDO and ENOUT can
share an open-drain qualification node; its receiver and reset fanout require
explicit bias/loading checks. WDI requires a connector/MCU-pin high of at
least 0.8 times the actual watchdog supply; a loaded logic-buffer guarantee
of only 2.4 V does not meet that at the top of the AON allocation.

Stage3 uses `MCU_WDI` (PD8) and the combined open-drain `MCU_NRST_N`
node (future PF2/NRST connection). `WD_RESET_VALID` (PD9) is the conditioned
active-high release indication, replacing the former `WATCHDOG_WDO_N` GPIO
name. WDO and ENOUT both sink that reset node; external debug reset must
be open-drain and must never force it high. Source requests are named
`USB_REQ`, `BENCH_REQ`, and `STACK_REQ` (PD0–PD2). `IHU_EN_VALID` (PE1)
is the conditioned IHU permission input. These are functional reservations;
the MCU and debug connector have not yet been physically captured.

Define MCU_ALIVE as qualified MCU_READY, watchdog-enabled/valid and AON reset
released. The previously studied stuck-high GPIO is not sufficient. A debug
reset or watchdog event must asynchronously clear the run latch and trigger
permission, with no automatic arm on watchdog recovery.

Complete AON loss also erases the hardware latches. Follow the
[persistent restart contract](bootstrap_input_contract.md): record an unclean
session before requesting main power and clear it only after verified normal
shutdown/discharge. An invalid or unclean record blocks automatic bench boot
until explicit fresh arm. This is a firmware requirement, not implemented
behavior in the partial schematic.

## State and command contract

States: OFF, QUALIFYING, POWERING, BOOTING, READY, ARMED, CAPTURING, STOPPING,
DISCHARGING and FAULT. Electrical rail health, Linux application readiness,
camera arm state and active session are separate conditions.

| Command | Required behavior |
|---|---|
| GET_STATUS | Mode/source/rail validity, last fault, readiness, session/capture IDs, storage and software version |
| SET_TIME | IHU UTC plus validity/uncertainty; bind it to an MCU monotonic reference and sequence |
| CONFIGURE_SESSION | Session ID, relative/UTC start, count/duration, cadence, exposure/gain per camera, processing profile, retention limits |
| START_SESSION | Validate permission, source/profile, time and bounds; acknowledge acceptance separately from READY |
| CAPTURE_ONCE | Allowed only with all three cameras armed and no overlapping capture transaction |
| STOP_SESSION | Inhibit new edges immediately; finish the current transaction and initiate normal shutdown |
| POWER_OFF | Inhibit triggers, request Jetson Linux shutdown, then verify rail discharge before OFF acknowledgement |
| CLEAR_FAULT / RETRY | Explicit authorization; inspect persistent faults; never synthesize an arm edge from voltage recovery |

On the UART, use framed versioned records with length, sequence and CRC;
JSON/text may be used inside the bounded frame for initial integration.
Cap messages at 1024 bytes; parser timeouts and backpressure must be bounded.
Jetson reports APP_READY, CAMERAS_ARMED, CAPTURE_COMPLETE, RESULT and
SHUTDOWN_PROGRESS. MCU stamps the actual trigger edge and capture ID.
Jetson verifies one valid frame from each spectral channel and reports their
association; enqueueing three Linux requests is not synchronous exposure.

Report result enum INVALID / CLEAR / DETECTED plus failure reason/quality,
session and capture IDs, trigger time/time uncertainty and compact metrics.
IHU associates its GPS context with that trigger time, rather than whichever
location happens to be current when processing finishes. UTC over CAN is
coarse synchronization; no precision PPS or new CSKB pin is implied.

Provisional defaults: 120 s boot/application deadline, 30 s normal shutdown
deadline, 10 s renewable IHU lease, 600 s maximum session, at most two explicitly
authorized retry attempts with 30 s cooldown. A timer or recovered voltage
cannot authorize a retry. Qualification uses the existing 100 ms stable-main-5-V
allocation. Startup/discharge is separately measured; the boot deadline is
not a deadline for module SYS_RESET release. On stop timeout, record a forced
stop fault and remove power using the accepted module handshake/kill paths;
do not acknowledge a clean SD shutdown. CAN loss cannot remove a hardware
IHU permission requirement or extend a session without its bound.

## Debug and observation

Provide pads for raw inputs, selected bus, +3V3_AON, +5V_ORIN, peripheral
3.3 V and 1.8 V, with nearby grounds. Probe source requests/lock, reset,
watchdog, run latch, converter enables, main window, POWER_EN,
ORIN_SYS_RESET_N and ORIN_SHUTDOWN_REQ_N. Give each camera its own trigger
and strobe probe and retain both UART sides for translation debugging.
SWD, MCU console, Jetson console, recovery USB and Wi-Fi have different roles.

Use one INA228 on the selected main bus, with a provisional Kelvin 10 mΩ,
1 W shunt and accuracy/thermal allocation. At 6 A this drops 60 mV and
dissipates 0.36 W; include that drop in low-battery headroom. Its reported
MAIN_ENERGY excludes bootstrap and the independently powered PD controller.
Measure whole-board/session energy with an external meter or EPS telemetry;
do not label the main-bus counter as total battery consumption.

Initial lab indicators: starting/qualifying, application-ready, and power/fault.
A three-second bench-only button requests graceful shutdown. CAN remains the
flight command path. No onboard USB-UART IC or always-active Wi-Fi module is
required. Recovery USB is a separate data port from the USB-C PD power input.

Sources: [STM32G0B1 datasheet](https://www.st.com/resource/en/datasheet/stm32g0b1re.pdf),
[TCAN334](https://www.ti.com/lit/ds/symlink/tcan334.pdf),
[TPS3431](https://www.ti.com/lit/ds/symlink/tps3431.pdf),
[INA228](https://www.ti.com/lit/ds/symlink/ina228.pdf), and local NVIDIA
DG-10931-001 v1.5 tables 12-7 and 12-13/14. These selections still need exact
package and electrical acceptance in the real schematic.
