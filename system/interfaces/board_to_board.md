# Board-to-board architecture

[System guide](../README.md) · [Canonical pin map](cskb_pinmap.md)

**Status: single-bus CAN Feather bench demonstrated; flight interconnect and A/B remain planned.**
IHU and COMMS now each use an Adafruit RP2040 CAN Bus Feather for this bench,
with onboard MCP25625 controllers/transceivers. A 500 kbit/s CAN harness has
carried an IHU-generated heartbeat through COMMS to Walter and back.
[Implementation/evidence](../../firmware/can_feather_bench/README.md).
EPS is currently charger/regulation hardware, not a full CAN node. RP2040 has
no native CAN peripheral; the selected bench boards supply external controllers.

## Bus roles

| Bus | Role | Initial connection |
|---|---|---|
| I2C | Legacy housekeeping firmware | IHU ↔ EPS; separate bench jumper interface to COMMS at 0x42 for status/ping |
| SPI | Existing comms PCB allocation/older plan | Stack signals assigned; packet firmware not implemented |
| CAN | Implemented standalone bench packet transport | CAN Feather IHU MCU ↔ CAN Feather COMMS MCU; one physical harness |
| CAN A/B | Intended redundant internal transport | Additional hardware/failover qualification remains open |
| UART | Debug and bring-up logs | Debug host ↔ board |

EPS may join CAN only after a digital controller is added. Refer to the pin map
for exact signals; both CAN buses are DNP in v0.1.

## Iteration gates

| Stage | Work | Exit criteria |
|---|---|---|
| Current I2C bench | Read EPS and COMMS housekeeping; preserve ping/status | Reliable reads and bounded timeout/recovery; no packet-forwarding claim |
| COMMS–Walter bench | Add framed UART and transport-independent packet service | Packet/return-packet loop, bounded queues, reset/error recovery |
| CAN A/B | Replace interim IHU–COMMS link with packet/control/status transport | Bounded fragmentation/reassembly, command/ack, arbitration and injected-fault recovery; separately qualify bus failover |

## Provisional CAN settings

- Classic CAN 2.0B; default target 500 kbps.
- MCP25625 controllers/transceivers are selected and exercised on both CAN
  Feathers for the single-bus bench. Production A/B controller allocation remains open.
- Each bus is linear with its own 120 Ω termination at both physical ends and
  a ground reference. The [pin map](cskb_pinmap.md) defines A/B allocations;
  it adds no switched supply.
- Redundant controller count and failover policy remain open. Do not connect
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
The [COMMS–Walter integration checklist](comms_walter.md) owns the current
controller packet service and migration milestones.
