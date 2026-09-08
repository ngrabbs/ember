#!/usr/bin/env python3
"""End-to-end sanity check for the EMBER payload bench.

Run this after any rewiring, reprogramming or power cycle, BEFORE writing new
code. Each check is independent and reports pass or fail, so a failure points
at one subsystem rather than leaving you to guess.

    python3 tools/sanity.py            # full check
    python3 tools/sanity.py --quick    # skip the timed loopback run
"""
import argparse, re, sys, time
from bench import console, setup_uart

FAILS = []


def check(ok, name, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        FAILS.append(name)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seconds", type=float, default=5.0)
    a = ap.parse_args()

    print("\nEMBER payload bench sanity check\n")
    setup_uart()

    # S1 - the console is alive. Everything else depends on this.
    banner = console("?")
    check(banner.startswith("EMBER"), "S1 UART console responds", banner or "(no reply)")
    if not banner:
        print("""
  Console dead. In likelihood order:

  1. The FPGA is not configured. JTAG configuration is VOLATILE - any power
     cycle of the Arty silently drops the bitstream and the board goes quiet
     with no other symptom.  Fix:  make program

  2. UART wiring. jb_uart_tx idles high, so JB pin 1 should measure ~3.3 V.
     Cable colours, from the cable's point of view:
        black -> JB pin 5 or 11 (GND)
        white -> JB pin 1   (cable RX, receives the FPGA's TX)
        green -> JB pin 2   (cable TX, drives the FPGA's RX)
        red   -> NOTHING. It is 5 V and the board is already powered.

  3. TX and RX swapped. If pin 1 measures 3.3 V and it is still silent, swap
     the white and green wires.
""")
        return 1

    # S2 - symbol engine and the JA1->JA4 loopback jumper.
    console("p3"); console("r3")                  # PRBS-7 at 1 Msym/s
    console("z")
    t0 = time.time()
    time.sleep(0.2 if a.quick else a.seconds)
    st = console("s")
    m = re.search(r"LOCK (\d) BITS ([0-9A-F]+) ERR ([0-9A-F]+) LOSS ([0-9A-F]+)", st)
    if not m:
        check(False, "S2 symbol engine status parses", st)
    else:
        lock, bits, err, loss = int(m[1]), int(m[2], 16), int(m[3], 16), int(m[4], 16)
        dt = time.time() - t0
        check(lock == 1, "S2a checker locked on the loopback",
              "pull the JA pin1->pin4 jumper and this should go to 0")
        # Zero errors over zero symbols is not a pass - the same false-pass
        # shape as a PRBS checker locking on an all-zero line.
        check(bits > 0 and err == 0, "S2b zero bit errors",
              f"{err} errors over {bits:,} symbols"
              + ("  <- nothing was checked" if bits == 0 else ""))
        check(loss == 0, "S2c zero lock losses", f"{loss}")
        if not a.quick and bits > 0:
            rate = bits / dt
            ok = abs(rate - 1e6) / 1e6 < 0.10
            check(ok, "S2d symbol rate is 1 Msym/s", f"measured {rate:,.0f} sym/s")

    # S3 - the DDS sequencer runs to completion, whatever the board does.
    console("i"); time.sleep(2.0)
    k = console("k")
    m = re.search(r"LOCK (\d) DONE (\d) TMO (\d) REF (\d) FTW ([0-9A-F]+)", k)
    if not m:
        check(False, "S3 DDS status parses", k)
    else:
        dlock, ddone, dtmo, dref, ftw = (int(m[1]), int(m[2]), int(m[3]),
                                         int(m[4]), m[5])
        check(ddone == 1, "S3a DDS sequencer completed", k)
        # The FPGA must not drive the reference net while the DDS runs from its
        # own oscillator - ck_io0 lands on the same node W1 feeds, and two
        # push-pull drivers there is what kept SYNC_CLK dead.
        check(dref == 0, "S3b reference generator released (ck_io0 high-Z)",
              "REF=1 drives ck_io0; safe only with W1 at 1&2 and the "
              "oscillator disconnected")
        check(dlock == 1, "S3c AD9910 PLL locked", k)
        if dtmo:
            print("         (TMO=1 means the sequencer gave up waiting for lock)")

    print()
    if FAILS:
        print(f"  {len(FAILS)} check(s) failed: {', '.join(FAILS)}\n")
        return 1
    print("  all checks passed\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
