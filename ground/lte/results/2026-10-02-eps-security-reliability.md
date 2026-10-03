# Ten-run EPS reliability after SRB2 security correction

Nine of ten independent attempts delivered real EPS POWER_STATUS through
IHU → CAN → COMMS → Walter UART → LTE-M/LibreSDR → OAI/srsEPC → UDP → Yamcs.
Every delivered packet matched all128 bytes at the IHU, receiver and archive.
Eight attempts passed the complete acceptance criteria, including diagnostic
query completion. All ten reached socket READY and confirmed Walter OFF/window0.

[Full packet/status/archive evidence](../../../system/ground_station/evidence/eps-security-reliability-20261003/report.json).
[Fixed baseline](../../../system/ground_station/evidence/eps-security-reliability-20261003/baseline.json).
[Radio metadata and final binary hash](../../../system/ground_station/evidence/eps-security-reliability-20261003/radio-summary.json).

## Fixed procedure

Runs took place October2, 2026 in America/Chicago; UTC timestamps are October3,
00:50:06–01:16:14. Each attempt starts a fresh bounded eNodeB/EPC and modem
window, sends one fresh EPS packet with no send retries, then stops the modem.
Modem deadline120 seconds, post-READY settle15 seconds; network processes have
independent deadlines. The controller boards remained powered throughout.
These are ten separate cell/modem windows, not ten whole-stack power cycles.

The eight-candidate OAI binary, including negotiated new-bearer security, stayed
unchanged: SHA-256
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`.
Profile `enb.band13.emtc.ce300tx20diag.conf`, antennas separated6–8feet,
IHU/COMMS/Walter diagnostic images unchanged. Both CAN controllers were restored
to normal mode before starting; battery-only EPS ADC was explicitly enabled.
Cached diagnostics were requested consistently without extra modem AT probes.
Recorder commit `cb3d92b` separately checks eNodeB/EPC child exits, because the
radio wrapper can return zero after a child failure.

## Results

| Attempt | IHU sequence | READY elapsed (s) | Exact UDP + Yamcs | Complete pass |
| --- | --- | --- | --- | --- |
| 1 | 6 | 26.849 | Yes | Yes |
| 2 | 7 | 16.546 | Yes | Yes |
| 3 | 8 | 49.531 | Yes | Yes |
| 4 | 9 | 20.675 | Yes | No: diagnostic reply |
| 5 | 10 | 26.858 | Yes | Yes |
| 6 | 11 | 39.226 | No: send rejected | No |
| 7 | 12 | 16.530 | Yes | Yes |
| 8 | 13 | 20.674 | Yes | Yes |
| 9 | 14 | 22.736 | Yes | Yes |
| 10 | 15 | 26.858 | Yes | Yes |

READY elapsed includes modem boot/configuration/socket opening, not just attach:
minimum16.53 seconds, median24.79, maximum49.53. Nine sends were modem-accepted;
all nine arrived and were independently matched to the Yamcs archive. Receiver
rejects and duplicates were zero. Each received packet has IHU boot979862082,
hardware provenance2, fresh readout, ADC-valid1 and conversion-valid1. Current
conversions retain unverified10mΩ sense-resistor assumptions.

Attempt4 delivered sequence9 correctly, but the subsequent cached diagnostic
query returned `UNKNOWN_REMOTE_LINK reason=6` for request159 instead of LTE_DIAG.
The host assertion returned exit1; its cleanup still collected later diagnostics
and confirmed OFF. IHU cumulative unknown replies increased1→2 at this attempt.
This is a controller query failure, not a lost EPS packet. It remains open.
[Selected error trace](../../../system/ground_station/evidence/eps-security-reliability-20261003/run04-diagnostic-error.txt).

Attempt6 reached READY, then cached diagnostics showed CEREG2 (searching),
registered0 and one registration loss before the send. Socket-open success is a
historical flag and did not imply a currently usable link. The send was rejected
with text CME `operation not supported`, no prompt and no final send OK.
Ground received nothing. Its radio log contains five reestablishment-request
mentions; those are log mentions, not a count of distinct over-the-air requests.
This directly motivates registration-aware send admission and bounded recovery.

All ten eNodeB/EPC children ended at their scheduled deadlines with exit124.
No assertion or maximum-retransmission lines were found in these logs; only
attempt6 logged reestablishment-request mentions. No eNodeB/EPC remained running
at final inspection. IHU CAN TEC/REC and fragment/timeout/overflow counters stayed
zero; cumulative tx_fail stayed1 from the earlier pre-series configuration-mode
HELLO failure. COMMS boot1875991883 stayed constant. No firmware was changed.

## Interpretation and next work

Delivery improved from the preceding6/10 series to9/10 in this bounded sample.
The new recorder also applies stricter process/diagnostic acceptance:8/10 passed
all checks. Ten attempts do not establish a statistical reliability guarantee
or prove that the security correction explains every previous failure.
The separate ULSCH allocation and PHY simulation regression issues remain open.

Next, gate sends on current registration, retain rejected telemetry in a bounded
queue with backoff, and trace the COMMS diagnostic timeout. After qualification,
add periodic EPS telemetry. CAN startup after reset, continuous service, downlink
commands, GPS exchange and spacecraft RF/timing validation remain separate work.
Raw subscriber-bearing radio logs and pcaps remain private on the ground host.
