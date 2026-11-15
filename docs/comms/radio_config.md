# UHF radio configuration

Use `radio config` on the IHU USB console, or send `REQUEST_RADIO_CONFIG`
from Yamcs and open **Devices & firmware → Radio configuration**. Both
request a fresh CAN readback from the transceiver. The CLI works in RX_ONLY
and LINK_ACTIVE. The UHF request and reply require LINK_ACTIVE.

| Schema v1 field | Type | Meaning |
| --- | --- | --- |
| Schema version | u8 | `1` |
| Supported profiles | u8 bit mask | Bit 0 supports `DBPSK_1200_V3` |
| Factory and active profile IDs | u8 each | `1` = DBPSK, 1,200 baud, EMBER RF framing v3 |
| Radio behavior | u8 | `1` = RX_ONLY, `2` = LINK_ACTIVE |
| Factory and active setting groups | u32, u32, u16 each | Nominal RX LO in Hz, nominal TX carrier in Hz, symbol rate in baud |
| Transceiver boot ID | u32 | Identifies the radio boot that supplied the readback |

The only supported profile uses a **435,000,000 Hz RX LO**, a
**437,000,000 Hz TX carrier**, and **1,200 baud**. Factory and active settings
match in this release. The bench gateway's **434,994,550 Hz uplink carrier**
is a ground setting. The LO and carrier values are nominal clock targets.

Yamcs decodes both big-endian `RADIO_CONFIG` payloads (telemetry ID 65).

| Schema | Payload | Layout |
| --- | --- | --- |
| 1 | 29 bytes | Common fields above |
| 2 | 40 bytes | Common fields → candidate profile (u8) → trial state (u8) → confirmation token (u32) → remaining time in ms (u32) → operation result (u8) |

Both schemas are archived as `/ember/RADIO_CONFIG`. Yamcs extracts the
five additional fields through the `RADIO_CONFIG_V2` container.

The IHU validates the CAN reply against both boot IDs and the outstanding
request, then returns it with the Yamcs transaction ID. A missing reply times
out. This interface reads settings without changing the radio or the schedule.
