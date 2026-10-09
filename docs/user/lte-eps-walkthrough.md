# Send one EPS battery-voltage packet to Yamcs over LTE

[Operator guides](README.md) · [IHU command reference](ihu-can-console.md) · [LTE engineering runbook](../../ground/lte/BRINGUP.md)

This guide walks through the existing bench setup, from powered boards to one
fresh EPS observation in Yamcs. Reviewed against repository source and tested
end to end on October 8, 2026 (local time). It assumes the firmware, private SIM configuration, SDR
images and LTE binaries from the previous bench work are already installed.
It does not install or flash firmware. LTE delivery has been demonstrated,
but registration and delivery can still fail; stop at a failed checkpoint.

## Which device does what?

```text
EPS charger -- I2C --> IHU -- CAN --> COMMS -- UART --> Walter
                                                       |
                                                       | LTE-M radio / UDP
                                                       v
Laptop browser <-- Yamcs <-- packet receiver <-- EPC / LTE cell / LibreSDR
                              all on ember-ground
```

| Device | Your interface | Its job in this procedure |
|---|---|---|
| Ground Pi, `ember-ground`, `192.168.1.251` | Linux SSH terminals | Runs Yamcs, LTE packet receiver, EPC and SDR LTE cell |
| m75q, `192.168.1.252` | Linux SSH terminals | Opens USB text consoles for IHU and COMMS when their USB cables are connected here |
| COMMS CAN Feather, ID `DF637882D39E4426` | Its own USB text console | Participates in CAN and forwards IHU requests to Walter |
| IHU CAN Feather, ID `DF641455DB822427` | Its own USB text console | Reads EPS and constructs the native POWER_STATUS packet |
| Walter | Controlled through IHU → COMMS; no direct AT console needed | Registers on LTE and submits the packet to ground UDP |
| Laptop | Web browser | Shows the received battery voltage and packet timestamp |

The configured ground host is a **Pi 5**, not a Pi 4. If using another Pi,
these installed paths and services must first be provisioned there.

**Where to type:** `sh` blocks below belong in the named computer's Linux shell.
`text` blocks belong in the named MCU's USB console. MCU consoles do not accept
shell comments. Explanations are outside those blocks so you can copy the
literal command without producing `ERROR unknown command`.

## 1. Connect and power the bench

- Power EPS, IHU, COMMS and Walter. Connect the battery if you want to measure
  battery voltage. Keep the boards powered during USB console changes.
- Connect IHU and COMMS by their established CAN harness, including CANH,
  CANL and ground. Use the established bus termination and 500 kbit/s setup.
- Connect the established COMMS–Walter UART harness and Walter power.
- Connect LibreSDR to the ground Pi and retain the previously tested LTE
  antenna/bench arrangement. Starting the cell below transmits RF.
- Connect both Feather USB consoles to m75q, or use the computer where their
  cables actually terminate. USB here is the operator console, not the LTE path.
- EPS on this IHU image uses **I2C1: GP2 SDA, GP3 SCL, address 0x68**.
  The older FreeRTOS Pico GP4/GP5 wiring and `ihu>` console are different.

## 2. Start and check Yamcs — ground Pi shell

From the laptop, open a terminal and connect to the Pi:

```sh
# LAPTOP SHELL: connect to the configured ground Pi.
ssh ngrabbs@192.168.1.251
```

Now run on the Pi:

```sh
# PI SHELL: start the existing Yamcs lab service.
sudo systemctl start ember-ground-starter

# PI SHELL: inspect the actual containers, not just the systemd unit.
cd ~/work/MSU_Cubesat/ember/ground/yamcs
docker compose ps

# PI SHELL: verify the separate LTE instance exists and responds.
curl -fsS http://127.0.0.1:8090/api/instances/ember-lte
```

The service can show `active (exited)` because it launches Docker Compose and
then returns. The Yamcs container must be running. If containers are stopped,
run `docker compose up -d` from this same directory, then repeat the checks.
If `ember-lte` returns 404, stop here: the runtime needs the LTE configuration;
the ordinary `ember` instance is not a substitute.

Open the [LTE EPS dashboard](http://192.168.1.251:8090/telemetry/displays/files/EPS.opi?c=ember-lte__realtime)
on your laptop. Confirm **instance `ember-lte`, processor `realtime`**. A
purple header with Play/Pause controls indicates replay. Old or expired values
do not prove reception in this session.

## 3. Open two USB consoles — m75q shell

Use separate laptop terminals for COMMS and IHU. In each:

```sh
# LAPTOP SHELL: connect to the computer hosting the Feather USB cables.
ssh ngrabbs@192.168.1.252
```

On m75q, list the available devices:

```sh
# M75Q SHELL: find the stable USB paths for both boards.
ls -l /dev/serial/by-id/
```

Use the path containing COMMS ID `DF637882D39E4426` in the COMMS terminal:

```sh
# M75Q SHELL: replace COMMS_USB_PATH with the actual full device path.
python3 -m serial.tools.miniterm --eol LF -e COMMS_USB_PATH 115200
```

Use the path containing IHU ID `DF641455DB822427` in the IHU terminal:

```sh
# M75Q SHELL: replace IHU_USB_PATH with the actual full device path.
python3 -m serial.tools.miniterm --eol LF -e IHU_USB_PATH 115200
```

`--eol LF` sends a newline on Enter; `-e` shows what you type. Baud 115200 is
a terminal setting for USB CDC here. Exit miniterm with **Ctrl+]**.
After opening a console, press **Enter once with an empty line** before typing
the first command. This finishes any partial command left in the MCU input
buffer by a previous session; an error on that empty line can be ignored.
Then enter `status` and check its actual reply.
If a board is missing from the list, connect its USB cable and list again.
If its USB is attached to the Pi instead, open its console there using the
same command with that host's device path. One process must own each port;
close diagnostic helpers before opening miniterm.

## 4. Put COMMS in normal CAN mode — COMMS console

Enter **one line at a time**, waiting for the response before the next:

```text
status
```

Confirm `role=COMMS_MCU`. This identifies the board and prints controller
state/error counters. `mode=80` means configuration mode; it cannot participate
in normal CAN traffic. `mode=40` is local loopback; `mode=00` is normal.

```text
normal
```

This enables COMMS participation on the physical CAN bus and clears its
remembered peer. Expect `CAN_NORMAL ready=1`.

```text
status
```

**Checkpoint:** `role=COMMS_MCU`, `can_ready=1`, `mode=00` and `pending=0`.
Leave COMMS powered. Both Feather images boot in configuration mode, so this
step must be repeated on a board after its power cycle or reset.

## 5. Establish the IHU CAN peer — IHU console

Run these separately, waiting for each reply:

```text
status
```

Confirm `role=IHU_MCU`. If it says `pending=1`, wait for that transaction's
`RESULT` before changing transport state. Run `help` if the application identity
or supported commands differ from this guide.

```text
telem off
```

Stops future automatic EPS reads/submissions so this manual test has no
competing timer traffic. It does not cancel an already pending transaction.

```text
lte queue off
```

Disables FIFO processing during this manual test. It does not erase queued
packets or turn Walter RF off. Check the reply's queue count; queued packets
are not the fresh observation we are about to send.

```text
normal
```

Enables IHU CAN participation and clears its previous peer. Expect
`CAN_NORMAL ready=1`. COMMS must already be in normal mode.

```text
hello
```

Requests the peer handshake. `SUBMITTED` only means local submission: wait
for `RESULT ... outcome=CAN_HELLO_CONFIRMED`. Do not issue `lte` or EPS send
commands before this result. Normal mode or a later reset requires a fresh HELLO.

**Checkpoint:** HELLO confirmed. If you get `FRAME_TX_FAILED`, `TIMEOUT`,
`BUSY` or `HELLO_REQUIRED`, use the troubleshooting table below rather than
continuing to LTE.

## 6. Check the battery measurement — IHU console

```text
eps adc on
```

Forces charger telemetry conversion on, including battery-only operation.
This explicitly changes CONFIG_BITS bit 2 and verifies readback; it preserves
other bits and does not bypass the thermistor or change charging policy.
Expect `EPS_ADC outcome=VERIFIED requested=1`.

Wait **at least five seconds**, then:

```text
eps json
```

Reads all 19 LTC4162 registers with PEC checks. It does not send the observation
over LTE. A complete readout is required; `EPS_READ outcome=FAILED` is a stop.
Check `telemetry_status` bit 0 is set (typically value `1`).

For the installed LAD two-cell pack, raw `vbat` around 21000 corresponds to
about 8.1 V: **pack volts = signed raw vbat × 0.0001924 × 2**. It is an ADC word,
not millivolts. Raw `vbat=3` or `4` is approximately 1–1.5 mV and does not show
a connected 8 V battery. Check the battery connector and measure pack voltage
before proceeding with a battery-voltage demonstration. State `2048` means
battery detection; it is not the NTC-pause state (`32`).

**Checkpoint:** complete PEC readout, ADC valid and a plausible battery voltage.
Current conversions still assume unverified sense resistors; die temperature
is not measured battery temperature.

## 7. Start the LTE packet listener — another ground Pi shell

With the [Pi readiness services](../../ground/pi/README.md) installed, the
persistent listener starts automatically when LibreSDR is attached. Check
`systemctl is-active ember-lte-listener` on the Pi. If it reports `active`,
**skip the manual listener below** and continue to section 8. Monitor reception
with `journalctl -fu ember-lte-listener`; packet captures rotate in
`/var/lib/ember-lte-listener/packets.jsonl` and it does not exit after one packet.

For the optional bounded manual listener, first run on the Pi:

```sh
# PI SHELL: free UDP 51000 and suspend automatic receiver supervision.
sudo systemctl stop ember-ground-readiness ember-lte-listener
```

This leaves any current hotspot active. Restore supervision after the trial
with `sudo systemctl start ember-ground-readiness`.

Open another SSH terminal to the Pi. Run:

```sh
# PI SHELL: generate a unique capture name and restrict file permissions.
cd ~/work/MSU_Cubesat/ember/ground/ember
umask 077
eps_capture="$HOME/work/ember-lte/logs/manual-eps-$(date -u +%Y%m%dT%H%M%SZ).json"

# PI SHELL: receive one native IHU EPS packet, or stop after 180 seconds.
python3 lte_receiver.py --count 1 --seconds 180 --output "$eps_capture"

# PI SHELL: print the capture location after the listener finishes.
printf 'Capture saved to: %s\n' "$eps_capture"
```

Expect `LISTEN UDP 51000; expected Walter 172.16.0.2:51001`. Leave this terminal
open. The receiver checks source, packet CRC/schema and native-IHU provenance,
then forwards the unchanged packet to Yamcs's loopback UDP port 10018.
**It exits after one accepted packet** or its deadline. Restart it for another
test. This listener does not start the LTE cell or register Walter.

## 8. Start the LTE cell — another ground Pi shell

Start this only after the console checks above, so the finite RF window is not
used up troubleshooting CAN. Use the previously tested LibreSDR/RF arrangement:

```sh
# PI SHELL: unique label for private EPC/eNodeB logs.
lte_run="manual-eps-$(date -u +%Y%m%dT%H%M%SZ)"

# PI SHELL: start EPC and the transmitting LTE-M cell for a bounded trial.
python3 ~/work/ember-lte/run-radio-check.py "$lte_run" \
  --seconds 150 --config enb.band13.emtc.ce300tx20diag.conf
```

This launches srsEPC and OAI with the existing private configuration and custom
LibreSDR FPGA image. It **transmits RF**, not merely listens. Wait for
`ALL RUs ready`/steady-state output and S1 setup. If it exits with an assertion
or other startup failure, do not open the Walter window. Full logs are in
`~/work/ember-lte/logs`; keep subscriber-bearing logs private.

## 9. Register Walter and send one observation — IHU console

```text
lte 120
```

Requests a maximum 120-second Walter RF window through CAN and COMMS. Wait for
`RESULT ... outcome=RF_WINDOW_ACCEPTED`. This is window admission, not proof
of registration. Opening/configuring the modem can take tens of seconds.

```text
lte status
```

Wait for the matching result. Repeat this query every few seconds, never while
a prior request is pending. Proceed only when it reports **`state=6`
(READY), `registered=1`**, and sufficient `window_ms` remains. The send admission
requires at least 16000 ms remaining; leave extra time for the response and
cleanup. A historical socket-open flag or window acceptance is not readiness.

```text
eps lte
```

Reads EPS again, constructs one native 128-byte POWER_STATUS packet, then asks
COMMS/Walter to submit it to ground over LTE. This sends a **fresh observation**,
not the earlier `eps json` sample. Wait for its result, which can take up to
22 seconds. `RESULT ... outcome=MODEM_ACCEPTED` means modem submission only.
Do not automatically repeat a send whose outcome is UNKNOWN.

## 10. Confirm ground reception — Pi listener and laptop browser

For the automatic listener, look for a new `Forwarded POWER_STATUS` journal
entry and the current packet in its capture log. The `SUMMARY` below applies
only to the optional bounded manual listener.

In the listener terminal, expect a decoded packet followed by
`SUMMARY ... received: 1`, ideally with rejected/duplicate counts zero.
The shell prints the capture path after the receiver finishes. No packet means no demonstrated
ground delivery, even if the modem reported acceptance.

On the laptop's **`ember-lte` / `realtime` EPS display**, check:

- A new packet timestamp matching this session, not an old replay/cached value.
- Valid readout and ADC conversion. With the battery connected, check a
  plausible battery-pack voltage. With only bench input connected, inspect
  input voltage; near-zero battery voltage is expected for this setup.
- In **EPS raw / quality**, native IHU provenance and `bridge_session_id=0`.

One packet becomes stale soon after arrival because this is a one-shot send.
Use parameter history/plots or archive replay to inspect it afterward. The
listener capture records the packet bytes; a full engineering acceptance check
also compares those bytes to the Yamcs archive, as the previous trials did.

### Verified bench example: October 8, 2026

With the battery unplugged and EPS on bench power, Walter reached READY with
`registered=1` about 37 seconds after window admission. One `eps lte` command
produced POWER_STATUS sequence 2. The Pi received it from `172.16.0.2:51001`
with no rejected packets or duplicates, and Yamcs archived it through
`eps-lte-in` at **2026-10-09 00:40:39.225 UTC** (October 8 locally).
The IHU result, Pi capture and Yamcs archive contained identical 128-byte packets.
Yamcs decoded **input voltage 10.61 V** and **battery voltage 0.002 V**.
Walter was stopped and confirmed OFF afterward. This is a transport check,
not a battery charging test. A one-shot display value becomes EXPIRED shortly
after reception; its timestamp and parameter history distinguish it from no data.

## 11. Stop the session — IHU console, then Pi shells

After the send result completes, enter on IHU:

```text
lte 0
```

Requests Walter RF stop. Wait for its result, then:

```text
lte status
```

Confirm **`state=0`, `registered=0`, `window_ms=0`**. If this cannot be confirmed,
use the physical Walter power control rather than assume RF stopped.

If you explicitly enabled the ADC just for this battery-only test, after the
transport is idle you can restore ordinary ADC behavior with:

```text
eps adc off
```

Expect verified `requested=0`. Battery-only ADC measurements can then become
unavailable. Keep ADC on if further readouts are intended; this choice is
separate from LTE shutdown.

Let the bounded Pi cell runner finish. OAI timeout exit `124` and EPC timeout
exit `124` are expected; EPC's deadline is five seconds later. The wrapper's
own exit code is not enough—inspect both printed child exits. Confirm on Pi:

```sh
# PI SHELL: no LTE cell/core processes should remain after their deadlines.
pgrep -a -x lte-softmodem
pgrep -a -x srsepc
```

No output is expected. If processes remain, identify and stop them before
leaving the bench. The receiver also exits after its packet/deadline; Ctrl+C
can stop it early. Exit USB consoles with Ctrl+]. Yamcs can remain running
to retain and inspect the archive.

## Troubleshooting: stop at the first failed checkpoint

| Symptom | Meaning | Next action and device |
|---|---|---|
| `mode=80` | CAN controller in configuration mode | On **that board's USB console**, run `normal`, then `status`; verify `mode=00`. Do this on both boards. |
| `mode=40` | Local CAN loopback | On **that board**, run `normal`. Local `selftest` PASS does not prove the harness. |
| `CAN_TX ... FRAME_TX_FAILED` | A CAN fragment failed before peer handshake | Wait for IHU `RESULT`, then collect `status` on **both** boards. Check COMMS power/normal mode, CANH/CANL, common ground, established termination and matching bitrate. LTE cannot fix this. |
| `RESULT ... UNKNOWN ... TIMEOUT` | No matching reply within the deadline | Inspect both board statuses and physical path. Re-establish HELLO after correcting the fault; an unknown send is not proof of no delivery. |
| `REJECT reason=BUSY` | Earlier transport work still active | Wait for its result; check **IHU** `status` for `pending=0`. Do not paste a batch of commands. |
| `REJECT reason=HELLO_REQUIRED` | IHU has no established peer | Put **both** CAN boards in normal mode, then complete **IHU** `hello`. |
| `ERROR unknown command` | Unrecognized text, or a partial line left by the previous console session | Press Enter once on an empty line, then run `help` on that MCU. Enter literal lines without comments, prompts or leading/trailing spaces; source line limit is 39 characters. |
| EPS read failed or ADC invalid | No usable current measurement | Check **IHU–EPS** power/I2C/PEC path; if ADC is off, explicitly enable and verify it, then wait for conversion. |
| ADC valid but `vbat=3–4` | Charger reports approximately zero battery voltage | Check **battery connector and measured pack voltage**. Input power alone does not demonstrate battery sensing. |
| RF accepted but LTE not READY/registered | Modem window admitted but usable bearer not established | Wait within the bound; inspect **Pi** cell output and **IHU** `lte status`. Stop with `lte 0` if it does not become ready. |
| `MODEM_ACCEPTED`, receiver got nothing | Ground delivery unproven | Check **Pi** listener is still running, correct cell/profile and peer address. Inspect capture/logs; do not relabel modem acceptance as reception. |
| Receiver got packet, LTE dashboard did not update | Ground forwarding/Yamcs path needs checking | Verify **Pi** Yamcs container and loopback UDP10018 mapping, then laptop context `ember-lte__realtime`. |

The `telem on 20` timer and `eps telemetry` are different paths: they submit
native telemetry through the normal CAN chain; they do not automatically open
an LTE window or replace the explicit `eps lte` procedure above.

## References and evidence limits

- [IHU/COMMS console command reference](ihu-can-console.md)
- [Yamcs operation](yamcs.md) and [runtime setup](../../ground/yamcs/README.md)
- [LTE receiver implementation](../../ground/ember/lte_receiver.py)
- [Bounded cell runner](../../ground/lte/scripts/run-radio-check.py)
- [Prior native EPS reliability results](../../ground/lte/results/2026-10-02-eps-security-reliability.md)

This document was checked against source and existing recorded trials. Writing
it did not start RF, issue MCU commands or prove a new complete hardware run.
