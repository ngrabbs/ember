# Charger and BMS library construction proposal

2026-10-23. Proposed project-owned candidates are **LTC4162IUFD-LADM#TRPBF** and **BQ40Z50RSMR-R2**. Registry searches returned no matching symbols. Existing generic QFN lands differ from the manufacturer patterns: the LTC candidate has longer lands and shifted row centers, while available 4 mm QFN32 examples use a substantially larger exposed pad than TI's 1.4 mm square. Construct exact review candidates rather than treating those as accepted package substitutions.

**Construction authorized 2026-10-23:** the user explicitly answered “Approve
charger and BMS construction” for these two exact parts under this document,
including exposed pads, full pin/pad checks, disposable render verification and
the bright-green enclosure/callout alternative to unsupported symbol-body color.
This authorizes construction; the resulting parts retain their custom review
markers and must pass the acceptance checks below before circuit integration.

## Construction and review rules

Use registered project-local libraries and portable paths. Each IC has one readable rectangular symbol, grouped by function with power above, grounds below and distinct physical pins retained even when functions repeat. Use a 1.27 mm electrical grid, show every pin number/name, exact manufacturer part number, footprint and datasheet metadata. Do not reorder physical numbering or merge repeated supply/switch pins. No new global-library edits are permitted.

Keep a bright-green **CUSTOM — REVIEW REQUIRED** enclosure/callout on disposable and real instances. Konnect's current symbol-authoring schema cannot set body graphics color; the enclosure is the proposed alternative under schematic policy S08. The candidates remain under review until physical pin/pad joins, query-back and actual schematic/footprint renders pass. Electrical ERC and rendered-sheet inspection are separate records.

Footprints use front copper/mask/paste, manufacturer nominal lands, a fabrication outline covering the maximum body dimensions, clear pin-1 markers and a courtyard at least 0.25 mm beyond the maximum body/pad envelope. No thermal via or stencil process is accepted by these nominal copper rules; finalize those with assembly/layout review. Check actual exported pad geometry and orientation before circuit use.

## LTC4162 UFD package

Authority: [LTC4162-L Rev A](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf), printed pp.3–4, 10–11 and 50, UFD drawing 05-08-1712 Rev C. Pin diagram is top view; the mechanical exposed-pad view is explicitly bottom view and must be mirrored when joining it to front-side lands. Normalize to a 4 mm X / 5 mm Y body, pin 1 upper-left on the left row; counterclockwise numbering in component view.

| Physical leads | Names in order |
|---|---|
| 1–8 | BOOST, INTVCC, VOUTA, CLN, CLP, INFET, VIN, VCC2P5 |
| 9–14 | NTCBIAS, NTC, RT, SMBALERT, SCL, SDA |
| 15–22 | DVCC, SYNC, CELLS0, CELLS1, BATSENS+, CSN, CSP, BATFET |
| 23–28 | PGND, PGND, SW, SW, VOUT, VOUT |
| 29 | AGND exposed pad, electrical ground |

Copper proposal after rotating the land drawing to this view: 28 lands, 0.70 mm radial length by 0.25 mm tangential width, 0.50 mm pitch. Left/right row centers are X = ±1.90 mm, with eight centers from Y = −1.75 to +1.75 mm. Top/bottom row centers are Y = ±2.40 mm, with six centers from X = −1.25 to +1.25 mm. Exposed pad 29 is 2.65 × 3.65 mm at the origin. Counts: 28 perimeter leads plus one exposed electrical pad, 29 unique symbol pins and 29 unique electrical pad numbers. Numbered electrical pads must be distinguished from unnumbered paste windows.

## BQ40Z50 RSM package

Authority: [TI SLUSCS4C](https://www.ti.com/lit/ds/symlink/bq40z50-r2.pdf), printed pp.3–4 and package addendum RSM0032A 4219107/A, pp.52–54 in the retrieved 55-page PDF. Normalize to component/front view with pin 1 upper-left on the left row, counterclockwise numbering. Confirm this using both the pin-function drawing and land drawing rather than reading the exposed-pad view as top view.

| Physical leads | Names in order |
|---|---|
| 1–8 | PBI, VC4, VC3, VC2, VC1, SRN, NC, SRP |
| 9–16 | VSS, TS1, TS2, TS3, TS4, NC, BTP_INT, PRES/SHUTDN |
| 17–24 | DISP, SMBD, SMBC, LEDCNTLA, LEDCNTLB, LEDCNTLC, PTC, PTCEN |
| 25–32 | FUSE, VCC, PACK, DSG, NC, PCHG, CHG, BAT |
| 33 | Exposed thermal pad, connect to VSS |

Copper proposal: 32 perimeter lands, 0.60 mm radial length by 0.20 mm tangential width, 0.40 mm pitch. All row centers are ±1.90 mm from the origin, with eight tangential centers from −1.40 to +1.40 mm. Corner radius 0.05 mm. Exposed pad 33 is 1.40 × 1.40 mm at the origin. Counts: 32 perimeter leads, including three internally NC leads, plus one exposed electrical ground pad; 33 unique symbol pins and 33 unique electrical pad numbers. Show the three NC pins and explicitly classify unused connections against the datasheet.

## Acceptance before integration

Reconcile every lead's function and electrical type against the full pin table; include all grounds and exposed pads. Query libraries and disposable instances, verify every saved pad center/size/layer, then inspect full and detail renders for numbering direction, pin-1 key and circuit readability. Do not infer production acceptance from successful authoring. The [completion ledger](rev_b_completion.md) retains configuration, protection, thermal and assembly work separately.
