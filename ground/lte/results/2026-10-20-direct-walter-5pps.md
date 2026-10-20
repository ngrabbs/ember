# Direct Walter 5 packet/s test — partial delivery and eNodeB crash

2026-10-20 UTC / October 19 local. One bounded RF attempt,
`lte-direct-5pps-20261020-01`, run 2026102005. Same temporary Walter firmware,
115200-baud modem UART, RLC/RRC-debug profile and 1 m antenna separation as the
2 packet/s point. Only requested rate changed. IHU/CAN/EPS/Yamcs bypassed.

| Item | Result |
| --- | --- |
| Registered READY | 16.525 s |
| Payload / requested rate / offer duration | 512 bytes / 5 packets/s / 10 s |
| Planned / attempted / modem accepted | 50 / 50 / 50 |
| Received / missing accepted | 12 / 38 |
| In ten-second receiver window / late | 12 / 0 |
| Received goodput / offered rate | 4.9152 / 20.48 kbps |
| Skipped / rejected / uncertain / unreached | 0 / 0 / 0 / 0 |
| Malformed / duplicate / out of order | 0 / 0 / 0 |
| USB parse errors / log drops | 0 / 0 |
| Ground radio exit | -6: fatal assertion |
| Walter final state | OFF confirmed |

Received sequences 0–11 passed CRC/body checks; sequences 12–49 did not appear in
the completed 190-second receiver capture. All receipts were within the fixed
ten-second window starting at first arrival. A ten-second post-send drain
produced no additional receipts. Modem acceptance does not prove delivery.
The summary's `measurement_complete` means the accounting window was captured;
this benchmark **failed delivery and ground-radio checks**.

The OAI eNodeB aborted at 00:32:58.484 UTC on `NPRB > 0` / `NPRB == 0`, in
`fill_dci_and_dlsch()`, `openair1/PHY/LTE_TRANSPORT/dci_tools.c:657`. Source at that
line requires a positive resource-block count after conversion of the downlink
allocation. The crash occurred during drain, after send completion
(00:32:51.358861) and last receipt (00:32:50.322002), before host OFF
(00:33:01.401850). Clock probes were retained; these host/log timestamps do not
establish radio-subframe alignment. Why the allocation was zero, and whether
this explains the earlier missing packets, remain unconfirmed.

Walter still reported registered after drain, despite the earlier ground crash.
That modem status does not establish a working bearer. No SRB retry-exhaustion
or RRC removal marker was captured in this run. This differs from the earlier
registration-loss symptom; a common cause has not been established.

Ground core ended at its bounded timeout (124); the receiver completed normally.
Coordinator/helper exit 0 is not a radio pass: the child radio exit was -6.
All ten source/binary/profile/end-state integrity checks passed. Cell/core/receiver
are stopped. No builds/flashes or production source changes; Walter temporary
image remains installed/OFF, original restore backups secured. One RF window,
no retry. Raw logs and 18,059 USB bytes/chunk timestamps stay private.

Best direct goodput remains **7.7824 kbps** from the preceding 2 packet/s point.
This failed point establishes neither sustainable 5 packet/s nor maximum LTE-M
capacity. Selected counts and receipts are saved in lab-log entry 005.

Next: inspect saved crash/allocation evidence offline before any further rate
run. Preserve the assertion; do not remove it as a workaround or change production
IHU/Walter MCU firmware.
