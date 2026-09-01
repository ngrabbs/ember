# Mini-TOTEM BPSK Transmit Chain Plan

## Goal

Build a small experimental transmit signal chain that lets us generate our own BPSK waveform in an FPGA, convert it to analog with a high-speed DAC, optionally upconvert it to S-band around 2.4 GHz, and observe the result on a scope, SDR receiver, or spectrum analyzer.

This is not meant to be the reliable mission radio. The reliable comms path should still be UHF/VHF or another proven radio. This chain is an experimental payload for learning FPGA-based digital communications and SDR-style RF architecture.

---

## Target Architecture

```text
Linux Host / Controller
        |
        | command/config/data stream
        v
IceZero FPGA
        |
        | parallel digital samples
        v
DAC902 / DAC904 high-speed DAC
        |
        | analog baseband or low-IF BPSK waveform
        v
IF low-pass or band-pass filter
        |
        | filtered IF signal
        v
Mini-Circuits ZX05-43MH-S+ mixer
        |
        | S-band RF output plus image products
        v
2.4 GHz band-pass filter
        |
        | cleaned S-band signal
        v
SDR receiver / spectrum analyzer / dummy load
```

---

## Engineering Description

In RF engineering terms, this project implements a **digital baseband / low-IF transmit chain** with later **RF upconversion**.

The FPGA is responsible for generating the digital waveform. The DAC converts that waveform to analog. The IF filter cleans up DAC images and unwanted high-frequency content. The mixer translates the IF waveform to S-band using a local oscillator. The RF band-pass filter selects the desired mixer product near 2.4 GHz and rejects the image, LO feedthrough, and other spurs.

A more formal description:

> We are implementing a digital BPSK transmit signal chain using an FPGA-generated baseband or low-IF waveform, a high-speed DAC, analog IF filtering, and mixer-based RF upconversion to S-band.

---

## Main Subsystems

### 1. Linux Host or Controller

The Linux host is used for development, loading FPGA bitstreams, generating test payloads, and configuring experiments. In a later version, the host could be replaced by a Pi Pico, RP2040 board, or other flight-like controller.

Possible jobs:

- Load FPGA bitstream.
- Send payload bytes or test commands.
- Configure symbol rate, packet length, PRBS mode, and test mode.
- Log results.
- Optionally control LO frequency if a programmable synthesizer is used.

### 2. IceZero FPGA

The FPGA is the core of the experiment.

Possible jobs:

- Generate a carrier numerically if using low-IF.
- Generate a PRBS test pattern.
- Map bits to BPSK symbols.
- Apply optional pulse shaping.
- Feed samples to the DAC at a fixed sample rate.
- Generate packet framing.
- Generate sync words or preambles.
- Provide debug outputs to LEDs or a logic analyzer.

For a first version, keep the FPGA design extremely simple.

### 3. DAC902 / DAC904

The DAC converts the FPGA-generated samples into an analog waveform.

The DAC output is not yet 2.4 GHz RF. It is either:

- **Analog baseband**, centered near 0 Hz, or
- **Low IF**, such as 1 MHz, 5 MHz, 10 MHz, 25 MHz, or 50 MHz.

For early tests, a low IF is easier to observe on a scope and easier to verify with an SDR.

### 4. IF Filter

The DAC output will contain unwanted images and switching artifacts. The IF filter removes as much of that as possible before the mixer.

Early testing can use a simple low-pass filter. Later testing should use a band-pass filter centered on the chosen IF.

### 5. Mixer / Upconverter

The mixer translates the IF signal to RF.

Example:

```text
IF = 50 MHz
LO = 2350 MHz
Mixer outputs = 2300 MHz and 2400 MHz, plus LO leakage and spurs
```

A 2.4 GHz band-pass filter is then used to select the desired 2400 MHz output.

### 6. 2.4 GHz RF Filter

This filter cleans up the mixer output before feeding an SDR, spectrum analyzer, dummy load, or later an RF amplifier.

For early bench tests, do not connect to an antenna. Use attenuation, a dummy load, or a short controlled lab link into an SDR receiver.

---

## Suggested Bring-Up Phases

## Phase 0 — Safety and Bench Setup

Before generating RF, set up the bench carefully.

Recommended equipment:

- Oscilloscope, preferably 100 MHz or better.
- Logic analyzer.
- SDR receiver that covers 2.4 GHz, or spectrum analyzer.
- 50 ohm terminators.
- SMA attenuators, such as 10 dB, 20 dB, and 30 dB.
- RF cables and adapters.
- Optional RF power meter.
- Optional signal generator for LO during early mixer tests.

Important precautions:

- Do not transmit into an antenna at first.
- Use a dummy load or cabled SDR receiver with attenuation.
- Watch signal levels into the SDR receiver.
- Add attenuation before the SDR input.
- Stay inside allowed ISM-band rules for any over-the-air testing.

---

## Phase 1 — FPGA Digital Output Test

### Objective

Prove that the FPGA can generate the correct digital sample stream before connecting the DAC.

### First Test Pattern

Start with simple patterns:

1. Constant midscale value.
2. Square wave sample pattern.
3. Sine lookup table.
4. BPSK symbol pattern.
5. PRBS-driven BPSK.

### What to connect

```text
IceZero FPGA digital DAC pins → logic analyzer
```

### What to look for

On the logic analyzer:

- Stable sample clock.
- Parallel data changing at the expected rate.
- Correct repeating pattern.
- No obvious pin-order mistakes.
- No clock/data timing issues.

### Code needed

FPGA modules:

- Clock divider or PLL/clock generation.
- Sample counter.
- Test pattern generator.
- Parallel DAC output register.

No Linux payload streaming is needed yet. The FPGA can generate patterns internally.

---

## Phase 2 — DAC Static and Simple Waveform Test

### Objective

Prove that the DAC is wired correctly and can produce basic analog waveforms.

### What to connect

```text
IceZero FPGA → DAC902/DAC904 → oscilloscope
```

Use a 50 ohm termination if required by the DAC output stage or module documentation.

### Test 1: Midscale DC

Send a constant digital value to the DAC.

Expected result:

- Scope shows a stable DC level.
- Changing the digital code changes the voltage.

### Test 2: Digital Ramp

Send an incrementing counter to the DAC.

Expected result:

- Scope shows a sawtooth waveform.
- Spectrum analyzer or SDR would show harmonics due to the ramp discontinuity.

### Test 3: Sine Lookup Table

Generate a sine wave from a lookup table.

Example choices:

```text
DAC sample rate: 40 MSPS
Sine frequency: 1 MHz
Samples per cycle: 40
```

Expected scope result:

- A clean sine-like waveform.
- Some quantization and DAC image artifacts.

### Code needed

FPGA modules:

- Sine lookup table ROM.
- Phase accumulator or table index counter.
- DAC output register.

Optional host code:

- Script to select waveform mode.
- Script to set phase increment if using an NCO.

---

## Phase 3 — Baseband BPSK Test

### Objective

Generate a simple BPSK symbol stream and observe it directly at the DAC output.

### Simplest BPSK mapping

```text
bit 0 → negative amplitude
bit 1 → positive amplitude
```

For an unsigned DAC:

```text
bit 0 → midscale - amplitude
bit 1 → midscale + amplitude
```

Example for a 14-bit DAC:

```text
midscale = 8192
amplitude = 3000
bit 0 sample = 5192
bit 1 sample = 11192
```

### First payload

Use a repeating pattern first:

```text
10101010 10101010 10101010 ...
```

Then use a sync word plus text payload:

```text
Preamble: 0x55 0x55 0x55 0x55
Sync:     0x1ACFFC1D
Payload:  "HELLO FPGA BPSK"
CRC:      optional later
```

### What to see on the scope

Without pulse shaping:

- A two-level waveform.
- Transitions between positive and negative symbol levels.
- A repeating 1010 pattern appears as a square wave at half the symbol rate.

This is valid as a first BPSK baseband test, but it has poor spectral behavior because hard transitions create wide sidelobes.

### Code needed

FPGA modules:

- Bit source.
- Symbol mapper.
- Samples-per-symbol counter.
- DAC output register.

Possible bit sources:

- Hardcoded repeating pattern.
- PRBS generator.
- Small ROM packet.
- Host-fed FIFO.

---

## Phase 4 — Low-IF BPSK Test

### Objective

Generate BPSK on a low intermediate frequency instead of raw two-level baseband.

This makes the waveform look more like a real modulated signal and makes later upconversion easier.

### Concept

A carrier is generated digitally inside the FPGA. BPSK flips the carrier phase by 180 degrees depending on the current bit.

Mathematically:

```text
s[n] = A · b[n] · cos(2π f_IF n / f_s)
```

Where:

```text
b[n] = +1 for bit 1
b[n] = -1 for bit 0
```

### Example parameters

```text
DAC sample rate: 40 MSPS
IF frequency:   5 MHz
Symbol rate:    100 ksym/s
Samples/symbol: 400
```

This is slow enough to debug but real enough to teach the architecture.

### What to see on the scope

You should see:

- A sinusoidal carrier at the IF frequency.
- 180-degree phase reversals at symbol transitions.
- With a repeated 1010 pattern, the phase flips every symbol.
- With long runs of identical bits, phase remains constant.

### What to see on an SDR or spectrum analyzer

At the IF output:

- A main lobe centered at the IF.
- Sidelobes depending on symbol rate and pulse shaping.
- Wider spectrum with hard rectangular symbols.
- Cleaner spectrum if pulse shaping is added.

### Code needed

FPGA modules:

- Numerically controlled oscillator, or NCO.
- Sine/cosine lookup table.
- PRBS or packet bit source.
- Symbol mapper.
- Multiplier or sign inverter.
- DAC output formatter.

For BPSK, multiplication by +1 or -1 can be implemented as a sign inversion instead of a full multiplier.

---

## Phase 5 — Add Pulse Shaping

### Objective

Improve spectral behavior by replacing hard symbol transitions with shaped pulses.

### Why it matters

Unfiltered BPSK has sharp transitions. Sharp transitions create wide spectral sidelobes. Real radios use pulse-shaping filters to control occupied bandwidth.

A common choice is a root-raised-cosine filter.

### What to see

On the scope:

- Smoother transitions.
- Less abrupt switching.

On the spectrum analyzer:

- Lower sidelobes.
- More controlled occupied bandwidth.

### Code needed

FPGA modules:

- FIR filter.
- Coefficient ROM.
- Symbol upsampler.
- Optional fixed-point scaling/saturation.

This is a good second-stage FPGA learning milestone. Do not start here. First get unshaped BPSK working.

---

## Phase 6 — Mixer Upconversion to 2.4 GHz

### Objective

Translate the low-IF BPSK waveform to S-band.

### Example setup

```text
DAC output IF: 50 MHz
LO frequency: 2350 MHz
Desired RF:    2400 MHz
Image:         2300 MHz
```

Mixer output contains both:

```text
LO + IF = 2400 MHz
LO - IF = 2300 MHz
```

Use a 2.4 GHz band-pass filter to keep the desired signal and reject the image.

### What to connect

```text
DAC → IF filter → mixer IF port
LO source → mixer LO port
mixer RF port → 2.4 GHz band-pass filter → attenuator → SDR/spectrum analyzer
```

### What to see on SDR or spectrum analyzer

You should see:

- A signal centered near 2.4 GHz.
- Occupied bandwidth related to BPSK symbol rate.
- Possible LO leakage at the LO frequency.
- Possible image frequency on the opposite side of the LO.
- Spurs or harmonics depending on filtering and drive levels.

### Code needed

No new FPGA code is required if the low-IF BPSK waveform already works.

Possible host code:

- Configure LO frequency if using a programmable synthesizer.
- Log test setup parameters.

---

## First Complete Test Recommendation

Do not make the first test complicated. The first complete success should be visible on the scope.

### Test A: FPGA to DAC sine wave

Goal:

- Prove the FPGA and DAC interface works.

Expected scope result:

- Stable sine wave at 1 MHz or 5 MHz.

### Test B: FPGA to DAC unshaped baseband BPSK

Goal:

- Prove bit-to-symbol mapping.

Transmit:

```text
10101010 repeated
```

Expected scope result:

- Two-level square-like waveform.

### Test C: FPGA to DAC low-IF BPSK

Goal:

- Prove real modulated carrier generation.

Transmit:

```text
Preamble: 0x55 repeated
Payload:  "HELLO FPGA BPSK"
```

Expected scope result:

- IF sine wave with 180-degree phase flips.

Expected SDR/spectrum result at IF:

- Signal centered at chosen IF.
- Bandwidth related to symbol rate.

### Test D: Upconvert to 2.4 GHz

Goal:

- Prove IF-to-RF translation.

Expected SDR/spectrum result:

- Signal near 2.4 GHz.
- Image and LO leakage visible before filtering.
- Cleaner desired signal after the 2.4 GHz band-pass filter.

---

## Software and HDL That Must Be Built

## Minimum FPGA HDL

### 1. Clocking Module

Purpose:

- Generate the DAC sample clock.
- Generate slower enables for symbol timing.

### 2. DAC Interface Module

Purpose:

- Register parallel sample data.
- Meet DAC setup/hold timing.
- Provide clock to DAC if required.

### 3. Test Pattern Generator

Purpose:

- Output constant value, ramp, square wave, or sine wave.

### 4. BPSK Bit Source

Purpose:

- Generate repeated 1010 pattern.
- Generate PRBS sequence.
- Later, read payload bytes from a FIFO.

### 5. Symbol Mapper

Purpose:

- Convert bits to +1/-1 symbols.

### 6. NCO / Carrier Generator

Purpose:

- Generate low-IF sine wave samples.

### 7. BPSK Modulator

Purpose:

- Apply 0-degree or 180-degree phase shift to the carrier.
- Implemented as carrier sign inversion.

### 8. Optional FIR Pulse-Shaping Filter

Purpose:

- Control bandwidth.
- Reduce sidelobes.

Do this after the unshaped version works.

---

## Minimum Host Software

The first version can avoid host streaming entirely. Let the FPGA generate test patterns internally.

Later host-side tools can include:

### 1. Bitstream Load Script

Purpose:

- Program the FPGA.

### 2. Register Control Script

Purpose:

- Select waveform mode.
- Set symbol rate.
- Set IF frequency.
- Select PRBS or packet mode.

### 3. Payload Sender

Purpose:

- Send bytes to FPGA FIFO.
- Example payload: `HELLO FPGA BPSK`.

### 4. Test Logger

Purpose:

- Record sample rate, IF frequency, symbol rate, LO frequency, filter used, observed spectrum, and screenshots.

---

## Optional Pico Role

The Pi Pico does not need to generate high-speed samples. That is the FPGA's job.

Good Pico responsibilities:

- Configure FPGA registers.
- Send packet payloads.
- Control test modes.
- Monitor voltage/current/temperature.
- Act as flight-style IHU controller.
- Enable/disable RF chain power.

Avoid making the Pico push real-time DAC samples. That defeats the purpose of using the FPGA.

---

## Suggested First FPGA Block Diagram

```text
                 ┌────────────────┐
                 │ clock/reset     │
                 └───────┬────────┘
                         v
                 ┌────────────────┐
                 │ mode control    │
                 └───────┬────────┘
                         v
 ┌───────────┐     ┌──────────────┐     ┌────────────┐
 │ PRBS /    │ --> │ BPSK mapper  │ --> │ sign select│
 │ packet ROM│     └──────────────┘     └─────┬──────┘
 └───────────┘                                │
                                              v
                                      ┌──────────────┐
                                      │ NCO sine ROM │
                                      └──────┬───────┘
                                             v
                                      ┌──────────────┐
                                      │ DAC formatter│
                                      └──────┬───────┘
                                             v
                                      ┌──────────────┐
                                      │ DAC pins     │
                                      └──────────────┘
```

---

## Data to Transmit First

Use increasingly realistic test data.

### Level 1: Alternating bits

```text
1010101010101010...
```

Good for seeing frequent phase reversals.

### Level 2: Repeating byte pattern

```text
0x55 0x55 0x55 0x55
```

Same as alternating bits, but packet-like.

### Level 3: Sync word and payload

```text
Preamble: 0x55 0x55 0x55 0x55
Sync:     0x1A 0xCF 0xFC 0x1D
Payload:  HELLO FPGA BPSK
```

### Level 4: PRBS

Use a PRBS sequence for BER-like testing later.

---

## What Success Looks Like

### On the logic analyzer

- Stable DAC sample clock.
- Parallel sample bus changes correctly.
- Symbol timing matches design.

### On the oscilloscope before DAC filtering

- Sine wave mode produces a sine-like output.
- Baseband BPSK produces two levels.
- Low-IF BPSK produces phase reversals.

### On the oscilloscope after IF filter

- Cleaner sine/IF waveform.
- Reduced high-frequency switching artifacts.

### On SDR/spectrum analyzer at IF

- Signal centered at selected IF.
- Bandwidth approximately related to symbol rate.
- Unshaped BPSK has visible sidelobes.
- Pulse-shaped BPSK has cleaner bandwidth.

### On SDR/spectrum analyzer after mixer

- Signal appears near target S-band frequency.
- LO leakage may be visible.
- Image frequency may be visible before filtering.
- Desired 2.4 GHz signal should dominate after RF band-pass filter.

---

## Major Risks

### 1. DAC Interface Timing

High-speed parallel DACs require clean timing. The FPGA must meet setup and hold requirements.

Mitigation:

- Start at lower sample rates.
- Use registered outputs.
- Keep wiring short.
- Use a proper PCB or very careful interconnect for higher speeds.

### 2. Signal Integrity

At tens or hundreds of MSPS, breadboards become problematic.

Mitigation:

- Avoid solderless breadboards.
- Use short wires or controlled interconnects.
- Move to a small PCB once the pinout is known.

### 3. DAC Output Conditioning

DAC modules may need output transformers, reconstruction filters, biasing, or 50 ohm matching.

Mitigation:

- Study the DAC module schematic.
- Scope the output before adding mixer.
- Add IF filter before mixer.

### 4. Mixer Drive Levels

Mixers expect certain LO and IF power levels.

Mitigation:

- Use attenuators.
- Check mixer datasheet levels.
- Start with low power.
- Verify with spectrum analyzer if available.

### 5. RF Filtering

Without filtering, mixer outputs are messy.

Mitigation:

- Treat the first RF output as a lab signal only.
- Use a 2.4 GHz band-pass filter before any antenna.
- Prefer cabled tests into an SDR with attenuation.

---

## Practical Development Order

1. Confirm IceZero toolchain works.
2. Blink LEDs and output a slow test clock.
3. Output a parallel counter to a logic analyzer.
4. Connect DAC and output DC midscale.
5. Output ramp waveform.
6. Output sine waveform.
7. Output two-level baseband BPSK.
8. Output low-IF BPSK.
9. Add simple packet ROM.
10. Add PRBS generator.
11. Add host/Pico control interface.
12. Add IF filter.
13. Add mixer with bench LO.
14. Add 2.4 GHz filter.
15. Observe on SDR/spectrum analyzer.
16. Only after all of that, consider over-the-air tests.

---

## Minimal Version Worth Building

The minimum successful demonstration is:

```text
IceZero FPGA → DAC → scope
```

With the FPGA generating:

```text
5 MHz low-IF BPSK
100 ksym/s symbol rate
Payload: repeating 0x55, then HELLO FPGA BPSK
```

If you can show the low-IF carrier phase flipping by 180 degrees on the scope, you have proven the most important part:

> The FPGA is generating its own BPSK waveform.

Everything after that is RF translation and cleanup.

---

## Longer-Term Version

Once the simple chain works, the project can grow toward a more complete CubeSat SDR payload:

```text
Linux or Pico controller
        ↓
FPGA packet/framing/modulation
        ↓
DAC low-IF generation
        ↓
Mixer/upconverter
        ↓
S-band RF filtering
        ↓
PA / attenuator / antenna interface
```

Later additions:

- QPSK mode.
- Root-raised-cosine pulse shaping.
- Forward error correction.
- AX.25-like framing or custom packet format.
- Telemetry beacon mode.
- Receive chain with ADC.
- Closed-loop BER testing.
- Ground station GNU Radio receiver.

---

## One-Sentence Summary

This project builds the front half of a CubeSat-style SDR transmitter: FPGA-generated BPSK, DAC conversion to analog IF, and later mixer-based translation to S-band for observation and experimentation.
