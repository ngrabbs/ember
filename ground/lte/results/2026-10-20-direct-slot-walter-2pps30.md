# Direct Walter: 2 packet/s over 30 seconds

2026-10-20 UTC / October 19 local. One bounded RF window,
`lte-direct-slot-2pps30-20261020-01`, run 2026102008. Same candidate radio,
512-byte UDP payload (including the 32-byte benchmark header), 115200-baud modem
UART, RLC/RRC-debug profile and 1 m antenna spacing. Requested rate and duration
changed from the preceding 3 packet/s, ten-second point. IHU/CAN/EPS/Yamcs bypassed.

| Item | Result |
| --- | --- |
| Registered READY | 16.554 s |
| Requested packets/s / offer seconds | 2 / 30 |
| Attempted / modem accepted / valid received | 60 / 60 / 60 |
| Within fixed 30-second receiver window / late | 60 / 0 |
| Received goodput / offered rate | **8.192 / 8.192 kbps** |
| First-to-last arrival span | 29.499925943 s |
| Missing / duplicate / malformed / out of order | 0 / 0 / 0 / 0 |
| Skipped / rejected / uncertain / unreached | 0 / 0 / 0 / 0 |
| Actual OAI / EPC child exits | 124 / 124, planned timeouts |
| Post-run integrity / final Walter state | 12/12 passed / OFF |

All 60 packets passed CRC/body checks. None arrived during the ten-second drain.
Goodput is 60 × 512 × 8 / 30 / 1000, measured over the fixed receiver window
starting at first valid arrival. This point kept pace with the offered rate for
30 seconds. It is not a repeated-reliability result or maximum LTE-M capacity.
The earlier best ten-second burst remains 11.8784 kbps, with a delayed tail.

The 30-second send requires at least 46 seconds left in the 120-second modem
window; the host checked this before admission (103.445 s remained). No window
extension. Only one completed RRC setup context observed; earlier two-context
crash prevention remains unqualified. SRB1 retry cleanup followed commanded OFF.

Candidate binary/source/cache/libraries/profiles match the existing manifest.
Cell/core/receiver stopped, no new source changes, builds, flashes or retry.
Walter temporary firmware remains installed/OFF; restore backups retained.
Raw USB accounting passed (20,709 bytes), zero parse errors/log drops; raw logs
stay private. Selected counts and all receipts saved in lab-log entry005.

Next: at most two matching 2 packet/s, 30-second repeats with fresh sessions/run
IDs, stopping at the first missing/late/uncertain packet, registration loss or
radio failure. That would give a small three-run pacing check before closing
the temporary benchmark and restoring Walter's original firmware.
