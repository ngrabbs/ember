# TX Chain Bring-Up Test Plan

## Stage 1: Si5351A Clock Generator

### Objective
Verify Si5351A generates correct LO frequencies for both TX and RX chains.

### Equipment Required
- Raspberry Pi Pico 2 (RP2350)
- Adafruit Si5351A STEMMA QT breakout (SMA on CLK1)
- TinySA or spectrum analyzer
- Oscilloscope (optional, for time-domain verification)
- SMA cables, DC block (optional)
- USB cable for Pico serial console

### Wiring
| Pico Pin | Si5351A Pin | Function |
|----------|-------------|----------|
| GP4 (pin 6) | SDA | I2C data |
| GP5 (pin 7) | SCL | I2C clock |
| 3V3 (pin 36) | VIN | Power |
| GND (pin 38) | GND | Ground |

### Firmware
`firmware/comms/drivers/si5351a_bringup.uf2`

Build:
```
cd firmware/comms/drivers
mkdir -p build && cd build
cmake -DPICO_SDK_PATH=/opt/pico-sdk -DPICO_BOARD=pico2 ..
make -j4
```

Copy `si5351a_bringup.uf2` to the Pico 2 (hold BOOTSEL, plug USB, drag file).

### Serial Console
Connect at 115200 baud (USB CDC). Commands:
- `0` / `1` — toggle CLK0 / CLK1 on/off
- `+` / `-` — shift CLK0 by 100 kHz
- `r` — reset to default frequencies
- `s` — print current status

### Test Procedure

#### 1.1 — I2C Communication
- [ ] Flash firmware, open serial console
- [ ] Confirm banner prints and "Si5351A initialized successfully!" appears
- [ ] If init fails: check wiring, confirm 3.3V on VIN pad, verify I2C address 0x60

#### 1.2 — CLK1 Output (RX LO)
- [ ] Connect TinySA to CLK1 SMA output
- [ ] Verify peak at **145.900 MHz**
- [ ] Expected level: approximately **-6 to +10 dBm** (depends on cable loss)
- [ ] Toggle CLK1 off (`1` command), confirm peak disappears
- [ ] Toggle CLK1 on, confirm peak returns

#### 1.3 — CLK0 Output (TX Carrier)
- [ ] Probe CLK0 header pin with oscilloscope
- [ ] Verify square wave at **145.667 MHz** (~6.86 ns period)
- [ ] Or: with TinySA on CLK1 SMA, CLK1 off, look for weaker radiated CLK0
  peak near 145.667 MHz (expect ~ -30 dBm due to board coupling, not conducted)

#### 1.4 — Frequency Stepping
- [ ] Press `+` several times, confirm CLK0 frequency increases by 100 kHz steps
- [ ] Press `-` to decrease, confirm movement tracks
- [ ] Verify on TinySA or scope that the output frequency matches `s` status readout
- [ ] Press `r` to reset, confirm return to 145.667 MHz

#### 1.5 — Harmonics (Preview for Tripler)
- [ ] With CLK0 or CLK1 active, scan TinySA up to 500 MHz
- [ ] Look for 3rd harmonic near **437 MHz** (CLK0) or **437.7 MHz** (CLK1)
- [ ] These will be weak (square wave harmonics roll off), but confirm they exist
- [ ] This previews what the frequency tripler will select and amplify

### Pass Criteria
- Both clocks output correct frequencies within 1 kHz
- Enable/disable toggles work (output appears/disappears)
- Frequency stepping produces expected shifts
- No spurious outputs within 10 dB of the carrier in the 100-200 MHz range

---

## Stage 2: Frequency Tripler (2N3904)

### Objective
Verify 3rd harmonic generation at 437 MHz from 145.667 MHz input.

### Equipment Required
- Si5351A running CLK0 at 145.667 MHz (from Stage 1)
- 2N3904 NPN transistor
- Bias resistors (values TBD — see design docs)
- 220 nH RFC inductor
- RF prototype board
- TinySA or spectrum analyzer
- NanoVNA (for filter tuning)
- SMA connectors and cables

### Test Procedure
_To be filled in when tripler circuit is assembled._

- [ ] Build class-C biased 2N3904 tripler on prototype board
- [ ] Connect Si5351A CLK0 output to tripler input
- [ ] Measure output spectrum on TinySA
- [ ] Verify 3rd harmonic at 437 MHz
- [ ] Measure fundamental (145.67 MHz) and 2nd harmonic (291.3 MHz) suppression
- [ ] Document power levels at each harmonic

---

## Stage 3: 437 MHz Bandpass Filter

_To be filled in after tripler validation._

---

## Stage 4: BPSK Modulator (74LVC1G86)

_To be filled in after XOR gate procurement._
