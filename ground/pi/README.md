# Pi power-on readiness


Current operation: one container with **`ember`** for LTE/UHF reception and
**`ember-bench`** for the IHU serial EPS/payload path. Use the
[environment guide](../yamcs/OPERATIONAL.md) for active setup; older reference procedures below may describe retired services.
The provisioned Pi 5 (`ember-ground`) starts Yamcs without a laptop terminal.
It prefers connected Ethernet and supplies a fallback demo Wi-Fi access point.
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
addresses work. Radio telemetry ports are loopback-bound; the bench bridge uses LAN UDP10020.

## Power up and use it

1. Connect the Pi's normal power supply and LibreSDR USB cable.
2. With connected Ethernet, browse the existing lab address. Without connected
   Ethernet, join `EMBER-Ground` and browse the hotspot address above.
3. Allow about a minute for Yamcs to initialize. Select `ember` / `realtime`
   for radio dashboards, or `ember-bench` / `realtime` for IHU serial EPS/payload. The LTE packet listener is already running when
   LibreSDR is present; do not open a second receiver on UDP 51000.
4. Start the bounded LTE cell and the IHU/Walter RF window using the established
   [LTE walkthrough](../../docs/user/lte-eps-walkthrough.md).

The receiver accepts native IHU POWER_STATUS, HEARTBEAT and SYSTEM_STATUS packets from Walter
`172.16.0.2:51001` at UDP 51000 and forwards unchanged bytes to Yamcs UDP 10018.
It does not configure LibreSDR, start EPC/eNodeB, register Walter or transmit RF.
Those actions retain their separate bounded trial controls. A plugged-in SDR
therefore means **ready to receive**, not an active LTE link.

## What runs automatically

- `ember-ground-starter`: enabled at boot; launches the existing Compose lab.
  Yamcs has Docker `restart: always` and starts Maven offline using the Pi's
  existing dependency cache. This requires the lab to be provisioned first.
- `ember-ground-readiness`: reconciles every five seconds. If `eth0` has carrier
  and NetworkManager reports connected, it keeps the hotspot off. Otherwise
  it activates `ember-demo-hotspot`. This checks the physical/local connection,
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

# Run the bounded receiver and trial from the LTE walkthrough, then restore:
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
bring `ember-demo-hotspot` down and delete that profile. Restore the **pre-install**
Yamcs `.env` backup, remove the starter's `readiness.conf` drop-in, run
`sudo systemctl daemon-reload`, and restart `ember-ground-starter`.
Do not restore old network profiles over newer unrelated network changes.

## Verification

Installed and verified on October 8, 2026: the user confirmed hotspot
authentication, DHCP and Yamcs browser access. Automatic Ethernet fallback
and return, listener crash recovery, and a full Pi reboot passed. After reboot,
Yamcs was healthy, the attached-SDR listener was active, and the earlier LTE
packet remained in the archive. See the [verification record](../../system/ground_station/evidence/pi-readiness-20261008.json).

Run `python3 -m unittest discover -s tests/ground -p test_pi_readiness.py -v`
from the repository. These checks use host loopback sockets, never RF, and
verify continued delivery, exact bytes, peer/CRC filtering and duplicates.
On the deployed Pi also verify hotspot AP/DHCP, client access, Ethernet return,
listener crash recovery, and a full reboot. Physical USB unplug/replug and a
cold boot with Ethernet absent are useful final demo checks.

NetworkManager's [shared IPv4 mode](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-settings-nmcli.html)
provides hotspot addressing/DHCP; the supervisor controls when that profile runs.

## Provision a new Pi

The installed Pi and verified settings are in the [lab inventory](../history/2026-10-01/lab_inventory.md).

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
