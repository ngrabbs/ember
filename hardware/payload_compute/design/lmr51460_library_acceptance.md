# LMR51460 physical library acceptance

Manufacturer: Texas Instruments. Exact candidate: **LMR51460SQDRRRQ1**,
PFM, DRR WSON-12, 3 ×3 mm. Source: [TI datasheet](https://www.ti.com/lit/ds/symlink/lmr51460-q1.pdf),
SLUSFR3, August 2024. Pin functions: p. 3, Figure 5-1 / Table 5-1.
Geometry: pp. 31–33, DRR0012G, drawing 4227052/A August 2021;
the later DRR0012E drawing also specifies a 1.3 ×2.5 mm exposed pad.

Planned symbol: `EMBER_Payload:LMR51460SQDRRRQ1`.
Planned footprint: `EMBER_Payload:TI_DRR0012_WSON_3x3mm_EP1.3x2.5mm`.
Origin at package center. X right, Y down on front-side footprint.
Pin 1 at upper left, then counterclockwise in component/top view.
All rows use this view; the schematic drawing arranges functions separately.

| Datasheet lead | Function | Symbol pin / name / type | Footprint pad | X / Y mm | Drawing view / direction | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Switch node | 1 / SW / power_out | 1 | -1.39 / -1.25 | Top, counterclockwise from upper-left key | p.3, p.32 |
| 2 | Switch node, duplicate connection | 2 / SW / passive | 2 | -1.39 / -0.75 | Top, counterclockwise | p.3, p.32 |
| 3 | Switch node, duplicate connection | 3 / SW / passive | 3 | -1.39 / -0.25 | Top, counterclockwise | p.3, p.32 |
| 4 | Bootstrap | 4 / BOOT / passive | 4 | -1.39 / 0.25 | Top, counterclockwise | p.3, p.32 |
| 5 | Power good | 5 / PG / open_collector | 5 | -1.39 / 0.75 | Top, counterclockwise | p.3, p.32 |
| 6 | Frequency set | 6 / RT / passive | 6 | -1.39 / 1.25 | Top, counterclockwise | p.3, p.32 |
| 7 | Feedback | 7 / FB / input | 7 | 1.39 / 1.25 | Top, counterclockwise | p.3, p.32 |
| 8 | Analog ground | 8 / AGND / power_in | 8 | 1.39 / 0.75 | Top, counterclockwise | p.3, p.32 |
| 9 | Enable | 9 / EN / input | 9 | 1.39 / 0.25 | Top, counterclockwise | p.3, p.32 |
| 10 | Supply | 10 / VIN / power_in | 10 | 1.39 / -0.25 | Top, counterclockwise | p.3, p.32 |
| 11 | Supply | 11 / VIN / power_in | 11 | 1.39 / -0.75 | Top, counterclockwise | p.3, p.32 |
| 12 | Supply | 12 / VIN / power_in | 12 | 1.39 / -1.25 | Top, counterclockwise | p.3, p.32 |
| 13 (exposed) | Power ground | 13 / PGND / power_in | 13 | 0 / 0 | Top, central exposed pad | p.3, pp.31–33 |

Leads 1–12 use 0.62 ×0.25 mm copper/paste/mask lands on 0.5 mm pitch,
0.05 mm corner radius. Pad 13 uses 1.3 ×2.5 mm copper/mask.
Two unnumbered paste-only apertures, 1.21 ×1.10 mm, centers (0, ±0.65),
provide approximately 82% paste coverage. They are not electrical pads.
Thermal vias are not embedded in the library: place them during PCB layout
and coordinate filling/tenting and stencil with assembly requirements.

Count reconciliation: 12 perimeter leads +1 electrical exposed pad =13
symbol pins /13 numbered copper pads. Two paste-only features give 15
total footprint pad objects; no duplicate electrical pads, shields or holes.
Repeated VIN and SW leads remain separate pins and require explicit wiring.

SW1 is the power-output ERC representative; SW2/SW3 are passive duplicates
of the same internal switch node. All three remain physically distinct pins
and are explicitly joined in the scratch circuit. This avoids falsely declaring
three independent power drivers. It does not omit or change physical leads.

## Evidence collected

- Created project-local symbol and footprint through Konnect and registered
  both libraries with relative project URIs. No global library was modified.
- Symbol query returns all 13 pin numbers, functions and electrical types.
  Scratch instance query returns all 13 placed pin positions.
- Repaired Konnect footprint query returns all 15 pad objects with individual
  positions, sizes, pad types, shapes, rotations, layers and corner ratios.
  The live PCB query independently returns the same 15 positions/layer sets.
- KiCad's exported [IPC-2581 readback](validation/payload_power_acceptance/payload_power_acceptance-readback.xml)
  independently contains all numbered package pins, their positions and
  round-rectangle dimensions, plus layer-specific pad stacks. IPC uses Y up;
  the table above uses KiCad Y down, so compare with negated IPC Y.
  Export assigns synthetic PAD13/PAD14 names to the two unnumbered paste-only
  features; neither has a copper layer. These are not extra IC leads.
- Inspected the [rendered footprint](validation/payload_power_acceptance/payload_power_acceptance-footprint-detail.png):
  front/top view, upper-left pin-1 dot and fab chamfer, six lands per side,
  exposed copper and two separated paste apertures. Corrected the generated
  courtyard to include 0.25 mm beyond the full 3 mm body and copper envelope.
- The [disposable regulator circuit](validation/payload_power_acceptance/payload_power_acceptance.kicad_sch)
  has zero direct KiCad ERC errors/warnings and passes wire, component,
  short and orphan checks. Its passives are provisional sizing values.

## Acceptance after Konnect repair — 2026-10-04

Status: **PASS for this exact LMR51460 symbol/footprint**. This is library
acceptance, not approval of the complete carrier power circuit or fabrication.

- Explicit `ipc_address` makes future Konnect startups independent of whether
  KiCad was open first. A fresh MCP process reports IPC responsive.
- Local Konnect fixes add per-pad library geometry, recognize legacy
  `fp_text reference` during offline pad lookup, and expose
  `set_symbol_footprint` with validated atomic compare-and-write behavior.
- Assigned the library default footprint through the new MCP tool and queried
  it back. Refreshed only U1's embedded scratch definition through Konnect;
  no pin moved. All 13 symbol functions/types match the datasheet mapping.
- Checked all 13 electrical lands and two separate paste-only apertures in
  the library query and live U1 query. Dimensions/layers match the independent
  IPC-2581 export. The scratch PCB remains an unconnected footprint study.
- Regenerated and inspected the scratch schematic render. ERC remains zero
  errors/warnings, and the exported topology still matches all 11 intended nets.

Saved evidence: [connection](validation/payload_power_acceptance/konnect-repair-connection.json),
[server provenance](validation/payload_power_acceptance/konnect-repair-installation.json),
[live pads](validation/payload_power_acceptance/payload_power_acceptance-live-pad-query.json),
[placed symbol](validation/payload_power_acceptance/payload_power_acceptance-instance-query.json),
[placed pins](validation/payload_power_acceptance/payload_power_acceptance-pin-query.json),
[default assignment](validation/payload_power_acceptance/konnect-symbol-footprint-fix.json),
and the symbol/footprint query files beside them. Reproduce the acceptance
comparisons with `python3 hardware/payload_compute/design/validation/check_power_study.py`.

The repaired executable is a local build of installed v0.11.1 plus a small
patch, not an upstream release. Source and rollback instructions are in
`/Users/nick/Documents/ChatGPT/EMBER/work/konnect-repair/LOCAL_REPAIR.md`.
Codex is configured to use it on its next MCP connection. This chat's original
MCP process retains its startup configuration; verification and protected
file changes above used fresh real Konnect MCP sessions.

Remaining work before power-block integration: exact passive MPNs, source
selection/protection, USB contract gating/current bounds, an independent 5 V
window monitor, fail-safe enable logic, sequencing and thermal validation.
