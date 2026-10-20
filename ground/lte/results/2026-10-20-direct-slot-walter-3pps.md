# Direct Walter: 3 packet/s pacing check

2026-10-20 UTC / October 19 local. One bounded RF window,
`lte-direct-slot-3pps-20261020-01`, run 2026102007. Same candidate radio,
512-byte synthetic UDP payload (including 32-byte benchmark header),
115200-baud modem UART, debug profile and 1 m antenna spacing. Only requested
rate changed from the preceding 5 packet/s point. IHU/CAN/EPS/Yamcs bypassed.

| Item | Result |
| --- | --- |
| Registered READY | 16.504 s |
| Requested packets/s / offer seconds | 3 / 10 |
| Attempted / modem accepted / valid received | 30 / 30 / 30 |
| Within ten-second receiver window / late during drain | 23 / 7 |
| Received goodput / offered rate | **9.4208** / 12.288 kbps |
| First-to-last arrival span | 12.520026689 s |
| Missing / duplicate / malformed / out of order | 0 / 0 / 0 / 0 |
| Skipped / rejected / uncertain / unreached | 0 / 0 / 0 / 0 |
| Actual OAI / EPC child exits | 124 / 124, planned timeouts |
| Post-run integrity / final Walter state | 12/12 passed / OFF |

All 30 packets passed CRC/body checks. Seven arrived outside the fixed ten-second
receiver window, during the ten-second drain after sending. Received goodput is
23 × 512 × 8 / 10 / 1000. No packet remained missing, but the receiver still fell
behind the offered pace. A first-to-last span is not one-way radio latency.

This is one short application result, not maximum capacity or repeatability.
Reducing the offer from 5 to 3 packet/s reduced the delayed tail but did not
eliminate it in this comparison. Different sessions can differ; no bottleneck
or general sustainable-rate threshold has been established. Best measured
direct goodput remains **11.8784 kbps** from the 5 packet/s point. Full-path best
remains 3.072 kbps.

No NPRB assertion; one completed RRC setup context observed. SRB1 retry cleanup
followed commanded OFF. The previous two-context crash path remains unqualified.
All ground processes stopped, candidate source/binary/cache/libraries/profiles
matched their manifest. No source changes, builds, flashes or second RF window.
Walter temporary firmware stays installed/OFF; original backups retained.
USB raw-byte/chunk accounting passed (12,759 bytes), no parse errors/log drops.
Raw logs remain private; selected counts and all receipts saved in lab-log 005.

Next: one 512-byte, 2 packet/s run over 30 seconds, with a separate 10-second drain.
Use a fresh run ID, maintain the 120-second modem cap and require 46 seconds of
remaining window before admitting the 30-second send. No automatic retries.
This checks pacing over a longer interval; it does not assume 2 packet/s is stable.
