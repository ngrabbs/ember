# System Test Definitions

## Purpose

Capture integrated system test cases and pass/fail criteria.

## Initial Test Buckets

- Power-up and reset behavior
- Telemetry transport integrity
- Command reception and execution
- Fault injection and recovery behavior

## Interconnect-Focused Additions

- I2C robustness test (EPS telemetry read consistency under bus stress)
- SPI framing test (error-rate and timeout behavior under sustained transfer)
- CAN arbitration test (multi-node command/status traffic)
- CAN fault confinement test (node-offline and bus-recovery behavior)
