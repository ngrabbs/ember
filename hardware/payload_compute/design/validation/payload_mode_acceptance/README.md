# Disposable bench-mode sampler

[Rendered schematic](payload_mode_acceptance.png),
[exported netlist](payload_mode_acceptance.net),
[package image](payload_mode_acceptance-footprint-detail.png),
[final query/check evidence](payload_mode_acceptance-final-evidence.json),
[physical maps](library_acceptance.md),
[mode and IHU contract](../../bench_mode.md).

The circuit locks the jumper until AON reset; MCU reset alone cannot resample
it. The PCB contains disposable U2/U4 package instances for physical mapping;
no routing/assembly readiness is claimed. Prior library/acceptance JSON files
are intermediate snapshots; final-evidence.json is authoritative for this study.

Connectivity checks have zero floating wire ends, unmarked unconnected pins,
shorts and orphans. ERC has one declared boundary error: AON_RESET_N lacks
the upstream TPS3808 reset driver from the separate latch study. Zero warnings.
The checker rejects any other ERC finding. MCU GPIO/firmware, jumper/passive
production selection and source/permission receivers remain outside this block.
