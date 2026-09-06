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
- Not currently a PCB. First results come from an IceZero, hand wiring, and a
  DAC module.

---

## Selected architecture

FPGA-generated **low-IF BPSK into a parallel DAC**. The modulated carrier exists
as an analog waveform at the DAC output, where it can be measured directly. No
RF hardware is required to see BPSK working.

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
│            │  ±1 symbols                                          │
│            v                                                      │
│   ┌────────────────────┐                                          │
│   │ NCO + modulator    │  low-IF carrier, 0° / 180° reversal      │
│   │ (+ RRC shaping)    │  shaping added only after unshaped works │
│   └────────┬───────────┘                                          │
│            │  12-bit parallel samples                             │
│            v                                                      │
│   ┌────────────────────┐                                          │
│   │ DAC902             │  20 MSPS initial · operate ≈ −6 dBFS     │
│   └────────┬───────────┘                                          │
│            │  analog low-IF BPSK                                  │
│            v                                                      │
│   oscilloscope · logic analyzer · SDR · 50 Ω termination          │
└───────────────────────────────────────────────────────────────────┘
             │
             │  the same signal, later, only if time allows
             v
   IF filter → mixer → 2.4 GHz BPF → attenuator → SDR / dummy load
   (off the critical path — see the trade study)
```

The alternative considered and deferred — a single-bit phase command driving an
S-band phase modulator — puts all of the modulation in RF hardware and leaves a
square wave on the bench. It was rejected for this scope for exactly that
reason. It remains the preferred path *if* an RF front end is ever built,
because it reuses the same link processor unchanged.

---

## Frequency and rate plan

One plan, adopted here, superseding the differing numbers scattered across the
earlier documents. Rates start deliberately low: hand-wired PMOD interconnect,
not ambition, sets the ceiling.

| Stage | Sample rate | IF | Symbol rate | Samples/symbol | Measured with |
|---|---:|---:|---:|---:|---|
| M1 sine check | 20 MSPS | 1 MHz | — | — | scope |
| M2 baseband BPSK | 20 MSPS | baseband | 100 ksym/s | 200 | scope, logic analyzer |
| M3 low-IF BPSK | 20 MSPS | 1 MHz | 100 ksym/s | 200 | scope |
| M4 shaped, faster | 50 MSPS | 5 MHz | 500 ksym/s | 100 | scope, SDR |
| RF (optional) | 100 MSPS | 20 MHz | 1 Msym/s | 100 | SDR / spectrum analyzer |

Board clock is 100 MHz, so every sample rate above is an exact integer divisor.

Note the tension recorded in the trade study: a **low** IF is what makes the
waveform easy to see on a bench scope, and a **high** IF is what makes the image
easy to filter after a mixer. Those are different optima. The bench plan
optimizes for observability; the optional RF stage gets its own sample-rate step
(100 MSPS / 20 MHz IF / 2380 MHz LO / 2400 MHz RF) rather than compromising the
bench work.

---

## Milestones

| ID | Milestone | Gate |
|---|---|---|
| **M0** | FPGA link processor: symbol timing, pattern selector, PRBS-7, registered output | Simulation confirms 127-symbol PRBS period and exact symbol timing; scope confirms alternating pattern at half the symbol rate |
| **M1** | FPGA → DAC interface: DC midscale, ramp, sine | Stable 1 MHz sine at the DAC output with no missing codes or bus glitches |
| **M2** | Unshaped baseband BPSK | Two-level waveform, correct symbol rate, sync word recoverable from a capture |
| **M3** | Unshaped low-IF BPSK | Visible 180° carrier phase reversals at symbol boundaries; SDR shows a lobe centered at the IF |
| **M4** | RRC pulse shaping, higher rate | Measurable sidelobe reduction against the M3 capture |
| **M5** | *(optional)* RF upconversion to 2.4 GHz | Signal at 2400 MHz into a dummy load, image and LO leakage characterized |

M0 comes from
[`fpga_link_processor_logic_interface_first_bringup.md`](fpga_link_processor_logic_interface_first_bringup.md)
with one amendment under the selected architecture: the **RTL, simulation, and
PRBS work is required**, while the external SN74LVC1G125 buffer and the hardware
loopback path become an **optional** signal-integrity exercise rather than a
gate. The generator/checker pair is proven in simulation. The buffered loopback
returns to being required only if the deferred phase-modulator architecture is
revived.

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
├── fpga/                            ← planned: rtl/ sim/ constraints/ Makefile
└── measurements/                    ← planned: captures/ raw_data/ per milestone
```

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

- [ ] Confirm what hardware is physically on hand: IceZero revision, DAC902 or
      DAC904 (bare or module), mixer, filters, SDR, spectrum analyzer.
- [ ] Verify the IceZero PMOD pin budget supports 12 data lines plus a clock.
- [ ] Record the IceZero revision, FPGA density, package, and oscillator marking.
- [ ] Study the DAC module's output stage and required termination before
      putting a probe on it.
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
