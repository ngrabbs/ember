# Commanding and monitoring EMBER in Yamcs

[Operator guides](README.md) · [Lab installation](../../ground/yamcs/README.md)

This guide describes the EMBER integration pinned to Yamcs 5.13.0, reviewed
October 4, 2026 against repository dictionary, adapters and configuration,
with LTE/UHF publication reconciled on October 5.
Deployment/UI checks cited below were recorded October 1–3; this review did not
connect to or change the running Pi. Check the selected instance, processor and
endpoint before sending a command.

## Instances and endpoints

The recorded bench web address is [Pi Yamcs](http://192.168.1.251:8090).
Use your configured host if different. The instance and processor appear in
Yamcs's header/context selector.

| Instance / processor | Data source | Command capability |
|---|---|---|
| `ember` / `realtime`, simulator configuration | Software GROUND_TEST endpoint | Four bench commands below |
| `ember` / `realtime`, USB configuration | Dedicated spare USB Pico, plus separate real IHU UART EPS input | Four commands reach the spare Pico; EPS UART input is observational only |
| `ember-lte` / `realtime` | Native IHU EPS received through Walter LTE-M; `eps-lte-in`, UDP 10018 | No telecommand data link configured |
| `ember-uhf` / `realtime` | Native IHU EPS over CAN → SDRB → UHF → LibreSDR; `eps-uhf-in`, UDP 10019 | No telecommand data link configured |
| `myproject` / `realtime` | Upstream quickstart sample | Upstream demonstration commands; not EMBER device controls |
| An Archive replay processor | Previously archived packets in its instance | Replay does not reissue hardware commands |

The optional `ember-uhf` configuration and native IHU cadence are now published.
Follow the [UHF setup](../../ground/uhf/README.md) and
[service runbook](../../ground/uhf/SERVICES.md) for an explicitly started bench.
Services remain disabled at boot; instance configuration does not establish an
active RF session. LTE and UHF share LibreSDR and require separate radio ownership.

All EMBER instances share the generated dictionary/displays; presence of a
command definition in an MDB does not establish a configured uplink. USB and
simulator configurations are alternatives for the `ember` command endpoint.
Have the lab operator confirm which is selected in `.env` and the active bridge
before changing its telemetry period. A wire endpoint named IHU does not turn
the spare command-test Pico into the physical EPS controller.

## Send a first command

1. Open the [EMBER command console](http://192.168.1.251:8090/commanding/send?c=ember__realtime&system=%2Fember).
   Confirm `ember` and `realtime` in the header and the intended command endpoint.
2. Under `/ember`, select `PING`. It has no arguments.
3. Send the command once. Open its entry in native **Command history**.
4. Inspect Sent, `EMBER_Acceptance`, Completion and `ember-outcome`, together
   with `ember-transaction-epoch`, `ember-transaction-id`, `ember-result-boot-id`
   and `ember-result-reason`.
5. A correlated COMPLETED result with reason NONE establishes the bench command
   exchange. It does not prove EPS charger control or an LTE uplink.

The existing USB validation records a completed hardware PING on the spare Pico.
If a command times out, inspect endpoint/link state before manually resending.
There is no automatic retry. **Resend this command allocates a new transaction**;
it can execute again. Identity-preserving retry is not exposed by this UI.

## Commands currently available

| Command | ID | Arguments | Action and expected replies |
|---|---|---|---|
| `PING` | `0x01` | None | ACCEPTED, then COMPLETED; no requested telemetry payload |
| `REQUEST_STATUS` | `0x02` | None | ACCEPTED, correlated SYSTEM_STATUS, then COMPLETED |
| `REQUEST_TELEMETRY` | `0x03` | `data_group=SYSTEM` (1) or `COMMS` (48) | ACCEPTED, correlated SYSTEM_STATUS or COMM_STATUS, then COMPLETED |
| `SET_PARAMETER` | `0x30` | `parameter_id=TELEMETRY_PERIOD` (1), `value` in milliseconds | ACCEPTED, then COMPLETED echoing parameter ID and applied value |

The editor may present enum labels; numeric values above identify the same wire
arguments. `TELEMETRY_PERIOD` accepts **100–60000 ms inclusive**, defaults to
1000 ms at endpoint boot and is nonpersistent. It controls periodic HEARTBEAT,
SYSTEM_STATUS and COMM_STATUS on the simulator/spare Pico. It does not change
EPS UART polling or Walter RF windows. The published CAN IHU image emits
telemetry manually; its later local cadence experiment is outside this PR.

For a period change, record the current period first. Select `SET_PARAMETER`,
show arguments/defaults, use parameter 1 and value 2000, and send once. Confirm
completion echoes 2000, request fresh status, and check heartbeat uptime deltas.
Restore the previous period when the test finishes.

The broader mission draft includes `SET_MODE`, `CLEAR_FAULT`, `REBOOT_IHU`,
payload commands, log requests and deployment tests. Those commands are **not
implemented by the current four-command bench dictionary**. The local UART
`reboot` command is a separate interface.

## What the responses look like

The web UI renders history acknowledgments and parameter values. It does not
print an `ihu>` transcript. The examples below are decoded packet fields from
[the reviewed software endpoint](../../ground/ember/simulator.py), with enum
labels added for readability; they are not screenshots or fresh hardware captures.

For a successful period change to 2000 ms, two COMMAND_RESPONSE packets have:

| Field | Acceptance | Completion |
|---|---|---|
| `command_id` | 48 (`SET_PARAMETER`) | 48 (`SET_PARAMETER`) |
| `stage` | 0 (`ACCEPTED`) | 2 (`COMPLETED`) |
| `reason` | 0 (`NONE`) | 0 (`NONE`) |
| `parameter_id` | 0 | 1 (`TELEMETRY_PERIOD`) |
| `value` | 0 | 2000 |

Their headers echo the same command epoch and transaction ID, and identify the
endpoint's boot. Acceptance fields zero do not mean the requested period is zero.
In history, the completed outcome appears as `ember-outcome=COMPLETED`, result
reason 0, and successful Completion. Correlation must match the issued command;
the Overview's cached “latest response” card is insufficient.

`REQUEST_STATUS` returns SYSTEM_STATUS fields such as:

```text
mode=3 (SAFE)
configuration=1 (GROUND_TEST)
telemetry_period_ms=2000
accepted_commands=<endpoint counter>
rejected_commands=<endpoint counter>
```

SAFE/GROUND_TEST are fixed bench states, not proof of a running flight mode
manager. The requested data echoes the command transaction; unsolicited
periodic telemetry uses epoch/transaction zero. A query's completion means the
endpoint generated/queued the requested data; independently confirm the
correlated telemetry arrived.

`REQUEST_TELEMETRY` group COMMS returns `rx_packets`, `tx_packets`, `crc_errors`,
`dropped_packets` and `rssi_dbm`. `rssi_dbm=-32768` is unavailable, as on the USB
endpoint. These are that endpoint's counters, not readings from the custom
communications board. The Pico TX counter means handed to its SDK USB writer,
not acknowledged ground delivery.

Invalid arguments that reach the endpoint return a single terminal response,
for example `command_id=48, stage=1 (REJECTED), reason=2 (INVALID_PARAMETER),
parameter_id=0, value=0`. The Yamcs argument editor may block an out-of-range
value before transmission; endpoint rejection tests use structurally valid
packets to exercise this separately. Malformed packets can be discarded without
an application result.

## Interpret command history

| Observation | Meaning |
|---|---|
| Yamcs Sent | Ground link transmission bookkeeping; no device acceptance implied |
| `EMBER_Acceptance` successful | Device reported ACCEPTED; execution result may still be pending |
| Completion successful and outcome COMPLETED | Correlated device terminal success |
| Acceptance/Completion NOK and outcome REJECTED | Explicit terminal refusal with reason |
| Completion NOK and outcome EXECUTION_FAILED | Device reported an execution failure |
| TIMEOUT and outcome UNKNOWN | Result deadline expired or endpoint boot changed; execution may have happened |
| Acceptance NA with a terminal result | Acceptance packet was missing, but a correlated terminal result arrived |

Acceptance deadline is five seconds; after acceptance, the terminal deadline
is ten seconds. The adapters track up to 256 pending commands in memory. Late
result reconciliation and recovery of pending correlation after a server restart
remain open. The endpoint's last-64 transaction cache is volatile: restart or
cache eviction can lose duplicate protection.

Defined response reasons are NONE (0), UNKNOWN_COMMAND (1), INVALID_PARAMETER
(2), MODE_NOT_ALLOWED (3), INTERLOCK (4), BUSY (5), FAULT_ACTIVE (6),
NOT_AVAILABLE (7), EXECUTION_ERROR (8), and TRANSACTION_CONFLICT (9). These are
protocol definitions; not every flight policy/reason is exercised by the simple
bench dispatcher. Changed arguments under an existing transaction identity
produce TRANSACTION_CONFLICT.

## Telemetry and displays available today

Open [Overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)
for the simulator/spare Pico, or [EPS](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember__realtime)
for the UART wrapper. For received native LTE EPS, explicitly select
[LTE EPS](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-lte__realtime).

| View or feature | What it provides | Interpretation |
|---|---|---|
| Overview.opi | Mode/configuration, period, heartbeat time, boot identity, counters and latest response | Latest received snapshots; inspect freshness and native command history |
| System.par | State, heartbeat, packet-specific boot/uptime and acquisition status | Endpoint uptime is not UTC |
| Comms.par | Endpoint packet/error counters and RSSI | Unavailable RSSI is not measured signal strength |
| Command-reports.par | Last response-field samples, bounded 40-row buffer | Not the correlated transaction history |
| EPS.opi | Real voltages, provisional currents, die temperature, raw charger state and quality/age | Hides invalid/expired engineering values |
| EPS.par | All 19 raw registers, engineering values, quality and provenance | Use numeric fields for history/charts; inspect ADC/conversion flags |
| Native parameter charts/history | Archived and live decoded values | Click a numeric value, or select a parameter from its table |
| Packet archive | Original received packet data and metadata | Preserve identity and provenance when comparing channels |
| Native command history | Per-command identity, acknowledgments and outcomes | Authoritative place to evaluate a command exchange |
| Archive replay | Play, pause and seek saved telemetry through an Archive processor | Historical processor time determines freshness |
| Bounded export/local replay | Portable session via `session.py` | Separate from live hardware and native interactive replay |

Current packet types are SYSTEM_STATUS (`0x01`), HEARTBEAT (`0x05`), POWER_STATUS
(`0x10`), COMM_STATUS (`0x30`) and COMMAND_RESPONSE (`0x31`). The dictionary owns
field order and units; [display interpretation](../../ground/yamcs/DISPLAYS.md)
explains packet-specific boot bindings and unavailable values.

For EPS, inspect `provenance`, link, readout/ADC/conversion validity, readout age
and `sense_values_verified`. Provenance 1 is an IHU UART observation packaged
by the Pi: header boot/uptime identifies the bridge session. Provenance 2 is an
IHU-native packet: header boot/uptime identifies IHU and bridge_session_id is zero.
Provenance identifies the producer, not successful RF transport. Native radio
archive evidence establishes the LTE path separately. Current-sense values
remain provisional; die temperature is not battery temperature.

Yamcs generation time currently equals ground reception time. The separate
spacecraft uptime field is not UTC. A link marked enabled or old value marked
acquired does not prove fresh data; compare packet activity, timestamps and
expiration-aware displays. Repeated Pi wrapper packets can contain the same
five-second UART readout. Readout age is not necessarily ADC conversion age.

## Replay and return to live operation

1. In the intended instance, open Archive and select a recorded time interval.
2. Select the timeline range tool, drag the interval, and choose **Replay range**.
3. Check the interval, assign a unique processor name and Start. Confirm the
   purple replay header and historical processor clock.
4. Open the EPS display in that replay context. Let a subscribed packet play,
   then pause if inspecting a sample. Seek through Archive in the same context;
   the recorded UI resumed playback on seek, so pause again as needed.
5. Return explicitly to the instance's `realtime` processor. Confirm the purple
   replay header/Play control disappears and the clock is current.

A paused replay sample does not age according to laptop wall time. Its link
status describes the archived packet; a historical LIVE label does not mean
hardware is connected now. See the [verified replay procedure](../../system/ground_station/archive_replay.md)
and [portable session procedure](../../system/ground_station/telemetry_sessions.md).
Archive retention, backups and tested restoration remain unfinished.

## Boundaries and troubleshooting

- **No new values:** verify instance/processor, fresh receive timestamps and link
  activity. An inactive RF bench cannot populate its isolated instance.
- **EPS INVALID or STALE:** inspect UART/radio availability, readout validity,
  ADC/cell/chemistry flags, age and expiration. Do not interpret sentinels as measurements.
- **Command UNKNOWN:** inspect transport and fresh endpoint status; determine
  whether the action occurred before sending a new transaction.
- **Command definition visible on LTE/UHF:** no telecommand link is configured;
  use local device consoles for the implemented bench controls.
- **Old command result still on Overview:** open the actual command's history;
  cached response parameters do not track the latest issued transaction.

Flight uplink authentication/authorization, full mission commands/events,
spacecraft UTC, reliable continuous radio operation and production CAN A/B
integration remain separate work. The existing lab procedures own setup/startup;
this guide does not require restarting services to inspect data.

## Implementation and recorded verification

Authoritative definitions: [dictionary.json](../../ground/ember/dictionary.json),
[bench contract](../../system/protocols/ember_bench_v1.md) and
[EPS payload](../../system/protocols/eps_power_status_v1.md).
Dispatch: [simulator](../../ground/ember/simulator.py) and
[USB endpoint](../../firmware/usb_bench/protocol.c).
Correlation: [command postprocessor](../../ground/yamcs/ember-java/EmberCommandPostprocessor.java)
and [result tracker](../../ground/yamcs/ember-java/EmberResults.java).
Instances: [Yamcs preparation](../../ground/yamcs/prepare.py).
Recorded verification: [USB commanding](../../system/ground_station/usb_validation.md),
[EPS quality](../../system/ground_station/eps_yamcs_setup.md),
[displays](../../ground/yamcs/DISPLAYS.md),
[archive replay](../../system/ground_station/archive_replay.md),
[LTE trials](../../ground/lte/README.md),
[UHF configuration](../../ground/uhf/prepare_yamcs.py) and
[recorded UHF trials](../../ground/uhf/README.md).
