# CubeSat Kit Bus (CSKB) Pin Map — Canonical

## Status

**This document is the single source of truth for this project's CubeSat
Kit Bus pin assignments.** Every board in the stack (EPS, flight
controller, comms, payload) MUST match the pin numbers defined here.
If a schematic doc and this file disagree, this file wins — update the
schematic, not this file.

## Scope and terminology

This project uses the **Pumpkin CubeSat Kit Bus (CSKB)** as defined in the
CubeSat Kit Motherboard Rev. E datasheet
([`system/interfaces/DS_CSK_MB_710-00484-E.pdf`](DS_CSK_MB_710-00484-E.pdf), Pumpkin P/N 710-00484,
doc Rev. A dated March 2012). The CSKB is delivered via **two physical
connectors**, `H1` and `H2`, each a 2×26 0.1″ (2.54 mm) pitch socket
(52 pins each, 104 pins total).

**This is NOT PC/104.** Pumpkin's motherboard also exposes a legacy
PC/104 system bus on separate connectors (`J1` + `J2`, 2×32 + 2×20,
using A/B/C/D row labels), of which Pumpkin only wires +5V and GND.
This project does not use the PC/104 system bus. The 104-pin count of
CSKB is, per Pumpkin's own footnote, "purely coincidental" with PC/104.

**Why CSKB:** future-proofing. If any subsystem is later
replaced with a Pumpkin MBM2 / Pumpkin EPS / iSpace board that speaks
CSKB, mechanical and electrical compatibility holds without rework.
Decision locked 2026-04-15 by Nick Grabbs.

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

## Pin numbering convention

H1 and H2 each use flat 1..52 pin numbering (odd pins down one column,
even pins down the other, 2×26 layout — see page 13 of the Pumpkin
datasheet). Pin 1 at the top-left, pin 2 at the top-right, pin 52 at
the bottom-right. No A/B/C/D row letters — those belong to the
separate PC/104 J1/J2 bus, not to CSKB.

## Direction legend

For each pin, the per-board column shows:

- `D` — **drives** the net (output / source)
- `C` — **consumes** the net (input / sink / load)
- `B` — **bidirectional** (I2C, CAN)
- `M` — **monitor only** (ADC tap, not a load)
- `—` — pin not connected on this board (net passes through)
- `R` — reserved (net defined, not routed on this board in v0.1)

## H1 Pin Assignments

H1 carries all of the stack's I/O, control, and user signals, plus the
system I2C bus.

| H1 pin | Pumpkin name | Net | EPS | IHU | Comms | Payload | Function |
|---|---|---|---|---|---|---|---|
| H1.16 | `IO.8` | `COMMS_IRQ` | — | C | D | — | Comms data-ready interrupt → IHU ISR (push-pull, active-low, normally high) |
| H1.19 | `IO.5` (URX0) | `UART_DBG_RX` | — | C | — | — | IHU debug UART RX (from ground/debug host) |
| H1.20 | `IO.4` (UTX0) | `UART_DBG_TX` | — | D | — | — | IHU debug UART TX (to ground/debug host) |
| H1.21 | `IO.3` (SCK0) | `SPI_COMMS_SCK` | — | D | C | — | SPI clock, IHU master → comms slave |
| H1.22 | `IO.2` (SDI0) | `SPI_COMMS_MISO` | — | C | D | — | SPI data, comms slave → IHU master |
| H1.23 | `IO.1` (SDO0) | `SPI_COMMS_MOSI` | — | D | C | — | SPI data, IHU master → comms slave |
| H1.24 | `IO.0` (-CS_SD) | `SPI_COMMS_CS_N` | — | D | C | — | SPI chip select, IHU → comms (active-low) |
| H1.29 | `-RESET` | `SYS_RESET_N` | R | R | R | R | Stack reset, reserved (no board drives it in v0.1) |
| H1.31 | `OFF_VCC` | `OFF_VCC` | R | R | R | R | Pumpkin power-control, reserved |
| H1.41 | `SDA_SYS` | `I2C_SDA` | D/B | B | B | B | Housekeeping I2C data (LTC4162 @ 0x68, Si5351A @ 0x60) |
| H1.42 | `VBACKUP` | `VBACKUP` | R | R | R | R | RTC/backup domain, reserved (single pin on CSKB) |
| H1.43 | `SCL_SYS` | `I2C_SCL` | D/B | B | B | B | Housekeeping I2C clock |
| H1.47 | `USER0` | `COMMS_EN` | — | D | C | — | IHU → comms enable (active-high) |
| H1.48 | `USER1` | `COMMS_FAULT_N` | — | C | D | — | Comms → IHU fault indication (open-drain, active-low) |
| H1.49 | `USER2` | `EPS_ALERT_N` | D | C | — | — | EPS `SMBALERT_N` (LTC4162) → IHU alert (open-drain, active-low) |
| H1.50 | `USER3` | `PAYLOAD_EN` | — | D | — | C | IHU → payload enable |
| H1.51 | `USER4` | `CAN_H` | — | B | B | B | CAN bus high (Iteration 2; DNP v0.1) |
| H1.52 | `USER5` | `CAN_L` | — | B | B | B | CAN bus low (Iteration 2; DNP v0.1) |

All other H1 pins (1–15, 17, 18, 25–28, 30, 32–40, 44–46) are
**reserved** on v0.1 — leave unconnected on every board. They
carry Pumpkin-defined signals (MHX transceiver, VREFs, RSVDn,
+5V_USB, PWR_MHX, -FAULT, SENSE, extra IO.9–IO.23) that this project
doesn't use but must not conflict with if a Pumpkin MB ever sits in
the stack.

## H2 Pin Assignments

H2 carries all of the stack's power rails plus the RBF/Separation
switches and additional USER pins.

| H2 pin | Pumpkin name | Net | EPS | IHU | Comms | Payload | Function |
|---|---|---|---|---|---|---|---|
| H2.25 | `+5V_SYS` | `+5V` | D | C | C | C | Stack 5 V rail (doubled with H2.26 for current sharing) |
| H2.26 | `+5V_SYS` | `+5V` | D | C | C | C | Stack 5 V rail (parallel) |
| H2.27 | `VCC_SYS` | `+3V3` | D | C | C | C | Stack 3.3 V rail (doubled with H2.28) |
| H2.28 | `VCC_SYS` | `+3V3` | D | C | C | C | Stack 3.3 V rail (parallel) |
| H2.29 | `DGND` | `GND` | D | C | C | C | Digital ground return |
| H2.30 | `DGND` | `GND` | D | C | C | C | Digital ground return |
| H2.31 | `AGND` | `GND` | D | C | C | C | Analog ground (single pin on CSKB; star-tied to DGND at EPS only) |
| H2.32 | `DGND` | `GND` | D | C | C | C | Digital ground return (third DGND pin) |
| H2.45 | `VBATT` | `VBAT` | D | — | M | C | Unregulated battery bus (6.0–8.4 V); monitor-only on comms, **consumed by payload** to feed its local 5V buck for the Jetson Orin Nano (stack +5V can't sustain Orin peak current — see Rule 7 below) |
| H2.46 | `VBATT` | `VBAT` | D | — | M | C | Battery bus (parallel) |
| H2.47 | `USER6` | `PAYLOAD_FAULT_N` | — | C | — | D | Payload → IHU fault indication (open-drain, active-low). Mirrors `COMMS_FAULT_N` (H1.48) pattern. Driven low by payload on `SHUTDOWN_REQ*` from Orin module (software shutdown, thermal, undervoltage). |
| H2.48 | `USER7` | `PAYLOAD_SLEEP_REQ_N` | — | D | — | C | IHU → payload sleep request (push-pull, active-low). IHU drives low to request the Orin enter SC7 sleep; payload routes to Orin `SLEEP/WAKE*` (SO-DIMM pin 240). |

All other H2 pins (1–24, 33–44, 49–52) are **reserved** at
v0.1 — leave unconnected on every board. They carry Pumpkin-defined
signals (extra IO.24–IO.47 analog inputs, RBF/Separation switches
S0–S5 on H2.33–H2.44, USER8–USER11 on H2.49–H2.52).

**Note on grounds:** the CSKB has three DGND pins (H2.29, H2.30, H2.32)
and only one AGND pin (H2.31). This project treats all four as a single
`GND` net (single-plane ground strategy) with AGND star-tied to DGND
at the EPS board only. If a future analog subsystem needs truly
isolated analog ground, revisit this.

## Naming aliases

A few nets have two names depending on which board you're looking at —
both names refer to the same wire:

| CSKB pin | EPS-side name | IHU-side name | Notes |
|---|---|---|---|
| H1.49 | `SMBALERT_N` (LTC4162 pin name) | `EPS_ALERT_N` | Same net, renamed at the connector for IHU clarity |

## Rules

1. **New signals** that need to traverse the stack MUST pick a free H1
   or H2 pin from the Pumpkin-reserved list and be added to this table
   before any schematic gets a net label for it.
2. **Board-local signals** (e.g., IHU-internal SPI to MRAM, comms RF
   nets) MUST NOT appear on any H1/H2 pin.
3. **Pull resistors** for stack signals live on exactly one board —
   see per-signal notes in each schematic doc. For v0.1:
   - `COMMS_IRQ` pull-up: IHU side (R11, 10 k)
   - `COMMS_FAULT_N` pull-up: IHU side (R13, 10 k)
   - `PAYLOAD_FAULT_N` pull-up: IHU side (10 k)
   - `EPS_ALERT_N` pull-up: IHU side (R12, 10 k)
   - `I2C_SDA` / `I2C_SCL` pull-ups: EPS side (R4/R5, 4.7 k)
4. **Power rail bypass** at the connector is placed on BOTH the
   source (EPS) and the sink (IHU/comms/payload). See individual
   schematic docs for Cxx reference designators.
5. Only the pins listed above need to be wired on any given board. A
   board may omit a CSKB pin if it doesn't use that signal.
6. **Connector choice** per board:
   - Stack endpoint (EPS in v0.1): `ESQ-126-37-G-D` × 2 (non-stackthrough)
   - Everything else (IHU, comms, payload): `ESQ-126-39-G-D` × 2 (stackthrough)
   - 10 mm extension `SSQ-126-22-G-D` only if a specific module needs
     24–25 mm clearance to the next board.
7. **Payload power exception:** the payload board is the only stack
   consumer that draws from `VBAT` (H2.45/H2.46) directly rather than
   from the regulated `+5V` rail. This is because the Jetson Orin Nano
   peaks at ~3 A on its 5 V input in 15 W mode, which exceeds the stack
   `+5V` rail provisioning (~2 A nominal). The payload board has its
   own VBAT→5V buck regulator sized for the Orin's peak current. The
   payload's `PAYLOAD_EN` (H1.50, IHU-controlled) gates this local buck
   so the rest of the stack does not see the inrush.

## Per-board references

- [`hardware/ihu/design/altium_ihu_schematic.md`](../../hardware/ihu/design/altium_ihu_schematic.md) — IHU Sheet 6 (Connectors & Debug)
- [`hardware/eps/design/schematic_guide.md`](../../hardware/eps/design/schematic_guide.md) — EPS Sheet 3 (Connectors & Telemetry)
- [`hardware/comms/design/schematic_guide.md`](../../hardware/comms/design/schematic_guide.md) — Comms Sheet 7 (Connectors)
- [`hardware/payload_compute/design/payload_carrier_pinmap.md`](../../hardware/payload_compute/design/payload_carrier_pinmap.md) — Payload carrier SO-DIMM↔CSKB pin assignments (Jetson Orin Nano)

## Source of truth

- [`system/interfaces/DS_CSK_MB_710-00484-E.pdf`](DS_CSK_MB_710-00484-E.pdf) — Pumpkin CubeSat Kit
  Motherboard Rev. E datasheet (doc Rev. A, March 2012). Pages 13–17
  hold the authoritative H1/H2 pin tables and the Samtec connector
  catalog.

## Revision history

| Rev | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-04-15 | NG | Initial canonical pin map (based on PPM H10 numbering — WRONG, superseded) |
| 0.2 | 2026-04-15 | NG | Rebuilt against Pumpkin datasheet Rev. E: bus renamed PC/104 → CubeSat Kit Bus (CSKB); pin numbers remapped from H10 (PPM) → H1/H2 (stack bus); connector family corrected to Samtec ESQ-126 (not ESQ-130); split into H1 signal table + H2 power table; added connector options catalog and endpoint-vs-stackthrough guidance |
| 0.3 | 2026-05-11 | NG / CC | Payload integration: H2.45/H2.46 (`VBAT`) payload column changed `M` → `C` (Orin Nano draws from VBAT, not stack +5V — see Rule 7); allocated H2.47 (`USER6`) = `PAYLOAD_FAULT_N` and H2.48 (`USER7`) = `PAYLOAD_SLEEP_REQ_N`; added `PAYLOAD_FAULT_N` pull-up to Rule 3; added Rule 7 (payload-power exception); pointed Per-board references at [`payload_carrier_pinmap.md`](../../hardware/payload_compute/design/payload_carrier_pinmap.md). |
