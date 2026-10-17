# IHU CAN Feather console

[Operator guides](README.md) · [Mode/output matrix and entry gates](../architecture/operations/04-ihu-runtime-policy.md)

This guide describes the IHU 0.13.0 source candidate and bench bridge 0.4.0.
It does not claim those versions are flashed. Earlier 0.12.0 RF validation is
recorded in the [fire-check runbook](../../ground/yamcs/FIRE_CHECK.md).
The active controller source is `firmware/can_feather_bench`; the older
FreeRTOS `firmware/ihu` has a separate [UART guide](ihu-debug-uart.md).

## Connect and identify

The recorded IHU USB identity is `DF641455DB822427`. Verify role=IHU_MCU using
`version` or `status`. USB CDC carries both console and structured wired
messages;115200 is an acceptable terminal setting. No additional physical
UART pins are allocated by this release. The historically named
`ember_comms_can_bench` image is the LTE CAN Feather, not the original-Pico
COMMS transceiver. Identify the role/device before any update.

On m75q, `ember-bench-bridge` exclusively owns the IHU port. For manual work,
record whether it is active, stop it, and open the identified port with a
single serial client. Close that client before restarting the bridge.
Do not stop `ember-fire-arm` to access IHU: it owns the separate COMMS port.

```sh
systemctl is-active ember-bench-bridge
sudo systemctl stop ember-bench-bridge
# Open /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00
# Close the manual client when finished, then restore an initially active bridge:
sudo systemctl start ember-bench-bridge
```

Boot is quiet. Send complete case-sensitive lines terminated with CR or LF;
there is no prompt, terminal editing or command history. The line bound is39
characters; longer lines are discarded. Opening a console or issuing `status`
does not turn on any stream. Command replies still work when every stream is OFF.

## Mode and six switches

```text
mode
outputs
output cli_debug on
output cli_telem on
output umb_debug on
output umb_telem on
output uhf_telem on
output lte_telem on
```

Use the corresponding `off` command to disable each output. `output all on`
is not supported. Every boot and accepted mode change clears all six.

| Command | Effect |
|---|---|
| `version` / `status` | Build identity; status also includes actual configuration/mode, effective switches, CAN state and transport counters |
| `mode` | Read configuration, mode, simulated-state flag, stub status and entry reason |
| `mode safe` | Enter SAFE when transport is idle, clear switches and stop UHF producer |
| `mode startup` / `mode commissioning` / `mode nominal` | GROUND_TEST simulation only; clear switches, no automatic deployment or mission routine; FLIGHT rejects these exits |
| `outputs` | Read six effective flags |
| `output NAME on` / `output NAME off` | Set one named switch; RF OFF stops future telemetry submission/unsent fragments; already admitted remote packets may finish |
| `faults` | Read latest 16 volatile fault records; no persistent history claimed |
| `help` | Read available command spellings |

`cli_debug` and `umb_debug` enable tagged asynchronous diagnostic copies.
`cli_telem` enables a human-readable health summary; `umb_telem` enables
structured `ihu-health-v1` summaries and permits bridge EPS forwarding.
These are logical formats on the current USB connection. Summaries and
internal EPS reads run about every 5 seconds when transport is idle. Discovery
cycles one entry every 2 seconds. Polling can be deferred during application/RF
work. EPS validity and discovery presence are distinct forms of evidence.

## Explicit subsystem work

| Commands | Purpose |
|---|---|
| `devices` / `devices scan` | Read registry or request a background discovery visit |
| `normal` | Put CAN in normal mode and clear remembered peer; obtain HELLO again |
| `selftest` | Local CAN loopback only; it leaves loopback mode, so follow with `normal` and HELLO |
| `hello comms` / `hello lte` / `hello payload` | Select route and establish fresh peer identity; busy target switches are refused |
| `ping N` | Echo1–240 bytes through selected CAN peer |
| `eps json` | Explicit19-register PEC-checked read; full valid transport read or failure, never a partial JSON |
| `eps adc on` / `eps adc off` | Explicit CONFIG_BITS force-ADC override with readback; does not change charging policy |
| `payload ident` / `payload status` / `payload heartbeat` | Request payload diagnostics after `hello payload` |
| `payload fire-check` | Request a fire result; payload 0.2.0 returns NO_FIRE/STATIC_STUB |
| `lte firmware` / `lte modem firmware` / `lte status` / `lte diagnostics` | Query selected LTE route; no RF window is started by these queries |
| `lte N` | Explicit Walter RF window,0 stops, maximum120 seconds; does not itself send telemetry |

Wait for a correlated terminal RESULT before issuing another application
command. Quiet output does not hide a solicited asynchronous result. A timeout
remains UNKNOWN and is never interpreted as NO_FIRE or success. Native RF
fire-check replies remain available with periodic UHF telemetry OFF, through
the separately bounded receive/reply session. No automatic operation retry.

## Explicit RF telemetry

Enabling a switch grants permission; it does not acquire a radio or start RF.
Prepare the matching COMMS/Walter and ground receiver sessions separately.
Do not let a live receiver and RF command service concurrently own LibreSDR.

| Commands | Required permission and route |
|---|---|
| `uhf heartbeat` / `uhf system` / `uhf eps` / `uhf devices` | uhf_telem ON, normal CAN, COMMS HELLO and idle transport |
| `uhf lte firmware` / `uhf modem firmware` | Same UHF gates, plus an identity previously queried from LTE and still fresh |
| `uhf run SECONDS PERIOD` | Same UHF gates; duration1–120s, period5–60s; sequential heartbeat/system/EPS/device cycles |
| `uhf stop` | Stop future cycles; previously admitted packets may finish |
| `heartbeat lte` / `system lte` / `eps lte` | lte_telem ON, LTE HELLO, matching modem firmware and explicit RF window/readiness |

## Removed controls

The old `telemetry`, `eps telemetry`, `telem on/off/status`, `eps enqueue` and
`lte queue ...` commands are removed from IHU 0.13.0. There is no hidden EPS-only
timer or queued LTE sender. Historical test artifacts do not enable those paths.
Do not apply these instructions to the older FreeRTOS CLI or LTE Feather role.

## Bench forwarding

Bridge0.4.0 with `--poll-eps` checks IHU `outputs` before each periodic EPS
request. With umb_telem OFF, unknown, or unavailable it emits no periodic EPS
packet; cached Yamcs values expire. To see bench EPS telemetry deliberately
select `output umb_telem on` using the sole console owner, then restore the
bridge. The setting survives bridge reconnects, but not IHU reset or mode change.
Explicit PAYLOAD_* command/result transactions do not require streaming flags.
