# Internal Housekeeping Unit Interfaces

**Scope:** board allocation and provisional targets. The FreeRTOS prototype
uses 100 kHz I2C0 GP4/GP5; the CAN Feather EPS reader uses 100 kHz I2C1 GP2/GP3.
Use the [operator guide](../../../docs/user/README.md) for the appropriate application.

## Scope

Define the external interfaces for the internal housekeeping unit board and assign
ownership expectations for each link.

## Board-to-Board Interfaces

| Interface | Peer | Direction | Baseline Use | Status |
|---|---|---|---|---|
| I2C (`SCL`, `SDA`) | EPS | Bidirectional | Charger/housekeeping telemetry | In progress |
| SPI (`SCLK`, `MOSI`, `MISO`, `CS_N`) | Comms RP2040 | Bidirectional | Older stack allocation | Packet firmware not implemented |
| UART (`TX`, `RX`) | Ground/debug host | Bidirectional | FreeRTOS prototype logs and CLI | Implemented at 115200 8N1; Feather bench uses USB console |
| CAN (`CANH`, `CANL`) | Comms/payload nodes | Bidirectional | Intended production packet transport | Single-bus Feather bench demonstrated; A/B integration pending |

## Control and Fault Signals (Provisional)

| Signal | Direction | Purpose | Status |
|---|---|---|---|
| `COMMS_EN` | Out | Enable/disable comms board operation | Provisional |
| `COMMS_FAULT_N` | In | Comms fault indication to IHU | Provisional |
| `COMMS_IRQ` | In | Comms data-ready / packet-available signal to IHU (active-low, IHU ISR triggers SPI read) | Provisional |
| `EPS_ALERT_N` | In | EPS fault/alert line to IHU | Provisional |
| `PAYLOAD_EN` | Out | Payload power/operation gating; H1.50 | Proposed 3.3 V push-pull, default low; electrical validation pending |

### Payload enable electrical proposal — 2026-10-04

User selected 3.3 V push-pull, default low for PAYLOAD_EN. Keep the output low
during startup/reset and configure a low output value before enabling its GPIO.
Payload supplies a pulldown so missing drive removes permission. Normal CAN
stops hold permission until verified power-down acknowledgement; low is an
immediate hardware kill. This contract is not proof of the current IHU circuit.
See [receiver/mode requirements](../../payload_compute/design/bench_mode.md)
for proposed voltage/load limits and outstanding qualification.

## Timing and Throughput Targets (Provisional)

- I2C target: 400 kHz fast mode for housekeeping telemetry
- SPI target: 4 to 8 MHz initial operating range
- CAN: 500 kbit/s classic CAN exercised on the Feather harness; production A/B remains planned
- IHU-comms heartbeat target: 100 ms nominal interval

## Ownership Rules

- IHU is system command authority and state-machine owner
- Comms RP2040 owns RF framing/modulation and radio-local timing
- EPS telemetry source remains EPS-side hardware path, consumed by IHU

## Interface Closure Checklist

- Final connector pin map and signal integrity constraints
- Pull-up/pull-down strategy and voltage-domain verification
- CRC and retry policy per transport
- Timeout behavior and degraded-mode actions per link

## Related Documents

- IHU architecture: [`hardware/ihu/design/overview.md`](overview.md)
- IHU-comms details: [`system/interfaces/comms_to_ihu.md`](../../../system/interfaces/comms_to_ihu.md)
- Global bus strategy: [`system/interfaces/board_to_board.md`](../../../system/interfaces/board_to_board.md)
