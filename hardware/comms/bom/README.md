# Comms BOM and sourcing

[Comms home](../README.md) · [Open work](../TODO.md)

**Sourcing requirement:** use exact parts from JLCPCB with live stock sufficient
for the intended build and assembly allowance. LCSC-only stock and cached catalogue
counts are insufficient. Preserve intentional DNP parts.

**Canonical embedded property: `LCSC Part #`.** All 147 purchasable placements
now carry a C-number in schematic and PCB, including DNP headers. Six bare
copper test pads use `N/A`; mounting holes are board geometry. Keep ordering
identity separate from DNP and hand-solder assembly choices.

[Current field audit and full BOM](evidence/lcsc_property_audit_2026-10-03.md)
records new selections and verification. L16, D15 and J9 exact ordering fields
are complete; U9 PSA4-5043+ is retained with October 3 stock evidence.
[RF prototype acceptance and limits](../verification/components/prototype_parts_2026-10-03.md).

All 55 original codes were checked against live JLCPCB rows October 3. The two
stock shortages and green LED package question are now resolved by qualified
substitutions: C90642 inductors, C882826 regulator, C125094 LEDs. The mixer is retained
per user decision; its six-piece stock snapshot remains an order-time risk.
[Current stock and assembly audit](evidence/stock_assembly_audit_2026-10-03.md).
Verify the selected service's assembly allowance. Confirm the order's assembly service and filter-part selections.
No purchases or reservations have been made.

C526972 was resolved in the earlier catalogue audit as **YAGEO CC0402BRNPO9BN9R1**.
Older model notes calling its identity unknown are superseded; exact RF models and
live procurement acceptance still need work.

- [Replacement candidate record](replacement_candidates.md)
- [Latest ordering-field completion](evidence/remaining_field_completion.md)
- [Passive-field completion](evidence/passive_field_completion.md)
- [Connector/IC-field completion](evidence/bom_field_completion.md)
- [Dated full audit](evidence/jlcpcb_bom_audit.md) and [live-stock snapshot](evidence/jlcpcb_live_audit.md)

Regenerate the native netlist before exporting the manufacturing BOM. The audit BOM is not a fabrication release; generate a filtered assembly BOM
and verify the vendor preview before ordering.
