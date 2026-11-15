# IHU firmware

[Changelog](CHANGELOG.md) · [Verified bench builds](../README.md#current-bench-builds)

The Internal Housekeeping Unit runs on the EMBER RP2040 CAN Feather. It
reads EPS and GPS, manages spacecraft modes, and exchanges commands and
telemetry with the transceiver, payload, and Walter MCU. The current
bench build is [IHU 0.31.0](releases/0.31.0/README.md) with the UHF startup profile.
[IHU 0.29.1 bench build and UF2](releases/0.29.1/README.md) remains available.

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

The command above selects the bench UHF profile. See the [profile matrix](#profiles-at-a-glance) for the other builds. Use a separate build directory for each profile.

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

## Profiles at a glance

The build flags select the profile at reset. All three flags default to `OFF`
in a fresh build directory.

| Profile | CMake flags to enable | What happens at boot | Available outputs and links |
|---|---|---|---|
| Regular `GROUND_TEST` | None | Checks local CAN, then enters `SAFE` with all six output flags off. | Enable CLI debug or telemetry, wired USB/umbilical debug or telemetry, UHF telemetry, and LTE telemetry individually from the console. |
| `GROUND_TEST / UHF` | `IHU_UHF_STARTUP` | Runs the startup checks and sends one CW beacon, then enters `NOMINAL / LINK_ACTIVE`. | USB startup log and diagnostics, plus Yamcs commands and replies over UHF. FULL telemetry starts enabled on a 120 s listen / 60 s transmit cycle. The independent heartbeat starts off. Yamcs can disable or adjust the schedule. |
| `GROUND_TEST / UHF` with RX_ONLY | `IHU_UHF_STARTUP` and `IHU_BOOT_RX_ONLY` | Runs the same startup checks and CW beacon, then enters `NOMINAL / RX_ONLY`. | USB startup log and diagnostics. UHF receive is active after the beacon. Command replies and scheduled UHF telemetry require LINK_ACTIVE. |
| `FLIGHT` | `IHU_FLIGHT_CONFIGURATION` | Enters `SAFE` with `HISTORY_UNAVAILABLE` if the CAN check passes. Flight routines are stubs. | USB diagnostics. All six optional outputs stay off. |

LTE is a [bench telemetry route](#usb-console) in regular GROUND_TEST.
The two UHF startup variants require the matching
[transceiver UHF startup build](../transceiver/README.md). CMake rejects
combining UHF startup with FLIGHT.

## Startup and modes

In regular GROUND_TEST, the console can select STARTUP, COMMISSIONING, SAFE,
or NOMINAL while the application is idle. Reset re-enters BOOT.

The UHF startup profile drives the transitions automatically. Its release
switches and antenna deployment are simulated. The CW beacon is a real
transceiver operation on the conducted bench.

| Mode | UHF startup profile |
|---|---|
| BOOT → SAFE | Start local services, check CAN and EPS, and wait for the transceiver to report ready. |
| STARTUP | Start the simulated antenna timer and radio silence timer when the transceiver is ready. The timers are 10 s and 15 s, respectively. |
| COMMISSIONING | Request one CW startup beacon and wait for transceiver receive readiness. |
| NOMINAL | Confirm the radio state for the selected UHF profile. |
| SAFE | A startup fault, link failure, or operator stop shuts down the UHF link and clears the outputs. Restart both boards to run startup again. |

The LINK_ACTIVE schedule begins with its listen phase. BASIC sends IHU status, valid EPS data, and
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
| `SET_RADIO_PROFILE` | Stages a supported UHF downlink profile for a timed trial. |
| `CONFIRM_RADIO_PROFILE` | Confirms the active trial with the token received in the UHF readback. |
| `REQUEST_RADIO_CONFIG` | Reads the transceiver defaults, active settings, and supported profiles over CAN. See the [radio configuration schema](../../docs/comms/radio_config.md). |
| `REQUEST_IHU_FAULTS` | Gets the latest 16 retained fault entries and the total for this boot. View the decoded names, boot ID, and uptimes on the Yamcs **IHU Faults** page. Works with scheduled telemetry off in LINK_ACTIVE. |
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

In the UHF startup profile, a due EPS health poll runs between GPS I²C
chunks. `eps status` shows sample age, the maximum interval between good EPS
samples, and the number of EPS polls that ran during GPS reads. EPS diagnostics
identify `I2C_TIMEOUT`, `PEC_CHECKSUM`, `I2C_ERROR`, and `STALE` separately.

The UHF startup profile enables the LTC4162 telemetry ADC on battery power
by default. Use `eps adc off` to restore automatic charger ADC behavior until
the next IHU reboot, or `eps adc on` to resume battery-only measurements.
The override changes only `force_telemetry_on` and leaves the measurement rate
and charge settings alone. Check `eps json` for `config_bits` and
`telemetry_status` before using the voltage readings.

The UHF startup profile console provides `startup`, `status`, `version`, `mode`,
`outputs`, `faults`, `rtos`, `radio`, `radio config`, `eps status`, `eps json`, and
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
