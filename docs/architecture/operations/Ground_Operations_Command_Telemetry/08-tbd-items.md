# Ground Operations - TBD Items
**Status:** Draft 0.1

Draft 0.1 defines the behavioral architecture. The items below remain open for subsystem coordination or implementation design.

## Command System
- Final command IDs, names, parameters, ranges, and encoding
- Sequence-number field size and rollover behavior
- Duplicate-command history/window and onboard implementation
- Final command-response timeout values
- Commands eligible for any future automatic retry

## Telemetry System
- Final telemetry IDs, fields, data types, and encoding
- Periodic and SAFE telemetry rates
- Event priorities/severity definitions
- Timestamp format and time synchronization
- Storage and retention policy

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
- Telemetry-generation interface

## Ground Console
- Programming language and software architecture
- GUI/framework and final screen layout
- Structured log storage format
- Configuration-file format
- Wired-interface implementation
- Final command-confirmation list
- Alarm/warning presentation
- Telemetry plotting
- Log export method
- Session ID implementation
- Stale-data thresholds

## Spacecraft Health / EPS
- Actual power/energy telemetry fields
- Battery, voltage, current, temperature, and storage thresholds
- Fault severity definitions
- Power interlocks
- SAFE entry/recovery inputs

## Payload / Detection
- Payload states and command parameters
- Detection confidence/metric
- Location information, if available
- Detection-event fields
- Stored-data references
- Capture parameters and checkout/test commands
- Payload health/fault information

## Deployment / Startup
- Deployment/release implementation
- Release inputs
- Startup, RF enable, and deployment timing
- Deployment-test behavior and interlocks

## Ground Testing
- Test hardware/software implementation
- Detailed procedures and pass/fail criteria
- Configured timeout values
- Communications/end-to-end RF criteria
- Hardware-in-the-loop implementation

## Next Development Activity
Coordinate the Draft 0.1 interfaces with Flight Communications, Spacecraft Management, EPS, and Payload. Use the resolved interface information to develop **Draft 0.2**, including implementation-level message fields, data types, timing, and transport details.
