# IHU 0.32.0 and transceiver 0.40.0

Build both UHF startup targets from `072d9f5157bc237926e71120f94f5b9606752e44`
with Pico SDK 2.1.1 and the Arm GNU toolchain. Follow the [IHU build guide](../../README.md#build-and-flash)
and [transceiver build guide](../../../transceiver/README.md#build-and-flash).
The transceiver ADC USB stream defaults to off.

| Local release artifact | SHA-256 |
| --- | --- |
| `ihu-0.32.0-uhf.uf2` | `3587633e5355e1fbf9f52aa5ef66f1895dc9e9228212c48905b41fcd60e7d04c` |
| `transceiver-0.40.0-uhf.uf2` | `af61ec52fa917de0e3f1b2c35815e04089afd7803ca8176612fec83d1d8650a4` |

Both release UF2s were rebuilt from clean source. The live test used earlier
bench builds of the same firmware logic. The tested transceiver had optional
ADC USB streaming disabled.

## Bench results

The tuned decoder recovered three additional failed PINGs in replay of 68 ADC
windows, preserved both live-pass PINGs, and matched every recovered frame
against the Yamcs command bytes. On the unchanged RF bench, four of five
PINGs spaced 19 seconds apart passed. Their ADC-window-end to decode-end times
were 124–219 ms against the 3-second deadline. One PING reached that deadline
with 21 CRC failures and no valid frame.

| RF transaction | Result |
| --- | --- |
| 48 · SET_RADIO_PROFILE | Staging acknowledgment received at 1200 baud |
| 49 · REQUEST_RADIO_CONFIG | Timed out on the uplink |
| 50 · REQUEST_RADIO_CONFIG | Yamcs received the active trial report at 1500 baud |
| Gateway stopped | Radio reverted to 1200 baud with boot ID `4070374067` unchanged |
| 51 · REQUEST_RADIO_CONFIG | Yamcs received `ROLLED_BACK` at 1200 baud after gateway restart |

See the [profile protocol](../../../../docs/comms/radio_config.md) and
[Ground 1.9.0 release record](../../../../ground/releases/README.md).
