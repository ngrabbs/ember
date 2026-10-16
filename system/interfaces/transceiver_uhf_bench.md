# Transceiver UHF bench admission and results

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

Reply sender is the COMMS boot ID established by HELLO; origin/request match
IHU boot/request. Eight payload bytes: version1, status8, native length16 BE,
CRC32 of the entire native packet32 BE. IHU verifies all fields before changing
request state. Status0 means admitted or local RF completion, depending on the
type; statuses1–4 mean full/invalid/stale/conflicting request;5 means failed RF
attempt (possibly partial);6 means cancelled without an attempt. No reply claims
a ground decode, LTE modem acceptance, or durable storage. A lost reply yields
UNKNOWN, never automatic retransmission.

Explicit COMMS console byte `g` starts ten seconds of collection on CAN A,
with HELLO support, then drains at most four packets and stops. IHU commands
`uhf heartbeat`, `uhf system`, `uhf eps` submit the existing telemetry producers.
Wait for QUEUED before the next request. Submit during collection only: CAN is
in standby during each bounded RF burst. Result replies are sent between bursts.
An arbitrary console byte cancels collection or interrupts a burst; an interrupted
burst is FAILED and remaining queued packets are CANCELLED. Each burst retains
the 1.5-second payload deadline and independent 2-second mute alarm. CAN errors
or an undelivered admission reply prevent the batch from being transmitted.

Queue capacity4; completed-result history8. Repeating an identical request
returns its queued or completed status and does not retransmit. Reusing a
request ID with different payload bytes is rejected. Older IDs outside history
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
