# Yamcs command dictionary

## Available in Yamcs

Use the [Yamcs operator guide](../../../ground/yamcs/README.md) to select the
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
| `ember` | `0x000D` | `SET_RADIO_PROFILE` | `profile`: `DBPSK_1200_V3` or `DBPSK_DL1500_V3` | Stages a timed UHF downlink profile trial and returns `RADIO_CONFIG`. |
| `ember` | `0x000E` | `CONFIRM_RADIO_PROFILE` | `confirmation_token` from the active trial readback | Confirms the trial profile. An unconfirmed trial rolls back automatically. |
| `ember-bench` | `0x0400` | `PAYLOAD_PING` | `bytes`: 1–240, default 1 | `PAYLOAD_PING_RESULT` with echo status and round-trip time. |
| `ember-bench` | `0x0401` | `PAYLOAD_IDENT` | None | `PAYLOAD_FIRMWARE` with build identity. |
| `ember-bench` | `0x0402` | `PAYLOAD_STATUS_QUERY` | None | `PAYLOAD_STATUS` status report. |
| `ember-bench` | `0x0403` | `PAYLOAD_HEARTBEAT_QUERY` | None | `PAYLOAD_STATUS` heartbeat report. |
| `ember`, `ember-bench` | `0x0404` | `PAYLOAD_FIRE_CHECK` | None | `PAYLOAD_FIRE_RESULT` with result, execution mode, and check ID. Use the check ID to correlate capture GPS if it arrives. |

Argument defaults above are the values shown in the Yamcs command editor.
