# Communications to Internal Housekeeping Unit Interface

## Purpose

Define the interface between communications hardware and internal housekeeping unit
logic.

## Controller Ownership

- Communications board hosts its own RP2040 for local TX/RX control and
  baseband handling.
- Internal Housekeeping Unit hosts a separate RP2040 for system-level command authority,
  routing, and integration logic.
- The two controllers communicate bidirectionally over the interfaces defined
  below.

## Baseline Interface (Iteration 1)

- Primary physical link: SPI (IHU master, comms slave)
- Data direction: bidirectional
- Nominal use: command exchange + telemetry/data transfer
- Debug link: UART during bring-up and integration

## Expanded Interface (Iteration 2)

- Add CAN control-plane messaging between IHU and comms
- Keep SPI for bulk or timing-sensitive transfers
- CAN carries mode changes, heartbeat, fault/status, and queue state

## Provisional Signal Set

- SPI (IHU master, comms slave): `SPI_COMMS_SCK` (CSKB H1.21),
  `SPI_COMMS_MOSI` (H1.23), `SPI_COMMS_MISO` (H1.22),
  `SPI_COMMS_CS_N` (H1.24)
- Data-ready interrupt: `COMMS_IRQ` (CSKB H1.16) — driven by comms
  RP2040 GP3 (push-pull, active-low, normally high); triggers IHU ISR
  to service the SPI slave FIFO. Pull-up lives on IHU side (R11, 10k).
- CAN (Iteration 2): `CANH`, `CANL`, `GND`
- Optional control: `COMMS_EN`, `COMMS_FAULT_N`

## Provisional Timing and Throughput Targets

- SPI clock target: 4 MHz to 8 MHz initial range
- CAN rate target: 500 kbps (classic CAN)
- IHU-comms heartbeat period: 100 ms nominal

## Fault Behavior

- Missing heartbeat timeout triggers comms link degraded state
- IHU retries command transaction with bounded retry count
- On repeated failure, IHU enters reduced service mode and logs fault

## Open Items

- Final SPI framing and CRC policy
- CAN message ID allocation for comms state and command ack
- Ownership of mode transitions when links disagree
