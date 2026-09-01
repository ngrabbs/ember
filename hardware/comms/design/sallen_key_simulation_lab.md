# Sallen-Key LPF Simulation Lab — LTspice

## Objective
Simulate the baseband Sallen-Key low-pass filter from the RX chain to verify:
- Cutoff frequency is ~3.3 kHz (passes 1200/2200 Hz AFSK tones)
- Rolloff rejects mixer products and out-of-band noise
- Filter shape matches expected 2nd-order Butterworth response

## Circuit to Build

Open LTspice. File → New Schematic.

### Step 1 — Place the Op-Amp

1. Click the component button (AND gate icon on toolbar, or press F2)
2. In the search box, type `UniversalOpamp2`
3. Place it in the middle of your schematic
4. This is a generic ideal op-amp — perfect for filter design since we
   care about the filter behavior, not op-amp quirks

### Step 2 — Place Resistors and Capacitors

Press F2, search for `res` (resistor) and `cap` (capacitor). You need:
- 2x resistors (R1, R2)
- 2x capacitors (C1, C2)

Arrange them like this:

```
              R1              R2
IN ──/\/\/──┬──/\/\/──┬──→ IN+ (pin 3)
            │         │
           C1        C2         OUT (pin 1)
            │         │           │
            └─── OUT ─┘          IN- (pin 2) ←┘
                 GND
```

Wait — let me be more explicit for LTspice placement:

1. Place R1 horizontally. Left pin is input, right pin goes to a junction.
2. Place R2 horizontally. Left pin connects to R1's right pin, right pin
   goes to the op-amp IN+ (non-inverting input).
3. Place C1 vertically. Top pin connects to the junction between R1 and R2.
   Bottom pin connects to the op-amp output.
4. Place C2 vertically. Top pin connects to the junction between R2 and IN+.
   Bottom pin connects to GND.

### Step 3 — Set Component Values

Right-click each component to set its value:
- R1: `22k`
- R2: `22k`
- C1: `2.2n`
- C2: `2.2n`

### Step 4 — Wire the Op-Amp Feedback

Wire the op-amp output (OUT) directly to the inverting input (IN-).
This sets unity gain.

Also wire the op-amp output to the bottom of C1 (the feedback cap).

### Step 5 — Add Power Supply

The UniversalOpamp2 needs supply rails.

1. Press F2, search for `voltage`. Place two voltage sources.
2. First voltage source: positive terminal up, set to `3.3`. Connect
   positive terminal to a net labeled `V+`, negative to GND.
3. Second voltage source: This is for the negative rail. For single-supply
   operation, just connect V- to GND.

To connect the supply to the op-amp:
- Right-click the op-amp → select "V+" pin → type the net name `V+`
- Or: press F4 (net label), type `V+`, place it on the op-amp's positive
  supply pin. Do the same with GND for V-.

Actually, the easier way:
1. Right-click the UniversalOpamp2 symbol
2. Set `Avol` to `1Meg` (open loop gain)
3. Set `GBW` to `10Meg` (gain-bandwidth, MCP6022 is 10 MHz)
4. The supply pins should have labels — connect V+ to 3.3V, V- to GND

### Step 6 — Add Input Source

For AC analysis, you need a voltage source at the input.

1. Press F2, search for `voltage`. Place it at the input (left side of R1).
2. Right-click the voltage source
3. Set DC value to `1.65` (mid-supply bias for single-supply)
4. Click "Advanced" → set AC Amplitude to `1`
5. Connect the negative terminal to GND

### Step 7 — Add Ground

Press G to place a GND symbol. Connect it to:
- Bottom of C2
- Bottom of input voltage source
- Bottom of power supply voltage sources
- V- pin of op-amp

### Step 8 — Add Output Label

Press F4 (net label). Type `OUT`. Place it on the wire at the op-amp output.
Do the same for the input — label it `IN`.

---

## Simulation 1: AC Analysis (Frequency Response)

This is the most important test — it shows you the filter's frequency
response (gain vs frequency).

### Run It

1. Simulate → Edit Simulation Cmd (or press S)
2. Click the "AC Analysis" tab
3. Set:
   - Type of sweep: **Decade**
   - Number of points per decade: **100**
   - Start frequency: **10** (Hz)
   - Stop frequency: **100k** (100,000 Hz)
4. Click OK. LTspice places a `.ac` directive on your schematic.
5. Click the Run button (running man icon, or press the play button)

### Read the Results

1. After simulation runs, click on the `OUT` net label (or the wire).
   LTspice plots the frequency response.
2. You should see two plots:
   - **Top: Magnitude (dB)** — should be flat (0 dB) until ~3.3 kHz,
     then roll off
   - **Bottom: Phase (degrees)** — should start at 0° and drop to -180°

### What to Look For

| Frequency | Expected Gain | Why |
|-----------|--------------|-----|
| 100 Hz | ~0 dB (flat) | Well below cutoff, signal passes |
| 1200 Hz | ~0 dB (flat) | AFSK mark tone — must pass |
| 2200 Hz | ~-1 to -2 dB | AFSK space tone — should mostly pass |
| 3300 Hz | ~-3 dB | Cutoff frequency (half power point) |
| 10 kHz | ~-20 dB | Above cutoff, being rejected |
| 33 kHz | ~-40 dB | 10x above cutoff, 2nd order = -40 dB/decade |

The -3 dB point should land near **3.3 kHz**. The formula is:
```
fc = 1 / (2π × R × C) = 1 / (2π × 22000 × 2.2e-9) = 3,289 Hz
```

### Verify the Rolloff Slope

A 2nd-order filter rolls off at **-40 dB/decade** (or -12 dB/octave).
- At 33 kHz (10× cutoff): should be about -40 dB
- At 330 kHz (100× cutoff): should be about -80 dB

If your rolloff is only -20 dB/decade, something is wrong with the
circuit — you might have a cap disconnected and it's acting as a
1st-order RC filter.

---

## Simulation 2: Transient Analysis (Time Domain)

This shows actual waveforms passing through the filter — makes it
concrete and visual.

### Set Up AFSK Input

Replace the AC source with a more interesting signal. Right-click the
input voltage source → Advanced:

1. Select "SINE" as the function
2. Set:
   - DC offset: `1.65` (mid-supply)
   - Amplitude: `0.5`
   - Freq: `2200` (AFSK space tone)
3. Click OK

Or for a more realistic test, use a mixed signal. Delete the voltage
source and place a behavioral source (press F2 → `bv`):
```
V = 1.65 + 0.3*sin(2*pi*1200*time) + 0.3*sin(2*pi*2200*time) + 0.1*sin(2*pi*10000*time)
```
This creates 1200 Hz + 2200 Hz (your AFSK tones) plus a 10 kHz interferer.

### Run It

1. Simulate → Edit Simulation Cmd
2. Click "Transient" tab
3. Set:
   - Stop time: `5m` (5 milliseconds — enough to see several cycles)
   - (leave other fields default)
4. Click OK, then Run

### Read the Results

1. Click the `IN` wire — you'll see the input waveform (messy, three
   frequencies mixed together)
2. Click the `OUT` wire — you should see the output waveform with:
   - 1200 Hz and 2200 Hz tones present (slightly reduced)
   - 10 kHz interferer significantly attenuated

You can overlay both by clicking IN first, then holding Alt and clicking
OUT to plot on the same axes.

---

## Simulation 3: Step Response (Optional)

This shows how the filter responds to a sudden change — useful for
understanding settling time.

1. Change input source to `PULSE`:
   - Vinitial: `1.15`
   - Von: `2.15`
   - Tdelay: `1m`
   - Trise: `1u`
   - Tfall: `1u`
   - Ton: `3m`
   - Tperiod: `10m`
2. Run transient analysis, stop time `5m`
3. The output should show a smooth rise (no ringing for Butterworth)
   with settling time of roughly 1/(2π×fc) ≈ 50 µs

If you see ringing or overshoot, the filter is underdamped. With equal
R and C values (R1=R2, C1=C2) in a unity-gain Sallen-Key, you get a
Butterworth response (Q = 0.707), which should have minimal overshoot
(~4%). Significant ringing means a wiring error.

---

## Experiments to Try

Once the basic sim works, try these to build intuition:

### A. Change Cutoff Frequency
- Double both caps to 4.7 nF → cutoff drops to ~1.5 kHz
  (should attenuate the 2200 Hz tone noticeably)
- Halve both caps to 1 nF → cutoff rises to ~7.2 kHz
  (10 kHz interferer gets through more)

### B. What If C1 is Disconnected from Output?
- Move C1's bottom terminal from OUT to GND
- Run AC analysis — you should see -20 dB/decade rolloff instead
  of -40 dB/decade (it's now just a passive 2nd-order RC, not a
  Sallen-Key)
- This demonstrates why the C1 feedback to the output matters

### C. Swap to MCP6022 SPICE Model
If you want to verify with the real op-amp model:
1. Download MCP6022 SPICE model from Microchip's website
2. In LTspice: Edit → Add SPICE Model, import the .mod file
3. Replace UniversalOpamp2 with the MCP6022 subcircuit
4. Rerun AC analysis — results should be nearly identical below
   1 MHz (op-amp non-idealities only matter near GBW)

### D. Add the U7B Gain Stage
After the filter, add:
- 100 nF AC coupling cap
- 10k/10k bias divider to 1.65V
- Non-inverting amp with Rf=100k, Rg=10k (gain = 11)
- Run transient sim with AFSK input to see the full baseband chain

---

## Checklist Before Moving On

- [ ] AC analysis shows -3 dB at ~3.3 kHz
- [ ] Rolloff is -40 dB/decade (confirms 2nd-order behavior)
- [ ] 1200 Hz tone passes with < 1 dB loss
- [ ] 2200 Hz tone passes with < 3 dB loss
- [ ] Transient sim shows AFSK tones pass, 10 kHz rejected
- [ ] Step response shows smooth rise with minimal overshoot

If all checks pass, your Sallen-Key filter is correct and ready for
the PCB.
