# USB main-path admission clamp prototype

> Historical experiment. [The integration baseline](source_hardware.md) uses
> a direct qualified logic EN interface with separate raw-window detectors.
> Do not copy this clamp into the next carrier as its accepted admission gate.

2026-10-04. A standalone TPS259470LRPWR input circuit and raw-powered enable
clamp are implemented. Exported topology passes its checks; **default-off
operation across temperature and power transitions remains unqualified**.
Do not integrate this as a proven safety gate or release it for fabrication.

The [fixture](validation/payload_admission_acceptance/README.md) implements
the USB 15 V main path. Q1 and Q2 are PMV16XNR; their exact physical assignments
are accepted in [the MOSFET map](admission_library_acceptance.md). U1 uses the
previously accepted [eFuse map](efuse_library_acceptance.md). Battery/stack
branches, source locks and status translation are external work.

## Circuit behavior to qualify

Q1 drains EN/UVLO to ground. A 20 kΩ / 10 kΩ raw-input divider biases its gate
on even when AON is absent. Q2 pulls that gate down when ADMISSION_GRANT is
high, releasing EN to the raw-input UV divider. Q2 has a 100 Ω gate series
resistor and 1 kΩ pulldown. The grant must come from qualified hardware source
admission, default low, rather than an unqualified MCU command. It must clear
during AON reset and MCU-alive failure. That driver is not implemented here.

At 6–23 V raw input, with 1% bias resistors and an assumed ±1.1 µA gate-node
leakage, Q1's gate is 1.966–7.777 V. Conditional on the published 25°C
RDS(on) maximum at VGS=1.8 V, the 23 V divider current produces about 2.03 µV
at EN: below the eFuse's 0.45 V minimum shutdown threshold. With a valid high
grant, the same conditional resistance gives about 38.3 µV on Q1's gate.
These DC numbers exclude injection, ground offsets and dynamic discharge.

A driver with VOH ≥2.4 V at the approximately 2.2 mA gate-pulldown load gives
Q2 VGS ≥2.178 V. A VOL allowance of 0.4 V gives about 0.364 V at Q2's gate;
the MOSFET threshold is not a guaranteed off/leakage limit. A hypothetical
10 µA power-off driver leakage gives about 10.2 mV, also not covered by the
device's zero-VGS drain-leakage specification. Select a stronger low-voltage
driver contract and qualify Q2 leakage at the resulting nonzero gate voltage.

Nexperia specifies the 1 µA maximum IDSS, 100 nA maximum IGSS and 1.8 V
RDS(on) limit used here at 25°C. The threshold minimum is measured at
250 µA, not at zero current. These data cannot prove the clamp across flight
temperatures. Slow/fast raw and AON ramps, gate-drain coupling, partial power,
detach, reset and negative input still require analysis and measurements.
Positive DC gate voltages fit the ±12 V gate rating; this does not establish
transient or reverse-input survival.

## USB thresholds and load allocation

Use 374 kΩ / 37.4 kΩ, both 0.1%, for USB EN/UVLO in this fixture. This
replaces the 1 MΩ / 100 kΩ eFuse-only screen: the same nominal ratio with
lower impedance reduces added clamp leakage error while retaining TI's
≥350 kΩ input pull-up recommendation. The provisional combined ±1.1 µA
allocation is ±0.1 µA eFuse leakage plus ±1.0 µA Q1 leakage. Q1 leakage at
the actual gate voltage and temperature is not yet proven to fit it.

| Threshold | Rising range | Falling range |
|---|---|---|
| USB UV, conditional leakage allocation | 12.578–13.889 V | 11.404–12.710 V |
| USB OV, 365 kΩ / 29.4 kΩ, ±0.1 µA | 15.804–16.473 V | 14.371–15.035 V |

The UV rising ceiling fits the assumed 14.25 V minimum full-profile input;
the OV rising floor exceeds the assumed 15.75 V maximum. Actual source,
cable and contract qualification remain required. Neither threshold proves
available current, nor does AUXOFF or FLT alone prove selected-source health.
Those outputs are intentionally unused in this bounded fixture.

RILM is 1.65 kΩ / 0.1%, giving a tabulated/scaled 1.798–2.202 A screen.
This supersedes the 1.30 kΩ estimate for this USB prototype. Check full-payload
boot/load peaks and total USB draw including bootstrap and PD-controller
loads against the actual 3 A contract. This setting does not prove that the
full Jetson lab profile will start successfully.

dVdt is 10 nF / 50 V and the study output capacitor is 100 µF / 35 V.
TI equation 4 gives a **nominal** 0.2 V/ms slew, 75 ms to 15 V and 20 mA
charging current for that capacitor alone. This is not a worst-case timing
bound and excludes downstream capacitance/load. ITIMER is open, without an
added blanking capacitor. EN has 4.7 nF; qualify its delay and fault-reset
discharge. This admission circuit does not replace the accepted direct IHU
PAYLOAD_EN hard-kill path to module power permission.

Input VDC means already protected raw USB. Coordinated entry fuse/TVS and
negative-input behavior of the external clamp are not implemented. The
reverse-blocking eFuse belongs upstream of the converter, not between the
5 V buck and Jetson's VDD_IN, where NVIDIA's reverse-current requirement applies.

Verification: 13 exported nets, zero ERC errors, one expected external-input
warning on ADMISSION_GRANT, and zero disconnected pins/wires, shorts,
orphans or symbol overlaps. The saved schematic and SVG were inspected.
The disposable PCB has only an unconnected MOSFET package placement.
Reproduce with `python3 design/admission_control_study.py` and
`python3 design/validation/check_admission_study.py`.

Next qualification: resolve the low-state/leakage contract; compare a more
fully specified clamp alternative if necessary; then characterize ramps,
temperature, input reversal, inrush and reset. Implement source-lock decoding,
bootstrap/entry protection and independent raw/bus/contract/fault feedback
before connecting this block to the carrier.

Sources: [TI TPS25947](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
SLVSFC9C May 2026, electrical characteristics and equations 3–4;
[Nexperia PMV16XN](https://assets.nexperia.com/documents/data-sheet/PMV16XN.pdf),
v.1 November 2014, characteristics and package tables.
