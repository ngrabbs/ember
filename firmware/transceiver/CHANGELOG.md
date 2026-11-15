# Transceiver changelog

[Current bench builds](../README.md#current-bench-builds) · [Transceiver guide](README.md)

| Date | Version | Change |
|---|---|---|
| 2026-11-14 | 0.38.0 · `819470b` | Services CAN during receive diagnostics and answers LINK_ACTIVE firmware identity requests for FULL telemetry. |
| 2026-11-14 | Sweep build · `32db8e1` | Adds a temporary transmit sweep and tinySA capture. The bench run logged restoration and verification of the prior image. |
| 2026-11-12 | 0.37.2 · `fc3616c`, `815faf4` | Adds passive RX and CAN diagnostics, then keeps ADC capture running through overlapping decode windows. The commits share the earlier version number. |
| 2026-11-05 | 0.37.2 · `14243dc` | Tries both measured receive IFs early in the decoder. |
| 2026-11-05 | 0.37.0–0.37.1 · `7909e7f`, `32b4b7c` | Adds the transparent bench UHF link and continuous Yamcs gateway. |
| 2026-11-05 | 0.36.0 · `0035364` | Adds the conducted startup demo and one-shot CW profile. |
| 2026-11-01 | 0.35.0 · `4dc34c7` | Supports the bounded UHF command path used for command validation and status records. |
| 2026-10-17 | 0.34.0 · `446db58` | Renames the COMMS application and UF2 to transceiver. |

## Earlier milestones

| Version | Change |
|---|---|
| 0.32–0.33 | Made IHU telemetry on demand and added an explicit identity request alongside the first-send announcement. |
| 0.25–0.30 | Added RX ADC characterization, captured DBPSK decoding, and bounded PING forwarding and reply diagnostics. |
| 0.22–0.23 | Added build identity reporting and LTE identity observation forwarding. |
| v17–v20 | Brought up IHU packet bridging, CAN admission and transmit results, and bounded batch and timed services. |
| v7–v16 | Brought up the clock, conducted tone, DBPSK, and phase/drive diagnostics. |
| v3–v6 | Added independent CAN checks, loopback, receive windows, HELLO, and startup readiness. |
