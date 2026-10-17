# Payload user guide

[Operator guides](README.md) · [IHU console](ihu-can-console.md) · [Yamcs](yamcs.md)

This guide covers the Raspberry Pi 4 on the LibreCube LC2502, payload software
**0.2.0**, IHU **0.13.0**, and the five implemented payload operations. Checked
against repository source and the installed Pi identity on October 17, 2026.
Earlier IHU 0.12.0 fire-check transcripts below remain useful examples of the
same payload protocol. Boot IDs, request IDs, uptimes and counters vary per run.

The payload responds on **CAN A at 500 kbit/s**, node **4**. It starts its CAN
interface and responder at boot without needing Wi-Fi or an open console.
It does not send periodic heartbeats or fire results on its own.

Fire check currently returns **NO_FIRE / STATIC_STUB**. It increments a check
counter but does not invoke a camera or detection algorithm. There are no
implemented camera, image acquisition/download, detector configuration,
payload power-switch, or CAN reboot/shutdown commands. Linux maintenance is
available separately through SSH.

## Choose an interface

| Interface | Where to use it | What it provides |
|---|---|---|
| SSH | `ngrabbs@192.168.1.253` (`ember-pi`) | Service control, logs, identity, CAN statistics, Linux reboot/shutdown |
| Direct SocketCAN client | A Linux host on the same CAN A bus, including the Pi itself | All five operations; automatically establishes HELLO |
| IHU USB console | IHU connected to m75q, `192.168.1.252` | Discovery, target selection and all five operations |
| Yamcs `ember-bench` / `realtime` | Ground station `http://192.168.1.251:8090` | All five operations over LAN → IHU USB → CAN A |
| Yamcs `ember` / `realtime` | Same ground station | Fire check over a bounded real RF transaction → IHU → CAN A |

The historical `ember-payload` instance is not the current operational bench
instance. Use `ember-bench`. The retired `ember-payload-bridge` service stays
disabled; `ember-bench-bridge` is the shared IHU serial owner.

## On the Pi: readiness, logs and maintenance

Connect:

```sh
ssh ngrabbs@192.168.1.253
```

### Check readiness and installed version

```sh
systemctl status ember-payload-can ember-payload --no-pager
ip -details -statistics link show can0
cat /opt/ember-payload/build_identity.json
sudo journalctl -b -u ember-payload-can -u ember-payload --no-pager
```

`ember-payload-can` is a successful oneshot: **active (exited)** is normal.
`ember-payload` should be **active (running)**. The link should be UP, bitrate
500000, and normally `ERROR-ACTIVE` (the healthy CAN error-confinement state).
Inspect RX/TX error counts as well as packet counts.

The installed identity was:

```json
{"git":"c35262eda021e9819d4263616769c77ce3736e75","dirty":0,"version":"0.2.0"}
```

A startup line looks like this recorded example:

```text
CAN_READY interface=can0 node=4 boot=4034088014 git=c35262eda021e9819d4263616769c77ce3736e75 version=0.2.0
```

`boot` identifies this responder process, not the Linux kernel boot. Restarting
the service changes it and clears its session and counters. The file identity
reports the installed software; a CAN IDENT reply verifies what the live
responder reports.

### Tail incoming commands

```sh
sudo journalctl -u ember-payload -f -o cat
# Fire-check requests only:
sudo journalctl -u ember-payload -f -o cat | grep --line-buffered 'type=98'
# Only messages from this Linux boot:
sudo journalctl -b -u ember-payload -o cat
```

Recorded request examples:

```text
REQUEST type=01 origin=1765436985 request=64 reply=02
REQUEST type=98 origin=1765436985 request=65 reply=99
```

Types in these log lines are **hexadecimal**. `origin` is the requester session
ID; `request` correlates that request and reply. `reply=99` means the handler
produced a fire-result response to queue; it does not prove that the IHU or
ground station received it. Look for the correlated IHU RESULT or Yamcs command
completion to establish end-to-end success. Rejections show `reply=7f`.
Discovery frames and malformed/incomplete application frames do not each get
an application `REQUEST` line. `BUSY reply queue full` indicates dropped work.

### Start, stop or restart

Run these on the Pi:

```sh
sudo systemctl stop ember-payload
sudo systemctl start ember-payload
sudo systemctl restart ember-payload
```

Stopping the responder also stops payload discovery replies. It does not take
the CAN interface down. If CAN initialization failed, fix the cause, then run:

```sh
sudo systemctl restart ember-payload-can
sudo systemctl start ember-payload
```

When deliberately reconfiguring an already running CAN interface, stop
`ember-payload` first, restart `ember-payload-can`, then start the responder.
Enable both for boot, or disable both to prevent automatic startup:

```sh
sudo systemctl enable ember-payload-can ember-payload
# Disable boot startup and stop the responder:
sudo systemctl disable ember-payload-can ember-payload
sudo systemctl stop ember-payload
```

Linux reboot and shutdown are SSH operations, not CAN services:

```sh
sudo reboot
sudo shutdown -h now
```

After reboot, check readiness again and establish a fresh CAN HELLO before
querying. The startup helper probes the MCP2515 at most 20 times; it does not
retry indefinitely. The service does not automatically recover CAN bus-off.

### Observe raw traffic

With `can-utils` installed:

```sh
candump can0,700:7FF,704:7FF,740:7FF,741:7FF
```

This displays discovery and fragmented application traffic. It does not decode
application results. It can run alongside the responder without replacing the
HELLO session. Raw CAN frames are not the same as completed application requests.

## From the IHU USB console

On m75q, identify and release the current serial owner before opening a terminal:

```sh
ssh ngrabbs@192.168.1.252
systemctl is-active ember-bench-bridge
sudo systemctl stop ember-bench-bridge
python3 -m serial.tools.miniterm \
  /dev/serial/by-id/usb-Raspberry_Pi_Pico_DF641455DB822427-if00 115200
```

This requires pyserial. Exit miniterm with **Ctrl+]**. After closing the terminal,
restore the bridge if it was initially active:

```sh
sudo systemctl start ember-bench-bridge
```

Do not open another program on the same port. Stopping the bridge suspends
Yamcs bench commands and serial forwarding. The separate `ember-fire-arm`
service uses the COMMS port, not this IHU port.

The IHU takes case-sensitive lines terminated by CR or LF. It has no prompt;
boot is quiet. Solicited replies work with every output stream OFF. In IHU
0.13.0 these manual application requests require the GROUND_TEST configuration;
FLIGHT rejects this console path with `FLIGHT_ROUTINE_STUB`. See the
[IHU mode/output policy](../architecture/operations/04-ihu-runtime-policy.md).

| Console command | Purpose / expected result |
|---|---|
| `help` | List actual commands in this IHU image |
| `version` | Verify `role=IHU_MCU` and firmware identity |
| `status` | IHU CAN readiness, selected target, peer ID, counters and pending work; not a payload status query |
| `devices` | Registry presence, age, boot identity and timeout counts |
| `devices scan` | Schedule background discovery; does not establish HELLO |
| `hello payload` | Select payload route and establish session; `CAN_HELLO_CONFIRMED` |
| `ping N` | Echo 1–240 bytes on the selected target; `CAN_ECHO_MATCHED` |
| `payload ident` | 32-byte identity; `FIRMWARE_IDENTITY` |
| `payload status` | 28-byte status snapshot; `PAYLOAD_STATUS` |
| `payload heartbeat` | Fresh 28-byte snapshot; `PAYLOAD_HEARTBEAT`; does not enable a timer |
| `payload fire-check` | One 16-byte fire result; `PAYLOAD_FIRE_RESULT` |
| `hello comms` / `hello lte` | Leave the payload route and establish the selected subsystem session |
| `normal` | Restore IHU CAN normal mode and clear remembered peer; HELLO required afterward |

Run this sequence **one line at a time**, waiting for each terminal RESULT:

```text
version
status
devices
hello payload
ping 8
payload ident
payload status
payload heartbeat
payload fire-check
hello comms
```

`ping N` sends bytes `00 01 ... N-1`. Other payload requests take no arguments.
Always select `hello payload` first: `ping` otherwise acts on the previously
selected subsystem. Discovery `ONLINE` alone does not authorize application
queries. The `selftest` command is an IHU local loopback diagnostic and leaves
loopback enabled; use `normal` and HELLO afterward if you used it.

### Example IHU replies

A recorded hardware fire-check transaction (IHU 0.12.0, payload 0.2.0):

```text
SUBMITTED request=1 type=1 bytes=0
RESULT request=1 outcome=CAN_HELLO_CONFIRMED peer=1559660849 bytes=0 hex=
SUBMITTED request=2 type=152 bytes=0
RESULT request=2 outcome=PAYLOAD_FIRE_RESULT peer=1559660849 bytes=16 hex=010001005cf689310001d62c00000001
FIRE_CHECK result=no_fire mode=STATIC_STUB check_id=1
```

Here console `type=152` is decimal (`0x98`). The 16 data bytes decode to version
1, NO_FIRE, STATIC_STUB, reserved 0, boot 1559660849, uptime 120364 ms, check ID 1.
The `FIRE_CHECK` summary can follow the RESULT asynchronously.

Recorded identification reply:

```text
FIRMWARE_REPLY peer=1559660849 version=0.2.0 dirty=0
RESULT request=8 outcome=FIRMWARE_IDENTITY peer=1559660849 bytes=32 hex=00020000c35262eda021e9819d4263616769c77ce3736e755cf689310001d6f5
```

Illustrative ping and status replies, with synthetic IDs/counters:

```text
SUBMITTED request=2 type=112 bytes=8
RESULT request=2 outcome=CAN_ECHO_MATCHED peer=42 bytes=8 hex=0001020304050607
PAYLOAD_REPORT boot=42 uptime_ms=1000 requests=3 replies=2 rejected=0 fragment_errors=0
RESULT request=3 outcome=PAYLOAD_STATUS peer=42 bytes=28 hex=010401000000002a000003e800000003000000020000000000000000
```

A heartbeat uses the same report layout and `outcome=PAYLOAD_HEARTBEAT`.
`ready=1` means the responder is running, not that cameras or a detector are ready.

## Direct Linux CAN client

From the repository root on a Linux host with an already configured `can0`:

```sh
python3 firmware/payload/client.py --interface can0 ping
python3 firmware/payload/client.py --interface can0 ident
python3 firmware/payload/client.py --interface can0 status
python3 firmware/payload/client.py --interface can0 heartbeat
python3 firmware/payload/client.py --interface can0 fire-check
```

Each invocation sends HELLO, then one operation. The client ping echoes the
fixed five-byte ASCII string `EMBER`; it has no size argument. It waits up to
three seconds per exchange and does not retry the operation automatically.
Example output using the recorded fire-result data:

```text
fire-check: boot=1559660849 request=2 payload=010001005cf689310001d62c00000001
```

The client requires `client.py` and `protocol.py` from the source/export. The
normal installed `/opt/ember-payload` runtime does not include `client.py`.
Do not run a second responder to test the existing one. A client on the same
Pi can communicate with the running responder using SocketCAN local delivery.

A client HELLO **replaces the IHU session**. Coordinate ownership and run
`hello payload` again on the IHU afterward. Two independent command sources
can invalidate each other's sessions. The payload has no command deduplication
cache: a repeated accepted fire-check request can increment `check_id` again.

## Through Yamcs

Use the current [bench payload display](http://192.168.1.251:8090/telemetry/displays/files/Payload.opi?c=ember-bench__realtime)
or [flight payload display](http://192.168.1.251:8090/telemetry/displays/files/Payload.opi?c=ember__realtime).
Firmware identity is on **Devices & firmware**. Inspect the selected instance,
reply timestamps, payload boot and command history before treating a value as
current. Old values can remain visible after a disconnect.

| Yamcs command | Arguments | IHU operation | Bench | Flight RF |
|---|---|---|---|---|
| `PAYLOAD_PING` | `bytes`: 1–240 | `ping N` | Yes | No |
| `PAYLOAD_IDENT` | None | `payload ident` | Yes | No |
| `PAYLOAD_STATUS_QUERY` | None | `payload status` | Yes | No |
| `PAYLOAD_HEARTBEAT_QUERY` | None | `payload heartbeat` | Yes | No |
| `PAYLOAD_FIRE_CHECK` | None | `payload fire-check` / native RF dispatch | Yes | Yes |

Use **Commanding → Send a command**, select `/ember/PAYLOAD_…`, configure any
arguments and send once. In bench, the bridge verifies IHU CAN readiness and
establishes `hello payload` automatically. It reports admission after the IHU
submits the request and completion after a validated matching reply. A
pre-dispatch refusal is a rejection; an ambiguous post-dispatch timeout stays
UNKNOWN. Inspect that command's correlated history rather than only the last
shared result parameter. There is no automatic application retry.

Payload telemetry groups are `PAYLOAD_STATUS`, `PAYLOAD_FIRMWARE`,
`PAYLOAD_PING_RESULT` and `PAYLOAD_FIRE_RESULT`. Fire results include `result`,
`execution_mode`, `reported_boot_id`, `reported_uptime_ms` and `check_id`.
Transport provenance is `IHU_CONSOLE_CAN_BENCH` (1) or `IHU_NATIVE_RF` (2).
NO_FIRE is valid only with an actual validated result; timeout is never NO_FIRE.

The flight command path uses LibreSDR → COMMS → IHU → payload and returns one
correlated native result over RF. USB arms a finite COMMS receive/reply window;
it does not carry the flight command/result. This transmits RF and requires
exclusive radio ownership and the configured arming/uplink services. Follow
[the fire-check runbook](../../ground/yamcs/FIRE_CHECK.md) before using it.
It is not an always-listening flight receiver. Do not run a live radio receiver
and the fire-check radio owner concurrently. Console stream switches do not
need to be enabled for a solicited fire-check reply.

For bridge-side diagnostics on m75q:

```sh
systemctl status ember-bench-bridge --no-pager
journalctl -u ember-bench-bridge -f -o cat
```

## Complete CAN command contract

These identifiers are **standard 11-bit classic CAN**, with at most eight data
bytes per frame. They are development addressing/correlation, not authentication.

| Purpose | CAN identifier | Data |
|---|---|---|
| Discovery query | `0x700` | Single eight-byte discovery request addressed to node 4 |
| Discovery reply | `0x704` | Single eight-byte discovery response |
| Application requests | `0x740` | Fragmented encoded packet |
| Application replies | `0x741` | Fragmented encoded packet |

Discovery is `version:u8=1, node:u8=4, nonce:u16, sender_boot:u32`, big endian;
nonce and sender must be nonzero. The reply echoes version/node/nonce and
substitutes the payload boot. Example: query `0104123400000001`, reply
`010412340000002a` for nonce `0x1234`, requester boot 1, payload boot 42.
Discovery does not establish a session. COMMS `0x710/0x711`, LTE `0x720/0x721`
and RF uplink `0x730/0x731` are separate routes.

### Accepted application types

The following are **packet types**, not CAN IDs or standalone one-byte frames.

| Request | Reply | Name | Request data | Reply data |
|---|---|---|---|---|
| `0x01` | `0x02` | HELLO | Empty | Empty; establish/replace requester session |
| `0x70` | `0x71` | ECHO / ping | 1–240 arbitrary bytes | Identical bytes |
| `0x18` | `0x19` | IDENT | Empty | 32-byte identity |
| `0x94` | `0x95` | STATUS | Empty | 28-byte report |
| `0x96` | `0x97` | HEARTBEAT | Empty | Fresh 28-byte report |
| `0x98` | `0x99` | FIRE_CHECK | Empty | 16-byte fire result |
| — | `0x7F` | ERROR | — | One-byte rejection reason |

All decoded requests require protocol version 1 and equal, nonzero `sender`
and `origin` IDs. HELLO sets the accepted requester ID; subsequent operations
must use that ID. Replies carry the payload's sender boot and preserve request
origin/request ID. After payload restart or another client's HELLO, establish
HELLO again. Session IDs provide correlation, not access control.

Rejection reasons are `1` unsupported version, `2` unsupported type, `3` invalid
or missing requester session, `4` invalid command data. Corrupt CRC, invalid
framing, wrong route and incomplete/oversize packets are discarded without an
application ERROR. Absence of a reply is UNKNOWN.

### Packet and fragment encoding

All multibyte application fields are big endian. Before encoding:

```text
magic[2]="EU" | version:u8 | type:u8 | sender:u32 | origin:u32 |
request:u32 | payload_length:u16 | payload[0..240] | crc:u16
```

CRC is CRC-16/CCITT-FALSE (initial `0xFFFF`) over header and payload. COBS-encode
header, payload and CRC together, then append a zero delimiter. Maximum encoded
length is 263 bytes. Split that into chunks of up to four bytes. Each CAN data
field is:

```text
flags:u8 | token:u16 | fragment_index:u8 | encoded_chunk[1..4]
```

Flags start at `0x10`, with bit 0 for START and bit 1 for END. Token is the low
16 bits of request ID; index begins at zero and increments. Nonfinal fragments
carry four encoded bytes. The receiver has a 500 ms interfragment timeout and
rejects duplicate starts and out-of-order fragments. Use
[`protocol.py`](../../firmware/payload/protocol.py) or the C transport codec;
`cansend can0 740#98` is not a valid fire-check request.

### Decoding reply data

Offsets below are relative to the **decoded application payload**, not the CAN
frame, COBS packet or Yamcs wrapper.

| Reply | Byte offsets and meaning |
|---|---|
| IDENT, 32 bytes | 0–2: version major/minor/patch; 3: dirty (0/1); 4–23: source SHA bytes; 24–27: daemon boot; 28–31: daemon uptime ms |
| STATUS / HEARTBEAT, 28 bytes | 0: report version 1; 1: node 4; 2: ready 1; 3: reserved 0; 4–7: boot; 8–11: uptime ms; 12–15: requests; 16–19: replies; 20–23: rejected; 24–27: fragment errors plus timeouts |
| FIRE_RESULT, 16 bytes | 0: report version 1; 1: result (0 NO_FIRE, 1 FIRE); 2: execution mode (1 STATIC_STUB, 2 ALGORITHM); 3: reserved 0; 4–7: boot; 8–11: uptime ms; 12–15: check ID |

Status counts include the current request, but the replies count is taken
before incrementing for that status/heartbeat reply. These are handler/queued
reply counters, not proof of bus delivery; SocketCAN statistics are separate.
Uptime and report counters are 32-bit; fire check IDs run from 1 through
`0xFFFFFFFF`, then wrap to 1. All reset when the responder restarts. The current
stub always reports result 0/mode 1; mode 2 is a defined future algorithm value.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| SSH works, no CAN replies | Check both services, existence of `can0`, bitrate and `ip -s -d link show can0` |
| `can0` absent; `MCP251x didn't enter in conf mode after reset` / error -110 | SPI/controller initialization failed before application CAN traffic. Inspect controller power/reset/connections and boot logs. A software reboot recovered the observed October 17 cold-power failure; its underlying cause remains unresolved |
| Payload service inactive with dependency failure | CAN setup failed; after recovery restart CAN setup and explicitly start the responder |
| CAN up but no application reply | Verify 500 kbit/s, normal mode, correct route, termination and fresh HELLO; inspect controller and fragment error counters |
| `REJECT reason=BUSY_TARGET_SWITCH` | IHU discovery/transaction holds the route; wait for it to finish before selecting again |
| `REJECT reason=HELLO_REQUIRED` or payload ERROR reason 3 | Re-establish `hello payload`; another client's HELLO or a restart may have changed session |
| `PAYLOAD_TARGET_REQUIRED`, `WRONG_TARGET` or `PAYLOAD_READ_ONLY_SERVICES` | Select payload before payload queries; power/LTE/UHF operations do not belong on its route |
| `REJECT reason=UHF_RUN_ACTIVE` | Let the bounded IHU UHF run finish, or explicitly stop it with `uhf stop` before switching target |
| `REJECT reason=NORMAL_MODE_REQUIRED` | Restore IHU `normal`, then obtain HELLO again |
| Old Yamcs values, no new requests in Pi log | Verify `ember-bench`, bridge ownership/readiness and timestamps; the old `ember-payload` URL/service is historical |
| Fire result absent/corrupt/timeout | Treat as UNKNOWN, never NO_FIRE; inspect the correlated command history and route logs |

## Updating or manually running the responder

Normal operation uses systemd. To replace the installed runtime, use a clean
source checkout and export into a **new** destination from the repository root:

```sh
python3 firmware/payload/export.py /tmp/ember-payload-export
scp -r /tmp/ember-payload-export ngrabbs@192.168.1.253:~/payload-export
ssh ngrabbs@192.168.1.253 'sudo sh ~/payload-export/install.sh'
```

Use a new remote export directory as well if `~/payload-export` already exists.
The installer replaces the runtime/service files, enables both units, configures
CAN and starts the responder. It does not rewrite Wi-Fi or boot overlays. The
export records source Git SHA, dirty flag and VERSION in `build_identity.json`.
See [installation details](../../firmware/payload/README.md#installation-and-startup)
for the required CAN A SPI0/16 MHz/GPIO25 boot overlay; CAN B remains unused.

For foreground diagnosis, stop the service first, ensure `can0` is configured,
then run one responder in a terminal on the Pi:

```sh
sudo systemctl stop ember-payload
python3 /opt/ember-payload/payload.py \
  --interface can0 \
  --identity /opt/ember-payload/build_identity.json \
  --lock /tmp/ember-payload-manual.lock
# Ctrl+C stops the foreground responder; then restore normal service:
sudo systemctl start ember-payload
```

The manual lock differs from the systemd lock: it does not protect against an
accidental service start in another terminal. Keep the service stopped until
the foreground process has exited. `--interface`, `--identity` and `--lock`
are the complete daemon options (`--help` lists them). The daemon has no
interactive command prompt. `can_setup.py` is the root-only startup helper;
prefer the systemd CAN unit over invoking it against a running responder.

## Source and recorded evidence

- [Payload service and protocol](../../firmware/payload/README.md)
- [IHU application](../../firmware/ihu/main.c) and [payload protocol validation](../../firmware/comms_transport/payload_protocol.h)
- [Operational ground routes and serial ownership](../../ground/yamcs/OPERATIONAL.md)
- [Fire-check RF procedure and limits](../../ground/yamcs/FIRE_CHECK.md)
- [Recorded IHU fire/identity transcript](../../system/ground_station/evidence/fire-check-20261017/direct-ihu.log)
- [Hardware fire-check validation](../../system/ground_station/evidence/fire-check-20261017/validation.json)
