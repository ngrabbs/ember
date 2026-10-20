# MPDCCH append-slot candidate applied and built

2026-10-20 UTC / October 19 local. The user requested patching the existing
ground build. The original source diff, staged diff, affected source files,
radio binary, runtime libraries and CMake cache were saved first: 22 files
hash-verified on ground and in a local private copy. No isolated worktree created.

The patch refreshes the current append slot immediately before each LTE-M
MPDCCH write. Previous source changes are retained; the PHY assertion is unchanged.

| Check | Result |
| --- | --- |
| Existing `build-lte/lte-softmodem` rebuild | Passed, exit 0 |
| MAC Msg4 action helper | Passed |
| MAC uplink HARQ helper | Passed |
| PHY DLSCH context helper | Passed |
| CMake cache / runtime libraries | Unchanged |
| Candidate source/binary and preserved reference checks | 12/12 passed |
| RF / MCU builds or flashes | None |
| Cell/core | Stopped |

Baseline radio SHA256:
`5c5de8e17db509b35823f401b99c7fdbe28144307da0be24fbc777c569768e11`.
Installed candidate SHA256:
`5b19f79079d0e750b6ac9251982b85a79ab3a0eb1c7574ff3c309033d861871c`.
Copies of both binaries are retained privately.

The three helper tests do not execute the full multi-context scheduler. The
earlier reduced fixture covers the pointer/count defect separately. Full radio
compilation is confirmed; live crash prevention and delivery improvement are
unverified. Best measured direct goodput remains **7.7824 kbps**.

Private ground rollback snapshot: `diagnostics/mpdcch-slot-20261020/before/`;
local mirror: `.runtime/throughput/mpdcch-slot-build-20261020/`. Restore the saved
scheduler source and original radio binary with the radio stopped; preserve the
pre-existing overlay. Do not reverse the older patch set or reset the checkout.
The original source/binary identity audit now deliberately differs: use the new
private `audit_mpdcch_slot.py`, which checks the candidate against its manifest
and keeps the earlier reference hashes intact. Old run records are unchanged.

Next: one bounded 512-byte, 5 packet/s comparison with the existing debug profile
and the rebuilt radio. Count receipt/late/missing outcomes and actual child radio
exit; a non-crashing run alone does not prove the two-context path was exercised.
No cable move or MCU firmware build needed.
