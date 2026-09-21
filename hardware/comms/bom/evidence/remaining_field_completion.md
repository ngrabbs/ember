# Clock, op amp and regulator capacitor selections — 2026-09-09

> **Dated record.** Measurements and audit scope apply to the recorded configuration.
> For current work and superseded blockers, see the [comms checklist](../../TODO.md).


| References | Exact manufacturer part | JLCPCB code | Previously observed live stock |
|---|---|---|---|
| Y2 | SI5351A-B-GTR | C504891 | 36,086 |
| U5 | MCP6022T-I/SN | C57639 | 17,659 |
| C103, C104 | CL10B105KA8NNNC | C29936 | 1,411,022 |

Applied ordering fields in schematic and PCB. Y2's R suffix and U5's T suffix specify tape-and-reel; their functional device, package and temperature grade are retained. Capacitor values remain 1 µF and footprints remain 0603; the Voltage field is updated from 16 V to the selected part's 25 V rating.

Manufacturer references: [Skyworks ordering information, page 34](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si5351-B.pdf), [Microchip ordering and SOIC dimensions](https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/MCP6021-Data-Sheet-DS20001685.pdf).

## Capacitor engineering selection

The [Samsung exact-part characteristic sheet](https://datasheet.octopart.com/CL10B105KA8NNNC-Samsung-Electro-Mechanics-datasheet-11897796.pdf) was rendered and visually inspected. Its typical DC-bias curve indicates roughly 10% loss at 3 V and 20% at 5 V. Including nominal ±10% tolerance and X7R ±15% temperature variation multiplicatively gives screening estimates of approximately 0.69 µF at C104 (3 V) and 0.61 µF at C103 (5 V). Both exceed the 0.47 µF design note at this screening level. This is an engineering selection based on typical data, not a guaranteed combined worst-case bound: small-signal amplitude, aging, lot variation and combined bias/temperature behavior still need validation. Retained the existing effective-capacitance design note. TI requires at least 0.47 µF effective output capacitance: https://www.ti.com/lit/ds/symlink/tlv755p.pdf

An alternative mirror of this sheet was corrupt and rendered without the DC-bias graph; it was not used for numerical estimates. The selected readable sheet is typical reference data; bench verification of capacitance/stability remains open, particularly input-capacitor margin at 5 V.

## Validation and remaining work

All schematic units, including all three U5 units, have matching requested fields. Complete parsed schematic structure is unchanged outside the ordering and Voltage properties. Native PCB read-back verified fields, placement, pad nets and routing. Fresh DRC: 0 errors, 1 existing header-silkscreen warning, 0 unconnected items. No electrical values or geometry changed, and ERC was not rerun.

Three ordering gaps remain: J9, L16 and D15. U9 separately remains out of stock and needs replacement. Hold L16 selection until the U9 bias network is finalized, since the new amplifier may require a different choke. J9 has a stocked candidate but awaits land-pattern confirmation. D15 still needs voltage-margin and package qualification. No RF substitution was applied in this pass.

Regenerate the native netlist before the final manufacturing BOM. Stock is not reserved. No commit, push or purchase made.
