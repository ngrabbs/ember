# EMBER Command Responses
**Status:** Draft 0.1

## ACK
ACK means a command was received, recognized, validated, and accepted for execution. It does not necessarily mean the action is complete.

```text
GROUND -> SET_MODE: NOMINAL
EMBER -> ACK: SET_MODE
EMBER -> MODE_EVENT: SAFE -> NOMINAL
```

## NACK
| Code | Reason | Meaning |
|---|---|---|
| 0x01 | UNKNOWN_COMMAND | Command ID not recognized |
| 0x02 | INVALID_PARAMETER | Invalid parameter |
| 0x03 | MODE_NOT_ALLOWED | Command not permitted in current mode |
| 0x04 | INTERLOCK | Safety/permission condition not satisfied |
| 0x05 | BUSY | System cannot perform command now |
| 0x06 | FAULT_ACTIVE | Active fault prevents execution |
| 0x07 | NOT_AVAILABLE | Requested function unavailable |

Responses should include the originating command sequence number.

## Ground Command Log
```text
14:32:01  SEQ 0041  REQUEST_STATUS   SENT
14:32:02  SEQ 0041  ACK              RECEIVED
14:32:02  SEQ 0041  STATUS           NOMINAL
14:34:16  SEQ 0042  PAYLOAD_CAPTURE  SENT
14:34:17  SEQ 0042  NACK             INTERLOCK
```

Ground Operations distinguishes COMMAND SENT, COMMAND RECEIVED, COMMAND ACCEPTED, COMMAND EXECUTED, and RESULT CONFIRMED.

## Transaction States
Ground Operations tracks each command as `CREATED`, `SENT`, `ACKNOWLEDGED`, `COMPLETED`, `NACKED`, or `TIMEOUT`.

A `TIMEOUT` means the outcome is unknown until spacecraft status can be verified. Draft 0.1 does not use automatic command retries. A retransmission of the same transaction retains its original sequence number; a new operator command receives a new sequence number.
