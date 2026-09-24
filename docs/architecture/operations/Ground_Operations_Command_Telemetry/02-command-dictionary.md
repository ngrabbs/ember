# EMBER Command Dictionary

**Status:** Draft 0.2

This document defines operator-initiated commands available through Ground Operations.

EMBER is intended to operate autonomously during normal mission operations. Commands are therefore used for manual control, configuration, testing, recovery, troubleshooting, and on-demand information requests. Routine mission operation, periodic telemetry, and event reporting do not require an operator command.

Command IDs, parameters, and permissions are preliminary.

## Command Dictionary

| ID | Command | Purpose | Parameters | Allowed Modes | Expected Response |
|---|---|---|---|---|---|
| 0x01 | PING | Verify command connection | None | COMMISSIONING, SAFE, NOMINAL | ACK + link response |
| 0x02 | REQUEST_STATUS | Request current basic spacecraft health/status | None | STARTUP*, COMMISSIONING, SAFE, NOMINAL | ACK + current status telemetry |
| 0x03 | REQUEST_TELEMETRY | Request current detailed telemetry | Data group | COMMISSIONING, SAFE*, NOMINAL | ACK + requested telemetry |
| 0x10 | SET_MODE | Request mode change | Requested mode | COMMISSIONING, SAFE, NOMINAL | ACK/NACK + mode event |
| 0x11 | CLEAR_FAULT | Clear recoverable fault | Fault ID | COMMISSIONING, SAFE*, NOMINAL | ACK/NACK + fault status |
| 0x12 | REBOOT_IHU | Controlled IHU restart | Confirmation value | COMMISSIONING*, SAFE*, NOMINAL* | ACK before reboot |
| 0x20 | PAYLOAD_CHECK | Perform payload checkout | Test selection | COMMISSIONING | ACK/NACK + results |
| 0x21 | PAYLOAD_CAPTURE | Request manual payload capture | Capture parameters | COMMISSIONING*, NOMINAL | ACK/NACK + payload status |
| 0x22 | REQUEST_DETECTION_DATA | Request stored detection/event data | Record/range | COMMISSIONING*, NOMINAL | ACK + data |
| 0x30 | SET_PARAMETER | Change approved parameter | Parameter ID + value | COMMISSIONING*, SAFE*, NOMINAL* | ACK/NACK + value |
| 0x31 | REQUEST_LOG | Request event/operations log | Log type/range | COMMISSIONING, SAFE*, NOMINAL | ACK + log |
| 0x40 | DEPLOY_TEST | Exercise deployment logic without flight deployment | Test selection | GROUND TEST ONLY | ACK/NACK + result |

\* Conditional; applicable permission checks must pass.

## Command Categories

Operator commands are grouped by purpose.

### Information Requests

These commands allow the operator to request current or stored information at any time permitted by the spacecraft mode.

- `PING`
- `REQUEST_STATUS`
- `REQUEST_TELEMETRY`
- `REQUEST_DETECTION_DATA`
- `REQUEST_LOG`

For example, EMBER may already provide periodic spacecraft status automatically, but `REQUEST_STATUS` allows the operator to request a fresh status report without waiting for the next scheduled update.

### Control and Configuration

These commands allow the operator to intentionally change spacecraft behavior or configuration.

- `SET_MODE`
- `CLEAR_FAULT`
- `SET_PARAMETER`
- `REBOOT_IHU`

These commands require onboard validation before execution.

### Payload and Test Commands

These commands provide manual payload operation and ground/integration testing.

- `PAYLOAD_CHECK`
- `PAYLOAD_CAPTURE`
- `DEPLOY_TEST`

Manual payload commands supplement autonomous payload operation and are not required for normal fire-detection activities.

## Relationship to Autonomous Operation

Commands do not initiate routine EMBER mission operation.

During normal operation, EMBER should autonomously:

- Monitor spacecraft health
- Perform scheduled mission activities
- Operate the payload when mission conditions permit
- Process payload data
- Generate periodic telemetry
- Generate event messages when significant conditions occur
- Store and queue mission events for transmission when required

Significant events such as fire detections and spacecraft faults should be generated and reported without waiting for an operator request.

Operator commands remain available when direct intervention or additional information is needed.

## Command Sequence Number

Every operator command should include a sequence number.

```text
SEQ: 0042
COMMAND: SET_MODE
PARAMETER: NOMINAL
