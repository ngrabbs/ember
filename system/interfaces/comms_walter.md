# COMMS MCU and Walter transport

Status: agreed architecture and draft packet interface, 2026-10-02.
Firmware forwarding and board integration are not implemented yet.

The RP2040 on the IHU board is the **IHU MCU**. The RP2040 on the communications
board is the **COMMS MCU** (Communications Controller). Walter's ESP32 manages
its cellular modem. The IHU's spacecraft-facing communications endpoint remains
the COMMS MCU as the external radio transport changes from Walter LTE-M to UHF.

```text
IHU MCU <-- internal packet transport --> COMMS MCU <-- framed UART --> Walter
                                            |
                                            +-- UHF radio transport (future)
```

The existing internal link is an I2C housekeeping/ping interface over bench
jumpers. The intended internal packet transport is CAN. These are independent
of the COMMS–Walter UART and of the ground-facing LTE/UHF link.

## Selected COMMS module and proposed wiring

User selected the **Adafruit RP2040 CAN Bus Feather** on 2026-10-02. This changes
the COMMS board pin profile; the old Pico firmware pin assignments are not a
drop-in match. The existing I2C baseline below describes the previous firmware,
not approved wiring for the Feather.

Proposed power entry: stack regulated 5 V to the Feather's **USB** power pad
and stack GND to GND. This pad shares USB VBUS. Adafruit identifies direct pad
power as technically possible but does not recommend it because a connected
computer can be back-powered. Provide carrier power selection/isolation before
using stack power alongside USB debugging. Do not apply 5 V to BAT or 3V;
3V is the onboard regulator output. Direct 3.3 V injection bypasses that
regulator and is not the selected approach.

Walter takes stack 5 V separately through VIN (physical pin 28), with GND at
pin 27. Its 3V3 OUT pin is an output. Do not power Walter through its USB-C
connector and VIN simultaneously; vendor documentation says they are directly
connected. Check regulator capacity/transients for both modules; Walter is not
powered through the Feather's 3V output.

| Proposed signal | Feather | Walter |
| --- | --- | --- |
| COMMS → Walter data | TX / RP2040 GPIO0, UART0 TX | IO44/RX0, physical pin 2 |
| Walter → COMMS data | RX / RP2040 GPIO1, UART0 RX | IO43/TX0, physical pin 3 |
| Logic reference | GND | GND, physical pin 27 |

Use 3.3 V UART logic, initially 115200 8N1. This is the ESP32 application UART,
not the Sequans modem test-point UART; Walter firmware must implement the
packet service here while separately managing its modem. UART0 boot/console
output must be handled during framing startup and application logs directed to
USB. Optional COMMS-controlled Walter RESET (physical pin 1, active low) needs
a separately allocated GPIO and open-drain release behavior; it is not yet assigned.

The Feather's onboard CAN uses SPI GPIO14/15/8 plus GPIO16/17/18/19/22/23.
The old COMMS housekeeping GP14/15 therefore conflicts with CAN, and the old
Si5351 GP20/21 conflicts with the Feather's NeoPixel power/data. Port those
assignments deliberately before loading the comms firmware. Interim I2C can
use Feather SDA GPIO2 / SCL GPIO3 (i2c1), subject to reviewing the remaining
radio/control assignments and the IHU harness. CAN termination and the IHU-side
CAN controller/transceiver still need implementation/verification.

Sources: [Feather pinout](https://learn.adafruit.com/adafruit-rp2040-can-bus-feather/pinouts),
[power management](https://learn.adafruit.com/adafruit-rp2040-can-bus-feather/power-management),
[Walter datasheet](https://www.quickspot.io/datasheet/walter_datasheet.pdf).
This is a proposed carrier mapping, not a schematic edit or tested hookup.

## Observed firmware baseline

The tracked firmware establishes the present interface:

- IHU master: GP4 SDA / GP5 SCL; COMMS slave: GP14 SDA / GP15 SCL,
  seven-bit address `0x42`, common ground. COMMS uses i2c1; its separate
  i2c0 GP20/GP21 remains the Si5351A master bus.
- `firmware/shared/comms_hk_proto.h` defines the shared status register map.
  `firmware/ihu/src/drivers/comms_link.c` implements status reads and scratch
  echo ping; `firmware/comms/src/tasks/hk_slave_task.c` serves them.
- Only the scratch echo register is writable. There is no current I2C
  telemetry packet queue, uplink forwarding, or transmit-command mailbox.
- Firmware pin comments explicitly identify this as jumper wiring. The current
  communications PCB's declared stack data signals are SPI; CAN A/B are planned.
  This document does not turn the jumper link into a routed stack connection.

The user selected CAN as the eventual IHU–COMMS link. SPI is the existing
hardware allocation/older plan, not a required firmware milestone before CAN.
CAN implementation, fragmentation, and hardware selection remain open.
The existing housekeeping schema should retain its meanings across migration.

## Responsibility and packet flow

| Owner | Responsibility |
| --- | --- |
| IHU MCU | Produce system telemetry, validate/authorize spacecraft commands, execute or dispatch them, generate acceptance/results |
| COMMS MCU | Bounded TX/RX queues, transport selection, packet forwarding, link health, local radio control |
| Walter | Cellular registration/socket lifecycle, send/receive application datagrams, report transport outcomes |
| Ground | Decode/archive telemetry and return correlated application acknowledgments/commands |

Downlink: IHU packet → internal transport → COMMS TX queue → Walter UART →
LTE UDP → ground receiver/Yamcs adapter. Uplink: ground datagram → Walter →
COMMS RX queue → internal transport → IHU validation and command handling.
An IHU command response travels back through the same downlink path.
Walter and the COMMS MCU do not replace IHU command authority.

Carry the existing EMBER bench packet bytes unchanged, including their source,
boot ID, sequence, transaction identity, and CRC. Do not reassign the IHU packet
source to COMMS just because it forwarded the packet. COMMS-originated health
can use the existing comms endpoint assignment. The outer UART/CAN transport
envelope is separate from application command IDs and packet schema.

## Draft COMMS–Walter service contract

These are logical messages; numeric wire IDs/header layout are still to be
defined in a shared header and tested against literal vectors before flashing.

| Message | Direction | Meaning |
| --- | --- | --- |
| HELLO / LINK_STATUS | Bidirectional / Walter → COMMS | Protocol version, sender boot/session identity, link state, capacity/error counters; report resets and registration changes |
| SEND_PACKET | COMMS → Walter | Submit one complete EMBER packet with a COMMS-local request ID |
| TX_RESULT | Walter → COMMS | Correlated queue admission/rejection and modem submission outcome, with explicit reason |
| RX_PACKET | Walter → COMMS | One received application packet plus receive identity/metadata |
| RX_RESULT | COMMS → Walter | Confirm queue admission or report overflow/invalid packet; not IHU command acceptance |

Initial application packet bound: 240 bytes, matching bench v1. Use explicit
length, protocol version, session/request identity, and an outer CRC. Use COBS
with a zero delimiter for UART framing, with a separately calculated bound
for the outer header plus 240-byte packet and CRC. Existing USB framing's
240-byte decoded bound cannot be reused unchanged for this larger envelope.
Select UART pins, voltage compatibility, rate, flow control, and queue limits
after checking both boards' pin usage. No pin assignment or PCB net is made here.

Report separate states: queued locally, accepted by modem, rejected, or unknown
after timeout/reset. Only a correlated ground/application acknowledgment proves
ground reception. Never convert modem `OK` into an IHU acceptance/completion
report. On a reset, identify a new session and mark unresolved submissions
unknown; do not silently retransmit uncertain commands. Reject malformed,
oversized, unsupported-version, or full-queue submissions explicitly.

Choose one external transport explicitly for the first bench implementation.
Automatic LTE/UHF failover and dual delivery require a later duplicate/recovery
policy. UHF remains safe at boot while the Walter path is being exercised.

## Owned implementation checklist

- [x] Name the IHU MCU and COMMS MCU and define their authority boundaries.
- [x] Inspect existing I2C firmware and distinguish housekeeping from packet transport.
- [x] Record CAN as the intended internal transport and Walter/UHF as external transports.
- [x] Select COMMS module and propose UART/power mapping from vendor pinouts.
- [x] Detect Feather BOOTSEL, preserve/verify its full flash, and install a
      standalone USB/UART diagnostic image; [build and hardware results](../../firmware/comms_feather_bench/README.md).
      USB commands passed; two UART probes submitted, no peer acknowledgment yet.
- [x] Preserve and verify Walter's complete ESP32 flash and build the standalone
      UART responder with the modem held in reset; [procedure](../../firmware/walter_uart_bench/README.md).
- [x] Install/check Walter responder over USB: upload hashes verified; status,
      help, unknown/overlong rejection, and growing uptime passed, with modem held reset.
- [ ] Move USB to Feather and prove matching PING/PONG identifiers over the
      physical UART in both directions; neither device has confirmed a peer yet.
- [ ] Port the COMMS board profile to the CAN Feather; resolve CAN/LED conflicts
      with old I2C/Si5351 GPIOs and allocate the UHF controls.
- [ ] Inventory remaining COMMS and Walter pins; verify electrical compatibility,
      power budget, reset/enable wiring, and antenna clearance before PCB placement.
- [ ] Freeze UART wire envelope, versions, lengths, numeric IDs, statuses,
      session/request correlation, queue bounds, and framing vectors.
- [ ] Add a transport-independent COMMS packet service and Walter adapter.
- [ ] Add Walter application firmware with bounded modem lifecycle, separate
      COMMS UART, receive forwarding, and observable errors; preserve current
      passthrough source/build or recovery image before replacement.
- [ ] Bench-wire COMMS–Walter and prove a packet/return-packet loop without RF,
      including corruption, overflow, timeout, unplug, and either-controller reset.
- [ ] Add an IHU packet path: choose a separately versioned interim I2C mailbox
      or implement CAN first. Preserve the existing v1 housekeeping/ping contract.
- [ ] Define CAN controller/transceiver implementation, IDs, fragmentation,
      reassembly bounds, timeouts, arbitration priorities, and A/B policy.
- [ ] Demonstrate IHU → COMMS → Walter → ground telemetry with original packet
      identity, then ground → Walter → COMMS → IHU and a correlated result.
- [ ] Connect decoded telemetry/results to Yamcs and retain a recorded/replayed
      session identifying the actual hardware/transport and quality.
- [ ] Integrate Walter with the COMMS MCU PCB after pin/power/interface validation.
- [ ] Add the UHF adapter behind the same COMMS packet service; repeat the
      forwarding tests without changing IHU application packet meanings.

LTE attach/telemetry has been demonstrated, but repeatability is unresolved and
reliability work is shelved. Local UART/packet-service development can proceed
independently. The [LTE checklist](../../ground/lte/TODO.md) retains RF work;
this checklist owns the controller/transport integration.
