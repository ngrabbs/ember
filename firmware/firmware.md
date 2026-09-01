# Firmware Roadmap

## Document Purpose

This roadmap defines firmware work for the current communications-board
baseline and separates optional exploratory payload work.

## Baseline Firmware Scope (Senior Design)

### Workstream A: Communications Board Control (RP2040)

- [x] Configure Si5351A outputs for TX and RX operating states
- [ ] Implement TX state machine (idle, beacon, packet transmit)
- [ ] Implement framing and bitstream path for BPSK/DBPSK transmission
- [ ] Implement RX sampling and command packet decode flow
- [ ] Implement half-duplex TX/RX arbitration and fault recovery behavior

### Workstream B: Platform Runtime and Reliability

- [ ] Select runtime model (bare metal or RTOS) based on timing and complexity
- [ ] Implement watchdog and recovery pathways
- [ ] Define boot states (safe mode, nominal mode, high-duty mode)
- [ ] Define board health telemetry schema and logging interface

### Workstream C: Bring-Up and Ground Support

- [x] Implement serial CLI for board bring-up and diagnostics
- [ ] Create repeatable RF bench-test helper scripts
- [ ] Implement ground-side telemetry decode utility for captured frames

## Baseline Exit Criteria

- [ ] Stable TX and RX operation with documented operating modes
- [ ] Verified recovery from expected fault and reset conditions
- [ ] Reproducible bench workflow for firmware-assisted RF validation


## Reference Material

- Firmware references are tracked in
  `docs/research/firmware_references.md`.
- Internal Housekeeping Unit firmware roadmap is tracked in
  `firmware/ihu/README.md`.
