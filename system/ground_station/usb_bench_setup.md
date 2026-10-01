# First USB hardware loop

[Ground checklist](TODO.md) · [Bench packet contract](../protocols/ember_bench_v1.md) · [Validation](usb_validation.md)

The Pi now runs Yamcs → host USB/UDP bridge → standalone RP2040 Pico → Yamcs.
The dedicated endpoint replaces the EMBER simulator; `myproject` remains the
upstream reference. Packet bytes/dictionary are unchanged across the transport.

## Current hookup

- Pi 5, Ethernet `192.168.1.251`, browser `http://192.168.1.251:8090`.
- One RP2040 Raspberry Pi Pico, revision B2, 2 MiB flash.
- USB-A to micro-USB **data cable**, Pi USB host to Pico. USB powers the Pico.
- Stable identity: `/dev/serial/by-id/usb-Raspberry_Pi_Pico_E663682593753535-if00`.
  Do not assume its current `ttyACM0` name will persist.

The Pi retains its own supply. No SDR, radio module, second Pico or GPIO
interconnect is required for this milestone. The next transport uses two
Pico/SX1280 endpoints; record the known-working radio wiring before changing it.

## Build and flash

m75q remains the build machine. From its repository, run
`sh tools/build_usb_bench.sh`. Transfer
`firmware/usb_bench/build/ember_usb_bench.uf2` to the Pi, verifying its hash.
For the deployed endpoint, stop the bridge before flashing/probing:

```sh
sudo systemctl stop ember-usb-bridge
sudo picotool reboot -u -f
# Wait for BOOTSEL re-enumeration before loading.
sudo picotool load -v /home/ngrabbs/ember_usb_bench.uf2
sudo picotool reboot
```

For another Pico, hold BOOTSEL while plugging in the data cable. Identify it
with `sudo picotool info -a` and save its existing flash **before** loading a
replacement (`sudo picotool save -a /home/ngrabbs/pico-before-ember-usb.uf2`).
Do not overwrite the existing backup. The original signal-generator firmware
on this Pico is preserved on Pi and Mac; paths/hashes are in the inventory.
Existing IHU firmware disables CDC and is not the USB bench application.

## Probe and run

After application re-enumeration, from the repository root:

```sh
python3 ground/ember/usb_probe.py --device /dev/serial/by-id/usb-Raspberry_Pi_Pico_E663682593753535-if00 --reset-test
sudo systemctl start ember-usb-bridge
python3 ground/yamcs/ember_smoke.py --url http://192.168.1.251:8090 --transport usb --fault-test
```

Direct probe requires the bridge stopped and checks the sole attached Pico.
`--reset-test` invokes `sudo -n picotool reboot -f`. It verifies a new boot ID,
cleared cache/counters and the default period. The Yamcs smoke checks both
periods through archived heartbeat uptimes and restores the original setting.
The local fault injection suppresses returned results, giving an UNKNOWN
timeout even though the command can have executed. Never automatically retry
an uncertain command; inspect state first.

[The Yamcs README](../../ground/yamcs/README.md#pi-usb-transport) documents `.env`,
`.usb.env`, service installation and software-reference fallback. The bridge
service is enabled and reconnects only the configured identity after USB
re-enumeration. Stop both bridge and starter to stop the whole lab.

## Optional UART debug

Use a USB/UART adapter with 3.3 V logic: Pico GP0 / pin1 TX → adapter RX,
GP1 / pin2 RX → adapter TX (optional), GND / pin3 → GND. Connect signal/ground
only; Pico power comes from micro-USB. UART0 is 115200 8N1 and emits a boot
banner. Debug output stays off the binary USB stream. No UART command console
is implemented by this dedicated endpoint.
