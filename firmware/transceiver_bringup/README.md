# Y24 transceiver bring-up

Original Pico only. This deliberately bounded image is separate from the legacy
`comms` application. It holds TX/RX inactive, both MCP25625 transceivers in standby,
and disables Si5351 outputs at boot and while idle. External CAN operation is limited to
explicit console test windows: `l`, `n`, and `h` (see below).

Version 3 performs one boot-time independent-register test using opposite
patterns in inactive TXB0D0 RAM, restores those bytes, then runs one internal
loopback frame per controller (standard ID 0x321, DLC 8, distinct payloads).
It checks RX ID/DLC/data and TX completion, clears flags, and returns to
configuration mode. Both STBY outputs stay high. Boot tests use only configuration and loopback modes. Mode and receive polls have 100-iteration bounds;
any failed test holds the affected controller in reset until reboot. A failed
independence check holds both in reset and skips loopback.

The repeated self-test line reports the boot-time result, not repeated frames.
Loopback codes: 0 pass, 1 initial configuration failure, 2 loopback-mode failure,
3 completion timeout, 4 received-frame mismatch, 5 configuration restore failure,
6 skipped. SPI0 uses 1 MHz, mode 0. This does not validate external CAN wiring,
transceiver operation, bus bitrate, or interrupt pins. See Microchip DS20005282C.

Outside an explicit clock-test window, every second it writes Si5351 register 3 = 0xFF and checks the readback, using
bounded I2C operations. `NOT_VERIFIED` is expected on a bare Pico. Successful
readback is register evidence, not an RF measurement. ADC1 is reported raw;
its reading is meaningless while the Pico is disconnected from RX_BASEBAND.

Pin assignments follow the ordered-board pad export at
`hardware/comms/verification/review_20261004_final/pads-all.json`:
CAN standby GP2/3, MISO GP4, SCK GP6, MOSI GP7, reset GP8/9,
TX/RX GP10/11, indicator GP12, CAN CS GP14/15, BPSK GP16,
CAN interrupts GP18/19, I2C SDA/SCL GP20/21, RX ADC GP27.

Build with the Pico SDK and ARM GCC:

```sh
cmake -S firmware/transceiver_bringup -B build/transceiver_bringup -DPICO_BOARD=pico
cmake --build build/transceiver_bringup -j4
```

Before flashing, save and verify the existing Pico flash. Before installation,
disconnect USB and both board supplies. Firmware output levels only apply once
this program starts; hardware pulls/mute must cover reset and power sequencing.
Do not operate the installed Pico from USB alone with board rails off.
This image does not qualify CAN, the receive path, or transmit hardware.

## Version 4: bounded CAN A receive windows

After successful boot tests, send `l` for a 10-second listen-only window, or `n`
for a 10-second normal-mode receive window that acknowledges valid CAN frames.
CAN A uses 500 kbit/s with the ordered 16 MHz oscillator, CNF1/2/3=00/f0/86.
All three transmit requests are cleared before normal-mode entry. The `l` and `n` windows never request application-frame transmission; normal mode
can produce CAN acknowledgments/error signaling. CAN B stays in standby.
Burst SPI reads and RX0-to-RX1 rollover reduce capture overhead.
Each window returns A to standby and configuration mode; failed transitions
hold it in reset. The first 32 received buffers are saved in RAM and printed after capture, with a total
frame count and final EFLG. Listen-only reception can include invalid traffic;
its error counters are not a bus-quality metric. This polling test is not a
high-load capture tool. RF control outputs remain inactive throughout.

The startup sequencing issue observed in the stack remains pending a physical
cold-start retest. Version 6 adds bounded readiness retries as described below.

## Version 5: one HELLO reply

Send `h` to open a ten-second CAN A normal-mode window and allow one HELLO_ACK
reply to one valid HELLO request from IHU (CAN ID 0x710). Reassembly and the
COBS/CRC envelope use the shared `comms_transport` headers. Version, type,
empty payload, sender/origin relationship, and fragment-token/request match
are checked. Other requests are ignored. A fresh random nonzero boot ID is
reported in the reply; origin and request are preserved. Replies use ID 0x711,
2 ms interfragment spacing and one-shot transmission with bounded completion.
No LTE, EPS control, RF command, or ECHO service is implemented here.
Failure stops transmission and holds A in reset; successful windows restore
standby/configuration. An IHU matched HELLO response, not just TX completion,
is the evidence of an end-to-end test.

Host checks:

```sh
python3 firmware/transceiver_bringup/tests/check.py
cc -std=c11 -Wall -Wextra -Werror -Ifirmware/transceiver_bringup -Ifirmware/comms_transport firmware/transceiver_bringup/tests/hello.c -o /tmp/y24-hello-test
/tmp/y24-hello-test
```

## Version 6: bounded startup readiness

Before the independence/loopback tests, keep both transceivers in standby and
attempt controller reset/readback up to twenty times (roughly five seconds).
Each attempt holds reset low for 10 ms, releases it for 20 ms, then requires two
configuration-register samples 20 ms apart. A failed attempt reasserts both
resets and waits 200 ms before retrying. Si5351 disable is attempted during
this sequence. Exhaustion leaves both resets asserted; no bus mode is enabled.

The `[startup]` line retains the result, attempt count, and last pre-failure-reset
CANSTAT/CANCTRL values. This is a controller-response check, not power-good
measurement, and does not make USB-only powering of the installed board safe.
Late power arrival beyond the retry window still requires a Pico restart.
Host fault injection covers delayed replies, permanent failure, and recovery;
actual cold-start validation is tracked in the lab log.

## Version 7: bounded CLK0 bench test

`s` reads Si5351 status, output controls and crystal-load register without enabling
an output. `c` requests a fixed 10 MHz CLK0 window, at most ten seconds from
before output enable. Send the single byte with no newline; any input during
the window aborts. CLK1/CLK2 stay disabled, TX/RX/BPSK stay low, and both CAN
transceivers stay in standby. No boot-time clock test runs.

The fixed plan follows [Skyworks AN619 rev 0.8](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN619.pdf):
25 MHz crystal, PLLA ×32, MS0 ÷80, integer mode, 2 mA output drive.
Configuration writes are read back; SYS_INIT, crystal-loss and PLLA-lock status
are checked before enabling and during the window. Failure or timeout attempts
both output disable and CLK0 power-down; shutdown failure is reported explicitly.
An I2C hardware failure can prevent shutdown, so firmware is not a replacement
for the physical TX mute. No USB printing occurs while the clock is enabled.

The existing crystal-load register is preserved. The exported design includes
external 15 pF C1/C2 as well as the Si5351's internal capacitance; total loading
and frequency accuracy need measurement before choosing a final setting.

Probe TP1 (CLK0_OUT, after C6/R3), with a short nearby ground at C81 pad 2.
TP1 is AC-coupled; do not assume its DC levels match the Si5351 pin directly.
Keep the tinySA disconnected for this scope-only check. Confirm probe placement
before sending `c`; a successful register test alone does not verify RF mute.

Additional host test:

```sh
cc -std=c11 -Wall -Wextra -Werror -Ifirmware/transceiver_bringup firmware/transceiver_bringup/tests/clock.c -o /tmp/y24-clock-test
/tmp/y24-clock-test
```

## Version 8: explicitly requested conducted TX tone

`t` requests one maximum-ten-second unmodulated carrier test targeting 437 MHz
at J9. CLK0 is 874 MHz /6 (145.666667 MHz), using PLLA = 25 MHz ×(34+24/25).
PLLA is fractional, MS0 integer, output drive 2 mA. RX clock stays off,
BPSK stays low and CAN transceivers stay in standby. TX_ACTIVE is asserted
only after verified configuration/lock while CLK0 is disabled, followed by
1 ms switch settling before enabling the clock. Cleanup attempts clock disable
and power-down, then always deasserts TX_ACTIVE, including I²C failures.
Any console input aborts. No automatic TX occurs on boot.

This test was requested with a DC block and external 30 dB pad into the tinySA
RF input. Remove the scope probe before RF measurements. C6's negative XOR
input level remains an open issue; running this exploratory test does not waive
it or qualify the TX chain. Report measured antenna power only after applying
known attenuator/cable loss and checking analyzer settings, overload and spurs.

## Version 9: integer-ratio comparison

`u` runs the same bounded conducted-TX test at nominal 437.5 MHz, with PLLA
875 MHz (25 MHz ×35), MS0 divide-by-six and the existing tripler. This is a
diagnostic comparison, not a change to the 437 MHz design target. The PLL
ratio has no fractional remainder; FBA_INT remains clear because 35 is odd
(AN619 §3.2.1). All mute, lock, timeout and abort behavior matches `t`.
The external DC block and 30 dB pad must remain connected to the tinySA RF input.

## Version 10: temporary crystal-load comparison

Single-byte commands `0`, `8`, `6` select 10, 8, 6 pF internal loading for one
muted 10 MHz window, then restore register183's saved value. AN619 specifies
D2,92,52 respectively; the reserved 00 setting is never selected. Configuration
is read back and allowed 200 ms to settle before the existing lock-checked
clock window. Cleanup retries restoration once if necessary but reports a
first-attempt restoration failure rather than hiding it. Read status after any
failure before continuing. This does not change external C1/C2 or calibrate the
crystal. The load values describe the Si5351 internal setting, not the total
assembled crystal load. TX/RX/BPSK stay low throughout.

## v11: one bounded DBPSK heartbeat

Single byte `b` sends one native COMMS heartbeat at1200 baud, approximately
673ms, with a2-second independent timer mute and checked cleanup. No automatic
transmission. See [waveform, limits and ground procedure](../../ground/bpsk/README.md).
C1/C2 removal and C6 replacement are physical prototype reworks documented in
the lab log; these firmware changes do not update KiCad source/BOM.

## v12: muted data-input measurement

Single byte `d` holds TX_ACTIVE and RX_ACTIVE low, verifies Si5351 output
disable, then toggles GP16 at approximately 10 Hz for at most five seconds.
Any console input aborts; GP16 returns low. Failed initial clock-disable
verification refuses the pattern. No clock or RF path is enabled by this test.
Probe C65 pad 1 (U7 pin 2 side), grounded at C65 pad 2, to check the data-input
logic levels. This measures settled data levels, not RF phase performance.

## v13: bounded RF phase holds

Explicit `p` sends ten alternating GP16 states (0,1,...), each 100 ms, at the
existing nominal 437 MHz setting: one second total RF. Uses the same checked
clock setup/cleanup, 1.5-second payload deadline and independent two-second
interrupt mute as `b`. Console input, late transition or timer aborts. No
periodic TX, telemetry packet or Yamcs forwarding. This isolates settled RF
phase states for receiver capture; verify scope removal and antenna setup first.

## v14: controlled CLK0 drive comparison

`p` remains the 2 mA baseline; explicit `j`, `k`, `m` select 4, 6, 8 mA for
one phase-hold burst respectively. Only register16 bits1:0 change, as documented
in [Skyworks AN619](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN619.pdf).
Frequency, PLL, divider, data sequence and bounds are unchanged. Cleanup restores
register16 to 0x80 (powered down, 2 mA field); future normal tests use 2 mA.
No automatic sweep or persistent drive setting. Check each result before advancing.

## v15: integer-PLL phase-hold comparison

Explicit `q` sends the same one-second phase holds at 4 mA using PLLA=875 MHz
(25 MHz times 35), MS0 divide by six, nominal tripled carrier 437.5 MHz.
Compare with `j` (4 mA, 437 MHz, PLLA=874 MHz fractional ratio). Retune the
receiver accordingly. The odd integer PLL ratio keeps FBA_INT clear, matching
the previously tested `u` plan. Existing mute/deadline/cleanup are unchanged.
This comparison also shifts the RF frequency by 500 kHz; any difference cannot
be attributed uniquely to PLL fractional behavior. No default frequency change.

## v16: explicit 4 mA packet comparison

Uppercase `B` sends one native heartbeat using 4 mA CLK0 drive at437 MHz.
Lowercase `b` retains the 2 mA baseline. Frame format, 1200-baud timing,
1.5-second deadline, two-second timer mute and shutdown are unchanged.
The strict ground decoder is unchanged; passing CRC and byte identity does
not establish ideal180-degree modulation or link reliability.

## v17: explicitly armed single IHU heartbeat bridge

`f` enables a maximum10-second CAN A receive window, admitting one validated
CF_CHAIN envelope from IHU containing a38-byte native IHU HEARTBEAT. It checks
envelope CRC/identity/token and native length/schema/type/source/boot/CRC,
returns CAN to standby/configuration, then wraps the unchanged packet in the
existing RF frame and sends once at4 mA. Missing/invalid packets or CAN errors
produce no RF. Existing RF deadlines and shutdown apply. No automatic service.

The existing IHU `telemetry` command uses a historical CF_CHAIN/Walter-echo
request. This bridge intentionally sends no CF_CHAIN_ACK: that would falsely
claim a Walter return. IHU may report request timeout; CAN receipt, RF decode
and Yamcs archive byte identity establish the one-way path independently.
Use a separate bounded `h`/IHU `hello` handshake first. No IHU firmware change,
EPS control, ground ACK, or unsolicited CAN-to-RF forwarding is implemented.

## v18: existing native telemetry over the transceiver

`f` now admits HEARTBEAT (38 bytes), SYSTEM_STATUS (46), POWER_STATUS (128),
and COMM_STATUS (50) from IHU, inside either CF_CHAIN or CF_SEND_PACKET.
The original native packet, source boot ID, sequence, uptime, validity flags,
and CRC remain unchanged. Unknown messages, commands/responses, transaction
fields, incorrect origin, length, token or either CRC are rejected. This does
not create new telemetry producers: COMM_STATUS requires an IHU producer.
Dictionary constants are generated into `native_wire.h`; the decoder test
checks that file against `ground/ember/dictionary.json`. Regenerate with:

```
python3 ground/ember/generate_c.py firmware/transceiver_bringup/native_wire.h
```

The largest admitted packet takes 1.273 seconds at 1200 baud, within the
unchanged 1.5-second payload deadline and independent 2-second mute timer.
Receiver windows are now four seconds with one-second stride, avoiding
truncation of longer packets at window boundaries. CAN remains unavailable
while this bench firmware transmits; this is still one explicitly armed packet.

For each transmission, using separate IHU and COMMS consoles:

1. On IHU, `normal`; on COMMS send `h` (single byte, no newline), then on IHU
   `hello`. Wait for `CAN_HELLO_CONFIRMED` and the COMMS receive window to end.
2. On the ground Pi, start a 15-second capture with a fresh output directory:
   `python3 /home/ngrabbs/work/ember-y24-bpsk/ground/bpsk/capture.py --seconds 15 --gain 0 --output /home/ngrabbs/work/ember-y24-bpsk/runs/UNIQUE_RUN --forward`
3. Wait for `BPSK_RX_READY`. On COMMS send `f` without a newline. After
   `[bridge] ARMED`, issue one IHU command: `eps telemetry` for EPS,
   `telemetry` for heartbeat, or `system lte` for system status. The existing
   `heartbeat lte` and `eps lte` commands also use the supported packet envelope;
   the historical command name does not select the RF hardware here.
4. Check `RF_complete=1`, `shutdown_verified=1`, a strict `dbpsk` decode, and
   the corresponding Yamcs packet after capture finishes.

No CF_CHAIN_ACK or CF_MODEM_ACCEPTED is generated by v18. The IHU therefore
reports a timeout and clears its peer (5 seconds for `telemetry` /
`eps telemetry`, 22 seconds for the `... lte` commands). Wait for IHU
`status` to show `pending=0`, then repeat the handshake before the next packet. This is a bench limitation, not a ground delivery status. A future
persistent service needs explicit RF admission/result semantics and queueing;
this change does not claim a Walter echo, LTE modem acceptance, or ground ACK.

## v19: acknowledged, bounded UHF batch

With IHU can-bench-v4, send COMMS `g` (one byte, no newline). It listens for10
seconds, accepts at most4 packets, drains them, and returns to muted standby.
A HELLO can be exchanged during collection, or use the existing `h` handshake
first. During collection issue IHU `uhf heartbeat`, `uhf system`, or `uhf eps`,
waiting for `UHF ... outcome=QUEUED` after each. Results subsequently report
`RF_TX_COMPLETE`, `RF_TX_FAILED`, or `CANCELLED`. These are local RF outcomes,
not acknowledgments from ground. IHU status retains the peer and reports
`pending=0 uhf_pending=0` after the final result, allowing the next batch without
another HELLO. Admission/result timeout means UNKNOWN and is never retried
silently. Any COMMS console byte stops the batch. No periodic service is started.

Use a fresh finite ground capture spanning the drain; for a three-packet batch,
start a15-second capture during the latter half of the collection window. The
receiver must report BPSK_RX_READY before draining begins. CAN is paused during
RF; submit all requests during collection. The existing `f` and old IHU commands
retain their prior behavior. See `system/interfaces/transceiver_uhf_bench.md`
for the wire contract, duplicate suppression and failure semantics.

## v20: timed autonomous packet service

Send `a` once to permit a maximum180-second LISTEN/TX service window (up to96
bursts). Unlike `g`, each valid queued packet is transmitted promptly and CAN
listening resumes for the next request. Any console byte stops the service;
boot never enables it. Existing per-burst timer, lock checks and mute remain.

With IHU v5, initialize normal CAN and HELLO, then use `uhf run 120 10` to send
heartbeat/system/EPS cycles every10 seconds for two minutes without per-packet
commands. Wait for receiver BPSK_RX_READY before starting the generator. IHU
`uhf stop` halts future production; COMMS `x` interrupts RF and closes the
permission window. IHU `status` reports mode, cycles and submitted count.
A135-second capture accommodates startup and the120-second run; forwarding
occurs after capture. See the UHF interface contract for bounds and faults.

COMMS v21 boots into CAN A normal mode after controller self-checks, with RF
muted. Discovery, HELLO and ECHO work without opening a console window. UHF
requests are explicitly rejected while RF service is disabled. `a`/`g` still
require explicit action and remain bounded; stopping returns to idle CAN
service. See the [device registry contract](../../system/interfaces/device_registry.md),
including the legacy LTE application-ID collision and future-node adoption.

## v22 / release 0.22.0: firmware identity

`VERSION` is the release version. Console `v` (or `s`) reports release, full
source Git SHA, dirty flag and boot ID. Exported builds must configure CMake
with `-DEMBER_GIT_REVISION=<40-character source commit>` and
`-DEMBER_GIT_DIRTY=0|1`; missing metadata fails configuration. Determine both
from the source checkout at export time, not the remote build directory.
Record the resulting UF2 SHA-256 separately; the Git SHA identifies source,
not an exact binary or toolchain. Dirty builds are explicitly marked and are
not reproducible from the commit alone. Release numbers must be updated with
changes intended as a new release; commit identity distinguishes builds.

Once per explicitly enabled `a`/`g` session, after its first admitted request,
COMMS sends its own COMMS_FIRMWARE telemetry before draining the IHU packet.
It contains version major/minor/patch, dirty flag and the full160-bit Git SHA
as five big-endian words. Its native source and boot ID are COMMS, not IHU.
The burst uses the existing timer/mute/abort checks and counts toward the96
attempt timed limit; a batch permits at most four data bursts plus one identity.
No queued data means no identity transmission; boot never enables RF. A failed
identity burst cancels the queued data rather than transmitting unchecked.

Yamcs exposes `/ember/COMMS_FIRMWARE_*` and the `Comms-Firmware.opi` display in
`ember-uhf__realtime`. This is the last received identity; it does not imply
that a later reset/reflash has already been observed. The dirty flag and Git
SHA are metadata, not secure boot or remote attestation.

Capture build identity automatically in the source checkout before exporting:

```bash
python3 firmware/transceiver_bringup/source_identity.py
```

The returned `cmake_args` are the arguments for the remote CMake configure.
`--cmake-args` prints them one per line. The helper marks tracked modifications
and non-ignored untracked files dirty; ignored build outputs do not count.
Capture immediately before copying source, with no intervening edits. Committing
or cleaning the checkout affects the next build, never an already flashed image.
Console version queries are for idle use; any console byte cancels active RF.

## 0.23.0 candidate: LTE identity observation forwarding

Adds IHU-sourced LTE_CAN_FIRMWARE/LTE_MODEM_FIRMWARE to the explicit UHF native
allowlist. CAN request/reply IDs and bounded RF behavior stay unchanged. The
installed0.22.0 demo image requires updating before these new packet types can
be forwarded. See the [CAN migration contract](../../system/interfaces/device_registry.md).

## Receive characterization (0.25.0)

`e` captures an ADC baseline with all Si5351 outputs disabled. `r` enables only
CLK1 at nominal 145 MHz (PLLA 870 MHz /6, 4 mA) for the RX tripler's 435 MHz LO.
Both are explicit, bounded 10-second tests; any console byte aborts. TX_ACTIVE
and BPSK_DATA remain low. RX_ACTIVE is only the indicator, not the antenna switch;
TX_ACTIVE low selects the RX antenna branch. CAN application service pauses during
these bench windows and returns through the existing main-loop reopen path.

After one second of settling, each test captures 4096 ADC1/GP27 samples at a
nominal 8 kS/s using software pacing. After verified shutdown, `[rx_adc]` reports
min/max/sum, elapsed microseconds, missed timing targets (>10 us), and 3 hexadecimal
digits per sample. Timing misses must be checked before using spectral results;
this is diagnostic acquisition, not a production demodulator. A failed or aborted
window does not emit a valid capture. Shutdown independently attempts output-disable
and power-down on CLK0/1/2, even after I2C failure. No receive packet is decoded or
executed, and no TX window is opened by these commands.

Host validation:

```sh
cc -std=c11 -Wall -Wextra -Werror -Wno-unused-function -I firmware/transceiver_bringup firmware/transceiver_bringup/tests/rx.c -o /tmp/ember-rx-test
/tmp/ember-rx-test
python3 firmware/transceiver_bringup/tests/check.py
```

The clock plan follows [Skyworks AN619 rev 0.8](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN619.pdf).
Register readback does not establish actual LO drive, frequency, or RF silence.
Use a low-level conducted source and document attenuation before injecting RF.

### Packet capture preparation (0.26.0)

Uppercase `R` keeps the same 10-second RX-only window but records 32768 ADC
samples (4.096 seconds) after the one-second settling interval. Lowercase `r`
and `e` retain the 4096-sample diagnostic capture. All data prints after shutdown.
The longer acquisition still pauses CAN service and does not parse or execute
received packets. Host tests cover both buffer lengths and the window deadline.

`ground/bpsk/adc_capture.py CONSOLE.txt` validates completion, shutdown, sample
count, timing and summary integrity, then constructs an analytic signal from the
real ADC capture and uses the strict existing DBPSK/CRC decoder offline. It has
no forwarding path. Native telemetry fixtures used for modem tests are synthetic
bench payloads, not spacecraft telemetry and not evidence of command handling.
Host simulation covers a real IF at 1.0/1.391/1.7 kHz with the nominal analog LPF,
quantization and noise, plus timing/capture-integrity failures and noise rejection.
Hardware packet reception has not yet been demonstrated.

### 0.27.1 captured onboard DBPSK diagnostic

`R` still acquires 32768 samples in the existing bounded RX window, then verifies
clock shutdown and dumps the raw capture. It now also attempts a fixed-memory
integer DBPSK decode after shutdown. Bad sample timing or ADC clipping rejects
the capture. Decoding tries the intended 1200 Hz IF first, then searches outward within
400–2600 Hz in 25 Hz increments and eight timing
hypotheses, stops at the first outer CRC32/native CRC16-valid telemetry frame,
and has a three-second deadline checked between frequency candidates. Any
console byte cancels decoding. CAN service resumes after this diagnostic.

The reported `mixer_hz` is the first successful search setting, **not a measured
carrier frequency**. Successful decode prints bytes only: `fixture_only=1
 dispatch=0`. Commands are rejected; no RF response, CAN forwarding or Yamcs
forwarding occurs. This remains a manually triggered capture diagnostic, not a
continuous command receiver. Three recorded hardware captures and synthetic
frequency/timing/noise/corruption tests run via
`python3 firmware/transceiver_bringup/tests/rx_decode_check.py`; hardware runtime
and a new live decode must be verified before calling the installed path proven.

### 0.28.0 PING-only ingress diagnostic

`R` also decodes command envelopes, then applies a separate PING-only gate.
Only a zero-payload native PING from ground to IHU, with nonzero transaction
epoch/ID and source boot ID, can produce `PING_ACCEPTED` on the console.
This preserves the existing ground→IHU command contract: acceptance means COMMS
validated ingress only. No IHU forwarding, execution, response or RF transmission
is enabled. Telemetry fixture decoding remains available.

The 16-entry transaction cache persists across diagnostic windows within a COMMS
boot. The same epoch/ID is `PING_DUPLICATE` even with a new RF/packet sequence;
a changed source boot ID under that key is a conflict. The cache does not evict:
a seventeenth new transaction is rejected until reboot. This is a bench duplicate
check, not authentication or persistent replay protection. Production uplink and
continuous listening remain out of scope.

The bounded transmitter adds named `ping`, `ping-wrong-target`, and `ping-bad-crc`
fixtures. Their fixed test transaction is epoch 0x52585031, ID 1; the latter two
are deliberate negative cases. All retain finite-burst and explicit GO behavior.
Tests: `tests/rx_ping.c` (host C with address/undefined-behavior sanitizers),
`tests/rx_decode_check.py`, startup/fault tests, and `ground/bpsk/test_uplink_probe.py`.

### 0.29.0 PING forwarding and held response

An accepted PING now makes one bounded CAN request on 0x730 after RX shutdown;
COMMS waits at most approximately two seconds for a correlated 0x731 response.
There is no automatic retry. The IHU independently gates PING, uses the native
command engine, and returns its actual COMPLETED response. COMMS validates
native CRC, response identity/stage, IHU boot consistency and transaction match.
It holds one validated 43-byte response for up to ten minutes. New accepted
requests invalidate the old response. An uncertain CAN outcome is not retried.

Uppercase `V` explicitly transmits that held response once through the existing
bounded BPSK transmitter. It consumes the held response before attempting RF.
Do not invoke V until the RF return cable/receiver setup has been verified.
Reception and CAN forwarding do not automatically enable RF transmission.

### 0.30.0 bounded automatic PING round trip

Uppercase `A` arms one local 20-second operation: acquire/decode one RX window,
forward one newly accepted PING to IHU, and transmit at most one fresh, validated
IHU completion. Old held responses are invalidated on entry. The authorization
is consumed once, is never boot-resumed, and requires at least three seconds
remaining before the existing two-second hard-mute transmitter can start.
Missing/duplicate/rejected packets, cancellation, expired lease and failed CAN
exchange cannot trigger a reply. `R` and `V` retain their separately staged modes.

The ground `roundtrip.py` sends one explicitly GO-triggered PING using TXRA,
then receives on RXA for 16 seconds after TX burst acknowledgment. It never
retries or forwards automatically. Each run must use a new transaction ID;
responses must match transaction and expected IHU boot ID. This remains a
manually initiated bounded trial, not continuous listening.
