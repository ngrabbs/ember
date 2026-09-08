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

---

## 2026-09-08 — IO_UPDATE fix programmed; SYNC_CLK still dead

First bench run with the 1 ms `IO_UPDATE` / `MASTER_RESET` widths actually
loaded onto the board. **The FPGA side is provably healthy and the DDS side has
not moved.**

Bitstream `top_arty_z7.bit` md5 `5edfb147031405fc9d682f1915f0d5de`, built
09:22:16 — after the `ad9910_ctrl.sv` fix at 09:20:49, so the wide pulses are in
it.

`make sanity`:

| Check | Result |
|---|---|
| S1 console | PASS |
| S2a checker locked on loopback | PASS |
| S2b bit errors | PASS — 0 over 7,757,103 symbols |
| S2c lock losses | PASS — 0 |
| S2d symbol rate | PASS — 993,501 sym/s at the 1 Msym/s setting |
| S3a DDS sequencer completed | PASS — `DONE 1` |
| S3b PLL lock | **FAIL** — `LOCK 0 TMO 1` |

Configured for the module's own 40 MHz oscillator: `c0538C132`, N = 25,
40 × 25 = 1 GHz. Note the console commits an eight-digit hex argument and
starts the sequence itself, so the following `i` is redundant.

### What was measured, and what it does not tell us

**Correction.** The scope probe was on the **SMA OUT port**, not on `SYC`. The
first write-up of this run read the capture as a dead `SYNC_CLK`; that
conclusion is withdrawn, because `SYNC_CLK` was never measured.

CH1 on the SMA OUT (10x probe, DC, 1 V/div, 100 ns/div):

| | |
|---|---|
| Frequency | none measurable |
| Vpp | 0.08 V |
| Vmax / Vmin | 0.84 V / 0.76 V |
| Vavg | 0.80 V, static |

It does not move during `MASTER_RESET` or across a full register-load sequence.
Capture: `F_smaout_static_40MHz_ref.png`.

What this establishes: **there is no RF output**, which is consistent with
`LOCK 0` and nothing more. A static DC level on the DAC output is what an
unlocked, non-transmitting AD9910 looks like. It does not discriminate between
no power, no reference clock, a wrong `CFR3`, and a register load that never
took effect — every one of those produces exactly this trace.

### The measurement that would discriminate

`SYNC_CLK` on the `SYC` pin, which is why the risk table names it first. It is
SYSCLK/4 and free-runs as soon as the part has power and a reference — no SPI,
no PLL, no correct configuration required. On the module's own 40 MHz oscillator
with the PLL unlocked, SYSCLK is the bare reference, so:

| `SYC` reading | Meaning |
|---|---|
| **10 MHz** | Part is powered and clocked. The fault is downstream — `CFR3`, the register load, or PLL settings |
| **Static at a rail (0 V or 3.3 V)** | Powered, but no reference reaching REF_CLK. Look at W1 and the oscillator |
| **Static mid-rail (~0.8 V)** | Undriven node — no power, or the probe is not on the pin |

Not yet measured.

### Bench measurements, 2026-09-08

| Point | Reading | Verdict |
|---|---|---|
| `PD` (header, 3rd bottom row) | **0.000 V** | Strap present, part enabled. Note this proves the *strap*, not that the die has power — a wire to ground reads 0 V either way |
| Chip pin 2 (core rail) | **1.792 V** | 1.8 V core rail good |
| Chip pin 11 (`DVDD_I/O`) | **3.270 V** | 3.3 V I/O rail good |
| `SYC` (header) | **silent** | No SYSCLK |
| ~pins 100–12 | 40 MHz present | **Treat as pickup, not evidence.** A driven net does not appear on ~13 contiguous pins; this is the 0.5 mm pitch problem this file already warns about |

Powered, enabled, and not clocked. With both rails confirmed at the package and
`PD` strapped, the only remaining explanation for a dead `SYNC_CLK` is that no
usable reference is reaching `REF_CLK` (pins 90/91).

### The bisect that settles it

The module is known good — the demo board proved it. The variable that has
changed since is **our FPGA being attached**. Three candidates, in order:

1. **`ck_io0` still landed on W1 pin 2.** `refclk_gen` free-runs, so the FPGA
   drives 12.5 MHz out of `ck_io0` continuously regardless of what the
   sequencer is doing. With the jumper at 2&3 that output fights the 40 MHz
   oscillator's output — two push-pull drivers on one node, the reference gets
   clamped to neither, and SYSCLK stops. Also the failure class that already
   cost this project a board.
2. **W1 not actually at 2&3.**
3. **`RST` held high.** The RTL deasserts it in `S_SETTLE` and it resets to 0,
   verified in simulation but not on the pin.

The decisive test is to reproduce the demo-board condition on this bench:
**disconnect every FPGA signal, strap `PD` and `RST` to GND, W1 at 2&3, power
up, scope on `SYC`.** Expect 10 MHz (40 MHz reference / 4, PLL unlocked).

- `SYC` alive with the FPGA off the board → the fault is in our wiring or our
  driving, and it bisects from there one signal at a time.
- `SYC` still dead → the fault is the module's reference path after all, and the
  earlier W1-to-`REF_CLK` suspicion comes back into play.

Either answer is worth more than another round of probing fine-pitch pins.

### Toolchain note: a second `hw_server` will steal the cable

`make program` failed first with `Device xc7z020_1 is no longer available`
immediately after the chain enumerated correctly as `arm_dap_0 xc7z020_1`.

Cause: an unrelated Vivado container on m75q was running its own `hw_server`
for a different board on a Digilent JTAG-HS2. `hw_server` opens **every** FTDI
device it can see, and the container is given `/dev/bus/usb` wholesale, so it
had also claimed the Arty's FT2232H and was holding it. The kernel log shows
both servers on the same device:

```
usb 3-1.2: usbfs: process <pid> (hw_server) did not claim interface 0 before use
```

Killing the other container's `hw_server` freed the cable and programming
succeeded immediately. **If programming fails this way, check for another
`hw_server` before suspecting the board:**

```bash
sudo lsof /dev/bus/usb/<bus>/<dev>     # who holds the Arty's FT2232H
```

---

## 2026-09-08, second session — reference gating fixed, part still not clocked

### The demo board settles the W1 question

Every pin of the demo driver board's header was checked: **none carries a
clock**. `REF_CLK` is not brought out on that header, and the module's only two
reference inputs are the external SMA and the onboard 40 MHz oscillator, both
selected by W1. So the module was clocked by its own oscillator through W1 when
it worked on the demo board. **The W1 → `REF_CLK` path is good**, and the
earlier "break between W1 and REF_CLK" is now properly refuted rather than just
doubted.

### A code fault, found and fixed

`refclk_gen` was instantiated with no enable and free-ran from power-on, driving
12.5 MHz onto `ck_io0` — which the pin map routes to W1's AD9910-side pin, the
same node the oscillator drives at W1 2&3. Two push-pull drivers on one node.

Fixed: the reference generator is now gated by `refclk_en`, default **off**, set
over the console with `x0` / `x1`, and reported as `REF n` in the `k` status
line. The disabled state is **high-Z, not low** — driving that node low against
a running oscillator is a harder short than the collision being prevented.
Confirmed in the implemented design: `OBUFT | 1` in `utilization.rpt`.

The console's default CFR3 is now `0x0538C132` (N = 25, for the module's own
40 MHz), matching the default `refclk_en = 0`. The two now agree; previously the
default was N = 80 for an FPGA reference that the default wiring did not supply.

### It was not the cause

With `REF 0` confirmed and `ck_io0` released, there is still no lock.

| Check | Result |
|---|---|
| S1 console | PASS |
| S2a–d symbol engine | PASS — 0 errors over 7,752,072 symbols, 992,788 sym/s |
| S3a sequencer completed | PASS |
| S3b reference released | PASS — `REF 0` |
| S3c PLL lock | **FAIL** — `LOCK 0 TMO 1` |

### The sharpest test yet: PLL bypassed

`c0738C000` — VCO SEL = 111, PLL enable = 0, input divider bypassed. This takes
the PLL out of the picture completely: SYSCLK becomes the bare 40 MHz reference,
and FTW `0x028F5C29` should put **exactly 400 kHz** on the SMA
(0x028F5C29 / 2^32 x 40 MHz). The sequencer loads the profiles even after a lock
timeout — `// carry on; 40 MHz still works` — so FTW does get written.

Measured on OUT, AC coupled, 1 us/div: **no tone. 100 mV of noise, no frequency
reading.**

That is the cleanest statement of the fault so far:

> With the PLL bypassed, the profiles loaded, `PD` strapped, both rails good at
> the package, the FPGA off the reference net, and W1 on a path proven good by
> the demo board — **the part still produces nothing.**

The DAC and output network are known good (1.32 Vpp on the demo board), so the
remaining explanation is that SYSCLK is absent: no reference is reaching
`REF_CLK`, or nothing is being captured.

### Still not measured: `SYC`

Every conclusion above is inference. `SYNC_CLK` is the one measurement that
separates "not clocked" from "clocked but not transferring", and the probe has
been on the SMA OUT for this entire session. **Expect 10 MHz** (40 MHz / 4) if
the part is clocked.

### Worth retrying: FPGA as the sole reference driver

The earlier "FPGA reference injected at W1 pins → no effect" result predates
both the `IO_UPDATE` width fix and the `S_DONE` restart fix, and this file
already notes that several results from that period "may never have re-run the
sequencer at all". It is worth repeating now:

- Remove the W1 jumper entirely, so nothing else drives the node.
- Wire `ck_io0` to W1 **pin 2** (the centre, AD9910 side).
- Console: `x1`, then `c0538C1A0` (N = 80 for 12.5 MHz).

With the jumper out, the FPGA is the only driver of `REF_CLK` and there is no
contention by construction.

---

## 2026-09-08 — found: the module needs `PWR`, and our interconnect omits it

Demonstrated, not inferred. Connecting **only the pins our FPGA drives** to the
demo board reproduced our exact failure on known-good hardware: no signal.
Adding **`PWR`** made it work.

Working set: **all four GND**, `CSB`, `SCK`, `SDO`, `SDIO`, `PF0`, `PF1`, `PF2`,
`IOUP`, `PD`, `PLL`, `RST`, **`PWR`**.

Our pin map has all of these except `PWR`.

### Why this explains everything

The one measurement that never fitted any theory was 40 MHz **present at U5 and
at W1, absent at the chip**, with both rails correct at the package. If `PWR`
gates an oscillator or a clock buffer upstream of `REF_CLK`, then the AD9910 is
healthy and simply unclocked — and that produces, in order: no SYSCLK, no PLL
lock, no output, and no 400 kHz even with the PLL bypassed. Every one of those
is what we measured.

### How this went wrong for a day

Three separate conclusions were written into the repo as fact and each was
withdrawn:

1. "Break between W1 and `REF_CLK`" — withdrawn on the demo-board test.
2. "W1 is good, the demo board proves it" — withdrawn when a 46 kHz capture
   turned out to be unable to show a 40 MHz clock.
3. "`SYNC_CLK` dead means no reference" — withdrawn when `SYC` measured **low on
   the demo board while it was working**, most likely because the demo firmware
   disables the pin in CFR2.

`SYC` was treated as the definitive test for hours. It is not: a low `SYC` is
consistent with a fully working part.

**The lesson is about method, not about the AD9910.** Every wrong conclusion
came from reasoning about what we could not see, using instruments whose limits
were not written down beside their readings. The thing that actually solved it
was a controlled substitution on known-good hardware — removing pins until it
broke, adding them back until it worked. That was available on day one and is
worth reaching for well before a fourth round of probing.

### Next

1. Measure `PWR` on the running demo board — steady 3.3 V, steady 5 V, or
   toggling. That decides whether it is a strap or a driven signal.
2. **Source it from the DDS module's own supply, never from the Arty.** Ground
   stays the only connection between the boards.
3. If it is driven rather than strapped, it goes on the ChipKit header — both
   Pmods are fully committed — and into the XDC and `ad9910_ctrl`.

---

## 2026-09-08 — M1 AND M2 MET. `PWR` strapped to GND, and the carrier came up.

`PWR` tied to GND at the module. Nothing else changed. First `make sanity` after
programming:

```
[PASS] S1  UART console responds
[PASS] S2a checker locked on the loopback
[PASS] S2b zero bit errors            0 errors over 7,814,100 symbols
[PASS] S2c zero lock losses           0
[PASS] S2d symbol rate                1,000,658 sym/s at the 1 Msym/s setting
[PASS] S3a DDS sequencer completed    DONE 1
[PASS] S3b reference generator released
[PASS] S3c AD9910 PLL locked          LOCK 1  TMO 0
all checks passed
```

`TMO 0` — the PLL locked promptly rather than timing out. SYSCLK is 1 GHz from
the module's own 40 MHz crystal, N = 25, `CFR3 = 0x0538C132`, with the FPGA off
the reference net entirely (`REF 0`, `ck_io0` high-Z).

### M1 gate: a measured tone at the programmed frequency

Scope on the SMA OUT, AC coupled, 10x probe. Period measurement at a timebase
chosen per frequency:

| FTW | Programmed | Measured | Error |
|---|---:|---:|---:|
| `0x00418937` | 1 MHz | 1.0000 MHz | 0 ppm |
| `0x028F5C29` | 10 MHz | 10.0000 MHz | 0 ppm |
| `0x0CCCCCCD` | 50 MHz | 50.0000 MHz | 0 ppm |
| `0x1999999A` | 100 MHz | ~100 MHz | scope-limited |

The carrier tracks the tuning word across two decades. The 100 MHz row is the
DS1202Z-E quantising period to 0.1 ns (readings land on 1/9.9 ns and 1/9.8 ns),
not DDS error. The instrument's hardware counter was tried and is less reliable
than the period measurement at this amplitude — recorded here so nobody repeats
it. Capture: `G_m1_carrier_10MHz_locked.png`.

Amplitude falls from 340 to 160 mVpp across 1 to 100 MHz — DAC sinc roll-off
plus cable and probe response, and modest overall because **we still never write
the DAC full-scale current** (register `0x03`; the JQIamo driver sets `0xFF`).

### M2 gate: 180 degree phase reversals at symbol boundaries

`PF0` is driven by `tx_symbol`, and profiles 0 and 1 are loaded 180 degrees
apart, so BPSK needed no further work once the carrier existed. Same carrier,
same scope settings, pattern changed over the console:

| Pattern | Trace | Counter | Freq max | Freq min |
|---|---|---:|---:|---:|
| `p0` constant 0 | single clean sine | 10.0000 MHz | 10.1 MHz | 9.90 MHz |
| `p3` PRBS-7 | **two overlapping phases** | 10.2520 MHz unstable | **13.3 MHz** | **6.67 MHz** |

Captures: `H_bpsk_p0.png`, `H_bpsk_p1.png`, `H_bpsk_p3.png`.

The frequency spread is the quantitative proof, not just the visual smear.
**6.67 MHz is exactly 10 MHz / 1.5.** A 180 degree phase reversal landing near a
zero crossing stretches the measured period to 1.5 T, which is the maximum a
half-cycle jump can produce; flips landing elsewhere in the cycle fill in the
range up to 13.3 MHz. A frequency error or a glitch would not produce that
signature. A clean carrier under `p0` and this under `p3`, with nothing changed
but the pattern selector, is the modulator working.

### What actually solved it

One wire. `PWR` strapped to ground.

The finding came from **controlled substitution on known-good hardware** — wiring
only our pin set to the demo board, confirming it failed the same way, then
adding pins until it worked. Not from reasoning about symptoms. Three conclusions
reached by reasoning were written into this repo as fact during the search and
all three were withdrawn:

1. "Break between W1 and `REF_CLK`."
2. "W1 is good, the demo board proves it."
3. "`SYNC_CLK` dead means no reference" — `SYC` measures **low on the demo board
   while it is working**, so a low `SYC` proves nothing.

Each was sound reasoning from real measurements. Each failed because the limits
of the instrument were not written down beside the reading — a 46 kHz logic
capture cannot show a 40 MHz clock, and a `SYNC_CLK` pin can be disabled in CFR2.

**Two pins on this breakout hold the part off when floating — `PD` and `PWR` —
and both present as a clock fault.** Check every strap with a meter before
diagnosing anything on this module.

---

## 2026-09-08 — DAC full-scale current and SPI readback added

Two gaps against the JQIamo reference driver, both closed. Neither was the cause
of the day's fault, but the second is the instrument whose absence made the
fault expensive to find.

### FSC: register 0x03, and it nearly doubled the output

The sequencer now writes the auxiliary DAC control register with `FSC = 0xFF`,
folded in after the profile writes so the final `IO_UPDATE` commits amplitude
and profiles together. Measured on the SMA, constant pattern, AC coupled:

| Carrier | Before | After | Gain |
|---:|---:|---:|---:|
| 1 MHz | ~0.340 V | **0.608 V** | +5.1 dB |
| 10 MHz | 0.292 V | **0.512 V** | +4.9 dB |
| 50 MHz | ~0.224 V | **0.416 V** | +5.4 dB |

`FSC` is a module parameter, so it can be turned down if a later stage needs
less drive. Capture: `I_bpsk_fsc_full_scale.png`.

### Readback: `v` reads CFR3 back off the part

Verified against real silicon, and it tracks changes rather than echoing our own
register:

```
readback          DDS CFR3 0538C132     the value the sequencer wrote
c0538C1A0   ->    DDS CFR3 0538C1A0     follows a live change
c0538C132   ->    DDS CFR3 0538C132     and back
```

The AD9910 powers up in **2-wire mode**, returning read data on `SDIO` rather
than `SDO`. So `dds_sdio` is now an `inout` with a tri-state (`OBUFT`, confirmed
in the implemented design), `spi_master` gained a `tx_read` input that releases
the line for a byte and captures it, and `ad9910_ctrl` gained a read path.

The alternative — set `CFR1[1]` for 3-wire and read on `SDO` — was the original
plan recorded in `spi_master`'s header and was never implemented. It is also
**circular as a diagnostic**: it needs a working write before it can verify that
writes work. The 2-wire path works from power-up defaults and assumes nothing.

`S_RD_CMD` is a separate state rather than joining the shared write state,
because that state raises `CS` by default and relies on each case re-lowering
it. A read must hold `CS` low across the bus turnaround, and inheriting the
wrong default there cost a debug cycle even in simulation.

### Why this mattered

The whole of 2026-09-08 was spent inferring the part's internal state from
external symptoms, and the inference was wrong three times. With `v`, the
question "does the part respond at all" is one keystroke and is not a matter of
opinion. **Build the instrument before the debugging session, not after it.**

### Test coverage

- `tb_spi_master` E8a-c: read bytes return the slave's value, a following write
  still transfers. E9a/b: `mosi_oe` low for every read edge, high for every
  write edge — on hardware that gates a tri-state, so getting it wrong means the
  FPGA and the AD9910 drive `SDIO` simultaneously.
- `tb_ad9910_ctrl` F11a/b: FSC framed as address 03 plus four bytes, value
  `0x000000FF`. F12a-d: readback returns the slave's value, one transaction,
  instruction byte `0x82`, five bytes. F13: `SDIO` released for every read data
  bit. F14: a read does not reset the part.
- `tb_uart_console` D15a-c: `v` issues exactly one read, waits for it to
  complete before printing, and tracks a changed value. The wait matters — an
  earlier version printed the previous value, which defeats the purpose.
