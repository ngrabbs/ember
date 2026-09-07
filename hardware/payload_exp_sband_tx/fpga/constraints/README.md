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
