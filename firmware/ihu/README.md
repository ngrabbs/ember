# IHU firmware

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds)

The Internal Housekeeping Unit runs on the EMBER RP2040 CAN Feather. It
reads EPS and GPS, manages spacecraft modes, and exchanges commands and
telemetry with the transceiver, payload, and Walter MCU. The verified IHU
0.28.0 bench image uses the UHF startup profile from
[`4e55d05`](https://github.com/ngrabbs/ember/commit/4e55d0563c3e681e4443f83aa58db6162eb14d17).

## Build and flash

Build from the repository root with CMake, Python 3, the Arm GNU toolchain,
and Pico SDK 2.1.1. The first configure fetches the pinned FreeRTOS 11.2.0
kernel unless its source is already available.

```sh
ihu_build=build/ihu-uhf-startup
cmake -S firmware/ihu -B "$ihu_build" \
  -DPICO_SDK_PATH="$PICO_SDK_PATH" -DIHU_UHF_STARTUP=ON \
  $(python3 firmware/transceiver/source_identity.py --cmake-args)
cmake --build "$ihu_build" --target ihu -j4
```

The command above selects the bench UHF profile. For regular GROUND_TEST,
set `ihu_build=build/ihu` and omit `-DIHU_UHF_STARTUP=ON`. All three profile flags
default to `OFF`. Use a separate build directory for each profile.

| Flag | When enabled |
|---|---|
| `IHU_UHF_STARTUP` | Runs the conducted startup sequence in GROUND_TEST. Requires the matching [transceiver UHF startup build](../transceiver/README.md). |
| `IHU_BOOT_RX_ONLY` | With the UHF startup profile enabled, stays in RX_ONLY after the startup beacon instead of entering LINK_ACTIVE. |
| `IHU_FLIGHT_CONFIGURATION` | Selects FLIGHT with inactive flight routines. CMake rejects combining this with the UHF startup profile. |

The artifact is `ihu.uf2` in the chosen build directory. Put the IHU in
BOOTSEL mode and check its current USB bus and address with `picotool info -a`.
Set `IHU_USB_BUS` and `IHU_USB_ADDRESS` to those values before running the
command below. Use the artifact from the profile you intend to install.

```sh
picotool load -v -x "$ihu_build/ihu.uf2" --bus "${IHU_USB_BUS:?set IHU USB bus}" --address "${IHU_USB_ADDRESS:?set IHU USB address}"
```

`-v` verifies flash and `-x` returns to application mode. Open the IHU USB
console at 115200 baud with exclusive access and send `version` and `status`
to check the reported role, version, commit, and mode.

## Startup and modes

Configuration is selected at build time. The normal GROUND_TEST profile
initializes the CAN and sensor workers, enters BOOT, checks the local CAN
controller, and settles in SAFE with all output flags off. The console can
select STARTUP, COMMISSIONING, SAFE, or NOMINAL while the application is
idle. Reset re-enters BOOT. FLIGHT enters SAFE with
`HISTORY_UNAVAILABLE` if the local CAN check succeeds and exposes the
inactive flight profile.

The UHF startup profile drives the transitions automatically. Its release
switches and antenna deployment are simulated. The CW beacon is a real
transceiver operation on the conducted bench.

| Mode | UHF startup profile |
|---|---|
| BOOT → SAFE | Start local services, check CAN and EPS, and wait for the transceiver to report ready. |
| STARTUP | Start the simulated antenna timer and radio silence timer when the transceiver is ready. The timers are 10 s and 15 s, respectively. |
| COMMISSIONING | Request one CW startup beacon and wait for transceiver receive readiness. |
| NOMINAL | Enter RX_ONLY with `IHU_BOOT_RX_ONLY=ON`, otherwise confirm LINK_ACTIVE with the transceiver. Heartbeat and scheduled telemetry start disabled. |
| SAFE | A startup fault, link failure, or operator stop shuts down the UHF link and clears the outputs. Restart both boards to run startup again. |

The LINK_ACTIVE schedule defaults to BASIC with 540 s listening and 60 s
available to send telemetry. BASIC sends IHU status, valid EPS data, and
schedule status. FULL adds device and system status, heartbeat, available
payload status and GPS, and firmware identities when peers respond.
### Ground station commands in Yamcs

On the ground station, open Yamcs, select the `ember` instance and its
`realtime` processor, then choose **Commanding → Send a Command**. The ground
radio sends these commands over UHF to the transceiver, which passes them to
the IHU over CAN A while the radio is in LINK_ACTIVE. Use the USB console
section below for commands typed directly into the IHU.

| Command | Arguments and effect |
|---|---|
| `SET_HEARTBEAT` | `enabled=0` or `enabled=1` stops or starts the 10 s heartbeat. |
| `SET_UHF_TELEMETRY` | `enabled=0` or `enabled=1` stops or starts the schedule. |
| `SET_UHF_TELEMETRY_SCHEDULE` | Listening 1–3600 s and telemetry 5–3600 s. |
| `SET_UHF_TELEMETRY_SET` | BASIC or FULL. |
| `REQUEST_STATUS` | Requests IHU status and queues a schedule status report. |

## USB console

Send one case-sensitive command per line. `help` lists commands for the
installed profile. The regular GROUND_TEST commands are grouped below.

| Task | Commands |
|---|---|
| Inspect build, health, and modes | `version`, `status`, `rtos`, `mode`, `faults`, `outputs` |
| Set simulated mode or output permission | `mode safe\|startup\|commissioning\|nominal`, `output NAME on\|off` |
| Check local CAN and peers | `selftest`, `normal`, `devices`, `devices scan`, `hello transceiver\|lte\|payload`, `ping N` |
| Read sensors | `eps json`, `gps`. `eps adc on\|off` changes charger ADC configuration. |
| Request payload results | After `hello payload`, use `payload ident`, `payload status`, `payload heartbeat`, or `payload fire-check`. |
| Send UHF telemetry | `uhf heartbeat`, `uhf system`, `uhf eps`, `uhf devices`, `uhf transceiver firmware`, `uhf lte firmware`, `uhf modem firmware`, `uhf run SECONDS PERIOD`, `uhf stop`. Select the transceiver, establish HELLO, and enable `uhf_telem`. Runs accept 1–120 s duration and 5–60 s period. LTE identity packets require a cached identity. |
| Use the LTE bench route | After `hello lte`, use `lte firmware`, `lte modem firmware`, `lte status`, or `lte diagnostics`. `lte SECONDS` requests a window up to 120 s, with zero requesting close. With `lte_telem` enabled, use `heartbeat lte`, `system lte`, or `eps lte`. |

The six output flags are `cli_debug`, `cli_telem`, `umb_debug`,
`umb_telem`, `uhf_telem`, and `lte_telem`. The CLI flags govern console
output and the UMB flags govern the wired debug and telemetry streams.
The UHF and LTE flags gate their corresponding telemetry paths. Turning a
stream off cancels future submissions on that path.

The UHF startup profile console provides `startup`, `status`, `version`, `mode`,
`outputs`, `faults`, `rtos`, `radio`, `eps status`, `eps json`, and
`gps`. Its stop commands are `mode safe` and `uhf stop`. Yamcs uses the
LINK_ACTIVE radio path for command and schedule control.

## Packet layouts

Fields below read left to right. Lengths are in bytes.

```text
Native EMBER packet
[CCSDS primary header 6] [EMBER secondary header 24] [Payload N] [CRC-16 2]

Shared CAN request/reply envelope, before COBS
[Magic 2] [Version 1] [Type 1] [Sender boot 4] [Origin boot 4] [Request ID 4] [Length 2] [Payload N] [CRC-16 2]

Each classic CAN data field, after COBS encoding and zero termination
[Version/flags 1] [Token 2] [Fragment index 1] [Envelope slice 1–4]

Transceiver DBPSK v3 downlink
[Preamble 32] [Sync 4] [Version 1] [Sequence 4] [Length 2] [Native EMBER packet N] [CRC-32 4] [Guard 16]
```

The native CRC-16 covers both native headers and the payload. The CAN
envelope CRC-16 covers the decoded envelope header and payload. The RF
CRC-32 covers version through the native packet. The radio preamble and
guard belong to the transceiver frame. The conducted link accepts native
packets up to 128 bytes.

| CAN request → reply | Peer |
|---|---|
| `0x710` → `0x711` | Transceiver |
| `0x720` → `0x721` | Walter MCU |
| `0x740` → `0x741` | Payload |

The [packet dictionary](../../ground/ember/dictionary.json) lists individual
native fields and their widths. See the [shared transport guide](../comms_transport/README.md)
for CAN framing and the [radio guide](../../docs/comms/README.md) for the
downlink format.
