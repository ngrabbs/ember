# Electrical Power System (EPS)

## Purpose

This directory tracks EPS architecture, interfaces, implementation status, and
bench validation for the modular CubeSat platform.

## Architecture Snapshot

- Energy source: SM141K10TF solar panel set (3S/3S2P under evaluation)
- Storage: 2S2P LG MJ1 18650 Li-ion battery pack
- Charge control: LTC4162 with MPPT and I2C telemetry
- Regulation target: TPSM5D1806 dual buck for 5 V and 3.3 V rails

Current hardware emphasis is charger and source-path bring-up. Integrated rail
distribution and finalized subsystem current budgets are still in progress.

## Documentation Map

- Architecture and rationale: `hardware/eps/design/overview.md`
- Electrical and logical interfaces: `hardware/eps/design/interfaces.md`
- Bench bring-up and acceptance criteria: `hardware/eps/bringup/phase1_validation.md`
- KiCad source: `hardware/eps/kicad/`
- Vendor parts and reference assets: `hardware/eps/components/`

## Status Summary

- Completed: baseline parts selected (SM141K10TF, LG MJ1 2S2P, LTC4162, TPSM5D1806)
- In progress: MPPT characterization, rail validation, protection architecture
- Open items: thermistor network finalization, balancing/protection strategy,
  integrated EPS release package

## Directory Structure

```plaintext
hardware/eps/
├── README.md
├── design/
│   ├── overview.md
│   └── interfaces.md
├── bringup/
│   └── phase1_validation.md
├── kicad/
├── releases/
└── components/
```
