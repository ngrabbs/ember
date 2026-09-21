# U9 replacement: circuit-specific screening — 2026-09-09

The exported native netlist confirms the existing receive chain: RX filter C67 (3.9 pF) directly feeds U9 input; U9 output is biased through L16 (220 nH), and C75 (100 nF) connects directly to U10 ADE-1+ RF input. There is no attenuation stage between U9 and the mixer. Therefore a higher-gain amplifier directly reduces antenna-referred mixer headroom, rather than simply improving receiver sensitivity.

## TQP3M9036 numerical screen

Calculated from the manufacturer's 5 V, 68 mA typical, 25 °C S-parameter table. The 435 MHz point is linear interpolation of complex S-parameters between 400 and 600 MHz; it is not measured data.

| Frequency | Gain | Rollett K | Magnitude of determinant |
|---|---:|---:|---:|
| 400 MHz | 24.800 dB | 1.126 | 0.621 |
| 435 MHz, interpolated | 24.406 dB | 1.122 | 0.627 |
| 600 MHz | 22.500 dB | 1.116 | 0.634 |

K > 1 and determinant magnitude < 1 meet the linear two-port unconditional-stability criterion at these sample points under the source's test conditions. The margin is modest. This does not establish stability over all frequencies, bias, temperature, actual package routing or real filter impedances. No 435 MHz noise figure is guaranteed by this table.

Source: [Qorvo manufacturer datasheet, pages 2–4, distributed by Mouser](https://www.mouser.com/datasheet/3/1081/1/TQP3M9036_Data_Sheet.pdf).

## Concrete implementation dependencies

- U9 input changes from old package pin 3 to new pin 2; output/DC from old pin 1 to new pin 7. New exposed paddle must connect to RF/DC ground. Verify the complete physical land pattern before library creation.
- Manufacturer reference circuit uses a 68 nH choke, but explicitly describes choke value as non-critical provided its reactive impedance is high at the operating frequency. At 435 MHz ideal 68 nH gives about 186 Ω and ideal 220 nH about 601 Ω. These ideal numbers do not include self-resonance or parasitics and are not sufficient for selecting L16. Qualify the stocked exact choke model with the amplifier network before changing its value or ordering code.
- Do not add another input coupling capacitor blindly: C67 is already the final series capacitor of the RX filter. Its loading changes with the amplifier input impedance.
- C75's 100 nF value differs from the manufacturer's 100 pF reference coupling capacitor. Its actual RF impedance/model must be included; do not equate nominal capacitance to RF performance.
- The shutdown divider is optional per the manufacturer; unloaded divider leaves the amplifier ON. Decide whether TX shutdown is required after checking switch isolation and receiver exposure. Direct IC shutdown thresholds differ from evaluation-board control thresholds.
- Determine mixer input compression/headroom using an accessible manufacturer specification, then propagate the actual loaded gain from antenna to mixer. Do not treat the LNA's +20 dBm output compression figure at 900 MHz as the receiver's usable dynamic range.

## J9 verification status

The installed standard KiCad footprint identifies exactly Molex 73415-1471. Its library geometry has a central signal hole and four ground holes at (±1.27, ±1.27) mm, all 0.84 mm drill. The manufacturer catalogue confirms a vertical 50 Ω MMCX through-hole jack, but its linked sales drawing failed to download. The catalogue lists 2.4 mm recommended PCB thickness, so also check protrusion and mechanical retention on the planned 1.6 mm board. Do not mark the complete mechanical verification closed on footprint name alone.

Catalogue: [Molex document distributed by RS](https://docs.rs-online.com/14f8/0900766b813c49e0.pdf).

No schematic/PCB changes in this pass. The earlier DRC remains the latest layout check. Ordering gaps remain J9, L16 and D15; U9 remains a proposed replacement. Saved results are screening evidence, not fabrication release.
