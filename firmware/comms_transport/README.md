# Shared communications transport

`comms_transport` contains C code and protocol definitions that EMBER firmware
uses to exchange packets between boards. The applications include the headers
or compile the driver they need as part of their own builds.

| Area | Shared code |
|---|---|
| CAN | [MCP25625 driver](mcp25625.h), [packet fragmentation and reassembly](can_fragment.h), and [device discovery](device_registry.h) |
| UART | [COBS framing and CRC](uart_link.h) for the Walter serial link. CAN packets reuse the same request and reply envelope. |
| Messages | Definitions for [LTE](lte_link.h), [UHF](uhf_link.h), [payload commands](payload_protocol.h), and [firmware identity](firmware_info.h). The applications decide when to send them and how to handle replies. |

| Firmware | How it uses the library |
|---|---|
| [IHU](../ihu/README.md) | Drives CAN and exchanges discovery, telemetry, and command messages with the transceiver, Walter MCU, and payload. |
| [Transceiver](../transceiver/README.md) | Uses CAN discovery, packet reassembly, and UHF message definitions to exchange packets with the IHU. |
| [Walter MCU](../walter_mcu/README.md) | Drives CAN on the LTE Feather and bridges requests to Walter over framed UART. |
| [Walter](../walter/README.md) | Decodes the UART frames and reports modem and LTE results to the Feather. |
| [Payload](../payload/README.md) | Implements the compatible CAN protocol in [Python](../payload/protocol.py). The shared C definitions are used on the IHU side. |

For the original UART wire format, test commands, and recorded results, see the
[COMMS–Walter UART echo bench note](uart_echo_bench.md).
