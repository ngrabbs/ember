# IHU–communications interface

[System guide](../README.md) · [Bus architecture](board_to_board.md)

**Status: CAN Feather bench packet transport demonstrated; full application integration pending.**
The communications-board RP2040 is the **COMMS MCU**; the IHU-board RP2040 is
the **IHU MCU**. COMMS owns link handling; IHU owns system command authority.
The [COMMS–Walter plan](comms_walter.md) owns the transport integration checklist.

| Stage | Transport | Use |
|---|---|---|
| Legacy bench firmware | I2C, IHU master / COMMS slave at 0x42, jumper wiring | Housekeeping and scratch-echo ping only |
| New CAN Feather bench | Single classic CAN harness, 500 kbit/s | Peer ping and IHU heartbeat forwarding through COMMS → Walter echo; [evidence](../../firmware/can_feather_bench/README.md) |
| Existing PCB allocation | SPI stack signals | Historical data-path allocation; packet firmware not implemented |
| Intended internal link | CAN A/B | Commands, telemetry packets, heartbeat, faults and queue state; replaces the interim link |
| Bring-up | UART debug | Logs and diagnostics |

## Signals

Use the [canonical pin map](cskb_pinmap.md) for all pin numbers, directions,
and pull resistors. Shared nets are:

- SPI: `SPI_COMMS_SCK`, `SPI_COMMS_MOSI`, `SPI_COMMS_MISO`, `SPI_COMMS_CS_N`.
- Data ready: `COMMS_IRQ`, allocated to comms RP2040 GP3; active-low push-pull,
  normally high. FIFO service/interrupt firmware remains unimplemented.
- Control/status: `COMMS_EN`, `COMMS_FAULT_N`.
- Iteration 2: CAN A (`CAN_H`, `CAN_L`) and CAN B (`CAN_B_H`, `CAN_B_L`), with GND.

## Provisional targets and recovery

| Parameter | Target |
|---|---|
| SPI clock | Initially 4–8 MHz |
| CAN rate | 500 kbps, classic CAN |
| IHU–comms heartbeat | 100 ms nominal |

A missed-heartbeat timeout marks the link degraded. IHU retries with a bounded
count; repeated failure enters reduced service and logs the fault.

**Open:** SPI framing/CRC, CAN IDs and acknowledgments, retry/timeout limits,
A/B failover, and mode-transition authority when links disagree. Redundancy is
allocated, not yet established by this document.

SPI timing/framing above belongs to the older hardware plan, not a required
implementation step. The 500 kbit/s CAN rate is exercised on the new Feather
bench; periodic heartbeat and flight recovery targets remain provisional. The
old jumper wiring was IHU GP4/GP5 ↔ COMMS GP14/GP15 plus GND. New CAN uses the
two Feathers' H/L/GND terminals, with user-confirmed termination and 60 ohms
measured across the bus. The bench proves neither routed stack nets nor CAN A/B
redundancy. Standalone packet forwarding works; integration into the complete
IHU/EPS/UHF firmware remains open.
