# Repeatability and signaling-bearer release — 2026-10-02

The first ten-packet demonstration did not reproduce consistently. A diagnostic
trial with bounded sender retries delivered nine of ten accepted packets, while
other repeats delivered none. RRC/RLC logging identified the immediate context
release trigger: signaling-bearer maximum retransmissions. Stable bench
operation remains unresolved.

## Controlled settings and trials

Antennas stayed at the reported six-to-eight-foot separation. Band 13, DL
751 MHz / UL 782 MHz, 50 PRB, TX gain 69.75, RX gain 35, and single-thread
operation were retained. Network applications were restarted and opening the
existing Walter passthrough reset the ESP/modem for each run. These are reset
starts, not verified hardware power-cycle/cold-boot tests. Thingy remained deferred.

| Run ID | OAI patch set / profile | Sender behavior | Accepted / received |
| --- | --- | --- | --- |
| `udp-repeat-20261002` | Six / `ce300tx20diag` | No socket queries; no retries | 1 / 0 |
| `udp-retry-20261002` | Six / `ce300tx20rrcdiag` | Up to three retries after completed pre-prompt rejection | 10 / 9 |
| `udp-settle-20261002` | Six / `ce300tx20diag` | Same retries; 15-second wait before close/reset | 10 / 0 |
| `udp-dlmcs-20261002` | Seven / `ce300tx20rrcdiag` | Same retries and wait | No send; modem stayed searching after a brief network-side attach |

`ce300tx20rrcdiag` changes only RLC/RRC logging from info to debug relative to
`ce300tx20diag`. Logging overhead and variable acquisition/reconnection mean
these trials do not isolate the effect of each change. A receiver startup
initially found the previous trial still bound to the UDP port; it was restarted
after the old receiver's deadline, before the diagnostic trial's first attach.
No failed bind is counted as a running receiver.

## Release cause traced

In `udp-retry-20261002`:

- 11:45:59.561–563 UTC: RRC Reconfiguration Complete, Attach Complete, EPC sends
  EMM Information.
- 11:46:01.097: RLC reports `max RETX reached on SRB 2`.
- 11:46:01.098: RRC reports radio-link failure for that same radio context.
- 11:46:01.099: context removed after the RRC release timer.

Later contexts again hit SRB2 or SRB1 retransmission limits and were removed.
Service Requests repeatedly restored bearers. This identifies the immediate
release mechanism, not why acknowledgments or signaling delivery failed.
Downlink HARQ/PUCCH, RLC STATUS handling, and reestablishment lifecycle need
further tracing. The network-side timer message alone was insufficient to
identify this cause in earlier info-level logs.

The retry trial received sequences 0–8, each 128 bytes, source 172.16.0.2, zero
duplicates or out-of-order arrivals, over 28.28 seconds. Sequence 9 was accepted
by the modem but never observed at the ground receiver. Socket close then
returned a completed error and recovery reset the modem. Early reset of queued
data is a hypothesis; the follow-up 15-second settling trial still delivered
zero packets, so waiting alone is not a sufficient repair. No latency or
repeatable loss-rate claim is made.

## Sender changes

The default still stops on a rejected send. `--send-retries 3` permits up to
three additional attempts, separated by two seconds, only for a completed
`operation not supported` error before a data prompt/payload submission. It
does not retry after submitting payload, a generic error, or a pending response.
The radio-enable deadline also bounds retries. The same sequence/payload is
retained for a pre-prompt retry. This is an experimental recovery policy;
the modem's internal reason for the rejection has not been established.

`--settle-seconds 15` waits after the accepted-send summary, before socket close
and serial-reset recovery, limited by the remaining enable deadline. This gives
queued data an observation window without claiming the queue is drained.
The accepted-send summary now precedes socket close, so a close error does not
hide the accepted count. Both controls are opt-in. Six focused tests exercise
the real production retry helper, including no resend after payload/timeout
and no command after a deadline expires during backoff. Serial framing and RF
behavior are outside those tests.

## Dedicated downlink scheduler candidate

Source inspection found that `schedule_ue_spec_br` initialized a local MCS to
zero. On a HARQ retransmission it skipped the new-payload MCS calculation, used
zero in MPDCCH, overwrote the saved MCS, and used that changed value for PDSCH
length. The seventh patch loads the saved per-HARQ MCS before either path.
New-transmission MCS calculation remains in place.

Binary after rebuilding:
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`.
The candidate applied after the reconstructed six-patch source and source
whitespace validation completed. No scheduler unit test qualifies this change.
The radio trial still reached RRC Reconfiguration Complete at 11:53:36.866,
then SRB2 maximum retransmissions at 11:53:38.162 and RRC failure at
11:53:38.163. Reestablishment requests began before that RLC failure. The modem
continued reporting search state; the sender therefore submitted no UDP data.
The correction did not eliminate the observed failure.

All seven patches reverse/reapply in order; all 16 affected reconstructed files
match the Pi source. The last trial recorded one RRC Setup Complete, one Msg4
ACK, three Msg4 retries, one exhausted attempt, and nine bounded CCCH timeouts.
No pool-exhaustion or dedicated-config assertion occurred. Its receiver and
packet capture recorded zero traffic. Both network applications exited 124 at
their bounded deadlines. Walter restored its full standard band list and
confirmed CFUN 0 at 11:55:20.338 UTC; no radio, EPC, or capture process remained.

## Remaining work and evidence

Trace dedicated downlink control/payload parameters, HARQ feedback and PUCCH
resource selection, and per-bearer RLC STATUS/acknowledgment processing. Keep
the missing-feedback failure distinct from stale reestablishment-context errors.
Then repeat ten-packet delivery, test idle/reconnect and cold power cycles, and
add a ground acknowledgment before treating modem acceptance as delivery.
The earlier PHY simulator regression also remains unresolved.

Private evidence is on the Pi under `~/work/ember-lte/logs/<run>-*` and the M75q
under `~/work/ember-lte/logs/<run>-walter.log`. Captures for `udp-settle-20261002`
and `udp-dlmcs-20261002` are in the Pi's private directory; subscriber records,
raw logs, and captures are not committed.
