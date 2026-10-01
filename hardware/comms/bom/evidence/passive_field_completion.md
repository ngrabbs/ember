# Passive ordering fields — 2026-09-09

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


Completed seven placements in both schematic and PCB:

| References | JLCPCB code | Manufacturer part |
|---|---|---|
| C83 | C53547 | FH 0402CG102J500NT |
| C102 | C1546 | FH 0402CG101J500NT |
| C105, C106 | C1525 | Samsung CL05B104KO5NNNC |
| R35, R36, R37 | C25744 | UNI-ROYAL 0402WGF1002TCE |

Exact codes were observed in stock in the signed-in JLCPCB audit on September 9. Stock is not reserved. C83/C102 retain 1 nF/100 pF respectively, using 50 V C0G ±5% 0402 parts. C105/C106 use 100 nF 16 V X7R ±10% 0402 parts. The 10 kΩ ±1% 0402 resistors are rated 62.5 mW; even 5 V across one dissipates only 2.5 mW.

Sources: [C83](https://jlcpcb.com/partdetail/54563-0402CG102J500NT/C53547), [C102](https://jlcpcb.com/partdetail/0402CG101J500NT/C1546), [C105/C106](https://jlcpcb.com/partdetail/CL05B104KO5NNNC/C1525), [resistors](https://jlcpcb.com/partdetail/0402WGF1002TCE/C25744).

Konnect applied the schematic fields. Native KiCad synchronized PCB properties with the editor closed. Reloaded fields match, every other parsed schematic element is unchanged, and PCB placement, pad nets and tracks are unchanged. Fresh DRC: 0 errors, 1 existing header-silkscreen warning, 0 unconnected items. ERC was not rerun for this property-only change.

Seven ordering gaps remain: Y2, J9, L16, U5, C103, C104 and D15. U9 additionally needs replacement because its existing part is out of stock. C103/C104 selection remains pending capacitor DC-bias qualification; [TI requires at least 0.47 µF effective output capacitance](https://www.ti.com/lit/ds/symlink/tlv755p.pdf). The candidate is Samsung CL10B105KA8NNNC, C29936, 1 µF 25 V X7R 0603. No RF replacement or tuning changes were made in this pass. RF performance and antenna mismatch testing remain open.

The native netlist predates the ordering edits and must be regenerated before the final manufacturing BOM. No commit, push or purchase was made.
