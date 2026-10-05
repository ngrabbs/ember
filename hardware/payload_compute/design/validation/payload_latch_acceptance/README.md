# Disposable run-latch acceptance circuit

[Rendered schematic](payload_latch_acceptance.png),
[KiCad schematic](payload_latch_acceptance.kicad_sch),
[exported netlist](payload_latch_acceptance.net),
[package rendering](payload_latch_acceptance-footprints-detail.png),
[query-back evidence](payload_latch_acceptance-accepted-library-evidence.json).

See [circuit/startup contract](../../run_latch.md) and
[exact physical pin maps](../../latch_library_acceptance.md).

This study contains the AON reset, converter permission gates and run latch.
The PCB has three disposable packages for mapping inspection only. It is not
an assembled/routed design and has not been merged into the carrier.

Connectivity checks find zero floating ends, unconnected unmarked pins,
shorts or orphans. ERC reports exactly four errors and four warnings:
SOURCE_OK_AON, MODE_PERMISSION, 5V_WINDOW_OK and SHUTDOWN_OK_AON each
lack an upstream driver and connect to one pin. These are declared external
boundaries, not suppressed errors or completed receivers. The repeatable
checker rejects any other ERC finding. MCU inputs are biased low but their
firmware and MCU circuits are likewise outside this block.

CT and Q_N are intentionally marked no-connect. Passives have study values
without accepted production MPNs/footprints. Hardware qualification remains.
