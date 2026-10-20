# Direct Walter pacing check and restoration

2026-10-20 UTC / October 19 local. Initial 512-byte, 2 packet/s, 30-second point
followed by at most two matching fresh-session repeats, stopping on first anomaly.
Both repeats passed. Same Walter/modem UART, patched ground binary, debug profile
and 1 m antenna spacing. Synthetic UDP outside IHU/CAN/EPS/Yamcs.

| Point | READY seconds | Attempted / accepted / received | Within 30s / late | Goodput kbps |
| --- | --- | --- | --- | --- |
| Initial | 16.554 | 60 / 60 / 60 | 60 / 0 | 8.192 |
| Repeat 1 | 16.054 | 60 / 60 / 60 | 60 / 0 | 8.192 |
| Repeat 2 | 15.925 | 60 / 60 / 60 | 60 / 0 | 8.192 |

**180/180 packets arrived within their respective receiver windows**, no late,
missing, duplicate, malformed or out-of-order packets, rejected/uncertain sends
or skipped slots. CRC/body checks passed. All actual radio/core child exits
were planned timeouts; post-run candidate integrity checks passed 12/12 for each
repeat. This is three separate 30-second pacing runs, not continuous 90 seconds or
maximum LTE-M/long-duration reliability qualification. Earlier failures remain
unresolved. Best ten-second burst 11.8784 kbps included a delayed tail.

No further RF tests are planned for this temporary benchmark. The verified
original 16 MiB Walter image was restored at offset 0 with flash parameters kept.
Fresh chip/security checks, full-image verification, original 0.3.0 / clean 9fcb020
USB identity and startup/final modem OFF checks passed. No RF window during
restoration. Raw images/NVS and restore console stay private.

IHU/Walter MCU firmware unchanged. The ground candidate remains installed with
its prepatch source/binary backups. Cell/core/receiver stopped. On October 20
local, the production IHU→CAN→WalterMCU→UART→Walter read-only check passed:
IHU 0.15.0, COMMS 0.8.0 and Walter 0.3.0, all clean. Walter state 0,
registered 0 and radio window 0 ms. Output permissions stayed unchanged; CAN
normal mode and zero error registers confirmed. No RF command or flashing.

The first query encountered a stale Walter session after restoration, incrementing
the IHU unknown counter once; its immediate retry required a new HELLO. A second
check met background-discovery busy responses. After renewing HELLO, the final
check passed with no further unknown or CAN error increments. Raw attempts are
retained privately; this establishes restored control communication, not RF delivery.

Selected per-run counts/receipts, repeat summary and restore checks saved in
lab-log entry 005. A useful measured claim is: approximately 8.2 kbps UDP goodput
across three 30-second, 512-byte paced runs, 180/180 in-window deliveries. This is
a bench-system measurement; it does not establish the modem's maximum rate.
