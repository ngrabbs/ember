# RLC acknowledgment trace — 2026-10-02

Walter acknowledged three successive downlink RLC sequence numbers during one
attempt, completing authentication and NAS security. The following RRC Security
Mode Command received no observed RLC acknowledgment and exhausted SRB1 retries.
This identifies a specific failure checkpoint; it does not establish its cause.
None of these three trials registered at the modem or submitted UDP packets.

## Controlled settings and results

All trials used the pinned OAI source with the seven production candidates,
temporary metadata tracing, Band 13, 50 PRB, TX gain 69.75, and the reported
six-to-eight-foot antenna separation. Walter's serial passthrough reset the
ESP/modem at each start. These were not verified power-cycle tests.

| Run ID | Profile suffix | RX gain | RRC Setup Complete | RLC RX / TX / retry events | STATUS / NACK events | UDP submitted / received |
| --- | --- | --- | --- | --- | --- | --- |
| `rlc-status-20261002` | `ce300tx20rrcdiag` | 35 | 2 | 4 / 12 / 10 | 0 / 0 | 0 / 0 |
| `rlc-lowlog-20261002` | `ce300tx20rlctrace` | 35 | 0 | 0 / 0 / 0 | 0 / 0 | 0 / 0 |
| `rlc-rx25-20261002` | `ce300tx20rx25rlctrace` | 25 | 2 | 11 / 19 / 10 | 3 / 0 | 0 / 0 |

The first trial used RLC RX/TX/retry/STATUS tracing and existing MAC debug
feedback. The next two added compact CE HARQ feedback at MAC info level.
`ce300tx20rlctrace` changes only MAC logging from debug to info relative to
`ce300tx20rrcdiag`. The RX25 variant changes only `att_rx` from 30 to 40,
reducing the calculated RX gain from 35 to 25; TX settings are unchanged.

Aggregate HARQ feedback was ACK/NACK/DTX 5/30/22, 6/12/1, and 15/15/27,
respectively. These include Msg4 and any dedicated traffic across contexts;
they are not per-packet delivery statistics. The middle trial never exercised
a dedicated RLC bearer. At MAC info level, the ordinary RA summarizer's DTX
debug matches are unavailable; its zero count must not be interpreted as
zero DTX. The compact trace supplies those counts instead.

## Successful STATUS sequence and next failure

In `rlc-rx25-20261002`, the first context exhausted SRB1 retries at
12:08:34.666 UTC without a STATUS acknowledgment. A later context reached:

| UTC time | Event |
| --- | --- |
| 12:08:57.905 | Downlink RLC data, 46 bytes, SN 0 |
| 12:08:57.923 | STATUS ACK_SN 1, no NACK list; first SDU delivered |
| 12:08:57.964 | EPC authentication accepted; NAS Security Mode Command sent |
| 12:08:57.985 | Downlink RLC data, 25 bytes, SN 1 |
| 12:08:58.003 | STATUS ACK_SN 2, no NACK list; second SDU delivered |
| 12:08:58.004 | EPC NAS Security Mode Complete |
| 12:08:58.065 | Downlink RLC data, 19 bytes, SN 2 |
| 12:08:58.084 | STATUS ACK_SN 3, no NACK list; third SDU delivered |
| 12:08:58.090 | RRC Security Mode Command generated and submitted on SRB1 |
| 12:08:58.166 | Downlink RLC data, 10 bytes, SN 3 |
| 12:08:58.246–686 | Poll/retry sequence; no ACK_SN 4 or NACK STATUS observed |
| 12:08:58.686 | SRB1 maximum retransmissions reached |

The entity address was reused between contexts. Correlate by radio context,
bearer, and time as well as address; it is not a persistent UE identifier.
The STATUS trace prints decoded fields before the handler's full consistency
check. Here the subsequent SDU-delivery and state progression also show that
the acknowledgments were processed. No payload or SIM secrets were added to
the metadata trace, but raw logs still contain private subscriber information.

This proves the STATUS path can work in this setup. It does not prove that
the lower RX gain repairs it, that RLC is generally correct, or that RRC
security configuration caused the missing acknowledgment. Acquisition varied
between attempts, and the previously observed post-attach SRB2 failures remain.
Next, correlate the failing dedicated downlink's MPDCCH/PDSCH parameters and
HARQ/PUCCH outcomes with SN 3. Resolve the outstanding PHY simulator baseline
before qualifying a scheduler/PHY repair.

## Verification and restoration

The temporary trace is saved separately in
[diagnostics](../diagnostics/README.md). It is not an eighth production patch.
After all trials, all three instrumented source files were restored and the
uninstrumented eNodeB rebuilt. Source whitespace checks passed; no trace markers
remain in those files. The restored binary matches the pre-trace SHA-256:
`13ab09bf176773e213dd02f950b96577c6369e9be54723e7a1db1281c14b6d8a`.

All 49 upstream RLC-v2 tests passed using copies of the restored production
sources in a private scratch directory. The upstream driver reports failures
without necessarily returning a failing exit status, so its output was also
checked for `FAILURE`; all 49 `.run` outputs were present and the failure log
was empty. This checks existing RLC behavior, not RF, LTE-M scheduling, or the
unresolved PHY simulation regression.

Each bounded eNodeB/EPC trial exited 124 at its deadline, without an observed
assertion. Walter restored its full band list and confirmed CFUN 0 at
12:03:24.425, 12:07:18.626, and 12:10:34.232 UTC. The final eNodeB/EPC exits were
12:10:45.928 / 12:10:50.905 UTC. No eNodeB or EPC process remained after restore.

Private evidence remains under `~/work/ember-lte/logs/<run>-*` on the Pi and
`~/work/ember-lte/logs/<run>-walter.log` on the M75q. The RLC suite log is
`~/work/ember-lte/logs/rlc-tests-20261002.log` on the Pi. Raw logs and subscriber
records are not committed.
