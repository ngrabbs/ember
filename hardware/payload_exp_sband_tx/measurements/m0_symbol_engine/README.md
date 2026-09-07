# M0 symbol engine — measurements

Bench results for milestone M0 on the Digilent Arty Z7-20.

## Setup

| | |
|---|---|
| Board | Arty Z7-20, XC7Z020-1CLG400C |
| Bitstream | `fpga/build/vivado/top_arty_z7.bit` |
| Clock | 125 MHz |
| Scope | Rigol — chosen over the Digilent because `symbol_tick` is one 125 MHz clock, 8 ns wide, and at 100–125 MS/s the Digilent can miss it entirely |
| Probes | Ch1 `tx_symbol` (Pmod JA pin 1), Ch2 `symbol_tick` (JA pin 2), ground on JA pin 5 or 11. **Both DC coupled** |
| Loopback | jumper JA pin 1 → pin 4 |

Controls: `pattern_sel = {SW1, SW0}` — `00` zero, `01` one, `10` alternating,
`11` PRBS-7. `btn[0]` reset, `btn[1]` advance rate, `btn[2]` hold to disable,
`btn[3]` clear the error latch. `led[1:0]` rate, `led[2]` locked, `led[3]`
sticky error or lock loss.

## Results

| Date | Test | Result |
|---|---|---|
| 2026-09-07 | Loopback, 1 Msym/s, 60 s | **60,000,000 symbols, zero errors, zero lock losses** |
| 2026-09-07 | Negative test: jumper pulled | `led[2]` goes dark — the checker fails honestly |
| 2026-09-07 | Alternating at 1 ksym/s | Clean square wave observed on Ch1 |

## Outstanding

- [ ] Constant zero and constant one — valid 3.3 V LVCMOS levels at the pin
- [ ] Alternating frequency = symbol rate / 2, at all four rates
- [ ] Zoomed capture on `symbol_tick`: the 8 ns pulse on the symbol edge, and
      `tx_symbol` not moving anywhere else
- [ ] Read `bit_count` and `error_count` back over the UART, so a partial
      failure in a long run can be quantified rather than only detected

Captures go in `captures/`, named `<date>_<pattern>_<rate>.png`, with the
timebase, coupling and trigger settings visible in the screenshot.
