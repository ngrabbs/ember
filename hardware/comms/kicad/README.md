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

## Current state — imported rev 0.5, RX rebuild pending

This project was imported from the Altium rev 0.5 design. The TX chain matches
the current plan (2SC3356 tripler, ADL5602 MMIC). **The RX chain does not.**

The architecture is moving to **all-UHF** — a 435 MHz uplink sharing the single
antenna — because the VHF front-end filters proved too difficult to realise.
The schematic still carries the 2 m uplink: a 2 m input band-pass filter, and
CLK1 at 145.90 MHz as the LO.

Annotations describing the RX front end are therefore accurate to what is drawn
today, not to where the board is going. When the RX is rebuilt, these change
together:

- Root sheet subtitle: `70 cm BPSK TX / 2m AFSK RX`
- Root sheet RX block: `2m BPF ( input filter )`
- Root sheet clock block: `CLK1 (145.90 MHz)`
- RX sheet: `2m Input Band-Pass Filter`
- `RX SMA <- 145.9 MHz antenna`

Until then, do not read the RX sheet as the target design. See
[`../design/kicad_implementation_plan.md`](../design/kicad_implementation_plan.md).

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
