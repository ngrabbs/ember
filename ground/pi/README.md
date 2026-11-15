# Pi power-on readiness


Current operation: one container with **`ember`** for LTE/UHF reception and
**`ember-bench`** for the IHU serial EPS/payload path. Use the
[environment guide](../yamcs/OPERATIONAL.md) for active setup; older reference procedures below may describe retired services.
The provisioned Pi 5 (`ember-ground`) starts Yamcs without a laptop terminal.
It prefers connected Ethernet and supplies a fallback Wi-Fi access point.
This layer preserves the installed Yamcs runtime, MDB and archive volumes.

| Connection | Open Yamcs | SSH |
|---|---|---|
| Existing lab Ethernet | `http://192.168.1.251:8090` | `ngrabbs@192.168.1.251` |
| Wi-Fi `EMBER-Ground` | `http://192.168.50.1:8090` | `ngrabbs@192.168.50.1` |

The hotspot password is stored privately on the deployed Pi at
`/home/ngrabbs/.ember-hotspot-password`; it is not committed here. SSH still
uses the existing authorized keys. The hotspot supplies DHCP and works
without Internet. The radio country is US; installation elsewhere must set
the appropriate country. Yamcs binds HTTP to all Pi IPv4 interfaces so both
addresses work. Yamcs telemetry ports UDP10018–10020 are bound to Pi loopback. The direct IHU
USB bridge starts only for the registered console. See the
[serial setup](../yamcs/OPERATIONAL.md#serial-ownership-and-eps).

Use the [demo checklist](../DEMO.md) to connect, select a receiver, and
verify a packet.

## What runs automatically

- `ember-ground-starter`: enabled at boot; launches the existing Compose lab.
  Yamcs has Docker `restart: always` and starts Maven offline using the Pi's
  existing dependency cache. This requires the lab to be provisioned first.
- `ember-ground-readiness`: reconciles every five seconds. If `eth0` has carrier
  and NetworkManager reports connected, it keeps the hotspot off. Otherwise
  it activates `ember-ground-hotspot`. This checks the physical/local connection,
  not Internet reachability. Connecting Ethernet again turns the hotspot off.
- The same supervisor starts `ember-lte-listener` when USB `2500:0020` is present
  (LibreSDR's current B210 identity), stops it when absent and retries failures.
  The ID also matches a genuine B210; update detection if using a different SDR.
- Docker restarts Yamcs after process exits. Every minute the supervisor checks
  Docker's existing health status and restarts an unhealthy Yamcs container.
  The existing healthcheck allows several minutes for initial startup.
- The listener filters peer, schema, CRC and native EPS provenance. Deduplication
  memory is bounded and expires after two minutes; it resets on service restart.
  Private packet logs rotate at 10 MB with three backups (about 40 MB total).

## Status and recovery — Pi SSH shell

```sh
# PI SHELL: confirm enabled boot services and currently running receiver.
systemctl is-enabled ember-ground-starter ember-ground-readiness
systemctl status ember-ground-starter ember-ground-readiness ember-lte-listener

# PI SHELL: see access point / Ethernet state and recent operational messages.
nmcli device status
journalctl -u ember-ground-readiness -u ember-lte-listener -n 30 --no-pager

# PI SHELL: check the live LTE instance, not an old display value.
curl -fsS http://127.0.0.1:8090/api/instances/ember

# PI SHELL: see private received packet captures; Yamcs archives are separate.
sudo tail -n 1 /var/lib/ember-lte-listener/packets.jsonl
```

`ember-ground-starter` normally says `active (exited)` because Compose keeps the
containers running. Inspect `docker ps` for Yamcs health. A freshly received
one-shot EPS value expires soon afterward; use its timestamp/history.

For a manual bounded listener trial, first stop supervision so it cannot restart
the persistent listener while you own UDP 51000:

```sh
# PI SHELL: temporarily hand UDP 51000 to the manual trial receiver.
sudo systemctl stop ember-ground-readiness ember-lte-listener

# Run the bounded receiver and LTE trial, then restore supervision:
sudo systemctl start ember-ground-readiness
```

Stopping the supervisor leaves the current hotspot state in place. Starting it
restores the Ethernet-first policy and attached-SDR listener within one cycle.

## Install on this already provisioned Pi

Install packages `dnsmasq-base` and `iw` if missing. Keep the private hotspot
password in a file readable only by its owner; never add it to the repository.
Run on the Pi from this checkout:

```sh
# PI SHELL: deploy only startup/networking assets; preserve the existing runtime.
sudo python3 ground/pi/install.py \
  --repo /home/ngrabbs/work/MSU_Cubesat/ember \
  --hotspot-password-file /home/ngrabbs/.ember-hotspot-password --country US
```

The installer backs up NetworkManager profiles and the Yamcs `.env` under
`/var/backups/ember-ground/<UTC timestamp>`, installs scripts at `/opt/ember-ground`,
adds a systemd starter drop-in, and appends a boot Compose override to the
existing `COMPOSE_FILE`. It temporarily restarts the lab to apply HTTP binding.
It leaves the existing static Ethernet profile and authorized SSH keys intact.
It enables Wi-Fi and sets its regulatory country. It does not flash boards.

For rollback, stop/disable `ember-ground-readiness`, stop `ember-lte-listener`,
bring `ember-ground-hotspot` down and delete that profile. Restore the **pre-install**
Yamcs `.env` backup, remove the starter's `readiness.conf` drop-in, run
`sudo systemctl daemon-reload`, and restart `ember-ground-starter`.
Do not restore old network profiles over newer unrelated network changes.

After changes, follow the [ground demo checklist](../DEMO.md) to verify
Ethernet or hotspot access, Yamcs links, and a fresh packet. Verify cold boot
and USB reconnect when changing startup supervision.

## Provision a new Pi

Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager. The current
Debian 13 Trixie image supports Pi 4 and Pi 5. Use a Pi 5 with at least 4 GB RAM
and cooling if available; Pi 4 is suitable for initial software tests. Radio
performance and the complete service memory budget still need benchmarking.

In Imager, select the exact board model and storage device, then configure:

- Hostname: `ember-ground`.
- A normal user, preferably the same username used for SSH elsewhere.
- SSH enabled, using the laptop's public key if available.
- Local time zone and Wi-Fi credentials if Ethernet is unavailable.

Use an appropriate supply and a reliable microSD card (32 GB or larger is a
practical start); SSD storage can follow for the telemetry archive. Connect
Ethernet and leave SDR/Pico hardware disconnected for this first milestone.

After first boot, from the laptop:

```sh
ssh YOUR_USER@ember-ground.local
uname -m
free -h
cat /etc/os-release
df -h /
```

Expect `aarch64`. Record model, RAM, username and IP in the lab inventory before
installing services. Run normal OS updates, then install Git, Python 3 and Docker
Engine with its Compose plugin using the
[official Debian repository instructions](https://docs.docker.com/engine/install/debian/).
The installed Pi passed native ARM64 image and starter checks.

Use the [Yamcs deployment guide](../yamcs/OPERATIONAL.md) for the shared station.
For the isolated software-only starter, see the [lab reference](../yamcs/HISTORY.md).

[official OS images](https://www.raspberrypi.com/software/operating-systems/),
[Imager/first-boot guide](https://www.raspberrypi.com/documentation/computers/getting-started.html).
