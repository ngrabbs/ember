# FPGA Link Processor and Logic Interface: First Bring-Up Plan

## Purpose

This document defines the smallest useful, testable portion of the experimental BPSK transmitter:

```text
FPGA test-pattern and symbol source
             ↓
Registered symbol output
             ↓
Logic buffer or voltage translator
             ↓
Logic-analyzer output and protected FPGA loopback
```

The goal is to prove the digital transmitter core and its electrical interface without depending on the oscillator, mixer, filters, amplifier, antenna, or DAC.

The first milestone is:

> Generate constant, alternating, and PRBS-7 symbol patterns in the FPGA; send them through an output-enable-controlled buffer; loop the buffered signal back into the FPGA; and count errors at progressively higher symbol rates.

This is the smallest building block that produces reusable evidence for every later RF architecture.

---

## 1. Why These Blocks Matter

The **FPGA link processor** is the reusable data and waveform engine. It can eventually provide:

- Source-data ingestion.
- Buffering and flow control.
- Packet framing and synchronization.
- CRC generation.
- Scrambling and optional forward-error correction.
- Symbol mapping.
- Symbol-rate timing.
- Test-pattern generation.
- Transmitter enable and fault handling.
- Telemetry counters and debugging.

The **logic buffer/level interface** provides the electrical boundary between the FPGA and the selected modulator. It can provide:

- Voltage compatibility.
- FPGA pin protection and isolation.
- A defined disabled state while the FPGA configures.
- Output-enable control.
- Greater drive current when appropriate.
- Edge damping and convenient test access.

These blocks are central, but they do not replace the RF front end. The eventual mixer, phase switch, or modulator determines the required electrical drive, while the filters and amplifier determine spectral cleanup and transmitted power.

In particular, a CMOS logic buffer is **not automatically a 50-ohm RF driver** and is not automatically suitable for driving a passive mixer's IF port. That decision requires the modulator's impedance, voltage, current, bandwidth, and linearity requirements.

---

## 2. Board Facts to Verify

The published IceZero TE0876 documentation reports:

- A Lattice iCE40 LP/HX-family FPGA.
- A 100 MHz SiT8008 onboard clock.
- 3.3 V LVCMOS I/O on the PMOD connectors.
- An open-source iCE40 build flow.

Sources:

- [Trenz TE0876 resources](https://wiki.trenz-electronic.de/display/PD/TE0876%2BResources)
- [IceZero Rev. 2 pinout and build notes](https://www.trenz-electronic.de/trenzdownloads/Trenz_Electronic/Modules_and_Module_Carriers/3.05x6.5/TE0876/REV02/Documents/iceZero-pinout-v5.pdf)
- [Lattice iCE40 LP/HX family data sheet](https://www.latticesemi.com/~/media/latticesemi/documents/datasheets/ice/ice40lphxfamilydatasheet.pdf)

The available IceZero documents contain device/revision caveats. The table below
is filled in from `iceZero-pinout-v5.pdf` (board rev2, document v7, 2022-07-02),
which is a complete pin map. **Every row is documentation, not observation** —
the right-hand column stays open until someone has the board in hand.

| Item | From pinout doc v7 (board rev2) | Physically confirmed |
|---|---|---|
| IceZero assembly/revision | TE0876-02, board rev2 | ☐ |
| FPGA top marking | `iCE40HX4K-TQ144` | ☐ |
| FPGA density: HX4K or HX8K | Marked HX4K (3520 LC). HX8K die inside (7680 LC), reached by targeting `--hx8k --package tq144:4k` | ☐ |
| FPGA package | 144-pin TQFP, 20 × 20 mm, 0.50 mm pitch, 107 I/O | ☐ |
| Oscillator marking/frequency | SiT8008AI-73-XXS-100.0000OE, 100 MHz, on pin 49 (`IOB_81_GBIN5`, a global buffer input) | ☐ |
| Selected PMOD connector | P1 — P2/P3/P4 held free for the M1 DAC bus | ☐ |
| Selected FPGA output pin | 139 (`IOT_217`) = `tx_symbol` | ☐ |
| Selected FPGA loopback input pin | 135 (`IOT_213`) = `tx_loopback` | ☐ |
| I/O-bank voltage | 3.3 V LVCMOS | ☐ |
| Pinout document revision | `iceZero-pinout-v5.pdf`, board rev2, doc v7 | ☐ |

Additional facts from the same document, all of which M0 now depends on:

| Resource | Pins |
|---|---|
| LEDs | LED1 #110, LED2 #93, LED3 #94 |
| Button | BTN #63 (`IOB_103_CBSEL0` — also a configuration-select pin, sampled at config time) |
| UART, J3 (**FTDI TTL-232R-3.3V only**) | TX #122 (FPGA out), RX #124 (FPGA in), CTS #119 (FPGA out), DTR #125 (ignore) |
| Configuration, via the Raspberry Pi header | CDONE #65, SDI #68, SDO #67, SCK #70, SS #71, CRESET_B #66 |
| PMOD signal pins, 8 each | P1 139,137,135,130 / 141,138,136,134 · P2 56,48,45,43 / 55,47,44,42 · P3 26,29,28,52 / 41,39,38,37 · P4 21,20,8,7 / 1,144,143,142 |

The bitstream is loaded by `icezprog`, which bitbangs the configuration pins from
the Raspberry Pi's GPIO. **A Raspberry Pi is a hard prerequisite** for anything
beyond simulation; the board is a Pi HAT and has no other documented programming
path.

Two cautions carried forward to bring-up:

- The J3 signal names above are read from the IceZero's perspective. A swapped
  TX/RX is the classic UART bring-up failure; confirm the direction with a scope
  or a loopback jumper before blaming the RTL.
- The PMOD **connector pin positions** (which physical pin of the 2×6 carries
  which FPGA pin) are inferred from the document's row/column layout. The FPGA
  pin numbers above are unambiguous and are what the `.pcf` uses, but check
  continuity with a meter before wiring anything to the connector.

Do not copy a constraint file for another iCE40 board without verifying every pin.

---

## Platform change: IceZero abandoned, Arty Z7 adopted (2026-09-07)

The IceZero TE0876-02 is **dead and out of the project**.

### What failed

| Finding | Evidence |
|---|---|
| 3.3 V rail dead | 300 mV at every PMOD 3.3 V pin |
| U8 (EP53A7HQI buck) failed | PVIN, AVIN and ENABLE all at 4.8 V, VS0/1/2 strapped, output 310 mV |
| 3.3 V rail hard-shorted | An external supply hit compliance at both 20 mA and 100 mA |

Two independent faults. Since U8 also feeds U10 (MCP1700) which makes the FPGA's
1.2 V core, the FPGA and the configuration flash have had no power at all since
the event — which is why the flash returned `00` to every JEDEC ID request and
CDONE never rose. **Nothing ever indicated the FPGA or the flash was itself
damaged**; they were simply never powered. That question is now moot.

### Root cause

A generic USB-serial cable was connected to **J3** with its **VCC wire
connected**, and the board was powered solely from that cable with the Raspberry
Pi detached. Two things were wrong:

1. The board's schematic and silkscreen both say **"FTDI TTL-232R-3V3 Only"**,
   and label J3 for that cable's colours (BLK / ORN / YLW / GRN). The cable used
   had white and green conductors — not that family — and generic USB-TTL cables
   commonly signal at 5 V. J3 places a 5 V pin directly beside FPGA I/O rated
   about 3.6 V absolute maximum.
2. Connecting a cable's VCC to a board that has its own supply is wrong
   regardless of the cable.

### A checker that could pass a dead wire

Found on the bench on 2026-09-07, and worth preserving because simulation could
not have found it.

With the pattern switches at `00` — constant zero — `prbs7_check` locked and
reported zero errors. An all-zero shift register satisfies the checker's
prediction recurrence trivially, since `0 = 0 XOR 0`. The consequence reaches
far past the test pattern: **a stuck-low loopback, an unseated jumper or a dead
output driver would all have reported "locked, zero errors"** — the one false
pass a bit-error counter must never give.

The guard added is exact rather than heuristic. The longest run of zeros in a
PRBS-7 sequence is six, so a seven-bit all-zero window cannot occur in a valid
stream and can only mean a dead line.

Simulation was structurally incapable of catching this: the generator cannot
emit all-zeros, because the seed is nonzero and the LFSR never enters that
state. Exposing it required driving the checker from something other than the
generator — which is what a person flipping two switches did, and what the
testbench now does deliberately.

### Rules adopted

- [ ] **Never connect a USB-serial cable's VCC** to a board that has its own
      power. GND, TX and RX only.
- [ ] **Verify the cable signals at 3.3 V** before it touches an FPGA pin. Wire
      colours are the cheapest tell: a genuine FTDI TTL-232R is
      black/brown/red/orange/yellow/green and nothing else.
- [ ] Prefer a connector that carries **no 5 V near 3.3 V logic** at all.

### Replacement: Digilent Arty Z7 (Zynq-7000)

Chosen for reasons that also remove the failure mode above: **USB-JTAG and
USB-UART are built in on one cable**, so there is no separate serial cable to
mis-wire and no 5 V pin next to an FPGA input.

What changes, and what does not:

| | Before (IceZero) | After (Arty Z7) |
|---|---|---|
| Device | iCE40HX4K-TQ144 | Zynq-7000 (XC7Z010 / XC7Z020) |
| Synthesis / P&R | yosys + nextpnr-ice40 | **Vivado 2024.2** |
| Constraints | `.pcf` | `.xdc` |
| Programming | `icezprog` over Raspberry Pi GPIO | Vivado hardware manager over USB-JTAG |
| Board clock | 100 MHz | **125 MHz** |
| Console / readout | FTDI cable on J3, or Pi header | Built-in USB-UART |
| **RTL** | — | **unchanged** |
| **Simulation** | — | **unchanged** (Verilator + Icarus) |

The RTL is portable because it contains no iCE40 primitives — plain
SystemVerilog throughout. It has been re-simulated at 125 MHz and passes
unmodified. All four symbol rates still divide the board clock exactly:

| Symbol rate | Clocks at 125 MHz |
|---:|---:|
| 1 ksym/s | 125,000 |
| 10 ksym/s | 12,500 |
| 100 ksym/s | 1,250 |
| 1 Msym/s | 125 |

So `tx_pattern_source`'s exact-divisor elaboration check still passes with only
`CLOCK_HZ` changed.

### Toolchain location

Vivado 2024.2 runs in a Docker container on the host **m75q (192.168.1.252)**,
with the Xilinx tree bind-mounted read-only and USB passed through. JTAG through
that container is already proven. Launcher and notes:
`/workspace/notes/home_lab/vivado-docker/`.

The IceZero board-facts table above is retained as a historical record. It is
no longer the target. An equivalent table for the Arty Z7 is written once the
board revision is confirmed and Digilent's master XDC is pulled in.


---

## 3. First-Milestone Architecture

```text
100 MHz board clock
        │
        v
┌────────────────────┐
│ Symbol tick divider│  1 k, 10 k, 100 k, 1 M symbols/s initially
└─────────┬──────────┘
          │ symbol_tick
          v
┌────────────────────┐
│ Pattern selector   │  0, 1, 1010..., PRBS-7
└─────────┬──────────┘
          v
┌────────────────────┐
│ Output register    │  changes only on clock edges
└─────────┬──────────┘
          │ FPGA_TX_SYMBOL
          v
┌────────────────────┐
│ Buffer/translator  │  hardware-disabled during FPGA configuration
└──────┬─────────┬───┘
       │         │
       │         └────────────→ scope or logic analyzer
       v
protected loopback input
       │
       v
┌────────────────────┐
│ PRBS checker       │
│ bit/error counters │
└────────────────────┘
```

### Recommended signal names

| Signal | Direction | Meaning |
|---|---|---|
| `clk_100m` | FPGA input | Board clock |
| `rst` | Internal/input | Synchronous reset |
| `pattern_sel[1:0]` | Internal/input | Constant 0, constant 1, alternating, PRBS-7 |
| `symbol_rate_sel` | Internal/input | Selects the initial test rate |
| `tx_enable` | Internal/input | Logical transmitter permission |
| `tx_symbol` | FPGA output | Registered binary symbol |
| `tx_oe_n` | FPGA output | Active-low external-buffer enable |
| `tx_loopback` | FPGA input | Protected return from the interface |
| `prbs_locked` | FPGA output/status | Checker synchronized to the expected sequence |
| `bit_count` | Status register | Number of checked symbols |
| `error_count` | Status register | Number of mismatches |

The eventual BPSK interpretation is:

```text
tx_symbol = 0 → request 0° RF phase
tx_symbol = 1 → request 180° RF phase
```

At this stage, `tx_symbol` is only a logic-level command. It is not an RF waveform.

---

## 4. Why the Output Must Be Registered

Combinational decoding can briefly glitch when several internal bits change at slightly different times. Driving the final pin from a flip-flop gives a single, clock-defined transition and makes timing analysis meaningful.

The iCE40 PIO includes an optional output register before the sysIO buffer; the Lattice data sheet documents this path. A normal fabric register placed close to the I/O can also be used, but the place-and-route timing report should confirm the result.

Rules:

- [ ] `tx_symbol` is assigned only in a clocked process.
- [ ] Pattern-selection changes are registered or applied while transmission is disabled.
- [ ] The symbol rate uses a clock-enable pulse; do not create a new fabric clock with ordinary logic.
- [ ] No asynchronous data path directly reaches `tx_symbol`.
- [ ] Reset produces a documented idle symbol.
- [ ] RF enable remains separate from the symbol value.

---

## 5. Minimal FPGA Functions

### 5.1 Symbol tick

For the first experiment, use an integer divider of the 100 MHz board clock:

```text
cycles_per_symbol = 100,000,000 / symbol_rate
```

Initial exact-divisor test rates:

| Symbol rate | Clock cycles per symbol |
|---:|---:|
| 1 ksym/s | 100,000 |
| 10 ksym/s | 10,000 |
| 100 ksym/s | 1,000 |
| 1 Msym/s | 100 |

Later, use a phase accumulator when arbitrary fractional symbol rates are needed.

### 5.2 Pattern selector

| `pattern_sel` | Output |
|---:|---|
| `00` | Constant zero |
| `01` | Constant one |
| `10` | Alternating `1010...` |
| `11` | PRBS-7 |

Constant patterns prove DC logic levels. The alternating pattern makes timing and symbol rate easy to measure. PRBS exercises transitions and enables automated error counting.

### 5.3 PRBS-7 convention

Use the polynomial:

```text
x^7 + x^6 + 1
```

For one explicit shift convention:

```text
new_bit = state[6] XOR state[5]
state   = {state[5:0], new_bit}
output  = state[6]
```

Requirements:

- [ ] Seed the state with a nonzero value, initially `7'b1111111`.
- [ ] Advance exactly once per `symbol_tick`.
- [ ] Document bit order, inversion, seed, and whether output is taken before or after the shift.
- [ ] Use the identical convention in the generator, checker, and software golden model.
- [ ] Confirm a 127-bit repeat period in simulation.

The representation `7'h41` used by parameterized libraries corresponds to PRBS-7 under their documented polynomial convention. Do not copy only the hexadecimal value without also matching that library's shift direction and output convention.

### 5.4 Output-enable behavior

Use a separate output-enable signal:

```text
not configured or reset or fault → interface disabled
configured and commanded         → interface enabled
```

The external buffer must have a resistor-defined disabled state during FPGA configuration. Firmware alone cannot guarantee the state of a pin before configuration completes.

---

## 6. Minimal Reference RTL

This is intentionally small teaching code, not a complete transmitter. Pin constraints, reset synchronization, status access, and hardware-specific I/O details remain to be added.

```systemverilog
module tx_pattern_source #(
    parameter int unsigned CLOCK_HZ    = 100_000_000,
    parameter int unsigned SYMBOL_RATE = 1_000
) (
    input  logic       clk,
    input  logic       rst,
    input  logic       tx_enable,
    input  logic [1:0] pattern_sel,
    output logic       tx_symbol,
    output logic       tx_oe_n
);
    localparam int unsigned DIVISOR = CLOCK_HZ / SYMBOL_RATE;
    localparam int unsigned CW = (DIVISOR <= 1) ? 1 : $clog2(DIVISOR);

    logic [CW-1:0] div_count;
    logic          symbol_tick;
    logic          alternating;
    logic [6:0]    prbs7 = 7'h7f;
    logic          selected_symbol;

    always_comb begin
        unique case (pattern_sel)
            2'b00: selected_symbol = 1'b0;
            2'b01: selected_symbol = 1'b1;
            2'b10: selected_symbol = alternating;
            2'b11: selected_symbol = prbs7[6];
        endcase
    end

    always_ff @(posedge clk) begin
        symbol_tick <= 1'b0;

        if (rst) begin
            div_count   <= '0;
            alternating <= 1'b0;
            prbs7       <= 7'h7f;
            tx_symbol   <= 1'b0;
            tx_oe_n     <= 1'b1;
        end else begin
            tx_oe_n <= ~tx_enable;

            if (div_count == DIVISOR-1) begin
                div_count   <= '0;
                symbol_tick <= 1'b1;
                alternating <= ~alternating;
                prbs7       <= {prbs7[5:0], prbs7[6] ^ prbs7[5]};
                tx_symbol   <= selected_symbol;
            end else begin
                div_count <= div_count + 1'b1;
            end

            if (!tx_enable)
                tx_symbol <= 1'b0;
        end
    end

    initial begin
        if (SYMBOL_RATE == 0 || CLOCK_HZ % SYMBOL_RATE != 0)
            $error("First bring-up requires an exact integer symbol-rate divisor");
    end
endmodule
```

Before hardware use, simulation must define whether the first output bit occurs from the initial PRBS state or after the first shift. The checker must use the same choice.

---

## 7. Logic Buffer and Level Interface

There are three distinct electrical cases.

### Case A: 3.3 V FPGA to 3.3 V high-impedance logic input

A single-channel three-state buffer such as the **SN74LVC1G125 powered at 3.3 V** is a reasonable prototype candidate. It has an active-low output enable and partial-power-down/back-drive protection. Place a pull-up on `/OE` so the output remains high impedance during FPGA configuration.

Reference: [TI SN74LVC1G125 data sheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf).

This part can provide buffering and down-translation when powered at the lower voltage. It should not be assumed to provide valid 3.3-to-5 V up-translation merely because its inputs tolerate 5.5 V.

### Case B: Different input and output logic voltages

A fixed-direction dual-rail translator such as the **TXU0101** is a prototype candidate when the FPGA voltage and destination logic voltage differ. Its two rails cover 1.1 V through 5.5 V, it has an output-enable input, and it includes defined input pulldowns and power-sequencing behavior.

Reference: [TI TXU0101 data sheet](https://www.ti.com/lit/ds/symlink/txu0101.pdf).

Do not select the translator until the destination's VIH, VIL, input current, allowable overshoot, and required switching rate are known.

### Case C: Mixer, analog modulator, 50-ohm input, or bipolar control

Neither logic part above should automatically drive this load. The final interface may instead need:

- A differential or complementary driver.
- A controlled bipolar voltage or current.
- AC coupling and bias generation.
- An RF transformer or balun.
- A fast analog switch or purpose-built biphase modulator.
- A resistive pad or impedance-matching network.

Record the eventual modulator requirements:

| Requirement | Value/source |
|---|---|
| Input type | |
| Input impedance | |
| Required low/high or positive/negative voltage | |
| Required drive current | |
| Maximum input voltage/current | |
| Input bandwidth | |
| Common-mode requirement | |
| Differential/complementary requirement | |
| DC coupling permitted? | |

---

## 8. Prototype Interface Schematic Requirements

```text
3.3 V FPGA_TX_SYMBOL ─────→ A   buffer/translator   Y ── Rseries ──→ test output

3.3 V FPGA_TX_OE_N ───────→ /OE
                                  │
                             local bypass
                                  │
                                 GND

/OE ── pull-up ── buffer output-side supply
```

Include:

- [ ] 0.1 µF bypass capacitor at each supply pin, placed close to the device.
- [ ] Optional bulk capacitor footprint near the interface connector.
- [ ] `/OE` pull-up that disables the output while the FPGA is unconfigured.
- [ ] Series-resistor footprint next to the driver; initially populate approximately 22–100 ohms only after considering trace/cable/load behavior.
- [ ] Test points before and after the buffer.
- [ ] Ground pins adjacent to signal pins at the connector.
- [ ] Clearly labeled supply-voltage test points.
- [ ] A protected loopback path.
- [ ] Optional shunt-resistor and AC-coupling footprints left unpopulated.

Series resistance is a signal-integrity tuning element, not a universal 50-ohm termination. TI's logic design guide discusses source-series and other termination methods: [Design Considerations for Logic Products](https://www.ti.com/lit/an/sdya002/sdya002.pdf).

### Loopback warning

If the output is translated above the FPGA's I/O voltage, do not return it directly to an FPGA pin. Use one of these instead:

- Loop back from the buffer input.
- Add a second down-translator.
- Use a resistor network only after validating thresholds, current, and transient limits.

---

## 9. Test Sequence

### Phase 0: Toolchain and clock

- [ ] Build and load a minimal LED counter.
- [ ] Confirm the 100 MHz clock assumption against the board marking.
- [ ] Run place-and-route timing analysis.
- [ ] Save tool versions and build command.

### Phase 1: Direct FPGA output

Connect only a high-impedance logic analyzer or properly compensated oscilloscope probe.

- [ ] Constant zero produces the expected low voltage.
- [ ] Constant one produces the expected high voltage.
- [ ] Alternating mode produces half the symbol-rate frequency.
- [ ] PRBS-7 repeats every 127 symbols in simulation/capture.
- [ ] `tx_symbol` remains at the documented idle state when disabled.
- [ ] No narrow glitches are visible during steady operation or pattern changes.

### Phase 2: Buffered output

- [ ] Confirm the buffer output is high impedance while the FPGA is unconfigured.
- [ ] Confirm `/OE` polarity.
- [ ] Measure both sides of the buffer.
- [ ] Measure propagation delay if the instruments permit.
- [ ] Check overshoot, undershoot, ringing, rise time, and fall time.
- [ ] Tune the source-series resistor if necessary.

### Phase 3: FPGA loopback and checker

- [ ] Return the signal through a voltage-safe path.
- [ ] Synchronize the returned asynchronous signal before general control use.
- [ ] For the PRBS data path, define the expected latency explicitly.
- [ ] Establish checker lock before incrementing `error_count`.
- [ ] Verify deliberate inversion produces errors.
- [ ] Verify a forced missing/extra bit produces loss of lock or errors.
- [ ] Run at 1 ksym/s for visual inspection.
- [ ] Repeat at 10 ksym/s, 100 ksym/s, and 1 Msym/s.
- [ ] At the intended test rate, check at least 1,000,000 symbols with zero errors.

### Phase 4: Packet source

Only after PRBS loopback is reliable, add:

```text
preamble → sync word → version/flags → payload length → payload → CRC
```

Do not add FEC, pulse shaping, or host streaming in the first milestone.

---

## 10. Measurement Worksheet

### Logic-level and waveform results

| Pattern/rate | FPGA-side Vlow/Vhigh | Buffer-side Vlow/Vhigh | Rise/fall time | Overshoot/undershoot | Notes |
|---|---|---|---|---|---|
| Constant 0 | | | | | |
| Constant 1 | | | | | |
| Alternating, 1 ksym/s | | | | | |
| Alternating, 10 ksym/s | | | | | |
| Alternating, 100 ksym/s | | | | | |
| Alternating, 1 Msym/s | | | | | |
| PRBS-7, 1 Msym/s | | | | | |

### Loopback results

| Symbol rate | Run time | Checked bits | Errors | Lock losses | Pass/fail |
|---:|---:|---:|---:|---:|---|
| 1 ksym/s | | | | | |
| 10 ksym/s | | | | | |
| 100 ksym/s | | | | | |
| 1 Msym/s | | | | | |
| Other: | | | | | |

### Startup behavior

| Event | Output behavior | Expected? | Notes |
|---|---|---|---|
| Interface powered, FPGA unconfigured | | | |
| FPGA configuration begins | | | |
| Configuration completes | | | |
| FPGA reset asserted | | | |
| FPGA reset released | | | |
| `tx_enable` asserted | | | |
| `tx_enable` removed | | | |
| FPGA power removed first | | | |
| Interface power removed first | | | |

---

## 11. Acceptance Criteria for Milestone One

**Amended 2026-09-06.** Three criteria in the original list assumed an external
SN74LVC1G125 buffer driving a destination logic input. The payload trade study
selected the DAC low-IF architecture, in which `tx_symbol` never leaves the
FPGA — it feeds the symbol mapper and NCO internally. There is no destination
to meet thresholds at and no buffered edge to inspect, so those criteria could
not be satisfied as written and are replaced by the equivalent measurements at
the FPGA pin. The buffer criteria are retained below as dormant, and become
live again only if the deferred phase-modulator architecture is revived.

### Simulation — met

- [x] RTL simulation confirms symbol timing and the 127-bit PRBS-7 period.
- [x] The output is registered and changes only at symbol boundaries.
- [x] Loopback checks at least 1,000,000 symbols at the selected target rate with zero errors.
- [x] The design recovers predictably after reset and disable/enable cycles.

### Hardware — Arty Z7-20, 2026-09-07

- [x] Board, device, clock and pin constraints recorded and physically
      confirmed — Arty Z7-20, XC7Z020-1CLG400C, 125 MHz, pins taken verbatim
      from Digilent's master XDC. Builds, programs, and runs.
- [x] Place-and-route completes and timing is met — **WNS +2.903 ns, WHS
      +0.122 ns** against the 8 ns clock. 112 LUTs and 200 registers, 0.2% of
      the part.
- [x] The hardware loopback checks at least 1,000,000 symbols with zero errors
      — **60,000,000 symbols in 60 s at 1 Msym/s, zero errors, zero lock
      losses.**
- [ ] Constant zero and constant one measure at the pin as valid 3.3 V LVCMOS
      levels. *(scope capture outstanding)*
- [ ] Alternating output frequency is the symbol rate divided by two, at every
      `rate_sel`. *(scope capture outstanding)*
- [ ] Edges show no threshold-crossing glitches and overshoot stays inside the
      device's tolerance. *(scope capture outstanding)*
- [ ] Scope captures committed under `measurements/m0_symbol_engine/`.

#### On trusting the sticky LED

The original criterion demanded the symbol count be *read back*, "not merely
inferred from an LED that failed to light" — and what was actually run is a
sticky error latch observed over a measured minute. That is defensible here,
for two specific reasons, and it is worth being precise about why rather than
quietly relaxing the bar:

1. **The count is computed, not estimated.** The symbol rate is 125 MHz divided
   by exactly 125, from a crystal, so 60 s is 60,000,000 symbols and not an
   approximation.
2. **The negative case was demonstrated.** Pulling the loopback jumper makes
   `led[2]` go dark and `led[3]` latch. An indicator that has never been seen
   to trip is not evidence; one that has been made to trip on demand is. That
   test is what converts a dark LED from an absence of information into a
   measurement.

The remaining gap is real but narrow: `bit_count` and `error_count` are still
not readable, so a *partial* failure late in a long run cannot be quantified,
only detected. Closing that is the first job of the UART readout.

### Dormant — revive only with the phase-modulator architecture

- [ ] The external buffer output remains disabled during FPGA configuration and reset.
- [ ] Constant levels meet the destination logic thresholds with margin.
- [ ] Buffered edges have no threshold-crossing glitches or damaging overshoot.

Passing this milestone proves the digital symbol path. It does **not** yet prove RF spectral purity, BPSK modulation quality, occupied bandwidth, EVM, or receiver performance.

---

## 12. Existing Implementations and What to Reuse

Review licenses before copying code, and pin any dependency to a specific commit.

### PRBS, LFSR, and CRC

- [Taxi HDL](https://github.com/fpganinja/taxi) is the maintained successor to several Alex Forencich Verilog libraries. It includes parameterized PRBS generators/checkers, LFSR/CRC modules, FIFOs, UART components, stream infrastructure, and cocotb/Verilator tests.
- [Taxi PRBS generator source](https://github.com/fpganinja/taxi/blob/master/src/lfsr/rtl/taxi_lfsr_prbs_gen.sv) shows explicit polynomial, shift style, inversion, data width, seed, and enable handling.
- [Older `verilog-lfsr` repository](https://github.com/alexforencich/verilog-lfsr) contains Verilog-2001 PRBS generator/checker and CRC wrappers with cocotb tests. Its author now marks it deprecated in favor of Taxi, but it remains a useful reference and has a different license from Taxi.
- [Analog Devices AD9361 PN monitor](https://github.com/analogdevicesinc/hdl/blob/main/library/axi_ad9361/axi_ad9361_rx_pnmon.v) is a production-oriented example of PRBS checking around a converter interface. It is more complex than this milestone and should be studied rather than dropped in unchanged.

Recommendation: write and verify the tiny local PRBS-7 for milestone one. Reevaluate Taxi when parallel PRBS, configurable CRC, stream FIFOs, or a larger data plane is required.

### UART and host data

- [ZipCPU `wbuart32`](https://github.com/ZipCPU/wbuart32) provides Verilog UART transmit/receive modules, FIFOs, simulation support, and formal verification. It is useful later if source data enters through UART. Its GPL licensing must be evaluated before incorporation.

### Streaming and FIFOs

- [Taxi HDL](https://github.com/fpganinja/taxi) provides current stream, FIFO, synchronization, and peripheral components.
- [Older `verilog-axis`](https://github.com/alexforencich/verilog-axis) documents frame-aware FIFOs, asynchronous FIFOs, width adapters, rate limiters, and test infrastructure. Prefer its maintained successor for a new design.

For the small iCE40, do not introduce AXI Stream merely for a one-bit test pattern. A simple `valid/ready/data` byte interface is sufficient until the design actually needs multiple producers, backpressure, or clock-domain boundaries.

### iCE40 examples and toolchain

- [Project IceStorm](https://github.com/YosysHQ/icestorm) documents the open iCE40 bitstream flow and includes board examples.
- [Open iCE40 HX8K example projects](https://github.com/nesl/ice40_examples) show small build trees, pin-constraint files, counters, UART transmission, and simulation-oriented exercises. These target different boards, so use their structure rather than their pin assignments.

---

## 13. Suggested Repository Layout

```text
hardware/payload_exp_sband_tx/
├── fpga_link_processor_logic_interface_first_bringup.md
├── fpga/
│   ├── rtl/
│   │   ├── tx_pattern_source.sv
│   │   ├── prbs7_gen.sv
│   │   └── prbs7_check.sv
│   ├── sim/
│   │   ├── tb_tx_pattern_source.sv
│   │   └── prbs7_golden.py
│   ├── constraints/
│   │   └── icezero_<verified-revision>.pcf
│   ├── Makefile
│   └── README.md
└── measurements/
    └── fpga_logic_interface/
        ├── README.md
        ├── captures/
        └── raw_data/
```

Do not create the hardware-specific constraint filename until the board revision and pin mapping are verified.

---

## 14. Next Review Package

Bring these results to the next design review:

- [ ] IceZero revision and FPGA top-marking photo.
- [ ] Selected PMOD pins and verified constraint entries.
- [ ] RTL and simulator output confirming PRBS period and bit order.
- [ ] Scope capture of constant high and low.
- [ ] Scope capture of the alternating pattern.
- [ ] Scope capture of PRBS before and after the buffer.
- [ ] Power-up/configuration capture showing the buffer remains disabled.
- [ ] Loopback bit count, error count, and lock-loss count.
- [ ] Buffer/translator part number and populated series resistor.
- [ ] Target RF modulator or mixer input requirements.

Those results will determine whether the interface can connect directly to the selected RF modulator or needs a dedicated analog/bipolar driver stage.
