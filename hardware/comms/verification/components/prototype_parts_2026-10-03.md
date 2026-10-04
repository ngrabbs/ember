# Prototype RF parts — October 3, 2026

These selections are saved in both schematic and PCB. They close exact ordering
identity for this prototype; they do not establish measured RF performance.

| Ref | Manufacturer / exact MPN | JLCPCB | Observed stock / orderable |
|---|---|---|---|
| L16 | Coilcraft 0805HP-221XGRC | [C40877572](https://jlcpcb.com/partdetail/Coilcraft-0805HP221XGRC/C40877572) | 250 / 250 |
| D15 | Nexperia PESD5V0F1BLD,315 | [C478204](https://jlcpcb.com/partdetail/Nexperia-PESD5V0F1BLD_315/C478204) | 1,287 / 1,200 |
| J9 | Molex 734151471 | C588477 | 7,269 / 7,018 |

Live page observations on October 3. All are available for assembly; L16/D15
are Extended SMT parts, J9 is a wave-solder part. Order-time availability,
assembly service eligibility and BOM/CPL preview still need confirmation. No
parts were purchased or reserved. Retain U9 PSA4-5043+ / C5240848.

## L16 engineering disposition

Keep the existing 220 nH bias circuit and audited `Ember_RF:L_Coilcraft_0805HP`
footprint. G changes tolerance from J=5% to G=2%; termination and package remain
the same. [Physical mapping audit](l16_footprint_acceptance.md) applies unchanged.
[Coilcraft document 1362](https://www.coilcraft.com/getmedia/c30565bc-9cf5-4393-9380-6f782e4b4cd8/0805hp.pdf)
gives 930 MHz typical SRF, Q75 typical at 250 MHz, 0.426 ohm maximum DCR and
0.5 A reference current. Ideal reactance at 435 MHz is 601 ohms, not a measured
impedance guarantee. At 100 mA the stated DCR gives 42.6 mV / 4.26 mW.
Mini-Circuits' PSA4-5043+ application circuit uses an output bias choke and notes
0.1–0.2 ohm typical resistance; this choke's maximum DCR is higher.

The historical >1.5 GHz SRF target remains **unmet**. Retaining the existing
prototype choke is an explicit prototype exception, not production approval.
Bench gates: measure gain, noise/sensitivity, return loss, bias isolation and
stability across the operating band and supply range. Swap/tune L16 if needed;
use current-limited power and inspect the supply for RF oscillation.

## D15 package and pin acceptance

Source: [Nexperia PESD5V0F1BLD datasheet](https://assets.nexperia.com/documents/data-sheet/PESD5V0F1BLD.pdf),
14 April 2023, page 2 transparent top view and page 8 land pattern, both visually
inspected. Package DFN1006D-2 / SOD882D, body 1.0 × 0.6 mm. Two symmetric
back-to-back junctions; no one-way cathode-to-ground requirement.

| Physical pin | Datasheet name | Device:D_TVS symbol | PCB pad / net |
|---|---|---|---|
| 1 | K1 | 1 / A1, passive | 1 / GND |
| 2 | K2 | 2 / A2, passive | 2 / ANT |

The symbol's A1/A2 names are generic terminal names. Footprint
`Diode_SMD:D_SOD-882D` has two electrical pads, 0.5 × 0.7 mm at x=±0.4 mm,
matching 1.3 mm outer span and 0.3 mm gap. Two additional unnumbered 0.3 × 0.6 mm
paste apertures at x=±0.35 mm explain the reported four pad objects; they are
not extra electrical pins. Existing disposable-instance checks and live pad
readback confirm the mapping. No footprint replacement or rerouting is needed.

Rating: 5.5 V standoff; 0.4 pF typical / 0.55 pF maximum capacitance; 10 kV
contact and 10 kV air ESD rating. Air rating is lower than the prior BRLD's
15 kV. These component ratings do not certify system-level ESD immunity.

Conditional prototype operating envelope: forward peak-envelope power at the
antenna port no greater than +20 dBm (100 mW), with VSWR no greater than 2:1.
For 50 ohms, Vpk=sqrt(2*P*Z)*(1+|Gamma|): 3.16 V matched and 4.22 V at 2:1,
below 5.5 V. Full reflection would reach 6.32 V; this selection does **not**
establish open/short antenna tolerance. Include modulation overshoot and
measurement uncertainty when setting drive. The ADL5602 compression figure is
not a guaranteed output limiter. Firmware does not enforce this envelope yet.
Begin into a rated 50-ohm dummy load at low drive; measure output/spectrum and
set drive limits before connecting an antenna. Verify antenna VSWR first.

## J9 and saved-design checks

Ordering fields now identify the existing Molex connector. Physical clearance
is closed by the user's installed-fit confirmation: top board, no board above,
16 mm standoffs. See [launch review](../j9_launch_and_fabrication_requirements.md).

Schematic edits used Konnect. The CLI-based sync dry run incorrectly omitted
unnamed nets and was not applied. Native KiCad synchronization reported only
L16/J9/D15 fields, D15 value, and existing unit metadata updates, with zero
warnings/errors. Footprint replacement and deletion were disabled.

Exported BOM and saved PCB field readback agree on all three MPN/LCSC pairs.
Fresh saved-board DRC: **0 errors, 0 unconnected items, 1 warning** (the existing
fixed H1/H2 silkscreen overlap). Pad assignments still agree with the previously
validated 209-net native netlist: 556 pad-map entries, zero mismatches. This was
a part-field/value update; no circuit wires or copper geometry were changed.
