# System overview

[Architecture](README.md) · [Interfaces](../../system/README.md)

**Status: architecture summary; operating modes are a separate draft.** EMBER
combines power, housekeeping, radio, and payload subsystems on the CSKB stack.
See [project scope](project_scope.md) for mission goals and validation scope.

| Subsystem | Responsibility |
|---|---|
| EPS | Energy input/storage, charging, rail generation, and power observability |
| Internal Housekeeping Unit (IHU) | System orchestration, command authority, and telemetry aggregation |
| Communications | RF uplink/downlink processing and the bridge to the IHU |
| Payload | Observation, detection processing, and mission data |

## Power and data flow

- **Power:** EPS supplies regulated rails; the documented payload carrier draws
  VBAT into a local converter. See [power interfaces](../../system/interfaces/power_interfaces.md).
- **Commands:** RF uplink → comms → IHU validation → subsystem dispatch.
- **Telemetry:** subsystem status and payload reports → IHU → comms downlink.
- **Buses:** I2C handles housekeeping; SPI carries IHU–comms data. CAN A/B is
  allocated for Iteration 2 control/status traffic. See the
  [interconnect plan](../../system/interfaces/board_to_board.md).

## Operating behavior

The [operations draft](operations/README.md) proposes BOOT, STARTUP,
COMMISSIONING, SAFE, and NOMINAL. It treats the earlier high-duty mode as scheduled
work within NOMINAL, pending team review. The draft does not establish approved
flight requirements or implemented behavior.
