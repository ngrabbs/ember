# Heartbeat and system status over LTE

[Operator guides](README.md) · [EPS/LTE startup walkthrough](lte-eps-walkthrough.md)

This extends the native EPS path with two one-shot IHU packets. The Pi receiver
and `LTE.opi` display are deployed, and all three boards are flashed with verified
full-flash backups. On October 9 at 09:13 America/Chicago, heartbeat, system
status and EPS arrived through LTE and matched the original IHU bytes in the Pi
capture and Yamcs archive. [Verification record](../../system/ground_station/evidence/lte-health-20261009.json).

This is one bounded three-packet success, not sustained-link qualification.
Earlier trials lost registration or failed to attach. LibreSDR must negotiate
USB 3 (`lsusb -t`: 5000M); USB 2 caused sample overflows. The successful test
used the original `enb.band13.emtc.ce300tx20diag.conf` profile and temporarily
set the Pi CPU governor to performance. Both boards must be in normal CAN mode:
a reset returns this bench firmware to configuration mode.
## What the packets mean

| IHU USB command | Native packet | Size | Contents |
|---|---|---|---|
| `heartbeat lte` | HEARTBEAT | 38 bytes | IHU boot ID, uptime, sequence, fixed bench labels and configured EPS cadence |
| `system lte` | SYSTEM_STATUS | 46 bytes | The same header, bench labels/cadence, admitted and refused CAN-request counters |
| `eps lte` | POWER_STATUS | 128 bytes | Existing fresh EPS readout; unchanged |

SAFE and GROUND_TEST identify this bench application. They do not prove a
flight safe-mode transition or absence of subsystem faults. No mode/configuration
command handler is introduced here. `telemetry_period_ms` is the configured
automatic EPS-over-CAN period (zero when disabled), not an automatic LTE send
interval. Heartbeat/status require explicit commands.

In this CAN bench image, `accepted_commands` counts successful **local CAN
request submissions**, including HELLO, link-status and packet-send requests.
`rejected_commands` counts refusals inside submission (busy, no peer, wrong
mode, exhausted ID or queue failure) and explicit matched peer refusals.
They do not count every console line or establish LTE reception. Unknown
outcomes/timeouts are not counted as refusals. Admitted requests can subsequently
be refused by the peer, so these are not mutually exclusive counters.
Counters reset on IHU reboot and are sampled before the current status send.

All three packets share the IHU telemetry sequence counter. Boot ID and uptime
come from the running MCU; no host-generated heartbeat or health values are
used for live acceptance testing. The ground allowlist still excludes command
responses, other sources and packets with nonzero transactions. EPS retains
its native-provenance checks.

## Send after the updated images are installed

Follow the startup walkthrough for the ground cell, normal CAN mode and IHU
HELLO. In a **Pi shell**, watch the already-running receiver:

```sh
# PI SHELL: watch actual arrivals and forwarding, not modem acceptance alone.
journalctl -fu ember-lte-listener
```

On the **IHU USB console**, start the bounded modem window:

```text
lte 120
```

Poll `lte status` until `state=6`, `registered=1` and enough time remains.
Send each command separately, waiting for its matched `RESULT` before the next:

```text
heartbeat lte
```

```text
system lte
```

Optionally check the EPS regression with `eps lte`. Each result should say
MODEM_ACCEPTED and include the original packet bytes; this is not a delivery ACK.
Leave the cell and Walter window active for at least 15 seconds after the last
acceptance and check arrivals before `lte 0`. Do not repeat UNKNOWN sends blindly.

Open the [LTE telemetry dashboard](http://192.168.1.251:8090/telemetry/displays/files/LTE.opi?c=ember-lte__realtime).
Its three panels show heartbeat, system status and EPS with separate reception
timestamps. The compact layout fits the three panels beside the Yamcs sidebar; View
→ Zoom out can reduce it further for narrow panels. Click a value for history; System raw/history lists the fields.
The existing common MDB already defines both new packet types, so no Yamcs
server restart is required to add their display or receiver routing.

## Firmware rollout

Both COMMS and Walter previously allowed heartbeat/EPS only. SYSTEM_STATUS
therefore requires all three new images, not just the IHU. The application wire
dictionary and CCSDS packet IDs are unchanged. The updated CAN image identifies
itself as `can-bench-v3`; `telemetry` retains the older non-LTE heartbeat echo.

Prepare backups of the installed images before flashing, identify each USB
device/board, and update with no active RF window. Re-establish normal CAN and
HELLO after reset. Keep the charger measurement/charging policy unchanged.
Acceptance requires native heartbeat/status/EPS packets received over LTE and
byte-for-byte comparison with the Yamcs archive; mocked/loopback tests alone
are not radio delivery evidence.
