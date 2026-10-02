# Walter Msg4 retry and SIM authentication

Bench observations from 2026-10-02 UTC. Thingy remained powered down.
Walter was connected to M75q, LibreSDR to Pi, with the established antennas
and approximate six-inch separation. OAI base revision remains
`29d5fa7d38bb1ee8935ef7ae30a396d53772ea4f`, now with the two experimental
patches in `ground/lte/patches`. No Walter firmware or SIM credentials were changed.

## Scheduler change and verification

The Msg4 candidate retains the original payload and NDI across retransmissions,
resends RV 0, schedules a new Type2-common MPDCCH and PDSCH, and programs feedback
again. It preserves feedback explicitly to distinguish ACK from exhausted
retries, both of which use MAC HARQ round 8. Four total transmissions are the
existing MAC limit. Unsupported retry modes are abandoned with resource release.
The exercised scope is FDD CE0, one MPDCCH/PDSCH/PUCCH repetition.

The first rebuild caught a pointer-type mismatch in subframe advancement; it
was corrected before any radio test. The completed target rebuild and whitespace
check succeeded. A standalone CTest test exercises the real production lifecycle
helper in 11 ACK/NACK/DTX/wait/exhaustion cases. It completed with no failed
cases. PHY timing and payload preservation still need broader regression coverage.
No `openair1` source was changed.

## Radio trials

| Run | TX attenuation | Legacy PRACH threshold | CE0 threshold | BR RARs | Msg4 retries | Msg4 ACK | RRC Setup Complete | Stop reason |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| msg4-retry | 30 | 100 | 200 | 12 | 0 | 0 | 0 | DLSCH allocation assertion |
| msg4-ceonly | 40 | 1000 | 200 | 13 | 1 | 1 | 1 | DLSCH allocation assertion |
| msg4-ce300 | 40 | 1000 | 300 | 7 | 0 | 1 | 1 | DLSCH allocation assertion |

TX attenuation 40 logs UHD TX gain 49.75; RX remains 35. These are not calibrated
RF power. Raising the ordinary-LTE threshold is diagnostic suppression of that
detector, not a supported LTE-M-only cell mode. Raising CE0 threshold changes
detection sensitivity; it does not repair allocation/reclamation.
Several parameters changed between the first two runs, so differences cannot
be attributed to any single parameter. The last two differ only in CE0 threshold.

At 10:02:10.872, the ceonly run generated Msg4. It recorded DTX and scheduled
retry round 1 at 10:02:10.880, generated Msg4 again at 10:02:10.883, received
ACK at 10:02:10.891, and decoded RRCConnectionSetupComplete at 10:02:10.956.
This exercises the retry in the live scheduler, rather than merely removing
the old assertion. Its first authentication attempt returned synchronization
failure, and the EPC sent another Authentication Request before OAI aborted.

The ce300 run recorded Msg4 ACK at 10:06:47.354. The EPC then recorded:

- 10:06:47.469: Authentication Request sent.
- 10:06:47.589: Authentication Response received and UE Authentication Accepted.
- 10:06:47.669: Security Mode Complete received.
- 10:06:47.789: Attach Accept added to Initial Context Setup Request.

This establishes accepted SIM authentication and NAS security-mode completion
through the LTE-M radio path. It does not establish completed attach or an IP
telemetry bearer: no Attach Complete, Initial Context Setup Response, or RRC
Reconfiguration Complete was observed. A gateway session request/allocation
alone would not establish a usable UE data path. Walter did not report registration.

## Remaining failure

All trials aborted at `dci_tools.c:1539`, `fill_mdci_and_dlsch`:
`no free or exiting dlsch_context`. The ce300 assertion occurred at
10:06:48.051, following additional BR random-access detections during ongoing
signaling. ULSCH exhaustion and the old Msg4 retransmission assertion were not
observed in these trials.

The PHY has eight DLSCH contexts shared by common signaling and UE traffic.
`find_dlsch` only allocates contexts with a zero HARQ mask. RAR identifiers
vary with PRACH timing, and their contexts have no UE HARQ acknowledgment.
Retained RAR contexts and false PRACH detections are candidates for the pool
pressure; exact slot ownership/reclamation needs a trace before implementing
a release fix. Do not assume increasing the pool or thresholds solves this.

Next: trace downlink allocations and release RAR resources after their final
transmission, while preserving contexts still used by scheduled/common traffic
and avoiding collisions with UE identifiers. Then repeat cold-start SIM
resynchronization, authentication, bearer setup, and numbered UDP telemetry.

## Reproduction and evidence

Tracked profiles:
`configs/oai/enb.band13.emtc.ceonlydiag.conf.example` and
`configs/oai/enb.band13.emtc.ce300diag.conf.example`.
Stage either without the `.example` suffix and select it using the bounded
Pi helper's `--config` argument. Use the controlled runbook and wait for
steady state before enabling Walter. These are diagnostic profiles, not defaults.

Private Pi logs: `~/work/ember-lte/logs/msg4-{retry,ceonly,ce300}-20261002-*`
and `build-msg4-retry.log`. M75q has corresponding modem logs. The summary
helper counts only events/temporary-context releases; full logs and subscriber
material remain outside Git. Its `harq0_dtx` count includes later dedicated
signaling, so it is not a count of Msg4 failures specifically.

Walter's full standard band list was restored and CFUN 0 confirmed at
10:07:14.470. All bounded radio/core sessions were stopped after testing.

Protocol references checked:
[ETSI TS 136 213 V13.6.0](https://www.etsi.org/deliver/etsi_ts/136200_136299/136213/13.06.00_60/ts_136213v130600p.pdf),
sections 7.1/7.1.7.1, 10.1.2.1, and 10.2, for Type2-common Msg4 reception,
RV mapping, and HARQ feedback resources/timing. This review and the bench
observations do not establish full conformance of the candidate.
