# Internal Housekeeping Unit Firmware

## Purpose

FreeRTOS-based control firmware for the IHU. Tracks
architecture, implementation milestones, and bring-up status for the
RP2040 system controller. Modeled on the AMSAT RT-IHU runtime (see
[RT-IHU](https://gitlab.amsat.org/engineering/golf/rt-ihu)) and the
`rp2040-freertos-ihu` proof-of-concept; both directly informed this
layout.

## Core Responsibilities

- System mode manager (safe, nominal, high-duty)
- Command parser, validation, and dispatch
- Subsystem link supervision (I2C/SPI, later CAN)
- Telemetry aggregation and framing handoff to comms
- Fault handling, retry policy, and recovery coordination

## v0.1 Status (proto board: RP2040 riser on top of EPS, GP4/GP5 → CSKB I2C)

Five FreeRTOS tasks are running on the bench proto:

- **`console`** — UART heartbeat every 5 s: uptime, task count, free
  heap. Confirms the scheduler is alive.
- **`blink`** — Onboard LED (GP25) at 1 Hz. Confirms firmware booted.
- **`eps-mon`** — Owns the boot bus scan, then polls the LTC4162 every
  5 s and decodes charger telemetry.
- **`comms-mon`** — Pings the comms board every 5 s and reads its
  status block. See [Housekeeping bus](#housekeeping-bus) below.
- **`cli`** — Interactive command line on the same UART.

Both monitor tasks share i2c0, so every transaction now goes through
the bus lock in [`src/config/i2c0_bus.h`](src/config/i2c0_bus.h).

## Project Layout

```text
firmware/ihu/
├── CMakeLists.txt                 # top-level project, pulls in SDK + kernel
├── pico_sdk_import.cmake          # standard Pico SDK locator
├── FreeRTOSConfig.h               # FreeRTOS feature flags (128 KB heap, 1 kHz tick)
├── lib/
│   └── FreeRTOS-Kernel/           # git submodule (FreeRTOS/FreeRTOS-Kernel)
└── src/
    ├── CMakeLists.txt             # executable + link libraries
    ├── main.c                     # task creation, vTaskStartScheduler()
    ├── config/
    │   ├── pinmap.h               # board pin assignments (LED, I2C)
    │   └── i2c0_bus.{c,h}         # shared housekeeping-bus init + mutex
    ├── cli/
    │   └── cli.{c,h}              # line buffer + command table
    ├── drivers/
    │   ├── ltc4162.{c,h}          # EPS charger (0x68)
    │   └── comms_link.{c,h}       # comms board housekeeping client (0x42)
    └── tasks/
        ├── console_task.{c,h}
        ├── blink_task.{c,h}
        ├── eps_monitor_task.{c,h}
        └── comms_monitor_task.{c,h}

firmware/shared/
└── comms_hk_proto.h               # housekeeping register map, shared with comms
```

Future additions slot into `src/drivers/` (MR25H40, STWD100),
`src/tasks/` (SPI link to comms, telemetry aggregator, command
dispatch, watchdog feed), and `src/state/` (mode FSM, persistent
state in MRAM).

## Housekeeping bus

i2c0 (GP4/GP5 → CSKB H1.41/H1.43) carries two devices:

| Address | Device | Driver |
|---|---|---|
| 0x68 | EPS LTC4162-L charger | `drivers/ltc4162.{c,h}` |
| 0x42 | Comms board | `drivers/comms_link.{c,h}` |

The comms board presents a 32-byte register file defined in
[`firmware/shared/comms_hk_proto.h`](../shared/comms_hk_proto.h) —
included by both firmware trees, so the map cannot drift between them.
The full table and the wiring notes are in the
[comms README](../comms/README.md#housekeeping-link-to-the-ihu).

`comms-mon` does two things per cycle: a round-trip **ping** (write a
32-bit token to the comms board's scratch register, read it back, check
it matches) and a **status block read**. The ping is what distinguishes
a live link from "something on the bus ACKed an address" — it exercises
the write path, the comms slave ISR, and the read path end to end.

```text
ihu> comms ping
pong from 0x42 — token 0xA5001F40 echoed, 412 us round trip

ihu> comms
link        : UP (last good 2 s ago, 412 us rtt)
fw / proto  : v0.1 / v1
uptime      : 184 s  (tasks=5, free heap=118904 B)
self-test   : complete
si5351a     : PASS  (raw status 0x11, PLLs locked)
rx baseband : PASS  (1648 mV, expect ~1650)
i2c devices : 1 on the comms board's own bus
tx active   : no (receive)
xacts served: 74  (polls from this IHU: 37)

ihu> comms raw        # 32-byte hex dump, for when the decode looks wrong
```

A board that drops off the bus is reported once, on the transition, not
once every 5 s forever. `comms` still shows the failure count and the
age of the last good poll on demand.

### Bus serialisation

`eps-mon`, `comms-mon`, and the CLI all reach i2c0. The RP2040 I2C
block holds one transaction's state at a time, so a preemption between
a register-pointer write and the repeated-START read that follows
splices two transactions together — and it does not fail loudly, it
returns plausible-looking wrong numbers.

So i2c0 is brought up once in `main()` and every logical transaction
runs between `ihu_i2c0_lock()` and `ihu_i2c0_unlock()`. "Logical"
means the whole sequence that has to be coherent — all eight LTC4162
telemetry registers, or the read-modify-write in `ltc4162_kick()` —
not each individual SDK call. Both drivers take the lock internally,
so callers do not have to think about it.

The comms poll is phased 2.5 s off the EPS poll so two 5 s cadences do
not contend every single cycle.

## Build (host: Linux/macOS with Pico SDK installed)

```bash
# 1. Clone with submodules (or update existing checkout):
git clone --recurse-submodules <repo-url>
# or:
git submodule update --init --recursive

# 2. Point at your Pico SDK (one-time setup):
export PICO_SDK_PATH=/path/to/pico-sdk

# 3. Build:
cd firmware/ihu
mkdir build && cd build
cmake ..
make -j$(nproc)
# Result: build/src/ihu.uf2  (≈58 KB)

# 4. Flash:
#    Hold BOOTSEL on the Pico, plug in USB, drag-and-drop the .uf2.
#    The board reboots into the application.

# 5. Connect a USB-to-serial adapter to the UART console:
#      adapter RX  <-  Pico GP0 (pin 1, TX)
#      adapter TX  ->  Pico GP1 (pin 2, RX)
#      adapter GND <-> Pico GND (pin 3/8/13/18/23/28/33/38)
#    Open at 115200 8N1:
#      screen /dev/ttyUSB0 115200      # Linux
#      screen /dev/tty.usbserial-* 115200   # macOS
#      PuTTY @ 115200                  # Windows

# Expected console output:
#   [ihu] booting (build May 18 2026 18:07:05)
#   [ihu] tasks created, starting scheduler
#   [ihu] console up — FreeRTOS scheduler running
#   [ihu] heartbeat #0  uptime=1504 ms  tasks=5  free_heap=119880
#   [i2c] scanning i2c0 (sda=GP4 scl=GP5 @ 100000 Hz)
#   [i2c]   found device at 0x68
#   [i2c] scan complete — 1 device(s)

# Boot-time LED diagnostics (GP25):
#   - 3 slow blinks (~150 ms each) right after stdio_init_all() —
#     confirms main() ran end-to-end before the scheduler started.
#   - 1 Hz steady heartbeat after the scheduler is up.
#   - Fast continuous blink (~6 Hz) = stack overflow or malloc-failed
#     panic — printf names the offending task on UART.
#   [ihu] heartbeat #1  uptime=6500 ms  tasks=4  free_heap=126432
#   ...
```

`build/` and all generated binaries are in `.gitignore` (top-level)
so nothing under the build tree gets committed.

## Workstreams

### Workstream A: Runtime and State Machine

- [x] Project skeleton: CMake + FreeRTOS + Pico SDK boot
- [x] Multi-task scheduler running with `console`, `blink`, `i2c-scan`
- [ ] Define explicit state machine for mode transitions
- [ ] Implement boot sequence and health gating checks
- [ ] Enforce default safe mode at boot until EPS I2C and comms SPI links
  are both healthy for N consecutive checks
- [ ] Implement safe-mode entry/exit conditions and actions

### Workstream B: Interface Drivers and Link Management

- [x] I2C0 bus init + reserved-address-aware bus scan
- [x] I2C0 bus mutex — two polling tasks plus the CLI now share it
- [x] LTC4162 driver: detect, decode telemetry (V_BAT, V_IN, I_BAT,
  charger state, alerts). MPPT configuration still open
- [x] Implement EPS housekeeping I2C client (periodic poll)
- [ ] Range/sanity limits on EPS telemetry
- [x] Comms board housekeeping client — ping + status block over I2C
- [ ] Implement IHU-comms SPI packet transport with CRC and sequence
  counter
- [x] Link heartbeat and timeout handling for the comms housekeeping link
- [ ] Link heartbeat and timeout handling for the SPI transport
- [ ] Add CAN transport abstraction for Iteration 2

### Workstream C: Command and Telemetry Services

- [ ] Implement command schema decode and dispatch table
- [ ] Implement ACK/NACK and execution result reporting
- [ ] Implement telemetry collection scheduler and queueing
- [ ] Implement priority policy (preserve safety alerts under congestion)

### Workstream D: Reliability and Diagnostics

- [x] UART console heartbeat with uptime + free-heap reporting
- [x] Promote console to a real CLI (line buffer, command table)
- [ ] Integrate watchdog (STWD100 on flight board, software WDT on proto)
  and reset-reason reporting
- [ ] Add structured fault/event log (RAM ring, persisted to MRAM)

## Phase 1 Exit Criteria

- [ ] IHU boots to deterministic safe state and reports reset reason
- [ ] Stable I2C polling and SPI packet exchange with bounded retry
  behavior
- [ ] Command/telemetry loop closes with reproducible test results

## Related Documents

- IHU hardware architecture: [`hardware/ihu/design/overview.md`](../../hardware/ihu/design/overview.md)
- IHU interfaces: [`hardware/ihu/design/interfaces.md`](../../hardware/ihu/design/interfaces.md)
- IHU bring-up tests: [`hardware/ihu/bringup/phase1_validation.md`](../../hardware/ihu/bringup/phase1_validation.md)
- Reference port: `/workspace/MSU_Cubesat/rp2040-freertos-ihu/`
- AMSAT RT-IHU: <https://gitlab.amsat.org/engineering/golf/rt-ihu>
  (local read-only checkout: `/workspace/AMSAT/rt-ihu/`)
