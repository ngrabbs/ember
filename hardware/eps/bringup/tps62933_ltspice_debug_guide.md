# TPS62933F Feedback Network & LTSpice Debug Guide

## Purpose

Rev A boards are back, the LTC4162 charger looks healthy, but the two
TPS62933F buck regulators are not producing their output rails. This
guide does three jobs:

1. Explains what the feedback network actually does — pin by pin —
   so you know what every voltage on the chip *should* be.
2. Provides an LTSpice **behavioral model** of the regulator (since TI
   does not publish a native LTSpice model) so you can predict the
   waveforms you should see at FB, SW, SS, and VOUT.
3. Gives a fault tree mapping bench symptoms → root cause.

The deliberate end state: you should be able to put scope probes on
five pins, compare to the LTSpice prediction, and identify the failing
mechanism in <30 minutes.

> **Read Section 2 (Vref Verification) first.** It catches the single
> most common silent failure on this design.

---

## Section 1 — 5-Minute Bench Sanity Check

Before any LTSpice work, run these four checks with a DMM. If any of
them fails, fix it before going further — they're cheap and catch the
gross errors.

| # | Check | Expected | If wrong |
|---|-------|----------|----------|
| 1 | `JP_RBF` jumper installed? | Removed | Pull it. Installing `JP_RBF` shorts R21 → forces `BUCK_EN` to GND → kills both bucks (Sheet 4 Section A). |
| 2 | DMM at U2/U3 pin 3 (VIN) to GND | Equal to `VOUT_PP`, > 3.8 V | If 0 V: trace open between LTC4162 VOUT and the buck VINs. If <3.8 V: charger isn't sourcing enough; check LTC4162 telemetry. |
| 3 | DMM at U2/U3 pin 2 (EN) to GND | ≥ 1.21 V (at `VOUT_PP` ≥ 5.6 V) | If lower: UVLO divider math is off, OR `VOUT_PP` is below the UVLO threshold. See Section 3. |
| 4 | DMM at U2/U3 pin 7 (SS) to GND | Slowly ramping 0 → ~0.6/0.8 V over ~5 ms, then steady at Vref | If stuck at 0 V: chip is disabled (EN low) OR internal short. If stuck at ~0.8 V immediately: SS cap (C33/C43) is missing or shorted. |

If all four pass and you still have no rail, jump to Section 2.

---

## Section 2 — CRITICAL: Verify Vref Against Your Datasheet

The schematic guide (`hardware/eps/design/altium_eps_schematic_guide.md`)
documents Vref as 0.8 V and sized the dividers for that. The TI
TPS62933 datasheet family (SLUSEA4 / SLUSEA4D) has historically listed
Vref = 0.6 V for the standard part. **The TPS62933F variant we used
may differ — open your downloaded copy of the datasheet, find the
"Electrical Characteristics" table, and read off `Internal voltage
reference` (or `VFB` regulation voltage).** Write that number here:

```
Vref (from datasheet, page ___): _________ V
```

This single number determines what your rails will regulate to. With
the BOM resistor values (R9=31.6 kΩ / R10=10 kΩ on the 3 V3 rail,
R13=52.3 kΩ / R14=10 kΩ on the 5 V rail), the three plausible cases
are:

| Vref (V) | 3 V3 rail Vout | 5 V rail Vout | Implication |
|----------|----------------|---------------|-------------|
| 0.6      | 0.6 × (1 + 31.6/10) = **2.50 V** | 0.6 × (1 + 52.3/10) = **3.74 V** | Dividers are wrong; rails will sit low. |
| 0.7      | 0.7 × 4.16 = **2.91 V** | 0.7 × 6.23 = **4.36 V** | Dividers are wrong; rails sit low. |
| 0.8      | 0.8 × 4.16 = **3.33 V** | 0.8 × 6.23 = **4.98 V** | Dividers correct (the schematic-guide assumption). |

**Decisive test:** force `VOUT_PP = 12 V` from a bench supply,
remove all stack-side load, and measure both rails. If the "3 V3" rail
sits at 2.5 V (not 0 V), Vref is 0.6 V and the divider is wrong, not
broken. The fix is then a resistor swap, not a layout debug.

If the rails sit at exactly 0 V even with the FB pin floating at the
right voltage during startup, that points elsewhere — see Section 6.

> **Why this matters more than usual:** "rails low but present" looks
> different on the bench than "rails dead." A 2.5 V "3 V3" rail will
> brown-out the RP2040, so downstream may *appear* dead while the
> regulator itself is happy. Always measure the rail directly at the
> regulator output cap before declaring it dead.

### Resistor swap table (if Vref = 0.6 V)

For E96 1% values, R_FBB = 10 kΩ:

| Target Vout | R_FBT formula                | R_FBT exact | E96 nearest |
|-------------|------------------------------|-------------|-------------|
| 3.30 V      | ((3.3 − 0.6) / 0.6) × 10 kΩ  | 45.0 kΩ     | **45.3 kΩ** (gives 3.318 V) |
| 5.00 V      | ((5.0 − 0.6) / 0.6) × 10 kΩ  | 73.3 kΩ     | **73.2 kΩ** (gives 4.992 V) |

These would replace R9 and R13 respectively.

---

## Section 3 — How the Feedback Loop Works (Theory)

A buck converter regulates by adjusting the duty cycle of the SW node
to make the FB pin equal Vref. Knowing what each pin does lets you
read a 5-pin scope trace as a story.

### The Pins

```
          ┌──────────────────────────────────────────────┐
          │                  TPS62933F                   │
          │                                              │
   VIN ──>│ pin 3 ────────────► [HS FET] ────► SW pin 5 ──┼──> L ──┬── VOUT
          │                        ▲                     │        │
          │                        │ Gate drive          │       Cout
          │                        │                     │        │
   EN ───>│ pin 2 ─► [UVLO] ─► EN_OK                     │       GND
          │                        ▲                     │
          │                        │                     │
          │   [Internal Vref] ─►[Error Amp]─►[PWM Comp]─►│
          │                        ▲                     │
          │                        │                     │
   SS  ──>│ pin 7 ◄── [Iss=5.5µA charges Css externally] │
          │                        │                     │
          │   FB pin 8 ◄───────────┘                     │
          │                                              │
   BST ──>│ pin 6 ◄── 100nF to SW (gate-drive bootstrap) │
          │                                              │
   RT ───>│ pin 1 (float = 500 kHz)                      │
          └──────────────────────────────────────────────┘
                            │
                            ▼ R_FBT (top)
                          FB ◄────┐
                            ▼     │
                          R_FBB   │ Sense node = Vout × R_FBB / (R_FBT + R_FBB)
                            ▼     │
                          GND ────┘
```

### The Control Law

In steady state, the loop drives:

```
V_FB = Vref
```

The divider sets:

```
V_FB = Vout × R_FBB / (R_FBT + R_FBB)
```

Solving for Vout:

```
Vout = Vref × (1 + R_FBT / R_FBB)
```

That's the entire DC equation. Everything else (compensation, slope
comp, soft-start) is dynamics around this set point.

### What FB Voltage Tells You

Put a DMM on FB. Three cases:

| FB reads | Meaning |
|----------|---------|
| ≈ Vref (e.g., 0.6 V or 0.8 V) | Loop is regulating. If Vout is wrong, your divider math is wrong (Section 2). |
| 0 V | Vout = 0 V. Either the chip isn't switching, or Vout is shorted to GND. |
| > Vref but < Vout/(divide ratio) | Loop is trying but losing — likely a saturation issue (inductor saturating, current limit, or VIN too low to support Vout). |
| Equals Vout × ratio with Vout below target | Loop is operating in dropout — Vin too close to Vout, can't deliver enough duty. Not your case at Vin = 12 V. |

### Soft-Start Behavior

`SS` (pin 7, with C33/C43 = 33 nF to GND) ramps as the chip starts:

```
t_SS = (Css × Vref) / Iss = (33 nF × 0.8 V) / 5.5 µA ≈ 4.8 ms   (Vref=0.8)
t_SS ≈ 3.6 ms   (Vref=0.6)
```

While SS < Vref, the *internal reference* the error amp compares
against is SS, not Vref. So Vout ramps linearly with SS until it hits
its target, then holds. On a scope, you should see SS ramp from 0 V
up to Vref, with VOUT tracking it (scaled by the divider ratio).

If SS never moves: the chip is disabled (EN logic low).
If SS jumps to Vref instantly: SS cap is missing or shorted.
If SS ramps but VOUT stays 0: SW node isn't switching — check BST cap,
inductor, or HS FET.

---

## Section 4 — LTSpice Behavioral Model

This is an averaged model: it captures regulation behavior, soft-start,
EN UVLO, and DC operating point, but does **not** simulate the
500 kHz switching node. That's deliberate — averaged models converge
faster, are easier to read, and answer "is my divider right?" cleanly.

For SW-node ringing or EMI questions, build the switched version in
Section 5.

### What This Model Captures

- DC output voltage as a function of FB divider, Vin, and Vref
- EN UVLO threshold (1.21 V rising) — chip refuses to start below it
- Soft-start ramp via external SS cap and 5.5 µA current source
- Output L–C filter response (settling, no ripple)
- Loop compensation (single-pole, conservative — won't oscillate)
- Duty-cycle clamp (0–95%, models max-duty limit)

### What It Does NOT Capture

- Switching ripple (no SW pulses — output is the averaged value)
- Slope compensation, sub-harmonic instability
- Current-mode behavior under load steps
- Diode/FET losses, BST cap behavior
- Real-world layout parasitics

### Build It in LTSpice

**Option A: paste the netlist.** Save the block below as
`tps62933_avg.cir`, open LTSpice, `File > Open` (set file type to
"Netlist (*.cir)"), then `Simulate > Run`.

```spice
* TPS62933F averaged behavioral model — 3.3 V rail
* Verify Vref against your datasheet — change .param Vref below.

.param Vref   = 0.8     ; <-- VERIFY: 0.6 V or 0.8 V from datasheet
.param Iss    = 5.5u    ; SS pin source current (datasheet)
.param Css    = 33n     ; external SS cap (C33)
.param L      = 4.7u    ; 3.3 V rail inductor (L20)
.param Cout   = 44u     ; 2× 22 µF effective (after derating, ~30 µF)
.param Rload  = 1.1     ; 3 A at 3.3 V → 1.1 Ω
.param Vinval = 12      ; VOUT_PP from charger
.param R_FBT  = 31.6k   ; R23
.param R_FBB  = 10k     ; R24

* --- Sources ---
V_VIN  VIN 0 PULSE(0 {Vinval} 1m 100u 100u 100 100)   ; ramps in at 1ms
V_EN   EN  0 PULSE(0 {Vinval} 2m 100u 100u 100 100)   ; enable at 2ms

* --- EN UVLO (1.21V rising) ---
B_EN_OK  EN_OK 0 V = IF(V(EN) > 1.21, 1, 0)

* --- Soft-Start integrator on SS pin ---
G_SS 0 SS VALUE = { IF(V(EN_OK) > 0.5, Iss, 0) }
C_SS SS 0 {Css}
R_SS_DRAIN SS 0 1G   ; bleed when EN low (sim convergence)

* --- Internal reference: ramps with SS until SS exceeds Vref ---
B_VREF VREF_INT 0 V = IF(V(SS) < Vref, V(SS), Vref)

* --- Error amplifier: transconductance + compensation cap ---
G_EA 0 COMP VALUE = { 1e-4 * (V(VREF_INT) - V(FB)) }
C_COMP COMP 0 100p
R_COMP COMP 0 10Meg

* --- Duty cycle from compensation node, clamped 0..0.95 ---
B_DUTY DUTY 0 V = LIMIT(V(COMP) * 1, 0, 0.95)

* --- Averaged switch node: V(SW) = Vin × duty when enabled ---
B_SW SW 0 V = IF(V(EN_OK) > 0.5, V(VIN) * V(DUTY), 0)

* --- Output filter L + Cout + load ---
L1     SW   VOUT {L}
C_OUT  VOUT 0    {Cout}
R_LOAD VOUT 0    {Rload}

* --- Feedback divider ---
R_FBT_R VOUT FB {R_FBT}
R_FBB_R FB   0  {R_FBB}

.tran 0 20m 0 1u
.backanno
.end
```

**Option B: build it graphically.** Use these LTSpice components:

| Symbol            | Where to find        | Settings                        |
|-------------------|----------------------|---------------------------------|
| Voltage source    | `voltage`            | PULSE(0 12 1m 100u 100u 100 100) for VIN, similar for EN |
| Behavioral source | `bv` (B-source)      | Use `V = IF(...)` expressions   |
| Behavioral G      | `bi` (B-source I)    | For G_SS                        |
| Capacitor         | `cap`                | 33 n (SS), 100 p (COMP), 44 u (Cout) |
| Resistor          | `res`                | Per netlist                     |
| Inductor          | `ind`                | 4.7 u                           |

Tip: in graphical mode, every behavioral source needs a unique label
on its output net (`SS`, `EN_OK`, `VREF_INT`, `COMP`, `DUTY`, `SW`).
Use the **net label tool** (F4) to name nets — that's how the B-source
expressions reference each other.

### What to Watch in the Simulation

After running `.tran 0 20m 0 1u`, plot these traces in order:

1. **`V(EN)`** — should step from 0 to 12 V at t=2 ms.
2. **`V(EN_OK)`** — steps from 0 → 1 right after EN crosses 1.21 V.
3. **`V(SS)`** — ramps linearly from 0 to Vref over ~5 ms, then flattens.
4. **`V(VREF_INT)`** — tracks SS up, then clamps at Vref.
5. **`V(VOUT)`** — ramps with VREF_INT (scaled by divider) until it
   reaches the target. Final value should be `Vref × (1 + 31.6/10)`.
6. **`V(FB)`** — should track VREF_INT exactly in steady state.
   *This is the single trace that confirms loop closure.*

### Quick Experiments You Can Run

Each of these takes 30 s and teaches one thing about the regulator:

1. **Change `.param Vref = 0.6`, re-run.** Vout drops to ~2.5 V. This
   is exactly what a Vref-mismatch fault on the bench looks like.
2. **Change `.param R_FBT = 45.3k`** with Vref=0.6. Vout returns to
   3.3 V. This is the resistor-swap fix from Section 2.
3. **Change `.param Vinval = 4`.** EN UVLO threshold at 1.21 V means
   the divider midpoint at 4 V is `4 × 61.9/(226+61.9) = 0.86 V` —
   below 1.21 V — so EN_OK stays low and Vout stays at 0. This shows
   the UVLO behavior.
4. **Change `.param Rload = 100`** (light load). Vout settles faster
   and overshoots less. Reproduces the "rail looks fine no-load but
   collapses under load" failure mode if you also lower Cout.
5. **Set `.param Cout = 1u`** (broken / missing output cap). Watch
   the loop go unstable — the error amp can't keep up without enough
   capacitance to integrate the duty changes.

---

## Section 5 — LTSpice Switched Model (Optional, for Ripple/EMI)

For switching-node debug (visible ringing on SW, ground bounce, ripple
on Vout), you need a model with actual PWM. This is more work — only
go here if Section 4 looks fine but you have a ripple/EMI problem.

### Approach

Replace the `B_SW` averaged source with:

```spice
* PWM oscillator at 500 kHz
V_OSC OSC 0 PULSE(0 1 0 1n 1n {1/(500k*0.5)} {1/500k})

* Comparator: SW gate = high when COMP > OSC ramp
B_GATE GATE 0 V = IF(V(COMP) > V(OSC), 1, 0)

* High-side switch model (ideal)
S1 VIN SW GATE 0 SW_MODEL
.model SW_MODEL SW(Ron=50m Roff=1Meg Vt=0.5 Vh=0.1)

* Low-side switch (synchronous rectifier — turns on when GATE low)
S2 SW 0 0 GATE SW_MODEL
```

This will show ~1–2 % ripple on Vout at 500 kHz. Useful for verifying
your output-cap derating assumption.

A simpler alternative: download the **TI TINA-TI** simulator (free,
Windows). TI publishes a working TPS62933 PSpice/TINA model at
`https://www.ti.com/product/TPS62933#design-development` (Tools section).
TINA uses a PSpice-compatible netlist, so you get TI's vetted model
with no behavioral approximation. Recommend this if you want
production-grade simulation; LTSpice is better for quick feedback-loop
intuition.

---

## Section 6 — Bench Measurement Plan

Once you have the LTSpice prediction, here's exactly what to put on
each pin to identify the failure. Set the bench supply to
`VOUT_PP = 12 V`, no stack load.

| Pin | Tool | Expected (steady state) | What it tells you |
|---|---|---|---|
| VIN (3) | DMM | 12 V                       | Power getting to the chip |
| EN  (2) | DMM | 12 × 61.9/(226+61.9) = **2.58 V** | UVLO above threshold |
| SS  (7) | Scope, slow | Ramp 0 → Vref over ~5 ms, then flat | Soft-start works |
| BST (6) | Scope, AC-coupled | ~5 V square wave at 500 kHz (referenced to SW) | HS gate drive working |
| SW  (5) | Scope | 500 kHz square, swings 0 ↔ ~Vin | Switching is happening |
| FB  (8) | DMM | Vref (0.6 or 0.8 V — your datasheet) | Loop closed |
| VOUT    | DMM | Vref × (1 + R_FBT/R_FBB)         | Final answer |

If `SW` is *not* a square wave but flat at 0 V or flat at VIN, the
PWM controller isn't running. Cause is upstream — EN, SS, or internal
fault. Check FB voltage:

- If FB ≈ 0 V and SW flat at VIN → loop wants to push Vout up but
  can't. Inductor open? HS FET dead? SW shorted to GND?
- If FB ≈ Vref but SW flat at 0 V → loop thinks Vout is fine. Check
  whether FB is being held by leakage or a wrong divider — disconnect
  the load and recheck.
- If FB > Vref → loop wants Vout down. The chip *will* refuse to
  switch in this state. This happens if Vout is being back-fed from
  somewhere else (another rail, the LTC4162 path, leftover charge),
  or if the divider math is wrong in a way that Vout reaches FB =
  Vref before the chip even ran (impossible at startup, but possible
  if the test setup has a parallel power source).

---

## Section 7 — Fault Tree for "No Output"

Read top to bottom; the first answer that fits is the most likely
cause.

```
START: VOUT = 0 V on the bench
  │
  ├─ Is JP_RBF installed?  ──► Yes ──► REMOVE IT. Done.
  │     │
  │     No
  │     ▼
  ├─ V(EN) ≥ 1.21 V?  ──► No ──► Check VOUT_PP and the EN UVLO divider.
  │                              At VOUT_PP=12V, EN should be 2.58 V.
  │                              If divider math is wrong, swap R8/R11
  │                              (or R12/R15) per datasheet §9.3.6.
  │     │
  │     Yes
  │     ▼
  ├─ V(SS) ramping?  ──► No ──► Either EN_OK is internally low (chip
  │                             damaged) or C33/C43 is open/shorted.
  │                             Replace SS cap, retest.
  │     │
  │     Yes, ramps then flattens
  │     ▼
  ├─ SW node switching at 500 kHz on scope?
  │     │
  │     No (flat at 0 V or VIN)
  │     │
  │     ├─ V(FB) > Vref? ──► Yes ──► Loop is in 0% duty. Vout being
  │     │                            back-fed. Disconnect external
  │     │                            sources. If still high, divider
  │     │                            wrong (Section 2).
  │     │
  │     ├─ V(FB) = 0 V? ──► HS FET or BST cap fault. Check C32/C42
  │     │                   (100 nF between BST and SW). Check inductor
  │     │                   continuity.
  │     │
  │     Yes, switching
  │     ▼
  ├─ V(VOUT) reaches some value but it's wrong?
  │     │
  │     ├─ VOUT ≈ 2.5 V on "3 V3" rail? ──► Vref is 0.6 V, divider
  │     │                                   sized for 0.8 V. Section 2
  │     │                                   resistor swap.
  │     │
  │     ├─ VOUT oscillates / unstable? ──► Output cap missing or
  │     │                                   wrong value (DC bias on
  │     │                                   X7R 22 µF at 25 V is
  │     │                                   non-trivial — measure the
  │     │                                   actual capacitance).
  │     │
  │     ├─ VOUT collapses under load? ──► Inductor saturating
  │     │                                  (check L20/L21 part — must
  │     │                                  be ≥ 5 A Isat) OR input
  │     │                                  rail collapsing under
  │     │                                  current draw (Iin from
  │     │                                  bench supply telling you
  │     │                                  this directly).
  │     │
  │     └─ VOUT ≈ correct value, just no current to load ──► Trace
  │                                                          break or
  │                                                          stack
  │                                                          connector
  │                                                          fault.
  ▼
END
```

---

## What to Bring Back to the Team

After running through this guide, the EPS team should have:

1. A confirmed Vref value from the datasheet, written in Section 2.
2. A bench-measured value at every pin in Section 6, alongside the
   LTSpice predictions, so divergence is obvious.
3. A clear answer to: "is this a divider sizing issue, a chip-level
   issue, or a load-side issue?"

If the answer is "divider sizing," the fix is two resistor swaps. If
it's "chip-level" (no SW switching with EN good), reflow or replace
U2/U3 first, then revisit. If it's "load-side," that's a different
investigation — the regulator is fine, the bus isn't.

---

## Related Documents

- Schematic source-of-truth: `hardware/eps/design/altium_eps_schematic_guide.md`
  (Sheet 2 covers the regulator stages)
- BOM: `hardware/eps/releases/CubeSat_EPS_rev_A_BOM.csv`
  (TPS62933FDRLR = LCSC C5219272; FB resistors are R9/R10/R13/R14)
- Bring-up checklist: `hardware/eps/bringup/phase1_validation.md`
- TI datasheet (download required, not in repo):
  `https://www.ti.com/product/TPS62933F` → "Datasheet"
- TI TINA-TI free SPICE simulator (alternative to LTSpice with
  TI-vetted model): `https://www.ti.com/tool/TINA-TI`
