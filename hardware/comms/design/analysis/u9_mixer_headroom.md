# U9 → U10 mixer headroom — 2026-09-09

Resolved the mixer specification lookup using indexed manufacturer data: ADE-1+ is a level-7 mixer (+7 dBm LO), with typical input 1 dB compression at +1 dBm. Its 50 mW RF maximum rating is approximately +17 dBm and is an absolute limit, not normal operating power. Source: https://www.minicircuits.com/WebStore/dashboardPdf?model=ADE-1%2B

With the candidate TQP3M9036's interpolated matched gain of 24.406 dB at 435 MHz, the no-pad estimate reaches typical mixer compression at -23.406 dBm at the LNA input. This excludes filter, coupling and mismatch losses and is not an antenna-referred guaranteed limit. Preserve the +7 dBm LO requirement during receiver verification; different LO drive changes mixer behavior.

| Attenuation after LNA | Estimated LNA input at typical mixer compression |
|---|---:|
| 0 dB | -23.41 dBm |
| 3 dB | -20.41 dBm |
| 6 dB | -17.41 dBm |
| 10 dB | -13.41 dBm |

A post-LNA attenuator is a concrete option to improve mixer matching and headroom. For a nominal 50 Ω 6 dB pi pad the ideal values are about 37.35 Ω series and 150.48 Ω for each shunt. Stocked exact values, package parasitics, power and layout still need qualification. At 24.4 dB preceding gain, the ideal 6 dB pad adds approximately 0.0108 to cascaded noise factor (not 6 dB to receiver noise figure). This does not establish total receiver noise figure, whose LNA and filter contributions remain unqualified.

Do not declare even the 6 dB option to be a mixer damage guarantee: the candidate LNA's quoted +20 dBm output compression is specified at 900 MHz, and compression is not a maximum saturated-output bound. Validate worst-case drive, transmitter leakage, switching transients and blocking. A pad improves headroom but cannot alone establish an unrestricted antenna-input rating.

Decision: retain the current PCB while treating a provision for post-LNA attenuation as part of the U9 replacement design. Do not install the higher-gain replacement as a simple package swap. Next implementation work is the verified U9 footprint, choke/coupling selection, loaded network simulation and a stocked attenuator option, followed by layout and ERC/DRC.

J9 sales-drawing downloads remain unavailable through the tried manufacturer/distributor URLs. No change to J9 or the PCB was made. This pass closes the mixer-specification lookup, not RF or mechanical qualification.
