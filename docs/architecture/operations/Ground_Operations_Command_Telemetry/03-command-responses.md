# EMBER Command Responses

**Status:** Draft 0.2

This document defines responses to operator-initiated commands. Autonomous periodic telemetry and event-driven messages are not required to originate from a command transaction and therefore do not normally use this command-response sequence.

## ACK

ACK means a command was received, recognized, validated, and accepted for execution. It does not necessarily mean the requested action is complete.

```text
GROUND -> SET_MODE: NOMINAL

EMBER -> ACK: SET_MODE

EMBER -> MODE_EVENT: SAFE -> NOMINAL
