# Walter OFF/ON control and OAI Msg3 cleanup

Tested 2026-10-02 UTC. Thingy:91 X was powered down by the user throughout.
Walter and LibreSDR retain the previously confirmed antennas and approximate
six-inch separation. OAI base revision and hardware are unchanged.
Runtime TX attenuation 30 gives logged UHD TX gain 59.75; RX gain is 35.
These are gain settings, not calibrated radiated power.

## Controlled baseline

Walter's CFUN 0 was confirmed before a 40-second OAI run. OAI reached steady
state at 09:34:55.026 and stopped at its deadline without BR random-access
responses, UL CCCH decodes, or either known assertion. EPC and OAI returned
timeout status 124.

In the subsequent run Walter returned OK to CFUN 1 at 09:38:43.839.
OAI generated a CE0 random-access response at 09:38:45.474, decoded UL CCCH
and generated a 41-byte RRCConnectionSetup at 09:38:45.484, then asserted at
09:38:45.494 in the unimplemented BL/CE Msg4 retransmission branch.
The OFF/ON timing and absence of Thingy strongly attribute this access request
to Walter. No subscriber identity was decoded and no EPC authentication or
IP bearer was reached.

Opening Walter's current ESP32 passthrough resets it and the modem. Its boot
radio behavior is not fully established; the test script waits 12 seconds,
then explicitly sets CFUN 0 before setting bands/APN and enabling the radio.
Do not interpret the serial-opening interval as a guaranteed radio-off window.
The separate OFF baseline begins after confirmed CFUN 0.

## Cleanup defect and patch evidence

Both a PHY+MAC debug run and a MAC-only debug run exhausted OAI ULSCH contexts
after eight BR responses. These runs include CRC-failed Msg3 and overlapping
ordinary LTE random-access detections; debugging output changes processing
load, so their differences from the info-level run are not solely RF evidence.

In `eNB_scheduler_ulsch.c`, the BL/CE first-Msg3-failure branch calls
`cancel_ra_proc` without `put_UE_in_freelist`. The latter already queues PHY
release and is used by the ordinary LTE exhausted-retry path. The experimental
patch adds that call before canceling the unsuccessful BL/CE attempt.

| Run | BR responses | BR contexts released | UL CCCH decoded | ULSCH exhaustion | Msg4 assertion |
| --- | ---: | ---: | ---: | ---: | ---: |
| OFF, unmodified | 0 | 0 | 0 | 0 | 0 |
| ON, info, unmodified | 1 | 0 | 1 | 0 | 1 |
| ON, PHY+MAC debug, unmodified | 8 | 0 | 0 | 1 | 0 |
| ON, MAC debug, unmodified | 8 | 0 | 0 | 1 | 0 |
| ON, MAC debug, patched | 11 | 10 | 1 | 0 | 1 |

In the patched run, OAI scheduled Msg4 BR at 09:44:51.725, recorded feedback
value 4 for HARQ process 0 at 09:44:51.733, then asserted on retransmission
round 1. The MAC code treats value 4 as DTX and handles it like NACK.
This means OAI detected no ACK/NACK; it does not establish whether Walter
decoded Msg4 or transmitted feedback. The patch improves resource reclamation
in this bounded run but does not complete random access.

## Reproduction and stored evidence

Private Pi logs: `~/work/ember-lte/logs/`:
`control-off-20261002-*`, `control-on-20261002-*`,
`control-debug-20261002-*`, `control-mac-20261002-*`,
`cleanup-mac-20261002-*`, and `build-msg3-cleanup.log`.
M75q has corresponding `*-walter-20261002.log` files.
Full logs remain outside Git. The helper
`scripts/summarize-ra-log.py` reports the table's counts without printing RNTIs.
Release counts match BR temporary RNTIs against release messages; they are not
a complete PHY allocation trace and reused RNTIs could confound longer runs.

The Pi target rebuild and `git diff --check` completed. The minimal build has
zero registered CTest tests; these are live bench observations, not an automated
unit-test suite. See [patch instructions](../patches/README.md) and the
[controlled runbook](../BRINGUP.md#controlled-walter-offon-tests).

Walter's full standard band list was restored and CFUN 0 confirmed at
09:45:12.426. Bounded OAI/EPC sessions ended; no telemetry link is claimed.

## Next work

1. Preserve this baseline and verify resource reclamation over longer repeated
   failures with an allocation/release regression test.
2. Trace Msg4 MPDCCH/PDSCH scheduling and expected PUCCH resource/timing against
   CE-mode-A rules. DTX can reflect downlink decode failure, uplink reception,
   timing/resource mismatch, or processing problems.
3. Implement bounded CE Msg4 retransmissions with correct RV, persistent payload,
   MPDCCH scheduling, PDSCH timing, feedback, and exhausted-retry cleanup.
4. Only after RRC completes, validate SIM authentication, IP bearer and numbered
   UDP telemetry. Keep Thingy interface work deferred as requested.
