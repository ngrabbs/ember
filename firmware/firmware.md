# Firmware Roadmap

**Scope:** FreeRTOS communications-board work. Separate CAN Feather, Walter LTE
bench applications have newer transport demonstrations; their
[implementation guides](../docs/user/README.md) and owning checklists record that
work. Unchecked rows here refer to production integration, not absence of bench evidence.

## Document Purpose

This roadmap defines firmware work for the current communications-board
baseline and separates optional exploratory payload work.

## Baseline Firmware Scope (Senior Design)

### Workstream A: Communications Board Control (RP2040)

- [x] Configure Si5351A outputs for TX and RX operating states
- [x] Boot self-test: safe the outputs, detect hardware, report
      ([`firmware/comms/README.md`](comms/README.md))
- [ ] Implement TX state machine (idle, beacon, packet transmit)
- [ ] Implement framing and bitstream path for BPSK/DBPSK transmission
- [ ] Implement RX sampling and command packet decode flow
- [ ] Implement half-duplex TX/RX arbitration and fault recovery behavior

### Workstream B: Platform Runtime and Reliability

- [x] Select runtime model (bare metal or RTOS) based on timing and complexity
      — FreeRTOS, kernel config shared with the IHU
- [ ] Implement watchdog and recovery pathways
- [ ] Implement boot/operating behavior from the [operations draft](../docs/architecture/operations/README.md),
      with explicit health gating; the full state machine remains open
- [x] Define board health telemetry schema — IHU↔comms register map,
      shared by both trees, written to carry over to the CAN
      `0x300-0x3FF` message group
      ([`firmware/shared/comms_hk_proto.h`](shared/comms_hk_proto.h))
- [x] Bench interim link exercising that schema (I2C over jumpers —
      **not** a flight interface; the comms PCB has no stack I2C)
- [ ] Integrate the demonstrated standalone MCP25625 CAN Feather transport
      into production runtime; finalize message IDs, A/B hardware and failover
- [ ] Logging interface

### Workstream C: Bring-Up and Ground Support

The communications-board RP2040 is the **COMMS MCU**; the IHU-board RP2040 is
the **IHU MCU**. The FreeRTOS I2C link is housekeeping/ping only. The standalone
CAN Feather application demonstrates packet transport; production integration
remains open. Walter provides the initial external
transport while UHF is developed, behind the same COMMS packet service.
The [integration checklist](../system/interfaces/comms_walter.md) owns UART
framing, queues, forwarding, and controller-reset validation.

- [x] Implement serial CLI for board bring-up and diagnostics
- [x] IHU-side ping and status readout for the comms board
      (`comms`, `comms ping`, `comms raw`) — transport-agnostic above
      the driver, so it survives the move to CAN
- [ ] Create repeatable RF bench-test helper scripts
- [ ] Implement ground-side telemetry decode utility for captured frames
- [ ] Integrate standalone CAN/Walter packet forwarding into production
      applications without changing packet meanings; UHF integration remains open

## Baseline Exit Criteria

- [ ] Stable TX and RX operation with documented operating modes
- [ ] Verified recovery from expected fault and reset conditions
- [ ] Reproducible bench workflow for firmware-assisted RF validation


## Reference Material

- Firmware references are tracked in
  [`docs/research/firmware_references.md`](../docs/research/firmware_references.md).
- Communications board firmware status is tracked in
  [`firmware/comms/README.md`](comms/README.md).
- Internal Housekeeping Unit firmware roadmap is tracked in
  [`firmware/ihu/README.md`](ihu/README.md).
