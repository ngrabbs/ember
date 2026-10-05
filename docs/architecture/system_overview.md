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
- **Command design intent:** RF uplink → comms → IHU validation → subsystem dispatch.
  Current Yamcs commanding reaches the simulator or dedicated USB bench Pico;
  the native EPS LTE input has no telecommand link. See the
  [operator guide](../user/yamcs.md).
- **Implemented telemetry:** FreeRTOS IHU EPS observations reach Yamcs through
  a Pi UART wrapper. The separate CAN Feather application generates native EPS
  packets, with recorded bounded LTE delivery evidence.
- **Buses:** I2C reads the EPS charger. The FreeRTOS IHU–comms jumper link
  provides status/ping; the standalone CAN Feather bench carries packets on one
  physical CAN harness. SPI is an older stack allocation. Production CAN A/B
  integration and failover remain open. See the
  [interconnect plan](../../system/interfaces/board_to_board.md).

For the implemented EPS/CAN/LTE bench path, worked examples, and definition ownership,
read [Telemetry: from a subsystem to the ground](telemetry_data_flow.md).

## Operating behavior

The [operations draft](operations/README.md) proposes BOOT, STARTUP,
COMMISSIONING, SAFE, and NOMINAL. It treats the earlier high-duty mode as scheduled
work within NOMINAL, pending team review. The draft does not establish approved
flight requirements or implemented behavior.
