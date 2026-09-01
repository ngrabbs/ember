# LO Drive Verification — TinySA Procedure

Bench procedure for measuring the Si5351A CLK1 output power at 145.9 MHz
into a 50 Ω load using the TinySA spectrum analyzer. The output of this
test feeds the go / no-go decision on R4 (the 33 Ω series resistor in
the CLK1 path on the comms board) and confirms the LO LPF design for
the ADE-1+ passive mixer.

See companion docs:
- [`si5351a_breakout_bench_test.md`](si5351a_breakout_bench_test.md) — Pico 2 + Adafruit 5640 setup code, breakout-vs-PCB circuit equivalence
- [`../design/rx_mixer_trade_study.md`](../design/rx_mixer_trade_study.md) — design rationale (why this measurement matters)
- [`../design/altium_comms_schematic.md`](../design/altium_comms_schematic.md) — Sheet 2 CLK1 design, Sheet 4 Section B.2 (LO LPF)
- `/workspace/MSU_Cubesat/100_day_challenge/docs/tool_inventory.md` — gear list and pad characterization data

---

## Goal of the measurement

Answer two specific questions:

1. **What power does CLK1 actually deliver into 50 Ω at 145.9 MHz?**
   Need ≥ +5 dBm to drive the ADE-1+ properly. Predicted ~+8 dBm with
   R4 = 33 Ω, ~+12 dBm with R4 = 0 Ω.

2. **How dirty is the spectrum?**
   The square-wave 3rd harmonic at 437.7 MHz lands on top of the TX
   band. Need to know how strong it is to confirm the 5-pole LO LPF
   (designed for 34 dB rejection at 437 MHz) is enough.

---

## The signal hazard

TinySA input absolute max is **+6 dBm** (Original) or **+10 dBm** (Ultra).
The Si5351A could be putting out +8 to +12 dBm at the fundamental, plus a
fat 3rd harmonic. **Always go through an attenuator pad.** Connecting
CLK1 directly to the TinySA can blow the front end.

Use a **20 dB Nooelec pad** in front of the TinySA. From the pad
characterization log, that pad is -19.53 dB at 144 MHz — so a +8 dBm
source becomes ~-11.5 dBm at the TinySA input. That's right in the
sweet spot for accurate measurement (TinySA is most accurate from
-50 to -10 dBm).

---

## Hardware setup

```
[Si5351A board]     [BECEN]       [Nooelec 20 dB]     [TinySA]
  CLK1 pin     ──→  DC block ──→     pad           ──→  RF in
   (SMA out)                                            (50Ω)
```

Gear from inventory:
- **TinySA** — primary instrument
- **BECEN SMA DC block** — between source and pad (Si5351A output has
  DC offset around VDDO/2; DC block keeps that off the TinySA)
- **Nooelec 20 dB pad** — characterized at -19.53 dB @ 144 MHz,
  -19.53 dB @ 434 MHz — trusted
- **2× SMA male-male jumpers** — your inspection-only pile is fine for
  this; we don't need cal-grade for a -10 dBm absolute power
  measurement. Sanity-check by reading the same power before and after
  wiggling the connections.
- **NanoVNA** — kept on hand for one optional sanity check (see below)

**Important:** if your breadboard doesn't have an SMA output from the
Si5351A CLK1 pin, add one (UFL pigtail or SMA pigtail soldered with
the shortest possible leads). The measurement is meaningless if you're
capacitively coupling a long alligator-clip lead to the TinySA — at
145 MHz that lead is a fraction of a wavelength and will detune
everything.

---

## Procedure

### Step 1 — Si5351A side preparation

Program CLK1 for 145.9 MHz at **8 mA drive strength** (highest setting).
See [`si5351a_breakout_bench_test.md`](si5351a_breakout_bench_test.md)
for the CircuitPython code.

Sanity-check on the **Rigol DS1202Z-E** first: hook the same SMA
pigtail to the scope with a 50 Ω feedthrough or termination, and look
for a roughly square wave at ~6.85 ns period. **Don't believe the
amplitude the scope reports** — 200 MHz BW means -1 to -2 dB rolloff
right at our frequency. Use the scope only to confirm "signal exists,
at the right frequency, looks clean."

### Step 2 — Hook up the chain

1. SMA jumper from Si5351A pigtail → DC block
2. DC block → 20 dB pad
3. 20 dB pad → SMA jumper → TinySA RF input
4. Tighten all SMA connections finger-tight + 1/8 turn with a small
   wrench (over-torquing damages the threads; finger-only often leaks
   RF and gives unstable readings)

### Step 3 — TinySA setup

- **Mode:** Spectrum Analyzer
- **Span:** 100 MHz to 800 MHz (covers fundamental + 3rd + 5th harmonics)
- **Reference level:** 0 dBm
- **Internal attenuator:** 0 dB (already externally attenuated)
- **Internal LNA:** OFF (plenty of signal)
- **RBW:** 10 kHz or 30 kHz (lets you see each harmonic clearly)
- **Sweep:** continuous

### Step 4 — Read the fundamental

Put a marker on the peak near 145.9 MHz. Read the displayed power.

**Add back the external attenuation:**

```
Actual CLK1 power = (TinySA marker reading) + 19.53 dB pad + ~0.1 dB cable loss
```

Example: TinySA shows -12 dBm at 145.9 MHz → CLK1 is delivering
-12 + 19.5 + 0.1 = **+7.6 dBm** into 50 Ω. ✓ Within spec for ADE-1+.

### Step 5 — Read the harmonics

Markers on:
- **3rd harmonic** at 437.7 MHz — note the level relative to fundamental
- **5th harmonic** at 729.5 MHz — same

For an ideal square wave, theory says:
- 3rd: -9.5 dB below fundamental
- 5th: -14 dB below fundamental

In practice with the Si5351A you'll see 3rd at -10 to -15 dB and 5th
at -15 to -25 dB.

**What this tells you:** the LO LPF needs to suppress the 3rd by
≥ 30 dB to put it below the noise floor downstream. The 5-pole
Butterworth gives 34 dB at 437 MHz. So after the LPF the 3rd should be
30 + 34 = ~64 dB below fundamental — comfortably gone.

### Step 6 — Re-run with R4 = 0 Ω

If you're testing the Adafruit breakout, the breakout has no series R
to begin with, so the direct reading IS your R4 = 0 Ω datapoint. To
simulate R4 = 33 Ω, see the methods documented in
[`si5351a_breakout_bench_test.md`](si5351a_breakout_bench_test.md)
(solder a 33 Ω in series, or use the Nooelec 3 dB pad as a rough
approximation).

If you're testing the assembled comms PCB, short out R4 (solder a wire
across it or replace with 0 Ω) and re-measure. Should be ~3 dB higher.

---

## What "good" and "bad" look like

| Result | Verdict |
|---|---|
| Fundamental +5 to +10 dBm, harmonics 10+ dB down | ✓ Use R4 = 33 Ω, design is good |
| Fundamental +8 to +12 dBm, harmonics 10+ dB down | ✓ R4 = 0 Ω, even better |
| Fundamental < +3 dBm | ✗ Drive too low — check Si5351A programming, check load, consider adding an LO amp |
| 3rd harmonic only -5 dB below fundamental | ✗ Output is clipping/distorting downstream — check pad isn't bad or that load isn't reactive |
| Reading shifts by > 2 dB when you wiggle cables | ✗ Bad SMA connection — re-seat |
| Multiple unexpected spurs near fundamental | ✗ Programming error or PLL fractional-divider birdies — recheck register settings |
| Reading drifts over 30 seconds | Probably thermal — let everything warm up 5 min, re-read |

---

## Pitfalls — the things that ruin this measurement

1. **Breadboard parasitics.** Tool inventory notes that *"at 437 MHz a
   breadboard layout will radiate unpredictably and present poor
   return loss."* At 145 MHz it's better, but still real. Expect the
   measurement to be ±2-3 dB from what the final PCB will deliver. The
   measurement is a sanity check, not a final number.

2. **Skipping the DC block.** The Si5351A output isn't a pure AC
   source — it has a DC component around VDDO/2 (~1.65 V). Some
   attenuators and especially the TinySA front end don't love DC.
   Always include the BECEN DC block.

3. **Untrusted cable losses.** Tool inventory says SMA jumpers are
   "calibration-grade unknown." At 145 MHz, a bad jumper might add
   0.5 dB extra loss — acceptable for this rough measurement, but if
   you want to be careful, run a quick NanoVNA S21 sweep through the
   cable + pad chain first (1 MHz to 1 GHz) and use the actual loss
   number.

4. **Reading the TinySA's number directly as "CLK1 power."** Most
   common mistake. The TinySA shows power *at its input port*. You
   have to mentally add back the 20 dB pad and any cable loss to get
   the source power.

5. **Internal attenuator on.** TinySA has a switchable internal
   attenuator. If it's on (default in some firmware), you've added
   another 20-30 dB and the readings will be way off. Verify it's at
   0 dB.

6. **LNA on with a strong signal.** Same thing in reverse — the
   internal LNA will saturate and give meaningless readings.

7. **Loading the breadboard with the scope before the TinySA run.** If
   you tee'd off with the scope probe still attached during the TinySA
   measurement, the probe's input capacitance (~10 pF) at 145 MHz is
   ~110 Ω — a non-trivial shunt across a 50 Ω source. **Remove the
   scope probe before reading the TinySA.**

8. **Letting EM interference fool you.** Si5351A output is unshielded
   on a breadboard, and the bench has WiFi, cell phones, etc. If you
   see a peak that *isn't* at a harmonic of 145.9 MHz, it might be
   ambient. Quick test: pull the SMA cable off the TinySA input
   briefly — anything that stays is ambient pickup, anything that
   disappears is from the DUT.

---

## Sanity check before committing the result

Once you have a number you trust:

- The Si5351A AN619 app note says 8 mA drive into 50 Ω gives ~+8 dBm
  typical at VHF. If you measured +8 ± 2 dBm, that's congruent with
  the datasheet and your design margins are real.
- If you measured +3 dBm or lower, something is wrong with the setup
  or the breadboard impedance is far from 50 Ω. Don't accept that
  number — recheck the chain.

---

## Recording results

Log each measurement run with:

- Date / time
- DUT (breakout vs PCB rev)
- Drive strength setting
- Series R config (0 Ω or 33 Ω)
- TinySA marker reading at 145.9 MHz, 437.7 MHz, 729.5 MHz
- External attenuation (pad value + cable loss)
- Computed source power (fundamental, 3rd harmonic, 5th harmonic)
- Notes on anything unusual (drift, spurs, instability)

Append rows to [`si5351a_bringup_log.md`](si5351a_bringup_log.md) so
the data lives alongside the rest of the Si5351A bring-up history.
