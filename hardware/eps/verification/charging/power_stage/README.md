# Charger power-stage sizing checkpoint

2026-10-23. Run `python3 calculate.py` to reproduce `results.json`. This is a
development circuit allocation for the approved LTC4162IUFD-LADM#TRPBF library
candidate, not a complete charger or authorization to bypass protection. No CAD
mutation is made here. The exact reference circuit must still be integrated and
verified after library acceptance.

## Development choices

| Role | Proposed part/value | Basis and remaining condition |
| --- | --- | --- |
| Charge and input shunts, separate parts | CRF1206-FZ-R033ELF, 33 mΩ, 1%, 50 ppm/K, 1 W P70 | About 0.970 A nominal full scale; Kelvin traces at each termination. Cell/source acceptance remains open. |
| RT | TNPW060363K4BEEA, 63.4 kΩ, 0.1%, 25 ppm/K, 0603 | Datasheet frequency test point: 1.4–1.6 MHz. Procurement and actual field metadata still require readback. |
| Charger inductor | XAL6060-153MEC, 15 µH, 20% | Prefer over the earlier 10 µH candidate for tolerance/bias margin; require at least 7.52 µH through actual peak current and temperature for this screen. No native substitution yet. |
| INFET and BATFET | CSD18543Q3A, one per function | Electrical candidate: 60 V, maximum 15.6 mΩ at 4.5 V gate drive/25°C. Physical land acceptance remains open; [manufacturer footprint construction proposal](../../../design/rev_b_charger_powerpath_footprint_rules.md) awaits approval. |
| VOUT hot-loop bank | Four CGA5L1X7R1H106K160AC, 10 µF/50 V/X7R/10%/1206 each | 40 µF nominal; final effective capacitance, ripple and loop response require verification. Place directly at VOUT/PGND. |
| BATSENS+ bank | Two of the same 10 µF/50 V parts | Require at least 10 µF total effective, not merely 20 µF nameplate. All battery sensing stays after hardware isolation. |
| INTVCC bypass | One of the same 10 µF/50 V parts | Require at least 4.7 µF effective at the actual internal-regulator voltage. |
| VCC2P5 bypass | GRM21BR71A475KE51L, 4.7 µF/10 V/X7R/10%/0805 | Require at least 1 µF effective; the 1 µF nameplate alternative has insufficient tolerance margin to claim that minimum. |
| VIN, VOUTA and DVCC bypass | GRM188R72A104KA35D, 100 nF/100 V/X7R/10%/0603 each | Existing project candidate; voltage rating does not establish effective capacitance. |
| BOOST | 22 nF ceramic, at least 6.3 V | GRM188R72A223KAC4D is a candidate; package suffix/current supplier specification still need verification. Do not use the obsolete GRM188R71H223KA01D merely because its old datasheet exists. |

The [LTC4162-L Rev A](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf),
printed pp.5, 10–11 and 30–33, provides the servo, bypass, inductor and PowerPath
requirements. Its complete project-local PDF was read for this analysis. For
2S, CELLS1 connects to INTVCC and CELLS0 to VCC2P5; ground unused SYNC. DVCC
and bus pull-ups use the essential +3V3 supply. Charger ground is system GND,
not raw BMS VSS. No battery Kelvin/sense wire may bridge RBF.

## Quantitative checks

At 35 V and 1.4 MHz, the manufacturer's inductor relation gives 7.5 µH. Applying
the stated inverse RT relation to 0.1%/25 ppm/K resistor variation over 65 K
gives a further screening corner of 1.3963 MHz and 7.5197 µH. This extrapolation
is not an additional frequency guarantee. A 4.7
or 6.8 µH nameplate cannot meet that value even before bias. A 10 µH/20% part
has only 8 µH before further losses. The proposed 15 µH part starts at 12 µH
at its negative tolerance corner and permits a further 37.34% reduction before
reaching 7.5197 µH. That is a design allowance, not a guaranteed bias/temperature
curve. [Coilcraft's XAL60xx table](https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/xal/xal60xx/)
lists 43.8 mΩ maximum DCR at 25°C, 5.8 A typical 30%-drop Isat and 4.5/6 A
reference RMS currents for 20/40°C rise for the 15 µH part. Actual AC/core loss,
hot inductance and control-loop behavior remain to be checked.

Using ±0.75 mV charge-servo accuracy and assuming the shunt TCR across a 65 K
excursion gives 0.9346–1.0057 A at full scale. This is a sensitivity: the Bourns
TCR test is +25 to +125°C, and the charger accuracy table has stated electrical
test conditions. In particular, input-servo ±0.2 mV has no full-temperature dot;
do not describe the 33 mΩ input resistor as a guaranteed 1 A source ceiling.
More fundamentally, the input-current loop reduces charging to prioritize
system loads; it does not act as a series current breaker for those loads.
Even perfect shunt accuracy would not establish that ceiling. The source
protection study's 1 A fixture bound must come from independently bounded
source capability, not from this charger setting.
The 45 mV peak threshold is typical only. Neither it nor a 1 A charging setting
limits total battery discharge or protects a failed-short switching device.
[Bourns CRF specification](https://www.bourns.com/docs/product-datasheets/crf.pdf).

For one CSD18543Q3A, 2/4/6 A gives 62/250/562 mW using the 25°C maximum
resistance. Doubling resistance gives 125/499/1123 mW as a hot sensitivity,
not a temperature guarantee. The two PowerPath FET roles do not normally add
as two series resistors in one path; evaluate their actual operating states.
The [TI SLPS633 datasheet](https://www.ti.com/lit/ds/symlink/csd18543q3a.pdf),
pp.1, 8 and 9, was actually rendered and inspected. Its drain region joins the
right-hand terminals and exposed metal; the stock symbol uses five logical
pin numbers, not eight independent drain connections. Stock footprint readback
has a custom-shaped drain pad and lands differing from TI's recommendation;
that readback alone does not accept its detailed shape or assembly process.

## Source loading and damping

The proposed VOUT/VOUTA additions increase nominal SYS capacitance from 102.6
to 142.7 µF, before any input damper or other circuitry. This revises the load
used for source-switch inrush studies; it is not a new accepted source budget.

ADI's example 2.5 Ω + 150 µF series shunt branch has ideal impedance magnitudes
2.716/2.525/2.502 Ω at 1/3/10 kHz. It is not a resistor in the main power path.
An ideal 35 V step would deposit 91.9 mJ in its resistor with 490 W initial
power and a 375 µs RC time constant. Therefore no small generic resistor or
bulk-capacitor substitution is accepted here. Select pulse-rated parts and
evaluate the complete source/filter/charger model before implementing this
branch. Existing low-ESR source bulk is not proof of that damping impedance.
The subsequent [damper checkpoint](../input_damping/README.md) proposes a
2.7 Ω power resistor and 204 µF hybrid bank, checks capacitor-short loading
and shows why the combined source/system bank still needs input-loop review.
The 150 µF example is not the current startup allocation.

## Remaining release gates

Default adjustable-variant 4.2 V/cell with +1.5% full-temperature error can
reach 8.526 V for 2S. Normal charge limits and sensor thresholds must be
coordinated with independently commissioned BMS/cell limits before use. A host
write is not the only safety barrier during boot or host failure.

The charger PowerPath and BMS still need an autonomous charger-to-pack
overvoltage fault boundary: a 35 V failed-short switching path can exceed the
BMS PACK/BAT/VCC pin limits. Ordinary BMS FETs or the charger current servo do
not establish containment. RBF, BMS state recovery, weak-source startup,
capacitor bias/aging bounds, thermal operation, all power-off bus paths and
the physical sensor harness remain integration gates. This record does not
close any of those by treating typical curves as guaranteed limits.
