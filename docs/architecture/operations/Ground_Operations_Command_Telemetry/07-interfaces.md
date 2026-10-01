# Ground Operations Subsystem Interfaces
**Status:** Draft 0.1

## Flight Communications
Ground Operations provides/defines operator commands, IDs, parameters, sequence numbers, logs, telemetry interpretation, and display requirements.

Flight Communications provides/defines the flight radio, spacecraft antenna, RF transmission/reception, radio status, communications errors, and associated signal conditioning.

Ground radio/modem, antenna, enclosure, console interface, packet transport, link testing, and end-to-end testing are shared areas whose exact ownership is TBD.

## Spacecraft Management
Provides or helps define mode management, command execution/validation, permission enforcement, fault handling, reset behavior, system status, and mode-transition information.

## EPS
Provides or helps define battery, voltage, current, energy state, power faults/limits/interlocks, and SAFE-entry information.

## Payload
Provides or helps define payload states/commands, detection events, health, capture/processing status, stored data, and detection confidence/metric.

## Interface Principle
Logical command/telemetry definitions should remain independent of the physical communications link where practical. `SET_MODE -> NOMINAL`, for example, should mean the same thing over wired test or RF transport.

Changes affecting command IDs, telemetry fields, transport, or operator behavior should be documented and reviewed by affected subsystem owners.

## Draft 0.1 Interface Contract
Ground Operations creates application-level messages and Flight Communications transports them. The shared interface must ultimately define the console-to-radio connection, application-message representation, maximum message size, link/error status, timing expectations, RF framing relationship, and integration-test interface. These implementation details remain TBD.
