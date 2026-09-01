# Payload Carrier Pin Map — Canonical

## Status

**This document is the single source of truth for the payload
carrier board's pin assignments** between the Jetson Orin Nano module
(260-pin SO-DIMM, TE 2309413-1) and the rest of the carrier (camera
connectors, CSKB stack interface, debug headers, power circuitry).

For stack-side pin assignments (H1/H2 nets crossing module boundaries),
the authority is [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md). This document covers
**carrier-internal** wiring only.

## Reference documents

| Doc | Designation | Local copy |
|---|---|---|
| Jetson Orin Nano Series Data Sheet | DS-11105-001 v1.1 | [`hardware/payload_compute/design/Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf`](Jetson_Orin_Nano_Series_DS-11105-001_v11.pdf) |
| Jetson Orin NX/Nano Design Guide | DG-10931-001 v1.1 | [`hardware/payload_compute/design/Jetson_Orin_NX_Series_and_Orin_Nano_Series_Design_Guide_DG-10931-001_v11.pdf`](Jetson_Orin_NX_Series_and_Orin_Nano_Series_Design_Guide_DG-10931-001_v11.pdf) |
| Jetson Orin NX/Nano Pin Function Names Guide | DA-11434-001 v1.0 | [`hardware/payload_compute/design/Jetson_Orin_NX_Orin_Nano_Pin_Function_Names_Guide_DA-11434-001_v1.0.pdf`](Jetson_Orin_NX_Orin_Nano_Pin_Function_Names_Guide_DA-11434-001_v1.0.pdf) |
| Jetson Orin Nano Devkit Carrier Spec | SP-11324-001 v1.3 | [`hardware/payload_compute/design/Jetson-Orin-Nano-DevKit-Carrier-Board-Specification_SP-11324-001_v1.3.pdf`](Jetson-Orin-Nano-DevKit-Carrier-Board-Specification_SP-11324-001_v1.3.pdf) |
| Pumpkin CSKB Datasheet | 710-00484 Rev. E | [`system/interfaces/DS_CSK_MB_710-00484-E.pdf`](../../../system/interfaces/DS_CSK_MB_710-00484-E.pdf) |
| CSKB pin map | — | [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md) |

## Module variant assumption

v0.1 uses the **Jetson Orin Nano devkit module** (boots from
microSD on the module itself). Per DG-10931 §6, "Module ID" (SO-DIMM
pin 217) is **tied to GND on the module** on legacy/devkit modules
to indicate 5V-only VDD_IN. Carrier MUST therefore drive VDD_IN at 5.0 V
and MUST NOT supply anything in the 5–20 V extended range. If we ever
swap to a wide-range production module, this assumption breaks and the
power tree needs revisiting.

## Direction legend

For each carrier-internal net:

- `O` — **driven by the Orin module** (output from SO-DIMM)
- `I` — **driven into the Orin module** (input to SO-DIMM)
- `B` — bidirectional (I²C, USB, JTAG-like)
- `P` — power rail (VDD_IN, GND)

## 1. Power

| SO-DIMM pin(s) | Module net | Carrier net | Dir | Notes |
|---|---|---|---|---|
| 251, 253, 255, 257, 259, 252, 254, 256, 258, 260 | `VDD_IN` | `+5V_ORIN` | I | 10 parallel pins. Sized for 3 A peak (15 W mode). Source = local buck from `VBAT` (NOT stack +5V — see Power architecture below). |
| 1, 2, 7, 8, 13, 14, 19, 20, 25, 26, 31, 32, 37, 38, 43, 44, 49, 50, 55, 56, 61, 62, 67, 68, 73, 74, 79, 80, 85, 86, 102, 107, 119, 125, 129, 132, 135, 138, 141, 144, 146, 147, 152, 153, 158, 159, 164, 165, 170, 171, 176, 177, 200, 201, 231, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250 | `GND` | `GND` | P | All GND pins tied to single ground plane. |
| 217 | `MODULE_ID` | `GND` | I | Legacy/devkit module: tie to GND on carrier to match the module's on-board GND tie. Per DG-10931 §6.1, this declares 5V-only VDD_IN. |
| 235 | `PMIC_BBAT` | (NC) | — | RTC backup. **v0.1: NOT POPULATED** — no coin-cell holder on carrier. RTC will reset on each power cycle; IHU supplies time-of-day over I²C after Orin boots. Revisit if a coin-cell-backed clock is later deemed worth the volume. |

### Power architecture

Stack +5V rail is provisioned at ~2 A (CSKB H2.25/H2.26). Orin Nano peaks
at ~3 A on VDD_IN in 15 W mode. Carrier therefore takes power from
**`VBAT`** (CSKB H2.45/H2.46, 6.0–8.4 V nominal) through a local buck
converter sized for ≥3 A @ 5.0 V output. This requires changing the
payload column for H2.45/H2.46 in [`cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md) from `M` (monitor)
to `C` (consumer) — flag for EPS conversation.

Decoupling at the SO-DIMM VDD_IN pins per DG-10931 recommended values
(see design guide §6 for the exact bulk + bypass cap distribution).

## 2. Power Sequencing & Control

| Pin | Module net | Carrier net | Dir | Notes |
|---|---|---|---|---|
| 237 | `POWER_EN` | `PWR_EN` | I | Level-active. High = on, low = off. Driven by carrier power-control logic after VDD_IN is stable. Pulldown is on the module. |
| 239 | `SYS_RESET*` | `SYS_RESET_N` | B | Bidir, open-drain. Module pulls high when its power-up sequence completes — carrier uses this as the supply enable for downstream 3.3V/1.8V devices. Carrier may pull low to reset SoC + QSPI without full power cycle. Module side pulls up to 1.8 V. |
| 233 | `SHUTDOWN_REQ*` | `SHDN_REQ_N` | O | Open-drain (VDD_IN = 5V pull-up on module). Asserted low by module on software/thermal/UV shutdown. Carrier MUST drive `PWR_EN` low when this asserts. Also propagated to CSKB H2.47 (`PAYLOAD_FAULT_N`, 3.3V open-drain) via channel 1 of a single 74LVC2G07 open-drain buffer (VCC = `+1V8_MOD`, 5V-tolerant input) — see CSKB stack interface §6.5 and altium_payload_schematic_guide.md §1.D for the VCC-at-1.8V analysis. |
| 214 | `FORCE_RECOVERY*` | `FRC_RCVRY_N` | I | Held LOW at SYS_RESET* release to enter USB Recovery Mode. Tied to a 2-pin jumper / test point on carrier; default = HIGH (pulled to 1.8 V on carrier via 10 kΩ). Only consulted during boot — once Linux is up, this pin becomes a regular GPIO. |
| 240 | `SLEEP/WAKE*` | `SLP_WAKE_N` | I | IHU-commanded sleep request. Connected to CSKB H2.48 (`PAYLOAD_SLEEP_REQ_N`, 3.3V CMOS from IHU). Pin tolerates 5V CMOS but accepts 3.3V drive level reliably; **v0.1: direct connection, no level translator** (IHU drives 3.3V, Orin V_IH worst-case at 3.0V is met). If validation shows marginal levels, add an AHCT1G125 buffer in rework. |
| 178 | `MOD_SLEEP*` | `MOD_SLEEP_N` | O | Asserts low when module is in SC7 (deep sleep). Carrier can use this to disable downstream loads. v0.1: route to test point TP2; optionally use as input to IHU via CSKB USER pin (not yet allocated). |
| 210 | `CLK_32K_OUT` | `CLK32K` | O | 32.768 kHz buffered clock from module. v0.1: not used externally, route to test point TP3 only. |

### 2.1 Test Point Allocation (canonical)

Single source of truth for TP refdes assignments — the schematic
guide and any future docs must match this table. If you need a TP
for a signal not listed, append it as TP8+ and update this table.

| TP | Net | Sheet | Status | Rationale |
|---|---|---|---|---|
| TP1 | `SYS_RESET_N` (SO-DIMM 239) | Sheet 1, §1.D | **Required** | Module power-up sequence capture — logic-analyzer hookup during bring-up |
| TP2 | `MOD_SLEEP_N` (SO-DIMM 178) | Sheet 1, §2 | Nice-to-have | Observe SC7 deep-sleep transitions |
| TP3 | `CLK_32K_OUT` (SO-DIMM 210) | Sheet 1, §2 | Nice-to-have | RTC clock diagnostic; also reserved as the buffered source if a future card swap requires M.2 pin 50 SUSCLK |
| TP4 | `PAYLOAD_FAULT_N` (74LVC2G07 ch.1 output → CSKB H2.47) | Sheet 1, §1.D | **Required** | Fault propagation observation — verify SHUTDOWN_REQ\* → IHU path |
| TP5 | `DBG_UART_TX_1V8` (SO-DIMM 203, pre-U60) | Sheet 1, §5 | **Required** | Probe the 1.8V UART before the level shifter; lets you debug if U60 fails or is suspected |
| TP6 | `DBG_UART_RX_1V8` (SO-DIMM 205, pre-U60) | Sheet 1, §5 | **Required** | Same — pre-shifter UART RX |
| TP7 | `+5V_TEST` (J50 pin 1, intentional single-pin net) | Sheet 4, §4.B | Optional | Probe whether the bench host is supplying VBUS during recovery debug. Only useful if you suspect cable issues. |

## 3. Cameras — 3× Pi Global Shutter Camera (Sony IMX296)

v0.1 carrier breaks out **CSI0, CSI1, CSI2** to three CSI ribbon
connectors, each at 2 lanes per DG-10931 Table 10-3. CSI3 is left unused
(reserved for future expansion).

**Camera module:** Raspberry Pi Global Shutter Camera (PN: SC0436), Sony
IMX296LQR-C (color, 1.58 MP, 3.45 µm pixel, global shutter). Reference:
`hardware/payload_compute/design/` (Pi GS Camera product brief, RP-008196-DS-1).
Selection rationale:

- Global shutter eliminates rolling-shutter exposure skew across the 3
  spectral channels — important for the K-line / O₂-reference ratio.
- 3.45 µm pixels (vs IMX477's 1.55 µm) give ~5× more NIR photon
  collection per pixel.
- Same CS/C-mount form factor as Pi HQ Camera, so the team's existing
  lens + Thorlabs filter assemblies still mount.
- IR-cut filter is user-removable (same surgery as Pi HQ); Bayer-strip
  surgery applies if monochrome behavior is needed (default sensor is
  color — see §3.6).

### 3.1 FFC connector

Per Pi documentation, the GS Camera native ribbon is the **15-pin
1.0 mm pitch standard CSI** connector (compatible with
**Amphenol SFW15R-2STE1LF** or equivalent). The ribbon ships at 150 mm.

For bench testing on the Orin Nano devkit carrier (which uses the
22-pin 0.5 mm "mini" CSI connector), a Raspberry Pi 15-to-22-pin adapter
cable is required. On the flight carrier we use the 15-pin
connector to plug the GS Camera ribbon in directly — saves an adapter
in the flight harness.

### 3.2 CSI ribbon pinout (15-pin Pi standard)

The Pi 15-pin standard CSI ribbon carries **only** the CSI-2 high-speed
pairs, I²C, power, and ground. **There is no MCLK pin on the ribbon** —
the IMX296 generates its own pixel clock from an onboard oscillator on
the camera PCB. There is also no TRIG / XTR pin on the ribbon — see §3.5
for hardware trigger routing.

Pi 15-pin CSI pinout (verify against Pi camera schematic before fab):

| FFC pin | Signal | Notes |
|---|---|---|
| 1 | GND | |
| 2 | CSI Data Lane 1 − | |
| 3 | CSI Data Lane 1 + | |
| 4 | GND | |
| 5 | CSI Data Lane 0 − | |
| 6 | CSI Data Lane 0 + | |
| 7 | GND | |
| 8 | CSI Clock − | |
| 9 | CSI Clock + | |
| 10 | GND | |
| 11 | CAM_GPIO0 | Shutdown / power-down to camera. v0.1: tied per-camera to a spare Orin GPIO (see §3.4). |
| 12 | CAM_GPIO1 | LED enable. v0.1: NC at carrier. |
| 13 | SCL | I²C clock, 3.3V (via mux — see §3.3) |
| 14 | SDA | I²C data, 3.3V |
| 15 | +3.3V | Camera supply, ≤250 mA per camera per Pi spec |

### 3.3 Lane assignments (per camera)

**Critical layout note** (DG-10931 §10): on the Orin Nano module,
**CSI_0_D1 and CSI_1_D0 have their P/N polarities swapped internally.**
For CSI0 and CSI1, the affected P/N pair must be swapped at the carrier
FFC end to compensate. CSI2 has no module-side swap. MIPI D-PHY
tolerates P/N swap via lane-deskew, but document the polarity explicitly
in the schematic.

Channel assignment follows the current filter plan — one on-line channel on the
potassium doublet and two continuum references outside the O₂ A-band. See
[`docs/research/k_line_detection.md`](../../../docs/research/k_line_detection.md).

#### Camera #0 (750 nm continuum reference)

| SO-DIMM pin | Module net | FFC pin | Carrier net | Notes |
|---|---|---|---|---|
| 12 | `CSI0_CLK_P` | 9 | `CAM0_CLK_P` | |
| 10 | `CSI0_CLK_N` | 8 | `CAM0_CLK_N` | |
| 6 | `CSI0_D0_P` | 6 | `CAM0_D0_P` | |
| 4 | `CSI0_D0_N` | 5 | `CAM0_D0_N` | |
| 18 | `CSI0_D1_P` | 2 | `CAM0_D1_N` | **P/N swap on module** — module D1_P routed to FFC D1_N |
| 16 | `CSI0_D1_N` | 3 | `CAM0_D1_P` | **P/N swap on module** |
| 213/215 | `CAM_I2C_SCL/SDA` | 13/14 | (via mux ch 0) | Shared bus |
| 127 | `GPIO04` | 11 | `CAM0_PWDN` | 1.8V GPIO → 3.3V FFC pin via the mux IC's spare buffer **OR** direct connect (3.3V CAM_GPIO0 tolerates 1.8V drive as logic low; for high level we may need a pull-up to 3.3V) — verify against Pi GS Cam schematic. |
| — | `+3V3` | 15 | (200 mA per cam) | Carrier 3.3V rail to FFC pin 15 |
| — | `GND` | 1, 4, 7, 10 | `GND` | |

#### Camera #1 (770 nm K-line on-line channel)

| SO-DIMM pin | Module net | FFC pin | Carrier net | Notes |
|---|---|---|---|---|
| 11 | `CSI1_CLK_P` | 9 | `CAM1_CLK_P` | |
| 9 | `CSI1_CLK_N` | 8 | `CAM1_CLK_N` | |
| 5 | `CSI1_D0_P` | 6 | `CAM1_D0_N` | **P/N swap on module** |
| 3 | `CSI1_D0_N` | 5 | `CAM1_D0_P` | **P/N swap on module** |
| 17 | `CSI1_D1_P` | 2 | `CAM1_D1_P` | |
| 15 | `CSI1_D1_N` | 3 | `CAM1_D1_N` | |
| 213/215 | (shared CAM_I2C) | 13/14 | (via mux ch 1) | |
| 130 | `GPIO06` | 11 | `CAM1_PWDN` | |

#### Camera #2 (780 nm continuum reference)

| SO-DIMM pin | Module net | FFC pin | Carrier net | Notes |
|---|---|---|---|---|
| 30 | `CSI2_CLK_P` | 9 | `CAM2_CLK_P` | |
| 28 | `CSI2_CLK_N` | 8 | `CAM2_CLK_N` | |
| 24 | `CSI2_D0_P` | 6 | `CAM2_D0_P` | |
| 22 | `CSI2_D0_N` | 5 | `CAM2_D0_N` | |
| 36 | `CSI2_D1_P` | 2 | `CAM2_D1_P` | |
| 34 | `CSI2_D1_N` | 3 | `CAM2_D1_N` | |
| 213/215 | (shared CAM_I2C) | 13/14 | (via mux ch 2) | |
| 211 | `GPIO09` | 11 | `CAM2_PWDN` | |

### 3.4 Camera I²C mux

IMX296 has a **fixed I²C address (0x1A)**, same as IMX477. Three sensors
on a shared bus would collide. Carrier needs a 4-channel 3.3V I²C
mux — **PCA9546A** (4-channel, leaner than the 8-channel TCA9548A)
downstream of `CAM_I2C_SCL/SDA`:

| Mux channel | Camera | Notes |
|---|---|---|
| 0 | Camera #0 | |
| 1 | Camera #1 | |
| 2 | Camera #2 | |
| 3 | unused | Capped at the mux IC; not routed to a connector |

Mux control: CAM_I2C bus itself (PCA9546A is I²C-controlled).
Mux `RESET#` driven by Orin **GPIO07** (SO-DIMM pin 206), 1.8V → 3.3V
through a single buffer in the same package as the SHUTDOWN_REQ*
translator (use the second channel of the 74LVC2G07 dual buffer for this).

Note: CAM_I2C bus pull-ups are already on the Orin module (2.2 kΩ to
3.3V per DG-10931 Table 10-6). Do NOT add additional pull-ups on carrier.

### 3.5 Hardware sync (XTR external trigger)

**Important physical-design note:** per the Pi GS Camera product brief
(RP-008196-DS-1, page 5), the external trigger (XTR) — along with XHS,
XVS, XMAS, SCL, SDA, 3V3, GND — is exposed on **solder pads at the back
edge of the camera PCB**, NOT on the 15-pin CSI ribbon. To use hardware
sync, a wire must be soldered to each camera's XTR pad and routed back
to the carrier.

XTR signal is **1.8V logic** — applying 3.3V will damage the IMX296.

Voltage match: Orin GPIO outputs are 1.8V CMOS, so XTR can be driven
directly from a single Orin GPIO with **no level shifter** — just series
resistors at each camera for ESD / impedance protection. This was the
key motivation for staying at 1.8V drive (saves one IC).

#### Trigger signal path

| SO-DIMM pin | Carrier net | Header | Notes |
|---|---|---|---|
| 128 | `GPIO05` → `CAM_TRIG_1V8` | J_TRIG pin 1 | 1.8V CMOS, single shared trigger source |
| — | `GND` | J_TRIG pin 2 | Return |

Carrier exposes a **2-pin 1.0 mm pitch JST-SH header (`J_TRIG`)**. A
field-assembled wire harness from J_TRIG fans out to each of the three
GS Camera XTR pads through a 3-way Y-splice, with a **100 Ω series
resistor at each camera** for ESD protection and to limit slew across
the harness. Total fan-out impedance is ~33 Ω from the Orin's
perspective — comfortable for a 1.8V CMOS driver.

This guarantees zero capture skew across the three spectral channels
because all three XTR pads see the same edge simultaneously, modulo
harness propagation (<1 ns for a 150 mm harness).

### 3.6 Color vs monochrome

The Pi Foundation GS Camera ships with **IMX296LQR-C (color)**. For
clean spectral measurement at the K-line wavelengths, the Bayer matrix
adds per-pixel spectral attenuation that's not flat across 750/770/780 nm.
Two paths:

- **Path A (matches team's existing workflow):** buy 3× standard Pi GS
  Cameras, perform the same Bayer-matrix removal + IR-cut filter removal
  the team already does on Pi HQ. Highest reproducibility with existing
  lab procedures. Permanent and not reversible per RPi docs.
- **Path B (clean monochrome from the start):** buy 3× Arducam IMX296
  mono camera modules (Arducam PN B0498) which use the IMX296LLR
  monochrome sensor variant. No surgery needed. Different vendor though,
  may have different FFC pinout / pad layout — verify before committing.

v0.1 default = **Path A** unless team explicitly chooses Path B.
This decision affects camera procurement only, not the carrier PCB.

## 4. USB Recovery / Bootloader Test Header

Per DG-10931 §3.2, the **only** signals needed for USB Recovery Mode are
`USB0_D_N/P`. No VBUS or USB-ID detection is required — when
`FORCE_RECOVERY*` is held low at SYS_RESET* rising edge, the module
configures USB0 as a device and waits for the flash tool.

v0.1: 5-pin internal test header (1.27 mm pitch), not a USB
connector. Used for bootloader recovery on the bench only. Not exposed
through the 1U structure.

| SO-DIMM pin | Module net | Carrier net | Header pin | Notes |
|---|---|---|---|---|
| 109 | `USB0_D_N` | `USB0_D_N` | 2 | High-speed USB 2.0 differential, 90 Ω diff, AC-coupled per DG-10931 §7.1.1 |
| 111 | `USB0_D_P` | `USB0_D_P` | 3 | |
| 87 | `GPIO00` (`USB_VBUS_EN0`) | `USB0_VBUS_DET` | 4 | Optional: 1.8V open-drain VBUS detect. v0.1: leave NC at module, do not route to header. |
| — | — | `+5V_TEST` | 1 | From bench host. Not used by module (recovery mode does not require VBUS). |
| — | — | `GND` | 5 | |

The `+5V_TEST` / VBUS pin is present for cable compatibility with USB
Micro-B breakout cables but is not electrically required. Mark on
silkscreen as "BOOTLOADER ONLY — DO NOT POWER FROM HERE."

## 5. Debug UART (Linux console)

Per DG-10931 §12, **UART1** is the Linux serial console by default.

| SO-DIMM pin | Module net | Carrier net | Test point | Notes |
|---|---|---|---|---|
| 203 | `UART1_TXD` | `DBG_UART_TX_1V8` | TP5 | 1.8V CMOS — needs level shifter to 3.3V before exposing. TP5 = pre-shifter probe per §2.1. |
| 205 | `UART1_RXD` | `DBG_UART_RX_1V8` | TP6 | 1.8V CMOS. TP6 = pre-shifter probe per §2.1. |
| 207 | `UART1_RTS*` | (NC) | — | RTS/CTS not exposed v0.1 |
| 209 | `UART1_CTS*` | (NC) | — | |

Expose as a 3-pin 1.27 mm header (TX/RX/GND) downstream of a 1.8V↔3.3V
level shifter (TXB0104 or equivalent), so a standard FT232/CP2102 USB-UART
adapter can connect directly.

## 6. CSKB Stack Interface

Signals crossing the CSKB connectors and their mapping to Orin SO-DIMM
pins. CSKB pin numbers and net names come from [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md)
and MUST match exactly — if there's a conflict, that file wins.

### 6.1 System I²C — IHU ↔ payload command channel

The payload's primary control interface to the IHU. Orin acts as I²C
target with a defined register map (TBD in firmware spec). Bus runs at
400 kHz (CSKB defaults).

| CSKB pin | CSKB net | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| H1.41 | `SDA_SYS` | 187 | `SDA_SYS` (Orin `I2C0_SDA`) | Bus pull-ups already on EPS side (R4/R5, 4.7 kΩ) — do NOT add additional pull-ups on payload. Canonical net name per [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md). |
| H1.43 | `SCL_SYS` | 185 | `SCL_SYS` (Orin `I2C0_SCL`) | |

### 6.2 Payload enable

| CSKB pin | CSKB net | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| H1.50 | `PAYLOAD_EN` | — | (gates payload buck) | IHU drives high to enable the local 5V buck regulator (i.e., powers the Orin's VDD_IN). Active-high, 3.3V CMOS from IHU. Connect to enable input of the VBAT→5V buck, NOT directly to any SO-DIMM pin. |

### 6.3 CAN (provisioned, DNP for v0.1)

Orin's CAN_TX/RX → CSKB CAN_H/L via a 3.3V CAN transceiver (TCAN332GDR
or equivalent). Iter-2 only; populate the transceiver footprint but the
CAN_H/L termination resistor and transceiver IC are DNP on v0.1 boards.

| CSKB pin | CSKB net | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| H1.51 | `CAN_H` | (via xcvr) | — | |
| H1.52 | `CAN_L` | (via xcvr) | — | |
| — | — | 143 | `CAN_RX` | To transceiver RXD |
| — | — | 145 | `CAN_TX` | From transceiver TXD |

### 6.4 Payload-side power consumption

| CSKB pin | CSKB net | Carrier behavior | Notes |
|---|---|---|---|
| H2.25/H2.26 | `+5V` | Not connected | Carrier does NOT pull from stack +5V (Orin peak ~3 A exceeds stack rail capacity). |
| H2.27/H2.28 | `+3V3` | Connected as `C` | Auxiliary 3.3V loads on the carrier: I²C mux (PCA9546A), CAN transceiver bias, status LEDs, level shifter VCCB on TXB0104 (debug UART, high side), **3.3V supply to all three Pi GS Camera FFCs (FFC pin 15)**, and **M.2 Key-E socket (§10)**. (Note: U4 74LVC2G07 buffer is on `+1V8_MOD`, NOT this rail — see §6.5 / §6.7.) Continuous ~900 mA, peak ~1.6 A (3× 250 mA cams + 100 mA logic + 750 mA M.2). Within CSKB +3V3 2 A rating but tight — see §10 power notes. M.2 is bench-only; flight build is DNP and the rail drops back to ~800 mA peak. |
| H2.45/H2.46 | `VBAT` | Connected as `C` | Source for local 5V buck (VBAT→VDD_IN). Buck sized for ≥3 A continuous at 5.0 V with ~90% efficiency → peak input ~22 W from VBAT during 15 W Orin mode. CSKB pinmap rev 0.3 reflects this. |
| H2.29–32, H2.31 | `GND` | Connected | All grounds tied to carrier ground plane. |

### 6.5 Fault propagation — PAYLOAD_FAULT_N

| CSKB pin | CSKB net | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| H2.47 | `PAYLOAD_FAULT_N` | 233 | `SHUTDOWN_REQ*` | Orin asserts `SHUTDOWN_REQ*` low (5V OD, pulled up to VDD_IN on module) on any software/thermal/UV fault. Carrier translates 5V OD → 3.3V OD via **channel 1 of a single 74LVC2G07** (dual open-drain buffer, **VCC = `+1V8_MOD`**, 5V-tolerant input). The OD output is rail-agnostic — IHU pulls up to 3.3V on its end per cskb_pinmap.md Rule 3. See altium_payload_schematic_guide.md §1.D for why VCC = 1.8V (V_IH compliance on ch.2 mux reset path). |

### 6.6 Sleep request — PAYLOAD_SLEEP_REQ_N

| CSKB pin | CSKB net | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| H2.48 | `PAYLOAD_SLEEP_REQ_N` | 240 | `SLEEP/WAKE*` | IHU drives 3.3V CMOS active-low. Direct connect to Orin `SLEEP/WAKE*` — no level translator for v0.1 (pin is rated 5V CMOS but accepts 3.3V drive cleanly per typical Tegra V_IH). If validation shows marginal levels, add an AHCT1G125 (5V supply, TTL input) in rework. |

### 6.7 Mux reset signal

The 74LVC2G07 dual-channel package used for PAYLOAD_FAULT_N also has a
second channel — repurpose it as the I²C mux reset translator:

| SO-DIMM pin | Direction | Carrier net | Endpoint | Notes |
|---|---|---|---|---|
| 206 | O (1.8V) | `MUX_RST_N_1V8` → 74LVC2G07 ch.2 → `MUX_RST_N_3V3` | PCA9546A `RESET#` | Single dual-channel buffer covers both fault propagation and mux reset — minimum part count. |

## 7. Explicitly NOT Connected on v0.1

These SO-DIMM pins are routed nowhere on the carrier (leave as NC at
the SO-DIMM connector). Listed here so they don't get accidentally
re-allocated.

| Pins | Module net | Reason |
|---|---|---|
| 39, 41, 45, 47, 51, 53, 57, 59 | DisplayPort 0 / USB 3.2 muxed | No DP, no USB 3 |
| 63, 65, 69, 71, 75, 77, 81, 83 | DisplayPort 1 | No DP |
| 70, 72, 76, 78, 82, 84 | DSI | No display |
| 88, 90, 92, 94, 96, 98, 100 | DP HPD / AUX / HDMI_CEC | No DP/HDMI |
| 131, 133, 134, 136, 137, 139, 140, 142, 148, 149, 150, 151, 154, 155, 156, 157, 160, 162, 180, 181 | PCIE0 x4 | No NVMe / M.2 Key M |
| 40, 42, 46, 48, 52, 54, 58, 60, 64, 66 | CSI4 / PCIE2 muxed | Only need 3× 2-lane CSI; no PCIe2 |
| 161, 163, 166, 168 | USBSS port 0 | No USB 3.2 |
| 184, 186, 188, 190, 192, 194, 196, 198, 202, 204 | Gigabit Ethernet MDI + LEDs | No Ethernet |
| 121, 123 | USB2_D | Reserved for future use |
| 89, 91, 93, 95, 97 | SPI0 | Reserved for future use (could be IHU↔payload high-rate link via CSKB USER pins, iter-2) |
| 99, 101, 103, 105 | UART0 | Reserved for future use |
| 104, 106, 108, 110, 112 | SPI1 | Reserved for future use |
| 193, 195, 197, 199, 220, 222, 224, 226 | I2S0, I2S1 | No audio |
| 189, 191 | I2C1 | Reserved (CAM_I2C and I2C0 are sufficient) |
| 232, 234 | I2C2 | Reserved |
| 219, 221, 223, 225, 227, 229 | SDMMC (muxed to PCIe2/3 control) | No SD on carrier (module already has its own microSD socket) |
| 33, 35, 21, 23, 27, 29 | CSI3 | 4th camera — reserved for future |
| 114, 116, 118, 120, 122 | CAM0_MCLK, CAM1_MCLK, CAM0_PWDN, CAM1_PWDN, GPIO01 (as MCLK2) | Pi GS Camera generates its own pixel clock from an onboard oscillator; no host MCLK needed. PWDN is on the 15-pin FFC (pin 11) and driven by a generic GPIO instead of these dedicated CAM_* pins. |
| 212, 216, 228, 230 | GPIO10, GPIO11, GPIO13, GPIO14 | Reserved spare GPIO; route to test points |
| 208 | GPIO08 | Reserved spare GPIO |
| 124, 126 | GPIO02, GPIO03 | Reserved spare GPIO |

## 8. GPIO allocation summary

| GPIO | SO-DIMM pin | Carrier function | v0.1 use |
|---|---|---|---|
| GPIO00 | 87 | USB0 VBUS detect | NC at module (recovery does not need VBUS_DET) |
| GPIO01 | 118 | spare | NC, test point |
| GPIO02 | 124 | spare | NC, test point |
| GPIO03 | 126 | spare | NC, test point |
| GPIO04 | 127 | Camera #0 PWDN → FFC pin 11 | **Used** |
| GPIO05 | 128 | Shared camera trigger → J_TRIG → 3× XTR pads | **Used** |
| GPIO06 | 130 | Camera #1 PWDN → FFC pin 11 | **Used** |
| GPIO07 | 206 | I²C-mux reset (PCA9546A `RESET#`) via 74LVC2G07 ch.2 | **Used** |
| GPIO08 | 208 | spare | NC, test point |
| GPIO09 | 211 | Camera #2 PWDN → FFC pin 11 | **Used** |
| GPIO10 | 212 | spare | NC, test point |
| GPIO11 | 216 | spare | NC, test point |
| GPIO12 | 218 | spare | NC, test point |
| GPIO13 | 228 | spare | NC, test point |
| GPIO14 | 230 | spare | NC, test point |

## 9. M.2 Key-E WiFi/BT socket (ground-bench only)

### 9.1 Purpose

Bench-time WiFi + Bluetooth for SSH, log streaming, `iperf`, and remote
debugging while the carrier is on the lab bench. **Validated against the
Realtek RTL8822CE** 802.11ac + BT 5.0 card shipped on the Orin Nano
devkit (lspci on the devkit shows it at bus `0001:01:00.0` on PCIe
controller 1). The same card transplants directly from the devkit to
this carrier; no software / driver changes needed.

The socket is **populated only for ground bench work**. The flight build
leaves the M.2 socket empty (no card), which keeps the radio off-orbit
(avoids licensing + interference) and reclaims ~750 mA on the 3.3V rail.

### 9.2 Socket and mechanical

| Item | Value |
|---|---|
| Footprint | M.2 2230 Key-E, 75-pin |
| Connector | **Amphenol `MDT420E01001`** — Key-E, 30 μin gold plating, **4.20 mm stack height**. Selected over the 2.75 mm single-sided variant (MDT275-series) purely on JLCPCB stock + price: 918 in stock at $1.22 vs. single-digit stock on the 2.75 mm variants. Functionally fine — a single-sided card like the RTL8822CE just has more empty air below it. The TE `2199125-4` we originally specified (2.15 mm) was out of stock. |
| Mount | M2.5 standoff (4.20 mm tall) + M2.5×3 mm screw. **Must match the MDT420 connector's 4.20 mm stack height.** Standard "M.2 NGFF" hardware kits target this height — widely available from Digi-Key/Mouser (Würth, Bivar, Keystone all stock M2.5×4.20 mm). JLCPCB doesn't carry the hardware. |
| Vertical budget | Stack 4.20 + card PCB 0.8 + card components ~1.5 = **~6.5 mm above carrier PCB top.** CSKB inter-board pitch ~15.24 mm → ~8.7 mm clearance to next board — comfortable. |
| Antenna | Two u.FL on the card → two MMCX or SMA-edge bulkhead connectors on the carrier (labeled `ANT1`, `ANT2`); DNP for flight |

### 9.3 PCIe Gen3 ×1 mapping (PCIE1 controller, lspci bus 0001)

The RTL8822CE WiFi side enumerates as `0001:01:00.0` on the Orin's
**PCIe Controller #1** (1-lane, root-port-only per DG-10931 Table for
PCIe Interface 1). All control signals are 3.3V open-drain with on-module
pull-ups — direct connect, no level translation, no carrier-side pull-ups.

| M.2 pin | M.2 signal | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| 35 | PETp0 | 174 | `PCIE1_TX0_P` | TX from Orin → M.2 RX. **Series 0.22 µF AC cap near SO-DIMM** (DG-10931 §7.4). 85 Ω differential, intra-pair ≤5 mil. |
| 37 | PETn0 | 172 | `PCIE1_TX0_N` | |
| 41 | PERp0 | 169 | `PCIE1_RX0_P` | RX into Orin. AC cap is inside the M.2 card; no cap on carrier RX side. 85 Ω differential. |
| 43 | PERn0 | 167 | `PCIE1_RX0_N` | |
| 47 | REFCLKp0 | 175 | `PCIE1_CLK_P` | 100 MHz REFCLK from Orin, DC-coupled. 100 Ω differential, length-match within ±50 mil of TX pair. |
| 49 | REFCLKn0 | 173 | `PCIE1_CLK_N` | |
| 52 | PERST0# | 183 | `PCIE1_RST*` | OD 3.3V, 4.7 kΩ PU on module. Direct connect. |
| 53 | CLKREQ0# | 182 | `PCIE1_CLKREQ*` | Bidir OD 3.3V, 47 kΩ PU on module. Direct connect. |
| 55 | PEWAKE0# | 179 | `PCIE_WAKE*` | OD 3.3V, 47 kΩ PU on module. Shared with PCIE0 controller — fine, only one device wakes at a time. |

### 9.4 Bluetooth-over-USB

RTL8822CE puts WiFi on PCIe but **BT on USB 2.0**. Use USB Port 1
(previously reserved for future use); USB0 is already committed to the
recovery test header.

| M.2 pin | M.2 signal | SO-DIMM pin | Module net | Notes |
|---|---|---|---|---|
| 3 | USB_D+ | 117 | `USB1_D_P` | USB 2.0 high-speed. 90 Ω differential per DG-10931 §7.1.1. NO AC coupling on USB 2.0. |
| 5 | USB_D− | 115 | `USB1_D_N` | |

### 9.5 Power

| M.2 pin | Net | Source | Notes |
|---|---|---|---|
| 2, 4, 72, 74 | +3.3V | `+3V3` (CSKB +3V3 via ferrite) | Series ferrite FB_M2 (60 Ω @ 100 MHz, ≥2 A rated, e.g. Murata BLM31KN601SH1) near socket for HF noise isolation from cameras. Bulk decoupling: 22 µF X7R + 4× 100 nF at the connector. M.2 Key-E spec allows ≤1.5 A peak / 750 mA continuous; RTL8822CE typical 400 mA / peak ~750 mA. |
| 1, 7, 11, 15, 17, 18, 21, 25, 27, 29, 31, 33, 39, 45, 51, 57, 71, 75 | GND | `GND` | Standard M.2 ground returns. |

If the M.2 +3.3V load causes EMI on the CSI lanes during bring-up, the
fallback is a local 5V_PAYLOAD → 3V3_M2 LDO (TLV757P or similar, ~1.27 W
dissipation at 750 mA — acceptable on the bench). Footprint-only for v0.1;
populate only if needed.

### 9.6 Radio kill switches

| M.2 pin | Signal | v0.1 wiring | Rationale |
|---|---|---|---|
| 56 | W_DISABLE1# (WiFi) | 10 kΩ PU to `+3V3`, always HIGH | No software kill switch v0.1. Card is bench-only; "kill" = unplug. |
| 54 | W_DISABLE2# (BT) | 10 kΩ PU to `+3V3`, always HIGH | Same. |

Future rev could route these to spare Orin GPIOs (GPIO08, GPIO10, etc.)
for software-controlled radio enable, but that's not needed for v0.1.

### 9.7 Explicitly NC on the M.2 socket (v0.1)

All M.2 pins not listed in §9.3–§9.6 are **NC at the socket** for v0.1.
Notable ones to call out so future revs don't think they were forgotten:

| M.2 pin(s) | Signal | Why NC |
|---|---|---|
| 50 | SUSCLK (32.768 kHz) | RTL8822CE has on-card LPO and does not require SUSCLK. Orin's `CLK_32K_OUT` (pin 210) is 1.8V CMOS and per DS-11105 needs a buffer if used externally — skip the buffer for v0.1, keep CLK_32K_OUT routed to a test point only. Cards that *require* SUSCLK (some Intel AX-series, Killer cards) will need a 1.8V→3.3V buffer added on a future rev. |
| 6, 16 | LED1#, LED2# | Radio activity LEDs not exposed. |
| 8, 9, 10, 12, 13, 14 | PCM/I2S (BT audio) | No audio path. |
| 19, 21, 23 | SDIO_CLK/CMD/D0 (alt WiFi I/F on SDIO-only cards) | RTL8822CE is PCIe, not SDIO. |
| 11, 20, 22, 32, 34, 36 | UART (BT alt) | RTL8822CE BT uses USB, not UART. |
| 38, 40, 42, 44, 46, 48 | Reserved / I²C / I2C_IRQ# | Not needed. |
| 58, 60, 67, 68, 69, 70, 73 | Coex / reserved | Not needed for a single-card system. |

### 9.8 Layout notes (PCIe Gen3 ×1)

1. **AC coupling caps on TX pair only**, placed near the SO-DIMM end, not the M.2 end (DG-10931 §7.4).
2. **Differential impedance:** 85 Ω ±10 % on PETp0/PETn0 and PERp0/PERn0; 100 Ω ±15 % on REFCLKp0/REFCLKn0.
3. **Length matching:** intra-pair ≤5 mil; inter-pair (between TX, RX, and REFCLK) ≤50 mil. Tighter than CSI MIPI.
4. **Reference plane:** keep all three diff pairs over a continuous ground plane the whole way from SO-DIMM to M.2 — no splits, no via stubs, no routing through anti-pads.
5. **Via count:** ideally zero on each pair; if a via is unavoidable, use ground-return vias adjacent.
6. **Lane swap is allowed** on a per-pair basis for the diff pairs (not the REFCLK) since Gen3 supports lane reversal at the controller. Don't swap unless it actually saves a layer change.
7. **PERST# / CLKREQ# / WAKE#:** route as plain 3.3V CMOS, no length matching, but keep them away from the diff pairs (≥3× trace width spacing).

## 10. Open items

1. **Verify Pi 15-pin CSI ribbon pinout** against the Raspberry Pi
   Compute Module datasheet / Pi GS Camera schematic before fab.
   Specifically: pin 11 = `CAM_GPIO0` (PWDN), pin 12 = `CAM_GPIO1`
   (LED EN), pins 13/14 = I²C SCL/SDA. The table in §3.2 reflects
   the commonly documented pinout but the official Pi GS Camera
   schematic is the authority.
2. **Verify CAM_GPIO0 (PWDN) voltage** on Pi GS Camera — is it 3.3V
   CMOS or 1.8V? If 3.3V, the Orin 1.8V GPIO drive may need a
   third buffer channel; if 1.8V, direct connect works. Reading
   the GS Camera schematic resolves this. Most Pi cameras run
   the FFC GPIOs at 3.3V so a third translator channel may be needed.
3. **GS Camera 3V3 supply current** — Pi spec says ≤250 mA per camera
   FFC pin 15. Verify the carrier 3.3V rail (sourced from CSKB
   `+3V3`) can handle 3× 150–250 mA + auxiliary logic. Stack +3V3
   is provisioned to 2 A total per `analysis/power/`,
   so this is fine, but verify the local trace widths.
4. **Camera trigger harness** mechanical design — 4-wire flying lead
   from J_TRIG to 3-way Y-splice → 3 cameras' XTR pads. Define
   wire AWG, length, strain relief, soldering procedure on the
   camera pad in `hardware/payload_compute/bringup/`.
5. **Monochrome decision** — Path A (strip Bayer on Pi GS Cams,
   matches team's existing workflow) vs Path B (Arducam IMX296
   mono modules). Decision affects procurement, not the carrier PCB.
6. **Camera-3 PWDN GPIO crosses VDD_IO domain.** GPIO09 (pin 211)
   is in a different power domain than GPIO04/06 — check pinmux
   options in DA-11434 for whether these can all be configured as
   1.8V CMOS outputs simultaneously. If not, may need to reassign.
7. **`PAYLOAD_SLEEP_REQ_N` direct-connect to `SLEEP/WAKE*`** —
   v0.1 assumption is that 3.3V CMOS drive meets the Orin's 5V CMOS
   V_IH. If validation fails, add an AHCT1G125 in rework.
8. **Thermal solution** — Orin module needs a heatspreader. No fan
   header populated; passive heatspreader bonded to the 1U chassis
   is required. Out of scope for this pin map; flagged for the
   mechanical / thermal trade study.
9. ~~**M.2 PCIe TX AC-cap location.**~~ **Resolved 2026-05-18.** Per
   PCIe CEM convention, AC coupling is the **transmitter's**
   responsibility on each end of the link: card-TX caps live on the
   card, host-TX caps live on the host, and both RX inputs are
   DC-coupled. The RTL8822CE reference design correctly shows no
   host-side caps because it's only depicting the card's own TX path.
   The Orin Nano design guide (DG-10931 §7.4) requires 0.22 µF series
   caps on PCIE1_TX0_P/N near the SO-DIMM — populate those, leave
   the RX side bare. This matches both standards.
10. **CSKB +3V3 peak headroom.** Ground bench worst case is ~1.6 A on
    +3V3 (3× cams @ 250 mA + M.2 @ 750 mA + logic). Confirm with EPS
    that the 2 A stack rail tolerates this — particularly during the
    ~10 ms M.2 PCIe link training inrush. If marginal, populate the
    fallback LDO footprint in §9.5 to move M.2 onto +5V_ORIN.
11. **M.2 antenna bulkhead routing.** Two u.FL pigtails from the card
    need to terminate at chassis bulkhead connectors (MMCX or
    SMA-edge). Mechanical placement TBD with the structures team;
    not on the carrier PCB itself.
12. **SUSCLK provisioning** for forward compatibility. v0.1 leaves
    M.2 pin 50 NC because RTL8822CE doesn't need it. If a future
    card swap (Intel AX210, Killer AX1675, etc.) requires SUSCLK,
    a single-gate 1.8V buffer (SN74LVC1G34 or 74AUP1G17) close to
    SO-DIMM pin 210, then a 1.8V→3.3V level shift to M.2 pin 50,
    will be needed. Reserve board area near the M.2 socket for this.
13. ~~**74LVC2G07 V_IH violation on channel 2 (mux reset path).**~~
    **Resolved 2026-05-24.** Original concern: 74LVC2G07 at VCC = 3.3 V
    has V_IH(min) = 2.0 V, but Orin GPIO07 drives only 1.8 V HIGH.
    **Resolution: keep the single 74LVC2G07 but power it from
    `+1V8_MOD` instead of `+3V3`.** The LVC family has a split V_IH
    spec — at VCC < 2.7 V, V_IH(min) = 0.65 × VCC = 1.17 V at VCC=1.8V,
    well below the 1.8 V CMOS HIGH. Both OD outputs remain rail-
    agnostic and pull up to 3.3 V through their external PUs (IHU side
    for `PAYLOAD_FAULT_N`, R34 on carrier for `MUX_RST_N_3V3`).
    Single-IC design preserved (no need to split into two 74LVC1G07).
    See altium_payload_schematic_guide.md §1.D and rev 0.3 entry.

## Revision history

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-11 | NG / CC | Initial draft against DS-11105 v1.1 module datasheet, DG-10931 v1.1 design guide. Allocates CSI0/1/2 to 3× Pi HQ Cameras, defines USB recovery test header, debug UART, CSKB stack mapping, GPIO summary. |
| 0.2 | 2026-05-11 | NG / CC | Camera switched from Pi HQ (IMX477) to Pi Global Shutter Camera (IMX296). Connector type 22-pin 0.5 mm → **15-pin 1.0 mm standard**. Removed CAM_MCLK / CAM_PWDN allocations (Pi cams use onboard oscillator). Trigger path: XTR on **separate solder pad** (not in FFC) — added 2-pin J_TRIG header + flying-lead harness. **No level shifter needed for trigger** (Orin 1.8V GPIO = XTR 1.8V logic). Added single 74LVC2G07 dual-channel buffer for SHUTDOWN_REQ→PAYLOAD_FAULT_N translation AND I²C mux reset. Removed coin-cell PMIC_BBAT (NC). Routed SLEEP/WAKE* (pin 240) to CSKB H2.48 (`PAYLOAD_SLEEP_REQ_N`). Reflected CSKB pinmap rev 0.3 allocations of H2.47/H2.48. |
| 0.3 | 2026-05-18 | NG / CC | Added **M.2 2230 Key-E WiFi/BT socket** (§9) for ground-bench SSH/iperf. Validated against Realtek RTL8822CE shipped on the Orin Nano devkit (lspci bus `0001:01:00.0`). Allocates PCIE1 ×1 (pins 167/169/172/173/174/175/182/183), USB1 (pins 115/117, BT-over-USB), and PCIE_WAKE* (pin 179). Removed those pins from §7 NC list. 3.3V supplied from CSKB +3V3 through a ferrite (FB_M2). All M.2 control signals are 3.3V on the Orin side — direct connect, no level translators. Socket is bench-only; flight build leaves it empty. Updated §6.4 CSKB +3V3 budget to reflect 1.6 A peak with M.2 + cams. Added 4 new open items (§10.9–§10.12) covering AC-cap location, 3V3 headroom, antenna bulkhead, and SUSCLK provisioning for future card swaps. |
| 0.4 | 2026-05-24 | NG / CC | Net-naming conformance pass against [`hardware/conventions/net_naming.md`](../../conventions/net_naming.md). Renamed `+3V3_PAYLOAD` → `+3V3` (stack rail uses canonical power port, no scope suffix). Renamed `+5V_PAYLOAD` → `+5V_ORIN` (board-local derived rail; suffix now describes purpose — the Orin module's VDD_IN — per the `+5V_TX_GATED` convention example). Renamed stack I²C carrier nets `I2C_SCL`/`I2C_SDA` → `SCL_SYS`/`SDA_SYS` to match cskb_pinmap.md canonical names. No electrical changes — net renaming only. |
| 0.5 | 2026-05-24 | NG / CC | **U4 buffer revisited.** Reverted from the two-74LVC1G07 split (recommended in rev 0.4 prose) back to a **single 74LVC2G07** by running it at **VCC = `+1V8_MOD`** (not `+3V3`). At VCC < 2.7 V the LVC family V_IH(min) is 0.65 × VCC = 1.17 V — accepts 1.8 V CMOS HIGH from Orin GPIO cleanly, while LVC inputs stay 5 V-tolerant so the 5 V `SHDN_REQ_N` source is fine. Both open-drain outputs are rail-agnostic and continue to pull to 3.3 V through external PUs. Updated §2, §6.5, §6.7, GPIO summary, and open item §10.13 to reflect the single-IC design. Saves one part vs the rev-0.4 prose recommendation. |
| 0.6 | 2026-05-24 | NG / CC | **Test point allocation rationalized.** Found cross-doc collisions — the pinmap §5 had assigned TP1/TP2 to the debug UART nets, while the schematic guide had TP1=SYS_RESET_N / TP2=MOD_SLEEP_N / TP3=CLK_32K_OUT. The schematic guide also had a TP4 collision (PAYLOAD_FAULT_N in Final Checklist vs +5V_TEST in §4.B alternative note). Added a new §2.1 "Test Point Allocation (canonical)" table as single source of truth for all TP refdes. Renumbered UART TPs in §5 from TP1/TP2 → TP5/TP6 to match. Schematic guide updated in parallel: §4.B optional `+5V_TEST` TP renumbered to TP7, Final Checklist updated to reference §2.1. No electrical changes — refdes-only fix. |
