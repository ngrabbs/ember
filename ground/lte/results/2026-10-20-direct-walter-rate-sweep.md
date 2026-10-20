# Direct Walter rate sweep — 2026-10-20 UTC

October 19 locally. The sweep stopped at its first failed point; no retries.
Same 512-byte payload, firmware, 115200-baud 8N1 UART, Band 13 profile and 1 m antenna
setup as the [working 1 packet/s point](2026-10-19-direct-walter-512.md).
IHU/CAN and EPS/Yamcs were outside this direct test.

| Offered packets/s | Planned slots | Attempted / modem accepted / received | Unreached slots | Result |
| --- | --- | --- | --- | --- |
| 2 | 20 | 3 / 3 / 0 | 17 | Registration lost; no valid rate |
| 5 | — | Not attempted | — | Stopped by the delivery gate |

Registered READY in 60.574 s. After three modem-accepted 512-byte sends, the modem
reported `+CEREG: 2`; the benchmark stopped with `registration_lost` and held the
modem in reset. Zero rejected, skipped or uncertain sends. All three accepted
packets were absent from the completed ground receiver capture.

The 17 future slots were never attempted; they are not lost packets. No complete
10-second receive window exists, so this attempt has no valid throughput result.
The earlier **4.096 kbps at 1 packet/s** remains the best completed direct point.

The accepted-but-undelivered symptom can occur while bypassing IHU/CAN. Its cause
and any dependence on offered rate remain unresolved; this is not a measured
LTE-M capacity limit.

Walter ended OFF; cell/core/receiver stopped. Zero USB log drops. Ground source,
binary and RF-profile integrity checks passed. No firmware builds/flashes or
production IHU/Walter MCU changes. The temporary Walter image remains installed;
original image backups remain private, with restoration pending after testing.

Private evidence: `.runtime/throughput/lte-direct-rate-20261020-2pps-01/`.
Selected counts/setup are in lab-log entry 005. Raw modem/core logs stay private.

Next: review the saved session-removal trace before reopening the higher-rate
sweep. No blind RF retries; reliability debugging remains paused.
