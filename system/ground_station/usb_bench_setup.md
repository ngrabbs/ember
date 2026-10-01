# First USB hardware loop

[Ground checklist](TODO.md) · [Bench packet contract](../protocols/ember_bench_v1.md)

PR #5 is merged into `main` at `a21832b`. The next iteration is
`feature/ground-station-usb`: replace the Python spacecraft simulator with a
single RP2040 Pico endpoint while preserving the Yamcs dictionary and CCSDS
packet bytes. USB bench firmware and the bridge are still to implement.

## Connect now

1. Use one spare **RP2040 Raspberry Pi Pico**, or Pico W with its model recorded
   before building. This is the simulated spacecraft/IHU endpoint for this test.
2. Connect a **USB-A to micro-USB data cable** from any Pi 5 USB-A port to the
   Pico's micro-USB socket. USB supplies both power and data. Leave the Pi on
   its existing power supply and Ethernet connection.
3. Keep this first endpoint as a standalone Pico; no RF module, SDR, second
   Pico, or GPIO interconnect is needed to prove the wired command loop.
4. To verify the cable/bootloader, hold **BOOTSEL while connecting** the Pico.
   It should appear as the `RPI-RP2` USB storage device. Release BOOTSEL after
   connection. Entering this mode alone does not replace the installed firmware.
   The [official Pico getting-started guide](https://datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf)
   describes the USB/UF2 bootloader workflow.

The Pi is the USB host; m75q remains the firmware build machine. We can transfer
the resulting UF2 to the Pi for installation. A USB serial port is expected
only after firmware providing CDC is loaded; the current IHU build intentionally
disables CDC in `firmware/ihu/src/CMakeLists.txt` and uses UART stdio.

## Optional debug connection

A USB-to-UART adapter with **3.3 V logic** can connect to another Pi USB port.
This is a separate debug stream, not the binary packet transport:

| Pico | Adapter |
|---|---|
| GP0 / pin 1, UART TX | RX |
| GP1 / pin 2, UART RX (optional input) | TX |
| GND / pin 3 | GND |

Use only the signal/ground wires; Pico power comes from its micro-USB connection.
The existing UART console uses 115200 8N1. A debug adapter is optional for the
first test and can be added if needed during firmware bring-up.

## Work remaining before packets flow

- Add a dedicated Pico SDK USB bench application, with bounded stream framing,
  CCSDS length/CRC validation, command handlers, transaction cache and telemetry
  scheduling. Keep debug text off the binary USB packet stream.
- Implement the Pi serial/UDP bridge and identify the device by its stable
  USB identity rather than assuming `/dev/ttyACM0` permanently names it.
- Explicitly switch the EMBER instance from its isolated simulator to the bridge;
  retain the simulator as a reproducible reference configuration.
- Repeat PING, requested status/telemetry, telemetry-period change, invalid
  argument, duplicate/conflict, timeout and endpoint-reset tests against hardware.
- Record the Pico model, USB identity, firmware commit/build and test results.

The two-Pico SX1280 transport and SDR/UHF BPSK tests follow this wired milestone.
