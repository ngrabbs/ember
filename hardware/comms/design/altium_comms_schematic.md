# Altium Schematic Instructions — Comms Board

## Design Summary

This board implements the CubeSat's full RF communications system on a
single PCB: a 437 MHz BPSK downlink transmitter (70cm) and a 145.9 MHz
AFSK uplink receiver (2m), with an RP2040 (Pico module) as the digital
controller.

```
CSKB Stack Connectors (from EPS, H1 signals + H2 power)
     │
     ├── +3V3 ──→ Si5351A, 74LVC1G86, MCP6022, RP2040
     ├── +5V  ──→ PSA4-5043+ LNA, ADL5602 MMIC
     ├── GND
     ├── I2C_SCL/SDA ──→ Internal Housekeeping Unit bus
     └── VBAT (unused on comms, monitor only)

Si5351A (3-output clock gen, I2C controlled by RP2040)
     ├── CLK0 (145.67 MHz) → XOR BPSK Mod → Tripler → BPF → ADL5602 MMIC → Output BPF → TX SMA
     ├── CLK1 (145.9 MHz)  → LO LPF → ADE-1+ Mixer LO input
     └── CLK2 (spare)

                 Antenna → RX SMA → 2m BPF → PSA4 LNA → ADE-1+ Mixer → Sallen-Key LPF → MCP6022 Gain → Pico ADC
```

Key design decisions:
1. **Power comes from the EPS via the CSKB stack connectors** — no on-board
   voltage regulators. +3V3 and +5V are generated on the EPS board and
   distributed through the stack connector.
2. **XOR BPSK modulation at 145.67 MHz** (before the tripler), not at
   437 MHz. The 74LVC1G86 has massive timing margin at 146 MHz but fails
   at 437 MHz. BPSK phase states are preserved through odd-order
   frequency multiplication (3 × 180° = 540° ≡ 180°).
3. **Frequency tripler** (class-C biased transistor) converts 145.67 MHz
   to 437 MHz. BFR92A (ft=5 GHz, SOT-23) for flight; 2N3904 for
   breadboard validation.
4. **Separate TX and RX SMA connectors** (no diplexer for prototype).
5. **Raspberry Pi Pico module** for prototype — bare RP2040 deferred to v2.

---

## Altium Project Setup

1. Create a new PCB project: `Comms_Board.PrjPcb`
2. Add seven schematic sheets (flat design):
   - `Overview.SchDoc` — title sheet, block diagram, design notes (non-electrical)
   - `Clock_Gen.SchDoc` — Si5351A and I2C interface
   - `TX_Chain.SchDoc` — XOR modulator, tripler, BPF, MMIC
   - `RX_Chain.SchDoc` — PSA4-5043+ LNA, ADE-1+ passive mixer, LO LPF, IF termination, Sallen-Key LPF, MCP6022 gain stage
   - `Digital_Control.SchDoc` — RP2040 (Pico module), USB, GPIOs
   - `Power.SchDoc` — power distribution, bypass, and protection
   - `Connectors.SchDoc` — CSKB H1 + H2 stack connectors, SMA connectors, test headers
3. Each sheet uses A3 landscape format
4. Set the project's designator scope to "Flat" so R1, C1, etc. are unique
   across all sheets

### Flat Design — How Inter-Sheet Connections Work

This project uses a **flat** (non-hierarchical) design, same as the EPS
board. There is no top-level sheet with sheet symbols. Instead, nets
connect between sheets using **net labels** and **power ports**:

- **Power ports** (`+3V3`, `+5V`, `GND`, `VBAT`) are global automatically —
  place the same power port symbol on any sheet and they connect.
- **Signal net labels** (`I2C_SDA`, `CLK0_OUT`, `BPSK_DATA`, etc.) are also
  global in a flat project — place the same net label on two different sheets
  and Altium connects them automatically.
- **No ports or sheet entries needed** — those are only for hierarchical designs.
  In a flat design, just use net labels with matching names across sheets.

This is simpler to set up and matches the EPS board's structure.

### Net Name Convention

Use these global net names consistently across all sheets. Use **power port
symbols** (not net labels) for supply rails so they are global automatically.

| Net Name | Type | Description |
|---|---|---|
| `+3V3` | Power port | 3.3V regulated rail (from EPS via bus) |
| `+5V` | Power port | 5.0V regulated rail (from EPS via bus) |
| `GND` | Power port | Ground (global) |
| `VBAT` | Power port | Unregulated battery bus from EPS (monitor only) |
| `I2C_SDA` | Net label | I2C data — Si5351A and internal housekeeping unit bus |
| `I2C_SCL` | Net label | I2C clock — Si5351A and internal housekeeping unit bus |
| `BPSK_DATA` | Net label | RP2040 GPIO to XOR gate data input |
| `CLK0_OUT` | Net label | Si5351A CLK0 output (145.67 MHz) |
| `CLK1_OUT` | Net label | Si5351A CLK1 output (145.9 MHz LO) |
| `BPSK_145` | Net label | XOR output, BPSK-modulated 145.67 MHz |
| `TRIPLER_OUT` | Net label | Tripler output, unfiltered 437 MHz |
| `TX_437` | Net label | Filtered 437 MHz, post-BPF |
| `TX_OUT` | Net label | MMIC output to TX SMA |
| `RX_IN` | Net label | RX SMA input to 2m BPF |
| `RX_IF` | Net label | ADE-1+ IF output (baseband, post-termination) |
| `RX_FILT` | Net label | Sallen-Key filter output |
| `RX_BASEBAND` | Net label | MCP6022 amplified output to Pico ADC |

#### Note on Power Port Symbols

Altium power port symbols come in several styles (circle, T-bar, arrow, etc.).
The style is **cosmetic only** — the net name on the power port is what
matters electrically. All power ports with the same net name connect globally
regardless of symbol shape. Convention used in this design:
- **T-bar** for supply rails (`+3V3`, `+5V`, `VBAT`)
- **Circle with line** for `GND`
- You can use any style as long as the net name matches exactly

#### Net naming for this board

Project-wide net naming convention is documented in
[`hardware/conventions/net_naming.md`](../../conventions/net_naming.md)
— read that first for the prefix system (`RF_`, `BB_`, `LO_`, etc.),
the Altium application techniques (Net Labels, Net Class directives,
Blankets), and the recovery procedure for inherited designs with
`NetCXX_Y` everywhere.

This subsection lists the **comms-board-specific** application of
that convention — the actual named nets that live inside the comms
schematic.

**TX chain (all `RF_*`):**

```
RF_TX_TRIPLER_OUT       BFR92A collector → pre-MMIC BPF
RF_TX_BPF1_TAP1, _TAP2  inside the pre-MMIC BPF (between cap and L)
RF_TX_MMIC_IN           BPF output → ADL5602 input
RF_TX_MMIC_OUT          ADL5602 output → output BPF
RF_TX_BPF2_TAP1, _TAP2  inside the output BPF
RF_TX_OUT               → TX antenna connector (same as TX_OUT in
                          the interface-net table above)
```

**RX chain (mix of `RF_*`, `LO_*`, `BB_*`):**

```
RF_RX_IN                from RX antenna connector (same as RX_IN above)
RF_RX_BPF_TAP1, _TAP2   inside the 2m BPF
RF_RX_LNA_IN            BPF out → PSA4 input
RF_RX_LNA_OUT           PSA4 output → ADE-1+ RF
RF_RX_MIXER_LO          LO LPF out → ADE-1+ LO
RF_LO_LPF_NODE1, _NODE2 inside the LO LPF

BB_RX_IF                ADE-1+ IF (same as RX_IF above)
BB_RX_FILT              Sallen-Key out (same as RX_FILT above)
BB_RX_BASEBAND          MCP6022 out → ADC (same as RX_BASEBAND above)
```

With this naming applied, the RF net class is populated by a single
wildcard pattern (`RF_*`), the Baseband class by `BB_*`, and the
Width rules scope cleanly to "Net Class = RF" — no manual list
maintenance as nets are added or removed.

For nets you haven't yet renamed (auto-named `NetCXX_Y` from the
initial layout pass), use the Net Class directive approach from the
project-level naming doc — drop a directive or blanket on each RF
chain region in the schematic and the class is populated without
touching the underlying net names.

---
---

## Board Stackup (4-layer, 1.6 mm — JLCPCB JLC04161H-7628)

The comms board is a **4-layer FR4** at **1.6 mm** total thickness,
fabricated to JLCPCB's standard JLC04161H-7628 stackup. This was
changed from the original 2-layer design in Rev 1.0 (see revision
history) because:

- 2-layer routing required snake-y power runs across the board,
  forcing breaks in the ground pour and degrading return-current
  integrity in the RF zones
- A solid ground plane on layer 2 makes 50 Ω microstrip impedance
  predictable and gives every signal trace a clean return path
- TX↔RX isolation (a real concern at 437 MHz with the receiver on the
  same board as the transmitter) is much better with a continuous
  ground plane and via fences than with an interrupted top-side pour
- The original LSM had a 0.32 mm dielectric — this was Altium's
  default placeholder, not a real fab stackup. Reviewer flagged the
  board as "looks thin" because the 3D view was showing a 0.41 mm
  total thickness instead of the actual 1.6 mm the fab would deliver

See [`rf_layout_guidelines.md`](rf_layout_guidelines.md) for the
ground-plane and via-stitching rules this stackup enables.

### Layer Stackup Diagram

```
┌──────────────────────────────────────────────────────────┐
│ Solder mask                  0.0152 mm                   │
│ L1 — Signals (top, RF zone)  0.035 mm (1 oz Cu)         │
├──────────────────────────────────────────────────────────┤  ← Prepreg 7628, 0.21 mm, εr ≈ 4.4
│ L2 — GND plane (solid)       0.0152 mm (½ oz Cu)         │
├──────────────────────────────────────────────────────────┤
│ Core FR4                     1.065 mm  (εr ≈ 4.4)        │
├──────────────────────────────────────────────────────────┤
│ L3 — Power distribution      0.0152 mm (½ oz Cu)         │
├──────────────────────────────────────────────────────────┤  ← Prepreg 7628, 0.21 mm
│ L4 — Signals (bottom)        0.035 mm (1 oz Cu)         │
│ Solder mask                  0.0152 mm                   │
└──────────────────────────────────────────────────────────┘
Total: 1.6 mm ± 10%
```

### Layer Purpose

| Layer | Purpose | Notes |
|---|---|---|
| L1 (top) | RF traces + RF components + top-side digital | All RF on this layer, kept short |
| L2 | **Solid ground plane** | No signal routing. Edge to edge. The reference plane for L1 50 Ω microstrip and a clean return for everything on every layer. |
| L3 | Power distribution | Pour `+3V3` and `+5V` islands here. May also carry low-speed signals if needed, but power first. |
| L4 (bottom) | Digital signals, slow control | SPI, I2C, USB, status LEDs, any signal that doesn't need RF performance. Keep away from RF zones above. |

### Altium Layer Stack Manager — How to Configure

1. **Tools → Layer Stack Manager**
2. Delete the existing 2-layer stack
3. Either:
   - **Recommended:** click "Tools → Presets → JLCPCB → JLC04161H-7628 (1.6 mm)" if your Altium has the preset library installed, OR
   - Build manually: Add Plane (L2 — assign to net `GND`), Add Plane (L3 — leave as Plane, individual nets pour at PCB level), and configure the dielectrics per the diagram above
4. **Materials:** set FR4 with Dk = 4.4 (or 4.3) for both prepreg layers and core
5. **Verify total thickness reads 1.600 mm** in the LSM properties pane
6. Save and re-pour all polygons. The 3D view should now show a realistic-thickness board.

### Impedance and Trace Width

50 Ω microstrip on the top signal layer, referenced to the first
inner layer (GND plane) below, with top prepreg = 0.21 mm and
εr = 4.4.

**Important — Altium vs documentation layer naming:**

Our docs and Altium label the layers differently. Don't let this trip
you up when configuring the impedance profile:

| This doc says... | Altium's UI calls it... |
|---|---|
| L1 (top signal) | **Top Layer** |
| L2 (GND plane) | **Layer 1** (first inner) |
| L3 (power) | **Layer 2** (second inner) |
| L4 (bottom signal) | **Bottom Layer** |

So when Altium's impedance profile says "Bottom ref: Layer 1," that's
referring to our **L2 GND plane** — which is correct for our top-layer
microstrip.

| Trace target | Width | Calculation basis |
|---|---|---|
| 50 Ω microstrip (with solder mask) | **0.358 mm (14 mil)** | h=0.21mm, εr=4.4, t=0.035mm, mask 0.015mm/side |
| 50 Ω microstrip (no mask, ideal) | ~0.38 mm | same, less mask loading |
| 50 Ω microstrip (alt thinner stack) | 0.14 mm (5.5 mil) | only if using JLC04161H-3313 with 0.075 mm top prepreg |

Always trust Altium's impedance calculator over hand calculations or
generic numbers — it uses your actual stackup including solder mask.
The 0.358 mm figure assumes JLC04161H-7628 plus solder mask checked
in the impedance profile. If your stackup differs, the calculated
width differs accordingly.

Every existing RF trace in the design must be re-set to the calculated
width. The procedure below sets up an Altium Design Rule that enforces
this automatically.

#### Step 1 — Create the RF net class

1. **Design → Classes** (opens Object Class Explorer)
2. Left tree → **Net Classes** → right-click → **Add Class**
3. Name it **`RF`**
4. In the right pane, move every RF-carrying net from Non-Members to
   Members using the `>` arrow. Nets to include:
   - `CLK0_OUT` (145.67 MHz, Si5351A → XOR)
   - `CLK1_OUT` (145.9 MHz, Si5351A → LO LPF)
   - Tripler output net (Q1 collector → pre-MMIC BPF)
   - All intermediate nets inside the pre-MMIC and output BPFs
   - MMIC input/output nets (around U2 / ADL5602)
   - Output net to TX SMA (`TX_OUT` or similar)
   - `RX_IN` from RX SMA to 2m BPF
   - LNA input/output nets (around U10 / PSA4-5043+)
   - Mixer RF/LO/IF nets (around U3 / ADE-1+)
   - LO LPF intermediate nets (C57/L13/C58/L14/C59)

   Exclude DC bias lines, baseband signals, and digital nets — they're not RF.

#### Step 2 — Create the Width rule

1. **Design → Rules** (opens PCB Rules and Constraints Editor)
2. Left tree → expand **Routing → Width**
3. Right-click **Width** → **New Rule**
4. Click the new rule and set:
   - **Name:** `RF_Trace_Width`
   - **Where The Object Matches:** change from "All" to **Net Class**,
     then select `RF`
   - **Constraints** (values from Altium impedance calculator, see Step 5):
     - Min Width: **0.34 mm**
     - Preferred Width: **0.358 mm** (or whatever the LSM impedance profile reports)
     - Max Width: **0.40 mm**
5. Apply

#### Step 3 — Set the rule priority

Default Width rule has higher priority than your new one unless you
move it up. Without this step, Altium ignores your RF rule.

1. Bottom of Rules dialog → click **Priorities…**
2. Select `RF_Trace_Width` → click **Increase Priority** until it's #1
3. Default `Width` becomes #2 (fallback for non-RF nets)
4. OK

#### Step 4 — (Recommended) RF clearance rule

Wider clearance between RF traces reduces coupling. Add a clearance
rule scoped to the same RF class:

1. Rules → **Electrical → Clearance** → right-click → New Rule
2. Name: `RF_Clearance`
3. Where: both First Object and Second Object = **Net Class = RF**
4. Min Clearance: **0.30 mm** (vs default 0.15 mm)
5. Priorities → bump above default Clearance rule

#### Step 5 — Verify impedance against your stackup

In Altium Designer 20+, the impedance calculator lives inside the
Layer Stack Manager, not under Tools.

1. **Design → Layer Stack Manager**
2. In the LSM window, find the **Impedance** view in the top toolbar
   (tab or pane button)
3. Click **+** to add a new Impedance Profile:
   - **Name:** `Z50_Microstrip_L1`
   - **Type:** Single Ended
   - **Reference Layer:** in Altium UI this is "Bottom ref" → pick
     `Layer 1` (Altium's first inner layer, = our L2 GND plane)
   - **Trace Layer:** Top Layer
   - **Target Impedance:** 50 Ω
   - **Tolerance:** ±10%
   - **Use solder mask:** ✓ checked (more accurate — mask loading
     pulls the required width down by ~0.02 mm)
4. Altium reports the required width — should be ~**0.358 mm** with
   solder mask checked, or ~0.38 mm without. The mask-checked value
   is what you should use because that's what your fabricated board
   will actually look like.
5. The "Top ref" field stays empty — there's no plane above a
   top-layer microstrip trace, only the reference plane below.

If your Altium version doesn't have the Impedance view in LSM, use
**Saturn PCB Toolkit** (free, https://saturnpcb.com/saturn-pcb-toolkit/),
"Conductor Impedance" → "Microstrip":
- Trace thickness: 0.035 mm (1 oz)
- Substrate height: 0.21 mm
- Dielectric constant: 4.4
- Target Z: 50 Ω
- Solve for width → ~0.38 mm

#### Step 6 — Re-route or re-set existing RF traces

After the rule is in place, existing RF traces don't automatically
update to the new width. For each one:
- Option A: select the trace → Properties panel → set Width to 0.38 mm
- Option B: select trace → right-click → **Routing → Retrace Selected**
  → Altium re-runs the trace with current rules applied (preferred,
  also re-applies clearance)
- Option C: delete and re-route — only do this if the trace is so old
  it doesn't follow current pad/component positions anyway

Run **DRC (Tools → Design Rule Check)** after the changes to confirm
no violations.

### Component / Mass Impact

- Extra copper: ~10 g per board for the two inner layers (negligible
  for a 1 U mass budget)
- Cost increase at JLCPCB: roughly $10–20 on a 5-board prototype run
  (2-layer ~$10, 4-layer ~$25)
- CSKB stack mechanics: unchanged (still 1.6 mm board, same H1/H2
  connector engagement)
- Mechanical drill / mounting: unchanged

---
---

## Sheet 1: Overview

This is a non-electrical title/overview sheet. No components or nets are
placed here — it serves as the front page of the schematic package and
provides context for anyone reviewing or building the design.

### Text Frame 1: Project Identification (Top of Sheet)

Place a large text frame across the top of the sheet:

> **CubeSat Communications Board — 70cm BPSK TX / 2m AFSK RX**
>
> Project: EMBER — Senior Capstone Design
> Board: Communications Subsystem, Single PCB
> Designer: Nick Grabbs / K15Y NG
> Revision: 0.2
> Date: (today)
> Repository: ember/hardware/comms

### Text Frame 2: System Block Diagram (Center of Sheet)

Place a text frame with the system architecture. In Altium, you can also
paste a graphic (Place > Drawing Tools > Graphic or import a bitmap/SVG).

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  CSKB Bus (H1 + H2, from EPS)                                          │
│  ┌─────────────────┐                                                     │
│  │ +3V3  +5V  GND  │                                                     │
│  │ I2C_SCL/SDA     │                                                     │
│  │ VBAT (monitor)  │                                                     │
│  └────────┬────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  ┌─── Power Distribution ───┐                                           │
│  │ Input protection, bulk   │                                           │
│  │ bypass, Pico VSYS feed   │                                           │
│  └──────────┬───────────────┘                                           │
│             │                                                            │
│     ┌───────┼────────────────────────────────────┐                       │
│     │       │                                    │                       │
│     ▼       ▼                                    ▼                       │
│  ┌────────────────┐  ┌─────────────────────────────────────────────┐     │
│  │ RP2040 (Pico)  │  │              Si5351A Clock Gen              │     │
│  │                │  │  25 MHz XTAL → PLL → CLK0 (145.67 MHz)     │     │
│  │ I2C master ────┼──│                      CLK1 (145.90 MHz)     │     │
│  │ BPSK data  ────┼──│──┐                   CLK2 (spare)          │     │
│  │ ADC input  ←───┼──│──│───────────────────────────────────┐      │     │
│  └────────────────┘  └──│───────────┬───────────────────────│──────┘     │
│                         │           │                       │            │
│                         ▼           ▼                       │            │
│  ┌─ TX Chain ──────────────────┐  ┌─ RX Chain ─────────────│──────┐     │
│  │                             │  │                         │      │     │
│  │ 74LVC1G86 XOR Modulator     │  │ 2m BPF (input filter)          │     │
│  │ (BPSK @ 145.67 MHz)        │  │      │                        │     │
│  │      │                      │  │ PSA4-5043+ LNA (+21 dB)       │     │
│  │ BFR92A Freq Tripler         │  │      │                        │     │
│  │ (145.67 → 437 MHz)         │  │ ADE-1+ Mixer ←─ LO LPF ← CLK1│     │
│  │      │                      │  │      │ (+ 51Ω IF term)       │     │
│  │ 437 MHz BPF (pre-MMIC)      │  │ Sallen-Key LPF (fc=3.3kHz)   │     │
│  │      │                      │  │      │                        │     │
│  │ ADL5602 MMIC (+20 dB)      │  │ MCP6022 Gain Stage (×11)      │     │
│  │      │                      │  │      └── → Pico ADC          │     │
│  │ 437 MHz BPF (output)       │  │  RX SMA ← 145.9 MHz antenna  │     │
│  │      │                      │  └───────────────────────────────┘     │
│  │ TX SMA → 437 MHz antenna   │                                        │
│  └─────────────────────────────┘                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Text Frame 3: Power Rail Summary (Bottom-Left)

> **Power Rails**
>
> | Rail | Source | Voltage | Consumers |
> |------|--------|---------|-----------|
> | +3V3 | EPS via CSKB (H2.27/28) | 3.3V ±2% | RP2040, Si5351A, 74LVC1G86, MCP6022 |
> | +5V | EPS via CSKB (H2.25/26) | 5.0V ±2% | PSA4-5043+ LNA, ADL5602 MMIC, tripler bias, Pico VSYS |
> | GND | EPS via CSKB (H2.29/30/32, H2.31 AGND) | 0V | All |
> | VBAT | EPS via CSKB (H2.45/46) | 6.0–8.4V | Monitor only (not used for power) |
>
> **Estimated current budget:**
> +3V3: ~150 mA (RP2040 ~50mA, Si5351A ~30mA, logic ~10mA, op-amp ~10mA)
> +5V: ~140 mA (PSA4 LNA ~60mA, ADL5602 ~60mA, tripler ~5mA, Pico VSYS ~10mA, margin ~5mA)
> Total: <300 mA — well within EPS TPS62933F capacity (3A per rail). Note: PSA4 LNA bias can be GPIO-gated for RX duty-cycling.

### Text Frame 4: Net Name Convention (Bottom-Center)

> **Net Name Convention**
>
> Power rails use **power port symbols** (global across all sheets).
> Signal nets use **net labels** (also global in flat design).
>
> | Net | Type | Description |
> |-----|------|-------------|
> | +3V3, +5V, GND, VBAT | Power port | Supply rails (global) |
> | I2C_SDA, I2C_SCL | Net label | I2C bus (Si5351A + IHU bus) |
> | CLK0_OUT, CLK1_OUT | Net label | Si5351A clock outputs |
> | BPSK_DATA | Net label | RP2040 → XOR modulator |
> | TX_OUT, RX_IN | Net label | RF paths to SMA connectors |
> | RX_BASEBAND | Net label | MCP6022 output → Pico ADC |

### Text Frame 5: Key Design Notes (Bottom-Right)

> **Key Design Decisions**
>
> 1. Power from EPS via CSKB bus — no on-board regulators
> 2. BPSK modulation at 145.67 MHz (before tripler) — 74LVC1G86
>    fails at 437 MHz, see overview.md timing analysis
> 3. Odd-order frequency multiplication preserves BPSK phase states
>    (3 × 180° = 540° ≡ 180° mod 360°)
> 4. Tripler bias 47kΩ — empirically optimized (-7.4 dBm @ 437 MHz)
> 5. All RF filter caps must be C0G/NP0 (not X7R)
> 6. I2C addresses: Si5351A = 0x60, EPS LTC4162 = 0x68 (no conflict)
> 7. Flat schematic design — nets connect by name across sheets
> 8. Prototype uses Pico module; bare RP2040 deferred to v2

### Text Frame 6: Sheet Index (Right Edge)

> **Sheet Index**
>
> | Sheet | Title | Contents |
> |-------|-------|----------|
> | 1 | Overview | This sheet — block diagram, design notes |
> | 2 | Clock Gen | Si5351A, 25 MHz crystal, I2C, clock outputs |
> | 3 | TX Chain | XOR modulator, tripler, BPF, ADL5602 MMIC |
> | 4 | RX Chain | PSA4 LNA, LO LPF, ADE-1+ mixer, IF term, Sallen-Key LPF, MCP6022 gain |
> | 5 | Digital Control | RP2040 (Pico module), GPIOs, USB |
> | 6 | Power | Distribution, protection, bypass |
> | 7 | Connectors | CSKB H1 + H2 bus, SMA ports, test points |

### Text Frame 7: Revision History (Bottom, or Separate Table)

> **Revision History**
>
> | Rev | Date | Author | Description |
> |-----|------|--------|-------------|
> | 0.1 | 2026-04-10 | NG | Initial schematic — all sheets placed, basic connectivity |
> | 0.2 | 2026-04-13 | NG | Added Connectors sheet, stack bus, removed on-board regulators, added overview sheet |
> | 0.3 | 2026-04-15 | NG | Added COMMS_IRQ on GP3 and SPI slave wiring on GP16–19; initial Pumpkin pin-number lock |
> | 0.4 | 2026-04-15 | NG | Rebuilt connectors against Pumpkin datasheet Rev. E: bus renamed PC/104 → CubeSat Kit Bus (CSKB); pin numbers remapped H10 → H1/H2; connector family corrected to 2× Samtec ESQ-126-39-G-D stackthrough (2×26, 52 pins each); see `system/interfaces/cskb_pinmap.md` |
> | 0.5 | 2026-04-30 | NG | Sheet 4 RX front-end rebuilt: SA612 active mixer (EOL, sourcing failed) replaced with ADE-1+ passive diode mixer + PSA4-5043+ MMIC LNA + 5-pole LC LPF on the LO line + 51 Ω IF termination. New refdes: U10 (LNA), L12 (Vd choke), L13/L14 + C57/C58/C59 (LO LPF), R19 (IF term), C53/C54/C55/C56/C60 (DC blocks + bypass). Removed: U3 became ADE-1+ (was SA612), and C21/C22/C26/C27 + R7 (SA612-specific support parts) deleted. +5V budget grew from ~80 mA to ~140 mA. Rationale in `rx_mixer_trade_study.md`; bench verification of LO drive level in `bringup/lo_drive_verification.md` and `bringup/si5351a_breakout_bench_test.md`. |
> | 0.6 | 2026-05-21 | NG | Pico pin reassignment for layout: `BPSK_DATA` moved from GP2 (pin 4) to GP20 (pin 26), `I2C_SDA` moved from GP4 (pin 6) to GP12 (pin 16, I2C0 alt), `I2C_SCL` moved from GP5 (pin 7) to GP13 (pin 17, I2C0 alt). All four originally-assigned pins (GP2/GP4/GP5/and the previously-unassigned spares) now free; spare GPIO header J3 candidate list updated accordingly. Net labels unchanged — no edits needed on other sheets. Added `rf_layout_guidelines.md` to Related Documents. |
> | 0.7 | 2026-05-21 | NG | Pico pin reassignment v2: clustered SPI + I2C onto the left-hand side of the Pico (pins 6–12) to shorten CSKB routing, freed GP16 (pin 21) for `BPSK_DATA` to shorten clock-edge run to the XOR/tripler. New mapping: `SPI_COMMS_MISO`=GP4 (pin 6), `SPI_COMMS_CS_N`=GP5 (pin 7), `SPI_COMMS_SCK`=GP6 (pin 9), `SPI_COMMS_MOSI`=GP7 (pin 10), `I2C_SDA`=GP8 (pin 11), `I2C_SCL`=GP9 (pin 12), `BPSK_DATA`=GP16 (pin 21). All on hardware peripherals (SPI0 + I2C0, both via alternate-function pin mux). Net labels unchanged — no edits needed on other sheets. Spare GPIO header J3 candidate list updated. |
> | 0.8 | 2026-05-21 | NG | I2C moved from GP8/GP9 (pins 11/12) to GP20/GP21 (pins 26/27) — keeps I2C on hardware I2C0 peripheral via different alternate-function pins, shifts I2C off the left side of the Pico for layout reasons (presumably to shorten the run to the Si5351A on the right side of the board). SPI block unchanged. GP8/GP9 returned to the spare GPIO header J3 candidate list. Net labels unchanged — no edits needed on other sheets. |
> | 0.9 | 2026-05-21 | NG | `RX_BASEBAND` moved from GP26/ADC0 (pin 31) to GP27/ADC1 (pin 32). Same ADC peripheral, different input channel — firmware change: `adc_select_input(0)` → `adc_select_input(1)`. Pin 31 freed (was the only ADC channel routed; now no signals on ADC0). Layout reason: shifting baseband signal entry one pin over. Net label unchanged. |
> | 1.0 | 2026-05-22 | NG | **Board converted from 2-layer to 4-layer** (JLCPCB JLC04161H-7628, 1.6 mm). Layer 2 = solid GND plane, Layer 3 = power distribution, L1/L4 = signals. Fixes (a) snake-y power routes that broke the ground pour in the RF zones on the 2-layer design, (b) Altium LSM showing 0.41 mm "thin" board because of placeholder dielectric value, (c) cleaner 50 Ω microstrip with predictable return path on L2. Triggered by reviewer feedback. New 50 Ω trace width: **0.38 mm (15 mil)** on top prepreg (0.21 mm, εr 4.4). Every existing RF trace must be re-set to 0.38 mm. New "Board Stackup" section added at the top of this doc. Also enables the via stitching / via fence techniques from `rf_layout_guidelines.md`. Mass impact ~10 g extra copper; cost impact ~$15 per 5-board run. |
> | 1.1 | 2026-05-22 | NG | Documentation improvement to the Board Stackup section: expanded "Impedance and Trace Width" subsection into a full 6-step procedure (RF net class, Width rule, rule priority, RF clearance rule, impedance verification, re-routing existing traces). Fixed obsolete reference to "Tools → Routing → Impedance Calculator" — in Altium 20+ this lives inside the Layer Stack Manager Impedance view. Added Saturn PCB Toolkit as fallback for older Altium versions. No schematic / layout changes. |
> | 1.2 | 2026-05-22 | NG | Refined 50 Ω trace width from 0.38 mm to **0.358 mm** based on Altium LSM impedance calculator with "Use solder mask" enabled (mask loading lowers required width by ~0.02 mm vs ideal). Width rule constraints updated accordingly (0.34 / 0.358 / 0.40 mm). Added a layer-naming mapping table (this doc's L1/L2/L3/L4 vs Altium's Top Layer / Layer 1 / Layer 2 / Bottom Layer) to prevent confusion when configuring impedance profiles. Clarified that the "Top ref" field stays empty for top-layer microstrip. No schematic / layout changes. |
> | 1.3 | 2026-05-22 | NG | Expanded "Net Name Convention" section with three new subsections: (1) **prefix convention** (`RF_*`, `LO_*`, `BB_*`) for naming internal nets so wildcard-based net classes work; (2) **three ways to populate an RF net class** — prefix-based wildcard, Net Class directive in the schematic (for fixing existing auto-named nets), or manual selection; (3) **how to rename `NetCXX_Y` nets** with net labels. Includes explicit examples of internal RF net names for the TX, RX, and LO chains. No schematic / layout changes; purely documentation. |
> | 1.4 | 2026-05-24 | NG | Net naming convention promoted to project level. Created `hardware/conventions/` directory and `hardware/conventions/net_naming.md` as the canonical project-wide reference (prefix system, Altium application techniques, recovery procedure for inherited designs). Refactored this doc's "Naming for wildcard rules" section to a short pointer to the project-level doc + the comms-specific named-net list (TX/RX/LO/BB chains). Added the project-level naming doc to Related Documents. No schematic / layout changes; documentation restructure to support cross-board consistency (EPS, IHU, payload all reference the same convention). |
> | 1.5 | 2026-05-31 | NG | **LO drive verification complete on Adafruit 5640 breakout + Pico 2 + TinySA Ultra.** Si5351A CLK1 at 145.9 MHz, 8 mA drive, no series R: measured **+9.4 dBm fundamental** into 50 Ω (exceeds ADE-1+ +7 dBm target), 2nd harmonic at -17 dB rel, 3rd harmonic at **437.683 MHz / -12.2 dB rel (-2.77 dBm absolute)**. Post-LPF 3rd harmonic at mixer input: -37 dBm — 30+ dB margin over worst-case TX-leak spur scenario. **R3 (CLK0) and R4 (CLK1) both set to 0Ω in BOM** — CLK1 needs full drive into the LPF/mixer chain; CLK0 doesn't care because XOR is high-Z (no functional difference between 0Ω and 33Ω at the XOR input). Footprints kept for swap to 33Ω if ringing/EMI mitigation needed during bring-up. Removed obsolete "consider 0Ω, verify on bench" caveat from the CLK output coupling Note. Full bench results in `bringup/si5351a_bringup_log.md`. **Design committed for fab.** |

### How to Build This Sheet in Altium

1. Create a new schematic sheet: `Overview.SchDoc`
2. Use Place > Text Frame for each section above
3. For the block diagram, you can either:
   - Use text frames with monospace font (as shown above)
   - Use Place > Drawing Tools > Line/Rectangle to draw boxes and arrows
   - Import a PNG/SVG of the block diagram (Place > Drawing Tools > Graphic)
4. No electrical components, no nets, no power ports on this sheet
5. Set the title block: "CubeSat Comms Board — Overview", Rev 1.5

---
---

## Sheet 2: Clock Gen (Si5351A)

This sheet contains the Si5351A clock generator, its crystal, I2C
pull-ups, and output coupling networks.

### Text Frame (Place > Text Frame, top of sheet):

> CLOCK GENERATOR — Si5351A (I2C address 0x60). Generates three
> independent clock outputs from a single 25 MHz crystal. CLK0 =
> 145.67 MHz (TX carrier, tripled to 437 MHz). CLK1 = 145.9 MHz
> (RX local oscillator for ADE-1+ passive mixer; see RX sheet).
> CLK2 = spare. All outputs driven at 8 mA (max) into 50Ω loads.
> Controlled by RP2040 over I2C.

---

### Section A: Si5351A IC (Center of Sheet)

#### Component

Search Manufacturer Part Search for "Si5351A-B-GT" (MSOP-10 package).
Place in the center of the sheet.

#### Pin-by-Pin Connections

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | VDD | `+3V3` | Main supply, bypass with 100nF + 10µF |
| 2 | GND | `GND` | |
| 3 | CLK0 | `CLK0_OUT` via 100nF DC block | TX carrier (145.67 MHz) |
| 4 | CLK1 | `CLK1_OUT` via 100nF DC block | RX LO (145.9 MHz) |
| 5 | CLK2 | No connect (or spare header) | Reserve for future use |
| 6 | VDDO | `+3V3` | Output driver supply, bypass with 100nF |
| 7 | SCL | `I2C_SCL` | I2C clock |
| 8 | SDA | `I2C_SDA` | I2C data |
| 9 | XA | Crystal pin 1 | 25 MHz crystal |
| 10 | XB | Crystal pin 2 | 25 MHz crystal |

#### Bypass Capacitors

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| C1 | 100nF, 16V, X7R | 0402 | VDD (pin 1) to GND | HF bypass |
| C2 | 10µF, 10V, X5R | 0805 | VDD (pin 1) to GND | Bulk bypass |
| C3 | 100nF, 16V, X7R | 0402 | VDDO (pin 6) to GND | Output driver bypass |

#### Note (Place > Note, next to bypass caps):

> C1/C2 at VDD: place C1 (100nF) directly at pin 1 with shortest
> possible traces. C2 (10µF) can be further away. C3 at VDDO: place
> directly at pin 6. Per Skyworks AN619, poor VDDO bypass causes
> increased output jitter. Keep all bypass return paths to GND short.

---

### Section B: 25 MHz Crystal (Left of Si5351A)

#### Components

| Ref | Value | Package | Connection | Notes |
|---|---|---|---|---|
| Y1 | 25.000 MHz, 10pF load | HC-49/US or 3.2x2.5mm SMD | XA (pin 9) and XB (pin 10) | Fundamental mode |
| C4 | 10pF, 50V, C0G/NP0 | 0402 | XA (pin 9) to GND | Crystal load cap |
| C5 | 10pF, 50V, C0G/NP0 | 0402 | XB (pin 10) to GND | Crystal load cap |

```
           Y1 (25 MHz)
XA (pin 9) ──┤├── XB (pin 10)
      │                │
    C4 (10pF)       C5 (10pF)
      │                │
     GND              GND
```

#### Note (Place > Note, next to crystal):

> Crystal load capacitance: CL = (C4 × C5)/(C4 + C5) + Cstray.
> With C4=C5=10pF and ~3pF stray: CL ≈ 8pF. Match to crystal's
> specified load capacitance. If crystal specifies 8pF load, use 10pF
> caps. If crystal specifies 10pF load, use 15pF caps. C0G/NP0
> dielectric is mandatory — X7R temperature drift will shift frequency.

---

### Section C: I2C Pull-Up Resistors (Bottom-Left)

#### Components

| Ref | Value | Package | Connection |
|---|---|---|---|
| R1 | 4.7kΩ, 1% | 0402 | I2C_SCL to +3V3 |
| R2 | 4.7kΩ, 1% | 0402 | I2C_SDA to +3V3 |

```
+3V3 ── R1 (4.7k) ──┬── I2C_SCL (port)
                     │
                  Si5351A SCL (pin 7)

+3V3 ── R2 (4.7k) ──┬── I2C_SDA (port)
                     │
                  Si5351A SDA (pin 8)
```

#### Note (Place > Note, next to pull-ups):

> I2C pull-ups: 4.7kΩ to +3V3. Si5351A address = 0x60 (7-bit).
> Standard mode (100 kHz) or Fast mode (400 kHz). These are the ONLY
> I2C pull-ups on the comms board — the EPS board has its own pull-ups
> for the LTC4162. If the bus is too slow (rounded edges on SCL), try
> 2.2kΩ. If multiple devices on the bus have pull-ups, the effective
> resistance drops — may need to remove one set.

---

### Section D: Clock Output Coupling (Right of Si5351A)

Each clock output needs a DC blocking cap and optional series resistor
for impedance matching.

#### Components

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| C6 | 100nF, 16V, X7R | 0402 | CLK0 (pin 3) to CLK0_OUT net | DC blocking |
| R3 | **0Ω**, 0402 | 0402 | Series in CLK0_OUT path | Footprint kept for source termination if needed; populate 0Ω (validated Rev 1.5) |
| C7 | 100nF, 16V, X7R | 0402 | CLK1 (pin 4) to CLK1_OUT net | DC blocking |
| R4 | **0Ω**, 0402 | 0402 | Series in CLK1_OUT path | Footprint kept for source termination if needed; populate 0Ω (validated Rev 1.5) |

```
CLK0 (pin 3) ── C6 (100nF) ── R3 (0Ω) ──→ CLK0_OUT (port)

CLK1 (pin 4) ── C7 (100nF) ── R4 (0Ω) ──→ CLK1_OUT (port)

CLK2 (pin 5) ── [no connect X] or spare header
```

#### Note (Place > Note, next to output coupling):

> DC blocking caps prevent Si5351A output bias from affecting
> downstream stages. R3 and R4 are populated as **0Ω** — the
> footprints remain so a 33Ω can be swapped back in if ringing or
> EMI shows up during bring-up, but the default is 0Ω.
>
> Rationale: CLK1 feeds the ADE-1+ passive mixer LO at 145.9 MHz
> (target +7 dBm), and bench measurement on the Adafruit breakout
> (Rev 1.5 bring-up log) showed +9.4 dBm into 50 Ω with no series R
> — 0Ω is needed to preserve full drive into the LPF/mixer chain.
> CLK0 feeds the XOR BPSK modulator (high-Z CMOS input); 0Ω is fine
> because the load doesn't draw current — XOR sees full rail-to-rail
> swing either way. 0Ω on both keeps the design consistent.
>
> Si5351A outputs are push-pull CMOS with ~50Ω source impedance at
> 8mA drive. CLK2 reserved — bring to a test header if board space
> permits.

---

### Sheet 2 Schematic Layout Suggestion

```
┌──────────────────────────────────────────────────────────────────┐
│  [Text Frame: Clock Generator Description]                       │
│                                                                  │
│        Y1 (25 MHz)          ┌────────────┐                       │
│     C4─┤├─C5              │  Si5351A   │                       │
│      │    │                │            │                       │
│     GND  GND    +3V3─C1─C2─┤VDD   CLK0├─C6─R3─→ CLK0_OUT port │
│                            │VDDO  CLK1├─C7─R4─→ CLK1_OUT port │
│                       C3──┤      CLK2├─[NC]                    │
│                            │XA    SCL ├──→ I2C_SCL port        │
│                   Y1 pin1──┤XB    SDA ├──→ I2C_SDA port        │
│                   Y1 pin2──┤      GND ├──GND                   │
│                            └────────────┘                       │
│                                                                  │
│   +3V3──R1──I2C_SCL         [Notes as specified]                │
│   +3V3──R2──I2C_SDA                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Sheet 2 Ports Checklist

- [ ] `I2C_SDA` — bidirectional, to RP2040 and CSKB H1.41
- [ ] `I2C_SCL` — bidirectional, to RP2040 and CSKB H1.43
- [ ] `CLK0_OUT` — output, 145.67 MHz to TX Chain
- [ ] `CLK1_OUT` — output, 145.9 MHz to RX Chain
- [ ] `+3V3` — power port (global, from EPS via bus)
- [ ] `GND` — power port (global)

---
---

## Sheet 3: TX Chain

This sheet implements the complete 437 MHz BPSK transmit chain: XOR
modulator, frequency tripler, band-pass filter, and MMIC amplifier.

### Text Frame (Place > Text Frame, top of sheet):

> TX CHAIN — 437 MHz BPSK downlink transmitter. The carrier from the
> Si5351A (145.67 MHz) is BPSK-modulated by the 74LVC1G86 XOR gate,
> then frequency-tripled to 437 MHz by a class-C biased BFR92A
> transistor. A 3-pole LC BPF selects the 3rd harmonic and rejects
> the fundamental and 2nd harmonic. The ADL5602 MMIC provides ~20 dB
> gain to bring the signal to ~+10 dBm output. BPSK phase states are
> preserved through odd-order multiplication: 3 × 180° = 540° ≡ 180°.

---

### Section A: XOR BPSK Modulator (Left of Sheet)

#### Components

| Ref | Value/Part | Package | Connection |
|---|---|---|---|
| U1 | SN74LVC1G86DBVR | SOT-23-5 | XOR gate |
| C8 | 100nF, 16V, X7R | 0402 | VCC (pin 5) to GND bypass |
| R5 | 100Ω, 1% | 0402 | Series on BPSK_DATA line |
| C9 | 10pF, 50V, C0G | 0402 | BPSK_DATA to GND (edge softening) |

#### Pin Connections

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | A | `CLK0_OUT` (from Si5351A) | 145.67 MHz carrier input |
| 2 | B | `BPSK_DATA` via R5/C9 network | Data from RP2040 GPIO |
| 3 | GND | `GND` | |
| 4 | Y | `BPSK_145` via 100nF DC block (C10) | Modulated output |
| 5 | VCC | `+3V3` | Bypass with C8 |

```
CLK0_OUT (port) ──→ pin 1 (A)
                                    74LVC1G86
BPSK_DATA (port) ── R5 (100Ω) ──┬── pin 2 (B)
                                 │
                              C9 (10pF)         pin 4 (Y) ── C10 (100nF) ──→ to tripler
                                 │
                                GND
                                           +3V3 ── C8 ── pin 5 (VCC)
                                           GND ────────── pin 3
```

#### Note (Place > Note, next to XOR gate):

> 74LVC1G86 operates at 145.67 MHz where it has massive timing
> margin (half-period = 3.43 ns vs typical tpd = 0.6–2.3 ns).
> R5/C9 on the data input provide edge softening to reduce spectral
> splatter — the data rate is only 1200–9600 baud so the RC time
> constant (1 ns) has zero effect on data. The BPSK signal at 145.67
> MHz feeds the frequency tripler; phase states (0°/180°) are
> preserved through the 3× multiplication. See overview.md for the
> full timing analysis showing why 437 MHz operation fails.

---

### Section B: Frequency Tripler (Center-Left)

#### Components

| Ref | Value/Part | Package | Connection | Notes |
|---|---|---|---|---|
| Q1 | BFR92A (flight) / 2N3904 (proto) | SOT-23 / SOT-23 | Tripler transistor | ft=5GHz / ft=300MHz |
| R6 | 47kΩ, 5% | 0402 | Base to GND | Class-C bias (optimized from breadboard testing) |
| L1 | 220nH, ±5% | 0805 (Coilcraft 0805CS) | VCC to collector | RFC, SRF > 1 GHz |
| C10 | 100nF, 16V, X7R | 0402 | XOR output to base | DC blocking / AC coupling input |
| C11 | 100nF, 16V, X7R | 0402 | Collector to BPF input | DC blocking / AC coupling output |
| C12 | 100nF, 16V, X7R | 0402 | +5V to GND at RFC top | Local bypass for tripler supply |

```
                    +5V
                     │
                  C12 (100nF)──GND
                     │
                  L1 (220nH RFC)
                     │
C10 (100nF) ──┬──── Collector
  from XOR    │
              │     Q1 (BFR92A)
           R6 (47k)
              │     Base
              │      │
             GND   Emitter ── C11 (100nF) ──→ TRIPLER_OUT
                     │
                    GND
```

Wait — the standard tripler topology has the output from the collector,
not the emitter. Corrected circuit:

```
                         +5V
                          │
                       C12 (100nF)──GND
                          │
                       L1 (220nH RFC)
                          │
BPSK_145 ── C10 (100nF) ─┬── Base
                          │
                       R6 (47kΩ)        Collector ── C11 (100nF) ──→ TRIPLER_OUT
                          │               │
                         GND           Q1 (BFR92A)
                                          │
                                       Emitter
                                          │
                                         GND
```

#### Note (Place > Note, next to tripler):

> Class-C frequency tripler. R6 (47kΩ) biases the transistor below
> cutoff — it only conducts on positive input peaks, generating
> strong harmonic content. 47kΩ was empirically optimized on the
> breadboard prototype: -7.4 dBm at 437 MHz with 2N3904 (vs -12.2 dBm
> at 10kΩ). BFR92A (ft=5 GHz, SOT-23) is the flight transistor;
> 2N3904 (ft=300 MHz) validated during bring-up. RFC L1 provides DC
> bias path while presenting high impedance at RF. SRF of L1 must
> be well above 437 MHz — Coilcraft 0805CS-221XJRC (SRF ~1.5 GHz).
> Supply is +5V for maximum collector swing and harmonic output.

---

### Section C: 437 MHz Band-Pass Filter (Center)

3-pole LC band-pass filter centered at 437 MHz. This is the most
critical filter in the TX chain — it must reject the fundamental
(145.67 MHz) and 2nd harmonic (291.3 MHz) by >30 dB.

#### Components

| Ref | Value | Package | Dielectric | Notes |
|---|---|---|---|---|
| C13 | 10pF, 50V | 0402 | C0G/NP0 | Series input cap |
| L2 | 15nH, ±2% | 0402 | — | Shunt inductor |
| C14 | 6.8pF, 50V | 0402 | C0G/NP0 | Shunt cap (with L2 forms resonator) |
| L3 | 15nH, ±2% | 0402 | — | Series coupling inductor |
| C15 | 6.8pF, 50V | 0402 | C0G/NP0 | Center shunt cap |
| L4 | 15nH, ±2% | 0402 | — | Shunt inductor |
| C16 | 10pF, 50V | 0402 | C0G/NP0 | Series output cap |

#### Note (Place > Note, next to BPF):

> 437 MHz BPF: 3-pole LC, ~5 MHz bandwidth, target <3 dB insertion
> loss. ALL capacitors MUST be C0G/NP0 dielectric — X7R has voltage-
> dependent capacitance that detunes the filter and generates
> intermodulation products at RF. Starting values — tune with VNA
> during bring-up. Required rejection: >30 dB at 145.67 MHz
> (fundamental), >30 dB at 291.3 MHz (2nd harmonic), >20 dB at
> 582.7 MHz (4th harmonic).

---

### Section D: MMIC Amplifier (Right)

#### Components

| Ref | Value/Part | Package | Connection | Notes |
|---|---|---|---|---|
| U2 | ADL5602ARKZ-R7 | SOT-89 (3-pin) | MMIC gain block | 20 dB gain, DC-4 GHz |
| C17 | 100nF, 16V, X7R | 0402 | Input DC block | AC coupling in |
| C18 | 100nF, 16V, X7R | 0402 | Output DC block | AC coupling out |
| L5 | 220nH, ±5% | 0805 | +5V to RFOUT pin (bias tee) | RFC for DC feed |
| C19 | 100nF, 16V, X7R | 0402 | +5V to GND at L5 junction | Supply bypass |
| C20 | 10µF, 10V, X5R | 0805 | +5V to GND | Bulk supply bypass |

#### ADL5602 Pin Connections

The ADL5602 is a **3-pin** SOT-89 device. There is no dedicated VCC pin —
DC bias enters through the **RFOUT pin** via an external bias tee (inductor
L5). This is standard for MMIC gain blocks.

| Pin | Name | Connect To | Notes |
|---|---|---|---|
| 1 | RFIN | `TX_437` via C17 (DC block) | RF input from BPF |
| 2 | GND | `GND` | Ground, solder pad to ground plane |
| 3 | RFOUT | Bias tee junction (see below) | RF output + DC bias input |

**Bias tee at RFOUT (pin 3):**

```
                         +5V
                          │
                    C19(100nF) C20(10µF)
                          │       │
                         GND     GND
                          │
                       L5 (220nH RFC)
                          │
TX_437 ── C17 (100nF) ── RFIN (pin 1)         pin 3 (RFOUT) ──┬── C18 (100nF) ──→ TX_OUT
                                                               │
                          GND (pin 2) ── GND                L5 (220nH)
                                                               │
                                                          +5V ─┘
```

Corrected diagram:

```
                                    +5V
                                     │
                               C19(100nF) C20(10µF)
                                     │       │
                                    GND     GND
                                     │
                                  L5 (220nH RFC)
                                     │
TX_437 ── C17 (100nF) ── pin 1 ─┤        ├─ pin 3 ──┬── C18 (100nF) ──→ TX_OUT
                                 │ ADL5602 │         │
                                 └─ pin 2 ─┘      L5 junction
                                     │               │
                                    GND            +5V (via L5)
```

The key point: pin 3 (RFOUT) carries both the RF signal out AND the DC
supply current in. L5 feeds DC from +5V to pin 3 while blocking RF from
reaching the supply. C18 passes RF to the output while blocking the DC
bias from reaching the TX SMA.

#### Note (Place > Note, next to MMIC):

> ADL5602: 50Ω matched input/output, 20 dB gain, DC to 4 GHz.
> 3-pin SOT-89 — NO separate VCC pin. DC bias enters through the
> RFOUT pin (pin 3) via bias tee inductor L5. This is standard for
> MMIC gain blocks. L5 (RFC) feeds DC while presenting high impedance
> at RF. C18 passes RF while blocking DC. Supply current ~60mA from
> +5V rail. C17 blocks DC at the input. Expected output: -7 dBm
> (tripler) + 20 dB (MMIC) ≈ +13 dBm at 437 MHz. May need an
> attenuator pad if output exceeds amateur power limits or if the
> MMIC saturates — check P1dB in datasheet.

---

### Section E: Output Band-Pass Filter (Far Right)

Second 437 MHz BPF, placed after the MMIC. The MMIC has broadband gain
(DC–4 GHz) so it amplifies any residual harmonics and spurs that made
it through the first BPF, and can generate its own intermodulation
products at high output levels. This output filter is the last stage
before the antenna — it ensures clean radiated spectrum and compliance
with amateur radio spurious emission limits.

#### Components

| Ref | Value | Package | Dielectric | Notes |
|---|---|---|---|---|
| C45 | 10pF, 50V | 0402 | C0G/NP0 | Series input cap |
| L6 | 15nH, ±2% | 0402 | — | Shunt inductor |
| C46 | 6.8pF, 50V | 0402 | C0G/NP0 | Shunt cap (with L6 forms resonator) |
| L7 | 15nH, ±2% | 0402 | — | Series coupling inductor |
| C47 | 6.8pF, 50V | 0402 | C0G/NP0 | Center shunt cap |
| L8 | 15nH, ±2% | 0402 | — | Shunt inductor |
| C48 | 10pF, 50V | 0402 | C0G/NP0 | Series output cap |

Same topology and starting values as the pre-MMIC BPF (Section C).

```
TX_OUT (from C18) ──[C45]──┬──[L7]──┬──[C48]──→ TX_OUT (to SMA, port)
                           │        │
                        L6 + C46  L8 + C47
                           │        │
                          GND      GND
```

#### Note (Place > Note, next to output BPF):

> Output BPF: identical topology to the pre-MMIC filter. Required
> because the ADL5602 has broadband gain (DC–4 GHz) and will amplify
> any residual spurs from the tripler, plus generate its own harmonics
> at +13 dBm output. FCC Part 97 / ITU amateur satellite rules require
> spurious emissions at least 43 dB below carrier for transmitters
> >5W, and good practice for QRP is >30 dB. Two cascaded 3-pole BPFs
> (pre- and post-MMIC) provide >60 dB total harmonic rejection.
> Same C0G/NP0 cap and tight-tolerance inductor requirements as the
> first BPF. Values may need independent tuning from the first BPF
> since the source/load impedances differ slightly.

---

### Sheet 3 Schematic Layout Suggestion

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  [Text Frame: TX Chain Description]                                          │
│                                                                              │
│  CLK0_OUT ─→ [XOR 74LVC1G86] ─C10─→ [Tripler BFR92A] ─C11─→ [BPF 1]        │
│  (port)       ↑ BPSK_DATA          R6(47k)  L1(RFC)    L2 C14               │
│               (port)                                    L3 C15               │
│                                                         L4 C16               │
│                                                           │                  │
│                                                     ─C17─→ [ADL5602] ─C18─→  │
│                                                                              │
│                                              [BPF 2] ─→ TX_OUT (port)       │
│                                              L6 C46                          │
│                                              L7 C47                          │
│                                              L8 C48                          │
│                                                                              │
│  [Notes throughout as specified]                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Sheet 3 Ports Checklist

- [ ] `CLK0_OUT` — input, 145.67 MHz from Clock Gen sheet
- [ ] `BPSK_DATA` — input, from Digital Control (RP2040 GPIO)
- [ ] `TX_OUT` — output, to Connectors sheet (TX SMA)
- [ ] `+3V3` — power port (XOR gate supply)
- [ ] `+5V` — power port (tripler and MMIC supply)
- [ ] `GND` — power port (global)

---
---

## Sheet 4: RX Chain

This sheet implements the 145.9 MHz AFSK uplink receiver: input BPF,
mixer, baseband Sallen-Key low-pass filter, and gain stage.

### Text Frame (Place > Text Frame, top of sheet):

> RX CHAIN — 145.9 MHz FM AFSK uplink receiver. A 2m band-pass filter
> at the input rejects out-of-band signals before the LNA. A
> PSA4-5043+ MMIC LNA (~21 dB gain, ~1 dB NF) sets the system noise
> figure and recovers the conversion loss of the downstream passive
> mixer. The ADE-1+ double-balanced diode mixer downconverts the 2m
> signal to baseband using the Si5351A CLK1 as LO; an LC low-pass on
> the LO line suppresses square-wave harmonics that would otherwise
> create spurious responses. A 51 Ω resistor terminates the mixer IF
> port. A 2nd-order Sallen-Key LPF (fc ≈ 3.3 kHz) filters the baseband,
> passing the 1200/2200 Hz AFSK tones while rejecting mixer products
> and noise. The MCP6022 U7B stage provides ~20 dB gain before the
> RP2040 ADC. Single-supply operation with 1.65V virtual ground
> (mid-supply bias). See rx_mixer_trade_study.md for the SA612 → ADE-1+
> swap rationale.

---

### Section A: 2m Input Band-Pass Filter (Far Left)

This filter sits between the RX SMA connector and the PSA4-5043+ LNA
input. It passes the 2m amateur band (~144–148 MHz) and rejects
out-of-band signals — especially the 437 MHz TX signal which could
leak back through the board and saturate the LNA or compress the
mixer, and commercial FM broadcast (88–108 MHz) which is extremely
strong compared to a satellite uplink.

#### Components

| Ref | Value | Package | Dielectric | Notes |
|---|---|---|---|---|
| C49 | 10pF, 50V | 0402 | C0G/NP0 | Series input cap |
| L9 | 82nH, ±2% | 0402 | — | Shunt inductor |
| C50 | 10pF, 50V | 0402 | C0G/NP0 | Shunt cap (with L9 forms resonator) |
| L10 | 82nH, ±2% | 0402 | — | Series coupling inductor |
| C51 | 10pF, 50V | 0402 | C0G/NP0 | Center shunt cap |
| L11 | 82nH, ±2% | 0402 | — | Shunt inductor |
| C52 | 10pF, 50V | 0402 | C0G/NP0 | Series output cap |

Starting values — 3-pole LC BPF centered at ~146 MHz. These will
need tuning with a VNA during bring-up.

```
RX_IN (port) ──[C49]──┬──[L10]──┬──[C52]──→ to PSA4 RF_IN (via C53 DC block)
                       │         │
                    L9 + C50   L11 + C51
                       │         │
                      GND       GND
```

#### Note (Place > Note, next to 2m BPF):

> 2m input BPF: 3-pole LC, centered ~146 MHz, ~4 MHz bandwidth.
> Critical for protecting the LNA front-end and mixer from overload. Must reject:
> - 437 MHz TX leakage (>40 dB — this is your own transmitter)
> - FM broadcast 88–108 MHz (>30 dB — these signals are very strong)
> - 2nd harmonic of LO at 291.8 MHz (>20 dB)
> ALL capacitors must be C0G/NP0. Starting values are estimates —
> tune L and C values with VNA to center the passband on 145.9 MHz
> and achieve <3 dB insertion loss at the operating frequency.
> If insertion loss is too high, consider a 2-pole filter instead
> (remove the center L10 coupling and one shunt section).

---

### Section B: LNA → LO LPF → ADE-1+ Mixer → IF Termination (Center-Left)

This section replaces the original SA612 active mixer (EOL part) with a
**PSA4-5043+ LNA** in front of an **ADE-1+ passive diode mixer**, plus a
5-pole LC LPF on the LO line to suppress Si5351A square-wave harmonics,
and a 51 Ω resistor terminating the IF port. See
[`rx_mixer_trade_study.md`](rx_mixer_trade_study.md) for the full
decision rationale.

The four sub-blocks are presented in signal-flow order: LNA, LO LPF, mixer,
IF termination.

---

#### B.1 — PSA4-5043+ LNA

| Ref | Value/Part | Package | Connection | Notes |
|---|---|---|---|---|
| U10 | PSA4-5043+ | SOT-89 (3 pin + tab) | VHF/UHF LNA | Mini-Circuits, JLC C5240848 |
| C53 | 100nF, 16V, X7R | 0402 | Input DC block | 2m BPF out → LNA RF_IN |
| C54 | 100nF, 16V, X7R | 0402 | Output DC block | LNA RF_OUT → LO of mixer path |
| L12 | 1 µH, wirewound, SRF > 500 MHz | 0805 or 1008 | Vd bias choke | Coilcraft 0805CS-102 or equiv RF wirewound |
| C55 | 100nF, 16V, X7R | 0402 | Vd HF bypass | Right at choke top |
| C56 | 10µF, 10V, X5R | 0805 | Vd bulk bypass | Within ~10 mm of L12 |

**PSA4-5043+ pin assignment** (verify against Mini-Circuits datasheet — SOT-89 case style "WW107"):

| Pin | Name | Connect To |
|---|---|---|
| 1 | RF_IN | C53 (DC block) ← 2m BPF output |
| 2 | GND | `GND` (tab also to GND) |
| 3 | RF_OUT / Vd | Bias choke L12 to +5V, AND C54 (DC block) → mixer RF input |

```
Signal path (no shunt to GND between C53 and pin 1 — series only):

  2m BPF out ── C53 (DC block) ─────────→ PSA4 pin 1 (RF_IN)

Ground reference (separate connection, not on signal path):

  PSA4 pin 2 ──── GND plane    (also tie SOT-89 tab to GND)

Bias / output (Vd injected at pin 3 through RF choke, then DC-blocked
into the mixer):

                                +5V
                                 │
                              C56 (10 µF)  ─── GND
                                 │
                              C55 (100 nF) ─── GND
                                 │
                              L12 (1 µH RF choke, SRF > 500 MHz)
                                 │
  PSA4 pin 3 ───────────────────┴───── C54 (DC block) ─→ ADE-1+ RF pin
  (RF_OUT and Vd share this pin)
```

> **PSA4-5043+ Note:** Self-biased pHEMT LNA. Vd applied at the RF_OUT
> pin through an RF choke; the DC block C54 separates RF from the bias.
> Typical performance at 145 MHz: ~21 dB gain, ~1.0 dB NF, +20 dBm
> P1dB(out), 60 mA at Vd=+5V. The 1 µH wirewound MUST have SRF above
> 500 MHz — a power inductor with low SRF will resonate inside our band
> and kill gain. Coilcraft 0805CS series or Murata LQW2BAS family in
> 1 µH are appropriate. Grounding: tie pin 2 *and* the SOT-89 tab to a
> solid ground plane with multiple vias. Layout: keep input and output
> traces short and on opposite sides of the package to avoid feedback.

---

#### B.2 — Si5351A LO Low-Pass Filter

A 5-pole Butterworth LC LPF, fc ≈ 200 MHz, in 50 Ω. The Si5351A output
is a CMOS square wave; without filtering, its 3rd harmonic at 437.7 MHz
would mix with our own 437 MHz TX leakage and create a spurious response
right on top of legitimate RX signals.

| Ref | Value | Package | Dielectric | Position |
|---|---|---|---|---|
| C24 | 100nF, 16V, X7R | 0402 | — | DC block on CLK1_OUT (preserved from old design) |
| C57 | 10pF, 50V | 0402 | C0G/NP0 | 1st shunt cap |
| L13 | 68nH, ±2% | 0402 | — | 1st series inductor |
| C58 | 33pF, 50V | 0402 | C0G/NP0 | Center shunt cap |
| L14 | 68nH, ±2% | 0402 | — | 2nd series inductor |
| C59 | 10pF, 50V | 0402 | C0G/NP0 | Output shunt cap |

```
CLK1_OUT (port) ── C24 ──┬── L13 ──┬── L14 ──┬──→ to ADE-1+ LO pin
                          │         │          │
                       C57 (10p)  C58 (33p)  C59 (10p)
                          │         │          │
                         GND       GND        GND
```

> **LO LPF Note:** 5-pole Butterworth, fc ≈ 200 MHz, calculated values
> rounded to nearest standard. Insertion loss at 145.9 MHz: ~0.2 dB.
> Attenuation at 3rd harmonic (437.7 MHz): ~34 dB. Attenuation at 5th
> harmonic (729.5 MHz): ~50 dB. C0G/NP0 dielectric is mandatory on all
> three caps — X7R will detune the filter. Inductors should be ±2%
> tolerance or better; 0402 multilayer chip inductors with Q > 25
> at 150 MHz are appropriate (e.g., Murata LQG15HS or Coilcraft 0402CS).
> Verify on VNA before fab — exact LPF response is sensitive to PCB
> parasitics at these frequencies.

---

#### B.3 — ADE-1+ Mixer

| Ref | Value/Part | Package | Notes |
|---|---|---|---|
| U3 | ADE-1+ | CD636 (7.87 × 5.59 mm, 6-pad SMT) | Mini-Circuits passive diode ring, Level 7 |

**ADE-1+ pin connections** (per datasheet [`C2942210.pdf`](C2942210.pdf)):

| Pin | Name | Connect To |
|---|---|---|
| 1 | GND | `GND` |
| 2 | IF | R19 (51 Ω term) to GND, then DC block C60 to Sallen-Key input |
| 3 | RF | C54 (LNA output DC block) ← PSA4 |
| 4 | GND | `GND` |
| 5 | GND | `GND` |
| 6 | LO | LO LPF output ← Si5351A CLK1 chain |

```
                        ┌──────────────────┐
                        │   ADE-1+         │
LNA out (via C54) ──── 3│ RF            IF │2 ──┬── R19 (51Ω) ── GND
                        │                  │     │
LO LPF out ─────────── 6│ LO               │     └── C60 ── to Sallen-Key
                        │                  │
                        │ GND  GND  GND    │
                        └──┬────┬────┬─────┘
                           1    4    5
                           │    │    │
                          GND  GND  GND
```

> **ADE-1+ Note:** Passive double-balanced diode-ring mixer, 0.5–500 MHz
> LO/RF, DC–500 MHz IF. **No DC supply required** — transformer-coupled
> on all three ports. Typical performance at our band: ~5 dB conversion
> loss, ~55 dB LO-RF isolation, ~45 dB LO-IF isolation, +15 dBm IIP3,
> +1 dBm P1dB. LO drive: +7 dBm specified, +4 dBm to +10 dBm tolerable
> with mild conversion-loss penalty. Max RF power 50 mW (+17 dBm).
> Package footprint (CD636) must be drawn in Altium — see
> recommended PCB land pattern in datasheet. Tie all three GND pads
> (1, 4, 5) to ground plane with vias underneath, kept short.

---

#### B.4 — IF Port Termination

| Ref | Value | Package | Connection |
|---|---|---|---|
| R19 | 51 Ω, 1% | 0402 | ADE-1+ pin 2 (IF) to GND |
| C60 | 100nF, 16V, X7R | 0402 | ADE-1+ pin 2 → Sallen-Key R8 (DC block) |

> **IF Termination Note:** Passive diode mixers require the IF port to
> see ~50 Ω across the band of interest, otherwise the diode bridge
> doesn't balance properly and IP3/conversion loss degrade sharply. The
> Sallen-Key input (22 kΩ at R8) is essentially open-circuit to the
> mixer — so we add R19 (51 Ω) directly across the IF port to GND. The
> Sallen-Key just senses the voltage across this resistor through DC
> block C60. For more sophisticated designs, replace R19 with a
> diplexer (RC LPF + RL HPF) to maintain 50 Ω at *all* frequencies, but
> a single resistor is adequate for AFSK at baseband.

---

### Section C: Sallen-Key Low-Pass Filter (Center)

2nd-order Butterworth LPF, fc ≈ 3.3 kHz. Passes AFSK tones
(1200/2200 Hz) and rejects mixer products and wideband noise.

#### Components

| Ref | Value | Package | Dielectric | Connection |
|---|---|---|---|---|
| R8 | 22kΩ, 1% | 0402 | — | Series input to junction |
| R9 | 22kΩ, 1% | 0402 | — | Junction to op-amp IN+ |
| C28 | 2.2nF, 25V, C0G/NP0 | 0402 | — | Junction (R8-R9) to op-amp output (feedback) |
| C29 | 2.2nF, 25V, C0G/NP0 | 0402 | — | Op-amp IN+ to GND |

**Op-amp: MCP6022 U7A** (half of dual MCP6022, pins 1-3)

| MCP6022 Pin | Name | Connect To |
|---|---|---|
| 1 | VOUT_A | Output → feedback to C28, → C30 (AC couple to gain stage) |
| 2 | VIN-_A | Direct wire to VOUT_A (pin 1) — unity gain feedback |
| 3 | VIN+_A | From R9, C29 to GND, C28 from junction |
| 8 | VDD | `+3V3` via C31 (100nF bypass) |
| 4 | VSS | `GND` |

```
                  R8 (22k)            R9 (22k)
RX_IF ──────────/\/\/──────┬────────/\/\/──────┬──→ IN+ (pin 3)
                           │                   │
                        C28 (2.2nF)          C29 (2.2nF)      VOUT (pin 1) ──→ RX_FILT
                           │                   │                │
                        VOUT (pin 1)          GND            IN- (pin 2) ←┘
                        (feedback)                           (unity gain)
```

#### Note (Place > Note, next to Sallen-Key):

> Sallen-Key topology per Art of Electronics Fig 6.16A. C28 is the
> FEEDBACK capacitor — connects from the R8/R9 junction to the op-amp
> output. C29 goes from IN+ to GND. This is NOT two caps to ground —
> C28's feedback to the output is what creates the complex pole pair
> and gives -40 dB/decade rolloff (2nd order). With R8=R9 and C28=C29
> (equal-component Butterworth), Q = 0.707, no ringing.
> fc = 1/(2π×R×C) = 1/(2π×22k×2.2nF) = 3,289 Hz.
> LTspice verified: -3dB at 2,985 Hz, 1200 Hz passes at -0.56 dB,
> 2200 Hz at -1.75 dB. C0G/NP0 caps required for filter accuracy.

---

### Section D: Baseband Gain Stage (Right)

MCP6022 U7B provides voltage gain to bring the baseband signal
to a level suitable for the RP2040's 12-bit ADC (0–3.3V range).

#### Components

| Ref | Value | Package | Connection | Notes |
|---|---|---|---|---|
| C30 | 100nF, 16V, X7R | 0402 | Sallen-Key output to gain stage input | AC coupling (removes DC offset) |
| R10 | 10kΩ, 1% | 0402 | +3V3 to bias junction | Bias divider top |
| R11 | 10kΩ, 1% | 0402 | Bias junction to GND | Bias divider bottom |
| C32 | 10µF, 10V, X5R | 0805 | Bias junction to GND | Bias decoupling (AC ground) |
| R12 | 10kΩ, 1% | 0402 | Non-inverting amp Rg (IN- to GND) | Gain-setting ground resistor |
| R13 | 100kΩ, 1% | 0402 | Feedback (VOUT to IN-) | Gain = 1 + Rf/Rg = 11 (20.8 dB) |
| C31 | 100nF, 16V, X7R | 0402 | MCP6022 VDD (pin 8) to GND | Supply bypass |

**Op-amp: MCP6022 U7B** (second half, pins 5-7)

| MCP6022 Pin | Name | Connect To |
|---|---|---|
| 7 | VOUT_B | Output → R13 feedback, → RX_BASEBAND port |
| 6 | VIN-_B | R12 to GND, R13 from VOUT_B |
| 5 | VIN+_B | C30 input, R10/R11 bias junction |
| 8 | VDD | `+3V3` (shared with U7A, one bypass cap C31) |
| 4 | VSS | `GND` (shared with U7A) |

```
                          R10 (10k)
                   +3V3 ──/\/\/──┬── bias (1.65V)
                                 │
                              R11 (10k)    C32 (10µF)
                                 │            │
                                GND          GND

RX_FILT ── C30 (100nF) ──┬──→ IN+ (pin 5)
                          │
                       bias (1.65V)
                                              VOUT (pin 7) ──→ RX_BASEBAND (port)
                                                │
                                             R13 (100k)
                                                │
                                            IN- (pin 6)
                                                │
                                             R12 (10k)
                                                │
                                               GND
```

#### Note (Place > Note, next to gain stage):

> Non-inverting amplifier, gain = 1 + 100k/10k = 11 (20.8 dB).
> R10/R11 bias the input to 1.65V (mid-supply) for single-supply
> operation. C32 (10µF) decouples the bias point at AC so it acts
> as a solid virtual ground for the signal. C30 AC-couples the
> Sallen-Key output to remove any DC offset from the filter.
> Output goes to RP2040 ADC (GP27/ADC1). Full-scale ADC input is
> 0–3.3V; with 1.65V bias, the signal can swing ±1.65V before
> clipping. Gain of 11 may need adjustment based on actual signal
> levels — change R13 to tune. MCP6022 GBW = 10 MHz, well above
> the ~3 kHz signal band.

---

### Sheet 4 Schematic Layout Suggestion

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│  [Text Frame: RX Chain Description]                                                │
│                                                                                    │
│  RX_IN ──[2m BPF]──C53──[PSA4]──C54──┐                                            │
│  (port)  L9 C50           │ Vd       │                                            │
│          L10 C51         L12         │   ┌──[ADE-1+]──┐                           │
│          L11 C52       +5V via       └──→│RF         IF│──┬─R19(51Ω)─GND          │
│                       C55/C56            │            │   │                       │
│                                          │           IF │──C60──[Sallen-Key]──┐  │
│             CLK1──C24──[LO LPF]─────────→│LO          │                       │  │
│             (port)    C57 L13 C58 L14 C59│GND GND GND │                       │  │
│                                          └────────────┘                       │  │
│                                                                               ↓  │
│                                                            [Gain Stage] → RX_BB  │
│                                                                               (port)│
│  [Notes throughout]                                                                │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Sheet 4 Ports Checklist

- [ ] `CLK1_OUT` — input, 145.9 MHz LO from Clock Gen sheet (drives LO LPF → ADE-1+)
- [ ] `RX_IN` — input, from Connectors sheet (RX SMA)
- [ ] `RX_BASEBAND` — output, to Digital Control (Pico ADC)
- [ ] `+3V3` — power port (MCP6022 supply)
- [ ] `+5V` — power port (PSA4-5043+ LNA Vd via L12 choke)
- [ ] `GND` — power port (global)

---
---

## Sheet 5: Digital Control

This sheet holds the RP2040 (Pico module), USB connector, and GPIO
assignments.

### Text Frame (Place > Text Frame, top of sheet):

> DIGITAL CONTROL — Raspberry Pi Pico module (RP2040-based). Handles
> BPSK/DBPSK encoding for TX, AFSK demodulation for RX, Si5351A
> configuration via I2C, and command processing. Using Pico module
> for prototype — all RP2040 support circuitry (flash, regulator,
> crystal) is on-module. Bare RP2040 redesign deferred to v2 flight
> board after RF chain validation.

---

### Section A: Pico Module (Center of Sheet)

Place a 2×20 pin header symbol (2.54mm pitch) or a Pico module
symbol if available in Manufacturer Part Search. Label each pin
with its net name.

#### Pico Module Pin Connections

| Pico Pin | Net Name | Goes To | Connection |
|---|---|---|---|
| GP3 (pin 5) | `COMMS_IRQ` | CSKB H1.16 | COMMS_IRQ net label (output, active-low, push-pull, normally high — asserts when RX packet ready or TX status change; IHU ISR triggers SPI read) |
| GP4 (pin 6) | `SPI_COMMS_MISO` | CSKB H1.22 | SPI0 RX/MISO (alt-function) — comms → IHU (slave TX) |
| GP5 (pin 7) | `SPI_COMMS_CS_N` | CSKB H1.24 | SPI0 CSn (alt-function) — slave select from IHU |
| GP6 (pin 9) | `SPI_COMMS_SCK` | CSKB H1.21 | SPI0 SCK (alt-function) — clock from IHU |
| GP7 (pin 10) | `SPI_COMMS_MOSI` | CSKB H1.23 | SPI0 TX/MOSI (alt-function) — IHU → comms |
| GP16 (pin 21) | `BPSK_DATA` | XOR gate pin 2 | BPSK_DATA net label (right side for layout) |
| GP20 (pin 26) | `I2C_SDA` | Si5351A SDA | I2C_SDA net label — I2C0 SDA (alt-function pin) |
| GP21 (pin 27) | `I2C_SCL` | Si5351A SCL | I2C_SCL net label — I2C0 SCL (alt-function pin) |
| GP27/ADC1 (pin 32) | `RX_BASEBAND` | MCP6022 output | RX_BASEBAND net label — uses ADC channel 1 |
| 3V3 (pin 36) | `+3V3` | Power (from EPS) | +3V3 power port |
| GND (pins 3,8,13,18,23,28,33,38) | `GND` | Ground | GND power port |
| VSYS (pin 39) | `VSYS` | System power input | See Power section |
| VBUS (pin 40) | `VBUS_USB` | From USB connector VBUS | USB power |

#### Note (Place > Note, next to Pico module):

> Pico module power: The Pico has an internal regulator that produces
> 3.3V from VSYS (1.8–5.5V input). For stack operation, feed +5V
> from the CSKB bus to VSYS through a Schottky diode (prevents
> back-feeding when USB is also connected). The Pico's internal 3V3
> regulator is then active and supplies the on-module 3V3. The +3V3
> power port on this board is the EPS-supplied rail — connect Pico
> pin 36 (3V3 OUT) to +3V3 only if you want the Pico to be powered
> from the bus. Do NOT connect both VSYS and 3V3(OUT) to the bus
> simultaneously without understanding the power path.

---

### Section B: USB Connector (Left of Pico)

For prototype, the Pico module's own Micro-USB connector is the
primary programming and debug interface. A separate USB connector
on the comms board is **optional** — skip for prototype and use
the Pico's built-in USB.

If adding a separate connector:

| Ref | Part | Package | Connection |
|---|---|---|---|
| J1 | USB Micro-B or USB-C | SMD | D+ to Pico USB_DP, D- to USB_DN |

#### Note (Place > Note):

> USB connector is optional for prototype. The Pico module has its
> own Micro-USB. For the flight board (v2 with bare RP2040), a USB-C
> connector would be placed here with 27Ω termination resistors on
> D+/D-.

---

### Section C: Debug/Programming Header (Optional, Bottom-Left)

| Ref | Part | Pins | Connection |
|---|---|---|---|
| J2 | 1×4 pin header, 2.54mm | 4 | SWCLK, SWDIO, GND, 3V3 |

Connect to Pico SWD pins: SWCLK (Pico debug pin), SWDIO (Pico debug
pin), GND, 3V3. Useful for debugging with a probe but not required if
using USB serial for bring-up.

---

### Section D: Status LEDs (Optional, Bottom-Right)

| Ref | Color | Connection | Indicates |
|---|---|---|---|
| D1 | Green | GPIO → R14 (330Ω) → LED → GND | TX active |
| D2 | Yellow | GPIO → R15 (330Ω) → LED → GND | RX active |
| D3 | Green | +3V3 → R16 (1kΩ) → LED → GND | Board power |

Use whatever free GPIOs are available. Mark as DNP for flight.

---

### Section E: Spare GPIO Header (Recommended)

| Ref | Part | Pins | Connection |
|---|---|---|---|
| J3 | 1×6 pin header, 2.54mm | 6 | Unused GPIOs — free pins available: GP2, GP8, GP9, GP10, GP11, GP12, GP13, GP14, GP15, GP17, GP18, GP19, GP22 (pick any 6) |

#### Note (Place > Note, next to spare header):

> Spare GPIO header: invaluable during integration and testing.
> Can be used for UART debug output, logic analyzer probing, or
> connecting additional sensors during orbit. Label pins with GPIO
> numbers.

---

### Sheet 5 Schematic Layout Suggestion

```
┌──────────────────────────────────────────────────────────────────┐
│  [Text Frame: Digital Control Description]                       │
│                                                                  │
│  [USB Connector]      [Pico Module / 2x20 Header]                │
│   (optional)           GP3  ── COMMS_IRQ (port → H1.16)          │
│   D+  D-  VBUS GND     GP4  ── SPI_COMMS_MISO  (port → H1.22)    │
│                        GP5  ── SPI_COMMS_CS_N  (port → H1.24)    │
│                        GP6  ── SPI_COMMS_SCK   (port → H1.21)    │
│                        GP7  ── SPI_COMMS_MOSI  (port → H1.23)    │
│                        GP16 ── BPSK_DATA (port)                  │
│                        GP20 ── I2C_SDA (port)                    │
│                        GP21 ── I2C_SCL (port)                    │
│                        GP27 ── RX_BASEBAND (port, ADC1)          │
│                        3V3  ── +3V3 (power port)                 │
│                        VSYS ── from +5V via Schottky             │
│                        GND  ── GND (power port)                  │
│                                                                  │
│  [Debug Header]        [Spare GPIO Header]                       │
│   SWCLK SWDIO GND      GP2 GP8 GP9 GP10 GP11 GP12 GP13 GP14 GP15 │
│                        GP17 GP18 GP19 GP22                        │
│                                                                  │
│  [Status LEDs]                                                   │
│   D1(TX) D2(RX) D3(PWR)                                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Sheet 5 Ports Checklist

- [ ] `I2C_SDA` — bidirectional, to GP20 (pin 26, I2C0 SDA alt-function)
- [ ] `I2C_SCL` — bidirectional, to GP21 (pin 27, I2C0 SCL alt-function)
- [ ] `BPSK_DATA` — output, from GP16 (pin 21)
- [ ] `COMMS_IRQ` — output, from GP3 (to Connectors sheet → H1.16)
- [ ] `SPI_COMMS_MISO` — output, from GP4 (pin 6, SPI0 RX alt-function) (to Connectors sheet → H1.22)
- [ ] `SPI_COMMS_CS_N` — input, to GP5 (pin 7, SPI0 CSn alt-function) (from Connectors sheet → H1.24)
- [ ] `SPI_COMMS_SCK` — input, to GP6 (pin 9, SPI0 SCK alt-function) (from Connectors sheet → H1.21)
- [ ] `SPI_COMMS_MOSI` — input, to GP7 (pin 10, SPI0 TX alt-function) (from Connectors sheet → H1.23)
- [ ] `RX_BASEBAND` — input, to GP27/ADC1
- [ ] `+3V3` — power port (Pico 3V3)
- [ ] `GND` — power port (global)

#### Note (Place > Note, next to GP3 / COMMS_IRQ label):

> COMMS_IRQ is a data-ready interrupt from the comms RP2040 to the
> internal housekeeping unit, modelled after the AX5043 IRQ pattern in AMSAT
> RT-IHU. Push-pull output, active-low, normally held high. Comms
> firmware asserts the line when (a) an RX packet has been fully
> received and is available in the slave FIFO, or (b) a TX-complete
> or TX-underrun status needs IHU attention. The IHU uses a GPIO-EXTI
> ISR to trigger a SPI read transaction; comms de-asserts the line
> after the IHU CS_N drops (or after a firmware-side clear). Do NOT
> add a pull-up on this board — the IHU side (R11 on IHU Sheet 4) has
> a 10k pull-up that keeps the line defined while comms is in reset.

---
---

## Sheet 6: Power

This sheet handles power distribution across the comms board. **All
regulated power (+3V3, +5V) comes from the EPS board via the CSKB
stack connector** — there are no on-board voltage regulators on the
comms board (prototype configuration).

### Text Frame (Place > Text Frame, top of sheet):

> POWER DISTRIBUTION — The comms board receives +3V3 and +5V from the
> EPS via the CSKB stack connectors. No on-board voltage regulation.
> This sheet provides input protection, bulk bypass capacitors, and
> distributes power to all subsystems. Power budget: ~150 mA on +3V3
> (RP2040 + Si5351A + logic), ~140 mA on +5V (PSA4-5043+ LNA + ADL5602
> MMIC + tripler bias). Total: <300 mA — well within EPS TPS62933F
> capacity (3A per rail).

---

### Section A: Input Protection and Filtering (Left of Sheet)

Power enters the board through the CSKB H2 connector (defined on the
Connectors sheet). On this sheet, we receive the power port symbols
and add protection and filtering.

#### Components

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| D4 | Schottky (SS14 or BAT54S) | SMA or SOT-23 | +5V line, anode to bus, cathode to internal +5V | Reverse polarity protection |
| C33 | 47µF, ≥10V (Panasonic EEE-FK1V470P wet Al-electrolytic **or** EEH-ZA1V470P polymer) | SMD can (~6.3mm) | +5V (after protection) to GND | Input bulk capacitor |
| C34 | 100nF, 16V, X7R | 0402 | +5V to GND | HF bypass at entry |
| C35 | 47µF, ≥10V (Panasonic EEE-FK1V470P wet Al-electrolytic **or** EEH-ZA1V470P polymer) | SMD can (~6.3mm) | +3V3 to GND | Input bulk capacitor |
| C36 | 100nF, 16V, X7R | 0402 | +3V3 to GND | HF bypass at entry |

```
+5V (from CSKB H2.25/26) ── D4 (Schottky) ──┬── +5V rail (internal)
                                       │
                                   C33(47µF) C34(100nF)
                                       │       │
                                      GND     GND

+3V3 (from CSKB H2.27/28) ───────────┬── +3V3 rail
                                       │
                                   C35(47µF) C36(100nF)
                                       │       │
                                      GND     GND
```

#### Note (Place > Note, next to input protection):

> D4 provides reverse polarity protection on the +5V rail. Adds
> ~0.3V forward drop — the ADL5602 and PSA4-5043+ LNA can tolerate
> this (ADL5602 specified for supply down to 4.5V; PSA4 Vd range is
> +3V to +5V, so 4.7V is within window). At 4.7V the PSA4 Id is
> slightly higher than at 5.0V — check current budget headroom.
> The +3V3 rail does NOT have a series diode because the RP2040 and
> Si5351A are sensitive to voltage drop — 3.0V may be too low for
> reliable operation. If reverse polarity protection is needed on
> +3V3, use a P-MOSFET instead of a Schottky (near-zero drop when
> conducting). Bulk caps dampen transients from the CSKB connector
> traces. The EPS has its own bulk caps at the connector — these
> are the receiving-end complements.

---

### Section B: Per-Subsystem Bypass (Center of Sheet)

Each IC has local bypass caps on its own sheet (Clock Gen, TX, RX,
Digital Control). This section provides additional board-level bulk
bypass at the power distribution point.

#### Components

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| C37 | 10µF, 10V, X5R | 0805 | +3V3 to GND | Board-level bulk, 3.3V |
| C38 | 100nF, 16V, X7R | 0402 | +3V3 to GND | Board-level HF, 3.3V |
| C39 | 10µF, 10V, X5R | 0805 | +5V to GND | Board-level bulk, 5V |
| C40 | 100nF, 16V, X7R | 0402 | +5V to GND | Board-level HF, 5V |

#### Note (Place > Note, next to bulk bypass):

> Board-level bulk bypass at the power distribution star point.
> Local bypass at each consumer IC is the responsibility of that
> IC's sheet (C1/C2/C3 on Clock Gen, C8 on TX, C21/C22 on RX, etc.).
> These caps cover trace inductance between the CSKB connector
> and the far side of the board. Place C37/C39 near the center of
> their respective power distribution traces.

---

### Section C: Pico Module Power Feed (Right of Sheet)

The Pico module needs power on its VSYS pin. Feed it from the +5V
bus through a Schottky diode so the Pico's internal regulator handles
its own 3.3V generation. The diode prevents back-feeding from USB
when the Pico is also connected to a computer.

#### Components

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| D5 | Schottky (BAT54 or SS14) | SOT-23 or SMA | +5V to Pico VSYS | Isolation diode |

```
+5V rail ── D5 (Schottky) ──→ VSYS (to Pico pin 39)
```

#### Note (Place > Note, next to D5):

> D5 isolates the stack +5V from the Pico's USB VBUS. When USB is
> connected, the Pico's internal diode on VBUS feeds VSYS. When
> running from the stack (no USB), D5 feeds VSYS from +5V. The
> Pico's internal 3.3V buck-boost regulator produces 3V3 from VSYS.
> Drop across D5 (~0.3V) gives VSYS ≈ 4.7V — well within the Pico's
> VSYS range (1.8–5.5V).

---

### Section D: Power Indicator LEDs (Optional, Bottom)

| Ref | Color | Connection | Indicates |
|---|---|---|---|
| D6 | Green | +3V3 → R17 (1kΩ) → LED → GND | 3.3V rail active |
| D7 | Green | +5V → R18 (1kΩ) → LED → GND | 5.0V rail active |

Mark as DNP (Do Not Populate) for flight — LEDs waste power in orbit.

#### Note (Place > Note, next to LEDs):

> Power indicator LEDs for bench debugging. I = (3.3-2.0)/1k = 1.3mA
> (dim but visible). Mark R17/R18 as DNP-optional in BOM for flight.

---

### Sheet 6 Schematic Layout Suggestion

```
┌──────────────────────────────────────────────────────────────────┐
│  [Text Frame: Power Distribution Description]                    │
│                                                                  │
│  +5V (power port) ── D4 (Schottky) ──┬── +5V internal           │
│                                      │                          │
│                                  C33(47µ) C34(100n)             │
│                                      │       │                  │
│                                     GND     GND                 │
│                                                                  │
│  +3V3 (power port) ──────────────────┬── +3V3                    │
│                                      │                          │
│                                  C35(47µ) C36(100n)             │
│                                      │       │                  │
│                                     GND     GND                 │
│                                                                  │
│  Board-level bulk: C37/C38 on +3V3, C39/C40 on +5V              │
│                                                                  │
│  +5V ── D5 ──→ VSYS (to Pico)                                   │
│                                                                  │
│  [Power LEDs]  D6(3V3) D7(5V)  [R17, R18 = 1k]                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Sheet 6 Ports Checklist

- [ ] `+3V3` — power port (global, from EPS via CSKB H2.27/28)
- [ ] `+5V` — power port (global, from EPS via CSKB H2.25/26)
- [ ] `GND` — power port (global)
- [ ] `VSYS` — net label, to Pico module VSYS pin

### Important Note on AMS1117-3.3 and MCP1701T-5002I

The v0.1 prototype schematic includes U5 (MCP1701T-5002I/MB, 5V LDO)
and U6 (AMS1117-3.3, 3.3V LDO) on the Power sheet. **These are no
longer needed** since power comes from the EPS via the bus connector.

**Action:** Remove U5, U6, and their associated input/output caps from
the Power sheet. If you want to keep them as a fallback for standalone
bench testing (without the EPS board), move them to a "standalone power"
section with a clear note that they are DNP when operating in the stack.

If keeping the AMS1117-3.3 for standalone operation: it **requires** a
≥10µF output capacitor for stability (the current v0.1 schematic is
missing this cap — add it). The MCP1701T-5002I/MB needs minimum 5.35V
input (Vout + dropout = 5.0 + 0.35 = 5.35V), so it needs a bench supply
of at least 5.5V.

---
---

## Sheet 7: Connectors

This sheet holds the CSKB H1 + H2 stack connectors, RF SMA connectors,
and any test point headers. It is the physical interface between the
comms board and the rest of the CubeSat stack.

### Text Frame (Place > Text Frame, top of sheet):

> CONNECTORS — CSKB H1 + H2 stack connectors for inter-board power
> and signal distribution, SMA connectors for TX and RX antenna
> ports, and test points for bench validation. All power (+3V3, +5V)
> arrives on H2; I2C, SPI, and COMMS_IRQ route through H1. The comms
> board is a power CONSUMER — it receives regulated rails from the
> EPS.

---

### Section A: CSKB H1 + H2 Stack Connectors (Center of Sheet)

#### Connector Selection

**Part: 2× Samtec ESQ-126-39-G-D** — 2×26 (52-pin) each, 0.1″
(2.54 mm) pitch, stackthrough through-hole vertical socket. One
populates the H1 (signals) position, one populates the H2 (power)
position, for a total of 104 pins per Pumpkin's CSKB layout. Same
stackthrough variant as the IHU board; EPS uses the non-stackthrough
ESQ-126-37-G-D because it is the stack endpoint.

The mating adjacent board's CSKB sockets are the same ESQ-126-39-G-D
on IHU and payload, and ESQ-126-37-G-D on EPS. Default stacking height
is 15 mm.

Search Manufacturer Part Search for "ESQ-126-39-G-D" or place a
generic 2×26 pin socket symbol (0.1″ (2.54 mm) pitch) and assign the
Samtec MPN in the component properties. **Mechanical note:** exact
X/Y position of the H1 and H2 footprints on the PCB must match
Pumpkin's motherboard layout (see [`DS_CSK_MB_710-00484-E.pdf`](../../../system/interfaces/DS_CSK_MB_710-00484-E.pdf) page 5,
"Simplified Mechanical Layout") before layout.

#### Pin Assignment (Pumpkin CSKB H1/H2)

> **Canonical reference:** [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md) is the
> authoritative pin map for the stack. The table below is a
> board-local view and must match that file. Update the canonical
> file first if anything here needs to change.

Pin numbers follow the Pumpkin CubeSat Kit Motherboard H1/H2 CSKB
convention (DS_CSK_MB_710-00484-E.pdf, doc Rev. A, March 2012,
pp. 13–16). The comms board uses only the subset it needs; all other
H1/H2 pins are left unconnected on this board but must remain in the
bus routing for other subsystems.

| Pin | Pumpkin name | Net | Direction (Comms) | Function |
|---|---|---|---|---|
| H1.16 | `IO.8` | `COMMS_IRQ` | Out | Data-ready interrupt to IHU (active-low, push-pull) |
| H1.21 | `IO.3` (SCK0) | `SPI_COMMS_SCK` | In | SPI clock from IHU |
| H1.22 | `IO.2` (SDI0) | `SPI_COMMS_MISO` | Out | SPI data, comms → IHU |
| H1.23 | `IO.1` (SDO0) | `SPI_COMMS_MOSI` | In | SPI data, IHU → comms |
| H1.24 | `IO.0` (-CS_SD) | `SPI_COMMS_CS_N` | In | SPI chip select from IHU |
| H1.41 | `SDA_SYS` | `I2C_SDA` | Bidirectional | Shared housekeeping I2C data |
| H1.43 | `SCL_SYS` | `I2C_SCL` | Bidirectional | Shared housekeeping I2C clock |
| H1.49 | `USER2` | `EPS_ALERT_N` | (not used on comms) | EPS LTC4162 alert — consumed by IHU only |
| H2.25 | `+5V_SYS` | `+5V` | Power In | 5 V stack rail (from EPS) |
| H2.26 | `+5V_SYS` | `+5V` | Power In | 5 V (parallel for current sharing) |
| H2.27 | `VCC_SYS` | `+3V3` | Power In | 3.3 V stack rail (from EPS) |
| H2.28 | `VCC_SYS` | `+3V3` | Power In | 3.3 V (parallel for current sharing) |
| H2.29 | `DGND` | `GND` | Power | Digital ground return |
| H2.30 | `DGND` | `GND` | Power | Digital ground return |
| H2.31 | `AGND` | `GND` | Power | Analog ground (tied to GND single plane) |
| H2.32 | `DGND` | `GND` | Power | Digital ground return (third DGND pin) |
| H2.45 | `VBATT` | `VBAT` | Power In (monitor only) | Battery bus for ADC telemetry |
| H2.46 | `VBATT` | `VBAT` | Power In (monitor only) | Battery bus (parallel) |

All other H1/H2 pins are reserved or left unconnected on the comms
board.

#### Note (Place > Note, next to CSKB connectors):

> CSKB stack connectors: 2× Samtec ESQ-126-39-G-D (2×26, 0.1″
> (2.54 mm), stackthrough headers, one each for H1 and H2). Pin
> assignment locked to the Pumpkin CSKB H1/H2 convention — all
> boards in the stack (EPS, IHU, comms, payload) use the
> same H1/H2 pin numbers for the same signal classes. The comms
> board is a power CONSUMER on all power pins and a SPI SLAVE to
> the IHU. COMMS_IRQ (H1.16) is driven by the comms RP2040 as a
> data-ready interrupt to the IHU. I2C is shared between EPS
> LTC4162 (0x68) and comms Si5351A (0x60) — no address conflict.
> See `system/interfaces/cskb_pinmap.md` for the full canonical
> pin map.

#### Bulk Bypass at Stack Connector

Place bypass caps physically close to the CSKB H2 connector pads:

| Ref | Value | Package | Connection | Purpose |
|---|---|---|---|---|
| C41 | 10µF, 10V, X5R | 0805 | +3V3 to GND at connector | Receiving-end bulk, 3.3V |
| C42 | 100nF, 16V, X7R | 0402 | +3V3 to GND at connector | Receiving-end HF, 3.3V |
| C43 | 10µF, 10V, X5R | 0805 | +5V to GND at connector | Receiving-end bulk, 5V |
| C44 | 100nF, 16V, X7R | 0402 | +5V to GND at connector | Receiving-end HF, 5V |

#### Note (Place > Note, next to bypass caps):

> Connector-side bypass caps are the receiving complement to the EPS
> board's connector-side caps (C60–C63 on EPS Sheet 3). Together they
> form a low-impedance distributed bypass across the stack connector.
> Place these caps as close to the connector pins as possible — trace
> inductance between connector and cap defeats the purpose.

---

### Section B: RF Connectors (Top-Right)

#### Components

| Ref | Part | Connection | Purpose |
|---|---|---|---|
| J4 | SMA edge-launch, female | `TX_OUT` net | 437 MHz TX antenna port |
| J5 | SMA edge-launch, female | `RX_IN` net | 145.9 MHz RX antenna port |

Search Manufacturer Part Search for "SMA edge launch" or "SMA PCB
connector". For prototype, through-hole SMA connectors work fine.
For flight, use edge-launch SMAs with ground tabs soldered to the
ground plane.

```
TX_OUT (port) ──→ J4 (SMA) ──→ to TX antenna / cable
RX_IN (port) ──→ J5 (SMA) ──→ from RX antenna / cable
```

#### Note (Place > Note, next to SMA connectors):

> Separate TX and RX SMA connectors — no diplexer for prototype.
> For flight, a diplexer can be added between a single antenna and
> the two SMA ports, or external to the board. SMA center pin
> impedance is 50Ω — match traces accordingly during PCB layout.
> Keep SMA-to-first-component traces as short as possible, with
> continuous ground plane underneath. Controlled-impedance traces
> (50Ω microstrip or CPWG) required for RF paths.

---

### Section C: Test Points (Bottom of Sheet)

#### Test Point List

| Ref | Net | Purpose | Measurement |
|---|---|---|---|
| TP1 | `+3V3` | 3.3V rail | Rail voltage, ripple (scope) |
| TP2 | `+5V` | 5.0V rail | Rail voltage, ripple (scope) |
| TP3 | `CLK0_OUT` | Si5351A CLK0 | 145.67 MHz carrier (spectrum analyzer) |
| TP4 | `BPSK_145` | XOR output | Modulated 145.67 MHz (scope/SA) |
| TP5 | `TRIPLER_OUT` | Tripler output | Unfiltered harmonics (SA) |
| TP6 | `TX_437` | Post-BPF | Filtered 437 MHz (SA) |
| TP7 | `RX_IF` | ADE-1+ IF output (post-termination, pre-DC-block) | Baseband signal (scope) |
| TP8 | `RX_BASEBAND` | MCP6022 output | Amplified baseband (scope) |
| TP9 | `GND` | Ground reference | Scope ground clip point |

Place TP9 (GND) as a large pad or loop — always need a convenient
ground reference for scope probing. Consider placing two GND test
points on opposite sides of the board.

#### How to Place Test Points in Altium

1. Place > Part > search "Test Point" in Manufacturer Part Search
2. Or: create a generic 1-pin schematic symbol called "TP"
3. Assign a footprint: round pad (1–2mm diameter) or Keystone 5019 loop
4. Label each test point with its net name in the Comment field
5. On the PCB, test points appear as pads — probe with scope/DMM

#### Note (Place > Note, next to test points):

> Test points are critical for bring-up and debugging. TP3–TP6
> trace the TX signal through the chain — essential for validating
> each stage independently. TP7–TP8 trace the RX chain. Use short
> probe leads on RF test points to minimize added inductance. TP9
> (GND) should be a loop-style test point for easy scope ground
> clip attachment. For flight boards, reduce to TP1/TP2 (power) +
> TP9 (GND) minimum.

---

### Section D: Test/Debug Header (Optional, Bottom-Right)

| Ref | Part | Pins | Connection |
|---|---|---|---|
| J6 | 1×6 pin header, 2.54mm | 6 | BPSK_DATA, I2C_SCL, I2C_SDA, CLK0_OUT, RX_BASEBAND, GND |

This header brings key signals to a convenient probe point for logic
analyzer or oscilloscope connection during integration testing.

---

### Sheet 7 Schematic Layout Suggestion

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Text Frame: Connectors Description]                                │
│                                                                      │
│  ┌─────────────────────────────────┐     ┌──────────┐                │
│  │ J1 (H1+H2): 2× ESQ-126-39-G-D   │     │ J4: SMA  │                │
│  │ CSKB (2×26 stackthrough, 0.1″)  │     │ TX OUT   │ ← TX_OUT port │
│  │                                 │     └──────────┘                │
│  │ H1.16  COMMS_IRQ  ←── GP3       │                                 │
│  │ H1.21  SPI_SCK    ──→ GP18      │     ┌──────────┐                │
│  │ H1.22  SPI_MISO   ←── GP16      │     │ J5: SMA  │                │
│  │ H1.23  SPI_MOSI   ──→ GP19      │     │ RX IN    │ ← RX_IN port  │
│  │ H1.24  SPI_CS_N   ──→ GP17      │     └──────────┘                │
│  │ H1.41  SDA_SYS    ──→ I2C_SDA   │                                 │
│  │ H1.43  SCL_SYS    ──→ I2C_SCL   │                                 │
│  │ H1.49  EPS_ALERT_N (not used)   │                                 │
│  │ H2.25/26  +5V   ──→ C43,C44     │                                 │
│  │ H2.27/28  +3V3  ──→ C41,C42     │                                 │
│  │ H2.29/30  DGND                  │                                 │
│  │ H2.31     AGND                  │                                 │
│  │ H2.32     DGND                  │                                 │
│  │ H2.45/46  VBAT (monitor only)   │                                 │
│  │ (other H1/H2 pins reserved)     │                                 │
│  └─────────────────────────────────┘                                 │
│  [H1 and H2 populated; 15 mm stacking per cskb_pinmap.md]            │
│                                                                      │
│  ┌──────────────────────────────────────────┐    ┌────────────────┐  │
│  │ Test Points                               │    │ Debug Header  │  │
│  │ TP1(3V3) TP2(5V) TP3(CLK0) TP4(BPSK145) │    │ J6 (1x6)     │  │
│  │ TP5(TRIP) TP6(437) TP7(IF) TP8(BB)       │    │ key signals  │  │
│  │ TP9(GND) TP10(GND)                       │    └────────────────┘  │
│  └──────────────────────────────────────────┘                        │
│                                                                      │
│  [Notes throughout as specified]                                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Sheet 7 Ports Checklist

- [ ] `TX_OUT` — input, from TX Chain (to TX SMA J4)
- [ ] `RX_IN` — output, from RX SMA J5 (to RX Chain)
- [ ] `I2C_SCL` — bidirectional, to CSKB bus (H1.43)
- [ ] `I2C_SDA` — bidirectional, to CSKB bus (H1.41)
- [ ] `COMMS_IRQ` — output, to CSKB bus (H1.16) from Digital Control GP3
- [ ] `SPI_COMMS_SCK` — input, from CSKB bus (H1.21) to Digital Control GP18
- [ ] `SPI_COMMS_MISO` — output, to CSKB bus (H1.22) from Digital Control GP16
- [ ] `SPI_COMMS_MOSI` — input, from CSKB bus (H1.23) to Digital Control GP19
- [ ] `SPI_COMMS_CS_N` — input, from CSKB bus (H1.24) to Digital Control GP17
- [ ] `EPS_ALERT_N` — input (reserved), from CSKB bus (H1.49) — not wired in v0.1
- [ ] `+3V3` — power port, from CSKB (H2.27, H2.28)
- [ ] `+5V` — power port, from CSKB (H2.25, H2.26)
- [ ] `GND` — power port, from CSKB (H2.29, H2.30, H2.31 AGND, H2.32)
- [ ] `VBAT` — power port, from CSKB (H2.45, H2.46) — monitor only

---
---

## After All Seven Sheets Are Done

### 1. Annotate

Tools > Annotate Schematic Quietly (or Annotate Schematic for manual
control). Assign unique designators across all sheets: R1, R2, ... C1,
C2, ... U1, U2, ... etc.

### 2. Compile and Validate

Project > Validate PCB Project. Check the Messages panel for:
- **Net mismatch** — net labels with the same name on different sheets
  must match exactly (case-sensitive)
- **Unconnected pins** — add no-connect X markers on any intentionally
  unconnected pins (e.g., Si5351A CLK2, unused Pico GPIOs)
- **Duplicate designators** — fix before proceeding (annotate should
  handle this)
- **Power port direction warnings** — usually benign but review to ensure
  power ports are connected, not floating

### 3. Fill in Title Blocks

On each sheet, double-click the title block and fill in:

| Field | Sheet 1 | Sheet 2 | Sheet 3 | Sheet 4 |
|---|---|---|---|---|
| Title | Comms — Overview | Comms — Clock Gen | Comms — TX Chain | Comms — RX Chain |
| Revision | 0.2 | 0.2 | 0.2 | 0.2 |
| Drawn By | Nick Grabbs / K15Y NG | Nick Grabbs / K15Y NG | Nick Grabbs / K15Y NG | Nick Grabbs / K15Y NG |
| Date | (today) | (today) | (today) | (today) |

| Field | Sheet 5 | Sheet 6 | Sheet 7 |
|---|---|---|---|
| Title | Comms — Digital Control | Comms — Power | Comms — Connectors |
| Revision | 0.2 | 0.2 | 0.2 |
| Drawn By | Nick Grabbs / K15Y NG | Nick Grabbs / K15Y NG | Nick Grabbs / K15Y NG |
| Date | (today) | (today) | (today) |

### 4. Export PDF

File > Smart PDF (or File > Print > PDF).
Save to `hardware/comms/releases/Comms_schematic_v0.2.pdf` for review.

---

## Complete BOM Summary

### Sheet 2: Clock Gen

| Ref | Value | Description | Qty |
|---|---|---|---|
| U4 | Si5351A-B-GT | Clock generator, MSOP-10 | 1 |
| Y1 | 25 MHz, 10pF load | Crystal, HC-49/US or SMD | 1 |
| C1 | 100nF, 16V, X7R | VDD bypass | 1 |
| C2 | 10µF, 10V, X5R | VDD bulk bypass | 1 |
| C3 | 100nF, 16V, X7R | VDDO bypass | 1 |
| C4, C5 | 10pF, 50V, C0G/NP0 | Crystal load caps | 2 |
| C6, C7 | 100nF, 16V, X7R | Clock output DC blocks | 2 |
| R1, R2 | 4.7kΩ, 1% | I2C pull-ups | 2 |
| R3, R4 | **0Ω**, 0402 | Clock output series resistors — populated 0Ω per Rev 1.5 bench validation (footprint kept for swap to 33Ω if ringing/EMI mitigation needed during bring-up) | 2 |

### Sheet 3: TX Chain

| Ref | Value | Description | Qty |
|---|---|---|---|
| U1 | SN74LVC1G86DBVR | XOR gate, SOT-23-5 | 1 |
| Q1 | BFR92A (or 2N3904 proto) | Tripler transistor, SOT-23 | 1 |
| U2 | ADL5602ARKZ-R7 | MMIC gain block, SOT-89 | 1 |
| C8 | 100nF, 16V, X7R | XOR VCC bypass | 1 |
| C9 | 10pF, 50V, C0G | Data edge softening | 1 |
| C10, C11 | 100nF, 16V, X7R | Tripler DC blocks (in/out) | 2 |
| C12 | 100nF, 16V, X7R | Tripler supply bypass | 1 |
| C13, C16 | 10pF, 50V, C0G/NP0 | Pre-MMIC BPF series caps | 2 |
| C14, C15 | 6.8pF, 50V, C0G/NP0 | Pre-MMIC BPF shunt caps | 2 |
| C17, C18 | 100nF, 16V, X7R | MMIC DC blocks (in/out) | 2 |
| C19 | 100nF, 16V, X7R | MMIC supply bypass | 1 |
| C20 | 10µF, 10V, X5R | MMIC supply bulk | 1 |
| C45, C48 | 10pF, 50V, C0G/NP0 | Output BPF series caps | 2 |
| C46, C47 | 6.8pF, 50V, C0G/NP0 | Output BPF shunt caps | 2 |
| R5 | 100Ω, 1% | Data series resistor | 1 |
| R6 | 47kΩ, 5% | Tripler class-C bias | 1 |
| L1 | 220nH, ±5%, 0805 | Tripler RFC | 1 |
| L2, L3, L4 | 15nH, ±2%, 0402 | Pre-MMIC BPF inductors | 3 |
| L5 | 220nH, ±5%, 0805 | MMIC RFC | 1 |
| L6, L7, L8 | 15nH, ±2%, 0402 | Output BPF inductors | 3 |

### Sheet 4: RX Chain

| Ref | Value | Description | Qty |
|---|---|---|---|
| U3 | ADE-1+ | Mini-Circuits passive diode mixer, CD636 SMT (6-pad) | 1 |
| U10 | PSA4-5043+ | Mini-Circuits VHF/UHF LNA, SOT-89 (~1 dB NF, ~21 dB gain) — JLC C5240848 | 1 |
| U7 | MCP6022-I/SN | Dual op-amp, SOIC-8 (U7A = filter, U7B = gain) | 1 |
| C24 | 100nF, 16V, X7R | CLK1 DC block (before LO LPF) | 1 |
| C28, C29 | 2.2nF, 25V, C0G/NP0 | Sallen-Key filter caps | 2 |
| C30 | 100nF, 16V, X7R | Gain stage AC coupling | 1 |
| C31 | 100nF, 16V, X7R | MCP6022 VDD bypass | 1 |
| C32 | 10µF, 10V, X5R | Bias point decoupling | 1 |
| C49, C52 | 10pF, 50V, C0G/NP0 | 2m BPF series caps | 2 |
| C50, C51 | 10pF, 50V, C0G/NP0 | 2m BPF shunt caps | 2 |
| C53 | 100nF, 16V, X7R | PSA4 input DC block (2m BPF → LNA) | 1 |
| C54 | 100nF, 16V, X7R | PSA4 output DC block (LNA → mixer RF) | 1 |
| C55 | 100nF, 16V, X7R | PSA4 Vd HF bypass | 1 |
| C56 | 10µF, 10V, X5R | PSA4 Vd bulk bypass | 1 |
| C57 | 10pF, 50V, C0G/NP0 | LO LPF input shunt cap | 1 |
| C58 | 33pF, 50V, C0G/NP0 | LO LPF center shunt cap | 1 |
| C59 | 10pF, 50V, C0G/NP0 | LO LPF output shunt cap | 1 |
| C60 | 100nF, 16V, X7R | ADE-1+ IF DC block to Sallen-Key | 1 |
| R8, R9 | 22kΩ, 1% | Sallen-Key filter resistors | 2 |
| R10, R11 | 10kΩ, 1% | Bias voltage divider (1.65V) | 2 |
| R12 | 10kΩ, 1% | Gain stage Rg | 1 |
| R13 | 100kΩ, 1% | Gain stage Rf (gain = 11) | 1 |
| R19 | 51Ω, 1% | ADE-1+ IF port termination to GND | 1 |
| L9, L10, L11 | 82nH, ±2%, 0402 | 2m BPF inductors | 3 |
| L12 | 1µH, wirewound, SRF > 500 MHz | 0805/1008 | PSA4 Vd bias choke | 1 |
| L13, L14 | 68nH, ±2%, 0402 | LO LPF series inductors | 2 |

### Sheet 5: Digital Control

| Ref | Value | Description | Qty |
|---|---|---|---|
| Pico | Raspberry Pi Pico | RP2040 module, 2×20 header | 1 |
| J1 | USB Micro-B (optional) | Programming/debug | 0–1 |
| J2 | 1×4 header | SWD debug (optional) | 0–1 |
| J3 | 1×6 header | Spare GPIOs | 1 |
| D1–D3 | LED, 0603 | Status LEDs (optional) | 0–3 |
| R14–R16 | 330Ω–1kΩ | LED resistors (optional) | 0–3 |

### Sheet 6: Power

| Ref | Value | Description | Qty |
|---|---|---|---|
| D4 | SS14 or BAT54S | +5V reverse polarity Schottky | 1 |
| D5 | BAT54 or SS14 | Pico VSYS isolation diode | 1 |
| C33 | 47µF, ≥10V — Panasonic EEE-FK1V470P (wet Al-electrolytic, 35V) **or** EEH-ZA1V470P (polymer) | +5V input bulk | 1 |
| C34 | 100nF, 16V, X7R | +5V input HF bypass | 1 |
| C35 | 47µF, ≥10V — Panasonic EEE-FK1V470P (wet Al-electrolytic, 35V) **or** EEH-ZA1V470P (polymer) | +3V3 input bulk | 1 |
| C36 | 100nF, 16V, X7R | +3V3 input HF bypass | 1 |
| C37 | 10µF, 10V, X5R | +3V3 board-level bulk | 1 |
| C38 | 100nF, 16V, X7R | +3V3 board-level HF | 1 |
| C39 | 10µF, 10V, X5R | +5V board-level bulk | 1 |
| C40 | 100nF, 16V, X7R | +5V board-level HF | 1 |
| D6, D7 | Green LED, 0603 | Power indicators (DNP flight) | 2 |
| R17, R18 | 1kΩ | LED resistors (DNP flight) | 2 |

### Sheet 7: Connectors

| Ref | Value | Description | Qty |
|---|---|---|---|
| J1 (H1 + H2) | 2× Samtec ESQ-126-39-G-D | CSKB 2×26 stackthrough socket, 0.1″ (2.54 mm), one each for H1 and H2 | 2 |
| J4 | SMA, female, edge-launch | TX antenna connector | 1 |
| J5 | SMA, female, edge-launch | RX antenna connector | 1 |
| J6 | 1×6 header (optional) | Debug signal header | 0–1 |
| C41 | 10µF, 10V, X5R | +3V3 connector bypass bulk | 1 |
| C42 | 100nF, 16V, X7R | +3V3 connector bypass HF | 1 |
| C43 | 10µF, 10V, X5R | +5V connector bypass bulk | 1 |
| C44 | 100nF, 16V, X7R | +5V connector bypass HF | 1 |
| TP1–TP10 | Test point pads | Probe points | 10 |

---

## Design Notes Summary

These are the key design decisions. Place a condensed version in the
title block "Notes" field or as a text frame on the Top sheet.

1. **Architecture:** 70cm BPSK TX / 2m AFSK RX, single PCB, RP2040 controller
2. **Power:** All regulated power (+3V3, +5V) from EPS via CSKB bus connector.
   No on-board regulators in stack configuration.
3. **Clock gen:** Si5351A, CLK0=145.67 MHz (TX, tripled to 437 MHz),
   CLK1=145.9 MHz (RX LO). Both within Si5351A spec (<200 MHz).
4. **BPSK modulation at 145.67 MHz** — XOR gate timing analysis shows
   74LVC1G86 fails at 437 MHz but has massive margin at 146 MHz.
   Phase states preserved through odd-order multiplication.
5. **Frequency tripler:** Class-C biased BFR92A (ft=5 GHz). Bias
   resistor 47kΩ optimized from breadboard testing (-7.4 dBm @ 437 MHz).
6. **MMIC:** ADL5602 (20 dB gain), replaces SPF5189Z. Expected output
   ~+13 dBm at 437 MHz.
7. **RX front-end:** PSA4-5043+ LNA (~21 dB gain, ~1 dB NF) feeding
   ADE-1+ passive double-balanced diode mixer (Mini-Circuits, Level 7,
   +7 dBm LO). 5-pole Butterworth LPF on the LO line (fc≈200 MHz)
   suppresses Si5351A square-wave harmonics. 51 Ω resistor terminates
   the IF port. **Changed from SA612 active mixer** due to SA612
   end-of-life sourcing. New architecture has ~5 dB better system NF.
   See [`rx_mixer_trade_study.md`](rx_mixer_trade_study.md) for full rationale.
8. **Baseband filter:** Sallen-Key LPF, fc=3.3 kHz, -40 dB/decade.
   LTspice verified: 1200 Hz at -0.56 dB, 2200 Hz at -1.75 dB.
9. **Gain stage:** MCP6022 non-inverting, gain=11 (20.8 dB), mid-supply
   bias at 1.65V.
10. **CSKB connectors:** 2× Samtec ESQ-126-39-G-D (2×26, 0.1″ stackthrough),
    populated at H1 (signals) and H2 (power). Pin assignment follows
    Pumpkin CubeSat Kit Bus per [`system/interfaces/cskb_pinmap.md`](../../../system/interfaces/cskb_pinmap.md)
    (datasheet Rev. E pp. 13–16). COMMS_IRQ on H1.16, SPI on
    H1.21/22/23/24, I2C on H1.41/43, +5V on H2.25/26, +3V3 on H2.27/28,
    DGND on H2.29/30/32, AGND on H2.31, VBAT on H2.45/46.
11. **RF connectors:** Separate TX/RX SMA, no diplexer for prototype.
12. **All RF filter caps must be C0G/NP0** — X7R is voltage-dependent
    and detunes filters at RF.
13. **I2C bus:** Shared between Si5351A (0x60) and EPS LTC4162 (0x68) —
    no address conflict. Pull-ups on comms board only (4.7kΩ to 3.3V).

---

## Related Documents

- Comms overview and design rationale: [`hardware/comms/design/overview.md`](overview.md)
- **Project-level net naming convention:** [`hardware/conventions/net_naming.md`](../../conventions/net_naming.md)
- **RX mixer trade study (SA612 → ADE-1+ + PSA4 LNA):** [`hardware/comms/design/rx_mixer_trade_study.md`](rx_mixer_trade_study.md)
- **RF layout guidelines (ground plane, via stitching, stackup):** [`hardware/comms/design/rf_layout_guidelines.md`](rf_layout_guidelines.md)
- Sallen-Key simulation lab: [`hardware/comms/design/sallen_key_simulation_lab.md`](sallen_key_simulation_lab.md)
- Sallen-Key LTspice files: `hardware/comms/design/sallen_key_ltspice_lab/`
- Si5351A bring-up log: [`hardware/comms/bringup/si5351a_bringup_log.md`](../bringup/si5351a_bringup_log.md)
- Tripler breadboard build guide: [`hardware/comms/bringup/tripler_breadboard.md`](../bringup/tripler_breadboard.md)
- TX test plan: [`hardware/comms/bringup/tx_test_plan.md`](../bringup/tx_test_plan.md)
- RX test plan: [`hardware/comms/bringup/rx_test_plan.md`](../bringup/rx_test_plan.md)
- EPS schematic guide: [`hardware/eps/design/schematic_guide.md`](../../eps/design/schematic_guide.md)
- EPS architecture: [`hardware/eps/design/overview.md`](../../eps/design/overview.md)
- v0.1 schematic PDF: `hardware/comms/design/satellite_comms_draft_v0.1.pdf`
