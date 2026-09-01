# Jetson Orin Nano vs. Original Jetson Nano — Module Compatibility Report

## TL;DR

**A single payload carrier CAN host either module** with the
current pinout (per `payload_carrier_pinmap.md`), provided MODULE_ID
(pin 217) stays tied to GND and VDD_IN stays at 5.0 V. NVIDIA
explicitly designed the Orin Nano as a **pin-compatible upgrade** to
the original Jetson Nano — the Orin Nano datasheet even prints both
signal names side-by-side in its SO-DIMM cross-reference table.

What that means here:

| Feature | Original Nano ($45 used) | Orin Nano ($200+) | Carrier change required? |
|---|---|---|---|
| Mechanical / SO-DIMM connector | Identical | Identical | None |
| Power (5 V VDD_IN, 5 A max) | Identical | Identical | None |
| Power sequencing pins | Identical | Identical | None |
| 3× CSI camera interfaces | Works | Works | None |
| Debug UART (UART1) | Works | Works | None |
| Stack I²C, CAM_I2C, all GPIOs | Works | Works | None |
| USB-2 recovery header | Works | Works | None |
| M.2 Key-E WiFi (over PCIE1) | **Won't enumerate** — no PCIE1 controller on Tegra X1 | Works | None — Nano just sees an empty M.2 slot |
| CAN bus (over CAN_RX/TX pins) | **Not functional** — Tegra X1 has no CAN controller | Works | None — DNP'd for v0.1 anyway |
| Stage-2 ML model performance | ~85× slower (INT8) | Full speed | Smaller model on Nano |
| Software stack | JetPack 4.x / L4T R32 / Ubuntu 18.04 | JetPack 6.x / L4T R36 / Ubuntu 22.04 | **Two parallel firmware images** |

**Recommendation:** keep the carrier as designed. Use $45 Original
Nanos as **bench / development / spare units** for the team to sharpen
ML skills cheaply, then fly an Orin Nano. Don't try to fly the
original Nano — its INT8 inference performance is too thin for the
Stage-2 CNN, and the JetPack 4.x stack is end-of-life.

---

## 1. Source Documents

| Module | Datasheet | Where to get it |
|---|---|---|
| Original Jetson Nano (Tegra X1, Maxwell GPU, 472 GFLOPS FP16) | DS-09366-001 v1.1 | NVIDIA Jetson Download Center — see `hardware/component_datasheets.md` |
| Jetson Orin Nano (Tegra Orin, Ampere GPU, 40 TOPS INT8) | DS-11105-001 v1.1 | `Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf`, this directory |

The Orin Nano datasheet's SO-DIMM Pinout table (page ~50) is the
single best reference for compatibility — it has **two columns side
by side**: "Jetson SODIMM Signal Name" (= what the original Nano calls
the pin) and "Jetson Orin Nano Function" (= what Orin uses it for).
For most pins these are identical strings.

## 2. Mechanical / Electrical

| Property | Original Nano | Orin Nano | Identical? |
|---|---|---|---|
| PCB dimensions | 69.6 × 45 mm | 69.6 × 45 mm | ✅ |
| Connector | 260-pin SO-DIMM, keyed | 260-pin SO-DIMM, keyed | ✅ |
| Mating socket | TE 2309413-1 (or equivalent) | TE 2309413-1 | ✅ |
| Pinout numbering | Top-odd / bottom-even | Top-odd / bottom-even | ✅ |
| VDD_IN nominal | 5.0 V (4.75–5.25 V) | 5.0 V (MODULE_ID = GND) | ✅ |
| VDD_IN max current | 5 A | 5 A | ✅ |
| VDD_IN pins | 251–260 (10 parallel) | 251–260 (10 parallel) | ✅ |
| Operating temp (commercial) | −25 to +80 °C (Tj) | −25 to +80 °C (Tj) | ≈ |
| PMIC_BBAT (pin 235) | 1.65–5.5 V | 1.65–5.5 V | ✅ |

The Orin Nano added a wide-input mode (5–20 V when MODULE_ID = HIGH)
that the original Nano doesn't have. The carrier ties MODULE_ID to GND
on the carrier, so this difference is invisible.

## 3. Pin-by-Pin Compatibility

### 3.1 Pins that are IDENTICAL in function on both modules

All of the following pins do the same thing on both modules. **No
carrier rework needed.**

| Category | Pins | Notes |
|---|---|---|
| Power input | 251–260 (VDD_IN) | 5 V on both |
| Ground | dozens — see DS tables | Identical pattern |
| Power sequencing | 233 (SHUTDOWN_REQ\*), 237 (POWER_EN), 239 (SYS_RESET\*), 240 (SLEEP/WAKE\*), 214 (FORCE_RECOVERY\*), 178 (MOD_SLEEP\*), 235 (PMIC_BBAT) | Same names, same functions, same drive types. Pull-up *values* on SHUTDOWN_REQ\* differ (100 kΩ on Nano, ~5 kΩ on Orin) but the level is the same. |
| CSI camera lanes | CSI0/1/2/3/4 — all clock and data pin numbers identical | The P/N swap on CSI0_D1 / CSI1_D0 exists on both modules (per DG-10931 §10 for Orin; original Nano TRM equivalent). |
| Camera control I²C | 213 (CAM_I2C_SCL), 215 (CAM_I2C_SDA) | 3.3 V open-drain on both, on-module pull-ups present on both |
| Stack I²C (FC) | 185 (I2C0_SCL), 187 (I2C0_SDA) | Identical |
| Secondary I²C | 189/191 (I2C1), 232/234 (I2C2) | Identical |
| USB 2.0 ports | 109/111 (USB0), 115/117 (USB1), 121/123 (USB2) | All three ports on both — used for recovery (USB0) and M.2 BT (USB1) in our design |
| USB 3.0 (USB-SS) | 161/163 (RX), 166/168 (TX) | Original calls it `USBSS_*`, Orin renames to `USBSS0_*` — same pins, same lanes |
| UART1 (Linux console) | 203/205/207/209 | Identical |
| UART2 | 236/238 | Identical |
| UART0 | 99/101/103/105 | Identical |
| SPI0 | 89/91/93/95/97 | Identical |
| SPI1 | 104/106/108/110/112 | Identical |
| I2S0 / I2S1 | 193–199 / 220–226 | Identical |
| Gigabit Ethernet | 184/186/188/190/192/194/196/198/202/204 (MDI + LEDs) | Identical (both have onboard Realtek PHY) |
| Clock outputs | 210 (CLK_32K_OUT) | Identical |
| GPIO00..14 | 87, 118, 124, 126, 127, 128, 130, 206, 208, 211, 212, 216, 218, 228, 230 | All pin numbers and electrical characteristics identical |
| CAM_PWDN / CAM_MCLK | 114, 120 (PWDN); 116, 122 (MCLK) | Identical |
| DisplayPort 0 (4-lane) | 39/41/45/47/51/53/57/59 (data), 88/90/92 (HPD/AUX) | Identical (we leave NC on both) |
| DisplayPort 1 (4-lane) | 63/65/69/71/75/77/81/83 (data), 96/98/100 (HPD/AUX), 94 (HDMI_CEC) | Identical (we leave NC on both) |
| MIPI DSI | 70/72/76/78/82/84 | Identical (we leave NC on both) |
| PCIE0 (×4 lane) | 131/133/134/136/137/139/140/142/148/149/150/151/154/155/156/157/160/162 (data/REFCLK), 180 (CLKREQ), 181 (RST) | Same pins, same function (×4 PCIe). We leave NC on both (no NVMe). |
| PCIE_WAKE\* | 179 | Identical |

### 3.2 Pins that are DIFFERENT (the deal-breakers)

These are the only places where Orin Nano uses pins that the original
Nano doesn't, or where the function changes. **None of them break the
current carrier design** — read each row carefully.

| Pin(s) | Original Nano | Orin Nano | Carrier uses these as… | Conflict? |
|---|---|---|---|---|
| **143, 145** | `RSVD` (reserved, no function) | `CAN_RX`, `CAN_TX` | CAN signals routed to TCAN332 transceiver (DNP for v0.1) | **No** — wired as CAN, harmless on Nano (RSVD), works on Orin |
| **167, 169** | `RSVD` | `PCIE1_RX0_N/P` | M.2 Key-E PCIe RX | **No conflict** — Nano leaves them floating; routing them as PCIe is safe |
| **172, 174** | `RSVD` | `PCIE1_TX0_N/P` | M.2 Key-E PCIe TX | **No conflict** — same as above |
| **173, 175** | `RSVD` | `PCIE1_CLK_N/P` | M.2 Key-E REFCLK | **No conflict** |
| **182, 183** | `RSVD` | `PCIE1_CLKREQ*`, `PCIE1_RST*` | M.2 Key-E control | **No conflict** |
| **217** | hardwired to **GND on the module** | `MODULE_ID` (GND = 5V-only, HIGH = wide-range) | Tied to GND on the carrier | **No conflict** — carrier-side GND tie matches both behaviours |
| **219, 221, 223, 225, 227, 229** | `SDMMC_DAT0..3, SDMMC_CMD, SDMMC_CLK` (SD card interface — onboard SDIO controller exposed) | `PCIE2_RST*, PCIE2_CLKREQ*, PCIE3_RST*, PCIE3_CLKREQ*, PCIE3_CLK_N/P` (control for the extra PCIe controllers, muxed with SDMMC) | **NC on our carrier** | **No conflict** — only an issue if a carrier needed to use SDMMC, which ours doesn't |

That's the complete list of functional differences in the 260-pin
SO-DIMM. Everything else is name-for-name identical.

### 3.3 Functional consequences on the **original Jetson Nano**

If you drop a $45 Original Nano into our carrier:

| Subsystem | Works? | Why / Why not |
|---|---|---|
| Boot from microSD (devkit module) | ✅ | Module-onboard microSD; carrier doesn't touch it |
| All 3 CSI cameras | ✅ | Tegra X1's NVCSI fully supports 3× 2-lane MIPI CSI-2 (12 lanes total available) |
| Camera I²C mux + trigger | ✅ | I²C and GPIO behavior identical |
| Linux console UART | ✅ | UART1 same pins, same 1.8 V CMOS |
| USB recovery (USB0) | ✅ | Tegra X1 recovery mode is similar — held LOW on FORCE_RECOVERY\* at SYS_RESET\* release |
| Stack I²C ↔ IHU | ✅ | I2C0 same pins |
| Stack +5V buck disable | ✅ | PAYLOAD_EN works the same |
| Fault propagation (SHDN_REQ → 74LVC1G07 → H2.47) | ✅ | Buffer doesn't care which module is asserting |
| Mux reset translator | ✅ | GPIO07 same pin |
| M.2 Key-E WiFi (RTL8822CE on PCIE1) | ❌ | Original Nano has no PCIE1 controller (pins 167/169/172-175/182/183 are RSVD). The card physically seats but won't enumerate. lspci will show no devices. |
| CAN bus | ❌ | Tegra X1 has no integrated CAN controller. Wired pins are dead. (DNP for v0.1 anyway.) |
| Stage-2 ML wildfire CNN | ⚠️ | Runs, but ~85× slower on INT8 workloads — likely too slow for the planned model. Smaller model required. |

If you drop a $200+ Orin Nano into the same carrier:

- Everything works as designed in `payload_carrier_pinmap.md` rev 0.3
  and `altium_payload_schematic_guide.md` rev 0.1.

## 4. Compute / ML Performance Asymmetry

| Metric | Original Nano | Orin Nano | Ratio |
|---|---|---|---|
| CPU | 4× ARM Cortex-A57 @ 1.43 GHz | 6× ARM Cortex-A78AE @ 1.5 GHz | ~3–4× |
| GPU | 128 CUDA cores, Maxwell | 1024 CUDA cores + 32 Tensor cores, Ampere | ~8× compute, much more for tensor workloads |
| ML inference (INT8) | ~0.47 TOPS (FP16 only — no INT8 dedicated path) | 40 TOPS | **~85×** |
| RAM | 4 GB LPDDR4 | 8 GB LPDDR5 | 2× |
| TDP / max power mode | 5 W or 10 W (MAXN) | 7 W or 15 W (MAXN) | ~1.5× |
| Storage | µSD or 16 GB eMMC (variant) | µSD (devkit) or NVMe via PCIE0 ×4 | Orin gets fast SSD path |

For the wildfire mission's Stage-2 CNN, the Original Nano
*can* run TensorFlow Lite or ONNX models, but realistic frame-rate
targets fall to ~1 fps for anything beyond MobileNet-class. Orin Nano
comfortably runs YOLO-class object detection at 10+ fps on the same
3-channel input.

## 5. Software Compatibility — the Hidden Cost

This is the part that's often understated.

| | Original Nano | Orin Nano |
|---|---|---|
| Latest JetPack | **4.6.x (EOL April 2024 for security updates)** | 6.x (current) |
| L4T (Linux for Tegra) | R32 series | R36 series |
| Ubuntu base | 18.04 LTS (EOL May 2023) | 22.04 LTS |
| Kernel | 4.9.x | 5.15.x |
| CUDA | 10.2 | 12.2 |
| TensorRT | 7.x / 8.0 | 8.6+ |
| Camera driver framework | Argus + V4L2, libcamera support spotty | Argus + V4L2 + libcamera (current) |
| Python ML library compatibility | Pinned to old TensorFlow / PyTorch | Modern versions |

A model trained and deployed for the Orin Nano **will not run as-is**
on the Original Nano. The team would maintain two parallel
firmware/software stacks, with different CUDA versions, different
camera drivers, and different ML runtimes. **This is the real reason
not to fly the original Nano**, even though the carrier supports it.

## 6. Recommended Strategy

Given the cost gap ($45 vs $200+), the realistic plan is:

1. **Flight unit: Orin Nano.** Better ML performance, supported
   software stack, longer product lifecycle.
2. **Ground / bench / EDU units: 2–3× Original Jetson Nanos.** Hand
   them to team members who want to sharpen Linux + ML skills.
   Carrier accepts them with the M.2 socket disabled and CAN ignored.
3. **Algorithm development:** prototype the Stage-1 spectral-ratio
   detector on the Original Nano (it's pure image math — fast
   enough). Develop the Stage-2 CNN on Orin Nano hardware from the
   start; do not waste time porting an Orin model back to L4T R32.
4. **Sparing / EDU outreach:** if the program later wants to ship
   "comparable" hardware to a high school robotics club or a
   public demo, the original-Nano version is the cheap variant.

### Concrete carrier changes needed to support both modules

**None.** The carrier as currently specified
(`payload_carrier_pinmap.md` rev 0.3) is already module-agnostic
within these compatibility limits. Specifically:

- ✅ MODULE_ID (pin 217) is tied to GND on the carrier
- ✅ VDD_IN is held to 5.0 V (no wide-range mode)
- ✅ The pins that differ in function (CAN, PCIE1, SDMMC/PCIE2-3) are
  either NC or used for features (CAN, M.2 WiFi) whose absence on
  Original Nano is acceptable
- ✅ All CSI cameras work on both modules
- ✅ All control / sequencing signals work on both modules

### What WOULD break compatibility (don't do these)

- **Routing SDMMC pins 219–229 to an external SD card socket on the
  carrier.** Works on Original Nano, doesn't work on Orin (those pins
  are PCIE2/3 control on Orin).
- **Driving MODULE_ID (pin 217) HIGH on the carrier** to enable Orin
  wide-input mode. Would conflict with the Original Nano's on-module
  GND tie — possibly drawing current through the Tegra die. Leave it
  tied to GND.
- **Skipping the PCIE1 AC coupling caps** on the host TX side because
  "the original Nano doesn't need them." Orin Nano *requires* them.

## 7. Things This Report Does NOT Cover

- **Thermal differences.** Orin Nano has a different heatspreader
  footprint than original Nano. Either module needs a chassis-bonded
  thermal solution; mechanical interface drawings differ slightly.
- **Software porting effort estimates.** A separate exercise.
- **The Jetson Nano 2GB variant** (P3448-0003) which has a slightly
  different memory bus but otherwise the same SO-DIMM pinout — same
  conclusions apply.
- **Production EOL status.** As of 2026-05, the Original Jetson Nano
  is no longer manufactured by NVIDIA; supply is secondary-market only
  (eBay, surplus). Reliability for flight is therefore uncertain — bench
  use only.

## 8. References

- NVIDIA Jetson Nano Datasheet (DS-09366-001 v1.1) — pinout table
  pp. 38–41, signal descriptions pp. 16–35
- NVIDIA Jetson Orin Nano Series Datasheet (DS-11105-001 v1.1) —
  SO-DIMM cross-reference pp. 50–53 (the two-column compatibility
  table is the single best resource)
- NVIDIA Jetson Orin NX / Orin Nano Design Guide (DG-10931-001 v1.1)
  — power sequencing §6, MIPI CSI lane swap notes §10
- `payload_carrier_pinmap.md` rev 0.3 — current carrier pin
  allocations
- `altium_payload_schematic_guide.md` rev 0.1 — current schematic
  organisation

## 9. Revision History

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-23 | NG / CC | Initial draft. Cross-referenced both datasheets, identified the only 7 pin functions that differ between modules (CAN, PCIE1, MODULE_ID, SDMMC↔PCIE2/3). Confirmed the carrier as designed accepts both modules without modification. Recommended Orin Nano for flight, Original Nano for bench/EDU. |
