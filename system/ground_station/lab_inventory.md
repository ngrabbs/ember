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

Docker Engine/Compose come from the official Debian ARM64 repository. The
Yamcs starter is a software simulator; no radio/device access is mounted.
