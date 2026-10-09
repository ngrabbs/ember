# Heartbeat and system status over LTE

[Operator guides](README.md) · [EPS/LTE startup walkthrough](lte-eps-walkthrough.md)

This extends the native EPS path with two one-shot IHU packets. The Pi receiver
and `LTE.opi` display are deployed, and all three boards are flashed with verified
full-flash backups. On October 9 at 09:13 America/Chicago, heartbeat, system
status and EPS arrived through LTE and matched the original IHU bytes in the Pi
capture and Yamcs archive. [Verification record](../../system/ground_station/evidence/lte-health-20261009.json).

Three subsequent ground-cell restart trials also passed, with 27/27 exact
IHU/Pi/Yamcs packet matches and no observed registration losses or new CAN
errors. Time to ready was 16.5, 61.9 and 16.6 seconds.
[Repeatability record](../../system/ground_station/evidence/lte-repeatability-20261009.json).
This is bounded bench evidence; sustained operation and cold power-up remain
to qualify.
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

## Repeat a bounded nine-packet check

Keep the IHU USB console free. First verify both CAN controllers are in normal
mode and `hello` returns CAN_HELLO_CONFIRMED. The COMMS console also needs
`normal` after a board reset; move the single USB cable as necessary while
keeping board power connected.

Check LibreSDR is at 5000M on the Pi. Record its current CPU governor before
changing it. The validated runs temporarily used performance; restore the
recorded governor after the ground radio has stopped.

```sh
# PI SHELL: inspect USB speed and the original CPU setting.
lsusb -t
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# PI SHELL: temporarily select performance for this bounded radio test.
for gov_file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    printf 'performance\n' | sudo tee "$gov_file" >/dev/null
done

# PI SHELL A: start the finite ground cell; this explicitly starts RF.
# Choose a new label each run so private radio logs are not overwritten.
python3 ~/work/ember-lte/run-radio-check.py health-repeat-N \
  --seconds 150 --config enb.band13.emtc.ce300tx20diag.conf
```

Wait for `ALL eNBs ready` and `Starting steady-state operation`, then use
another terminal:

```sh
# M75Q SHELL: request a 120-second Walter window, wait for registration,
# and send three rounds of heartbeat + system status + EPS (nine packets).
# The helper saves original packet bytes and closes Walter's window on exit.
python3 ~/work/ember-lte/operator-tools/eps_lte_trial.py \
  --port /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 \
  --seconds 120 --count 3 --telemetry heartbeat system eps \
  --diagnostics --settle 15 \
  --output ~/work/ember-lte/logs/health-repeat-N
```

MODEM_ACCEPTED is only modem admission. Verify the nine original hex strings
in the Pi's `/var/lib/ember-lte-listener/packets.jsonl` and the `ember-lte`
Yamcs archive. Check the helper's final status is state=0/window_ms=0 and let
the finite ground-cell process exit before starting another run. Confirm
`pgrep -x lte-softmodem` and `pgrep -x srsepc` return no processes. If a send
fails or has an unknown outcome, inspect the saved evidence instead of
blindly repeating it.

```sh
# PI SHELL: restore the recorded governor after RF is stopped.
# This example restores ondemand, which was the setting on our tested Pi.
for gov_file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    printf 'ondemand\n' | sudo tee "$gov_file" >/dev/null
done
```
