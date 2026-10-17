# Payload ground support 1.3.0

The `ember-payload` instance provides a payload dashboard, parameter table,
command history and four commands. The first implementation uses a LAN bench
route: Yamcs (.251) → UDP → m75q (.252) → IHU USB console → CAN A (500 kbit/s)
→ Pi payload (.253). This is not the transceiver's RF uplink/downlink. Camera
and image functions are outside this release.

Open `http://192.168.1.251:8090/telemetry/displays/files/Payload.opi?c=ember-payload__realtime`.
The display's command button selects the correct instance. Commands are
`PAYLOAD_PING` (1–240 bytes), `PAYLOAD_IDENT`, `PAYLOAD_STATUS_QUERY` and
`PAYLOAD_HEARTBEAT_QUERY`. Heartbeat is explicitly requested; the bridge does
not poll autonomously. Cached values remain visible after link loss; compare
reply timestamps and query status to establish current liveness. Expired
parameters can show Yamcs invalid-value borders.

The wrapper records the actual IHU boot ID, a bridge session ID, payload boot
ID and transport provenance. Firmware fields describe the actual responding
Pi build. A native command is accepted only after the IHU submits its CAN
request, and completed only after a correlated, validated application reply.
Use per-command history for outcomes. A timeout after dispatch stays unknown;
there is no automatic operation retry. Duplicate suppression is bounded to
64 transactions in memory and does not survive bridge restarts. Do not replay
old command datagrams after reconnect/restart. Only an explicit target-switch
busy refusal before dispatch is retried for up to three seconds.

## Deployment

Preserve dirty checkouts. The tested station's working source was actually
`/home/ngrabbs/work/MSU_Cubesat/ember`, with newer deployed UHF definitions
than that source; running legacy `prepare.py` would overwrite them. Use a
separate clean checkout/export for these scripts. Back up the active runtime,
Compose configuration and environment before deployment. The tested backup is
`/home/ngrabbs/work/deploy-backups/payload-20261017/yamcs-before.tgz` on .251.

1. On the ground host, run `python3 ground/yamcs/prepare_payload.py --runtime
   /path/to/active/.runtime/quickstart`. This adds an isolated Java package,
   MDB and instance and preserves the existing instances/classes. It needs an
   existing ember or ember-uhf instance template.
2. Add `ground/yamcs/compose.payload.yaml` to the existing Compose overlays.
   It exposes UDP 10020 at `EMBER_HTTP_BIND`. Compile the runtime using the
   existing Maven container, then recreate only the Yamcs service. Verify all
   existing instances are RUNNING alongside `ember-payload`.
3. On m75q, install `ground/ember` under `/opt/ember-payload-ground/ember`,
   install the system pyserial package and install/enable
   `ground/yamcs/ember-payload-bridge.service`. Adjust the stable IHU serial
   path if different. It binds .252:10028 and accepts only .251 source IP.
   This is a trusted bench LAN service, not an authenticated command endpoint.
4. Run `python3 ground/yamcs/install_payload_displays.py --url
   http://192.168.1.251:8090`. Only payload files and namespaced script copies
   are uploaded; existing displays/scripts are preserved.
5. Run `python3 ground/yamcs/build_identity.py --url
   http://192.168.1.251:8090 --instance ember-payload --release 1.3.0 --payload
   --publish --output ground/releases/yamcs-payload-1.3.0.json`.
   `Payload-Ground-Build.opi` and `payload-ground-build.json` are separate
   from the existing UHF release audit. The fingerprint covers the loaded
   payload MDB and shared display bucket. Use `--check` against that manifest
   to detect later drift.

The bridge exclusively owns the IHU USB console. Stop it with
`sudo systemctl stop ember-payload-bridge` before manual console work; it
attempts to select COMMS before releasing ownership. Restart afterward.
Stopping the bridge is enough to disable this command route. To roll back
Yamcs, remove the added Compose overlay and restore the backed-up runtime
while Yamcs is stopped; retain its persistent data volume.

## Validation

`tests/ground/test_payload_ground.py` exercises correlation, duplicate
suppression, invalid input, unknown outcomes, target-selection refusal and
isolated/idempotent generation. The full ground suite ran 59 tests, one
skipped. Maven compiled all new classes. Live Yamcs history confirmed all
four commands completed, including 32- and 240-byte pings; 241 bytes was
rejected. The dashboard and its command navigation were inspected in the
browser. See `ground/releases/payload-live-validation.json` and the 1.3.0
manifest for recorded deployment evidence. IHU is 0.11.0, Pi payload is
0.1.0 and the bench bridge is 0.1.0; deployed firmware build identities retain
their recorded base commit and dirty flag from the hardware validation build.
