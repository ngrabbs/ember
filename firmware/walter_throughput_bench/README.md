# Temporary Walter throughput benchmark

The bounded bench series closed on October 19 local / October 20 UTC. Three
separate 512-byte, 2 packet/s, 30-second points delivered 180/180 within their
receiver windows (8.192 kbps each). Walter's original 0.3.0 image is restored and
the USB and final read-only IHU→COMMS→Walter identity/OFF checks passed.
This project is retained for reproduction, not installed production code.
See [closeout](../../ground/lte/results/2026-10-20-direct-pacing-closeout.md).

Built, host-tested and installed on 2026-10-19. Startup/OFF checks passed;
First 128-byte / 1 packet/s direct delivery check passed (10/10, 1.024 kbps).
The 512-byte / 1 packet/s check also passed (10/10, 4.096 kbps).
The 2 packet/s attempt lost registration (3 accepted, 0 received); 5 packet/s was
not attempted. Higher-rate testing is paused; 1024-byte packets remain unqualified.
This is a separate ESP32-S3 image. The production IHU, Walter MCU and Walter
application sources remain unchanged. Reliability debugging is paused.

## What it measures

USB → Walter ESP32 → modem UART/AT → LTE-M → a separate ground UDP receiver.
This removes IHU/CAN pacing. It still includes a **115200-baud, 8N1 UART** and one
AT send transaction at a time: the raw UART payload ceiling is 92.16 kbps before
AT overhead. Results are application goodput, not maximum LTE-M PHY throughput.

The modem is held in reset at boot. Only USB `on` opens an RF window, at most
120 seconds; another `on` cannot extend it. Deadline and UART writes are
nonblocking. A disconnected/full USB log queue cannot delay the RF deadline.
COMMS UART is not initialized and cannot enable this image's modem.

Pins match production: modem RX14/TX48, CTS47/RTS21; GPIO45 active-low reset.
Band13 and APN `srsapn` match the existing lab configuration. Operator selection
and RAT are not changed. `AT+COPS?`, `AT+CGMR`, registration and signal responses
are exposed in private USB logs; the initial sequence disables AT echo with
`ATE0`. This reads the modem's actual status rather than inferring it from the
ESP32 application identity. No SIM keys or IMSI queries are implemented.

UDP destination `172.16.0.1:51002`, local port51003. These ports are separate from
production telemetry/Yamcs51000/51001. Nothing is installed as a ground service.

## USB commands

Every response is one JSON object per line. Keep reading throughout the test.

| Command | Action |
| --- | --- |
| `version` | Temporary image identity, exact source digest, UART baud and USB log-drop count |
| `status` | Identity plus state, CEREG, remaining RF window and counters |
| `on 120` | Explicit bounded window, modem boot/configuration/registration/socket setup |
| `query operator` | Read current `AT+COPS?` response when READY and idle |
| `query firmware` | Read actual modem `AT+CGMR` response |
| `query signal` | Read `AT+CSQ` |
| `query registration` | Read `AT+CEREG?` |
| `query pdp` | Read `AT+CGACT?` |
| `run 12345 128 1 10` | Run ID12345,128-byte packets,1 offered packet/s,10 seconds |
| `off` | Assert modem reset, terminate any run, classify pending submission UNKNOWN |

Wait for `ready` before `run`. Choose a fresh nonzero u32 run ID. Packet sizes
128/512/1024, integer offered rates1–100 packet/s and durations1–30 seconds are
bounded; **start with128 bytes**. The 512-byte low-rate point has now passed; 1024-byte
payloads still need hardware qualification. Admission requires duration plus16 seconds of RF-window headroom.
A modem error, AT timeout, registration loss or deadline stops the run and RF.
No rejected or unknown packet is retried.

Sequence numbers are planned sending slots. Slots missed because the modem is
busy are counted as **skipped**, not packet loss. Future slots after an abort
are **unreached**. `accepted` requires the send prompt, the exact payload and
final modem OK; reception is checked separately. Logs with dropped events are
not acceptable measurement evidence.

## Separate ground receiver

Start before enabling Walter; use the same run ID as the sender:

```sh
python3 ground/lte/scripts/direct-bench-receiver.py --run 12345 --seconds 180 > receiver.jsonl
```

The receiver validates `ELTB` version1, the32-byte network-order header, total
length, CRC32 and deterministic body pattern before recording metadata. Header:
magic4,version1,flags1,header-size2,run4,slot4,sender-ms4,total-size2,reserved2,
CRC32-4,boot4. CRC covers the whole datagram with its own field zeroed. This is
synthetic benchmark data, not an EMBER telemetry packet.

Record USB JSON lines separately, including `status` after `run_done` to check
`log_drops=0`. Let the receiver cover the full window and drain. Then:

```sh
python3 ground/lte/scripts/direct-bench-summary.py sender.jsonl receiver.jsonl --run 12345
```

Goodput counts the entire UDP payload, including the32-byte benchmark header.
The receive window has the requested duration and begins at the first valid
arrival. Report unique bytes ×8 /duration, skipped slots, accepted-but-missing,
unknown outcomes, duplicates and late arrivals separately. Missing/short receiver
captures or incomplete sender outcomes do not produce a valid rate. No one-way
latency is inferred from device and ground clocks.

## Build and host checks

Use PlatformIO6.1.18, espressif32@6.10.0 / Arduino2.0.17. Set the checkout's
40-character `EMBER_GIT_REVISION`. `identity.py` also hashes this project's
actual sources/configuration and the shared CEREG parser, including uncommitted
changes, so the temporary binary is identifiable without a production release.

```sh
EMBER_GIT_REVISION=$(git rev-parse HEAD) pio run -d firmware/walter_throughput_bench
clang++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  firmware/walter_throughput_bench/tests/engine_test.cpp -o /tmp/ember-bench-engine-test
/tmp/ember-bench-engine-test
python3 firmware/walter_throughput_bench/tests/test_receiver.py
```

Tests exercise the actual engine under blocked UART, deadlines/millis wrap,
registration loss, prompt/payload/final-OK ordering, rejection/unknown handling
and pacing skips. The C++ packet vector is independently checked by Python;
a real local UDP test checks corruption and duplicates. These are not RF tests.

## Hardware preparation and restoration

Leave USB on the IHU until the image, receiver and backup tooling are ready.
Then move it to Walter, leaving the stack boards separately powered.

Before any flash write:

1. Identify Walter's USB device and query its current `version`, `status`, `off`.
   Require the expected Walter application role; never target a Feather port.
2. With pinned esptool4.5.1, explicitly select `--chip esp32s3`, read chip/MAC,
   security information and detected flash size. Confirm the actual16 MiB flash
   and that its protection state permits this backup/restore procedure.
3. Create **two complete16 MiB restore images**, leaving the loader without an
   intervening application boot. Require identical SHA-256 hashes and sizes.
   A raw full-flash read works; for a slow USB connection, read programmed64 KiB
   regions and reconstruct erased regions only after the loader confirms their
   MD5 equals all-FF bytes. Verify every region and the whole-image MD5 against
   the device before and after each snapshot. This uses esptool4.5.1 read/checksum
   operations only. Save chip identity, original USB identity, region checksums,
   hashes and exact tool/build versions. Copy the verified backup off the M75q
   before writing.
4. Use the prepared application's pinned PlatformIO upload only after that gate.
   Reconnect and verify temporary role/source digest, modem OFF and zero window.
   Build/preparation requests no RF window; verify OFF after the upload.

Raw full-read alternative, after resolving the real Walter port and esptool path:

```sh
python3 "$ESPTOOL" --chip esp32s3 --port "$WALTER_PORT" --baud 460800 --after no_reset read_mac
python3 "$ESPTOOL" --chip esp32s3 --port "$WALTER_PORT" --baud 460800 --after no_reset flash_id
python3 "$ESPTOOL" --chip esp32s3 --port "$WALTER_PORT" --baud 460800 --after no_reset get_security_info
python3 "$ESPTOOL" --chip esp32s3 --port "$WALTER_PORT" --baud 460800 --after no_reset read_flash 0 0x1000000 original-a.bin
python3 "$ESPTOOL" --chip esp32s3 --port "$WALTER_PORT" --baud 460800 --after no_reset read_flash 0 0x1000000 original-b.bin
```

Backups contain private flash/NVS data: keep them outside Git with private
permissions. Do not erase the device as a preparation step. To restore, first
verify the backup hash and target chip identity, then write the complete original
image at offset0 with flash parameters kept, verify it against flash, reboot,
and confirm the original Walter identity and OFF state through USB and then IHU.
Restoring ESP32 flash does not restore external modem NVM; this benchmark uses
the existing band/APN and does not program RAT/operator selection or modem firmware.

No production firmware version increment or PR is part of this temporary test.
