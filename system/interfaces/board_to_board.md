# Board-to-board architecture

[System guide](../README.md) · [Canonical pin map](cskb_pinmap.md)

**Status: staged interconnect plan; CAN settings below are provisional.**
IHU and comms each use an RP2040. EPS is currently charger/regulation hardware,
not a full digital node. RP2040 has no native CAN peripheral; the proposed CAN
implementation choice remains open (PIO CAN or external controller, with
appropriate transceivers). The internal controller names are IHU MCU and COMMS MCU.

## Bus roles

| Bus | Role | Initial connection |
|---|---|---|
| I2C | Current housekeeping | IHU ↔ EPS; separate bench jumper interface to COMMS at 0x42 for status/ping |
| SPI | Existing comms PCB allocation/older plan | Stack signals assigned; packet firmware not implemented |
| CAN A/B | Intended internal packet/control/status transport | IHU MCU ↔ COMMS MCU, then payload nodes |
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
- PIO CAN versus external controller selection remains open; MCP2515 is one
  existing candidate, not a selected implementation.
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
The [COMMS–Walter integration checklist](comms_walter.md) owns the current
controller packet service and migration milestones.
