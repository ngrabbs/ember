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
