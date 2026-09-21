# Receive chain

[Design guide](README.md) · [RX tests](../bringup/rx_test_plan.md)

**Baseline: 435 MHz RX through the shared J9 antenna.**

J9 → U11 switch → input filter → U9 PSA4-5043+ → U10 ADE-1+ →
baseband filter/amplifier → RP2040 ADC. CLK1 near 145 MHz feeds the RX-LO
tripler/filter path; verify the mixer's +7 dBm LO requirement under actual loading.

## Current design boundaries

- The filter output capacitor C67 feeds U9. L16 supplies RF-output bias; C75 couples
  U9 to the mixer. The recorded design has no post-LNA attenuator.
- TQP3M9036 is a **proposed replacement**, requiring package verification, loaded
  gain/stability/noise analysis, a qualified choke/coupling network, and mixer
  headroom review. See the [U9 studies](analysis/README.md).
- A nominal 6 dB post-LNA pad is under study, not installed or accepted. Its
  selection must account for receiver noise, overload, TX leakage, and RF ratings.
- The baseband bias repair retains a 1.65 V ideal midpoint and ×11 AC gain.
  The equal-R/equal-C unity-gain filter has ideal Q=0.5, f0≈3.29 kHz and
  −3 dB≈2.12 kHz, not the older Butterworth claim. See the
  [calculation record](../verification/baseband_and_header_review.md).

Older VHF/SA612 descriptions and unqualified system-noise claims are superseded.
Verify the assembled chain using the [prototype worksheet](../bringup/rf_prototype_checklist.md).
