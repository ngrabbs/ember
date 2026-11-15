# Pi payload CAN A responder

[Changelog](CHANGELOG.md) · [Current bench builds](../README.md#current-bench-builds)

Version 0.7.1 runs as a Python service on the payload Pi. On CAN A at
500 kbit/s it responds to addressed IHU requests for identity, status, and fire
checks. The deployed live camera configuration captures a triplet, runs the
spectral detector, and attaches GPS evidence to the fire-check result when
available. See [live fire-check configuration](#live-fire-check-configuration-060).

## Addressing

| Purpose | Standard 11-bit CAN ID |
|---|---|
| Existing discovery query, target node 4 | `0x700` |
| Existing payload discovery reply | `0x704` |
| New IHU-to-payload application route | `0x740` |
| New payload-to-IHU application route | `0x741` |

transceiver `0x710/0x711`, LTE `0x720/0x721`, and deployed RF uplink
`0x730/0x731` remain unchanged. Payload uses `0x740/0x741` specifically
to avoid the RF uplink allocation, which is newer than main. The candidate
preserves the installed IHU uplink implementation from `08b36205d8e324ae31fb3ea5c2cdc3b32c38ce62`. Source of truth:
[`device_registry.h`](../comms_transport/device_registry.h) and
[`can_fragment.h`](../comms_transport/can_fragment.h). These development IDs
are correlation mechanisms, not authentication or flight addressing.

## Wire contract

`protocol.py` interoperates with the C COBS/CRC-16/CCITT-FALSE envelope and
four-byte CAN fragmentation. Multibyte fields are big endian. Every reply
retains requester boot/request IDs and carries the payload's nonzero daemon
boot/session ID. Fragment token equals request ID's low16 bits. Reassembly
is bounded to263 bytes with a500 ms interfragment timeout. Wrong routes,
EFF/RTR/error frames, CRC errors, duplicate starts, out-of-order fragments and
oversize transfers are discarded. Discovery does not establish an app session.

| Service | Request / final reply | Data |
|---|---|---|
| HELLO | `0x01 / 0x02` | Empty; establishes requester session |
| Ping/ECHO | `0x70 / 0x71` | 1–240 bytes echoed unchanged |
| Identification | `0x18 / 0x19` | Empty request; existing32-byte identity |
| Status | `0x94 / 0x95` | Empty request;28-byte report |
| Heartbeat | `0x96 / 0x97` | Empty request; fresh28-byte liveness report |
| Fire check | `0x98 / 0x99` | Empty request;16-byte result |
| Rejection | `0x7F` | Reason: version1, type2, session3, payload4 |

Identity: version major/minor/patch (3 bytes), dirty (1), full source SHA (20),
daemon boot ID (4), daemon uptime milliseconds (4). Status/heartbeat:
version=1, node=4, ready=1, reserved=0 (one byte each), then six uint32 fields:
daemon boot ID, daemon uptime_ms, requests handled, replies queued before
this report, rejected requests, fragment errors plus timeouts. Counters wrap.
Ready means this responder is running, not camera or external device health.
SocketCAN link statistics remain separate (`ip -s -d link show can0`).

These immediate read-only services return a final response directly. Separate
admission/completion replies belong to future long operations. Silence means
UNKNOWN, never success; there is no automatic application retry. Only the
current HELLO requester session may query; a new HELLO replaces it. No
cryptographic authentication is claimed.

## Installation and startup

The Pi boot configuration must already include in `[all]`:

```ini
dtparam=spi=on
dtoverlay=spi0-1cs
dtoverlay=mcp2515,spi0-0,oscillator=16000000,interrupt=25
```

Leave CAN B/SPI1 and conflicting UART D overlays disabled. The installer does
not rewrite boot settings. Python3 and iproute2 are the runtime dependencies;
can-utils is useful for diagnosis. The service account is `ngrabbs`.

```sh
python3 firmware/payload/export.py /tmp/payload-export
scp -r /tmp/payload-export ngrabbs@192.168.1.253:~/payload-export
ssh ngrabbs@192.168.1.253 'sudo sh ~/payload-export/install.sh'
```

Export destination must be new. Export records the source checkout SHA and
dirty flag, not the Pi's Git state. Runtime goes to `/opt/ember-payload`; no
secrets or Wi-Fi credentials are exported. Read installed identity from
`/opt/ember-payload/build_identity.json`.

`ember-payload-can.service` retries the known boot-time SPI probe failure at
most20 times, then sets `can0` normal/500kbit/s, loopback off. Exhaustion fails
startup visibly. It changes no other interface and does not auto-restart
bus-off. Inspect wiring before deliberately restarting this unit. Linux's
mcp251x driver here lacks one-shot support: hardware retransmission is
distinct from an application retry.

`ember-payload.service` starts after CAN readiness and runs without root. It
uses a single-owner lock and bounded reply queue. systemd bounds repeated
restarts. Each daemon restart changes its boot ID, requiring another HELLO.
Wi-Fi is not part of either service's startup ordering.

```sh
systemctl status ember-payload-can ember-payload
journalctl -u ember-payload-can -u ember-payload -b
ip -details -statistics link show can0
```

## IHU console

```text
devices
hello payload
ping 32
payload ident
payload status
payload heartbeat
hello transceiver
```

Wait for each correlated RESULT before the next command. Background discovery
can make target selection BUSY; retry after it finishes. Validated replies
refresh registry liveness. Payload identity does not overwrite LTE/Walter
identity caches. UHF/LTE operations are rejected on the payload route.
Target switches are blocked during a running UHF session.

Existing IHU images already discover node4; the application commands require
v0.11.0. A bench client can independently test the responder with
`python3 firmware/payload/client.py --interface can0 status`. Its HELLO replaces
the IHU session, so reselect `hello payload` afterward.

## Validation

Run `python3 -m unittest discover -s tests/ground`. Payload tests compare Python
packets/fragments against the real C codec and check CRC, sequence and timeout
recovery, discovery correlation and session gating. Actual IHU handler tests
cover route isolation, report validation and preservation of LTE identity.
Hardware evidence and remaining deployment limits are in `validation.json`.

## Fire check 0.2.0

Version 0.4.0 can run the existing replaceable detector on real captures. Enable
`EMBER_PAYLOAD_DETECTOR_CONFIG` as described in the [user guide](../../docs/user/payload.md#real-capture-and-detection-version-040).
Valid binary decisions return ALGORITHM mode; UNKNOWN returns ERROR 11 and a
persistent evidence record, so unusable images never become a false NO_FIRE.

Version 0.3.0 adds an opt-in real-camera capture before this static detector
result. Set `EMBER_PAYLOAD_CAPTURE_URL=http://127.0.0.1:8001` and permit AF_INET
in the systemd service. See the [user guide](../../docs/user/payload.md#real-capture-before-the-fire-check-reply)
for setup, logging, deadlines and failure handling. Capture uses a worker so
CAN discovery and heartbeat remain responsive. With the adapter enabled, a
successful reply confirms that all three image files have been saved; the
NO_FIRE/STATIC_STUB fields still describe a stub detector.

IHU0.12.0 `hello payload` then `payload fire-check` commands one check. The
payload returns version1, result0=NO_FIRE/1=FIRE, mode1=STATIC_STUB/2=ALGORITHM,
reserved0, boot32, uptime_ms32, check_id32 (all integers big endian).
Version 0.2.0 always returns NO_FIRE/STATIC_STUB and increments check_id.
No camera or detector is invoked in that version. An absent, corrupt or uncorrelated reply is
UNKNOWN, never NO_FIRE. Session HELLO, envelope CRC and request correlation apply.
The future detector replaces the explicit stub and reports ALGORITHM.

Yamcs PAYLOAD_FIRE_CHECK is available in both instances. Bench uses serial/CAN;
flight uses the real finite RF path documented in ground/yamcs/FIRE_CHECK.md.

Fire-check deployment and the two byte-matched Yamcs RF results are recorded in
[`validation.json`](../../system/ground_station/evidence/fire-check-20261017/validation.json).

## Live fire-check configuration (0.6.0)

On a Pi with the Koenig camera daemon, install the supplied optional systemd
drop-ins for both `ember-payload.service` and `payload-daemon.service`. Install
`config/fire-check.json` as `/etc/ember-payload/fire-check.json` on first setup.
Preserve the installed JSON on upgrades. Retire the old `camera-capture.conf`
and `detector.conf` settings when enabling this profile. Restart both services
after editing the JSON so both processes use the same configuration.

This file selects the camera directory, evidence directory, camera request
budget, total fire-check deadline, worker startup timeout, calibration, and
detector profile. The profile selects a registered algorithm and holds its
thresholds and registration settings. The default 10-second total budget
includes capture and detection and leaves room for the IHU's 12-second
CAN reply window. Camera settings used for each exposure are read from the
camera daemon and recorded with the result.

The daemon owns the original JPEGs. The detector reads them in place and
undoes camera rotation in memory. The evidence directory stores JSON only,
including the image names, sizes, and hashes for inputs the worker read.
Keep the originals if the run must be reproducible. Choose an evidence
directory under the service's writable state directory or explicitly grant
write access when changing that root. The responder needs read access to
the camera image directory. The drop-in exposes the default camera directory
read-only. Update that sandbox permission when moving the camera store outside
the allowed directory.

A future uplink could stage a validated profile and activate it by version
or hash, using algorithms already installed on the payload. Adding a new
algorithm would require a separate software update.
