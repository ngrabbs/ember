# EMBER flight and bench environments

One Docker container runs two Yamcs instances at [the Pi](http://192.168.1.251:8090).
Choose the environment, then stay in its `realtime` processor. Both use the same
`/ember` packet namespace and dictionary source; archives, current values,
command history and display buckets are independent.

| Instance | Purpose | Links | Displays |
|---|---|---|---|
| `ember` | Radio reception and bounded fire-check command | `lte-tm-in` UDP10018; `uhf-tm-in` UDP10019; fire-check TC UDP10029 | `ember_displays` |
| `ember-bench` | One physical IHU serial connection | `ihu-serial-in` UDP10020; `ihu-serial-out` to m75q UDP10028 | `ember_bench_displays` |

The bench input/output pair represents the two directions of one serial path,
not two connected devices. The IHU is currently attached by its USB serial
console to m75q (.252), which bridges it to Yamcs on the ground Pi (.251).
The old spare-Pico USB and separate EPS UART services are disabled.

Open [flight overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)
or [bench overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember-bench__realtime).
Flight Overview summarizes heartbeat/system/power; bench Overview summarizes
serial EPS/payload/power. Both use Overview, Power, Payload and Devices & firmware.
Flight exposes PAYLOAD_FIRE_CHECK through the bounded real RF path. Bench exposes
PAYLOAD_PING, PAYLOAD_IDENT, PAYLOAD_STATUS_QUERY, PAYLOAD_HEARTBEAT_QUERY and
PAYLOAD_FIRE_CHECK through serial/CAN. See [fire-check operation](FIRE_CHECK.md).

## IHU0.13.0 quiet-output policy

With bench bridge0.4.0, all IHU streams start OFF. The bridge checks `outputs`
and forwards periodic EPS only when `output umb_telem on` has been deliberately
selected. Disabling it stops new forwarding; old ground values expire. This
policy is separate from explicit PAYLOAD_* command replies and the bounded RF
command session. See the [mode/output matrix](../../docs/architecture/operations/04-ihu-runtime-policy.md).
The installation history below describes earlier always-polling bridge versions.

## Serial ownership and EPS

`ember-bench-bridge.service` on m75q exclusively owns the physical IHU console.
It polls observational `eps json` every five seconds between payload command
transactions and sends POWER_STATUS to the bench instance. It does not change
charger configuration, ADC mode or thermistor protection. Ground wrappers retain
provenance 1 and a bridge-session boot identity. Their currents use provisional
10 mΩ sense values; `sense_values_verified` remains false.

For manual console access, on m75q:

```sh
# Release the IHU console; periodic EPS telemetry and payload commands stop.
sudo systemctl stop ember-bench-bridge
# After closing your manual serial program, resume the shared owner.
sudo systemctl start ember-bench-bridge
journalctl -u ember-bench-bridge -n 30 --no-pager
```

Payload commands traverse IHU → CAN A → payload Pi. Consult [PAYLOAD.md](PAYLOAD.md)
for command outcomes. A busy/failed route never falls back to another endpoint.
Bench traffic is not forwarded into flight automatically.

Within each instance, exact CRC-valid duplicates are suppressed for 120 seconds,
with a 4096-entry bound. Flight LTE/UHF copies therefore share one archive entry;
the same bytes may independently appear in the bench archive. Suppression resets
with Yamcs. Link counters still count arrivals. POWER_STATUS expiry is 57 seconds
in flight and 9.5 seconds in bench, using Yamcs's default 1.9 tolerance. Inspect
receive times and readout validity; cached values alone do not establish liveness.

## Deployment and startup

Preserve dirty source checkouts. The deployed source export is
`/home/ngrabbs/work/ember-environments-20261017` on the Pi. The active runtime
remains `/home/ngrabbs/work/MSU_Cubesat/ember/ground/yamcs/.runtime/quickstart`.

1. Pause `ember-ground-readiness` while maintaining Yamcs, so its unhealthy-container
   recovery cannot restart the server during backup. Stop Yamcs explicitly and
   back up its complete runtime, Compose environment and persistent data volume.
2. Run `python3 ground/yamcs/prepare_operational.py --runtime /path/to/quickstart`
   from the clean source. The helper also saves configs, both MDBs and Java
   sources privately under `.unified-backups/TIMESTAMP`; this is not a data backup.
3. Append `ground/yamcs/compose.operational.yaml` last in `COMPOSE_FILE`, retaining
   the existing boot/radio overlays and Ethernet/hotspot HTTP binding. It publishes
   only radio UDP10018/10019 on loopback and bench UDP10020 on the station interface.
   Reference simulators stay behind an explicit profile.
4. Stop and disable the Pi's old `ember-usb-bridge` and `ember-eps-bridge`. On m75q,
   install the complete `ground/ember` directory under `/opt/ember-bench/ember`
   and install `ember-bench-bridge.service`. Stop/disable the old
   `ember-payload-bridge` before enabling the new service; never run two serial owners.
5. Start the normal `ember-ground-starter` service, then resume readiness supervision.
   `/api/instances` must show `ember` and `ember-bench` RUNNING, each with two links.
   Verify flight has one fire-check command definition and bench has five.
6. Run `python3 ground/yamcs/install_displays.py --url http://PI:8090` to install
   both buckets. It backs up replaced objects and verifies uploaded bytes; named old
   duplicate pages are retired only after backup. See [display cleanup](DISPLAYS.md).
   Audit each separately with `build_identity.py --instance ember` and
   `--instance ember-bench`, using explicit new release/output/publish arguments.

Yamcs and the serial bench service are enabled at boot. Existing Ethernet-first
hotspot and LibreSDR listener supervision remain in place. This change does not
transmit automatically at boot; only an explicit flight fire-check command starts a bounded RF transaction.

## History and rollback

Private pre-split backups are at
`/home/ngrabbs/work/deploy-backups/environments-20261017` on the Pi.
Existing `ember` history is preserved, including bench records received before
this split. New serial records go to `ember-bench`; historical records were not
moved, retimestamped or reinjected. Older `ember-lte`, `ember-uhf`, `ember-payload`
and `myproject` archives also remain in the same persistent volume.

Optional `--legacy-history ember-lte` (repeat for other legacy names) enables
historical instances without hardware links. Run preparation without those
options to return to the normal two-instance UI. Old replay URLs require the
corresponding historical instance/processor.

To roll back, pause readiness, stop Yamcs and the new bench bridge, restore the
saved runtime/Compose environment and previous bridge service, then restart.
Keep the live data volume to retain new records. Restore old data backups to
separate recovery volumes rather than overwriting post-migration history.

## Validation

The ground unit suite covers both MDBs, idempotent preparation, command routing,
shared serial polling and disconnect recovery. `operational_check.py` runs only
against a separate loopback validation server on HTTP8091 with TM11018/11019/
11020 and mock TC11028. It verifies radio deduplication, independent bench
archives, bad-CRC rejection, flight refusal of serial-only commands, bench completion and
cross-instance reply isolation. Never inject its synthetic packets into production.

See [deployment evidence](../../system/ground_station/evidence/yamcs-environments-20261017.json).
Physical RF requalification remains separate from configuration and serial tests.
