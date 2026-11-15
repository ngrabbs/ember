# Transceiver 0.41.0

Confirmation stores the active profile in two alternating, CRC-checked flash
sectors. The radio restores the latest valid record at boot. A blank store
uses the 1200-baud factory profile. An unconfirmed trial returns to the saved
profile after its deadline. The [profile guide](../../../../docs/comms/radio_config.md)
covers the Yamcs commands and trial states.

## Local UF2

Follow the [UHF startup build instructions](../../README.md#build-and-flash)
from source commit `402bcef7ca066ea805c265992f0b29cca26266e3` using Pico SDK
2.1.1. Leave `TRANSCEIVER_RX_ADC_CAPTURE` off for normal bench use.

| File | SHA-256 |
| --- | --- |
| `transceiver-0.41.0-clean-uhf.uf2` | `cbc0b19410af55b73c1b947809a6b01b102731e964dc9c989b3e673d930f2649` |

The clean UF2 was rebuilt and checksum-verified. The bench ran a development
UF2 with the same firmware logic and ADC streaming disabled.

## Bench results

- Mock flash checks passed for empty storage, interrupted writes, corrupt
  record fallback, alternating sectors, and suppression of redundant writes.
- The bounded noise-rejection pass recovered one captured request offline
  and preserved previously decoded frames across 68 earlier windows. Live
  reception was intermittent. The tinySA saw all four spaced uplink bursts
  at about −50 dBm beside the EMBER antenna, including the PING that failed CRC.
- Yamcs confirmed the 1500-baud profile. After reboot, the radio had a new
  boot ID and reported `CONFIRMED` at 1500 baud. Yamcs received both PING
  and configuration replies at 1500 baud.
- With 1500 baud saved, transaction 139 staged a 1200-baud trial. The
  IHU console showed the trial active at 1200. No confirmation was sent.
  After the 45-second deadline, transaction 140 returned `ROLLED_BACK`
  over UHF at 1500 baud with radio boot ID `1023998050` unchanged and
  no candidate remaining.
- The first rollback attempt entered SAFE after staging. Its cause was
  undetermined. The retry started from a reboot and used the same RF setup.
