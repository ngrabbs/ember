# IHU automatic UHF link bench profile

**IHU 0.22.0 and transceiver 0.37.2** are the matching pair. This profile is
for the conducted CAN Feather / original Pico bench, with the two RF paths
connected and attenuated. The legacy bench profile and the flight stub remain
separate. See [startup and CW procedure](ihu-cw-startup-demo.md) for wiring,
flash verification, and rollback.

Build the IHU with `-DIHU_BOOT_DEMO=ON` and the radio with
`-DTRANSCEIVER_BOOT_DEMO=ON`, in fresh build directories. A normal build has both
options off. With the new matched pair there is no serial arm or per-boot mode
command. The IHU checks CAN and EPS, waits for the radio, simulates both
deployment switches and antenna deployment, waits for the 15-second silence
timer, and sends the configured CW beacon once. On the radio's confirmed
receive transition, it automatically requests `LINK_ACTIVE`. The IHU enters
`GROUND_TEST / NOMINAL` only on the radio's matching acknowledgement.

| Radio behavior | Entry and effect |
| --- | --- |
| MUTED | Before startup RF, or on stop/failure. No automatic restart. |
| RX_ONLY | After CW and before link activation. Set the optional IHU build flag `-DIHU_BOOT_RX_ONLY=ON` to stay there for receive-only tests. |
| LINK_ACTIVE | Default after successful demo startup. Valid RF frames go to the IHU. Only packets submitted by the IHU go back out on RF. |

Use `radio` on the IHU console to see the behavior, uplinks, generated replies,
local TX completions, dropped uplinks and heartbeat period. `startup` also shows
the retained transition trace. `mode safe` / `uhf stop` stop the exercise.
The dedicated link's heartbeat schedule is separate from the six manual output
switches, which stay off in this profile.

## Packet flow

The radio validates the outer RF frame length/CRC, then passes its payload
bytes unchanged over CAN. The IHU validates native message integrity,
addressing and command semantics.

| Yamcs command | Result in GROUND_TEST / NOMINAL |
| --- | --- |
| PING | Correlated command completion |
| REQUEST_STATUS | Current IHU_STATUS snapshot |
| REQUEST_TELEMETRY | IHU_STATUS for SYSTEM (`data_group=1`). Other groups are rejected. |
| STATUS_CAPTURE | Five status records sampled at 1 Hz and returned as STATUS_RECORDS. Each new capture replaces the previous RAM bank. |
| STATUS_FETCH | The same frozen records for the matching `capture_id` while the IHU stays powered |
| PAYLOAD_FIRE_CHECK | The IHU commands the payload over CAN and sends its result back over UHF. The payload HELLO has a 5-second timeout and the result has a 12-second timeout. An unavailable payload returns NOT_AVAILABLE. Inspect payload files separately when needed. |
| IHU_REBOOT | Returns MODE_NOT_ALLOWED in NOMINAL. Reboot requires SAFE with outputs off. This profile stops the link on entry to SAFE. |
| SET_HEARTBEAT | `enabled=1` starts the 10-second heartbeat. `enabled=0` stops it. The IHU boots with heartbeat off. |
| SET_UHF_TELEMETRY_SCHEDULE | Set `listen_seconds` (1–3600) and `telemetry_seconds` (5–3600). The boot defaults are 540 and 60. |
| SET_UHF_TELEMETRY | `enabled=1` starts with a listen phase. `enabled=0` stops scheduled telemetry and retains the configured durations until reboot. |
| SET_UHF_TELEMETRY_SET | Choose `BASIC` or `FULL`. Defaults to BASIC on reboot. |

Issue one command at a time and wait for its result. While a status capture
or fire check is in progress, the IHU reserves the reply slot and drops new
commands. When enabled, the first HEARTBEAT is due 10 seconds after the
command, with subsequent intervals skipped when the link is busy. The setting
is held in RAM and resets to off on boot.
A queued reply has priority over a
heartbeat not yet submitted. There is one in-flight transmission, one waiting
reply, no telemetry backlog, and no automatic retry of uncertain TX.

All outgoing packets use the same opaque transmit request. The radio
frames the bytes, sends the bounded BPSK burst, mutes TX and reestablishes RX.
The radio never checks whether the bytes represent a reply or telemetry.
A local completion reports local send and restored RX, not Yamcs reception.

CAN A uses 0x757 for uplink packet fragments and 0x758 for downlink packet
fragments. Both reuse the CRC-protected UL envelope and CAN fragmentation with
`type=0xb0`, sender boot, destination boot and nonzero increasing request ID.
Packet payloads are limited to 128 bytes in this profile. IDs 0x759/0x75a report
local TX success/failure, and 0x75b/0x75c request/confirm link activation.
Control frames are two **big-endian** 32-bit words: correlation token (or TX
request ID for a result), followed by transceiver boot ID. CAN correlation on
this isolated bench is not authentication.

The IHU renews its active link every 200 ms; expiry at the radio is 750 ms.
Each BPSK burst has the existing 2-second TX mute alarm. A missing or failed
local TX result returns the IHU to SAFE, without retry. Telemetry cadence is
initial bench policy, not a flight requirement.

## Scheduled telemetry

The IHU enters NOMINAL with scheduled telemetry off. The defaults are nine
minutes listening followed by a one-minute telemetry window. Yamcs can select
either set. The IHU sends one of each listed packet per window.

| Set | Packets in transmission order |
| --- | --- |
| BASIC | `IHU_STATUS`, `POWER_STATUS` |
| FULL | `IHU_STATUS`, `POWER_STATUS`, `DEVICE_STATUS`, `SYSTEM_STATUS`, `HEARTBEAT`, `PAYLOAD_STATUS` |

EPS values use the latest valid housekeeping sample. Device status reports the
cached registry and its observation ages. The IHU polls the payload over CAN
once per FULL window. It sends `PAYLOAD_STATUS` only after a valid reply.
Packets carry zero transaction IDs.
If the link is busy, packets wait within the window or are skipped when there
is insufficient time left. The next cycle starts on schedule.

Uplink reception remains available between bursts in both phases. Solicited
replies take priority and can transmit during the listen phase. Enabling the
schedule turns off the separate periodic heartbeat. A change to either duration
or the packet set starts a fresh listen phase when enabled. Disable then enable to
start a new cycle. The durations, packet set, and enable state reset on reboot.

## Ground test

The [ground RF gateway](../../ground/bpsk/LINK_GATEWAY.md) keeps SDR receive
streaming and transmits Yamcs commands without an m75q serial arm. It continuously
forwards valid telemetry and replies to Yamcs `ember`. A single PING can miss a
receive window: the spacecraft radio uses ADC capture blocks with decoder gaps
and is half-duplex during transmission. An RF timeout is UNKNOWN; the gateway
does not retransmit automatically.

Before accepting the pair, verify conducted CW timing, heartbeat off on boot, heartbeat enable and disable,
a correlated ground PING result, returned RX, stop/lease expiry during a burst,
and no replay of an uncertain transmission. Hardware acceptance is separate
from builds and host tests.


## GPS position from USB

On IHU 0.24.0, connect the Adafruit PA1010D breakout to the Feather's STEMMA
QT port and run `gps` on the IHU USB console. The IHU reads a fresh
checksummed GGA sentence over I²C at address `0x10`, on demand. A fix reports
latitude and longitude in signed decimal degrees and the satellites used.
`NO_FIX` means the receiver replied without a fix. `NO_DATA` means no valid
fresh GGA sentence arrived within 2.5 seconds. `I2C_ERROR` means the I²C read
failed. If the sensor worker is busy, retry the command.

For a first fix, give the patch antenna an unobstructed view of the sky,
pointing up. STEMMA QT supplies power whenever its rail is on. The command
controls when the IHU reads the receiver. It leaves receiver power and its
NMEA settings alone.
