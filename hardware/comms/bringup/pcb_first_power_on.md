# Comms PCB — First Power-On / Fault-Finding Log

**Board:** cubesat_communications Rev A (first fab, JLC)
**Date:** 2026-08-15
**Status:** ❌ Rev A non-functional — fatal schematic wiring error found. Rev B required.

---

## TL;DR

The board would not power up: the entire **+5V rail was shorted to GND**
(0.69 Ω, polarity-independent) on both populated boards, and applying +5V
smoked the tripler.

**Root cause:** a **schematic wiring error** — the +5V RFC feed (L1) is
routed to the **base** of tripler transistor Q1 (BFR92A) instead of its
**collector**. This dumps +5V through the choke straight into the
base-emitter junction (a forward diode with no current limit), forcing
runaway current and cooking the part.

- **Root cause:** Q1 `L1 → base` wiring error → **rev-B one-line fix**
  (rewire L1 to the collector, ECO, re-route). See
  [`../design/altium_comms_schematic.md`](../design/altium_comms_schematic.md)
  Section B (Frequency Tripler).
- **Casualty (to confirm):** U2 (ADL5602) most likely shorted by the fault
  event → **replace on the two physical boards**.
- **Validation:** LTspice model
  [`../design/ltspice_simulations/tripler.asc`](../design/ltspice_simulations/tripler.asc)
  reproduces both the failure and the fix; FFT of the corrected circuit
  shows the intended 437 MHz tripled output.

---

## Symptoms

- **Bare (unpopulated) board:** all +5V vias isolated from GND. Copper is
  clean — the PCB fab / pour spacing is fine.
- **Both populated boards:** +5V ↔ GND reads **0.69 Ω, the same in both
  probe polarities**.
- Applying +5V **smoked the tripler**.

The polarity-independent 0.69 Ω is the key clue: a *bolted* short (failed-short
part or bridge), **not** a healthy semiconductor junction (which would read
polarity-dependent / diode-like).

## What made this hard to troubleshoot

**+5V is a single continuous net.** Every "+5V node" on the board — U2 bias,
tripler supply, PSA4 LNA choke, Pico VSYS — is the *same copper*. A single
short anywhere pins the **entire rail**, so every +5V test point reads 0.69 Ω
to ground. Probing from node to node all read "shorted," which looked like
many faults but is one net with one short.

**Lesson banked:** you cannot localize a rail short by hopping between nodes
on that rail — they are electrically identical. You localize by *cutting* the
net into pieces (lift a choke, pull a part) and re-measuring.

## Fault isolation sequence

1. **Polarity-swap test** on +5V→GND: 0.69 Ω both directions → bolted short,
   not a live junction. Rules out the MMIC Darlington DC paths (those read
   higher and are polarity-dependent).
2. **Divide the rail:** on the spare board, **lifted L5** (the ADL5602's
   220 nH RFC) → **the standing short cleared.** This localized the *measured*
   bolted short to the U2 branch.
3. **Inspected Q1 in schematic:** the +5V/L1 feed is wired to Q1's **base**,
   not collector. This is the fault that smokes on power-up.

## Why one root cause explains all of it

The Q1 `L1 → base` error is the **root cause**. On power-up it drives a
destructive rail current; the standing bolted short that was actually measured
(cleared at L5, polarity-independent) is most consistent with **U2 (ADL5602)
failing short as a casualty** of that fault event, then clamping the shared
+5V rail. So:

- "The transistor tied the whole 5V rail to ground" is true at the **cause**
  level.
- The physical dead short chased on the bench was most likely **U2 collateral
  damage**, not the live B-E junction (which reads diode-like, not 0.69 Ω).

## The bug in detail — Q1 (BFR92A) tripler

**BFR92A SOT-23 pinout:**

| Pin | Function |
|---|---|
| 1 | Base |
| 2 | Emitter |
| 3 | Collector |

**Intended (correct) class-C tripler** (per schematic Section B):

- `+5V → L1 (220 nH RFC) → collector (pin 3)`
- `base (pin 1) ← R6 (47 kΩ to GND, class-C bias) + C10 (input coupling)`
- `emitter (pin 2) → GND`
- `collector → C11 → 437 MHz BPF`

**As-drawn (wrong):** L1 lands on the **base** (pin 1). At DC the input
coupling (C10) and output coupling (C11) both block, so the *only* current
path is:

```
+5V → L1 (choke, ~0.3 Ω DC) → base → B-E junction (~0.7 V) → emitter → GND
```

The B-E junction clamps the base to ~0.7 V; the remaining ~4.3 V drops across
the choke's tiny DCR → current runs away, limited only by copper. The
collector does no useful work (Ic ≈ 0). A BFR92A rated for tens of mA / a few
hundred mW is driven to amps → smoke.

> Note: Q1 pin 2 → GND (emitter grounded) is **correct** — this is a
> common-emitter stage, the emitter is supposed to be grounded. Only the
> L1/base connection is wrong.

## LTspice validation

Model: [`../design/ltspice_simulations/tripler.asc`](../design/ltspice_simulations/tripler.asc)

- **Broken circuit** (as-PCB, L1 → base), `.dc V2 0 5` or ramped `.tran`
  with `V2 = PWL(0 0 1m 5)`:
  - Base node clamps at ~0.7 V while `I(L1)`/`Ib(Q1)` explode exponentially
    once the ramp passes the junction knee; `Ic(Q1) ≈ 0`.
  - With realistic `L1 Rser = 0.3 Ω`, peak current caps around ~14 A — still
    ~500× the part rating. That runaway *is* the smoke.
- **Fixed circuit** (L1 → collector), `V1 = SINE(0 1.65 145.67Meg)`,
  `.tran 0 2u 0 50p`, `.options plotwinsize=0`:
  - No rail runaway; transistor idles safely and conducts on drive peaks.
  - **FFT of the output shows a strong 3rd harmonic at 437 MHz** (with
    fundamental 145.67 MHz and 2nd at 291 MHz to be rejected by the
    downstream BPF, which is not modeled here).

LTspice gotchas learned:
- `.op` gives a single point (no waveform); use `.dc` (source on X-axis) or a
  ramped `.tran` (time on X-axis) to get plots.
- Set `L1 Rser` to a realistic **0.3 Ω** — the default `1m` yields a
  non-physical kilo-amp current. Change it **inside LTspice** (right-click →
  Series Resistance); editing the `.asc` on disk while LTspice is open gets
  clobbered on save.
- FFT requires `.options plotwinsize=0` (disable waveform compression) or the
  spectrum is garbage.

---

## Rev-B action items

- [ ] **Fix Q1 wiring:** rewire so `L1 (+5V RFC) → collector (pin 3)`; base
      (pin 1) keeps only R6 + C10. ECO to PCB, re-route the tripler.
- [ ] **Reselect Q1 transistor** — the populated MMBT3904 (ft = 300 MHz) is
      below the 437 MHz output; pick an ft ≥ ~2 GHz RF NPN and **verify its
      SOT-23 pinout vs. the footprint**. See "Transistor sourcing" below.
- [ ] **Replace U2 (ADL5602)** on both physical boards (see recheck below).
- [ ] **Confirm U2 status** — measure RFOUT → GND on a **never-powered**
      board (or after a fresh U2):
      - Open → U2 was fine / single root cause was Q1.
      - Still ~0.7 Ω → U2 is a casualty; replace.
- [ ] **Redesign the TX 437 MHz BPFs** — the as-built values give essentially
      **zero 2nd-harmonic rejection**, and the C86059 inductor (Q≈17) is too
      lossy. Rev B: new cap values + **Coilcraft 0402HP-10NXGRW** (10 nH, Q≈55
      @437, SRF 4.7 GHz, wirewound, on JLC) replacing C86059, for both the
      pre-MMIC and output BPF. See "TX BPF study" below.
- [ ] **RX front end → ALL-UHF (supersedes the 2 m RX).** Move RX to ~435 MHz
      (adopted 2026-08-17 — kills the FM/NF problem, one shared antenna).
      Preselector = 435 BPF, **validated**: 10 nH 0402HP, Ccpl 6 p / Cres 35.75 p,
      IL 1.9 dB, FM −49 dB. Add **RX-LO tripler** (CLK1 ×3 → 435, clone of the
      TX tripler). **PSA4 UHF re-match.** Baseband (Sallen-Key + MCP6022 + ADC)
      unchanged. Single shared UHF antenna + diplexer / T-R switch. See "RX
      architecture — moving to ALL-UHF" and "RX 2 m BPF study" below.
- [ ] **Add a tuned collector tank to the tripler.** As-built, L1 is a 220 nH
      RFC choke feeding straight into the BPF — no resonant load at 437. Result
      (end-to-end sim): the collector puts out ~34 dB MORE fundamental than 3rd
      harmonic, and the BPF can't rescue it (437 only −12.9 dBm, fund/2nd right
      behind it). Fix: make L1 a **~15 nH tank inductor** (still carries DC
      bias) + **~8 pF tank cap** resonant at 437. Sim result with the tank:
      collector fundamental collapses 6.0 V → 0.06 V and the 437 develops.
      **RESOLVED end-to-end:** with the tank (15 nH ∥ 8.2 pF) + narrowed BPF
      (Ccpl 4.2 p / Cres 38 p, well-centered), the integrated tripler→BPF sim
      at Vd=1.4 gives, projected through the MMIC + 2nd BPF to the antenna:
      **~+12 dBm carrier, fundamental −58 dBc, 2nd harmonic −35 dBc, 4th −35
      dBc** — in spec on power AND spurs. TX path validated end-to-end. Exact
      BPF caps are VNA-tune targets (the pre- and post-MMIC filters see
      different source impedances, so each tunes in place).
- [ ] **Add BPF tuning pads (layout).** At each shunt resonator node of both
      437 MHz BPFs, add a small capacitive **tuning pad** next to a ground
      finger. Size the fixed shunt cap slightly LOW (e.g. 33 pF vs the 36 pF
      target) and tune *up* by adding solder to the pad (add-only is easier
      than knife-trimming copper). Keep filter caps in the open (no shield can
      over them) for VNA-guided rework. Rationale: the sim center is a starting
      point — cap tolerance (±2%) and PCB parasitics at 437 MHz will detune it,
      so plan on 2–4 VNA tweaks at bring-up. Same treatment worth adding to the
      2m RX BPF and the LO LPF. For the flight unit: tune fully, then lock
      tight-tolerance parts (can't VNA-tune in orbit).
- [ ] **Re-verify the pre-power sequence** after rework: +5V→GND and +3V3→GND
      should be open (kΩ+ as bulk caps charge), no rail-to-rail shorts, before
      applying any supply.

## Footprint / schematic pinout audit (do before committing rev B)

A genuine drafting slip put +5V on Q1's base. Verify every three-terminal
active device's C/B/E (or pin function) against its datasheet **in the
schematic** before the next fab:

| Ref | Part | Package | Pinout verified vs datasheet? |
|---|---|---|---|
| Q1 | BFR92A | SOT-23 | ❌ FAIL — L1 on base, must move to collector |
| U2 | ADL5602 | SOT-89 | [ ] verify RFIN/GND(tab)/RFOUT |
| U10 | PSA4-5043+ | SOT-89 | [ ] verify RF_IN / GND / RF_OUT+Vd |
| U1 | Si5351A | — | [ ] verify VDD/VDDO/pins |
| U? | 74LVC1G86 | — | [ ] verify XOR pinout |
| U7 | MCP6022 | SOIC-8 | [ ] verify op-amp pinout |

---

## Transistor sourcing (Q1) — ACTION NEEDED

- **Design intent:** BFR92A (ft = 5 GHz) for flight; 2N3904 (ft = 300 MHz)
  for prototype only.
- **Rev A reality:** BFR92A was not stocked at JLCPCB, so the board was
  populated with a **FOSAN MMBT3904** (2N3904 in SOT-23, **ft = 300 MHz**).
- **Problem:** the tripler *output* (437 MHz) is *above* the MMBT3904's ft.
  Past ft, transit time / junction caps smear the current pulses and roll off
  the wanted 3rd harmonic. It produces a weak 437 MHz (breadboard: ~−7.4 dBm
  with 2N3904) but with poor conversion efficiency, thin margin into the
  ADL5602, and high part/temp/bias sensitivity. Not a flight-grade choice.
- **Need:** a JLCPCB-sourceable NPN RF transistor, **ft ≥ ~2 GHz** (ideally
  5 GHz+), SOT-23.

| Part | ft | Pinout (SOT-23) | Notes |
|---|---|---|---|
| **2SC3356 (mark R25)** ✅ SELECTED | **7 GHz** | same as MMBT3904 (datasheet-confirmed) | highest ft, cheapest, **drops into existing footprint — no footprint change** |
| BFR92A | 5 GHz | 1=B, 2=E, 3=C | intended part; also footprint-compatible |
| BFR92P (e.g. BFR92PE6327) | 5 GHz | **1=C, 2=E, 3=B** | ⚠ **MIRRORED pinout** — would re-swap B/C; rejected |
| MMBT3904 (populated) | 300 MHz | 1=B, 2=E, 3=C | ❌ too slow for 437 MHz |

**Decision: 2SC3356 (R25).** Datasheet confirms its SOT-23 pinout matches the
MMBT3904, so it drops into the existing footprint with **no layout change to
the transistor pads**. The only tripler change for Rev B is the L1→collector
*net* fix. 7 GHz ft, cheaper than the BFR92P, and avoids the BFR92P mirrored-
pinout trap entirely.

> **⚠ PINOUT WARNING — do not repeat the Q1 bug.**
> `BFR92PE6327` (found on JLC, electricals ideal) is the **BFR92P**, whose
> pinout is **mirrored** vs. BFR92A / MMBT3904: pin 1 = **Collector**,
> pin 3 = **Base**. The current footprint is wired for 1=B / 3=C, so dropping
> a BFR92P in unchanged would **re-swap base and collector** — the exact fault
> that smoked Rev A. Either (a) source a plain **BFR92A** to match the existing
> footprint pinout, or (b) use the **BFR92P** and lay the footprint out to its
> 1=C / 2=E / 3=B pinout deliberately in Rev B. Verify against the datasheet
> pinout diagram for the exact ordering P/N before committing copper.

## LTspice tripler study — bias & drive (2026-08-15)

Model: [`../design/ltspice_simulations/tripler.asc`](../design/ltspice_simulations/tripler.asc)
(fixed topology, L1 → collector).

> **Model caveat:** run with LTspice's generic default NPN (`standard.bjt`:
> TF = 0, no junction caps → an idealized, infinitely-fast device) into a
> broadband 50 Ω load (no tuned tank). **Conceptual conclusions are valid;
> absolute 437 MHz levels and exact optima are optimistic** until re-run with
> a real device model (BFR92A/P or 2N3904) and a 437 MHz tuned load.

**Finding 1 — drive optimum ≈ 1.0 V amplitude.**
2D sweep Vd = 0.6–1.4 V. Absolute 3rd-harmonic (437 MHz) turns on sharply
between 0.8→1.0 V and **peaks at Vd ≈ 1.0 V**, then rolls off gently. Full
logic-level drive from the XOR (~1.65 V amp) sits ~1 dB past the peak, in the
flat region — acceptable, no change needed.

**Finding 2 — base resistor R6 is non-critical over 10 k–220 k.**
Sweeping Rb 10 k → 220 k moved output < 0.1% (residual scatter is numerical
noise). The base network is a **hard self-bias clamp**: for large R the DC
self-bias saturates at ≈ −(V_peak − 0.7 V) *independent of R*. R6 only becomes
a tuning knob below ~a few hundred ohms.
- **Design-positive:** R6 = 47 k tolerance is a non-issue — any value ≳ few kΩ
  gives the same deep class-C clamp.
- To use bias as an actual knob, sweep Rb ~100 Ω–5 kΩ, not kilohms.

**Self-bias mechanism (why overdriving hurts):** rectified base current charges
C10; more drive → more negative average base bias → narrower conduction →
richer harmonics but *lower* absolute current/output. There is an optimum
drive; more is not better.

**Flag:** breadboard showed 47 k beating 10 k by ~5 dB; the ideal-model sim
shows no such difference. The real R6 sensitivity lives in device dynamics
(ft, junction caps) the default model lacks → yet another reason to re-run
with a real transistor model before trusting absolute numbers.

### Real-device model (2SC3356) — RETRACTED interim result

An intermediate 2SC3356 run at `.tran 0 .1u` (100 ns) appeared to show a drive
optimum at Vd ≈ 1.0 V and a "null" past it. **That was a settling artifact** —
the self-bias RC (R1·C1) is far longer than 100 ns, so the bias never
established and the transistor was conducting far too widely. **Disregard it**
(and the interim "pad the XOR drive down" advice it produced). The settled run
below supersedes it.

### Real-device model (2SC3356) — settled, tuned load (VALID)

`.tran 0 200u 199u 50p` (≈4 RC, settled — DC(out) = 5.000, DC(tank) ≈ 3e-11
confirm steady state), C1 = 1 n, Rb = 47 k, with the 437 MHz tuned collector
load (Cblk 10 n → parallel L 8.2 n ∥ C 16 p ∥ R 50, f0 ≈ 439 MHz).

Power delivered to the 50 Ω load, `P = V_pk²/(2·50)` from `V(tank)` 3rd harmonic:

| Vd (V) | V(tank) 437 MHz (V) | Delivered |
|---|---|---|
| 0.8 | 0.0193 | −24 dBm |
| 1.0 | 0.0633 | −14 dBm |
| 1.2 | 0.109 | −9 dBm |
| 1.3 | 0.132 | −7.6 dBm |
| 1.4 | 0.153 | **−6.3 dBm** |

- **Output rises monotonically with drive and is saturating** (dB steps shrink)
  — no optimum/null. **More drive helps; do NOT pad the XOR.** Extend the sweep
  (Vd → 3) to find the saturation point / true operating output.
- **Absolute level validated against the bench:** −6.3 dBm at Vd = 1.4 matches
  the breadboard's **−7.4 dBm** (2N3904); the faster 2SC3356 giving ~1 dB more
  is expected. The settled sim now agrees with measured reality — the earlier
  cold-start +11 dBm figures were artifacts.
- **Tank works:** 437 MHz is the largest component in `V(tank)` (5.5× the
  fundamental; 145 MHz suppressed ~15 dB). Loaded Q ~2, so 291/583 MHz are only
  ~5–6 dB down — the real 3-pole BPF cleans those up.
- **R6 still non-critical** over 10 k–220 k (confirmed on the earlier sweeps).

**Link-budget implication (grounded in the settled model + bench agreement):**
tripler ~−6 dBm → ADL5602 +20 dB → ~+14 dBm at MMIC out → −~2 dB output BPF →
**~+11–12 dBm at the antenna port**. Supports the design's original
+13 dBm-at-MMIC / ~+11 dBm-at-antenna estimate.

**Methodology lesson:** self-biased class-C stages need the transient run out
to several R·C to reach steady state before the harmonic content is meaningful.
Use a short save window (`.tran … Tstart …`) to keep the raw file small during
the long settle. Under-settled runs drastically *over*-estimate output.

---

## TX 437 MHz BPF study (2026-08-15) — as-built filter has no rejection

Both TX band-pass filters (pre-MMIC and output; identical topology and values)
were modeled from the as-built values in `Schematic PDF_..._20260815.pdf`:

- Topology: `series C10(10pF) → [L2 15nH ∥ C12 6.8pF] → series L3(15nH) →
  [L4 15nH ∥ C13 6.8pF] → series C11(10pF)` (per-filter refdes vary).
- Inductor: **JLC C86059**, 15 nH 0402, **Q = 8 @ 100 MHz** (→ ~Q17 @ 437),
  DCR 320 mΩ, SRF 2.5 GHz. A lossy multilayer part, not a high-Q RF inductor.
- Sim: `hardware/comms/design/ltspice_simulations/Filters/437MHz_BPF_asbuilt.asc`
  (and `.cir`), inductor loss modeled via `Rser`/`Cpar`.

**Finding — the as-built filter is mis-centered AND far too broad:**

| Config | f_center | IL @ center | rej @ 291 (2nd) | rej @ 146 (fund) |
|---|---|---|---|---|
| As-built values | ~607 MHz | −0.8 dB | −7.6 dB | −27.6 dB |
| Caps ×2.8 (centered) | 437 MHz | −1.5 dB | **−1.7 dB** | −14.6 dB |

Even perfectly centered on 437, the 2nd harmonic passes at **−1.7 dB**
(target > 30 dB). The as-built values are not a real filter — the shunt
resonators sit at ~298 MHz, not 437, and the coupling is far too tight.

**Good news — the low-Q inductor is NOT the blocker.** The design doesn't need
the 5 MHz bandwidth the schematic note mentions (that would be lossy *and*
overkill). A **moderate ~50–80 MHz bandwidth** at 437 gives *both* low
insertion loss (Q ≈ 17 is fine that wide) *and* >30 dB at 291 (which is 33%
away — easy for a proper 3-pole). Plan: keep each filter broad-ish and
low-loss, and rely on the **two cascaded stages** (pre + post-MMIC) for the
~60 dB total; aim each at ~15–20 dB at 291.

**Retune** (`437MHz_BPF_asbuilt.asc`): resonator caps `Cres` (center) and I/O
coupling caps `Ccpl` (bandwidth) split into independent knobs; inductor Q
parameterized.

| Cres | Ccpl | Q | f_center | IL | rej_2nd | rej_fund | rej_4th |
|---|---|---|---|---|---|---|---|
| 8.2p | 4.7p | 17 | 640 MHz | −1.5 | −15.1 | −39.7 | — |
| 22p | 4.7p | **17** | 437 MHz | **−4.7** | −11.2 | −37.2 | −20.0 |
| 22p | 4.7p | **40** | 438 MHz | **−2.3** | −10.5 | −37.3 | −19.9 |

**Conclusion — the inductor is the lever.** Centered on 437, the C86059
(Q≈17) forces **4.7 dB** insertion loss; a Q=40 inductor cut that to 2.3 dB
with rejection unchanged. You cannot tune out of it (narrower = better
rejection but worse IL). The fix is a high-Q RF inductor.

**Rev-B BPF design — L-coupled (⚠ SUPERSEDED 2026-08-18 by the cap-coupled Chebyshev, next section):**

| Board part | As-built | Rev B |
|---|---|---|
| Series coupling caps (C10/C11, C9/C19) | 10 pF | **4.7 pF C0G** |
| Shunt resonator caps (C12/C13, C20/C21) | 6.8 pF | **33 pF C0G** |
| Inductors (L2/L3/L4, L6/L7/L8) | 15 nH C86059 | **10 nH Coilcraft 0402HP-10NXGRW** (Q≈55@437, SRF 4.7 GHz) |

Simulated response (`437MHz_BPF_asbuilt.asc`, `Lval=10n Q=55 Cres=33p Ccpl=4.7p`):
f_center 437.0 MHz, **IL −2.5 dB**, rej_fund −40.7 dB, **rej_2nd −14.1 dB**,
rej_4th −23.7 dB. Two cascaded → ~−28 dB at 291 MHz; with the tripler's native
~−6 dB 2nd/3rd ratio, the 2nd harmonic sits **~−34 dBc at the antenna** —
clears the >30 dBc amateur/QRP spurious target. Antenna power ~+9 dBm.
All values are standard 0402 C0G / stock parts.

---

## TX 437 MHz BPF — FINAL: 2-pole cap-coupled Chebyshev (2026-08-18, LOCKED)

The L-coupled Rev-B filter above works, but its 2nd-harmonic rejection is weak
(~−14 dB/stage). A **capacitively-coupled 2-pole Chebyshev** was benchmarked
head-to-head and wins decisively. Sims:
`Filters/437MHz_BPF_2nd_order_chebyshev.asc` (filter-alone) and
`ltspice_simulations/tx_circuit_cheby.asc` (full chain).

**Topology change:** replace the series *coupling inductor* with a series
*coupling cap*, and drop the resonator caps way down:

| Element | L-coupled (superseded) | **Cap-coupled cheby (LOCKED)** |
|---|---|---|
| Resonators (×2) | 10 nH 0402HP ∥ 33–36 pF | 10 nH 0402HP ∥ **9.1 pF** |
| Inter-resonator coupling | series **inductor** (10 nH) | series **cap 1.6 pF** |
| I/O coupling caps | 4.7 pF | **3.9 pF** |
| (all caps C0G ±2%) | | |

**Filter-alone S21:** IL@437 −1.2 dB, rej_2nd(291) −37 dB, rej_4th(583) −13 dB.
583 is the weak side — high-side coupling-cap feedthrough, inherent to a 2-pole.
A **3-pole** was also tried: superb rejection (2nd −70, 4th −40) but **IL −10.7 dB**
(synthesized too narrow → narrow-band × finite Q blows up IL) — rejected.

**In-chain tuning** (`tx_circuit_cheby.asc`, `.four` on txout, Cres stepped):
output power *and* 583 rejection both optimize at **Cres = 9.1 pF**. Note the
standalone 50 Ω `.ac` *mis-predicts* the center (put 9.1 p at 431 MHz) — the tank
source impedance shifts it, so **tune in-chain, not off the 50 Ω sweep.**

**Result vs the L-coupled chain (both full-chain to the antenna):**

| | L-coupled chain | **cap-coupled cheby** |
|---|---|---|
| Power @ 437 | +11.3 dBm | **+11.9 dBm** |
| 2nd (291) | −34 dBc | **−69 dBc** |
| Worst spur | −34 (291) | **−36.6 (583)** |

Cheby wins on **both** output power and worst-case spur. Collector tank
(L1 15 nH / C7 8.2 pF) unchanged — the Cres retune alone did it. **583 is the
watch-item**; the layout tuning pads (add C → larger Cres) buy more 583 margin
add-only if a spurious-emissions measurement ever demands it. 3-pole remains the
only-if fallback (build wide, more Ccpl, to keep IL ~2–2.5 dB).

---

## RX 2 m input BPF study (2026-08-17) — close-in FM rejection vs. noise figure

The 2 m input BPF (145.9 MHz, **before the PSA4 LNA**) is the tightest
optimization on the board. It must reject FM broadcast (88–108 MHz), the LO
2nd harmonic (291.8 MHz), and 437 MHz TX leakage, while adding minimal
insertion loss — because **IL before the LNA adds ~dB-for-dB to system NF.**

Sim: [`../design/ltspice_simulations/rx_circuit.asc`](../design/ltspice_simulations/rx_circuit.asc)
(3-pole coupled-resonator, same topology as the TX BPF; inductors modeled as
high-Q **0402HP, Q≈40 @146 MHz** replacing the as-built C167487 multilayer).

**Tuning progression (S21):**

| Config | f_center | IL @146 | rej FM(100) | rej LO2(292) | rej TX(437) |
|---|---|---|---|---|---|
| as-built (82n/10p, ideal L) | 222 MHz | — | −14 | −7.6 | −18 |
| Cres 32p, ideal L | 146 | ~0 | −11 | −29.5 | −38 |
| Cres 32p, **Q=40** | 145 | **−2.24** | −11.5 | −30 | −39 |
| Ccpl 6p (narrowed), Q=40 | 151 | **−4.2** pk | −17.7 | −35.5 | −43.5 |

**Findings:**
1. As-built values mis-center (222 not 146) — same as the TX filter; re-center by raising `Cres`.
2. **FM (100 MHz) is the binding constraint and cannot be met by narrowing.**
   FM is only 0.68×f0 (close-in): rejecting it 30 dB needs a narrow filter, but
   narrowing doubled the IL (2.2 → 4.2 dB) and FM was *still* only −17.7 dB.
   Reaching FM −30 dB would push IL past 5–6 dB → **system NF 6–7 dB
   (unacceptable).**
3. The broad, low-loss shape (IL ~2.2 dB) already meets TX (−38) and LO2 (−30).
   **Only FM fails, and it needs a targeted tool, not a narrower filter.**

**Design options (tradeoff, for the rev-B decision):**

| Approach | FM rejection | NF impact | Complexity | When it wins |
|---|---|---|---|---|
| **Notch @ ~100 MHz** (series L-C shunt zero) | deep but narrow; single notch may miss band edges | **~none** | +1 L +1 C, tune | a specific close-in interferer — **our case; try first** |
| Add a pole (4+) | steeper all skirts | **worse** (+loss pre-LNA) | +parts/space | broad rejection when loss is affordable — *not* RX |
| Elliptic/Cauer | zeros placed systematically | moderate | hard to tune, tolerance-sensitive | multiple close-in zeros, all-passive pre-LNA |
| Split filtering around LNA | sharp filter *after* LNA | **best** (post-LNA loss ~free) | re-arch board | standard low-NF RX; bigger change |
| Relax FM spec | — | **best** (broad low-loss) | none | if PSA4 IIP3/P1dB tolerates in-orbit FM |

**The asymmetry:** adding a pole is the *wrong* direction — it buys selectivity
by spending pre-LNA loss (= NF), the one resource RX can't afford. The notch
does the opposite (deep rejection, ~zero passband loss).

**Notch attempt — also hit the NF wall.** Broad BPF + one 100 MHz notch nailed
the FM *center* (−30.6) but the band *edges* leaked (88 −13.5, 108 −24.5) at
IL 2.9 dB. Two notches (91/106 MHz) covered the edges better but **loaded the
146 passband** (each notch is only ~50 Ω of shunt reactance at 146 since FM is
close-in) → **IL jumped to 5.3 dB** and the middle still leaked (98 −24, 100
−25). A series-L-C notch is only "free" for a *narrow, far* interferer; FM is
*wide and close-in*, so it can't avoid loading the passband.

**CONCLUSION — pre-LNA FM rejection is an NF dead end.** We hit the wall from
both directions: narrowing the filter (IL 2.2 → 4.2, FM still leaks) *and*
notching (IL 2.9 → 5.3, FM still leaks). **Rejecting a wide, close-in
interferer band before the LNA fundamentally costs noise figure**, whatever the
method. This is physics, not tuning.

**Rev-B direction for the RX front end:**
- Use the **broad, low-loss preselector** (`Ccpl=10p / Cres=32p`, 0402HP,
  IL ~2 dB) — it already gives TX −38, LO2 −30, and ~−11 dB natural FM rolloff.
- **Do the FM interferer analysis first:** strongest FM-station ERP + path loss
  to orbit + antenna gain vs. the PSA4 P1dB/IIP3 with ~−11 dB preselection. If
  the LNA tolerates the residual FM, you're done.
- **If not, split the filtering around the LNA** — sharp FM/image filter
  *after* the LNA, where the ~21 dB gain makes its loss ~free for NF.
- **Do NOT** add poles or notches before the LNA for FM.

Reusable VHF/FM-rejection filter template (BPF + notch toolkit + S21 harness)
saved at `../design/ltspice_simulations/Filters/146MHz_BPF_FM-reject_template.asc`.
Working preselector: `../design/ltspice_simulations/rx_circuit.asc` (notches
stripped).

**Status:** filter conclusion reached — but see the architecture decision
below, which may make the whole RX-filter FM problem moot.

### RX architecture — moving to ALL-UHF (proposed, 2026-08-17)

The FM NF wall prompted reconsidering the V/U split (70 cm BPSK TX @437 /
2 m AFSK RX @146). **Proposal: move RX to UHF (~435) → an all-UHF system.**
Would supersede the 2026-04-03 V/U comms decision if adopted.

**Gains:**
- **FM interference disappears** — at 435, FM (88–108) is 4× away, trivially
  rejected. Kills the entire NF wall above; RX preselector becomes easy.
- **One antenna, ~3× shorter** — no 52 cm 2 m whip; ~17 cm UHF λ/4, shared
  TX/RX via diplexer or T/R switch. Big CubeSat mechanical win.
- **Design/BOM commonality** — reuses the UHF filter + tripler work already done.

**Costs:**
- **RX LO harder** — Si5351A maxes ~200 MHz, can't make 435 directly. Add an
  **RX-LO tripler** (CLK1 145 → ×3 → 435), a copy of the TX tripler.
- **~9.5 dB more uplink path loss** (f²) — usually covered by the ground station
  (fixed ground antenna gains ~9.5 dB at UHF too).
- **3× Doppler** (~±10 kHz) — software-correctable.
- **TX↔RX isolation** only if full-duplex (437 vs 435 close-in duplexer);
  **non-issue if half-duplex** (assumed mode).

**Gating checks before committing:** (1) confirm **half-duplex**; (2) confirm
the **uplink budget** tolerates ~9.5 dB more path loss.

**Proposed all-UHF RX chain** (same topology as the 2 m RX; RF/LO to UHF):
`UHF ant → 435 preselector BPF (easy) → PSA4 LNA (re-matched 435) → ADE-1+ mixer
← [Si5351A CLK1 145 → ×3 tripler → LO filter → 435 LO] → 51Ω IF term →
Sallen-Key LPF (3.3 kHz) → MCP6022 ×11 → RP2040 ADC`. Baseband unchanged; the
delta is the UHF input filter (trivial), the PSA4 UHF re-match, and the added
RX-LO tripler (+ its LO-drive verification at 435, like the 145.9 LO was).

**Status: ADOPTED (2026-08-17).** Both gating checks pass — **half-duplex
confirmed**, and the **UHF/UHF uplink budget already has plenty of margin**
(previously analyzed). RX moves to UHF (~435 MHz); supersedes the 2026-04-03
V/U comms decision. The RX 2 m BPF FM problem is **obviated** — no post-LNA FM
filter, no FM interferer analysis needed. Rev-B/v2 RX = **435 preselector +
RX-LO tripler (CLK1 ×3) + PSA4 UHF re-match**, baseband unchanged. Single
shared UHF antenna + diplexer/T-R switch. (Breaks IARU V-up/U-down convention —
fine for the senior-design demonstrator; revisit only if IARU-coordinating a
real flight.)

**UHF preselector VALIDATED (2026-08-17):** `../design/ltspice_simulations/rx_circuit.asc`
retuned to 435 MHz with the TX BPF recipe — **10 nH 0402HP (Q55), Ccpl 6 p,
Cres 35.75 p** (broadened from the TX values, since the RX preselector doesn't
need sharp skirts). Result: **f_center 435.5 MHz, IL 1.9 dB, rej FM(100)
−48.8 dB, rej LO-2nd-harm(870) −34.8 dB.** Clean, low-loss, FM-immune, done in
three runs. The VHF version couldn't reject FM at *any* IL — this is the proof
the all-UHF move was right.

**RX-LO chain VALIDATED (2026-08-17):** `../design/ltspice_simulations/rx_lo_tripler.asc`
= the TX chain retargeted (V1 @145 MHz → ×3 = 435). Result: **435 MHz LO at
+12.2 dBm, fundamental −100 dBc, 2nd −34 dBc** — clean and strong. +12 dBm is
~5 dB *over* the ADE-1+ +7 dBm spec → **pad down**; LO drive is a non-issue (the
"RX LO got harder" concern is resolved — a clone of the TX chain over-delivers).
Design note: an ADL5602 LO amp is overkill (+20 dB / ~100 mA) when only ~+13 dB
is needed — use a smaller/lower-power LO amp or a pad on the real board.

**Mixer decision — KEEP the ADE-1+ (2026-08-17).** It's the priciest BOM part
($6), but no cheaper *active* mixer is available at UHF: SA612 EOL, BF1105/9 no
JLC stock, AD8342 $7.56 (dearer), AD831 $32. **Tayloe detector doesn't work at
UHF** — it needs a 4× LO clock (1740 MHz for 435), beyond the Si5351A, the CMOS
switch, and the ÷4 logic; it's an HF-only technique. Fallback if cost-driven:
a **discrete diode ring** (quad Schottky + 2 baluns, ~$2.5, never EOL) — but the
~$3.5 saving isn't worth the tuning/board-space for a few units. Full analysis
in `../design/rx_mixer_trade_study.md` §11.

---

## TX chain — end-to-end validated in LTspice (2026-08-17)

Full rev-B TX chain modeled as one schematic with placed components:
**tripler (2SC3356) → collector tank → pre-MMIC BPF → ADL5602 MMIC → post-MMIC
BPF → 50 Ω antenna.** Reference sim:
[`../design/ltspice_simulations/tx_circuit.asc`](../design/ltspice_simulations/tx_circuit.asc)
(the MMIC is a behavioral gain block: 50 Ω in/out, +20 dB, soft P1dB via
`tanh`, broadband; not the real device model — captures gain/impedance/
compression, not phase/noise/DC-bias).

Node-by-node at Vd = 1.4 (`.four`, signal-flow order):

| Node | 437 (3rd) | 2nd (291) rel | Note |
|---|---|---|---|
| `out` (collector) | 0.52 V | — | tank shorts fundamental (6 V → 0.05 V), develops 3rd |
| `bpf_out` (pre-MMIC BPF) | −5.5 dBm | −20 dBc | first filter shapes |
| `mmicout` (MMIC out) | +14 dBm | −20 dBc | +20 dB; spurs unchanged (broadband amp cleans nothing) |
| **`txout` (antenna)** | **+11.2 dBm** | **2nd −33.8 dBc**, fund −98 dBc, 4th −58 dBc | second filter cleans |

**Result: +11.2 dBm at the antenna, every spur ≥ 34 dB down** — in spec on
power AND spectral purity, and matching the earlier link-budget assumption
(link closes with margin, see `../../../notes/.../link_budget`).

**Notes for the real build:**
- `V(mmicout)` swings high (~2.7 V) → the post-MMIC BPF input isn't a clean
  50 Ω at 437 in the lumped sim; **VNA-tune the 2nd BPF input match** so the
  MMIC sees ~50 Ω.
- BPSK is constant-envelope, so the MMIC can be run nearer P1dB (up to ~+16 dBm
  antenna) if more link margin is ever wanted — but not needed.

This sim is the worked proof of all four rev-B TX fixes together (Q1 wiring,
2SC3356, collector tank, BPF redesign). Keep it as the TX reference.

> **Update (2026-08-18):** the BPF was subsequently upgraded from L-coupled to a
> **cap-coupled 2-pole Chebyshev** (see "TX 437 MHz BPF — FINAL" above). In the
> full chain (`tx_circuit_cheby.asc`) that lifts the antenna to **+11.9 dBm** and
> the worst spur to **−36.6 dBc** — better on both counts than the L-coupled
> numbers in the table above. The cap-coupled chain is now the TX reference.

---

## Files

- **KiCad implementation plan (all-UHF v2):** [`../design/kicad_implementation_plan.md`](../design/kicad_implementation_plan.md)
- **End-to-end TX reference sim (cap-coupled cheby, CURRENT):** [`../design/ltspice_simulations/tx_circuit_cheby.asc`](../design/ltspice_simulations/tx_circuit_cheby.asc)
- End-to-end TX sim (L-coupled, superseded): [`../design/ltspice_simulations/tx_circuit.asc`](../design/ltspice_simulations/tx_circuit.asc)
- Schematic doc: [`../design/altium_comms_schematic.md`](../design/altium_comms_schematic.md)
- Tripler LTspice model: [`../design/ltspice_simulations/tripler.asc`](../design/ltspice_simulations/tripler.asc)
- 437 MHz BPF sims: [`437MHz_BPF_2nd_order_chebyshev.asc`](../design/ltspice_simulations/Filters/437MHz_BPF_2nd_order_chebyshev.asc) (cheby, current), [`437MHz_BPF_asbuilt.asc`](../design/ltspice_simulations/Filters/437MHz_BPF_asbuilt.asc) (L-coupled)
- Tripler breadboard notes: [`tripler_breadboard.md`](tripler_breadboard.md)
- Si5351A / LO bring-up: [`si5351a_bringup_log.md`](si5351a_bringup_log.md)
