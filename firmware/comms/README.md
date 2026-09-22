# Comms Board Firmware

FreeRTOS control firmware for the RP2040 on the ember transceiver board.
Structure deliberately mirrors [`firmware/ihu`](../ihu/README.md) — same
RP2040, same Pico SDK, same kernel config — so the two boards stay
legible to the same reader and debugging habits transfer.

## v0.1 Status — boots, reports, detects

Three tasks run on the bench proto:

- **`selftest`** — one-shot. Safes every output pin, then detects and
  reports what hardware is actually present. Deletes itself when done.
- **`console`** — heartbeat every 5 s: uptime, task count, free heap.
  Confirms the scheduler is alive. Holds off until the self-test has
  published its report.
- **`blink`** — Pico module LED (GP25) at 1 Hz. Confirms firmware booted.

The self-test is the substance of v0.1. It does three things, in order:

1. **Safe the outputs.** `BPSK_DATA` low (a floating XOR input puts
   random phase on the carrier), `TX_ACTIVE` low (receive — matching the
   board pull-down on the planned PE4259 T/R switch), `COMMS_IRQ` high
   (de-asserted; the pull-up is on the IHU side, so a floating pin looks
   like a spurious data-ready).
2. **Detect.** i2c0 bus scan, Si5351A status probe, RX baseband DC bias.
3. **Report.** One line per check, then a pass/fail summary.

It deliberately **does not** configure or enable the Si5351A outputs.
CLK0 feeds the XOR modulator and the tripler, so enabling it puts a
carrier into the PA — that belongs behind an explicit command, not in
the boot path. Clock configuration is still the standalone bench app in
[`drivers/`](drivers/) (see `hardware/comms/bringup/tx_test_plan.md`).

### What the self-test can actually see

The Si5351A is the only digitally addressable part on this board, so
detection is not a long list — but the two checks between them cover
both halves of the design:

| Check | How | Reads on failure |
|---|---|---|
| i2c0 bus | Scan 0x08–0x77, skipping reserved addresses | Nothing responds → pull-ups (R1/R2), +3V3, or wiring |
| Si5351A | Read-only status register probe at 0x60 — ACK, `SYS_INIT`, `LOL_A`/`LOL_B`, revision | No ACK → part absent or unpowered. `SYS_INIT` stuck → usually a missing or dead 25 MHz crystal (Y1), since the internal init waits on it |
| RX baseband | ADC1 (GP27) DC level, 64 samples averaged | The MCP6022 gain stage is biased to mid-supply, so it idles at ~1.65 V. Near 0 V → unpowered/unpopulated, or the R10/R11 bias divider is open. Near 3.3 V → saturated, or the divider is shorted to +3V3. **An ADC pin with nothing attached floats and usually drifts to a rail**, so on a bare Pico or a partial build this reads as a fault when it is just an unconnected input — check continuity from the MCP6022 output to GP27 first |

Two details that only show up on real hardware:

- **Both PLLs report locked at boot**, on their power-on default dividers.
  That is the good case, not a surprise: the PLLs can only lock if Y1 is
  actually oscillating, which makes this a free 25 MHz crystal health
  check. Unlocked here is not a fault by itself — it only becomes one if
  it persists after `si5351_init()`.
- **`status` reads `0x11` on a healthy part.** Bit 4 is `LOS_CLKIN`,
  which is an Si5351**C** function; our A part has no CLKIN pin and
  reports it set. Decoded for completeness, not a fault.

The banner also prints the RP2040 unique board ID (so bench logs say
which Pico) and the reset reason (power-on vs. watchdog timeout).

### Expected console output

Shape of the boot report on a fully populated board — illustrative, not
a captured bench log:

```text
[comms] booting (build Sep 22 2026 14:11:03)
[comms] tasks created, starting scheduler

==================================================
 ember comms board — RP2040 transceiver controller
 firmware v0.1   build Sep 22 2026 14:11:03
 board id E66038B713849C2A
 reset: power-on / external
==================================================
[comms] outputs safed: BPSK_DATA=0 TX_ACTIVE=0 (RX) COMMS_IRQ=1 (de-asserted)
[comms] scanning i2c0 (sda=GP20 scl=GP21 @ 400000 Hz)
[comms]   found device at 0x60 (Si5351A)
[si5351a] present at 0x60  status=0x11  rev=1
[si5351a]   PLLA locked  PLLB locked  (power-on defaults; both locked means Y1 25 MHz is oscillating)
[rx-bb] GP27 (ADC1) idle bias = 1.648 V  (expect 1.65 ±0.35 V)
--------------------------------------------------
[comms] selftest: si5351a=PASS  rx-baseband=PASS  i2c-devices=1
[comms] clock outputs left DISABLED — CLK0 drives the XOR modulator and PA, so TX stays off until commanded
[comms] timing: console-wait=1250 banner=8 scan=41 si5351=2 rx-bb=1  total=1302 ms
--------------------------------------------------
[comms] heartbeat #0  uptime=3004 ms  tasks=4  free_heap=119880
```

On a bare Pico with nothing attached, expect `si5351a=FAIL` and
`rx-baseband=WARN` — that is the self-test working, not a bug.

### Boot-time LED diagnostics (GP25)

- 3 slow blinks (~150 ms each) right after `stdio_init_all()` — confirms
  `main()` ran end-to-end before the scheduler started.
- 1 Hz steady heartbeat once the scheduler is up.
- Fast continuous blink (~6 Hz) = stack overflow or malloc-failed panic;
  `printf` names the offending task on the console.

## Pin assignments

From the rev 0.9 Pico pin table in
[`hardware/comms/design/schematic_guide.md`](../../hardware/comms/design/schematic_guide.md),
cross-checked against `hardware/comms/kicad/Digital_Control.kicad_sch`.
Full detail, including the places those two disagree, is in
[`src/config/pinmap.h`](src/config/pinmap.h).

| GPIO | Net | Function |
|---|---|---|
| GP3 | `COMMS_IRQ` | Data-ready to IHU, active-low, pull-up on the IHU side |
| GP4 / GP5 / GP6 / GP7 | `SPI_COMMS_MISO` / `CS_N` / `SCK` / `MOSI` | SPI0 to IHU — comms is the **slave**. Declared, not yet driven |
| GP10 / GP11 | `TX_ACTIVE` / `RX_ACTIVE` | Status LEDs today; `TX_ACTIVE` becomes T/R switch control in the all-UHF rebuild |
| GP12 | `3V3_IND` | Board power LED |
| GP14 / GP15 | `SDA_HK` / `SCL_HK` | I2C1 **slave** at 0x42 — the IHU's housekeeping link. Not yet on the schematic; see below |
| GP16 | `BPSK_DATA` | Baseband bits into the 74LVC1G86 XOR modulator |
| GP20 / GP21 | `I2C_SDA` / `I2C_SCL` | I2C0 to the Si5351A (0x60), 4.7k pull-ups on board |
| GP25 | — | Pico module onboard LED (not on the comms schematic) |
| GP27 | `RX_BASEBAND` | MCP6022 output into **ADC1** (guide rev 0.9 moved this off ADC0) |
| GP0 / GP1 | — | UART0 console, free on the schematic, lands on the spare GPIO header |

## Project layout

```text
firmware/comms/
├── CMakeLists.txt              # top-level project, pulls in SDK + kernel
├── pico_sdk_import.cmake       # standard Pico SDK locator
├── FreeRTOSConfig.h            # kept identical to the IHU's, bar the header comment
├── drivers/                    # chip drivers + standalone bench apps
│   ├── si5351a.{c,h}           #   shared: linked into both this app and the bench tool
│   ├── si5351a_bringup.c       #   standalone RF bring-up app (its own CMakeLists.txt)
│   └── CMakeLists.txt
└── src/
    ├── CMakeLists.txt          # executable + link libraries
    ├── main.c                  # task creation, vTaskStartScheduler()
    ├── config/
    │   └── pinmap.h            # board pin assignments + board constants
    └── tasks/
        ├── selftest_task.{c,h}
        ├── hk_slave_task.{c,h}  # I2C slave — answers the IHU
        ├── console_task.{c,h}
        └── blink_task.{c,h}

firmware/shared/
└── comms_hk_proto.h            # housekeeping register map, shared with the IHU
```

`drivers/` predates this app and keeps its own build, because
`hardware/comms/bringup/` documents that path. The FreeRTOS app compiles
`si5351a.c` straight out of it rather than carrying a second copy.

## Build

```bash
export PICO_SDK_PATH=/path/to/pico-sdk

cd firmware/comms
cmake -S . -B build
cmake --build build -j"$(nproc)"
# Result: build/src/comms.uf2  (~48 KB)
```

Flash by holding BOOTSEL, plugging in USB, and dropping the `.uf2`.

### FreeRTOS kernel

The kernel submodule currently lives under the IHU tree and both boards
run the same version on purpose, so this project points at
`../ihu/lib/FreeRTOS-Kernel` by default rather than carrying a second
checkout. Run `git submodule update --init --recursive` from the repo
root if it is missing. To override:

```bash
cmake -S . -B build -DFREERTOS_KERNEL_PATH=/path/to/FreeRTOS-Kernel
```

A `lib/FreeRTOS-Kernel` added here later takes precedence automatically.

### Console

**Both** transports are enabled. The SDK fans `printf` out to every
enabled stdio driver, so the boot report lands on whichever one you have
hooked up — or on both at once.

**USB CDC** — the Pico module's own micro-USB, which the schematic guide
calls the primary programming and debug interface for the prototype:

```bash
screen /dev/ttyACM0 115200      # Linux
screen /dev/tty.usbmodem* 115200  # macOS
```

**UART0** — GP0 (TX) / GP1 (RX), 115200 8N1, via a USB-to-serial adapter.
Unassigned on the comms schematic and brought out on the spare GPIO
header, so it stays available on the populated board and keeps working
while USB is busy re-flashing or the host has dropped the port:

```text
adapter RX  <-  Pico GP0 (pin 1, TX)
adapter TX  ->  Pico GP1 (pin 2, RX)
adapter GND <-> Pico GND
```

```bash
screen /dev/ttyUSB0 115200
```

The self-test polls `stdio_usb_connected()` for up to 3 s before
printing, so the banner is not lost to enumeration; it returns as soon
as the host attaches, and gives up if nothing does. The console task
waits on the self-test's published result rather than a fixed delay, so
a heartbeat can never land in the middle of the boot report.

The IHU is UART-only because TinyUSB wants a FreeRTOS-aware config to
avoid deadlocking during scheduler start. That is satisfied here —
`FreeRTOSConfig.h` sets `configSUPPORT_PICO_SYNC_INTEROP` and
`configSUPPORT_PICO_TIME_INTEROP`, which is what the SDK needs to drive
the TinyUSB device task from FreeRTOS, and nothing prints from an ISR.
TinyUSB costs about 15 KB of flash.

> **USB writes can stall the whole board.** `pico_stdio_usb`'s writer
> busy-spins on `tud_task()` — it does not yield — for up to
> `PICO_STDIO_USB_STDOUT_TIMEOUT_US` whenever the CDC buffer is full and
> the host is not draining it. At the SDK default of 500 ms per stalled
> 64-byte chunk, a board with an enumerated but idle port spends most of
> its time in that spin, starving every lower-priority task. Because the
> self-test runs above the periodic tasks, that shows up as a boot that
> takes tens of seconds.
>
> `src/CMakeLists.txt` caps it at 100 ms, which is still far more than a
> real terminal needs. The `timing:` line in the boot report is there to
> catch it: if `total` dwarfs the sum of the stages, the time went into
> console I/O, not into the checks. The real fix for the TX path is not
> to `printf` from it at all — symbol timing is the one hard real-time
> deadline on this board.

## Housekeeping link to the IHU

The IHU is master on the shared CSKB housekeeping I2C bus and already
polls the EPS charger there. This board answers on the same bus at
**0x42**, presenting a 32-byte register file — so from the IHU's side,
asking the comms board how it is doing looks exactly like reading the
charger, and a bench `i2cdetect`/`i2cdump` finds it with no custom
tooling.

The register map, bus address, and byte order live in one place,
[`firmware/shared/comms_hk_proto.h`](../shared/comms_hk_proto.h), which
both firmware trees include. Neither side can drift.

| Offset | Size | Field | Notes |
|---|---|---|---|
| 0x00 | u8 | `WHO_AM_I` | `0xEC` — distinct from 0x00 and 0xFF, so a dead bus cannot read as a live board |
| 0x01 | u8 | `PROTO_VER` | checked by the IHU on every poll |
| 0x02 | u8 | `FW_VER` | major<<4 \| minor |
| 0x03 | u8 | `STATUS` | self-test done, Si5351A present, PLLs locked, RX bias OK, TX active, watchdog reset, fault |
| 0x04 | u8 | `SELFTEST` | two bits per check: PASS / WARN / FAIL |
| 0x05 | u8 | `I2C_DEVS` | devices found on *this* board's own bus |
| 0x06 | u8 | `TASKS` | FreeRTOS task count |
| 0x07 | u8 | `SI5351_STATUS` | register 0, undecoded |
| 0x08 | u32 | `UPTIME_S` | little-endian, as are all multi-byte fields |
| 0x0C | u32 | `FREE_HEAP` | |
| 0x10 | u16 | `RX_BB_MV` | RX baseband DC bias, millivolts |
| 0x12 | u16 | `XACT_COUNT` | transactions served since boot |
| 0x14 | u32 | `SCRATCH` | **the only writable register** — the ping echo |
| 0x18 | — | reserved | reads as zero |

`SCRATCH` is what makes this a ping rather than a presence check. The
IHU writes a 32-bit token and reads it back; a match proves the write
path, this board's slave ISR, and the read path all work end to end.
An address probe only proves that *something* ACKed.

There are deliberately **no command registers**. Keying the PA belongs
on the SPI link behind framing and a CRC, not on a housekeeping bus
where one corrupted byte could put RF on the antenna.

### Why this is on i2c1, not the I2C the schematic shows

The schematic guide (rev 1.5) ties the CSKB housekeeping pair
(H1.41/H1.43) and the Si5351A to the **same net**, `I2C_SDA`/`I2C_SCL`
on GP20/GP21. That is a two-master bus: the IHU drives it to reach the
EPS, and this board drives it to reach the Si5351A. The RP2040 I2C
block cannot be master and slave at the same time, so serving the IHU
off GP20/21 would mean flipping the peripheral between modes and
dropping any IHU transaction that arrived mid-flip.

So the firmware puts the housekeeping slave on its own peripheral:
**i2c1 on GP14/GP15**, both previously on the J3 spare list, both i2c1
alternate-function pins. i2c0/GP20/21 stays master-only to the Si5351A,
untouched.

**Board delta this implies** — not yet reflected in the schematic:
cut H1.41/H1.43 off the `I2C_SDA`/`I2C_SCL` net and route them to
GP14/GP15 as a new `SDA_HK`/`SCL_HK` pair. Bus pull-ups stay on the EPS
side (R4/R5, 4.7k); do not add more here. R1/R2 keep pulling up i2c0 for
the Si5351A and are unaffected.

**On the bench today** this is two jumpers — IHU GP4/GP5 to comms
GP14/GP15, plus a common ground — so the firmware is testable before
any respin.

### Checking it from the IHU console

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
```

`comms raw` dumps the register file as hex — the view you want when the
decoded output looks wrong and you need to know whether the problem is
the wire or the parser.

On this board, the console heartbeat carries the same counter from the
other direction:

```text
[comms] heartbeat #12  uptime=65021 ms  tasks=5  free_heap=118904  ihu=74 xacts
```

Still `ihu=0` after the IHU has booted means the bus is not carrying
traffic — check the jumpers before suspecting either firmware.

## Workstreams

### Workstream A: Runtime and boot

- [x] Project skeleton: CMake + FreeRTOS + Pico SDK boot
- [x] Multi-task scheduler running with `selftest`, `console`, `blink`
- [x] Deterministic output safing at boot (TX off, IRQ de-asserted)
- [x] Boot hardware detection + report (i2c scan, Si5351A, RX baseband)
- [x] Reset-reason reporting (power-on vs. watchdog)
- [ ] Define boot states (safe mode, nominal, high-duty) and gate on the
      self-test result
- [ ] Integrate the watchdog and a feed task

### Workstream B: RF control

- [x] Si5351A driver: PLL/multisynth configuration for TX and RX (bench)
- [x] Si5351A read-only status probe
- [ ] Promote clock configuration into a task, behind an explicit command
- [ ] TX state machine (idle, beacon, packet transmit)
- [ ] Framing and bitstream path for BPSK/DBPSK
- [ ] RX sampling and command packet decode
- [ ] Half-duplex TX/RX arbitration and fault recovery

### Workstream C: IHU link and ground support

- [x] Housekeeping I2C slave — the IHU can ping this board and read its
      status block (see below)
- [ ] SPI0 slave transport with CRC and sequence counter
- [ ] `COMMS_IRQ` assert/clear tied to the RX FIFO and TX status
- [ ] Promote the console to a real CLI (port `firmware/ihu/src/cli/`)
- [x] Board health telemetry schema (housekeeping register map — the
      bulk telemetry schema still rides the SPI link)

## Related documents

- Firmware roadmap: [`firmware/firmware.md`](../firmware.md)
- IHU firmware: [`firmware/ihu/README.md`](../ihu/README.md)
- Schematic guide (pin table, net names):
  [`hardware/comms/design/schematic_guide.md`](../../hardware/comms/design/schematic_guide.md)
- Architecture: [`hardware/comms/design/architecture.md`](../../hardware/comms/design/architecture.md)
- All-UHF rebuild plan:
  [`hardware/comms/design/kicad_implementation_plan.md`](../../hardware/comms/design/kicad_implementation_plan.md)
- Si5351A bring-up log:
  [`hardware/comms/bringup/si5351a_bringup_log.md`](../../hardware/comms/bringup/si5351a_bringup_log.md)
