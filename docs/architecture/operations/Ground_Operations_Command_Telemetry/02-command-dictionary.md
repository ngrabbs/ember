# EMBER Command Dictionary

## Available in Yamcs

Use the [Yamcs operator guide](../../../../ground/yamcs/README.md) to select the
instance and check Command History. `ember` uses UHF. `ember-bench` uses the
direct IHU USB bridge and requires regular GROUND_TEST firmware for payload
commands. The UHF startup profile restricts USB to read-only console commands.

These are the commands exposed by the lab station as of November 15, 2026.
Results below describe successful execution. Check the correlated response
and any listed telemetry. A timeout leaves the outcome unknown.

| Instance | Wire ID | Command | Arguments | Expected result |
|---|---|---|---|---|
| `ember` | `0x0001` | `PING` | None | Correlated `COMMAND_RESPONSE` confirms the command path. |
| `ember` | `0x0002` | `REQUEST_STATUS` | None | `SYSTEM_STATUS`; the IHU also queues `UHF_SCHEDULE_STATUS`. |
| `ember` | `0x0003` | `REQUEST_TELEMETRY` | `data_group`: `1` (SYSTEM, default) or `48` (COMMS) | Requested `SYSTEM_STATUS` or `COMM_STATUS`. |
| `ember` | `0x0004` | `STATUS_CAPTURE` | None | Freezes five 1 Hz status records in RAM and returns a capture ID. |
| `ember` | `0x0005` | `STATUS_FETCH` | `capture_id` from `STATUS_CAPTURE` | `STATUS_RECORDS` for that capture. |
| `ember` | `0x0006` | `IHU_REBOOT` | None | Acknowledges the scheduled reboot when SAFE with outputs off. Verify the new boot with `REQUEST_STATUS`. |
| `ember` | `0x0007` | `SET_HEARTBEAT` | `enabled`: `0` (default) or `1` | Completion reports the applied value. When enabled, heartbeat runs every 10 s. |
| `ember` | `0x0008` | `SET_UHF_TELEMETRY_SCHEDULE` | `listen_seconds`: 1–3600, default 120. `telemetry_seconds`: 5–3600, default 60. | Completion reports the applied schedule. Check `UHF_SCHEDULE_STATUS`. |
| `ember` | `0x0009` | `SET_UHF_TELEMETRY` | `enabled`: `0` (default) or `1` | Completion reports whether the schedule was stopped or enabled. |
| `ember` | `0x000A` | `SET_UHF_TELEMETRY_SET` | `telemetry_set`: `BASIC` or `FULL` (default) | Completion reports the selected telemetry set. |
| `ember` | `0x000B` | `REQUEST_IHU_FAULTS` | None | `IHU_FAULTS` with the latest 16 retained entries and this boot’s fault total. |
| `ember` | `0x000C` | `REQUEST_RADIO_CONFIG` | None | `RADIO_CONFIG` with the transceiver’s active settings, defaults, and supported profiles. |
| `ember-bench` | `0x0400` | `PAYLOAD_PING` | `bytes`: 1–240, default 1 | `PAYLOAD_PING_RESULT` with echo status and round-trip time. |
| `ember-bench` | `0x0401` | `PAYLOAD_IDENT` | None | `PAYLOAD_FIRMWARE` with build identity. |
| `ember-bench` | `0x0402` | `PAYLOAD_STATUS_QUERY` | None | `PAYLOAD_STATUS` status report. |
| `ember-bench` | `0x0403` | `PAYLOAD_HEARTBEAT_QUERY` | None | `PAYLOAD_STATUS` heartbeat report. |
| `ember`, `ember-bench` | `0x0404` | `PAYLOAD_FIRE_CHECK` | None | `PAYLOAD_FIRE_RESULT` with result, execution mode, and check ID. Use the check ID to correlate capture GPS if it arrives. |

Argument defaults above are the values shown in the Yamcs command editor.

## Proposed mission commands

**Mission design draft · 0.2.** The table and examples below retain the
original proposal. IDs, parameters, permissions, and responses are preliminary.
Use the live table above for lab operations.

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
```
