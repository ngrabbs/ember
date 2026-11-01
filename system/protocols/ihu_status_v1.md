# Solicited IHU status snapshot over UHF

`REQUEST_STATUS` (command 2, no arguments) returns one correlated `IHU_STATUS`
(telemetry 58, payload version 1) on the operational UHF route. This replaces
neither the existing uncorrelated SYSTEM_STATUS stream nor its wire layout.
The response is 56 bytes including the native header/CRC; payload is 24 bytes.

The dictionary defines field order and types. Mode/configuration/output flags
come from the live IHU policy. `boot_ready_ms` records the end of application
initialization in IHU uptime milliseconds, after CAN and sensor-task startup;
it is not a ground round-trip measurement or evidence of health qualification.
CAN readiness and EFLG are observed controller values. `eps_attempted` and
`eps_valid` describe the latest housekeeping register read only. Age is
UINT32_MAX when no valid current readout exists. Battery mV is INT32_MIN
(unavailable) in this snapshot; use native POWER_STATUS for electrical data.
Device states are aged at snapshot generation. `health_gate_implemented=0`
explicitly discloses that automatic mission enablement based on health is absent.
No field declares a disconnected battery healthy.

Yamcs publishes correlated completion, elapsed milliseconds, native packet bytes,
IHU boot ID, actual mode/output mask, initialization time, CAN and EPS status.
Missing radio replies remain UNKNOWN/TIMEOUT; they are not healthy status.
COMMS and ground admit only the exact command/response contract, matching epoch,
transaction and IHU identity with valid native CRC. No automatic retry or
unsolicited transmission is introduced. The bench bridge remains disabled.
