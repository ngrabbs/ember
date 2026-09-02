# PCB Trace Sizing Quick Reference

A working reference for sizing traces on the EPS, comms, and internal housekeeping unit
boards. Two physical limits set the width: **thermal** (I²R heating) and
**voltage drop** (resistive loss). Whichever is tighter wins.

> **This board is 2-layer.** Only the *outer layer* column applies to EPS —
> both its faces are outer. The inner-layer column is kept because the comms
> board is 4-layer and uses the same table. JLCPCB also offers 2 oz on
> 2-layer, which halves these widths; the numbers below are 1 oz.

## Quick Lookup — 1 oz Copper, 10 °C Rise (IPC-2152)

| Current | Outer layer | Inner layer |
|---|---|---|
| 0.5 A | 0.15 mm (6 mil)  | 0.30 mm (12 mil) |
| 1 A   | 0.30 mm (12 mil) | 0.60 mm (24 mil) |
| 2 A   | 0.65 mm (25 mil) | 1.4 mm (55 mil)  |
| 3 A   | 1.0 mm (40 mil)  | 2.3 mm (90 mil)  |
| 5 A   | 1.7 mm (65 mil)  | 4.0 mm (155 mil) |
| 10 A  | 4.0 mm (155 mil) | 9.0 mm (350 mil) |

Notes:

- **Inner traces need ~2× the width** of outer traces. Heat can't radiate
  out of inner layers, so the limit is conduction through FR4.
- **2 oz copper**: divide widths by ~2.
- For **20 °C rise** instead of 10 °C: multiply width by ~0.6.
- The "10 °C rise" assumption is conservative for ambient ≤ 50 °C. For
  on-orbit environments with no convection, derate by another ~30 %
  unless you've explicitly modeled the thermal path.

So to answer "is 1 mm wide enough?" — on an outer layer with 1 oz copper,
1 mm trace handles ~3 A continuous at 10 °C rise. Anything below that:
yes. Anything above: probably no.

## Voltage Drop Check

R_trace = ρ × L / (W × t)

For 1 oz copper (t = 0.035 mm), this simplifies to:

```
R [mΩ] ≈ 0.49 × L_mm / W_mm
```

So a 1 mm wide × 10 mm long 1 oz trace = ~5 mΩ. At 3 A, ~15 mV drop —
usually fine. At 3 A on a 100 mm long trace at the same width: 50 mΩ
→ 150 mV → 4.5 % of a 3.3 V rail. That's too much for a power rail —
widen the trace, use a pour, or shorten the route.

**Rule of thumb for power rails:** keep total trace IR drop under
**1 % of rail voltage** under worst-case load.

## Rules of Thumb

- Signal traces (< 100 mA): 0.15 mm (6 mil) is the JLCPCB minimum-cost
  width; use that as your default for signals.
- Power traces (1–3 A): 0.5–1.0 mm on outer layer, 2× that on inner.
- Anything > 3 A: stop routing as a discrete trace, use a copper pour
  or polygon plane on the net.
- GND and the primary battery/PowerPath rail: pour, always.
- Don't neck down power traces under components — keep the wide section
  as continuous as possible.

## Vias for Power

A 0.3 mm drill / 0.6 mm pad via handles roughly **0.5–1 A** of continuous
current. For high-current nets crossing layers, stitch multiple vias.

**Rule of thumb: 1 via per 0.5 A** for conservative margin.

The LTC4162 PowerPath VOUT (up to ~3 A) needs **≥ 6 vias** if it has to
cross layers, ideally placed inside the copper pour so they don't choke
the current path.

## Tools

- **Saturn PCB Toolkit** (free, Windows) — implements IPC-2152, fastest
  for one-off lookups.
- **KiCad** — built-in `Tools → Calculator Tools → Track Width`.
- Enforcement is by **net class** — `Board Setup → Net Classes` sets the
  width per class, and a custom rule in the board's `.kicad_dru` can put a
  hard floor under the high-current classes.

## Reference Sizes (1 oz outer, JLCPCB stackup)

For sanity checks against existing boards — these are the targets, not
necessarily what got built.

| Net | Worst-case current | Min width (outer) | Recommended |
|---|---|---|---|
| `VOUT_PP` (LTC4162 → bucks) | 3 A | 1.0 mm | Pour |
| Buck SW nodes (U2/U3 pin 5 → inductor) | 3 A peak | 1.0 mm | 1.0 mm, kept very short |
| `+3V3`, `+5V` (regulator → CSKB) | 3 A | 1.0 mm | Pour |
| LTC4162 BATFET drain–source (charge path) | 3.2 A | 1.0 mm | Pour |
| Solar panel input (Vmp ≈ 22 V at < 60 mA per face) | 60 mA | 0.15 mm | 0.3 mm for margin |
| I2C / SPI / GPIO | < 10 mA | 0.15 mm | 0.15 mm |
| Stack-bus signal pins (CSKB) | < 100 mA | 0.15 mm | 0.25 mm |

## Common Mistakes

1. **Wide traces with thin necks**: the narrowest section sets the
   thermal limit. Don't route a 1 mm trace into a 0.15 mm pad neck.
   Use teardrops or a thermal relief fan-out.
2. **Inner-layer power without enough vias to the outer pour**: heat
   has nowhere to go. If a power trace must run on an inner layer,
   stitch vias to outer copper every 5–10 mm.
3. **Treating GND like a low-priority net**: ground return current
   needs the same cross-section as the forward current. Solid plane
   on at least one layer is the only sane answer for any board
   carrying > 100 mA.
4. **Ignoring pad-to-trace transitions**: a thermal relief on a
   ground pour can necks down the effective path to ~4 narrow spokes.
   For high-current pads (battery, charger, regulator GND), use a
   **direct connect** (no thermal relief) and rely on the rest of the
   pour for thermal mass.

## When in Doubt

Default to **0.5 mm for power, pour for anything > 2 A, 0.15 mm for
signals**, then run the IPC-2152 calculator on anything that feels
marginal. The cost of an extra 0.5 mm of copper is zero. The cost of a
trace that vaporizes during a battery short is the whole board.
