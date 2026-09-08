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
| **`PWR`** | **GND** | **the module does not run.** Measured at 5.1 mV on the working demo board, so it is a strap, not a supply — the name is misleading. Proven by substitution 2026-09-08: our exact pin set on the demo board failed to generate a signal, and adding `PWR` fixed it |
| `TEN` | GND | TxENABLE; matters only with the parallel data port |
| `OSK` | GND | output shift keying |
| `DRC` `DRO` `DPH` | GND | digital ramp control |

`PD` is the one that costs an afternoon. A floating `PD` looks exactly like a
dead SPI bus, a missing reference clock and a broken DAC all at once, because
the part is simply off.

**`PWR` cost a second afternoon, the same way.** Two different pins on this
breakout hold the part off when left floating, and neither announces itself:
the symptoms are identical to a clock fault. Before diagnosing anything on this
module, confirm **every** strap in the table above with a meter. A pin that is
not in your wiring list is not the same as a pin that does not matter.

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

> **FOUND, 2026-09-08 — the module needs `PWR` connected, and we never wired
> it.** Demonstrated on known-good hardware rather than inferred: with only the
> pins our FPGA drives connected to the demo board, the module **failed to
> generate a signal**. Adding `PWR` made it work. The working set is:
>
>   **all four GND**, `CSB`, `SCK`, `SDO`, `SDIO`, `PF0`, `PF1`, `PF2`,
>   `IOUP`, `PD`, `PLL`, `RST`, and **`PWR`**.
>
> Our interconnect has every one of those except `PWR`. This explains the whole
> day, including the observation that never fitted any theory: 40 MHz present at
> U5 and at W1 but absent at the chip, while both rails measure correct at the
> package. If `PWR` gates an oscillator or a clock buffer upstream of
> `REF_CLK`, the AD9910 is healthy and simply has no reference - which also
> produces no PLL lock, no output, and no 400 kHz even with the PLL bypassed.
>
> **Source `PWR` from the DDS module's own supply, never from the Arty.** Ground
> remains the only connection between the boards. This project has already lost
> one FPGA board to a cross-board supply wire.
>
> Everything below is superseded and retained only as a record of how a wrong
> conclusion survived three revisions.

> **Superseded, 2026-09-08 (fourth revision). Stop reading conclusions from
> this section; read the facts list instead.**
>
> New fact that invalidates the two revisions below: **`SYC` is low on the demo
> board while the module is working.** The demo board produced a clean 1.32 Vpp
> tone, which is impossible without SYSCLK, so the part was clocked and `SYC`
> was low simultaneously - most likely the demo firmware disables the
> `SYNC_CLK` pin in CFR2, as the JQIamo library does. **A low `SYC` therefore
> proves nothing.** Every inference in this file that ran "SYC dead -> no
> reference" is void, including our own bench readings.
>
> The `CSB` clock below is also probably not a hidden reference. A true alias
> almost never lands exactly on fs/2, and 688,906 of 688,915 one-sample runs
> means the signal really is near 23.01 kHz - which is what back-to-back SPI
> looks like (a 5-byte transaction at 1 MHz SCLK is ~40 us, a ~23 kHz rate at
> ~50% duty). Needs a scope to settle; the LA cannot.
>
> **What is actually established:** the module works on the demo board; both
> rails are good at the package on our bench; `PD` is strapped; our bench
> produces no output even with the PLL bypassed, where a clocked part would
> show 400 kHz. Whether our module is clocked is **not currently known** - the
> instrument we were using to decide it does not answer the question.
>
> **The open question is now "does the part respond to SPI at all", and we
> cannot answer it because we never implemented readback.** That is the gap to
> close next.

> **Superseded, 2026-09-08 (third revision).** The "Resolved" note below is
> itself withdrawn. It argued that the demo board could not have supplied a
> clock, because no pin of its header appeared to carry one. That observation
> was an artifact: a logic-analyzer capture at 46 kHz renders a 40 MHz clock as
> a 23 kHz square wave, which does not look like a clock.
>
> The capture `measurements/dev_board_cap2.bin` shows the pin labelled `CSB`
> holding a **50.00% duty square wave for 14.97 s unbroken** — 688,906 of
> 688,915 runs exactly one sample long, longest idle 152 us. Chip select is
> bursty and idles for milliseconds; this is a free-running clock.
>
> **So the demo board does supply a reference on the header, and the original
> "break between W1 and REF_CLK" diagnosis is back.** It is consistent with
> every measurement taken since: `SYC` flat at 0.021 V on our bench, no lock, no
> output, and the old "FPGA reference injected at W1 pins - no effect" result
> that never fitted the W1-is-good theory.
>
> Open: which physical pin carries that clock, and at what frequency. The LA
> cannot answer the second - it only establishes "above 23 kHz".
>
> **Lesson: this file has now asserted three different conclusions about the
> same trace. Each was reasoned from real measurements, and the first two were
> wrong because of what the measurement could not see rather than what it
> showed.** Record the instrument's limits beside the reading.

> **Superseded, 2026-09-08 — see above.** W1 reaches `REF_CLK`
> correctly. The module has only two reference inputs, both selected by W1: the
> external-clock SMA (pins 1&2) and the onboard 40 MHz oscillator (pins 2&3).
> `REF_CLK` is not brought out on the control header, so the demo driver board —
> which connects only to that header — could not have supplied a clock. The
> module therefore ran on its own 40 MHz through W1 when it worked on the demo
> board, which proves the path.
>
> The original "absent at the chip" measurement was taken at 0.5 mm pitch, which
> this project has since recorded as not a measurement.
>
> The reference-path fault was ours. `refclk_gen` free-runs and drives 12.5 MHz
> onto `ck_io0`, which the table below routes to W1's AD9910-side pin — the same
> node the jumper at 2&3 connects the oscillator to. Two push-pull drivers on one
> node, and `REF_CLK` sees neither cleanly.
>
> **Running from the onboard oscillator therefore requires that `ck_io0` be
> physically disconnected, and it should be gated off in the RTL rather than
> left free-running.**

The text below is retained as the original reasoning:

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
