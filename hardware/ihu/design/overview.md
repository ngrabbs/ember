# Internal Housekeeping Unit Architecture Overview

**PCB design authority:** [Hardware requirements and electrical interface specification](hardware_requirements.md),
draft 0.1, October 24, 2026. It distinguishes decided direction from proposals and
open electrical contracts. Existing firmware behavior remains revision-specific.

## Scope

This document defines the baseline architecture for the internal housekeeping unit board
that coordinates EPS, communications, and payload behavior.

## System Role

- Intended mode behavior: see the [operations draft](../../../docs/architecture/operations/README.md); the full mode manager is not implemented
- Serve as command authority for subsystem actions
- Aggregate housekeeping telemetry for downlink
- Provide fault supervision and recovery orchestration

## Baseline Hardware Direction

- New PCB MCU: STM32G0B1 family with dual native FDCAN controllers; exact MPN/package open
- GNSS: ATGM336H-5N31 for ground/demo; antenna assembly and flight suitability open
- Primary board interfaces:
  - I2C for EPS housekeeping telemetry
  - UART for debug and bring-up in the FreeRTOS prototype
  - CAN for the standalone Feather bench packet path
  - SPI remains an older stack signal allocation
- Intended production interface:
  - CAN A/B via native MCU controllers and separate external transceivers; redundant operation remains unqualified

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
  telemetry and the selected comms link are both valid for consecutive checks;
  the health policy and complete mode manager remain unimplemented

### Nominal Mode

- Periodic housekeeping telemetry
- Command handling and subsystem coordination
- Standard payload and communications duty cycle

### Legacy high-duty concept

The current [operations draft](../../../docs/architecture/operations/README.md)
places scheduled higher-duty activity within NOMINAL. The earlier separate-mode
concept is retained here as history, not an implemented mode.

## Design Priorities

- Deterministic command handling with bounded retries/timeouts
- Fault containment and graceful degradation
- Clear ownership boundaries between IHU and subsystem controllers
- Testable interfaces with measurable acceptance criteria

## Open Decisions

- Final pin-map and connector assignment for SPI/I2C/UART/GPIO alerts
- Watchdog architecture (single-stage vs staged recovery)
- Safe-mode trigger thresholds and clear-exit conditions
- Exact STM32 package/pin and memory fit, CAN PHY selection and failover policy;
  the single-bus Feather bench uses MCP25625 and is not this PCB architecture

## Related Documents

- IHU interfaces: [`hardware/ihu/design/interfaces.md`](interfaces.md)
- IHU bring-up plan: [`hardware/ihu/bringup/phase1_validation.md`](../bringup/phase1_validation.md)
- System interconnect plan: [`system/interfaces/board_to_board.md`](../../../system/interfaces/board_to_board.md)
