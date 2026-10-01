# EMBER Ground Operations Console
**Status:** Draft 0.1

The console should allow the operator to view spacecraft mode/configuration, health, power, temperatures, faults, payload, communications, and storage; send permitted commands; receive ACK/NACK; view command results and detection/mode events; and review command/telemetry history.

## Command Controls
The console should prevent obviously invalid commands based on reported mode, without replacing onboard validation.

```text
CURRENT MODE: SAFE

REQUEST STATUS       AVAILABLE
REQUEST TELEMETRY    CONDITIONAL
PAYLOAD CAPTURE      DISABLED
FIRE OBSERVATION     DISABLED
RETURN TO NOMINAL    CONDITIONAL
REBOOT IHU           CONDITIONAL
```

## Example Status Display
```text
EMBER GROUND OPERATIONS
--------------------------------
MODE:            NOMINAL
CONFIGURATION:   FLIGHT
SYSTEM HEALTH:   OK
POWER:           OK
PAYLOAD:         IDLE
COMMUNICATIONS:  CONNECTED
STORAGE:         OK
FAULTS:          NONE
--------------------------------
Last Telemetry:  14:32:08
```

The console should clearly distinguish SAFE entry, faults, command rejection, mode changes, communications/payload faults, and fire-detection events. Final GUI and storage details are TBD.

## Draft 0.1 Behavior
The console should identify stale/unknown telemetry instead of presenting old values as current; prominently display `GROUND TEST` versus `FLIGHT`; show command transaction states; translate NACK reason codes into human-readable information; and distinguish ground-interface connectivity from confirmed spacecraft communication.

Selected higher-consequence commands require explicit operator confirmation. Normal operation uses human-readable commands and parameters rather than raw command IDs.
