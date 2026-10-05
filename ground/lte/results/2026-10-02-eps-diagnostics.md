# EPS LTE diagnostic trials — 2026-10-02

The physical 96-byte diagnostic service passes over IHU → CAN → COMMS → UART
→ Walter and back. The native 128-byte EPS echo also passes with ADC-valid data.
[Chain evidence](../../../system/ground_station/evidence/lte-diagnostics-chain-check-20261002.json).

Three separate diagnostic trials each submitted one real EPS packet. Walter
observed a send prompt and final OK for all three; the EPC-side receiver saw
zero packets. These are diagnostic trials after the fixed ten-run series,
not additional qualification runs. No modem send rejection was reproduced.
[Report and snapshots](../../../system/ground_station/evidence/eps-diagnostics-20261002/report.json).

| Trial | Walter acceptance | Ground receipt | eNodeB result |
| --- | --- | --- | --- |
| 01 | Yes | No | ULSCH-context assertion; abort |
| 02 | Yes | No | SRB2 max retransmissions, then ULSCH-context assertion; abort |
| 03, metadata trace | Yes | No | SRB2 max retransmissions; bounded normal timeout |

Trial 02 captured registration loss **before** RF shutdown: cached state READY,
registered 0, CEREG 0, one observed registration loss, and approximately 87 seconds
left in the admitted window. Trial 01 only sampled after shutdown, so its loss
counter cannot establish the same ordering. Trial 03 still reported registered 1
before shutdown despite the ground bearer release; modem status can lag ground
state. Historical socket-open OK is not a live socket health check.

## Trace checkpoint

Trial 03 temporarily applied the existing RLC/HARQ metadata patch. It used the
same RF parameters as trials 01/02, with RLC debug logging. All timestamps below
are UTC ground-log collection times. RNTI 48e0 reached:

| UTC time | Event |
| --- | --- |
| 22:02:22.171–571 | SRB1 STATUS ACK_SN progressed through 1, 2, 3, 4, 5, 6, 8 |
| 22:02:22.753 | SRB2/LCID2 downlink PDU, 61 bytes, SN0 |
| 22:02:22.769–23.869 | Repeated SN0 retransmissions; VT_A0/VT_S1; no SRB2 STATUS acknowledgment observed |
| 22:02:23.869 | SRB2 maximum retransmissions reached |
| 22:02:23.870 | EPC UE Context Release Completed |

HARQ feedback includes ACK, NACK, and DTX during this interval. HARQ ACK does
not by itself prove an RLC SDU or application packet was delivered. Correlation
to each MPDCCH/PDSCH transmission still needs scheduler/PHY inspection.
The metadata trace stores lengths, counters and entity mapping, not PDU payloads.
[Selected events](../../../system/ground_station/evidence/eps-diagnostics-20261002/run-03-radio-metadata.json).

The earlier assertion is in `openair1/SCHED/fapi_l1.c`, calling
`find_ulsch(..., SEARCH_EXIST_OR_FREE)`. The implementation in
`openair1/PHY/LTE_TRANSPORT/dci_tools.c` returns -1 when it finds neither an
active matching context nor an allocated context with a zero HARQ mask. This
points to context exhaustion/unavailability after repeated random-access
attempts. It does not establish why masks/contexts were not reclaimed or why
the initial SRB2 transmission failed. Do not simply remove the assertion.

## Follow-up and limits

Trace dedicated SRB2 MPDCCH/PDSCH allocation, retransmission parameters and
HARQ/PUCCH association; separately instrument ULSCH allocation and cleanup during
reconnects. Capture an actual modem rejection with the new CME diagnostics.
Then add registration-aware send admission and bounded recovery/queueing, and
repeat qualification. Queueing alone cannot repair the observed bearer failure.

The unchanged ten-run result remains six deliveries out of ten. These trials
do not qualify continuous operation, downlink commands, GNSS or flight use.
All three trials confirmed Walter OFF/window0 and all network/receiver processes
ended. Temporary source instrumentation was reversed and the normal eNodeB
rebuilt; its SHA-256 was checked against the pre-trace binary. Raw OAI/EPC logs
remain private on the Pi; subscriber records are not committed.
