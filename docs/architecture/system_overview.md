# System Overview

## Purpose

Provide a subsystem-level description of the modular satellite architecture and
major design assumptions.

## Subsystem Boundaries

- EPS: source, storage, charging, and regulated rail generation
- Internal Housekeeping Unit: system orchestration, command authority, data aggregation
- Communications: RF uplink/downlink processing and transport bridge
- Payload: mission-specific data generation and control surface

## Major Data and Power Flows

- Power flow: EPS -> regulated rails -> IHU/comms/payload
- Command flow: RF uplink -> comms decode -> IHU validation -> subsystem dispatch
- Telemetry flow: subsystem status -> IHU aggregation -> comms downlink framing

## Interconnect Strategy (Current)

- I2C: housekeeping and charger telemetry (EPS-centric)
- SPI: IHU <-> comms high-rate deterministic data exchange
- CAN (Iteration 2): system control-plane messaging and fault broadcast

See `system/interfaces/board_to_board.md` for the detailed interconnect plan.

## Operational Modes

- Safe mode: reduced loads, heartbeat and minimal telemetry retained
- Nominal mode: full command/telemetry operation
- High-duty mode: prioritized payload/telemetry transfer windows
