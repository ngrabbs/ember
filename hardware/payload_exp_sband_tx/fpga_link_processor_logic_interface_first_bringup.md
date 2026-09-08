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

## 2. Board Facts

**Target board: Digilent Arty Z7-20, XC7Z020-1CLG400C.** Every row below is
confirmed on the board in hand, not read off a datasheet.

| Item | Value |
|---|---|
| FPGA | XC7Z020-1CLG400C (Zynq-7000, dual-core ARM PS + Artix-7 class PL) |
| Board clock | 125 MHz on `H16`, LVCMOS33 — an 8.000 ns `create_clock` |
| I/O standard | 3.3 V LVCMOS on the Pmods and the ChipKit headers |
| Programming | USB-JTAG, Vivado hardware manager. **Volatile** — any power cycle drops the bitstream |
| Constraints | `.xdc`, derived verbatim from Digilent's `Arty-Z7-20-Master.xdc` |
| PS usage | **None.** This is a PL-only design; the PS is not instantiated |

Sources:

- [Digilent Arty Z7 reference manual](https://digilent.com/reference/programmable-logic/arty-z7/reference-manual)
- [Digilent master XDC files](https://github.com/Digilent/digilent-xdc) — `Arty-Z7-20-Master.xdc`

### Pin assignments in use

Taken from `fpga/constraints/arty_z7_20.xdc`, which is the file of record.

| Resource | Pins |
|---|---|
| Clock | `clk` H16 |
| Switches | `sw[0]` M20, `sw[1]` M19 |
| Buttons | `btn[0]` D19, `btn[1]` D20, `btn[2]` L20, `btn[3]` L19 |
| LEDs | `led[0]` R14, `led[1]` P14, `led[2]` N16, `led[3]` M14 |
| Pmod JA — bench interface | `tx_symbol` Y18, `symbol_tick` Y19, `tx_oe_n` Y16, `loopback` Y17 |
| Pmod JB — console | `uart_tx` W14, `uart_rx` Y14 |
| Pmod JB/JA — AD9910 | `cs_n` T11, `sclk` T10, `sdio` V16, `sdo` W16, `io_update` V12, `master_reset` W13, `pf0` U18, `pf1` U19, `pf2` W18, `pll_lock` W19 |
| ChipKit `ck_io0` | `dds_refclk` T14 — 125 MHz / 10 = 12.5 MHz |

Three cautions that carry into every bench session:

- **The console is not on the programming cable.** The board's USB-UART is wired
  to the PS, and no PS is instantiated, so the console runs on Pmod JB through
  an external 3.3 V USB-serial cable. Connect **GND, TX and RX only**.
- **A swapped TX/RX is the classic UART bring-up failure.** The names above are
  from the FPGA's perspective. Confirm direction with a loopback jumper or a
  scope before blaming the RTL. This has already cost time once, when the cable
  was on Pmod JA instead of JB.
- **JTAG configuration is volatile.** If the board loses power, the bitstream is
  gone and every symptom looks like a logic bug. `make program` first, then
  `make sanity`, then debug.

### The symbol rates still divide exactly

The design moved from a 100 MHz board to this one, and the exact-divisor
elaboration check in `tx_pattern_source` holds with only `CLOCK_HZ` changed:

| Symbol rate | Clocks at 125 MHz |
|---:|---:|
| 1 ksym/s | 125,000 |
| 10 ksym/s | 12,500 |
| 100 ksym/s | 1,250 |
| 1 Msym/s | 125 |

The RTL is portable because it instantiates no vendor primitives — plain
SystemVerilog throughout.

### Toolchain location

Vivado 2024.2 runs in a Docker container on the host **m75q (192.168.1.252)**,
with the Xilinx tree bind-mounted read-only and USB passed through for JTAG.
Sources are pushed with `make bitstream`; the bitstream and reports come back.
Launcher and notes: `/workspace/notes/home_lab/vivado-docker/`.

---

## 2a. A Checker That Could Pass a Dead Wire

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

The same shape recurs elsewhere and is worth watching for: `make sanity` was
also reporting a pass for "zero bit errors over zero symbols". Zero errors out
of nothing measured is not a pass.

---

## 2b. Bench Wiring Rules

These are not general cautions. This payload has already destroyed one FPGA
board, and the cause was a single wire.

- [ ] **Never connect a USB-serial cable's VCC** to a board that has its own
      power. GND, TX and RX only. Back-feeding a powered board through a VCC pin
      kills its regulator — which is exactly what happened here, with the board
      drawing its entire supply through a serial cable's 5 V conductor.
- [ ] **Verify the cable signals at 3.3 V** before it touches an FPGA pin. Check
      the datasheet, not the wire colours. The Adafruit 954 signals at 3.3 V
      despite carrying a 5 V power wire, so colour alone proves nothing.
- [ ] **Ground is the only connection to a separately powered board.** The
      AD9910 module has its own 5 V barrel jack. GND between the two boards and
      nothing else — no 5 V, no 3.3 V, in either direction.
- [ ] **No antenna at any stage.** Everything cabled, attenuated and terminated.

---

## 3. First-Milestone Architecture

```text
125 MHz board clock
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

The 7-series I/O block includes an output flip-flop (`OFDRE`) inside the IOB itself, which Vivado will infer and pack automatically when the driving register has no other fanout; `set_property IOB TRUE` forces it. A normal fabric register placed close to the I/O also works, but the place-and-route timing report should confirm the result either way.

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

For the first experiment, use an integer divider of the 125 MHz board clock:

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
- [x] Board clock confirmed: 125 MHz on `H16`, per Digilent's master XDC.
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
- [x] The hardware loopback checks at least 1,000,000 symbols with zero errors,
      **and the count is read back and recorded** — 62,049,047 symbols, zero
      errors, zero lock losses, read over the UART console rather than inferred.
      Measured symbol rate 1,000,000 sym/s, 0.0000% from nominal. BER < 4.8e-8
      at 95% confidence.
- [x] Constant zero and constant one measure at the pin as valid 3.3 V LVCMOS
      levels — **0.063 V and 3.338 V**.
- [x] Alternating output frequency is the symbol rate divided by two, at every
      `rate_sel` — **0.000% error at all four rates**.
- [x] The PRBS-7 stream captured at the pin decodes and matches the golden
      model — phase 19, exact.
- [x] `symbol_tick` measures **8.000 ns**, one 125 MHz clock.
- [~] Edges show no threshold-crossing glitches and overshoot stays inside the
      device's tolerance. **Partial**: no glitches seen, but the edge and
      overshoot figures were taken on a standard probe ground lead and are
      measurement-limited. Re-measure with a short ground spring before
      accepting the overshoot number.
- [x] Scope captures committed under `measurements/m0_symbol_engine/captures/`.

#### On trusting the sticky LED — superseded

An earlier revision of this document argued at some length that observing a
sticky error latch over a measured minute was an acceptable substitute for
reading the count, on the grounds that the rate is exact and the negative case
had been demonstrated by pulling the jumper.

That argument is now moot rather than merely weakened: the UART console reads
`bit_count`, `error_count` and `loss_count` directly, and the run above is a
counted one. The reasoning is left here only as a record that the criterion was
softened before it was met, which is worth noticing when the next criterion
starts to look inconvenient.

The jumper-pull test remains valuable and should stay in the procedure — an
indicator never seen to trip is not evidence, whatever else is being measured.

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

For a design this small, do not introduce AXI Stream merely for a one-bit test pattern. A simple `valid/ready/data` byte interface is sufficient until the design actually needs multiple producers, backpressure, or clock-domain boundaries.

### Board support and toolchain

- [Digilent digilent-xdc](https://github.com/Digilent/digilent-xdc) is the source of record for Arty Z7 pin constraints. Copy `Arty-Z7-20-Master.xdc` and uncomment what the design uses; do not transcribe pin names by hand.
- [Digilent Arty Z7 reference manual](https://digilent.com/reference/programmable-logic/arty-z7/reference-manual) documents the connectors, clocking, and the Pmod / ChipKit pin mapping.
- The build here runs Vivado in non-project mode from `fpga/vivado/build.tcl`, so the whole flow is a script in git rather than a `.xpr` no one can diff.

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
│   │   └── arty_z7_20.xdc
│   ├── vivado/
│   │   └── build.tcl
│   ├── Makefile
│   └── README.md
└── measurements/
    └── fpga_logic_interface/
        ├── README.md
        ├── captures/
        └── raw_data/
```

The constraint filename names the exact board variant, because the Z7-10 and Z7-20 share a footprint but not a part number.

---

## 14. Next Review Package

Bring these results to the next design review:

- [x] Board variant confirmed and constraint file derived from the vendor master XDC.
- [x] Selected Pmod pins and verified constraint entries.
- [ ] RTL and simulator output confirming PRBS period and bit order.
- [ ] Scope capture of constant high and low.
- [ ] Scope capture of the alternating pattern.
- [ ] Scope capture of PRBS before and after the buffer.
- [ ] Power-up/configuration capture showing the buffer remains disabled.
- [ ] Loopback bit count, error count, and lock-loss count.
- [ ] Buffer/translator part number and populated series resistor.
- [ ] Target RF modulator or mixer input requirements.

Those results will determine whether the interface can connect directly to the selected RF modulator or needs a dedicated analog/bipolar driver stage.
