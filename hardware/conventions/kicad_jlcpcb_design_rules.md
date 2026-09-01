# KiCad Design Rules & Impedance — JLCPCB Constraints

**Scope:** every PCB migrated to or started in KiCad (comms transceiver
first). JLCPCB standard 4-layer 1.6 mm FR4 (`JLC04161H-7628`) unless stated
otherwise.
**Owner:** hardware lead.
**Status:** living document — update when JLCPCB changes stackups/capabilities.

This is the **KiCad companion** to
[`altium_jlcpcb_design_rules.md`](altium_jlcpcb_design_rules.md). Same target
numbers (that doc is the source of truth for the *values*); this doc is *where
they go in KiCad* and how to do controlled impedance without Altium's Impedance
Profiles. Read the Altium doc for the *why* behind each value.

---

## 0. Quick start (the morning refresher)

You want: JLCPCB 4-layer stackup set, plus certain traces forced to 50 Ω. In
Altium that was "run the plugin → add an Impedance Profile → rules apply it."
KiCad splits that into **stackup → calculator → net class**. The click-path:

1. **`File → Board Setup → Physical Stackup`** — set 4 layers / 1.6 mm, enter the
   `JLC04161H-7628` dielectric heights + εr (§2). KiCad has **no JLCPCB plugin**,
   so you type them.
2. **Get the 50 Ω width** — easiest is **JLCPCB's online impedance calculator**
   (jlcpcb.com/impedance): pick `JLC04161H-7628`, L1, 50 Ω → it gives the width.
   Should reproduce our **~0.358 mm** (§3). (KiCad's own calc: `Tools →
   Calculator Tools → Transmission Line`.)
3. **`Board Setup → Net Classes`** — make a class **`RF`**, set its **Track
   Width** to that value. Assign nets by pattern **`RF_*`** (§4). Our net-naming
   convention makes this one line.
4. **(Recommended) Custom rule** so DRC actually flags off-width RF traces (§5.3).
5. **Order:** tell JLCPCB "impedance controlled" at checkout — it's not in the
   Gerbers (§6).

That's the whole thing. Details below.

---

## 1. Altium → KiCad concept map

| What you did in Altium | KiCad equivalent |
|---|---|
| Run JLCPCB stackup plugin | `Board Setup → Physical Stackup`, enter values **by hand** (no plugin) |
| Layer Stack Manager → **Impedance Profile** (field solver → W/G) | **PCB Calculator → Transmission Line** tab, or JLCPCB's online impedance calc → W (manual, one-time) |
| Diff Pair Routing rule *references* the profile (live) | `Net Classes` → set Track Width / Diff Pair Width+Gap to the computed number (static) |
| Assign net to class → width applies | `Net Classes` → **net-name pattern** assignment (`RF_*` → `RF`) |
| Rule auto-recalcs if stackup changes, DRC flags off-target | **No live recalc** — recompute by hand if stackup changes; a **custom rule** (§5.3) gives you the DRC-flags-off-width behavior |
| Design → Rules (widths, clearances, vias…) | `Board Setup → Design Rules → Constraints` + per-class overrides in `Net Classes` |
| Export/import `.RUL` | Import a saved **`.kicad_dru`** (custom rules) + reuse a template `.kicad_pro`/net-class setup |

**The one real capability gap:** KiCad has no live impedance-profile ↔ stackup
binding. You compute the width once against the stackup and pin it into a net
class. If JLCPCB revises the stackup, nothing warns you — recompute manually.
The §5.3 custom rule is how you get DRC to at least flag traces that drift off
the width you chose.

---

## 2. Stackup — `Board Setup → Physical Stackup`

1. First set the layer count: `Board Setup → Board Editor Layers` → **4 copper
   layers**, board thickness **1.6 mm**.
2. `Board Setup → Physical Stackup` → enter `JLC04161H-7628` per-dielectric
   thickness, εr (Epsilon R), loss tangent, and copper weight.

**Get the live numbers from JLCPCB's stackup / impedance page** — they are the
authority and occasionally revise. The impedance-critical dimension is the
**L1 ↔ L2 prepreg** (the ground plane directly under your top-layer RF traces):

| Layer | Function | Copper | Dielectric below |
|---|---|---|---|
| L1 (top) | Signal / RF | ~0.5 oz | **prepreg 7628 ≈ 0.2 mm, εr ≈ 4.4** ← sets 50 Ω width |
| L2 (inner) | **Solid GND plane** | 0.5 oz | core (FR4) ~1.2 mm |
| L3 (inner) | Power islands / slow sig | 0.5 oz | prepreg |
| L4 (bottom) | Signal / GND pour | ~0.5 oz | — |

> **Note / reconcile:** the stackup name "7628" is the L1↔L2 prepreg glass style
> (~0.2 mm). Using h ≈ 0.2 mm, εr ≈ 4.4 reproduces the **0.358 mm** 50 Ω width we
> already validated in Altium. The Altium doc §10 table lists a thinner prepreg
> (3313 / 0.107 mm) — if those disagree, **trust JLCPCB's current stackup page**
> and fix whichever doc is stale. The width always follows from the *real*
> dielectric height, so match your fab stackup and recompute.

Keep **L2 a solid, unbroken GND plane** under all L1 RF traces — that's the
single biggest SI win (see `../comms/design/rf_layout_guidelines.md`).

---

## 3. 50 Ω trace width

Two ways to get the number; use whichever, they should agree within a few µm:

**A. JLCPCB online impedance calculator (recommended — their exact stackup).**
jlcpcb.com/impedance → choose `JLC04161H-7628` → layer **L1 (top, microstrip)**
→ target **50 Ω single-ended** → read off the width. This is exactly what the
Altium JLCPCB plugin did internally, so it's the most faithful to what gets
fabbed. Expected: **≈ 0.358 mm** with solder mask.

**B. KiCad built-in.** `Tools → Calculator Tools → Transmission Line` (or the
standalone **PCB Calculator** app):
- Model: **Microstrip** if the RF trace has ground only *below* (L2); **Grounded
  Coplanar Waveguide (GCPW)** if you also flood ground on both sides of the
  trace on L1 (common and preferable for RF — then the ground-gap matters too).
- Inputs: εr ≈ 4.4, substrate height h = L1→L2 prepreg (~0.2 mm), copper
  thickness t (0.5 oz ≈ 17.5 µm), Z0 = 50 Ω, freq ≈ 437 MHz → **solve for W**.
- Add solder-mask loading if the model supports it (drops W slightly).

For **diff pairs** (payload carrier: PCIe/USB/CSI), use the **coupled**
microstrip model to get width **and** gap, then enter both in the net class.

---

## 4. Net classes & assignment — `Board Setup → Net Classes`

Define classes with per-class Clearance / Track Width / Via Size / Diff Pair
Width+Gap, then assign nets by **pattern** (lower half of the Net Classes
dialog). Our [`net_naming.md`](net_naming.md) prefixes make assignment trivial:

| Net class | Pattern(s) | Track Width | Clearance | Notes |
|---|---|---|---|---|
| `Default` | (everything else) | 0.2 mm (8 mil) | 0.2 mm | digital signal default |
| `RF` | `RF_*`, `LO_*` | **0.358 mm** (50 Ω, from §3) | per RF layout guide | L1 only, solid GND under |
| `PWR` | `+3V3`, `+5V` | 0.5 mm (~20 mil) | 0.2 mm | low-current rails |
| `PWR_HIGH` | `VBAT`, high-current rails | 1.27 mm (50 mil) | 0.25 mm | outer layers only |
| `DIFF_*` | per board (`DP_CSI`, `DP_PCIE`, `DP_USB`) | per impedance target | per target | Diff Pair W+G fields |

Assignment example (Net Classes dialog → patterns): `RF_*` → `RF`. Because RF
nets are named `RF_TX_MMIC_OUT`, `RF_RX_LNA_OUT`, etc., that one pattern catches
them all. Verify membership in the **Net Inspector** (Appearance panel) or by
coloring nets by class.

---

## 5. Design rules — `Board Setup → Design Rules`

### 5.1 Constraints (global minimums) — mirror the Altium §2 cheat-sheet

| Constraint (KiCad Constraints page) | Value | Altium equiv |
|---|---|---|
| Minimum track width | 0.2 mm | 8 mil default |
| Minimum clearance | 0.2 mm | 8 mil |
| Minimum via diameter | 0.6 mm | 24 mil pad |
| Minimum via drill / hole | 0.3 mm | 12 mil |
| Minimum annular width | 0.15 mm | 6 mil/side |
| Minimum through-hole (PTH) | 0.3 mm | — |
| Hole to hole clearance | 0.6 mm | 0.6 mm |
| Copper to edge clearance | 0.3 mm | 12 mil |
| Copper to hole clearance | 0.25 mm | 10 mil |
| Silk min line width (Text & Graphics defaults) | 0.15 mm | 6 mil |
| Silk text height (refdes) | 0.8 mm; warnings 1.0 mm | 32 / 40 mil |
| Solder mask min web/sliver (Solder Mask/Paste page) | 0.127 mm | 5 mil |
| Solder mask expansion | 0.1 mm | 0.1 mm |

Full reasoning for every number: `altium_jlcpcb_design_rules.md` §3–§7. Values
are identical — only the dialog location differs.

### 5.2 Pre-defined track/via sizes
`Board Setup → Design Rules → Pre-defined Sizes` — add the RF width (0.358 mm)
and the power widths (0.5 / 1.27 mm) as pickable track sizes, and the standard
via (0.6 / 0.3 mm) so you can switch on the fly while routing.

### 5.3 Custom rule — enforce the 50 Ω width band (the Altium "scoped rule")
KiCad's **Custom Rules** (`Board Setup → Design Rules → Custom Rules`, saved to
`<board>.kicad_dru`) are the closest thing to Altium's scoped width rule and
give you **DRC-flags-off-width** behavior. Add:

```
(version 1)

(rule "RF 50ohm microstrip width"
  (condition "A.NetClass == 'RF'")
  (constraint track_width (min 0.35mm) (opt 0.358mm) (max 0.37mm)))
```

Now any `RF`-class trace routed outside 0.35–0.37 mm throws a DRC violation —
your safety net against fat-fingering the RF width. Adjust the band to whatever
the JLCPCB calc gives for the fabbed stackup. (Do the same per diff-pair class
with `diff_pair_gap` / `track_width` constraints if desired.)

---

## 6. Ordering controlled impedance at JLCPCB

Same as Altium — **impedance intent is NOT in the Gerbers.** At the JLCPCB order
page:
- Select the **impedance-controlled** option and specify stackup `JLC04161H-7628`.
- Tolerance ±10 % standard (±5 % costs more).
- Impedance **test report** ~$5–15/order: **skip for dev/v0.x runs, order for
  flight builds** (per Altium doc §8).
- 4-layer minimum for any controlled impedance (impossible to control on 2-layer).

Order controlled impedance for the **comms board** (50 Ω microstrip) and the
**payload carrier** (PCIe/USB/CSI diff pairs).

---

## 7. Reuse across boards (KiCad has no `.RUL` import)

KiCad doesn't have Altium's single `.RUL` export/import. To reuse:
- **Custom rules:** copy the `.kicad_dru` file into the next project (or keep a
  shared `jlcpcb_baseline.kicad_dru` in this folder and copy it in).
- **Constraints + net classes:** fastest is to **start new boards from a
  template `.kicad_pro`/`.kicad_pcb`** that already has the stackup, constraints,
  net classes, and pre-defined sizes set. Save one once the comms board is
  dialed in and reuse it.
- **Stackup:** re-enter (or copy the stackup section of the template board).

> **TODO (first board to finish rules):** save a
> `jlcpcb_baseline.kicad_dru` and a template project into
> `hardware/conventions/` so subsequent boards skip the setup.

---

## 8. New-board checklist (KiCad)

- [ ] `Board Editor Layers` → 4 layers, 1.6 mm
- [ ] `Physical Stackup` → enter `JLC04161H-7628` (verify against JLCPCB live page), solid L2 GND
- [ ] Get 50 Ω width (JLCPCB impedance calc or KiCad Transmission Line) → record it
- [ ] `Net Classes` → create `RF` / `PWR` / `PWR_HIGH` / `DIFF_*`, set widths (RF = the 50 Ω number)
- [ ] `Net Classes` patterns → `RF_*`→`RF`, `+3V3`/`+5V`→`PWR`, `VBAT`→`PWR_HIGH`
- [ ] `Design Rules → Constraints` → enter §5.1 minimums
- [ ] `Design Rules → Pre-defined Sizes` → RF/power widths + standard via
- [ ] `Design Rules → Custom Rules` → paste §5.3 RF-width rule (+ diff-pair if needed)
- [ ] Run DRC on empty board — confirm no false positives
- [ ] At order time: JLCPCB → impedance controlled, `JLC04161H-7628`, report for flight only

---

## 9. References

- [`altium_jlcpcb_design_rules.md`](altium_jlcpcb_design_rules.md) — source of truth for the *values* + the *why*; §8 impedance, §10 stackup
- [`net_naming.md`](net_naming.md) — the `RF_*` / `+3V3` / `VBAT` prefixes the net-class patterns key off
- [`../comms/design/rf_layout_guidelines.md`](../comms/design/rf_layout_guidelines.md) — ground plane, via stitching, GCPW vs microstrip, 0402 grounding
- JLCPCB impedance calculator + stackups: https://jlcpcb.com/impedance (authoritative; verify before each order)
- KiCad docs: Board Setup → Physical Stackup; Custom Design Rules (`.kicad_dru`) reference

---

## 10. Revision history

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-08-16 | NG / CC | Initial KiCad companion to the Altium design-rules doc. Altium→KiCad concept map; stackup via Physical Stackup; 50 Ω width via JLCPCB/KiCad calculators; net classes + `RF_*` pattern assignment; Constraints mirror of the Altium cheat-sheet; §5.3 custom `.kicad_dru` rule to enforce the 50 Ω width band (the DRC-flags-off-width safety net Altium's Impedance Profile gave for free); JLCPCB impedance-order notes; reuse-via-template guidance. Flags the L1↔L2 prepreg discrepancy vs Altium §10 to reconcile against JLCPCB's live stackup. |
