# EMBER Ground Operations Console

**Status:** Draft 0.2

The Ground Operations Console provides the primary human interface to EMBER.

The console is primarily used to monitor spacecraft health and mission activity, display alerts and events, review telemetry and historical data, and provide operator command capability when manual interaction is required.

Normal EMBER mission operation does not require continuous operator input.

## Primary Console Functions

The console should allow the operator to:

- Monitor current spacecraft mode and configuration
- Monitor spacecraft health, power, temperatures, faults, payload, communications, and storage
- Receive and display periodic telemetry
- Receive and prominently display significant event messages
- Alert the operator to fire detections and spacecraft faults
- View telemetry age and communication status
- Review historical telemetry and event information
- Send permitted operator commands
- Request current status or telemetry on demand
- Receive and display ACK/NACK responses
- Track command transaction status
- Review command, telemetry, and event logs

## Monitoring and Status

The console should provide an at-a-glance view of current spacecraft condition.

```text
EMBER GROUND OPERATIONS

--------------------------------

MODE:             NOMINAL
CONFIGURATION:    FLIGHT
SYSTEM HEALTH:    OK

POWER:            OK
PAYLOAD:          IDLE
COMMUNICATIONS:   CONNECTED
STORAGE:          OK
FAULTS:           NONE

--------------------------------

Last Telemetry:   14:32:08
Telemetry Age:    4 sec
