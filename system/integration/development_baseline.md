# Development baseline across macOS and m75q

Recorded 2026-10-01. These are distinct Git checkouts, not synchronized copies.
PRs #2–#5 are merged; macOS, m75q and Pi share baseline `a21832b`.
The active hardware USB branch is `feature/ground-station-usb`.

| Role | Location |
|---|---|
| macOS CAD and documentation | `/Users/nick/Desktop/ember` |
| Pi ground repository | `ngrabbs@192.168.1.251:~/work/MSU_Cubesat/ember` |
| m75q host repository | `ngrabbs@192.168.1.252:~/work/MSU_Cubesat/ember` |
| macOS remote-mount view of m75q | `/Volumes/work/MSU_Cubesat/ember` |
| Repository in `amsat-dev-x86` (`amsat-dev:x86`) | `/workspace/MSU_Cubesat/ember` |
| SDK in the container | `/opt/pico-sdk` (host: `/home/ngrabbs/tools/pico-sdk`) |

Use SSH to run builds and Git operations on m75q. Accessing its files through
the mounted volume does not run commands in the Linux build environment;
the mount also reports executable modes differently from the host checkout.
Use Git branches and PRs to exchange changes, not directory mirroring.

## Reconciliation

- GitHub `main` at `fdbf638` already contains the newer all-UHF comms design.
  Preserve that CAD as the shared baseline.
- Mac comms checkpoint `b3f4a0d` preserves its complete saved project. Three
  files still differ from current `main`: `Digital_Control.kicad_sch`,
  `transceiver.kicad_pcb`, and `transceiver.kicad_pro`. Keep the checkpoint
  branch available and review those differences natively before adopting them;
  replacing the current board wholesale would also remove newer settings.
- m75q's firmware diagnostics and payload carrier conversion were committed
  separately. Its branch incorporates current `main` and retains the working
  Pico application, IHU housekeeping client, bus serialization, and shared schema
  that were absent from current `main`. I2C between the two Picos is a bench
  harness; the flight transport still needs implementation.
- PR #3 merged the firmware/payload baseline; PR #4 merged the ground-station
  plan, environment documentation and conflict-marker repairs.
- PR #2 merged the command/telemetry Draft 0.2. Adopt its application meanings
  and coordinate the [remaining definitions](../ground_station/dustin_followup.md)
  before freezing packet IDs or field layouts.

The firmware retains legacy clock-generator bring-up settings, including a
145.9 MHz RX-LO value. These are not an approved UHF receiver configuration.
Specify the actual UHF RF/LO/IF frequency plan before enabling the flight modem;
an internal LO frequency should not be confused with the uplink RF frequency.

## Reproducible build

From macOS:

```sh
ssh ngrabbs@192.168.1.252 \
  'cd ~/work/MSU_Cubesat/ember && sh tools/build_pico_baseline.sh'
```

Or run `sh tools/build_pico_baseline.sh` from the repository on m75q.
The script configures and builds both `comms` and `ihu` in separate ignored
`build-baseline` trees using the existing container, then runs host-side
Si5351 driver regression checks. It does not flash hardware. UF2/ELF outputs
are under `firmware/<target>/build-baseline/src/`.

Override `EMBER_BUILD_CONTAINER`, `EMBER_CONTAINER_WORKSPACE`,
`EMBER_PICO_SDK_PATH`, or `EMBER_BUILD_JOBS` if the container layout changes.
The SDK currently used is 2.1.1; clean configuration may fetch/build picotool.
The existing container runs builds as root, so its build outputs may be
root-owned on the host. No container images or SDK installation were changed.

## Validation and remaining gates

- Fresh Release builds of both Pico applications pass in `amsat-dev-x86`.
- Si5351 mock-I2C tests cover immediate readiness, readiness on the final poll,
  a stuck initialization flag, absent device, and read-only status decoding.
- Fault-clear console reporting is restricted to a previously reported fault;
  healthy status changes must not produce a false recovery message.
- Legacy IHU/comms hardware behavior and RF reception remain unverified.
  The separate USB bench endpoint passes command dispatch on hardware; see
  [USB validation](../ground_station/usb_validation.md).
- The payload carrier is a preserved conversion checkpoint, not an ERC/DRC,
  mechanical, or fabrication acceptance. The older root TODO has other historical
  subsystem status notes that require checking before reuse.

All three hosts share the merged baseline. Ground software work uses
`feature/ground-station-usb`. Never discard local edits to make a pull succeed.

m75q fetches GitHub over HTTPS to avoid its current SSH host-key failure.
Its configured push URL remains SSH; pushes for this reconciliation are made
from macOS. Repair and verify m75q's GitHub SSH trust/authentication before
expecting direct pushes from that host.

## Dedicated USB bench build

On m75q, run `sh tools/build_usb_bench.sh`; output is
`firmware/usb_bench/build/ember_usb_bench.uf2`. This builds a standalone Pico SDK
endpoint and does not change or flash the FreeRTOS IHU/comms applications.
The SDK is 2.1.1 (`ee68c78d0afae2b69c03ae1a72bf5cc267a2d94c`); GCC ARM is
14.2.1. SDK picotool discovery fetched develop revision
`ba3df406c37774144a059b2bdae73ab52587a1d2` (2.3.2-develop). That cached
build tool revision is recorded, but a clean SDK build can fetch newer develop;
fully pinning the build tool remains a reproducibility improvement. Pi flash
installation uses Debian picotool 2.1.1+dfsg-1.
