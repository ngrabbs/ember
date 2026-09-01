# Board-to-Board Interconnect Architecture

## Scope

Define a practical interconnect strategy for EPS, internal housekeeping unit, and
communications boards, with room to learn and apply CAN in the system.

## Design Constraints

- Internal Housekeeping Unit board baseline MCU: RP2040
- Communications board baseline MCU: RP2040 (local TX/RX control)
- EPS currently centered on charger/regulation hardware (not a full digital node)
- RP2040 has no native CAN peripheral, so CAN requires an external controller
  and transceiver

## Recommended Bus Roles

### I2C (Housekeeping)

- Use for low-rate telemetry/configuration devices
- Primary near-term use: LTC4162 charger telemetry/control path
- Keep bus local where possible; avoid long, high-capacitance board runs

### SPI (High-Rate Deterministic Link)

- Use for high-rate and deterministic board-to-board data exchange
- Recommended near-term use: IHU <-> Comms data path (telemetry buffers,
  payload chunks, firmware services if needed)

### CAN (System Control and Fault-Tolerant Messaging)

- Use for board-level command/status messaging and subsystem state broadcast
- Recommended learning target: IHU + Comms + payload-side node(s)
- EPS can join later if/when a digital EPS controller node is added

## Iteration Plan

## Iteration 1 (Low Risk Bring-Up)

- IHU <-> EPS: I2C for charger telemetry + discrete fault/alert GPIO if needed
- IHU <-> Comms: SPI for primary data transfer
- UART retained for debug/bring-up logs only

Exit criteria:
- IHU reads charger telemetry reliably
- IHU and comms exchange packets over SPI without framing loss
- Timeout/recovery behavior validated

## Iteration 2 (CAN Learning and Operational Integration)

- Add CAN as control-plane bus between IHU and comms, then payload node(s)
- Keep SPI between IHU and comms for bulk or time-critical data
- Use CAN for heartbeat, mode control, health status, and fault broadcast

Exit criteria:
- Multi-node CAN traffic verified with clean arbitration behavior
- Command/ack and heartbeat logic works under injected faults
- IHU can isolate a failed node while keeping remaining nodes operational

## Provisional CAN Implementation Notes

- CAN flavor: classic CAN 2.0B (initial), target 500 kbps default
- RP2040 implementation: SPI CAN controller (for example MCP2515 class) plus
  3.3 V CAN transceiver
- Topology: linear bus with 120 ohm termination at both physical ends
- Connector guidance: at least CANH, CANL, GND, and optional switched supply

## Provisional Message Groups

- `0x100-0x1FF`: internal housekeeping unit commands and mode requests
- `0x200-0x2FF`: EPS status/alerts (when EPS digital node exists)
- `0x300-0x3FF`: communications status and queue state
- `0x400-0x4FF`: payload status and control
- `0x700-0x7FF`: debug and development traffic

## Related Documents

- IHU/comms details: `system/interfaces/comms_to_ihu.md`
- Data ownership and flows: `system/interfaces/data_interfaces.md`
- System integration execution: `system/integration/integration_plan.md`
