# M0 symbol engine — measurements

Bench results for milestone M0 on the Digilent Arty Z7-20.

## Setup

| | |
|---|---|
| Board | Arty Z7-20, XC7Z020-1CLG400C |
| Bitstream | `fpga/build/vivado/top_arty_z7.bit` |
| Clock | 125 MHz |
| Scope | **Rigol DS1202Z-E**, 200 MHz, 1 GSa/s, at 192.168.1.50. Chosen over the Digilent because `symbol_tick` is one 125 MHz clock, 8 ns wide, and at 100–125 MS/s the Digilent can miss it entirely |
| Probes | **10× attenuation** — the scope must be told `:CHANnel<n>:PROBe 10` or every voltage reads a factor of ten low |
| Automation | `fpga/tools/bench.py` drives both ends: the FPGA over its UART console, the scope over SCPI on port 5555. A capture run needs nobody at the bench |
| Probes | Ch1 `tx_symbol` (Pmod JA pin 1), Ch2 `symbol_tick` (JA pin 2), ground on JA pin 5 or 11. **Both DC coupled** |
| Loopback | jumper JA pin 1 → pin 4 |

Controls: `pattern_sel = {SW1, SW0}` — `00` zero, `01` one, `10` alternating,
`11` PRBS-7. `btn[0]` reset, `btn[1]` advance rate, `btn[2]` hold to disable,
`btn[3]` clear the error latch. `led[1:0]` rate, `led[2]` locked, `led[3]`
sticky error or lock loss.

## Results

| Date | Test | Result |
|---|---|---|
| 2026-09-07 | Loopback, 1 Msym/s, counted over 62 s | **62,049,047 symbols, zero errors, zero lock losses** |
| 2026-09-07 | Symbol rate, measured | **1,000,000 sym/s** — 0.0000% from nominal |
| 2026-09-07 | Negative test: jumper pulled | `led[2]` goes dark — the checker fails honestly |
| 2026-09-07 | Alternating at 1 ksym/s | Clean square wave observed on Ch1 |

### The counted loopback run

Raw console output, verbatim. UART on Pmod JB at 115200 8N1, read from the
Vivado host over `/dev/ttyUSB0`. Commands `p3` (PRBS-7), `r3` (1 Msym/s), `z`
(zero the counters), then `s` before and after the run.

```text
LOCK 1 BITS 0000001F43DC ERR 00000000 LOSS 0000     <- after zeroing
LOCK 1 BITS 000003D20EF3 ERR 00000000 LOSS 0000     <- 62.049030 s later
```

| Quantity | Value |
|---|---:|
| Start count | 0x1F43DC = 2,048,988 |
| End count | 0x3D20EF3 = 64,098,035 |
| **Symbols checked** | **62,049,047** |
| **Errors** | **0** |
| **Lock losses** | **0** |
| Elapsed | 62.049030 s |
| **Measured rate** | **1,000,000 sym/s** |
| Nominal rate | 1,000,000 sym/s (125 MHz ÷ 125) |
| Rate error | 0.0000% |

Two things fall out of this beyond the pass itself.

**The divider is measured, not assumed.** Every document since the trade study
has asserted that the four symbol rates divide the board clock exactly. The
measured rate agrees with the nominal to the resolution of the measurement,
which turns that assertion into an observation.

**A bit-error-rate bound.** Zero errors in 62,049,047 bits gives, at 95%
confidence, **BER < 4.8 × 10⁻⁸** — using the standard zero-failure bound
`3/N`. This is the payload's first quantitative link-quality figure. It
describes the FPGA's own symbol path through a jumper wire, not an RF link, and
should not be quoted as anything else.

## Scope captures, 2026-09-07

All driven over SCPI from `fpga/tools/bench.py`, with the pattern and rate set
over the UART console in the same script.

### A — constant levels at Pmod JA pin 1

| Pattern | Vavg | LVCMOS33 limit | |
|---|---:|---|---|
| constant 0 | **0.063 V** | VOL ≤ 0.4 V | pass |
| constant 1 | **3.338 V** | VOH ≥ 2.4 V | pass |

`A_constant_zero_0v.png`, `A_constant_one_3v3.png`

### B — alternating: frequency is half the symbol rate

| Symbol rate | Measured | Expected | Error |
|---:|---:|---:|---:|
| 1 ksym/s | 500.0 Hz | 500 Hz | **0.000%** |
| 10 ksym/s | 5,000.0 Hz | 5,000 Hz | **0.000%** |
| 100 ksym/s | 50,000.0 Hz | 50,000 Hz | **0.000%** |
| 1 Msym/s | 500,000.0 Hz | 500,000 Hz | **0.000%** |

`B_alternating_1ksym_500Hz.png`

### C — PRBS-7 decoded from the pin

Ch1 captured at 1 ksym/s, thresholded at 1.65 V, sampled at each symbol centre,
and matched against the golden model at all 127 phases:

```text
1100001010001111001000101100111010100111110100001110001

*** MATCHES the golden PRBS-7 sequence at phase 19 ***
```

This closes the loop end to end — Python golden model, to SystemVerilog RTL, to
a Vivado bitstream, to silicon, to copper, to a scope probe, and back to the
same golden model that started it. `C_prbs7_1ksym.png`

### D — the 8 ns symbol_tick

Triggered on Ch2 at 20 ns/div, PRBS-7 at 1 Msym/s:

| Measurement | Value | |
|---|---:|---|
| `symbol_tick` width | **8.000 ns average** (7.6–8.4 spread) | one 125 MHz clock, exactly |
| `symbol_tick` rise | 5.47 ns average | see the caveat below |
| `tx_symbol` rise | 6.40 ns | see the caveat below |
| `tx_symbol` fall | 3.60 ns | |
| Tick amplitude | 3.52 V top, 4.00 V peak | see the caveat below |

`D_symbol_tick_8ns_1Msym.png`

**The edge and overshoot numbers are measurement-limited, not design numbers.**
These were taken with a 10× probe on its standard alligator ground lead, whose
inductance rings at exactly these edge rates. Rise times of 5–6 ns on an FPGA
output that genuinely switches in well under 2 ns are the probe, not the pin;
and the 4.0 V peak — which would be marginal against an LVCMOS33 absolute
maximum of roughly VCCO + 0.55 V — is very likely ground-lead ringing. **Before
anyone draws a conclusion about overshoot, re-measure with a short ground
spring.** The 8.000 ns width is unaffected: a width measurement between 50%
crossings is insensitive to this.

## Outstanding

- [x] Constant zero and constant one — valid 3.3 V LVCMOS levels at the pin
- [x] Alternating frequency = symbol rate / 2, at all four rates
- [x] Zoomed capture on `symbol_tick`: the 8 ns pulse measured at 8.000 ns
- [x] Read `bit_count` and `error_count` back over the UART
- [ ] Re-measure edge rates and overshoot with a short ground spring, to
      separate probe artefact from real signal
- [ ] The scope's real-time clock is wrong — captures carry 2014 timestamps.
      Set it before the next session so capture provenance is meaningful.

The `DS1Z_QuickPrint*.png` files are the initial manual captures taken at the
bench before the SCPI automation existed. Kept for the record.

Captures go in `captures/`, named `<date>_<pattern>_<rate>.png`, with the
timebase, coupling and trigger settings visible in the screenshot.
