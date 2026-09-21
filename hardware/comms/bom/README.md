# Comms BOM and sourcing

[Comms home](../README.md) · [Open work](../TODO.md)

**Sourcing requirement:** use exact parts from JLCPCB with live stock sufficient
for the intended build and assembly allowance. LCSC-only stock and cached catalogue
counts are insufficient. Preserve intentional DNP parts.

The latest ordering-field record leaves **J9, L16, and D15** unresolved; **U9**
needs replacement separately. Stock observations in the evidence folder are dated
snapshots, not current availability or reservations.

| Item | Remaining decision |
|---|---|
| U9 | Qualify TQP3M9036 candidate with package, bias/coupling, stability and mixer headroom |
| L16 | Choose with the final U9 network; current J and candidate G tolerance variants are not identical |
| D15 | Qualify exact replacement package, RF loading, standoff/mismatch and ESD ratings |
| J9 | Verify Molex 73415-1471 drawing and board fit before completing ordering fields |
| Filter tuning | 9.1 pF baseline; 8.2/7.5 pF candidates require distinct exact parts and measurements |
| Build quantity | Recheck scarce filter inductors and stack sockets against quantity plus allowance |

C526972 was resolved in the earlier catalogue audit as **YAGEO CC0402BRNPO9BN9R1**.
Older model notes calling its identity unknown are superseded; exact RF models and
live procurement acceptance still need work.

- [Replacement candidate record](replacement_candidates.md)
- [Latest ordering-field completion](evidence/remaining_field_completion.md)
- [Passive-field completion](evidence/passive_field_completion.md)
- [Connector/IC-field completion](evidence/bom_field_completion.md)
- [Dated full audit](evidence/jlcpcb_bom_audit.md) and [live-stock snapshot](evidence/jlcpcb_live_audit.md)

Regenerate the native netlist before exporting the manufacturing BOM. This cleanup
has not refreshed stock, applied substitutions, or generated a fabrication release.
