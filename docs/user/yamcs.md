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
9.5 seconds in bench and 57 seconds in flight. Cached payload observations are
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
