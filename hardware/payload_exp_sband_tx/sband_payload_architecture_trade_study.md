# Experimental S-Band Payload — Architecture Trade Study

**Status:** Decision made 2026-09-05 — FPGA-generated low-IF BPSK into a parallel DAC. **Superseded 2026-09-08** when the converter on hand turned out to be an AD9910 DDS: see *Superseded by the hardware* below. The S-band RF front end remains deferred off the critical path.

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
| SBX-5 | First results with hand wiring; no custom PCB required | Schedule | Pmod / ChipKit headers plus a converter module. *(Realised as an Arty Z7-20 and an AD9910 breadboarded together.)* |
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

### Frequency and rate plan (supersedes A and B) — MOOT 2026-09-08

*(Sample rates are meaningless for a DDS: the AD9910 runs at a fixed 1 GHz
SYSCLK and the carrier is a 32-bit tuning word. See the payload README for the
current plan. Kept for the reasoning about observability versus image
rejection, which still applies to the M5 mixer stage.)*

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

### Converter selection: DAC902 or DAC904 — REOPENED 2026-09-06, MOOT 2026-09-08

*(Neither part is on hand; the converter is an AD9910 DDS. Kept because the
error below is instructive.)*

| | Data lines | Plus clock | Resolution |
|---|---:|---:|---:|
| DAC902 | 12 | 13 | 12-bit |
| DAC904 | 14 | 15 | 14-bit |

**The original decision here was wrong and is withdrawn.** It selected DAC902 on
the grounds that a 12-bit bus plus a clock fits in two 8-pin PMOD connectors
while a 14-bit bus does not. The IceZero pinout document shows four 2×6 PMOD
connectors carrying **eight signal pins each, 32 in total**. Two connectors give
sixteen signals, so DAC904's fifteen fits with a pin to spare, and the board has
twice as many pins again beyond that. Pin budget does not decide this.

What survives of the argument is weaker and no longer sufficient on its own: two
extra bits buy nothing at this stage, since the DAC is operated near −6 dBFS,
quantization sits far below the noise the rest of the bench contributes, and no
measurement through M4 is resolution-limited. Against that, DAC904 costs two more
hand-soldered wires.

**Decision deferred to the hardware inventory.** Whichever part is actually on
hand wins; if both are, take the DAC902 for the smaller bus. Revisit properly if
a spurious-free dynamic range measurement ever becomes a deliverable.

### Amendment to the M0 bring-up document

`fpga_link_processor_logic_interface_first_bringup.md` was written for Option 2's electrical interface. Under Option 1:

- **Still required:** the symbol-tick divider, pattern selector, PRBS-7 with its documented shift/seed/output convention, the registered output rule, RTL simulation confirming the 127-symbol period, and the board-facts verification table. This is the reusable core and it is architecture-independent.
- **Now optional:** the SN74LVC1G125 buffer, the `/OE` pull-up, the series resistor, and the hardware loopback path. The PRBS generator/checker pair is proven in simulation. The buffered loopback stays a worthwhile signal-integrity exercise and a good way to learn the instruments, but it is no longer a gate.
- **Reinstated as required** only if Option 2 is revived for an RF build.

The measurement worksheets in that document remain useful as-is; the DAC bus is measured the same way a buffered logic output is.

### Superseded by the hardware: AD9910 DDS (2026-09-08)

The converter on hand is an **AD9910 DDS**, not the DAC902 the order history
suggested. That reverses part of this study's conclusion and the reversal should
be recorded rather than quietly absorbed.

**What the AD9910 changes.** It is not a converter you feed samples to. It is a
1 GSPS synthesiser with a 14-bit DAC, a 32-bit frequency word and eight profile
registers holding independent frequency, phase and amplitude, selected by three
pins. Program profile 0 at 0° and profile 1 at 180° on the same frequency, drive
`PROFILE[0]` from `tx_symbol`, and the carrier flips phase per symbol. **BPSK
costs one FPGA pin.**

**This is Option 2, the one this study deferred.** Section 3 rejected the
single-bit phase-modulator path because "all of the modulation happens in the
phase modulator" and "what the FPGA emits is one logic-level bit… a square wave
on an oscilloscope". That reasoning was correct for a *discrete* phase modulator
that did not exist yet. It does not hold when the carrier source and phase
switch arrive in one chip that is already on the desk.

**What it costs, honestly.** The deciding argument for the DAC path was HDL
content: an NCO, a sine table, an upsampler, fixed-point scaling and eventually
an RRC FIR. **The DDS removes all of it.** What replaces it is SPI control of a
real RF part, a register map, and the discipline of reading a 64-page datasheet
carefully — different content, and arguably more transferable, but the study
should not pretend the trade is free.

**What it does not change.** The symbol engine is untouched. Framing, symbol
timing, PRBS generation and checking, and the console all feed the DDS exactly
as they would have fed a DAC. M0 is unaffected and complete.

**What survives for later.** The AD9910's 16-bit parallel port (`D0`–`D15`,
`F[1:0]`) accepts amplitude, phase or frequency words at up to 250 MSPS. That is
where QPSK and pulse shaping would live, and it restores most of the HDL content
the profile-pin approach removes — at M4, not now.

**Observability, the study's primary criterion, is better not worse.** The
original argument was that the DAC path put a modulated carrier on a scope with
no RF hardware. The DDS puts a *cleaner* modulated carrier on a scope, at a
programmable frequency up to about 400 MHz, out of a coaxial connector.

The converter sub-decision — DAC902 versus DAC904, reopened above on a
pin-count argument that turned out to be wrong — is now moot. Neither part is
present.

### Platform change: IceZero to Arty Z7 (2026-09-07)

The IceZero failed in hardware — a dead EP53A7HQI buck regulator plus a hard
short on the 3.3 V rail, traced to a generic USB-serial cable connected to J3
with its VCC wire attached. The payload moves to a Digilent Arty Z7.

**This does not reopen the architecture decision.** The trade selected
FPGA-generated low-IF BPSK into a DAC on the strength of observability, HDL
content and a deliberately low sample rate — none of which depend on which FPGA
runs the logic. The RTL is plain SystemVerilog with no vendor primitives and
re-simulates unchanged at the Arty's 125 MHz, where all four symbol rates still
divide exactly.

What the change does affect is downstream: the toolchain becomes Vivado 2024.2,
constraints become `.xdc`, and the M1 converter interface is planned against the
Arty's Pmod and ChipKit connectors rather than the IceZero's four PMODs. *(That
interface turned out to be an SPI link to a DDS rather than a parallel DAC bus —
see* Superseded by the hardware *below.)* The
Zynq's PS also opens an option the iCE40 never had — a hard ARM core for control
and readout — which should be considered at M1 rather than assumed now.

### The A20 oscillator moves off the critical path

The surplus Tektronix hybrid runs near 2.2 GHz. Under the original DAC plan
that ruled it out: reaching 2.4 GHz from a 2.2 GHz LO needs an IF around
200 MHz, which is beyond a DAC902's sample rate in first Nyquist and a
substantially harder reconstruction problem.

**Partly revived 2026-09-08.** The AD9910 generates cleanly up to about
400 MHz, so a 200 MHz IF is now trivial rather than impossible, and
2.2 GHz + 200 MHz = 2.4 GHz becomes a viable frequency plan. The objection that
removed the A20 from consideration was a property of the DAC, not of the
oscillator.

That does not promote it to the critical path — M5 is still optional and the
A20's own document still holds a blocking hold point before power. But if an
S-band stage is ever built, the A20 is a candidate again rather than excluded,
and the frequency plan would be 2.2 GHz LO with a 200 MHz IF rather than
2.38 GHz LO with 20 MHz.

For now it is **not this payload's LO**. It remains a legitimate independent bench activity: identifying an undocumented microwave hybrid, reconstructing its bias network from service documentation, and characterizing frequency, power, drift, and phase noise is a genuinely instructive exercise, and its document already carries the right hold points. It proceeds on its own schedule and blocks nothing.

The band-allocation concern raised earlier — that 2200–2290 MHz is space-operations spectrum rather than amateur — is **not** a constraint here, because SBX-7 forbids radiating anything at any frequency. Everything terminates in a cable, a pad, and a load. The constraint is the bench rule, not the allocation.

### Consequence for the RF front end

Deferred entirely. If time remains after M4, M5 is built from the `sband_experimental_tx` diagram. If Option 2 is preferred at that point — because a phase modulator and a synthesizer turn out to be easier to source than a mixer and an LO chain — the link processor transfers unchanged, and only the output stage differs. Neither outcome invalidates M0 through M4.

---

## 6. Risks and open items

Rewritten 2026-09-08. Every risk in the original table concerned a parallel DAC
bus, iCE40 resources or the IceZero toolchain, and none of those exist any more.

| Risk | Severity | Mitigation |
|---|---|---|
| A pulse narrower than one `SYNC_CLK` period is silently ignored by the AD9910 | **Realised** | `IO_UPDATE`, `MASTER_RESET` and profile changes are all captured on `SYNC_CLK` = SYSCLK/4, which before PLL lock is just the reference over four. A 96 ns `IO_UPDATE` cost this project most of a day. Widths are now 1 ms, matching a known-good reference implementation |
| Register writes land in a buffer and do nothing without `IO_UPDATE` | High | The sequencer pulses it after every register group, and `tb_ad9910_ctrl` asserts those pulses specifically. A design that writes perfect registers and forgets the pulse is indistinguishable from a dead bus |
| Confusing "no output" with "no clock" | High | `SYNC_CLK` needs no configuration, no SPI and no PLL. Measure it first on any AD9910 problem; if it is dead nothing downstream is worth investigating |
| Reference clock over flying leads or a breadboard | Medium | The AD9910 accepts 3.2–60 MHz, so divide down rather than up: 12.5 MHz has an 80 ns period and tolerates a breadboard where 31.25 MHz does not. Keep a ground return beside it |
| Diagnosing an undocumented module from the outside | **Realised** | Substitute a known-good driver early. The demo board settled in minutes what hours of probing had not, and refuted a written conclusion |
| Profile-pin BPSK removes the HDL content that justified this study | Medium | Accepted for M1–M3. The parallel port at M4 restores it, with QPSK and pulse shaping |
| Scope creep back into RF before the modulator works | Medium | This document. S-band is M5 and optional. The A20 is a side activity. Neither may precede M2 |
| A20 powered without confirmed bias conditions | High | The hold point in its own document is mandatory and blocking. Vintage hybrid, exposed bond wires, unknown absolute maxima |
| Team treats the engineering-model scope as an excuse for informal records | Medium | Milestones have written gates and measurement worksheets. The record is the deliverable as much as the waveform is |

### Open items

- [x] PMOD pin budget — closed 2026-09-06, then moot: no parallel bus is used.
- [x] Board facts — closed. Arty Z7-20, `constraints/arty_z7_20.xdc`.
- [x] Bench control and readout — **UART console**, now on Pmod JB rather than
      the IceZero's J3. Reads `bit_count` and `error_count` directly, which is
      what let the M0 gate be counted rather than inferred.
- [x] Converter selection — moot. The part on hand is an AD9910 DDS.
- [ ] **M1**: `PLL_LOCK` and a measured tone. Bench work, not RTL.
- [ ] Inventory the RF half for M5: mixer, filters, SDR, spectrum analyser. The
      AD9910 reaches about 400 MHz, so S-band still needs upconversion.
- [ ] Directory name reconsidered — `sband_tx` describes the optional half.

---

## 7. Verification plan

Rewritten 2026-09-08 for the DDS milestones. Each gate is stated so that "done"
is not a matter of opinion.

**M0 — symbol engine** ✅ *met*
1. Simulation shows PRBS-7 repeating with a period of exactly 127 symbols, matching a Python golden model on seed, shift direction and output tap.
2. Simulation shows `tx_symbol` changing only on symbol boundaries, at exactly `CLOCK_HZ / SYMBOL_RATE` cycles.
3. On hardware, the alternating pattern measures at half the symbol rate at all four rates. *Measured: 0.000% error at 500 Hz, 5 k, 50 k, 500 kHz.*
4. Loopback checks at least 1,000,000 symbols with zero errors, **and the count is read back**. *Measured: 62,049,047 symbols, zero errors, zero lock losses.*
5. The PRBS captured at the pin decodes and matches the golden model. *Measured: phase 19, exact.*

**M1 — AD9910 bring-up**
6. `SYNC_CLK` is present at SYSCLK/4 — the first thing to check, since it needs no configuration, no SPI and no PLL.
7. `PLL_LOCK` asserts, and the console reports `LOCK 1` with no `TMO`.
8. A measured tone appears at the `OUT` SMA at the programmed frequency, within the tuning-word resolution.
9. Changing the tuning word over the console moves the carrier as computed.

**M2 — BPSK** *(the milestone that matters)*
10. With `PROFILE[0]` driven from `tx_symbol`, the carrier shows unambiguous 180° phase reversals at symbol boundaries, and **no** reversal during a long run of identical bits.
11. The reversals occur at the programmed symbol rate, cross-checked against `symbol_tick`.
12. Captures, tool versions, RTL revision and settings committed to `measurements/`.

**M3 — characterisation**
13. Occupied bandwidth measured against symbol rate on an SDR or analyser, and compared with the sinc envelope expected of unshaped rectangular symbols.
14. Carrier-frequency error measured against the programmed value.

**M4 — beyond BPSK**
15. QPSK via profiles 0–3, or amplitude shaping through the ASF and OSK path, with a measurable sidelobe reduction against the M2 capture under identical settings. The comparison, not the absolute number, is the result.
16. Optionally, the 16-bit parallel port driven from the FPGA — this is where the HDL content the DDS removed comes back.

**M5 — S-band, optional**
17. A signal near 2400 MHz into a dummy load, with the image and LO leakage identified and their rejection measured before and after the band-pass filter.

---

## 8. Decision summary

### As it stands, 2026-09-08

> **Selected:** FPGA-generated symbols driving an **AD9910 DDS in
> profile-switched BPSK**. Two profiles at the same frequency 180° apart,
> `PROFILE[0]` driven from `tx_symbol`. BPSK on a real carrier, out of a
> coaxial connector, for one FPGA pin.
>
> **Unchanged:** the symbol engine. Framing, symbol timing, PRBS generation and
> checking feed the DDS exactly as they would have fed a converter. M0 is
> complete and unaffected.
>
> **Deferred:** the S-band front end. The AD9910 reaches about 400 MHz, so
> 2.4 GHz still needs a mixer — M5, and still off the critical path.
>
> **Held for M4:** the AD9910's 16-bit parallel port, which takes amplitude,
> phase or frequency words at up to 250 MSPS. That is where QPSK and pulse
> shaping go, and it restores most of the HDL content that profile-pin BPSK
> removes.
>
> **Net benefit:** BPSK arrives at M2 instead of M3, with far less RTL, at a
> higher and cleaner carrier than the DAC path would have produced.
>
> **Net cost:** the NCO, sine table, upsampler and RRC FIR that justified the
> original selection are gone, replaced by SPI control and a register map.
> Different learning, not free.

### As originally decided, 2026-09-05 — superseded

> **Selected:** FPGA-generated low-IF BPSK into a DAC902, starting at 20 MSPS with a 1 MHz IF and 100 ksym/s, rising to 50 MSPS / 5 MHz once the interface is proven. The modulated waveform exists at the DAC output and is measured there.
>
> **Adopted as an interim step:** a 1-bit sigma-delta output through an RC filter, to prove the modulator logic before any DAC wiring exists.
>
> **Deferred:** the S-band RF front end and the single-bit phase-modulator architecture. Retained together as the future RF path, reusing the link processor unchanged.
>
> **Rejected:** COTS SDR transmitters (produce a waveform, teach nothing, fail SBX-1 and SBX-3) and running the experiment on the comms board at 437 MHz (fails SBX-10 and SBX-3).
>
> **Moved off the critical path:** the Tektronix A20 oscillator. It cannot serve as the LO for the selected RF plan, and remains a worthwhile independent characterization exercise.

The rejections still hold — a COTS SDR still teaches nothing, and the comms
board is still the mission radio rather than an experiment bed. What changed is
that the hardware on hand implements the option this study deferred, and does it
better than the discrete build it imagined.

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
