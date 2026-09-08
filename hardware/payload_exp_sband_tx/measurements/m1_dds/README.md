# M1 — AD9910 DDS bring-up

Bench record for the DDS half of M1 on the Digilent Arty Z7-20.

## Status: root cause found — our IO_UPDATE pulse was too short

**Superseded diagnosis.** This document previously concluded "a break between
W1 and REF_CLK, a fault on the DDS board". That was wrong, and the correction is
recorded below rather than edited away, because the reasoning that produced it
was plausible and the way it failed is worth keeping.

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

## The module is fine — proven by substitution

Running the module on the demo driver board it shipped with produced a clean
**1.32 Vpp tone, stable at 44.6 kHz**, measured across every timebase, with a
consistent 22.4 us period. `E_demoboard_output_working.png`.

That single test destroyed the "board fault" conclusion. The module clocks, its
PLL runs, its DAC and output network work. Substituting a known-good driver
should have been the first move once the FPGA side was verified clean, rather
than many rounds of probing an undocumented board from the outside.

## Root cause: IO_UPDATE was never wide enough

Found by reading a known-good reference implementation
([JQIamo/AD9910-arduino](https://github.com/JQIamo/AD9910-arduino)). Its
register values essentially match ours — same VCO band, same charge pump; the
only real difference is CFR3[15], where it leaves the divide-by-two input
divider engaged and we bypass it, which is harmless either way.

The difference that mattered was timing:

```c
void AD9910::update(){
  digitalWrite(_updatePin, HIGH);
  delay(1);                        // ONE MILLISECOND
  digitalWrite(_updatePin, LOW);
}
```

Ours was **96 ns**. The datasheet (Table 3, pin 55) states that `I/O_UPDATE` and
`PROFILE[2:0]` are captured on the rising edge of `SYNC_CLK`, and `SYNC_CLK` is
SYSCLK/4. **Before the PLL locks, SYSCLK is the bare reference**, so:

| Reference | SYNC_CLK | period | 96 ns pulse |
|---|---:|---:|---|
| onboard 40 MHz | 10 MHz | 100 ns | 1.0 period — marginal |
| our 31.25 MHz | 7.81 MHz | 128 ns | 0.8 period — missed |
| our 12.5 MHz | 3.125 MHz | 320 ns | **0.3 period — missed** |

**The pulse was never wide enough in any configuration tried.** The first
`IO_UPDATE`, the one that transfers CFR3 and enables the PLL, was never
captured. So CFR3 never took effect, the PLL never enabled, `PLL_LOCK` stayed
low, and profile 0 kept its reset default of FTW = 0 — leaving the DAC at DC
and the SMA silent. Every symptom, and the SPI bus tested perfectly throughout
because the writes themselves were landing in the buffer correctly.

Worse: dropping the reference from 31.25 MHz to 12.5 MHz to suit the breadboard
made it *less* likely to work, by lengthening the SYNC_CLK period against a
fixed pulse width. That change was reasoned about carefully and was actively
counterproductive.

Fixed: `RESET_US`, `SETTLE_US` and `IOUP_US` are now 1 ms each, matching the
reference implementation, with the reasoning in the module header so nobody
shortens them again.

## A second bug that corrupted the search

`ad9910_ctrl` could not restart. `S_DONE` handled `start` by stepping to
`S_IDLE`, but `start` is one cycle wide and was gone by the time the FSM
arrived — so **every second `i` command silently did nothing**. The alternating
`DONE 0 / DONE 1 / DONE 0` across repeated re-inits was read as a polling race
and dismissed. It was not: half of those runs never executed. Several W1 and
`PD` results recorded as negative may never have re-run the sequencer at all.

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

**Substitute a known-good driver early.** One test on the demo board settled in
minutes what hours of probing had not, and it decisively refuted a conclusion
that had already been written down as fact.

**Read the reference implementation before debugging the hardware.** The root
cause was a `delay(1)` in a public Arduino library. It was findable at any point
and would have saved the entire investigation.

**A confident diagnosis from consistent evidence can still be wrong.** "The
40 MHz reaches W1 and SYNC_CLK is dead, therefore the trace is broken" was
sound reasoning from real measurements, and it was wrong, because it assumed
our own driving of the part was correct.

## Next

1. Reconnect the FPGA to the DDS per the pin map. Leave `ck_io0` disconnected
   and use the module's own 40 MHz with **W1 at 2&3** — the configuration the
   demo board just proved works.
2. Console `c0538C132` sets N = 25 for 40 MHz × 25 = 1 GHz, then `i`, then `k`.
3. `make sanity` first, after any rewiring, before anything else.

If it locks, `PF0` already carries the symbol stream and the SMA should show
BPSK immediately.
