# EMBER Command Dictionary
**Status:** Draft 0.1

Command IDs, parameters, and permissions are preliminary.

| ID | Command | Purpose | Parameters | Allowed Modes | Expected Response |
|---|---|---|---|---|---|
| 0x01 | PING | Verify command connection | None | COMMISSIONING, SAFE, NOMINAL | ACK + link response |
| 0x02 | REQUEST_STATUS | Request basic spacecraft health/status | None | STARTUP*, COMMISSIONING, SAFE, NOMINAL | ACK + status telemetry |
| 0x03 | REQUEST_TELEMETRY | Request detailed telemetry | Data group | COMMISSIONING, SAFE*, NOMINAL | ACK + telemetry |
| 0x10 | SET_MODE | Request mode change | Requested mode | COMMISSIONING, SAFE, NOMINAL | ACK/NACK + mode event |
| 0x11 | CLEAR_FAULT | Clear recoverable fault | Fault ID | COMMISSIONING, SAFE*, NOMINAL | ACK/NACK + fault status |
| 0x12 | REBOOT_IHU | Controlled IHU restart | Confirmation value | COMMISSIONING*, SAFE*, NOMINAL* | ACK before reboot |
| 0x20 | PAYLOAD_CHECK | Perform payload checkout | Test selection | COMMISSIONING | ACK/NACK + results |
| 0x21 | PAYLOAD_CAPTURE | Request payload capture | Capture parameters | COMMISSIONING*, NOMINAL | ACK/NACK + payload status |
| 0x22 | REQUEST_DETECTION_DATA | Request stored detection/event data | Record/range | COMMISSIONING*, NOMINAL | ACK + data |
| 0x30 | SET_PARAMETER | Change approved parameter | Parameter ID + value | COMMISSIONING*, SAFE*, NOMINAL* | ACK/NACK + value |
| 0x31 | REQUEST_LOG | Request event/operations log | Log type/range | COMMISSIONING, SAFE*, NOMINAL | ACK + log |
| 0x40 | DEPLOY_TEST | Exercise deployment logic without flight deployment | Test selection | GROUND TEST ONLY | ACK/NACK + result |

\* Conditional; applicable permission checks must pass.

## Command Sequence Number
Every command should include a sequence number.

```text
SEQ: 0042
COMMAND: SET_MODE
PARAMETER: NOMINAL
```

## Initial Logical Structure
```text
Sequence Number
  |
Command ID
  |
Parameters
  |
Integrity Check
```

Final packet format, field sizes, and integrity-check method are TBD. Ground Operations should block obviously invalid commands, while onboard software independently validates every command.
