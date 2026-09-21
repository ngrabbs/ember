# Board-to-board architecture

[System guide](../README.md) · [Canonical pin map](cskb_pinmap.md)

**Status: staged interconnect plan; CAN settings below are provisional.**
IHU and comms each use an RP2040. EPS is currently charger/regulation hardware,
not a full digital node. RP2040 has no native CAN peripheral; the proposed CAN
implementation uses an external controller and transceivers.

## Bus roles

| Bus | Role | Initial connection |
|---|---|---|
| I2C | Low-rate housekeeping/configuration; avoid long, high-capacitance runs | IHU ↔ LTC4162 charger, with discrete alerts |
| SPI | Bulk or timing-sensitive data, telemetry buffers, and possible firmware services | IHU master ↔ comms slave |
| CAN A/B | Iteration 2 commands, heartbeat, mode, health, and fault/status messages | IHU ↔ comms, then payload nodes |
| UART | Debug and bring-up logs | Debug host ↔ board |

EPS may join CAN only after a digital controller is added. Refer to the pin map
for exact signals; both CAN buses are DNP in v0.1.

## Iteration gates

| Stage | Work | Exit criteria |
|---|---|---|
| 1: I2C + SPI | Read EPS telemetry; exchange IHU–comms packets | Reliable charger reads, no SPI framing loss, validated timeout/recovery |
| 2: CAN A/B | Add control/status traffic; retain SPI for bulk data | Clean multi-node arbitration; command/ack and heartbeat under injected faults; demonstrate failed-node containment and bus failover |

## Provisional CAN settings

- Classic CAN 2.0B; default target 500 kbps.
- SPI CAN controller (MCP2515 class is an example), plus 3.3 V transceivers.
- Each bus is linear with its own 120 Ω termination at both physical ends and
  a ground reference. The [pin map](cskb_pinmap.md) defines A/B allocations;
  it adds no switched supply.
- Controller count, selection, and failover policy remain open. Do not connect
  CAN A and CAN B together or assume that a failed node can always be isolated.

| Proposed ID range | Message group |
|---|---|
| `0x100–0x1FF` | IHU commands and mode requests |
| `0x200–0x2FF` | EPS status/alerts, if a digital node is added |
| `0x300–0x3FF` | Comms status and queue state |
| `0x400–0x4FF` | Payload status and control |
| `0x700–0x7FF` | Debug/development |

Next: [IHU–comms interface](comms_to_ihu.md), [data ownership](data_interfaces.md),
and [integration sequence](../integration/integration_plan.md).
