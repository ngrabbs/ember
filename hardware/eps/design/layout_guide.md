# Layout & Routing Guide — EPS Board

**Board:** [`hardware/eps/kicad/`](../kicad/), project `eps`. 2-layer,
JLCPCB 1.6 mm FR-4.
**Rules:** the numbers below that are project-wide live in
[`../../conventions/kicad_jlcpcb_design_rules.md`](../../conventions/kicad_jlcpcb_design_rules.md);
this guide covers what is specific to laying out *this* board.

## Board Summary

| Parameter | Value |
|---|---|
| Form factor | PCI-104 (96 mm x 90 mm) |
| Layer count | 2 |
| Thickness | 1.6 mm (standard) |
| Fabricator | JLCPCB |
| Assembly | JLCPCB SMT (top side), hand-solder THT |
| Min trace/space | 0.15 mm / 0.15 mm (project default; JLCPCB 2-layer allows 0.10 mm) |
| Min drill | 0.3 mm (JLCPCB standard) |
| Copper weight | 1 oz both layers (2 oz available on 2-layer — see §1) |

---

## 1. Layer Stackup

**This board is 2-layer.** Rev A was fabbed 2-layer and the KiCad project is
2-layer; earlier revisions of this guide called for 4, which was never what
got built.

| Layer | KiCad | Purpose |
|---|---|---|
| Top | `F.Cu` | SMD pads, signal traces, power routing, ground pour in the gaps |
| Bottom | `B.Cu` | THT pads, secondary routing, and the main ground pour |

JLCPCB 2-layer 1.6 mm FR-4, Dk ≈ 4.5. No `JLC04161H-*` stackup code applies —
those are 4-layer only.

### The 2-layer consequence

On a 4-layer board an inner plane gives every trace a continuous return path
for free. **You do not have that here.** Ground is a pour on both faces, and
every gap you cut in it — a trace crossing, a row of THT pads — is a detour
the return current has to take. On a switching power board that detour is
loop area, and loop area is radiated noise.

That makes three things non-negotiable:

- **The bottom pour is the return path.** Keep it as unbroken as you can
  under the switching nodes and their loops. Route bottom-side signals around
  the power sections, not through them.
- **Stitch the two pours together** every 5–10 mm, and densely around the
  switchers, so top and bottom ground sit at the same potential.
- **Never let a trace on one layer split the pour on the other** beneath a
  power loop. If a bottom trace has to cross under the LTC4162 or a buck,
  move it or take it around.

### Copper weight — worth a decision

JLCPCB offers **1 / 2 / 2.5 / 3.5 / 4.5 oz** on 2-layer (4-layer outer is
fixed at 1 oz). With no inner planes to spread current or heat, 2 oz is worth
pricing for this board: it halves the width needed for a given current and
roughly doubles the copper available as a heat spreader under the regulators.

Current default is **1 oz**, and the trace widths in
[`trace_sizing_quickref.md`](trace_sizing_quickref.md) assume it. If you move
to 2 oz, revisit them.

### Power routing without a plane

There is no inner plane to zone into rails — power is distributed on the top
layer as wide traces and poured islands. See §6 for the detail.

---

## 2. Component Placement

### Top Side (F.Cu) — SMD Components, JLCPCB Assembly

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

### Bottom Side (B.Cu) — THT and Battery

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
  with a via to the bottom ground pour directly at the cap's ground pad
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
   Via the ground pad straight down to the bottom ground pour.

2. **Inductor (L20/L21)** — place so the pad connected to SW (pin 5)
   is as close to pin 5 as possible. A short, wide trace (0.4-0.5 mm)
   from SW to the inductor pad. This trace has fast voltage
   transitions (0 V to VOUT_PP at 500 kHz).

3. **Output caps (C34-C36 / C44-C46)** — place at the inductor
   output pad. These filter the output ripple and close the power
   loop. Via their ground pads to the bottom ground pour.

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
- Connect the vias to the bottom ground pour
- On the bottom layer, add a copper fill pad under the via grid if no
  battery holder interferes — this spreads heat to the bottom copper
- Set a negative paste-mask expansion on the exposed pad so solder paste
  doesn't flow down the vias — in KiCad, the pad's **Solder Paste Margin**
  in Pad Properties. Alternatively use via-in-pad with filled/capped vias
  if budget allows; for prototype, tented or open vias with reduced paste
  are fine

### TPS62933F (U2, U3) Thermal Pad

SOT-583 has a small exposed pad on the bottom. Same approach:
- 4 thermal vias (2x2 grid, 0.3 mm drill) under the pad
- Connect to the bottom ground pour
- The TPS62933F dissipates very little at the currents you'll use
  (~200-500 mA typical per rail), so this is mostly precautionary

### Power Inductors (L1, L20, L21)

Shielded inductors dissipate heat through their pads and the
magnetic core. Ensure the pads connect to copper fills (not isolated
islands) so heat can spread. No thermal vias needed — the pads
connect to power nets that are already wide copper.

---

## 6. Copper Fills and Stitching

### Top Side (F.Cu) Fills

Pour a `GND` fill on all unused top-side area. On a 2-layer board this is not
just shielding — together with the bottom pour it *is* the return path.

- Stitch the top pour to the bottom pour with vias every 5–8 mm around the
  perimeter and across open areas
- Stitch densely around the buck regions, inside the power-loop area, so the
  two pours are one low-impedance ground
- Do not leave isolated islands of pour. An unstitched island is a floating
  antenna, not a ground

### Bottom Side (B.Cu) Fills

The bottom pour is the primary ground. Keep it as continuous as possible,
especially beneath the LTC4162 and both bucks.

- Pour `GND` across all unused bottom area
- Leave clearance around the battery holder pads and the PCI-104 connector
  field
- Route bottom-side signals around the power sections. Any trace that crosses
  under a switching loop cuts the return path and forces the current around it

### Power distribution (no inner plane)

There is no power plane on this board. Distribute rails on the **top layer**:

- Poured islands on top for `VOUT_PP` and `VBAT` — the highest-current nets —
  sized per [`trace_sizing_quickref.md`](trace_sizing_quickref.md)
- `VOUT_PP` runs from the U1 output area to the U2/U3 inputs; this is the
  main distribution path and wants to be short and wide
- `+3V3` and `+5V` fan out from their regulators as wide top-side traces
- Keep 0.3 mm minimum between adjacent power islands

## 7. Via Strategy

| Via Type | Drill | Annular Ring | Use |
|---|---|---|---|
| Standard signal | 0.3 mm | 0.6 mm | Signal routing, layer transitions |
| Power via | 0.4 mm | 0.8 mm | Power rail connections (VOUT_PP, VBAT, +3V3, +5V) |
| Thermal via | 0.3 mm | 0.6 mm | Under IC thermal pads, to the bottom ground pour |
| Stitching via | 0.3 mm | 0.6 mm | GND pour stitching, top pour to bottom pour |

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
position-file export. After generating outputs:
1. Export the position file (`File → Fabrication Outputs → Component
   Placement (.pos)`), CSV format, units mm
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
- All component reference designators
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

Project-wide constraints are **already set in the project** and live in
[`../../conventions/kicad_jlcpcb_design_rules.md`](../../conventions/kicad_jlcpcb_design_rules.md)
§5.1 — don't restate them here, they drift. `Board Setup → Design Rules →
Constraints` currently holds:

| Constraint | Value |
|---|---|
| Min track width | 0.2 mm |
| Min clearance | 0.2 mm |
| Min via diameter / drill | 0.6 / 0.3 mm |
| Min annular width | 0.15 mm |
| Hole to hole | 0.6 mm |

`eps.kicad_dru` adds the board-specific rules: a minimum-width floor on the
high-current classes, and extra clearance around switching nodes.

### Net-Specific Trace Width Rules

Set in `Board Setup → Net Classes`, assigned by net-name pattern. These are
the classes the project actually carries:

| Net class | Patterns | Track width | Clearance |
|---|---|---|---|
| `PWR_HIGH` | `VBAT`, `BATT_POS`, `VOUT_PP`, `VIN_CHG`, `SW_NODE` | 1.27 mm | 0.25 mm |
| `PWR` | `+3V3`, `+5V` | 0.5 mm | 0.2 mm |
| `Default` | everything else — I2C, feedback, control nets | 0.2 mm | 0.2 mm |

`eps.kicad_dru` enforces a 1.0 mm floor on `PWR_HIGH` — the IPC-2152 width
for 3 A on 1 oz outer copper — so DRC catches a high-current rail routed at
signal width.

---

## 11. Pre-Fabrication Checklist

Before generating Gerbers:

- [ ] Run DRC — zero errors (warnings reviewed and accepted)
- [ ] Verify all thermal pads have via grids connected to the bottom ground pour
- [ ] Verify no signal traces cross under/over SW node traces without
      a continuous ground plane between them
- [ ] Verify CIN HF caps (C2, C31, C41) are within 3 mm of their
      respective IC VIN pins
- [ ] Verify FB divider resistors are within 3 mm of FB pins
- [ ] Verify the bottom ground pour has no unintended splits or slots under the power loops
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

`File → Fabrication Outputs → Gerbers (.gbr)`. Select these layers:

| Layer | KiCad name |
|---|---|
| Top copper | `F.Cu` |
| Bottom copper | `B.Cu` |
| Top solder mask | `F.Mask` |
| Bottom solder mask | `B.Mask` |
| Top silkscreen | `F.SilkS` |
| Bottom silkscreen | `B.SilkS` |
| Top paste | `F.Paste` |
| Board outline | `Edge.Cuts` |

Options: **Use Protel filename extensions** on (JLCPCB expects them),
plot on a single page, no X2 attributes.

Drill file: `File → Fabrication Outputs → Drill Files`, Excellon format,
PTH and NPTH in one file, drill units mm.

Zip all files and upload to JLCPCB. Use their online Gerber viewer to
verify before ordering.

---

## Related Documents

- Schematic guide: [`altium_eps_schematic_guide.md`](altium_eps_schematic_guide.md) — still Altium-worded, conversion pending
- EPS architecture: [`hardware/eps/design/overview.md`](overview.md)
- Bring-up plan: [`hardware/eps/bringup/phase1_validation.md`](../bringup/phase1_validation.md)
- TPS62933F datasheet: TI SLUSEA4D (layout section 12, pp. 40-41)
- LTC4162-L datasheet: pp. 48-52 (PCB layout considerations)
