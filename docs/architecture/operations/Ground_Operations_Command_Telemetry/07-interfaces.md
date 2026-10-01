# Ground Operations Subsystem Interfaces

**Status:** Draft 0.2

Ground Operations interfaces with Flight Communications, Spacecraft Management, EPS, and Payload.

The interface design supports both operator-initiated commands and autonomous spacecraft-generated telemetry and events.

## Flight Communications

Ground Operations provides or defines:

- Application-level commands
- Command IDs and parameters
- Command sequence numbers
- ACK/NACK interpretation
- Telemetry and event definitions
- Message interpretation and display requirements
- Operator alerts
- Ground-side logging
- Ground console behavior

Flight Communications provides or defines:

- Flight radio
- Spacecraft antenna
- RF transmission and reception
- Radio status
- Communications errors
- Associated signal conditioning
- Transport of application-level messages between EMBER and Ground Operations

Ground radio/modem, ground antenna, enclosure, console-to-radio interface, packet transport, link testing, and end-to-end testing are shared areas whose exact ownership is TBD.

Ground Operations should not depend on RF-specific details when interpreting an application-level message.

## Spacecraft Management

Spacecraft Management provides or helps define:

- Autonomous spacecraft operation
- Mode management
- Command execution and validation
- Command permission enforcement
- Fault handling
- Reset behavior
- System status
- Mode-transition information
- Event generation and routing
- Telemetry collection and routing

Ground Operations provides the operator interface for viewing this information and issuing commands when operator interaction is required.

Spacecraft Management remains responsible for onboard validation even when Ground Operations has already checked command permissions.

## EPS

EPS provides or helps define:

- Battery status
- Voltage
- Current
- Energy state
- Power faults
- Power limits
- Power interlocks
- SAFE-entry information
- Power-related event conditions

Ground Operations uses this information for periodic status displays, requested telemetry, alerts, and event logging.

Power-related events such as low-energy conditions should be capable of generating event-driven messages without requiring an operator request.

## Payload

Payload provides or helps define:

- Payload states
- Payload commands
- Payload health
- Capture status
- Processing status
- Detection results
- Detection confidence/metric
- Stored detection data
- Data references
- Fire-detection events

Normal payload mission activity should not require continuous Ground Operations commands.

When the payload identifies a qualifying fire detection, the resulting information should support generation of an autonomous `FIRE_DETECTED` event for storage, routing, and eventual transmission to Ground Operations.

Manual payload commands remain available for testing, checkout, troubleshooting, and approved manual operations.

## Application Messaging Interface

Ground Operations uses an application-level messaging model consisting of:

```text
+----------------------+
| Periodic Telemetry   |
+----------------------+

+----------------------+
| Event Messages       |
+----------------------+

+----------------------+
| Operator Commands    |
+----------------------+

+----------------------+
| Command Responses    |
+----------------------+