# System Integration Plan

## Purpose

Track subsystem integration order, prerequisites, and verification checkpoints.

## Draft Plan

1. EPS standalone validation
2. IHU <-> EPS I2C telemetry integration
3. IHU <-> Comms SPI data-link integration
4. End-to-end telemetry and command verification over SPI path
5. CAN bus bring-up with IHU and comms nodes
6. Expand CAN to payload node and validate multi-node arbitration

## Planned Iteration Gates

- Gate A: I2C and SPI links stable under nominal load
- Gate B: End-to-end command and telemetry loop closes reliably
- Gate C: CAN control-plane heartbeat and fault signaling validated
