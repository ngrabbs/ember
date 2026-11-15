# Payload firmware

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds)

Payload 0.7.1 is a Python service on the payload Pi. It answers the IHU over
CAN A and can capture three camera images, run spectral fire detection, and
save result and GPS evidence. The verified deployment reports
[`deeac88`](https://github.com/ngrabbs/ember/commit/deeac88c986bbe0f6697bf90183e1b407fe06b34).

## Install and run 0.7.1

Use a clean checkout of the payload source above to reproduce the deployed
source identity. The Pi needs Python 3, `iproute2`, and the LC2502 CAN A
overlay. On Raspberry Pi OS Trixie, check these lines under `[all]` in
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
test "$(cat firmware/payload/VERSION)" = 0.7.1
python3 firmware/payload/export.py /tmp/ember-payload-0.7.1-export
sed 's/^id ngrabbs /id pi /' /tmp/ember-payload-0.7.1-export/install.sh \
  > /tmp/ember-payload-0.7.1-export/install-pi.sh
unit=/tmp/ember-payload-0.7.1-export/systemd/ember-payload.service
sed 's/^User=ngrabbs$/User=pi/' "$unit" > "$unit.tmp" && mv "$unit.tmp" "$unit"
ssh pi@192.168.1.46 'test ! -e ~/ember-payload-0.7.1-export' &&
  scp -r /tmp/ember-payload-0.7.1-export pi@192.168.1.46:~/
ssh pi@192.168.1.46 'sudo sh ~/ember-payload-0.7.1-export/install-pi.sh'
)
```

The installer copies the runtime to `/opt/ember-payload`, enables and restarts
the CAN and responder services, and starts the responder. The CAN unit brings
up `can0` at 500 kbit/s. Check the running identity and CAN state on the Pi:

```sh
systemctl status ember-payload-can ember-payload --no-pager
journalctl -b -u ember-payload --grep=CAN_READY -n 1 --no-pager
cat /opt/ember-payload/build_identity.json
ip -details -statistics link show can0
```

`CAN_READY` reports the firmware version, source commit, and responder boot
ID. After a responder restart, establish a new HELLO session before issuing
direct CAN requests.

### Live camera fire checks

The base responder runs a static fire-check stub when no capture options are
configured. The live profile uses the Koenig camera daemon, NumPy and OpenCV
for the service's `/usr/bin/python3`, and the calibration file whose hash is
specified in the profile. Install the two supplied systemd drop-ins on a Pi
with the camera daemon already installed. Run these commands from the export
directory on the Pi:

```sh
sudo install -d /etc/ember-payload
if ! sudo test -f /etc/ember-payload/fire-check.json; then
  sudo install -m 644 config/fire-check.json /etc/ember-payload/fire-check.json
fi
sudo install -D -m 644 systemd/ember-payload.service.d/fire-check.conf \
  /etc/systemd/system/ember-payload.service.d/fire-check.conf
sudo install -D -m 644 systemd/payload-daemon.service.d/fire-check.conf \
  /etc/systemd/system/payload-daemon.service.d/fire-check.conf
sudo systemctl daemon-reload
sudo systemctl restart payload-daemon ember-payload
```

Before restarting, check the camera directory, evidence directory, calibration
file and hash in `/etc/ember-payload/fire-check.json`. The shipped drop-in gives
the responder read-only access to `/home/pi/payload_images` and writable state
under `/var/lib/ember-payload`. Match the bind path and service permissions to
any site-specific directory changes. On upgrades, preserve the installed JSON
and calibration. When migrating from the older split configuration, retire
the legacy `camera-capture.conf` and `detector.conf` drop-ins.

A fire check requests one triplet while the camera daemon is idle, with its
timer off and burst count set to one. The 10-second payload deadline includes
capture and analysis. The camera daemon keeps the original JPEGs. The
responder writes evidence JSON with image names, sizes, hashes, and results.

## Ground station commands in Yamcs

On the ground station, open **Commanding → Send a Command** in the
`realtime` processor. Choose the instance that matches the route.

| Yamcs instance | Route | Commands |
|---|---|---|
| `ember` | Ground radio → UHF → transceiver → IHU → CAN A → payload | `PAYLOAD_FIRE_CHECK` |
| `ember-bench` | Ground bridge → IHU USB → CAN A → payload | `PAYLOAD_PING` (1–240 bytes), `PAYLOAD_IDENT`, `PAYLOAD_STATUS_QUERY`, `PAYLOAD_HEARTBEAT_QUERY`, `PAYLOAD_FIRE_CHECK` |

Use **Command History** to check the correlated result. A timeout leaves the
outcome unknown. In a regular GROUND_TEST IHU console session, select
`hello payload` before using `payload ident`, `payload status`,
`payload heartbeat`, `payload fire-check`, or `ping N`.
The startup demo uses the Yamcs RF path for fire checks. See the
[IHU console guide](../ihu/README.md#usb-console).

## Fire detection algorithms

Both registered detectors compare the on-band image with a continuum
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
reports UNKNOWN. Select the algorithm with `detector_profile.algorithm` and
supply its settings in `detector_profile.detector`. See the
[detector registry](ember_detector/registry.py) and
[offline analysis guide](ember_detector/README.md#run-from-the-repository-root).

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
[Version 1] [Node 1] [Ready 1] [Reserved 1] [Payload boot 4] [Uptime ms 4] [Requests 4] [Replies 4] [Rejected 4] [Fragment errors 4]

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

The CAN envelope uses big-endian fields and CRC-16/CCITT-FALSE. Fire results
use decision values 0 for NO_FIRE, 1 for FIRE and 2 for UNKNOWN. An UNKNOWN
detector result uses report version 2. See the [CAN codec](protocol.py),
[Yamcs packet dictionary](../../ground/ember/dictionary.json), and
[radio framing guide](../../docs/comms/README.md).

Earlier release and bench notes are in the [changelog](CHANGELOG.md) and
[previous guide](https://github.com/ngrabbs/ember/blob/10cf329/firmware/payload/README.md).
