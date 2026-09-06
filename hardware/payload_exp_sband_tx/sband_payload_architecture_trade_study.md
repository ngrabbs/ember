# Experimental S-Band Payload — Architecture Trade Study

**Status:** Decision made 2026-09-05 — **FPGA-generated low-IF BPSK into a parallel DAC** selected. The S-band RF front end is deferred off the critical path. The single-bit phase-modulator architecture is retained as the future RF path, not the bench path.

**Driver:** Five days of design writing produced three mutually exclusive transmitter architectures and three different frequency plans across four documents, with nothing recording which one is being built. Work cannot start until that is closed.

**Scope correction that drives the decision:** EMBER is a capstone build targeting an engineering model. It will not fly. Flight-worthiness, if ever addressed, is a documentation exercise. Nothing in this payload radiates over the air. The payload's value is therefore concentrated in the *digital* half — generating data, pushing it through an FPGA, and producing a measurable modulated waveform — not in the RF front end.

This document captures the trade so it can be cited in the design review and so the reasoning survives the next time someone asks "why is there a DAC here instead of the XOR modulator we already built for the comms board."

---

## 1. Background

Three architectures exist in the directory, written across five days, each in a different document:

| Label | Where | Topology | Frequency plan |
|---|---|---|---|
| **A** | `mini_totem_bpsk_if_to_sband_plan.md` (Sep 1) | FPGA → DAC → IF filter → mixer → 2.4 GHz BPF | IF 50 MHz, LO 2350 MHz |
| **B** | `sband_experimental_tx_rf_block_diagram.drawio` (Sep 4) | Same as A, plus RRC shaping, driver, PA, coupler, detector, low-jitter clock | IF 20 MHz, LO 2380 MHz, 100 MSPS |
| **C** | `sband_direct_bpsk_rf_block_diagram.drawio` (Sep 5) | FPGA → logic buffer → 0°/180° phase modulator switching a 2.4 GHz PLL/VCO carrier. No DAC, no IF, no mixer | carrier ≈ 2400 MHz direct |

A and B are the same architecture at two levels of maturity, and are treated below as one option.

A fourth thread runs alongside: `fpga_link_processor_logic_interface_first_bringup.md` (Sep 5) defines a first milestone in which the FPGA drives a *single registered bit* through an SN74LVC1G125 into a loopback PRBS checker. That is architecture C's electrical interface. The newest thinking had drifted toward C without anything saying so.

A fifth thread is the surplus Tektronix 7L13 A20 oscillator at ~2.2 GHz, characterized in its own document, informally treated as a candidate LO.

---

## 2. Requirements

Derived from the corrected scope, not from a mission link budget — there is no link to close.

| ID | Requirement | Source | Target |
|---|---|---|---|
| SBX-1 | Primary deliverable is an FPGA-generated modulated waveform, measured | Learning objective | Observable BPSK produced by HDL the team wrote |
| SBX-2 | Modulation must be observable without any RF hardware | Bench reality; RF deferred | Visible on a ≤200 MHz scope and a logic analyzer |
| SBX-3 | Must exercise real digital-communications content in HDL | Learning objective | Framing, CRC, symbol timing, symbol mapping, NCO, pulse shaping |
| SBX-4 | Must terminate in a signal a later RF front end can accept | Keep the S-band option alive | Analog IF at a defined level and impedance, or a defined logic-level phase command |
| SBX-5 | First results with hand wiring; no custom PCB required | Schedule | IceZero PMOD headers plus a DAC module |
| SBX-6 | Instruments limited to what the bench has | Availability | Scope, logic analyzer, DMM required; SDR and spectrum analyzer desirable |
| SBX-7 | No over-the-air transmission at any stage | Scope | Cabled, attenuated, terminated. No antenna |
| SBX-8 | No flight qualification | Scope | Flight-worthiness is a documentation exercise only, if requested |
| SBX-9 | First observable BPSK inside the fall bench window | Schedule | Weeks, not months, to a scope capture showing phase reversal |
| SBX-10 | Must not put the mission radio at risk | System | Experiment runs on separate hardware from the comms board |

SBX-2 is the requirement that decides the trade. Under the corrected scope it is not negotiable: an architecture whose modulation only becomes visible after S-band hardware exists cannot deliver the primary result on this bench, on this schedule.

---

## 3. Options considered

| # | Option | Modulation lives in | Observable on a scope without RF? | HDL content | New hardware needed |
|---|---|---|---|---|---|
| **1** | **FPGA + parallel DAC, low-IF BPSK** (A/B) | **FPGA** | **Yes — the modulated carrier itself** | **High** — NCO, mapper, upsampler, FIR, fixed-point | **DAC module** |
| 2 | FPGA 1-bit phase command + S-band phase modulator (C) | RF front end | No — a square wave until S-band exists | Low–medium — symbol engine only | PLL/VCO, phase modulator, filters |
| 3 | FPGA 1-bit sigma-delta into an RC filter | FPGA | Yes, at low IF | Medium — plus a modulator | None — two passives |
| 4 | COTS SDR transmitter (HackRF / PlutoSDR) driven from a host | Vendor silicon | Yes | **None** | SDR |
| 5 | Run the modulation experiment at 437 MHz on the existing comms board | Comms board XOR modulator | No | Low | None |

### Eliminated

**Option 4 — COTS SDR.** Produces a textbook BPSK spectrum in an afternoon and teaches nothing about how it was made. It fails SBX-1 and SBX-3 outright: the deliverable is *our* HDL generating the waveform, not a waveform. Retained only as an independent cross-check instrument — if an SDR is on hand, use it to *receive* Option 1's output, which is a legitimate and useful role.

**Option 5 — Do it at UHF on the comms board.** Superficially attractive: the hardware exists, the XOR modulator at 145.67 MHz works, and the tripler already carries BPSK phase to 437 MHz. Rejected on two counts. It fails SBX-10 by making the mission radio the experiment bed, at a point where the comms board is being brought up for its actual job. And it fails SBX-3: the comms board's modulation is a single GPIO into an XOR gate, so the FPGA has nothing interesting to do. The experiment would reduce to writing a bitstream generator, which is the part already solved on the RP2040.

**Option 2 — Direct 1-bit phase modulation.** This is the strongest *RF* architecture in the set and the weakest *bench* architecture, for the same reason: all of the modulation happens in the phase modulator. What the FPGA emits is one logic-level bit. On an oscilloscope that is a square wave, indistinguishable from a clock divider, and it stays a square wave until an S-band carrier source, a phase modulator, filters, and a driver exist and work together. Under the corrected scope that pushes the entire deliverable behind the RF work that was just declared non-critical. **Deferred, not rejected** — see §5.

### Adopted as an interim step

**Option 3 — Sigma-delta on an FPGA pin.** A one-bit noise-shaped output through a small RC filter produces a genuine analog waveform from an iCE40 with no converter and no procurement. Bandwidth is modest, the spectrum is dominated by shaping noise outside the passband, and it will never drive a mixer — but it will show a low-IF carrier reversing phase on a scope, using hardware already on the desk. Adopted as **M0.5**, an optional de-risking step between the symbol engine and the DAC bring-up. It proves the modulator logic before any DAC wiring exists, which means a failure at M1 is unambiguously an interface problem rather than a modulator problem.

### Selected

**Option 1 — FPGA-generated low-IF BPSK into a parallel DAC.**

---

## 4. Why Option 1

**It satisfies SBX-2 with no RF hardware at all.** At 20 MSPS with a 1 MHz IF, the DAC output is a 1 MHz carrier that visibly reverses phase at symbol boundaries. Any bench oscilloscope resolves it. That capture *is* the milestone, and it requires no mixer, no LO, no filter, and no PA.

**It carries the most HDL content per unit of RF risk.** Option 1 needs a phase accumulator, a sine table, a symbol mapper, an upsampler, sample-rate and symbol-rate timing, fixed-point scaling and saturation, and — at M4 — a root-raised-cosine FIR. Option 2 needs a symbol engine and an output flip-flop. Both are worth building; only one of them fills a semester of FPGA work.

**It keeps the S-band option alive at zero cost.** Option 1's DAC output is exactly the signal the deferred RF chain wants at its IF port. Adding the mixer later changes nothing upstream. The two drawio diagrams stop being rival plans and become the same plan at two stages.

**The rate ceiling is a choice, not a constraint.** The stated objection to Option 1 is signal integrity: a 12-bit parallel bus at 100 MSPS over PMOD headers and hand wiring is genuinely difficult, and the `mini_totem` document lists it as risk #1. That objection assumes 100 MSPS. Nothing about demonstrating BPSK requires it. At 20 MSPS the bus period is 50 ns, edge rates are set by the iCE40 output driver rather than the data rate, and hand wiring with adjacent ground returns is entirely tractable. **Decoupling the sample rate from the ambition removes the only strong argument against Option 1.**

**The instruments already available are the right ones.** A scope and a logic analyzer are sufficient through M3. An SDR or spectrum analyzer improves M3 and M4 but gates neither.

### The observability/filtering tension

Worth recording explicitly, because it explains why the frequency plan has two regimes rather than one compromise:

- A **low** IF (1–5 MHz) is what makes the waveform legible on a bench scope, and keeps the sample rate low enough for hand wiring.
- A **high** IF (20+ MHz) is what puts the mixer image far enough from the desired product to filter — at 2400 MHz RF, a 20 MHz IF places the image at 2360 MHz, 40 MHz away, which a practical band-pass filter can reject. A 1 MHz IF would place it 2 MHz away, which nothing reasonable can.

These are different optima and there is no single IF that serves both. The bench plan therefore optimizes for observability, and the optional RF stage gets its own sample-rate and IF step rather than degrading the bench work to accommodate hardware that may never be built.

---

## 5. Consequences

### Frequency and rate plan (supersedes A and B)

| Stage | Sample rate | IF | Symbol rate | Samples/symbol | Clock divisor from 100 MHz |
|---|---:|---:|---:|---:|---:|
| M0.5 sigma-delta | 100 MHz bit rate | 250 kHz | 10 ksym/s | — | 1 |
| M1 sine | 20 MSPS | 1 MHz | — | — | 5 |
| M2 baseband BPSK | 20 MSPS | baseband | 100 ksym/s | 200 | 5 |
| M3 low-IF BPSK | 20 MSPS | 1 MHz | 100 ksym/s | 200 | 5 |
| M4 shaped | 50 MSPS | 5 MHz | 500 ksym/s | 100 | 2 |
| M5 RF (optional) | 100 MSPS | 20 MHz | 1 Msym/s | 100 | 1 |

Every sample rate is an exact integer divisor of the 100 MHz board clock, which keeps the symbol-tick divider exact and satisfies the assertion already written into `tx_pattern_source`.

The M5 row adopts the `sband_experimental_tx` drawio's plan — 20 MHz IF, 2380 MHz LO, 2400 MHz RF, image at 2360 MHz. The `mini_totem` plan's 50 MHz IF / 2350 MHz LO is superseded.

### Converter selection: DAC902 over DAC904

| | Data lines | Plus clock | Resolution |
|---|---:|---:|---:|
| DAC902 | 12 | 13 | 12-bit |
| DAC904 | 14 | 15 | 14-bit |

Pin count decides it. A 12-bit bus plus a clock fits in two 8-pin PMOD connectors with a pin to spare; a 14-bit bus does not. Two extra bits of resolution buy nothing at this stage — the DAC is operated near −6 dBFS anyway, quantization is far below the noise the rest of the bench contributes, and no measurement through M4 is resolution-limited. **DAC902 selected.** Revisit only if a spurious-free dynamic range measurement ever becomes a deliverable.

This depends on verifying the IceZero PMOD pin budget against the board's actual revision — an open item, not an assumption.

### Amendment to the M0 bring-up document

`fpga_link_processor_logic_interface_first_bringup.md` was written for Option 2's electrical interface. Under Option 1:

- **Still required:** the symbol-tick divider, pattern selector, PRBS-7 with its documented shift/seed/output convention, the registered output rule, RTL simulation confirming the 127-symbol period, and the board-facts verification table. This is the reusable core and it is architecture-independent.
- **Now optional:** the SN74LVC1G125 buffer, the `/OE` pull-up, the series resistor, and the hardware loopback path. The PRBS generator/checker pair is proven in simulation. The buffered loopback stays a worthwhile signal-integrity exercise and a good way to learn the instruments, but it is no longer a gate.
- **Reinstated as required** only if Option 2 is revived for an RF build.

The measurement worksheets in that document remain useful as-is; the DAC bus is measured the same way a buffered logic output is.

### The A20 oscillator moves off the critical path

The surplus Tektronix hybrid runs near 2.2 GHz. The selected RF plan, if it is ever built, needs a 2380 MHz LO. The A20 does not reach it, and forcing the plan to fit the A20 would put the output near 2.18–2.25 GHz and require an IF around 200 MHz — beyond a DAC902's sample rate in first Nyquist, and a substantially harder reconstruction problem.

It is therefore **not this payload's LO**. It remains a legitimate independent bench activity: identifying an undocumented microwave hybrid, reconstructing its bias network from service documentation, and characterizing frequency, power, drift, and phase noise is a genuinely instructive exercise, and its document already carries the right hold points. It proceeds on its own schedule and blocks nothing.

The band-allocation concern raised earlier — that 2200–2290 MHz is space-operations spectrum rather than amateur — is **not** a constraint here, because SBX-7 forbids radiating anything at any frequency. Everything terminates in a cable, a pad, and a load. The constraint is the bench rule, not the allocation.

### Consequence for the RF front end

Deferred entirely. If time remains after M4, M5 is built from the `sband_experimental_tx` diagram. If Option 2 is preferred at that point — because a phase modulator and a synthesizer turn out to be easier to source than a mixer and an LO chain — the link processor transfers unchanged, and only the output stage differs. Neither outcome invalidates M0 through M4.

---

## 6. Risks and open items

| Risk | Severity | Mitigation |
|---|---|---|
| Parallel DAC bus over PMOD hand wiring is noisy or unreliable | High at ≥50 MSPS, low at 20 MSPS | Start at 20 MSPS. Registered outputs only. Short wires with adjacent ground returns. No solderless breadboard. Raise the rate only after M3 passes, and treat M4's 50 MSPS as the point where a small PCB may become necessary |
| IceZero PMOD pin budget insufficient for 12 data + clock | Medium | Verify against the board's actual revision and pinout before committing. DAC902 chosen partly for this. DDR or multiplexed transfer only as a last resort — it complicates the very interface being brought up |
| DAC902 is a current-output converter; probing it needs the right termination | Medium | Study the module schematic or datasheet output stage before connecting a probe. Establish the load and expected voltage swing on paper first. Scope with a proper 50 Ω path, not a 10× probe on an unterminated output |
| iCE40 resources insufficient for an RRC FIR at M4 | Medium | Device density is unconfirmed (HX4K vs HX8K). M4 is the last milestone, not a gate for M1–M3. Reduce taps, reduce samples per symbol, or use a symmetric folded FIR. Unshaped BPSK is a complete result on its own |
| Toolchain problems on IceZero | Low | The bring-up document's Phase 0 gate — a blinking LED and a timing report — before any of this |
| Scope bandwidth or memory depth inadequate | Low | 1 MHz IF and 100 ksym/s were chosen to be comfortable on any bench scope. If the scope struggles at M3, the plan is already wrong somewhere else |
| Scope creep back into RF before the digital chain works | Medium | This document. RF is M5 and optional. The A20 is a side activity. Neither may precede M3 |
| A20 powered without confirmed bias conditions | High | The hold point in its own document is mandatory and blocking. Vintage hybrid, exposed bond wires, unknown absolute maxima |
| Team treats the engineering-model scope as an excuse for informal records | Medium | Milestones have written gates and measurement worksheets. The record is the deliverable as much as the waveform is |

### Open items

- [ ] Physical hardware inventory: IceZero revision, DAC902/904 availability and form (bare IC or module), mixer, filters, SDR, spectrum analyzer.
- [ ] IceZero revision, FPGA density, package, oscillator marking recorded per the bring-up document's board-facts table.
- [ ] PMOD pin budget verified for 12 data lines plus a clock.
- [ ] DAC output stage and termination understood on paper before first probe.
- [ ] Directory name reconsidered — `sband_tx` describes the optional half.

---

## 7. Verification plan

Each milestone's gate, stated so that "done" is not a matter of opinion.

**M0 — symbol engine**
1. Simulation shows the PRBS-7 sequence repeating with a period of exactly 127 symbols, with the seed, shift direction, and output-tap convention documented and matching a Python golden model.
2. Simulation shows `tx_symbol` changing only on symbol boundaries, at exactly `CLOCK_HZ / SYMBOL_RATE` clock cycles.
3. On hardware, the alternating pattern measures at half the symbol rate on a scope, at 1 k, 10 k, 100 k, and 1 Msym/s.
4. No narrow glitches during steady operation or pattern changes.

**M0.5 — sigma-delta (optional)**
5. A low-IF carrier is visible through the RC filter, with phase reversal at symbol boundaries. Confirms the modulator logic before any DAC wiring exists.

**M1 — DAC interface**
6. Constant midscale code produces a stable, expected DC level; changing the code changes the voltage monotonically.
7. A digital ramp produces a clean sawtooth with no missing codes and no bit-order errors.
8. A 1 MHz sine at 20 MSPS is stable, with visible quantization steps at the expected 20 samples per cycle.

**M2 — baseband BPSK**
9. Two-level output at the expected symbol rate.
10. A recorded capture of `0x55` preamble plus the `0x1ACFFC1D` sync word is decodable back to the transmitted bits by hand or by script.

**M3 — low-IF BPSK** *(the milestone that matters)*
11. Scope capture shows a 1 MHz carrier with unambiguous 180° phase reversals at symbol boundaries, and no reversal during a long run of identical bits.
12. Where an SDR or analyzer is available, the spectrum shows a main lobe centered at 1 MHz with the sidelobe structure expected of unshaped rectangular symbols.
13. Captures, tool versions, RTL revision, and settings committed to `measurements/`.

**M4 — pulse shaping**
14. Sidelobe levels measurably lower than the M3 capture taken under identical analyzer settings. The comparison, not the absolute number, is the result.

**M5 — RF, optional**
15. A signal near 2400 MHz into a dummy load, with the image at 2360 MHz and LO leakage at 2380 MHz identified and their rejection measured before and after the band-pass filter.

---

## 8. Decision summary

> **Selected:** FPGA-generated low-IF BPSK into a DAC902, starting at 20 MSPS with a 1 MHz IF and 100 ksym/s, rising to 50 MSPS / 5 MHz once the interface is proven. The modulated waveform exists at the DAC output and is measured there.
>
> **Adopted as an interim step:** a 1-bit sigma-delta output through an RC filter, to prove the modulator logic before any DAC wiring exists.
>
> **Deferred:** the S-band RF front end and the single-bit phase-modulator architecture. Retained together as the future RF path, reusing the link processor unchanged.
>
> **Rejected:** COTS SDR transmitters (produce a waveform, teach nothing, fail SBX-1 and SBX-3) and running the experiment on the comms board at 437 MHz (fails SBX-10 and SBX-3).
>
> **Moved off the critical path:** the Tektronix A20 oscillator. It cannot serve as the LO for the selected RF plan, and remains a worthwhile independent characterization exercise.
>
> **Net benefit:** the primary result — an FPGA generating its own BPSK, visible on a scope — is reachable with a DAC module, hand wiring, and instruments already on the bench. No RF hardware gates it, and no procurement gates it beyond one converter.
>
> **Net cost:** one DAC module, a 12-bit parallel interface to wire carefully, and a self-imposed rate ceiling that must not be raised until M3 passes.

---

## Related documents

- Payload overview and milestones: [`README.md`](README.md)
- M0 symbol engine and interface: [`fpga_link_processor_logic_interface_first_bringup.md`](fpga_link_processor_logic_interface_first_bringup.md)
- Narrative and bring-up phases: [`mini_totem_bpsk_if_to_sband_plan.md`](mini_totem_bpsk_if_to_sband_plan.md)
- Selected architecture, drawn: [`sband_experimental_tx_rf_block_diagram.drawio`](sband_experimental_tx_rf_block_diagram.drawio)
- Deferred architecture, drawn: [`sband_direct_bpsk_rf_block_diagram.drawio`](sband_direct_bpsk_rf_block_diagram.drawio)
- Independent activity: [`tektronix_7l13_a20_2p2ghz_oscillator_characterization.md`](tektronix_7l13_a20_2p2ghz_oscillator_characterization.md)
- Format precedent: [`../comms/design/rx_mixer_trade_study.md`](../comms/design/rx_mixer_trade_study.md)
- Mission radio: [`../comms/design/overview.md`](../comms/design/overview.md)
