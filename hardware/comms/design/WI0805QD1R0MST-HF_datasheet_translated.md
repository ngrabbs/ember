# DDY WI0805QD1R0MST-HF — Datasheet (English Translation)

Translated from the original Chinese datasheet ([`C18221300.pdf`](C18221300.pdf)),
DDY/Huizhou Deli Electronics, Rev A, dated 2022-09-27. All units are
millimeters unless otherwise stated.

This is the part being considered for **L12** (PSA4-5043+ Vd bias choke,
1 µH) on the RX chain. See [`rx_mixer_trade_study.md`](rx_mixer_trade_study.md)
for the application context.

---

## 1. Part Number Decoder

The DDY series uses a structured part number:

```
WI  0805  QD  1R0  M  S  T  -  HF
 1    2    3   4   5  6  7      8
```

| Field | Meaning | Value for this part |
|---|---|---|
| 1 | Product symbol | `WI` = wire-wound chip inductor |
| 2 | Package size | `0805` (imperial — 0805 SMD) |
| 3 | Material / chip type | `QD` |
| 4 | Inductance | `1R0` = 1.0 µH (`R` is the decimal point) |
| 5 | Tolerance | `M` = ±20% (alt: `K` = ±10%) |
| 6 | Terminal material | `S` = tin (锡 = tin) |
| 7 | Packaging | `T` = tape & reel (alt: `B` = bulk) |
| 8 | Environmental | `HF` = halogen-free (alt: `LF` = lead-free, `FP` = red-phosphor-free) |

So **WI0805QD1R0MST-HF** = 0805 wire-wound chip inductor, 1.0 µH, ±20%
tolerance, tin terminals, tape & reel, halogen-free.

---

## 2. Package Dimensions (millimeters)

| Symbol | Meaning | Value | Type |
|---|---|---|---|
| L | Length (long axis of body) | 2.40 | max |
| W | Width (short axis of body) | 1.73 | max |
| T | Thickness / height | 1.52 | max |
| E | Land pad length (along inductor's long axis) | 1.02 | typical |
| F | Land pad width (across inductor's short axis) | 1.78 | typical |
| D | Gap between the two land pads | 0.76 | typical |

### Body view (looking down at the part)

```
       ←─── L (2.40 max) ───→

  ┌───────────────────────────┐  ↑
  │ [term]  [coil shield]     │  │
  │                           │ W (1.73 max)
  │ [term]  [coil shield]     │  │
  └───────────────────────────┘  ↓
                                  height T = 1.52 max
```

### Land pattern (what you draw in Altium)

```
   ←──── E ────→   ←─D─→   ←──── E ────→
   ┌─────────────┐         ┌─────────────┐    ↑
   │             │         │             │    │
   │   Pad 1     │         │   Pad 2     │    F = 1.78
   │             │         │             │    │
   └─────────────┘         └─────────────┘    ↓
   ←──────────── 2E + D = 2.80 ────────────→
```

- Each pad: **1.02 mm × 1.78 mm** (E × F)
- Gap between pads: **0.76 mm** (D)
- Total footprint span along the long axis: **2 × 1.02 + 0.76 = 2.80 mm**
- Total footprint span along the short axis: **1.78 mm** (= F)

Body sits centered on top, terminals lap onto the inner edges of each
pad. Standard 0805 reflow rules apply.

---

## 3. Electrical Characteristics — WI0805QD1R0MST-HF row

(Full series table on p.4 of the PDF; only the row for this part is
reproduced below. Other inductance values in the series have different
SRF, Rdc, Isat, Irms specs.)

| Parameter | Symbol | Value | Conditions |
|---|---|---|---|
| Inductance | L | 1.0 µH | at test frequency |
| Tolerance | — | ±20% | `M` suffix |
| Test frequency | Freq | 1 MHz | for L measurement |
| Quality factor | Q | 10 (typ) | at 1 MHz |
| **Self-resonant frequency** | **SRF** | **550 MHz (typ)** | — |
| **DC resistance** | **Rdc** | **0.12 Ω (max)** | ±30% spec on Rdc itself |
| Saturation current | Isat | 1200 mA (typ) | DC current at which inductance drops |
| **RMS current** | **Irms** | **1000 mA (typ)** | DC current causing ~40°C rise above ambient |

### Application sanity check (for L12 / PSA4 bias choke)

- PSA4-5043+ draws ~60 mA → 60/1000 = 6% of Irms rating → trivial, no thermal concern
- DC voltage drop: 60 mA × 0.12 Ω = **7.2 mV** → trivial
- Inductive reactance at 145.9 MHz: 2π × 145.9 MHz × 1 µH = **916 Ω** ideal
- At 145.9 MHz with parasitic from 550 MHz SRF: effective Z ≈ 860 Ω → good RF choke

---

## 4. General Specifications

| Spec | Value |
|---|---|
| Operating temperature | -40 °C to +85 °C |
| Storage temperature | -10 °C to +40 °C |
| Storage humidity | 65 % RH max |
| Moisture sensitivity level | MSL 2 (1 year floor life at <30 °C / 65 % RH) |
| Rated DC current basis | Irms is defined as DC current producing ~40 °C temperature rise |

---

## 5. Soldering Conditions

### Reflow soldering (lead-free profile)

| Stage | Spec |
|---|---|
| Pre-heat ramp | 60–180 s, ramping to 150 °C |
| Soak | 60–150 s, 150–200 °C |
| Time above 217 °C (liquidus) | 20–40 s |
| Peak temperature | 260 °C max (10 s max at peak) |
| Total cycle time | 480 s max |
| Max reflow cycles | 2 |
| Solder paste thickness | 0.08 mm preferred, 0.10 mm max |

### Hand soldering

- 20 W iron, 1.0 mm tip diameter
- 3 seconds max per joint
- Pre-heat board to 150 °C, then peak 330–350 °C, then natural cooling
  (allow more than 1 min above ambient before handling)

---

## 6. Appearance Standard

The only flagged cosmetic defect is "copper wire exposed in the
magnetic shield area." Up to **0.06 mm² of exposed copper wire** in
that region is acceptable. Larger exposure is a reject.

This is a QC criterion the manufacturer uses; not something you need
to act on at the design stage.

---

## 7. Packaging Information (Tape & Reel)

### Tape pocket dimensions (mm)

For the 0805 tape:

| Symbol | Meaning | Value |
|---|---|---|
| A | Pocket length | 1.85 |
| B | Pocket width | 2.40 |
| T | Pocket depth | 1.45 |

Polystyrene tape, 8 mm wide (W = 8.4 mm), 2 mm component-to-component
pitch (E = 2 mm), 1.5 mm sprocket hole (Ø1.5).

### Reel dimensions (mm)

| Symbol | Meaning | Value |
|---|---|---|
| ΦA | Reel outer diameter | 178 |
| ΦB | Hub outer diameter | 60 |
| ΦC | Center hole diameter | 13 |
| ΦD | (mounting hole circle?) | 21 |
| E | (reel feature) | 2 |
| W | Reel width (tape channel) | 8.4 |
| t | Flange thickness | 2 |
| R | (radius/edge) | 1 |

### Quantity per reel

**2000 pieces per reel** (盘 = reel).

### Peel-strength notes

Cover-tape peel-off:
- 0402 to 1210 sizes: 20 g to 80 g peel force
- Peel angle: 165° to 180°
- Peel speed: 300 mm/min ± 10 %

---

## 8. Application Restriction

The Chinese note at the bottom of the packaging page states:

> This material is **not intended for automotive or related
> applications**. The manufacturer will not accept any quality or
> liability claims arising from such use.

For a CubeSat EM/prototype this is fine. Don't plan to use this part
in any flight hardware that needs automotive-grade (AEC-Q) qualification.

---

## Sources

- Original (Chinese): [`C18221300.pdf`](C18221300.pdf) (DDY rev A, 2022-09-27)
- Translated by: Claude/comms session, 2026-05-20
- Verify all dimensions against the original PDF before committing the
  footprint. If anything below doesn't match what the PDF shows, the
  PDF is authoritative.
