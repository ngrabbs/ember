# UHF radio configuration

Use `radio config` on the IHU USB console, or send `REQUEST_RADIO_CONFIG`
from Yamcs and open **Devices & firmware → Radio configuration**. Both
request a fresh CAN readback. The CLI works in RX_ONLY and LINK_ACTIVE.
UHF commands require LINK_ACTIVE.

| Profile | ID | Uplink | Downlink | RF framing |
| --- | --- | --- | --- | --- |
| `DBPSK_1200_V3` | 1 | 1200 baud | 1200 baud | DBPSK v3 |
| `DBPSK_DL1500_V3` | 2 | 1200 baud | 1500 baud | DBPSK v3 |

Both profiles use a nominal 435 MHz receive LO and 437 MHz transmit carrier.
The ground gateway sends at 434.994550 MHz on the bench and decodes either
downlink rate. The factory profile is `DBPSK_1200_V3`.

1. During the listen window, send `SET_RADIO_PROFILE` with the other
   profile. The command completes when the radio reports `STAGED`.
2. The radio switches after five seconds. Send `REQUEST_RADIO_CONFIG`
   and check that the response shows `TRIAL` and the candidate as active.
3. Send `CONFIRM_RADIO_PROFILE` with the token from that UHF response
   within the 45-second trial. An unconfirmed trial returns to the last
   confirmed profile, including when the ground receiver is offline.
   Confirmed choices are held in radio RAM. A radio reboot loads the factory
   profile.

| Schema v2 field | Type | Meaning |
| --- | --- | --- |
| Schema version | u8 | `2` |
| Supported profiles | u8 bit mask | Bits 0 and 1 identify profiles 1 and 2 |
| Factory and active profile IDs | u8 each | Profile IDs from the table above |
| Behavior | u8 | `1` RX_ONLY, `2` LINK_ACTIVE |
| Factory and active setting groups | u32, u32, u16 each | Nominal RX LO and TX carrier in Hz, downlink symbol rate in baud |
| Transceiver boot ID | u32 | Radio boot that supplied the report |
| Candidate profile | u8 | Candidate ID or zero |
| Trial state | u8 | `0` STABLE, `1` STAGED, `2` TRIAL, `3` CONFIRMED, `4` ROLLED_BACK |
| Confirmation token | u32 | Nonzero only in a readback during an active trial |
| Remaining time | u32 | Milliseconds remaining at the time of the report |
| Operation result | u8 | `0` READBACK, `1` stage accepted, `2` REJECTED, `3` CONFIRMED |

The `RADIO_CONFIG` reply is a 40-byte big-endian payload, telemetry ID 65.
The IHU validates the CAN reply against both boot IDs and the outstanding
request. Yamcs correlates each command with its response. The schedule
continues with the selected profile and keeps its configured durations.
