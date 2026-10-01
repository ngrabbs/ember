# Ground lab inventory

[Ground station checklist](TODO.md) · [Pi preparation](pi_setup.md)

Recorded 2026-10-01. The dedicated ground host is **Raspberry Pi 5 Model B
Rev 1.0, 8 GB RAM**. m75q remains the Pico build host and interim simulator
reference; these are independent Git checkouts and separate Yamcs archives.

| Item | Ground Pi |
|---|---|
| Hostname | `ember-ground` |
| Ethernet | `192.168.1.251/24` |
| Gateway and DNS | `192.168.1.1` |
| SSH user | `ngrabbs` |
| SSH authentication | Existing Ed25519 public key shared by Mac and m75q; key-only login |
| Administrative access | Passwordless sudo rule for `ngrabbs`, verified after boot |
| OS | Raspberry Pi OS Lite, Debian 13 Trixie, ARM64 |
| Image | `2026-09-15-raspios-trixie-arm64-lite.img.xz` |
| Image SHA-256 | `cdf4f3bfac35ae947b46e4e767f935453810549779ac3290e05a6754aee627e5` |
| Storage | 128 GB SD, expanded root approximately 117 GiB |
| Repository | `/home/ngrabbs/work/MSU_Cubesat/ember` |
| Ground software branch | PR #5 merged at `a21832b`; next work is `feature/ground-station-usb` |
| Browser address | `http://192.168.1.251:8090` |
| Time zone | America/Chicago |

The compressed image passed its integrity/hash checks and the raw write passed
a complete byte comparison before personalization. The USB reader disconnected
during the first comparison; a retry succeeded. Headless personalization uses
the image's `userconf` service plus NetworkManager Ethernet configuration. The
initial missing sudo rule was repaired offline and sudo access now works.

Initial powered-idle check: 29.6°C, `get_throttled=0x0`. This is a spot check,
not a modem load/power/cooling qualification. The power supply/cooling hardware
and SDR/Pico connections still need recording. Wi-Fi is not configured.

Docker Engine/Compose come from the official Debian ARM64 repository. The upstream Yamcs starter remains a software reference. The EMBER USB
override now connects to the Pico through a host bridge; no radio is attached
and no USB device is mounted into Docker.

## USB endpoint — 2026-10-01

RP2040 Raspberry Pi Pico B2, flash2048KiB, ID `E663682593753535`.
BOOTSEL USB2e8a:0003; application USB2e8a:000a / Raspberry Pi Pico.
Stable CDC path: `/dev/serial/by-id/usb-Raspberry_Pi_Pico_E663682593753535-if00`.
Pi USB-A to micro-USB data cable supplies power/data; no RF attached.

Original application: `rp2040-si5351-sig-gen`, SDK2.1.1, Release Aug25 2026.
Saved complete flash before replacement:

- Pi: `/home/ngrabbs/pico-before-ember-usb-20261001.uf2`.
- Mac: `/Users/nick/Documents/ChatGPT/EMBER/pico-before-ember-usb-20261001.uf2`.
- Backup SHA256: `7898bf27766f280ca01ec12ea9c0d7068404718d961aff311bdfb93501532dd4`.

Installed dedicated EMBER USB bench-v1. Final UF2 SHA256:
`92d60d31b589e46ddd4401887328b7b231b8c567287d93e11a668ac97c39b4d4`.
Artifact copies: `/home/ngrabbs/ember_usb_bench.uf2` on Pi and
`/Users/nick/Documents/ChatGPT/EMBER/ember_usb_bench.uf2` on Mac; source/build
on m75q under `firmware/usb_bench`. Pi packages: picotool2.1.1+dfsg-1 and
python3-serial3.5-2. The host bridge runs as ngrabbs/dialout; Docker receives
packets over UDP without USB device passthrough. See [USB validation](usb_validation.md).
