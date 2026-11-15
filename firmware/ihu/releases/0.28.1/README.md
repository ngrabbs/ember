# IHU 0.28.1 bench build

[Download the GROUND_TEST UF2](ihu-0.28.1-ground-test.uf2) for the EMBER CAN Feather (RP2040). Built from `1fae8155588e4aafba05a6df4dab972b1dad284b` with `IHU_BOOT_DEMO=ON` and `IHU_BOOT_RX_ONLY=OFF`.

SHA-256
`8d8a4f346bef97dd67c301afeb2325404fd7bcecd3105207a074ab284a887e6c`

## Bench verification

On November 15, 2026, `picotool` verified the UF2 readback on IHU `DF641455DB822427` connected to `ember-ground`. The USB console displayed the 0.28.1 banner with BASIC scheduled telemetry off and a 540 s listen / 60 s telemetry default. The first boot reached SAFE while waiting for the transceiver. After restarting both boards, the IHU reached NOMINAL with LINK_ACTIVE.

| Yamcs PING | Observed result |
| --- | --- |
| Command ID | `1794754748177-ihu-0281-flash-check-1` |
| Transaction ID | `13` |
| Issued | `2026-11-15T14:58:31.177Z` |
| Reply on `uhf-tm-in` | `2026-11-15T14:58:35.365Z` |
| Yamcs completion | `OK` / `COMPLETED` |

The ground station bench bridge was stopped during the PING.
