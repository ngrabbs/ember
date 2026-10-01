# Yamcs starter lab

[Ground station checklist](../../system/ground_station/TODO.md) · [Ground software](../README.md)

Run the upstream Yamcs simulator to prove browser access, telemetry decoding,
archiving, and command transport before adding EMBER packets or radios. This
is an isolated software lab: its `myproject` dictionary and sample command names
are upstream examples, not the EMBER flight dictionary. Example commands only
increment the simulator's receive counter; they do not execute spacecraft actions
or return EMBER acceptance/completion reports.

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
network; production operator access is a separate setup task. Only HTTP is
published; both UDP directions remain inside the isolated Docker network.

## Smoke check

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

The simulator replays about one day of sample data and does not loop. It is not
a service for long-term operation; restart it for another smoke session. Pi
archive retention/backup and the EMBER MDB are still on the checklist.

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
