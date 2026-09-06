#!/usr/bin/env python3
"""PRBS-7 golden model for the EMBER experimental S-band payload.

This file is the single source of truth for the PRBS-7 convention. The RTL in
`rtl/prbs7_gen.sv` must reproduce it bit for bit, and `sim/tb_prbs7.sv` checks
that mechanically against the vector file written here.

Convention (matches rtl/prbs7_gen.sv):

    polynomial   x^7 + x^6 + 1
    state        7 bits, state[6] is the MSB
    seed         7'b111_1111 (0x7F)
    output       state[6], taken BEFORE the shift
    feedback     state[6] XOR state[5]
    next state   {state[5:0], feedback}

The "output before the shift" choice is the one detail most likely to be got
wrong when a generator and a checker are written by different people, so it is
stated here, in the RTL header, and in the bring-up document, and it is checked
by test rather than trusted.

Usage:
    python3 prbs7_golden.py --self-test
    python3 prbs7_golden.py --write vectors/prbs7_expected.txt
"""

import argparse
import sys

SEED = 0x7F
PERIOD = 127
MASK = 0x7F


def prbs7(n, seed=SEED):
    """Yield n bits of the PRBS-7 sequence, output taken before each shift."""
    state = seed
    for _ in range(n):
        out = (state >> 6) & 1
        fb = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | fb) & MASK
        yield out


def states(n, seed=SEED):
    """Yield the n successive register states, starting with the seed."""
    state = seed
    for _ in range(n):
        yield state
        fb = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | fb) & MASK

def _fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# Checker model
#
# A bit-accurate model of rtl/prbs7_check.sv, used to confirm that the
# thresholds and run lengths asserted by sim/tb_prbs7.sv actually hold before
# those numbers are baked into a testbench. It is a design aid, not a
# substitute for simulating the RTL.
# ---------------------------------------------------------------------------

HUNT, VERIFY, LOCKED = "HUNT", "VERIFY", "LOCKED"
LOAD_BITS = 7


class Prbs7Checker:
    """Mirrors the free-running checker FSM in rtl/prbs7_check.sv."""

    def __init__(self, lock_threshold=32, loss_threshold=8, decay_bits=64):
        self.lock_threshold = lock_threshold
        self.loss_threshold = loss_threshold
        self.decay_bits = decay_bits
        self.state = HUNT
        self.sr = 0
        self.load = 0
        self.good = 0
        self.bucket = 0
        self.decay = 0
        self.bits = 0
        self.errors = 0
        self.losses = 0

    @property
    def locked(self):
        return self.state == LOCKED

    def feed(self, rx):
        sr = self.sr
        predicted = ((sr >> 6) ^ (sr >> 5)) & 1
        shift_rx = ((sr << 1) | rx) & MASK
        shift_pred = ((sr << 1) | predicted) & MASK

        if self.state == HUNT:
            self.sr = shift_rx
            self.load += 1
            if self.load == LOAD_BITS:
                self.load = 0
                self.good = 0
                self.state = VERIFY

        elif self.state == VERIFY:
            if rx == predicted:
                self.sr = shift_pred
                self.good += 1
                if self.good == self.lock_threshold:
                    self.good = self.bucket = self.decay = 0
                    self.state = LOCKED
            else:
                self.sr = shift_rx
                self.load = 0
                self.good = 0
                self.state = HUNT

        else:  # LOCKED
            self.bits += 1
            if rx == predicted:
                self.sr = shift_pred
                self.decay += 1
                if self.decay == self.decay_bits:
                    self.decay = 0
                    self.bucket = 0
            else:
                self.errors += 1
                self.decay = 0
                self.bucket += 1
                if self.bucket == self.loss_threshold:
                    self.bucket = 0
                    self.losses += 1
                    self.load = 0
                    self.sr = shift_rx
                    self.state = HUNT
                else:
                    self.sr = shift_pred


def _stream(seed=SEED):
    """Endless PRBS-7 bit stream."""
    state = seed
    while True:
        yield (state >> 6) & 1
        fb = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | fb) & MASK


def checker_model_test():
    """Reproduce tb_prbs7.sv Part B and confirm the numbers it asserts."""
    errors = 0
    src = _stream()
    chk = Prbs7Checker()

    def run(n, invert=False, drop=False):
        """Feed n bits; drop=True discards the first one to force a slip."""
        for i in range(n):
            bit = next(src)
            if drop and i == 0:
                continue
            chk.feed(bit ^ (1 if invert else 0))

    # B1 - locks on a clean stream, then counts no errors.
    run(PERIOD + 32 + 64)
    if not chk.locked:
        errors += _fail("B1 did not lock on a clean stream")
    else:
        print("  ok  B1 locks within 127 + 32 + 64 bits of a clean stream")
    base = chk.errors
    run(4000)
    if chk.errors != base or chk.losses != 0:
        errors += _fail(f"B1 clean run counted {chk.errors - base} errors, {chk.losses} losses")
    else:
        print("  ok  B1 zero errors and zero lock losses over 4000 clean bits")

    # B2/B3 - an isolated error counts exactly one and does not cost lock.
    for label in ("B2", "B3"):
        base = chk.errors
        chk.feed(next(src) ^ 1)
        run(64 + 16)
        delta = chk.errors - base
        if delta != 1 or not chk.locked:
            errors += _fail(f"{label} isolated error counted {delta}, locked={chk.locked}")
        else:
            print(f"  ok  {label} one injected error counts exactly one, lock retained")

    # B4 - a continuously inverted stream must cost lock and never re-lock.
    losses_before = chk.losses
    run(2000, invert=True)
    if chk.locked or chk.losses == losses_before:
        errors += _fail(f"B4 inverted stream: locked={chk.locked}, losses={chk.losses}")
    else:
        print("  ok  B4 a continuously inverted stream costs lock within 2000 bits")
    run(4000, invert=True)
    if chk.locked:
        errors += _fail("B4 re-locked on an inverted stream")
    else:
        print("  ok  B4 never re-locks while the inversion is held")

    # B5 - clearing the inversion restores lock with no further errors.
    run(PERIOD + 32 + 64)
    if not chk.locked:
        errors += _fail("B5 did not re-lock after the inversion was removed")
    else:
        print("  ok  B5 re-locks once the inversion is removed")
    base = chk.errors
    run(4000)
    if chk.errors != base:
        errors += _fail(f"B5 counted {chk.errors - base} errors after re-lock")
    else:
        print("  ok  B5 no further errors after re-lock")

    # B6 - a dropped bit is a phase slip: lose lock, then re-lock.
    losses_before = chk.losses
    run(2000, drop=True)
    if chk.losses == losses_before:
        errors += _fail("B6 a dropped bit did not cost lock within 2000 bits")
    else:
        print("  ok  B6 a dropped bit costs lock within 2000 bits")
    run(4000)
    if not chk.locked:
        errors += _fail("B6 did not re-lock after the slip")
    else:
        print("  ok  B6 re-locks at the new phase after the slip")
    base = chk.errors
    run(4000)
    if chk.errors != base:
        errors += _fail(f"B6 counted {chk.errors - base} errors after re-locking")
    else:
        print("  ok  B6 no further errors once re-locked")

    # How quickly a slip actually trips the bucket, averaged over phases. This
    # is the number that sets the 2000-bit allowance in the testbench.
    worst = 0
    for phase in range(PERIOD):
        s = _stream()
        for _ in range(phase):
            next(s)
        c = Prbs7Checker()
        for _ in range(PERIOD + 32 + 64):
            c.feed(next(s))
        if not c.locked:
            continue
        before = c.losses
        next(s)                      # drop one bit
        n = 0
        while c.losses == before and n < 5000:
            c.feed(next(s))
            n += 1
        worst = max(worst, n)
    if worst >= 2000:
        errors += _fail(f"a slip took {worst} bits to unlock; the testbench allows 2000")
    else:
        print(f"  ok  worst-case slip unlocks in {worst} bits, over all 127 phases "
              f"(testbench allows 2000)")

    return errors



def self_test():
    """Check the properties that make this a maximal-length sequence."""
    errors = 0
    seq = list(prbs7(4 * PERIOD))

    # 1. Period is exactly 127 - not merely a divisor of it.
    period = next(
        (p for p in range(1, PERIOD + 1)
         if all(seq[i] == seq[i + p] for i in range(2 * PERIOD))),
        None,
    )
    if period != PERIOD:
        errors += _fail(f"period is {period}, expected {PERIOD}")
    else:
        print(f"  ok  period is exactly {PERIOD} symbols")

    # 2. Every nonzero register state is visited exactly once per period.
    visited = list(states(PERIOD))
    if len(set(visited)) != PERIOD:
        errors += _fail(f"{len(set(visited))} distinct states, expected {PERIOD}")
    elif 0 in visited:
        errors += _fail("the all-zeros state was reached - the LFSR is locked up")
    else:
        print(f"  ok  visits all {PERIOD} nonzero states, never all-zeros")

    # 3. Balance: 2^6 ones and 2^6 - 1 zeros in one period.
    ones = sum(seq[:PERIOD])
    if ones != 64:
        errors += _fail(f"{ones} ones per period, expected 64")
    else:
        print(f"  ok  balance is {ones} ones / {PERIOD - ones} zeros per period")

    # 4. Periodic autocorrelation is 127 at zero shift and -1 at every other
    #    shift. This is the property that makes a slipped checker fail to match
    #    at the wrong phase, and it is what the bit-slip test in the testbench
    #    relies on.
    bipolar = [1 - 2 * b for b in seq[:PERIOD]]
    for shift in range(PERIOD):
        corr = sum(bipolar[i] * bipolar[(i + shift) % PERIOD] for i in range(PERIOD))
        expected = PERIOD if shift == 0 else -1
        if corr != expected:
            errors += _fail(f"autocorrelation at shift {shift} is {corr}, expected {expected}")
            break
    else:
        print("  ok  autocorrelation is 127 at zero shift, -1 at every other shift")

    # 5. The complement of the sequence is not a phase of the sequence, so a
    #    continuously inverted stream must cost the checker its lock rather
    #    than quietly re-locking. The inversion test asserts this.
    inverted = [1 - b for b in seq[:PERIOD]]
    if any(inverted == seq[s:s + PERIOD] for s in range(PERIOD)):
        errors += _fail("the inverted sequence is a phase of the sequence")
    else:
        print("  ok  the inverted sequence is not a phase of the sequence")

    # 6. Seed appears at the top of the period, so the first output bit is the
    #    MSB of 0x7F, which is 1.
    if seq[0] != 1:
        errors += _fail(f"first output bit is {seq[0]}, expected 1 (MSB of the seed)")
    else:
        print("  ok  first output bit is 1, the MSB of the 0x7F seed")

    return errors


def write_vectors(path, count=PERIOD):
    with open(path, "w") as fh:
        for bit in prbs7(count):
            fh.write(f"{bit}\n")
    print(f"  wrote {count} bits to {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="check the maximal-length properties of the sequence")
    ap.add_argument("--checker-model", action="store_true",
                    help="model rtl/prbs7_check.sv and confirm the testbench thresholds")
    ap.add_argument("--write", metavar="PATH",
                    help="write one period of expected bits, one per line")
    ap.add_argument("--count", type=int, default=PERIOD,
                    help=f"bits to write (default {PERIOD}, one period)")
    ap.add_argument("--print", dest="show", type=int, metavar="N",
                    help="print the first N bits as a string")
    args = ap.parse_args()

    if not (args.self_test or args.checker_model or args.write or args.show):
        ap.print_help()
        return 2

    rc = 0
    if args.self_test:
        print("PRBS-7 golden model self-test")
        rc = self_test()
        print("PASS" if rc == 0 else f"{rc} check(s) FAILED")
    if args.checker_model:
        print("PRBS-7 checker model, mirroring sim/tb_prbs7.sv part B")
        rc2 = checker_model_test()
        print("PASS" if rc2 == 0 else f"{rc2} check(s) FAILED")
        rc += rc2
    if args.write:
        write_vectors(args.write, args.count)
    if args.show:
        print("".join(str(b) for b in prbs7(args.show)))
    return 1 if rc else 0


if __name__ == "__main__":
    sys.exit(main())
