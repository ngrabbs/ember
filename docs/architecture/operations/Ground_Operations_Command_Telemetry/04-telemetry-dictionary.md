# EMBER Telemetry Dictionary
**Status:** Draft 0.1

| ID | Telemetry Item | Purpose | Example Data | Availability |
|---|---|---|---|---|
| 0x01 | SYSTEM_STATUS | Overall status | Mode, configuration, health | All operational modes |
| 0x02 | CURRENT_MODE | Current mode | BOOT, STARTUP, COMMISSIONING, SAFE, NOMINAL | All modes |
| 0x03 | MODE_EVENT | Mode transition | Previous/new mode, reason | On mode change |
| 0x04 | RESET_STATUS | IHU restart reason | Power-on, command, watchdog, fault | After boot |
| 0x05 | UPTIME | Time since reset | Seconds | IHU operational |
| 0x10 | POWER_STATUS | Power condition | Battery voltage/current, energy | As available |
| 0x11 | THERMAL_STATUS | Temperatures | IHU, payload, radio, battery | As available |
| 0x12 | FAULT_STATUS | Faults/warnings | ID, severity, state | All operational modes |
| 0x20 | PAYLOAD_STATUS | Payload state | Off, idle, capturing, processing, fault | COMMISSIONING/NOMINAL |
| 0x21 | DETECTION_EVENT | Possible fire detection | Event ID, result, time | When generated |
| 0x22 | STORAGE_STATUS | Storage condition | Used/free, record count | As available |
| 0x30 | COMM_STATUS | Communications condition | RX/TX, errors, link info | When available |
| 0x31 | COMMAND_RESPONSE | Command result | Sequence #, ACK/NACK, reason | After command |
| 0x32 | GROUND_LINK_STATUS | Link information | Packet/error statistics TBD | Link active |
| 0x40 | DEPLOYMENT_STATUS | Deployment condition | Armed, completed, fault | STARTUP/as required |
| 0x41 | CONFIG_STATUS | Configuration | GROUND TEST or FLIGHT | Boot/on request |
| 0x50 | EVENT_LOG | Historical events | ID, timestamp, information | On request |

## Telemetry Categories
1. Periodic health telemetry
2. Event telemetry
3. Command-response telemetry

## Detection Event Contents
```text
Event ID
Timestamp
Detection Result
Detection Confidence / Metric  TBD
Location                       TBD
Payload Status
Stored Data Reference
```

## Minimum SAFE Telemetry
```text
Current Mode
SAFE Entry Reason
Battery / Energy State
Critical Temperatures
Active Faults
Communications Status
Recovery Status
```

SAFE mode prioritizes essential health and recovery information over routine mission data.
