# New-bank transient results

Typical-model development screening. The current 220 pF no-load-release failure is an expected rejection, not accepted hardware. Bleeder cases are analysis-only.

| Case | Bank peak V | Protected peak V | Final V | Pass-bank fault mJ | Result |
|---|---:|---:|---:|---:|---|
| bank_bridge_min | 35.8630 | 5.1336 | -0.0001 | 2.7875 | Stated checks pass |
| bank_bridge_nom | 35.0287 | 5.0511 | -0.0001 | 3.6230 | Stated checks pass |
| bank_bridge_max | 35.0304 | 5.0328 | -0.0001 | 3.0724 | Stated checks pass |
| bank_finite330_min | 35.3362 | 5.1197 | -0.0001 | 2.3080 | Stated checks pass |
| bank_bypass_min | 35.0552 | 5.1061 | -0.0001 | 3.2090 | Stated checks pass |
| bank_finite330_max | 34.9998 | 5.0368 | -0.0000 | 0.9477 | Stated checks pass |
| bank_bypass_max | 35.0082 | 5.0761 | -0.0001 | 3.4677 | Stated checks pass |
| bank_start_low | 4.9613 | 4.8155 | 4.8155 | 1.6023 | Stated checks pass |
| bank_start_max | 5.1169 | 4.9712 | 4.9712 | 1.5903 | Stated checks pass |
| bank_load_release | 5.1148 | 5.2998 | 5.0445 | 0.0002 | Stated checks pass |
| bank_reset | 35.0286 | 5.0398 | 4.9671 | 37.0536 | Stated checks pass |
| bank_gate_corner | 35.8635 | 5.1853 | -0.0001 | 3.7794 | Stated checks pass |
| bank_start_endurance | 5.1140 | 4.9712 | 4.9712 | 1.5903 | Stated checks pass |
| bank_release_low_trip | 5.1148 | 5.2016 | 4.5698 | 0.0029 | Expected rejection: no_load_release_latch |
| bleed_100_load_release | 5.1131 | 5.1307 | 5.0421 | 0.0019 | Stated checks pass |
| bleed_100_fault | 35.8601 | 5.1801 | -0.0000 | 56.1790 | Stated checks pass |
| bleed_330_load_release | 5.1123 | 5.1315 | 5.0438 | 0.0009 | Stated checks pass |
| bleed_330_fault | 35.8707 | 5.1836 | -0.0000 | 174.7053 | Stated checks pass |
| bleed_100_load_release_10n | 5.1131 | 5.1307 | 5.0421 | 0.0019 | Stated checks pass |
| bleed_100_fault_10n | 35.8601 | 5.1801 | -0.0000 | 10.2023 | Stated checks pass |
| bleed_330_load_release_10n | 5.1123 | 5.1315 | 5.0438 | 0.0009 | Stated checks pass |
| bleed_330_fault_10n | 35.8707 | 5.1836 | -0.0000 | 9.7356 | Stated checks pass |
