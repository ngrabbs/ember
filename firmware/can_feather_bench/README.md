# IHU–COMMS CAN Feather bench

The new IHU MCU and COMMS MCU both use Adafruit RP2040 CAN Bus Feathers with
onboard MCP25625 CAN controllers/transceivers. This standalone Pico SDK project
builds `ember_ihu_can_bench.uf2` and `ember_comms_can_bench.uf2` from one source,
with distinct roles. It replaces neither the complete FreeRTOS IHU/EPS application
nor the UHF COMMS application. The IHU role now supports manual read-only EPS
register observation; it does not write the EPS, activate UHF,
control LTE radio state, execute flight commands, or implement CAN redundancy.
Walter retains the installed framed diagnostic with its modem held in reset.

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
inner CRC, and fixed SAFE/GROUND_TEST bench fields. Period=0 identifies manual
emission; there is no periodic telemetry scheduler in this image. These are
controller-generated bench health fields, not EPS sensor readings.

IHU `eps json` reads the 19-register LTC4162-L profile at address `0x68`,
100 kHz I2C0, **D4/GPIO4 SDA and D5/GPIO5 SCL**, with common ground. These
are different from the Feather's labeled SDA/SCL pads (GPIO2/3).
Each word uses a repeated start and verifies SMBus PEC; a failed read returns
`EPS_READ outcome=FAILED` and the failed register instead of a partial JSON
readout. All successful raw words are preserved, including invalid/warming ADC
status. This command is rejected while a CAN request/transmission is pending.
It makes no charger configuration writes and does not yet forward EPS packets
through CAN or LTE. Native EPS packet forwarding is the next integration step.

The reader-enabled IHU image was built and flash-readback verified on 2026-10-02;
UF2 SHA-256 `bc2720b9d6471c4193d83a512ab7a26cfd141715763aaeda041de6ad59462d8b`.
After flashing, IHU boot `613337324` confirmed CAN HELLO with COMMS boot
`4252110043`. Hardware EPS reads remain pending SDA/SCL wiring confirmation.
Host EPS tests cover valid reads, an independently computed PEC/golden frame,
corrupt data rejection, all-or-nothing output on a late failed register, and
recovery; pointer-only writes are asserted. COMMS firmware was not reflashed.

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

[Saved evidence](../../system/ground_station/evidence/ihu-comms-walter-can-20261002.json)
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
