# IHU 0.28.1 bench build

[Download the GROUND_TEST UF2](ihu-0.28.1-ground-test.uf2) for the EMBER CAN Feather (RP2040). Built from `91b55e40593c64561e5ed31cc88c6f54b0e5536e` with `IHU_UHF_STARTUP=ON` and `IHU_BOOT_RX_ONLY=OFF`.

SHA-256
`a2a7602d9f3262ee145e39d3d63a07fb3e10cc142d3db5b1948167d8bd7a1123`

The rebuilt UF2 identifies as `ihu-uhf-startup` 0.28.1 and contains the `GROUND_TEST / UHF` banner. The IHU and transceiver builds passed with UHF startup on, off, and enabled by their previous flags.

## Bench verification of the earlier 0.28.1 build

This hardware test used source commit `1fae8155588e4aafba05a6df4dab972b1dad284b`, before the naming cleanup. The rebuilt UF2 has build verification only.

On November 15, 2026, `picotool` verified the UF2 readback on IHU `DF641455DB822427` connected to `ember-ground`. The USB console displayed the 0.28.1 banner with BASIC scheduled telemetry off and a 540 s listen / 60 s telemetry default. The first boot reached SAFE while waiting for the transceiver. After restarting both boards, the IHU reached NOMINAL with LINK_ACTIVE.

| Yamcs PING | Observed result |
| --- | --- |
| Command ID | `1794754748177-ihu-0281-flash-check-1` |
| Transaction ID | `13` |
| Issued | `2026-11-15T14:58:31.177Z` |
| Reply on `uhf-tm-in` | `2026-11-15T14:58:35.365Z` |
| Yamcs completion | `OK` / `COMPLETED` |

The ground station bench bridge was stopped during the PING.
