# Constraints

**Target changed 2026-09-07: Digilent Arty Z7 (Zynq-7000).**

The IceZero is dead — a failed EP53A7HQI buck regulator plus a hard short on its
3.3 V rail. The full failure record, root cause and the rules adopted afterwards
are in
[`../../fpga_link_processor_logic_interface_first_bringup.md`](../../fpga_link_processor_logic_interface_first_bringup.md).

No `.xdc` is committed yet. Write `arty_z7.xdc` from **Digilent's official master
XDC** for the board revision in hand rather than transcribing pin names by hand,
and record which master file it came from.

## Signals to constrain

| Signal | Notes |
|---|---|
| `clk` | 125 MHz board clock. Needs a `create_clock` of 8.000 ns |
| `rst` | A button, active high, synchronised internally |
| `tx_enable`, `pattern_sel[1:0]`, `rate_sel[1:0]` | Slide switches and buttons, or UART commands |
| `tx_symbol` | Pmod pin — the signal to put a scope on |
| `symbol_tick` | Pmod pin — one clock wide, use it as the scope trigger |
| `tx_loopback` | Pmod pin, jumpered back from `tx_symbol` |
| `prbs_locked` | LED |
| `uart_tx`, `uart_rx` | Built-in USB-UART, no external cable |

Confirm the variant before writing anything: **Z7-10 is XC7Z010-1CLG400C**,
**Z7-20 is XC7Z020-1CLG400C**. They share a footprint but not a part number.

## Why this board

USB-JTAG and USB-UART are built in on a single cable. There is no separate
serial cable to mis-wire and no 5 V pin sitting beside 3.3 V logic — which is
exactly what killed the IceZero.

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

Under the old iCE40 target the symbol engine closed at 119 MHz against a 100 MHz
clock. The Arty's clock is 125 MHz and the Zynq's fabric is far faster, so
timing is not expected to be a constraint — but the Vivado timing report
replaces that number and should be recorded here once it exists.


---

# AD9910 interconnect — Arty Z7-20 to the DDS breakout

Eleven signals plus ground. The Arty's two Pmods have exactly ten pins free
after M0, so `PD` is strapped at the DDS board rather than driven.

## Power — read this first

The AD9910 breakout has its **own 5 V barrel jack**. Connect **GND between the
two boards and nothing else**. No 5 V, no 3.3 V, in either direction. Two
independently powered boards sharing a ground reference and signal lines.

This is not a general caution. The IceZero that this payload started on was
destroyed by exactly one wire: a USB-serial cable's 5 V conductor connected to
a board that already had its own supply.

Signal levels are compatible without translation — the AD9910 is a 3.3 V CMOS
part (`DVDD_I/O` = 3.3 V ±5%) and the Arty's Pmods are LVCMOS33. The
AMS1117-1.8 on the breakout feeds the AD9910's internal core rails only.

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

## Strapped at the DDS board

| DDS pin | Tie to | Why |
|---|---|---|
| `PD` | GND | power-down, must be low; not worth an FPGA pin |
| `TEN` | GND | TxENABLE, only used with the parallel data port |
| `DRC` `DRO` `DPH` | GND | digital ramp control, unused |
| `OSK` | GND | output shift keying, unused |

`D0`–`D15` and `F0`/`F1` (the 16-bit parallel modulation port) are left
unconnected. They are the route to QPSK and pulse shaping later, at up to
250 MSPS, but profile-pin BPSK needs none of them.

## Clock

`W1`, the jumper by the 40 MHz oscillator, selects the onboard reference versus
the external-clock SMA (`外部时钟`). Its position does not have to be determined
by inspection: `PLL_LOCK` answers it. With `W1` on the onboard oscillator the
PLL locks at 40 MHz × 25 = 1 GHz; with it on the external SMA and nothing
connected, there is no reference and lock never asserts. `ad9910_ctrl` reports
that as `lock_timeout` rather than hanging.

## What to expect

After `ad9910_ctrl` runs, the `OUT` SMA carries a tone at whatever FTW is
loaded. With `PF0` driven from `tx_symbol`, that tone flips 180° per symbol —
BPSK, at a real carrier, out of a coaxial connector.
