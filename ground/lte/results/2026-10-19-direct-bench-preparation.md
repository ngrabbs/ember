# Direct Walter benchmark preparation — 2026-10-19

Built, host-tested and installed. Startup/OFF checks passed. The later
[first direct delivery check](2026-10-19-direct-walter-smoke.md) passed 10/10 packets;
The later [512-byte point](2026-10-19-direct-walter-512.md) also passed 10/10;
1024-byte packets and higher offered rates remain unqualified.
Production IHU, Walter MCU and Walter application sources are unchanged.

- Project: `firmware/walter_throughput_bench`, temporary USB-controlled image.
- Modem reset held at startup; explicit RF window ≤120s; no window extension.
- One send at a time, numbered/CRC-checked datagrams, no retries after rejection
  or uncertain outcome. Busy slots and unattempted slots are counted separately.
- Fixed115200-baud modem UART; this measures UART/AT application goodput.
- Separate ground receiver UDP51002; sender local51003. Production51000 unchanged.
- Initial 128-byte and 512-byte low-rate checks passed; 1024-byte support still
  needs modem qualification.
- Pinned PlatformIO6.1.18 / espressif32 6.10.0 / Arduino2.0.17 / esptool4.5.1.
- ESP32-S3 build passed with application warnings treated as errors.
  Static RAM38,344 bytes; flash usage316,201 bytes; image316,560 bytes.
- Actual engine host checks passed with AddressSanitizer/UBSan: pacing/skips,
  blocked UART, prompt/payload/final-OK order, rejection/unknown outcomes,
  registration loss, bounded deadlines/millis wrap, and read-only operator query.
- Three Python tests passed: cross-language CRC/payload vector and corruption,
  real UDP socket/duplicates, summary accounting and uncertain outcomes.
- Build input hashes and downloaded artifacts match the local source exactly.

Source digest: `391f67568ce7062faa4030523a1da08d2aff3b7bff7b5158c2f8301d2b65a24b`.
Application SHA256: `8fa818c5ec34644cde870b47506a1906d6361994377bfe9eeaecf177ca13ddbe`.
Private build manifest/artifacts: `ground/lte/.runtime/throughput/direct-bench-artifacts-20261019/`.
These hashes match the installed temporary image. Low-rate 128/512-byte delivery
has passed; maximum throughput remains unmeasured.

## Installation and non-RF checks

- USB moved to Walter; original clean application 0.3.0 identified.
- ESP32-S3 /16 MiB flash and unencrypted protection state confirmed.
- Two complete16 MiB restore images match. Programmed64 KiB regions were read;
  erased regions were checksum-verified, with whole-device checksums before/after
  each snapshot. Both copies were transferred locally and reverified before writing.
- Pinned PlatformIO upload passed; application verified against flash afterward.
- Installed temporary role `WALTER_THROUGHPUT_TEMP`, version 0.1.0; source digest
  and binary match the values above. Production application backup remains private.
- Six OFF-state checks passed: startup OFF, invalid 0- and 121-second windows rejected,
  run/query while OFF rejected, final explicit OFF confirmed. Zero USB log drops.
- No cell or RF window started. IHU and Walter MCU firmware unchanged.

First bounded 128-byte direct-Walter check completed successfully; see the
linked result above. The 512-byte point has also passed. Next: 512-byte offered-rate
points at 2 and 5 packets/s. Stop on failed admission/registration rather than restarting reliability
experiments. Restore the original Walter image when temporary testing is finished.

The [project instructions](../../../firmware/walter_throughput_bench/README.md)
contain the USB commands, receiver protocol and backup/restore procedure.
Reliability debugging remains paused. No PR, production release or IHU flash.
