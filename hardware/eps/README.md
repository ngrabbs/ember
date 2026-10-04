# Electrical Power System (EPS)

## Purpose

This directory tracks EPS architecture, interfaces, implementation status, and
bench validation for the modular CubeSat platform.

## Architecture Snapshot

- Energy source: SM141K10TF solar panels; documented Rev A arrangement is four series modules per face, with four faces in parallel
- Storage: 2S2P LG MJ1 18650 Li-ion battery pack
- Charge control: LTC4162 with MPPT and I2C telemetry
- Rev A regulation: two TPS62933F buck stages for 5 V and 3.3 V, as recorded in the release BOM

Rev B proposes independent pack protection, hardware RBF/deployment source
isolation, an STM32 supervisor, and CAN A/B. Parts, fit and acceptance remain
under development; the older TPSM5D1806 overview is not the fabricated baseline.

Current hardware emphasis is charger and source-path bring-up. Integrated rail
distribution and finalized subsystem current budgets are still in progress.

## Documentation Map

- Next revision draft: [`Rev B architecture and implementation plan`](design/rev_b_plan.md)
- Implementation handoff: [Rev B provisional BOM and schematic checklist](design/rev_b_bom_and_schematic_checklist.md)
- Architecture and rationale: [`hardware/eps/design/overview.md`](design/overview.md)
- Electrical and logical interfaces: [`hardware/eps/design/interfaces.md`](design/interfaces.md)
- Bench bring-up and acceptance criteria: [`hardware/eps/bringup/phase1_validation.md`](bringup/phase1_validation.md)
- Verification checkpoint and previews: [verification index](verification/README.md)
- Draft controller symbols and footprints: [candidate library notes](libraries/README.md)
- KiCad source: `hardware/eps/kicad/`
- Vendor parts and reference assets: `hardware/eps/components/`

## Status Summary

- Fabricated: Rev A with LTC4162 and TPS62933F stages; current assembly includes documented bench rework
- In progress: Rev B architecture and circuit definition, charger diagnosis, MPPT characterization and rail validation
- Open items: verified thermistor charging, independent protection, all-source
  RBF shutdown, measured current/energy budgets, mechanical fit and qualified release package

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
