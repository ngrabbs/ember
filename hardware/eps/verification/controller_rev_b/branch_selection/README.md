# Independent CAN supply branch candidate — development review

2026-10-23. Written selection only: no branch symbol, footprint, or schematic has been authored. Exact proposed ordering is **TPS2553DBVR-1**, active-high, latch-off, six-lead DBV. Approval of custom construction and fault timing qualification remain open.

## Circuit and load budget

Use one independent switch for each TCAN3413DR. Feed its IN from permitted essential +3V3, bypass IN with at least 100 nF, default EN high through 10 kΩ, and set ILIM with TNPW0603210KBEEA (210 kΩ, 0.1%, 25 ppm/K, 0.11 W general P70). Feed OUT through CRCW12061R00FKEAHP (1 Ω, 1%, 0.75 W P70) to a distinct 3V3_CANA or 3V3_CANB supply. Both TCAN VCC and VIO, their existing 1.2 µF nominal bypass, and TXD/STB 10 kΩ pullups belong behind that channel's switch and resistor. Do not leave VIO or pullups on the shared rail. This is a proposed interface migration, not an existing connection.

The TCAN3413 guaranteed dominant VCC load is 60 mA with 50 Ω bus loading (55 mA at 60 Ω); published recessive maximum is 8.2 mA. Add up to 0.3 mA VIO with RXD unloaded and 0.665 mA for two asserted pullups: 60.965 mA steady allocation. RXD loading and bus capacitance add dynamic current, so 80 mA is a provisional working allocation with 90 mA sensitivity. These are not measured maximum traffic currents. Both bus pins forced to ±25 V allow a published 130 mA supply fault current; that abnormal condition may trip the branch. Standby maxima are 4 µA VCC plus 15 µA VIO. No accepted IHU/MCU total essential current budget exists yet. During one branch fault, the essential source must also support its full 151.2 mA bounded limit plus the healthy branch's valid traffic, MCU, oscillator, IHU and all other simultaneous loads. That combined fault-load reserve and the shared regulator response remain unallocated. [TCAN3413 Rev A](https://www.ti.com/lit/ds/symlink/tcan3413.pdf).

The TPS2553-1 supports 2.5–6.5 V and autonomous latch-off after a 5–10 ms overcurrent deglitch. The published 210 kΩ table is 110–150 mA; including resistor initial tolerance and ±65 K TCR in its bound equations gives 109.998–151.195 mA. Hot maximum DBV Ron is 135 mΩ. The minimum static buck estimate 3.232799 V yields 3.162598 V at the 60.965 mA allocation including resistor tolerance. Thus normal static headroom is plausible; it does not establish dynamic survival. Reset requires an EN cycle or supply cycle; independent reset and FAULT GPIO ownership are not allocated. [TPS2553-1 SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553-1.pdf), [exact ordering](https://www.ti.com/product/TPS2553-1/part-details/TPS2553DBVR-1).

## Guaranteed versus typical fault response

The short-response figure is **2 µs typical at 5 V**, with no guaranteed maximum at 3.3 V. The latch delay is guaranteed 5–10 ms, but that does not bound the initial current spike. Reverse comparator threshold is 95–190 mV with 3–7 ms turnoff; this is not an ideal-diode isolation guarantee. The listed 1 µA reverse leakage at IN=0/OUT=6.5 V is a 25°C condition, not a full-temperature backfeed guarantee.

[calculate.py](calculate.py) reproduces [calculations.json](calculations.json). For a deliberately conservative sensitivity, switch minimum Ron is unspecified, so only the 0.9835 Ω minimum series resistance bounds initial peak: 3.380 A. With 96 µF effective shared capacitance, assumed 10 mΩ ESR and no regulator help, an opposite branch initially carrying 60.965 mA remains about 3.060 V for a 2 µs response, 3.026 V at 3 µs, and falls below 3 V by 5 µs. At 90 mA valid traffic allocation it reaches 2.993 V at 3 µs. CRCW K-grade TCR is ±100 ppm/K, distinct from the 25 ppm/K ILIM resistor. Existing ripple, wiring, component uncertainty, input-source interaction and actual control response remain outside this charge-balance sensitivity. **A guaranteed surviving CAN-B rail during CAN-A short is therefore not established.** Do not freeze the 96 µF floor as sufficient.

The resistor's initial pulse can approach 11 W for microseconds; its HP pulse curve and repetitive/cold operation need qualification. Current-limit dissipation is small, and the bounded current-limited portion of the latch-window source energy is about 5.03 mJ, excluding the unbounded initial burst. Charging 1.2 µF with minimum limit minus the normal load takes about 81 µs by charge balance, below the minimum deglitch, but actual switch rise/inrush behavior still needs testing. Do not use this estimate to approve a shorted capacitor.

TPS22946 was considered but its startup/current-blanking behavior gives weaker initial fault isolation for this small load; TPS25221's higher minimum programmable current and continuous-limiting behavior do not implement the proposed low-current autonomous latch behavior. Neither is selected.

## Logic and power-off paths

Propose 1 kΩ series resistors on TXD, STB and RXD. A normal GPIO-to-ground branch fault is limited to approximately 3.32 mA per line; this does not isolate an arbitrary bus-to-logic breakdown. With an allocated MCU VOL of 0.4 V, 10 kΩ TXD pullup and the TCAN's 200 µA input-current bound, the TXD low estimate is 0.848 V versus 0.9 V VIL at a 3.0 V branch. RXD VOH is only 2.4 V at 3.0 V VIO, leaving about 73 mV over a 0.7×3.3244 V MCU threshold before leakage/tolerance. These small margins need final ST conditions and dynamic review. The 1 kΩ/50 pF sensitivity adds about 60 ns to a 70% edge, relative to 2 µs at 500 kbit/s; actual capacitance is unverified.

TCAN specifies ±1 µA logic-pin off leakage for VCC=VIO=0 and a 3.6 V pin. Both supplies must move together. These conditions do not prove arbitrary reverse-powered partial states or destructive bus faults safe. Essential supply loss also removes both channels and their common MCU; independent branch switches cannot remove that common-cause failure. Never claim whole-board galvanic isolation or comprehensive A/B redundancy from this proposal.

## Proposed construction rules — approval required

No matching TPS2553 symbol exists in the installed official libraries queried; no KiCadLib library is registered. Proposed exact identity: TPS2553DBVR-1, DBV0006A SOT-23-6, no exposed/mechanical pad. Use a functional rectangular single-unit symbol, visible numbered pins, left IN/EN, right OUT/active-low FAULT, downward GND, and a separately accessible ILIM analog resistor pin. Pin types: IN/GND power-in, EN input, FAULT open-collector, OUT power-out, ILIM passive (analog programming port; avoids inventing a digital drive contract). No hidden pins, swapped units, stacked pads or inferred pad numbers.

| Datasheet lead, top view | Symbol function | Manufacturer land (mm, x/y-down) |
|---|---|---|
| 1, upper left | IN | −1.30, −0.95 |
| 2, middle left | GND | −1.30, 0 |
| 3, lower left | EN | −1.30, +0.95 |
| 4, lower right | active-low FAULT | +1.30, +0.95 |
| 5, middle right | ILIM | +1.30, 0 |
| 6, upper right | OUT | +1.30, −0.95 |

The TI DBV0006A example land drawing (4214840/G, August 2024, PDF page 35) gives six 1.1×0.6 mm lands, 2.6 mm opposing center distance, 0.95 mm vertical pitch and R0.05 typical corner. Actual primary pin figure and land page were rendered and inspected. The stock Package_TO_SOT_SMD:SOT-23-6 query instead returns 1.325×0.6 mm pads at x=±1.1375, y=−0.95/0/+0.95, roundrect ratio 0.25. Numbering agrees, geometry differs: it must not be described as the exact manufacturer pattern. Approve either that stock footprint after an explicit land comparison, or new manufacturer-pattern construction; neither is silently accepted here.

For any approved new symbol/footprint: use project-local portable libraries; read back all six names/numbers/types and pad coordinates, inspect disposable top-view symbol/footprint renders, then connect a disposable circuit and compare exported endpoints before real placement. Record source URL/revision/order suffix, metadata, courtyard/assembly details and pending review. S08 requires bright-green review marking; exposed symbol APIs have not demonstrated persistent body-color support, so an explicit approved alternative is required. S11 field presentation and S03 native ERC severity remain separate known API limitations. No placeholder custom MPN satisfies acceptance.
