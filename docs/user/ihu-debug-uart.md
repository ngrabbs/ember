# IHU debug UART

[Operator guides](README.md) · [Firmware and build](../../firmware/ihu/README.md)

This guide covers `firmware/ihu`, the FreeRTOS Pico prototype with an `ihu>`
prompt. It supports local text diagnostics; it does not expose the flight
command dictionary. The CAN Feather runs a [different USB console](ihu-can-console.md).
Source reviewed October 4, 2026; numeric examples below are illustrative unless
identified as a dated capture.

## Connect and open the console

Use a USB-to-UART adapter with **3.3 V logic**, a common ground, and the existing
board power arrangement. Connect the signal wires as follows:

| Adapter | Pico GPIO | Pico physical pin |
|---|---|---|
| RX | GP0, IHU TX | 1 |
| TX | GP1, IHU RX | 2 |
| GND | GND | 3, or another documented Pico ground |

Open **115200 baud, 8 data bits, no parity, 1 stop bit**, with flow control off.
Disable terminal local echo: the firmware echoes typed characters. Pico USB CDC
stdio is disabled in this application, so its USB cable alone is not the CLI.
EPS uses I2C0 GP4/GP5 at 100 kHz in this image.

On the ground Pi, `ember-eps-bridge` owns the UART adapter exclusively. Before
interactive use, note whether it is active, then stop it on that Pi:

```sh
systemctl is-active ember-eps-bridge
sudo systemctl stop ember-eps-bridge
screen /dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0 115200
```

The device path is specific to the recorded installation. Identify your adapter
before using it; vendor-identical adapters can make this path ambiguous. On
macOS, use your identified `/dev/tty.usbserial-*` device; on Windows select the
adapter's COM port with the same serial settings.

At boot the firmware prints scheduler and monitor output, then after about
3.5 seconds:

```text
CLI ready — type 'help'
ihu>
```

If already running, press Enter to obtain a prompt. Do not reboot solely to
get a prompt. Commands are case-sensitive. Enter can send CR or LF; CRLF may
produce an extra empty prompt. Backspace/Delete edits the current line; Ctrl-C
clears the line being typed. It does not cancel an already executing handler.
There is no command history, quoting, completion or shell scripting. Lines hold
95 characters and at most eight tokens; extra characters are silently dropped.
Use exactly the documented syntax: several handlers ignore extra arguments,
and `eps` with an unrecognized subcommand falls back to the engineering report.

After finishing, close the terminal so it releases the adapter. With `screen`,
Ctrl-A then K closes the session. If you used `quiet`, send `loud` before closing.
Restart the bridge if it was active before you stopped it:

```sh
sudo systemctl start ember-eps-bridge
systemctl status ember-eps-bridge
```

Confirm fresh EPS packets return in Yamcs. The bridge itself does not set
quiet mode or change charger configuration. See [installation and validation](../../system/ground_station/eps_yamcs_setup.md).

## Commands available in this application

All ten command names appear in `help`, including handlers disabled by build
options. Presence in help does not mean a charger write is enabled.

| Syntax | What it does | Response or important effect |
|---|---|---|
| `help` | Lists the command table | Starts with `commands:` and prints each name and description |
| `stats` | Reads runtime counters | Uptime, task count, current free heap and minimum-ever free heap |
| `eps` | Prints the latest valid monitor snapshot in engineering units | State, charge status, voltages, currents and chip die temperature; may refuse if no valid snapshot |
| `eps raw` | Performs a fresh 19-register charger read | Register address, name, hex/decimal word and ADC/chemistry/cell flags |
| `eps json` | Performs the same raw read and emits machine-readable JSON | One `ltc4162-l-readout-v1` object with uptime and all 19 register words |
| `comms` | Reads the monitor's last successful comms snapshot and current link health | Includes link state, age, firmware/protocol, self-tests and TX state; explicitly labels stale values |
| `comms ping` | Writes a scratch token, reads it back and checks it | `pong` with token and round-trip time, or connection/echo diagnostics |
| `comms raw` | Reads the comms 32-byte register file | Four rows of eight hex bytes, identity and protocol versions |
| `quiet` | Suppresses routine heartbeat and telemetry text | Polling continues; comms alerts still print |
| `loud` | Restores routine output | `background output re-enabled` |
| `kick` | In a write-enabled build, pulses charger suspension to restart evaluation | Blocked by default; writes charger state if enabled |
| `ntc-bypass on` / `ntc-bypass off` | In a write-enabled build, widens JEITA limits or restores the driver's defaults, then kicks the charger | Changes temperature-related charging behavior; blocked by default |
| `charge-test start` / `charge-test stop` | In the timed-test build, starts a supervised maximum 60-second charging test or requests stop/restoration | Disabled by default; test removes battery temperature protection |
| `reboot` | Requests a watchdog reset after printing a message | Resets the whole IHU; no confirmation prompt |

## Reading responses

An illustrative `stats` exchange:

```text
ihu> stats
uptime    : 6500 ms (6 s)
tasks     : 7
free heap : 112880 bytes
min heap  : 112400 bytes (lowest ever)
ihu>
```

Task count includes runtime tasks and can differ by build. Heap numbers are
bytes; uptime is elapsed scheduler time, not UTC.

`eps` uses the monitor snapshot rather than forcing a new raw poll. It prints
`state`, `charge`, `system_stat`, `V_IN`, `V_OUT`, `V_BAT`, `die_temp`, `I_IN`
and `I_BAT`. Positive battery current means charging into the battery. Chip die
temperature is not battery temperature. Current conversion assumes the configured
sense resistors; their fitted values remain unverified in the bench evidence.
When the snapshot is invalid, the exact response is:

```text
no current valid telemetry — use eps raw/json to inspect bus/ADC/chemistry
```

An illustrative engineering report has this layout. Values vary; these numbers
are not a new hardware capture:

```text
ihu> eps
state       : ntc-pause
charge      : off
system_stat : 0x00A1
V_IN        : 10.600 V
V_OUT       : 10.560 V
V_BAT       :  8.180 V
die_temp    :  24.54 C (chip die, not battery)
I_IN        :   +90.0 mA
I_BAT       :    -2.0 mA (positive = charging into battery)
```

`eps raw` begins `LTC4162 observational readout (addr=0x68):` and ends with
ADC-valid, chemistry and detected-cell fields. It returns unsigned raw words;
signed current interpretation belongs in the decoder. A complete read can
contain invalid ADC measurements. Zero raw readings do not establish zero volts
or current when ADC-valid is zero.

This complete JSON example uses the captured October 1 readout values, formatted
as the current one-line response. It demonstrates unavailable ADC data:

```json
{"profile":"ltc4162-l-readout-v1","uptime_ms":11825,"registers":{"config_bits":0,"charger_config_bits":1,"charger_state":256,"charge_status":0,"limit_alerts":0,"charger_state_alerts":0,"charge_status_alerts":0,"system_status":161,"vbat":0,"vin":0,"vout":0,"ibat":0,"iin":0,"die_temp":0,"thermistor_voltage":0,"bsr":0,"jeita_region":7,"chem_cells":224,"telemetry_status":0}}
```

The [shared register list](../../firmware/shared/ltc4162_registers.h) owns the
19 names; `telemetry_status` bit 0 is ADC-valid. Raw register reads are sequential,
not an atomic ADC snapshot. `uptime_ms` is obtained after the read. If the bus,
lock or PEC check fails, no partial JSON is returned:

```text
[eps-readout] no complete readout (bus/lock/PEC failure)
```

Routine output may interleave with your command. Use `quiet` before a manual
JSON capture, then `loud` afterward. The exact quiet response is:

```text
background output suppressed (use 'loud' to re-enable)
  (telemetry still polling — use 'eps' for on-demand readout)
```

The comms commands use the **jumper I2C housekeeping link at 0x42**, not RF or
CAN. A successful example is:

```text
ihu> comms ping
pong from 0x42 — token 0xA5001F40 echoed, 412 us round trip
```

Token and timing vary. This proves scratch echo over that bus, not radio
reception or spacecraft command execution. `comms` reports `UP`/`DOWN`, time
since the last good poll, round-trip time, firmware/protocol, uptime/tasks/heap,
self-test completion, Si5351A/baseband checks, local I2C device count, TX state
and served transactions. A DOWN snapshot may still show old values; look for
`values below are stale`. Before any successful reply it prints:

```text
link        : DOWN — comms board has never answered
```

`comms raw` can report `i2c0 busy (lock timeout)`, no ACK, or a short read. An
unknown comms subcommand returns `usage: comms [ping|raw]`.

## Build-dependent control commands

Default builds set both `IHU_EPS_ALLOW_CHARGER_WRITES=OFF` and
`IHU_EPS_TIMED_BENCH_TEST=OFF`. `kick` and `ntc-bypass` then return:

```text
read-only diagnostics: charger writes disabled
```

A timed charging command returns:

```text
timed charging test disabled in this build
```

The two build options cannot both be enabled. A legacy write-enabled build also
changes charger initialization, so it is more than permission for a CLI handler.
Do not infer the image's build options from the help list. Verify its recorded
build provenance before using a charger-control procedure.

Write-enabled responses include `LTC4162 kicked — suspend_charger pulsed, state
machine re-evaluating`, or `LTC4162 kick I2C write failed`. NTC bypass reports
`NTC bypass ENABLED (jeita window widened) — kicking charger to re-evaluate`,
`NTC bypass DISABLED (defaults restored) — kicking charger to re-evaluate`, or
`ntc-bypass write failed`. The kick's result is not separately reported by the
NTC handler. “Defaults restored” does not mean the original pre-test configuration
was recovered. NTC bypass is a bench intervention, not a normal diagnostic step.

The timed-test start response is:

```text
BENCH CHARGE TEST ACTIVE: 60s, minimum servo, <=4.10V/cell, NO BATTERY TEMPERATURE PROTECTION
```

Start can instead print `charge-test refused or failed; inspect EPS; disconnect
input if recovery failed`. Stop returns `charge-test stop: restored/suspended`
or `charge-test stop: FAILED; disconnect charge input`. Follow the
[supervised bench procedure](../../system/ground_station/eps_bench_setup.md)
for preparation and recovery; the syntax here does not qualify battery safety.

`reboot` prints `rebooting via watchdog in 100 ms...`, then resets. `quiet` is
runtime state and resets on boot. An unknown top-level name prints
`unknown command: NAME  (try 'help')`.

## Source and validation scope

Behavior: [CLI](../../firmware/ihu/src/cli/cli.c),
[build options and stdio](../../firmware/ihu/src/CMakeLists.txt),
[pin configuration](../../firmware/ihu/src/config/pinmap.h), and
[EPS driver](../../firmware/ihu/src/drivers/ltc4162.c).
Recorded hardware context and readouts: [EPS bench setup](../../system/ground_station/eps_bench_setup.md).
UART/Yamcs ownership and quality checks: [October 1 validation](../../system/ground_station/eps_yamcs_setup.md).
These sources were inspected during documentation work; no charger command was executed.
