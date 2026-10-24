# EPS candidate libraries

These symbols and manufacturer-derived land patterns were created through Konnect for the Rev B controller study. They are draft candidates and are not registered into the fabricated EPS project.

| Device | Active symbol in `Ember_EPS_Candidates` | Draft footprint |
|---|---|---|
| Historical mislabeled N map; do not use as GP | `STM32G0B1KET6_GP_DRAFT_v2` (identity correction pending) | `ST_LQFP32_7x7mm_P0.8mm_DRAFT` |
| TCAN3413DR | `TCAN3413D_DRAFT_v3` | `TI_D0008A_SOIC8_3.9x4.9mm_P1.27mm_DRAFT` |
| ECS-3225MV-160-BN-TR | `ECS_3225MV_DRAFT_v2` | `ECS_3225MV_3.2x2.5mm_DRAFT` |

The 2026-10-23 [pinout correction](../verification/stm32_gp_candidate_verification.md) withdraws the earlier GP identity and selects STM32G0B1KET6N. Fresh native mapping and symbol identity are required before integration.

Earlier versions remain as superseded study trials. CAN v2 was an unsuccessful orientation trial; use v3 for continued validation. Placed scratch instances have explicit footprint assignments, but library defaults for Footprint and Description still need completion through Konnect before library acceptance.

See the [verification index](../verification/README.md) for manufacturer references, exported pad checks and electrical limitations. Pin/pad readback and visual review do not establish assembly acceptance, final board fit or fabrication readiness.

## Protection study

`Ember_EPS_Protection.kicad_sym` adds `PESD2CANFD24V_T_DRAFT` for a separate disposable TVS study. Pin/pad identity is checked against a standard SOT-23 comparison; land-pattern/assembly and electrical acceptance remain open. The symbol is not placed in the controller circuit. See [candidate verification](../verification/can_tvs_candidate_verification.md).

## Power-stage study

`Ember_EPS_Power.kicad_sym` and `Ember_EPS_Power.pretty` add the active `LMR51635XDDCR_DRAFT_v2` symbol and `TI_DDC0006A_SOT23_6_DRAFT` footprint. Six physical leads/pads are checked against TI’s top-view pin map and example lands through exports and disposable renders. Version 1 is superseded. Default symbol Footprint/Description and assembly settings remain incomplete; explicit scratch instance fields are present. See the [essential buck draft](../verification/essential_buck_stage_draft.md). These libraries are not registered into Rev A.

## Integrated recovery study

The recovery library includes approved Panasonic `Panasonic_CP_D8_6.3x7.7mm_REVIEW` and `Panasonic_CP_F_8x10.2mm_REVIEW` land-pattern constructions for C13–C15 and C7. Both use positive pad 1 at left in component view, exact manufacturer recommended lands and maximum-body courtyards. Query-back and disposable saved-board exports/renders agree. Fabrication text, solder/stencil and mechanical/environmental qualification remain open; see [construction evidence](../verification/panasonic_bulk_footprints.md).

`Ember_EPS_Recovery:TPS552872RYQR_REVIEW` and `TI_RYQ0021A_DRAFT` are project-owned review candidates. The user approved TI-derived construction and a bright-green review callout on 2026-10-23; this did not approve production use. Query-back and disposable renders cover 21 electrical numbers; pad 9 is a three-object composite (23 pad objects total). The editable [development project](../studies/recovery_5v/recovery_5v.kicad_pro) has portable project-local table references. See [design/acceptance limits](../design/rev_b_5v_recovery_design.md).
