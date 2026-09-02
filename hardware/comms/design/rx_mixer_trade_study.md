# RX Mixer Selection — Trade Study

**Status:** Decision made 2026-04-30 — ADE-1+ passive mixer with PSA4-5043+ LNA selected over SA612 active mixer.

**Driver:** SA612 family (SA612, SA602, NE602) availability has collapsed across major distributors. Mini-Circuits ADE-1+ stock on hand. Need a defensible substitute before fabricating the comms board.

This document captures the trade so it can be cited in the final design review and so the reasoning survives the next time someone asks "why didn't you just use an SA612 / why is there an LNA in front of a mixer."

---

## 1. Background

The original RX front-end was an SA612A Gilbert-cell active mixer feeding a baseband Sallen-Key LPF and op-amp gain stage. The SA612 was attractive for one reason: it combined an LNA-equivalent (the Gilbert cell's intrinsic ~14 dB conversion gain) and a mixer into a single SOIC-8 with a 4.5 V supply. Cheap and integrated.

Two problems forced a re-evaluation:

1. **Availability.** SA612A / SA602 / NE602 are end-of-life. DigiKey shows zero stock, JLCPCB doesn't carry them, secondary sources are quoting at 5–10× MSRP with long lead times. Sourcing risk is real for a flight build.
2. **Performance ceiling.** SA612 NF is ~6 dB, IIP3 is ~-15 dBm. For a CubeSat uplink at -90 to -100 dBm, the noise figure dominates the link budget. Any swap was an opportunity to improve the receive chain.

We had four spare ADE-1+ passive mixers from a previous AMSAT project. That triggered this trade.

---

## 2. Requirements

| ID | Requirement | Source | Target |
|---|---|---|---|
| RX-1 | RF center frequency | Architecture | 145.9 MHz (2m amateur band) |
| RX-2 | IF range | AFSK modem | DC – 5 kHz baseband |
| RX-3 | LO source | Si5351A CLK1 | 145.9 MHz, CMOS square wave |
| RX-4 | System NF | Link budget | < 5 dB |
| RX-5 | RF input from antenna | Architecture | -120 to -60 dBm |
| RX-6 | Out-of-band tolerance | Self-TX leakage | Survive +20 dBm @ 437 MHz worst-case |
| RX-7 | Power available | EPS / +5V rail | < 200 mW for entire RX RF section |
| RX-8 | JLC availability | Manufacturing | Stocked at JLCPCB (or already on hand) |
| RX-9 | Single-board layout | Form factor | All RF parts SMD, 1U-compatible |

---

## 3. Options Considered

| Option | Type | Conv gain | NF | LO drive | Supply | Pkg | JLC stock | Notes |
|---|---|---|---|---|---|---|---|---|
| SA612A | Active Gilbert | +14 dB | ~6 dB | ~0 dBm | +5V, 3 mA | SOIC-8 | **0** | EOL, sourcing failed |
| SA602AN | Active Gilbert | +14 dB | ~6 dB | ~0 dBm | +5V, 3 mA | DIP-8 | **0** | Same family, same fate |
| **ADE-1+** | Passive diode ring | **-5 dB** | **~5 dB** | +7 dBm | None | CD636 | Have stock | Selected |
| TUF-3+ | Passive diode ring | -5 dB | ~5 dB | +7 dBm | None | CD636 | Limited | ADE-1+ equivalent, no advantage |
| ADL5350 | Passive | -7 dB | ~7 dB | +5 dBm | None | LFCSP-8 | Yes | Higher loss, no advantage |
| MAX2680 | Active | +14 dB | ~7 dB | -10 dBm | +3V, 8 mA | SOT-23-6 | Limited | Drop-in-ish for SA612, marginal stock |
| Tayloe detector (74HC4066) | Switching/direct-conv | ~0 dB | depends on Rfb | CMOS | +3.3V, ~5 mA | SOIC-14 | Yes | Different architecture; bigger redesign |
| Discrete FET ring | DIY passive | -6 dB | ~5 dB | +7 dBm | None | discretes | Yes | Tunability headache, not worth it |

**Eliminated:**
- SA612 / SA602 / NE602 — sourcing risk, no second source
- TUF-3+ / ADL5350 — no performance advantage over ADE-1+, no incumbent stock
- MAX2680 — would work, but locks us back into the "one active mixer chip" sourcing pattern that already failed once
- Tayloe — interesting, but requires reworking the Si5351A clock plan (need quadrature LO at 4× LO frequency) and rewriting the baseband DSP. Out of scope for this revision.
- Discrete FET ring — too much hand-tuning for limited gain over ADE-1+

**Selected: ADE-1+.**

---

## 4. Architectural Consequence: LNA Required

The ADE-1+ swap costs **19 dB** of conversion gain vs. the SA612 (+14 dB gain → -5 dB loss). That gain has to come back from somewhere in the chain, and the right place is **before** the mixer rather than after, for noise figure reasons.

**Friis cascade math:**

| Configuration | NF_sys |
|---|---|
| SA612 only | ~6 dB |
| ADE-1+ alone + IF amp at end | dominated by ADE-1+ NF (5 dB) plus IF-amp NF referred back through the lossy mixer → degrades to ~12 dB+ |
| ADE-1+ with LNA (NF=3.5 dB, G=17 dB) in front | NF ≈ 3.5 + (10^0.5 − 1)/10^1.7 ≈ **3.6 dB** |
| ADE-1+ with LNA (NF=1.0 dB, G=21 dB) in front | NF ≈ 1.0 + (10^0.5 − 1)/10^2.1 ≈ **1.0 dB** |

Either LNA option beats the original SA612 design. The LNA placement matters more than the LNA NF — getting *any* gain in front of the mixer transforms the cascade.

---

## 5. LNA Sub-Trade

JLCPCB inventory survey (2026-04-30):

| Part | Stock | Gain @ 145 MHz | NF | OIP3 | Supply | Verdict |
|---|---|---|---|---|---|---|
| MAX2611EUS+T | 374 | ~17 dB | ~3.5 dB | +14 dBm | +5V, 20 mA | Viable, simpler |
| BGA2851,115 | 0 | ~22 dB | ~1 dB | — | +3V, 5 mA | Out of stock, eliminated |
| **PSA4-5043+** | 1157 | **~21 dB** | **~1 dB** | +38 dBm | +3 to +5V, 60 mA | **Selected** |
| MGA-30889 | 0 | ~14 dB | ~0.5 dB | — | +3V, 60 mA | Out of stock, eliminated |

### PSA4-5043+ vs MAX2611 head-to-head

**PSA4-5043+ wins on:**
- Noise figure by 2.5 dB — directly buys back 2.5 dB of link margin, equivalent to extending a usable pass by several minutes of elevation
- Linearity (24 dB more OIP3) — survives strong out-of-band emitters (Earth-pointing antennas pick up paging, radar, FM broadcast leakage)
- Stock depth (3× higher at JLC)
- Documentation quality (Mini-Circuits publishes full S-parameter files, suitable for QUCS/LTspice modeling)
- Self-biased pHEMT — only Vd and an RF choke needed externally

**MAX2611 wins on:**
- Current draw — 20 mA vs 60 mA on the +5V rail (200 mW penalty for PSA4)

### Resolution

The 200 mW penalty was the only argument for MAX2611. Evaluated against:
- Total comms board RX budget: ~100 mA on +5V (was ~80 mA with SA612)
- New total with PSA4: ~140 mA on +5V = 700 mW — within RX-7 budget if RX is duty-cycled
- LNA bias can be GPIO-gated (route +5V_LNA through a small load switch driven by RP2040) if duty-cycled receive is needed — reduces orbital-average to negligible

**Selected: PSA4-5043+.** NF advantage of 2.5 dB is permanent and irrecoverable; current penalty is mitigable.

---

## 6. Final RX Chain Architecture

```
RX SMA → 2m BPF → PSA4-5043+ → DC block → ADE-1+ RF
                                              ↑
                                  CLK1 → DC block → LO LPF
                                              ↓
                                         ADE-1+ IF → 51Ω term → DC block → Sallen-Key LPF → MCP6022 gain → ADC
```

**Component additions vs SA612 design:**
- U10 — PSA4-5043+ LNA (SOT-89)
- L12 — Vd bias choke (1 µH wirewound, SRF > 500 MHz)
- C53, C54 — LNA input/output DC blocks
- C55, C56 — Vd bypass (100 nF + 10 µF)
- L13, L14, C57, C58, C59 — 5-pole LC LPF on LO (Butterworth, fc ≈ 200 MHz)
- R19 — 51 Ω IF port termination

**Component removals vs SA612 design:**
- U3 was SA612 → now ADE-1+ in CD636 footprint
- C21, C22 — SA612 supply bypass (passive mixer needs no supply)
- C26, C27 — single-ended AC grounds for unused SA612 differential pins
- R7 — 1 kΩ SA612 IF load (ADE-1+ is naturally 50 Ω)

---

## 7. Link Budget Impact

For a 2m uplink from a typical amateur ground station:

| Parameter | Old (SA612) | New (PSA4 + ADE-1+) |
|---|---|---|
| System NF | ~6 dB | ~1.0 dB |
| Antenna → mixer signal path | -90 dBm (typ) | -90 dBm |
| Signal at ADC after gain | reasonable | +5 dB higher SNR |
| 1 dB compression point (IIP) | ~-15 dBm | ~+0 dBm (mixer) preceded by LNA P1dB = +0 dBm input |
| Out-of-band overload tolerance | Marginal | Much improved |
| 437 MHz TX leakage rejection | 2m BPF only | 2m BPF + LO LPF |

**Net: ~5 dB improvement in link margin** for the cost of one additional IC and ~150 mW continuous receive power.

---

## 8. Risks and Open Items

| Risk | Severity | Mitigation |
|---|---|---|
| Si5351A LO drive insufficient for +7 dBm at mixer LO port | Medium | Bench-verify with spectrum analyzer at CLK1_OUT into 50 Ω before fabrication. Drop R4 (33 Ω series) to maximize drive. If still low (<+4 dBm), add a small LO amplifier (BFR93A or ERA-2+). |
| LO square-wave harmonics create spurious mixer responses (3rd harmonic at 437.7 MHz coincides with our own TX) | High | 5-pole LPF on LO line provides ~34 dB rejection at 3rd harmonic. Verify on bench with mixer-output spectrum sweep. |
| PSA4-5043+ stability at VHF with 50Ω source/load | Low | Mini-Circuits publishes S-params and K-factor — both indicate unconditional stability across 50 MHz–4 GHz. Layout grounding still matters; follow app-note ground via pattern. |
| LNA P1dB exceeded by strong out-of-band signal | Low | PSA4 P1dB(out) = +20 dBm → input P1dB ≈ -1 dBm. Antenna would need to see -1 dBm of unfiltered RF before LNA compresses. 2m BPF rejects most plausible offenders. |
| Power budget margin shrinks | Low | LNA bias can be GPIO-controlled (load switch on +5V_LNA rail) to duty-cycle receive. RP2040 can gate it via spare GPIO. |
| ADE-1+ footprint must be drawn in Altium (CD636 not in default libraries) | Low | Mini-Circuits publishes recommended PCB land pattern in the datasheet (this one, p.1). One-time CAD task. |

---

## 9. Verification Plan (for bring-up)

Before committing to fab:
1. **LO drive level** — measure CLK1_OUT power into 50 Ω terminator with spectrum analyzer. Must be ≥ +5 dBm at 145.9 MHz fundamental, with 3rd harmonic at 437 MHz ≥ 30 dB below fundamental after LO LPF.
2. **LNA gain and NF** — characterize PSA4 on a breakout board with VNA before designing it into the comms board.
3. **Mixer conversion loss** — feed -50 dBm at 145.9 MHz RF, +7 dBm at 145.9 MHz LO, measure IF baseband output level. Expect ~5 dB conversion loss.
4. **End-to-end** — inject -100 dBm test signal at RX SMA, verify ADC sees recognizable AFSK tones.

After fab:
5. Full cascaded NF measurement (Y-factor method or noise source) — verify system NF < 5 dB target.
6. IIP3 measurement — verify > -20 dBm input intercept (margin over weakest expected uplink).
7. Self-TX leakage test — key transmitter at full power, measure IF noise floor. Must not desense receiver.

---

## 10. Decision Summary

> **Selected:** ADE-1+ passive diode mixer + PSA4-5043+ LNA, with a 5-pole LC low-pass filter on the LO line and a 51 Ω termination on the IF port.
>
> **Rejected:** continued use of SA612 family (sourcing), MAX2680 (sourcing pattern risk), MAX2611 LNA (NF penalty), Tayloe detector (scope).
>
> **Net benefit:** ~5 dB link margin improvement, second-sourced parts, better long-term sourceability.
>
> **Net cost:** one additional IC, +150 mW continuous receive power (mitigable via GPIO duty-cycling), new CAD footprint for CD636.

---

## 11. Cost revisit — all-UHF context (2026-08-17)

The all-UHF architecture change (RX moved to 435 MHz — see
[`../bringup/pcb_first_power_on.md`](../bringup/pcb_first_power_on.md)) plus
BOM-cost pressure (**ADE-1+ at $6.00 is the single most expensive part on the
comms board**) reopened the mixer choice. Re-surveyed for a cheaper 435 MHz part:

**Cheap active mixer ICs — none available:**
- SA612 / SA602 — still EOL (the original reason we left).
- BF1105 / BF1109 dual-gate MOSFETs — not in JLCPCB stock.
- AD8342 — $7.56 (dearer than the ADE-1+; no saving). AD831 — $32 (way over).

**Tayloe detector (quadrature sampling) — HF-only, not viable at UHF** (confirms
the earlier "scope" rejection). Appealing on paper: ~$1–2, ~1 dB loss (vs the
ring's 6 dB → better NF), high IIP3, native I/Q for the Pico, no image. **But it
needs a switching clock at 4× the RX frequency = 4 × 435 = 1740 MHz** to drive
the ÷4 quadrature ring counter — beyond the Si5351A (~200 MHz), the CMOS switch
(FST3253-class, a few hundred MHz), and the ÷4 logic (74AC/HC ~200 MHz).
Clocking it would need a UHF synth (ADF4351 ~$8) + fast ECL dividers, erasing
the saving. The Tayloe is fundamentally an HF/low-VHF technique.

| Option | Cost | Trade |
|---|---|---|
| **Keep ADE-1+** | $6.00 | integrated, known-good, LO chain validated; priciest single part |
| Discrete diode ring (quad Schottky + 2 SMD baluns) | ~$2.5 | saves ~$3.5, **always in stock** (no EOL risk), still passive (loss + 7 dBm LO), + baluns/tuning/board space |
| Single-transistor mixer (e.g. 2SC3356) | ~$0.5 | cheapest, some gain, but poor LO-RF isolation & dynamic range — riskiest |

**Decision (2026-08-17): KEEP the ADE-1+.** For a senior-design build of a few
units, the ~$3.5 a discrete ring saves is outweighed by the design time, two
baluns, board space, and VNA tuning — engineering hours cost more than the part
saving. **Discrete diode ring held as the cost-reduction fallback** if the build
scales to many units or the budget tightens (Schottky quads + baluns never go
EOL — dodges the SA612 problem). An active mixer would be preferred (gain + only
~0 dBm LO → could drop the LO amp), but none is available at UHF at a sensible
price. Note the dependency: the validated RX-LO chain (+12 dBm, padded to +7)
assumes the ADE-1+; a future active mixer would let the LO chain shed its amp.

---

## Related Documents

- Schematic instructions: [`schematic_guide.md`](schematic_guide.md) — Sheet 4 updated with new front-end
- RX chain notes: [`rx_chain.md`](rx_chain.md)
- ADE-1+ datasheet: [`C2942210.pdf`](C2942210.pdf)
- Architecture overview: [`overview.md`](overview.md)
