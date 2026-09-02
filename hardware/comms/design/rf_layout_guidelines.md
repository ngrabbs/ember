# RF Layout Guidelines — Comms Board

Short reference for the ground plane, via stitching, and stackup
decisions when laying out the comms board (and similar VHF/UHF mixed-
signal PCBs). Read this before starting layout, re-read it when the
board feels too crowded to keep ground solid.

---

## The core rule

> **No slot, no antipad bridge, no break in the ground plane may cross
> under any RF trace.**

The reason is **return currents**. At RF, return current doesn't take
the shortest physical path — it takes the path of least *inductance*,
which means it flows directly underneath the signal trace, concentrated
within ~3× the dielectric thickness of the trace. Picture an invisible
mirror-image current following every RF trace on the layer below.

If the return current has to detour around an opening, the resulting
loop is an antenna at exactly the frequency you're trying to keep on
the board. Slot in ground under a 437 MHz trace = 437 MHz radiator.

The rule is narrower than "ground plane never breaks anywhere." A slot
in an unused corner is fine. A slot crossing under your CLK0 trace is
a problem.

---

## Use a 4-layer stackup — it makes the headache go away

```
Layer 1 (top)    — Components + signals (RF on top, kept short)
Layer 2          — SOLID GROUND, edge to edge, nothing else
Layer 3          — Power distribution (+3V3, +5V islands OK here)
                   + slow signals
Layer 4 (bottom) — More signals (digital control, I2C, longer routes)
```

With layer 2 dedicated to ground, you literally never have to break
it. All signals on layers 1, 3, and 4 see continuous ground beneath
them. The "hard to keep unbroken" problem only really shows up on
2-layer boards where you're forced to choose between routing a signal
and having ground.

If forced onto 2 layers: every gap in the ground pour becomes a
hazard, and the rule becomes "make everything you can a ground pour,
and never let any signal cross the gaps." Much harder.

> **For the comms board specifically:** the realized stackup is JLCPCB
> `JLC04161H-7628` (1.6 mm, FR4). Full layer thicknesses and dielectric
> values are in
> [`../../conventions/kicad_jlcpcb_design_rules.md`](../../conventions/kicad_jlcpcb_design_rules.md)
> §2. The 50 Ω microstrip width is **0.358 mm**, confirmed against
> jlcpcb.com/impedance (14.12 mil, L1→L2, single-ended, non-coplanar).

---

## Microstrip, not coplanar — and what that costs you

**Decision (2026-09-02): the RF traces on this board are plain microstrip.**
Ground below on L2, and the L1 ground pour is held *back* from RF traces.

This is a real choice, not a default, because the two geometries need
different trace widths for the same 50 Ω:

| Geometry | What it is | 50 Ω width here |
|---|---|---|
| **Microstrip** (chosen) | Ground only below, on L2. Nothing alongside on L1. | **0.358 mm** |
| Grounded coplanar (GCPW) | Ground below *and* poured either side on L1, at a controlled gap | narrower — depends on the gap |

The trap: this document tells you elsewhere to pour ground on L1 and stitch
it down. If that pour comes up close alongside an RF trace, the trace stops
being microstrip and becomes GCPW whether you meant it or not — and at
0.358 mm its impedance lands **below** 50 Ω. How far below depends entirely
on the gap, which is why an uncontrolled pour beside RF is the worst of the
three options.

### The rule

**Keep the L1 ground pour at least 3 × trace width — 1.1 mm — back from any
RF trace.** At that distance the coplanar contribution is small enough to
ignore and the microstrip number holds.

Everywhere else on L1, pour and stitch normally; the standoff applies only
alongside RF nets.

### Enforcing it

Two options, in order of preference:

1. **Zone clearance.** Set the L1 ground zone's own clearance to 1.1 mm.
   Simple, and it applies to everything the pour approaches. Slightly
   conservative for non-RF nets, which costs nothing on a board this size.
2. **A custom rule** in `transceiver.kicad_dru` scoped to the RF class, if
   you want the standoff only where it matters. Test it with DRC before
   relying on it — a malformed rule makes KiCad silently drop the whole
   rules file.

Do **not** raise the `RF` net-class clearance to 1.1 mm to achieve this. That
would also force 1.1 mm between RF traces and the pads they connect to, which
is unroutable through the filters and the mixer.

### If you ever switch to GCPW

Recompute the width on jlcpcb.com/impedance with the coplanar option and a
chosen gap, then update **both** the `RF` net class width and the width band
in `transceiver.kicad_dru`. They have to move together — the `.dru` rule is
what stops a stale width from shipping.

---

## Via stitching vs via fence — two different tools

### Via stitching

Vias every ~5 mm that tie the **top-layer ground pour** to the **bottom-
layer (or layer-2) ground plane** throughout the RF region. Keeps the
top pour at the same potential as the inner plane, prevents resonant
cavities between layers.

Spacing rule: ≤ λ/20 at the highest frequency you care about.
- At 437 MHz in FR4 (εr ≈ 4.3): λ ≈ 330 mm in air, ~160 mm in FR4 →
  **stitch every ~5–8 mm**
- At 145 MHz: looser, ~15 mm acceptable, but keep at 5 mm for
  consistency

### Via fence

A closely-spaced row of vias forming a "wall" around the perimeter of
an RF section. Purpose is **isolation** — keeping one RF zone's signal
out of another.

Spacing rule: ≤ λ/10 at the highest frequency to be isolated.
- At 437 MHz in FR4: **vias every ~15 mm or tighter** for a real fence

For the board you want **both**:
- Stitching throughout each RF zone (general ground integrity)
- Fences at zone boundaries (isolation)

---

## What NOT to do

Common bad advice you might hear:

1. **"Split ground into analog and digital."**
   1980s audio-frequency wisdom, actively harmful at RF. The seam
   between two grounds becomes a high-impedance discontinuity. Return
   currents have to detour, creating loops; the seam itself becomes a
   slot antenna. A single solid well-stitched ground outperforms split
   grounds at any frequency above ~1 MHz. Don't do it.

2. **"Star ground / single-point connection."**
   Same problem. Made sense at audio frequencies with point-to-point
   wiring; doesn't apply to multilayer PCB design at RF.

3. **"Cut a slot under the SPI to isolate it from the RF."**
   The slot becomes a coupling antenna — the exact opposite of
   isolation. Route SPI well away from RF zones on a different layer
   and let the ground plane stay solid.

---

## Practical layout sequence for the comms board

1. **Place RF components first**, in two distinct zones:
   - **TX chain:** XOR → tripler → pre-MMIC BPF → ADL5602 → output BPF → TX SMA
   - **RX chain:** RX SMA → 2m BPF → PSA4 LNA → LO LPF + ADE-1+ → IF term → Sallen-Key
2. Pour ground on the top layer **around** RF components (not under
   them — *around* them, filling the gaps between traces)
3. Dedicate layer 2 as solid ground, edge to edge, no breaks anywhere
4. Add via **stitching** in both RF zones, ~5 mm spacing
5. Add a via **fence** between the TX and RX zones — this is the most
   important fence. Your own 437 MHz TX is the strongest signal your
   RX will ever see. Without isolation, the receiver desensitizes.
6. Add a via fence around the Si5351A to keep clock-edge harmonics
   from radiating across the board
7. Route SPI / I2C / USB / status LEDs on the bottom layer, well
   clear of RF zones
8. Power distribution on layer 3 — separate +3V3 and +5V pours are
   fine here, as long as layer 2 ground stays solid

---

## Component-level reminders that interact with the layout

- **SMA edge launches:** ground the connector body to the top pour
  *and* stitch down to layer 2 with at least 4 vias right at the
  launch point. Cheapest place to leak signal is at the connector.
- **MMIC, LNA, mixer ground pads:** stitch the chip's ground pad
  directly to layer 2 with multiple vias (not just one). The ADL5602
  and PSA4-5043+ both depend on a low-inductance ground for stability.
- **ADE-1+ ground pads (pins 1, 4, 5 plus tab):** all three GND pads
  get vias to layer 2. Don't share ground via with the IF return path.
- **Bypass caps:** placed *between* the IC pin and a via to ground
  plane. The via goes between the cap and the IC, not on the far side
  of the cap. Shortens return loop.
- **RF trace impedance:** all RF traces are 50 Ω microstrip (controlled
  width on layer 1 referenced to layer 2 ground). On this board's
  `JLC04161H-7628` stackup — 0.2104 mm prepreg to L2, εr 4.4 — that is
  **0.358 mm**. Keep the L1 ground pour 1.1 mm back so it stays microstrip
  rather than becoming coplanar.

---

## Shunt component grounding — why the GND-side leg matters

This deserves its own treatment because it's one of the most common
ways a well-designed BPF ends up off-frequency on the bench.

### The misconception

When you set up a `Net Class = RF` Width rule, it applies to the **RF
signal-side** of every shunt component (the leg that connects to the
50 Ω signal node). The **ground-side** leg is on the `GND` net, not
an RF net, so the RF width rule does not apply to it. You don't need
to add anything to the RF class for those grounds — and you wouldn't
want to.

### What actually matters: length, not width

The ground-side leg of a shunt component (BPF shunt L or C, MMIC GND
pad, bypass cap GND pad) carries the same RF current as the signal
side — Kirchhoff. The reason it's "GND" not "RF" is just naming.

Any trace length between the component's GND pad and a via stitching
it down to L2 adds **series inductance** that is effectively in
series with the shunt element itself. For a 6.8 pF BPF cap, even
~1 nH of via/lead inductance shifts the resonator's center
frequency noticeably. You spend your VNA tuning time chasing this
parasitic instead of designing the filter.

**The leg's width does not save you from this — only its length.**
A 0.358 mm wide leg with 2 mm of length has nearly the same
inductance as a 0.2 mm wide leg of the same length. The fix is to
make the leg zero length.

### The right pattern depends on package size

For **larger pads** (0805+, MMIC ground pads, SMA tabs), a via right
under the pad works perfectly:

```
GOOD (via under the GND pad of a large component):

  RF trace ── [0805 or MMIC pad] ── (via stitched directly here)
                                       │
                                       ▼
                                    L2 GND plane

BETTER (multiple parallel vias to lower via-inductance):

  RF trace ── [MMIC GND pad] ── (3 vias clustered at the pad)
                                  │││
                                  ▼▼▼
                               L2 GND plane
```

For **0402 components**, via-in-pad causes tombstoning and solder
theft (see next subsection). Use a **short dogbone fanout** instead:

```
GOOD for 0402 (short trace, then via):

  RF trace ── [0402 pad] ─── 0.3–0.4 mm trace ─── via ─── L2
                                                   │
                                                   ▼
                                                L2 GND plane

BAD (any longer leg, regardless of size):

  RF trace ── [shunt L or C] ────── trace ────── via ─── L2
                                                  ↑
                                       This length is parasitic
                                       inductance that detunes
                                       the filter
```

### Why 0402 needs special handling

0402 pads are ~0.55 mm wide. A standard JLCPCB via is 0.3 mm drill /
0.5 mm pad. Dropping that via directly under the component pad leaves
~0.025 mm of solder area on each side — not enough for the solder to
wet the pad properly. Three consequences:

1. **Tombstoning** — the via creates a heat sink into L2, making the
   GND-side pad heat slower than the RF-side pad during reflow.
   The lighter pad melts solder first and surface tension lifts the
   component up onto that end. Common failure mode for 0402 with
   via-in-pad on hobbyist reflow profiles.
2. **Solder theft** — capillary action pulls molten solder down
   through the via during reflow, starving the joint. Weaker mechanical
   bond, potentially open.
3. **Fab-process workarounds cost extra** — JLCPCB's POFV (Plated
   Over Filled Via) solves both problems but adds ~$3–5/order. Reasonable
   for a flight build, annoying for prototypes.

The 0.3–0.4 mm dogbone trace adds ~0.5 nH of parasitic inductance
(trace + via combined). On a 437 MHz BPF with 20 nH shunt inductors,
that's a ~1.25 % downward shift in resonant frequency — ~5 MHz at
437 MHz. Easily tuned in during bring-up with the VNA; not a
showstopper.

### Package-size cheat-sheet for via-at-GND-pad

| Package | Via-in-pad? | Notes |
|---|---|---|
| 0201 | Never | Component smaller than via pad |
| **0402** | **No — use dogbone** | Tombstoning + solder theft severe |
| 0603 | Marginal; OK with tenting | Tighter margin; still some tombstoning risk |
| 0805 | Yes | Pad large enough; minimal risk |
| 1206+ | Yes | Plenty of margin |
| MMIC / LNA GND tabs | **Yes, multiple vias required** | IC datasheets specify this |
| SMA edge-launch GND tabs | Yes, 4+ vias | Standard practice |

### Practical Altium technique

For **0402 BPF shunts**:
1. Place the component
2. Add a short trace (0.3–0.4 mm long, ~0.5 mm wide) from the GND
   pad outward
3. Drop a via at the trace endpoint (`P, V`)
4. Verify via net is `GND`

For **MMIC, LNA, SMA, 0805+ GND pads**:
1. Place the component
2. **Immediately drop a via on the GND pad** — `P, V` and click the pad
3. Verify via net is `GND`
4. If pad geometry allows, **fan out with 2–4 vias** clustered at
   the pad — parallel vias reduce ground inductance roughly as 1/N

### Multi-via grounding cheat-sheet (when to splurge on extra vias)

| Component | Vias at GND pad | Why |
|---|---|---|
| BPF shunt cap (RF resonator) | 1–2 | One usually adequate; 2 if there's pad space |
| BPF shunt inductor | 1–2 | Same as above |
| Decoupling cap on a slow IC | 1 | The IC is slow, parasitic L barely matters |
| Decoupling cap on a fast IC (Si5351A, MMIC bias) | 2–3 | Switching/RF current return path; minimize inductance |
| MMIC / LNA ground pad | 4+ | These chips depend on ultra-low-Z ground for stability — a poorly-grounded MMIC can oscillate. Use as many vias as the pad allows. |
| ADE-1+ GND pads (pins 1, 4, 5 + tab) | 2 each, plus separate vias under the tab | Don't share vias between pins; each GND pin should have its own via path |
| SMA connector body ground | 4+ | The launch is where signal integrity first goes wrong if it goes wrong |

### Why this isn't an RF-rule problem

Because the inductance penalty depends on length, not width, you
cannot fix this with a Width rule no matter how it's scoped. The
solution lives in **placement and via fanout discipline**, not in
the rules system. The rules give you correct 50 Ω microstrip on
the signal side; you give the GND side correct vias by hand.

---

## Quick-reference cheatsheet

| Question | Answer |
|---|---|
| Ground plane unbroken across the whole board? | Layer 2 yes. Top layer pour: yes within RF zones, fine to have gaps elsewhere. |
| Slot in ground OK? | Only if no RF trace passes within ~3× dielectric thickness of it |
| Stitching via spacing | ≤ λ/20 at highest freq, ~5 mm at 437 MHz |
| Via fence spacing | ≤ λ/10 at the freq you're isolating, ~15 mm at 437 MHz |
| Split analog/digital ground? | **No** — single solid plane |
| Where do bypass caps go? | Between IC pin and ground via |
| Where does the GND-side via of a 0402 shunt go? | **Dogbone — short 0.3–0.4 mm trace then via.** Via-in-pad causes tombstoning + solder theft on 0402. |
| Where does the GND via of a MMIC / LNA / 0805+ ground pad go? | **Directly in the pad. Multiple vias if pad allows.** |
| Does the RF Width rule apply to GND-side legs of shunts? | **No** — they're on the `GND` net, not RF. Length matters, not width. |
| Star ground? | **No** — old advice, doesn't apply |

---

## TL;DR

- "Unbroken ground" really means "no break under any RF trace" — not
  literally every mm²
- 4-layer stackup with a dedicated solid ground plane on layer 2 makes
  this almost effortless
- Via stitching + via fences are real tools — use them around RF
  zones, especially the TX↔RX boundary
- Resist the urge to split analog/digital grounds. Single solid plane
  wins at every frequency you care about

---

## Related Documents

- Altium schematic instructions: [`altium_comms_schematic.md`](altium_comms_schematic.md)
- RX mixer trade study: [`rx_mixer_trade_study.md`](rx_mixer_trade_study.md)
- Bring-up procedures: [`../bringup/`](../bringup/)
