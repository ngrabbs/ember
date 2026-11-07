# UCC33020 library construction rules — APPROVED

2026-10-24. User explicitly approved: **“Approve UCC33020 construction under those rules.”** This authorizes the exact symbol/footprint and disposable verification below, including the bright-green review enclosure alternative. Circuit integration still requires electrical checks. At approval, no UCC native library or circuit had been authored; the ADuM approval is separate.

## Sources and selected identity

Texas Instruments **UCC33020RAQR**, SLUSFK4A Rev A, May 2025, [manufacturer datasheet](https://www.ti.com/lit/ds/symlink/ucc33020.pdf). The downloaded document contains the 7-Nov-2025 package addendum: Active/Production, VSON-FCRLF RAQ, 12 logical pins, 3000 large tape-and-reel, −40 to +125°C, marking U33020. This is an ordering-table observation, not a procurement or qualification result.

Actual source figures inspected: physical pin functions p4; electrical tables pp6–8; typical application p23; package **RAQ0012C**, 4230399/A, 01/2024, pp34–36. Source hashes, page images and stock TLV767 querybacks are in [candidate evidence](../verification/bms/ucc33020_candidate/README.md). Parent symbol search returned no UCC33020; independent configured footprint searches `RAQ`, `VSON-12`, `UCC33` each returned zero. Recheck configured KiCadLib and official libraries immediately before any approved authoring.

## Proposed symbol

Use existing portable project-owned `Ember_Charger_BMS_Review` library; proposed identifier `Ember_Charger_BMS_Review:UCC33020RAQR_REVIEW`. One unit, twelve separate pins, no stacked or omitted grounds. Keep primary pins on the left and secondary pins on the right, with an isolation divider and 1.27 mm pin grid. Preserve every electrical type; do not change a type to silence ERC.

| Lead | Function | Proposed type | Front footprint X/Y mm |
|---|---|---|---|
| 1 | EN/FLT | bidirectional: enable input plus low fault output | −2.4 / −1.625 |
| 2 | VINP | power_in | −2.4 / −0.975 |
| 3 | GNDP | power_in | −2.4 / −0.325 |
| 4 | GNDP | power_in | −2.4 / +0.325 |
| 5 | GNDP | power_in | −2.4 / +0.975 |
| 6 | GNDP | power_in | −2.4 / +1.625 |
| 7 | SEL | input | +2.4 / +1.625 |
| 8 | VCC | power_out | +2.4 / +0.975 |
| 9 | GNDS | power_in | +2.4 / +0.325 |
| 10 | GNDS | power_in | +2.4 / −0.325 |
| 11 | GNDS | power_in | +2.4 / −0.975 |
| 12 | GNDS | power_in | +2.4 / −1.625 |

Every row uses the p4 **top view**, pin 1 upper left, counterclockwise numbering: 1–6 down the left, 7–12 up the right. The p34 underside drawing reverses vertical orientation; do not copy that drawing as a front footprint. No NC, mechanical contacts or central exposed pad exist. Section 10.1 explicitly says no thermal pad: ground contacts dissipate heat. A generic thermal-pad note in the appended land drawing does not authorize adding pad 13.

Require `Reference`, `Value`, `Footprint`, `Datasheet`, `MFG P/N=UCC33020RAQR`, `Manufacturer=Texas Instruments`, `PackageSize=RAQ0012C`, description and review status. Use a visible **CUSTOM — REVIEW REQUIRED** bright-green enclosure/callout, retaining the known unsupported body-color limitation. This alternative is included in the explicit UCC approval recorded above; the separate ADuM approval is not used as blanket authorization. Keep the marker through development acceptance.

## Proposed footprint and explicit decomposition

Proposed ID `Ember_Charger_BMS_Review:TI_RAQ0012C_VSON12_5x4mm_CombLand_REVIEW`. Nominal front-view body X=5.0, Y=4.0 mm; maximum 5.1 × 4.1 mm, height 1.05 mm. Lead pitch 0.65 mm and row centers X=±2.4 mm per p35. All pads SMD, no drills or vias. No imported/unverified 3D model.

The manufacturer has **12 logical contacts but eight continuous copper regions**: six isolated small contacts and two comb-shaped ground regions joining leads 3/4/5 and 9/10/11. Preserve all twelve symbol numbers. Proposed supported rounded-rectangle decomposition:

- Twelve numbered tooth objects at the table coordinates, each 0.60 × 0.30 mm, corner radius 0.05 mm (`roundrect_rratio=1/6`), layers F.Cu/F.Mask.
- Left comb spine, duplicate number **3**, center (−2.25,+0.325), size 0.30 × 1.60 mm, radius 0.05 mm; right spine duplicate number **9**, center (+2.25,−0.325), same size/radius/layers. This forms the required 0.30 mm inner rail and preserves distinct logical ground aliases. Grounds 3/4/5 and 9/10/11 must each resolve to one net in every fixture and circuit.
- Fourteen separate unnumbered F.Paste-only copies of those tooth/spine shapes. Their union follows the manufacturer's p36 full comb paste example for a 0.125 mm stencil. Record overlaps explicitly and inspect the exported aperture union; do not count overlapping objects as separate physical stencil openings.
- Fourteen unnumbered F.Mask-only shapes expanded by 0.07 mm on every side: width/height +0.14 mm, radius 0.12 mm. This implements the p35 preferred NSMD opening despite absent native mask-margin API. The mask union includes the base F.Mask regions on the numbered copper pads and these larger blank shapes; no extra numbered mask-only object is permitted. Verify the saved/rendered union and mask clearance between distinct nets.

**Raw object contract: 42 total = 14 copper + 14 paste-only + 14 mask-only.** Copper number multiplicities: 3 and 9 each twice; all other 1–12 once. There are 12 unique logical copper numbers, eight connected copper regions, eight connected paste regions, eight mask regions, zero central EPs and zero mechanical/drilled pads. Check raw lists before any dictionary conversion, exact counters, layer sets, coordinates, sizes and radii. A future supported polygon-pad path could avoid decomposition but is outside this exact proposal until reviewed.

This overlapping rounded-rectangle alternative cannot reproduce the manufacturer's internal concave R0.05 fillets exactly. `check_decomposition.py` compares nominal uniformly R0.05-filleted combs against the proposed unions on a 0.001 mm raster: symmetric-difference area 0.002124 mm² per comb, 0.004248 mm² combined; all differing samples within 0.043 mm in each coordinate of a sharp corner (0.052 mm conservative raster bound). The opened comparison image shows the missing concave fillets. This is a proposal calculation, not saved-footprint proof; retain the manufacturing/stencil/thermal review item. Do not label this an exact TI copper outline.

F.Fab: closed 5.0 × 4.0 mm nominal body with visible pin-1 chamfer, 0.10 mm stroke; readable value/reference. F.SilkS: top/bottom body lines outside the maximum Y envelope, clear of mask, plus pin-1 marker outside pad/mask. F.CrtYd: closed rectangle X=±3.10, Y=±2.40, unfilled 0.05 mm stroke; derived from maximum body and pad/mask extents plus ≥0.25 mm clearance. Verify actual marker/text extents separately. No copper under the isolation gap; system copper/creepage and heat-spreading remain PCB-stage requirements, not proven by courtyard.

## Required acceptance after approval

Query every saved library pin/field and raw footprint object against the table and dimensions. Build a **new independent disposable** project; place the symbol and actual PCB footprint via Konnect, query and save, requery all raw live/saved pads, and compare counters without collapsing duplicates. Render/open/inspect schematic full/detail plus front copper, paste, mask, silk, courtyard and numbered fab. Inspect pin-1 key, top/bottom translation, comb continuity, distinct-domain gap, apertures and text. Export disposable CLI netlist/ERC; document intentional unwired pins without fake NCs. Preserve every historical fixture and main design hash. No real circuit placement until this gate and electrical selection pass; no production/assembly/flight claim.

## Electrical selection remains open

UCC33020 offers defined EN thresholds, soft-start timeout, output OVP and hiccup recovery; these do not establish the complete supply's transient behavior. No explicit prebiased-start guarantee was found. SEL is sampled while secondary VCC is below 2.7 V. Retain input-current/inrush, minimum effective capacitance, load envelope, startup/fault/restart, LDO dropout/reverse current and output margin gates. Only ISO1540 side 2 and its pullups would use the proposed isolated supply; system GND and GND_BMS_RAW remain joined only through the existing current shunt. No new native construction or circuit selection is implied by this proposal.
