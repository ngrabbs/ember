# CSKB connectors and mechanical reference

[System interfaces](../README.md) · [Canonical pin map](cskb_pinmap.md)

**Status: documented v0.1 connector baseline.** Use this page for connector
selection, stack spacing, and alignment. Signal assignments remain in the pin map.

## Connectors — mechanical

Boards use **two** CSKB connectors side by side (H1 + H2),
matching Pumpkin's layout.

### Project defaults (v0.1)

| Role | Boards | Samtec P/N | Type | Stacking height |
|---|---|---|---|---|
| Primary (stackable modules) | IHU, comms, payload | **ESQ-126-39-G-D** | 52-pin stackthrough, 0.1″ pitch | 15 mm |
| Endpoint (bottom of stack) | EPS | **ESQ-126-37-G-D** | 52-pin non-stackthrough, 0.1″ pitch | N/A (endpoint) |

**Why this split:** per Pumpkin's footnote on page 17 of the Rev. E
datasheet, "Non-stackthrough connectors are normally fitted only on an
MB and form an endpoint to the CubeSat Kit Bus connector stack.
Stackthrough connectors are normally fitted to all other modules."
EPS is the stack endpoint (acts as the motherboard), so it
uses the non-stackthrough part; every other board uses the
stackthrough part so it can sit anywhere in a mixed stack.

**v0.1 stacking height: 15 mm between modules** — the normal CSKB
default.

### Connector options catalog (for future reference)

The full Pumpkin Samtec family, so we never have to re-derive it:

| # | Samtec P/N | Pins | Type | Use case |
|---|---|---|---|---|
| 1 | `ESQ-126-37-G-D` | 52 (2×26) | Non-stackthrough | CSKB connector for endpoint module (MB / EPS) |
| 2 | `ESQ-126-39-G-D` | 52 (2×26) | Stackthrough | CSKB connector for all other stacked modules |
| 3 | `SSQ-126-22-G-D` | 52 (2×26) | 10 mm extension | **Inserted between modules to increase stacking height from 15 mm to 24–25 mm.** Not a primary connector — use only if taller spacing is required (e.g., to clear a tall component). |
| 4 | `ESQ-104-37-G-D` | 8 (2×4) | Non-stackthrough | PC/104 J1/J2 power connector (endpoint); not used here PC/104 |
| 5 | `ESQ-104-39-G-D` | 8 (2×4) | Stackthrough | PC/104 J1/J2 power connector; not used here |
| 6 | `SSQ-104-22-G-D` | 8 (2×4) | 10 mm extension | PC/104 J1/J2 power extension; not used here |
| 7 | `LSS-150-02-L-DV` | 100 (2×50) | Hermaphroditic | PPM connector (H10) on Pumpkin processor modules; not used here |

**When we might need #3 (SSQ-126-22-G-D):** if any board has a
component taller than ~13 mm above its top surface, we'll need to
insert this 10 mm extension between that board and the next, for 25 mm
spacing on that interface. Flag this early during mechanical review.

### Mechanical alignment note

X/Y position of H1 and H2 on every PCB MUST match Pumpkin's
motherboard layout (see [`DS_CSK_MB_710-00484-E.pdf`](DS_CSK_MB_710-00484-E.pdf) page 5,
"Simplified Mechanical Layout") so a mixed stack with any Pumpkin /
MBM2 / iSpace board mates without rework. Verify footprint position
and H1–H2 spacing against the Pumpkin drawing before any PCB layout.


## Source

[Pumpkin Motherboard Rev. E datasheet](DS_CSK_MB_710-00484-E.pdf)
(P/N 710-00484, document Rev. A, March 2012): page 5 for
mechanical alignment, pages 13–17 for connector numbering and catalog.
