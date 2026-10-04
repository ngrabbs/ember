# LM73100 replacement acceptance record

Status: **SCHEMATIC IMPLEMENTED AND VERIFIED; FOOTPRINT ACCEPTED ON DISPOSABLE PCB. REAL PCB PLACEMENT/ROUTING AND NATIVE ERC PENDING.**

Changes are bounded to Power.kicad_sch and project Ember_RF library additions. The parent verified the real schematic editor closed, placed U99 on a disposable PCB via Konnect IPC, inspected copper/paste against TI figures, and released implementation. No real PCB changes were made by the schematic agent.

## Selected part

TI LM73100RPWR, LCSC C3210761, VQFN-HR RPW0010A (2 × 2 mm, 10 leads).
Live lookup previously returned 4,306 stocked; Extended part. Recheck before ordering.
- https://jlcpcb.com/partdetail/TexasInstruments-LM73100RPWR/C3210761
- Datasheet: https://www.ti.com/lit/ds/symlink/lm7310.pdf
- Local authoritative download: work/lm73100.pdf
- RPW land pattern and stencil: PDF pages 50–51, drawing 4225183/A 08/2019.

## Pin mapping and verified schematic connections

| Pin | Name | Schematic type | Connection |
|---|---|---|---|
| 1 | EN/UVLO | input | R46 470k to +5V_CON; local net PWR_EN |
| 2 | OVLO | input | GND; overvoltage lockout disabled |
| 3 | PG | open collector | NC marker; unused |
| 4 | PGTH | input | GND; unused power-good threshold |
| 5 | IN | power input | +5V_CON, C117 input bypass |
| 6 | OUT | power output | +5V, C118 output bypass |
| 7 | DVDT | passive | C116 10nF to GND; local net PWR_DVDT |
| 8 | GND | power input | GND |
| 9 | IMON | passive | GND; unused monitor |
| 10 | DNC | no connect | NC marker; footprint solder land only, NO external copper |

No exposed pad. No mechanical pads. Pins 1,4,7,10 each comprise two overlapping, identically numbered rounded-rectangle pad objects, creating the manufacturer L-shaped land. Fourteen copper objects represent ten logical pins.

The two side banks of the schematic symbol are functional organization only; they do not imply physical package order. OUT is the +5V power driver; PWR_FLAG #FLG04 moved from +5V to +5V_CON: the input is supplied by the external EPS and U15 now drives +5V.

## New components implemented

| Ref | Value | LCSC | MPN | Footprint |
|---|---|---|---|---|
| U15 | LM73100RPWR | C3210761 | LM73100RPWR | Ember_RF:Texas_RPW0010A_VQFN-HR-10_2x2mm |
| R46 | 470k, 1% | C23178 | 0603WAF4703T5E | Resistor_SMD:R_0603_1608Metric |
| C116 | 10nF, 50V X7R 10% | C57112 | 0603B103K500NT | Capacitor_SMD:C_0603_1608Metric |
| C117 | 1uF, 50V X5R 10% | C15849 | CL10A105KB8NNNC | Capacitor_SMD:C_0603_1608Metric |
| C118 | 1uF, 50V X5R 10% | C15849 | CL10A105KB8NNNC | Capacitor_SMD:C_0603_1608Metric |

All refs were unused in all seven real child sheets at last inventory. Existing C58/C61 output bulk, C68/C70 input bypass, D14 Pico isolation and all other components are preserved. Six new power symbols reserved #PWR01043 through #PWR01048.

## Copper geometry acceptance

Coordinates relative to package center, top view; dimensions in mm. F.Cu and F.Mask, no automatic F.Paste. Rounded rectangles have nominal corner radius 0.05 mm.

| Pad | Center x,y | Width,height |
|---|---|---|
| 1 | -0.9,-0.7 and -0.725,-0.875 | 0.6,0.3 and 0.25,0.65 |
| 2 | -0.9,-0.225 | 0.6,0.25 |
| 3 | -0.9,+0.225 | 0.6,0.25 |
| 4 | -0.9,+0.7 and -0.725,+0.875 | 0.6,0.3 and 0.25,0.65 |
| 5 | -0.25,0 | 0.3,2.4 |
| 6 | +0.25,0 | 0.3,2.4 |
| 7 | +0.9,+0.7 and +0.725,+0.875 | 0.6,0.3 and 0.25,0.65 |
| 8 | +0.9,+0.225 | 0.6,0.25 |
| 9 | +0.9,-0.225 | 0.6,0.25 |
| 10 | +0.9,-0.7 and +0.725,-0.875 | 0.6,0.3 and 0.25,0.65 |

Body 2×2 mm. Courtyard ±1.45 mm. Pin-1 silkscreen dot at (-1.45,-0.9).
Paste is separate rounded polygon graphics following TI stencil example:
- corner horizontal centers (±0.9,±0.6875), size 0.6×0.275;
- corner vertical centers (±0.7125,±0.875), size 0.25×0.65;
- middle side centers (±0.9,±0.225), size 0.6×0.25;
- central pin 5/6 split openings centers (±0.25,±0.63), size 0.28×1.06, 0.2 mm gap.

TI stencil example shifts corner vertical paste inward 0.0125 mm relative to copper center. This is intentional transcription of the 1.425 mm stencil dimension versus 1.45 mm land dimension. Verify against manufacturer images before accepting. Parent accepted native disposable placement/readback and exported copper/paste inspection. Production Gerber and assembly preview remain required.

## Electrical/layout constraints

- VIN range 2.7–23 V. Selected design is a nominal 5 V input path.
- Maximum RON 44.85 mΩ over datasheet range; forward-regulation drop up to 28.4 mV at light load. Do not treat ON resistance as the only drop at tiny loads.
- Reverse re-enable threshold can reach 125 mV. Verify supply dips, ramp and recovery at bench; the IC is not a regulator.
- 10nF DVDT sets approximately 0.2 V/ms, about 25 ms for 5 V nominal. Includes capacitor and IC-current tolerance; not an exact delay.
- R46 exceeds TI recommended ≥350k for EN tied to an input that can exceed 5 V or reverse polarity.
- Fixed fast-trip threshold is high (~21.9 A typical). This part does not provide a tailored low-current overload limit. System supply/current limiting remains necessary.
- Put C117/C118 physically adjacent to IN/OUT and ground. Retain C58 47u nearby on output and C68/C70 on input.
- Very short DVDT and ground loops; keep switching signals away.
- Size high-current power connections for twice the qualified maximum load, per TI layout guidance. Avoid thermal-via reliance on unfilled via-in-pad without manufacturing acceptance.
- Pin 10 DNC must not join a trace or zone. No external copper beyond its solder land.
- Qualify ≥4.5 V at CAN controllers and ADL5602 including EPS regulation, ripple, transients and PCB losses. Current budget still requires system closure; known maximum CAN+two RF gain-block load alone is ≥312 mA, excluding Pico and other loads.

## Evidence and implementation artifacts

All paths below under /Users/nick/Documents/Codex/2026-09-09/ds/ unless absolute.

- Pre-change archive: work/power-before-lm73100.zip
- Project library: /Users/nick/Desktop/ember/hardware/comms/kicad/lib/Ember_RF.kicad_sym
- Footprint: /Users/nick/Desktop/ember/hardware/comms/kicad/lib/Ember_RF.pretty/Texas_RPW0010A_VQFN-HR-10_2x2mm.kicad_mod
- Disposable project: work/power-disposable/power-disposable.kicad_pro
- Disposable PCB: work/power-disposable/power-disposable.kicad_pcb
- Disposable schematic: work/power-disposable/power-disposable.kicad_sch
- Manufacturer images: work/lm73100-land.png, work/lm73100-paste.png
- Footprint native readback: work/power-footprint-readback.json
- MCP symbol creation and library update: work/power-symbol-v3-*.json
- Accepted symbol-only render: work/power-disposable4.png
- Proposed block render: work/power-block-preview2.png
- Named-net readback: work/power-scratch-final-4.json
- Native exported disposable netlist: work/power-disposable.net
- Disposable ERC: work/power-scratch-erc.json
- Real-sheet scripts executed through Konnect: work/power-block-build.py, work/power-block-wire.py, work/power-old-cleanup.py

Scratch ERC: no symbol/library mismatch or unconnected pins in proposed U15 block; two expected undriven supply findings for external +5V_CON/GND. Other findings belong isolated U1 symbol test above. Disposable contains both U1 and U15: do not F8 it into the real PCB.

Final script moves U15 GND downward instead of the left GND label shown in preview, preventing overlap with C116 reference. It also labels PWR_EN/PWR_DVDT and uses globally unique power references. Actual final Power render inspected after implementation. Full native root ERC remains a parent check. Real Power now contains the verified replacement circuit.


## Final implementation verification (2026-10-03)

- D8 removed. U15/R46/C116/C117/C118 added with embedded LCSC numbers and manufacturer part numbers.
- #FLG04 relocated to +5V_CON; no second power-output driver on +5V.
- All 18 other existing components retain identical values, references, positions, rotations and footprints in MCP component readback.
- Existing C58/C59/C61/C62, D12/D13/D14, R26/R31 and other sheet circuitry preserved.
- Thirty total Power-sheet symbols including power symbols/flags.
- Exact pin-net assertions pass for all new parts. PG3 and DNC10 each have an NC marker.
- Konnect detects zero shorts and zero orphan items.
- Root CLI ERC has **zero Power-sheet findings**, 38 historical root dangling-wire artifacts, and two intentional MCP25625 SO-type library mismatch warnings. Do not treat this as a replacement for native full-project ERC.
- Stale series-diode voltage-drop/current-budget notes replaced; Pico isolation note corrected to D14.
- Final drawing is readable, without new wire/text overlaps.

Retained evidence in this directory's `lm73100/` folder:
- `power-schematic.png`: final real Power sheet.
- `pin-net-assertions.json`: pass/fail assertions, net mapping, preservation check.
- `power-netlist-summary.json`: MCP final symbol/pin/net readback.
- `root-cli-erc.json`: full CLI result for classification.
- `disposable-pads.json`: parent's placed footprint native readback.
- `disposable-copper-paste.png`: parent's inspected exported footprint crop.
- `ti-land-pattern.png`, `ti-paste-pattern.png`: manufacturer drawings.

**Required PCB follow-through:** use native F8, preserve existing route/layout, place and route U15 and four passives, isolate DNC10, run native ERC/DRC and manufacturing preview. The library's default reference text overlaps top pads; no library field-placement MCP operation was exposed. Move the actual U15 reference away from pads/copper through the PCB text-position tool after placement, then include it in silkscreen checks. No copper or paste geometry change is needed.


## PCB follow-through complete

Native F8 synchronized the block; D8 removed. U15/R46/C116–C118 placed/routed, DNC10 isolated and reference text moved clear. Saved/refilled DRC 0 errors/unconnected; native ERC 0 errors; native parity 213 nets/572 logical pad entries, zero mismatch. See `../../releases/review_20261003_1952/README.md` for bounded rail review and remaining EPS dynamic/thermal bench qualification.
