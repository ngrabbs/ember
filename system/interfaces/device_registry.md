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
| LTE | CAN A | 3 | Discovery implemented in LTE CAN Feather0.8.0; hardware validation pending |
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

## Application addressing migration

| Node | Request | Reply | Discovery reply |
|---|---|---|---|
| COMMS transceiver (2) | `0x710` | `0x711` | `0x702` |
| LTE CAN Feather (3) | `0x720` | `0x721` | `0x703` |

The registry contains the route IDs. Existing transceiver and SDRB IDs remain
unchanged. The LTE Feather must be upgraded before joining their bus; older LTE
images still answer0x710 and must stay disconnected. Firmware deployment and a
simultaneous two-device bench test are required before declaring coexistence
qualified. Hardware ACK does not prove correct application addressing.

IHU0.8.0 defaults to COMMS. `hello comms` (or bare `hello`) selects COMMS;
`hello lte` selects LTE. Each selection clears the application peer and fragment
parser and performs a new HELLO. Switching is rejected during outstanding CAN
or UHF work, discovery, automatic telemetry or enabled LTE queuing. Only the
selected reply ID enters application reassembly. One application route is
active at a time; discovery still observes both nodes. UHF commands reject the
LTE target and LTE-specific requests reject the COMMS target. The existing
finite RF limits and no-auto-retry rules remain.

LTE boots CAN-ready and answers node3 discovery without starting Walter RF.
The modem remains reset until an explicit bounded LTE window request.

## Firmware identity queries

`version` on each Feather or Walter console prints semantic version, full source
SHA, dirty flag and boot ID. Build identity inputs are mandatory; exported source
must carry the original checkout's SHA/dirty state rather than the build host's.

With `hello lte` established:

- `lte firmware` reads the Feather identity using application type0x18/reply0x19.
- `lte modem firmware` requests Walter identity through the Feather using
  type0x7c/reply0x7d; the UART hop uses0x18/0x19 after HELLO.

Both requests have zero payload. Successful replies carry32 bytes: version
major/minor/patch/dirty (4), SHA (20), device boot ID (4), and device uptime (4),
all multibyte numbers big endian. Requests never open RF windows. The Feather
checks Walter's sender and reported boot ID before forwarding its identity.

Within180 seconds of the observations, select `hello comms`, explicitly enable
COMMS RF, then use `uhf lte firmware` or `uhf modem firmware` to forward the
corresponding observation. Each is one ordinary bounded UHF request. It is not
added to the existing three-packet automatic cycle. COMMS0.23.0 admits the new
message IDs;0.22.0 does not. Receiver2.1.0 includes their dictionary definitions.

Native `LTE_CAN_FIRMWARE` (51) and `LTE_MODEM_FIRMWARE` (52) are IHU-sourced
observations, not impersonated LTE packets. Their payload contains the32-byte
identity plus a4-byte observation age. Header boot/uptime identify IHU;
`reported_boot_id` and `reported_uptime_ms` identify the queried device. They
are historical evidence after a reset until queried again. Yamcs displays and
LTE-Firmware.par expose that distinction. No LTE firmware image has been
hardware-verified merely because the host tests and builds pass.

## Migration validation status — October 17

- [x] Host tests of actual IHU/LTE Feather handlers: route selection, busy-switch
  rejection, wrong-ID fragments, per-device discovery/liveness, read-only
  Feather/Walter identity relay, identity age limit and independent Python decode.
- [x] Walter host checks: identity query leaves modem OFF/reset; malformed query
  rejected; existing bounded modem tests pass.
- [x] 47 ground tests (46 pass, one optional virtual-CAN skip),14 receiver tests,
  transceiver startup/fault checks and extended native bridge checks pass.
- [x] ARM Release builds of both Feather roles and original Pico; Walter
  PlatformIO build passes. Firmware candidates: Feather family0.8.0,
  Walter0.3.0, COMMS0.23.0; receiver candidate2.1.0.
- [ ] Save and verify backups of the identified LTE Feather and Walter.
- [ ] Flash/verify LTE candidates with LTE still disconnected from CAN A.
- [ ] Flash/verify IHU migration and confirm COMMS-only operation first.
- [ ] Connect upgraded LTE with appropriate two-end termination; observe both
  discovery replies and independent HELLO/echo/identity queries, RF disabled.
- [ ] Update COMMS/receiver/MDB for new identity messages, query both LTE CPUs,
  and verify original identity bytes through bounded UHF into Yamcs.
- [ ] Visually inspect both new live identity displays and audit a new Yamcs
  asset manifest. Existing1.0.0/receiver2.0.0 demo deployment is unchanged.

Prior LTE source needed its pending PR #20 native SYSTEM_STATUS allowlist;
that small forwarding change is retained here. No other #19/#20 deployment
or networking changes are included. This branch builds on PR #21.
