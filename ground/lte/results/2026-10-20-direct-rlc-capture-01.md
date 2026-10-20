# Direct Walter RLC diagnostic — capture aborted

2026-10-20 UTC / October 19 local. One bounded attempt with the existing
`enb.band13.emtc.ce300tx20rlcdebug.conf` profile. Only RLC/RRC log levels changed;
radio parameters and firmware stayed unchanged. USB events had host UTC and
monotonic timestamps; clock probes were recorded before/after.

| Item | Result |
| --- | --- |
| RF windows | 1; no retry |
| Registered READY / benchmark started | Neither reached |
| New benchmark packets attempted / received | 0 / 0 |
| Collector | JSON parsing error during modem configuration |
| Initial collector cleanup confirmation | Failed to parse/confirm |
| Recovery | Independent OFF/status check passed |
| Ground end state | Cell/core/receiver stopped; integrity checks passed |
| Valid rate / SRB failure evidence | None |

The original reader assumed a timed-out USB `readline()` always returned a
complete JSON object. It could instead receive a fragment. That offending
fragment was not retained. A later OFF-only check did retain an incomplete
83-byte status response with no newline; its transport-side cause is unresolved.

The revised private reader buffers fragments across timeouts, bounds line size,
keeps raw bytes plus timestamped chunk offsets, and records malformed complete
lines. Cleanup allows at most three idempotent status queries; telemetry and RF
commands are not automatically retried.

Host checks passed: every split boundary, one-byte reads, multiple lines,
timeout/resume, raw-byte accounting and oversized-line limits. A subsequent
live **OFF-only** check parsed 12 status replies with zero parse errors, confirmed
OFF and opened zero RF windows. It ended without a trailing fragment. The revised
reader has not yet completed an RF capture.

No firmware builds or flashes; IHU/Walter MCU production code unchanged. The
original hypothesis remains unconfirmed. Best completed direct point remains
4.096 kbps. Raw logs and USB captures remain private.

Private evidence: `.runtime/throughput/lte-direct-rlcdiag-20261020-01/`.
Selected results are in lab-log entry 005. Earlier measurement files are unchanged.

Next: one bounded diagnostic using the revised host reader, with a new run ID.
No cable move or firmware build needed. No second RF attempt was made here.
