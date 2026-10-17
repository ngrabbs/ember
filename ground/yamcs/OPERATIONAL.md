# One operational EMBER instance

Use **`ember` / `realtime`** at [the Pi](http://192.168.1.251:8090).
The normal server starts only this instance. USB, UART, UHF, LTE and payload
arrivals use the same dictionary, parameter namespace, dashboards, alarms and
new archive. Changing the receiving link does not change the spacecraft.

Open [Overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime),
[Telemetry](http://192.168.1.251:8090/telemetry/displays/files/Telemetry.opi?c=ember__realtime),
[EPS](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember__realtime),
[Payload](http://192.168.1.251:8090/telemetry/displays/files/Payload.opi?c=ember__realtime)
or [Links](http://192.168.1.251:8090/links?c=ember__realtime).
`LTE.opi` remains a compatibility copy of the common telemetry page.

| Link | Existing UDP endpoint | Purpose |
|---|---|---|
| `usb-in` | Pi loopback 10016 | USB packet bridge telemetry |
| `eps-uart-in` | Pi loopback 10017 | Ground-wrapped IHU EPS UART observations |
| `eps-lte-in` | Pi loopback 10018 | Validated native LTE telemetry |
| `eps-uhf-in` | Pi loopback 10019 | Validated UHF telemetry |
| `payload-ihu-bench-in` | Pi LAN 10020 | IHU/payload CAN bench observations |
| `usb-out` | Docker host gateway 10026 | PING, REQUEST_STATUS, REQUEST_TELEMETRY, SET_PARAMETER |
| `payload-ihu-bench-out` | m75q 192.168.1.252:10028 | PAYLOAD_PING, PAYLOAD_IDENT, PAYLOAD_STATUS_QUERY, PAYLOAD_HEARTBEAT_QUERY |

Only the two command links can transmit commands. Each has its own TC stream
with explicit command-name patterns; neither stream is a catch-all. A failed
payload route does not fall back to the USB bench endpoint. No RF command
uplink or automatic RF start was added. Existing radio ownership/window
controls and the LTE listener remain in place.

The spare USB Pico is still a bench application, not the physical IHU. Its
response correlation uses the `usb` result domain; physical telemetry/results
use `spacecraft`. Ground-wrapped EPS uses its bridge session for header boot
identity, so it is excluded from physical-IHU boot-change detection. Packet
provenance and boot IDs remain visible; transport consolidation does not make
bench simulations into spacecraft observations.

The first CRC-valid exact packet copy is processed/archived with its receiving
link. Other identical arrivals within 120 seconds are suppressed across links,
with a 4096-entry bound. Different boot IDs, uptime, payload or provenance are
distinct. Raw link counters still count arrivals. The filter resets with Yamcs;
it is not durable duplicate suppression. Per-link sequence gaps are not emitted
as spacecraft loss alarms in this combined mode, where packets may use different
paths. POWER_STATUS uses the existing sparse-radio 30-second allowance in the
shared MDB (57-second expiry with Yamcs's default 1.9 tolerance). Check actual
receive times and EPS readout validity as well as displayed cached values.

## Prepare or update a station

Use a clean source checkout, preserving dirty working trees and local runtime
customizations. `prepare.py --transport usb` now prepares the consolidated
operational configuration for a new lab. To migrate an already provisioned Pi,
use the additive runtime preparation below instead of legacy regeneration.
The helper saves previous configs, common MDB and Java sources privately under
`RUNTIME/.unified-backups/TIMESTAMP/`; this is not a data-volume backup.

1. Save the active Compose configuration/environment and runtime. Stop Yamcs
   before backing up its complete `yamcs-data` volume. Retain both backups.
2. From the clean source, run:

   ```sh
   python3 ground/yamcs/prepare_operational.py --runtime /path/to/quickstart
   ```

3. Retain existing USB, UHF, payload and boot overlays, appending
   `ground/yamcs/compose.operational.yaml` last in `COMPOSE_FILE`. That overlay
   removes simulator dependencies and places the reference simulators behind
   an explicit profile. Stop any already-running reference simulator container.
   Keep the Pi's Ethernet/hotspot HTTP binding. The telemetry UDP ports above
   are unchanged, so receiver services need no destination change.
4. Compile the runtime and recreate only Yamcs using its normal Compose
   deployment. Verify `/api/instances` lists only `ember` RUNNING, and all seven
   links are present. Check a fresh observation's link and parameter timestamp.
5. Run `python3 ground/yamcs/install_displays.py --url http://PI:8090`. It backs
   up replaced objects and verifies uploaded bytes. Old release/build manifests
   are dated records, not fingerprints of this new deployment. Publish a new
   `build_identity.py --instance ember` audit after installing the displays.

The deployed clean source is `/home/ngrabbs/work/ember-unified-20261017` on the
Pi. Its active runtime remains under
`/home/ngrabbs/work/MSU_Cubesat/ember/ground/yamcs/.runtime/quickstart`, in the
existing service/volume. Private pre-migration backups are at
`/home/ngrabbs/work/deploy-backups/unified-20261017/` on the Pi. See the committed
[deployment evidence](../../system/ground_station/evidence/yamcs-unified-20261017.json).

## Existing history and rollback

Old `ember-lte`, `ember-uhf`, `ember-payload` and `myproject` data remains in its
original archive in the same persistent volume. It was not reinjected into
realtime, retimestamped, or silently merged into `ember`. A restored copy of
the pre-migration volume was tested against recorded packet witnesses from
all five instances. New operational records go only to `ember`.

For occasional access, prepare the runtime with an additional option, then
restart Yamcs:

```sh
python3 ground/yamcs/prepare_operational.py --runtime /path/to/quickstart \
  --legacy-history ember-lte
```

Repeat the option for other old archives if needed. These optional instances
have **no telemetry or command data links** and an unroutable TC stream; they
are for historical access. They are not hardware command endpoints. Run the
helper without these options and restart to return to the single-instance UI.
Old proof/replay URLs work only when the relevant historical instance and replay
processor are available; new `ember` does not inherit old replay processors.

To roll back, stop Yamcs, restore the saved runtime and Compose environment,
and start its original deployment. Keep the live data volume intact to retain
new records. Restoring the entire pre-migration data backup would also revert
post-migration records, so restore it to a separate volume for recovery/history
inspection rather than overwriting new data.

## Validation

`tests/ground/test_operational_yamcs.py` verifies preparation, idempotence,
retained legacy files, complete MDB and exclusive command patterns. The Java
`EmberDuplicatesTest` checks exact bytes, TTL, instance isolation and eviction.
`operational_check.py` is an integration check for a **separate loopback-only
validation server on port 8091**, remapped to TM11016–11020 and mock TC11026/
11028. It sends synthetic packets/commands only there. Do not repoint this
check at an operational instance. It covers all five inputs, shared duplicates,
CRC rejection, separate command routes, result-domain isolation, EPS-wrapper
boot handling and disabled-route refusal without fallback.
