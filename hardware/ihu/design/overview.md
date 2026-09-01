# Internal Housekeeping Unit Architecture Overview

## Scope

This document defines the baseline architecture for the internal housekeeping unit board
that coordinates EPS, communications, and payload behavior.

## System Role

- Execute mode logic (safe, nominal, high-duty)
- Serve as command authority for subsystem actions
- Aggregate housekeeping telemetry for downlink
- Provide fault supervision and recovery orchestration

## Baseline Hardware Direction

- MCU: RP2040
- Primary board interfaces:
  - I2C for EPS housekeeping telemetry
  - SPI for IHU <-> comms bidirectional data exchange
  - UART for debug and bring-up
- Planned Iteration 2 interface:
  - CAN control-plane network via external CAN controller/transceiver

## Functional Block View

```text
Uplink Command (via Comms) -> IHU Command Parser/Dispatcher
                                   -> EPS control/monitor path
                                   -> Comms mode + queue control
                                   -> Payload control path

Subsystem Telemetry -> IHU Aggregator -> Downlink Packet Assembly -> Comms TX
```

## Runtime Behavior (Design Intent)

### Safe Mode

- Minimal subsystem activity
- Preserve command reception and essential telemetry
- Restrict non-essential loads/operations
- Default boot mode at power-up/reset
- Exit condition (provisional): transition to nominal only after EPS I2C
  telemetry and comms SPI heartbeat are both valid for consecutive checks

### Nominal Mode

- Periodic housekeeping telemetry
- Command handling and subsystem coordination
- Standard payload and communications duty cycle

### High-Duty Mode

- Elevated telemetry/payload transfer throughput
- Controlled by mission timeline or command

## Design Priorities

- Deterministic command handling with bounded retries/timeouts
- Fault containment and graceful degradation
- Clear ownership boundaries between IHU and subsystem controllers
- Testable interfaces with measurable acceptance criteria

## Open Decisions

- Final pin-map and connector assignment for SPI/I2C/UART/GPIO alerts
- Watchdog architecture (single-stage vs staged recovery)
- Safe-mode trigger thresholds and clear-exit conditions
- CAN controller/transceiver part selection for Iteration 2

## Related Documents

- IHU interfaces: `hardware/ihu/design/interfaces.md`
- IHU bring-up plan: `hardware/ihu/bringup/phase1_validation.md`
- System interconnect plan: `system/interfaces/board_to_board.md`
