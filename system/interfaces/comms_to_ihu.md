# IHU–communications interface

[System guide](../README.md) · [Bus architecture](board_to_board.md)

**Status: documented ownership and assigned signals; framing and timing are draft.**
The comms RP2040 owns local TX/RX and baseband handling. The IHU RP2040 owns
system command authority, routing, and integration.

| Stage | Transport | Use |
|---|---|---|
| Iteration 1 | SPI, IHU master / comms slave, bidirectional | Commands and telemetry/data |
| Iteration 2 | CAN A/B alongside SPI | Mode, heartbeat, fault/status, and queue state; SPI retains bulk/timing-sensitive data |
| Bring-up | UART debug | Logs and diagnostics |

## Signals

Use the [canonical pin map](cskb_pinmap.md) for all pin numbers, directions,
and pull resistors. Shared nets are:

- SPI: `SPI_COMMS_SCK`, `SPI_COMMS_MOSI`, `SPI_COMMS_MISO`, `SPI_COMMS_CS_N`.
- Data ready: `COMMS_IRQ`, driven by comms RP2040 GP3; active-low push-pull,
  normally high. IHU services the SPI slave FIFO through its interrupt handler.
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
