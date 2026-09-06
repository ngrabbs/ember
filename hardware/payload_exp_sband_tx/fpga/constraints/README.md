# Constraints

**Still no `.pcf` — but the blocker has moved.**

The pin map is now known. `iceZero-pinout-v5.pdf` (board rev2, doc v7) gives every
FPGA pin number, and those are recorded in the board-facts table in
[`../../fpga_link_processor_logic_interface_first_bringup.md`](../../fpga_link_processor_logic_interface_first_bringup.md).
What is missing is the top-level design the constraints would apply to, and a
physical confirmation that the board in hand matches the document.

Write `icezero_rev2.pcf` once `rtl/top.sv` exists, and record which pinout
document revision it came from.

---

## Planned pin assignment

| Signal | FPGA pin | Where |
|---|---:|---|
| `clk` | 49 | `IOB_81_GBIN5` — 100 MHz SiT8008, on a global buffer input |
| `btn` | 63 | `IOB_103_CBSEL0` — the only button |
| `led1` | 110 | `IOT_168` |
| `led2` | 93 | `IOR_140_GBIN3` |
| `led3` | 94 | `IOR_141_GBIN2` |
| `uart_tx` | 122 | J3 `IOT_190`, FPGA output |
| `uart_rx` | 124 | J3 `IOT_191`, FPGA input |
| `uart_cts` | 119 | J3 `IOT_178`, FPGA output, driven low |
| `tx_symbol` | 139 | PMOD P1, `IOT_217` |
| `tx_oe_n` | 137 | PMOD P1, `IOT_215` |
| `tx_loopback` | 135 | PMOD P1, `IOT_213` |
| `symbol_tick` | 130 | PMOD P1, `IOT_206` — scope trigger |

P2, P3 and P4 are deliberately left free: 24 signal pins, which is where the M1
DAC bus goes.

## Build flow

From the vendor's notes on the pinout sheet, adapted to this design:

```bash
yosys     -p 'synth_ice40 -top top -json top.json' rtl/*.sv
nextpnr-ice40 --hx8k --package tq144:4k \
              --json top.json --pcf constraints/icezero_rev2.pcf \
              --asc top.asc --freq 100
icepack   top.asc top.bin
icezprog  top.bin          # on the Raspberry Pi
```

Note `--hx8k --package tq144:4k`: the part is marked HX4K but carries an HX8K
die, and this is the combination the vendor documents. `icezprog` bitbangs the
configuration pins from the Pi's GPIO header — the board is a Pi HAT and has no
other documented programming path.

## Timing

A trial place-and-route of `tx_pattern_source` against this pin plan reports
**119.45 MHz, passing at 100 MHz**, using 50 of 7680 logic cells. The symbol
engine therefore runs directly off the board oscillator; no PLL and no clock
division are needed. Worth re-checking as the design grows — M1 adds an NCO, a
sine table and a 12-bit output bus, and 15–19% margin is comfortable rather than
generous.
