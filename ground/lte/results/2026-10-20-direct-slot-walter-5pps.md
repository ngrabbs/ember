# Rebuilt ground radio: 5 packet/s delivery comparison

2026-10-20 UTC / October 19 local. One bounded RF window,
`lte-direct-slot-5pps-20261020-01`, run 2026102006. Same 512-byte direct benchmark,
115200-baud modem UART, one AT send in flight, debug profile and 1 m antenna
separation. Only ground change is the MPDCCH append-slot patch/rebuild.

| Item | Result |
| --- | --- |
| Registered READY | 16.284 s |
| Requested packets/s / offer seconds | 5 / 10 |
| Attempted / modem accepted / valid received | 50 / 50 / 50 |
| Within fixed ten-second receiver window / late | 29 / 21 |
| Received goodput / offered rate |**11.8784** / 20.48 kbps |
| First-to-last arrival span | 15.700036160 s |
| Missing / duplicate / malformed / out of order | 0 / 0 / 0 / 0 |
| Skipped / rejected / uncertain / unreached | 0 / 0 / 0 / 0 |
| Actual OAI / EPC child exits | 124 / 124, planned bounded timeouts |
| Post-run candidate integrity | 12/12 passed |
| Final Walter state | OFF confirmed |

All 50 packets passed CRC/body checks. Twenty-one arrived after the fixed
ten-second window, during the ten-second drain following send completion.
Received goodput is 29 × 512 × 8 / 10 / 1000, counting the 32-byte benchmark header.
All offered data eventually arrived, but delivery fell behind the offered pace;
20.48 kbps is not the measured sustainable receive rate. This is one short direct
ESP32/modem/SDR/UDP result, outside IHU/CAN/EPS/Yamcs—not maximum LTE-M capacity
or a repeatability qualification.

The preceding unpatched 5 packet/s attempt delivered 12/50 and later crashed.
This patched run delivered 50/50 and did not crash. Only one completed RRC setup
context was observed, so the previous two-context crash condition was not
demonstrated. Do not attribute all delivery improvement to this patch or claim
that live crash prevention is proven. SRB1 retry cleanup followed host OFF.

Candidate radio SHA256:
`5b19f79079d0e750b6ac9251982b85a79ab3a0eb1c7574ff3c309033d861871c`.
Profile `enb.band13.emtc.ce300tx20rlcdebug.conf`, RF parameters unchanged.
Cell/core/receiver stopped. Original source/binary rollback snapshot retained;
no further source changes, builds, MCU flashes or second RF window. USB remains
on Walter, temporary image installed/OFF. 18,059 raw USB bytes validated with
chunk accounting; zero JSON errors/log drops. Raw logs remain private.

Best measured direct goodput is now **11.8784 kbps**. Full-path best remains
3.072 kbps. Selected counts and all packet receipts saved in lab-log 005.
Next: one bounded 3 packet/s point to check whether delivery keeps pace at lower
offered load. No automatic retries or larger rate jump.
