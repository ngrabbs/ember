# Altium Schematic Instructions — Payload Carrier (Jetson Orin Nano)

## Design Summary

This payload carrier hosts a **Jetson Orin Nano** module (260-pin SO-DIMM)
on the 1U CubeSat stack. It breaks the module out to:

- 3× narrowband NIR cameras (Pi Global Shutter Camera, IMX296) for K-line
  wildfire detection
- The CSKB stack (Internal Housekeeping Unit I²C, fault propagation, sleep request)
- A bench-only M.2 Key-E WiFi/BT socket for ground SSH/iperf
- A USB-2 recovery test header and a debug UART for bring-up

```
                            ┌───────────────────────────────────────────┐
                            │  Jetson Orin Nano Module (TE 2309413-1)   │
                            │  260-pin SO-DIMM, 5V VDD_IN, 15 W peak    │
                            └─────────────────┬─────────────────────────┘
                                              │
            ┌─────────────────┬────────────────┼─────────────────┬─────────────────┐
            │                 │                │                 │                 │
       ┌────┴────┐      ┌─────┴─────┐   ┌──────┴──────┐   ┌──────┴─────┐    ┌──────┴─────┐
       │ VBAT→5V │      │ 3× CSI    │   │ I²C0,       │   │ M.2 Key-E  │    │ USB0 →     │
       │  buck   │      │ + PCA9546A│   │ CAN(DNP),   │   │ PCIE1×1 +  │    │ recovery   │
       │  3A     │      │ + J_TRIG  │   │ FAULT/SLEEP │   │ USB1 (BT)  │    │ + dbg UART │
       │ (LTC/TI)│      │ (cameras) │   │ (CSKB H1/H2)│   │ (bench)    │    │            │
       └─────────┘      └─────┬─────┘   └─────────────┘   └────────────┘    └────────────┘
                              │                                                            
                       3× Pi GS Camera                                                     
                       (with XTR wire-harness                                              
                        from J_TRIG)                                                       
```

Key design decisions baked in (see `payload_carrier_pinmap.md` for the
authoritative pin-by-pin allocation):

1. **VDD_IN sourced from VBAT, not stack +5V.** Orin peaks at 3 A @ 5 V,
   which exceeds the stack +5V rail (2 A). A local VBAT→5V buck on the
   carrier handles the full Orin load and is gated by `PAYLOAD_EN`.
2. **All control signals between Orin and the M.2 Key-E are 3.3V.** No
   level translators on the M.2 path — direct connect (per DG-10931).
3. **Single 74LVC2G07 dual-channel open-drain buffer** handles both the
   `SHUTDOWN_REQ*` → `PAYLOAD_FAULT_N` translation (5V OD → 3.3V OD) and
   the PCA9546A mux reset translation (1.8V → 3.3V).
4. **Camera trigger is 1.8V direct** — Orin 1.8V GPIO = IMX296 XTR 1.8V
   logic. No trigger level shifter required.
5. **Coin-cell RTC backup is omitted.** IHU supplies time-of-day over I²C
   after Orin boots.

---

## Altium Project Setup

1. Create a new PCB project: `Payload_Carrier.PrjPcb`
2. Add four schematic sheets:
   - `Sheet1_SODIMM_Power.SchDoc`
   - `Sheet2_Cameras.SchDoc`
   - `Sheet3_CSKB_Stack.SchDoc`
   - `Sheet4_M2_USB_UART.SchDoc`
3. Each sheet uses **A3 landscape** format. The SO-DIMM symbol is large;
   A4 will not fit it comfortably with its support circuitry.
4. Set project's designator scope to **"Flat"** so R1, C1, U1, etc. are
   unique across all four sheets.
5. The board outline, M2.5 mounting hole pattern, and CSKB H1/H2 header
   placement should match the stack template (see `system/
   interfaces/cskb_pinmap.md` for the stack template reference).

### Sheet Cross-Reference

| Sheet | Title | Major contents |
|---|---|---|
| 1 | SO-DIMM, Power & Sequencing | TE 2309413-1 connector symbol, VBAT→5V buck, MODULE_ID strap, decoupling, POWER_EN / SYS_RESET / SHUTDOWN_REQ sequencing, 74LVC2G07 dual buffer |
| 2 | Cameras | 3× 15-pin FFC, PCA9546A I²C mux, J_TRIG header, CAM_PWDN routing |
| 3 | CSKB Stack Interface | H1/H2 PC/104-style stack connectors, I²C to IHU, CAN xcvr (DNP), PAYLOAD_EN gate, fault/sleep wiring, status LEDs |
| 4 | M.2 + USB Recovery + Debug UART | M.2 2230 Key-E socket, USB-2 recovery test header, 1.8V↔3.3V UART level shifter, FORCE_RECOVERY jumper |

### Net Name Convention

Use these global net names consistently across all sheets per
`hardware/conventions/net_naming.md`. Use **power port symbols** (not
net labels) for supply rails so they are global automatically. Stack
rails entering on the CSKB use their canonical names (`+3V3`, `+5V`,
`VBAT`); board-local derived rails carry a scope suffix
(`+5V_ORIN`, `+3V3_M2`, `+1V8_MOD`). Inter-board signals use the
canonical CSKB net names from `system/interfaces/cskb_pinmap.md`
(`SCL_SYS`, `SDA_SYS`, `PAYLOAD_EN`, `PAYLOAD_FAULT_N`,
`PAYLOAD_SLEEP_REQ_N`).

| Net Name | Type | Description |
|---|---|---|
| `VBAT` | Power port | Battery bus from CSKB H2.45/H2.46, 6.0–8.4 V |
| `+5V_ORIN` | Power port | Local buck output to Orin VDD_IN, 5.0 V, ≥3 A |
| `+3V3` | Power port | From CSKB H2.27/H2.28 — feeds cams, mux, M.2 |
| `+3V3_M2` | Power port | M.2 socket 3.3V branch, downstream of FB_M2 |
| `+1V8_MOD` | Power port | Orin's `SYS_VDD_1V8` output (pin 213-ish — verify) |
| `GND` | Power port | Single ground (analog/digital split unnecessary here) |
| `PWR_EN` | Net label | Carrier POR → Orin `POWER_EN` (SO-DIMM 237) |
| `SYS_RESET_N` | Net label | Bidir reset, Orin `SYS_RESET*` (SO-DIMM 239) |
| `SHDN_REQ_N` | Net label | Orin `SHUTDOWN_REQ*` (5V OD), SO-DIMM 233 |
| `FRC_RCVRY_N` | Net label | Orin `FORCE_RECOVERY*` (1.8V), SO-DIMM 214 |
| `SLP_WAKE_N` | Net label | Orin `SLEEP/WAKE*` (5V CMOS in), SO-DIMM 240 |
| `MOD_SLEEP_N` | Net label | Orin `MOD_SLEEP*` (1.8V out), SO-DIMM 178 |
| `PAYLOAD_EN` | Net label | From CSKB H1.50 — gates the VBAT→5V buck |
| `PAYLOAD_FAULT_N` | Net label | To CSKB H2.47 — 3.3V OD, from 74LVC2G07 ch.1 |
| `PAYLOAD_SLEEP_REQ_N` | Net label | From CSKB H2.48 — direct to `SLP_WAKE_N` |
| `CAM_I2C_SCL` | Net label | Orin `CAM_I2C_SCL` for cameras (SO-DIMM 213), 3.3V — board-internal bus |
| `CAM_I2C_SDA` | Net label | Orin `CAM_I2C_SDA` for cameras (SO-DIMM 215), 3.3V |
| `SCL_SYS` | Net label | Stack I²C clock (Orin `I2C0_SCL`, SO-DIMM 185) ↔ CSKB H1.43. Canonical per cskb_pinmap.md. |
| `SDA_SYS` | Net label | Stack I²C data (Orin `I2C0_SDA`, SO-DIMM 187) ↔ CSKB H1.41. |
| `CAM0..2_*` | Net label | CSI clock/data pairs, PWDN per camera (Sheet 2) |
| `CAM_TRIG_1V8` | Net label | Shared trigger GPIO, 1.8V (SO-DIMM 128) |
| `MUX_RST_N_1V8` | Net label | 1.8V input to 74LVC2G07 ch.2 |
| `MUX_RST_N_3V3` | Net label | 3.3V OD output to PCA9546A `RESET#` |
| `M2_PETP0`, `M2_PETN0` | Net label | PCIe TX after AC caps |
| `M2_PERP0`, `M2_PERN0` | Net label | PCIe RX (no caps on carrier side) |
| `M2_REFCLKP`, `M2_REFCLKN` | Net label | 100 MHz REFCLK |
| `M2_USB_DP`, `M2_USB_DN` | Net label | BT-over-USB to Orin USB1 |
| `M2_PERST_N`, `M2_CLKREQ_N`, `M2_PEWAKE_N` | Net label | PCIe control (3.3V OD) |
| `DBG_UART_TX_1V8`, `DBG_UART_RX_1V8` | Net label | Orin side, 1.8V |
| `DBG_UART_TX_3V3`, `DBG_UART_RX_3V3` | Net label | Header side, 3.3V |
| `USB0_D_P`, `USB0_D_N` | Net label | Recovery USB 2.0 differential |

Net labels referencing the same signal but on different sides of a
translator MUST differ in name (e.g., `MUX_RST_N_1V8` vs
`MUX_RST_N_3V3`). This makes the ERC visualize the level shift.

---

## Sheet 1: SO-DIMM, Power & Sequencing

This sheet has three sections: the SO-DIMM symbol itself (central), the
VBAT→5V buck (top-left), and the power-sequencing / buffer block
(bottom). The SO-DIMM symbol is the central nervous system of the
schematic; every other sheet ports signals into and out of it.

### Section A: Module Connector (Center of Sheet)

#### J1 — Orin Nano SO-DIMM (TE 2309413-1)

Search Manufacturer Part Search for "2309413-1" or place from your
component library. The footprint is a **0.5 mm pitch 260-pin SO-DIMM
right-angle socket**. The symbol is large — split it into multiple
visual sub-symbols if Altium supports multi-part components, or use a
single tall symbol grouped by function (power, CSI, USB, control,
etc.) along the symbol edges.

**Pin assignments:** all 260 pins per
`hardware/payload_compute/design/payload_carrier_pinmap.md` — that file is the
authority. Do NOT re-derive pin numbers from the datasheet at the
schematic level; copy them from the pinmap so revs stay in sync.

Group the pins on the symbol body in this order (top to bottom):

1. **VDD_IN (10 pins, 251–260)** — left edge, all tied together
2. **GND (many)** — distributed along both edges
3. **MODULE_ID (217)** — tied to GND
4. **CSI ports 0–4** — left side, grouped by lane
5. **PCIE1** (167/169/172/173/174/175/182/183) and **PCIE_WAKE\*** (179) — right side (goes to Sheet 4 M.2)
6. **USB0** (109/111) and **USB1** (115/117) — right side
7. **Power sequencing pins** (237, 239, 233, 214, 240, 178) — bottom
8. **I2C0** (185/187) and **CAM_I2C** (213/215) — bottom
9. **UART1** (203/205) — bottom
10. **GPIO00–14** + clock outputs — bottom-right
11. **Explicit NC pins** — collected into a single "NC" net label
    block at the bottom (see pinmap §7)

#### Text Frame (Place > Text Frame, top of sheet):

> SO-DIMM MODULE CONNECTOR — TE 2309413-1, 260-pin 0.5 mm SO-DIMM.
> Pinout is governed by payload_carrier_pinmap.md. v0.1 module variant:
> Jetson Orin Nano devkit (microSD on module). MODULE_ID (pin 217) is
> tied to GND on the carrier to indicate 5V-only VDD_IN per DG-10931
> §6.1. If a wide-range production module is later substituted, this
> tie must be revisited and the buck topology re-evaluated.

#### MODULE_ID Strap

| Ref | Value | Package | Connection |
|---|---|---|---|
| (direct trace) | — | — | SO-DIMM pin 217 → `GND` |

No resistor, no jumper. Direct trace. Annotate on the schematic with a
small "MODULE_ID = GND (5V-only mode)" callout near pin 217.

### Section B: VBAT → +5V_ORIN Buck (Top-Left of Sheet)

The Orin Nano draws up to 3 A @ 5 V in 15 W mode. Use a synchronous
buck rated comfortably above 3 A continuous, accepting 6.0–8.4 V Vin
(VBAT range) with margin to 12 V (margin for misconfigured bench supply).

#### U2 — TPS62933F Synchronous Buck

The same part the EPS board uses for the +3V3 and +5V stack rails
(parts commonality). 3 A continuous, 3.8–30 V input, SOT-583. JLCPCB
basic part.

**Pinout (TPS62933F, SOT-583):**

| Pin | Name | Function |
|---|---|---|
| 1 | RT | Switching frequency (float = 500 kHz) |
| 2 | EN | Enable — gated by `PAYLOAD_EN` |
| 3 | VIN | `VBAT` |
| 4 | GND | `GND` |
| 5 | SW | Switch node → L2 |
| 6 | BST | Bootstrap cap to SW (100 nF) |
| 7 | SS | Soft-start cap to GND (33 nF) |
| 8 | FB | Feedback divider tap |

**Pin Connections:**

| Pin | Connect To | Notes |
|---|---|---|
| 1 | NC (float) | Selects 500 kHz |
| 2 | `PAYLOAD_EN` | Direct from CSKB H1.50, 3.3V CMOS (V_IH(EN) = 1.21 V — comfortable) |
| 3 | `VBAT` via C10 + C11 | Input bypass |
| 5 | L2 (4.7 µH) → `+5V_ORIN` | Switch node |
| 6 | C12 (100 nF) to SW | Bootstrap |
| 7 | C13 (33 nF) to GND | ~5 ms soft-start |
| 8 | R10/R11 divider | Output sense |

#### Component Table

| Ref | Value | Package | Connection | Notes |
|---|---|---|---|---|
| U2 | TPS62933FDRLR | SOT-583 | per pinout above | JLCPCB basic part |
| C10 | 10 µF, 25 V, X7R ceramic | 1210 | `VBAT` → `GND` | Bulk input bypass |
| C11 | 100 nF, 50 V, X7R ceramic | 0402 | `VBAT` → `GND`, at VIN pin | HF input bypass — MUST be at the pin |
| L2 | 4.7 µH, ≥ 5 A Isat, ≤ 30 mΩ DCR | 5×5 mm shielded SMD | SW → `+5V_ORIN` | Würth 74438357047 |
| C12 | 100 nF, 16 V, X5R ceramic | 0402 | BST → SW | Bootstrap |
| C13 | 33 nF, 16 V, X7R ceramic | 0402 | SS → `GND` | Soft-start, ~5 ms |
| R10 | 52.3 kΩ, 1%, 0603 | 0603 | `+5V_ORIN` → FB | Top of FB divider |
| R11 | 10 kΩ, 1%, 0603 | 0603 | FB → `GND` | Bottom of FB divider |
| C14 | 22 µF, 10 V, X7R | 1210 | `+5V_ORIN` → `GND` | Output bulk |
| C15 | 22 µF, 10 V, X7R | 1210 | `+5V_ORIN` → `GND` | Output bulk |
| C16 | 100 nF, 16 V, X7R | 0402 | `+5V_ORIN` → `GND` | Output HF |

**Feedback calculation (datasheet §10.2.2.2):**
R_FBT = ((5.0 − 0.8) / 0.8) × 10 kΩ = **52.5 kΩ** → nearest E96 = **52.3 kΩ**.
Resulting V_OUT = 0.8 × (1 + 52.3 / 10) = **4.984 V** (within ±1 %).

#### Note (Place > Note, next to U2):

> +5V_ORIN buck: TPS62933F, 3 A continuous, 500 kHz, ~5 ms soft-start.
> Vin range 3.8–30 V comfortably accepts VBAT (6.0–8.4 V). Gated by
> PAYLOAD_EN from CSKB H1.50 — the buck is OFF whenever the IHU says so.
> The 3 A continuous rating is exactly at the Orin Nano peak (15 W mode).
> If bring-up shows thermal stress or current limit hits, the drop-in
> upgrade is the **LM61460-Q1** (6 A, HSOP-8, similar BOM but different
> footprint — flag as a v0.2 stretch).

#### Note (Place > Note, next to C11):

> C11 (100 nF input bypass) MUST be placed directly across VIN and GND
> pins with the shortest possible trace. This is the high-frequency
> commutation loop and is the most layout-critical component on the buck.

### Section C: SO-DIMM Decoupling

Distribute decoupling capacitors on the **`+5V_ORIN`** net at the
SO-DIMM connector pins labeled **`VDD_IN`** (module-side pin name per
NVIDIA's datasheet — pins 251–260, 10 pins in parallel). Use the
values from DG-10931 §6 Table 6-1 (or the latest revision). Suggested
starting point:

| Ref | Value | Package | Placement |
|---|---|---|---|
| C20, C21 | 100 µF, 10 V, polymer | D-case | Bulk on `+5V_ORIN`, within 10 mm of the SO-DIMM `VDD_IN` block |
| C22–C26 | 10 µF, 10 V, X7R | 0805 | One per pair of `VDD_IN` pins, < 5 mm |
| C27–C36 | 100 nF, 10 V, X7R | 0402 | One per `VDD_IN` pin, < 2 mm |

Refer to the design guide for exact distribution. Do NOT skip any —
the Orin's PMIC has tight transient response requirements that the
on-module caps alone don't meet.

### Section D: Power Sequencing & Buffers (Bottom of Sheet)

This section implements the recommended Orin power-up sequence and
the two 74LVC2G07 buffer channels.

#### Sequencing per DG-10931 §6.3

The recommended sequence is:

1. VBAT applied
2. **PAYLOAD_EN asserted** by IHU → buck enables → VDD_IN ramps to 5 V
3. Buck reaches regulation (≥10 ms after EN) → **POWER_EN asserted** to module
4. Module performs internal sequencing → **SYS_RESET\*** rises (open-drain release)
5. Carrier may now apply downstream 3.3 V / 1.8 V loads (M.2, level shifters) — they must rise within 1.5 ms / 4 ms of SYS_RESET\* release per DG-10931 §6.3

For v0.1 we keep the sequencer simple: tie POWER_EN to a delayed copy
of the buck's PG (power good) output. The TPS62933F doesn't have a PG
pin, so use a simple RC delay on the EN-to-POWER_EN path instead.

#### POWER_EN Generation

```
+5V_ORIN ──┬── R30 (10k) ──┬── PWR_EN ──→ SO-DIMM pin 237 (POWER_EN)
              │               │
              │              C40 (10uF)
              │               │
              │              GND
              │
            R31 (49.9k)
              │
             GND
```

Time constant: τ = 10 kΩ × 10 µF = 100 ms — well above the buck's
~5 ms soft-start and gives the module ~95 ms of stable VDD_IN before
POWER_EN goes high. Voltage divider with R31 sets the steady-state
PWR_EN voltage to ~3.3 V (acceptable per module spec).

| Ref | Value | Package | Connection |
|---|---|---|---|
| R30 | 10 kΩ, 1% | 0402 | `+5V_ORIN` → `PWR_EN` |
| R31 | 49.9 kΩ, 1% | 0402 | `PWR_EN` → `GND` |
| C40 | 10 µF, 10 V, X7R | 0805 | `PWR_EN` → `GND` |

#### Note (Place > Note, next to R30/R31/C40):

> POWER_EN delay generator. The TPS62933F has no PG output, so we use
> an RC delay (~100 ms) from +5V_ORIN-stable to PWR_EN-high. This
> guarantees the module sees stable VDD_IN before POWER_EN asserts.
> If a fault forces +5V_ORIN to collapse, C40 discharges through
> R31 and PWR_EN falls to 0 within ~50 ms — fast enough to avoid
> brown-out of the SoC. **Open item:** consider replacing with a
> dedicated supervisor IC (TPS3702, NCV30161) in v0.2 for a clean
> deterministic delay and a discrete PG output.

#### SYS_RESET\* Pull-Up

| Ref | Value | Package | Connection |
|---|---|---|---|
| R32 | 10 kΩ, 1% | 0402 | `SYS_RESET_N` → `+1V8_MOD` |

The module also has a 10 kΩ PU to VDD_1V8 internally. The carrier-side
pull-up adds redundancy; remove if the bus loading is excessive.

Add a test point `TP1 = SYS_RESET_N` so a logic analyzer can capture
the rise edge during bring-up.

#### FORCE_RECOVERY\* Jumper

`FRC_RCVRY_N` is the strap that puts the module into USB recovery
mode. It is only consulted at SYS_RESET\* release, then becomes a
regular GPIO.

```
+1V8_MOD ── R33 (10k) ──┬── FRC_RCVRY_N ──→ SO-DIMM pin 214
                        │
                       JP1 (2-pin header, normally OPEN)
                        │
                       GND
```

| Ref | Value | Package | Connection |
|---|---|---|---|
| R33 | 10 kΩ, 1% | 0402 | `+1V8_MOD` → `FRC_RCVRY_N` |
| JP1 | 2-pin 2.54 mm header | THT | `FRC_RCVRY_N` → `GND` |

Default: JP1 open, FRC_RCVRY_N held HIGH by R33, module boots normally.
Install JP1 jumper before power-on to enter USB recovery mode.

Silkscreen: "RECOVERY — Jumper to enter USB recovery mode".

#### Note (Place > Note, next to JP1):

> USB recovery mode strap. Per DG-10931 §3.2, FORCE_RECOVERY\* must be
> held LOW when SYS_RESET\* releases for the module to enter recovery
> mode. Install jumper JP1, then power-cycle the board. Once Linux
> boots, this pin is a regular GPIO and the jumper state no longer
> matters.

#### 74LVC2G07 Dual Open-Drain Buffer (U4) — VCC = +1V8_MOD

Single 74LVC2G07 (SOT-23-6, TSSOP-6, or SOT-26 depending on JLCPCB
variant — see BOM note below) handles two open-drain translation
functions:

| Channel | Input net | Output net | Purpose |
|---|---|---|---|
| 1 | `SHDN_REQ_N` (5V OD, ~5 kΩ PU to VDD_IN on module) | `PAYLOAD_FAULT_N` (3.3V OD, PU on IHU side per cskb_pinmap.md Rule 3) | Translate Orin shutdown request to CSKB stack |
| 2 | `MUX_RST_N_1V8` (1.8V CMOS, Orin GPIO07) | `MUX_RST_N_3V3` (3.3V OD, R34 PU on carrier) | Translate Orin GPIO to PCA9546A `RESET#` |

**Pinout (74LVC2G07, 6-pin):**

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | 1A | `SHDN_REQ_N` (from SO-DIMM 233) | Channel 1 input — 5V OD source, 5V-tolerant input |
| 2 | GND | `GND` | |
| 3 | 2A | `MUX_RST_N_1V8` (from SO-DIMM 206, GPIO07) | Channel 2 input — 1.8V CMOS source |
| 4 | 2Y | `MUX_RST_N_3V3` → off-sheet port to Sheet 2 | Channel 2 OD output → PCA9546A `RESET#` |
| 5 | VCC | `+1V8_MOD` | **Note: VCC at 1.8V, not 3.3V — see analysis below** |
| 6 | 1Y | `PAYLOAD_FAULT_N` → off-sheet port to Sheet 3 | Channel 1 OD output → CSKB H2.47 |

##### Why VCC = +1V8_MOD (not +3V3)

The 74LVC family has a **split V_IH spec depending on VCC range**
(per TI/Nexperia datasheets):

- **VCC = 2.7 V to 5.5 V:** V_IH(min) = **2.0 V** (TTL-compatible)
- **VCC = 1.65 V to 2.7 V:** V_IH(min) = **0.65 × VCC**

If we ran this part at VCC = +3V3, channel 2 would fail: the 1.8 V
HIGH from Orin GPIO (V_OH(min) ~1.65 V) does NOT meet the 2.0 V
V_IH(min). The buffer would interpret a legitimate 1.8 V HIGH as
indeterminate or LOW — non-compliant, and over temperature would glitch.

Running at VCC = +1V8_MOD eliminates this:
- **V_IH(min) = 0.65 × 1.8 = 1.17 V** — comfortably met by both inputs
  (5 V from channel 1, 1.8 V from channel 2)
- LVC inputs remain **5 V-tolerant regardless of VCC**, so channel 1's
  5 V OD source is fine
- Both outputs are **open-drain** — VCC does not constrain the output
  HIGH level. The external pull-ups set HIGH (3.3 V on IHU side for
  ch.1; R34 to +3V3 on carrier for ch.2)
- Output drive current drops from ~24 mA (VCC=3.3 V) to ~8 mA
  (VCC=1.8 V) — still plenty for OD with kΩ-class pull-ups (~330 µA
  load through 10 kΩ to 3.3 V)
- Propagation delay increases slightly (~6 ns → ~10 ns) — irrelevant
  for these slow control signals

##### Component table

| Ref | Value | Package | Connection |
|---|---|---|---|
| U4 | 74LVC2G07 (e.g. Nexperia 74LVC2G07GW or Diodes 74LVC2G07W6-7) | TSSOP-6 / SOT-26 — pick whichever is in JLCPCB stock; both are rework-friendly | per pinout above, VCC = `+1V8_MOD` |
| C45 | 100 nF, 16 V, X7R ceramic | 0402 | VCC pin (pin 5) → `GND`, at the package |
| R34 | 10 kΩ, 1% | 0402 | `MUX_RST_N_3V3` → `+3V3` (OD pull-up for channel 2 output) |

**JLCPCB variant note:** prefer **74LVC2G07GW** (Nexperia, TSSOP-6 /
SC-74A) for easiest hand-rework. **74LVC2G07W6-7** (Diodes, SOT-26)
is a fine alternate. Avoid the **GV** variant (smaller package,
harder to rework).

**BOM hint for Nexperia GW variants** — same silicon, same TSSOP-6
footprint, same pinout. Pick by build context:

| Order code | Grade | Temp range | When to use |
|---|---|---|---|
| `74LVC2G07GW,125` | Standard commercial (the `,125` is just a reel-size suffix, typically 3000 pcs / 7" reel) | −40 to +85 °C industrial | **v0.1 prototype, bench, dev boards** — cheaper, usually in stock |
| `74LVC2G07GW-Q100H` | AEC-Q100 automotive-qualified (more lot screening, wider guaranteed temp range) | −40 to +125 °C (Q100 Grade 1) | **Future flight build** — nicer match for LEO thermal swings; drop-in upgrade later |

For the current build, **`74LVC2G07GW,125`** is the default
BOM line. Reserve the `-Q100H` upgrade for the flight-cut variant.

**Pull-up note for PAYLOAD_FAULT_N:** the IHU side supplies the
pull-up on H2.47 per `cskb_pinmap.md` Rule 3, so do NOT add a
pull-up on the payload side.

**Pull-up note for MUX_RST_N_3V3:** R34 is on the **payload** side
because the mux RESET# input has no other PU source.

### Section E: Module Sleep / Wake Routing

| Net | SO-DIMM pin | Routing |
|---|---|---|
| `SLP_WAKE_N` | 240 | Direct to CSKB H2.48 (off-sheet port to Sheet 3) — no level shifter for v0.1 (pin rated 5V CMOS but accepts 3.3V drive cleanly) |
| `MOD_SLEEP_N` | 178 | Route to TP2 (test point) for v0.1; not used externally |
| `CLK_32K_OUT` | 210 | Route to TP3 (test point) for v0.1; M.2 SUSCLK is NC (pinmap §9.7) |

### Sheet 1 Off-Sheet Ports

Place these on the right edge of the sheet, all as **Bidirectional**
unless noted:

| Port | Direction | Goes to |
|---|---|---|
| `+5V_ORIN` | Output | Power port (global, automatic) |
| `+3V3` | Input | Sheet 3 (sources from CSKB) |
| `+1V8_MOD` | Output | Sheet 4 (UART shifter low side) |
| `PWR_EN`, `SYS_RESET_N` | (internal, no port) | — |
| `PAYLOAD_FAULT_N` | Output | Sheet 3 |
| `SLP_WAKE_N` | Input | Sheet 3 (`PAYLOAD_SLEEP_REQ_N` from CSKB) |
| `MUX_RST_N_3V3` | Output | Sheet 2 (PCA9546A `RESET#`) |
| `PAYLOAD_EN` | Input | Sheet 3 |
| `CAM_I2C_SCL`, `CAM_I2C_SDA` | Bidir | Sheet 2 (camera mux) |
| `I2C0_SCL`, `I2C0_SDA` | Bidir | Sheet 3 (IHU I²C) |
| `CAM_TRIG_1V8` | Output | Sheet 2 (J_TRIG header) |
| `CAM0_PWDN`..`CAM2_PWDN` | Output | Sheet 2 |
| 12 × CSI differential pairs | Output | Sheet 2 |
| 8 × PCIE1 pairs + control | Bidir | Sheet 4 |
| `PCIE_WAKE_N` | Bidir | Sheet 4 |
| `USB0_D_P/N`, `USB1_D_P/N` | Bidir | Sheet 4 |
| `DBG_UART_TX_1V8`, `DBG_UART_RX_1V8` | Bidir | Sheet 4 |
| `CAN_TX`, `CAN_RX` | Bidir | Sheet 3 |
| `FRC_RCVRY_N` | (internal — JP1 on this sheet) | — |

---

## Sheet 2: Cameras

This sheet contains three IMX296 Pi GS Camera interfaces, the PCA9546A
I²C mux, and the J_TRIG hardware-sync header.

### Text Frame (top of sheet):

> CAMERAS — 3× Raspberry Pi Global Shutter Camera (Sony IMX296). Each
> camera connects via the 15-pin 1.0 mm Pi-standard CSI FFC. The IMX296
> has a fixed I²C address (0x1A); a PCA9546A 4-channel I²C mux gives
> each camera its own slot. The XTR (external trigger) pin on each
> camera is NOT on the FFC — it is on a back-edge solder pad and is
> wired through a 3-way Y-splice harness from the J_TRIG header.
> XTR is 1.8 V logic, so the Orin's 1.8 V trigger GPIO drives it
> directly with only series resistors for ESD.

### Section A: PCA9546A I²C Mux (Top of Sheet)

#### U10 — PCA9546A (4-channel I²C mux, TSSOP-16)

Pinout per NXP `PCA9546APW,118` datasheet (NXP doc PCA9546A v5.1).
**Verify against your Altium symbol library before placing — the
pinout in this table was corrected 2026-05-24 from an earlier
incorrect version.**

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | A0 | `GND` | Address strap |
| 2 | A1 | `GND` | Address strap |
| 3 | RESET\* | `MUX_RST_N_3V3` (from Sheet 1, U4 ch.2 / pin 4) | Active-low, OD; R34 (10 kΩ) PU to `+3V3` already on Sheet 1 |
| 4 | SD0 | `CAM0_SDA` | Channel 0 data → Camera #0 |
| 5 | SC0 | `CAM0_SCL` | Channel 0 clock → Camera #0 |
| 6 | SD1 | `CAM1_SDA` | Channel 1 data → Camera #1 |
| 7 | SC1 | `CAM1_SCL` | Channel 1 clock → Camera #1 |
| 8 | VSS | `GND` | Ground |
| 9 | SD2 | `CAM2_SDA` | Channel 2 data → Camera #2 |
| 10 | SC2 | `CAM2_SCL` | Channel 2 clock → Camera #2 |
| 11 | SD3 | NC | Channel 3 unused |
| 12 | SC3 | NC | Channel 3 unused |
| 13 | A2 | `GND` | Address strap → I²C addr = 0b1110_000 = **0x70** (with A2=A1=A0=GND) |
| 14 | SCL | `CAM_I2C_SCL` (from Sheet 1) | Master-side clock |
| 15 | SDA | `CAM_I2C_SDA` (from Sheet 1) | Master-side data |
| 16 | VDD | `+3V3` | 3.3 V supply |

Per `payload_carrier_pinmap.md` §3.4: **do NOT add pull-ups on the
master-side CAM_I2C bus — the Orin module already has 2.2 kΩ pull-ups
to 3.3 V internally.** Add 4.7 kΩ pull-ups on each downstream channel
(SC0/SD0, SC1/SD1, SC2/SD2) since the cameras don't have on-PCB
pull-ups for the FFC I²C signals.

| Ref | Value | Package | Connection |
|---|---|---|---|
| U10 | PCA9546A (NXP `PCA9546APW,118` preferred, TI `PCA9546APWR` alt) | TSSOP-16 | per pinout above |
| C50 | 100 nF, 16 V, X7R | 0402 | `+3V3` → `GND` at VCC pin |
| R50, R51 | 4.7 kΩ, 1% | 0402 | `CAM0_SCL`/`CAM0_SDA` → `+3V3` |
| R52, R53 | 4.7 kΩ, 1% | 0402 | `CAM1_SCL`/`CAM1_SDA` → `+3V3` |
| R54, R55 | 4.7 kΩ, 1% | 0402 | `CAM2_SCL`/`CAM2_SDA` → `+3V3` |

**JLCPCB BOM hint:** **`PCA9546APW,118`** (NXP — the chip's original
designer) is ~2.4× cheaper than the TI `PCA9546APWR` second-source
(~$0.39 vs ~$0.93 at typical JLCPCB pricing) and usually has more
stock. Same TSSOP-16 footprint, pinout, and electrical behavior —
silicon-compatible drop-in. NXP's `,118` suffix is just their 13"
reel-size code.

#### Note (Place > Note, next to U10):

> PCA9546A: 4-channel I²C mux. The IMX296 has fixed addr 0x1A —
> three sensors on one bus would collide. The mux gives each camera
> its own slot. Channel 3 is left unconnected. Address = 0x70
> (A2/A1/A0 = 000). Master-side CAM_I2C has on-module Orin pull-ups
> (2.2 kΩ to 3.3 V per DG-10931) — do NOT add carrier-side pull-ups
> on the master bus. Add 4.7 kΩ pull-ups per downstream channel.

### Section B: Camera FFC Connectors (Center of Sheet)

Three identical FFC connectors: J10 (Camera #0), J11 (Camera #1),
J12 (Camera #2). Use the Pi-standard **15-pin 1.0 mm pitch CSI**
connector (Amphenol SFW15R-2STE1LF or equivalent).

#### J10 — Camera #0 FFC (representative; J11, J12 identical wiring with their own CSI lanes)

| FFC pin | Signal | Carrier net | Notes |
|---|---|---|---|
| 1 | GND | `GND` | |
| 2 | CSI Data 1 − | `CAM0_D1_N` (from SO-DIMM CSI0_D1_P — **P/N swap on module**) | |
| 3 | CSI Data 1 + | `CAM0_D1_P` (from SO-DIMM CSI0_D1_N — **P/N swap on module**) | |
| 4 | GND | `GND` | |
| 5 | CSI Data 0 − | `CAM0_D0_N` | |
| 6 | CSI Data 0 + | `CAM0_D0_P` | |
| 7 | GND | `GND` | |
| 8 | CSI Clock − | `CAM0_CLK_N` | |
| 9 | CSI Clock + | `CAM0_CLK_P` | |
| 10 | GND | `GND` | |
| 11 | CAM_GPIO0 (PWDN) | `CAM0_PWDN` (from Sheet 1) | See §3.3 in pinmap re: voltage |
| 12 | CAM_GPIO1 (LED EN) | NC | |
| 13 | SCL | `CAM0_SCL` (from mux ch 0) | |
| 14 | SDA | `CAM0_SDA` (from mux ch 0) | |
| 15 | +3.3V | `+3V3` | Per Pi spec ≤250 mA per camera |

**Note: P/N polarity swap on CSI0 and CSI1.** Per DG-10931 §10, the
Orin module has a P/N swap on **CSI_0_D1** and **CSI_1_D0**. Compensate
at the FFC end so the CSI-2 sublayer can use D-PHY lane deskew. **CSI2
has no module-side swap.** The pinmap (§3.3) has the per-camera
breakdown — copy it verbatim.

#### Note (Place > Note, next to J10):

> Pi GS Camera FFC, 15-pin 1.0 mm pitch. Camera #0 = 750 nm continuum
> channel. Wiring verified against `payload_carrier_pinmap.md` §3.3.
> P/N swap on the D1 pair is intentional and is at the Orin module —
> swap back at the FFC end. ALL three cameras: do NOT route the FFC
> pin 12 (LED_EN); leave NC. PWDN voltage is an open item — verify
> against the Pi GS Camera schematic whether FFC pin 11 is 3.3V or
> 1.8V CMOS.

### Section C: Camera Trigger Header (Bottom-Right)

#### J13 — J_TRIG (2-pin JST-SH, 1.0 mm pitch)

| Pin | Signal | Carrier net | Notes |
|---|---|---|---|
| 1 | `CAM_TRIG_1V8` (from Sheet 1) | 1.8 V CMOS, single shared trigger | |
| 2 | `GND` | Return | |

Series resistors are on the wire harness (3× 100 Ω, one per camera),
not on the carrier. The carrier exposes only the 2-pin header.

| Ref | Value | Package | Connection |
|---|---|---|---|
| J13 | JST SH 2-pin (BM02B-SRSS-TB) | 2-pin SMD | per pinout above |

#### Note (Place > Note, next to J13):

> J_TRIG — single shared 1.8 V hardware-sync trigger for all 3
> cameras. The Orin's 1.8 V GPIO drives the cameras' XTR pads
> directly (XTR is also 1.8 V). The wire harness fans out 1→3
> through a Y-splice with 100 Ω series ESD resistor at each camera.
> Total fan-out impedance ≈ 33 Ω from the Orin — comfortable.
> See pinmap §3.5 and the bringup-doc harness assembly procedure
> (TBD: `hardware/payload_compute/bringup/`).

### Sheet 2 Off-Sheet Ports

| Port | Direction | Goes to |
|---|---|---|
| `CAM_I2C_SCL`, `CAM_I2C_SDA` | Bidir | Sheet 1 |
| `MUX_RST_N_3V3` | Input | Sheet 1 |
| `CAM_TRIG_1V8` | Input | Sheet 1 |
| `CAM0_PWDN`..`CAM2_PWDN` | Input | Sheet 1 |
| 12× CSI diff pairs | Input | Sheet 1 |
| `+3V3`, `GND` | — | Global power ports |

---

## Sheet 3: CSKB Stack Interface

This sheet contains the H1/H2 stack header connectors and all signals
that cross the stack boundary: I²C to IHU, CAN (DNP), fault
propagation, sleep request, PAYLOAD_EN, and stack power consumption.

### Text Frame (top of sheet):

> CSKB STACK INTERFACE — H1/H2 PC/104-style 52-pin headers per Pumpkin
> CSKB spec. Pin assignments are authoritative in
> `system/interfaces/cskb_pinmap.md` — copy from that file, do NOT
> re-derive. Payload pulls VBAT and +3V3 from the stack; +5V is NOT
> used (Orin Nano peak 3 A exceeds stack +5V 2 A rating).

### Section A: H1 / H2 Connectors

#### J20 — H1 (52-pin stack-through, Samtec ESQ-126-XX-X-D)
#### J21 — H2 (52-pin stack-through, Samtec ESQ-126-XX-X-D)

The carrier uses **stack-through** parts (signals pass through), not
endpoint parts. Place J20 and J21 on the right edge of the sheet so
their right-edge pins (going off-sheet) become the off-sheet ports.

Pin-by-pin assignments per `cskb_pinmap.md`. Critical payload-facing
pins for this sheet:

| H-pin | CSKB net | Direction | Connect to |
|---|---|---|---|
| H1.41 | `I2C_SDA` | Bidir | `I2C0_SDA` (Sheet 1, SO-DIMM 187) |
| H1.43 | `I2C_SCL` | Bidir | `I2C0_SCL` (Sheet 1, SO-DIMM 185) |
| H1.50 | `PAYLOAD_EN` | Input | `PAYLOAD_EN` (to Sheet 1 buck U2 EN pin) |
| H1.51 | `CAN_H` | Bidir | CAN xcvr U30 (DNP) |
| H1.52 | `CAN_L` | Bidir | CAN xcvr U30 (DNP) |
| H2.25/26 | `+5V` | — | **NC on this board** — confirm pin is not back-driven |
| H2.27/28 | `+3V3` | Power | `+3V3` (feeds cameras, mux, M.2) |
| H2.29–32 | `GND` | Power | `GND` (multiple pins; tie all to plane) |
| H2.45/46 | `VBAT` | Power | `VBAT` (to Sheet 1 buck U2 VIN) |
| H2.47 | `PAYLOAD_FAULT_N` | Output | `PAYLOAD_FAULT_N` (from Sheet 1 U4 ch.1 / pin 6) |
| H2.48 | `PAYLOAD_SLEEP_REQ_N` | Input | `SLP_WAKE_N` (to Sheet 1, SO-DIMM 240) |

All other H1/H2 pins NOT used by the payload should still be brought
into the connector symbol (since they pass through), but left as NC
nets on this board.

### Section B: CAN Transceiver (DNP for v0.1)

The CAN footprints are populated empty for v0.1 — provision the traces
and pads but leave the IC, terminator, and supply caps unpopulated.

#### U30 — TCAN332GDR (DNP)

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | TXD | `CAN_TX` (from Sheet 1, SO-DIMM 145) | From Orin CAN controller |
| 2 | GND | `GND` | |
| 3 | VCC | `+3V3` | 3.3 V supply |
| 4 | RXD | `CAN_RX` (to Sheet 1, SO-DIMM 143) | To Orin CAN controller |
| 5 | (NC) | — | |
| 6 | CAN_L | `CAN_L` → H1.52 via 60.4 Ω/60.4 Ω split-term | DNP |
| 7 | CAN_H | `CAN_H` → H1.51 via 60.4 Ω/60.4 Ω split-term | DNP |
| 8 | (NC) | — | |

| Ref | Value | Package | DNP? | Connection |
|---|---|---|---|---|
| U30 | TCAN332GDR | SOIC-8 | **DNP** | per pinout |
| C70 | 100 nF X7R 0402 | 0402 | **DNP** | VCC bypass |
| R70 | 60.4 Ω, 1%, 0402 (E96 — exact 60 Ω doesn't exist in any std series) | 0402 | **DNP** | CAN_H to midpoint |
| R71 | 60.4 Ω, 1%, 0402 (E96) | 0402 | **DNP** | midpoint to CAN_L |
| C71 | 4.7 nF, 50 V, X7R 0402 | 0402 | **DNP** | midpoint to GND (split termination) |

Mark all of U30 / C70 / R70 / R71 / C71 with **DNP** on the schematic
(Altium Variant: "Iter1-Flight" → these components Not Fitted).

##### Topology — split termination network

R70/R71/C71 form a **split termination** across the differential
pair — they are NOT series elements between U30 and the bus. U30's
pin 7 (CAN_H) and pin 6 (CAN_L) connect **directly** to the
`CAN_H` and `CAN_L` nets, alongside the connector pins and the
termination spur.

```
   U30 (TCAN332)                                        CSKB H1
   ┌──────────┐
   │       8 ─┤NC
   │       7 ─┼──────── CAN_H ──────●────────●──────● H1.51 (CAN_H)
   │          │                     │
   │          │              R70 = 60.4 Ω 1% 0402
   │          │                     │
   │          │      MIDPOINT ──●───┤
   │          │                 │   │
   │          │   C71 = 4.7 nF  │   │
   │          │  50V X7R 0402 ──┤ R71 = 60.4 Ω 1% 0402
   │          │                 │   │
   │          │                GND  │
   │          │                     │
   │       6 ─┼──────── CAN_L ──────●────────●──────● H1.52 (CAN_L)
   │       5 ─┤NC
   │       4 ─┤RXD ── CAN_RX (from Sheet 1, SO-DIMM 143)
   │       3 ─┤VCC ── +3V3 (with C70 = 100 nF bypass)
   │       2 ─┤GND ── GND
   │       1 ─┤TXD ── CAN_TX (from Sheet 1, SO-DIMM 145)
   └──────────┘
```

**How it works:**
- **Differential impedance** = R70 + R71 = **120.8 Ω** across the
  pair. Matches the CAN bus 120 Ω characteristic impedance, well
  within ISO 11898-2's 100–130 Ω tolerance window. C71 doesn't
  affect the differential signal — its midpoint is a virtual
  ground for diff signals (equal/opposite voltage swings cancel).
- **Common-mode impedance** = ~30 Ω (R70 ∥ R71) in series with
  C71's AC impedance to GND. Common-mode noise on the bus gets
  shunted to GND through C71. Single-resistor (120 Ω) termination
  doesn't give you this filter — that's why "split" is preferred
  for any board with EMI sensitivity nearby (e.g., our 70cm
  comms board peer).
- **Layout:** when populated, place the R70 / C71 / R71 group
  **close to the CSKB connector**, NOT close to U30. The
  termination's job is to match impedance at the **end** of the
  transmission line; placing it near U30 leaves an unterminated
  stub from the resistors to the bus.

#### Note (Place > Note, next to U30):

> CAN transceiver provisioned but DNP for v0.1 (iter 1 doesn't need
> CAN — IHU↔payload uses I²C exclusively). Populate U30 + companions in
> v0.2 if CAN traffic is needed. Split termination (R70 + R71 + C71)
> is standard CAN-FD best practice — populate together with U30.

#### Note (Place > Note, next to R70/R71/C71):

> Split termination across the differential pair, NOT in series with
> the bus. See "Topology — split termination network" diagram above.
> When populated, layout this group close to H1.51/H1.52 (bus end),
> not close to U30. **DNP if the board sits in the middle of the
> stack** — CAN buses are terminated only at the two end nodes.

### Section C: Stack Power Routing

| Source | Destination | Notes |
|---|---|---|
| H2.45/H2.46 (`VBAT`) | `VBAT` → Sheet 1 buck VIN | Source of all carrier 5V power |
| H2.27/H2.28 (`+3V3`) | `+3V3` (global) | Feeds cameras, mux, M.2 |
| H2.29–32 (`GND`) | `GND` (global) | Multiple pins, tie all |
| H2.25/H2.26 (`+5V`) | NC | Carrier does NOT pull from stack +5V |

Place a **bulk decoupling cap** (10 µF X7R 1206) at each of VBAT and
+3V3 entry points, and a **100 nF** HF bypass on +3V3.

| Ref | Value | Package | Connection |
|---|---|---|---|
| C80 | 22 µF, 25 V, X7R | 1210 | `VBAT` → `GND` (at H2.45/46 entry) |
| C81 | 10 µF, 10 V, X7R | 1210 | `+3V3` → `GND` (at H2.27/28 entry) |
| C82 | 100 nF, 16 V, X7R | 0402 | `+3V3` → `GND` (HF, near entry) |

### Section D: Status LEDs

Place 3 status LEDs at the board edge for bring-up visibility:

| Ref | Color | Driver | Net | Function |
|---|---|---|---|---|
| LED1 | Green | R80 (1 kΩ) + LED to GND | `+5V_ORIN` | Buck output present |
| LED2 | Green | R81 (1 kΩ) + LED to GND | `+3V3` | Stack +3V3 present |
| LED3 | Yellow | R82 (1 kΩ) + LED to `+3V3` | `PAYLOAD_FAULT_N` | Lit when fault asserted (LOW) |

Silkscreen labels next to each: "BUCK OK", "3V3 OK", "FAULT".

### Sheet 3 Off-Sheet Ports

| Port | Direction | Goes to |
|---|---|---|
| `VBAT` | Output | Sheet 1 |
| `PAYLOAD_EN` | Output | Sheet 1 |
| `PAYLOAD_FAULT_N` | Input | Sheet 1 |
| `SLP_WAKE_N` | Output | Sheet 1 |
| `I2C0_SCL`, `I2C0_SDA` | Bidir | Sheet 1 |
| `CAN_TX`, `CAN_RX` | Bidir | Sheet 1 |
| `+3V3`, `GND` | — | Global power ports |

---

## Sheet 4: M.2 Key-E + USB Recovery + Debug UART

This sheet contains the bench-only support hardware: M.2 WiFi/BT
socket, USB-2 recovery test header, and the Linux console UART
level shifter.

### Text Frame (top of sheet):

> BENCH-ONLY SUPPORT — M.2 2230 Key-E WiFi/BT socket for ground SSH,
> 5-pin USB-2 recovery test header for bootloader fallback, and
> 1.8V↔3.3V level shifter for the Linux console UART. The M.2 socket
> is DNP-populated only for the flight build (empty socket, no card).
> The USB header and UART shifter remain populated for ground
> diagnostics post-integration. See pinmap §9 (M.2), §4 (USB recovery),
> §5 (debug UART).

### Section A: M.2 Key-E Socket (Top Half of Sheet)

#### J40 — M.2 2230 Key-E (75-pin)

**Part: Amphenol `MDT420E01001`** — Key-E, 30 μin gold, **4.20 mm
stack height**. (The TE `2199125-4` we originally targeted was out
of stock on JLCPCB at order time; the Amphenol MDT420 series was
both well-stocked, cheaper, and has the better plating.)

**Why 4.20 mm stack and not the ideal 2.75 mm?** Pure sourcing
decision. The 2.75 mm Amphenol variant (MDT275-series) had only
3–20 in stock across plating options; the 4.20 mm variant had 918+
across the same. Functionally a single-sided card like the RTL8822CE
works identically in a double-sided 4.20 mm socket — just more empty
air below the card. Contact engagement is the same.

**Vertical budget check:** 4.20 mm stack + 0.8 mm card PCB + ~1.5 mm
card components = ~6.5 mm above carrier PCB top. CSKB inter-board
pitch is ~15.24 mm → ~8.7 mm clearance to the next board.
Comfortable.

**Mounting hardware** (not on the carrier PCB BOM — order
separately from Digi-Key/Mouser):
- M2.5 threaded standoff, **4.20 mm tall** — must match the
  connector stack height
- M2.5 × 3 mm screw to retain the card
- Sourcing: standard "M.2 NGFF" hardware kits target 4.20 mm
  (Würth, Bivar, Keystone, etc.)

If the standoff is too short the card flexes; too tall and the
card-edge contacts don't fully seat in the connector.

**Pin assignments per `payload_carrier_pinmap.md` §9.3–§9.7.** That
document is the authority — copy from it. Highlights:

| M.2 pin | Signal | Carrier net | Notes |
|---|---|---|---|
| 2, 4, 72, 74 | +3.3V | `+3V3_M2` | Downstream of FB_M2 ferrite |
| 35, 37 | PETp0/n0 | `M2_PETP0/N0` | After AC caps C90/C91 |
| 41, 43 | PERp0/n0 | `M2_PERP0/N0` | DC-coupled — no caps on this side |
| 47, 49 | REFCLKp0/n0 | `M2_REFCLKP/N` | DC-coupled |
| 52 | PERST# | `M2_PERST_N` | Direct from SO-DIMM 183 |
| 53 | CLKREQ# | `M2_CLKREQ_N` | Direct from SO-DIMM 182 |
| 55 | PEWAKE# | `M2_PEWAKE_N` | Direct from SO-DIMM 179 |
| 3, 5 | USB_D+/D− | `M2_USB_DP/DN` | From SO-DIMM 117/115 |
| 54, 56 | W_DISABLE2/1# | (via R85/R86 to `+3V3_M2`) | Always enabled |
| 50 | SUSCLK | NC | RTL8822CE doesn't need it |
| (all other) | various | NC | See pinmap §9.7 |

#### M.2 Power Section

| Ref | Value | Package | Connection |
|---|---|---|---|
| FB_M2 | 60 Ω @ 100 MHz, ≥ 2 A | 0805 ferrite bead (Murata BLM21PG600SN1) | `+3V3` → `+3V3_M2` |
| C92 | 22 µF, 10 V, X7R | 1210 | `+3V3_M2` → `GND`, at socket |
| C93–C96 | 100 nF, 16 V, X7R | 0402 | `+3V3_M2` → `GND`, one per VCC pin (2/4/72/74) |
| R85 | 10 kΩ, 1% | 0402 | `+3V3_M2` → M.2 pin 54 (W_DISABLE2#) |
| R86 | 10 kΩ, 1% | 0402 | `+3V3_M2` → M.2 pin 56 (W_DISABLE1#) |

#### M.2 PCIe AC Caps

Per the open item resolution in pinmap §10.9: AC caps on **host TX
only**, near the SO-DIMM end (NOT near the M.2 socket).

| Ref | Value | Package | Connection |
|---|---|---|---|
| C90 | 0.22 µF, 16 V, X7R | 0402 | SO-DIMM PCIE1_TX0_P → `M2_PETP0` |
| C91 | 0.22 µF, 16 V, X7R | 0402 | SO-DIMM PCIE1_TX0_N → `M2_PETN0` |

C90/C91 should be **placed on the Sheet 1 side** of the schematic
(adjacent to the SO-DIMM pins 174/172) so the layout intent matches.
Add a note pointing to Sheet 4 for the M.2-side wiring.

#### Note (Place > Note, next to J40):

> M.2 2230 Key-E WiFi/BT socket. Validated against Realtek RTL8822CE
> shipped on the Orin Nano devkit (lspci 0001:01:00.0). Bench-only —
> flight build leaves socket empty. All control signals are 3.3 V on
> the Orin side, direct connect, no level translators needed.
> AC coupling caps on PCIE1_TX are on Sheet 1 near the SO-DIMM (not
> here) per PCIe CEM convention — see pinmap §10.9.

#### Antenna Bulkhead

Add two SMA-edge or MMCX bulkhead footprints near the M.2 socket for
the RTL8822CE's two u.FL pigtails:

| Ref | Type | Connection |
|---|---|---|
| J41 | MMCX bulkhead (or SMA edge) | "ANT1" (silkscreen) — DNP for flight |
| J42 | MMCX bulkhead (or SMA edge) | "ANT2" (silkscreen) — DNP for flight |

Pigtails are field-installed; the carrier just hosts the bulkhead
footprints. Mechanical placement coordinates with the structure team
(see pinmap §10.11).

### Section B: USB-2 Recovery Test Header (Center-Right)

#### J50 — USB Recovery Header (5-pin 1.27 mm, internal)

This is NOT a USB-A or USB-C connector — it's a 5-pin internal pin
header that mates with a USB recovery breakout cable.

| Pin | Signal | Carrier net | Notes |
|---|---|---|---|
| 1 | +5V (from host) | `+5V_TEST` | Not used by module — see ERC note below |
| 2 | USB D− | `USB0_D_N` (from SO-DIMM 109) | 90 Ω diff, AC-coupled internally |
| 3 | USB D+ | `USB0_D_P` (from SO-DIMM 111) | |
| 4 | NC | NC | (VBUS_DET optional, not used v0.1) |
| 5 | GND | `GND` | |

Silkscreen: "BOOTLOADER ONLY — DO NOT POWER FROM HERE".

| Ref | Value | Package | Connection |
|---|---|---|---|
| J50 | 5-pin 1.27 mm header (Würth 614005113301) | THT | per pinout |

**ERC note for `+5V_TEST`:** Altium will warn that `+5V_TEST` is a
single-pin net (only touches J50 pin 1). **This is intentional.** The
pin exists for mechanical cable compatibility — standard USB
breakout cables wire all five conductors and the VBUS wire has to
land somewhere — but the Orin's recovery mode needs only D+/D-, and
we explicitly don't want the bench host back-powering any carrier
rail. To suppress the warning, drop a **Generic No-ERC marker** on
J50 pin 1: `Place → Directives → Generic No ERC` (shortcut `P, X`).
Do **NOT** "fix" the warning by tying `+5V_TEST` to `+5V_ORIN` or any
other rail — that defeats the isolation the silkscreen warning
exists to protect. Alternative: add a test point `TP7` on
`+5V_TEST` (gives the net a second pin AND lets you probe the
bench host's VBUS during recovery debug — slightly useful but
optional). **TP refdes per `payload_carrier_pinmap.md` §2.1
canonical TP allocation table.**

### Section C: Debug UART Level Shifter (Bottom-Right)

#### U60 — TXB0104QPWRQ1 (1.8V ↔ 3.3V bidirectional, TSSOP-14)

UART1 from the Orin is 1.8 V CMOS; a standard FT232/CP2102 USB-UART
adapter expects 3.3 V. Use a TXB0104 bidirectional level shifter
(4 channels — only 2 used) to expose TX/RX at 3.3 V on the debug
header.

Pinout per TI `TXB0104` datasheet (SCES643, TSSOP-14 = "PW" /
"QPWRQ1" package). **Verify against your Altium symbol library
before placing — this table was corrected 2026-05-24 from an
earlier scrambled version.** Structural pattern: A-side power
and A-channels on the left (pins 1–7), B-side power and
B-channels on the right (pins 8–14), with B-channels numbered
in reverse so A1↔B1, A2↔B2 etc. line up physically across the IC.

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | VCCA | `+1V8_MOD` | A-side (low) supply, 1.8 V |
| 2 | A1 | `DBG_UART_TX_1V8` (from SO-DIMM 203) | Ch.1 low side — Orin TX (1.8 V) → translates to B1 (3.3 V) |
| 3 | A2 | `DBG_UART_RX_1V8` (to SO-DIMM 205) | Ch.2 low side — adapter TX (3.3 V on B2) → translates to A2 (1.8 V) → Orin RX |
| 4 | A3 | NC | Channel 3 unused |
| 5 | A4 | NC | Channel 4 unused |
| 6 | NC | NC | (per datasheet — no internal connection) |
| 7 | GND | `GND` | Ground |
| 8 | OE | `+1V8_MOD` (always enabled) | Output enable, referenced to VCCA. Tied HIGH = translation active. Tie directly to VCCA for "always on" behaviour. |
| 9 | NC | NC | (per datasheet — no internal connection) |
| 10 | B4 | NC | Channel 4 unused |
| 11 | B3 | NC | Channel 3 unused |
| 12 | B2 | `DBG_UART_RX_3V3` → J60 pin 3 | Ch.2 high side — adapter TX (3.3 V) |
| 13 | B1 | `DBG_UART_TX_3V3` → J60 pin 2 | Ch.1 high side — adapter RX (3.3 V) |
| 14 | VCCB | `+3V3` | B-side (high) supply, 3.3 V |

| Ref | Value | Package | Connection |
|---|---|---|---|
| U60 | TXB0104 (TI `TXB0104QPWRQ1` preferred — TSSOP-14, AEC-Q100 auto-grade) | TSSOP-14 | per pinout |
| C100 | 100 nF, 16 V, X7R | 0402 | VCCA → GND |
| C101 | 100 nF, 16 V, X7R | 0402 | VCCB → GND |

**JLCPCB BOM hint:** original spec was `TXB0104PWR` (standard TSSOP-14
commercial grade) but that variant was out of stock at order time.
**`TXB0104QPWRQ1`** is the same TSSOP-14 part, automotive-grade
(AEC-Q100), ~$0.89 — a bit pricier than the QFN/BGA alternatives
but worth the premium because:
- **Same TSSOP-14 footprint** as the original — no Altium symbol /
  footprint change needed (avoids re-deriving the pinout and risking
  transcription errors)
- **Hand-rework friendly** (leaded TSSOP), unlike the QFN/BGA alts
  which need a hot-air station or reflow
- Q1 auto-qualification is a bonus for thermal range, not required

Avoid the cheaper QFN (`TXB0104RUTR` X2QFN-14, `TXB0104RGYR` VQFN-14)
and BGA (`TXB0104YZTR` DSBGA) variants — they'd save ~$0.50 per IC
but force an Altium footprint rebuild and make rework hard.

#### J60 — Debug UART Header (3-pin 1.27 mm or 2.54 mm)

| Pin | Signal | Notes |
|---|---|---|
| 1 | `GND` | Adapter ground reference |
| 2 | `DBG_UART_TX_3V3` | From Orin, to adapter's RX |
| 3 | `DBG_UART_RX_3V3` | From adapter's TX, to Orin |

Silkscreen: "UART: GND - TX - RX". Match the Adafruit/SparkFun pinout
convention so users plug straight in.

#### Note (Place > Note, next to U60):

> Debug UART level shifter. TXB0104 auto-direction-senses on each
> channel — no DIR pin needed. VCCA = 1.8 V (from Orin module),
> VCCB = 3.3 V (carrier rail). OE tied to VCCA so the shifter wakes
> up with the module. Header J60 matches the standard
> FT232/CP2102 GND-TX-RX pinout: a USB-UART adapter plugs straight in.
> Linux serial console comes up at **115200 8N1** on UART1 per
> JetPack defaults.

### Sheet 4 Off-Sheet Ports

| Port | Direction | Goes to |
|---|---|---|
| `+3V3`, `+1V8_MOD`, `GND` | — | Global power ports |
| 8× PCIE1 pairs + control (PERST_N, CLKREQ_N, PEWAKE_N) | Bidir | Sheet 1 |
| `USB0_D_P/N`, `USB1_D_P/N` | Bidir | Sheet 1 |
| `DBG_UART_TX_1V8`, `DBG_UART_RX_1V8` | Bidir | Sheet 1 |

---

## Final Checklist Before First-Order Review

- [ ] **All IC pinout tables in this doc verified against the actual datasheet.** (Two pinout-transcription errors have been caught and fixed historically — PCA9546A in rev 0.4, TXB0104 in rev 0.5. Before placing any IC symbol, cross-check pin numbers in this guide against the manufacturer's datasheet for the exact JLCPCB part you're ordering — don't trust the table blindly.)
- [ ] All four sheets present with the names specified in §"Altium Project Setup"
- [ ] SO-DIMM pinout matches `payload_carrier_pinmap.md` exactly (spot-check 10 random pins)
- [ ] MODULE_ID (pin 217) hardwired to GND
- [ ] All VDD_IN pins (251–260) tied together with adequate decoupling per DG-10931 §6
- [ ] TPS62933F EN tied to `PAYLOAD_EN` (not always-on)
- [ ] U4 = single 74LVC2G07 with **VCC tied to `+1V8_MOD`** (NOT `+3V3`) — see §1.D analysis. C45 (100 nF) at VCC pin.
- [ ] R34 (10 kΩ PU on `MUX_RST_N_3V3` → `+3V3`) is present on Sheet 1 (no PU on the payload side of `PAYLOAD_FAULT_N` — IHU provides that per cskb_pinmap Rule 3)
- [ ] No carrier-side pull-ups on `CAM_I2C` master bus (Orin has on-module 2.2 kΩ)
- [ ] 4.7 kΩ pull-ups on each downstream PCA9546A channel (cameras don't include them)
- [ ] CSI0 D1 and CSI1 D0 P/N polarities swapped at the FFC end (DG-10931 §10)
- [ ] CAN transceiver (U30, R70, R71, C70, C71) marked **DNP**
- [ ] M.2 socket marked **DNP for flight variant**
- [ ] M.2 PCIe TX AC caps (C90/C91) placed on Sheet 1 near SO-DIMM, NOT near M.2 socket
- [ ] M.2 RX side has NO AC caps on the carrier
- [ ] FORCE_RECOVERY* default = HIGH (jumper open) via R33 (10 kΩ to +1V8_MOD)
- [ ] Status LEDs LED1/LED2/LED3 placed at board edge with current-limiting resistors
- [ ] Test points per `payload_carrier_pinmap.md` §2.1 canonical allocation: TP1 (SYS_RESET_N), TP2 (MOD_SLEEP_N), TP3 (CLK_32K_OUT), TP4 (PAYLOAD_FAULT_N), TP5 (DBG_UART_TX_1V8 pre-shifter), TP6 (DBG_UART_RX_1V8 pre-shifter), and **optional** TP7 (+5V_TEST diagnostic)
- [ ] Antenna footprints J41/J42 placed for u.FL pigtails (DNP for flight)
- [ ] Silkscreen labels on all bench-only headers ("BOOTLOADER ONLY", "RECOVERY", "UART: GND-TX-RX")
- [ ] ERC clean (open inputs flagged, no floating nets except documented NC)
- [ ] Cross-reference back to `payload_carrier_pinmap.md` open items §10 to confirm all are either resolved or known

## Open Items to Flag During Schematic Capture

These come straight from `payload_carrier_pinmap.md` §10 — track them
on the schematic as TODO callouts so reviewers see them:

1. **Verify Pi GS Camera FFC pin 11 (PWDN) voltage** — 3.3 V or 1.8 V?
   If 3.3 V, the Orin 1.8 V GPIO needs a third 1.8 V → 3.3 V buffer.
2. **Verify Pi GS Camera schematic CSI ribbon pinout** matches the
   pinmap §3.2 table.
3. **CSKB +3V3 peak headroom** with M.2 + 3 cameras (~1.6 A peak).
4. **Camera-3 PWDN GPIO crosses Orin VDD_IO domain** — confirm via DA-11434.
5. **PAYLOAD_SLEEP_REQ_N** 3.3 V CMOS into Orin 5 V CMOS input — direct connect.
6. ~~**74LVC1G07 split-package decision**~~ **Resolved 2026-05-24.**
   Reverted to a single 74LVC2G07 (was: two single-channel 74LVC1G07).
   Trick is running U4 at VCC = `+1V8_MOD` instead of `+3V3`, which
   shifts V_IH(min) from 2.0 V (TTL spec @ VCC ≥ 2.7 V) to 0.65 × VCC
   = 1.17 V — accepting the 1.8 V Orin GPIO cleanly. Both open-drain
   outputs are rail-agnostic and continue to pull up to 3.3 V through
   their external PUs. See §1.D for the full analysis.

## Revision History

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-18 | NG / CC | Initial draft, 4-sheet structure: SO-DIMM+Power+Seq, Cameras, CSKB Stack, M.2+USB+UART. Components selected for parts commonality with EPS (TPS62933F buck). Flagged 74LVC2G07 V_IH issue and recommended split to two 74LVC1G07. Aligned with payload_carrier_pinmap.md rev 0.3 (M.2 Key-E added). |
| 0.2 | 2026-05-24 | NG / CC | Net-naming conformance pass against `hardware/conventions/net_naming.md`. Renamed `+3V3_PAYLOAD` → `+3V3` (stack rail uses canonical power port). Renamed `+5V_PAYLOAD` → `+5V_ORIN` (board-local rail; suffix now describes the load — Orin module VDD_IN). Renamed `I2C_FC_SCL`/`I2C_FC_SDA` → `SCL_SYS`/`SDA_SYS` (kills stale "FC" prefix; matches cskb_pinmap canonical). Fixed wrong cross-reference in net table where `CAM_I2C_*` was incorrectly described as "Orin `I2C0_*`" — those are two different I²C buses on the Orin. Updated Net Name Convention prose to reference net_naming.md. No electrical / sheet-structure changes. |
| 0.3 | 2026-05-24 | NG / CC | **U4 reverted to single 74LVC2G07 (was: two 74LVC1G07).** Realized during BOM selection that running the dual-channel 2G07 at **VCC = `+1V8_MOD`** (not `+3V3`) resolves the V_IH violation that originally drove the split — at VCC < 2.7 V the LVC family V_IH(min) is 0.65 × VCC = 1.17 V, comfortably below the Orin 1.8 V CMOS HIGH. Both OD outputs continue to pull up to 3.3 V through external PUs (IHU-side for `PAYLOAD_FAULT_N`, R34 on carrier for `MUX_RST_N_3V3`). Saves one IC. Rewrote §1.D with the new analysis. JLCPCB part: prefer Nexperia **74LVC2G07GW** (TSSOP-6, rework-friendly) or Diodes **74LVC2G07W6-7** (SOT-26). Resolved open item §6. |
| 0.4 | 2026-05-24 | NG / CC | **Errata: §2.A PCA9546A pinout table was wrong** — pin numbers in the original (rev 0.1) table did not match the actual NXP `PCA9546APW,118` datasheet. Corrected pinout: pin 1 = A0, pin 2 = A1, pin 3 = RESET\*, pins 4–7 = SD0/SC0/SD1/SC1, pin 8 = VSS, pins 9–12 = SD2/SC2/SD3/SC3, pin 13 = A2, pin 14 = SCL, pin 15 = SDA, pin 16 = VDD. Net connections unchanged (channel-to-camera mapping, address straps to GND, R34 PU on RESET\* → 3.3 V) — only the pin numbers shifted. **Anyone who built the Altium symbol from the original table needs to verify and rebuild.** Also folded in two earlier doc-clarity fixes (§1.C VDD_IN-vs-+5V_ORIN clarification, §2.A PCA9546A JLCPCB BOM hint) that landed on main as `d5ecc64` without a rev bump. |
| 0.5 | 2026-05-24 | NG / CC | **Errata: §4.C U60 TXB0104 pinout table was wrong.** Same class of error as the PCA9546A in rev 0.4 — pin numbers in the original (rev 0.1) table did not match the TI TXB0104 datasheet (SCES643). Corrected pinout: pin 1 = VCCA, pin 2 = A1, pin 3 = A2, pin 4 = A3, pin 5 = A4, pin 6 = NC, pin 7 = GND, pin 8 = OE, pin 9 = NC, pin 10 = B4, pin 11 = B3, pin 12 = B2, pin 13 = B1, pin 14 = VCCB. Net connections unchanged (Orin TX on A1↔B1, Orin RX on A2↔B2, OE tied to VCCA, channels 3/4 NC) — only pin numbers shifted. **Anyone who built the Altium symbol from the original table needs to verify and rebuild.** Added a "verify all IC pinout tables against datasheet" item at the top of the Final Checklist so the next pinout transcription error gets caught at review time, not mid-bring-up. |
| 0.6 | 2026-05-24 | NG / CC | **Test point allocation rationalized — refdes fix.** Internal TP4 collision: Final Checklist had TP4 = PAYLOAD_FAULT_N while §4.B optional alternative also called its +5V_TEST test point TP4. Renumbered §4.B optional to **TP7** to match the canonical TP table that now lives in `payload_carrier_pinmap.md` §2.1 (TP1–TP7 assignments + status). Updated Final Checklist to reference §2.1 directly with the full list (TP1 SYS_RESET_N, TP2 MOD_SLEEP_N, TP3 CLK_32K_OUT, TP4 PAYLOAD_FAULT_N, TP5 DBG_UART_TX_1V8 pre-shifter, TP6 DBG_UART_RX_1V8 pre-shifter, optional TP7 +5V_TEST). No electrical changes. Companion change in pinmap rev 0.6. |
