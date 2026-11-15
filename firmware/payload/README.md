# Payload firmware

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds)

The payload runs on the Raspberry Pi 4 and answers the IHU on CAN A. The live
profile captures three narrowband images, checks for fire, and saves the result
with available GPS evidence. The last verified bench build is **0.7.1** at
[`deeac88`](https://github.com/ngrabbs/ember/commit/deeac88c986bbe0f6697bf90183e1b407fe06b34).

## Build and install

From a clean checkout of the source you intend to deploy, export the Python
runtime and its build identity to a new directory.

```sh
python3 firmware/payload/export.py /tmp/ember-payload-export
```

Install the export on a Pi with Python 3, `iproute2`, and the LC2502 CAN overlay.
The installer and systemd unit must use the Pi's service account. For the CAN
overlay, bench transfer, account setup, and camera drop-ins, see the
[deployment instructions](DETAILS.md#bench-installation).

On the Pi, check the running identity and CAN state.

```sh
journalctl -b -u ember-payload --grep=CAN_READY -n 1 --no-pager
ip -details -statistics link show can0
```

## Profiles at a glance

| Profile | Fire-check behavior |
|---|---|
| Base responder | Returns a static `NO_FIRE` test result. |
| Live cameras | Requests one triplet and analyzes it within 10 seconds. A failed registration quality check returns `UNKNOWN`. |

The live profile requires the Koenig camera daemon, calibration, NumPy, and
OpenCV. See the [live setup](DETAILS.md#live-camera-fire-checks) and
[detector details](DETAILS.md#fire-detection-algorithms).

## Startup and modes

Systemd initializes `can0` at 500 kbit/s, then starts the responder. The
`CAN_READY` log includes the version, source commit, and boot ID. The IHU
establishes a HELLO session before sending requests and renews it after a
responder restart.

## Commands

| Yamcs instance | Route | Payload commands |
|---|---|---|
| `ember` | UHF through the transceiver and IHU | `PAYLOAD_FIRE_CHECK` |
| `ember-bench` | IHU USB bridge in regular GROUND_TEST | `PAYLOAD_FIRE_CHECK`, `PAYLOAD_IDENT`, `PAYLOAD_PING`, `PAYLOAD_STATUS_QUERY`, `PAYLOAD_HEARTBEAT_QUERY` |

In the regular GROUND_TEST USB console, send `hello payload` before
`payload ident`, `payload status`, `payload heartbeat`, `payload fire-check`,
or `ping N`. The UHF startup profile accepts fire checks through Yamcs over
UHF. See the [IHU console guide](../ihu/README.md#usb-console).

Check Command History and the reported execution mode. Use the check ID to
correlate GPS telemetry when available. See the
[Yamcs command dictionary](../../docs/architecture/operations/yamcs-commands.md).

## Packet layouts

Payload is CAN node 4. Discovery uses `0x700 → 0x704`. Requests use `0x740`
and replies use `0x741`. The IHU carries results to Yamcs in EMBER telemetry.
See the [CAN and telemetry layouts](DETAILS.md#packet-layouts).
