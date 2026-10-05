# EMBER Command Responses

**Mission design draft:** this page records proposed application behavior.
For commands available in the current lab, use the [Yamcs operator guide](../../../user/yamcs.md)
and [bench contract](../../../../system/protocols/ember_bench_v1.md). Draft commands
such as SET_MODE and REBOOT_IHU are not exposed by the current Yamcs bench MDB.

**Status:** Draft 0.2

This document defines responses to operator-initiated commands. Autonomous periodic telemetry and event-driven messages are not required to originate from a command transaction and therefore do not normally use this command-response sequence.

## ACK

ACK means a command was received, recognized, validated, and accepted for execution. It does not necessarily mean the requested action is complete.

```text
GROUND -> SET_MODE: NOMINAL

EMBER -> ACK: SET_MODE

EMBER -> MODE_EVENT: SAFE -> NOMINAL
```
