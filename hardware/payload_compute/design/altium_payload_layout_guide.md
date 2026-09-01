# Altium Layout Instructions — Payload Carrier (Jetson Orin Nano)

## Scope

This is the layout-side companion to [`altium_payload_schematic_guide.md`](altium_payload_schematic_guide.md).
The schematic guide tells you what to draw; this guide tells you how to
turn it into a manufacturable PCB.

**v0.1 scope of this document:** the differential-pair workflow. Other
layout topics (stackup, placement, power routing, copper pour, via
stitching, DRC, manufacturing output) are stubbed at the end and will
fill in as the layout progresses.

**Read the schematic guide first.** Layout decisions depend on which
sheet a signal lives on, what voltage domain it's in, and what its
sensitive neighbors are.

---

## 1. Differential Pair Layout

Differential pairs carry signals as a balanced P/N pair. They tolerate
common-mode noise far better than single-ended traces and are required
for any signal above ~250 MHz. Getting them right is the single most
important layout job on this board.

### 1.1 What we have to manage

| Net group | Pairs | Impedance | Pair count | Source / sink | Sheet (sch) |
|---|---|---|---|---|---|
| **MIPI CSI-2 (D-PHY)** | `CAM0_CLK`, `CAM0_D0`, `CAM0_D1` + same for `CAM1` and `CAM2` | **100 Ω diff** | 9 | Orin SO-DIMM → camera FFC (J10/J11/J12) | 2 |
| **PCIe Gen2 — data** | `M2_PETP0/N0` (TX), `M2_PERP0/N0` (RX) | **85 Ω diff** | 2 | Orin SO-DIMM ↔ M.2 socket (J40) | 4 |
| **PCIe Gen2 — REFCLK** | `M2_REFCLKP/N` | **100 Ω diff** | 1 | Orin SO-DIMM → J40 | 4 |
| **USB 2.0** | `USB0_D_P/N` (recovery), `USB1_D_P/N` (M.2 BT) | **90 Ω diff** | 2 | Orin SO-DIMM ↔ J50 / J40 | 1 / 4 |

**Total: 14 differential pairs.** Three different impedance targets
(85 / 90 / 100 Ω), three different routing-rule classes.

### 1.2 Tolerances — intra-pair and inter-pair length matching

| Net group | Intra-pair skew | Inter-pair skew | Max total length | Notes |
|---|---|---|---|---|
| MIPI CSI-2 (each camera) | ≤ 5 mil | Clock-vs-data pairs within one camera ≤ 50 mil | ~200 mm (D-PHY tolerates up to ~300 mm but keep tighter) | The 3 pairs per camera are a length-matched group |
| PCIe Gen2 data (TX, RX) | ≤ 5 mil | TX vs RX skew not tightly spec'd (separate links) | ~150 mm typical | TX needs AC caps near SO-DIMM (see schematic guide §9.5 / open item §10.9) |
| PCIe Gen2 REFCLK | ≤ 5 mil | REFCLK vs TX skew ≤ 50 mil within the M.2 link | ~150 mm | DC-coupled — no caps on carrier |
| USB 2.0 | ≤ 25 mil | n/a — only one pair per link | ~200 mm | 90 Ω diff per USB-IF; no length match between USB0 and USB1 |

"mil" = 0.001 inch = 25.4 µm. So "≤ 5 mil" = ~0.13 mm.

### 1.3 Critical layout note from the schematic side — CSI P/N swaps

Per [`payload_carrier_pinmap.md`](payload_carrier_pinmap.md) §3.3 and DG-10931 §10, the Orin module
has a **P/N polarity swap on `CSI0_D1` and `CSI1_D0`**. The schematic
compensates by routing module D1_P to FFC D1_N and vice versa. **The
swap lives in the schematic netlist, not in the layout.** When you
route these pairs, follow the netlist — don't try to "uncross" the
swap during routing. CSI2 has no swap.

---

## 2. PCB Stackup (sets impedance widths)

A 4-layer JLCPCB JLC04161H-7628 stackup (their default 1.6 mm 4-layer)
is the assumed baseline:

| Layer | Function | Copper | Dielectric below |
|---|---|---|---|
| L1 (top) | Signals (mostly diff pairs and power) | 0.5 oz (≈17.5 µm) | 0.107 mm prepreg → L2 GND |
| L2 (inner 1) | **Solid GND plane** — the reference for L1 diff pairs | 0.5 oz | 1.265 mm core → L3 |
| L3 (inner 2) | Power planes (split into `+3V3`, `+5V_ORIN`, etc. zones) | 0.5 oz | 0.107 mm prepreg → L4 |
| L4 (bottom) | Signals (low-speed) + GND pour for stitching | 0.5 oz | — |

**Why this stackup matters for diff pairs:** all critical diff pairs
(CSI, PCIe, USB) should be routed on **L1 with L2 GND as the
reference plane**. The L1→L2 dielectric thickness (0.107 mm) drives
the trace width needed to hit each impedance target.

**Stackup consistency across the project.** The comms board uses the
same JLCPCB JLC04161H-7628 stackup — see
[`hardware/comms/design/rf_layout_guidelines.md`](../../comms/design/rf_layout_guidelines.md) for the full
discussion of why 4-layer with a dedicated solid L2 GND is the right
default for every board, and [`altium_comms_schematic.md`](../../comms/design/altium_comms_schematic.md)
for layer-by-layer dielectric thicknesses and the Altium Layer Stack
Manager setup.

### 2.1 Diff-pair trace dimensions — let Altium compute them

**Don't hardcode widths in design rules.** Use Altium's **Impedance
Profiles** feature in the Layer Stack Manager (AD20 and later). You
define a named profile that says "this is what 85 Ω differential
on Top over L2 GND looks like," Altium runs its 2D field solver
against the actual JLCPCB-populated stackup, and the design rule
just references the profile by name.

Why this is strictly better than typing W/G values into a rule:

- **Stackup is the single source of truth.** If JLCPCB's stackup
  values change on a later order (different prepreg, different Dk,
  different copper weight), Altium auto-recalculates W/G for every
  profile and flags any existing route that no longer hits the
  target. With hardcoded widths, you'd have to manually update
  every rule and would silently miss one.
- **No external calculator needed.** JLCPCB's online impedance
  calculator becomes a sanity check, not the source of truth.
- **The Interactive Diff Pair Router uses the profile width
  automatically** when you route a pair scoped to that rule —
  no per-route fiddling.

Approximate widths/gaps that you should see Altium compute for the
JLC04161H-7628 stackup (L1 over L2 GND, 0.107 mm prepreg, Dk ≈ 4.3,
0.5 oz Cu). **These are sanity-check values, not values to type in:**

| Target impedance | Expected trace width (W) | Expected gap (G) | Used for |
|---|---|---|---|
| **85 Ω diff** | ~0.13 mm (5.1 mil) | ~0.10 mm (3.9 mil) | PCIe TX/RX |
| **90 Ω diff** | ~0.12 mm (4.7 mil) | ~0.10 mm (3.9 mil) | USB 2.0 |
| **100 Ω diff** | ~0.10 mm (3.9 mil) | ~0.10 mm (3.9 mil) | MIPI CSI, PCIe REFCLK |

If Altium's profile computes a width that differs from these by more
than ~20 %, **something is off in the stackup** — re-check the
Layer Stack Manager for the right dielectric and copper-weight values
(JLCPCB plugin should populate them; if it didn't, run the plugin
again).

For order-time impedance verification, JLCPCB will run a quote-time
impedance check if you order "controlled impedance" service (small
surcharge, ~$5–15, worth it for a flight-critical board; optional
for v0.1 dev runs).

---

## 3. Setting up Differential Pairs in Altium

Four places diff pairs need to be configured: **schematic** (defines
the P/N relationship), **Layer Stack Manager** (defines the impedance
profiles), **PCB editor** (groups pairs into classes and hosts the
routing rules), and **interactive router** (lets you draw both
traces simultaneously).

### 3.1 Define pairs in the schematic

For each P/N net pair on the schematic:

1. Make sure the net labels end in **`_P` and `_N`** (or `+` and `−`).
   The pinmap already follows this convention — `CAM0_CLK_P` /
   `CAM0_CLK_N`, `M2_PETP0` / `M2_PETN0`, `USB0_D_P` / `USB0_D_N`,
   etc. Altium auto-detects pairs from this suffix.
2. Place a **Differential Pair directive** on the pair:
   `Place → Directives → Differential Pair`
   Drop one directive on each of the two nets (or one straddling
   them). The pair is now recognised as a pair across the schematic.
3. Compile the project. Errors will fire if a directive is missing
   its partner or if the suffix doesn't match a `_N` / `_P` partner.

Alternative (bulk): use a **Blanket** with a Differential Pair
parameter:
`Place → Directives → Blanket`, draw over a region containing all
three CSI pairs for a camera, add `DiffPair = TRUE` parameter.
Saves clicks when you have 9 CSI pairs to mark.

### 3.2 Create Impedance Profiles in the Layer Stack Manager

This is the step that lets Altium compute trace widths for you
instead of you typing them into design rules.

1. Open `Design → Layer Stack Manager`.
2. Confirm the stackup is the JLCPCB JLC04161H-7628 4-layer 1.6 mm
   (the JLCPCB Altium plugin populates this — run the plugin first
   if you haven't).
3. Switch to the **Impedance** tab at the bottom of the Layer Stack
   Manager.
4. **Add three differential profiles** (one per impedance target on
   this board):

   | Profile name | Target Z₀ | Signal layer | Reference layer | Used for |
   |---|---|---|---|---|
   | `100R_DIFF_L1` | 100 Ω differential | L1 (Top) | L2 (GND) | MIPI CSI lanes, PCIe REFCLK |
   | `85R_DIFF_L1` | 85 Ω differential | L1 (Top) | L2 (GND) | PCIe TX, PCIe RX |
   | `90R_DIFF_L1` | 90 Ω differential | L1 (Top) | L2 (GND) | USB 2.0 |

5. For each profile, leave Altium's field solver to compute W and G.
   Verify the computed values match the §2.1 sanity-check table
   within ~20 %. If they don't, the stackup is misconfigured —
   re-run the JLCPCB plugin or check dielectric values.

6. Save the project. The profiles now appear by name in
   `Design → Rules → Differential Pairs Routing` rule scope.

**Why on L1 only:** all critical diff pairs on this board route on
L1 with L2 as reference. We don't route diff pairs on L4 (where
they'd reference back through L3 power plane — bad). If a future
board needs L4 diff pairs, add a parallel `*_DIFF_L4` profile then.

### 3.3 Confirm pairs in the PCB editor

After ECO-ing the schematic to the PCB:

`Design → Classes → Differential Pairs` should show every pair from
the schematic. If a pair is missing, the schematic directive didn't
take — fix in the schematic and re-ECO. **Don't add pairs only in the
PCB editor** — they'll drift out of sync with the schematic on the
next ECO pass.

### 3.4 Group pairs into classes (for batch rule application)

Create three **Differential Pair Classes** for organized rule
management:

| Class name | Members | Used for |
|---|---|---|
| `DP_CSI` | all 9 CAM*_CLK / CAM*_D0 / CAM*_D1 pairs | 100 Ω impedance rule, MIPI length match |
| `DP_PCIE` | M2_PET, M2_PER, M2_REFCLK pairs | 85/100 Ω rules + intra-pair 5 mil match |
| `DP_USB` | USB0_D, USB1_D pairs | 90 Ω rule, 25 mil intra-pair |

`Design → Classes → Differential Pair Classes → Add Class` — drag
members in. Then design rules below can target the class name
instead of listing every pair individually.

Also create a parallel set of **Net Classes** (for non-diff design
rules like clearance, via type):
- `NET_CSI` (all CSI nets including the P/N members)
- `NET_PCIE` (all PCIE1 nets + control signals)
- `NET_USB` (USB diff nets only)

---

## 4. Design Rules for Differential Pairs

Open `Design → Rules` (shortcut `D, R`). Diff-pair constraints split
across two branches of the rules tree:

| Constraint type | Rules-tree location | Used for |
|---|---|---|
| Impedance (W/G/coupling) | **Routing → Differential Pairs Routing** | Width, gap, max uncoupled length — references the Impedance Profile from §3.2 |
| Length matching (intra- and inter-pair skew) | **High Speed → Matched Lengths** | P-to-N match within a pair, and pair-to-pair match within a CSI bundle or PCIe link |
| Clearance to other nets | **Electrical → Clearance** (scoped to diff-pair classes) | 3× W separation from non-pair traces |

The `Routing → Differential Pairs Routing` rule does NOT have a
"Matched Length" sub-rule — earlier versions of this doc pointed
there, which was wrong. All length-matching rules belong under the
High Speed branch.

### 4.1 Differential Pair Routing — reference Impedance Profiles, not hardcoded W/G

`Routing → Differential Pairs Routing → Add new rule`

Create **one rule per impedance group**. Each rule references the
**Impedance Profile** you set up in §3.2 instead of hardcoded W/G
values — Altium pulls width and gap from the profile automatically.

In the rule dialog: under "Constraints", select **"Use Impedance
Profile"** and pick the profile name. The Width and Gap fields will
populate from the profile's field-solver output.

| Rule name | Scope | Impedance Profile | Layer constraint |
|---|---|---|---|
| `DP_CSI_100R` | `InDifferentialPairClass('DP_CSI')` | `100R_DIFF_L1` | Top layer only |
| `DP_PCIE_85R` | `InDifferentialPair('M2_PETP0') OR InDifferentialPair('M2_PERP0')` | `85R_DIFF_L1` | Top layer only |
| `DP_PCIE_100R` | `InDifferentialPair('M2_REFCLKP')` | `100R_DIFF_L1` | Top layer only |
| `DP_USB_90R` | `InDifferentialPairClass('DP_USB')` | `90R_DIFF_L1` | Top layer only |

The `100R_DIFF_L1` profile is shared between the CSI rule and the
PCIe REFCLK rule — same impedance target, same layer, same reference
plane, same field-solver result. No need to duplicate the profile.

**Why this is better than typing W/G:** if JLCPCB changes the
stackup (different prepreg, different copper weight) on a later
order, the profile auto-recomputes and every existing route gets
DRC-flagged if it no longer hits the target. With hardcoded W/G,
the rule would silently stay at the old width and you'd have to
remember to update it.

**Fallback if you're on pre-AD20 Altium** (no Impedance Profile
support): hardcode the width and gap from the §2.1 sanity-check
table. Verify against JLCPCB's online impedance calculator.

### 4.2 Intra-pair length match (P vs N within one pair)

`Design → Rules → High Speed → Matched Lengths`

The Matched Lengths rule enforces that **all nets matching its
scope** are within `Tolerance` of each other. To enforce P-vs-N
matching within each differential pair, scope a rule **per pair** —
the rule then has exactly two nets to match (the P and the N), so
it does the right thing.

Tolerances per net group (from §1.2):

| Net group | Per-pair tolerance |
|---|---|
| MIPI CSI (all 9 pairs) | **5 mil** |
| PCIe Gen2 (all 3 pairs) | **5 mil** |
| USB 2.0 (both pairs) | **25 mil** |

You can either:

**(a) One rule per pair** (verbose but explicit, 14 rules total for
this board):

| Rule name | Scope | Tolerance |
|---|---|---|
| `Intra_CAM0_CLK` | `InDifferentialPair('CAM0_CLK')` | 5 mil |
| `Intra_CAM0_D0` | `InDifferentialPair('CAM0_D0')` | 5 mil |
| `Intra_CAM0_D1` | `InDifferentialPair('CAM0_D1')` | 5 mil |
| … (same for CAM1, CAM2) … | | |
| `Intra_PCIE_TX` | `InDifferentialPair('M2_PET0')` | 5 mil |
| `Intra_PCIE_RX` | `InDifferentialPair('M2_PER0')` | 5 mil |
| `Intra_PCIE_REFCLK` | `InDifferentialPair('M2_REFCLK')` | 5 mil |
| `Intra_USB0` | `InDifferentialPair('USB0_D')` | 25 mil |
| `Intra_USB1` | `InDifferentialPair('USB1_D')` | 25 mil |

**(b) One rule per impedance group with a "groups of 2" interpretation**
(less verbose, 3 rules; relies on Altium's pair-aware matching):

| Rule name | Scope | Tolerance |
|---|---|---|
| `Intra_DP_CSI` | `InDifferentialPairClass('DP_CSI')` + Groups Mode = Pairs | 5 mil |
| `Intra_DP_PCIE` | `InDifferentialPairClass('DP_PCIE')` + Groups Mode = Pairs | 5 mil |
| `Intra_DP_USB` | `InDifferentialPairClass('DP_USB')` + Groups Mode = Pairs | 25 mil |

In modern Altium (AD22+), the Matched Lengths rule has a **"Groups"**
dropdown — set it to "Differential Pairs" and it matches each pair's
P and N to each other rather than matching all members of the class
to each other. If your Altium version supports this, (b) is far
cleaner. If you can't find that option (older versions), fall back
to (a).

When the rule violates, Altium flags the longer trace as needing
serpentine compensation. Use **Length Tuning**
(`Route → Interactive Length Tuning`, shortcut `U, R`) to add
serpentines exactly where you need them — see §5.4 below.

### 4.3 Inter-pair length match (CSI bundle / PCIe link)

`Design → Rules → High Speed → Matched Lengths`

Same rule type as §4.2, different scope and tolerance. To match the
**lengths of multiple pairs to each other** (e.g., the CSI CLK pair
+ D0 pair + D1 pair for one camera), you need a logical "signal
chain" that spans multiple pairs — Altium's **xSignal Classes**.

**Step 1 — create xSignal classes:**

`Design → xSignals → Create xSignals from Connected Nets` (or define
manually). Set up one class per CSI camera bundle plus one for the
PCIe link:

| xSignal class | Members | Why grouped |
|---|---|---|
| `xSig_CAM0` | CAM0_CLK_P, CAM0_CLK_N, CAM0_D0_P, CAM0_D0_N, CAM0_D1_P, CAM0_D1_N | CLK and data pairs in one camera must arrive together within the D-PHY skew budget |
| `xSig_CAM1` | (same shape, CAM1 nets) | Same reason, per camera |
| `xSig_CAM2` | (same shape, CAM2 nets) | Same |
| `xSig_PCIE` | M2_PETP0, M2_PETN0, M2_PERP0, M2_PERN0, M2_REFCLKP, M2_REFCLKN | PCIe TX, RX, and REFCLK in the same link |

**Step 2 — add a Matched Lengths rule per xSignal class:**

| Rule name | Scope | Tolerance |
|---|---|---|
| `Inter_CAM0` | `InxSignalClass('xSig_CAM0')` | **50 mil** |
| `Inter_CAM1` | `InxSignalClass('xSig_CAM1')` | **50 mil** |
| `Inter_CAM2` | `InxSignalClass('xSig_CAM2')` | **50 mil** |
| `Inter_PCIE` | `InxSignalClass('xSig_PCIE')` | **50 mil** |

Leave the Groups dropdown at "All Nets" for these — we want every
member of the xSignal class within 50 mil of every other member.

**USB 2.0 doesn't need inter-pair matching** — each USB port is a
separate link, no relationship between USB0 and USB1 lengths.

### 4.4 Rule priority

If a net is in the scope of multiple Matched Lengths rules (which
will happen — every CSI pair member is in both an intra-pair rule
*and* an inter-pair xSignal rule), Altium evaluates rules by
**priority**. Set:

- Intra-pair rules (§4.2) at **higher priority** (lower priority
  number, e.g. 1)
- Inter-pair rules (§4.3) at **lower priority** (higher priority
  number, e.g. 2)

This way the tighter intra-pair tolerance wins where it applies,
and the looser inter-pair tolerance applies across the bundle.

### 4.5 Clearance and isolation

Diff pairs need extra space from non-diff traces to avoid coupling
that breaks the impedance.

Standard rule of thumb: **diff-pair-to-other-trace gap ≥ 3 × W**
(where W is the trace width). For our 5 mil width that's a 15 mil
clearance — set this as a Clearance rule scoped to
`InDifferentialPairClass('DP_*')` vs `All`.

---

## 5. Routing Differential Pairs

### 5.1 Pre-routing checklist

Before you draw the first diff pair, confirm:
- [ ] Stackup is set up (`Design → Layer Stack Manager`) with L2 = solid GND, no splits
- [ ] **Impedance Profiles created** in Layer Stack Manager's Impedance tab (`100R_DIFF_L1`, `85R_DIFF_L1`, `90R_DIFF_L1` per §3.2) and their computed W/G values look sane vs the §2.1 reference table
- [ ] All diff pairs appear in `Design → Classes → Differential Pairs`
- [ ] Net classes and differential pair classes are populated
- [ ] Design rules from §4 are in place and pass DRC pre-flight (`Tools → Design Rule Check → Run`)
- [ ] Component placement is locked: SO-DIMM, M.2 socket, 3× FFC, USB recovery header, debug UART header

If placement is still moving, **don't route diff pairs yet** — you'll
have to rip them up.

### 5.2 The Interactive Differential Pair Router

Shortcut: **`U, M`** (or `Route → Interactive Differential Pair Routing`).

The router draws both P and N traces in lockstep. Click on either
member of a pair to start; the router automatically picks up the
matched-width / matched-gap settings from the design rule scoped to
that pair.

Useful in-routing shortcuts (while the router is active):
- **Tab** — open the pair properties dialog mid-route to override
  width/gap for that segment
- **Shift + W** — toggle width from the rule's preferred to its alt
  value (rare; only if you defined alts)
- **Shift + Space** — cycle through corner styles (45°, 90°, arc)
- **`/`** — toggle the layer you're routing on (if you defined the
  rule to allow multiple layers — usually you don't for diff pairs)

### 5.3 Routing order

Route in this order to keep critical paths shortest and most direct:

1. **PCIe Gen2** (highest signal speed: 5 GT/s on each TX/RX pair).
   Route these first while the rest of the board is still empty.
   Get TX, RX, and REFCLK on the same layer (L1) with no via
   transitions if possible. Match lengths within the 50 mil window
   per §4.3.
2. **MIPI CSI-2** for each camera. Route one camera at a time —
   keep its 3 pairs (CLK + D0 + D1) together as a bundle. Match
   the 3 pairs within 50 mil per `xSig_CAM*`. **Don't try to
   length-match across cameras** — each camera is a separate D-PHY
   link.
3. **USB 2.0** (USB0 to J50 recovery header, USB1 to J40 M.2 BT).
   Lowest priority — USB 2.0 is forgiving.
4. **Single-ended high-speed signals** (PCIe control: PERST, CLKREQ,
   WAKE; CSI auxiliary: PWDN, mux RST).
5. **Power** (`+5V_ORIN`, `+3V3`, `+1V8_MOD`) — use copper pour /
   wide traces, not narrow routes.
6. **Slow control** (I²C, UART, GPIO, status LEDs) — leftover space.

### 5.4 Length tuning (serpentines / accordions)

When `DP_*_intra` or `Matched Lengths` rules show violations:

`Route → Interactive Length Tuning` (shortcut `U, R`).

Click the trace you want to lengthen. Altium adds serpentines
("accordion" pattern) on the trace until it matches the longer
partner. Visual feedback: a moving target gauge shows current
vs goal length.

**Best practices for serpentines:**
- Place them on the **shorter** trace (you can only add length, not
  remove it)
- Keep serpentine amplitude small — peaks should not get closer than
  **3 × trace width** to the other half of the pair (or to nearby
  traces)
- Add serpentines **near the source** when possible — adding them
  near a high-speed sink (like the M.2 socket) can degrade signal
  integrity
- For CSI clock pairs, add serpentines on the DATA pairs to match the
  clock, not vice versa — keeping the clock path as short and clean
  as possible matters most

### 5.5 Reference plane rules — and why they matter

**The physics in one sentence:** every diff-pair trace on L1 has an
invisible mirror-image return current flowing directly underneath it
on L2 GND, concentrated within ~3× the dielectric thickness. If the
return current has to detour around a slot, anti-pad bridge, or plane
split, the resulting loop becomes an antenna at exactly the
frequencies you're sending down the trace (and an EMI radiator into
the rest of the board). For our PCIe Gen2 at 5 GT/s, that's a
~2.5 GHz radiator. Avoid.

[`hardware/comms/design/rf_layout_guidelines.md`](../../comms/design/rf_layout_guidelines.md) covers this at depth
under "The core rule" and "What NOT to do" — it's written for the
comms RF chain but the physics is identical for high-speed digital
diff pairs. Read those two sections before you start routing.

**Concrete rules for this board:**

1. **L2 GND plane must be continuous under every diff-pair route.**
   No splits, no slot antennas, no anti-pads that interrupt the
   return current path. If you absolutely have to cross a power
   plane split (rare with our stackup since power is on L3, not L2),
   bridge the gap with a **stitching capacitor** (typically 100 nF
   0402, GND to the power island).
2. **Don't route across plane changes.** If you have to switch
   layers (e.g., L1 → L4), place a **return via pair** (two GND vias
   adjacent to the signal via pair) so the return current has a path
   from L2 to L4 GND pour right where the signal makes the layer
   transition.
3. **No diff-pair routing under tall components** like the SO-DIMM
   socket body or the M.2 connector body — keeps the EM environment
   stable.
4. **Stay away from board edges.** Keep diff pairs at least **5 × W**
   (~25 mil for our typical widths) from the board edge to maintain
   the impedance environment.
5. **Do NOT split analog/digital ground.** Single solid L2 GND
   outperforms split grounds at every frequency above ~1 MHz. The
   comms RF guide hammers this point — it's just as true for our
   high-speed digital design. There is no `AGND` net on this board,
   and there shouldn't be one.

### 5.6 Common pitfalls

- **Forgetting the P/N swap on CSI0_D1 and CSI1_D0.** The schematic
  handles it; trust the netlist. Don't try to physically uncross.
- **Routing a diff pair with a via on only one side of the pair.**
  Vias have to be matched — if you via-down the P trace, you must
  via-down the N trace within ~10 mil.
- **90° corners.** Use **45° corners** or **arcs** instead; 90°
  corners cause impedance discontinuities at multi-GHz.
- **Tee-off stubs.** If you have to branch a diff pair (very rare —
  AC caps don't count), the stub length should be < 100 mil.
- **AC caps on PCIe TX:** must be **on the host TX side, near the
  SO-DIMM**, NOT near the M.2 socket. See pinmap §10.9 resolution.

### 5.7 Decoupling and bypass cap placement

This isn't a diff-pair rule per se, but our diff-pair signal integrity
depends on clean rails feeding the SO-DIMM, the M.2 socket, and every
IC. Two principles to follow:

**Principle 1 — cap goes between the IC pin and the GND via, in that
order.** The via that returns current to L2 GND should be on the
**far side of the cap from the IC**, not on the near side. This
shortens the high-frequency return loop:

```
GOOD (return loop is small):

   IC.VCC ── trace ── [bypass cap] ── via ── L2 GND ── (loop returns through plane)
                                       │
                                       ▼
                                    L2 GND plane

BAD (return loop has to detour around the cap):

   IC.VCC ── trace ── via ── [bypass cap] ── trace ── via ── L2 GND
                       │                                       │
                       ▼                                       ▼
                    L2 GND plane                            L2 GND plane
```

**Principle 2 — for 0402 GND-side legs, use a dogbone fanout, NOT
via-in-pad.** This is a manufacturing constraint, not a signal-
integrity one. JLCPCB's standard via is 0.3 mm drill / 0.5 mm pad —
larger than a 0402 component's ~0.55 mm wide pad. Via-in-pad on a
0402 causes:

- **Tombstoning** during reflow (via sinks heat into L2, one end of
  the cap melts solder slower, surface tension lifts the component)
- **Solder theft** (capillary action pulls molten solder down through
  the via)

The fix is a short ~0.3–0.4 mm trace from the GND pad to a via:

```
GOOD for 0402 (short dogbone):

  IC pin ── [0402 cap] ── 0.3–0.4 mm trace ── via ── L2 GND
                                                │
                                                ▼
                                             L2 GND plane

BAD for 0402 (via-in-pad):

  IC pin ── [0402 cap]
              │   │         ← via in the pad causes tombstoning
              ▼   ▼            and solder theft during JLCPCB reflow
           L2 GND plane
```

For **larger packages (0805, 1206, SOT-583 GND pin, MMIC GND pads)**,
via-in-pad is fine — the pad is large enough that solder still wets
properly. For our board:

| Cap location | Package | Pattern |
|---|---|---|
| SO-DIMM VDD_IN decoupling (C20/21 bulk polymer D-case) | D-case | Via under each pad OK — pads are large |
| SO-DIMM VDD_IN mid-freq (C22–C26 10 µF X7R 0805) | 0805 | Via under each GND pad OK |
| SO-DIMM VDD_IN HF (C27–C36 100 nF 0402) | **0402** | **Dogbone — short trace then via** |
| M.2 socket VCC decoupling (C92–C96) | 1210 + 0402 | Bulk = via under pad; HF 0402 = dogbone |
| IC bypass caps (C50, C70, C100, C101, C45) | 0402 | **All dogbone** |
| TPS62933F input cap C11 (100 nF 0402) | 0402 | Dogbone, but keep the total loop <2 mm — this is the most layout-critical cap on the board (per schematic guide §1.B note) |

**Note:** the comms RF guide ([`rf_layout_guidelines.md`](../../comms/design/rf_layout_guidelines.md) §"Shunt
component grounding") covers this in much more depth, including the
multi-via grounding rules for MMIC / LNA pads. Our payload doesn't
have those exposed-pad RF parts, but the dogbone principle for 0402
is identical and the cheat-sheet there is worth reading.

---

## 6. Verification

After routing all diff pairs:

1. **`PCB → Reports → Differential Pair Length Report`** — gives you
   intra-pair skew for every pair. Anything red is a DRC violation.
2. **`Tools → Design Rule Check → Run`** with full ruleset. Filter
   for `Differential` and `Length` violations.
3. **xSignal length report** under `Design → xSignals → xSignals
   Report` — verifies the inter-pair grouping for CSI bundles and
   the PCIe link.
4. Visual check: for each pair, walk the trace from source to sink
   and confirm no reference-plane discontinuities, no via mismatches,
   no serpentines too close to other signals.

---

## 7. Layout topics — TBD (stubs for future revs)

The following sections will be filled in as the layout progresses.
Listed here so the doc structure is set and nothing gets forgotten.

- **7.1 PCB stackup decision and confirmation** (we've assumed JLC04161H-7628 in §2; verify against JLCPCB's current default 4-layer 1.6 mm process)
- **7.2 Mechanical setup**: board outline matching the CSKB stack template, M2.5 mounting holes (and the M.2 standoff hole), CSKB H1/H2 connector placement
- **7.3 Component placement strategy**: SO-DIMM in the centre, M.2 socket footprint, FFC connectors at board edges for camera ribbon routing, CSKB connectors on the +Z and −Z edges
- **7.4 Power routing and copper pours**: `+5V_ORIN`, `+3V3`, `+1V8_MOD`, polygon pour rules, thermal relief
- **7.5 Via stitching**: GND stitching density around RF-sensitive regions and along board edges
- **7.6 Decoupling cap placement**: SO-DIMM VDD_IN caps (per DG-10931 §6 distribution), per-IC bypass caps, bulk caps near power entry
- **7.7 Antenna pigtail routing**: 50 Ω-controlled u.FL → MMCX/SMA routing from the M.2 socket card edge to the chassis bulkhead
- **7.8 DRC + manufacturing output**: full DRC clean criteria, gerber generation, JLCPCB-specific output requirements, fab notes, pick-and-place + BOM CSV
- **7.9 Layer assignment summary**: final per-net layer choices (which nets ended up on L1 vs L4, where vias landed)

---

## 8. References

- [`payload_carrier_pinmap.md`](payload_carrier_pinmap.md) — canonical pin allocation; the diff-pair list in §1.1 above is sourced from here
- [`altium_payload_schematic_guide.md`](altium_payload_schematic_guide.md) — schematic-side conventions (net naming, sheet structure, component refdes)
- [`hardware/conventions/net_naming.md`](../../conventions/net_naming.md) — project-wide net naming convention (`_P`/`_N` suffix is required for diff pairs)
- **[`hardware/comms/design/rf_layout_guidelines.md`](../../comms/design/rf_layout_guidelines.md)** — written for the comms RF chain, but the sections on **return current physics**, **never splitting the ground plane**, **via stitching at frequency-dependent spacing**, and the **0402 dogbone vs via-in-pad** discussion are directly applicable to our high-speed digital diff pairs and decoupling caps. Read it. Specifically:
  - "The core rule" (return currents and why ground splits are slot antennas) — applies verbatim to our diff pairs
  - "What NOT to do" (no split grounds, no star ground) — same physics for our digital signals
  - "Shunt component grounding" + the package-size cheat-sheet — same dogbone rule for our 0402 bypass caps
- NVIDIA Jetson Orin NX/Nano Design Guide (DG-10931) — §7 PCIe layout, §10 MIPI CSI layout, §7.1 USB layout
- MIPI Alliance D-PHY Specification v2.5 — for CSI layout deep-dive (not needed for this design, but the reference)
- PCIe CEM Specification — for PCIe routing rules deep-dive

---

## 9. Revision History

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-24 | NG / CC | Initial draft. Focused on the differential-pair workflow (§1–§6) since that's where the user is starting layout work. Catalogs all 14 diff pairs from the schematic, gives target impedances + length-match tolerances, walks through Altium setup (schematic directives, PCB classes, design rules, interactive routing, length tuning, verification). Other layout topics (§7) stubbed for fill-in as the layout progresses. Cross-references [`hardware/comms/design/rf_layout_guidelines.md`](../../comms/design/rf_layout_guidelines.md) for the return-current physics + 0402 dogbone-grounding deep-dive (the RF guide's physics applies directly to our high-speed digital diff pairs and 0402 decoupling caps). Added §5.7 on decoupling/bypass cap placement (cap-then-via order, dogbone for 0402 GND-side legs) since clean rails are what feed the diff-pair signal integrity. |
| 0.2 | 2026-05-25 | NG / CC | **Switched diff-pair width spec from hardcoded W/G to Altium Impedance Profiles.** Added new §3.2 walking through profile creation in the Layer Stack Manager (`100R_DIFF_L1`, `85R_DIFF_L1`, `90R_DIFF_L1`). Rewrote §4.1 to reference profiles by name in the design rules instead of typing W/G values — Altium's 2D field solver computes the exact widths from the actual JLCPCB-populated stackup. §2.1 demoted from "source of truth" to "sanity-check table" (if the profile's computed W differs by >20 % from these values, the stackup is misconfigured). §5.1 pre-routing checklist now includes "Impedance Profiles created". Includes a fallback note for pre-AD20 Altium users who don't have profile support. |
| 0.3 | 2026-05-25 | NG / CC | **Fixed wrong rule path for length matching.** §4.2 originally pointed to `Routing → Differential Pairs Routing → Matched Length` — that sub-rule doesn't exist. Length matching (both intra-pair and inter-pair) lives in **`High Speed → Matched Lengths`**, with `Routing → Differential Pairs Routing` reserved for width/gap/impedance only. Restructured §4: added an intro table explaining the rules-tree split (Routing branch vs High Speed branch). Rewrote §4.2 (intra-pair) with two valid approaches — per-pair rules (verbose, always works) and per-class with Groups=Pairs (AD22+ only, cleaner). Rewrote §4.3 (inter-pair) with explicit `High Speed → Matched Lengths` path and xSignal class workflow. Added new §4.4 on rule priority (intra rules higher priority than inter so the tighter tolerance wins on the overlap). Renumbered old §4.4 Clearance to §4.5. |
