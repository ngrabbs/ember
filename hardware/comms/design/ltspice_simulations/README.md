# LTspice models and experiments

[Design guide](../README.md) · [RF analysis](../analysis/README.md)

Retained simulation sources include earlier VHF, Rev-A, filter, and teaching
experiments. They are not all descriptions of the current board.

- `tx_circuit*.asc`: transmitter experiments and variants.
- `rx_circuit.asc`, `rx_lo_tripler*.asc`: receiver/LO experiments.
- `Filters/`: filter designs, as-built variants, and comparison circuits.
- `CubeSat_TX_Chain/`: tripler/transistor comparison work and model dependencies.
- Other named lab/example files are exploratory material.

Keep `.asc`, `.asy`, `.mod`, `.cir`, and deliberate `.net` inputs tracked.
Waveforms and transient logs are ignored. The current measured-qualification
plan is in [bring-up](../../bringup/README.md); do not promote old “validated”
simulation claims into hardware specifications.
