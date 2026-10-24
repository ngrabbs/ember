# Added source-inductance sensitivity

2026-10-24. Extends the [input-limiter investigation](../input_limiter/README.md). **No input limiter, source inductor, return diode or circuit integration is selected by this study.**

Two completed typical-model runs add a deliberately imposed1.232 µH /10 mΩ inductor between the650 µF source bank and LTC4231 input shunt. A generic diode returns that node to the upstream bank when the controller opens; a100 nF controller-input bypass remains downstream of the inductor. Existing5.6925 µF buck input capacitance stays downstream of the pass MOSFET. This is an added engineered source element, not an assumption that a harness provides this inductance. No vendor model was changed. The buck proxy, forced controller bias, linear inductors and generic clamps retain all previous limitations.

| Imposed load | Protected peak | Input FET current peak | Added inductor peak | Failed-buck inductor peak |
|---|---:|---:|---:|---:|
| 2 A | 3.28521 V | 56.80 A | 63.40 A | 198.53 A |
| No load | 3.38277 V | 56.48 A | 63.07 A | 198.22 A |

The inductor reduces the input MOSFET pulse from about162 A in the earlier comparable case, but transfers a substantial pulse-current/energy requirement to the magnetic and return path. Controller IN reaches37.13 V and about−7.06 V; downstream SOURCE reaches−11.77 V. These are modeled transients, not confirmation of controller operation through those excursions. In particular37.13 V exceeds the36 V recommended operating ceiling even though it is below the40 V absolute ceiling. Full FET trajectory/hot SOA, controller bias behavior and input/output clamp interaction remain open.

Input FET gate-to-source peaks at15.86 V, and the output pair stays below6.73 V in these models. Input FET positive port energy in the first millisecond is20.13 mJ, with1.42 kW peak port power. The reduced peak current therefore does not imply reduced absorbed energy compared with the earlier15.49 mJ direct-short experiment. This integral is not an avalanche rating or hot linear-SOA pass; controller retry and return-path behavior remain part of that duty.

The1.232 µH value was an imposed sensitivity, not a published combined minimum. As a practical check, [Coilcraft XGL1060-222MEC](https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xgl/xgl1060/xgl1060-222/) lists2.2 µH±20% and31 A at30% inductance drop at25°C; [XGL1010-222MED](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xgl/xgl1010/xgl1010-222/) lists36 A at that drop. Neither establishes a1.232 µH floor at the observed63 A, across temperature. They therefore do not justify selecting the linear source-guard model. Saturation reference is distinct from RMS thermal rating and pulse survival. No larger magnetic is silently assumed to fit the PCB.

`run.py` preserves the exact modified driver; original model hashes, raw hashes, portable decks and normalized completed logs are archived. Vendor models/raw files remain external. `archive.py` checks original files and generates the plot. Root actually opened `source_guard.png`; this is simulation-plot inspection, not native sheet inspection. Two Gear cases at0.5 µs maximum step are not a convergence or worst-case guarantee. No repeated/corner/hardware pass is claimed.

The schematic baseline before this investigation is2600a17. This source-guard study performs no native mutations. The independent ADC development build may subsequently change the main graph under its own contract, so this study does not assert a continuing whole-repository native freeze. The source-inductance direction remains unselected until a real magnetic/return network, controller voltage range, physical fit and full fault interruption duty can be supported. The rail-measurement block proceeds independently without treating this protection study as released.
