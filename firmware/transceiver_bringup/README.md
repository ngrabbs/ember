# Y24 transceiver bring-up

Original Pico only. This deliberately bounded image is separate from the legacy
`comms` application. It holds TX/RX inactive, both MCP25625 transceivers in standby,
and never enables a Si5351 clock output or sends a frame onto the external CAN bus. Console commands are single bytes: `l` and `n` (see below).

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

Every second it writes Si5351 register 3 = 0xFF and checks the readback, using
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
All three transmit requests are cleared before normal-mode entry. This image
never requests application-frame transmission on the external bus; normal mode
can produce CAN acknowledgments/error signaling. CAN B stays in standby.
Burst SPI reads and RX0-to-RX1 rollover reduce capture overhead.
Each window returns A to standby and configuration mode; failed transitions
hold it in reset. The first 32 received buffers are saved in RAM and printed after capture, with a total
frame count and final EFLG. Listen-only reception can include invalid traffic;
its error counters are not a bus-quality metric. This polling test is not a
high-load capture tool. RF control outputs remain inactive throughout.

The startup sequencing issue observed in the stack is still open. Boot checks
run once and fail closed; they do not automatically retry when rails arrive later.
