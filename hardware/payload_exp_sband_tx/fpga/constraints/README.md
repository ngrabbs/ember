# Constraints

**Target board: Digilent Arty Z7-20 (XC7Z020-1CLG400C).**

`arty_z7_20.xdc` is the constraint file of record. Every pin in it is taken
verbatim from **Digilent's official master XDC**
([digilent-xdc](https://github.com/Digilent/digilent-xdc) → `Arty-Z7-20-Master.xdc`)
rather than transcribed by hand. Re-derive from that file if the board revision
changes; do not edit pin names in place.

Note the variants share a footprint but not a part number: **Z7-10 is
XC7Z010-1CLG400C**, **Z7-20 is XC7Z020-1CLG400C**. This payload is on the Z7-20.

## Signals constrained

| Signal | Notes |
|---|---|
| `clk` | 125 MHz board clock. Needs a `create_clock` of 8.000 ns |
| `rst` | A button, active high, synchronised internally |
| `tx_enable`, `pattern_sel[1:0]`, `rate_sel[1:0]` | Slide switches and buttons, or UART commands |
| `ja_tx_symbol` | Pmod JA pin 1 — the signal to put a scope on |
| `ja_symbol_tick` | Pmod JA pin 2 — one clock wide, use it as the scope trigger |
| `ja_loopback` | Pmod JA pin 4, jumpered back from pin 1 |
| `led[2]` | `prbs_locked` |
| `jb_uart_tx`, `jb_uart_rx` | Pmod JB pins 1–2, 115200 8N1, **3.3 V cable, GND/TX/RX only** |

`ck_io0` on the ChipKit header carries the AD9910 reference clock; JA and JB are
fully used by the bench interface, the console and the DDS control lines.

## Why this board

**USB-JTAG is built in**, so programming needs no external adapter and no
bit-banged configuration path. The 125 MHz board clock is an exact multiple of
all four symbol rates, and the Zynq's PL has room to spare — the whole M0+M1
design uses under 1% of it.

One caveat worth stating plainly: the board's USB-UART is wired to the **PS**
(MIO), and this is a **PL-only design** with no PS instantiated, so the console
does *not* come out of the programming cable. It runs on **Pmod JB** with an
external 3.3 V USB-serial cable. Connect GND, TX and RX only — never the cable's
VCC. See the power note below; that exact wire has already cost this payload one
FPGA board.

## Build flow

Vivado 2024.2 runs in a Docker container on **m75q (192.168.1.252)**, with the
Xilinx tree bind-mounted read-only and USB passed through for JTAG. JTAG through
that container is already proven working.

```bash
# on m75q
~/vivado-docker/vivado-run.sh vivado -mode batch -source build.tcl

# inside the container, to program:
hw_server &
vivado -mode tcl
  open_hw_manager; connect_hw_server; open_hw_target
  current_hw_device [lindex [get_hw_devices] 0]
  set_property PROGRAM.FILE design.bit [current_hw_device]
  program_hw_devices
```

Launcher and notes: `/workspace/notes/home_lab/vivado-docker/`.

## Timing

Closed with room to spare. From `build/vivado/timing_summary.rpt`, against the
8.000 ns board-clock period:

| Metric | Value |
|---|---:|
| WNS (setup) | **+1.727 ns** → F<sub>max</sub> ≈ 159 MHz |
| WHS (hold) | +0.051 ns |
| WPWS (pulse width) | +3.020 ns |
| Failing endpoints | **0** of 1720 |

Timing is not a constraint at M0 or M1. Record a new row here if the design
grows enough to move these numbers.

## Utilisation

From `build/vivado/utilization.rpt` — the full M0 symbol engine plus the UART
console, SPI master, AD9910 sequencer and reference-clock divider:

| Resource | Used | Available | % |
|---|---:|---:|---:|
| Slice LUTs | 518 | 53,200 | 0.97 |
| Slice registers | 718 | 106,400 | 0.67 |
| Bonded IOB | 27 | 125 | 21.6 |

Pins, not logic, are the scarce resource on this board — which is why `PD` is
strapped at the DDS rather than driven.


---

# AD9910 interconnect — Arty Z7-20 to the DDS breakout

Eleven signals plus ground. The Arty's two Pmods have exactly ten pins free
after M0, so `PD` is strapped at the DDS board rather than driven.

## Power — read this first

The AD9910 breakout has its **own 5 V barrel jack**. Connect **GND between the
two boards and nothing else**. No 5 V, no 3.3 V, in either direction. Two
independently powered boards sharing a ground reference and signal lines.

This is not a general caution. This payload has already lost one FPGA board to
exactly one wire — a USB-serial cable's 5 V conductor connected to a board that
already had its own supply. Back-feeding a powered board through a VCC pin kills
its regulator.

Signal levels are compatible without translation — the AD9910 is a 3.3 V CMOS
part (`DVDD_I/O` = 3.3 V ±5%) and the Arty's Pmods are LVCMOS33. The
AMS1117-1.8 on the breakout feeds the AD9910's internal core rails only.

## Ground straps at the DDS board — do these FIRST

These are wires, not options. The AD9910's unused inputs have no pulldowns on
this breakout (the `101` arrays on the header lines are 100 Ω series
resistors), so anything left unconnected floats.

| DDS pin | Tie to | Consequence if left floating |
|---|---|---|
| **`PD`** | **GND** | **the chip is powered down and ignores SPI entirely** — no PLL lock, no output, no response to anything |
| `TEN` | GND | TxENABLE; matters only with the parallel data port |
| `OSK` | GND | output shift keying |
| `DRC` `DRO` `DPH` | GND | digital ramp control |

`PD` is the one that costs an afternoon. A floating `PD` looks exactly like a
dead SPI bus, a missing reference clock and a broken DAC all at once, because
the part is simply off.

## Pmod JB — serial port and control

| JB pin | FPGA pin | Signal | Dir | DDS header |
|---:|---|---|---|---|
| 3 | T11 | `dds_cs_n` | out | `CSB` |
| 4 | T10 | `dds_sclk` | out | `SCK` |
| 7 | V16 | `dds_sdio` | out | `SDIO` |
| 8 | W16 | `dds_sdo` | **in** | `SDO` |
| 9 | V12 | `dds_io_update` | out | `IOUP` |
| 10 | W13 | `dds_master_reset` | out | `RST` |
| 5 or 11 | — | GND | — | `GND` |

JB pins 1 and 2 stay with the UART console.

## Pmod JA — profile select and status

| JA pin | FPGA pin | Signal | Dir | DDS header |
|---:|---|---|---|---|
| 7 | U18 | `dds_pf0` | out | `PF0` — **the BPSK pin** |
| 8 | U19 | `dds_pf1` | out | `PF1` |
| 9 | W18 | `dds_pf2` | out | `PF2` |
| 10 | W19 | `dds_pll_lock` | **in** | `PLL` |
| 5 or 11 | — | GND | — | `GND` |

JA pins 1–4 stay with `tx_symbol`, `symbol_tick`, `tx_oe_n` and the loopback.
Putting `PF0` on the same connector as `tx_symbol` is deliberate: the symbol and
the phase command it produces can be probed on adjacent pins.

## ChipKit header — reference clock

| Header | FPGA pin | Signal | Dir | DDS |
|---|---|---|---|---|
| `IO0` | T14 | `dds_refclk` | out | W1's **AD9910-side pin** (see Clock, below) |

Both Pmods are fully committed, so the reference lives on the ChipKit header.

## Parallel port

`D0`–`D15` and `F0`/`F1` (the 16-bit parallel modulation port) are left
unconnected. They are the route to QPSK and pulse shaping later, at up to
250 MSPS, but profile-pin BPSK needs none of them.

## Clock — the FPGA supplies it

The breakout's own 40 MHz oscillator runs correctly (measured at exactly
40.000 MHz on U5) but its output never reaches the AD9910's `REF_CLK`.
`SYNC_CLK`, which needs no configuration at all and appears at SYSCLK/4 the
moment a reference exists, was dead in every condition: both W1 positions,
reseated, power-cycled, with `PD` grounded and `XTAL_SEL` confirmed at 0 V, and
with a reference injected at each W1 pin. The board's supplies all measure
correct. The fault is a break between W1 and `REF_CLK`.

So `dds_refclk` on `IO0` supplies the reference instead. Beyond working around
the fault, this makes the DDS carrier and the symbol clock **coherent** — both
derived from the same 125 MHz oscillator, so no frequency offset can accumulate
between the carrier and symbol timing.

`N` in CFR3 must match the reference, and it is settable live over the console
with `cXXXXXXXX` — no rebuild needed to change it:

| Divide | Reference | N | CFR3 | Notes |
|---:|---:|---:|---|---|
| /4 | 31.2500 MHz | 32 | `c0538C140` | marginal through a breadboard |
| /8 | 15.6250 MHz | 64 | `c0538C180` | good |
| /10 | 12.5000 MHz | 80 | `c0538C1A0` | **best for breadboard** — 80 ns period |

All three give exactly 1 GHz SYSCLK, inside VCO5's 920–1030 MHz band. `/16` and
`/20` would need N = 128 and 160, past the datasheet's 127 limit. Change the
divide with `REFCLK_DIV` in `top_arty_z7`, and the matching CFR3 over the
console.

## Breadboard notes

Most of this interconnect is slow and a breadboard is fine for it: SPI at
1 MHz, `PF0` at up to 1 Msym/s, and the reset and update strobes are all
untroubled by a few pF of stray capacitance.

**The reference clock is the exception.** A breadboard contact is a few pF with
real series inductance, and at 31 MHz with fast CMOS edges that rings. Two
mitigations, in order of preference:

1. **Drop the reference to 12.5 MHz** (`REFCLK_DIV = 10`, console `c0538C1A0`).
   An 80 ns period is far more forgiving, and the AD9910 accepts anything from
   3.2 MHz upward.
2. **Keep the reference off the breadboard** — run it as a single short direct
   wire, twisted with its own ground return.

And use **several ground wires, not one**. Eleven signals sharing a single
ground return is how you get crosstalk and unreliable levels; tie the
breadboard's ground rail to the DDS board at two or three points, and put a
ground immediately adjacent to the reference clock wire.

## What to expect

After `ad9910_ctrl` runs, the `OUT` SMA carries a tone at whatever FTW is
loaded. With `PF0` driven from `tx_symbol`, that tone flips 180° per symbol —
BPSK, at a real carrier, out of a coaxial connector.
