# IHU CAN Feather console

[Operator guides](README.md) · [Transmission matrix](#transmission-matrix) · [Mode/output matrix and entry gates](../architecture/operations/04-ihu-runtime-policy.md)

This guide describes IHU **0.14.0**, COMMS **0.33.0**, and bench bridge **0.4.0**.
The earlier IHU 0.13.0 [deployment record](../../system/ground_station/evidence/ihu-0.13.0-20261017/deployment.json)
is retained separately. Earlier 0.12.0 RF validation is
recorded in the [fire-check runbook](../../ground/yamcs/FIRE_CHECK.md).
The active controller source is `firmware/ihu`. The retired FreeRTOS UART
application is available through Git history.

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

With COMMS 0.33.0, a healthy board accepts IHU UHF requests immediately over
CAN. No COMMS USB console enable or `a`/`g` window is needed. Enabling
`uhf_telem` permits sends; issue `uhf heartbeat` for one packet or
`uhf run 60 10` for a bounded run. Each admitted request transmits through the
existing finite RF bursts and returns to idle CAN, with RF muted.
The ground receiver must be running to observe packets. LTE still requires
an explicit Walter RF window.
Do not let a live receiver and RF command service concurrently own LibreSDR.

| Commands | Required permission and route |
|---|---|
| `uhf heartbeat` / `uhf system` / `uhf eps` / `uhf devices` | uhf_telem ON, normal CAN, COMMS HELLO and idle transport |
| `uhf comms firmware` | Same UHF gates; request one fresh COMMS-owned firmware packet, no cached LTE identity needed |
| `uhf lte firmware` / `uhf modem firmware` | Same UHF gates, plus an identity previously queried from LTE and still fresh |
| `uhf run SECONDS PERIOD` | Same UHF gates; duration1–120s, period5–60s; sequential heartbeat/system/EPS/device cycles |
| `uhf stop` | Stop future cycles; previously admitted packets may finish |
| `heartbeat lte` / `system lte` / `eps lte` | lte_telem ON, LTE HELLO, matching modem firmware and explicit RF window/readiness |

## Transmission matrix

Checked against IHU **0.14.0**, COMMS **0.33.0** (default on-demand service),
serial bench bridge **0.4.0**, and payload **0.2.0**. These are the implemented
operational packet paths, not every message defined by the dictionary.

**Yes** means included on a successful operation; **Selected** means only when
its matching command is issued; **—** means not emitted by that path.
Timeouts, rejected commands and invalid replies do not imply a successful result.

| Packet | UHF run | UHF single send | LTE single send | RF fire check | Bench EPS polling | Bench payload command |
|---|---|---|---|---|---|---|
| `HEARTBEAT` | Yes | Selected | Selected | — | — | — |
| `SYSTEM_STATUS` | Yes | Selected | Selected | — | — | — |
| `POWER_STATUS` | Yes | Selected | Selected | — | Yes | — |
| `DEVICE_STATUS` | Yes | Selected | — | — | — | — |
| `COMMS_FIRMWARE` | First telemetry request after COMMS boot only | First after boot, or explicit `uhf comms firmware` | — | — | — | — |
| `LTE_CAN_FIRMWARE` | — | Selected | — | — | — | — |
| `LTE_MODEM_FIRMWARE` | — | Selected | — | — | — | — |
| `PAYLOAD_FIRMWARE` | — | — | — | — | — | Selected |
| `PAYLOAD_STATUS` | — | — | — | — | — | Selected |
| `PAYLOAD_PING_RESULT` | — | — | — | — | — | Selected |
| `PAYLOAD_FIRE_RESULT` | — | — | — | Yes | — | Selected |
| `COMMAND_RESPONSE` | — | — | — | — | — | Command stages |
| `COMM_STATUS` | — | — | — | — | — | — |

UHF single sends are `uhf heartbeat`, `uhf system`, `uhf eps`, `uhf devices`, and
`uhf comms firmware`, `uhf lte firmware` / `uhf modem firmware` commands listed
above. The latter two
require an LTE identity queried within the previous 180 seconds; querying
`lte firmware` or `lte modem firmware` alone returns a console reply and does
not put that identity on RF. LTE single sends are `heartbeat lte`, `system lte`
and `eps lte`; there is no LTE telemetry-run scheduler in this application.

Bench packet wrappers are generated by the serial bridge for Yamcs
`ember-bench`; they are not RF transmissions. Bench payload commands select
one result: IDENT → `PAYLOAD_FIRMWARE`, STATUS_QUERY or HEARTBEAT_QUERY →
`PAYLOAD_STATUS` (different report kind), PING → `PAYLOAD_PING_RESULT`, and
FIRE_CHECK → `PAYLOAD_FIRE_RESULT`. The bridge separately emits
`COMMAND_RESPONSE` stages. A direct IHU console query returns text/application
reply data; it does not itself generate those ground wrappers.

The operational RF fire-check transaction returns one native
`PAYLOAD_FIRE_RESULT`, with no COMMS firmware prefix or extra heartbeat/status
set. The separate diagnostic native RF PING path returns `COMMAND_RESPONSE`;
it is not part of `uhf run` or the Yamcs flight fire-check command.

### What a UHF run contains

The four IHU producers run in this order:

| IHU packet | Included measurements/state | Not acquired by this producer |
|---|---|---|
| `HEARTBEAT` | Mode, configuration, configured telemetry period; header boot ID and uptime | Detailed subsystem measurements |
| `SYSTEM_STATUS` | Mode/configuration, period, admitted/refused request counters | Payload diagnostics or radio diagnostics |
| `POWER_STATUS` | Fresh 19-register PEC-checked EPS read, raw values, ADC/conversion validity, derived voltage/current/temperature | Other subsystem measurements |
| `DEVICE_STATUS` | Cached registry state, seen flag, age, boot ID and timeout count for EPS, EPS_NEXT, COMMS, LTE and payload | A fresh status/heartbeat/IDENT query to every subsystem |

Discovery is deferred during the run; registry ages can increase. The EPS stage
makes its own read. A failed EPS transaction stops the run; an invalid ADC
conversion can still be reported as raw data with validity flags cleared.
Payload fire checks, payload firmware/status reports and LTE firmware reports
are not automatically added to a run. No camera/image/detection data is sent.

COMMS 0.33.0 sends one automatic `COMMS_FIRMWARE` before the first admitted
telemetry request after its boot. It records that announcement only after
successful local RF transmission. Later packets and runs omit it. Starting a
new run, opening a diagnostic window, or restarting IHU does not reset this
COMMS-boot state. There is no RF announcement just because COMMS boots.

A successful first cycle after COMMS boot is:

```text
COMMS_FIRMWARE → HEARTBEAT → SYSTEM_STATUS → POWER_STATUS → DEVICE_STATUS
```

Later cycles contain the four IHU packets only. `uhf run 60 10` starts the first
cycle as soon as transport is ready, then aims to start another cycle
approximately every 10 seconds for 60 seconds. Six full cycles produce
**24 IHU packets**, plus **one COMMS firmware packet if it has not already been
announced during this COMMS boot**: normally 24 or 25 RF packets, rather than
the 48 packets in COMMS 0.32.0 on-demand operation.

These counts assume healthy timing. Each stage waits for its correlated RF
result and a 250 ms turnaround guard; delayed cycles do not produce catch-up
bursts. A fault stops production. The 60-second limit stops new submissions;
an already-admitted packet may finish.

To reacquire the identity after joining the ground link late, issue
`uhf comms firmware` outside an active run. This sends exactly one
`COMMS_FIRMWARE`, using the same permission/HELLO gates and local RF result
tracking. A new explicit command sends it again; replaying the same transport
request does not retransmit. It also satisfies the first-boot announcement if
that has not happened yet. The request payload is empty, so its UHF console
result reports `bytes=0`; that is the CAN request length, not the RF packet size.
No synthetic IHU heartbeat accompanies it. Explicit and automatic identity
sends share the existing RF deadlines, shutdown checks and no-retry behavior.

COMMS USB `a`/`g` diagnostic windows use this same boot-scoped announcement
state. Solicited RF fire-check replies remain separate and get no identity prefix.

### Triggers, pacing and output gates

| Path/control | What starts output | Pacing / stop condition |
|---|---|---|
| `output uhf_telem on` | Permission only; no packet or run starts | A send or run command is still required; OFF stops the producer/unsent work |
| UHF single-send commands above | Explicit command, UHF permission, COMMS HELLO and healthy idle transport | One requested packet; automatic identity only if not yet announced after COMMS boot; no automatic retry |
| `uhf run SECONDS PERIOD` | Explicit command with the same UHF gates | Duration 1–120 s, cycle period 5–60 s; stop with `uhf stop`, UHF OFF, mode change, reset, expiry or fault |
| `output lte_telem on` / `lte N` | Permission / bounded modem window; neither sends telemetry alone | Explicit LTE packet commands still required; window maximum 120 s |
| `heartbeat lte` / `system lte` / `eps lte` | Explicit command, LTE permission, LTE HELLO and modem readiness/window | One selected packet submission; no periodic LTE producer |
| RF fire-check response | Addressed ground command and bounded COMMS receive/reply session | At most one validated reply per session; independent of UHF/LTE telemetry switches |
| Bench EPS forwarding | Running bridge with `--poll-eps` and `umb_telem=1` | Approximately every 5 s between command transactions; unknown/OFF permission stops forwarding |
| Bench payload result | One supported Yamcs bench payload command | Solicited result/stages; streaming switches may all remain OFF |
| `cli_telem` | Explicit ON | Compact text health summary approximately every 5 s when idle; not an RF/native packet set |
| `umb_telem` | Explicit ON | Structured `ihu-health-v1` summary approximately every 5 s when idle; also permits bridge EPS forwarding |
| `cli_debug` / `umb_debug` | Explicit ON | Event-driven tagged diagnostic lines; not periodic telemetry packets |

CLI/umbilical formats currently share USB CDC. The bridge does not forward the
`ihu-health-v1` summary as the heartbeat/system/device set; it separately polls
EPS and wraps `POWER_STATUS`. Existing manual, solicited replies remain available
with stream flags OFF. All six flags clear on reset and accepted mode changes.

These output permissions are available in GROUND_TEST SAFE and the simulated
ground-test modes. IHU FLIGHT configuration remains restricted by its inactive
routine stubs. The Yamcs `ember` flight instance names the ground RF path; it
does not mean the IHU is in FLIGHT configuration. See the
[mode/configuration matrix](../architecture/operations/04-ihu-runtime-policy.md).
RF completion is local radio evidence; confirm ground reception separately.

Implementation references: [IHU producers and dispatch](../../firmware/ihu/main.c),
[run scheduler](../../firmware/ihu/uhf_run.h),
[COMMS announcement and RF drain](../../firmware/comms/rf_service.h),
[RF solicited replies](../../firmware/comms/uplink_service.h), and
[serial bridge](../../ground/ember/payload_bridge.py).

## Removed controls

The old `telemetry`, `eps telemetry`, `telem on/off/status`, `eps enqueue` and
`lte queue ...` commands are removed from IHU 0.13.0. There is no hidden EPS-only
timer or queued LTE sender. Historical test artifacts do not enable those paths.
Do not apply these instructions to the older FreeRTOS CLI or LTE Feather role.

## Bench forwarding

Bridge 0.4.0 with `--poll-eps` checks IHU `outputs` before each periodic EPS
request. With umb_telem OFF, unknown, or unavailable it emits no periodic EPS
packet; cached Yamcs values expire. To see bench EPS telemetry deliberately
select `output umb_telem on` using the sole console owner, then restore the
bridge. The setting survives bridge reconnects, but not IHU reset or mode change.
Explicit PAYLOAD_* command/result transactions do not require streaming flags.
