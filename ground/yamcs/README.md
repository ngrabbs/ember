# Yamcs ground lab

[Ground station checklist](../../system/ground_station/TODO.md) · [Ground software](../README.md)

Two isolated Yamcs instances run together: `myproject` keeps the pinned
upstream demonstration and its archive; `ember` uses the
[bench dictionary](../ember/README.md) and an executable simulated endpoint.
The default configuration uses software only; the USB override connects
EMBER to the dedicated Pico bench endpoint. EMBER returns correlated acceptance,
rejection and completion reports; the upstream sample only counts commands.

## Start

Requires Git, Python 3, Docker Engine and Docker Compose. The Maven/Java and
simulator runtimes are containerized. Run from this folder:

```sh
python3 prepare.py
docker compose up -d
docker compose ps
docker compose logs --tail 30 yamcs simulator
```

First startup downloads Java/Maven dependencies and compiles Yamcs; allow several
minutes. The simulator waits for Yamcs readiness before sending packets. Source is pinned to
[upstream quickstart commit 61e9416](https://github.com/yamcs/quickstart/tree/61e94169687f8729832c754e0813bf90271e4800),
which selects Yamcs 5.13.0. Container tags are fixed here, but image digests have
not yet been locked. Both images run natively on the ARM64 Pi 5; see the
[lab inventory](../../system/ground_station/lab_inventory.md).

`prepare.py` generates `ember.xml` and Java field offsets from the JSON
dictionary, copies the tracked Java link adapters into the ignored source
clone, and adds the `ember` instance. After changing dictionary/adapters, rerun
`prepare.py` and `docker compose restart yamcs`; restart `ember-simulator`
after changing its code. No archive volume is removed during an update.

It also prepares the isolated `ember-lte` instance, sharing the dictionary and
display bucket while keeping its archive/processor separate. Only `eps-lte-in`
UDP10018 is configured there, without a TC data link. The USB Compose override
publishes this port on loopback. `ground/ember/lte_receiver.py` accepts native
POWER_STATUS packets at EPC UDP51000 from Walter172.16.0.2:51001, verifies the
wire/provenance, and forwards the original bytes. The
[LTE EPS display](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-lte__realtime)
remains empty until actual radio packets arrive; existing `ember` USB/Pi wrappers
cannot populate it. Receiver capture and byte-matched Yamcs archive checks are
required before claiming full LTE delivery.

Default HTTP access is `http://localhost:8090`. For a remote host, tunnel from
the laptop, substituting its username and address:

```sh
ssh -N -L 8090:127.0.0.1:8090 ngrabbs@192.168.1.252
```

For direct browser access on the trusted bench LAN, select the host's LAN address:

```sh
EMBER_HTTP_BIND=192.168.1.252 docker compose up -d
```

The starter has no operator authentication configured. Keep it on the bench
network; production operator access is a separate setup task. In simulator mode only HTTP is
published; both UDP directions remain inside the isolated Docker network.

## EMBER displays

[The operator overview](http://192.168.1.251:8090/telemetry/displays/files/Overview.opi?c=ember__realtime)
shows received state, counters, heartbeat time and latest command report.
[Display setup and interpretation](DISPLAYS.md) covers installation, native
detail tables and the distinction between cached values and live connectivity.

## Smoke check

For EMBER, open [the Pi command console](http://192.168.1.251:8090/commanding/send?c=ember__realtime&system=%2Fember).
Select `SET_PARAMETER`, show arguments with defaults, set `parameter_id=1`
and `value=2000` (ms), and Send. The report separates Yamcs Sent from
EMBER_Acceptance and Completion. Inspect `ember-outcome`, transaction identity
and result boot ID. Requested telemetry and results echo the same transaction;
periodic telemetry uses transaction zero. `Resend this command` allocates a
new transaction; an identity-preserving retry is not yet exposed in the UI.

The automated check verifies accepted/completed 1000→2000 ms changes using
actual archived heartbeat uptime deltas, all four commands, correlated query
data and invalid-argument rejection. It restores the original period. The
optional fault test suppresses one transaction's returned packets and checks
TIMEOUT with `ember-outcome=UNKNOWN`, without automatic retries:

```sh
python3 ember_smoke.py --url http://192.168.1.251:8090 --fault-test
```

Run `--fault-test` on the Docker host. Its loopback-only control socket lives
inside `ember-simulator` and is never published. All ordinary command and
telemetry UDP remains on the private Compose network (10026 and 10016).
Acceptance timeout is 5 s; terminal timeout after acceptance is 10 s.
Outstanding correlation is bounded to 256 commands and held in memory;
reconciliation after a Yamcs restart and late-result handling remain open.
The simulator's last-64 transaction cache prevents duplicate execution during
a boot; changed contents with the same identity are rejected. A simulator
restart changes boot ID and restores the default 1000 ms period.

### Upstream reference check

Open the `myproject` instance and `realtime` processor. Confirm inbound link
counts grow, packets decode, and parameters update. Issue the example
`SwitchVoltageOn` with `Battery=1`; check outbound count and the simulator's
received-command count. View packet archive and command history. Sample data
is prerecorded, but the upstream preprocessor assigns the current Yamcs-local
generation time because these packets have no time secondary header. This does
not validate spacecraft time decoding or synchronization.

```sh
python3 smoke.py
curl -fsS http://localhost:8090/api/links/myproject
docker compose logs --tail 5 simulator
```

## Stop and retain data

For a portable, bounded housekeeping session with local decoded replay, use
the [record/replay procedure](../../system/ground_station/telemetry_sessions.md).
It exports raw packets and original metadata from this archive without changing
the running services. Offline replay is separate from the live Yamcs processor.

```sh
docker compose stop
docker compose start
```

`docker compose down` also preserves named volumes. Do not use `down -v` unless
deliberately deleting the lab archive. Data is in the `yamcs-data` named volume
at `/yamcs-data`, outside Maven build outputs. An installation-specific signing
key is generated once in the ignored starter configuration. Preserve that
configuration with the archive when migrating an existing installation.

`smoke.py` checks growing receive counts, packet archive retrieval, and sample
command delivery using the simulator’s receive counter. Run it on the Docker
host; use `--url http://HOST:8090` when bound to a specific LAN address.

The upstream simulator replays a finite sample and does not loop. It is not
a service for long-term operation; restart it for another smoke session. Pi
archive retention/backup remain on the checklist. The EMBER simulator continues
publishing independently of the finite upstream sample.

## Pi boot startup

The supplied systemd unit assumes user `ngrabbs`, Docker group membership, and
checkout `/home/ngrabbs/work/MSU_Cubesat/ember`. Adjust those paths for a different
host. It starts Compose after Docker and network readiness and stops the lab
cleanly at shutdown. Container restart policies also recover exited processes.

```sh
sudo install -m 0644 ember-ground-starter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ember-ground-starter
systemctl status ember-ground-starter
```

Use `sudo systemctl stop ember-ground-starter` to stop the whole lab intentionally.
Its `active (exited)` state means Compose startup finished; inspect container
health and run the smoke check to verify the application itself.

## Pi USB transport

The deployed Pi selects USB in ignored `.env`:

```dotenv
EMBER_HTTP_BIND=192.168.1.251
EMBER_PACKET_TRANSPORT=usb
COMPOSE_FILE=compose.yaml:compose.usb.yaml
```

Install `python3-serial` and `picotool` on the Pi. Create ignored `.usb.env`
with the actual device identity and Docker bridge gateway:

```dotenv
EMBER_USB_DEVICE=/dev/serial/by-id/usb-Raspberry_Pi_Pico_E663682593753535-if00
EMBER_USB_BIND=172.17.0.1
```

Verify the gateway locally (`docker network inspect bridge`); it can differ
on another host. `prepare.py` reads the selected transport from `.env` or
`--transport usb`. Then:

```sh
python3 prepare.py --transport usb
docker compose stop ember-simulator
docker compose up -d
sudo install -m 0644 ember-usb-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ember-usb-bridge
python3 ember_smoke.py --url http://192.168.1.251:8090 --transport usb --fault-test
```

The service assumes the same checkout/user as the starter and `dialout`
membership. USB override keeps the EMBER simulator inactive and preserves
`myproject`. TM UDP10016 is published only on host loopback; TC UDP10026 binds
the Docker host gateway. Loopback UDP10027 is local fault injection for the
smoke check. The bridge runs on the host; no USB device is mounted into Docker.
The starter reads `COMPOSE_FILE` at boot and the bridge reconnects the same
Pico identity after re-enumeration, without queuing commands for replay.

To stop the entire hardware lab, stop `ember-usb-bridge` before
`ember-ground-starter`. To return to the software reference, stop the bridge,
remove `COMPOSE_FILE` from `.env`, set `EMBER_PACKET_TRANSPORT=simulator`, run
`python3 prepare.py --transport simulator` and `docker compose up -d`. Both
configurations retain the existing archives. Use the matching `--transport`
for `ember_smoke.py`.
