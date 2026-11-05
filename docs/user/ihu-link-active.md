# IHU automatic UHF link bench profile

**IHU 0.18.1 and transceiver 0.37.1** are the matching pair. This profile is
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
addressing and command semantics. This profile admits **PING and REQUEST_STATUS**;
other uplinks still reach the IHU and are counted as dropped there. It does
not admit payload execution or reboot commands. The IHU generates the terminal
correlated PING response or IHU_STATUS snapshot from its latest validated observations, and schedules a native HEARTBEAT every **10 seconds**
(first due 10 seconds after activation). A queued reply has priority over a
heartbeat not yet submitted. There is one in-flight transmission, one waiting
reply, no telemetry backlog, and no automatic retry of uncertain TX.

Both kinds of outgoing packet use the same opaque transmit request. The radio
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

## Ground test

The [ground RF gateway](../../ground/bpsk/LINK_GATEWAY.md) keeps SDR receive
streaming and transmits Yamcs PINGs without an m75q serial arm. It continuously
forwards valid telemetry and replies to Yamcs `ember`. A single PING can miss a
receive window: the spacecraft radio uses ADC capture blocks with decoder gaps
and is half-duplex during transmission. An RF timeout is UNKNOWN; the gateway
does not retransmit automatically.

Before accepting the pair, verify conducted CW timing, several heartbeats,
a correlated ground PING result, returned RX, stop/lease expiry during a burst,
and no replay of an uncertain transmission. Hardware acceptance is separate
from builds and host tests.
