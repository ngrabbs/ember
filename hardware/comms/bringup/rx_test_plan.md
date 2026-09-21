# RX qualification plan

[Bring-up guide](README.md) · [RX design](../design/rx_chain.md)

**Planned for the 435 MHz ADE-1+ receiver.** The old SA612 procedure is superseded.
Use the [prototype worksheet](rf_prototype_checklist.md) for setup and acceptance limits.

| Stage | Check |
|---|---|
| Input filter | Baseline and candidate S11/S21/S22 with active/bias branches isolated |
| LNA/bias | Gain, current, RF supply leakage, stability and input/output loading |
| Mixer LO | Actual 435 MHz drive at U10 under loading; compare with +7 dBm requirement |
| Headroom | Blocking/compression and any proposed post-LNA pad; include TX leakage |
| Baseband | Midpoint, filter response, gain and ADC headroom against actual circuit values |
| End to end | Sensitivity/demodulation error criterion, switching transients and recovery |

Do not qualify a proposed U9 replacement using only its gain or catalogue noise
figure. Preserve baseline data before any component substitution, and record exact
MPNs, supply conditions, instruments and calibration planes.
