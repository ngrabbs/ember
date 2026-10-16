# Expected devices and runtime health

The source of truth for bench device identities is
[`device_registry.h`](../../firmware/comms_transport/device_registry.h).
This follows rt-ihu's fixed identities plus runtime health checks. It is not a
scan of every possible CAN identifier and does not infer device health from CAN
hardware ACK alone.

| Entry | Interface | Discovery node | Revision expectation |
|---|---|---|---|
| EPS | I2C1, address0x68 | None | Current LTC4162; PEC-checked config read |
| EPS_NEXT | CAN A | 1 | Future CAN-enabled EPS |
| COMMS | CAN A | 2 | Current transceiver, responder implemented |
| LTE | CAN A | 3 | CAN hardware exists; discovery firmware adoption pending |
| PAYLOAD | CAN A | 4 | Future CAN-enabled payload |

The IHU starts CAN in normal mode and probes one registry entry every two
seconds when application transport is idle (one complete cycle about ten
seconds). `devices` prints each state, whether it has ever responded, last-seen
age, responder boot ID and timeout count. `devices scan` schedules the next
background check immediately; it does not interrupt active traffic. States:
NOT_SEEN, ONLINE, STALE after30 seconds without new evidence, or FAULT for a
local transport/I2C error. A later successful check restores ONLINE. Silence
alone cannot distinguish absent hardware from firmware without discovery.

Scanning pauses during a UHF run, outstanding application requests, pending CAN
transmission, automatic telemetry, LTE queuing or local loopback. Validated UHF
results refresh COMMS liveness; successful EPS packet reads refresh EPS
liveness. EPS liveness is independent of ADC validity/calibration. No scan
writes EPS configuration, enables RF, or starts a telemetry producer.

## Additive CAN discovery v1

Classic standard-ID CAN,500 kbit/s, CAN A only. CAN B remains standby; no A/B
failover is implied. Development request ID0x700 carries eight bytes:

| Bytes | Value |
|---|---|
| 0 | Version1 |
| 1 | Target node1–4 |
| 2–3 | Nonzero16-bit nonce, big endian |
| 4–7 | Nonzero requester boot ID, big endian |

Only the addressed node responds, using standard ID`0x700 + node` and the same
layout, replacing bytes4–7 with its own boot ID. One probe is outstanding,
with a one-second deadline. Version, target, reply ID, nonce and nonzero boot
must match. No nonce reuse is allowed in an IHU boot; after65535 probes a reboot
is needed to resume CAN discovery. This is a bench correlation mechanism,
not authentication or capability negotiation. Future nodes can reuse
`dr_respond()`; their application commands still require separate contracts.

## Boot-ready transceiver

COMMS v21 performs its existing controller checks, then enables CAN A normal
mode with RF muted. Idle service answers discovery, legacy HELLO and ECHO.
UHF send requests receive explicit `UHF_DISABLED=7` rejection until the operator
opens `a` or `g`. After those bounded windows end, idle CAN service resumes.
The independent burst mute/deadline protections remain. Controller faults
latch that interface in reset until reboot. CAN readiness is not measured RF
silence, and discovery does not replace the explicit application HELLO.

## Legacy coexistence limitation

The current transceiver and older LTE bridge both use request0x710/reply0x711
for their application envelopes. Keep only one of those legacy responders on
a bus until an explicitly coordinated application-address migration is done.
Discovery IDs are distinct, but do not resolve that pre-existing collision.
This change implements discovery only on the transceiver; no LTE, payload or
future EPS firmware was flashed or claimed compatible.
