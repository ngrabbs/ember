# Charger/BMS library candidates — partial acceptance

2026-10-23, basis `6be2bc7`. Construction was explicitly authorized under `hardware/eps/design/rev_b_charger_bms_library_rules.md`. Both candidates remain **CUSTOM — REVIEW REQUIRED** and are **not accepted for real circuit placement**: the disposable placed-board acceptance gate is blocked.

## Saved candidates and physical checks

Portable project library nickname `Ember_Charger_BMS_Review` contains `LTC4162IUFD-LADM_TRPBF` (Value and MFG P/N = **LTC4162IUFD-LADM#TRPBF**) and `BQ40Z50RSMR-R2`. The symbol and footprint files live under `hardware/eps/rev_b/libraries/`; registrations in the integrated and disposable project tables use `${KIPRJMOD}` relative paths. Existing table entries were preserved. No global library was changed.

`physical_map.csv` contains **62 per-lead rows** with source function, symbol name/type, pad number, exact X/Y/size/layers, drawing view/direction and electrical-type reconciliation. All 29 LTC and 33 BQ library pins/pads were queried back, as were both disposable schematic instances. Every pin endpoint is on the 1.27 mm grid. The LTC footprint has 28 separate perimeter pads plus AGND EP29; BQ has 32 perimeter pads plus EP33 allocated to VSS under the approved construction rules. There are no duplicate pad numbers, mechanical pads, drills, thermal vias or unnumbered paste windows. Repeated SW, PGND and VOUT pins are retained separately.

Authority is ADI **LTC4162-L Rev A**, printed pp.3–4/10–11/50, UFD drawing **05-08-1712 Rev C**, and TI **SLUSCS4C**, printed pp.3–7, with **RSM0032A 4219107/A** package drawings on pp.52–54 of the retrieved 55-page PDF. The ADI exposed-pad mechanical view is bottom view; it was mirrored/rotated to the front/component 4 mm X / 5 mm Y view. Both front-side maps place pin 1 upper-left on the left row and count counterclockwise, with footprint X right and Y down. Manufacturer pin and land figures were actually opened and inspected. `source_manifest.json` records PDFs/figure paths and hashes.

LTC copper is 0.70×0.25 mm on left/right rows X=±1.90 and 0.25×0.70 mm on top/bottom Y=±2.40, 0.50 mm pitch; EP29 is 2.65×3.65 mm. BQ copper is 0.60×0.20 mm radially, rows ±1.90, 0.40 mm pitch, 0.05 mm corner radius; EP33 is 1.40×1.40 mm. Fab outlines cover maximum 4.1×5.1 / 4.1×4.1 mm body envelopes, with chamfered pin-1 corners. Courtyards extend at least 0.25 mm beyond the maximum body/pad envelope. Explicit silk pin-1 dots are inside the courtyard.

BQ NC7/14/29 are passive internally unconnected leads because TI permits floating or VSS ties. BTP_INT and FUSE retain output types despite documented unused-to-VSS instructions: future intentional ties need an explained ERC disposition, not weakened pin types. SMBC/SMBD retain bidirectional input/open-drain behavior. LEDCNTL A/B/C are bidirectional per the equivalent diagram and input/high/low output specifications, rather than open collector. DISP is modeled as the documented display-control input. PTCEN retains TI's analog-input classification. LTC VOUT27/28 are power inputs to the switching regulator despite the pin name; SW25/26 are separate switching power outputs. `physical_map.csv` explains every lead.

## Electrical evidence and preserved design

Run `python3 hardware/eps/verification/rev_b/charger_bms_library/verify_library.py` from the repository root. It checks all saved pin/pad querybacks, instance coordinates, exported embedded pin types and exact MFG fields, counts, geometry, relative registration paths, source hashes and the unchanged integrated component/endpoint graph.

All seven integrated schematic files and the native project settings are byte-identical to the checkpoint. The only changes to previously tracked KiCad sources are the two portable library-table registrations. Historical study sources are untouched. The freshly exported integrated root remains **160 parts / 91 nets**, with **16 existing unconnected MCU-pin ERC errors / zero warnings**.

The disposable sheet intentionally has no wires, source flags or NC masking. Its XML contains **62 separate singleton nets**, one per lead; ERC reports 94 errors (58 `pin_not_connected`, 23 `pin_not_driven`, 13 `power_pin_not_driven`) and zero warnings. These are unwired inspection-fixture findings, not a circuit acceptance test. ERC violation counts are not substituted for the exact exported per-lead singleton check.

## Actual rendered inspection

`symbols.png`/`symbols.pdf` show the saved B-page fixture; `charger_symbol.png` and `bms_symbol.png` are detail crops. All were actually inspected, including the corrected clear U1 identification area. Bright-green **CUSTOM — REVIEW REQUIRED** callouts implement the user-approved alternative to unsupported body color. The body remains its normal rendered color. Pin numbers/names, separate repeated leads and exposed-ground pins are visible. Exact MPN metadata is retained; S11 custom-field style/default-library-field authoring remains an API limitation, so the visible Value provides the exact MPN and instance fields are verified independently.

Both **saved library footprints** were exported by KiCad CLI `fp export svg`, rasterized with `rsvg-convert`, and inspected at copper/silk/courtyard and numbered fab detail scales. Pin-1 keys and counterclockwise row numbering agree with the manufacturer figures; the UFD large EP29 and RSM small EP33 are clear. Fab sketch overlays cross some tiny pad-number strokes; the exact API pad-number/coordinate checks provide the full numeric record. Root independently inspected the final full schematic, both symbol details and both sets of library footprint details.

These are **library renders**, not disposable placed-board renders. The blank scratch PCB is preserved, with zero placed footprints. Do not present the library exports as completing the instance gate.

## Blocked gate and remaining work

**Revalidated 2026-10-23, 22:14 UTC:** the configured IPC connection still
serves only COMMS and reports the requested scratch board as not open. Desktop
inventory now explicitly reports that the Mac is locked and automatic unlock
failed. This prevents safe inspection/switching of the editor; the user must
unlock the Mac. Save existing KiCad work, close PCB editors and open
`disposable/charger_bms_check.kicad_pcb` first, then verify its exact absolute
path through Konnect before placing anything. No locked-desktop bypass or
unrelated save/discard was attempted. The existing schematic mutation owner is
idle with mutation held.

Konnect's active startup transport is `ipc:///tmp/kicad/api.sock`, serving the unrelated live comms `transceiver.kicad_pcb`. `place_component` refused the scratch path because that board was not open; during the manager modal it also returned `NNG recv failed: Timed out` and explicitly stated the board was not modified. The scratch PCB was successfully opened in a separate standalone editor, which owns `/tmp/kicad/api-22683.sock`; no exposed tool can select/reconnect to that endpoint. The manager modal was canceled and the configured socket became responsive again, still serving only comms. Agent and root attempts to inspect the original app's saved/dirty state then failed with computer-use server error **-10005: timeoutReached**. No unrelated save/discard, socket/config edit, process termination or custom-backend bypass was attempted.

Resume only with a supported transport/editor binding and verified exact scratch document. Place both footprints through Konnect, query every instance pad, save through Konnect, export and actually inspect the placed-board render. Until then physical board-instance acceptance remains **BLOCKED**, and the candidates stay out of real circuits. Nominal copper/paste/mask does not qualify stencil segmentation, assembly tolerances, thermal vias, application circuitry, sourcing, fit or thermal behavior. Review markers remain.

`changed_files.txt` lists this boundary's exact deliverable files; `candidate_source_sha256.json` ties querybacks to native sources and `evidence_sha256.json` records deliverable evidence hashes. Generated scratch PRL/lock/history files and routine ignored CLI logs are excluded.

## Committed-checkpoint verifier correction

The documented verifier was rerun against the committed tree and failed its
native-file change assertion: that assertion expected only the two modified
library tables, omitting the eight approved additions once they became tracked.
The correction requires the exact ten source-manifest paths and their Git
statuses: two modified tables and eight added library/fixture sources. Every
source must still match its reviewed hash, and the eight existing integrated
schematic/project files must remain unchanged. Stage approved additions before
using this check on a new checkpoint; untracked files are not delivery evidence.

The corrected verifier passes all 62 physical rows, saved schematic-instance
checks and current native-source hashes. The integrated protection verifier was
also rerun successfully. The result remains **PARTIAL**, with both disposable
board-instance flags false. No ERC or rendered-board pass was manufactured, and
no KiCad source, project setting or library changed in this correction.
