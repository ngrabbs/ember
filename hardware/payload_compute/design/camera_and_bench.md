# Camera acquisition and student-bench baseline

2026-10-04. Hardware provisions and validation plan, not measured acceptance.
The user has tested these cameras only on Pi4. Trigger through the Arducam
mux did not work; that setup does not prove independent Jetson CSI operation.

## Camera identity and software gate

Koenig uses InnoMaker CAM-IMX296RAW. Preserve the three 750/770/780 nm channels.
Inventory exact PCB revision and mono/color sensor before ordering connectors
or accepting a trigger circuit. The manufacturer now documents
CAM-IMX296Mono-GS/Color-GS and supplies single/dual Orin Nano overlays for
JetPack 6 / L4T r36.4.4 / kernel 5.15.148. It explicitly excludes Jetson
hardware trigger/strobe support. These are starting points for driver work,
not evidence that our older cameras or a three-camera carrier already work.

Use three independent two-lane CSI paths and a camera-only PCA9546A I2C
switch. Sensor address 0x1a and EEPROM 0x50–0x53 collide across cameras;
select one I2C branch at a time. All CSI paths can stream concurrently.
Linux device tree needs three sensor instances below the correct mux nodes,
matching physical lanes, SoC polarity mapping, enables and clocks. No MIPI
camera multiplexer is added. Keep driver changes reproducible and versioned;
booting an incompatible kernel must report INVALID rather than a clear result.

## Trigger and strobe electrical boundary

Manufacturer manual V2.0.2, pages 13–15, shows J3 TRIG+ pin 1 and external
return pin 2, **3.3–5.0 V input**, an optocoupler LED and 200 Ω onboard series
resistor. This is not the Raspberry Pi camera's direct 1.8 V XTR pad. The
manual's illustrations and text use different optocoupler names: inspect the
actual revision before accepting LED current, CTR and propagation limits.

Reserve one current-capable driver per camera, driven from the shared STM32
timer and powered from the qualified camera domain. Never drive all three
LED loads directly from a single MCU pin or a small UART translator. Start
with 3.3 V input as the documented operating point; choose the driver and
any added resistance using actual optocoupler limits and measured current.
Provide connector-side test access and optional series resistance footprints.

Idle is HIGH and capture uses the falling edge / low pulse in the documented
trigger mode. Initialize timer HIGH before enabling outputs. Gate loss must
return the camera input to its defined idle while camera power remains, not
force a sustained LOW exposure. Ensure that partial power and camera enable
transitions do not create unintended captures or back-power the board.
One initial pulse width applies to all three cameras; gains may differ per
filter. Different exposure widths with a common leading edge would require
additional timer outputs and a revised pin/resource plan.

J2 is an isolated phototransistor strobe return. Provide a collector pull-up
and emitter return on each receiver, not a push-pull translator assumption.
The manual's flash-current example is not a guaranteed logic-edge timing
specification. Check exact polarity, CTR, leakage, pull-up value and edge delay
before assigning STM32 timer capture thresholds. A weak pull-up may meet DC
logic and still obscure exposure skew. Measure all three optical/exposure and
strobe edges; equal MCU edges do not establish equal exposure start times.

Jetson reports CAMERAS_ARMED only after all three devices are configured,
buffers queued and streams ready. STM32 then triggers and timestamps the
capture. Jetson associates three frames with that capture ID and returns
INVALID if a frame is missing, stale or outside the configured timing/skew
bound. Define a measured skew requirement before calling captures synchronized.

## Storage, processing and reporting

At 1456 × 1088, three frames stored in 16-bit containers occupy 9,504,768 bytes
(about 9.064 MiB), excluding metadata. Packed 10-bit data would be 5,940,480
bytes; actual driver stride and format decide the real amount. SD speed,
capacity, endurance and available filesystem space must be measured.

Use a bounded data partition: initial policy reserves 70% for an ordinary
ring, 10% for protected detections and 20% free headroom, separately from the
OS allocation. Quotas are configurable. When protected quota fills, retain
compact results and report retention loss; do not expand protection without
bound or fill the OS filesystem. Interrupted writes/reboot recovery are tests.

The detection result is INVALID, CLEAR or DETECTED with reason/quality,
capture ID and time uncertainty. IHU attaches GPS/time at the trigger event;
processing completion time is not the observation location. No full-image CAN
transfer is enabled initially. Even an impossible zero-overhead 500 kbit/s
link needs over 152 seconds for one uncompressed three-frame set. Retain
images locally and validate them over ground Wi-Fi. Optional bounded thumbnails
are future protocol work, not a reason to enlarge the initial hardware.

## Portable bench workflow

Use a qualified USB-C bank/cable supplying the preferred 15 V / 3 A profile.
No bank has been selected; USB-A 5 V / 2.1 A is not a full-payload baseline.
Fit the bench jumper before power. One cable powers the board; normal boot
starts the existing Koenig web workflow and automatic Wi-Fi AP fallback.
Use a unique visible SSID such as EMBER-PAYLOAD-xxxx, per-unit credentials,
and a printed local access address. The operator needs no internet or shell.

Indicators distinguish starting, ready and power/fault. Insufficient USB
power leaves supervision alive with a clear fault and no boot/brownout loop.
Web Stop or a three-second bench button hold requests graceful shutdown;
wait for verified-off indication before unplugging. Faults need a fresh arm.
Removing/inserting the jumper while powered does not change the latched mode.
Ground fan/spreader and Wi-Fi card are present during lab qualification.

The [bootstrap input and restart contract](bootstrap_input_contract.md) requires
at least 500 mA at initial 5 V attachment from the qualified C-to-C source.
After complete AON loss, an unclean session record prevents repeated automatic
boots; the local button supplies deliberate recovery. Clean first attachment
retains automatic boot. The journal and button recovery still need firmware
implementation and interrupted-write testing.

## Evidence to collect on the prototype

| Test | Required observation / acceptance |
|---|---|
| Inventory | Module SKU/storage, camera revision/mono-color, cable contact side, Wi-Fi card, fan and USB source identities |
| One camera | Correct stream format/stride, repeatable raw capture, stable exposure/gain, no stale-frame substitution |
| Two then three | All devices enumerate through mux; independent streams/frame IDs; target-rate stress with SD writes |
| Hardware trigger | Driver exposes mode safely; no boot/shutdown false captures; three current waveforms and optical/strobe timing measured |
| Detection | Calibrated filter/exposure processing; reference negatives/positives; invalid capture never reports CLEAR |
| Portable boot/load | Worst source/cable droop, inrush, camera/fan/M.2 peak load, 7 W and conditional 15 W modes, no unsolicited power cycles |
| Shutdown / fault | CAN stop retains permission through SD flush; hard kill works with hung MCU/Jetson; fresh arm required; measured 3.3/1.8 V decay |
| Mode / feeds | Jumper hot-change, two lab feeds, USB 5 V attach, selected-source detach and source-lock retention after MCU reset |
| Complete power loss | Repeated PD hard resets/brownouts during SD writes; unclean boot remains inhibited until explicit arm; journal survives interrupted writes |
| AP usability | Boot without known network, laptop-only capture/download, normal stop, readable insufficient-power behavior |
| Long session | Thermal stability, storage quota, failed SD writes, full protected quota, watchdog/CAN lease timeout, recovered boot |

Sources: [Koenig setup](https://github.com/ngrabbs/koenig_wildfire/blob/main/docs/hardware_setup.md),
[manufacturer driver](https://github.com/INNO-MAKER/cam-imx296raw-trigger),
[manufacturer manual V2.0.2](https://github.com/INNO-MAKER/cam-imx296raw-trigger/blob/main/CAM-IMX296RAW-UserManual-V202.pdf),
and [manufacturer FFC reference](https://docs.inno-maker.com/home/mipi-cameras/imx296-mipi-cameras).
