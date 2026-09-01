# Altium Layout & Routing Guide — EPS Board

## Board Summary

| Parameter | Value |
|---|---|
| Form factor | PCI-104 (96 mm x 90 mm) |
| Layer count | 4 |
| Thickness | 1.6 mm (standard) |
| Fabricator | JLCPCB |
| Assembly | JLCPCB SMT (top side), hand-solder THT |
| Min trace/space | 0.15 mm / 0.15 mm (JLCPCB 4-layer standard) |
| Min drill | 0.3 mm (JLCPCB standard) |
| Copper weight | 1 oz outer, 0.5 oz inner (JLCPCB 4-layer default) |

---

## 1. Layer Stackup

Use JLCPCB's standard 4-layer stackup (JLC04161H-7628):

| Layer | Name | Purpose |
|---|---|---|
| L1 (Top) | `Signal + Components` | SMD pads, signal traces, short power jumps |
| L2 (Inner 1) | `GND` | Unbroken ground plane — this is the most important layer |
| L3 (Inner 2) | `Power` | Power distribution: VOUT_PP, VBAT, +3V3, +5V fills |
| L4 (Bottom) | `Signal + THT` | Battery holder pads, PCI-104 socket pads, THT jumper headers, secondary signal routing |

### Ground Plane Rules

- **L2 is sacred.** Do not route signals on L2. Do not split it. Do not
  put power fills on it. The only acceptable voids are the drill hits
  from vias and THT pads.
- Every IC decoupling cap return via goes straight down to L2.
- If you need to cross a signal trace over a power region on L3, that's
  fine — L2 provides the continuous return path underneath.

### Power Plane (L3) Zoning

Divide L3 into copper fill zones for each rail. Suggested layout:

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   VOUT_PP fill          │    +3V3 fill           │
│   (left/center,        │    (right, near        │
│    near LTC4162         │     U2 output and      │
│    and buck inputs)     │     PCI-104)           │
│                         │                        │
│─────────────────────────┼────────────────────────│
│                         │                        │
│   VBAT fill             │    +5V fill            │
│   (bottom-left,        │    (right, near        │
│    near battery         │     U3 output and      │
│    connectors)          │     PCI-104)           │
│                         │                        │
└──────────────────────────────────────────────────┘
```

Connect L3 fills to L1 pads via multiple vias at each IC power pin
cluster. Use 0.3 mm drill / 0.6 mm annular ring stitching vias.

---

## 2. Component Placement

### Top Side (L1) — SMD Components, JLCPCB Assembly

This is where all the SMD parts go. JLCPCB assembles this side.

#### Placement Zones

```
┌──────────────────────────────────────────────────────────────────┐
│                          96 mm                                   │
│  ┌─────┐                                                        │
│  │ MTG │   ZONE 1: Solar Input              ZONE 2: Charger     │
│  │ HOLE│   J1-J4 JST (top edge)             LTC4162 + MOSFETs   │
│  └─────┘   D1-D4 blocking diodes            MN1, MN2, RS1, RS2  │
│            R1, C1 impedance comp             L1, C3, C4          │
│                                              NTC, pullups        │
│                                                                  │
│ 90 mm     ZONE 3: Buck Regulators           ZONE 4: Connectors  │
│            U2 (3.3V) + L20 + caps            PCI-104 J1 area     │
│            U3 (5.0V) + L21 + caps            (footprint on       │
│            R20/R21 UVLO divider               bottom, but keep   │
│            JP_RBF nearby                      top-side bypass     │
│                                               caps C60-C63 here) │
│  ┌─────┐                                                        │
│  │ MTG │   ZONE 5: Safety & Test            ZONE 5 cont.        │
│  │ HOLE│   JP_INH1, JP_INH2                 TP1-TP8             │
│  └─────┘   R50, status LEDs                 (board edges)        │
│            D10, D11, D12, R30, R31                               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Placement Priorities (do these first, in this order)

1. **PCI-104 connector (J1)** — position is fixed by the PCI-104
   template. The socket body is on the bottom. Top-side bypass caps
   (C60-C63) go adjacent to the connector pin field.

2. **LTC4162-L (U1)** — center-left of the board. This is the largest
   IC (QFN-28, 4x5mm) and drives the most routing. Orient so that:
   - VIN pins (pin 7) face toward the solar input JSTs (top edge)
   - VOUT/SW pins (25, 26, 27, 28) face toward the buck regulators
   - I2C pins (13, 14) face toward the PCI-104 connector

3. **FDMC8327L MOSFETs (MN1, MN2)** — place immediately adjacent to
   U1, as close as physically possible. MN1 (input FET) between the
   solar input and U1's CLP/CLN pins. MN2 (battery FET) between U1's
   CSP/CSN and the battery path. These carry the full charge/load
   current.

4. **Current sense resistors (RS1, RS2)** — directly between their
   respective MOSFET source pads and the LTC4162 sense pins. Keep
   Kelvin sense traces (CLP/CLN, CSP/CSN) routed from the inner edges
   of the resistor pads, not from the power traces.

5. **Charger inductor (L1, 4.7 uH)** — between U1 SW pins and the
   CSP node. Keep the SW trace short — this is a high-dV/dt node
   that radiates.

6. **TPS62933F U2 and U3** — place side-by-side in Zone 3. Each buck
   forms a tight power loop (VIN → IC → SW → inductor → COUT → GND
   → CIN → VIN). Place input caps (C30/C31, C40/C41) touching the
   VIN/GND pins. Place inductors (L20, L21) touching the SW pads.
   Place output caps (C34-C36, C44-C46) at the inductor output.

7. **Solar JSTs (J1-J4)** — along the top edge of the board for
   cable management to face-mounted panels.

8. **RBF and inhibit jumpers** — along a board edge (left or bottom)
   for physical access during integration. JP_RBF should be near the
   R20/R21 divider it shorts across.

9. **Test points** — along board edges where a scope probe can reach
   without blocking other components.

### Bottom Side (L4) — THT and Battery

| Component | Placement |
|---|---|
| PCI-104 socket (J1) | Fixed position per PCI-104 template |
| Battery holders (2S2P) | Center-bottom or wherever the mechanical envelope allows. 4x 18650 holders take significant board area (~70 x 40 mm for 2x2). Verify clearance to the PCI-104 socket and mounting holes. |
| JST solar connectors (J1-J4) | THT pins poke through from top; solder on bottom |
| Battery JST (J5) / bench header (J6) | Near battery holders |
| RBF/inhibit jumper headers | THT pins poke through; solder on bottom |

---

## 3. Critical Routing — Power Loops

The three switching converters on this board (LTC4162, U2, U3) each
have a high-current, high-frequency power loop that MUST be kept as
small and tight as possible. A large loop area = more radiated EMI,
more ringing on the switch node, and potentially failed EMC or
degraded regulation.

### LTC4162 Power Loop

```
VIN_CHG → MN1 drain-source → CLP/RS1/CLN → U1 pin 3 (VOUTA)
  → L1 → CSP → RS2 → CSN → VBAT
  (return via GND plane back to CIN)
```

- C2 (100 nF HF bypass at VIN) must be within 3 mm of U1 VIN pin
  with a via to L2 GND directly at the cap's ground pad
- L1 should be as close to U1 SW pins as possible
- The SW node trace (L1 to U1) carries high dV/dt — keep it short
  and wide (0.5 mm min), but don't spread it out (area = antenna)
- C4 (BST cap) must be between BST and SW pins with minimal trace

### TPS62933F Power Loops (U2 and U3 — identical strategy)

```
VOUT_PP → CIN (C30/C31) → VIN (pin 3) → SW (pin 5) → L20 → COUT (C34/C35)
  (return via GND plane from COUT ground back to CIN ground)
```

**This is the single most layout-critical loop on each buck.** The
path from CIN+ through the IC to the inductor and back through the
output cap ground to CIN ground must be as small as possible.

Rules for each TPS62933F:

1. **C31/C41 (100 nF HF input cap)** — this cap closes the high-
   frequency loop. Place it directly at the VIN (pin 3) and GND
   (pin 4) pads. The trace from C31 pad to VIN pin should be < 2 mm.
   Via the ground pad straight down to L2.

2. **Inductor (L20/L21)** — place so the pad connected to SW (pin 5)
   is as close to pin 5 as possible. A short, wide trace (0.4-0.5 mm)
   from SW to the inductor pad. This trace has fast voltage
   transitions (0 V to VOUT_PP at 500 kHz).

3. **Output caps (C34-C36 / C44-C46)** — place at the inductor
   output pad. These filter the output ripple and close the power
   loop. Via their ground pads to L2.

4. **BST cap (C32/C42, 100 nF)** — directly between BST (pin 6) and
   SW (pin 5). This is a high-frequency gate drive path. Keep the
   loop area tiny.

5. **C30/C40 (10 uF bulk input cap)** — can be slightly further out
   (within 5 mm of VIN pin). It handles lower-frequency bulk energy
   storage, so loop area is less critical than C31/C41.

### Rule of Thumb for All Power Loops

If you can cover the entire CIN → VIN → SW → L → COUT → GND → CIN
loop with your thumbnail, the layout is good. If you need two
thumbnails, it's too big.

---

## 4. Signal Routing

### I2C Bus (SCL, SDA, SMBALERT_N)

- Route on L1 as a group, 0.2 mm traces, with GND guard spacing
- Keep away from SW nodes and inductor traces (noise coupling)
- Route from U1 pins 13/14 toward the PCI-104 connector
- The 10 kOhm pullup resistors (R4, R5, R6) should be near U1, not
  at the connector end

### Feedback Dividers (R23/R24, R25/R26)

- Route FB traces (from divider midpoint to U2/U3 pin 8) as short as
  possible — these are high-impedance sense nodes
- Keep FB traces away from SW nodes, inductors, and power traces
- Route on L1 only, no vias in the FB path
- Place the divider resistors within 3 mm of the FB pin

### EN UVLO Divider (R20/R21) and BUCK_EN Net

- R20/R21 should be close to U2/U3 EN pins
- JP_RBF connects across R21 — place the jumper header physically
  adjacent to R21 so the cross-sheet connection is a short trace
- The BUCK_EN net is low-frequency DC — routing is not critical, but
  keep it away from SW nodes for noise immunity

### DEPLOY_ARMED and Enable Nets

- Low-frequency DC logic nets, not routing-critical
- Keep the COMMS_TX_EN and BURN_EN traces routed to dedicated PCI-104
  pins for clean board exit

---

## 5. Thermal Management

### LTC4162-L (U1) Thermal Pad

The QFN-28 exposed pad is the primary heat dissipation path. At the
low solar currents (~80 mA), thermal is not a concern. But at bench
supply testing (3.2 A charge current), the IC will warm up.

- Place a grid of thermal vias (0.3 mm drill, 0.6 mm annular) under
  the exposed pad — minimum 9 vias in a 3x3 grid
- Connect the vias to the L2 GND plane
- On L4 (bottom), add a copper fill pad under the via grid if no
  battery holder interferes — this spreads heat to the bottom copper
- In Altium: set the paste mask expansion to negative so solder paste
  doesn't flow down the vias (or use via-in-pad with filled/capped
  vias if budget allows — but for prototype, tented or open vias with
  reduced paste are fine)

### TPS62933F (U2, U3) Thermal Pad

SOT-583 has a small exposed pad on the bottom. Same approach:
- 4 thermal vias (2x2 grid, 0.3 mm drill) under the pad
- Connect to L2 GND
- The TPS62933F dissipates very little at the currents you'll use
  (~200-500 mA typical per rail), so this is mostly precautionary

### Power Inductors (L1, L20, L21)

Shielded inductors dissipate heat through their pads and the
magnetic core. Ensure the pads connect to copper fills (not isolated
islands) so heat can spread. No thermal vias needed — the pads
connect to power nets that are already wide copper.

---

## 6. Copper Fills and Stitching

### Top Side (L1) Fills

Pour a GND copper fill on all unused L1 area. This provides
shielding, reduces EMI, and gives the autorouter return paths.

- Use the same `GND` net as L2
- Stitch L1 GND pour to L2 with vias every 5-8 mm around the board
  perimeter and in open areas
- Add stitching vias around the buck converter regions (inside the
  "thumbnail" power loop area) to create a low-impedance ground
  connection between L1 and L2

### Bottom Side (L4) Fills

Pour GND on unused L4 area as well, stitched to L2. Leave clearance
around battery holder pads and the PCI-104 connector field.

### Power Plane (L3) Fills

- Define separate polygon pours for VOUT_PP, VBAT, +3V3, +5V
- Use net-tied vias from L1 component pads down to the appropriate
  L3 fill for power distribution
- Clearance between L3 fills: 0.3 mm minimum (JLCPCB standard)
- VOUT_PP fill should extend from U1 VOUT output area to U2/U3 VIN
  input areas — this is the main power distribution path

---

## 7. Via Strategy

| Via Type | Drill | Annular Ring | Use |
|---|---|---|---|
| Standard signal | 0.3 mm | 0.6 mm | Signal routing, layer transitions |
| Power via | 0.4 mm | 0.8 mm | Power rail connections (VOUT_PP, VBAT, +3V3, +5V) |
| Thermal via | 0.3 mm | 0.6 mm | Under IC thermal pads, to L2 GND |
| Stitching via | 0.3 mm | 0.6 mm | GND pour stitching, L1/L4 to L2 |

For power connections carrying > 1 A, use multiple vias in parallel.
Rule of thumb: each 0.3 mm via in 1 oz copper can carry ~0.5 A with
moderate temperature rise. So for a 3 A path, use at least 6 vias.

---

## 8. JLCPCB Assembly Notes

### Fiducials

JLCPCB requires at least 2 (preferably 3) fiducial marks on the
assembly side for optical alignment. Place 1 mm diameter copper
circles with 2 mm solder mask opening:
- Two fiducials in opposite corners of the board (diagonal)
- One optional third fiducial near the center or opposite edge

### Component Orientation

JLCPCB uses the component centroid file and rotation data from the
Altium pick-and-place export. After generating outputs:
1. Export Pick and Place files (File > Assembly Outputs > Generates
   Pick and Place Files)
2. Verify the CSV has correct X/Y/Rotation for each part
3. JLCPCB's online tool lets you visually verify placement before
   ordering — use it

### Which Parts JLCPCB Assembles vs. Hand-Solder

**JLCPCB assembles (top-side SMD):**
- U1 (LTC4162, QFN-28)
- U2, U3 (TPS62933F, SOT-583)
- MN1, MN2 (FDMC8327L, WDFN-8)
- All resistors, capacitors, inductors (0402-1210)
- Blocking diodes D1-D4
- LEDs D10-D12
- NTC thermistor RT1

**You hand-solder (THT):**
- J1-J4 (JST solar connectors)
- J5 (battery JST)
- J6 (bench supply header)
- J1/PCI-104 socket (MMS-130-02-L-DV-A)
- JP_RBF, JP_INH1, JP_INH2 (2.54 mm pin headers)
- Battery holders (bottom side)
- Test point pins/loops if using THT style (or use SMD test pads
  and skip this)

---

## 9. Silkscreen

### Required Markings

- Board name: `EPS v0.1`
- All component reference designators (Altium default)
- Connector labels: `SOLAR X+`, `SOLAR X-`, `SOLAR Y+`, `SOLAR Y-`,
  `BATT`, `BENCH`, `STACK (J1)`
- Rail labels near test points: `+3V3`, `+5V`, `VBAT`, `VOUT_PP`
- **RBF marking** — large, visible text near JP_RBF:
  `RBF - REMOVE BEFORE FLIGHT`
- **Inhibit markings** near JP_INH1/JP_INH2:
  `INH1` and `INH2 - DEPLOY INHIBITS`
- Polarity indicators on all polarized components (diodes, LEDs,
  electrolytic caps, battery connectors)
- Pin 1 dots on all ICs
- Board orientation mark (e.g., arrow indicating "top" relative to
  the stack)

### Suggested Bottom Silkscreen

- `EPS v0.1 — BOTTOM`
- Battery polarity markings on holders: `B+ B-`
- PCI-104 connector pin a1 indicator

---

## 10. Design Rule Check (DRC) Settings

Set these in Altium before routing (Design > Rules):

| Rule | Value | Notes |
|---|---|---|
| Min trace width | 0.15 mm | JLCPCB 4-layer minimum |
| Min clearance | 0.15 mm | Trace-to-trace, trace-to-pad |
| Min drill size | 0.3 mm | JLCPCB standard process |
| Min annular ring | 0.13 mm | JLCPCB minimum |
| Power trace width | 0.5-1.0 mm | For VOUT_PP, VBAT, +3V3, +5V |
| Signal trace width | 0.2 mm | I2C, feedback, control nets |
| High-current trace width | 1.0-2.0 mm | Charger input/output, buck SW nodes |

### Net-Specific Trace Width Rules

In Altium, create net class rules (Design > Rules > Routing > Width):

| Net Class | Nets | Min Width | Preferred Width |
|---|---|---|---|
| `Power_High` | VOUT_PP, VBAT, SOLAR_BUS, VIN_CHG, SW_NODE | 0.5 mm | 1.0 mm |
| `Power_Rail` | +3V3, +5V | 0.4 mm | 0.8 mm |
| `Signal` | I2C_SCL, I2C_SDA, SMBALERT_N, FB nets | 0.15 mm | 0.2 mm |
| `Control` | BUCK_EN, DEPLOY_ARMED, COMMS_TX_EN, BURN_EN | 0.15 mm | 0.2 mm |

---

## 11. Pre-Fabrication Checklist

Before generating Gerbers:

- [ ] Run DRC — zero errors (warnings reviewed and accepted)
- [ ] Verify all thermal pads have via grids connected to L2 GND
- [ ] Verify no signal traces cross under/over SW node traces without
      a continuous ground plane between them
- [ ] Verify CIN HF caps (C2, C31, C41) are within 3 mm of their
      respective IC VIN pins
- [ ] Verify FB divider resistors are within 3 mm of FB pins
- [ ] Verify L2 GND plane has no unintended splits or slots
- [ ] Verify all power vias have sufficient count for current
- [ ] Check board outline matches PCI-104 template (96 x 90 mm)
- [ ] Check mounting hole positions match template
- [ ] Check PCI-104 connector position matches template
- [ ] Verify fiducials are present (2 minimum)
- [ ] Verify silkscreen text is legible (min 0.8 mm height)
- [ ] Verify RBF and INH labels are prominent
- [ ] Generate and review pick-and-place CSV for JLCPCB
- [ ] Export Gerbers and upload to JLCPCB viewer for visual check

---

## 12. Gerber Export Settings (for JLCPCB)

File > Fabrication Outputs > Gerber Files:

| Layer | Gerber Suffix |
|---|---|
| Top Copper | `.GTL` |
| Inner 1 (GND) | `.G1` |
| Inner 2 (Power) | `.G2` |
| Bottom Copper | `.GBL` |
| Top Solder Mask | `.GTS` |
| Bottom Solder Mask | `.GBS` |
| Top Silkscreen | `.GTO` |
| Bottom Silkscreen | `.GBO` |
| Top Paste | `.GTP` |
| Board Outline | `.GKO` (mechanical 1) |

Drill file: File > Fabrication Outputs > NC Drill Files (`.DRL`)

Zip all files and upload to JLCPCB. Use their online Gerber viewer to
verify before ordering.

---

## Related Documents

- Schematic guide: `hardware/eps/design/altium_eps_schematic_guide.md`
- EPS architecture: `hardware/eps/design/overview.md`
- Bring-up plan: `hardware/eps/bringup/phase1_validation.md`
- TPS62933F datasheet: TI SLUSEA4D (layout section 12, pp. 40-41)
- LTC4162-L datasheet: pp. 48-52 (PCB layout considerations)
