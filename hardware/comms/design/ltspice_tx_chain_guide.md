# LTspice TX Chain Simulation Guide

**Board:** Communications
**Purpose:** Simulate the 437 MHz BPSK TX chain stage-by-stage, validating the design before board spin and building intuition for bring-up.

---

## Stage 1: Frequency Tripler (BFR92A)

This is the highest-value simulation. The tripler is the only nonlinear stage in the TX chain and the hardest to predict analytically. SPICE was literally built for this kind of circuit.

### 1.1 Get the BFR92A SPICE model

Download from NXP: search "BFR92A SPICE model" on nxp.com. You'll get a `.lib` or `.mod` file. Save it to your LTspice working directory. Add to your schematic:

```
.lib BFR92A.lib
```

If you can't find the exact model, the 2N3904 model built into LTspice (`nmos` library) works for a first pass — you already validated the tripler with a 2N3904 on the breadboard. Just know that the BFR92A (ft = 5 GHz) will have better harmonic content at 437 MHz than the 2N3904 (ft = 300 MHz).

### 1.2 Build the circuit

```
* === Stage 1: BFR92A Frequency Tripler ===
* Si5351A CLK0 output stand-in: 145.67 MHz square wave, 3.3Vpp, 40Ω source
V_CLK clk_src 0 PULSE(0 3.3 0 0.5n 0.5n {0.5/145.67e6} {1/145.67e6})
R_SRC clk_src tripler_in 40

* Class-C bias: R5 sets DC operating point below cutoff
R5 tripler_in 0 47k

* RFC: DC bias path, high impedance at RF
* Model as ideal inductor — add series R for realistic Q if desired
L1 vcc tripler_out 220n
R_L1 vcc vcc_clean 0

* BFR92A transistor (SOT-23 pinout: 1=E, 2=B, 3=C)
* If using 2N3904 for initial sim, replace Q1 line:
*   Q1 tripler_out tripler_in 0 2N3904
Q1 tripler_out tripler_in 0 BFR92A

* Supply
V_VCC vcc 0 5

* Load (50Ω — represents input impedance of the BPF)
R_LOAD tripler_out 0 50

* Bypass caps on supply
C_bypass1 vcc 0 100n
C_bypass2 vcc 0 10u

* --- Simulation commands ---
* Run long enough to reach steady state (>50 RF cycles)
.tran 0 500n 100n 0.1n
```

### 1.3 What to inspect

**Time domain — click the `tripler_out` node:**

You should see a distorted waveform, NOT a clean sine. The class-C bias means Q1 only conducts on positive input peaks — the output is a series of narrow current pulses. These pulses are rich in harmonics, which is exactly what we want.

Things to look for:
- The output should be a train of sharp spikes at the 145.67 MHz repetition rate
- Peak amplitude depends on supply voltage and load — expect a few hundred mV across 50Ω
- If you see a clean sine wave, the bias isn't class-C enough (R5 too low)

**Frequency domain — FFT the output:**

Right-click the time-domain plot → View → FFT. Set:
- Number of data points: 65536 (or higher for resolution)
- Windowing: Hanning or Blackman-Harris

You should see spectral lines at:

| Harmonic | Frequency | What to look for |
|----------|-----------|-------------------|
| 1st (fundamental) | 145.67 MHz | Strongest line — this is the input frequency |
| 2nd | 291.34 MHz | Present but we don't want it |
| **3rd** | **437.01 MHz** | **This is our TX frequency — measure its power** |
| 4th | 582.68 MHz | Should be weaker than 3rd |
| 5th | 728.35 MHz | Much weaker |

**Key measurements from the FFT:**

1. **3rd harmonic power relative to fundamental:** Read the dB levels of the 145.67 MHz and 437 MHz peaks. The difference tells you the conversion loss of the tripler. On your breadboard with 2N3904 you measured -7.4 dBm at 437 MHz — the sim should be in the same ballpark.

2. **Odd vs even harmonics:** Class-C tripler should have stronger odd harmonics (1st, 3rd, 5th) than even (2nd, 4th). If the even harmonics are dominant, the conduction angle is wrong — try adjusting R5.

### 1.4 Experiment: sweep R5 bias resistor

This directly corresponds to your breadboard finding that 47kΩ was optimal.

Run the simulation three times with R5 = 10kΩ, 47kΩ, and 100kΩ. For each run, FFT the output and record the 437 MHz peak level.

| R5 | Expected effect |
|----|----------------|
| 10kΩ | More base current → transistor conducts longer per cycle → wider conduction angle → stronger fundamental, weaker harmonics. You measured -12.2 dBm at 437 MHz on the breadboard with this value. |
| 47kΩ | Sweet spot — narrow conduction angle, strong 3rd harmonic. Breadboard measured -7.4 dBm at 437 MHz. |
| 100kΩ | Very narrow conduction → even less fundamental power reaches the base, so overall output drops even though harmonic content is rich. Diminishing returns. |

This experiment builds intuition for why 47kΩ was the empirical optimum.

### 1.5 Experiment: compare 2N3904 vs BFR92A

Run the same circuit with both transistor models. The BFR92A (ft = 5 GHz) should show:
- Higher 3rd harmonic power (the transistor can actually switch at 437 MHz)
- Cleaner harmonic spectrum (sharper current pulses = more defined harmonics)
- Less roll-off at higher harmonics

The 2N3904 (ft = 300 MHz) is being asked to generate a harmonic at 437 MHz — above its ft. It still works (you proved it on the breadboard) but the harmonic content falls off faster.

---

## Stage 2: Tripler + Pre-MMIC Band-Pass Filter

Now cascade the BPF after the tripler to see harmonic selection in action.

### 2.1 Add the BPF to the tripler output

Remove `R_LOAD` from Stage 1 and connect the BPF in its place. Use whatever component values you've tuned to in the BPF experiments (or start with the schematic values and iterate):

```
* === Stage 2: Add 437 MHz BPF after tripler ===
* Remove R_LOAD from Stage 1, replace with:

* Input coupling cap
C10 tripler_out bpf_n1 10p

* Shunt resonator 1
L3 bpf_n1 0 15n
C12 bpf_n1 0 6.8p

* Series coupling inductor
L2_bpf bpf_n1 bpf_n2 15n

* Shunt resonator 2
L4 bpf_n2 0 15n
C13 bpf_n2 0 6.8p

* Output coupling cap
C11 bpf_n2 bpf_out 10p

* 50Ω load (represents MMIC input)
R_LOAD bpf_out 0 50
```

**Important:** Use the values you've tuned in the BPF-only simulations. The starting values above (15nH/6.8pF/10pF) are from the schematic and may not produce a centered passband — adjust C12/C13 and coupling caps based on your earlier BPF experiments.

### 2.2 What to inspect

**Time domain — compare `tripler_out` vs `bpf_out`:**

Plot both nodes on the same graph (click tripler_out, then hold Alt and click bpf_out). You should see:
- `tripler_out`: distorted, spiky waveform (rich in harmonics)
- `bpf_out`: cleaner, more sinusoidal waveform (BPF selected the 3rd harmonic)

The BPF output won't be a perfect sine — the filter has finite rejection, so some fundamental and 2nd harmonic leak through. But it should be visibly smoother than the tripler output.

**FFT — compare spectra before and after BPF:**

FFT both `tripler_out` and `bpf_out`. You should see:

| Harmonic | Before BPF | After BPF |
|----------|-----------|-----------|
| 145.67 MHz (1st) | Strong | Suppressed by >30 dB |
| 291.3 MHz (2nd) | Moderate | Suppressed by >30 dB |
| 437 MHz (3rd) | Target | **Passed with minimal loss** |
| 582.7 MHz (4th) | Weak | Suppressed by >20 dB |

The ratio between the 437 MHz peak and the next-strongest harmonic in the `bpf_out` spectrum is the spectral purity of your TX signal at this stage.

### 2.3 Experiment: intentionally detune the BPF

Shift C12/C13 so the BPF is centered at 420 MHz instead of 437 MHz (increase the cap values). Re-run and FFT the output. You'll see:
- The 437 MHz component is attenuated (filter is off-center)
- The output amplitude drops
- The waveform at `bpf_out` might show more distortion (multiple harmonics leaking through at similar levels)

This shows why VNA tuning on the bench matters — even a 4% offset in center frequency causes measurable signal loss.

---

## Stage 3: MMIC Gain Block (Behavioral) + Output BPF

The ADL5602 doesn't have a SPICE model, so we model it as an ideal gain block. This stage is about signal levels and spectral purity, not MMIC internals.

### 3.1 Add behavioral MMIC after the pre-MMIC BPF

Replace `R_LOAD` from Stage 2 with:

```
* === Stage 3: ADL5602 MMIC (behavioral model) ===
* 20 dB voltage gain, 50Ω input/output impedance
* B-source models the gain; R_in models input impedance

R_MMIC_in bpf_out 0 50
B_MMIC mmic_out 0 V=10*V(bpf_out)
R_MMIC_out mmic_out mmic_matched 50

* Bias tee (DC feed for MMIC — models the L5/C24 network)
* In behavioral model the MMIC doesn't need DC bias, but include
* the bias tee passives so parasitic effects are captured
L5 vcc mmic_out_ac 220n
C24 mmic_out_ac mmic_clean 100n

* --- Output BPF (identical topology to pre-MMIC) ---
C19 mmic_matched obpf_n1 10p

L6 obpf_n1 0 15n
C21 obpf_n1 0 6.8p

L7_bpf obpf_n1 obpf_n2 15n

L8 obpf_n2 0 15n
C22 obpf_n2 0 6.8p

C20 obpf_n2 tx_out 10p

* Antenna impedance (50Ω)
R_ANT tx_out 0 50
```

Note: The behavioral MMIC is simplified. It won't model compression (P1dB), noise, or stability. For those you'd need the real S-parameter model in a linear simulator. What it WILL show you is signal levels and how the output BPF cleans up the spectrum after amplification.

### 3.2 What to inspect

**Signal level through the chain:**

Measure peak-to-peak voltage at each stage (use cursors on the time-domain plot):

| Node | Expected level | How to check |
|------|---------------|--------------|
| `tripler_out` | ~100-300 mVpp | Raw harmonic content |
| `bpf_out` | Depends on BPF insertion loss | 437 MHz component only |
| `mmic_matched` | ~10× bpf_out | 20 dB gain |
| `tx_out` | Slightly less than mmic_matched | Output BPF insertion loss |

Convert final Vpp to dBm: P(dBm) = 10 × log10(Vrms² / 50 / 0.001), where Vrms = Vpp / (2√2) for a sine wave.

Your target: ~+10 to +13 dBm at `tx_out` (based on -7 dBm tripler output + 20 dB MMIC gain).

**FFT — full chain spectral purity:**

FFT the `tx_out` node. This is your transmitted spectrum. Measure:

| Metric | How to read it | Target |
|--------|---------------|--------|
| Carrier power at 437 MHz | Peak of the 437 MHz line | +10 to +13 dBm |
| Fundamental suppression | Difference between 437 MHz and 145.67 MHz peaks | > 60 dB (two cascaded BPFs) |
| 2nd harmonic suppression | Difference between 437 MHz and 291.3 MHz | > 60 dB |
| 4th harmonic suppression | Difference between 437 MHz and 582.7 MHz | > 40 dB |

The two cascaded BPFs (pre- and post-MMIC) should give combined rejection of 2× what a single BPF provides. This is why we have two filters — the MMIC has broadband gain and amplifies everything, so the output BPF cleans up after it.

### 3.3 Experiment: see why you need the output BPF

Temporarily remove the output BPF — connect `mmic_matched` directly to `R_ANT`. FFT the output.

You'll see that the MMIC amplified ALL the residual harmonics that leaked through the first BPF. The 2nd harmonic at 291.3 MHz, which was maybe -35 dB below carrier after the first BPF, is now only -15 dB below carrier after 20 dB of broadband gain. Without the output BPF, you'd be transmitting a dirty signal that violates FCC Part 97 spurious emission limits.

Put the output BPF back and FFT again — the harmonics drop back down. This demonstrates the purpose of having BPFs on both sides of the MMIC.

### 3.4 Experiment: MMIC compression (bonus)

The behavioral model `V=10*V(in)` is perfectly linear — it will happily output 100V if you feed it 10V. Real MMICs compress. The ADL5602 has P1dB ≈ +19 dBm output.

To model compression, replace the B-source with a soft-limiting function:

```
* Soft-clipping MMIC model (P1dB ≈ +19 dBm → ~2.8 Vpp into 50Ω)
.param Vclip=1.4
B_MMIC mmic_out 0 V=Vclip*tanh(10*V(bpf_out)/Vclip)
```

The `tanh()` function provides smooth compression. If the tripler output is low enough that 10× gain stays below Vclip, the output is nearly linear. If the gain product exceeds Vclip, the output compresses and generates its own harmonics — which is another reason you need the output BPF.

---

## Stage 4: Full Chain with BPSK Modulation (Optional)

This stage adds the XOR modulator to see the modulated signal. It's useful for understanding the BPSK spectrum but not essential for hardware validation.

### 4.1 Add BPSK modulation before the tripler

Replace the simple clock source with a modulated carrier:

```
* === Stage 4: BPSK modulation ===
* 145.67 MHz carrier
V_CARRIER carrier 0 PULSE(0 3.3 0 0.5n 0.5n {0.5/145.67e6} {1/145.67e6})

* 1200 baud data signal (AFSK tones not needed for BPSK — just a bit stream)
V_DATA data 0 PULSE(0 3.3 0 1n 1n {0.5/1200} {1/1200})

* XOR modulator (behavioral model)
* XOR truth table: output = carrier XOR data
* When data=0, output follows carrier (0° phase)
* When data=1, output is inverted carrier (180° phase)
B_XOR bpsk_out 0 V=3.3*((V(carrier)>1.65) ^ (V(data)>1.65))

R_SRC bpsk_out tripler_in 40
```

### 4.2 What to inspect

**Time domain — watch for phase reversals:**

Plot `bpsk_out` and `data` on the same graph. Every time `data` transitions, the carrier phase should flip 180°. This is BPSK modulation — the carrier itself doesn't change frequency or amplitude, just phase.

**Time domain — verify phase preservation through tripler:**

Plot `tx_out` (after the full chain) and `data` together. The 437 MHz output should also show phase reversals at data transitions. Since 3 × 180° = 540° = 180°, the tripler preserves BPSK phase states. This is the key property of odd-order frequency multiplication that makes the whole TX architecture work.

**FFT — BPSK spectrum shape:**

FFT the `tx_out` with a long transient (>1000 data bits, so `.tran 0 1m 0.5m 0.1n` — warning: slow). The spectrum should show:
- Main lobe centered at 437 MHz with width = 2 × data rate = 2.4 kHz (for 1200 baud)
- sinc-function sidelobes falling off on both sides
- This is very narrow compared to the BPF bandwidth — confirming the filter doesn't distort the modulation

### 4.3 What you learn from Stage 4

- BPSK modulation at 145.67 MHz (before tripling) is valid — the phase states survive 3× multiplication
- The data rate (1200 baud) is so slow relative to the carrier that the modulated bandwidth is negligible compared to the BPF passband — no intersymbol interference from the filter
- This connects to Ray's comment about latency: the filter's group delay (~ns) vs the bit period (~833 µs) means the filter has zero effect on the modulation quality

---

## Summary: What each stage teaches you

| Stage | Key lesson | Validates |
|-------|-----------|-----------|
| 1 | Nonlinear harmonic generation; R5 bias optimization | Breadboard measurements (-7.4 dBm @ 47kΩ) |
| 2 | BPF harmonic selection; why filter center matters | BPF component values; rejection specs |
| 3 | Why two BPFs needed; MMIC amplifies everything | Output spectral purity; FCC compliance |
| 4 | BPSK phase preservation through odd-order multiply | Core TX architecture assumption |

## Tips for all stages

- **Use `.tran` (transient), not `.ac`**, for the tripler and full chain — the tripler is nonlinear and `.ac` only does linear small-signal analysis. `.ac` is fine for the BPF alone but not with the tripler.
- **FFT resolution** depends on simulation duration: Δf = 1/T_sim. For 500ns sim → Δf = 2 MHz. For 5µs sim → Δf = 200 kHz. Use longer sims for sharper spectral lines, but they're slower.
- **Wait for steady state** before measuring — the first ~50ns are transient startup. Use the `.tran` start-save parameter (3rd argument) to skip the startup: `.tran 0 500n 100n 0.1n`.
- **Save disk space** by only recording nodes you care about: `.save V(tripler_out) V(bpf_out) V(tx_out)`.
- **Compare sim to bench** at every stage. If the tripler sim gives -10 dBm and your breadboard gave -7.4 dBm, that 2.6 dB gap is real information about what the SPICE model doesn't capture (parasitics, probe loading, model accuracy).
