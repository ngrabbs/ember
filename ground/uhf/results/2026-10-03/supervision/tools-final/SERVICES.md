# Optional UHF application supervision

The installed services explicitly start the existing bench applications. They
are disabled at boot, do not arm the IHU timer, and never retry a radio fault.
AMSAT's UHD/FPGA/boot image, RF routing and transponder demonstration are unchanged.
This remains a bench integration, not a production spacecraft scheduler.

## Installed profiles

| Host | Service | Application/config |
| --- | --- | --- |
| SDRB, via m75q USB console | `ember-uhf-sdrb.service` | `/home/petalinux/ember-uhf-20261003/sdrb.json` |
| Ground Pi `192.168.1.251` | `ember-uhf-ground.service` | `/home/ngrabbs/work/ember-uhf-20261003/ground.json` |

Unit sources and JSON profiles are in [services](services). They are installed
under each account's `~/.config/systemd/user`; changing the installation paths
requires updating both the JSON and unit. Keep the existing custom LibreSDR FPGA
and the SDRB native mixer module. LTE must release LibreSDR before UHF starts.

On the Pi, `sudo loginctl enable-linger ngrabbs` was applied so the user manager
survives SSH logout. This does not enable the UHF service. Check with
`loginctl show-user ngrabbs -p Linger`; undo with
`sudo loginctl disable-linger ngrabbs` after stopping UHF if desired.
SDRB's account has lingering disabled; its logged-in serial console keeps the
user session active. Closing the serial reader leaves that shell logged in;
logging out of the shell can stop its user services. Do not rely on RF surviving
SDRB logout or reboot. No SDRB login/startup policy was changed.

## Start, arm, observe, stop

1. Keep the IHU timer off (`telem off`) while preparing the radios. Check CAN is
   normal at 500 kbit/s and the existing HELLO peer is valid; LTE queue must be off.
   Check that the correct RF antennas/path are fitted and no other process owns
   either radio or console. This installed profile forwards HT 435.1 MHz to
   434.2 MHz and inserts telemetry at 434.1 MHz.
2. Start ground reception:

   ```sh
   ssh ngrabbs@192.168.1.251 'systemctl --user start ember-uhf-ground.service'
   ssh ngrabbs@192.168.1.251 'python3 ~/work/ember-uhf-20261003/supervisor.py status --config ~/work/ember-uhf-20261003/ground.json'
   ```

3. In the SDRB Linux console, check `ip -details link show can1`. If its existing
   500 kbit/s configuration is correct, bring it up and start the optional apps:

   ```sh
   sudo ip link set can1 up
   systemctl --user start ember-uhf-sdrb.service
   python3 ~/ember-uhf-20261003/supervisor.py status --config ~/ember-uhf-20261003/sdrb.json
   ```

   Both supervisor reports must reach `RUNNING`. A successful `systemctl start`
   alone is not a readiness or packet-delivery check. CAN reader and forwarder
   initialize before RF starts; they ignore old CAN records. No CAN application
   replies are enabled. The supervisor never configures or takes CAN down.
4. In the IHU console, use `telem on 20`. The MCU now schedules fresh EPS reads
   every 20 seconds; USB does not trigger each packet. Observe the ground run's
   `receiver/packets.jsonl` and new Yamcs `ember-uhf` archive arrivals. Use the
   [realtime EPS display](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-uhf__realtime);
   the old paused proof processor will not advance.
5. Stop the IHU timer first (`telem off`), then stop the services:

   ```sh
   # SDRB console
   systemctl --user stop ember-uhf-sdrb.service
   # Ground host
   systemctl --user stop ember-uhf-ground.service
   ```

   Check supervisor `STOPPED`, all child return codes, radio release and any
   errors. RF stops before the forwarder/CAN reader. Leave CAN configuration to
   the operator; take it down only after readers close if returning to the idle
   bench. A service fault does not disable the independent MCU timer, so send
   `telem off` explicitly. Diagnose the saved failed run before a manual restart.

`systemctl --user restart ...` is an explicit restart, never an automatic retry.
Do not run the detached CLI and unit for the same role simultaneously. A finite
CLI alternative is `supervisor.py start --config PROFILE --seconds 120`
(also `--transmit` for SDRB). Its lease begins after all local readiness gates;
startup has separate deadlines. `supervisor.py stop --config PROFILE` requests
graceful shutdown. A shared observer deadline across hosts remains separate.

## Ownership and evidence

Each role has one private owner lock/control socket and a fresh UUID run
directory. Any component exit, RX/TX error or decoder queue fault stops that
role without retry. Child processes receive SIGTERM if their supervisor dies;
systemd also owns descendants. A new manual start records stale-owner failure.
Software tests cover owner death, duplicate startup, component failure,
retention, storage quota and graceful stop.

Status: `~/.cache/ember-uhf-{sdrb,ground}/status.json`. Runs:
SDRB `~/ember-uhf-supervised`, Pi `~/work/ember-uhf-supervised`.
The current run is checked against 128 MiB once per second; exceeding the quota
fails/stops the role. Five completed marked runs plus the active run are retained.
Unmarked directories are preserved. Live ground reception saves no IQ and keeps
64 packet details in memory; packet JSONL and process logs remain complete until
quota shutdown. Export evidence before later starts prune old completed runs.

`RUNNING` means local processes passed readiness, not RF/Yamcs delivery. Check
decoded packet identities and archive reception times independently. The
[supervision evidence](results/2026-10-03/supervision) retains successful controls,
early logout shutdowns and a TX startup fault separately. Short checks do not
establish endurance, arbitrary restart reliability, SSB quality or flight use.
