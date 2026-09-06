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
make check      # golden + lint + both testbenches
make sim-long   # the M0 gate: 1,000,000 symbols, zero errors
make count      # iCE40 resource usage, per module
make waves      # FST traces for GTKWave
make tools      # install notes if something is missing
```

`make golden` is worth running first on any machine. It needs nothing but
Python 3 and it checks the part of the design most likely to be wrong.

Every simulation target runs **Verilator `--lint-only` before Icarus compiles**.
Verilator's diagnostics are markedly better, so it should be the first thing to
see a change; Icarus then runs the event-driven testbench. The RTL is held to a
clean `-Wall` with no suppressions except one documented empty debug port.

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

**M0 is verified in simulation.** All checks pass and the acceptance gate is
met.

| Run | Result |
|---|---|
| `make golden` | 6 sequence properties + 12 checker-model scenarios pass |
| `make lint` | Verilator `-Wall` clean, RTL and both testbenches |
| `make sim-prbs` | 22 checks pass |
| `make sim-tx` | 26 checks pass (200,000 symbols) |
| `make sim-long` | **1,000,000 symbols, 0 errors, 0 lock losses** — the M0 gate — in 4.8 s |

The suite was checked against a deliberately broken design as well as a working
one: inverting one PRBS feedback tap drops the period from 127 to 93 and fails
A1, A2, A3, A4b, B1b and B1d with a nonzero exit status. A test suite that
cannot fail is not evidence of anything.

Two bugs were found and fixed getting here:

- `div_target` held the divisor but was sized `clog2(DIV_MAX)` bits, one short
  of representing `DIV_MAX` itself. A divisor of 2 truncated to zero and only
  produced the right period by accident of the borrow. It now stores the
  terminal count `DIV-1`, which always fits. Found by reading, before the
  toolchain existed.
- `tb_prbs7` let one clock edge through before sampling, so the capture began
  at b[1] and the golden-vector comparison was off by one bit. Found by the
  testbench itself — A1 failed while the phase-independent checks A2, A3 and A4
  all passed, which is exactly the signature of a phase offset rather than a
  broken generator.

### Resource usage

From `make count`, synthesised for iCE40 with `-noflatten`:

| Module | LUT4 | Flip-flops | Carry |
|---|---:|---:|---:|
| `prbs7_gen` | 2 | 7 | — |
| `tx_pattern_source` | 29 | 25 | 31 |
| **Total** | **31** | **32** | **31** |

Small enough that device density is not a constraint at M0. The carry cells are
the symbol-rate divider, which is sized for the slowest rate — 100,000 counts
at 1 ksym/s from a 100 MHz clock. It shrinks if the slow rates are dropped.
This is a synthesis estimate only; place-and-route and timing closure wait on a
verified pin constraint file.

### Toolchain of record

| Tool | Version |
|---|---|
| oss-cad-suite | 20260906 |
| Icarus Verilog | 14.0 (devel) s20260301-403-g5ab23063f |
| Verilator | 5.053 devel rev v5.052-22-g7cf8c5cca |
| Yosys | 0.68+195 (git sha1 435977e97) |
| Python | 3.11.6 |

`make tools` prints the install route. The recommended one is the YosysHQ
oss-cad-suite tarball: one download, no root, and iverilog, verilator, yosys,
nextpnr-ice40, icestorm and gtkwave all at consistent versions.

## Next

The open questions were settled on 2026-09-06. An IceZero, a Raspberry Pi and an
FTDI TTL-232R-3.3V cable are all on hand; bench control and readout go over
**UART on J3**; and the three bring-up criteria that assumed an external buffer
have been amended, because under the selected architecture `tx_symbol` never
leaves the FPGA. The pin plan and build flow are in
[`constraints/README.md`](constraints/README.md).

What remains is build work rather than open questions:

- [ ] `rtl/uart_tx.sv`, `rtl/uart_rx.sv` and a small command/status core — set
      pattern, rate and enable by typed command; print `prbs_locked`,
      `bit_count` and `error_count` on demand.
- [ ] `rtl/top.sv` — instantiate the symbol engine and the checker, map the
      pins, drive the LEDs, and provide reset. The checker's loopback comes back
      through a PMOD jumper.
- [ ] `constraints/icezero_rev2.pcf`, then place-and-route and a timing report.
- [ ] Decide whether to force the output flop into the IO cell (`SB_IO` with
      `PIN_OUTPUT_REGISTERED`) or leave the placement to nextpnr. It affects how
      strongly the no-glitch claim holds at the pin rather than in the fabric.
- [ ] Confirm the board is TE0876-02 rev2, and confirm the J3 TX/RX direction
      before blaming the RTL for a silent UART.
- [ ] Load the bitstream and capture the M0 traces: constant high and low,
      alternating at each rate, PRBS-7. Commit them under `../measurements/`.
- [ ] Run the hardware gate — 1,000,000 symbols, zero errors — and record the
      count read back over the UART rather than inferring it from an LED.
