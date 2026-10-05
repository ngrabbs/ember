# IHU CAN Feather USB console

[Operator guides](README.md) · [Implementation and bench evidence](../../firmware/can_feather_bench/README.md)

This guide covers the standalone `ember_ihu_can_bench` application, reviewed
October 4, 2026, reconciled with main on October 5. It uses USB text stdio. It has no `ihu>` prompt and does not
implement the FreeRTOS UART command set. The COMMS role shares the six common
commands below but has no IHU-only EPS/LTE commands.

## Identify and connect

Open the exact IHU USB serial device and run `status` and `help`. The recorded
IHU flash identity is `DF641455DB822427`; COMMS is `DF637882D39E4426`.
Their USB vendor descriptors may both say Raspberry Pi Pico. Verify `role=IHU_MCU`
in the status response before issuing IHU controls. USB CDC carries the text;
there is no physical UART baud setting for this interface. A terminal can use
115200. Do not share the port with `can_chain.py` or another diagnostic helper.

The source uses exact, case-sensitive line matching with a 39-character limit.
CR or LF dispatches a line. Long lines are discarded with
`ERROR command too long`; unknown names return `ERROR unknown command`.
This parser does not implement the FreeRTOS terminal's editing or command echo;
send complete literal lines. Status/log output is suppressed when USB is not
connected, while the MCU keeps running its CAN/UART transport loop.

EPS wiring is **I2C1 GP2 SDA / GP3 SCL, 100 kHz, address 0x68**, with a common
ground. These are the Feather's labeled I2C pads. The FreeRTOS Pico GP4/GP5
wiring does not apply to this image.

## Command reference

| Syntax | Effect and prerequisites | Response |
|---|---|---|
| `status` | Reads role, boot/peer identity, controller registers, link/error counters and pending work | One `STATUS` line; `mode=00` is normal, `40` loopback, `80` configuration |
| `help` | Prints compiled role's command list | One `COMMANDS` line |
| `selftest` | Sends a local MCP loopback frame, leaving controller in loopback mode; requires idle transport | `SELFTEST started=1 kind=LOCAL_LOOPBACK no_peer_proof=1`, then PASS/FAIL |
| `normal` | Enters normal CAN mode and clears remembered peer; requires idle transport | `CAN_NORMAL ready=1` on success; obtain a fresh HELLO afterward |
| `hello` | Exchanges CAN identity; normal mode required | `SUBMITTED ...`, then `RESULT ... outcome=CAN_HELLO_CONFIRMED ...` |
| `ping N` | Exchanges N ascending payload bytes, 1–240; normal mode and HELLO required | `CAN_ECHO_MATCHED` on exact return; this is CAN diagnostic echo |
| `telemetry` | Builds one native HEARTBEAT and submits it through the CAN chain | `WALTER_BENCH_RETURN` after matching chain reply, or rejection/UNKNOWN |
| `eps json` | Reads all 19 charger registers with PEC, without configuration writes; requires idle transport | Complete `ltc4162-l-readout-v1` JSON, or `EPS_READ outcome=FAILED ...` |
| `eps adc on` / `eps adc off` | Explicitly changes CONFIG_BITS bit 2 and verifies readback; requires idle transport | `EPS_ADC outcome=VERIFIED` or `UNKNOWN`, plus requested/before/after fields |
| `eps telemetry` | Reads EPS, creates native 128-byte POWER_STATUS, submits CAN chain; normal mode, HELLO and idle transport required | `SUBMITTED` and a chain result; no packet on failed read |
| `telem on [seconds]` | Arms native EPS cadence; default 20 seconds, accepted range 5–3600; normal CAN, HELLO and LTE queue off required | `AUTOTELEM` state or `REJECT` with range/readiness reason |
| `telem status` / `telem off` | Reads timer state or prevents future timer reads; off does not cancel a pending transaction | `AUTOTELEM enabled=... period_ms=... next_ms=... due=... skipped=... submitted=... failed=... pending=... uptime_ms=...` |
| `lte N` | Requests bounded Walter RF window, 0 stops, maximum 120 seconds; requires CAN HELLO and compatible Walter firmware | `RF_WINDOW_ACCEPTED` means window admission, not modem registration |
| `lte status` | Requests Walter link state | `LTE_STATUS` and correlated `RESULT` |
| `lte diagnostics` | Requests extended Walter diagnostic fields | `LTE_STATUS`, `LTE_DIAG`, then correlated `RESULT` |
| `eps lte` | Reads EPS and requests one Walter UDP submission | `MODEM_ACCEPTED` means modem submission, not ground reception |
| `eps enqueue` | Captures one real native EPS packet into volatile four-entry FIFO; requires idle transport | `EPS_QUEUED ...`, or BUSY/full/read failure |
| `lte queue on` / `lte queue off` | Enables/disables FIFO processing; does not start RF or erase queued packets | `LTE_QUEUE` state and counters |
| `lte queue status` | Reads FIFO count, state, hold reason and attempts | `LTE_QUEUE enabled=... count=... capacity=4 ...` |
| `lte queue drop` | Drops the oldest non-active packet | Updated `LTE_QUEUE` or `REJECT reason=QUEUE_EMPTY_OR_ACTIVE` |

## A diagnostic session

For CAN link checks, both controllers need normal mode. If you run `selftest`,
wait for its result, then return that controller to normal. Run these on IHU,
waiting for each result before continuing:

```text
status
normal
hello
ping 32
eps json
```

Illustrative exchanges below use source-defined labels; identities, request
numbers and bytes vary. Ellipses are presentation omissions, not literal output:

```text
CAN_NORMAL ready=1
SUBMITTED request=1 type=1 bytes=0
RESULT request=1 outcome=CAN_HELLO_CONFIRMED peer=4252110043 bytes=0 hex=
```

Do not type `SUBMITTED` or `RESULT`; these are replies. Normal mode clears the
previous peer, so `hello` must follow `normal`. A local loopback PASS proves the
controller's local path, not the external CAN harness.

`telemetry` sends one HEARTBEAT; `eps telemetry` sends one native EPS packet
through CAN/Walter echo. A returned echo does not establish radio delivery.
The native EPS timer is disabled at boot and is not persisted. After normal CAN
and HELLO, with the LTE queue off, `telem on 20` schedules the first read after
20 seconds. Busy/unavailable transport periods are skipped without catch-up or
backlog. The timer continues without an open USB console; `telem off` prevents
future reads but does not cancel a pending transaction.

An illustrative status reply (timing and counters vary):

```text
AUTOTELEM enabled=1 period_ms=20000 next_ms=40000 due=1 skipped=0 submitted=1 failed=0 pending=0 uptime_ms=20000
```

`submitted` counts local CAN submission, not RF delivery. No ADC configuration
or LTE RF-window change is made by arming the timer. The [UHF runbook](../../ground/uhf/README.md)
and [optional service runbook](../../ground/uhf/SERVICES.md) own the separate
SDRB/radio setup and ground/archive checks. Services remain disabled at boot.

For bounded LTE experiments, follow the [LTE runbook](../../ground/lte/BRINGUP.md).
`lte N` admits a finite RF window and `eps lte` submits one real EPS packet;
check ground capture and archived byte identity independently of modem acceptance.

## EPS readout and ADC behavior

The JSON schema and quality rules match the [UART readout example](ihu-debug-uart.md#reading-responses).
The CAN image prints a failure register if any read/PEC check fails:

```text
EPS_READ outcome=FAILED register=3a reason=I2C_OR_PEC
```

The register shown is illustrative. Invalid ADC data is still included in a
successful raw JSON read. Native EPS engineering fields use unavailable sentinels
when conversion is invalid. Sense-resistor values remain provisional; die
temperature is not battery temperature.

`eps adc on` explicitly forces telemetry conversion during battery-only use;
it is a configuration change, not an observational read. An illustrative reply:

```text
EPS_ADC outcome=VERIFIED requested=1 config_before=0000 config_after=0004
```

`UNKNOWN` means the write/readback did not establish the requested state. It
must not be treated as proof that no write occurred. The helper preserves other
CONFIG_BITS; it does not change charging policy. Low-speed ADC conversions can
remain about five seconds apart, so repeated reads may return the same conversion.

## Outcomes and recovery

| Reply | Meaning and next step |
|---|---|
| `SUBMITTED` | A local request was queued; wait for a correlated result |
| `REJECT reason=BUSY` | Existing transport work is active; wait and inspect `status` |
| `REJECT reason=NORMAL_MODE_REQUIRED` | Set normal mode, then obtain HELLO |
| `REJECT reason=HELLO_REQUIRED` | No established peer; perform HELLO |
| `REJECT reason=BUSY_OR_CAN_NOT_READY` | EPS packet submission prerequisites failed; inspect mode, peer and pending state |
| `RESULT ... outcome=PEER_REJECTED reason=...` | Peer explicitly refused; inspect peer diagnostics |
| `RESULT ... outcome=UNKNOWN reason=TIMEOUT` | Response deadline expired; inspect actual state and establish a fresh HELLO |
| `CAN_TX outcome=UNKNOWN reason=FRAME_TX_FAILED` | A fragment failed; local CAN transport does not prove application outcome |
| `WALTER_BENCH_RETURN` | Exact packet returned through the diagnostic chain; not an RF receipt |
| `MODEM_ACCEPTED` | Walter modem accepted a submission; check ground capture/archive independently |

Ordinary application requests use a five-second bound; LTE packet submission
uses a 22-second IHU bound. There is one pending application request. Requests
are not automatically retried after uncertain outcomes. The experimental LTE
FIFO retries only explicit pre-submission NOT_READY/BUSY, up to three attempts;
uncertain, expired or other failed outcomes hold the packet for inspection.
Queue retirement counts modem acceptance. Review the
[FIFO policy](../../ground/lte/results/2026-10-02-queue-preparation.md) before use.

## Source and evidence

Syntax/output: [command dispatcher](../../firmware/can_feather_bench/main.c),
[USB build configuration](../../firmware/can_feather_bench/CMakeLists.txt),
[EPS reader](../../firmware/can_feather_bench/eps_readout.h) and
[LTE queue policy](../../firmware/comms_transport/lte_queue.h) and
[native timer policy](../../firmware/can_feather_bench/autotelem.h).
Recorded hardware checks: [CAN/EPS milestones](../../firmware/can_feather_bench/README.md)
and [native LTE trials](../../ground/lte/README.md).
Production RTOS integration, CAN redundancy, reliable continuous LTE, and RF
command uplink are still separate work.
