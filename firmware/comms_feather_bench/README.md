# COMMS CAN Feather UART bench

Standalone Pico SDK application for the Adafruit RP2040 CAN Bus Feather.
This is not the existing UHF/FreeRTOS COMMS firmware and does not replace its
board profile. It uses USB CDC for console/logs, UART0 GPIO0 TX / GPIO1 RX at
115200 8N1, and GPIO13 for the status LED. CAN, I2C, Si5351, and UHF control
pins are not initialized. The custom board header corrects the ordinary SDK
Feather SPI/NeoPixel mappings, without enabling those peripherals.

The UART connects Feather TX to Walter IO44/RX0 (pin 2), Feather RX to Walter
IO43/TX0 (pin 3), and common GND. The ESP32 firmware must provide the peer;
this is not a direct Sequans modem connection. See the
[carrier/interface plan](../../system/interfaces/comms_walter.md) for power entry,
USB power isolation, and reserved pins.

The current image is `uart-framed-v1`; it supersedes the initial text PING
image described in the historical evidence below. It includes the shared
[COBS/CRC UART bench service](../comms_transport/README.md).

USB commands, each terminated by newline: `status`, `help`, `hello`, `echo N`
(1–240 byte pattern), `packet HEX` (opaque bench packet), and `raw HEX` (bounded
fault injection). `hello` establishes Walter's boot identity before packets.
Only one request can be pending. Replies are checked for correlation and exact
payload; a timeout reports UNKNOWN and requires a fresh handshake. USB input is
bounded to 559 bytes, overlong/NUL-containing lines are discarded through their
delimiter, and UART reception uses the shared bounded COBS reader. No UART frames
are sent automatically at startup. The USB write timeout remains 20 ms; sustained
UART throughput/FIFO behavior is not qualified. No IHU or modem delivery is implied.

## Build

Requires Pico SDK and the ARM GCC toolchain. On m75q's existing container,
copy this directory and its sibling `comms_transport` to a separate work tree rather than overwriting its
repository. The tested source/build trees are:

```text
host:      ~/work/MSU_Cubesat/ember-comms-feather/src
container: /workspace/MSU_Cubesat/ember-comms-feather/src
shared:    /workspace/MSU_Cubesat/ember-comms-feather/comms_transport
build:     /workspace/MSU_Cubesat/ember-comms-feather/build
```

```sh
docker exec amsat-dev-x86 cmake \
  -S /workspace/MSU_Cubesat/ember-comms-feather/src \
  -B /workspace/MSU_Cubesat/ember-comms-feather/build \
  -DPICO_SDK_PATH=/opt/pico-sdk -DCMAKE_BUILD_TYPE=Release
docker exec amsat-dev-x86 cmake --build \
  /workspace/MSU_Cubesat/ember-comms-feather/build -j4
```

Result: `ember_comms_feather_bench.uf2`. The application compiles with
`-Wall -Wextra -Werror`. Tested SDK 2.1.1 and ARM GCC 14.2.1.

## Flash, console, and recovery

Select the actual bootloader device before writing; do not assume the recorded
bus/address still applies. A USB-enabled picotool was built separately from the
existing cached source, because the SDK build's picotool lacked USB support.
On m75q it is `~/work/ember-comms-feather/picotool-usb`, version 2.3.2-develop.
The build container added libusb development headers and pkg-config; existing
application source/SDK were not replaced.

```sh
sudo ~/work/ember-comms-feather/picotool-usb info -a
# In BOOTSEL, after selecting the intended board:
sudo ~/work/ember-comms-feather/picotool-usb load -v -x \
  ~/work/MSU_Cubesat/ember-comms-feather/build/ember_comms_feather_bench.uf2 \
  --bus USB_BUS --address USB_ADDRESS
```

Verified USB identity after flash:
`/dev/serial/by-id/usb-Raspberry_Pi_Pico_DF637882D39E4426-if00`.
The SDK's USB descriptor calls it Raspberry Pi Pico; the flash ID and application
status identify this particular Feather. Use USB at 115200 with pyserial or a
serial terminal and send `status\n`. Baud-triggered reset is disabled; physical
BOOTSEL remains available. Keep the Feather separately powered when moving
the USB cable to Walter for its firmware work, following the power-isolation plan.

Before flashing, picotool saved and verified all 8 MB of the original flash to
`~/work/ember-comms-feather/original-full-flash-20261002.uf2` on m75q. Its SHA-256:
`dd06d6a0b26f1816716259a3969ba7d8fc8de2dd334a1acc1c91a152743b5ce6`.
It contained `rt-ihu-testbed`, built 2026-09-18 for `adafruit_feather_rp2040`.
The root-owned full-flash backup and original metadata remain outside Git.
To restore, enter BOOTSEL and load that full-flash UF2 with verified device
selection and `-v -x`; this replaces the bench image and restores all saved flash.

## Hardware verification — 2026-10-02

Flash ID: `DF637882D39E4426`, 8192 KB. picotool load/readback verification
passed. UF2 SHA-256:
`1629ec848d9823f5e3ad10ca81d7c34aed976208a7333ac8137841f267400d7f`.

The USB check verified role/board/version, growing uptime, help, unknown command
rejection, and overlong-command rejection. Two requested probes increased
`tx_bytes` from 0 to 42 and `probes` from 0 to 2. `rx_bytes` remained at 1,
with no recognized peer acknowledgment. That byte does not prove correct wiring.
No Walter firmware was flashed and no modem/RF command was issued.

Private build/flash/USB evidence is under `~/work/ember-comms-feather/` on m75q.
After installing the [Walter responder](../walter_uart_bench/README.md), USB was
moved back to this Feather while Walter remained separately powered. Probes
3–12 each returned exactly `EMBER_UART_PONG v1 N\n` with the matching identifier:
10/10 successful diagnostic round trips. TX bytes increased 42 → 255 and RX bytes
95704 → 95917, exactly 213 bytes in each direction. The initial RX count includes
earlier unclassified bytes from before this run; it is not a clean-session count
or a reliability measurement. A subsequent five-second idle check left both
counts unchanged and produced no unsolicited USB logs.

Private evidence: `/media/ngrabbs/BACKUP-A/ember-walter-bridge/feather-roundtrip.log`,
`feather-roundtrip.json`, and `feather-idle.log` on m75q. The host decoded bounded
UART RX hex chunks and compared the complete reply bytes against each request.
This confirms both UART directions at 115200 8N1. Reset/framing behavior, telemetry
packet forwarding, IHU packet transport, and CAN operation remain untested.

The framed image build/flash and missing-peer timeout checks are recorded in
[the transport evidence](../comms_transport/README.md). The original full-flash
backup remains the recovery image; the text diagnostic round trip above is
historical evidence, not a result for the new binary envelope.
