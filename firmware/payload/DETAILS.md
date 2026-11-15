# Payload deployment and protocol

[Payload guide](README.md)

## Bench installation

To reproduce the recorded bench build, use a clean checkout of
[`deeac88`](https://github.com/ngrabbs/ember/commit/deeac88c986bbe0f6697bf90183e1b407fe06b34).
The Pi needs Python 3, `iproute2`, and the LC2502 CAN A overlay. On Raspberry Pi OS Trixie, check these lines under `[all]` in
`/boot/firmware/config.txt` before booting:

```ini
dtparam=spi=on
dtoverlay=spi0-1cs
dtoverlay=mcp2515,spi0-0,oscillator=16000000,interrupt=25
```

Use a fresh export directory on both hosts. These commands target the bench
Pi at `pi@192.168.1.46`. The 0.7.1 installer and base unit default to
`ngrabbs`, so adjust the two account references in the exported copy for
this Pi before installing.

```sh
(
set -e
test "$(git rev-parse HEAD)" = deeac88c986bbe0f6697bf90183e1b407fe06b34
test -z "$(git status --porcelain)"
test "$(cat firmware/payload/VERSION)" = 0.7.1
python3 firmware/payload/export.py /tmp/ember-payload-0.7.1-export
sed 's/^id ngrabbs /id pi /' /tmp/ember-payload-0.7.1-export/install.sh \
  > /tmp/ember-payload-0.7.1-export/install-pi.sh
unit=/tmp/ember-payload-0.7.1-export/systemd/ember-payload.service
sed 's/^User=ngrabbs$/User=pi/' "$unit" > "$unit.tmp" && mv "$unit.tmp" "$unit"
ssh pi@192.168.1.46 'test ! -e ~/ember-payload-0.7.1-export'
scp -r /tmp/ember-payload-0.7.1-export pi@192.168.1.46:~/
ssh pi@192.168.1.46 'sudo sh ~/ember-payload-0.7.1-export/install-pi.sh'
)
```

The installer copies the runtime to `/opt/ember-payload`, enables and restarts
the CAN and responder services, and starts the responder. Check both service units on the Pi and compare the
installed build identity with the startup log in the [payload guide](README.md#build-and-install).

```sh
systemctl status ember-payload-can ember-payload --no-pager
cat /opt/ember-payload/build_identity.json
```

### Live camera fire checks

Install the two systemd drop-ins on a Pi with the Koenig camera daemon
and NumPy and OpenCV available to `/usr/bin/python3`. Run these commands
from the export directory on the Pi.

```sh
sudo install -d /etc/ember-payload
if ! sudo test -f /etc/ember-payload/fire-check.json; then
  sudo install -m 644 config/fire-check.json /etc/ember-payload/fire-check.json
fi
sudo install -D -m 644 systemd/ember-payload.service.d/fire-check.conf \
  /etc/systemd/system/ember-payload.service.d/fire-check.conf
sudo install -D -m 644 systemd/payload-daemon.service.d/fire-check.conf \
  /etc/systemd/system/payload-daemon.service.d/fire-check.conf
```

Verify the camera and evidence paths and the calibration file and hash in
`/etc/ember-payload/fire-check.json`. The shipped drop-in gives the responder
read-only access to `/home/pi/payload_images` and writable state
under `/var/lib/ember-payload`. Match the bind path and service permissions to
any site-specific directory changes. On upgrades, preserve the installed JSON
and calibration. When migrating from the older split configuration, retire
the legacy `camera-capture.conf` and `detector.conf` drop-ins.

```sh
sudo systemctl daemon-reload
sudo systemctl restart payload-daemon ember-payload
```

A fire check requests one triplet while the camera daemon is idle, with its
timer off and burst count set to one. The 10-second payload deadline includes
capture and analysis. The camera daemon keeps the original JPEGs. The
responder writes evidence JSON with image names, sizes, hashes, and results.

## Fire detection algorithms

The two EGSE detectors compare the on-band image with a continuum
interpolated from the two reference bands. Calibration, registration and
validity masking happen before either detector runs.

| Algorithm | Behavior |
|---|---|
| `spectral_excess_v1` | Measures absolute and fractional on-band excess, then checks the size of connected candidate regions. |
| `spectral_guarded_v1` | Uses the local maximum in each reference band before interpolating. This suppresses false candidates along slightly misaligned edges at the cost of sensitivity to small or weak sources. |

The live bench profile uses `spectral_guarded_v1` with normalized ORB
homography registration. Registration uses contrast-normalized copies to
match features. The detector measures intensities from the original
decoded images after calibration. A failed registration quality gate
reports UNKNOWN. Set `detector_profile` in `fire-check.json` to a built-in
name or an edited profile object, then restart the camera daemon and
payload responder. RAW profiles require the optional Python dependencies and
a DNG from each camera. See the [offline detector guide](ember_detector/README.md#select-and-tune-development-profiles).

## Packet layouts

Lengths are in bytes and fields read left to right. The payload is CAN node 4.
Discovery uses `0x700 → 0x704` and application requests use `0x740 → 0x741`.
HELLO establishes the requester session. Replies retain the request ID and
origin boot ID and add the responder's boot ID.

```text
Classic CAN data field
[Version/flags 1] [Token 2] [Index 1] [COBS envelope slice 1–4]

Reassembled envelope, after removing the zero terminator and decoding COBS
[Magic 2] [Version 1] [Type 1] [Sender boot 4] [Origin boot 4] [Request ID 4] [Len 2] [Payload N] [CRC-16 2]

CAN fire-check request payload
[Optional GPS tag 18]

CAN fire-check result payload
[Report version 1] [Decision 1] [Mode 1] [Analysis error 1] [Payload boot 4] [Uptime ms 4] [Check ID 4] [Optional GPS tag 18]

GPS tag
[Status 1] [Satellites 1] [Latitude E7 4] [Longitude E7 4] [MSL altitude mm 4] [Age ms 4]

CAN identity reply payload
[Major 1] [Minor 1] [Patch 1] [Dirty 1] [Git SHA 20] [Payload boot 4] [Uptime ms 4]

CAN status / heartbeat reply payload
[Version 1] [Node 1] [Ready 1] [Detector profile ID 1] [Payload boot 4] [Uptime ms 4] [Requests 4] [Replies 4] [Rejected 4] [Fragment errors 4]

Native EMBER packet sent to Yamcs
[CCSDS primary header 6] [EMBER secondary header 24] [Telemetry payload N] [CRC-16 2]

Yamcs PAYLOAD_FIRE_TAGGED telemetry payload
[Version 1] [Transport 1] [Decision 1] [Mode 1] [Bridge session 4] [Payload boot 4] [Uptime ms 4] [Check ID 4] [GPS tag 18] [Analysis error 1]
```

| CAN service | Request → reply | Reply payload |
|---|---|---|
| HELLO | `0x01 → 0x02` | Empty |
| ECHO | `0x70 → 0x71` | 1–240 bytes echoed |
| Identity | `0x18 → 0x19` | 32 bytes |
| Status | `0x94 → 0x95` | 28 bytes |
| Heartbeat | `0x96 → 0x97` | 28 bytes |
| Fire check | `0x98 → 0x99` | 16 bytes, or 34 with GPS |
| Error | `0x7F` reply | 1 reason byte |

Status and heartbeat queries report the selected family and input format as
`PAYLOAD_STATUS.detector_profile_id`. Zero means unreported. Updated IHU and
USB bridge builds append this field to ground telemetry. Regenerate the wire
headers, Yamcs database, and displays when deploying the update. The fire
result's `execution_mode` describes how the result was produced. The
evidence configuration hash distinguishes tuning within a profile family.

The CAN envelope uses big-endian fields and CRC-16/CCITT-FALSE. Fire results
use decision values 0 for NO_FIRE, 1 for FIRE and 2 for UNKNOWN. An UNKNOWN
detector result uses report version 2. See the [CAN codec](protocol.py),
[Yamcs packet dictionary](../../ground/ember/dictionary.json), and
[radio framing guide](../../docs/comms/README.md).
