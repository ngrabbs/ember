# Transceiver UHF bench admission and results

Operator packet coverage and pacing: [transmission matrix](../../docs/user/ihu-can-console.md#transmission-matrix).

This additive protocol uses the existing version-1 CAN fragment/COBS envelope
and IDs IHU `0x710`, COMMS `0x711`. It does not change CF_CHAIN, LTE requests,
native telemetry, or the RF framing. Both endpoints must run the UHF-aware
firmware. Constants live in `firmware/comms_transport/uhf_link.h`.

| Envelope type | Meaning |
| --- | --- |
| 0x80 CF_UHF_SEND | Request one transmission of the unchanged native telemetry payload |
| 0x81 CF_UHF_ADMITTED | Packet validated and retained in the volatile queue |
| 0x82 CF_UHF_RESULT | Local RF attempt completed, failed, or was cancelled |
| 0x83 CF_UHF_REJECTED | Request was not admitted |
| 0x84 CF_UHF_FIRMWARE | Zero-payload request for one COMMS-generated firmware RF packet |

Reply sender is the COMMS boot ID established by HELLO; origin/request match
IHU boot/request. Eight payload bytes: version1, status8, native length16 BE,
CRC32 of the entire native packet32 BE. IHU verifies all fields before changing
request state. Status0 means admitted or local RF completion, depending on the
type; statuses1–4 mean full/invalid/stale/conflicting request;5 means failed RF
attempt (possibly partial);6 means cancelled without an attempt. No reply claims
a ground decode, LTE modem acceptance, or durable storage. A lost reply yields
UNKNOWN, never automatic retransmission.

COMMS **0.33.0** accepts valid IHU UHF requests through healthy idle CAN at
boot, without a COMMS USB console lease. IHU **0.14.0** requires the local
`uhf_telem` permission and a fresh COMMS HELLO. `uhf heartbeat`, `uhf system`,
`uhf eps` or a bounded `uhf run` submit existing telemetry producers. Permission
alone starts no generator. Admission is acknowledged before RF begins; no
admission reply means no drain, and the fault latches until reboot.

An admitted telemetry request is drained immediately. One COMMS firmware
identity burst precedes the first such request after COMMS boot; successful
identity transmission sets a boot-scoped flag. Later requests, IHU reboots and
diagnostic windows do not repeat it. CF_UHF_FIRMWARE requires an empty payload
and requests exactly one fresh identity, even after announcement; it also sets
the same flag on success. Its reply length/digest describe the empty request.
No identity is emitted merely at boot or on a failed/rejected admission. After terminal results,
CAN A returns to normal and RF remains muted until another request. Each burst
retains the 1.5-second payload deadline and independent 2-second mute alarm.
CAN is quiesced during RF, so wait for a terminal result before another manual
send. An arbitrary COMMS console byte can cancel/interrupt a diagnostic burst.
CAN, RF/clock or idle clock-disable failures latch the board unavailable until
reboot. There is no boot-time RF, timed permission expiry, automatic producer,
or retransmission after uncertain RF. Ground reception is separate.

The `a` (timed) and `g` (batch) COMMS console tests remain diagnostic options;
the historical gate they opened is not required for on-demand transmission.

Queue capacity4; completed-result history8. Repeating an identical request
returns its queued or completed status and does not retransmit. Reusing a
request ID with a different request type or payload bytes is rejected. Older IDs outside history
are rejected by the per-origin high-water mark. The state is volatile: COMMS
reset changes boot ID and loses queue/history. A different IHU origin can take
over only when the queue is empty and resets history/high-water. This is a
single-IHU bench protocol, not persistent delivery or multi-origin arbitration.

IHU tracks up to four outstanding results. Admission has the existing5-second
request timeout; a queued packet has a30-second result timeout measured from
submission. Admission releases the synchronous pending slot while retaining the
result tracker. Status reports `uhf_pending`. No periodic forwarding is enabled
by these commands. Legacy `f` remains the one-shot, no-application-ACK bridge.

Validation includes queue capacity/FIFO, duplicate and stale requests, conflicting
bytes, cancellation/failure history, peer/origin/request/digest/length validation,
and hardware batch/abort tests recorded in the lab log. RF completion does not
qualify modulation quality, range, or the receive chain.

## Historical timed operating mode (COMMS v20 / IHU v5)

The manual COMMS lease below is superseded by 0.32.0. IHU 0.13.0 also removes
the legacy automatic telemetry and LTE queue controls described here.

Inspired by rt-ihu's separation of boot, downlink state control, telemetry
collection and radio execution. This is still EMBER bench firmware, with no
launch/deployment logic, persistent transmit enable, automatic power-mode
transitions, or demonstrated RF receive path.

Boot leaves the generator IDLE and the radio muted. Explicit COMMS `a` opens a
maximum180-second service permission window (up to96 RF attempts). The service
alternates LISTEN and bounded transmit/result handling, returning to LISTEN
between packets. It reserves2.5 seconds before window expiry for shutdown and
will not start another burst in that interval. Any COMMS console byte stops it,
including before another queued burst starts. `g` retains the finite batch test.

After normal CAN and HELLO, IHU `uhf run 120 10` enables a120-second producer
run, starting a heartbeat/system/EPS cycle every10 seconds. Duration range1–120
seconds, cycle period5–60 seconds. Only one packet is outstanding; the next
waits for its RF result and a250 ms turnaround guard. Delayed cycles do not
accumulate into catch-up bursts. Missing/failed results, bus faults or an EPS
read/submission failure stop production in FAULT. Health packets report the
configured cycle period. Modes:0 IDLE,1 RUNNING,2 EXPIRED,3 STOPPED,4 FAULT.

`status` is allowed during the run. `uhf stop` stops future production; an
already admitted packet may finish. Use COMMS stop for immediate RF interruption.
Other IHU console operations are refused while RUNNING; existing automatic
telemetry and LTE queue must be off before starting. All run state is volatile:
reset returns to IDLE and never resumes a prior run. An expired/stopped/faulted
run requires a fresh explicit command. The COMMS permission window must cover
the whole generator run; it is independent of IHU timing and never auto-renews.

On the ground, use a finite receiver capture covering the run. capture.py now
accepts1–180 seconds; retained IQ is decoded and optionally forwarded after the
capture ends. This is not yet a continuously running ground decoder service.
Local RF completion and independent Yamcs byte verification remain separate.

## Historical boot CAN service (v21 / IHU v7)

The idle UHF_DISABLED behavior below is superseded by 0.32.0.

CAN A now listens at boot and after bounded RF service ends. Idle discovery,
HELLO and ECHO do not enable RF. Idle UHF requests receive REJECTED status7
(UHF_DISABLED). IHU CAN also enters normal mode at boot; `devices` reports the
central [device registry](device_registry.md). The application HELLO and explicit
RF window are still required before transmitting. Background discovery pauses
during a UHF run so it does not collide with CAN-muted RF bursts. CAN B remains
standby. This supersedes earlier descriptions of idle CAN configuration mode.
