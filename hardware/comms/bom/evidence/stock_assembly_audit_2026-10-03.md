# JLCPCB stock and assembly audit — October 3, 2026

**INCOMPLETE — do not order from this audit.** Live browser search checked all
55 embedded supplier codes. Stock is not reserved, and displayed stock is not
proof of orderable quantity with the selected service's assembly allowance.
See the [complete CSV](live_stock_2026-10-03.csv) and [JSON](live_stock_2026-10-03.json).
The Konnect downloaded catalogue did not support exact C-code lookup reliably;
all availability conclusions here use the live rendered JLCPCB rows.

## Qualified substitutions and remaining supply risk

The original stock snapshot is retained for traceability. All three substitutions
are now applied to schematic and PCB with embedded `LCSC Part #`:

| References | Current part | LCSC | Live stock Oct 3 | Nominal for two boards |
|---|---|---|---:|---:|
| L12/L13/L19–L24 | Murata LQW15AN10NG00D | C90642 | 33,826 | 16 |
| U12 | TI TLV73330PDBVR | C882826 | 1,003 | 2 |
| D12/D13 | Lite-On LTST-C190KGKT | C125094 | 613,210 | 4 |

[Pin/package and RF screening acceptance](../../verification/components/stock_substitutions_2026-10-03.md).
[Current BOM](stock_substitution_bom_2026-10-03.csv) and
[stock snapshot with replacements](live_stock_after_substitutions_2026-10-03.json).
The original C40976557/C507268 shortages and C125113 side-view package question
are closed by these substitutions. Other original stock observations are unchanged.

U10 ADE-1+ C2942210 is retained per the user's explicit decision. Six displayed
versus two nominal is still subject to order-time stock and assembly allowance.
No components have been purchased or reserved. All 55 current codes have nominal
quantity coverage in the combined snapshot, but this is not order acceptance.

## Assembly coverage

From the saved full 153-placement audit BOM:

| Handling | References / quantity per board |
|---|---|
| JLCPCB assembly candidates | 140 placements, subject to blockers and service preview |
| Hand solder | H1/H2 stack sockets and JP1/JP2 termination headers: 4 placements |
| DNP | J6/J7/J8: 3 placements; retain embedded codes for future use |
| PCB features | TP1–TP6: 6 bare pads, no purchased component |
| Board-only features | MH1–MH4 mounting holes, excluded from BOM/CPL |
| Separate hand assembly | Pico module and jumper shunts are not separate rows in this exported BOM; account for these in the manual build kit |

J9 is a wave-solder MMCX connector; service and side eligibility must be
confirmed with JLCPCB. Do not assume an SMT-only assembly includes it.
The full BOM preserves supplier codes for hand-solder and DNP parts; final
assembly BOM/CPL filtering must use the table above. The two termination shunts
are installed only where the board is at a CAN bus end.

## Remaining release evidence

Resolve the two stock blockers and LED mapping. Confirm mixer allowance, final
assembly service/sides, exact four-layer impedance stackup, finish and order
options. Then generate fresh Gerbers/drills and filtered BOM/CPL through Konnect,
inspect the outputs and the vendor's rotation/polarity preview. No purchase,
upload, reservation, component substitution or KiCad source change occurred in
this stock-audit pass. Last saved DRC remains the previous verified 0 errors,
0 unconnected, 1 fixed H1/H2 silk warning; it was not rerun for documentation-only work.
