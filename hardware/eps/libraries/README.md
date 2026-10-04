# EPS candidate libraries

These symbols and manufacturer-derived land patterns were created through Konnect for the Rev B controller study. They are draft candidates and are not registered into the fabricated EPS project.

| Device | Active symbol in `Ember_EPS_Candidates` | Draft footprint |
|---|---|---|
| STM32G0B1KET6 GP LQFP32 | `STM32G0B1KET6_GP_DRAFT_v2` | `ST_LQFP32_7x7mm_P0.8mm_DRAFT` |
| TCAN3413DR | `TCAN3413D_DRAFT_v3` | `TI_D0008A_SOIC8_3.9x4.9mm_P1.27mm_DRAFT` |
| ECS-3225MV-160-BN-TR | `ECS_3225MV_DRAFT_v2` | `ECS_3225MV_3.2x2.5mm_DRAFT` |

Earlier versions remain as superseded study trials. CAN v2 was an unsuccessful orientation trial; use v3 for continued validation. Placed scratch instances have explicit footprint assignments, but library defaults for Footprint and Description still need completion through Konnect before library acceptance.

See the [verification index](../verification/README.md) for manufacturer references, exported pad checks and electrical limitations. Pin/pad readback and visual review do not establish assembly acceptance, final board fit or fabrication readiness.

## Protection study

`Ember_EPS_Protection.kicad_sym` adds `PESD2CANFD24V_T_DRAFT` for a separate disposable TVS study. Pin/pad identity is checked against a standard SOT-23 comparison; land-pattern/assembly and electrical acceptance remain open. The symbol is not placed in the controller circuit. See [candidate verification](../verification/can_tvs_candidate_verification.md).
