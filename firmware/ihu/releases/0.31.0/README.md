# IHU 0.31.0 and transceiver 0.39.0 radio readback

Both UF2s were built from `9cfe2a95d596de98d73297a6708ae2e7fc5d6e87`
with their UHF startup profiles enabled. Flash readback passed on both boards.

| Target | Flashed file | SHA-256 |
| --- | --- | --- |
| IHU RP2040 CAN Feather | [IHU 0.31.0 UF2](ihu-0.31.0-ground-test.uf2) | `ee2f18c4bec5a9044d207e17458e6c3908af3ea086959caf7e9359c82e87af41` |
| Transceiver original Raspberry Pi Pico | [Transceiver 0.39.0 UF2](../../../transceiver/releases/0.39.0/transceiver-0.39.0-uhf.uf2) | `8defb35eab3ec4b67a4922e13cceabe083b98cef8069e140fc3869b449f9fb8f` |

## Bench verification

On November 15, 2026, the IHU reached NOMINAL / LINK_ACTIVE and
`radio config` received a CAN reply. The Yamcs `REQUEST_RADIO_CONFIG` reply
arrived on `uhf-tm-in`, and the Radio Configuration page matched the CLI.

| Readback | Observed value |
| --- | --- |
| Schema | `1` |
| Supported, factory, and active profile | `DBPSK_1200_V3` |
| Factory and active nominal RX LO | `435000000 Hz` |
| Factory and active nominal TX carrier | `437000000 Hz` |
| Factory and active symbol rate | `1200 baud` |
| Radio behavior and boot ID | `LINK_ACTIVE`, `962158568` |
| IHU boot ID | `2824418717` |

The first UHF response was archived while the deployed Yamcs completion
handler was incomplete. After correcting it, the repeat request completed
in 3.888 seconds.

| Yamcs command | Observed result |
| --- | --- |
| Command ID | `1794759909825-transceiver-config-bench-3` |
| Issued | `2026-11-15T16:24:32.825Z` |
| Reply on `uhf-tm-in` | `2026-11-15T16:24:36.713Z` |
| Command completion | `OK` / `COMPLETED` |

[Configuration schema](../../../../docs/comms/radio_config.md) ·
[Yamcs ground 1.8.0 manifest](../../../../ground/releases/yamcs-flight-1.8.0.json)
