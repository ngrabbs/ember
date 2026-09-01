# CubeSat Communications Board (70cm TX / 2m RX)
### Senior Design Project – RF Comms Subsystem

## Overview
This board implements the satellite's full RF communications system on a single PCB:
- **Downlink TX:** 437 MHz (70cm) BPSK telemetry transmitter
- **Uplink RX:** 145.9 MHz (2m) command receiver
- **Controller:** RP2040 (Raspberry Pi Pico)

Both chains share the Si5351A clock generator (3 outputs) and are controlled by the RP2040.
The TX chain uses a frequency tripler to reach 437 MHz from the Si5351A's usable range.

Design goals:
- Discrete RF chains (not module-based) to demonstrate real RF design
- Single PCB with TX/RX isolation for CubeSat stack integration
- BPSK/DBPSK telemetry downlink with G3RUH-style framing + FEC
- Simple, reliable command uplink (FM AFSK / AX.25)
- Follow IARU amateur satellite band conventions (VHF up / UHF down)

### Band Plan

| Function | Band | Frequency | Modulation | Data |
|----------|------|-----------|------------|------|
| Downlink TX | 70cm UHF | ~437 MHz (IARU coordinated) | BPSK/DBPSK | Telemetry, beacon, payload data |
| Uplink RX | 2m VHF | ~145.9 MHz (IARU coordinated) | FM AFSK (1200 baud) | Short command packets |

Note: Final frequencies require IARU amateur satellite coordination.

---

## System Architecture

### Transmit Chain (437 MHz Downlink)
```
Si5351A CLK0 (145.67 MHz) → XOR BPSK Modulator → Frequency Tripler → 437 MHz BPF → SPF5189Z MMIC → Output BPF → Diplexer → Antenna
                                     ↑
                        Pico GPIO (data)
```

The XOR modulator operates at 145.67 MHz where the 74LVC1G86 has excellent
timing margin, then the tripler brings the BPSK signal to 437 MHz. BPSK phase
states (0° and 180°) are preserved through odd-order frequency multiplication
(3 × 180° = 540° ≡ 180° mod 360°). See "74LVC1G86 Timing Analysis" section
for the research that led to this architecture.

### Receive Chain (145.9 MHz Uplink)
```
Antenna → Diplexer → 2m BPF → SA612 Mixer → Baseband LPF → MCP6022 Op-Amp → Pico ADC
                                    ↑
                          Si5351A CLK1 (LO @ 145.9 MHz)
```

### Shared Resources
- **Si5351A:** CLK0 = 145.67 MHz (tripled to 437 MHz for TX), CLK1 = 145.9 MHz (RX LO), CLK2 = spare
- **RP2040:** TX encoding + RX demodulation + command processing
- **Antenna:** Single antenna via diplexer, or dual SMA connectors

---

## Si5351A Frequency Limit — Design Rationale

The Si5351A cannot directly generate 437 MHz. This section documents the
research and trade study that led to the frequency tripler approach.

### The Problem

The Si5351A internal VCO runs at 600–900 MHz. The output multisynth divider
has valid values of **4, 6, 8**, and any fractional value from 8+1/1048575 to
2048 (per Skyworks AN619). To reach 437 MHz, you would need a divider of
~2.06 (900/437), but the minimum divider is 4.

| Divider | Max Output (900 MHz VCO) |
|---------|--------------------------|
| 4       | 225 MHz                  |
| 6       | 150 MHz                  |
| 8       | 112.5 MHz                |

The datasheet specifies 200 MHz maximum output. Real-world testing by the ham
community (RFzero, PA3FWM, NanoVNA users, EEVblog) shows:
- Some devices reach ~290 MHz, but the max frequency is **device-dependent and unreliable**
- Phase noise and spurs degrade significantly above 200 MHz
- Signal quality becomes "much less clean" near limits (RFzero documentation)
- **No reports of any Si5351A producing usable output at 437 MHz**

Sources:
- [PA3FWM — Si5351 programming](https://pa3fwm.nl/technotes/tn42a-si5351-programming.html): Documents VCO range 600–900 MHz, divider minimum of 4, max output 200 MHz
- [RFzero — Si5351A tutorial](https://rfzero.net/tutorials/si5351a/): "possible to use beyond 290 MHz, but maximum frequency depends very much on the actual device"
- [Skyworks AN619](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN619.pdf): Official register map — valid multisynth dividers are 4, 6, 8, and fractional 8+ to 2048
- [QRP Labs VFO kit](http://www.qrp-labs.com/vfo.html): Specifies Si5351A range as 3.5 kHz to 200 MHz

### Options Evaluated

**Option 1: Si5351A at 145.67 MHz + frequency tripler → 437 MHz (SELECTED)**
- Si5351 outputs 437/3 = 145.667 MHz — well within spec, clean output
- Class-C biased transistor generates harmonics; BPF selects 3rd harmonic
- One transistor + a few passives added to the chain
- Keeps a single oscillator IC for both TX and RX (CLK0=145.67 MHz, CLK1=145.9 MHz)
- Frequency multiplier chains are a classic RF technique used in spacecraft transponders
- The 101 Things Ham Transmitter project independently concluded that Si5351 is the right
  oscillator for Pico-based transmitters, validating this IC choice even with the tripler
- **Trade-off:** Extra stage to tune, tripler output ~-10 to -5 dBm before MMIC

**Option 2: ADF4351 PLL synthesizer (35 MHz – 4.4 GHz)**
- Outputs 437 MHz directly with excellent phase noise
- Up to +5 dBm output — more than Si5351
- Confirmed working on 70cm by multiple ham experimenters (thestone.zone ADF4351 build,
  NanoVNA designs)
- **Trade-off:** ~$15–20 vs ~$3 for Si5351; SPI interface with complex 6×32-bit register
  programming; single output so you'd still need Si5351 for RX LO; overkill for a single
  fixed frequency; adds a second synthesizer IC and more board complexity

**Option 3: Si5351A pushed beyond spec**
- Unreliable — device-dependent, not guaranteed to reach even 300 MHz
- Unacceptable for flight hardware where you need every unit to work
- **Rejected**

**Option 4: Si5356A (up to 350 MHz)**
- Still can't reach 437 MHz even at max spec
- **Rejected**

### Why the Tripler Wins

1. **One oscillator IC** for the entire board — CLK0 and CLK1 are both ~146 MHz, well within Si5351A spec
2. **Proven RF technique** — multiplier chains are textbook spacecraft transponder design and a strong capstone demonstration topic
3. **Minimal added hardware** — one transistor, one RFC, a few passives
4. **No firmware complexity increase** — the Si5351 programming is identical, just set CLK0 to 145.67 MHz instead of 437 MHz
5. **Educational value** — demonstrates understanding of harmonic generation, spectral filtering, and RF chain design

---

## 74LVC1G86 Timing Analysis — Why We Modulate Before the Tripler

The original design placed the XOR BPSK modulator after the tripler, operating
at 437 MHz. Datasheet analysis shows this is unreliable. Moving the modulator
before the tripler (at 145.67 MHz) solves the problem completely.

### The Problem: 437 MHz vs Gate Timing

At 437 MHz:
- **Period = 2.29 ns, half-period = 1.14 ns**

The 74LVC1G86 propagation delay from both manufacturers' datasheets:

| Source | Vcc | Load (CL) | tpd typical | tpd max | Est. BW | Atten @ 437 MHz |
|--------|-----|-----------|-------------|---------|---------|-----------------|
| TI | 3.3V | 15 pF | 0.6 ns | 4.0 ns | 583 MHz | -1.9 dB |
| TI | 5.0V | 15 pF | 0.8 ns | 3.3 ns | 437 MHz | -3.0 dB |
| Nexperia | 3.0–3.6V | 30 pF | 2.3 ns | 5.0 ns | 152 MHz | -9.7 dB |
| Nexperia | 4.5–5.5V | 30 pF | 1.9 ns | 4.0 ns | 184 MHz | -7.8 dB |

*(BW estimated as 0.35/tpd; attenuation modeled as single-pole rolloff)*

The TI and Nexperia numbers differ because of different test load capacitances
(15 pF vs 30 pF). Real PCB parasitics push toward the Nexperia numbers. Key findings:

- **TI best-case typical (15 pF, 3.3V):** 0.6 ns tpd → BW ~583 MHz. Would work
  at 437 MHz with ~2 dB loss. But this assumes minimal loading — optimistic.
- **Nexperia typical (30 pF, 3.3V):** 2.3 ns tpd → BW ~152 MHz. At 437 MHz,
  signal is attenuated by ~10 dB (only 33% amplitude). **Not viable.**
- **All max specs fail:** 4–5 ns tpd → BW 70–87 MHz. Zero usable signal at 437 MHz.
  Some units would simply not work.
- **Input transition rate spec (Δt/Δv):** Nexperia specifies max 10 ns/V at
  3.3V. A 437 MHz square wave has ~1.14 ns half-period — violates this spec.

Sources: [TI SN74LVC1G86 datasheet (SCES222Q)](https://www.ti.com/lit/ds/symlink/sn74lvc1g86.pdf),
[Nexperia 74LVC1G86 datasheet Rev.15](https://assets.nexperia.com/documents/data-sheet/74LVC1G86.pdf)

### Alternative Evaluated: 74AUC2G86

The 74AUC family is significantly faster:

| Parameter | 74AUC2G86 | Source |
|-----------|-----------|--------|
| tpd max (datasheet) | 2.0 ns @ 2.5V | TI datasheet |
| tpd measured | 0.46 ns | Hackaday.io bench test |
| Rise time measured | 0.56 ns | Hackaday.io bench test |
| Fall time measured | 0.53 ns | Hackaday.io bench test |
| Ring oscillator freq | 360 MHz | Hackaday.io bench test |
| Est. BW (measured tpd) | ~756 MHz | Calculated |
| Atten @ 437 MHz | -1.3 dB | Calculated |

This would work at 437 MHz. **However:**
- Max Vcc = **2.7V** (can't run at 3.3V with the rest of the board)
- Max output drive = **9 mA** (vs 24 mA for 74LVC) — weaker signal
- Requires level shifting or separate supply rail
- Still marginal based on datasheet max spec (2.0 ns tpd → BW 175 MHz)

Source: [Hackaday.io — "Just How Fast are 74AUC Gates?"](https://hackaday.io/project/28833-microhacks/log/157535-just-how-fast-are-74auc-gates)

### The Solution: Modulate at 145.67 MHz, Then Triple

Instead of fighting gate timing at 437 MHz, we modulate at 145.67 MHz where
the 74LVC1G86 works with massive margin:

| Parameter | At 145.67 MHz | At 437 MHz |
|-----------|---------------|------------|
| Half-period | **3.43 ns** | 1.14 ns |
| tpd typical (Nexperia, 30 pF, 3.3V) | 2.3 ns | 2.3 ns |
| tpd as fraction of half-period | **67%** (works) | 202% (fails) |
| Estimated attenuation | **-2.9 dB** | -9.7 dB |
| tpd max (5.0 ns) as fraction | 146% (marginal) | 439% (impossible) |

At 145.67 MHz, even the worst-case Nexperia max spec only causes attenuation —
the signal still gets through. Typical devices will work cleanly.

**BPSK is preserved through the tripler** because odd-order frequency
multiplication preserves 180° phase shifts:
- Phase state 0°: × 3 = 0° ✓
- Phase state 180°: × 3 = 540° = 180° (mod 360°) ✓

**Bandwidth tripling is negligible** at our data rates:
- At 1200 baud: ±2.4 kHz → ±7.2 kHz after tripling
- At 9600 baud: ±19.2 kHz → ±57.6 kHz after tripling
- Both fit easily in a 5 MHz channel

### Revised TX Chain

```
Si5351A CLK0 (145.67 MHz) → XOR BPSK @ 145.67 MHz → Tripler → 437 MHz BPF → MMIC → Output BPF
                                    ↑
                       Pico GPIO (data, 1200–9600 baud)
```

This eliminates the 437 MHz timing concern entirely while using the same
components. The only trade-off is the 3× bandwidth expansion, which is
irrelevant at these data rates.

---

## Transmitter Design (437 MHz)

### 1. Si5351A Oscillator (145.67 MHz)

- Device: Si5351A (I2C, shared with RX LO)
- Output: CLK0 @ 145.667 MHz (× 3 = 437.0 MHz after tripler)

Connections:
- CLK0 → 100 nF DC blocking cap → 33Ω series resistor → XOR modulator input

Notes:
- Use max drive strength (8 mA)
- 145.67 MHz is well within Si5351A spec — clean, reliable output
- Integer PLL mode preferred for best phase noise (set VCO to 875 MHz, divider = 6 → 145.833 MHz; or VCO to 874 MHz, divider = 6 → 145.667 MHz). Exact VCO/divider combo depends on desired TX frequency from IARU coordination.
- CLK1 outputs 145.9 MHz for RX LO — both outputs are in the same frequency neighborhood, which is convenient for shared PLL configuration

---

### 2. BPSK Modulator (XOR Phase Switch) — at 145.67 MHz

- Device: 74LVC1G86 (single XOR gate, SOT-23)
- **Operating frequency: 145.67 MHz** (NOT 437 MHz — see timing analysis below)

Connections:
- Input A: 145.67 MHz carrier from Si5351A CLK0
- Input B: Data bitstream (Pico GPIO, slow — 1200 to 9600 baud)
- Output: BPSK modulated signal at 145.67 MHz → feeds tripler

Notes:
- At 145.67 MHz, the 74LVC1G86 has massive timing margin:
  - Half-period at 145.67 MHz = 3.43 ns
  - Typical tpd at 3.3V = 0.6 ns (TI, 15 pF) to 2.3 ns (Nexperia, 30 pF)
  - Even worst-case max tpd (4–5 ns) only causes attenuation, not failure
- Add 100Ω series resistor on data line
- RC edge softening (100Ω + 10 pF) on data line to reduce spectral splatter
- The modulated signal is still at 145.67 MHz — the tripler brings it to 437 MHz while preserving the BPSK phase states

---

### 3. Frequency Tripler (145.67 MHz → 437 MHz)

- Device: Single NPN transistor (BFR96 recommended, 2N3904 acceptable for prototyping)

#### Circuit

```
                          Vcc (3.3V or 5V)
                           |
                          RFC (220 nH)
                           |
XOR output ──[100nF]───┬──┤ Collector
(BPSK @ 145.67 MHz)   |  |
               10kΩ    |  └──[100nF]──→ 437 MHz BPF → MMIC
               to GND  |
                        |
                      Base
                        |
                     Emitter
                        |
                       GND
```

#### Operating Principle
- The 10 kΩ base resistor to ground sets **class-C bias** — the transistor is
  biased below cutoff and only conducts on positive peaks of the input signal
- Class-C operation produces strong harmonic content: fundamental (145.67 MHz),
  2nd (291.3 MHz), **3rd (437 MHz)**, 4th (582.7 MHz), 5th (728.3 MHz)
- The following BPF selects the 3rd harmonic and rejects everything else
- **BPSK preservation:** The input is already BPSK-modulated at 145.67 MHz.
  Odd-order frequency multiplication preserves BPSK: a 180° phase shift × 3 =
  540° = 180° (mod 360°). The 437 MHz output carries the same BPSK modulation.
- **Bandwidth tripling:** The BPSK signal bandwidth is tripled by the
  multiplier. At 1200 baud: ±2.4 kHz becomes ±7.2 kHz. At 9600 baud: ±19.2 kHz
  becomes ±57.6 kHz. Both are negligible in a 5 MHz channel — no concern.

#### Component Selection
- **BFR96 (preferred):** ft = 5 GHz, excellent gain at UHF, SOT-89 package.
  Low output capacitance for clean harmonic generation.
- **2N3904 (prototyping):** ft = 300 MHz — will work but with lower 3rd harmonic
  output. Fine for breadboard validation.
- **MMBFJ310 JFET (alternative):** Self-biasing simplifies the circuit. Drain
  current cutoff naturally creates harmonic-rich output.
- **RFC:** 220 nH — impedance at 145 MHz is ~200Ω (adequate RF choke).
  Must have SRF well above 437 MHz. A 100 nH choke also works.
- **Bias resistor:** 10 kΩ to GND sets the class-C operating point. Adjust to
  optimize 3rd harmonic output — lower values increase conduction angle
  (more fundamental, less harmonics), higher values reduce it (more harmonics,
  less total power). Start at 10 kΩ and tune.

#### Expected Performance
- Input: ~+10 dBm from Si5351A (8 mA drive, 50Ω)
- 3rd harmonic output: approximately **-10 to -5 dBm** at 437 MHz (with BFR96)
- Fundamental suppression provided by the BPF (must be >30 dB)
- 2N3904 may yield -15 to -10 dBm at 437 MHz due to lower ft

#### Layout Notes
- Keep trace from Si5351 to tripler short (<10 mm)
- Ground plane under tripler circuit
- Place BPF immediately after tripler — no long 437 MHz traces before filtering

---

### 3. Post-Tripler Band-Pass Filter (437 MHz)

This is the most critical filter in the TX chain. It must:
- Pass 437 MHz (3rd harmonic)
- Reject 145.67 MHz fundamental (>30 dB suppression required)
- Reject 291.3 MHz 2nd harmonic (>30 dB)
- Reject 582.7 MHz and above (>20 dB)

Target:
- Center: 435–438 MHz
- Bandwidth: ~5 MHz
- Insertion loss: <3 dB

Starting component values (3-pole LC, tune with VNA):

- C1 = 10 pF
- L1 = 15 nH
- C2 = 6.8 pF
- L2 = 15 nH
- C3 = 10 pF

Topology: Input — C — L — C — L — C — Output

Notes:
- NP0/C0G caps mandatory at UHF
- Chip inductors with SRF > 1 GHz (e.g., Coilcraft 0402HP series)
- PCB trace inductance contributes significantly at 437 MHz — account for parasitic L in simulation
- **Filter tuning is critical** — expect multiple VNA iterations
- May benefit from a 4th or 5th pole if fundamental rejection is insufficient
- The 3:1 frequency ratio (145.67 to 437 MHz) helps — the fundamental is far from passband

---

### 4. RF Gain Stage

- Device: SPF5189Z (MMIC gain block)

Connections:
- Input: AC-coupled (100 nF) from modulator
- Output: AC-coupled (100 nF) to output BPF
- Bias:
  - Vcc: 3.3–5V
  - RFC: 56 nH choke (SRF > 1 GHz)
  - Bypass caps: 100 pF + 10 nF + 1 µF close to device

Expected:
- ~15–20 dB gain at 437 MHz
- SPF5189Z is well-characterized at 70cm — commonly used in 70cm LNAs/preamps
- Input from modulator: approximately -10 to -5 dBm (tripler output, minus BPF insertion loss, minus modulator loss)
- Output: approximately **+5 to +15 dBm** (~3–30 mW)

---

### 5. Optional PA Stage (v2)

Option A (simple):
- Second SPF5189Z MMIC in cascade
- SPF5189Z saturates around +17 dBm, so second stage mainly recovers modulator losses
- Realistic output with two stages: ~+17 dBm (50 mW)

Option B (discrete class-E, higher power):
- FDT86256 MOSFET (low Coss ~8 pF, Vds 150V max)
- Target: +27 dBm (~500 mW) for viable LEO downlink
- Resonant output network + pi matching to 50Ω
- BPSK is constant-envelope, so class-E works without supply modulation
- Reference: 101 Things class-E amplifier design + Python calculator
- **Note:** Class-E at 437 MHz is challenging — parasitic capacitances significant. May need GaN or LDMOS devices.

Option C (pragmatic):
- RFPA0133 or similar integrated PA module rated for 70cm
- Less "discrete RF design" but reliable path to power

---

### 6. Output Band-Pass Filter (437 MHz)

A second BPF after the MMIC / PA stage for spectral cleanliness at the antenna port.

Target:
- Center: 435–438 MHz
- Bandwidth: ~5 MHz

Same topology and values as the post-tripler BPF (section 3). Can share the same
design or be optimized separately for the higher power level.

Notes:
- At PA output power levels, ensure caps and inductors are rated for the current
- This filter ensures regulatory compliance for harmonic emissions
- Combined with the post-tripler BPF, gives >60 dB total harmonic suppression

---

### 7. TX Firmware (Pico)

- DBPSK encoding with G3RUH scrambling
- Frame structure: sync word + payload + CRC
- Convolutional encoding (rate 1/2, K=7) — from AO-40 FEC stack
- GPIO bitstream output to XOR gate

Stretch goals:
- Reed-Solomon outer code (full AO-40 stack)
- Interleaving (80×65 grid)
- Beacon mode (periodic health telemetry, no ground command needed)

---

## Receiver Design (145.9 MHz)

### Design Philosophy
The uplink receiver needs to be **simple and reliable**, not high-performance. It receives short command packets from a ground station running 5–50W into a directional antenna. The link budget is generous compared to the downlink.

### 1. Input Band-Pass Filter (2m)

Target:
- Center: 144–146 MHz
- Bandwidth: ~4 MHz

Starting component values:
- C1 = 68 pF
- L1 = 120 nH
- C2 = 47 pF
- L2 = 120 nH
- C3 = 68 pF

Topology: Input — C — L — C — L — C — Output

Notes:
- Provides front-end selectivity and TX-RX isolation
- Helps reject the 145.67 MHz TX oscillator leaking through diplexer (though the diplexer's HPF should already attenuate this — belt and suspenders)
- NP0/C0G caps, air-core or high-SRF inductors

---

### 2. SA612 Mixer / IF Stage

- Device: SA612A (NE602 equivalent, SO-8)
- Function: Double-balanced mixer + internal oscillator (oscillator unused — external LO from Si5351)

Connections:
- Input (pin 1/2): From 2m BPF, AC-coupled (100 nF)
- LO input (pin 6): Si5351A CLK1 @ 145.9 MHz, AC-coupled
- Output (pin 4/5): Baseband audio, differential

Notes:
- SA612 works well at VHF, specified to 500 MHz
- Very low power (~3 mA @ 4.5V)
- Provides ~18 dB conversion gain
- Input impedance ~1.5 kΩ — may need resistive or LC matching from 50Ω BPF output
- Direct-conversion: LO = signal frequency, output is baseband audio

---

### 3. Baseband Low-Pass Filter

- Passive RC or active Sallen-Key LPF
- Cutoff: ~3.5 kHz (for 1200 baud AFSK)
- Removes mixer products and out-of-band noise

Suggested:
- 2-pole Sallen-Key using one section of MCP6022
- Component values: R = 22 kΩ, C = 2.2 nF (fc ≈ 3.3 kHz)

---

### 4. Baseband Amplifier

- Device: MCP6022 (dual op-amp, second section)
- Function: Amplify baseband to fill Pico ADC range (0–3.3V)
- Gain: adjustable, ~20–40 dB depending on signal level
- DC bias at VCC/2 for single-supply operation

---

### 5. Pico ADC Sampling + Demodulation

- ADC input: Amplified baseband audio
- Sample rate: ~9.6 kHz (8× oversampling of 1200 baud)
- Software AFSK demodulation (Bell 202: 1200/2200 Hz tones)
- AX.25 frame parsing: flag detection, address check, CRC validation
- Command dispatch to main flight software

Notes:
- AX.25/AFSK experience already exists from the RT-IHU Testbed
- Consider HDLC flag detection with bit-stuffing in software
- Implement command authentication (simple HMAC or sequence numbering) to prevent spoofing
- **Important:** Amateur radio prohibits encryption, but authentication of commands is a gray area — research IARU/FCC stance for your coordination request

---

## Diplexer (Antenna Sharing)

A diplexer allows TX (437 MHz) and RX (145.9 MHz) to share a single antenna.

### Topology: High-pass / Low-pass

The ~3:1 frequency ratio makes this straightforward:
- **Low-pass leg** (passes 145.9 MHz, rejects 437 MHz) → to RX chain
- **High-pass leg** (passes 437 MHz, rejects 145.9 MHz) → from TX chain
- **Common port** → antenna

### Starting Design (5th-order Chebyshev, tune with VNA)

Low-pass leg (cutoff ~200 MHz):
- Series L: 56 nH
- Shunt C: 33 pF
- Series L: 56 nH

High-pass leg (cutoff ~300 MHz):
- Series C: 15 pF
- Shunt L: 22 nH
- Series C: 15 pF

Notes:
- Target >30 dB isolation between TX and RX ports
- 50Ω at all three ports
- This is a starting point — simulate in QUCS or LTspice, then tune on VNA
- Place between antenna SMA and the TX/RX BPFs
- **Note on TX oscillator leakage:** The Si5351 CLK0 at 145.67 MHz is close to
  the RX band (145.9 MHz). The diplexer's HPF leg will attenuate 145.67 MHz
  before it reaches the antenna, and the LPF leg will pass any 145.67 MHz
  leaking into the RX path. The RX BPF provides additional filtering. Monitor
  this during integration testing — if CLK0 leakage desenses the receiver,
  add shielding around the Si5351 or use firmware T/R switching to disable CLK0
  during RX windows.
- Alternative: Skip diplexer, use two SMA connectors + two antennas (simpler RF, more mechanical complexity on the CubeSat)

---

## Single-PCB Layout

### Board Partitioning (4-layer)

```
┌──────────────────────────────────────────────────────┐
│  [SMA]  DIPLEXER                                     │
│         ┌───────┐                                    │
│    ┌────┤ LPF   ├──── RX SECTION ──────────────┐     │
│    │    └───────┘  BPF → SA612 → LPF → Amp     │     │
│    │    ┌───────┐                               │     │
│    └────┤ HPF   ├──── TX SECTION ──────────────┤     │
│         └───────┘  Tripler → BPF → XOR →       │     │
│                    MMIC → BPF                   │     │
│         ┌──────────────────────────────────────┤     │
│         │     DIGITAL SECTION                  │     │
│         │  RP2040 / Pico    Si5351A            │     │
│         │  I2C   SPI   GPIO   UART             │     │
│         └──────────────────────────────────────┘     │
│  [CSKB H1 + H2 stack connectors]                    │
└──────────────────────────────────────────────────────┘
```

### Layer Stack
- **Top:** RF traces + components (TX and RX sections physically separated)
- **Inner 1:** Solid ground plane (no splits under RF paths)
- **Inner 2:** Power planes (3.3V, 5V)
- **Bottom:** Digital signals, I2C, SPI, UART, stack connector

### Isolation Strategy
- **Physical separation:** TX and RX sections on opposite sides of the board
- **Ground via stitching:** Dense via fence between TX and RX sections
- **Guard traces / ground pour** between sections
- **Shield cans:** Optional copper shield cans over TX and RX sections (recommended over tripler + Si5351 area to contain 145.67 MHz leakage)
- Minimum 10 mm separation between TX and RX RF traces
- Si5351A placed in digital section — short I2C to Pico, routed clock traces to TX (CLK0) and RX (CLK1) sections with controlled impedance
- Keep digital lines away from RF paths

### PCB Constraints
- **Impedance:** 50Ω microstrip on top layer (calculate trace width for your stackup)
- **Board size:** Must fit CubeSat Kit stack form factor (~90 × 96 mm max, or custom to fit 1U ~100 × 100 mm)
- **Connectors:** 1× SMA (antenna) or 2× SMA (if no diplexer), CSKB H1 + H2 stack connectors, optional debug header

---

## Bill of Materials

### Active Components
| Component | Part | Package | QTY | Purpose |
|-----------|------|---------|-----|---------|
| Clock generator | Si5351A | QFN-20 or breakout | 1 | TX oscillator (145.67 MHz) + RX LO (145.9 MHz) |
| Frequency tripler | BFR96 (or 2N3904 for proto) | SOT-89 (or TO-92) | 1 | 145.67 → 437 MHz harmonic generation |
| BPSK modulator | 74LVC1G86 | SOT-23-5 | 1 | XOR phase switch (operates at 145.67 MHz) |
| TX gain | SPF5189Z | SOT-89 | 1–2 | MMIC amplifier |
| RX mixer | SA612A | SO-8 | 1 | Double-balanced mixer |
| RX op-amp | MCP6022 | SO-8 | 1 | Baseband filter + gain |
| Controller | RP2040 | Pico module or QFN | 1 | TX/RX DSP + control |

### Passives (RF)
| Component | Values | Type | Notes |
|-----------|--------|------|-------|
| Tripler bias | 10 kΩ | Resistor | Class-C bias to GND |
| Tripler RFC | 220 nH | Chip inductor, SRF > 1 GHz | Collector choke |
| TX BPF caps (×2 filters) | 10 pF, 6.8 pF | NP0/C0G | 437 MHz post-tripler + output BPFs |
| TX BPF inductors (×2 filters) | 15 nH | High-SRF chip (>1 GHz) | 437 MHz post-tripler + output BPFs |
| RX BPF caps | 68 pF, 47 pF | NP0/C0G | 145 MHz filter |
| RX BPF inductors | 120 nH | Air-core or chip | 145 MHz filter |
| Diplexer caps | 15 pF, 33 pF | NP0/C0G | HP/LP legs |
| Diplexer inductors | 22 nH, 56 nH | High-SRF chip | HP/LP legs |
| DC blocking | 100 nF | Ceramic | Throughout RF chain |
| MMIC RFC | 56 nH | Chip inductor, SRF > 1 GHz | SPF5189Z bias |
| Bypass | 100 pF, 10 nF, 1 µF | Ceramic | Power filtering |

### Passives (Baseband)
| Component | Values | Notes |
|-----------|--------|-------|
| LPF resistors | 22 kΩ | Sallen-Key filter |
| LPF caps | 2.2 nF | Sallen-Key filter |
| Gain resistors | TBD | Set op-amp gain |
| Bias resistors | 10 kΩ / 10 kΩ divider | VCC/2 bias |

### Connectors / Mechanical
- SMA edge-mount (1 or 2)
- CSKB H1 + H2 stack headers (2× Samtec ESQ-126-39-G-D, per `system/interfaces/cskb_pinmap.md`)
- Optional shield cans (recommended over tripler and Si5351 sections)
- Test points on key RF nodes (Si5351 output, tripler output, post-BPF, modulator output, MMIC output, SA612 baseband)

---

## Bring-Up Procedure

### Phase 1: TX Chain
1. **Si5351 CLK0** — Verify 145.67 MHz output on TinySA. Check for clean signal, note harmonics.
2. **XOR modulator at 145.67 MHz** — Feed Si5351 into XOR gate with square wave data from Pico. Verify BPSK modulation on TinySA/oscilloscope at 145.67 MHz. This should work easily — well within gate timing. Observe spectral spreading when data toggles.
3. **Tripler** — Connect modulated 145.67 MHz signal to tripler. Verify 3rd harmonic at 437 MHz on TinySA. Measure relative power of fundamental (145.67), 2nd (291.3), 3rd (437), and 5th (728.3). Adjust bias resistor to maximize 3rd harmonic. **Verify BPSK is preserved** — toggle data and confirm phase reversal visible at 437 MHz. If using 2N3904 and output is too weak, switch to BFR96.
4. **Add post-tripler BPF** — Tune on VNA for 435–438 MHz passband. Verify fundamental suppression >30 dB. Verify 2nd harmonic suppression >30 dB. This is the most critical tuning step.
5. **Add MMIC** — Verify ~15–20 dB gain. Check for oscillation. Measure output power.
6. **Add output BPF** — Verify final spectral cleanliness.
7. **Full TX chain** — Transmit known BPSK pattern. Validate on RTL-SDR or HackRF. Measure total output power.

### Phase 2: RX Chain
1. **Si5351 CLK1** — Verify 145.9 MHz LO output.
2. **SA612 + LO** — Inject known 145.9 MHz signal from signal generator or second Si5351 output. Verify baseband output on oscilloscope.
3. **Add RX BPF** — Confirm front-end selectivity on VNA.
4. **Add baseband LPF + amp** — Verify clean audio-band output.
5. **Full RX chain** — Transmit AX.25 packet from HT or Direwolf. Verify Pico decodes the frame.

### Phase 3: Integration
1. **Diplexer** — Verify isolation (>30 dB) between TX and RX ports on VNA.
2. **CLK0 leakage test** — With CLK0 at 145.67 MHz active, measure leakage into RX path. If significant, add shielding or implement T/R switching in firmware.
3. **Half-duplex test** — Confirm TX doesn't desense RX. Test firmware T/R sequencing.
4. **Full system** — Beacon TX + command RX in flight software. End-to-end test with ground station SDR + 2m HT.

---

## Test Equipment

- **TinySA Ultra:** Spectrum analysis (TX output, harmonics, spurs, tripler output characterization)
- **TinyVNA / NanoVNA:** Filter tuning, diplexer tuning, impedance matching
- **Oscilloscope:** Baseband timing, data/clock alignment, ADC input levels
- **RTL-SDR / HackRF:** RX validation (receive own downlink at 437 MHz)
- **2m FM HT:** TX validation (send test uplink commands at 145.9 MHz)
- **Direwolf (PC):** AX.25 packet generation for uplink testing
- **Analog Discovery:** Baseband and digital debug

---

## Firmware Summary

### TX Tasks
- Telemetry collection from flight computer (via CAN/UART/I2C)
- G3RUH scrambling → convolutional encoding → DBPSK symbol generation
- GPIO bitstream output to XOR modulator
- Beacon scheduler (periodic transmission, no ground command needed)
- Si5351 CLK0 enable/disable for T/R switching

### RX Tasks
- ADC sampling of baseband audio (~9.6 kHz)
- Bell 202 AFSK demodulation (software PLL / correlation)
- AX.25 HDLC frame parsing (flag, address, control, data, CRC)
- Command validation and dispatch
- Command acknowledgment (queue for next TX window)

### Operational Modes
- **Safe mode:** Beacon-only TX, RX listening. Minimum power.
- **Nominal:** Beacon TX + telemetry dumps + RX command processing.
- **High duty:** Continuous TX (payload data dump). RX between transmissions.

---

## Open Design Questions

1. **PA stage:** Link budget analysis needed. +15 dBm (30 mW) from single MMIC may be marginal from LEO. +27 dBm (500 mW) likely needed. Class-E feasibility at 437 MHz needs evaluation.
2. **Tripler transistor selection:** BFR96 is recommended but bench test with 2N3904 first for prototyping. Measure actual 3rd harmonic output to confirm levels.
3. ~~**74LVC1G86 at 437 MHz**~~ **RESOLVED:** Datasheet analysis confirmed gate cannot reliably operate at 437 MHz (tpd exceeds half-period). Solved by moving modulator before tripler — XOR operates at 145.67 MHz with large timing margin. BPSK preserved through odd-order multiplication. See "74LVC1G86 Timing Analysis" section.
4. **Half-duplex vs simplex:** Board supports half-duplex (TX and RX, not simultaneous). Firmware T/R sequencing, potentially with Si5351 CLK0 gating to eliminate oscillator leakage during RX.
5. **Antenna:** Single deployable antenna (dual-band) vs two antennas? Dual-band whip/monopole designs exist for 2m/70cm.
6. **IARU coordination:** Submit frequency coordination request early — this can take months. Exact TX/RX frequencies will determine final Si5351 PLL configuration.
7. **Command authentication:** Research FCC/IARU rules on command verification for amateur satellites.

---

## References

- [CubeSatSim (Alan Johnston)](https://github.com/alanbjohnston/CubeSatSim) — UHF CubeSat emulator, APRS telemetry
- [101 Things Ham Transmitter](https://101-things.readthedocs.io/en/latest/ham_transmitter.html) — Pi Pico PIO RF oscillator, class-E amplifier design. Author independently concluded Si5351 PLL is the better oscillator approach vs PIO-generated RF.
- [101 Things Breadboard Radio](https://101-things.readthedocs.io/en/latest/breadboard_radio.html) — Tayloe detector SDR receiver with Pi Pico, MCP6022 baseband, direct-conversion architecture
- [AMSAT AO-40 FEC documentation](https://www.amsat.org/articles/g3ruh/125.html) — G3RUH scrambling, convolutional + RS FEC, DBPSK encoding
- [PA3FWM — Si5351 programming](https://pa3fwm.nl/technotes/tn42a-si5351-programming.html) — Detailed Si5351 internals: VCO 600–900 MHz, multisynth divider 4–2048, max output 200 MHz
- [RFzero — Si5351A tutorial](https://rfzero.net/tutorials/si5351a/) — Practical Si5351A limits: "possible beyond 290 MHz but device-dependent"
- [Skyworks AN619](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN619.pdf) — Official Si5351 register map, valid multisynth divider values: 4, 6, 8, fractional 8+ to 2048
- [thestone.zone — ADF4351 build](http://thestone.zone/radio/2024/05/27/adf4351-board.html) — ADF4351 confirmed working on 70cm (~-2 dBm), evaluated as alternative to tripler approach
- [SA612A datasheet](https://www.nxp.com/docs/en/data-sheet/SA612A.pdf) — Double-balanced mixer, VHF specs
- [TI SN74LVC1G86 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g86.pdf) — Switching characteristics: tpd 0.6 ns typ / 4.0 ns max at 3.3V, 15 pF
- [Nexperia 74LVC1G86 datasheet](https://assets.nexperia.com/documents/data-sheet/74LVC1G86.pdf) — Switching characteristics: tpd 2.3 ns typ / 5.0 ns max at 3.3V, 30 pF
- [Hackaday.io — 74AUC gate speed measurements](https://hackaday.io/project/28833-microhacks/log/157535-just-how-fast-are-74auc-gates) — Measured 74AUC tpd = 0.46 ns, ring oscillator 360 MHz
- [IARU Satellite Frequency Coordination](https://www.iaru.org/reference/satellites/) — Frequency coordination process
- [CubeSat frequency conventions](https://cubesat-resources.space/development/comms/) — UHF downlink / VHF uplink is standard amateur CubeSat practice

---

## License / Attribution

CC0 Public Domain — see LICENSE
