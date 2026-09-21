# RF replacement candidates

[Comms sourcing](README.md) · [Open work](../TODO.md)

**Dated candidate evidence from September 9, 2026.** Quantities below are historical
observations, not live stock today. Candidates remain unapplied and unqualified.

## Agreed transmitter scope — 2026-09-09

User confirmed keeping the existing low-power transmitter rather than targeting 1–2 W. Retain the ADL5602 power-stage architecture. Approximate +20 dBm (~100 mW) amplifier compression capability is not a clean-output specification; actual antenna output is expected in the tens of milliwatts and must be measured with filter/switch losses and drive level included.

This supersedes the tentative 1–2 W suggestion and closes the architecture clarification. It does not establish a guaranteed maximum output or antenna VSWR limit. Continue in-stock U9 and D15 replacement qualification within this low-power scope. Check D15 RF voltage margin against measured/limited peak power and antenna mismatch before final acceptance; do not infer mismatch tolerance from this agreement.

- [x] Confirm existing low-power TX architecture; no 1–2 W PA redesign.
- [ ] Qualify stocked U9 replacement and D15 replacement, then apply and validate through KiCad tools.
- [ ] Measure maximum antenna output and verify protection margin, mismatch behavior and TX spectrum.

## Candidate evaluation — 2026-09-09

Status: promising replacement candidates identified; **not applied and not yet fully qualified**. No purchases or PCB/schematic edits in this pass.

## U9: Qorvo TQP3M9036 / C920261

The recorded JLCPCB search found **947 pieces**. This is the preferred candidate to investigate for replacing the unavailable PSA4-5043+.

Qorvo specifies 50–2000 MHz operation and a 2×2 mm eight-pin DFN, requiring a new footprint. Its 5 V current is 68 mA typical, 90 mA maximum under the stated test conditions. Published gain is 24.8 dB at 400 MHz and 22.5 dB at 600 MHz; that makes receiver gain and mixer overload checks necessary. The advertised 0.45 dB noise figure is at 900 MHz, not a guaranteed 435 MHz result. [Qorvo product page](https://www.qorvo.com/products/p/TQP3M9036), [Qorvo datasheet distributed by Mouser](https://www.mouser.com/datasheet/3/1081/1/TQP3M9036_Data_Sheet.pdf).

Implementation requires a verified physical pin map, exposed-pad grounding, new local routing, and review of the choke/DC-block/bypass network. The reference circuit uses a 68 nH choke; retain neither that value nor the current 220 nH blindly. Shutdown-control thresholds at the evaluation-board input differ from those at the IC pin. Avoid attaching the existing logic signal directly without checking the reference divider. No package pin map has yet been accepted for layout.

Qorvo's direct datasheet and S-parameter downloads returned HTTP 429; the distributor-hosted manufacturer datasheet was readable. Complete 435 MHz gain/noise/stability and filter-loading evaluation remains open.

## D15 candidates

| Part | JLC code | Stock evidence | Assessment |
|---|---|---|---|
| Nexperia PESD5V0F1BLD,315 | C478204 | 2,805 catalogue only | Same SOD882D package, but lower air-discharge rating; not selected |
| Nexperia PESD5V0F1BRSFYL | C552550 | **11,452 live** | Preferred candidate for further checking; smaller SOD962 footprint required |

The BLD version retains 5.5 V standoff and 0.4 pF typical capacitance, but its air-discharge rating is 10 kV, versus 15 kV for the current BRLD part. [BLD manufacturer datasheet](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BLD.pdf), [current BRLD manufacturer datasheet](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BRLD.pdf).

The BRSF candidate preserves 10 kV contact/15 kV air ESD ratings and reduces capacitance to 0.25 pF typical/0.3 pF maximum. Its 5 V standoff is lower, and its surge-current rating is 2.2 A versus 2.5 A for BRLD. It is therefore not an identical substitution. [BRSF manufacturer datasheet](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BRSF.pdf).

### Antenna voltage check before choosing D15

For a 50 Ω sinusoidal incident wave, worst-position standing-wave peak voltage is `sqrt(2 × Pforward × 50) × (1 + |Γ|)`, where `|Γ| = (VSWR−1)/(VSWR+1)`. These are simplified voltage ceilings at the diode's nominal standoff, **not approved transmitter-power limits**; allow margin, modulation peaks, tolerances, and the actual diode location/network.

| Standoff | Matched load | VSWR 2:1 | VSWR 3:1 |
|---|---:|---:|---:|
| Candidate 5 V | 24.0 dBm | 21.5 dBm | 20.5 dBm |
| Existing 5.5 V | 24.8 dBm | 22.3 dBm | 21.3 dBm |

The low-power TX architecture is selected; measured peak antenna power and allowed mismatch remain unresolved. Check both current and proposed diode against those limits; low capacitance alone is not sufficient.

## Alternatives screened out or deferred

- TQP3M9037 / C415712: 1,426 live pieces, but its published operating band starts above 435 MHz. Do not choose it just because it is stocked. [Qorvo](https://www.qorvo.com/products/p/TQP3M9037).
- SPF5043Z / C470902: no in-stock entry in the catalogue; not a solution to the sourcing constraint.
- BGA2869,115 / C515583: different package and receiver characteristics; not approved as a low-noise drop-in.

## Next implementation gates

- [ ] Resolve antenna peak-power/mismatch requirement and select D15 with suitable voltage margin.
- [ ] Evaluate TQP3M9036 loading, gain, noise and mixer headroom at 435 MHz.
- [ ] Verify exact symbol-to-package-to-pad maps and manufacturer land patterns.
- [ ] Apply the local schematic/layout changes through KiCad tools, synchronize ordering fields and rerun native checks.

The existing stock shortage remains open until replacements are qualified and applied. This report supersedes the statement that no stocked candidates were known; it does not declare the board ready for fabrication.
