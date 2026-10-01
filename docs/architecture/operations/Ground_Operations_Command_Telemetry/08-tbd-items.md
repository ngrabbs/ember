# Ground Operations - TBD Items

**Status:** Draft 0.2

Draft 0.2 defines the current Ground Operations behavioral and application-messaging architecture. The items below remain open for subsystem coordination, team approval, or implementation design.

## Command System

- Final command IDs, names, parameters, ranges, and encoding
- Sequence-number field size and rollover behavior
- Duplicate-command history/window and onboard implementation
- Final command-response timeout values
- Commands eligible for any future automatic retry
- Final command-completion criteria
- Final list of commands requiring operator confirmation

## Telemetry System

- Final telemetry IDs, fields, data types, and encoding
- Periodic telemetry rates
- SAFE telemetry rates
- Heartbeat rate and contents
- Requested-telemetry behavior
- Timestamp format and time synchronization
- Telemetry priority definitions
- Stale-data thresholds
- Storage and retention policy

## Event Messaging

- Final event IDs, fields, data types, and encoding
- Event priority and severity definitions
- Critical-event delivery requirements
- Event queue size and behavior
- Event storage location
- Event retention period
- Retransmission behavior
- Ground acknowledgment requirements for critical events
- Behavior when communications are unavailable
- Behavior when communications are restored
- Duplicate-event handling
- Relationship between event priority and communications scheduling

## Fire Detection Events

- Final `FIRE_DETECTED` message contents
- Detection confidence/metric
- Detection threshold information, if required
- Location information, if available
- Spacecraft timestamp requirements
- Stored-data reference
- Event priority
- Onboard storage requirements
- Ground alert behavior
- Delivery/retransmission requirements
- Operator acknowledgment requirements, if any

## Communications / Flight Communications Interface

- Ground radio/modem and final ownership
- Ground antenna and final ownership
- Console-to-radio physical/software interface
- Application-message representation at communications handoff
- RF packet/frame format
- Maximum application/RF message sizes
- RF data rate
- Integrity/error-control method
- Available radio/link status information
- Communications error reporting
- RF timing expectations
- Message-priority handling
- Event queue interaction with Flight Communications
- End-to-end RF test implementation

## Spacecraft Management / IHU

- Command parser interface
- Mode-manager interface
- Onboard permission/interlock implementation
- ACK/NACK generation details
- Sequence-number and duplicate-command handling
- Reset behavior
- Fault-handling interface
- Spacecraft timestamp generation
- Periodic telemetry-generation interface
- Event-generation and routing interface
- Message queue implementation
- Message-priority handling
- Autonomous mission-operation interfaces

## Internal Messaging / Transport

- Final internal transport interfaces between subsystems
- Whether physical CAN is used for applicable Iteration 2 interfaces
- CAN message identifiers and priorities if physical CAN is implemented
- Mapping between application-level messages and physical transport
- SPI/UART/CAN interface responsibilities where applicable
- Transport-specific framing and integrity checks
- Buffering and queue behavior between application and transport layers

The use of a CAN-style application messaging concept does not by itself select CAN as the physical transport.

## Ground Console

- Programming language and software architecture
- GUI/framework and final screen layout
- Structured log storage format
- Configuration-file format
- Wired-interface implementation
- Final command-confirmation list
- Alarm/warning presentation
- Fire-detection alert presentation
- Operator event-acknowledgment behavior
- Telemetry plotting
- Log export method
- Session ID implementation
- Stale-data thresholds
- Event-history display
- Communications-loss indication

## Spacecraft Health / EPS

- Actual power/energy telemetry fields
- Battery, voltage, current, temperature, and storage thresholds
- Fault severity definitions
- Power interlocks
- SAFE entry/recovery inputs
- Low-power event trigger and contents

## Payload / Detection

- Payload states and command parameters
- Autonomous payload operating schedule
- Detection confidence/metric
- Location information, if available
- Detection-event fields
- Stored-data references
- Capture parameters and checkout/test commands
- Payload health/fault information
- Payload-to-IHU detection-event interface

## Deployment / Startup

- Deployment/release implementation
- Release inputs
- Startup, RF enable, and deployment timing
- Deployment-test behavior and interlocks
- Startup telemetry/event behavior

## Ground Testing

- Test hardware/software implementation
- Detailed procedures and pass/fail criteria
- Configured timeout values
- Periodic telemetry verification criteria
- Autonomous event-generation test criteria
- Fire-detection event test method
- Communications-loss/store-and-forward testing
- Event retransmission testing
- Communications/end-to-end RF criteria
- Hardware-in-the-loop implementation

## Next Development Activity

Coordinate the Draft 0.2 application-message and interface requirements with Flight Communications, Spacecraft Management, EPS, and Payload.

Resolve the highest-priority interface TBDs before assigning final message IDs, field sizes, timing requirements, priorities, or transport-specific behavior.

Use the resolved interface information to develop the next implementation-level revision, including final message fields, data types, timing, transport mapping, event-delivery behavior, and ground-console implementation requirements.
