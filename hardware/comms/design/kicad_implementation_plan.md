# Comms Board — KiCad Implementation Plan (all-UHF)

**Scope:** rebuild the comms/transceiver board in KiCad incorporating every
rev-B fix and the all-UHF architecture change. This is effectively a **v2
board** (new RX front end + single antenna), not a patch of the smoked Rev A.
**Status:** analysis phase complete (TX + RX validated in LTspice); this is the
implementation scaffold.

**KiCad project:** [`hardware/comms/kicad/`](../kicad/) — project name `transceiver`

## Source-of-truth references (don't restate — link)

- **Rev-B / analysis log:** [`../bringup/pcb_first_power_on.md`](../bringup/pcb_first_power_on.md) — every finding, validated value, and decision
- **KiCad design rules / stackup / 50 Ω:** [`../../conventions/kicad_jlcpcb_design_rules.md`](../../conventions/kicad_jlcpcb_design_rules.md)
- **Net naming:** [`../../conventions/net_naming.md`](../../conventions/net_naming.md)
- **RF layout:** [`rf_layout_guidelines.md`](rf_layout_guidelines.md)
- **Mixer decision:** [`rx_mixer_trade_study.md`](rx_mixer_trade_study.md) §11
- **CSKB pinmap:** `../../../system/interfaces/cskb_pinmap.md`
- **Validated sims:** `ltspice_simulations/tx_circuit.asc`, `rx_circuit.asc`, `rx_lo_tripler.asc`

---

## 0. Consolidated design (the "decisions BOM")

Everything validated, in one place. Details/rationale in the log.

### TX chain — 437 MHz BPSK downlink (~+11 dBm at antenna)
| Block | Part / value | Notes |
|---|---|---|
| Carrier | Si5351A **CLK0 = 145.67 MHz** | ×3 → 437 |
| BPSK mod | 74LVC1G86 XOR | ⚠ verify full-swing at 145.67 MHz (or 74AUC1G86); R6/C16 does NOT control splatter — do firmware pulse-shaping |
| Tripler | **2SC3356 (R25)**, R5 = 47 kΩ class-C | drops into MMBT3904 footprint |
| **Collector tank** | **L1 = 15 nH + Ctank ≈ 8.2 pF** | ⚠ **L1 → COLLECTOR** (Rev-A bug was L1→base); tank replaces the 220 nH RFC |
| Pre-MMIC BPF | **2-pole cap-coupled Chebyshev**: 2× (10 nH 0402HP-10NXGRW ∥ **9.1 pF** Cres) + **1.6 pF** series coupling cap + **3.9 pF** I/O caps — all C0G ±2% | **In-chain-tuned** (Cres 9.1 p = power peak *and* 583 margin); + tuning pads. **See filter decision note below** |
| MMIC | ADL5602 (+20 dB) | bias tee: 220 nH RFC + 100 n/10 µ, DC block after RFOUT |
| Output BPF | same as pre-MMIC | + tuning pads |

> **Filter decision note (2026-08-18).** TX BPF = **2-pole *capacitively*-coupled Chebyshev**:
> two `10 nH 0402HP ∥ 9.1 pF` resonators, coupled by a **1.6 pF series cap**, with **3.9 pF I/O
> coupling caps** (all C0G). Chosen over the as-built *inductively*-coupled filter (series-L
> coupling, big Cres) and over a 3-pole.
>
> **Filter-alone S21 comparison:**
> - **2-pole cheby:** IL@437 −1.2 dB, 2nd(291) −37 dB, 4th(583) −13 dB. (583 = the weak side —
>   high-side coupling-cap feedthrough, inherent to a 2-pole.)
> - **As-built (L-coupled):** IL −2.9 dB, 2nd −16 dB (basically unfiltered), 4th −25 dB.
> - **3-pole cheby:** rejection superb (2nd −70, 4th −40) **but IL@437 = −10.7 dB** — synthesized
>   too narrow; narrow band × finite inductor Q (~55) blows up IL. Rejected: ~9 dB of TX power.
>
> **In-chain tuning result** (full `tx_circuit`, `.four` on txout, Cres stepped): output power *and*
> 583 rejection both optimize at **Cres = 9.1 pF** — and note the standalone 50 Ω `.ac` *mis-predicts*
> this (it put 9.1 p at 431 MHz); the tank's source impedance shifts the effective center, so
> **tune in-chain, not off the 50 Ω filter sweep.** Winning config vs the as-built chain:
> **power +11.9 dBm** (was +11.3), **worst spur −36.6 dBc @ 583** (was −34 @ 291), **291 crushed to
> −69 dBc.** Cheby wins on *both* power and worst-case spur. Tank (L1 15 nH / C7 8.2 pF) unchanged —
> Cres alone did it.
>
> **Pads / margin:** populate 9.1 pF; adding pad C (→ larger Cres) buys *more* 583 rejection at a
> small power cost — the add-only direction, use only if a spurious-emissions measurement demands it.
> **3-pole stays the only-if fallback** — and if ever built, build it **wide** (more Ccpl) to keep
> IL ~2–2.5 dB.

### RX chain — 435 MHz uplink (all-UHF, half-duplex)
| Block | Part / value | Notes |
|---|---|---|
| Preselector | **2-pole cap-coupled cheby**: 2×(10 nH 0402HP ∥ **9.1 pF**) + 1.6 pF coupling + 3.9 pF I/O (C0G, ±2%) | **Validated**: IL **1.37 dB** (beats 3-pole's 1.9 → better NF), center 432.5 (fine; sits slightly low = *better* 870 rej), FM −91, **870 (LO 2nd) −23 dB**. 9.1 p is E24 std; no tune needed. See RX validation note below |
| LNA | PSA4-5043+ | **broadband** (0.05–4 GHz, internally matched) → no band-specific match needed; **key fix = RF_OUT bias choke L14 1 µH → 220 nH wirewound** (SRF > 1.5 GHz, ≥100 mA). 1 µH self-resonates ~200–400 MHz → capacitive at 435 → shunts RF, kills gain. 220 nH → XL ≈ 600 Ω isolation |
| Mixer | **ADE-1+** (kept) | diode-ring fallback if cost-driven — trade study §11 |
| RX LO | Si5351A **CLK1 = 145 MHz** → 2SC3356 tripler + tank + **cap-coupled cheby BPF** + LO amp | ×3 → 435; **validated +11.85 dBm**, 2nd −70, worst spur −35.5; **pad to +7 dBm** at mixer |
| IF term | 51 Ω | |
| Baseband | Sallen-Key LPF (fc 3.3 kHz) → MCP6022 ×11 → RP2040 ADC | **unchanged** from 2 m design; **noise-limits system NF** — see note |

> **RX validation note (2026-08-18).** Full RX chain re-simmed on the cap-coupled cheby topology (matches the board).
> - **LO chain** (`rx_lo_tripler_cheby.asc`): **+11.85 dBm** at 435, fundamental −121, **2nd(290) −70** (cheby crushes it vs −34 L-coupled), worst spur 4th(580) −35.5. Pad to +7 dBm at the mixer LO port.
> - **Preselector** (`Filters/435_preselector_cheby.asc`, 50 Ω antenna source): 2-pole cheby, **IL 1.37 dB**, center 432.5, FM(100) −91, **870 (LO 2nd) −23 dB**. Kept 2-pole (not 3-pole 36 p) because it *wins on IL/NF* (1.37 vs 1.9) and −23 dB at 870 is sufficient: the **ADE-1+ is double-balanced (~30 dB inherent 2×LO suppression)** → ~50 dB total 870-spur rejection. Slightly-low center is a feature (pushes 870 farther into the stopband). 9.1 pF, no tuning needed.
> - **Cascaded NF (Friis):** front-end (presel 1.37 + PSA4 0.7 dB/21 dB + ADE-1+ ~6 dB) = **~2.2 dB** ✅. **But** the passive mixer's 6 dB loss leaves only ~13.6 dB gain ahead of the MCP6022 baseband amp (~20 dB NF at 50 Ω), so **system NF ≈ 7.7 dB** — baseband-dominated. Acceptable for a ground-station **uplink** (huge link margin). ⚠ **If sensitivity is ever needed**, add ~10–15 dB gain before the mixer (2nd LNA) or a low-noise first baseband stage → system NF back toward ~2.5 dB.

### System
| | |
|---|---|
| Antenna | **single UHF**, shared via **SPDT T/R switch** — **PE4259** (simple, 1× GPIO, integrated charge pump) or **PE42423** (SatNOGS-proven). RFC=antenna w/ **DC-block cap + shunt ESD diode**; RF1=TX_OUT, RF2=RX_IN; CTRL=`TX_ACTIVE` + **pull-down → RX default at boot** |
| Clock | Si5351A: CLK0 145.67 (TX), CLK1 145 (RX LO), CLK2 spare; 25 MHz XTAL, I²C |
| Power | +3V3 / +5V from EPS via CSKB; reverse-protection Schottky; bias tees + decoupling |
| Digital | RP2040 (Pico module): I²C→Si5351A, BPSK_DATA→XOR, ADC←baseband; **firmware pulse-shaping (new)** |
| Stackup | JLC04161H-7628 4-layer 1.6 mm, 50 Ω microstrip (~0.358 mm), solid L2 GND |

---

## Phase 0 — KiCad project setup

- [x] Confirm/repair the `transceiver` project opens clean
- [x] **Physical Stackup** → JLC04161H-7628 entered and verified against jlcpcb.com/impedance; ENIG, impedance-controlled flag set. Confirm L2 is a solid unbroken GND pour under the L1 RF traces when routing
- [x] **Design Rules → Constraints** → per design-rules doc §5.1
- [x] **Net Classes** → `RF` (0.358 mm), `PWR` (0.5 mm), `PWR_HIGH` (1.27 mm) created and assigned. `RF_*`/`LO_*` patterns added for the rename; 30 explicit per-net patterns remain until the RF nets are renamed to the `net_naming.md` convention
- [x] **Custom rule** (`transceiver.kicad_dru`) → copied from `hardware/conventions/jlcpcb_baseline.kicad_dru`; band still to confirm against the fabbed stackup (design-rules §5.3)
- [ ] Confirm the 50 Ω width against the JLCPCB impedance calculator — `RF` class is set to the validated 0.358 mm in the meantime

## Phase 1 — Schematic (by sheet)

### Clock Gen
- [ ] Si5351A unchanged; confirm CLK0 → TX, **CLK1 → RX-LO tripler** (was direct 145.9 LO)
- [ ] Fix the "TODO: these caps are wrong" note on the crystal load caps

### TX chain
- [ ] **Q1: 2SC3356**, footprint verified vs datasheet (1=B,2=E,3=C — matches MMBT3904)
- [ ] **L1 → collector** (fix the Rev-A base/collector wiring error), value **15 nH**
- [ ] Add **Ctank ≈ 8.2 pF** collector→GND
- [ ] Pre-MMIC + output BPF: **cap-coupled cheby** — 2× (10 nH 0402HP ∥ 9.1 p) + 1.6 p series coupling cap + 3.9 p I/O caps (C0G; in-chain-tuned targets) + **tuning pads** at shunt nodes
- [ ] ADL5602 bias tee + DC block; **watch the RFOUT node** (Rev-A U2 short spot)
- [ ] XOR: bench-verify LVC1G86 swing at 145.67 (or swap 74AUC1G86)

### RX chain (all-UHF — largely new)
- [ ] 435 preselector BPF: **2-pole cap-coupled cheby** (10 n ∥ 9.1 p / 3.9 p I/O / 1.6 p coupling, C0G) + tuning pads
- [ ] PSA4-5043+ (broadband, no match needed) — **swap RF_OUT bias choke L14: 1 µH → 220 nH wirewound** (SRF > 1.5 GHz, ≥100 mA; Coilcraft 0603HP / Murata LQW18A)
- [ ] ADE-1+ mixer, 51 Ω IF term
- [ ] **RX-LO tripler** block (clone TX tripler, driven by CLK1) + LO filter + **LO pad to +7 dBm**
- [ ] Baseband (Sallen-Key + MCP6022) — copy from Rev A unchanged

### Power / Digital / Connectors
- [ ] Power: reverse-Schottky, bulk + local bypass, bias-tee supplies
- [ ] Digital: RP2040 pinmap (SPI/I²C/BPSK_DATA per Rev-A revision 0.7), Pico VSYS feed
- [ ] Connectors: **single UHF SMA/MMCX**; CSKB H1/H2 (Pumpkin pinmap); test points
- [ ] **T/R switch**: SPDT **PE4259** (or PE42423) — RFC = antenna via **series DC-block cap + shunt ESD/limiter diode** (SatNOGS pattern); RF1 = TX_OUT, RF2 = RX_IN; CTRL = `TX_ACTIVE` GPIO **+ pull-down (fail-safe RX at boot)**; **VDD ≈ 2.75 V** (PE4259 is *not* 3V3-native → add a small 2.75 V LDO from 3V3/5V, + 100 n bypass) — or use **AS179-92LF** (no VDD rail, 2-line/inverter control). Symbol+FP from **SnapEDA** (stock QFN footprint). Switch IL (~0.35 dB) adds to RX-path NF → front-end NF ~2.5 dB

### Whole-schematic
- [ ] **Footprint pinout audit** — every 3-terminal RF part vs datasheet (2SC3356, ADL5602, PSA4, ADE-1+, 74LVC1G86, MCP6022) — the Rev-A lesson
- [ ] Net names per convention (`RF_*`, `LO_*`, rails)

## Phase 2 — Layout

- [ ] Floorplan: TX chain, RX chain, LO, clock, digital, power zones; keep RF short/straight
- [ ] Solid L2 GND under all RF; via stitching (~λ/20) + via fences on RF traces
- [ ] 50 Ω microstrip for `RF_*`; shunt grounding via 0402 dogbone (not via-in-pad)
- [ ] **Tuning pads** at every BPF shunt node (both TX BPFs, RX preselector, LO BPF)
- [ ] Keep filter caps in the open (no shield can) for VNA rework
- [ ] Power on outer layers; wide rails; multiple vias on high-current transitions
- [ ] DRC clean (incl. the custom RF-width rule)

## Phase 3 — Fab & assembly

- [ ] Gerbers/BOM/CPL; JLCPCB **impedance-controlled** order (JLC04161H-7628); skip test coupon for this run
- [ ] Assembly: hand-populate RF sections; leave tuning pads bare
- [ ] Pre-power continuity: +5V/+3V3→GND open (kΩ+), no rail-to-rail short (the Rev-A check)

## Phase 4 — Bring-up

- [ ] Current-limited first power; touch-test MMICs; verify Vdd at chip pins
- [ ] Si5351A alive (I²C, CLK0/CLK1 present)
- [ ] **VNA-tune the filters** (both TX BPFs, RX preselector, LO BPF) via tuning pads to targets
- [ ] TX chain: tripler output, MMIC output, antenna power (~+11 dBm), spur check (≥33 dBc)
- [ ] RX LO: verify +7 dBm at mixer (like the 145.9 LO drive verification)
- [ ] RX chain: preselector, LNA gain, mixer conversion, baseband tones; **cascaded NF measurement**
- [ ] Self-TX-leakage / half-duplex T/R switching test
- [ ] Log everything in a new `bringup/` entry

---

## Open items / risks to resolve during implementation

- **PSA4 UHF match** — needs S-parameters; design the matching networks (Smith chart / calc), not yet simmed.
- **LO amp choice** — ADL5602 works (+12 dBm, pad to +7) but is power-hungry; pick a smaller LO amp if power-budget-driven.
- **XOR swing at 145.67** — bench-verify LVC1G86; 74AUC1G86 is the faster fallback.
- **T/R switch** — RESOLVED (2026-08-18): SPDT **PE4259** (simple, 1-GPIO) or **PE42423** (SatNOGS-proven), fail-safe pull-down → RX at boot, borrow SatNOGS's antenna DC-block + ESD diode. See RX checklist.
- **Firmware pulse-shaping** — required for real BPSK splatter control (R6/C16 doesn't do it); and the tripler dilutes shaping ×3 (shape more aggressively at 145).
- **Rev-A physical boards** — separate from this v2; if reused, still need the U2 short recheck + Q1 rework (log rev-B items).

---

## Sequencing note

Do it in the phase order above, but the **schematic is the long pole** — get every
block placed and net-named with the validated values before touching layout, so
the layout is one coherent pass (the whole reason we finished analysis first). The
filters and LO go in as "starting values + tuning pads"; the VNA dials them in at
bring-up.
