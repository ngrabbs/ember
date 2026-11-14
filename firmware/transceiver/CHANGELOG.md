# Transceiver changelog

[Current bench builds](../README.md#current-bench-builds) · [Transceiver guide](README.md)

| Date | Version | Change |
|---|---|---|
| 2026-11-14 | Sweep build · `32db8e1` | Adds a temporary transmit sweep and tinySA capture. The bench run logged restoration and verification of the prior image. |
| 2026-11-12 | 0.37.2 · `fc3616c`, `815faf4` | Adds passive RX and CAN diagnostics, then keeps ADC capture running through overlapping decode windows. The commits share the earlier version number. |
| 2026-11-05 | 0.37.2 · `14243dc` | Tries both measured receive IFs early in the decoder. |
| 2026-11-05 | 0.37.0–0.37.1 · `7909e7f`, `32b4b7c` | Adds the transparent bench UHF link and continuous Yamcs gateway. |
| 2026-11-05 | 0.36.0 · `0035364` | Adds the conducted startup demo and one-shot CW profile. |
| 2026-11-01 | 0.35.0 · `4dc34c7` | Supports the bounded UHF command path used for command validation and status records. |
| 2026-10-17 | 0.34.0 · `446db58` | Renames the COMMS application and UF2 to transceiver. This is the transceiver version on `main`. |
