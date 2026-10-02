# Walter COMMS UART bench responder

Standalone ESP32-S3 diagnostic paired with
[the COMMS CAN Feather diagnostic](../comms_feather_bench/README.md).
UART0 receives on Walter IO44/RX0 (physical pin 2) and transmits on IO43/TX0
(pin 3), at 115200 8N1. Feather GPIO0 TX connects to Walter RX, Feather GPIO1 RX
to Walter TX, with common GND. See the
[interface/power plan](../../system/interfaces/comms_walter.md).

The application holds the Sequans modem's active-low GPIO45 reset low. It does
not initialize the modem UART, send AT commands, or enable cellular/GNSS.
Native USB hardware CDC carries console logs independently of UART0. ESP32
ROM boot output can still appear on UART0 during reset; this diagnostic is not
the future binary framing protocol.

USB commands: `status` and `help`, terminated by newline. Unknown commands and
overlong lines are rejected. UART accepts `EMBER_UART_PING v1 N\n`, with N a
one-to-ten-digit decimal identifier, and replies `EMBER_UART_PONG v1 N\n`.
It sends nothing automatically. Lines use bounded 80-byte buffers; invalid
UART lines increment the error counter. Status reports RX/TX bytes, ping/error
counts, uptime, and the application's modem reset state. Counters wrap at 32 bits.

This proves neither packet forwarding nor LTE delivery. It has no IHU link,
CAN service, queues, application CRC, or reconnect logic. Sustained UART traffic,
FIFO overruns, and USB logging backpressure are not qualified.

## Build and install

Pinned PlatformIO 6.1.18 and Espressif32 platform 6.10.0 were used on m75q.
The resolved Arduino framework is `3.20017.241212+sha.dcc1105b` (Arduino 2.0.17),
with Xtensa GCC `8.4.0+2021r2-patch5`. Application source builds with
`-Wall -Wextra -Werror`. The generic ESP32-S3 DevKit board profile is overridden
to 16 MB flash, DIO, and native USB; the default partition table uses only the
initial portion of flash. This diagnostic does not use PSRAM or WalterModem.

On m75q, source is copied to a separate project beneath the external disk:

```sh
TASK_BASE=/media/ngrabbs/BACKUP-A/ember-walter-bridge
export PLATFORMIO_CORE_DIR="$TASK_BASE/pio"
export TMPDIR="$TASK_BASE/tmp"
"$TASK_BASE/venv/bin/pio" run -d "$TASK_BASE/project"
# Select the intended board before uploading:
"$TASK_BASE/venv/bin/pio" run -d "$TASK_BASE/project" -t upload \
  --upload-port /dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:58:7C:6F:0C:24-if00
```

Tool dependencies and temporary downloads live on that disk, avoiding m75q's
small root filesystem. Use `PLATFORMIO_CORE_DIR`, not `PIO_CORE_DIR`.
PlatformIO writes the generated bootloader, partitions, boot selector, and
application at their generated offsets; no whole-chip erase is necessary.
The upload tool verifies hashes of written regions.

## Original firmware recovery

Before replacing the unknown-provenance AT passthrough, its modem reported
`CFUN 0` at 2026-10-02 17:05:21 UTC. Native esptool 4.8.1 saved all 16,777,216
ESP32 flash bytes and `verify_flash` matched the on-device digest. This saves
ESP32 firmware/NVS/filesystem, not a separate Sequans modem firmware image.
Keep the private backup outside Git because it may contain provisioning data.

M75q backup: `/media/ngrabbs/BACKUP-A/ember-walter-bridge/original-flash-20261002.bin`.
SHA-256: `b53079b03812a6e0ba92f7f8c681a9e4274d866d8c5f224e712722c1ef07cf89`.

Recovery, only when deliberately returning to the original application:

```sh
TASK_BASE=/media/ngrabbs/BACKUP-A/ember-walter-bridge
"$TASK_BASE/venv/bin/esptool.py" --chip esp32s3 \
  --port /dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:58:7C:6F:0C:24-if00 \
  --baud 460800 write_flash --flash_mode keep --flash_freq keep --flash_size keep \
  0 "$TASK_BASE/original-flash-20261002.bin"
```

Restoring the old application restores its modem startup/reset behavior. Check
its radio state before resuming tests. Full-image restoration has not been
exercised; the saved image was verified before writing the new application.

## Bench evidence — 2026-10-02

Walter: ESP32-S3 revision 0.2, MAC `24:58:7c:6f:0c:24`, 16 MB flash,
embedded 2 MB PSRAM. Build passed; upload hashes verified.
Application binary SHA-256:
`629b566ea1c01b4c1ce86239a4d510163743391fc1383a9e81ff07f137aba51a`.

USB status/help, unknown-command rejection, overlong-command rejection, and
growing uptime passed. Both sampled statuses reported zero RX/TX bytes, pings,
and errors, with `modem=HELD_RESET`. Opening USB reset this ESP32 application
(first sampled uptime 401 ms); initialization reapplies modem reset. The state
report describes firmware intent, not an independent electrical measurement.

Build, package, original backup verification, flash, and USB logs are private
under the m75q task directory above. After moving USB back to the powered Feather
and keeping Walter separately powered, ten probes (identifiers 3–12) returned
ten exact `EMBER_UART_PONG v1 N\n` replies. The host decoded Feather UART RX hex
chunks and compared complete reply bytes to each expected identifier. Both
directions carried 213 bytes, with no additional RX bytes during a subsequent
five-second idle check. Logs: `feather-roundtrip.log`, `feather-roundtrip.json`,
and `feather-idle.log`. This verifies the physical UART diagnostic, not the
planned framed packet service or LTE telemetry. Reset and fault tests remain open.

To repeat, follow the USB/VIN power-isolation plan, connect USB to Feather, send
`probe`, and decode its UART RX hex log. A matching PONG identifier proves the
diagnostic round trip; UART submission alone does not.

Modem reset polarity was checked against the pinned
[QuickSpot passthrough source](https://github.com/QuickSpot/walter-arduino/blob/c30b707f8d64b49daec80de6bccfc80c04e42d58/examples/passthrough/passthrough.ino).
Physical header mapping is from the
[Walter datasheet](https://www.quickspot.io/datasheet/walter_datasheet.pdf).
