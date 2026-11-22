# EMBER flight and bench environments

One Docker container runs two Yamcs instances at [the Pi](http://192.168.1.251:8090).
Choose the environment, then stay in its `realtime` processor. Both use the same
`/ember` packet namespace and dictionary source; archives, current values,
command history and display buckets are independent.

| Instance | Purpose | Links | Displays |
|---|---|---|---|
| `ember` | Radio reception and UHF commands | `lte-tm-in` UDP10018; `uhf-tm-in` UDP10019; UHF TC UDP10029 | `ember_displays` |
| `ember-bench` | One physical IHU serial connection | `ihu-serial-in` UDP10020; `ihu-serial-out` to the Pi host on UDP10028 | `ember_bench_displays` |

See the [operator guide](README.md) for displays and commands.
The retired `grabbs-ground` application belongs on its own host. The operational
preparer removes its instance entry and injected timeline header from this server.

## IHU-requested UHF telemetry

Follow the instructions for the installed [transceiver build](../../firmware/transceiver/README.md#commands).
Verify a fresh `uhf-tm-in` packet using the [demo checklist](../DEMO.md#3-verify-a-fresh-packet).

## Serial ownership and EPS

Plug the IHU console directly into the Pi. A udev rule matches the registered
USB serial number and starts `ember-bench-bridge@ttyACM0.service` (use the
actual tty name). It owns the console, enables the two Yamcs bench links, and
polls `eps json` every five seconds when `umb_telem` is enabled. Ground wrappers
retain provenance 1 and a bridge-session boot identity. Current readings use
provisional 10 mΩ sense values and report `sense_values_verified=false`.

Unplugging the console stops the service and disables both bench links. To
use the console manually on the Pi, stop the service first, close the manual
serial program when finished, then start the service again.

```sh
sudo systemctl stop ember-bench-bridge@ttyACM0
sudo systemctl start ember-bench-bridge@ttyACM0
journalctl -u ember-bench-bridge@ttyACM0 -n 30 --no-pager
```

Enable `output umb_telem on` on the IHU when you want periodic EPS forwarding.
For payload results, see the [operator guide](README.md#commands-and-results).

Within each instance, exact CRC-valid duplicates are suppressed for 120 seconds,
with a 4096-entry bound. Flight LTE/UHF copies therefore share one archive entry;
the same bytes may independently appear in the bench archive. Suppression resets
with Yamcs. Link counters still count arrivals. Use packet receive times and readout validity to check liveness.

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
3. Set `COMPOSE_FILE` in the Pi's Yamcs `.env` to the base file, boot
   overlay, and operational overlay, in that order. The deployed Pi uses:

   ```dotenv
   EMBER_HTTP_BIND=0.0.0.0
   COMPOSE_FILE=compose.yaml:/opt/ember-ground/compose.boot.yaml:/home/ngrabbs/work/ember-environments-20261017/ground/yamcs/compose.operational.yaml
   ```

   Follow the [LAN and Tailscale setup](../pi/README.md#yamcs-over-lan-and-tailscale)
   before starting Docker. Tailscale peers access the published HTTP port directly.
   The operational overlay keeps HTTP on Ethernet and the hotspot and
   publishes telemetry UDP10018–10020 on loopback. The serial command link
   resolves `ember-ground-host` through Docker's host gateway.
4. Keep the Pi's old `ember-usb-bridge` and `ember-eps-bridge` disabled.
   Start Yamcs with `ember-ground-starter`, then resume readiness supervision.
5. On the Pi, install pyserial if needed and register the serial number from
   `udevadm info -q property -n /dev/ttyACM0` (`ID_SERIAL_SHORT`).

   ```sh
   sudo sh ground/pi/install_bench_bridge.sh IHU_USB_SERIAL
   ```

   The installer uses Docker's default bridge gateway and the Yamcs Compose
   network. Pass the network name as the second argument if it differs from
   `ember-ground-starter_default`. Rerun it if the network changes. Verify both
   instances are running and the two bench links follow the USB connection.
6. Run `python3 ground/yamcs/install_displays.py --url http://PI:8090` to install
   both buckets. It backs up replaced objects and verifies uploaded bytes; named old
   duplicate pages are retired only after backup. To restore a display, upload
   its saved object to the original bucket and path. Backups live under
   `ground/yamcs/.runtime/display-backups/TIMESTAMP/INSTANCE/`.
   Audit each separately with `build_identity.py --instance ember` and
   `--instance ember-bench`, using explicit new release/output/publish arguments.

Yamcs starts at boot. The serial bench service starts when the registered IHU is present. Existing Ethernet-first
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

To roll back, pause readiness, stop Yamcs and the active bench bridge unit, restore the
saved runtime/Compose environment and previous bridge service, then restart.
Keep the live data volume to retain new records. Restore old data backups to
separate recovery volumes rather than overwriting post-migration history.

## Validation

The ground unit suite covers both MDBs, idempotent preparation, command routing,
shared serial polling and disconnect recovery. `operational_check.py` runs only
against a separate loopback validation server on HTTP8091 with TM11018/11019/
11020 and mock TC11028/11029. It verifies radio deduplication, independent bench
archives, bad-CRC rejection, payload status completion over both command routes,
and cross-instance reply isolation. Never inject its synthetic packets into production.

Physical RF requalification remains separate from configuration and serial tests.
