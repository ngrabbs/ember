# Verified ordering fields completed — 2026-09-09

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


Added exact JLCPCB and manufacturer ordering fields to both schematics and PCB:

| References | JLCPCB code | Exact manufacturer part |
|---|---|---|
| H3, H4 | C7466599 | Samtec ESQ-126-39-G-D |
| U10 | C2942210 | Mini-Circuits ADE-1+ |
| U11 | C470892 | pSemi PE4259-63 |
| U12 | C507268 | TI TLV75530PDBVR |
| U13 | C7836 | TI SN74LVC1G17DBVR |

These are purchasing-field completions for existing parts, not circuit substitutions. Previously observed live quantities are recorded in the live-stock audit; header quantity remains limited to five pieces and the build quantity is still unresolved.

Konnect applied schematic edits with the schematic editor closed. The previously authorized native KiCad API synchronized the PCB fields with the PCB editor closed; the board was then reopened. Query-back and a full schematic structure comparison confirmed that only the requested ordering properties changed. PCB read-back confirmed matching fields and unchanged placement, pad nets and routing. Fresh DRC: **0 errors, 1 existing header-silkscreen warning, 0 unconnected items**.

Missing ordering-code placements are reduced from 20 to 14. U9 and D15 remain unchanged: their candidate substitutions require physical package work and RF qualification. Native schematic ERC was not rerun for this metadata-only change; the complete schematic structure outside the ordering properties is unchanged.

The prior native netlist export predates these metadata changes. Its connectivity remains valid, but regenerate it before generating a manufacturing BOM. No commit or purchase was made.
