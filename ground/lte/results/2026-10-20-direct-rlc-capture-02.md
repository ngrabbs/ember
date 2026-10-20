# Direct Walter diagnostic — completed delivery

2026-10-20 UTC / October 19 local. One bounded RF window, label
`lte-direct-rlcdiag-20261020-02`, run 2026102004. Revised USB reader; existing
RLC/RRC-debug profile changes logging only. Same firmware, radio settings and
1 m antenna separation as before.

| Item | Result |
| --- | --- |
| Registered READY | 16.854 s |
| UDP payload / requested rate / duration | 512 bytes / 2 packets/s / 10 s |
| Attempted / modem accepted / valid received | 20 / 20 / 20 |
| Received goodput | **7.7824 kbps** |
| Skipped / rejected / uncertain / unreached | 0 / 0 / 0 / 0 |
| Missing / duplicate / late / malformed / out of order | 0 / 0 / 1 / 0 / 0 |
| USB JSON errors / firmware log drops | 0 / 0 |
| Walter final state | OFF confirmed |

Goodput counts the complete 512-byte UDP payload, including the 32-byte benchmark
header, over ten seconds from first valid arrival. 19 packets arrived within that
window; the final packet arrived 10.079680 s after the first, about 80 ms late.
All 20 eventually arrived. Offered rate was 8.192 kbps. CRC/body checks passed. This
is a paced direct ESP32/modem-UART/AT result; IHU/CAN/EPS/Yamcs are outside this
test. It does not establish maximum LTE-M throughput or repeated reliability.

The earlier registration-loss failure did not recur. Debug logs include SRB1
maximum-retry cleanup after commanded OFF, roughly 25 seconds later. This is a
shutdown reference, not evidence of the earlier live-session trigger. That
hypothesis remains unconfirmed. No higher-rate attempt or second RF window here.

The revised reader retained 10,105 raw USB bytes with timestamped chunk offsets;
complete JSON and byte accounting checks passed, with no trailing fragment.
Raw modem/core/USB data stays private. Ground capture completed; cell/core/receiver
stopped and all ten integrity checks passed. No builds, flashes, or production
IHU/Walter MCU/source changes. Temporary Walter image remains installed/OFF;
original verified restore images remain secured.

Selected counts and packet receipts are in lab-log entry 005.
Next: one gated 512-byte, 5 packet/s point using a fresh run ID, if continuing
the rate sweep. Stop on registration loss, uncertain send, or missing delivery;
do not restart reliability loops.
