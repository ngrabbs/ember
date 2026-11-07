# Isolated BMS supply selection screen

2026-10-24. Development analysis only; **no native design change and no circuit integration acceptance**. Run `python3 calculate.py` to reproduce [calculated.json](calculated.json). The current authoritative root remains the 243-part / 137-net UART checkpoint. Scope is electronics component screening over −40 to +85°C; battery/environmental qualification remains open.

## Why construction is held

The ADuM5028-3BRIZ construction approval is recorded and remains valid under its agreed rules. Its conditional electrical gate has not passed. The [ADI Rev E datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/adum5020-5028.pdf) Table 6 guarantees 30 mA capability in the tighter 3.135–3.465 V window; it has adequate DC capacity. However, ripple/noise and 190 mA full-load primary current are typical values, not guaranteed maxima. The new startup guidance requires a monotonic input starting near zero and a discharged output; repeated UVLO/PDIS restarts with output charge can overshoot. Its suggested 6.2 V clamp protects a different limit than ISO1540's 5.5 V operating maximum. A direct 3.3 V secondary implementation therefore lacks a closed startup/dynamic margin. This is a circuit gate, not withdrawal of the user's library approval.

Actual ADI pages 6 and 17 were inspected by the root reviewer; the design owner also inspected startup pp18–19. Download SHA-256: ca6f1be8b4051f0434793cdd0b198b8695b8af7eabc4a14798d0f3ccc4e4c7b3. The PDF is Rev E, August 2026.

## Historical candidate topology — superseded for preferred selection

Permitted essential +3V3 → UCC33020RAQR → **5.5 V isolated intermediate** → TLV76733DRVR → `3V3_BMS_ISO`. Use UCC SEL tied to secondary GNDS for 5.5 V. Only ISO1540 side 2 and its two existing pullups move to the isolated supply; raw return remains GND_BMS_RAW. Side 1 remains on permitted +3V3. No ground-domain bypass, new raw-cell always-on regulator, or signal-interface rename is proposed.

The [TI UCC33020 SLUSFK4A](https://www.ti.com/lit/ds/symlink/ucc33020.pdf) full-input-range ±4% DC screen gives 5.28–5.72 V for the 5.5 V setting. The 5.0 V setting's corresponding 4.8 V lower bound sits at the TLV767's nominal-output-plus-1.5 V electrical-table test condition; ripple would remove that headroom. The 5.5 V choice adds 480 mV of static headroom to that condition. It is an engineering choice pending the remaining gates, not a guarantee of the full transient envelope. In particular, the UCC 75 mVpp ripple row is for 5.0 V at 25°C and cannot be transferred as a guaranteed 5.5 V all-temperature bound.

[TLV767 SLVSE84D](https://www.ti.com/lit/ds/symlink/tlv767.pdf) specifies ±1% over temperature at 1 mA–1 A under its stated conditions. A provisional 3.0 kΩ, 0.1%, 25 ppm/K bleeder supplies at least 1.086 mA over the 65 K component-screening excursion used by the existing bus study. Its maximum dissipation is about 3.71 mW. The conditional 3.267–3.333 V range gives 267 mV above ISO1540's 3.0 V operating minimum. This calculation does not claim a dynamic or fault maximum.

The all-low ISO1540 side-2 IC maximum (6.7 mA), two pullups pessimistically pulled to zero (1.714 mA), and bleeder (1.114 mA) total 9.528 mA. Reserve 12 mA as a provisional planning allocation, leaving about 2.47 mA for switching/other overhead. Loaded LDO ground current and the final transient budget still need bounds; 95 µA is a **no-load** maximum only. At 12 mA the intermediate supplies about 68.6 mW and the LDO pass element dissipates at most about 29.4 mW under the screened static corners. These are conditional planning values, not qualified power maxima.

## Release gates

- Confirm UCC 5.5 V load/temperature coverage. The 0.5 W table entry at 3.3 V input explicitly specifies a 5.0 V output and 25–85°C; do not call it a guaranteed 5.5 V or cold rating.
- Select exact capacitors and establish effective capacitance/ESR across voltage, tolerance and temperature. TLV recommended nominal COUT starts at 1 µF; its footnote requires at least 0.5 µF effective for stability. Use a more conservative ≥1 µF effective design target.
- Bound primary current/inrush against the essential rail and qualify its transient behavior. Neither no-load current nor a typical efficiency gives a loaded maximum at this application point.
- Complete reverse-current protection. TLV767 §9.1.4 explicitly warns of unlimited reverse current and recommends external protection (Figure 9-1); its output pulldown is not an accepted substitute for input-short/capacitor-discharge analysis.
- Establish startup with both initially discharged and prebiased outputs, input collapse, short, repeated UVLO and hiccup recovery. UCC SEL is sampled while output is below 2.7 V; no explicit arbitrary prebias guarantee was found. Internal OVP threshold and shutdown are not an instantaneous voltage-peak bound.
- Set EN/FLT control/fault reporting using the published ≥18 kΩ pullup condition, with exact MCU allocation and default state recorded before integration. Do not silently consume reserved PD3.
- Complete stock LDO pin/pad acceptance and approved UCC custom construction/queryback/render gates. UCC rules approval is pending; ADuM approval does not cover another part. Electrical verification and actual rendered inspection remain separate.
- Verify no alternate feed or ground return bypasses the shunt/RBF boundary; close powered/unpowered logic, EMC and thermal/layout acceptance.

Manufacturer source images and library readbacks are in [candidate evidence](../ucc33020_candidate/README.md). Root independently inspected UCC pp6–7 and TLV p6; these confirm table-column interpretation. Neither this static script nor a source-image review is a circuit simulation or bench result.

A possible autonomous default-on EN/FLT pullup is 20 kΩ, 0.1%, 25 ppm/K: at the existing static primary minimum 3.2328 V and 10 µA maximum EN current, the screened high is 3.0323 V, above the 2.1 V rising-threshold maximum. This satisfies the datasheet fault-reporting resistor condition without consuming a reserved MCU pin. It remains a topology candidate; fault observability/testpoint and exact selected part must be recorded with the circuit. The 5.5 V-output no-load primary maximum is **18 mA**, rather than the 15 mA limit for 5 V mode.

## Selection follow-up

The [LT3014 review](../lt3014_screen/README.md) is now the preferred post-regulator candidate because its documented reverse-output protection addresses the TLV-specific discharge concern. It allows returning UCC to 5.0 V mode with more dropout headroom. Retain this earlier calculation as a comparison; do not use its 5.5 V strap, TLV part or bleeder as the current proposed implementation. Neither candidate is integrated yet.
