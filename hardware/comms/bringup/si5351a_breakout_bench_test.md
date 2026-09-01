# Si5351A Breakout Bench Test — CLK1 Power Verification

Procedure for verifying Si5351A CLK1 LO drive level for the
comms board RX chain, using the **Adafruit 5640 Si5351A breakout** and
a **Pico 2** as the I2C host.

**Goal:** confirm that CLK1 at 145.9 MHz can deliver ≥ +5 dBm into 50 Ω,
which is what the ADE-1+ passive mixer wants for proper conversion loss.
Also characterize the 3rd harmonic at 437.7 MHz to confirm the 5-pole LO
LPF design is adequate.

See companion docs:
- [`../design/rx_mixer_trade_study.md`](../design/rx_mixer_trade_study.md) — why this measurement matters
- [`../design/altium_comms_schematic.md`](../design/altium_comms_schematic.md) — Sheet 4 Section B.2 (LO LPF design)
- [`../../../docs/research/`](../../../docs/research/) — TinySA / NanoVNA tool inventory

---

## Part 1 — CircuitPython code for Pico 2 + Adafruit 5640

Easiest path is CircuitPython since Adafruit publishes a library for
this exact chip.

### Setup

1. Flash CircuitPython for RP2350: https://circuitpython.org/board/raspberry_pi_pico2/
2. Drop `adafruit_si5351.mpy` from the CircuitPython library bundle into
   `/lib/` on the `CIRCUITPY` drive
3. Wire it up:

```
Pico 2 GP0  (SDA) ──→ Adafruit 5640 SDA
Pico 2 GP1  (SCL) ──→ Adafruit 5640 SCL
Pico 2 3V3        ──→ Adafruit 5640 VIN
Pico 2 GND        ──→ Adafruit 5640 GND
```

Or use a STEMMA QT cable if your Pico 2 carrier has a QT connector.

### code.py

```python
import time
import board
import busio
import adafruit_si5351

# I2C0 on default Pico pins
i2c = busio.I2C(scl=board.GP1, sda=board.GP0)
while not i2c.try_lock():
    pass
print("I2C devices:", [hex(a) for a in i2c.scan()])
i2c.unlock()
# Expect to see 0x60 (Si5351A address)

si = adafruit_si5351.SI5351(i2c)

# Target: CLK1 = 145.9 MHz exactly
# Strategy: PLL_A = 25 MHz * (35 + 2/125) = 875.4 MHz
#           CLK1  = PLL_A / 6 = 145.9 MHz
# Integer-only multisynth divider keeps phase noise clean.

XTAL_FREQ_HZ    = 25_000_000
TARGET_FREQ_HZ  = 145_900_000
MULTISYNTH_DIV  = 6
PLL_FREQ_HZ     = TARGET_FREQ_HZ * MULTISYNTH_DIV  # = 875_400_000

mult_int = PLL_FREQ_HZ // XTAL_FREQ_HZ                       # = 35
mult_frac_num = (PLL_FREQ_HZ - mult_int * XTAL_FREQ_HZ)      # = 400_000
# Reduce 400000/25000000 = 16/1000 = 2/125
mult_frac_den = XTAL_FREQ_HZ // 200_000                      # = 125
mult_frac_num = mult_frac_num // 200_000                     # = 2

print(f"PLL A = 25 MHz * ({mult_int} + {mult_frac_num}/{mult_frac_den})")
print(f"      = {(mult_int + mult_frac_num/mult_frac_den) * XTAL_FREQ_HZ / 1e6:.4f} MHz")

si.pll_a.configure_fractional(mult_int, mult_frac_num, mult_frac_den)
si.clock_1.configure_integer(si.pll_a, MULTISYNTH_DIV)

# Force CLK1 drive strength to 8 mA (highest).
# The library exposes this on recent versions; if not, we poke the
# register directly. CLK1_CTL is register 0x11, bits 1:0 = IDRV.
try:
    si.clock_1.set_drive_strength(adafruit_si5351.DRIVE_8MA)
    print("Set drive via library API")
except AttributeError:
    # Fallback: direct register write
    CLK1_CTL_ADDR = 0x11
    while not i2c.try_lock():
        pass
    i2c.writeto(0x60, bytes([CLK1_CTL_ADDR]))
    rx = bytearray(1)
    i2c.readfrom_into(0x60, rx)
    new_ctl = (rx[0] & 0xFC) | 0x03  # IDRV = 11 = 8mA
    i2c.writeto(0x60, bytes([CLK1_CTL_ADDR, new_ctl]))
    i2c.unlock()
    print(f"Set drive via register write: 0x{new_ctl:02X}")

# Enable outputs
si.outputs_enabled = True
si.clock_1.enabled = True

print(f"CLK1 reports: {si.clock_1.frequency / 1e6:.4f} MHz")
print("CLK1 should now be on. Hook up the TinySA.")

# Optional: A/B sweep of drive strengths.
# Flip the loop guard to True to cycle through and watch the TinySA
# power change.
while False:
    for drive in (adafruit_si5351.DRIVE_2MA,
                  adafruit_si5351.DRIVE_4MA,
                  adafruit_si5351.DRIVE_6MA,
                  adafruit_si5351.DRIVE_8MA):
        si.clock_1.set_drive_strength(drive)
        print(f"Drive = {drive}")
        time.sleep(10)
```

### Sanity checks before trusting the reading

- The I2C scan should print `['0x60']` — if not, the breakout isn't
  talking. Check wiring before going further.
- The "PLL A =" print should show 875.4000 MHz — if it shows something
  else, the multiplier math is wrong (or the library on disk is a
  version with a different `configure_fractional` signature).
- `si.clock_1.frequency` should report ~145900000 Hz.

---

## Part 2 — Does the breakout circuit match the planned PCB?

**Short answer:** for power measurement purposes, yes — with one
caveat that you can compensate for.

### Schematic comparison

| Item | Adafruit 5640 breakout | Planned project PCB | Affects RF measurement? |
|---|---|---|---|
| Si5351A IC | Same chip, same package | Same chip | No diff |
| 25 MHz crystal | Onboard, ~10pF caps | Y1 + C4/C5 (10pF) | No diff |
| VDD/VDDO bypass | 100nF only (typical Adafruit) | 100nF + 10µF | Negligible at 145 MHz |
| I2C pull-ups | 10 kΩ (typical) | 4.7 kΩ | None (DC bus only) |
| Power input | VIN → onboard 3.3V LDO | Direct +3V3 from EPS | Trivial — both deliver ~3.3V |
| Output coupling | **Direct from chip pin to SMA**, no DC block, no series R | 100nF DC block (C7) + 33Ω series (R4) | **Yes — this is the one that matters** |
| Output trace impedance | Short trace, uncontrolled but short → ~50Ω effective at 145 MHz | Designed 50Ω microstrip | Negligible at 145 MHz with short traces |

### The one real difference: that series resistor

The breakout has the CLK1 pin connected almost directly to an SMA —
no DC block, no series resistor. The planned PCB has a **33 Ω series
resistor (R4)** between the Si5351A pin and the output.

That series resistor forms a voltage divider with the 50 Ω load.
Working through the math (treating the Si5351A as a voltage source
with ~25–50 Ω effective output impedance):

| Configuration | Expected fundamental power | What the TinySA shows |
|---|---|---|
| Breakout direct (no R4) | +10 to +13 dBm | Direct reading |
| PCB with R4 = 33 Ω | 2.5 to 3 dB lower | Subtract ~3 dB from breakout reading |
| PCB with R4 = 0 Ω | Same as breakout | Equal to breakout reading |

### Measurement plan

1. **Measure the breakout direct.** That's the baseline — equivalent to
   the PCB with R4 = 0 Ω.
2. **To simulate R4 = 33 Ω**, either:
   - **(a)** Solder a 33 Ω resistor in series at the SMA pigtail (one
     cheap 0603 + a couple of pads on a tiny chunk of perfboard, in
     line before the BECEN DC block), or
   - **(b)** Use a characterized **Nooelec 3 dB pad** (-2.76 dB @ 144 MHz)
     in series before the existing 20 dB pad. Not exactly the same
     topology (the pad is a 50Ω-preserving pi network; R4 alone isn't)
     but the *power drop* it imposes is within ~0.5 dB of what R4
     would cause.
3. **What you actually want to know** can come from just measurement
   (1): if the breakout direct reads ≥ +9 dBm at the fundamental, the
   PCB with R4 = 33 Ω will hit the ≥ +5 dBm target with margin. If the
   breakout reads less than ~+8 dBm, populate R4 as 0 Ω on the PCB.

### Two things that *would* invalidate the measurement

1. **A long un-shielded jumper from the breakout SMA to the TinySA.**
   Anything more than a foot of unshielded coax at 145 MHz starts to
   pick up ambient and radiate, which biases the measurement. Stick to
   shielded SMA jumpers, kept short.

2. **The breakout's SMA edge-launch parasitics differing from the
   PCB's edge-launch** — but at 145 MHz this is sub-1 dB at worst.
   Negligible compared to what other layout differences contribute in
   the final circuit.

### Harmonic content (the *more* important measurement)

This part transfers **cleanly** from breakout to PCB. Square-wave
harmonic ratios are intrinsic to the Si5351A's output buffer — they
don't depend on R4 or any of the differences above. Whatever 3rd-
harmonic-to-fundamental ratio measured on the breakout (probably -10
to -15 dB) is what the PCB will show. That's what tells you whether
the 5-pole LO LPF design is adequate.

---

## TL;DR

- Code above gets CLK1 to 145.9 MHz @ 8 mA on the breakout
- Breakout measurement is valid; subtract ~3 dB from the breakout
  reading to predict the PCB with R4 = 33 Ω
- Harmonic ratios transfer 1:1, no correction needed
- The only way to mess this up is wiring sloppiness — use the TinySA
  setup procedure (Nooelec 20 dB + BECEN DC block + short SMA jumpers,
  full procedure documented separately in the LO drive verification
  walk-through)
