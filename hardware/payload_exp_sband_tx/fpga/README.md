# FPGA — M0 symbol engine

Milestone M0 of the experimental S-band payload: the reusable symbol source
that every later architecture sits on top of. Symbol timing, pattern selection,
PRBS-7, and a registered output.

See [`../README.md`](../README.md) for the payload's scope and milestones and
[`../sband_payload_architecture_trade_study.md`](../sband_payload_architecture_trade_study.md)
for why this block is built before anything else.

---

## Quick start

```bash
cd hardware/payload_exp_sband_tx/fpga
make golden     # Python only - no HDL toolchain needed
make sim        # both testbenches
make sim-long   # the M0 gate: 1,000,000 symbols, zero errors
make tools      # install notes if something is missing
```

`make golden` is worth running first on any machine. It needs nothing but
Python 3 and it checks the part of the design most likely to be wrong.

---

## What is here

| Path | Contents |
|---|---|
| `rtl/prbs7_gen.sv` | PRBS-7 generator, x^7 + x^6 + 1 |
| `rtl/prbs7_check.sv` | Free-running PRBS-7 checker with lock detection and error counting |
| `rtl/tx_pattern_source.sv` | Symbol-tick divider, pattern selector, registered output, buffer enable |
| `sim/prbs7_golden.py` | Golden model of the sequence, plus a model of the checker |
| `sim/tb_prbs7.sv` | Sequence properties and checker behaviour |
| `sim/tb_tx_pattern_source.sv` | Symbol timing, patterns, output registration, loopback |
| `constraints/` | Deliberately empty until the board is identified — see its README |

---

## The PRBS-7 convention

Stated once, here, and matched by the RTL, the golden model, and the checker:

```text
polynomial   x^7 + x^6 + 1
state        7 bits, state[6] is the MSB
seed         7'b111_1111 (0x7F)
output       state[6], taken BEFORE the shift
feedback     state[6] XOR state[5]
next state   {state[5:0], feedback}
```

"Output before the shift" is the detail most often got wrong when a generator
and a checker are written separately, or when a hex polynomial value is copied
out of a library that uses a different shift direction. It is not trusted here:
`sim/prbs7_golden.py` writes one period to `sim/vectors/prbs7_expected.txt` and
`tb_prbs7.sv` compares the RTL against that file bit for bit.

The first 127 bits, for eyeballing a scope capture:

```text
1111111000000100000110000101000111100100010110011101010011111010
000111000100100110110101101111011000110100101110111001100101010
```

A useful identity that falls out of the convention, and the one the checker
predicts with:

```text
b[k+7] = b[k] XOR b[k+1]
```

---

## Why the checker is free-running

Once locked, `prbs7_check` predicts each bit from its own history and shifts
the *predicted* bit into its register, not the received one.

A self-synchronising checker — one that shifts the received bit in — is simpler
and needs no lock logic, but a single channel error passes through the register
three times and is counted three times. That makes it useless for measuring a
bit error rate. It also never reports a loss of lock, because it silently
re-synchronises to whatever it is fed.

The cost is that lock has to be managed explicitly:

```text
HUNT    shift 7 received bits in to acquire a phase
VERIFY  free-run; 32 consecutive correct predictions before declaring lock
LOCKED  count checked bits and errors
```

VERIFY exists so a random seven-bit load is not mistaken for a lock.

Loss of lock uses a leaky bucket rather than a run of consecutive errors. After
a bit slip the received stream is a different phase of the same sequence, so
predictions fail at random with probability one half — a consecutive-error
counter would take hundreds of bits to trip. The bucket fills on each error and
empties after 64 consecutive good bits, so an isolated error decays away and
leaves lock intact, while a slip unlocks quickly. The checker model measures
the worst case across all 127 phases at **27 bits**; the testbench allows 2000.

---

## Timing contract

```text
symbol_tick is asserted for exactly one clock cycle, in the same cycle in which
a new symbol first appears on tx_symbol.
```

Both are registered off the same clock edge, so on a scope or logic analyser
`symbol_tick` marks the first clock of every symbol and works directly as a
trigger.

`tx_symbol` is assigned only inside `always_ff`. Nothing combinational reaches
it — not `pattern_sel`, not `rate_sel`, not the pattern state — so it cannot
glitch while several internal bits settle. `tb_tx_pattern_source.sv` enforces
this continuously with a monitor that fails if `tx_symbol` ever changes on a
cycle where `symbol_tick` is low.

`pattern_sel` and `rate_sel` are sampled at symbol boundaries while
transmitting, and freely while disabled. Configuring the part while disabled
and then enabling starts the first symbol at the requested pattern and rate.

`tx_oe_n` is separate from the symbol value on purpose: permission to drive the
interface and the data being driven are different things. It is only half the
story — the external buffer also needs a resistor-defined disabled state,
because no register in this FPGA has a defined value before configuration
completes.

---

## Symbol rates

Four rates are selectable at run time, so a bench session does not need a
rebuild between them. Each must divide the board clock exactly; the RTL refuses
to elaborate otherwise rather than silently producing a rate that is a fraction
of a percent off.

| `rate_sel` | Default rate | Clocks per symbol at 100 MHz |
|---|---:|---:|
| `00` | 1 ksym/s | 100,000 |
| `01` | 10 ksym/s | 10,000 |
| `10` | 100 ksym/s | 1,000 |
| `11` | 1 Msym/s | 100 |

The testbench overrides these to divisors of 16, 8, 4 and 2 so that a
million-symbol run finishes in seconds. Only the ratio matters to the checks.

## Patterns

| `pattern_sel` | Output | What it proves |
|---|---|---|
| `00` | constant zero | DC low level at the destination |
| `01` | constant one | DC high level and drive |
| `10` | alternating | Symbol rate — measures as half the symbol rate on a scope |
| `11` | PRBS-7 | Transitions, and automated error counting |

---

## Test coverage

`make sim` runs both testbenches. Every check is self-verifying; a failure
returns a nonzero exit status rather than printing something a reader has to
notice.

**`tb_prbs7`** — A1 golden-vector match · A2 period exactly 127 · A3 64/63
balance · A4 all 127 nonzero states visited and all-zeros never reached · B1
locks and counts zero errors on a clean stream · B2/B3 one injected error
counts exactly one and keeps lock · B4 a continuously inverted stream costs
lock and never re-locks · B5 removing the inversion restores lock cleanly ·
B6 a dropped bit costs lock, then re-locks at the new phase.

**`tb_tx_pattern_source`** — C1 reset idle state and disabled interface · C2
nothing ticks while disabled · C3 enable asserts the buffer enable · C4 every
`rate_sel` gives exactly its divisor · C5 constant patterns hold · C6
alternating toggles every symbol · C7 the continuous registered-output monitor ·
C8 PRBS-7 through the loopback checker with zero errors · C9 a disable/enable
cycle resumes on a clean boundary and re-locks.

`make sim-long` is the M0 gate: at least 1,000,000 symbols with zero errors.

---

## Status

The RTL, testbenches, golden model, and build flow are written. **The
testbenches have not yet been run against a simulator** — no HDL toolchain was
available on the machine they were written on. What *has* been verified is the
Python layer, which runs anywhere:

- `prbs7_golden.py --self-test` confirms the sequence properties.
- `prbs7_golden.py --checker-model` models the checker FSM bit for bit and
  reproduces every scenario in `tb_prbs7` part B, which is what grounds the
  thresholds and run lengths the testbench asserts.

Expect to fix compile errors on the first `make sim`. Install the toolchain
(`make tools`), run `make check`, and record the result here.

## Next

- [ ] Run `make sim` and `make sim-long`; record tool versions and results.
- [ ] Run `make synth` for an iCE40 resource estimate.
- [ ] Fill in the board-facts table in the bring-up document, then write
      `constraints/icezero_<verified-revision>.pcf`.
- [ ] Capture the scope traces listed in the M0 gate and commit them under
      `../measurements/`.
