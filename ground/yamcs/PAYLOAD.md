# Payload ground support 1.3.0

The `ember-bench` instance provides a payload dashboard, parameter table,
command history and four commands. The first implementation uses a LAN bench
route: Yamcs (.251) → UDP → m75q (.252) → IHU USB console → CAN A (500 kbit/s)
→ Pi payload (.253). This is not the transceiver's RF uplink/downlink. Camera
and image functions are outside this release.

Open `http://192.168.1.251:8090/telemetry/displays/files/Payload.opi?c=ember-bench__realtime`.
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

Use [operational preparation](OPERATIONAL.md) for the two environments and displays.
The m75q service is now `ember-bench-bridge`, installed under `/opt/ember-bench/ember`.
It owns the same IHU serial port, accepts commands on UDP10028 and sends telemetry
to Pi UDP10020. It also polls observational EPS JSON every five seconds between
commands. Stop this service before manual IHU console access, then restart it.
The retired `ember-payload-bridge` must remain disabled to avoid two serial owners.

Only the four `PAYLOAD_*` commands are routed here. The flight `ember` instance
has no command definitions or uplink. Its payload dashboard can show radio
observations when available, but cannot issue a bench command. The original
payload 1.3.0 manifest below remains historical; audit the current bench with
`build_identity.py --instance ember-bench`. Bridge version is now 0.2.0.

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
