# Panasonic recovery-supply bulk footprints

2026-10-23. The user approved manufacturer-derived D8/F construction, pad 1 positive, maximum-body clearances, query-back and rendered comparison. These are project-owned **review candidates**; construction approval does not qualify soldering, stencil, mechanical retention or the hybrid capacitors for flight.

Sources: Panasonic hybrid-capacitor catalog, [manufacturer PDF](https://industrial.panasonic.com/content/data/CP/PDF/news2014/en/VH_E.pdf), printed p. 13, Land/Pad Pattern; [ZK catalog, 01-Sep-2025](https://industrial.panasonic.com/cdbs/www-data/pdf/RDD0000/ABA0000C1229.pdf), p. 1, maximum body dimensions. The exact selected [EEHZK1V101XP](https://industrial.panasonic.com/ww/products/pt/hybrid-aluminum/models/EEHZK1V101XP) and [EEHZA1H680P](https://industrial.panasonic.com/ww/products/pt/hybrid-aluminum/models/EEHZA1H680P) package dimensions were checked separately. The land table and package drawings were rendered and inspected during this design work.

## Construction and mapping

All dimensions are mm, front/component view, footprint-local X right and Y down. These two-terminal capacitors have no manufacturer lead numbering: the project assigns **pad 1 to positive at left**, matching the positive pin of the existing `Device:C_Polarized` symbol. The fabrication base chamfer and visible silkscreen `+` identify that side. There are exactly two distinct electrical pads and no holes or extra exposed pad.

| Footprint in `Ember_EPS_Recovery` | Instances | Positive pad 1 centre | Negative pad 2 centre | Each rectangular land | Inner gap | Courtyard half-size X/Y |
|---|---|---|---|---|---|---|
| `Panasonic_CP_D8_6.3x7.7mm_REVIEW` | C13–C15 | (−2.50, 0) | (+2.50, 0) | 3.20 × 1.60 | 1.80 | 4.35 / 3.65 |
| `Panasonic_CP_F_8x10.2mm_REVIEW` | C7 | (−3.55, 0) | (+3.55, 0) | 4.00 × 2.00 | 3.10 | 5.80 / 4.50 |

Each pad uses F.Cu, F.Mask and F.Paste with no drill. Nominal fabrication outlines show the circular can and insulating base. Courtyards use at least 0.25 mm beyond the maximum body and pad envelope: D8 maximum transverse body/base size 6.8 mm; F 8.5 mm. Body-height maxima are 8.0 and 10.5 mm respectively. No 3D model is assigned. The courtyard describes the component/pad assembly envelope, not a reserved vent, harness or thermal keepout.

The native schematic assigns all four instances explicitly. Fresh CLI netlist verifies C7.1 on `SYS_PWR_PERMITTED`, C13–C15.1 on `5V0_RECOVERY_RAW`, and all four pin-2 connections on GND. Existing net endpoint sets are unchanged.

## Independent checks

- Konnect library query-back verifies numbers, dimensions, centres, front-layer sets, absence of drills, and maximum-envelope courtyard margins.
- Disposable C13 and C7 instances were placed beside the existing IC package in the **study PCB only**. Konnect's supported closed-board path persisted them because live IPC was unavailable. This PCB has no stage connectivity, placement or routing acceptance.
- Queried placed-pad positions match the chosen locations. An independent KiCad IPC-2581 export verifies both package pin numbers, local coordinates and exact standard rectangular primitives.
- The actual [copper/silkscreen/courtyard render](../studies/recovery_5v/package.png) was inspected: both positive markers are beside the correct land and silk is clear of pads.
- The actual [fabrication render](../studies/recovery_5v/package-fab.png) was also inspected. Its long default Value texts overlap across scratch parts. Pad numbering and outlines are visible, but fabrication-text presentation is **not accepted**. The exposed library API cannot reposition those fields, and the placed-value edit requires unavailable live IPC. No source-file workaround was used.
- Fresh schematic rendering is unchanged by the footprint-field assignments; the previously inspected page and circuit details still apply. Direct KiCad 10 ERC remains **0 errors, 0 warnings**.

See [machine-readable query/export evidence](evidence/2026-10-23_recovery_5v_panasonic.json), [saved component/connection verification](evidence/2026-10-23_recovery_5v_verified.json), and the [development BOM](../studies/recovery_5v/development_bom.csv). All 28 development components now have explicit footprint IDs; complete package qualification is not implied by nonblank fields.

Remaining: fabrication text, stencil/reflow acceptance, vent and stack clearance, mounting/retention, capacitor effective ratings and environment. The source-OV, startup, cold-transient, thermal and S11 schematic-presentation gates in the [converter design](../design/rev_b_5v_recovery_design.md) remain separate.
