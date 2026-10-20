# Direct Walter delivery check — 2026-10-19

One bounded direct-Walter run passed. This is a low-rate baseline, not maximum
LTE-M throughput. IHU and Walter MCU firmware stayed unchanged.

Path: USB → Walter ESP32 → modem UART/AT → LTE-M → LibreSDR → separate UDP 51002
receiver. Same Band 13 profile, stock LibreSDR antennas, full-band Walter antenna,
1 m over-the-air separation. Temporary Walter image 0.1.0; UART 115200 baud, 8N1.

| Item | Result |
| --- | --- |
| Registered READY | 60.094 s after opening the window |
| Packet size / offered rate / duration | 128 bytes / 1 packet/s / 10 s |
| Planned / attempted / modem accepted / received | 10 / 10 / 10 / 10 |
| Skipped / rejected / uncertain / missing | 0 / 0 / 0 / 0 |
| Duplicates / late / malformed | 0 / 0 / 0 |
| Received application goodput | **1.024 kbps** |
| Actual modem release (`AT+CGMR`) | `UE8.2.1.0` |
| Registered operator response | `+COPS: 1,2,"99970",7` |
| USB log drops | 0 |
| End state | Walter OFF; cell/core/receiver stopped |

Goodput counts the complete 128-byte UDP payload, including its 32-byte benchmark
header, over a 10-second receive window beginning at the first valid arrival.
CRC and deterministic content were checked. No one-way latency or maximum-rate
claim. This single pass does not resolve the earlier intermittent failures.

Original ground sources, binaries and baseline RF profile passed integrity
checks. No builds or flashes this run. The temporary Walter image remains
installed; original-image restoration is pending after temporary tests.

Private evidence: `.runtime/throughput/lte-direct-smoke-20261019-01/`.
Selected counts and receipts are in lab-log entry 005. Raw modem/core logs and
original flash images remain private. Reliability debugging stays paused.

Next: qualify 512-byte packets at 1 packet/s, then sweep offered rates. Keep the
production IHU unchanged and stop on failed bring-up rather than blind retries.
