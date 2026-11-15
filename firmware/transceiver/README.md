# Transceiver firmware

The transceiver moves EMBER packets between the IHU on CAN A and the UHF radio.
Version **0.39.0** runs on the original Raspberry Pi Pico.

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds) ·
[Radio guide](../../docs/comms/README.md)

The current [verified UHF startup UF2](releases/0.39.0/transceiver-0.39.0-uhf.uf2) supports [configuration readback](../../docs/comms/radio_config.md). The
previous 0.38.0 bench image was built from
[`819470b`](https://github.com/ngrabbs/ember/commit/819470bbf877fa66f980bf9d0d138c081905af6c).
To reproduce that image, run the build commands from a detached worktree
and use the historical flag `-DTRANSCEIVER_BOOT_DEMO=ON`.

```sh
git worktree add --detach ../ember-transceiver-038 819470bbf877fa66f980bf9d0d138c081905af6c
cd ../ember-transceiver-038
```

## Build and flash

Install the Pico SDK, Arm GNU toolchain, CMake, Python 3, and
[picotool](https://github.com/raspberrypi/picotool). Set `PICO_SDK_PATH` to
your SDK checkout. Run from the repository root.

```sh
radio_build=build/transceiver-uhf-startup
cmake -S firmware/transceiver -B "$radio_build" -DPICO_BOARD=pico \
  -DPICO_SDK_PATH="${PICO_SDK_PATH:?set Pico SDK path}" \
  -DTRANSCEIVER_UHF_STARTUP=ON \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build "$radio_build" --target transceiver -j4
```

| CMake option | What it controls |
|---|---|
| `PICO_BOARD=pico` | Selects the original RP2040 Raspberry Pi Pico required by this target. |
| `PICO_SDK_PATH` | Points CMake to the Pico SDK. |
| `TRANSCEIVER_UHF_STARTUP=ON` | Enables IHU-coordinated conducted startup and the LINK_ACTIVE bench link. Pair it with the [IHU UHF startup build](../ihu/README.md#build-and-flash). |
| `TRANSCEIVER_UHF_STARTUP=OFF` | Default. Keeps RF muted at idle and sends IHU-requested telemetry in bounded bursts. Use a separate build directory such as `build/transceiver`. |
| `EMBER_GIT_REVISION`, `EMBER_GIT_DIRTY` | Embed the full source SHA and dirty flag. The helper sets both from Git. For a source export, pass both as `-D` options using the original SHA and dirty flag (0 or 1). |

The artifact is `transceiver.uf2` in the chosen build directory. With the
board rails powered, put the transceiver Pico into BOOTSEL mode. Run
`picotool info -a` to identify its USB bus and address. Set
`RADIO_USB_BUS` and `RADIO_USB_ADDRESS` to those values and
`RADIO_BACKUP` to a new backup path ending in `.uf2`.

```sh
picotool save -a -v "${RADIO_BACKUP:?set a new backup UF2 path}" \
  --bus "${RADIO_USB_BUS:?set transceiver USB bus}" \
  --address "${RADIO_USB_ADDRESS:?set transceiver USB address}" &&
picotool load -v -x "${radio_build:?set build directory}/transceiver.uf2" \
  --bus "$RADIO_USB_BUS" --address "$RADIO_USB_ADDRESS"
```

The first command saves and verifies the existing flash. The second writes
and verifies the new UF2, then reboots into it. Check the reported version and
commit using the console instructions below.

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

In the **UHF startup profile profile**, use `startup` or `radio` on the **IHU**
console to inspect the link. The transceiver USB console prints startup and
receive diagnostics. Input on that port can send the radio into SAFE, so read
the log without typing. Check the build identity from the startup line or
from the transceiver identity in FULL telemetry.

## How UHF telemetry reaches Yamcs

```text
IHU → CAN A → transceiver Pico → UHF DBPSK v3 → LibreSDR on ground Pi
    → DBPSK decoder → UDP 127.0.0.1:10019 → Yamcs ember / realtime / uhf-tm-in
```

1. Start the [DBPSK receiver](../../ground/bpsk/README.md#live-uhf-receiver)
   with forwarding enabled and wait for `BPSK_RX_READY`.
2. In the default build, request telemetry from the IHU console as described
   above. In the UHF startup profile, the IHU controls telemetry in LINK_ACTIVE.
   See the [IHU Yamcs commands](../ihu/README.md#ground-station-commands-in-yamcs)
   to enable the schedule and select BASIC or FULL.
3. The [ground decoder](../../ground/bpsk/live.py) validates the RF frame and
   native packet, then forwards the original native bytes. Find a fresh packet
   on `uhf-tm-in` in the [Yamcs archive](../../ground/yamcs/OPERATIONAL.md)
   and compare it with the receiver's `packets.jsonl`. A transceiver TX result
   reports local completion. The archive confirms ground delivery.

## Packet layouts

Fields are shown in transmission order. All widths are in bytes.

```text
CAN A frame data
[Version/flags 1] [Token 2] [Fragment index 1] [COBS frame slice 1–4]

UHF DBPSK v3 frame
[Preamble 32] [Sync 4] [Version 1] [Sequence 4] [Length 2] [Native packet N] [CRC-32 4] [Guard 16]

Native EMBER packet (also the UDP payload to Yamcs)
[CCSDS primary header 6] [EMBER secondary header 24] [Telemetry payload N] [CRC-16 2]
```

CAN carries slices of the service envelope described in the
[shared transport guide](../comms_transport/README.md). On UHF, Length counts
the native packet bytes. The outer CRC-32 covers Version through the native
packet. The transmitted frame and conducted CAN bridge limit the native
packet to 128 bytes. See the [radio guide](../../docs/comms/README.md) for
modulation, byte order, and receiver settings.

| Path | Packets and handling |
|---|---|
| Default CAN A | IHU requests on `0x710`, transceiver replies on `0x711`. `CF_UHF_SEND` carries a native packet, and `CF_UHF_FIRMWARE` requests a fresh identity. Admission, rejection, and transmit results are correlated to the request. [CAN framing](../comms_transport/can_fragment.h) · [UHF request and result definitions](../comms_transport/uhf_link.h) |
| Default UHF downlink | Relays validated IHU telemetry. `COMMS_FIRMWARE` (message ID 50) carries major, minor, patch, dirty flag, and the 20-byte source SHA. The first admitted telemetry request after boot triggers the identity before the telemetry burst. The firmware also accepts explicit identity requests. Local TX completion reports the radio result. Confirm ground delivery separately in the receiver or Yamcs. [Packet dictionary](../../ground/ember/dictionary.json) |
| Default UHF uplink diagnostic | The bounded PING path passes validated requests to the IHU on `0x730` and reads the correlated reply on `0x731`. The IHU owns command execution. [PING envelope](../comms_transport/uplink_ping.h) |
| Conducted LINK_ACTIVE | Validates the RF and CAN envelopes and passes native packets between radio and IHU. The IHU handles application commands and decides what to include in FULL. Transceiver CAN identity replies carry version, SHA, boot ID, and uptime. [UHF startup CAN definitions](../comms_transport/uhf_startup_link.h) · [CAN identity format](../comms_transport/firmware_info.h) |

## Startup and state transitions

Both builds start with TX and RX inactive. Firmware initializes the GPIO,
SPI, I²C, and ADC, checks that the two CAN controllers respond independently,
and runs internal loopback on each. It opens CAN A for service if the checks
pass. CAN B stays in standby. The console prints the build identity and boot ID.

| Profile | Normal progression | Fault behavior |
|---|---|---|
| Default | **Muted idle → bounded transmit → muted idle.** CAN A polls for requests at idle. The radio quiesces CAN for the RF burst and reopens it afterward. | A startup, CAN, or clock shutdown failure can latch the affected service unavailable until reboot. Inspect `[startup]`, `[selftest]`, `[can]`, and `Si5351_disable` in the USB log. |
| UHF startup profile | **Wait for IHU → startup CW → RX-only → LINK_ACTIVE.** The IHU's CAN handshake gates the one-shot startup beacon and then enables packet forwarding. Receive windows continue between admitted transmissions. | Stop, missing IHU keepalive while linked, CAN or radio failure, or a console byte leads to SAFE. The startup profile stops ADC capture and attempts to mute the RF clocks. Inspect `[uhf_startup] SAFE` and `clock_shutdown_verified`. Reset both boards before a new run. |

See [default startup and service loop](main.c),
[default RF service](rf_service.h), and [UHF startup profile startup and loop](uhf_startup.h).
