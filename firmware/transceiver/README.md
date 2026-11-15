# Transceiver firmware

The transceiver moves EMBER packets between the IHU on CAN A and the UHF radio.
Version **0.38.0** runs on the original Raspberry Pi Pico.

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds) ·
[Radio guide](../../docs/comms/README.md)

| Build profile | Behavior |
|---|---|
| Default | Keeps RF muted at idle. Accepts IHU telemetry on CAN A and sends it in bounded UHF bursts. The USB console provides diagnostics. |
| Conducted bench demo | Built with `TRANSCEIVER_BOOT_DEMO=ON`. The IHU coordinates startup and runs the LINK_ACTIVE bench link. The transceiver samples RX continuously and answers CAN identity requests for FULL telemetry. This is the profile verified on the bench. |

## Build

From the repository root, with the Pico SDK, ARM GCC, CMake, and Python 3 installed:

```sh
cmake -S firmware/transceiver -B build/transceiver -DPICO_BOARD=pico \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build build/transceiver --target transceiver -j4
# build/transceiver/transceiver.uf2
```

For the conducted bench demo, use a separate build directory and add
`-DTRANSCEIVER_BOOT_DEMO=ON`. The option defaults to OFF. For an exported source
tree, supply `-DEMBER_GIT_REVISION=<full SHA>` and `-DEMBER_GIT_DIRTY=0|1`
from the original checkout instead of running the identity helper in the export.

Back up and verify the existing Pico image before flashing. Power the board
rails when operating an installed Pico over USB.
[Exact source of the verified bench build](https://github.com/ngrabbs/ember/commit/819470bbf877fa66f980bf9d0d138c081905af6c)

## Commands

The default transceiver console takes one case-sensitive byte over USB. Send
the byte without Enter. Commands that open a diagnostic window can interrupt
normal CAN service. Use conducted RF for RF diagnostics.

| Task | Command | Expected result |
|---|---|---|
| Check the installed build | `v` or `s` | Version, full Git SHA, dirty flag, boot ID, and clock status |
| Inspect CAN A | `l` or `n` | Bounded listen-only or normal-mode receive window. Normal mode acknowledges valid frames. |
| Check a CAN peer | `h` | Bounded normal-mode window that answers one HELLO |
| Inspect RX samples | `r` or `e` | Bounded ADC capture with the receiver clock enabled or with it off, respectively |
| Decode a captured packet | `R` | Captures and decodes a burst. A valid PING can be forwarded to the IHU. This command does not transmit the held response. |
| Exercise the bounded PING path | `A` | Opens the automatic receive and reply window. The arm and result must pass the firmware's checks before a response can transmit. |
| Check the clock with RF muted | `c` | Bounded CLK0 diagnostic with TX and RX inactive |

For normal telemetry in the **default profile**, use the IHU console after CAN
and HELLO are healthy. Enable `output uhf_telem on`, then use
`uhf heartbeat`, `uhf run SECONDS PERIOD`, or `uhf transceiver firmware`.
The transceiver accepts requests while idle. Check the radio guide for receiver
setup and confirm a fresh packet at the ground station.

In the **conducted demo profile**, use `startup` or `radio` on the **IHU**
console to inspect the link. The transceiver USB console prints startup and
receive diagnostics. Input on that port can send the demo into SAFE, so read
the log without typing. Check the build identity from the startup line or
from the transceiver identity in FULL telemetry.

## Packets

The on-air frame wraps an EMBER packet. Fields are in transmit order and widths
are in bytes.

```text
[Preamble 32] [Sync 4] [V3 1] [Seq 4] [Len 2] [EMBER packet N] [CRC-32 4] [Guard 16]
```

`Len` counts the inner packet, which has its own CRC-16. The outer CRC-32 covers
version through the inner packet. See the [radio guide](../../docs/comms/README.md)
for modulation, byte order, and receiver settings. The transceiver's transmitted
frame and the conducted CAN bridge both limit the inner packet to 128 bytes.

| Path | Packets and handling |
|---|---|
| Default CAN A | IHU requests on `0x710`, transceiver replies on `0x711`. `CF_UHF_SEND` carries a native packet, and `CF_UHF_FIRMWARE` requests a fresh identity. Admission, rejection, and transmit results are correlated to the request. [CAN framing](../comms_transport/can_fragment.h) · [UHF request and result definitions](../comms_transport/uhf_link.h) |
| Default UHF downlink | Relays validated IHU telemetry. `COMMS_FIRMWARE` (message ID 50) carries major, minor, patch, dirty flag, and the 20-byte source SHA. The first admitted telemetry request after boot triggers the identity before the telemetry burst. The firmware also accepts explicit identity requests. Local TX completion reports the radio result. Confirm ground delivery separately in the receiver or Yamcs. [Packet dictionary](../../ground/ember/dictionary.json) |
| Default UHF uplink diagnostic | The bounded PING path passes validated requests to the IHU on `0x730` and reads the correlated reply on `0x731`. The IHU owns command execution. [PING envelope](../comms_transport/uplink_ping.h) |
| Conducted LINK_ACTIVE | Validates the RF and CAN envelopes and passes native packets between radio and IHU. The IHU handles application commands and decides what to include in FULL. Transceiver CAN identity replies carry version, SHA, boot ID, and uptime. [Demo CAN definitions](../comms_transport/boot_demo_link.h) · [CAN identity format](../comms_transport/firmware_info.h) |

## Startup and state transitions

Both builds start with TX and RX inactive. Firmware initializes the GPIO,
SPI, I²C, and ADC, checks that the two CAN controllers respond independently,
and runs internal loopback on each. It opens CAN A for service if the checks
pass. CAN B stays in standby. The console prints the build identity and boot ID.

| Profile | Normal progression | Fault behavior |
|---|---|---|
| Default | **Muted idle → bounded transmit → muted idle.** CAN A polls for requests at idle. The radio quiesces CAN for the RF burst and reopens it afterward. | A startup, CAN, or clock shutdown failure can latch the affected service unavailable until reboot. Inspect `[startup]`, `[selftest]`, `[can]`, and `Si5351_disable` in the USB log. |
| Conducted demo | **Wait for IHU → startup CW → RX-only → LINK_ACTIVE.** The IHU's CAN handshake gates the one-shot startup beacon and then enables packet forwarding. Receive windows continue between admitted transmissions. | Stop, missing IHU keepalive while linked, CAN or radio failure, or a console byte leads to SAFE. The demo stops ADC capture and attempts to mute the RF clocks. Inspect `[boot_demo] SAFE` and `clock_shutdown_verified`. The demo calls for both boards to be reset before a new run. |

See [default startup and service loop](main.c),
[default RF service](rf_service.h), and [conducted demo startup and loop](boot_demo.h).
