# Operating EMBER in Yamcs

[Operator guides](README.md) · [Deployment and rollback](../../ground/yamcs/OPERATIONAL.md)

Open [Yamcs on the ground Pi](http://192.168.1.251:8090). One container runs
two environments. Select `realtime` to inspect live data.

| Instance | Use | Links |
|---|---|---|
| `ember` | Flight-oriented LTE/UHF telemetry, regardless of radio path | `lte-tm-in`, `uhf-tm-in` |
| `ember-bench` | Direct IHU serial EPS observations and payload commands | `ihu-serial-in`, `ihu-serial-out` |

Each has its own values, history, alarms and displays. Both decode the same
`/ember` packet namespace. The bench input/output links represent one physical
serial connection, currently attached to m75q. No spare-Pico simulation runs
in these operational instances.

## View telemetry

Open [flight overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)
for last heartbeat/system reports and a power summary, or
[bench overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember-bench__realtime)
for serial EPS and payload observations. Every page has the same four tabs:
Overview, Power, Payload, and Devices & firmware. Firmware identity is consolidated
on Devices; raw tables remain available for diagnostics and charts.
Only bench offers payload command/history buttons. Flight has no implemented
command uplink or command definitions. Old Telemetry/LTE and individual firmware
page bookmarks should use Overview or Devices instead.

Heartbeat and system fields are last reports with receive timestamps; their
current definitions do not expire. Other pages distinguish missing, current
and expired observations using existing packet expiry/validity. Missing firmware
is shown as No identity. A cached firmware version is not a liveness check.

Compare packet timestamps, link activity and validity before trusting a value.
The bench bridge polls `eps json` every five seconds between command transactions;
this reads the charger without changing settings. POWER_STATUS expires after
9.5 seconds in bench and 11 minutes 24 seconds in the live instance. Cached payload observations are
not proof that the payload is currently reachable.

EPS provenance 1 identifies a ground-wrapped IHU console observation, whose
header boot/uptime belongs to the bridge session. Provenance 2 identifies an
IHU-native packet. Inspect ADC/conversion/readout flags and age. Current-sense
values remain provisional; charger die temperature is not battery temperature.
See [display interpretation](../../ground/yamcs/DISPLAYS.md).

Exact duplicate radio arrivals within 120 seconds produce one flight archive
record; raw link counters still count both arrivals. Bench archives are independent.
Older mixed `ember` history remains in place; new bench records begin in
`ember-bench`. Old transport archives are retained, with optional historical
access described in the deployment guide.

## Send a bench command

1. Open the [bench command console](http://192.168.1.251:8090/commanding/send?c=ember-bench__realtime&system=%2Fember).
   Confirm `ember-bench` / `realtime` in the header.
2. Select `PAYLOAD_STATUS_QUERY` under `/ember`; no arguments are required.
3. Send once and open that command's native Command history entry.
4. Inspect Acceptance, Completion, `ember-outcome`, transaction identity and
   result reason. Check that fresh payload status also arrived on the Payload page.

| Command | Purpose |
|---|---|
| `PAYLOAD_PING` | Round trip with 1–240 bytes |
| `PAYLOAD_IDENT` | Payload firmware identity |
| `PAYLOAD_STATUS_QUERY` | Current payload status |
| `PAYLOAD_HEARTBEAT_QUERY` | Explicitly requested payload heartbeat |

These traverse Yamcs on .251 → m75q .252 → IHU serial → CAN A → payload Pi .253.
They do not use an RF uplink. See [payload operation](../../ground/yamcs/PAYLOAD.md).
The old spare-Pico `PING`/`SET_PARAMETER` workflow is a historical reference,
not a command route in either current instance.

| Result | Interpretation |
|---|---|
| Sent | Ground bookkeeping; no device acceptance implied |
| ACCEPTED | Device submitted the request; terminal result is pending |
| COMPLETED | Correlated terminal success |
| REJECTED / EXECUTION_FAILED | Explicit refusal or application failure; inspect reason |
| UNKNOWN / TIMEOUT | Execution may have occurred; investigate before resending |

There is no automatic operation retry. Resending creates a new transaction and
may execute again. Duplicate protection and pending correlation are bounded and
volatile across process restarts. The latest-response dashboard card is not a
substitute for the actual command's history.

## Schedule live UHF telemetry

In `ember / realtime`, use `SET_UHF_TELEMETRY_SCHEDULE` to set
`listen_seconds` and `telemetry_seconds`. Use `SET_UHF_TELEMETRY` with
`enabled=1` to start, or `enabled=0` to stop. The IHU boots with telemetry
off and defaults of 540 seconds listening and 60 seconds for telemetry.
Use `SET_UHF_TELEMETRY_SET` to choose `BASIC` or `FULL`. BASIC sends one
`IHU_STATUS` and one `POWER_STATUS` per window. FULL adds one
`DEVICE_STATUS`, one `SYSTEM_STATUS`, one `HEARTBEAT`, and one
`PAYLOAD_STATUS` when the payload replies over CAN, plus one `GPS_STATUS`.
The Devices display receives the transceiver, payload, LTE CAN MCU and
Walter firmware identities when those devices respond during the window.
The Overview GPS panel shows the fix status, coordinates, MSL altitude,
and satellites used. `PAYLOAD_STATUS` fills the
health fields on the Payload display. BASIC is the boot
default. The command report confirms the selected set and applied values.
See the [IHU schedule and RF behavior](ihu-link-active.md#scheduled-telemetry).

## Fire check capture GPS

Send `PAYLOAD_FIRE_CHECK` from `ember / realtime`. The Payload display shows
the latest tagged result, check ID and GPS status. Command History retains
the tag for each command. The payload writes `capture.json` beside the case
evidence, with the original image filenames, capture interval, GPS status
and check ID. An on-demand GPS read runs before capture. The payload
qualifies the estimated fix age at the end of the capture interval using a
6-second limit. An unavailable or stale fix leaves the coordinates empty
and the fire check proceeds.

## Command report reason codes

Open the command in **Command History**. The completion message shows the
numeric reason and its name, for example `reason 7 (NOT_AVAILABLE), payload
error 11 (ANALYSIS_NO_DECISION)`. The report also exposes separate fields
`ember-result-reason` and `ember-result-reason-name`, plus
`ember-payload-error-code` and `ember-payload-error-name` when applicable.
A timeout has no reason code from the spacecraft. The names are added to new
command records as replies arrive.

| `ember-result-reason` | Name | Meaning |
| ---: | --- | --- |
| 0 | `NONE` | No error reported |
| 1 | `UNKNOWN_COMMAND` | Command is unrecognized |
| 2 | `INVALID_PARAMETER` | An argument is invalid or unsupported |
| 3 | `MODE_NOT_ALLOWED` | The current mode prohibits the command |
| 4 | `INTERLOCK` | A required interlock condition is unmet |
| 5 | `BUSY` | A required resource is busy |
| 6 | `FAULT_ACTIVE` | An active fault blocks the command |
| 7 | `NOT_AVAILABLE` | The requested data or result is unavailable |
| 8 | `EXECUTION_ERROR` | The command encountered an execution error |
| 9 | `TRANSACTION_CONFLICT` | The transaction conflicts with a previous request |

For a fire check that returns `NOT_AVAILABLE`, read the payload error as a
second code. These meanings apply to payload 0.6.1.

| `ember-payload-error-code` | Name | Meaning |
| ---: | --- | --- |
| 0 | `NO_PAYLOAD_ERROR_REPORTED` | The IHU had no specific payload error to forward, including when no CAN reply arrived. |
| 1 | `UNSUPPORTED_CAN_VERSION` | Unsupported CAN packet version |
| 2 | `UNSUPPORTED_PAYLOAD_COMMAND` | Unsupported payload command |
| 3 | `SENDER_OR_SESSION_MISMATCH` | Sender or session mismatch, including a missing valid HELLO |
| 4 | `INVALID_CAN_PAYLOAD` | Invalid CAN command payload |
| 5 | `CAPTURE_BUSY` | A capture is already in progress |
| 8 | `CAPTURE_OR_EVIDENCE_ERROR` | Capture raised an exception or the responder could not save reply evidence. |
| 11 | `ANALYSIS_NO_DECISION` | The analysis returned no usable decision. Check the run's `result.json` on the payload Pi for the detector reason. |

For example, `7 / 0` can indicate that the IHU got no response to its CAN
handshake. `7 / 11` means the payload replied with an analysis error, such as
`ANALYSIS_DEADLINE` or `REGISTRATION_TOO_FEW_MATCHES`.

## Manual console and troubleshooting

On m75q, run `sudo systemctl stop ember-bench-bridge` before opening the IHU
console. This stops both EPS polling and payload command handling. Close the
manual console, then run `sudo systemctl start ember-bench-bridge`. Do not start
the retired EPS, spare-USB or payload-only bridge services alongside it.

For missing values, confirm the environment and `realtime` processor, then inspect
Links and archive reception times. An enabled link alone does not prove traffic.
For EPS invalid/stale values, check readout/ADC flags rather than interpreting
sentinels as voltages. Radio apps retain their existing ownership/window controls.

For replay, choose the archive interval in the intended instance, start a named
Archive processor and confirm the replay header/clock. Return explicitly to
`realtime` afterward. Historical freshness follows replay time, not laptop time.
See [archive replay](../../system/ground_station/archive_replay.md).

Authoritative packets: [dictionary](../../ground/ember/dictionary.json),
[bench contract](../../system/protocols/ember_bench_v1.md), and
[EPS format](../../system/protocols/eps_power_status_v1.md).
