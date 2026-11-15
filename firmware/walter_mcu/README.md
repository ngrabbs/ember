# Walter MCU firmware

This directory builds the **RP2040 app on the LTE board's Adafruit CAN Bus
Feather**. It bridges requests from the IHU on CAN to the
[Walter ESP32-S3 app](../walter/README.md) on UART. Walter handles LTE-M
registration and UDP transmission. The Walter MCU app in this checkout is
version [0.14.1](VERSION).

| Interface | Connection |
| --- | --- |
| CAN | MCP25625 at 500 kbit/s. Node 3 answers discovery on `0x703` after a request on `0x700`. Application requests use `0x720` and replies use `0x721`. |
| UART | 115200 baud, 8N1. Feather GP0 TX → Walter RX44, Feather GP1 RX ← Walter TX43, with shared ground. |
| USB | Local console for version, status and bench checks. |

## Build and flash

Install CMake, the Pico SDK, an ARM embedded toolchain and `picotool`.
Set `PICO_SDK_PATH` to your Pico SDK checkout and run from the repository root.
CMake selects the shared `ember_can_feather` board profile without a role flag.
The identity
helper supplies the source commit and dirty flag.

```sh
cmake -S firmware/walter_mcu -B build/walter_mcu \
  -DPICO_SDK_PATH="${PICO_SDK_PATH:?set Pico SDK path}" \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build build/walter_mcu --target walter_mcu -j4
```

Put the LTE Feather into BOOTSEL mode. Use `picotool info -a` to identify its
USB serial number, bus and address. Confirm the serial number belongs to the
LTE Feather, then set `LTE_USB_BUS` and `LTE_USB_ADDRESS` before
uploading. The build produces `build/walter_mcu/walter_mcu.uf2` and
`build/walter_mcu/walter_mcu.elf`.

```sh
picotool info -a
picotool load -v -x build/walter_mcu/walter_mcu.uf2 \
  --bus "${LTE_USB_BUS:?set LTE Feather USB bus}" \
  --address "${LTE_USB_ADDRESS:?set LTE Feather USB address}"
```

Enter `version` on the Feather's USB console to verify the reported version,
Git commit and dirty flag. Use `status` to inspect the bridge and `hello`
to check the UART peer.

## LTE requests

The IHU opens the window, checks status and submits native packets over CAN.
The Feather reassembles CAN fragments, translates the request to the Walter
UART service, then returns the correlated reply to the IHU. The Feather
starts no radio window on its own. See the
[Walter guide](../walter/README.md#how-lte-telemetry-reaches-yamcs) for the
ground path and end-to-end check.

| Service | CAN request / reply | Walter UART request / reply |
| --- | --- | --- |
| Open or close radio window | `0x74 / 0x75` | `0x10 / 0x11` |
| Send native telemetry | `0x76 / 0x77` | `0x12 / 0x13` |
| Radio status | `0x78 / 0x79` | `0x14 / 0x15` |
| Radio diagnostics | `0x7A / 0x7B` | `0x16 / 0x17` |
| Walter ESP32-S3 app identity | `0x7C / 0x7D` | `0x18 / 0x19` |

## Packet layouts

Bytes are shown in transmission order. CAN carries slices of a COBS-framed
envelope. UART carries the complete COBS frame in one byte stream. The bridge
translates the service envelope and preserves the native telemetry bytes on a
send request.

```text
CAN frame data
[Version/flags 1 B] [Token 2 B] [Fragment index 1 B] [COBS frame slice 1–4 B]

UART frame / reassembled CAN fragments
[COBS-encoded envelope, variable] [00 delimiter 1 B]

Decoded envelope
[EU magic 2 B] [Version 1 B] [Type 1 B] [Sender boot 4 B] [Origin boot 4 B]
[Request ID 4 B] [Payload length 2 B] [Payload 0–240 B] [CRC-16 2 B]

Send request payload (native EMBER packet)
[CCSDS primary header 6 B] [EMBER secondary header 24 B] [Telemetry payload N B] [CRC-16 2 B]
```

Envelope integers are big-endian. The envelope CRC covers its decoded header
and payload. See the [shared transport guide](../comms_transport/README.md)
for the framing implementation.
