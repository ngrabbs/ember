# Altium Design Rules — JLCPCB Constraints

**Scope:** every PCB in this project (EPS, IHU, comms, payload, future
boards). All boards are fabbed by JLCPCB on their standard
4-layer 1.6 mm FR4 process unless explicitly stated otherwise.
**Owner:** hardware lead.
**Status:** living document — update when JLCPCB publishes new
capabilities or when we move a board to their advanced process tier.

> **KiCad users:** this doc is the source of truth for the *values*; see
> [`kicad_jlcpcb_design_rules.md`](kicad_jlcpcb_design_rules.md) for *where they
> go in KiCad* and how to do controlled impedance without Altium Impedance
> Profiles (stackup → calculator → net class → custom rule).

This is the **single source of truth for design rule values** when you
set up a new Altium PCB project. The intent: type these numbers into
Altium's `Design → Rules` dialog once for a new board, export the
result to a `.RUL` file, commit it next to this doc, and re-import on
every subsequent board.

---

## 1. How to use this doc

1. New project? Run **JLCPCB's Altium stackup plugin** for layer
   thicknesses + impedance reference (the plugin does that part
   automatically — don't fight it). For our 4-layer 1.6 mm default
   stack see §10.
2. Then open `Design → Rules` and enter the values from §3–§7 below.
3. Once the rules are set, **export as `.RUL` and commit to repo**
   under `hardware/conventions/jlcpcb_baseline.RUL` (file
   doesn't exist yet — first project to fully set up the rules
   creates it).
4. On every subsequent board, **import that `.RUL` instead of typing
   the values again**. The values below are documentation of what the
   `.RUL` should contain.

---

## 2. Quick reference cheat-sheet

Everything you need at a glance. Detailed reasoning + Altium rule
names in §3 onward.

| Constraint | JLCPCB min (standard process) | **Project default** | Where it lives in Altium |
|---|---|---|---|
| Track width (signal) | 5 mil / 0.127 mm | **8 mil / 0.2 mm** | Routing → Width |
| Track width (low-current power, <500 mA) | 5 mil | **20 mil / 0.51 mm** | Routing → Width (Net Class `PWR`) |
| Track width (medium power, ~1 A) | 5 mil | **30 mil / 0.76 mm** | Routing → Width (Net Class `PWR_HIGH`) |
| Track width (high power, ≥3 A — `+5V_ORIN`, `VBAT`) | 5 mil | **50 mil / 1.27 mm** on L1 or L4 outer | Routing → Width (Net Class `PWR_HIGH`) |
| Clearance (track-to-track) | 5 mil | **8 mil / 0.2 mm** | Electrical → Clearance |
| Clearance (track-to-pad) | 5 mil | **8 mil** | Electrical → Clearance |
| Clearance (copper-to-edge) | 0.2 mm / 8 mil | **0.3 mm / 12 mil** (extra room for v-cut / panel rails) | Manufacturing → Board Outline Clearance |
| Via drill | 0.3 mm / 12 mil | **0.3 mm / 12 mil** (use standard, advanced costs extra) | Routing → Routing Via Style → Hole Size |
| Via diameter (outer pad) | drill + 0.2 mm = **0.5 mm** | **0.6 mm / 24 mil** (0.15 mm annular ring per side) | Routing → Routing Via Style → Diameter |
| Annular ring | 4 mil / 0.1 mm | **6 mil / 0.15 mm** (matches the via spec above) | (implicit from drill + diameter) |
| Hole-to-hole (centre-to-centre) | 0.5 mm | **0.6 mm** | Manufacturing → Hole to Hole Clearance |
| Hole-to-trace | 8 mil / 0.2 mm | **10 mil / 0.25 mm** | Manufacturing → Minimum Solder Mask Sliver (see §5) |
| PTH hole-to-edge | 0.3 mm | **0.5 mm** | (mechanical placement — not enforceable as Altium rule, check manually) |
| NPTH hole-to-edge | 0.15 mm | **0.3 mm** | (mechanical placement) |
| Soldermask sliver | 4 mil / 0.1 mm | **5 mil / 0.127 mm** | Mask → Solder Mask Sliver |
| Soldermask expansion | 0.1 mm typical | **0.1 mm** (Altium default) | Mask → Solder Mask Expansion |
| Silkscreen line width | 5 mil / 0.127 mm | **6 mil / 0.15 mm** | Placement → Silkscreen (no built-in rule — check manually) |
| Silkscreen text height (refdes) | 24 mil / 0.6 mm legible | **32 mil / 0.8 mm** for refdes, **40 mil** for warnings | (text properties on each label) |
| Controlled impedance tolerance | ±10 % | match the tolerance, accept ~$5–15 surcharge for flight boards | Routing → Differential Pairs Routing (impedance target) |
| Board thickness | 1.6 mm standard, 0.4 / 0.6 / 0.8 / 1.0 / 1.2 / 2.0 also stocked | **1.6 mm** | Layer Stack Manager |
| Standard layer count | 1, 2, 4, 6, 8 | **4 (every board)** | Layer Stack Manager |

---

## 3. Track width and current capacity

JLCPCB's 5 mil minimum is more about **manufacturing yield** than
**signal carrying capacity**. We pad signal tracks to 8 mil for
robustness against over-etching, easier visual inspection, and
hand-rework headroom. Power tracks need the width for current.

### 3.1 Signal traces

| Net class | Width | Reason |
|---|---|---|
| Default (digital signal, GPIO, I²C, UART, SPI) | **8 mil / 0.2 mm** | Comfortable yield, easy probing |
| Controlled-impedance diff pair | per impedance target (see §4 in `altium_payload_layout_guide.md`) | Width and gap dictated by Z₀, not this table |
| RF signal (comms board 50 Ω microstrip) | per stackup (typical ~0.38 mm at JLCPCB 4-layer) | See `hardware/comms/design/rf_layout_guidelines.md` |

### 3.2 Power traces — current capacity guideline

These widths assume **1 oz outer-layer copper** (JLCPCB's default on
the 4-layer 1.6 mm process — note that the JLC04161H-7628 stackup is
actually **0.5 oz outer** in some variants; check the stackup plugin
output and add ~30 % to widths if you're on 0.5 oz). All values are
for ≤ 10 °C temperature rise:

| Current (continuous) | Width (1 oz outer) | Width (0.5 oz outer) | Used for |
|---|---|---|---|
| < 200 mA | 8 mil (signal default) | 8 mil | I²C pull-up rails, status LEDs |
| 500 mA | 15 mil | 20 mil | Camera 3.3 V (per FFC), M.2 socket 3.3 V branch |
| 1 A | 25 mil | 35 mil | Stack +3V3, +5V from CSKB to board entry |
| 2 A | 50 mil | 70 mil | Stack +3V3 rail, M.2 + cameras combined |
| 3 A | 70 mil | 100 mil | **`+5V_ORIN`** (Orin VDD_IN at peak 15 W) |
| 5 A | 110 mil | 160 mil | (margin/safety) |
| VBAT (~2 A typical, 4 A peak) | use 60 mil on outer, with copper-pour return | | Sized for the local buck's input |

For currents above ~2 A on inner layers, multiply outer-layer widths
by **2×** (inner layers dissipate heat poorly compared to outer
layers). Better practice: **always route power on outer layers**, use
copper pours for distribution where possible, and reserve inner
layers for ground/signal.

**Online calculator:** when in doubt, use Saturn PCB Toolkit's "PCB
trace width" tool or [https://www.4pcb.com/trace-width-calculator.html](https://www.4pcb.com/trace-width-calculator.html)
(IPC-2221 based). Plug in your copper weight, max temp rise, and
length.

---

## 4. Vias

JLCPCB charges no per-via fee but does limit minimums by process tier.
Stick to the standard tier (no surcharge) values.

### 4.1 Standard via

| Property | Value | Notes |
|---|---|---|
| Drill | **0.3 mm / 12 mil** | Standard tier; smaller = surcharge |
| Outer pad diameter | **0.6 mm / 24 mil** | Gives 0.15 mm (~6 mil) annular ring per side |
| Annular ring | **0.15 mm / 6 mil per side** | 50 % above JLCPCB's 4 mil minimum |
| Aspect ratio | drill : board thickness ≤ 1 : 8 | A 0.3 mm drill in a 1.6 mm board is 1:5.3, fine |
| Filled? | No (open / tented depending on use) | See §4.3 |

Altium setup: `Design → Rules → Routing → Routing Via Style → Add new`
with Hole Size = 0.3 mm, Diameter = 0.6 mm.

### 4.2 Power vias (when carrying ≥ 1 A through a via)

Same drill, but **use multiple parallel vias** instead of one large
via — paralleling vias drops the effective inductance roughly as 1/N
and spreads the current.

| Current through layer transition | Recommended | Why |
|---|---|---|
| < 500 mA | 1 via | Standard via is rated ~1.5 A continuous |
| 500 mA – 1.5 A | 2 vias | Margin + lower inductance |
| 1.5 A – 3 A | 4 vias | `+5V_ORIN` transition from L3 power plane to L1 surface, e.g. |
| 3 A – 5 A | 6+ vias | `VBAT` to buck input |

### 4.3 Tented / open / filled vias

| Treatment | When to use | Cost |
|---|---|---|
| **Tented** (soldermask covers the via) | Default — most signal and most power vias | No surcharge |
| **Open / exposed** (no soldermask) | Test points, debugging, or vias under fiducials | No surcharge |
| **Plated Over Filled Via (POFV)** | Via-in-pad on QFN/BGA exposed ground pads where solder theft would otherwise be a problem | **+$3–5 per order** |

The 0402 dogbone-vs-via-in-pad discussion in
`hardware/comms/design/rf_layout_guidelines.md` covers when POFV is
worth the surcharge. **Short answer: not for v0.1 dev runs; yes for
flight builds with reliability stakes.**

---

## 5. Clearances

Altium dialog: `Design → Rules → Electrical → Clearance`

| Clearance type | JLCPCB minimum | **Project default** | Altium rule scope |
|---|---|---|---|
| Track to track (same net OK, different nets) | 5 mil | **8 mil** | `Different Nets Only` |
| Track to pad | 5 mil | **8 mil** | (same rule) |
| Track to via | 5 mil | **8 mil** | (same rule) |
| Pad to pad (different nets) | 5 mil | **8 mil** | (same rule) |
| **High-voltage clearance** (>50 V, if applicable) | per IPC-2221 / IPC-9592 | Tier B uncoated, sea-level | Scoped clearance rule |
| Copper pour to track (different net) | 5 mil | **10 mil** | Plane → Polygon Connect Style |
| Copper to board edge (mech rail) | 8 mil | **12 mil / 0.3 mm** | Manufacturing → Board Outline Clearance |
| Diff pair to other trace | 5 mil | **3 × W (~25 mil)** | Differential Pair-specific clearance (see layout guide §4.4) |

For the high-current case (`+5V_ORIN`, `VBAT`) the default 8 mil
clearance is plenty — these are still low-voltage rails, just high
current. Don't over-think it.

---

## 6. Holes (PTH and NPTH)

| Property | JLCPCB minimum | **Project default** |
|---|---|---|
| Min PTH drill (through-hole component pin) | 0.3 mm | 0.3 mm |
| Min NPTH (mechanical hole, no plating) | 0.5 mm | 0.5 mm (but use 2.5 mm for M2.5 mounting holes) |
| Hole-to-hole centre-to-centre | 0.5 mm | 0.6 mm |
| Hole-to-trace clearance | 0.2 mm | 0.25 mm |
| Hole to board edge (PTH) | 0.3 mm | 0.5 mm |
| Hole to board edge (NPTH) | 0.15 mm | 0.3 mm |

**Common hole sizes** (PTH unless noted):

| Use | Drill | Pad | Notes |
|---|---|---|---|
| Standard via | 0.3 mm | 0.6 mm | §4.1 |
| M2.5 mounting hole (NPTH) | **2.7 mm** | n/a | Clearance for M2.5 (2.5 mm) screw + tolerance |
| M3 mounting hole (NPTH) | **3.2 mm** | n/a | Clearance for M3 screw |
| Standard 2.54 mm header pin | 1.0 mm | 1.7–1.8 mm | Most pin headers |
| 0.1" socket headers (Samtec ESQ-126 for CSKB) | per datasheet | per datasheet | Don't deviate |
| 1.27 mm header pin | 0.7 mm | 1.2 mm | Debug headers, recovery |
| JST-SH 1.0 mm (J_TRIG) | per datasheet | per datasheet | SMD anyway |
| SMA edge launch | per connector datasheet | — | Comms board only |

---

## 7. Solder mask + silkscreen

### 7.1 Solder mask

| Property | JLCPCB minimum | **Project default** |
|---|---|---|
| Soldermask sliver (between two adjacent pads) | 4 mil / 0.1 mm | 5 mil / 0.127 mm |
| Soldermask expansion (mask opens larger than pad) | 0.1 mm typical | 0.1 mm (Altium default) |
| Soldermask colour | green standard, blue / red / black / white / yellow / purple +$ | **green** unless otherwise specified |

### 7.2 Silkscreen

| Property | JLCPCB minimum | **Project default** |
|---|---|---|
| Line width | 5 mil | 6 mil |
| Text height (refdes, labels) | 24 mil legible / 32 mil recommended | **32 mil for refdes, 40 mil for warnings** |
| Silkscreen-to-pad clearance | 0.15 mm | 0.2 mm |
| Silkscreen on copper? | Will be ignored by JLCPCB | Don't place silkscreen on top of copper pads |

**Required silkscreen items on every board:**
- Board name + revision (e.g. "payload-carrier rev 0.1")
- All refdes (R1, C1, U1, etc.) — visible after assembly
- Connector pinout labels (pin 1 dot/triangle on all headers)
- Polarity markers on caps + diodes
- Any silkscreen warnings called out in the schematic guide (e.g. "BOOTLOADER ONLY", "RECOVERY", "UART: GND-TX-RX")

---

## 8. Controlled impedance

When ordering a board with diff pairs that need to hit a specific
impedance (every board with PCIe, USB, CSI, or RF):

| Item | Standard tier | Notes |
|---|---|---|
| Tolerance | ±10 % | Tighter (±5 %) costs more |
| Surcharge for impedance test report | ~$5–15 per order | Per-order, not per-board |
| Layers supported | 4-layer minimum | Impossible to control well on 2-layer |
| Test method | TDR on coupon | JLCPCB sends a coupon trace pair; they TDR-test it |

**For boards in this project:** order controlled impedance for the comms
board (50 Ω microstrip) and the payload carrier (PCIe, USB, CSI).
Skip the impedance test report for v0.1 dev runs (save the $10);
order it for flight builds.

Diff pair widths come from the per-board layout guides, not from this
doc — see `altium_<board>_layout_guide.md` §2 for each board's
specific impedance target widths.

**Workflow recommendation (project-wide):** **use Altium's Impedance
Profiles in the Layer Stack Manager** to compute diff-pair widths,
not hardcoded W/G values in design rules. After running the JLCPCB
stackup plugin, switch to the Layer Stack Manager's **Impedance** tab,
add a named profile per impedance target (e.g. `100R_DIFF_L1`,
`85R_DIFF_L1`, `90R_DIFF_L1`), and Altium's built-in 2D field solver
computes W/G against the actual JLCPCB-populated stackup. Then your
Differential Pair Routing rules reference the profile by name. If
JLCPCB changes the stackup on a later order, the profile auto-
recalculates and DRC flags any route that no longer hits target — no
manual sync. See `hardware/payload_compute/design/altium_payload_
layout_guide.md` §3.2 for the step-by-step walkthrough.

---

## 9. Net classes — recommended starting set

These net classes carry width / clearance / spacing rules. Set them
up once and apply rules by class instead of by individual net.

| Net class | Members | Width rule | Clearance rule | Other rules |
|---|---|---|---|---|
| `NET_SIG` (default) | All digital signals not otherwise classified | 8 mil | 8 mil | — |
| `NET_PWR` | Low-current rails (<500 mA) — I²C pull-ups, status LED supplies | 20 mil | 8 mil | — |
| `NET_PWR_HIGH` | Medium/high-current rails — `+5V_ORIN`, `VBAT`, `+3V3` (when carrying mux+cam+M.2 combined) | 50 mil | 10 mil | Plane connect: direct |
| `NET_RF` | Comms board 50 Ω microstrip | per stackup | per RF layout guide | Layer-constrained to L1, length match where applicable |
| `NET_DIFF_*` | See `altium_<board>_layout_guide.md` per board (DP_CSI, DP_PCIE, DP_USB, etc.) | per impedance target | per impedance target | Differential Pair Routing rule |

`NET_PWR_HIGH` deserves the wider clearance because the current means
adjacent traces could couple noticeably under fast load steps — keeps
SI cleaner.

---

## 10. JLCPCB stackup reference (for completeness)

The 4-layer 1.6 mm process is `JLC04161H-7628`. The Altium **JLCPCB
stackup plugin** populates the Layer Stack Manager with these values
automatically — don't fight the plugin, just run it. For reference,
the dielectric stack is:

| Layer | Function | Copper weight | Dielectric below | Material |
|---|---|---|---|---|
| L1 (top) | Signal / power / RF | 0.5 oz (≈17.5 µm) | 0.107 mm prepreg (3313) | — |
| L2 (inner) | **Solid GND plane** | 0.5 oz | 1.265 mm core (FR4) | Dk ≈ 4.3 |
| L3 (inner) | Power islands / slow signals | 0.5 oz | 0.107 mm prepreg | — |
| L4 (bottom) | Signal / GND pour | 0.5 oz | — | — |

**Why this stackup is the project default:** see
`hardware/comms/design/rf_layout_guidelines.md` "Use a 4-layer
stackup" section — solid L2 GND under L1 signals means you can't
accidentally split the ground plane under your critical traces, which
is the single biggest signal-integrity win available.

---

## 11. Setup procedure for a new board (checklist)

The first time you bring this doc into Altium for a new project:

- [ ] Create new PCB project + PcbDoc
- [ ] Run **JLCPCB stackup plugin** → confirms L1-L4 stack (§10)
- [ ] **In Layer Stack Manager → Impedance tab**, add the impedance profiles your board needs (e.g. `100R_DIFF_L1` for CSI / REFCLK / RF, `85R_DIFF_L1` for PCIe data, `90R_DIFF_L1` for USB 2.0, `50R_SE_L1` for RF microstrip). Altium's field solver populates W/G from the JLCPCB stackup automatically.
- [ ] `Design → Rules`:
  - [ ] Routing → Width: add `NET_SIG` (8 mil), `NET_PWR` (20 mil), `NET_PWR_HIGH` (50 mil), per §3
  - [ ] Routing → Routing Via Style: standard via 0.3 mm drill / 0.6 mm pad per §4
  - [ ] Electrical → Clearance: per §5 table — 8 mil between different nets, 10 mil pour-to-track
  - [ ] Manufacturing → Board Outline Clearance: 0.3 mm copper-to-edge
  - [ ] Manufacturing → Hole to Hole Clearance: 0.6 mm
  - [ ] Mask → Solder Mask Sliver: 0.127 mm
  - [ ] Mask → Solder Mask Expansion: 0.1 mm
  - [ ] (per-board) Routing → Differential Pairs Routing: scope to each board's DP class, **reference the Impedance Profile by name** (do NOT hardcode W/G — see §8 workflow note)
- [ ] Create Net Classes per §9 — drag nets in from the Net list
- [ ] **Export rules to `.RUL`** — `Design → Rules → right-click → Export Rules`
- [ ] **Commit the .RUL file** to repo at `hardware/conventions/jlcpcb_baseline.RUL`
- [ ] Run DRC with empty PCB to confirm rules don't trip false positives

Subsequent boards: skip everything except "run stackup plugin",
"import .RUL", and "create Net Classes". Less than 5 minutes.

---

## 12. When to deviate

The "Project default" column intentionally pads JLCPCB's minimums for
yield. **Deviate when**:

- **Going to JLCPCB's advanced process tier** (3.5 mil minimum) for a
  dense flight-critical board with components that can't otherwise
  be routed. Updates this doc with the new defaults.
- **A specific component requires tighter** — e.g., a 0.4 mm pitch
  BGA needs 4 mil traces minimum to escape. Local override the width
  rule with a higher-priority scoped rule; document the exception in
  the board's layout guide.
- **High-voltage clearance** required (>50 V working). Use IPC-2221
  Table 6-1 to determine required spacing; add a scoped clearance
  rule.

Don't deviate "to save space" — if the board is too dense for the
project defaults, the answer is almost always **a bigger board, not
tighter rules**.

---

## 13. References

- JLCPCB capabilities page: https://jlcpcb.com/capabilities/pcb-capabilities (verify current values; this doc reflects ~2026-05)
- `hardware/conventions/net_naming.md` — net naming convention used by the Net Classes in §9
- `hardware/comms/design/rf_layout_guidelines.md` — ground plane, via stitching, 0402 dogbone-vs-via-in-pad deep-dive
- `hardware/payload_compute/design/altium_payload_layout_guide.md` — payload-specific diff-pair classes (DP_CSI, DP_PCIE, DP_USB) and impedance target widths
- IPC-2221 — generic PCB design standard, used for current capacity + voltage clearance lookups
- Saturn PCB Toolkit (free) — useful for impedance, current capacity, via inductance calculations

---

## 14. Revision history

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | NG / CC | Initial draft. Captures JLCPCB standard-process minimums and project defaults for trace width, vias, clearances, holes, soldermask, silkscreen. Net Class starting set (NET_SIG, NET_PWR, NET_PWR_HIGH, NET_RF, NET_DIFF_*). Setup checklist for new boards. Stackup reference (JLC04161H-7628 4-layer 1.6 mm) cross-references the JLCPCB Altium plugin and the comms RF layout guide. |
| 0.2 | 2026-05-25 | NG / CC | Added project-wide **Impedance Profile workflow** recommendation to §8 — diff-pair widths should come from named profiles in the Layer Stack Manager (Altium 2D field solver against actual JLCPCB stackup), referenced by name in Differential Pair Routing rules, not hardcoded W/G values. Updated §11 new-board setup checklist to include profile creation as a pre-rules step. Cross-references payload layout guide §3.2 for the step-by-step walkthrough. |
