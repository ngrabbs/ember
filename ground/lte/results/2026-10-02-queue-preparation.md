# Registration-aware admission and bounded EPS queue preparation

Following the fixed-security9/10 delivery series, the Walter candidate rejects
SEND_PACKET unless it is READY, currently registered and has at least16 seconds
remaining. It drains pending registration URCs before checking readiness, while
preserving replies to an already-active AT command. When READY loses registration,
it uses bounded CEREG queries to refresh registration within the existing RF
window. It never extends the deadline. Modem errors still stop RF.

The IHU bench harness now has an opt-in four-packet volatile FIFO. It stores the
original native EPS bytes and identities. It queries Walter status before each
send, waits while OFF/unregistered, and retains packets across explicitly opened
RF windows. No radio window opens automatically. Queue retirement means modem
final OK, not ground acknowledgment; match receiver and Yamcs independently.

## Policy and ownership

`eps enqueue` captures one real EPS readout with no transmission. `lte queue on`
enables service; `lte queue off` stops new queue submissions and leaves any
in-flight request to finish. `lte queue status` reports enabled/count/state/hold,
attempts/accepted/full/retries. `lte queue drop` explicitly discards the oldest
packet when no queue request is active. A fifth enqueue rejects without overwriting.
EPS enqueue also rejects while a CAN exchange is active, because synchronous
I2C reads must not interrupt response reception.

States0idle/1status-query/2send/3held; hold reasons1unknown/2modem-rejected/
3attempts-exhausted/4expired. At most three send attempts per packet. Explicit
pre-submission NOT_READY/BUSY responses back off2 then4 seconds; absent readiness
is polled every2 seconds without submitting a packet. A head packet waiting at
least300 seconds is held at the next admission poll; expiry does not erase it.
Timeout, peer reset, generic link uncertainty and modem rejection hold the FIFO
for inspection. They are not automatically retried. No application-level ground
ACK, persistence, periodic sampling, or automatic power-cycle recovery exists.

This is a bench policy in the IHU harness, using the existing COMMS relay and
unchanged CAN/UART message IDs. Operational transport queues still belong in the
COMMS application per the architecture. Move this tested policy there during
application integration; the bench harness is not the spacecraft IHU application.

## Verification and deployment state

All36 ground tests passed, including native sanitizer-backed FIFO tests for
capacity, byte retention, timer wrap, registration gating, window time remaining,
backoff, attempt exhaustion, uncertain outcomes, rejection, expiry and explicit
drop. The mock Walter test proves that a registration-loss URC pending at send
admission causes NOT_READY with no send AT command/payload; a subsequent CEREG
query can restore admission. These tests do not establish actual RF recovery.
Both Feather targets and the Walter candidate build successfully with the pinned
toolchains. COMMS firmware is unchanged on hardware.

The initial IHU queue image was flashed/readback-verified and hardware-tested:
four actual EPS packets retained with service enabled and Walter OFF; a fifth
rejected; zero send attempts/acceptances; explicit clear then queue disabled.
CAN counters stayed clear. [Radio-off evidence](../../../system/ground_station/evidence/lte-queue-preparation-20261003/radio-off.json).
The initial test image SHA-256 was
`687120561a5d2c6bae3207dd89fe39ac0a6afb54dbf8181555ed13d25579156f`.
The final IHU candidate adds the active-CAN enqueue guard, SHA-256
`0350c02cd01fb1dbb1af452d0656e36e9a72087d9e7219ed7b30c1bea9eeb428`.
Walter candidate application SHA-256:
`69e21cca9d8edfbc4ec512a905f73948d834ac5b5c302b01284bad3b52cccb20`.
Both final candidate images are installed and verified. Walter rebooted with
boot2175643340, modem OFF/window0, zero accepted/rejected packets and zero
framing errors. Four flash segments passed hash verification.
[Deployment evidence](../../../system/ground_station/evidence/lte-queue-preparation-20261003/deployment.json).
The [subsequent queued OTA test](2026-10-02-queued-eps.md) delivered all three
original packets into Yamcs, after radio-off retention, and confirmed OFF. The
earlier ten-run test used the old admission firmware, not this candidate. Forced
registration-loss recovery remains unqualified.

The private8MB IHU pre-queue flash backup was saved and verified on M75q:
`/media/ngrabbs/BACKUP-A/ember-walter-bridge/ihu-before-queue-20261003.uf2`,
SHA-256 `9a4263fd2f882bad54736e5b172898b98ccf7fd122abda4fcd35b38f8b795683`.
After verified backup, the immediate load encountered USB re-enumeration; the
separate retry succeeded. Backup restoration has not been exercised.

`ground/ember/eps_queue_trial.py --port IHU_SERIAL --count 3 --seconds 120
--output PRIVATE_DIRECTORY` runs the next bench test. Start bounded receiver,
eNodeB/EPC and capture first. The test verifies an empty queue, captures hardware
EPS packets, exercises radio-off retention, enables one RF window and queue
service, collects exact FIFO modem acceptances, disables service and requests OFF.
It saves packet identities for independent byte comparison against UDP/Yamcs.
It will not discard preexisting queue contents or claim modem OK as reception.

The final IHU active-CAN enqueue guard subsequently passed on hardware;
[guard evidence](../../../system/ground_station/evidence/lte-queue-preparation-20261003/final-guard.json).
