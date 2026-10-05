# EPS Rev B battery and solar isolation study

Draft dated 2026-10-03. Recommend evaluating separate back-to-back P-channel MOSFET pairs for battery and solar isolation, controlled directly by hardware interlock contacts. This gives a compact starting circuit without an MCU startup dependency. The topology is selected for evaluation; exact parts, gate networks, transient protection and depleted-pack recovery are not yet validated. No CAD source has been changed.

[Architecture plan](rev_b_plan.md) · [Pin and fit study](rev_b_pin_and_fit_study.md) · [Inhibit authority](../../../docs/architecture/inhibit_and_deployment.md)

## Power paths and gate control

Place the battery isolation pair after the independent pack-protection FETs and before every charger battery connection and downstream battery feed. Place the solar isolation pair after the face blocking diodes and before the charger's input network. Retain the LTC4162 input and battery PowerPath MOSFETs; the new pairs have separate hardware-shutdown responsibility.

For each pair, connect the two P-channel sources together and their gates together. The drains form the two external power terminals. Their opposing body diodes prevent a complete diode-only path through the pair when off. [TI SLVA948](https://www.ti.com/lit/an/slva948/slva948.pdf), §2, describes back-to-back common-source and common-drain switches with bidirectional off-state blocking. The body diodes can still energize the internal common-source node from either terminal; this node must remain inside the isolated gate-control circuit.

```text
Protected battery port -- D [P-FET] S -- S [P-FET] D -- Interlocked battery
                                      |
                              Common source node
                                      |
                     Gate-to-source off resistor and clamp
                                      |
                                Common gates
                                      |
                      Limited gate pull-down through
                      required hardware contact loop
                                      |
                                     GND
```

This is a functional connection sketch, not a complete schematic. The solar pair uses the same arrangement with higher voltage ratings. Closing the permission loop pulls the gate below the common source and permits conduction. Opening it lets the local gate-to-source resistor turn both devices off. Fit gate-source voltage protection and individual gate resistors as required by switching and stability analysis. Confirm turn-off time and immunity to capacitive gate coupling; a large pull-up resistor alone is not sufficient evidence.

Use separate dry-contact loops for the battery and solar gate controls. A two-pole RBF mechanism can open both loops, with deployment contacts or appropriately isolated hardware controls also enforcing shutdown. Do not join the battery and solar common-source or gate nodes. Final pole count, contact ratings, low-current contact reliability and harness pinout require mechanism selection. The two poles of one mechanism share mechanical failures and do not establish two independent hazard inhibits.

No MCU output is required to enable these source paths. The hardware contacts permit power after RBF removal and deployment-switch release; the independent pack protector still controls which battery charge/discharge states are allowed. An MCU-controlled managed-load switch is downstream and cannot override an open interlock.

The off-state gate resistors, clamps and upstream solar blocking network are passive, but their leakage and stored energy still require accounting. If an active gate driver replaces this circuit, explicitly revise the retained-power boundary and identify its source, off-state consumption and isolation. Do not silently add an always-powered controller to the existing BMS-only proposal.

## Candidate components and alternatives

| Option | Evidence | Evaluation decision |
|---|---|---|
| Battery P-channel pair, Si7149DP reference | [Vishay datasheet](https://www.vishay.com/docs/68934/si7149dp.pdf): 30 V magnitude drain rating; maximum 9.4 mΩ at −4.5 V gate drive; PowerPAK SO-8 | Use as a loss/area reference, not an orderable parts freeze. Check actual gate drive at minimum pack voltage and startup. Below its specified drive, do not extrapolate the resistance guarantee. |
| Solar P-channel pair, DMP6023LE reference | [Diodes datasheet](https://www.diodes.com/datasheet/download/DMP6023LE.pdf): 60 V magnitude drain rating; maximum 35 mΩ at −4.5 V; SOT223 | Voltage-class and loss reference. The retrieved document is marked advance information; obtain an accepted current production specification before selection. Gate clamp and charger overvoltage protection remain separate requirements. |
| External N-channel pair with driver | Requires gate voltage above the common source, suitable off-state behavior and operation with either power terminal energized | Alternative if battery conduction loss or inrush control defeats the P-channel solution. Compare complete circuit area, standby current and recovery behavior. |
| LTC4368 circuit breaker | [ADI datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4368.pdf): 2.5–60 V operation, back-to-back N-channel drive, ±50 mV sense thresholds for the −1 variant and −3 mV reverse threshold for −2 | Not the first battery-isolation choice. Normal charging is reverse current in this orientation; thresholds and recovery must allow it. A controller powered from a zero-volt protected port cannot be assumed to reopen itself. The −2 reverse threshold is particularly unsuitable as a drop-in charging path. |

Simple ideal-diode selection is inappropriate for the battery isolation stage because normal charging must pass in the opposite direction to discharge. The independent BMS owns battery fault protection; the isolation pair owns hardware shutdown. The discrete pair does not add current limiting or short-circuit detection by itself.

## Preliminary loss and voltage calculations

For the battery reference, two devices at the specified 25 °C resistance give `Rpair = 18.8 mΩ`. These calculations exclude BMS FETs, both current shunts, connectors, fuse, traces and the managed payload switch.

| Battery current magnitude | Pair voltage drop | Pair conduction loss | Loss with illustrative 2× resistance |
|---|---|---|---|
| 2 A | 37.6 mV | 0.075 W | 0.150 W |
| 4 A | 75.2 mV | 0.301 W | 0.602 W |
| 6 A | 112.8 mV | 0.677 W | 1.354 W |

Use `Vdrop = I × Rpair` and `Ploss = I² × Rpair`. The doubled resistance is a sensitivity case, not a guaranteed hot-temperature maximum or a selected design margin. These currents are sizing scenarios, not measured peaks or trip settings. Establish temperature-adjusted resistance, actual copper thermal paths and transient safe operating area before accepting the circuit. Gate charge and inrush can matter more than steady loss during startup.

For the solar reference, `Rpair = 70 mΩ` gives about 21 mV and 6.3 mW at an assumed 0.30 A total array current. This is an illustrative four-face electrical budget, not proof that all faces are illuminated simultaneously. Include gate-bias consumption in low-light tests.

The [array budget](../../../analysis/power/README.md) lists module open-circuit voltage as 6.91 V at its reference condition. A four-module string is therefore 27.64 V at that condition. The [source voltage and fault budget](rev_b_source_voltage_and_fault_budget.md) now derives 32.164 V at −40°C using the manufacturer’s typical coefficient. Guaranteed cold/AM0 maximum and switching transients remain unknown. The [LTC4162-L specification](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf) allows charging input up to 35 V; using 60 V MOSFETs does not raise that charger limit. Establish the cold voltage envelope and then select coordinated clamp or overvoltage cutoff circuitry, including tolerance and source energy. Do not choose a TVS by nominal voltage alone.

## Charger sensing and recovery

The retained TPS62933F bucks impose an additional constraint: their [maximum operating input is 30 V](https://www.ti.com/lit/ds/symlink/tps62933f.pdf). Because they are fed from PowerPath, the solar envelope must protect them and their input capacitors as well as LTC4162. Use the lowest applicable limit with tolerance and transient margin. Buck EN shutdown does not protect VIN from overvoltage; revise source conditioning or converter selection if necessary. The follow-up study recommends replacing the 30 V buck stages and adding autonomous solar OV isolation inside the RBF boundary.

Keep all LTC4162 battery voltage, current-sense and auxiliary battery connections on the interlocked side. A Kelvin lead to raw cells would cross the cutoff boundary. The BMS reads actual cell nodes; charger measurements observe its local terminal. Evaluate charge regulation and termination with the voltage drop of the complete protection/isolation path. Preserve separate BMS and charger shunts in their selected reference arrangements rather than assuming they can be shared.

The common-source P-channel arrangement can obtain gate bias from either external terminal, which makes charger-side recovery worth evaluating. This does not prove recovery through the independent BMS. Check its charge/discharge FET states, precharge, pack detection, wake sequence and configuration before relying on this path. Never add an unreviewed permanent resistor or diode around the source cutoff to make recovery work.

Solar PowerPath may start essential loads with a missing battery, but that feature does not establish stable startup under weak illumination or wake a shut-down pack manager automatically. Validate the complete charger, BMS, isolation pair and essential buck combination with firmware held in reset. A missing, overdischarged or otherwise unsafe pack must not be charged merely to achieve startup.

## Bench acceptance before schematic freeze

Use a current-limited supply and cell simulator first. For both isolation pairs, test each terminal energized alone, both energized, both current directions where applicable, open contact loops, unplugged harness, supply ramp/brownout, contact bounce and external back-power. Observe common-source voltage, gate-source voltage, cutoff time, residual output voltage and leakage across temperature.

Then test startup capacitance and load steps, including the charger/PowerPath contribution. Calculate and measure MOSFET linear-mode energy during turn-on; select slew control, active drive or an interlocked precharge path if needed. Every precharge path must obey RBF and deployment shutdown. Verify that a downstream short triggers the intended independent protection without exceeding FET, trace or fuse limits.

Finally exercise permitted depleted-pack recovery, BMS charge-only/discharge-only states, solar-only operation and repeated interlock re-actuation. Set numerical acceptance limits from the current envelope, module requirements and launch rules. The exit is a complete component/gate-network specification plus measured or simulated evidence; the present study supplies the topology and sizing basis only.
