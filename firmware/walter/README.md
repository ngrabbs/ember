# Walter LTE firmware

This directory builds the **ESP32-S3 app on the Walter module**. It accepts
requests from the [Walter MCU](../walter_mcu/README.md), controls the onboard
Sequans modem with AT commands, and sends native EMBER telemetry over LTE-M
as UDP. The Sequans modem runs its own firmware. The ESP32-S3 app in this
checkout is version [0.3.0](VERSION).

## Build and flash

Install PlatformIO Core 6.1.18 and run these commands from the repository root.
The `walter` environment in [platformio.ini](platformio.ini) sets the board,
framework and USB options. The build records the source commit and dirty state.

```sh
export EMBER_GIT_REVISION="$(git rev-parse HEAD)"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
  export EMBER_GIT_DIRTY=1
else
  export EMBER_GIT_DIRTY=0
fi

pio run -d firmware/walter -e walter
pio run -d firmware/walter -e walter -t upload --upload-port "${WALTER_USB_PORT:?set Walter USB port}"
pio device monitor --port "$WALTER_USB_PORT" --baud 115200
```

Set `WALTER_USB_PORT` to the Walter USB serial device before uploading.
The build produces `firmware/walter/.pio/build/walter/firmware.bin`.
Enter `version` over USB to verify the reported version, Git commit and
dirty flag. Use `status` to inspect the app and modem state, and `off` to
close the radio window.

## How LTE telemetry reaches Yamcs

```text
IHU → CAN → Walter MCU (RP2040) → UART → Walter (ESP32-S3)
    → Sequans modem → LTE-M eNodeB / EPC → ground Pi UDP listener
    → Yamcs ember / realtime / lte-tm-in
```

1. The IHU opens a radio window through the Walter MCU. Walter starts with
   the modem held in reset. On an open request it boots the modem, configures
   Band 13 and APN `srsapn`, registers, and opens a UDP socket. A window lasts
   up to 120 seconds. Closing it or reaching its deadline returns Walter to
   the off state.
2. The IHU sends a native packet such as `POWER_STATUS`, `HEARTBEAT` or
   `SYSTEM_STATUS`. The Walter MCU forwards the request over UART. Walter
   passes the native packet to the modem as one UDP payload, from port
   `51001` to the ground endpoint at `172.16.0.1:51000`.
3. The [ground Pi listener](../../ground/pi/lte_listener.py) checks the peer
   and packet, drops duplicates, and forwards the original bytes to
   `127.0.0.1:10018`. Find the received packet in the Yamcs archive under
   the `ember` instance and `realtime` processor on `lte-tm-in`.
   `MODEM_ACCEPTED` confirms that the modem accepted the send. The archive
   confirms ground delivery.

For a bench check, use the [LTE runbook](../../ground/lte/BRINGUP.md) to prepare
the lab cell and ground endpoint, and check the [Yamcs link](../../ground/yamcs/OPERATIONAL.md).
On the IHU USB console in the normal ground-test build, send `hello lte`,
`output lte_telem on` and `lte 120`. Use `lte status` until it reports
registered and READY (state 6) with at least 16 seconds left, then send `eps lte`.
Check the archive for `POWER_STATUS`, then close the window with `lte 0`
and turn off the output with `output lte_telem off`.

## Packet layouts

Bytes are shown in transmission order. The UDP payload is one complete native
EMBER packet. CAN and UART framing are described in the
[Walter MCU guide](../walter_mcu/README.md#packet-layouts).

```text
LTE datagram
[UDP header 8 B] [Native EMBER packet, variable]

Native EMBER packet (UDP payload)
[CCSDS primary header 6 B] [EMBER secondary header 24 B] [Telemetry payload N B] [CRC-16 2 B]
```

See the [IHU packet guide](../ihu/README.md) and
[ground dictionary](../../ground/ember/dictionary.json) for telemetry fields.

For earlier bench results and flash recovery notes, see the
[previous Walter guide](https://github.com/ngrabbs/ember/blob/a237f01e8fd64fa45ac621644caaa3f1656ca779/firmware/walter/README.md).
