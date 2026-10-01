# EMBER operator displays

[Open the Pi overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)

Yamcs calls these Displays. EMBER selects its own `ember_displays` bucket at
instance level; the `myproject` reference keeps the default `displays` bucket.
They use native Yamcs OPI/parameter-table formats, rather than a separate web
application or a desktop-only profile. Laptop browser access is sufficient.

- **Overview.opi:** spacecraft mode/configuration, telemetry period, boot ID,
  endpoint RX/TX/CRC/drop counters, RSSI, latest response stage/reason/command/
  parameter/value, last heartbeat reception time and uptime. Click a numeric
  value to open its native parameter history/plotting page.
- **System.par:** editable native table of state, heartbeat and common header,
  with generation time, raw/engineering values and acquisition status.
- **Comms.par:** packet/error counters and raw RSSI, plus common header.
- **Command-reports.par:** scrolling live response-field samples with a bounded
  40-row buffer. This is not a transaction log; native **Command history** owns
  correlated acceptance/completion, rejected and UNKNOWN/timeout outcomes.
- Buttons open these tables, the native command console/history and link status.
  Navigation buttons do not issue commands.

## Install and update

On the Pi or m75q, from `ground/yamcs`:

```sh
python3 prepare.py
# Required once after introducing the instance displayBucket setting:
docker compose restart yamcs
# Once the server is ready:
python3 install_displays.py --url http://192.168.1.251:8090
```

Use m75q's URL on m75q. `generate_displays.py` builds into ignored
`.runtime/ember-displays`; table fields come from the bench dictionary.
The installer creates the bucket if absent, skips unchanged files, backs up
any modified existing object under `.runtime/display-backups/TIMESTAMP/`, and
verifies uploaded bytes by downloading them again. It only installs the six
managed objects; unrelated displays are preserved. Rerunning installation
replaces managed files, so preserve/adopt browser table edits in source first.
Modified files are backed up locally, but that directory is not an archive
backup. The bucket itself persists in the existing Yamcs data volume.

An OPI is edited through source/generation or Yamcs Studio. Parameter tables
can be edited in the browser and saved. Browser View → Zoom out/in adjusts
layout for a narrow panel; the native web viewer starts at actual size even
though the OPI includes Studio's auto-zoom setting. A narrow Codex browser
panel was checked at 60% scale. No custom browser renderer is installed.

## Interpret the data

These are **latest received** snapshots. Yamcs can retain values while the
physical endpoint is disconnected. Compare last-heartbeat time with mission
time, and check packet/link counts before treating values as current. No
calculated freshness alarm or physical-link connectivity lamp is implemented.
When replaying, the samples/time follow the selected processor; do not compare
replayed sample time with the laptop's wall clock.

Bench generation time currently equals Yamcs reception time, not spacecraft
UTC. Uptime is separate and wraps at 32 bits. RSSI=-32768 is rendered
**Unavailable** on the overview; USB has no measured radio signal strength.
Endpoint TX counts mean handed to the SDK USB writer, not acknowledged delivery.
Counters/cache and period settings reset on Pico reboot.

The common transaction header changes on **every** packet, including periodic
telemetry with transaction zero. It is deliberately omitted from the command
card/table, so a cached COMPLETED response is not paired with an unrelated
header. The native command history contains per-command transaction IDs and
outcomes. Response fields are also last received snapshots, not a promise that
the most recently issued command has completed. A new Pico boot can leave old
response fields cached until another response arrives; check command history.

## Validation — 2026-10-01

- 23 parameter bindings resolve against the live Pi EMBER mission database;
  all 51 generated widget IDs are unique.
- Native OPI renders real Pico values, advancing uptime/heartbeat time and
  packet counts; SAFE / GROUND_TEST and1000ms match the endpoint.
- A real hardware PING completed after the display configuration restart;
  the overview shows its COMPLETED / NONE response and report timestamp.
- System table navigation and received values/timestamps verified in browser;
  clicking telemetry period opens the native chart with an archived/live1000ms
  trace. Interactive processor replay remains a separate checklist item.
- Overview RSSI sentinel shows Unavailable; missing response samples use an
  unfilled placeholder rather than fabricated success.
- Installation is idempotent and preserves previous changed object bytes.

References: [Yamcs display support](https://docs.yamcs.org/yamcs-server-manual/web-interface/telemetry/),
[instance display bucket configuration](https://docs.yamcs.org/yamcs-server-manual/web-interface/configuration/).
The renderer/format was checked against Yamcs5.13.0 source and @yamcs/opi1.3.3.
