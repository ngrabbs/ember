# M1 — AD9910 DDS bring-up

Bench record for the DDS half of M1 on the Digilent Arty Z7-20.

## Status: blocked on a fault in the DDS board's reference clock path

The FPGA side is complete and verified. The AD9910 breakout does not clock.

## Setup

| | |
|---|---|
| DDS | AD9910BSVZ breakout, 40 MHz onboard oscillator, own 5 V barrel jack |
| FPGA | Arty Z7-20, `top_arty_z7`, `ad9910_ctrl` + `spi_master` + `refclk_gen` |
| Interconnect | see [`../../fpga/constraints/README.md`](../../fpga/constraints/README.md) |
| Console | UART on Pmod JB, 115200 8N1, via `/dev/ttyUSB0` on the Vivado host |
| Scope | Rigol DS1202Z-E over SCPI, driven from `fpga/tools/bench.py` |

## The fault

`SYNC_CLK` (AD9910 pin 55, header `SYC`) outputs SYSCLK/4 and **requires no
configuration whatsoever** — the part powers up with the PLL bypassed, so
SYSCLK is the bare reference and SYNC_CLK should appear the instant a reference
exists. It measured flat, at noise level, in every condition tried.

That one fact explains every symptom:

```
no REF_CLK -> no SYSCLK -> no SYNC_CLK
           -> IO_UPDATE cannot transfer the register buffer
           -> CFR3 never takes effect -> PLL never enabled -> PLL_LOCK low
           -> profile 0 keeps its reset default FTW = 0 -> DAC at DC -> silent SMA
```

It is upstream of everything, which is why the SPI wiring tested perfect and
changed nothing.

## What was eliminated

| Checked | Method | Result |
|---|---|---|
| Supplies U1 / U2 / U3 | DMM | 1.79 / 3.29 / 1.80 V — correct |
| U5 oscillator | scope | exactly **40.000 MHz**, clean 3.3 V swing |
| `PD` / EXT_PWR_DWN (pin 18) | DMM | grounded. Was **floating** initially — a genuine fault, fixed |
| `XTAL_SEL` (pin 95) | DMM | ~0 V — correct for external drive |
| `MASTER_RESET` polarity | datasheet | active high; our pulse-then-low is right |
| `SCLK` edge | datasheet | rising edge on write; SPI mode 0 is right |
| SPI wiring at the DDS header | DMM | `CSB` 3.3 V idle, `SCK`/`IOUP`/`RST` 0 V — correct |
| W1, both positions | scope on `SYC` | no effect, reseated and power-cycled |
| FPGA reference injected at W1 pins | scope on `SYC` | no effect |
| 40 MHz path | scope | present at U5 and at W1, **absent at the chip** |

**Conclusion:** a break between W1 and the AD9910's `REF_CLK` (pins 90/91).

## Lessons worth keeping

**A floating `PD` looks like three faults at once.** `EXT_PWR_DWN` floating high
puts the part in full power-down, where it ignores SPI entirely — presenting
simultaneously as a dead serial bus, a missing clock and a broken DAC. It was
in the pin map, but in a "strapped at the board" table *below* the wiring
tables, where it read as optional housekeeping. It has been moved to the front
and marked required. **A mandatory connection belongs in the list people
follow, not in a footnote after it.**

**Probing 0.5 mm pitch is not a measurement.** Readings at `REF_CLK` were not
repeatable between attempts, and low-amplitude pickup of the injected reference
was indistinguishable from a real driven signal. Where a header pin exists for
the same net, use it.

**`SYNC_CLK` is the right first test on any AD9910.** It needs no
configuration, no SPI and no PLL. If it is dead, nothing else is worth
investigating until it is not.

## Next

1. Rebuild the interconnect through a breadboard, per the pin map's breadboard
   notes — reference clock at **12.5 MHz** (`REFCLK_DIV = 10`, console
   `c0538C1A0`), several ground returns.
2. If `SYNC_CLK` still does not run, the remaining options are a fine wire from
   W1's chip side directly to `REF_CLK`, or a replacement board.
3. `make sanity` re-runs the full end-to-end check after any rewiring.
