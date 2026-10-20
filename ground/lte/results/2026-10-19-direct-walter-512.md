# Direct Walter 512-byte check — 2026-10-19

The 512-byte point passed. Same setup as the
[128-byte baseline](2026-10-19-direct-walter-smoke.md); only payload size changed.

| Item | Result |
| --- | --- |
| Packet size / offered rate / window | 512 bytes / 1 packet/s / 10 s |
| Planned / attempted / modem accepted / received | 10 / 10 / 10 / 10 |
| Received application goodput | **4.096 kbps** |
| Skipped / rejected / uncertain / missing | 0 / 0 / 0 / 0 |
| Duplicates / late / malformed / out of order | 0 / 0 / 0 / 0 |
| Registered READY | 38.385 s |
| USB log drops | 0 |
| End state | Walter OFF; cell/core/receiver stopped |

USB → Walter ESP32 → modem UART/AT → LTE-M → LibreSDR → separate UDP 51002 receiver.
Same Band 13 profile, 1 m antenna separation, temporary image 0.1.0 and 115200-baud 8N1
UART. Actual modem release `UE8.2.1.0`.

CRC and deterministic packet content were checked. Goodput includes the complete
512-byte UDP payload, including the 32-byte benchmark header, over 10 seconds from
first reception. This is a paced result, not maximum LTE-M throughput or a
reliability result. IHU/CAN and EPS/Yamcs were outside this measurement.

Ground source/binary/profile integrity passed. No firmware builds or flashes.
Original images remain backed up privately; temporary Walter image stays
installed until testing is finished. Production IHU and Walter MCU unchanged.

Private evidence: `.runtime/throughput/lte-direct-512-20261019-01/`.
Selected counts/setup and packet receipts are in lab-log entry 005. No raw modem
or core logs published. Reliability investigation remains paused.

Next: keep 512-byte packets and test 2 and 5 offered packets/s with explicit receiver
checks between points. Stop on registration loss or uncertain send outcomes.
