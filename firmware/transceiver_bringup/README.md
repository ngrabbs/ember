# Y24 transceiver bring-up

Original Pico only. This deliberately bounded image is separate from the legacy
`comms` application. It holds TX/RX inactive, both MCP25625 transceivers in standby,
and never enables a Si5351 clock output or sends a CAN frame. There are no commands.

Version 2 releases the CAN controller resets after a 10 ms hold, waits 10 ms,
then reads CANSTAT (0x0E) and CANCTRL (0x0F) through SPI0 at 100 kHz, mode 0.
Only READ instructions are issued. Both mode fields must indicate configuration
mode (0x80 masked with 0xE0); otherwise that controller is held in reset until
reboot. Standby stays high throughout. These read-only checks do not validate
CAN bus traffic, interrupts, or register writes. See Microchip DS20005282C.

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
