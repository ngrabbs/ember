# IHU–COMMS CAN Feather bench

The new IHU MCU and COMMS MCU both use Adafruit RP2040 CAN Bus Feathers with
onboard MCP25625 CAN controllers/transceivers. This standalone Pico SDK project
builds `ember_ihu_can_bench.uf2` and `ember_comms_can_bench.uf2` from one source,
with distinct roles. It replaces neither the complete FreeRTOS IHU/EPS application
nor the UHF COMMS application. The IHU role now supports manual read-only EPS
register observation and explicit battery-only ADC enable; it does not change
charging policy, activate UHF, execute flight commands, or implement CAN redundancy.
Version2 adds native EPS packet forwarding and explicit bounded Walter LTE requests.
Both CAN Feathers are updated and native EPS forwarding through Walter echo
passed. Walter still has the installed framed diagnostic with its modem held
in reset; its LTE hardware update and RF qualification remain pending.

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

Development IDs: IHU → COMMS `0x710`; COMMS → IHU `0x711`; local loopback test
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
are not Walter UART message types. COMMS maps CHAIN onto a separately correlated
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
inner CRC, and fixed SAFE/GROUND_TEST bench fields. The period field is zero
when automatic EPS cadence is off, or its configured period when enabled.
`telemetry` emits a manual HEARTBEAT; `telem on` schedules EPS POWER_STATUS. These are
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
require the matching COMMS/Walter updates and hardware qualification below.

The I2C1 reader-enabled IHU image was built and flash-readback verified on
2026-10-02. Three consecutive hardware reads returned all 19 registers with
valid PEC. The charger reported `telemetry_status=0` and zero ADC words;
these are unavailable engineering measurements. No charger writes were made.
IHU boot `2021172893` also confirmed CAN HELLO with COMMS boot `4252110043`.
[Captured readouts and status](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/ihu-eps-i2c1-20261002.json).
Host EPS tests cover valid reads, an independently computed PEC/golden frame,
corrupt data rejection, all-or-nothing output on a late failed register, and
recovery; pointer-only writes are asserted. COMMS firmware was not reflashed.

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
COMMS boot `4252110043` after flashing.
[Battery-only evidence](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/ihu-eps-battery-adc-20261002.json).
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
These require [Walter LTE bench firmware](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/firmware/walter_lte_bench/README.md).
CAN types74/75 RF window,76/77 send/modem-accepted,78/79 status.
COMMS maps them to distinct UART application types, not diagnostic ECHO.
IHU prints RF_WINDOW_ACCEPTED or MODEM_ACCEPTED, neither claiming ground receipt.
Packet responses preserve exact bytes; status response is16 bytes with correlated
boot/request identity. One chain request remains active; no automatic retries.
COMMS bounds UART sends17s, IHU bounds application sends22s. Other requests retain
2s/5s bounds. The fragment layer and diagnostic heartbeat transport are unchanged.

Builds and host codec/modem mocks pass. Existing CAN heartbeat hardware evidence
does not qualify these new EPS/LTE paths. Flash COMMS, prove real EPS echo with
the current Walter, then flash Walter, test radio-off status and bounded RF.

Prepared artifacts on 2026-10-02:

| Image | SHA-256 | Hardware state |
|---|---|---|
| IHU v2 UF2 | `3290196ccb7859b1c3069fd717a619a9995986fc18f036baafaece2a2f15fd1e` | Flashed/readback verified; EPS ADC-valid and CAN HELLO pass |
| COMMS v2 UF2 | `e1a708fa17fef613d007cfbe19aef0f6d8756bbdf18d3c9fcdcf637357594be6` | Flashed/readback verified; CAN loopback, HELLO and 128-byte echo pass |
| Walter LTE application bin | `851ef9b67618c3cbf33e7a2af56d2637e30ed1c8ca04246d1869162bbe493669` | Built; not flashed |

IHU v2 boot3148122192 read EPS with ADC-valid1 and confirmed the still-running
COMMS v1 boot4252110043 over CAN.
[Pre-COMMS-update evidence](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/ihu-eps-v2-pre-comms-20261002.json).
Run `ground/ember/can_chain.py --eps --port IHU_SERIAL --output RUN_DIRECTORY`
after COMMS is updated and its CAN mode set to normal. This checks ten native
ADC-valid EPS returns plus five sized CAN echoes and HELLO. Without `--eps` it
checks the heartbeat baseline. Neither mode activates LTE.

COMMS v2 hardware update completed: boot1790982730, IHU peer3148122192.
Local loopback, physical CAN HELLO and an exact128-byte CAN echo passed;
TEC/REC/EFLG and CAN/fragment/timeout errors remained zero. Left COMMS in normal
CAN mode with Walter powered separately; UART chain had not been exercised in
this post-flash check (`walter_peer=0`, `chain_ok=0`).
[COMMS post-flash evidence](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/comms-eps-v2-flash-check-20261002.json).
The subsequent real EPS chain test passed: ten native128-byte POWER_STATUS
returns (sequences0–9, readout_count1–10), ADC/conversion-valid1, IHU boot3148122192
and COMMS boot1790982730. CRC/header/identity/sequence/engineering quality checks
passed along with five sized CAN echoes and HELLO. IHU matched count increased
by16; CAN/fragment/timeout/BUSY/UNKNOWN errors remained zero. Battery8.099–8.100 V,
output about8.080 V, die21.464 °C; current scaling remains provisional.
[Real EPS evidence](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/ihu-comms-walter-eps-can-20261002.json).
This verifies actual EPS reads through CAN and UART echo, not LTE reception.
COMMS post-chain counters were not independently sampled with USB on IHU.
Walter LTE upload still follows.

```text
IHU heartbeat -- CAN --> COMMS -- framed UART --> Walter bench echo
IHU validates <-- CAN -- COMMS <-- framed UART -- identical packet
```

COMMS validates the heartbeat header/inner CRC and preserves the complete inner
packet. Walter is handshaken when necessary; COMMS verifies its exact echo before
returning CHAIN_ACK to IHU. IHU checks peer/session/request/type and the complete
packet bytes. Only then does it print `WALTER_BENCH_RETURN`. This proves the
local three-controller path, not LTE reception or spacecraft command execution.
UART logs are skipped when COMMS USB is disconnected to avoid waiting for an
absent console during forwarding. Sustained traffic remains unqualified.

## Build and flash

Keep the repository layout: this project needs sibling `comms_transport` and
`ground/ember/generate_c.py`, `codec.py`, and `dictionary.json`.
On m75q the standalone work tree is `~/work/MSU_Cubesat/ember-can/`:

```sh
docker exec amsat-dev-x86 cmake \
  -S /workspace/MSU_Cubesat/ember-can/firmware/can_feather_bench \
  -B /workspace/MSU_Cubesat/ember-can/firmware/can_feather_bench/build \
  -DPICO_SDK_PATH=/opt/pico-sdk -DCMAKE_BUILD_TYPE=Release
docker exec amsat-dev-x86 cmake --build \
  /workspace/MSU_Cubesat/ember-can/firmware/can_feather_bench/build -j4
```

Identify the board before flashing. COMMS flash ID is `DF637882D39E4426`, IHU
`DF641455DB822427`. Native USB descriptors call both Raspberry Pi Pico; the
unique flash IDs and role status distinguish them. Use the USB-enabled picotool
at `~/work/ember-comms-feather/picotool-usb`. For a running SDK USB image:

```sh
sudo ~/work/ember-comms-feather/picotool-usb load -v -x -f \
  --ser ACTUAL_FLASH_ID PATH_TO_CORRECT_ROLE.uf2
```

For a physical BOOTSEL device, inspect `lsusb` and picotool info, then select its
actual bus/address. Do not use COMMS serial selection or its image for IHU.
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
1, 8, 32, 239, and 240 bytes passed across the physical bus. After updating COMMS,
COMMS-initiated HELLO and a 32-byte echo also passed, with zero reported CAN errors.

The first chain attempt exposed stale loop time after synchronous UART HELLO
handling started ECHO: unsigned subtraction immediately expired the new request.
COMMS now refreshes time after UART callbacks before checking expiration. The
corrected image is installed and verified; the first failed transcript remains
private in `can-chain-pre-fix-20261002/`. IHU binary is unchanged by this COMMS-only fix.

The full chain retest passed: CAN HELLO plus all five boundary echoes, followed
by 10/10 38-byte heartbeats generated on the physical IHU and returned unchanged
through COMMS and Walter. Heartbeat sequences 1–10 retained IHU boot ID
1272163253, with increasing uptime 430875–438121 ms. Each inner CRC decoded
correctly. IHU's match count rose 6 → 22 (16 new matches); TX-success/RX counters
each rose by 317 including the local self-test, with no increase in CAN TX
failure/timeout, RX bad/overflow, fragment error/timeout, busy drop, or UNKNOWN.
TEC/REC stayed zero and EFLG was zero at completion. The existing UNKNOWN=1 is
the earlier clock bug, not a new failure. COMMS post-chain counters were not
independently sampled.

[Saved evidence](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/system/ground_station/evidence/ihu-comms-walter-can-20261002.json)
includes decoded heartbeats, hardware identities, binary hashes, counter baselines,
and scope. The private transcript is `can-chain-20261002/can-chain.log` beneath
the m75q task directory. All 30 existing ground tests also passed.

Current UF2 SHA-256:

- IHU: `c5cff5e021e2b21c3b9316193a49fca53891da875be2dc1be7e4b5e2bebee403`
- COMMS: `507110580861478d2e688fa16053a0457de1bcd6edc59dd8936bbb9ebc5cdf78`

With COMMS in normal mode and Walter powered, connect USB to IHU and run:

```sh
python3 ground/ember/can_chain.py \
  --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 \
  --output /path/to/private/evidence
```

It checks local self-test, CAN handshake/five boundary echoes, ten IHU-generated
heartbeat returns through Walter, decoded IHU boot/sequence/uptime, and no new
CAN/fragment errors or application timeouts. Output includes full USB transcript
and decoded JSON. Fault injection, independent reset/recovery, live EPS integration,
periodic streaming, Yamcs ingestion, CAN B, UHF, and LTE delivery remain future work.

## Opt-in EPS FIFO candidate

The IHU bench harness can stage four actual EPS packets with `eps enqueue`.
`lte queue on/off/status/drop` controls a volatile FIFO; it never starts RF.
Only explicit pre-submission NOT_READY/BUSY is retried, at most three send
attempts. Uncertain outcomes, modem rejection and expiry hold the original
packet for inspection. Enqueue refuses active CAN exchanges. Queue retirement
means modem acceptance; independently validate reception/archive.
[Policy, tests and deployment record](https://github.com/ngrabbs/ember/blob/feature/lte-m-bench/ground/lte/results/2026-10-02-queue-preparation.md).
The operational queue belongs in COMMS; this is bench harness staging.


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
by one further packet while the USB console was closed/DTR released for25 seconds.
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
exercised. COMMS, Walter and all AMSAT software/images were left unchanged.
