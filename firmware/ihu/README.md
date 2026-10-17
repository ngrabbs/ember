# IHU firmware

Active IHU CAN Feather application, formerly `firmware/can_feather_bench`.
The earlier FreeRTOS prototype was removed and remains available in Git history.
This directory builds only the IHU: CMake project/target `ihu`, output `ihu.uf2`.
The LTE CAN Feather has its own [Walter MCU application](../walter_mcu/README.md),
project/target/output `walter_mcu`. Walter ESP32-S3 firmware remains in
[`firmware/walter`](../walter/README.md); the original-Pico UHF application is
[transceiver](../transceiver/README.md). Configure fresh build directories.
Each application owns its source and VERSION file; the split retains version
0.14.1 and does not flash hardware. Shared board/build configuration lives in
[`shared/pico_can`](../shared/pico_can/README.md).

```sh
cmake -S firmware/ihu -B build/ihu -DPICO_SDK_PATH="$PICO_SDK_PATH" \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build build/ihu --target ihu -j4
# build/ihu/ihu.uf2
```

For the inactive FLIGHT stub build, use a separate build directory with
`-DIHU_FLIGHT_CONFIGURATION=ON`. No LTE Feather target is generated here.

## transceiver firmware request — 0.14.0

`uhf transceiver firmware` requests one fresh `COMMS_FIRMWARE` over UHF from transceiver
0.33.0. It requires UHF permission, normal CAN, a current transceiver HELLO and idle
transport, and reports the existing QUEUED/local RF result. transceiver constructs
its own packet; the zero-length request acknowledgement does not represent the
RF packet length. Install transceiver 0.33.0 before using the new command. transceiver now
automatically announces once per boot on the first telemetry request, rather
than before every request. See the [transmission matrix](../../docs/user/ihu-can-console.md#transmission-matrix).

## Mode/output cleanup —0.13.0

The current IHU boots quietly into SAFE/GROUND_TEST with six output switches
OFF. Essential EPS sampling, presence discovery and command handling remain
active. Explicit command replies are preserved. `mode` and `outputs` report
actual state; `output NAME on/off` controls cli_debug, cli_telem, umb_debug,
umb_telem, uhf_telem and lte_telem independently. Entering a mode or resetting
clears all switches. Flight builds are inactive stubs and restrict operation
when qualified flight history is unavailable. No physical test jumper is used.

Read the [runtime matrix, entry gates and migration procedure](../../docs/architecture/operations/04-ihu-runtime-policy.md).
Pair with bench bridge 0.4.0; periodic EPS forwarding is now permission-gated.
The old EPS-only `telem` timer, CAN echo telemetry shortcuts and LTE queue
console/pumps are retired. Older sections below record historical releases
and hardware evidence; their retired command instructions do not apply to0.13.0.

## Payload fire check —0.12.0

`payload fire-check` commands the selected payload, validates its16-byte result,
and prints FIRE_CHECK result=no_fire/fire with STATIC_STUB/ALGORITHM provenance.
The RF uplink admits PAYLOAD_FIRE_CHECK in addition to PING, establishes payload
HELLO, and returns one correlated native PAYLOAD_FIRE_RESULT via transceiver.
RF transactions use a separate16-entry fail-closed per-boot duplicate cache;
there is no automatic retry. Console mutation and background work cannot take
over the active RF transaction. Existing transceiver/LTE routes are retained.
STATUS now reports the same semantic version as FIRMWARE.

## Payload application route —0.11.0

IHU adds `hello payload`, `ping N`, `payload ident`, `payload status`, and
`payload heartbeat`, using request/reply IDs0x740/0x741 and existing discovery
node4/reply0x704. The responder runs on the Pi/LC2502; see the
[payload contract](../payload/README.md). transceiver/LTE routing remains unchanged.

## CAN addressing migration candidate —0.8.0

At this historical milestone, one image family built the IHU and **LTE CAN Feather** roles. The historical
`ember_comms_can_bench.uf2` filename means the LTE Feather, not the original-Pico
UHF transceiver. Check board USB identity before flashing.

- LTE application request/reply IDs are now0x720/0x721; transceiver stays0x710/0x711.
- LTE boots CAN-ready and answers discovery node3 with RF unchanged/off.
- On IHU use `hello transceiver` or `hello lte` before that route's commands.
- `version` / `status` reports semantic version, SHA, dirty flag and boot ID.
- `lte firmware` and `lte modem firmware` query the two LTE processors without RF.

Builds now require `-DEMBER_GIT_REVISION=<40 lowercase hex>` and
`-DEMBER_GIT_DIRTY=0|1`. Capture these before exporting source with
`python3 firmware/transceiver/source_identity.py` from the source checkout.
See the [migration contract](../../system/interfaces/device_registry.md) for
blocked target switching, identity telemetry, deployment order and validation.
Old0x710 LTE firmware must remain off the shared bus until upgraded.

## Historical CAN Feather development

**Historical application summary, reviewed 2026-10-04:** native EPS readout,
single-bus CAN forwarding and recorded bounded LTE delivery are implemented
in the standalone bench. Manual telemetry and the opt-in native EPS timer are available. Automatic
emission defaults off; the timer skips busy or unavailable transport periods. The [USB console guide](../../docs/user/ihu-can-console.md)
owns operator syntax. Production FreeRTOS command integration and CAN A/B
remain open. Version/flash tables below are dated milestones; identify the
correct application version and its recorded validation before flashing.

The new IHU MCU and transceiver MCU both use Adafruit RP2040 CAN Bus Feathers with
onboard MCP25625 CAN controllers/transceivers. This standalone Pico SDK project
historically built `ember_ihu_can_bench.uf2` and `ember_comms_can_bench.uf2` from
one source with distinct roles; current builds use the separate projects above. It replaces neither the complete FreeRTOS IHU/EPS application
nor the UHF transceiver application. The IHU role now supports manual read-only EPS
register observation and explicit battery-only ADC enable; it does not change
charging policy, activate UHF, execute flight commands, or implement CAN redundancy.
Version2 adds native EPS packet forwarding and explicit bounded Walter LTE requests.
Both CAN Feathers have recorded native EPS forwarding through Walter echo.
Walter LTE upload and later bounded delivery trials are recorded in the
[LTE evidence index](../../ground/lte/README.md). Those trials do not qualify
continuous RF reliability.

User confirmed H-to-H, L-to-L, and common ground, with both terminators present
and 60 ohms measured across the bus. This qualifies the bench harness, not the
routing of the spacecraft stack. Both modules have one CAN channel; A/B redundancy
still requires additional hardware and policy.

## Driver and board profile

Pico SDK 2.1.1 / ARM GCC 14.2.1; source builds with `-Wall -Wextra -Werror`.
The corrected Feather board header selects the 8 MB flash profile and GPIO13 LED.
The onboard MCP25625 uses SPI1 GPIO14 SCK / GPIO15 MOSI / GPIO8 MISO, CS19,
reset18, standby16, RTS17, interrupt22, and RX-buffer output23. SPI operates at
1 MHz, mode 0. The driver polls RX0/RX1 and TX0; it does not require an IRQ ISR.
Standby is released low, reset is released high, and RTS is kept inactive high.

500 kbit/s, classic CAN, standard 11-bit data frames, 16 MHz oscillator.
CNF1/2/3 = `00 f0 86` (16 time quanta; SJW1; 9/16 sample point). Driver checks
configuration-mode/register readback. Both images start in configuration mode;
USB `normal` enables bus participation. No packets transmit automatically at boot.
A power cycle therefore requires `normal` again on that board.

One hardware TX buffer is used, with one-shot transmission and a 50 ms completion
bound. A frame failure stops the remaining fragments; pending application work
later reports UNKNOWN. A CAN ACK/TX-complete alone never proves packet delivery.
Status exposes TX success/failure/timeout, RX/overflow, TEC/REC/EFLG, fragmentation
errors/timeouts, application matches, pending work, and controller identities.
Bus-off recovery, saturated-bus behavior, priority scheduling, and FIFO capacity
under unrelated traffic remain unqualified.

Primary references: [Adafruit pinout](https://learn.adafruit.com/adafruit-rp2040-can-bus-feather/pinouts),
[two-Feather CAN test](https://learn.adafruit.com/adafruit-rp2040-can-bus-feather/can-bus-test-2),
[Adafruit register/timing implementation](https://github.com/adafruit/Adafruit_MCP2515/blob/master/src/Adafruit_MCP2515.cpp),
and [CircuitPython timing table](https://github.com/adafruit/Adafruit_CircuitPython_MCP2515/blob/main/adafruit_mcp2515/__init__.py).
The bench driver is local C code, not an imported Arduino library.

## CAN packet transport

Development IDs: IHU → transceiver `0x710`; transceiver → IHU `0x711`; local loopback test
`0x712`. These are in the existing reserved debug range; they do not assign
production spacecraft arbitration IDs. Standard data frames only; extended and
RTR traffic are rejected by the driver.

Each fragment carries:

| Byte | Meaning |
| --- | --- |
| 0 | `0x10` version marker, bit0 START, bit1 END; other low bits zero |
| 1–2 | Big-endian 16-bit transfer token, low bits of envelope request ID |
| 3 | Zero-based fragment index |
| 4–7 | Up to four bytes of the complete COBS/CRC UART envelope |

Non-final fragments have exactly four payload bytes. Envelope bound is 263 bytes,
thus at most 66 fragments. Fragments are paced at least 2 ms apart, with one
outgoing envelope and one incoming assembly per controller. Reassembly enforces
route/token/index/size and a 500 ms interfragment deadline. Gaps, duplicate START,
wrong token/order, or overflow abort assembly. A complete envelope must still
pass full magic/length/CRC/identity validation. Token alone is not a session
identity: the full envelope carries origin/sender boot IDs and 32-bit request ID.
There are no fragment retransmissions or automatic application retries.

The [shared UART envelope](../comms_transport/README.md) supplies HELLO and opaque
ECHO semantics. CAN adds diagnostic CHAIN `0x72` and CHAIN_ACK `0x73`; those IDs
are not Walter UART message types. transceiver maps CHAIN onto a separately correlated
Walter HELLO/ECHO exchange. Error reasons add BUSY=5, remote-link-unknown=6,
and invalid heartbeat=7. An unknown remote link stays UNKNOWN at the IHU,
rather than becoming a delivery or command-acceptance report. If a response queue
is occupied, the bench counts a busy drop; the requester times out. Production
queue admission/outcome guarantees are still a separate milestone.

## Heartbeat path and commands

USB commands on either board: `status`, `help`, `selftest`, `normal`, `hello`,
and `ping N` (1–240 ascending bytes). `selftest` is local MCP loopback, leaving
mode loopback; it does not prove an external CAN link. `normal` is required
before `hello`. A matching HELLO establishes peer boot identity before a ping.
One request can be pending; timeout is five seconds, then a fresh HELLO is required.

IHU additionally accepts `telemetry`. The IHU itself generates a 38-byte EMBER
HEARTBEAT with IHU source, ground target, its own boot ID, sequence, uptime,
inner CRC, and fixed SAFE/GROUND_TEST bench fields. Period=0 identifies manual
emission with the EPS timer disabled; an enabled timer reports its configured period. These are
controller-generated bench health fields, not EPS sensor readings.

IHU `eps json` reads the 19-register LTC4162-L profile at address `0x68`,
100 kHz I2C1, **SDA/GPIO2 and SCL/GPIO3**, with common ground.
This uses the Feather's labeled I2C pads; the earlier D4/D5 profile has been replaced.
Each word uses a repeated start and verifies SMBus PEC; a failed read returns
`EPS_READ outcome=FAILED` and the failed register instead of a partial JSON
readout. All successful raw words are preserved, including invalid/warming ADC
status. This command is rejected while a CAN request/transmission is pending.
Reads make no configuration writes. Version2 adds `eps telemetry` for native EPS
packets through CAN/UART echo and `eps lte` for modem submission; those paths
require the matching transceiver/Walter updates and hardware qualification below.

The I2C1 reader-enabled IHU image was built and flash-readback verified on
2026-10-02. Three consecutive hardware reads returned all 19 registers with
valid PEC. The charger reported `telemetry_status=0` and zero ADC words;
these are unavailable engineering measurements. No charger writes were made.
IHU boot `2021172893` also confirmed CAN HELLO with transceiver boot `4252110043`.
[Captured readouts and status](../../system/ground_station/evidence/ihu-eps-i2c1-20261002.json).
Host EPS tests cover valid reads, an independently computed PEC/golden frame,
corrupt data rejection, all-or-nothing output on a late failed register, and
recovery; pointer-only writes are asserted. transceiver firmware was not reflashed.

`eps adc on` / `eps adc off` explicitly read-modify-write only CONFIG_BITS
`force_telemetry_on` bit2, then verify the whole register. Other bits, including
sampling speed and charge policy, are preserved. No automatic configuration
writes occur at boot; commands are rejected during pending CAN work. A failed
write/readback reports UNKNOWN rather than claiming a verified state.
This overrides the chip's normal battery-only ADC shutdown. The existing
low-speed mode remains about five seconds between ADC cycles, so a successful
register read does not necessarily represent a new conversion.
See [ADI datasheet, pages 18/21/39](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf).

Battery-only hardware check subsequently verified CONFIG_BITS `0000` → `0004`
and three PEC-valid readouts with ADC-valid=1: approximately 8.108 V pack (2S
configuration), 8.089 V output and 21.46 °C charger die temperature. Current
scaling retains the unverified 10 mOhm resistor assumption. ADC override is left
enabled for the telemetry bench. IHU boot `117567991` confirmed CAN HELLO with
transceiver boot `4252110043` after flashing.
[Battery-only evidence](../../system/ground_station/evidence/ihu-eps-battery-adc-20261002.json).
Installed UF2 SHA-256:
`596e450977b203cea339b74621f6173f5d82a5766e6cac613570a20d7ba2f811`.

## Version2 native EPS / LTE integration (qualification pending)

`eps telemetry` reads all19 PEC-checked registers, then builds a128-byte native
POWER_STATUS packet and sends it through the same CAN CHAIN/ECHO path. Common
boot, sequence and uptime originate on IHU. Payload provenance2 identifies
IHU_NATIVE; bridge_session_id0 explicitly means no Pi wrapper. readout_count
counts complete EPS reads packaged by this command or `eps lte`; console-only
`eps json` reads do not increment it. No packet is emitted after a failed read.
Engineering values are present only for ADC-valid compatible chemistry/cells;
otherwise INT32_MIN is used. Sense resistor values remain unverified assumptions.
Reads are sequential and do not imply atomic or new ADC conversions.

`lte N` admits a bounded RF window (0 stops, maximum120 seconds); `lte status`
queries Walter's state; `eps lte` reads EPS and requests a single UDP submission.
These require [Walter LTE bench firmware](../walter/README.md).
CAN types74/75 RF window,76/77 send/modem-accepted,78/79 status.
transceiver maps them to distinct UART application types, not diagnostic ECHO.
IHU prints RF_WINDOW_ACCEPTED or MODEM_ACCEPTED, neither claiming ground receipt.
Packet responses preserve exact bytes; status response is16 bytes with correlated
boot/request identity. One chain request remains active; no automatic retries.
transceiver bounds UART sends17s, IHU bounds application sends22s. Other requests retain
2s/5s bounds. The fragment layer and diagnostic heartbeat transport are unchanged.

Builds and host codec/modem mocks pass. Existing CAN heartbeat hardware evidence
does not qualify these new EPS/LTE paths. Flash transceiver, prove real EPS echo with
the current Walter, then flash Walter, test radio-off status and bounded RF.

Prepared artifacts on 2026-10-02:

| Image | SHA-256 | Hardware state |
|---|---|---|
| IHU v2 UF2 | `3290196ccb7859b1c3069fd717a619a9995986fc18f036baafaece2a2f15fd1e` | Flashed/readback verified; EPS ADC-valid and CAN HELLO pass |
| transceiver v2 UF2 | `e1a708fa17fef613d007cfbe19aef0f6d8756bbdf18d3c9fcdcf637357594be6` | Flashed/readback verified; CAN loopback, HELLO and 128-byte echo pass |
| Walter LTE application bin | `851ef9b67618c3cbf33e7a2af56d2637e30ed1c8ca04246d1869162bbe493669` | Built; not flashed |

IHU v2 boot3148122192 read EPS with ADC-valid1 and confirmed the still-running
transceiver v1 boot4252110043 over CAN.
[Pre-transceiver-update evidence](../../system/ground_station/evidence/ihu-eps-v2-pre-comms-20261002.json).
Run `ground/ember/can_chain.py --eps --port IHU_SERIAL --output RUN_DIRECTORY`
after transceiver is updated and its CAN mode set to normal. This checks ten native
ADC-valid EPS returns plus five sized CAN echoes and HELLO. Without `--eps` it
checks the heartbeat baseline. Neither mode activates LTE.

transceiver v2 hardware update completed: boot1790982730, IHU peer3148122192.
Local loopback, physical CAN HELLO and an exact128-byte CAN echo passed;
TEC/REC/EFLG and CAN/fragment/timeout errors remained zero. Left transceiver in normal
CAN mode with Walter powered separately; UART chain had not been exercised in
this post-flash check (`walter_peer=0`, `chain_ok=0`).
[transceiver post-flash evidence](../../system/ground_station/evidence/comms-eps-v2-flash-check-20261002.json).
The subsequent real EPS chain test passed: ten native128-byte POWER_STATUS
returns (sequences0–9, readout_count1–10), ADC/conversion-valid1, IHU boot3148122192
and transceiver boot1790982730. CRC/header/identity/sequence/engineering quality checks
passed along with five sized CAN echoes and HELLO. IHU matched count increased
by16; CAN/fragment/timeout/BUSY/UNKNOWN errors remained zero. Battery8.099–8.100 V,
output about8.080 V, die21.464 °C; current scaling remains provisional.
[Real EPS evidence](../../system/ground_station/evidence/ihu-comms-walter-eps-can-20261002.json).
This verifies actual EPS reads through CAN and UART echo, not LTE reception.
transceiver post-chain counters were not independently sampled with USB on IHU.
Walter LTE upload still follows.

```text
IHU heartbeat -- CAN --> transceiver -- framed UART --> Walter bench echo
IHU validates <-- CAN -- transceiver <-- framed UART -- identical packet
```

transceiver validates the heartbeat header/inner CRC and preserves the complete inner
packet. Walter is handshaken when necessary; transceiver verifies its exact echo before
returning CHAIN_ACK to IHU. IHU checks peer/session/request/type and the complete
packet bytes. Only then does it print `WALTER_BENCH_RETURN`. This proves the
local three-controller path, not LTE reception or spacecraft command execution.
UART logs are skipped when transceiver USB is disconnected to avoid waiting for an
absent console during forwarding. Sustained traffic remains unqualified.

## Historical build and flash

These commands and identities record the earlier combined application. Use
the current build command at the top of this guide or the separate
[Walter MCU build guide](../walter_mcu/README.md).

Keep the repository layout: this project needs sibling `comms_transport` and
`ground/ember/generate_c.py`, `codec.py`, and `dictionary.json`.
On m75q the standalone work tree is `~/work/MSU_Cubesat/ember-can/`:

```sh
docker exec amsat-dev-x86 cmake \
  -S /workspace/MSU_Cubesat/ember-can/firmware/ihu \
  -B /workspace/MSU_Cubesat/ember-can/firmware/ihu/build \
  -DPICO_SDK_PATH=/opt/pico-sdk -DCMAKE_BUILD_TYPE=Release
docker exec amsat-dev-x86 cmake --build \
  /workspace/MSU_Cubesat/ember-can/firmware/ihu/build -j4
```

Identify the board before flashing. transceiver flash ID is `DF637882D39E4426`, IHU
`DF641455DB822427`. Native USB descriptors call both Raspberry Pi Pico; the
unique flash IDs and role status distinguish them. Use the USB-enabled picotool
at `~/work/ember-comms-feather/picotool-usb`. For a running SDK USB image:

```sh
sudo ~/work/ember-comms-feather/picotool-usb load -v -x -f \
  --ser ACTUAL_FLASH_ID PATH_TO_CORRECT_ROLE.uf2
```

For a physical BOOTSEL device, inspect `lsusb` and picotool info, then select its
actual bus/address. Do not use transceiver serial selection or its image for IHU.
Initial IHU bootloader was bus3/address82; that address is historical.

Full 8 MB flash backups were saved and verified before installing these images.
Each UF2 is 16 MB because UF2 encodes 256 payload bytes per 512-byte block.
Backups are private/root-owned mode600, under the m75q directory
`/media/ngrabbs/BACKUP-A/ember-walter-bridge/`:

- `comms-before-can-20261002.uf2`: SHA-256
  `82e058a1be51b0aef204ac27e551da0e0de43fcce09a206e63b020bc9d714aab`;
  restores the proven framed UART bench image.
- `ihu-before-can-20261002.uf2`: SHA-256
  `9a9a236028ad18f4fd4f6c123731b9a9f80a56844c455464d5ca25fc189c1eed`;
  previous program `rt-ihu-can-sim`, SDK2.1.1, old Pico build profile.

To restore a board, enter BOOTSEL, reidentify that exact physical device, and
load its own backup with `-v -x`. Restoration has not been exercised; backup
readback verification passed. Keep the existing module supply/USB isolation plan.

## Validation and current evidence

Native fragmentation tests:

```sh
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I firmware/comms_transport firmware/comms_transport/tests/test_can_fragment.c \
  -o /tmp/ember_can_fragment_test
/tmp/ember_can_fragment_test
```

Passed: all 1–263-byte fragment bounds; missing/duplicate/order/token/route errors;
interfragment timeout/timer wrap; recovery; all 1–240-byte real envelope round trips
with unchanged identity/payload. Both board builds and flash readback passed.
Both MCP local loopback tests passed. IHU-initiated HELLO plus exact echoes at
1, 8, 32, 239, and 240 bytes passed across the physical bus. After updating transceiver,
transceiver-initiated HELLO and a 32-byte echo also passed, with zero reported CAN errors.

The first chain attempt exposed stale loop time after synchronous UART HELLO
handling started ECHO: unsigned subtraction immediately expired the new request.
transceiver now refreshes time after UART callbacks before checking expiration. The
corrected image is installed and verified; the first failed transcript remains
private in `can-chain-pre-fix-20261002/`. IHU binary is unchanged by this transceiver-only fix.

The full chain retest passed: CAN HELLO plus all five boundary echoes, followed
by 10/10 38-byte heartbeats generated on the physical IHU and returned unchanged
through transceiver and Walter. Heartbeat sequences 1–10 retained IHU boot ID
1272163253, with increasing uptime 430875–438121 ms. Each inner CRC decoded
correctly. IHU's match count rose 6 → 22 (16 new matches); TX-success/RX counters
each rose by 317 including the local self-test, with no increase in CAN TX
failure/timeout, RX bad/overflow, fragment error/timeout, busy drop, or UNKNOWN.
TEC/REC stayed zero and EFLG was zero at completion. The existing UNKNOWN=1 is
the earlier clock bug, not a new failure. transceiver post-chain counters were not
independently sampled.

[Saved evidence](../../system/ground_station/evidence/ihu-comms-walter-can-20261002.json)
includes decoded heartbeats, hardware identities, binary hashes, counter baselines,
and scope. The private transcript is `can-chain-20261002/can-chain.log` beneath
the m75q task directory. All 30 existing ground tests also passed.

Historical heartbeat-chain UF2 SHA-256 (before the later native EPS images):

- IHU: `c5cff5e021e2b21c3b9316193a49fca53891da875be2dc1be7e4b5e2bebee403`
- transceiver: `507110580861478d2e688fa16053a0457de1bcd6edc59dd8936bbb9ebc5cdf78`

With transceiver in normal mode and Walter powered, connect USB to IHU and run:

```sh
python3 ground/ember/can_chain.py \
  --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 \
  --output /path/to/private/evidence
```

It checks local self-test, CAN handshake/five boundary echoes, ten IHU-generated
heartbeat returns through Walter, decoded IHU boot/sequence/uptime, and no new
CAN/fragment errors or application timeouts. Output includes full USB transcript
and decoded JSON. At that heartbeat checkpoint, EPS integration, cadence, Yamcs and radio delivery
were future work; later sections and the LTE evidence index record native EPS
and LTE delivery. Production FreeRTOS scheduling remains separate work; the optional UHF bench
and native timer are described below. Independent reset/fault recovery, endurance, production
integration and CAN B remain open.

## Opt-in EPS FIFO candidate

The IHU bench harness can stage four actual EPS packets with `eps enqueue`.
`lte queue on/off/status/drop` controls a volatile FIFO; it never starts RF.
Only explicit pre-submission NOT_READY/BUSY is retried, at most three send
attempts. Uncertain outcomes, modem rejection and expiry hold the original
packet for inspection. Enqueue refuses active CAN exchanges. Queue retirement
means modem acceptance; independently validate reception/archive.
[Policy, tests and deployment record](../../ground/lte/results/2026-10-02-queue-preparation.md).
The operational queue belongs in transceiver; this is bench harness staging.

## Opt-in native IHU EPS cadence — October 3, 2026

The IHU bench firmware now has a local timer for the same readout and `CF_CHAIN`
packet path used by `eps telemetry`. No SDRB-specific command or packet field was
added. Automatic emission is disabled at boot and the setting is not persisted.
After `normal` and a successful `hello`, with the LTE queue disabled:

```text
telem on 20
telem status
telem off
```

`telem on` alone selects20 seconds; an explicit period must be5..3600 seconds.
The first read occurs after one period. Status reports enabled, period/next time,
due/skipped/submitted/failed counters and pending transaction state. Submitted
means local CAN submission, not RF reception. Manual `eps telemetry` remains
available. The manual heartbeat reports the configured telemetry period while
this timer is enabled, or zero while disabled.

The timer runs in the IHU loop without a USB scheduling dependency. It checks for
an idle CAN transaction before invoking the existing bounded synchronous EPS
reader. Busy, unhandshaken, non-normal CAN or active LTE queue periods are skipped;
there is no catch-up burst or retained telemetry backlog. Failed reads are counted
and the next scheduled period reads fresh data. Peer loss needs the existing
manual HELLO recovery. `telem off` prevents future reads but does not cancel an
already submitted transaction. No ADC override, charger policy or LTE RF-window
command is added. Production FreeRTOS scheduling remains a separate integration.

[Saved proof](../../ground/uhf/results/2026-10-03/native-autotelem/result.json):
three native packets at20-second intervals with passive USB observation, followed
by one further packet while the USB console was closed/DTR released for 25 seconds.
All four were delivered over CAN→SDRB→UHF→LibreSDR→Yamcs. The first three have
IHU returned-byte evidence; the fourth has native counter/closed-console timing
and byte identity at CAN/socket/RF/archive. The physical cable stayed connected.
Timer boot-off, period rejection and manual packet operation passed. Final timer
state is off; radios are released and SDRB CAN0/1 are down.

Both roles built with Pico SDK `2.1.1-1-gee68c78` and GCC14.2.1, warnings treated
as errors; only IHU `DF641455DB822427` was flashed and verified. The tested IHU UF2
SHA256 is `44bb70d0256567e78e6ac7acd3836faca45eef0c27281184c12b9a0e65a7789f`.
The separate m75q build tree is
`/home/ngrabbs/work/MSU_Cubesat/ember-autotelem-20261003`. The verified full8MB
pre-change backup stays private on m75q:
`/media/ngrabbs/BACKUP-A/ember-autotelem-20261003/ihu-before-autotelem.uf2`, SHA256
`a87c2204f52490a27d47402637e4a63f97754b0e9579091b23b468eeda8dbfd0`.
Build/flash/source identities are retained with the proof; restoration was not
exercised. transceiver, Walter and all AMSAT software/images were left unchanged.

## UHF transceiver batch client (can-bench-v4)

After HELLO with the physical transceiver, while its explicit `g` collection
window is open, use `uhf heartbeat`, `uhf system`, or `uhf eps`. Wait for QUEUED
before submitting another packet (maximum4 outstanding). A separate local
RF_TX_COMPLETE / RF_TX_FAILED / CANCELLED reply releases each result tracker;
none implies ground reception. `status` reports `uhf_pending`. Admission has
5 seconds, final results30 seconds; timeouts are UNKNOWN without automatic
retry. Existing LTE commands and automatic telemetry defaults are unchanged.
Health packet producers from the deployed can-bench-v3 are preserved.

## Timed telemetry producer (can-bench-v5)

The default is IDLE, including after resets. With transceiver `a` service running and
normal CAN/HELLO established, `uhf run 120 10` produces heartbeat/system/EPS
cycles every 10 seconds for 120 seconds. One packet is in flight at a time and
results are checked before advancing. `status` reports progress; `uhf stop`
stops future production, while an admitted packet may finish. Stop transceiver too
for an immediate RF abort. Bad/missing results or producer failure enter FAULT;
there is no automatic retry, restart, or persistent enable. Legacy automatic
telemetry and LTE queue must be off. Mode numbers and detailed limits are in
`system/interfaces/transceiver_uhf_bench.md`.

IHU v6 corrects timed-run recovery after a prior CAN transmit error. Each new
explicit run snapshots lifetime TX failure/timeout counters; only a subsequent
change faults that run. Current CAN mode, readiness, peer and EFLG checks remain
active. Historical counters are preserved for diagnosis rather than cleared.

IHU v7 adds the [expected-device registry](../../system/interfaces/device_registry.md).
CAN enters normal mode at boot. `devices` reports runtime health; `devices scan`
expedites the next idle-time probe. Scanning never arms RF. Current EPS is checked
on I2C; future EPS and payload plus LTE have reserved CAN discovery identities.
