> Superseded availability status: signed-in live checks are complete for all 32 existing codes. See `jlcpcb_live_audit.md`: U9 and the exact D15 option are preorder-only; J9 has an in-stock listing. Earlier login-blocked and catalogue-only statements below are historical.

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


# Complete BOM catalogue audit — 2026-09-09

Audit scope: 127 entries from the native exported schematic netlist. Three are intentional DNP headers (J6/J7/J8); six are bare test pads (TP11–TP16), requiring no purchased component. Of 118 purchasable placements, 98 resolve to 32 exact JLC catalogue codes; 20 placements have missing/placeholder codes. Existing nonempty manufacturer fields agree with the corresponding catalogue MPNs. This is a catalogue identity audit, not a complete electrical-equivalence or live-stock approval.

## Live verification

The browser-rendered JLCPCB product panels showed:

- **C40976557 / 0402HP-10NXGRW: 19 in stock and available to order.** Eight per board; sufficient for at most two boards before assembly allowance. This supersedes the older indexed count of five.
- **C40877572 / 0805HP-221XGRC: 255 in stock and available to order.** Candidate for L16; current schematic specifies the J variant. No substitution applied and RF qualification remains open.

Evidence URLs: [10 nH filter inductors](https://jlcpcb.com/partdetail/Coilcraft-0402HP10NXGRW/C40976557), [L16 candidate](https://jlcpcb.com/partdetail/Coilcraft-0805HP221XGRC/C40877572). Stock is an observation, not a reservation. Build quantity is awaiting the user's answer.

JLCPCB's search redirected to account sign-in. Further live verification through search requires sign-in. Cached quantities below must not be represented as current confirmed stock.

## Missing-code placements and candidates

| References | Candidate exact part / JLC code | Catalogue stock | Remaining check |
|---|---|---:|---|
| Y2 | SI5351A-B-GTR / C504891 | 36,118 | Tape/reel ordering variant, exact specification and live stock |
| H3/H4 | ESQ-126-39-G-D / C7466599 | 5 | Exact existing header, two per board; live quantity risk |
| J9 | Molex 73415-1471 footprint | — | No in-stock exact match found; source exact part or qualify connector/land-pattern replacement |
| C83 | FH 0402CG102J500NT / C53547 | 296,985 | 1 nF candidate; circuit requirements and live stock |
| L16 | 0805HP-221XGRC / C40877572 | 255 live | Review tolerance variant; RF choke qualification still open |
| U5 | MCP6022T-I/SN / C57639 | 17,659 | SOIC-8 exact ordering option and live stock |
| U10 | Mini-Circuits ADE-1+ / C2942210 | 191 | Verify manufacturer identity, exact package and live stock |
| C102 | FH 0402CG101J500NT / C1546 | 4,270,941 | 100 pF candidate; RF suitability and live stock |
| C103/C104 | Samsung CL10B105KA8NNNC / C29936 | 1,412,648 | 1 µF 0603 candidate; voltage/DC-bias requirements and live stock |
| C105/C106 | Existing CL05B104KO5NNNC / C1525 | 35,496,429 | Reuse existing 100 nF 0402 selection after rail check/live stock |
| D15 | PESD5V0F1BRLD | — | Exact part not found in in-stock search; alternatives have different suffix/package/capacitance and need qualification |
| R35/R36/R37 | 0402WGF1002TCE / C25744 | 29,028,423 | 10 kΩ 0402 candidate; requirements and live stock |
| U11 | PE4259-63 / C470892 | 6,750 | Original manufacturer part; exclude similarly named clones, verify live stock |
| U12 | TLV75530PDBVR / C507268 | 1,183 | Exact ordering code; verify manufacturer/live stock |
| U13 | SN74LVC1G17DBVR / C7836 | 5,899 | Verify TI identity and live stock; similarly named other-manufacturer entries exist |

All rows are candidates or unresolved items, not automatically approved substitutions. The CSV lists every original BOM entry and its status.

## Additional supply risks

- Current 10 nH Coilcraft part has 19 live pieces. Murata **LQW15AN10NG00D / C90642** has 38,134 catalogue pieces and is a candidate for evaluation, not a drop-in approval. Replacing the inductor invalidates the use of the Coilcraft equivalent model for that part; rerun the filter study with the selected part's model before committing.
- R20/R21 **AF0402FR-0722KL / C4230864** have 61 catalogue pieces; evaluate a more available 22 kΩ 0402 option.
- R27/R33 **AC0402JR-0747KL / C144710** have 191 catalogue pieces.
- L17/L18 **0402HP-15NXJRW / C39750903** have 137 catalogue pieces.

## Required next work

1. Complete live availability checks after JLCPCB sign-in; record quantities against actual build size and assembly allowance.
2. Resolve connector and ESD-diode sourcing before changing their footprints.
3. Validate the better-stocked inductor's RF model and the L16 tolerance variant.
4. Populate qualified exact ordering fields and synchronize schematic/PCB using KiCad tools; rerun affected checks.

No schematic or PCB changes in this audit. The previously verified layout result is unchanged; this audit adds procurement blockers rather than claiming fabrication readiness.
