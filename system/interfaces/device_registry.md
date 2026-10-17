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
| LTE | CAN A | 3 | Discovery verified alongside COMMS with LTE CAN Feather0.8.0 |
| PAYLOAD | CAN A | 4 | Future CAN-enabled payload |

The IHU starts CAN in normal mode and probes one registry entry every two
seconds when application transport is idle (one complete cycle about ten
seconds). `devices` prints each state, whether it has ever responded, last-seen
age, responder boot ID and timeout count. `devices scan` schedules the next
background check immediately; it does not interrupt active traffic. States:
NOT_SEEN, ONLINE, STALE after30 seconds without new evidence, or FAULT for a
local transport/I2C error. A later successful check restores ONLINE. Silence
alone cannot distinguish absent hardware from firmware without discovery.

Scanning pauses during an active UHF packet cycle, outstanding application requests, pending CAN
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

Walter hardware milestone: full16MiB pre-update flash saved on the bench host
and copied locally with matching SHA-256
`44c99d01b2154e43874c5db0804cf48e869acd58a0ea9f78ed4dbfcfce9317dc`.
Installed Walter0.3.0 from source
`9fcb0209f1bb192369fce34d863a3862f8040de6`, dirty0; esptool verified
all written regions. Application binary SHA-256:
`0fca229ca82b59e115a630d36eadd97c921979ab4afab48b539000abde9fd98c`.
USB `version`/`status` confirmed that identity and modem OFF (`state=0`,
`radio_window_ms=0`, `requests=0`). No RF window was requested. The UART
identity relay and CAN coexistence remain pending the Feather/IHU updates.
Full flash backups are private artifacts, not repository files.

LTE CAN Feather hardware milestone: identified flash ID `DF637882D39E4426`,
previously running can-bench-v3. Full8MiB backup passed picotool read-back
verification; local and bench-host copies share SHA-256
`e0acf6f03437c2a3567e2140bb66a7ed37d70a57a429301192c504cb8cd66af0`.
Installed0.8.0 from the same clean `9fcb020` source, with flash verification.
UF2 SHA-256:
`efdce37a4220bf642929b1812e15263b58feef69677bfc4ad24db66f61d2a0fd`.
USB confirmed `role=LTE_CAN_MCU`, version0.8.0, full matching source SHA,
dirty0, CAN normal (`can_ready=1 mode=00`) at500kbit/s, zero error counters,
no pending requests and no active Walter chain. LTE remained isolated from
CAN A; these checks do not yet establish discovery/addressing coexistence.

IHU hardware milestone: identified `DF641455DB822427`, previously can-bench-v7.
Full8MiB backup passed read-back verification and local-copy hash comparison:
`f636fad0362ca93cc56409bfacfa8c1bc070c5e81ef892716ed5e14623f8adc0`.
Installed0.8.0 from clean `9fcb020` with verified flash; UF2 SHA-256
`a3a8a027f5a6a42f2e1a479d7dec671874774ae50dbb14049ba1010b38aa678f`.
USB confirmed the full source identity. Automatic discovery reported EPS and
COMMS ONLINE and isolated LTE NOT_SEEN. `hello comms` completed and `ping 32`
returned all32 expected bytes. Final CAN status: normal500kbit/s, TEC/REC0,
EFLG00, no TX failures/timeouts, RX errors/overflows or fragment errors;
no pending requests, UHF mode0 and zero RF submissions. Both-node coexistence
still requires connecting upgraded LTE.

Subsequent integrated-stack test passed: after resetting the host USB controller
to recover the missing IHU console (USB disk unmounted), automatic discovery
reported COMMS and LTE ONLINE with distinct boot IDs and no discovery timeouts
for either. Independent HELLO and32-byte echoes passed on both application
routes. IHU read LTE_CAN0.8.0 and Walter0.3.0 identities, both clean `9fcb020`,
through CAN and the Feather/Walter UART relay. Walter status remained OFF with
zero RF window and zero modem sends. Final IHU status showed seven matched
requests, zero CAN errors, TX failures/timeouts, RX/fragment errors, unknown
responses or pending work. The first HELLO met the discovery busy guard and
was explicitly retried successfully after discovery finished. No RF was started.

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
- [x] Save and verify backups of the identified LTE Feather and Walter.
- [x] Flash/verify LTE candidates with LTE still disconnected from CAN A.
- [x] Flash/verify IHU migration and confirm COMMS-only operation first.
- [x] Connect upgraded LTE with appropriate two-end termination; observe both
  discovery replies and independent HELLO/echo/identity queries, RF disabled.
- [x] Update COMMS/receiver/MDB for new identity messages, query both LTE CPUs,
  and verify original identity bytes through bounded UHF into Yamcs.
- [x] Visually inspect both new live identity displays and audit a new Yamcs
  asset manifest. Deployed Yamcs assets1.1.0 and receiver2.1.0 match their manifests.

Prior LTE source needed its pending PR #20 native SYSTEM_STATUS allowlist;
that small forwarding change is retained here. No other #19/#20 deployment
or networking changes are included. This branch builds on PR #21.

RF deployment result: COMMS0.23.0 installed with full2MiB backup and verified
flash. Original backup SHA-256:
`839cff3f4159bf78cb183725a3ff2e904f6587bb5728c3173390915b6464a5ee`.
The 120-second receive session forwarded six of six packets with no receiver
errors. Both LTE identities, COMMS identity, HEARTBEAT, SYSTEM_STATUS and
POWER_STATUS matched transmit bytes and new Yamcs `eps-uhf-in` archive entries
exactly. Both identity dashboards visibly rendered their actual versions,
clean source SHA and distinct device boot IDs. TX stopped and Si5351 outputs
verified disabled afterward. See ground/releases/README.md for installed
versions, manifest scope and reproducible UHF freshness settings.

## Device status downlink (IHU 0.9.0 / COMMS 0.24.0)

DEVICE_STATUS (53) carries a version1,72-byte payload: payload_version and
scan_paused bytes, followed by five14-byte records in registry order (EPS,
EPS_NEXT, COMMS, LTE, PAYLOAD). Each record has state8, seen8, age_ms32,
boot_id32 and timeouts32, with integers big endian. Never-seen age is UINT32_MAX;
seen is authoritative. Header boot and uptime identify the reporting IHU.

`uhf devices` sends a manual snapshot through the selected COMMS route. Each
explicit bounded `uhf run` cycle now sends heartbeat, system, EPS and device
status (four packets). Discovery can run between completed cycles, never while
application packets/results or CAN transmission are pending; a pending discovery
reply delays the next telemetry cycle. No additional RF window or boot transmit
is introduced. At short periods scan opportunities may be limited: device age
and STALE report that limitation honestly. Existing run duration/period bounds
and no catch-up/retry behavior remain.

Devices.opi and Devices.par show the snapshot; NOT_SEEN means no verified reply
since IHU boot, not proof of physical absence. EPS_NEXT/PAYLOAD are labelled
planned. STALE is assigned by IHU after30 seconds without evidence; FAULT is a
local interface/read fault. Yamcs snapshot expiration (90-second expected
interval under the existing processor policy) is separate from device state.
RF-off means the display eventually expires and retains historical rows.

Device downlink hardware validation (October17): IHU0.9.0 and COMMS0.24.0
installed with verified flash and full prior-image backups; both reported clean
source `f4a6a0a881d2be75463024e722dbe3880b54460e`. A60-second,10-second-period
run produced six complete four-packet cycles plus COMMS identity. All25 packets
matched transmitter, receiver and Yamcs archive bytes. All six registry snapshots
showed EPS, COMMS and LTE ONLINE, with fresh LTE observations between cycles;
EPS_NEXT/PAYLOAD remained NOT_SEEN. Receiver100-second session had no errors;
final IHU CAN counters had zero failures/timeouts/errors and no pending work.
RF stopped with TX=0 and Si5351 outputs verified disabled. Devices.opi was
visually inspected with real telemetry. STALE/FAULT/never-seen/wrap semantics
were host-tested; no physical device was disconnected to induce a live failure.
Receiver2.2.0 and Yamcs assets1.2.0 match checked-in manifests.
