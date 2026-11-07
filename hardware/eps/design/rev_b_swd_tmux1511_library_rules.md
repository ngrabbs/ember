# TMUX1511PWR SWD switch symbol construction proposal

**CONSTRUCTION AUTHORIZED — 2026-10-24.** The user explicitly approved
TMUX1511 construction under these rules, including the green review alternative,
layout reservation and disposable checks. This authorizes construction and
package verification; real EPS integration and qualification remain separate.
2026-10-24. This proposal covers only a project-owned review symbol for TI
TMUX1511PWR with an unchanged stock TSSOP-14 land. It does not select or qualify
the final SWD protection circuit and does not authorize real PCB work.

## Source and search basis

Manufacturer source: [TI SCDS390B, revised March 2025](https://www.ti.com/lit/ds/symlink/tmux1511.pdf),
actual pin/functions p3, operating limits p4, electrical/dynamic tables p6–7,
function/truth table p21–22, application p23–25, order table PDF p31 and
PW0014A outline/land/stencil PDF p42–44. Package drawing 4220202/B, December2023.
The October2025 ordering addendum lists TMUX1511PWR, PW14 TSSOP, 2000/reel,
−40..125°C. Exact order identity is PWR; other suffixes/packages are not synonyms.
Local primary PDF, images, hash and query evidence belong to
`verification/controller_rev_b/swd_interface_candidate`.

Configured KiCadLib is absent. Installed-library TMUX1511 search and broad
3126 search both returned zero; exact `74xx:74CBTLV3126` and
`74xx:SN74CBTLV3126` are absent. Available quad analog-switch families do not
have this physical control map. Do not force a buffer, inverted enable, or
incorrectly numbered surrogate, and do not alter any vendor/global library.

## Authorized authoring boundary

Append only `TMUX1511PWR_REVIEW` to the already portable project review library
`Ember_Charger_BMS_Review` under `hardware/eps/rev_b/libraries/` (resolve actual
registered file before writing; do not invent a parallel library). Preserve all
previous symbol subtrees and project registrations. Reuse unchanged stock
`Package_SO:TSSOP-14_4.4x5mm_P0.65mm`; no new footprint is proposed here.

Use four recognizable active-high SPST units plus a fifth power unit, all with
one shared physical reference. Each channel shows its separate S/D pair and
SEL input, with a clear adjacent `SEL HIGH = closed; LOW = open` callout.
Konnect has no conventional switch glyph; use a clear rectangular functional
unit with S left, D right and SEL below, keeping names/numbers visible rather
than misrepresenting the channel as a logic buffer. All electrical anchors on
1.27mm grid, visible pin lengths at least2.54mm. Preserve each physical lead once
across the five units, no hidden duplicated power contacts or implicit net ties.
Channel-unit endpoints may be S(−10.16,2.54), D(+10.16,2.54),
SEL(0,−7.62); supply-unit VDD(0,+7.62), GND(0,−7.62), in library Y-up coordinates.
Inspect actual generated body bounds/field anchors in a disposable schematic
before accepting those coordinates; expand spacing on the same grid if needed.

Constructed presentation uses expanded S(−15.24,+5.08), D(+15.24,+5.08),
SEL(−15.24,−5.08) on the lower input row, all3.81mm pins, with supply-unit
VDD(−12.7,+10.16), GND(+12.7,−10.16). These offsets separate the inherited
Value field from vertical control/power pin strokes without changing any
physical number/type/unit membership. The five rectangular functional units
and adjacent truth-table callout are the supported switch presentation.

## Complete physical map

TI top/component view: pin1 at upper-left index, CCW down left1–7 then up
right8–14. Footprint coordinate system is front/component X-right/Y-down.
S/D terminals use bidirectional electrical types matching TI I/O; SEL is input;
supplies power_in. They are not push-pull outputs or synthesized logic gates.

| Lead | TI function | Unit | Symbol type | Stock pad X/Y mm |
| --- | --- | --- | --- | --- |
| 1 | SEL1 | A | input | −2.8625 / −1.95 |
| 2 | S1 | A | bidirectional | −2.8625 / −1.30 |
| 3 | D1 | A | bidirectional | −2.8625 / −0.65 |
| 4 | SEL2 | B | input | −2.8625 / 0 |
| 5 | S2 | B | bidirectional | −2.8625 / +0.65 |
| 6 | D2 | B | bidirectional | −2.8625 / +1.30 |
| 7 | GND | E | power_in | −2.8625 / +1.95 |
| 8 | D3 | C | bidirectional | +2.8625 / +1.95 |
| 9 | S3 | C | bidirectional | +2.8625 / +1.30 |
| 10 | SEL3 | C | input | +2.8625 / +0.65 |
| 11 | D4 | D | bidirectional | +2.8625 / 0 |
| 12 | S4 | D | bidirectional | +2.8625 / −0.65 |
| 13 | SEL4 | D | input | +2.8625 / −1.30 |
| 14 | VDD | E | power_in | +2.8625 / −1.95 |

Counts: 14 physical leads,14 symbol pins,14 raw electrical pads,14 unique
numbers; no NC/EP/mechanical/drilled pads. No duplicate pad-number collapse.

## Stock land and mechanical qualification limits

Each stock pad is1.475×0.400mm roundrect, ratio0.25 (R0.10), F.Cu/F.Mask/F.Paste,
no drill. TI example is1.50×0.45mm, X±2.90mm, R0.05. Thus stock is a generic
land deviation, not the exact TI example. Reconcile effective saved mask margin
and paste in the actual fixture. TI preferred NSMD example limits nominal mask
opening expansion to0.05mm MAX around copper; stock pad-generated mask with
inherited margin is not an independently specified aperture. Do not claim a nominal inherited mask setting
proves manufacturing registration tolerance.

TI body maximum4.5×5.1mm excludes0.25mm/side interlead flash across width and
0.15mm/side mold protrusions along length. Worst envelope is therefore5.0×5.4mm
(lead-tip span up to6.6mm). The stock stepped courtyard extends to X±3.85 and
Y±2.75, with inner corners X±2.45 around Y2.4..2.75: it does not provide a full
0.25mm margin around that worst-flash envelope. Development contact-map use is
conditional on a later layout reservation of **at least7.70×5.90mm**, full
rectangle X±3.85/Y±2.95, independently of the smaller stock courtyard.
This proposal does not silently enlarge the stock footprint or claim assembly
acceptance. If that conditional reservation is rejected, obtain separately
agreed footprint-construction rules before modifying/authoring a land.

## Metadata and review marker

Value and MFG P/N: `TMUX1511PWR`; Manufacturer: `Texas Instruments`;
PackageSize: `PW0014A / TSSOP-14`; Datasheet exact TI URL above.
Description states quad active-high bidirectional SPST with powered-off protection.
Retain visible **CUSTOM — REVIEW REQUIRED** on every placed functional/power
unit or its adjacent grouped review enclosure. Wording is `Construction authorized:
TMUX1511PWR review candidate` only after explicit user approval; never call the
candidate electrically/physically qualified. Bright-green body color is unsupported
by the installed authoring API; request the bright-green enclosure/callout
alternative explicitly. No opaque overlay hiding pins, no global theme change.
Apply complete instance fields through supported tools; distinguish unsupported
library custom-default/field-position presentation from saved metadata.

## Required acceptance before development use

Only after user approval, construct through Konnect, query every saved pin/type
and every raw pad, then place all five symbol units and an actual footprint in
a new independent disposable project. Confirm exact IPC board identity before
PCB writes. Requery saved/live instances with raw counts before dictionaries.
Inspect full page and detail, pin1/key, CCW front map, copper, mask, paste,
numbered fab, silk and courtyard; record the generic land and reservation limits.
Run raw CLI netlist/ERC with truthful fixture NC/power dispositions; never
weaken types to hide errors. Preserve main305-part source and all older fixtures
byte-for-byte; exclude runtime .history/.git/caches/locks/PRL from portable
evidence without deleting them. Return a saved verified package checkpoint
before any main-circuit integration or real PCB synchronization.

## Circuit questions outside this authoring approval

Preferred candidate is four switched paths (SWDIO, SWCLK, NRST and VTref), VDD
from permitted essential+3V3, local100nF bypass and autonomous selects high when
permitted supply is valid. No MCU enable or NRST-dependent gating: connect-under-
reset must work even with broken firmware. Probe must not power the target.
Target-side pulls/bleeds, probe VTref load, cable waveform/ESD, off leakage,
partial-power/brownout and source-inhibit acceptance remain circuit gates.
The ±2µA powered-off leakage row is specified at VDD=0; it is not a guaranteed
continuous bound over the undefined low-supply region. Package acceptance alone
does not select this circuit or establish RBF/back-power closure.
