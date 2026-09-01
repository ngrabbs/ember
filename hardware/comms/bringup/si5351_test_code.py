# CircuitPython test code for Adafruit 5640 Si5351A breakout on Pico 2.
# Outputs 145.9 MHz on CLK1 at 8 mA drive strength.
# Companion to: hardware/comms/bringup/si5351a_breakout_bench_test.md
# Companion to: hardware/comms/bringup/lo_drive_verification.md

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
# Library API on recent versions; fallback to direct register write.
try:
    si.clock_1.set_drive_strength(adafruit_si5351.DRIVE_8MA)
    print("Set drive via library API")
except AttributeError:
    # Fallback: direct register write
    # CLK1_CTL is register 0x11, bits 1:0 = IDRV
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
# Set ENABLE_DRIVE_SWEEP = True to cycle through all four settings.
ENABLE_DRIVE_SWEEP = False

if ENABLE_DRIVE_SWEEP:
    while True:
        for drive in (adafruit_si5351.DRIVE_2MA,
                      adafruit_si5351.DRIVE_4MA,
                      adafruit_si5351.DRIVE_6MA,
                      adafruit_si5351.DRIVE_8MA):
            si.clock_1.set_drive_strength(drive)
            print(f"Drive setting = {drive}")
            time.sleep(10)
