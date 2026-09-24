# EMBER Command / Telemetry Protocol

**Status:** Draft 0.2

This document defines the Ground Operations application-level command, telemetry, event, and response behavior. It intentionally does not define the final RF frame, binary field sizes, or radio-specific transport.

## 1. Application Messaging Architecture

EMBER uses an autonomous, event-driven application messaging architecture.

Normal mission operation does not require continuous operator commands. EMBER autonomously performs scheduled mission activities, monitors spacecraft health, processes payload data, generates periodic telemetry, and reports significant mission or spacecraft events.

Ground Operations supports four primary application-level message categories:

| Category | Direction | Purpose | Examples |
|---|---|---|---|
| Periodic Telemetry | EMBER -> Ground | Automatically report routine spacecraft status | HEARTBEAT, POWER_STATUS, PAYLOAD_STATUS |
| Event Messages | EMBER -> Ground | Automatically report significant conditions or mission events | FIRE_DETECTED, FAULT_EVENT, MODE_EVENT |
| Operator Commands | Ground -> EMBER | Request information or initiate approved operator actions | REQUEST_STATUS, SET_MODE, PAYLOAD_CAPTURE |
| Command Responses | EMBER -> Ground | Report command acceptance, rejection, requested data, or completion | ACK, NACK, requested telemetry |

### Autonomous Message Flow

Periodic telemetry and event messages may originate onboard without a corresponding operator command.

```text
Spacecraft / Payload Activity
            |
            v
     Status or Event
            |
            v
     Application Message
            |
            v
      Store / Queue
            |
            v
   Communications Path
            |
            v
    Ground Operations
            |
            v
   Display / Alert / Log
```

A significant event such as `FIRE_DETECTED` should be generated as a result of onboard mission processing rather than an operator request.

If communications are unavailable, significant events should be preserved for later delivery according to the final event-storage and communications design.

### Operator Interaction

Operator commands supplement autonomous operation.

Ground Operations retains command capability for:

- On-demand status and telemetry requests
- Configuration
- Testing and checkout
- Manual operations
- Fault recovery
- Troubleshooting
- Approved overrides

For example, periodic `SYSTEM_STATUS` telemetry may be generated automatically while `REQUEST_STATUS` remains available when the operator wants a fresh status report immediately.

### CAN-Style Messaging Concept

The application architecture uses a CAN-style, event-driven messaging concept where practical.

In this context, CAN-style describes the messaging behavior: defined messages may be generated when information or events become available without requiring continuous operator polling.

This does not require CAN to be the physical transport.

Application-level messages should retain the same meaning regardless of whether they are carried through an internal spacecraft interface, a wired development/test connection, or the RF communications path.

Physical transport selection and message-to-transport mapping remain interface-level design decisions.

## 2. Command Transaction Flow

1. Operator selects a command.
2. Ground console checks the command against known permissions and required parameters.
3. A sequence number is assigned.
4. The application-level command message is created.
5. The command is handed to the active communications interface.
6. The command is transported to EMBER by the wired or RF path.
7. The IHU receives the command.
8. Spacecraft Management validates the command.
9. Invalid commands generate a NACK; valid commands generate an ACK.
10. An accepted command is executed.
11. The affected subsystem generates the appropriate result, status, or event telemetry.
12. The response is transported to Ground Operations.
13. Ground Operations correlates command-related responses using the sequence number where applicable.
14. The console displays and logs the result.

Ground Operations distinguishes three concepts:

- **Transport:** Did the message get there?
- **Acceptance:** Did EMBER accept the command? This is represented by ACK/NACK.
- **Completion:** Did the requested action actually occur? This is confirmed by the resulting telemetry or event.

The console shall not report command success merely because the command was transmitted.

### Responsibility Boundary

| Activity | Primary Responsibility |
|---|---|
| Operator selects command | Ground Operations |
| Ground-side permission/basic validation | Ground Operations |
| Assign sequence number | Ground Operations |
| Build application command | Ground Operations |
| Console-to-communications handoff | Ground Operations / Flight Communications interface |
| Ground RF transport | Shared / Flight Communications |
| Flight radio receive | Flight Communications |
| Delivery to IHU | Flight Communications / Spacecraft Management interface |
| Validate mode/interlocks | Spacecraft Management |
| Execute command | Spacecraft Management / affected subsystem |
| Generate response/telemetry/event | Spacecraft Management / affected subsystem |
| RF return path | Flight Communications |
| Decode/display/alert/log | Ground Operations |

The wired development path may bypass RF while preserving the same application-level protocol:

```text
Ground Console -> Wired Test Interface -> IHU
```

## 3. Command States

Ground Operations uses the following command transaction states:

| State | Meaning |
|---|---|
| `CREATED` | Console created the transaction. |
| `SENT` | Command was handed off for transmission. |
| `ACKNOWLEDGED` | EMBER received, validated, and accepted the command. |
| `COMPLETED` | Resulting telemetry/event confirms the requested action occurred. |
| `NACKED` | EMBER received but rejected the command. |
| `TIMEOUT` | Expected response was not received within the configured interval. |

Normal flow:

```text
CREATED -> SENT -> ACKNOWLEDGED -> COMPLETED
```

Possible branches include:

```text
SENT -> NACKED

SENT -> TIMEOUT

ACKNOWLEDGED -> TIMEOUT
```

A timeout means **the outcome is unknown until spacecraft status can be verified**.

A generic `FAILED` state is not used because it does not distinguish rejection, loss of communications, or an unknown result.

## 4. Timeout & Retry Behavior

No automatic command retries are required in Draft 0.2.

```text
COMMAND SENT
     |
     +--> ACK/NACK received -> Continue transaction
     |
     +--> No expected response -> TIMEOUT
                                  |
                                  v
                            Outcome UNKNOWN
                                  |
                                  v
                             Verify Status
```

Read-only requests such as `PING`, `REQUEST_STATUS`, `REQUEST_TELEMETRY`, `REQUEST_DETECTION_DATA`, and `REQUEST_LOG` may be manually resent.

Commands that change spacecraft state require verification before resending where practical.

| Command | Timeout Handling |
|---|---|
| `PING` | May be manually resent. |
| `REQUEST_STATUS` | May be manually resent. |
| `REQUEST_TELEMETRY` | May be manually resent. |
| `REQUEST_DETECTION_DATA` | May be manually resent. |
| `REQUEST_LOG` | May be manually resent. |
| `SET_MODE` | Verify current mode before resending. |
| `CLEAR_FAULT` | Verify fault state before resending. |
| `PAYLOAD_CHECK` | Verify payload state before resending. |
| `PAYLOAD_CAPTURE` | Verify capture/event state before resending. |
| `SET_PARAMETER` | Read/verify parameter before resending. |
| `REBOOT_IHU` | Do not blindly resend. |
| `DEPLOY_TEST` | Do not blindly resend. |

Read-only commands may later support automatic retry after testing demonstrates that behavior is appropriate.

Command-response timeout values shall be configurable and will be established through communications design and end-to-end testing.

Autonomous event retransmission is separate from operator-command retry behavior. Event delivery, retransmission, and acknowledgment requirements remain TBD.

## 5. Sequence Numbers & Duplicate Handling

1. Ground Operations assigns a sequence number to every new command transaction.
2. ACK/NACK responses reference the originating sequence number.
3. Sequence numbers allow Ground Operations to match responses with commands, including when responses arrive out of order.
4. A new operator command receives a new sequence number.
5. A retransmission of the same transaction retains the original sequence number.
6. Sequence numbers support duplicate-command detection.
7. EMBER should not blindly re-execute a detected duplicate transaction.
8. Sequence-number field size, rollover behavior, and duplicate-detection history/window remain TBD.

Example:

```text
SEQ 0041  REQUEST_STATUS
SEQ 0042  SET_MODE NOMINAL
SEQ 0043  REQUEST_TELEMETRY
```

A repeated command shall not be assumed to require repeated execution. The final duplicate-command handling method will be coordinated with Spacecraft Management.

Autonomous periodic telemetry and event messages do not require an originating command sequence number.

Events may require their own unique event identifiers for storage, duplicate detection, and ground-side tracking.

## 6. Application Message Structures

### Command

```text
Sequence Number
      |
Command ID
      |
Parameters
      |
Integrity Check
```

Example:

```text
SEQ:        0042
COMMAND:    SET_MODE
PARAMETER:  NOMINAL
INTEGRITY:  TBD
```

### ACK

```text
Sequence Number
Command ID
Response = ACK
```

### NACK

```text
Sequence Number
Command ID
Response = NACK
Reason Code
```

ACK means the command was accepted; it does not by itself mean the requested operation completed.

### Completion Evidence

| Command | Completion Evidence |
|---|---|
| `PING` | Link response |
| `REQUEST_STATUS` | Requested status received |
| `REQUEST_TELEMETRY` | Requested telemetry received |
| `SET_MODE` | `MODE_EVENT` and/or current mode confirms result |
| `CLEAR_FAULT` | Updated `FAULT_STATUS` |
| `REBOOT_IHU` | New `RESET_EVENT` / reconnection |
| `PAYLOAD_CHECK` | Payload test result |
| `PAYLOAD_CAPTURE` | Updated `PAYLOAD_STATUS` and/or resulting event |
| `REQUEST_DETECTION_DATA` | Requested records received |
| `SET_PARAMETER` | Resulting parameter value verified |
| `REQUEST_LOG` | Requested log received |
| `DEPLOY_TEST` | Deployment-test result |

### Periodic Telemetry

Conceptual structure:

```text
Telemetry ID
Timestamp
Telemetry Data
Integrity Check
```

Example:

```text
TELEMETRY:  POWER_STATUS
TIME:       14:32:18
VOLTAGE:    TBD
CURRENT:    TBD
ENERGY:     TBD
INTEGRITY:  TBD
```

Periodic telemetry does not require an originating operator command.

Examples include:

```text
HEARTBEAT
SYSTEM_STATUS
CURRENT_MODE
POWER_STATUS
THERMAL_STATUS
FAULT_STATUS
PAYLOAD_STATUS
STORAGE_STATUS
COMM_STATUS
```

Final telemetry rates remain TBD.

### Event Message

Conceptual structure:

```text
Event ID / Message ID
Spacecraft Timestamp
Event Type
Event Data
Stored Data Reference, if applicable
Integrity Check
```

Example:

```text
EVENT:      FIRE_DETECTED
EVENT ID:   0172
TIME:       14:36:21
RESULT:     POSITIVE
METRIC:     TBD
LOCATION:   TBD
DATA REF:   RECORD 0172
INTEGRITY:  TBD
```

Event messages may be generated autonomously without an operator command.

Examples include:

```text
FIRE_DETECTED
MODE_EVENT
RESET_EVENT
FAULT_EVENT
LOW_POWER_EVENT
```

### Requested Telemetry

Requested telemetry is generated because of an operator information request.

Example:

```text
GROUND -> REQUEST_STATUS
EMBER  -> ACK
EMBER  -> SYSTEM_STATUS
```

The returned information should include, or otherwise permit, correlation to the originating command transaction where practical.

### Application and Transport Separation

Application-level definitions are separate from RF transport/framing.

Flight Communications may wrap application data in radio-specific headers, addressing, packet types, error-control fields, or other transport information.

The same application message should retain the same meaning when transported over wired development/test interfaces or RF.

## 7. Autonomous Event Behavior

Significant spacecraft and mission events should be generated automatically.

Example fire-detection flow:

```text
Payload Observation
       |
       v
Payload Processing
       |
       v
Fire Detected?
   |       |
  NO      YES
   |       |
   |       v
   |   FIRE_DETECTED
   |       |
   |       v
   |   Store Event
   |       |
   |       v
   |   Queue for Delivery
   |       |
   |       v
   |   Communications Available?
   |       |
   |    +--+--+
   |    |     |
   |   NO    YES
   |    |     |
   |    v     v
   |  RETAIN TRANSMIT
   |    |
   |    v
   |  WAIT FOR
   |  COMMUNICATIONS
   |
   +----> Continue Mission Operation
```

The spacecraft should continue autonomous mission operation regardless of whether an operator is actively connected.

### Event Storage

Significant events should be stored onboard when immediate delivery is not possible.

The final design must determine:

- Event queue size
- Event storage location
- Event retention period
- Message priorities
- Retransmission behavior
- Ground acknowledgment requirements
- Duplicate-event handling
- Behavior after communications are restored

These items remain TBD.

### Fire Detection

A fire detection is a mission event and is not automatically a spacecraft fault.

Ground Operations should display a `FIRE_DETECTED` event prominently and preserve the associated event information.

Final fire-event fields are coordinated with Payload and may include:

```text
Event ID
Spacecraft Timestamp
Detection Result
Detection Confidence / Metric
Location
Payload Status
Stored Data Reference
```

Fields not available from the Payload subsystem shall not be invented by Ground Operations.

## 8. Ground Console Behavior

The console behavior is defined functionally; the final GUI layout and software framework remain TBD.

### Primary Functions

The console should provide:

- Spacecraft status and configuration
- Automatic telemetry monitoring
- Event and alert display
- Fire-detection alerts
- Command selection and parameters
- On-demand information requests
- Command transaction status
- Telemetry and event display
- Command/system history and logging

At minimum, the operator should be able to view:

- Mode
- Configuration
- System health
- Power
- Payload
- Communications
- Storage
- Faults
- Most recent telemetry time
- Telemetry age
- Significant mission events

### Stale Data

The console shall distinguish current information from missing, unknown, or stale telemetry.

Old information shall not continue to be presented as current without an indication that it is stale.

The stale-data threshold is TBD.

### Command Permissions

The console should use the Permission Matrix to disable commands that are obviously inappropriate for the reported spacecraft mode.

Ground-side filtering is an operator aid and does not replace onboard validation.

If required spacecraft state is unknown or stale, commands that depend on that state should not be treated as known-safe solely from the console's previous local state.

### Confirmation

Routine read-only commands do not require an additional confirmation.

Selected higher-consequence commands should require explicit operator confirmation.

Initial candidates include:

- `REBOOT_IHU`
- `DEPLOY_TEST`
- Selected `SET_MODE` operations
- Selected `SET_PARAMETER` operations

The final confirmation list is configurable/TBD.

Example:

```text
CONFIRM COMMAND

Command: REBOOT_IHU
Current Mode: NOMINAL

Warning: This command will restart the flight computer.

[Cancel] [Confirm & Send]
```

### Transaction Display

The console shall display:

```text
CREATED
SENT
ACKNOWLEDGED
COMPLETED
NACKED
TIMEOUT
```

NACK reason codes should be translated into human-readable descriptions.

A timeout shall be shown as an unknown outcome rather than an automatic failure or success.

The console should recommend status verification before resending state-changing commands.

### Events and Alerts

Initial event categories are:

- **Information:** normal mode changes and routine operational events
- **Warning:** timeout, degraded communications, or noncritical fault
- **Critical:** SAFE entry or critical spacecraft fault
- **Mission Event:** fire detection or other mission-specific detection

A fire detection should be displayed prominently without automatically classifying it as a spacecraft fault.

Final event severity, priority, audible notification, and operator acknowledgment requirements remain TBD.

### Communications Indication

The console should distinguish, where data permits, between:

- Ground-interface connectivity
- Radio readiness
- RF receive activity
- Recent spacecraft communications
- Stale spacecraft communications
- Communications unavailable

A connected ground device shall not automatically imply that EMBER communication is confirmed.

### Configuration Indication

`GROUND TEST` versus `FLIGHT` shall be prominently displayed.

Test-only commands shall not be enabled solely by operator selection; the spacecraft-reported configuration must permit them.

### Operator Interface

Normal operation should use human-readable command names and parameters.

Raw command construction may be provided later as a developer/debug capability but is not the normal operator workflow.

### Console Design Philosophy

The Ground Operations Console primarily serves as:

```text
MONITOR
   +
ALERT
   +
LOG
   +
CONFIGURE
   +
TEST
   +
OVERRIDE / RECOVER
```

The ground console is not required for EMBER to continue normal autonomous mission operation.

## 9. Logging & Data Storage

Each operating or test period should have a unique Session ID so its records can be grouped together.

The exact Session ID format remains configurable.

### Logged Record Categories

- `SESSION` - start/stop, configuration, connection type
- `COMMAND` - command, sequence number, parameters, state changes
- `RESPONSE` - ACK/NACK and reason
- `TELEMETRY` - received spacecraft telemetry
- `EVENT` - mode changes, resets, detections, other events
- `FAULT` - fault activation/clearing
- `COMM` - communications loss/recovery/errors/timeouts
- `OPERATOR` - important operator actions where appropriate

Common fields should include timestamp, Session ID, record type, sequence number when applicable, source, message/event, and details.

### Command Transaction Record

Each command should maintain a transaction history containing applicable times for:

- Creation
- Transmission
- ACK/NACK
- Completion
- Timeout
- Final state
- Completion evidence

### Raw and Decoded Data

Ground Operations should preserve raw received application data where practical in addition to decoded operator-readable records.

This permits later reprocessing if the decoder changes or an integration problem must be investigated.

### Telemetry and Detection Records

Telemetry records should preserve:

- Telemetry ID/type
- Timestamp
- Decoded values
- Source

Detection events should have unique event records containing available metadata such as:

- Event ID
- Timestamp
- Result
- Detection metric/confidence
- Location
- Payload status
- Stored-data reference

Fields not yet defined remain TBD.

Large payload products should normally be referenced by the event record rather than embedded directly in routine logs.

### Time

Ground Operations shall timestamp locally generated events and preserve spacecraft-provided timestamps when available.

Ground receive time and spacecraft event time should remain distinguishable when both exist.

Final clock synchronization and timestamp format are TBD.

### Storage

Starting a new session shall not overwrite previous session records.

Logs shall use a structured, machine-readable format that can be reviewed or exported by the team.

Possible implementations include:

```text
CSV
JSON
SQLite
Other structured format
```

The final storage technology and retention policy are TBD.

## 10. Ground Operations / Flight Communications Interface

Ground Operations creates operator-initiated application messages and interprets spacecraft-generated application messages.

Flight Communications transports those messages over the communications path.

### Ground Operations Provides

- Application-level command information
- Sequence numbers
- Command IDs
- Parameters
- Telemetry/event interpretation requirements
- Application integrity information, if used
- Operator/console requirements
- Alert requirements
- Ground-side logging requirements

### Flight Communications Provides

- Received application data
- Radio/link status information that the selected hardware can provide
- Communications errors that can be exposed to Ground Operations
- RF transport between ground and spacecraft

Ground Operations then:

- Decodes received data
- Correlates command responses
- Updates transaction state
- Updates telemetry
- Processes spacecraft events
- Generates operator alerts
- Logs results

### Shared Interface Contract

Ground Operations and Flight Communications must agree on:

- Console-to-radio physical/software interface
- Application-message representation at the handoff
- Maximum message size
- Link-status information
- Communications error reporting
- Connection state reporting
- Timing expectations
- Message-priority behavior
- Event queue interaction
- Critical-event delivery requirements
- Relationship between application messages and RF packets/frames
- Ground/integration test interface

Exact values remain TBD.

### Wired and RF Paths

Where practical, the same application protocol should operate over both paths:

```text
                     +---- WIRED ----+
                     |               |
Ground Application --+               +--> EMBER Application
                     |               |
                     +----- RF ------+
```

This permits command, telemetry, and event software development before the complete radio system is available.

### Working Ownership

Ground Operations owns:

- Operator console
- Human-readable commands
- Command dictionary
- Telemetry/event dictionary
- Sequence-number tracking
- Transaction states
- Telemetry interpretation/display
- Event/alert presentation
- Ground-side logging
- Ground-software side of the wired test interface

Flight Communications owns:

- Flight radio
- Spacecraft antenna
- RF transmission/reception
- Radio-specific operation

Ground radio/modem and antenna implementation, console-to-radio interface, application-message handoff, communications error/status reporting, integration testing, and end-to-end verification are shared areas until final ownership is agreed.

## 11. Ground Test & Verification Strategy

Testing should progress from isolated software testing to complete end-to-end RF testing.

```text
Ground Console Software
        |
        v
Simulated Messages
        |
        v
Wired Connection to EMBER
        |
        v
Ground + Flight Communications Integration
        |
        v
RF End-to-End Test
```

Testing must verify both:

```text
Ground -> EMBER
Operator Commands
```

and:

```text
EMBER -> Ground
Autonomous Telemetry / Events
```

### Initial Verification Tests

| Test | Purpose | Expected Result |
|---|---|---|
| GO-01 Valid Command | Verify normal command transaction | ACK and expected result received |
| GO-02 Invalid Command | Verify rejection handling | NACK and correct reason displayed |
| GO-03 Mode Permission | Verify mode restrictions | Disallowed command blocked/rejected |
| GO-04 Timeout | Verify no-response handling | `TIMEOUT`; result shown `UNKNOWN` |
| GO-05 Duplicate Command | Verify duplicate protection | Duplicate recognized; action not blindly repeated |
| GO-06 Periodic Telemetry | Verify autonomous telemetry reception | Data generated, decoded, displayed, and logged |
| GO-07 Mode Event | Verify autonomous transition reporting | Previous/new mode and reason displayed/logged |
| GO-08 Fault Event | Verify autonomous fault reporting | Fault identified and logged |
| GO-09 Fire Detection Event | Verify autonomous mission-event handling | `FIRE_DETECTED` prominently displayed and logged |
| GO-10 Session Logging | Verify records | Commands, responses, telemetry, and events preserved |
| GO-11 Wired End-to-End | Verify development path | Console communicates successfully with EMBER over wired path |
| GO-12 RF End-to-End | Verify operational path | Commands, responses, telemetry, and events operate over RF |
| GO-13 On-Demand Status | Verify manual request with periodic telemetry active | Fresh status returned and correlated |
| GO-14 Communications Loss | Verify autonomous operation without ground link | EMBER continues operating and significant event is preserved |
| GO-15 Communications Recovery | Verify stored-event recovery | Preserved event becomes available after link restoration |
| GO-16 Heartbeat | Verify routine spacecraft indication | Heartbeat received, decoded, displayed, and logged |

### Fire Detection Verification

A fire-detection test should verify:

```text
Test / Simulated Payload Input
          |
          v
Payload Detection
          |
          v
FIRE_DETECTED
          |
          v
Event Stored
          |
          v
Event Routed
          |
          v
Ground Receives
          |
          v
Console Alerts
          |
          v
Event Logged
```

The test should not require an operator command to cause the Ground Operations software to receive and process the event once the spacecraft detection event has been generated.

### Communications-Loss Verification

Testing should verify that loss of ground communications does not by itself stop autonomous EMBER mission operation.

Conceptually:

```text
EVENT GENERATED
      |
      v
LINK AVAILABLE?
   |        |
  NO       YES
   |        |
   v        v
STORE     TRANSMIT
   |
   v
QUEUE
   |
   v
LINK RESTORED
   |
   v
EVENT AVAILABLE FOR DELIVERY
```

Exact retransmission and delivery-confirmation behavior remain TBD.

### Formal Test Record

Each formal test should record:

- Test ID and name
- Date/time
- Session ID
- Configuration
- Connection type
- Initial conditions
- Procedure
- Expected result
- Actual result
- Pass/fail determination
- Notes
- Associated log files

Exact timeout values, RF performance criteria, telemetry rates, event-delivery criteria, and electrical limits are not defined by this draft and will be established through subsystem design and integration testing.

## 12. Open Items & Team Decisions

### Flight Communications Decisions

Coordination with Flight Communications is required for:

- Ground radio/modem hardware and ownership
- Ground antenna
- Console-to-radio interface
- Radio data interface
- RF packet format
- Maximum message size
- Data rate
- Link-status information
- Communications error information
- RF integrity/error-control method
- Timing expectations
- Message-priority handling
- Critical-event delivery
- RF test capability

### Spacecraft Management / IHU Decisions

Coordination is required for:

- Command parser interface
- Mode-manager interface
- Onboard permission enforcement
- ACK/NACK generation
- NACK reason handling
- Sequence-number handling
- Duplicate-command detection
- Reset behavior
- Fault handling
- Spacecraft timestamps
- Periodic telemetry generation
- Autonomous event generation
- Event routing
- Message queue behavior
- Message priorities
- Autonomous mission-operation interfaces

### EPS Decisions

EPS will define the actual:

- Power/energy measurements
- Status fields
- Faults
- Temperatures
- Interlocks
- SAFE entry/recovery inputs
- Low-power event conditions

Ground Operations will not invent unavailable EPS telemetry.

### Payload Decisions

Payload will define actual:

- Payload states
- Checkout functions
- Capture parameters
- Detection result/metric
- Detection thresholds where applicable
- Location information if available
- Stored-data references
- Faults
- Payload status information
- Payload-to-IHU fire-detection interface

### Internal Messaging / Transport Decisions

The team must determine:

- Final internal subsystem transport interfaces
- Whether physical CAN is implemented for applicable interfaces
- CAN IDs/priorities if physical CAN is implemented
- SPI/UART/CAN responsibilities where applicable
- Mapping between application messages and physical transports
- Transport-specific framing
- Buffering and queue behavior

The CAN-style application messaging concept does not by itself select CAN as the physical transport.

### Ground Operations Implementation Decisions

Ground Operations still owns later selection of:

- Console programming language
- GUI/framework
- Log storage format
- Configuration format
- Wired-interface implementation
- Operator-screen layout
- Alert presentation
- Log export method
- Session ID implementation
- Ground-side timeout configuration
- Stale-data thresholds

### Protocol Status

| Item | Status |
|---|---|
| Application message categories | Draft defined |
| Autonomous operation concept | Draft defined |
| Command IDs | Draft defined |
| Telemetry IDs | Draft defined |
| Event IDs | Draft defined |
| ACK/NACK concept | Defined |
| NACK reason codes | Draft defined |
| Sequence-number requirement | Defined |
| Sequence-number field size | TBD |
| Sequence rollover | TBD |
| Duplicate history/window | TBD |
| Parameter encoding | TBD |
| Timestamp format | TBD |
| Integrity-check method | TBD |
| Maximum application-message size | TBD |
| RF packet format | TBD with Flight Communications |
| Command timeout values | TBD through testing |
| Periodic telemetry rates | TBD |
| Message priorities | TBD |
| Event queue size | TBD |
| Event retention | TBD |
| Critical-event acknowledgment | TBD |
| Event retransmission behavior | TBD |
| Fire-detection message fields | Draft / TBD with Payload |
| Log storage format | TBD |
| Wired physical interface | TBD |
| Ground radio interface | TBD |
| Physical CAN implementation | TBD by applicable interfaces |

## 13. Draft 0.2 Status and Next Development

Draft 0.2 defines the Ground Operations behavioral and application-messaging architecture.

The architecture now includes:

- Autonomous spacecraft operation
- Periodic telemetry
- Event-driven spacecraft messages
- Fire-detection event reporting
- Operator commands
- On-demand information requests
- ACK/NACK behavior
- Command states and timeout philosophy
- Sequence-number and duplicate-command concepts
- Application-level message structures
- Ground console behavior
- Event and telemetry logging
- Ground/Flight Communications boundary
- Wired test concept
- Autonomous-event testing
- Communications-loss testing
- Initial verification tests
- Remaining interface TBDs

The next development activity is to coordinate these application-message and interface requirements with Flight Communications, Spacecraft Management, EPS, and Payload.

Final message IDs, field sizes, data types, telemetry rates, message priorities, event-delivery behavior, physical transport mapping, packet limits, timestamp format, integrity method, and timeout values should not be locked until the applicable subsystem interfaces are resolved.
