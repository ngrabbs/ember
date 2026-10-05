# Ten-run native EPS LTE reliability test

Completed 2026-10-02: **6/10 full-chain deliveries**. Eight sends were accepted
by Walter, two were rejected, and two accepted packets never reached the UDP
receiver. All six received128-byte packets match the IHU submission and Yamcs
archive exactly. Receiver rejects and duplicates: zero. All ten runs reached
socket READY and confirmed modem OFF afterward; all IHU CAN transmit/receive/
fragment error counters remained zero.

| Run | RF admission to socket READY (s) | Outcome | Modem OFF |
| --- | ---: | --- | --- |
| 1 | 22.71 | MODEM_REJECTED | Yes |
| 2 | 28.89 | DELIVERED | Yes |
| 3 | 28.87 | DELIVERED | Yes |
| 4 | 26.85 | DELIVERED | Yes |
| 5 | 16.55 | DELIVERED | Yes |
| 6 | 22.73 | DELIVERED | Yes |
| 7 | 16.55 | MODEM_REJECTED | Yes |
| 8 | 16.55 | ACCEPTED_WITHOUT_RECEPTION | Yes |
| 9 | 26.85 | DELIVERED | Yes |
| 10 | 16.55 | ACCEPTED_WITHOUT_RECEPTION | Yes |

READY latency: 16.55–28.89s, median22.72s.
This includes the12-second modem boot wait, registration polling and socket
setup; it is not a precise NAS attach timer. EPC Attach Complete was observed
in 10/10 runs. UTC timestamps are retained
in the evidence.

Each attempt restarted OAI/eNodeB and srsEPC, opened one120-second modem window,
requested one fresh EPS packet through IHU → CAN → COMMS → Walter, and allowed
up to15seconds settling before modem shutdown. Network/capture windows were
bounded separately. Controllers and Walter ESP32 remained powered; these are
modem/network session tests, not whole-system power-cycle tests. Firmware and
radio profile were fixed throughout: seven-candidate OAI, band13, CE300/TX20
profile, Walter application SHA256
`a3ff11d897bd974bae5dd8992b352cde483682cbd098786fcc8ba7debe244d01`.

Run2 received early, exposing an overly short20-second process wait in the
runner. Its packet, archive and OFF evidence were preserved; all remote
processes finished normally. The bookkeeping was repaired and testing resumed
at run3 without repeating the first two runs. This is recorded in run2's note.

[Full report and packets](../../../system/ground_station/evidence/eps-reliability-20261002/report.json).
Private EPC/OAI logs and pcaps remain on ember-ground under
`~/work/ember-lte/logs/eps-reliability-20261002-*`; do not publish subscriber keys.
Controller logs/readouts remain on M75q under the private bench work directory.

Reproduction: with USB on IHU and all boards powered, run
`python3 ground/ember/lte_reliability.py --label UNIQUE_LABEL --output PRIVATE_OUTPUT`.
The runner uses the existing SSH hosts, staged binaries and private runtime
profile; it does not flash firmware. An existing report resumes remaining runs.
Unexpected shutdown verification failure stops the series. Packet reception,
byte matching, archive matching and normal process exits are required separately
for success. Timing-only updates to the host helper do not change radio firmware.

Next: expose detailed modem rejection diagnostics and socket/registration state;
trace the two accepted-but-undelivered packets at the OAI uplink/bearer layer.
Then implement bounded telemetry queues, recovery/backoff and duplicate handling,
and repeat this same test before claiming reliable periodic delivery.
