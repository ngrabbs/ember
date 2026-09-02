# Comms Board — KiCad Project

The transceiver board's KiCad project lives in this directory, project name
`transceiver`. It is tracked in git: KiCad's `.kicad_sch`, `.kicad_pcb` and
`.kicad_pro` are plain-text S-expressions, so schematic and layout changes
diff and review like any other source. Only KiCad's per-user and generated
files are ignored — `.kicad_prl`, `fp-info-cache`, `*-backups/`, autosaves.

Expected contents:

| File | Purpose |
|---|---|
| `transceiver.kicad_pro` | Project file — net classes, constraints |
| `transceiver.kicad_sch` | Root schematic, plus one file per sheet |
| `transceiver.kicad_pcb` | Layout |
| `transceiver.kicad_dru` | Custom rules — copy [`../../conventions/jlcpcb_baseline.kicad_dru`](../../conventions/jlcpcb_baseline.kicad_dru), then retune |
| `lib/` | Project-local symbols and footprints |

## Before starting

Work through Phase 0 of
[`../design/kicad_implementation_plan.md`](../design/kicad_implementation_plan.md):
stackup, constraints, net classes, and the custom RF width rule. The rules
themselves are in
[`../../conventions/kicad_jlcpcb_design_rules.md`](../../conventions/kicad_jlcpcb_design_rules.md),
and net names come from [`../../conventions/net_naming.md`](../../conventions/net_naming.md).

RF layout practice — ground pour, via stitching, the 50 Ω geometry — is in
[`../design/rf_layout_guidelines.md`](../design/rf_layout_guidelines.md).

Fabrication outputs go to `../releases/`, not here.
