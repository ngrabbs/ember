# EMBER Command / Telemetry Protocol
**Status:** Draft 0.1

This document defines the Ground Operations application-level command/telemetry behavior. It intentionally does not define the final RF frame, binary field sizes, or radio-specific transport.

## 1. Command Transaction Flow
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
| Generate response/telemetry | Spacecraft Management / affected subsystem |
| RF return path | Flight Communications |
| Decode/display/log | Ground Operations |

The wired development path may bypass RF while preserving the same application-level protocol:

```text
Ground Console -> Wired Test Interface -> IHU
```

## 2. Command States
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

Possible branches include `SENT -> NACKED`, while either `SENT` or `ACKNOWLEDGED` may ultimately lead to `TIMEOUT` when an expected response is not received.

A timeout means **the outcome is unknown until spacecraft status can be verified**. A generic `FAILED` state is not used in Draft 0.1 because it does not distinguish rejection, loss of communications, or an unknown result.

## 3. Timeout & Retry Behavior
No automatic command retries are required in Draft 0.1.

```text
COMMAND SENT
    |
    +--> ACK/NACK received -> Continue transaction
    |
    +--> No expected response -> TIMEOUT -> Outcome UNKNOWN -> Verify status
```

Read-only requests such as `PING`, `REQUEST_STATUS`, `REQUEST_TELEMETRY`, `REQUEST_DETECTION_DATA`, and `REQUEST_LOG` may be manually resent. Commands that change spacecraft state require verification before resending where practical.

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

## 4. Sequence Numbers & Duplicate Handling
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

## 5. Command & Response Message Structure
### Command
```text
Sequence Number
Command ID
Parameters
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
| `REBOOT_IHU` | New `RESET_STATUS` / reconnection |
| `PAYLOAD_CHECK` | Payload test result |
| `PAYLOAD_CAPTURE` | Updated `PAYLOAD_STATUS` and/or resulting event |
| `REQUEST_DETECTION_DATA` | Requested records received |
| `SET_PARAMETER` | Resulting parameter value verified |
| `REQUEST_LOG` | Requested log received |
| `DEPLOY_TEST` | Deployment-test result |

### Telemetry
```text
Telemetry ID
Timestamp
Telemetry Data
Integrity Check
```

Example:

```text
TELEMETRY:  MODE_EVENT
TIME:       14:32:18
PREVIOUS:   SAFE
NEW:        NOMINAL
REASON:     GROUND_COMMAND
INTEGRITY:  TBD
```

Command responses carry the originating sequence number. Routine asynchronous telemetry does not require a command sequence number. Telemetry directly associated with a command should include, or otherwise permit, correlation to the originating transaction where practical.

Application-level definitions are separate from RF transport/framing. Flight Communications may wrap application data in radio-specific headers, addressing, packet types, error-control fields, or other transport information.

## 6. Ground Console Behavior
The console behavior is defined functionally; the final GUI layout and software framework remain TBD.

### Primary Functions
The console should provide:
- Spacecraft status and configuration
- Command selection and parameters
- Command transaction status
- Telemetry and event display
- Command/system history and logging

At minimum, the operator should be able to view mode, configuration, system health, power, payload, communications, storage, faults, and the time of the most recent telemetry.

### Stale Data
The console shall distinguish current information from missing, unknown, or stale telemetry. Old information shall not continue to be presented as current without an indication that it is stale. The stale-data threshold is TBD.

### Command Permissions
The console should use the Permission Matrix to disable commands that are obviously inappropriate for the reported spacecraft mode. Ground-side filtering is an operator aid and does not replace onboard validation.

If required spacecraft state is unknown or stale, commands that depend on that state should not be treated as known-safe solely from the console's previous local state.

### Confirmation
Routine read-only commands do not require an additional confirmation. Selected higher-consequence commands should require explicit operator confirmation. Initial candidates include `REBOOT_IHU`, `DEPLOY_TEST`, and selected `SET_MODE` or `SET_PARAMETER` operations. The final confirmation list is configurable/TBD.

Example:

```text
CONFIRM COMMAND
Command: REBOOT_IHU
Current Mode: NOMINAL
Warning: This command will restart the flight computer.

[Cancel] [Confirm & Send]
```

### Transaction Display
The console shall display `CREATED`, `SENT`, `ACKNOWLEDGED`, `COMPLETED`, `NACKED`, and `TIMEOUT` states. NACK reason codes should be translated into human-readable descriptions.

A timeout shall be shown as an unknown outcome rather than an automatic failure or success. The console should recommend status verification before resending state-changing commands.

### Events and Alerts
Initial event categories are:
- **Information:** mode change, normal command completion
- **Warning:** timeout, degraded communications, noncritical fault
- **Critical:** SAFE entry or critical spacecraft fault

A fire detection is a mission event and should be displayed prominently without automatically classifying it as a spacecraft fault.

### Communications Indication
The console should distinguish, where data permits, between ground-interface connectivity, radio readiness, RF receive activity, and recent spacecraft communications. A connected ground device shall not automatically imply that EMBER communication is confirmed.

### Configuration Indication
`GROUND TEST` versus `FLIGHT` shall be prominently displayed. Test-only commands shall not be enabled solely by operator selection; the spacecraft-reported configuration must permit them.

### Operator Interface
Normal operation should use human-readable command names and parameters. Raw command construction may be provided later as a developer/debug capability but is not the normal operator workflow.

## 7. Logging & Data Storage
Each operating or test period should have a unique Session ID so its records can be grouped together. The exact Session ID format remains configurable.

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
Each command should maintain a transaction history containing applicable times for creation, transmission, ACK/NACK, completion, timeout, final state, and completion evidence.

### Raw and Decoded Data
Ground Operations should preserve raw received command/telemetry data where practical in addition to decoded operator-readable records. This permits later reprocessing if the decoder changes or an integration problem must be investigated.

### Telemetry and Detection Records
Telemetry records should preserve the telemetry ID/type, timestamp, decoded values, and source. Detection events should have unique event records containing available metadata such as event ID, timestamp, result, detection metric/confidence, location, payload status, and stored-data reference. Fields not yet defined remain TBD.

Large payload products should normally be referenced by the event record rather than embedded directly in routine logs.

### Time
Ground Operations shall timestamp locally generated events and preserve spacecraft-provided timestamps when available. Ground receive time and spacecraft event time should remain distinguishable when both exist. Final clock synchronization and timestamp format are TBD.

### Storage
Starting a new session shall not overwrite previous session records. Logs shall use a structured, machine-readable format that can be reviewed or exported by the team. CSV, JSON, SQLite, or another format may be selected during implementation; the final storage technology and retention policy are TBD.

## 8. Ground Operations / Flight Communications Interface
Ground Operations creates application-level messages; Flight Communications transports those messages over the communications path.

### Ground Operations Provides
- Application-level command information
- Sequence number
- Command ID
- Parameters
- Application integrity information, if used
- Operator/console requirements

### Flight Communications Provides
- Received application data
- Radio/link status information that the selected hardware can provide
- Communications errors that can be exposed to Ground Operations
- RF transport between ground and spacecraft

Ground Operations then decodes received data, correlates command responses, updates transaction state, updates telemetry, generates operator events, and logs the results.

### Shared Interface Contract
Ground Operations and Flight Communications must agree on:
- Console-to-radio physical/software interface
- Application-message representation at the handoff
- Maximum message size
- Link-status information
- Communications error reporting
- Connection state reporting
- Timing expectations
- Relationship between application messages and RF packets/frames
- Ground/integration test interface

Exact values remain TBD.

### Wired and RF Paths
Where practical, the same application protocol should operate over both paths:

```text
                    +---- WIRED ----+
                    |               |
Ground Application -+               +--> EMBER Application
                    |               |
                    +----- RF ------+
```

This permits command/telemetry software development before the complete radio system is available.

### Working Ownership
Ground Operations owns the operator console, human-readable commands, command/telemetry dictionaries, sequence-number tracking, transaction states, telemetry interpretation/display, logging, and the ground-software side of the wired test interface.

Flight Communications owns the flight radio, spacecraft antenna, RF transmission/reception, and radio-specific operation.

Ground radio/modem and antenna implementation, console-to-radio interface, application-message handoff, communications error/status reporting, integration testing, and end-to-end verification are shared areas until final ownership is agreed.

## 9. Ground Test & Verification Strategy
Testing should progress from isolated software testing to complete end-to-end RF testing:

```text
Ground Console Software
        |
        v
Simulated Command / Telemetry
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

### Initial Verification Tests
| Test | Purpose | Expected Result |
|---|---|---|
| GO-01 Valid Command | Verify normal command transaction | ACK and expected result received |
| GO-02 Invalid Command | Verify rejection handling | NACK and correct reason displayed |
| GO-03 Mode Permission | Verify mode restrictions | Disallowed command blocked/rejected |
| GO-04 Timeout | Verify no-response handling | `TIMEOUT`; result shown `UNKNOWN` |
| GO-05 Duplicate Command | Verify duplicate protection | Duplicate recognized; action not blindly repeated |
| GO-06 Telemetry | Verify telemetry reception | Data decoded, displayed, and logged |
| GO-07 Mode Event | Verify transition reporting | Previous/new mode and reason displayed/logged |
| GO-08 Fault Event | Verify fault reporting | Fault identified and logged |
| GO-09 Detection Event | Verify mission-event handling | Detection prominently displayed and logged |
| GO-10 Session Logging | Verify records | Commands, responses, telemetry, and events preserved |
| GO-11 Wired End-to-End | Verify development path | Console communicates successfully with EMBER over wired path |
| GO-12 RF End-to-End | Verify operational path | Complete command/response transaction succeeds over RF |

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

Exact timeout values, RF performance criteria, telemetry rates, and electrical limits are not defined by this draft and will be established through subsystem design and integration testing.

## 10. Open Items, Team Decisions & Draft 0.1 Exit Criteria
### Flight Communications Decisions
Coordination with Flight Communications is required for ground radio/modem hardware and ownership, ground antenna, console-to-radio interface, radio data interface, RF packet format, maximum message size, data rate, link-status information, communications error information, RF integrity/error-control method, timing expectations, and RF test capability.

### Spacecraft Management / IHU Decisions
Coordination is required for command parser interface, mode-manager interface, onboard permission enforcement, ACK/NACK generation, NACK reason handling, sequence-number handling, duplicate-command detection, reset behavior, fault handling, spacecraft timestamps, and telemetry generation.

### EPS Decisions
EPS will define the actual power/energy measurements, status fields, faults, temperatures, and interlocks available to Ground Operations. Ground Operations will not invent unavailable EPS telemetry.

### Payload Decisions
Payload will define actual payload states, checkout functions, capture parameters, detection result/metric, location information if available, stored-data references, faults, and other payload status information.

### Ground Operations Implementation Decisions
Ground Operations still owns later selection of console programming language, GUI/framework, log storage format, configuration format, wired-interface implementation, operator-screen layout, log export method, Session ID implementation, and ground-side timeout configuration.

### Protocol Status
| Item | Status |
|---|---|
| Command IDs | Draft defined |
| Telemetry IDs | Draft defined |
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
| Telemetry update rates | TBD |
| Log storage format | TBD |
| Wired physical interface | TBD |
| Ground radio interface | TBD |

### Draft 0.1 Exit Criteria
Draft 0.1 is considered architecturally complete when the following are documented:
- Command categories and draft IDs
- Telemetry categories and draft IDs
- ACK/NACK behavior and reason codes
- Command states and timeout philosophy
- Sequence-number concept and duplicate-command requirement
- Application-level message structure
- Ground console behavior
- Logging requirements
- Ground/Flight Communications boundary
- Wired test concept
- Initial verification tests
- Remaining TBDs and responsible interfaces

Draft 0.1 defines behavioral architecture rather than final binary encoding. Draft 0.2 should incorporate actual interface information from Flight Communications, Spacecraft Management, EPS, and Payload and begin locking down field sizes, data types, parameter definitions, telemetry contents, packet limits, timestamp format, integrity method, timeout values, and telemetry rates.
