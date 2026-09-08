# Experimental S-Band BPSK Transmitter

**Status:** active bench experiment · architecture decided 2026-09-05
· see [`sband_payload_architecture_trade_study.md`](sband_payload_architecture_trade_study.md)

An FPGA-generated BPSK transmitter built to be understood, probed, and measured
on a bench. It is an experimental payload concept for EMBER, not part of the
mission-critical link. The reliable radio is and remains the UHF comms board in
[`../comms/`](../comms/).

---

## Scope

EMBER is a senior capstone project. The spacecraft is built toward an
**engineering model** — it will not fly, and no part of this payload is being
qualified for flight. If an instructor later asks what would have to change for
a flight model, that is answered as a **documentation exercise**, not a design
change. Nothing in this directory should be read as a flight claim.

Within that scope, the value of this payload is concentrated in one place:

> Generate real data, push it through an FPGA, and produce a modulated waveform
> you can put a probe on — framing, symbol timing, symbol mapping, and carrier
> generation implemented in HDL and then measured with a scope, a logic
> analyzer, and an SDR.

The S-band RF front end — mixer, filters, driver, PA, antenna — is the *second*
half of that story and is explicitly **not** on the critical path. The digital
chain is designed to terminate in a signal that an RF front end could accept, so
that the RF work can be added later without redesigning anything upstream.

### What this is

- A digital modulation teaching and measurement exercise with real hardware.
- A reusable FPGA link processor: framing, CRC, scrambling, PRBS, symbol timing.
- A signal chain that ends at an oscilloscope, logic analyzer, SDR, or 50 Ω load.
- A written engineering record of what was built, measured, and decided.

### What this is not

- Not the mission radio.
- Not flight hardware, and not on a path to flight qualification.
- Not an over-the-air transmitter. **Nothing here radiates.** Every test is
  cabled, attenuated, and terminated. There is no antenna in any configuration
  of this payload, at any stage, which removes licensing and coordination from
  the problem entirely.
- Not currently a PCB. First results come from an Arty Z7-20, a breadboard
  interconnect, and an AD9910 DDS module.

---

## Selected architecture

FPGA-generated symbols driving an **AD9910 DDS in profile-switched BPSK**. The
FPGA produces the symbol stream; the DDS holds two profiles at the same
frequency 180° apart and one pin selects between them, so the carrier flips
phase per symbol. The modulated carrier comes out of a coaxial connector at a
real RF frequency.

```text
┌───────────────────────── THE DELIVERABLE ─────────────────────────┐
│                                                                   │
│   host / test vectors / packet ROM                                │
│            │  bytes                                               │
│            v                                                      │
│   ┌────────────────────┐                                          │
│   │ FPGA link          │  framing · CRC · scrambler · PRBS        │
│   │ processor          │  symbol timing · BPSK symbol mapping     │
│   └────────┬───────────┘                                          │
│            │  tx_symbol — ONE PIN                                 │
│            v                                                      │
│   ┌────────────────────┐     ┌──────────────────────────┐        │
│   │ AD9910 PROFILE[0]  │ <───│ ad9910_ctrl + spi_master │        │
│   │ 0 → profile 0, 0°  │     │ CFR3 · profiles · IOUP   │        │
│   │ 1 → profile 1,180° │     └──────────────────────────┘        │
│   └────────┬───────────┘                                          │
│            │  1 GSPS DDS, 14-bit DAC, up to ~400 MHz              │
│            v                                                      │
│   oscilloscope · SDR · spectrum analyser · 50 Ω termination       │
└───────────────────────────────────────────────────────────────────┘
             │
             │  later, only if time allows
             v
   mixer → 2.4 GHz BPF → attenuator → SDR / dummy load
   (the AD9910 reaches ~400 MHz; S-band still needs upconversion)
```

**Superseded 2026-09-08.** This was previously "FPGA-generated low-IF BPSK into
a parallel DAC", with a DAC902 fed 12-bit samples from an NCO in the FPGA. The
converter actually on hand turned out to be an **AD9910 DDS**, not the DAC902
the order history suggested. See the trade study for what that changes, and what
it costs: the DDS removes the NCO, sine table and DAC-formatter work that the
trade study valued as HDL content, and replaces it with SPI control of a real RF
part. The symbol engine — the part M0 built — is unchanged and feeds the DDS
directly.

---

## Frequency and rate plan

The AD9910 runs at a 1 GHz system clock and its frequency is a 32-bit tuning
word, so the carrier is set in software rather than by a sample-rate plan:

```text
FTW = round(f_out × 2³² / SYSCLK)        SYSCLK = 1 GHz
```

| Reference | N (CFR3) | SYSCLK | Console |
|---|---:|---:|---|
| module's own 40 MHz | 25 | 1 GHz | `c0538C132` |
| FPGA `ck_io0`, 12.5 MHz | 80 | 1 GHz | `c0538C1A0` |

Carrier choices for the bench:

| Carrier | FTW | Notes |
|---:|---|---|
| 1 MHz | `0x00418937` | trivially visible on any scope |
| 10 MHz | `0x028F5C29` | the default; comfortable on a 200 MHz scope |
| 100 MHz | `0x1999999A` | a realistic IF |
| ~400 MHz | — | the AD9910's practical ceiling |

Symbol rates come from the FPGA and are unchanged from M0 — 1 k, 10 k, 100 k
and 1 Msym/s, each an exact divisor of the 125 MHz board clock.

---

## Milestones

Renumbered 2026-09-08 for the DDS architecture. **BPSK now arrives at M2
instead of M3, and with far less RTL** — the DDS supplies the carrier and the
phase switch that the DAC path would have built in the FPGA.

| ID | Milestone | Gate |
|---|---|---|
| **M0** ✅ | FPGA link processor: symbol timing, pattern selector, PRBS-7, registered output | **Met.** 62,049,047 symbols, zero errors; PRBS decoded from the pin against the golden model; `symbol_tick` measured at 8.000 ns |
| **M1** | AD9910 bring-up: SPI, PLL lock, a stable CW tone | `PLL_LOCK` asserted and a measured tone at the programmed frequency out of the SMA |
| **M2** | **BPSK** — `tx_symbol` drives `PROFILE[0]` | Visible 180° carrier phase reversals at symbol boundaries, at a known symbol rate |
| **M3** | Characterisation | Occupied bandwidth against symbol rate; spectrum on an SDR or analyser; carrier-frequency error |
| **M4** | Beyond BPSK | QPSK via profiles 0–3, or amplitude shaping via the ASF and OSK path |
| **M5** | *(optional)* S-band | Mixer to 2.4 GHz, image and LO leakage characterised, into a dummy load |

M2 is the milestone that matters. Seeing the carrier reverse phase on a scope,
driven by the FPGA's own PRBS-7, is the proof that this is a modulator and not a
signal generator.

**M0 is verified in simulation** — Verilator-lint clean, both testbenches
passing, and the gate met at 1,000,000 symbols with zero errors. What remains
of M0 is the hardware half: constraints, a bitstream, and the captures. See
[`fpga/README.md`](fpga/README.md) for results and the toolchain of record.

> **Platform change, 2026-09-07.** The IceZero is dead — a failed buck regulator
> and a hard short on its 3.3 V rail, caused by a generic USB-serial cable
> connected to J3 with its VCC wire attached. The payload moves to a **Digilent
> Arty Z7**, which brings USB-JTAG and USB-UART on one cable and removes that
> failure mode entirely. The RTL and the whole simulation flow are unaffected
> and already re-verified at the Arty's 125 MHz. Synthesis moves from
> yosys/nextpnr to **Vivado 2024.2**. Full record in the
> [bring-up document](fpga_link_processor_logic_interface_first_bringup.md).

M3 is the milestone that matters. Seeing the carrier flip phase on a scope is
the proof that the FPGA is generating its own BPSK.

---

## Documents

| Document | Status | Covers |
|---|---|---|
| [`sband_payload_architecture_trade_study.md`](sband_payload_architecture_trade_study.md) | **Current** — decision record | Architecture options, selection, consequences, risks |
| [`fpga_link_processor_logic_interface_first_bringup.md`](fpga_link_processor_logic_interface_first_bringup.md) | **Current** for M0, amended above | Symbol engine, PRBS-7 convention, registered output, buffer/level interface, test sequence, worksheets |
| [`mini_totem_bpsk_if_to_sband_plan.md`](mini_totem_bpsk_if_to_sband_plan.md) | **Reference** — frequency plan superseded | Overall narrative, bring-up phases, HDL module list, risks. Its 50 MHz IF / 2350 MHz LO plan is replaced by the table above |
| [`sband_experimental_tx_rf_block_diagram.drawio`](sband_experimental_tx_rf_block_diagram.drawio) | **Current** for the optional RF stage | Selected architecture drawn out, including the deferred RF chain and LO |
| [`sband_direct_bpsk_rf_block_diagram.drawio`](sband_direct_bpsk_rf_block_diagram.drawio) | **Deferred** — not selected | The 1-bit phase-modulator alternative, retained as the future RF path |
| [`tektronix_7l13_a20_2p2ghz_oscillator_characterization.md`](tektronix_7l13_a20_2p2ghz_oscillator_characterization.md) | **Current**, off the critical path | Bench characterization of a surplus 2.2 GHz oscillator, run as an independent activity |

The A20 oscillator is a separate curiosity, not this payload's LO — at ~2.2 GHz
it does not fit the 2380 MHz LO the optional RF stage would need. Its
characterization has real instructional value and its own hold points, and it
proceeds on its own schedule without blocking anything here.

---

## Directory layout

Currently flat. It grows as work lands:

```text
hardware/payload_exp_sband_tx/
├── README.md                        ← this file
├── sband_payload_architecture_trade_study.md
├── fpga_link_processor_logic_interface_first_bringup.md
├── mini_totem_bpsk_if_to_sband_plan.md
├── tektronix_7l13_a20_2p2ghz_oscillator_characterization.md
├── *.drawio
├── fpga/                            ← M0 symbol engine: rtl/ sim/ constraints/
└── measurements/                    ← planned: captures/ raw_data/ per milestone
```

The FPGA work has its own README: [`fpga/README.md`](fpga/README.md) covers the
PRBS-7 convention, the timing contract, the test coverage, and how to build and
simulate.

The constraint filename is not created until the IceZero revision and pin
mapping are physically verified — see the board-facts table in the bring-up
document.

---

## Bench rules

These are short because the scope is narrow.

- **No antenna, ever.** Cable, attenuator, dummy load, or an SDR input behind at
  least 30 dB of pad.
- Terminate unused RF ports.
- Use a DC block ahead of any analyzer or SDR.
- The A20 oscillator has a **hard hold point** before power is applied. Its
  supply polarity, range, current, and startup sequence must be documented and
  independently checked first. Do not skip it: the assembly is a vintage hybrid
  with exposed bond wires and unknown absolute-maximum ratings.
- Avoid solderless breadboards for anything carrying the DAC bus or its clock.

---

## Open items

All four items about the Arty variant, the master XDC, the M0 bitstream and the
DAC inventory are closed: it is a Z7-20, `constraints/arty_z7_20.xdc` exists,
M0's hardware gate is met, and the converter question is moot — the part on hand
is an AD9910, not a DAC902.

- [ ] **M1**: get `PLL_LOCK` and a measured tone. The remaining work is on the
      bench, not in the RTL — reconnect per the pin map, use the module's own
      40 MHz with W1 at 2&3 (the configuration its demo board proved), then
      `c0538C132`, `i`, `k`.
- [ ] Confirm whether the module's onboard oscillator reaches `REF_CLK` at all,
      now that the `IO_UPDATE` width fix removes the confound that made this
      look like a board fault.
- [ ] Inventory the RF half for M5: mixer, filters, SDR, spectrum analyser. The
      AD9910 reaches about 400 MHz, so S-band still needs upconversion.
- [ ] Re-measure edge rates and overshoot with a short ground spring, to
      separate probe artefact from real signal — carried over from M0.
- [ ] Decide whether the directory name still fits. It says `sband_tx`; the work
      is a digital modulation bench experiment whose S-band stage is optional.

---

## Related repository documents

- [`../comms/design/overview.md`](../comms/design/overview.md) — the mission UHF
  radio, whose XOR-modulator BPSK chain is the closest existing relative of the
  deferred architecture
- [`../comms/design/rx_mixer_trade_study.md`](../comms/design/rx_mixer_trade_study.md)
  — format precedent for the trade study here
- [`../../docs/comms/modulation.md`](../../docs/comms/modulation.md) — modulation background
- [`../../docs/architecture/project_scope.md`](../../docs/architecture/project_scope.md) — project scope and positioning
