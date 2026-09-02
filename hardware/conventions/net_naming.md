# Net Naming Convention

**Scope:** all PCB designs in this project — EPS, comms, IHU, payload
carrier, future boards.
**Owner:** hardware lead.
**Status:** Living document — update when a convention proves wrong or
incomplete.

This document defines how nets are named on every schematic in the
project. The goal is wildcard-friendly grouping, readable DRC reports,
and cross-board consistency.

If you're laying out a new board, read this first.

---

## Why this exists

Altium auto-names unlabeled nets as `NetCXX_Y` (where `CXX` is a
component reference and `Y` is a pin number). Auto-named nets:

- Can't be matched by wildcard rules (`RF_*` matches nothing)
- Make DRC reports unreadable ("clearance violation on `NetC73_2`" —
  which net is that?)
- Force per-net manual class assignment in the Object Class Explorer
- Make schematic review painful for the next person

A consistent prefix convention solves all of these. Set up the
convention once, follow it on every board, and your Design Rules,
class assignments, and review process become trivial.

---

## The prefix convention

Name every meaningful internal net with a **domain prefix**. The
prefix tells you the signal's electrical character at a glance and
makes wildcard-based Net Class membership work.

| Prefix | Use for | Example |
|---|---|---|
| `RF_` | Any net carrying ≥ 100 MHz signal | `RF_TX_BPF1_TAP1`, `RF_RX_MIXER_RF` |
| `LO_` | Local oscillator distribution (RF, but called out for clarity) | `LO_LPF_NODE1` — or fold under `RF_LO_*` if you prefer |
| `BB_` | Baseband / analog audio (DC to ~100 kHz analog) | `BB_IF_OUT`, `BB_FILT_OUT`, `BB_ADC_IN` |
| `DIG_` | Digital signals (slow logic, GPIO, I²C, SPI, UART) | usually unnecessary if the net's functional name is clear (e.g. `SPI_MISO` is self-evident) |
| `PWR_` | Power rails | usually use **power ports** instead — see Power and Ground section |
| `ANA_` | General analog (sensor outputs, op-amp biases) when not baseband | `ANA_VREF`, `ANA_BIAS_25V` |
| `THM_` | Thermal / temperature sense signals | `THM_BATT_NTC`, `THM_MMIC_DIODE` |

Pick the prefix that matches the **electrical character** of the
signal, not its physical location. A 10 kHz audio signal traveling
across an RF board is still `BB_*`, not `RF_*`.

### Functional naming within a domain

After the prefix, name the net by **what signal it carries and
where**, not by the component reference designator. The component
reference can change between revisions; the function shouldn't.

Bad: `NetC73_2` (auto-named, opaque)
Bad: `RF_NET3` (prefixed but still opaque)
Better: `RF_TX_BPF1_TAP1` (prefix + chain + stage + role)

Pattern: `<prefix>_<board-or-chain>_<stage>_<role>`

Examples from various boards:

```
# Comms board RF chains
RF_TX_TRIPLER_OUT       ← BFR92A collector → pre-MMIC BPF
RF_TX_BPF1_TAP1         ← inside the pre-MMIC BPF
RF_TX_MMIC_IN           ← BPF output → ADL5602 input
RF_TX_MMIC_OUT          ← ADL5602 output → output BPF
RF_TX_OUT               ← final stage → TX antenna connector
RF_RX_IN                ← from RX antenna connector → 2m BPF
RF_RX_LNA_OUT           ← PSA4 output → mixer RF
RF_RX_MIXER_LO          ← LO LPF out → ADE-1+ LO

# Baseband (also on comms board)
BB_RX_IF                ← mixer IF
BB_RX_FILT              ← Sallen-Key out
BB_RX_BASEBAND          ← final gain stage → ADC

# EPS thermal
THM_BATT_NTC            ← LTC4162 NTC input
THM_BUCK1_DIE           ← TPS62933F die temp sense (if used)
```

---

## Power and ground naming

Use **power port symbols** for supply rails, not net labels with `PWR_`
prefix. Power ports are global automatically and Altium handles them
specially.

Canonical rail names across the project:

| Net name | Meaning |
|---|---|
| `+3V3` | 3.3 V regulated rail (EPS-supplied via stack-bus) |
| `+5V` | 5.0 V regulated rail (EPS-supplied via stack-bus) |
| `VBAT` | Unregulated battery bus (~7 V nominal, ~6 V to ~8.4 V) |
| `GND` | Single ground reference (do not split analog/digital) |

**Notation rules:**
- Always include the `+` sign on positive rails (`+3V3`, not `3V3`)
- Use `V3` notation, not `V3.3` or `V_3.3` or `_3V3` (`+3V3`, `+1V8`)
- `GND` only — no `AGND`/`DGND`/`PGND` (see RF layout guidelines for
  why a single solid plane outperforms split grounds at any
  frequency above ~1 MHz)

If you need a derived or filtered local rail on a single board, prefix
it to indicate scope:

```
+3V3_LNA       ← LNA-filtered +3V3, board-local
+5V_TX_GATED   ← +5V switched by RP2040 GPIO
```

---

## Inter-board (stack-bus) net naming

Nets that cross the CSKB stack-bus connect signals between boards.
These deserve a clear signal that they're system-level, not
board-internal.

**Convention:** stack-bus signal nets use the **`_SYS`** suffix on
the pinmap-canonical name.

| CSKB pin | Net name | Description |
|---|---|---|
| H1.41 | `SDA_SYS` | System I²C data |
| H1.43 | `SCL_SYS` | System I²C clock |
| H1.16 | `COMMS_IRQ` | Comms → IHU data-ready (or use `IRQ_SYS_<n>` if multiple) |
| H1.21–24 | `SPI_<bus>_<line>` | e.g. `SPI_COMMS_SCK`, `SPI_COMMS_MOSI` |
| H2.25/26 | `+5V` | System +5 V rail (power port) |
| H2.27/28 | `+3V3` | System +3.3 V rail (power port) |

The `_SYS` suffix is a flag for the design-reviewer that says: "this
net leaves my board and is shared with the rest of the stack."
Pinmap definition lives in
[`system/interfaces/cskb_pinmap.md`](../../system/interfaces/cskb_pinmap.md).

Inter-board net names must match exactly across every board's
schematic. If the EPS calls a net `SDA_SYS` and the comms board
calls it `I2C_SDA`, those are *different nets* as far as system
integration is concerned, and any cross-board protocol doc has to
reconcile them by hand.

---

## How to apply the convention in Altium

Three mechanisms, in priority order:

### 1. (Best, prospective) Net Labels — name as you draw

For every meaningful net, place a **Net Label** (`Place → Net Label`
or shortcut `P, N`) on the wire and type the name following the
prefix convention. The named net overrides Altium's `NetCXX_Y`
auto-name.

Costs ~5 seconds per net at draw time. Saves you the recovery work
discussed below.

### 2. (Retrofit) Net Class directives — group without renaming

When you've inherited a design with `NetCXX_Y` everywhere and don't
want to rename hundreds of nets, use **Net Class directives**:

1. **Place → Directives → Net Class**
2. Drop the directive on a wire in the chain you want to group
3. Set Class Name to the target (e.g., `RF`)
4. Every electrically-connected net joins that class on compile,
   regardless of its auto-generated name

For grouping an entire schematic region in one shot:
- **Place → Directives → Blanket** with a Net Class parameter
- Draw the blanket over the region — every net inside the blanket
  joins the class

For typical RF boards, 3–5 blanket placements cover the entire RF
chain.

### 3. (Last resort) Manual class assignment

In Object Class Explorer, select nets one at a time and move them
into the target class. Always works. Slow. Save this for one-off
edge cases.

---

## Recovering from an existing design with auto-named nets

If you're inheriting a design with `NetC40_1` everywhere and you
want to bring it into compliance:

1. **Don't try to rename everything at once.** Schematic rework + ECO
   churn isn't worth it.
2. **Apply Net Class directives in the schematic** to get classes
   populated correctly (see mechanism #2 above) — this fixes the
   immediate problem (rule scoping) without touching net names.
3. **As you make new design changes**, rename the affected nets to
   the convention by placing Net Labels. The net retains its
   connectivity; only the name updates.
4. **For critical-path nets** (RF traces especially), rename
   explicitly so DRC reports and schematic reviews stay readable.
5. **Run ECO** after any rename to push the new name to the PCB.
   Existing copper doesn't move; only metadata changes.

---

## Worked examples per board

Each board's design doc should include a short list of its
domain-specific named nets. Examples below are illustrative, not
exhaustive — see each board's `altium_<board>_schematic.md` for the
full list.

### Comms board

See [`hardware/comms/design/schematic_guide.md`](../comms/design/schematic_guide.md)
for the full RF / BB chain listing. Examples:
`RF_TX_TRIPLER_OUT`, `RF_TX_BPF1_TAP1`, `RF_RX_LNA_OUT`,
`RF_RX_MIXER_LO`, `BB_RX_IF`, `BB_RX_BASEBAND`.

### EPS board

See [`hardware/eps/design/schematic_guide.md`](../eps/design/schematic_guide.md).
Suggested naming once renamed: `PWR_PANEL_RAW_<face>` for solar
inputs, `PWR_BATT_BUS` for the 2S battery bus,
`THM_BATT_NTC` for charge-disable thermal sense.

### IHU, payload, future boards

Adopt this convention from day one. Reference this document in the
board's `altium_<board>_schematic.md`.

---

## Reference designators (separate convention)

Net naming is one piece. Reference designators (R1, C1, U1, J1, etc.)
have their own convention. A `refdes_conventions.md` in this directory is
the intended home for it; until it is written, follow Altium / IPC defaults:
R = resistor, C = capacitor, L = inductor, U = IC, Q = transistor,
D = diode, J = connector, Y = crystal/oscillator, TP = test point,
FB = ferrite bead.

---

## Related documents

- [`hardware/comms/design/rf_layout_guidelines.md`](../comms/design/rf_layout_guidelines.md) — ground plane, via stitching, stackup rules (also project-relevant despite living under comms/)
- [`system/interfaces/cskb_pinmap.md`](../../system/interfaces/cskb_pinmap.md) — canonical CSKB pin assignments
- Each board's `altium_<board>_schematic.md` — board-specific applications of this convention
