# Pico USB bench endpoint

[Packet contract](../../system/protocols/ember_bench_v1.md) · [Hardware setup](../../system/ground_station/usb_bench_setup.md)

Standalone Pico SDK application for one RP2040 Pico acting as the bench IHU.
It implements PING, status/telemetry queries, telemetry-period changes,
correlated outcomes and last-64 transaction caching. This endpoint stays in
SAFE / GROUND_TEST, uses no radio drivers and is separate from the FreeRTOS
IHU/comms applications. Settings/cache are nonpersistent; each reboot generates
a new nonzero random boot ID and restores the 1000 ms default.

On m75q, from the repository root:

```sh
sh tools/build_usb_bench.sh
```

The script builds in the existing `amsat-dev-x86` container with Pico SDK 2.1.1,
Release, `PICO_BOARD=pico`. Output is `build/ember_usb_bench.uf2` and `.elf`.
It does not flash hardware. CMake generates `build/generated/wire.h` from
`ground/ember/dictionary.json`; rerun configuration after dictionary edits.
Build environment versions and the picotool pinning limitation are recorded in
[development baseline](../../system/integration/development_baseline.md).

USB CDC carries binary COBS-framed CCSDS packets only. Raw SDK driver access
avoids stdio newline translation. No USB debug prints or USB-baud reset are
allowed on this stream. The SDK vendor reset remains available to picotool.
UART0 GP0 TX / GP1 RX at 115200 8N1 emits a boot banner; UART input does not
execute commands. An optional debug adapter needs 3.3 V logic and common GND.

The parser bounds encoded frames to 241 bytes, decoded packets to 240 bytes,
and expires partial frames after 500 ms. Oversize/timeout discards through the
next zero delimiter. Payload lengths, identity and CRC are checked before
argument validation/dispatch. The state/cache uses fixed storage. USB output
uses the SDK writer with a 20 ms timeout; the TX counter means handed to that
writer, not delivered to the ground. There is no automatic command replay.

Host checks compile the actual C core/framer using a host C compiler:

```sh
python3 -m unittest discover -s tests/ground -v
```

On-device checks and flash-backup instructions are in the hardware setup.
