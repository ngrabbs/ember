# EPS Rev B source voltage and fault budget

Study dated 2026-10-04. **Recommend retaining 4S solar strings, replacing the 30 V buck stages with higher-voltage stages, and adding autonomous solar overvoltage isolation inside the hardware interlock boundary.** This is an architecture recommendation, not a selected protection circuit or accepted flight envelope. No KiCad source was changed. The current controller draft still has no regulator implementation.

[Source isolation](rev_b_source_isolation_study.md) · [Implementation checklist](rev_b_bom_and_schematic_checklist.md) · [Calculation and capacitor membership evidence](../verification/evidence/2026-10-04_source_envelope.json) · [CAN TVS study](../verification/can_tvs_candidate_verification.md)

## Source evidence and temperature calculation

The repository's [SM141K10TF datasheet](../components/SM141K10TF/SM141K10TF%20DATA%20SHEET%20202105.pdf), printed page 1, states typical module Voc = 6.91 V and dVoc/dT = −17.4 mV/K, referenced to 25°C, AM1.5, 1000 W/m². Its operating-temperature range is −40°C to +90°C. Although the filename says 202105, the inspected document is marked **Preliminary, Rev. Dec. 2024**. The evidence records its hash. It gives typical values, not guaranteed worst-case limits.

Use the module coefficient directly; do not multiply it by the module's internal cell count again:

`Voc_4S_typ(T) = 4 × [6.91 − 0.0174 × (T − 25)] V`

| Module temperature | Typical 4S open-circuit voltage |
|---|---:|
| +90°C | 23.116 V |
| +25°C | 27.640 V |
| 0°C | 29.380 V |
| −20°C | 30.772 V |
| −40°C | 32.164 V |

These are linear estimates using published typical parameters. They exclude manufacturing spread, orbital spectrum/irradiance changes, wiring transients and temperature-coefficient uncertainty. Do not extrapolate below −40°C as an accepted source specification. No guaranteed blocking-diode drop is subtracted: at light load/open circuit, its voltage drop cannot provide a fixed protective margin.

[TI TPS6293x Rev D](https://www.ti.com/lit/ds/symlink/tps62933f.pdf), printed page 5, specifies 30 V recommended maximum VIN and 32 V absolute maximum. The typical calculation crosses those levels at approximately −8.91°C and −37.64°C respectively. The latter is a source estimate, not proof of the voltage on a measured Rev A VIN pin. It is sufficient to reject unconditional reuse of the 30 V stages with 4S strings. Buck EN removes switching permission, not voltage at VIN.

[ADI LTC4162-L Rev A](https://www.analog.com/media/en/technical-documentation/data-sheets/LTC4162-L.pdf), printed pages 1 and 3, specifies charging input through 35 V and 36 V absolute maximum on VIN and related power/sense nodes. At the typical −40°C estimate, only 2.836 V remains below the charging-input ceiling; this is not a validated allowance for tolerance and overshoot. Its low-loss input PowerPath feeds system loads; it does not produce an 8.4 V regulated system rail. Its input-current loop can reduce charging to zero but cannot limit system load current (page 17). The internal vin_ovlo indication is approximately 38.6 V (page 45), above the published absolute rating, and cannot substitute for external protection.

## Proposed source conditioning

Functional order:

`solar faces → blocking network → hardware RBF/deployment isolation → SOLAR_PERMITTED → autonomous OV isolation → VIN_CHG / input PowerPath → VOUT_PP → regulators`

The OV controller and any necessary bias are supplied within the interlocked domain. RBF insertion must remove their source power as well as MCU, charger and load power. The independent pack BMS remains the only proposed retained active circuit. Monitoring SOLAR_PERMITTED upstream of the added OV switch permits fault detection while the protected output is disconnected; downstream-only monitoring can lose its bias and repeatedly reconnect into the fault. Verify actual power-off leakage, stored energy and any battery-fed bias path. This drawing does not select the MOSFET orientation or prove bidirectional isolation.

Keep RBF permission and OV fault isolation separate in the requirements: an MCU cannot override either. Solar OV should remove solar input while permitting the protected battery path to support essential EPS/IHU/recovery COMMS. Demonstrate PowerPath handover under maximum load. When the battery is absent, depleted or its BMS is open, an OV event may remove all power; safety still takes priority, and autonomous restart behavior must be specified.

Evaluate buck parts with **at least 42 V recommended operating capability**, with 60 V alternatives where they improve coordinated margin. This is a search requirement, not acceptance of every 42 V part. Compare quiescent/light-load loss, 3.3 V and 5 V current, minimum battery-input dropout, startup, thermal dissipation, EMI and footprint. Higher buck ratings do not raise the LTC4162 limit. Requalify all capacitors, FETs, blocking diodes and sensing networks in each voltage domain; upstream devices see the unconditioned solar envelope.

For a selected design, require a feasible interval between maximum normal voltage and the protected limit:

- Minimum actual OV trip must exceed accepted normal Voc, including tolerance and the selected operational allowance.
- Maximum actual trip plus voltage accumulated during detection/turn-off and switching overshoot must remain below the lowest protected operating limit, with explicit design margin.
- Independently demonstrate transient peaks below every applicable absolute rating. Never use absolute ratings as normal setpoints.
- Coordinate clamp voltage, current, energy and repetition with isolation delay and MOSFET safe operating area. A nominal TVS voltage is insufficient.

If these inequalities have no feasible interval, revise array wiring, source conditioning or charger selection. No threshold is frozen here. A cutoff below 30 V would discard cold-array availability and could prevent startup when unloaded Voc remains high; retaining the existing bucks requires proving that behavior is acceptable. A 3S string is another option (24.123 V typical at −40°C), but changing four-module face wiring requires a new array/MPPT/power budget. A 2S2P face changes input current and hot-temperature charging headroom. Neither is an automatic substitution.

## Rev A capacitor reconciliation

The released BOM groups C3/C9/C10/C18/C19 as 22 µF, 25 V parts. The saved XML export places C3 on VIN_CHG with a different value; C10/C18/C19 are on regulated rails with different values, and C9 has only GND exported. C12/C13/C21/C22 occur on VOUT_PP but also differ from released BOM values. C29/C30 and C31/C32 are on 3.3 V and 5 V respectively in the saved export. The JSON preserves exact values and connected endpoints.

Therefore **do not assert that all five released 25 V capacitors sit on solar, or that none does**. The saved export has known missing connections and does not establish the fabricated/reworked assembly. Inspect physical markings/assembly records and trace the actual input and PowerPath capacitors. Any actual 25 V capacitor on a node reaching 27.64 V at the reference condition is unacceptable even before cold analysis. Final voltage-rating and effective-capacitance acceptance must include DC bias, temperature and transients.

The existing Markdown datasheets have been corrected to remove the unsupported “28 V (4S cold)” claim and to distinguish 35 V charging range from 36 V absolute maximum. Their pre-existing PDF exports are historical and have not been regenerated; do not use them as Rev B electrical authority.

## Continuous faults and CAN coordination

| Source / path | Known starting point | Acceptance still needed |
|---|---|---|
| Battery → source switch / load short | 2S pack, 8.4 V normal charge ceiling; user expects upward of 2 A load | Peak/inrush measurement, prospective short current, BMS/fuse delay, harness and FET energy. The load estimate is not a short-current ceiling. |
| Solar → input short | Module Isc typical 58.6 mA at reference conditions; series wiring does not add current | Illuminated parallel-string count, hot/AM0 current envelope, backfeed from batteries or bench supplies, cable/capacitor energy and protection behavior. |
| Solar or battery → CAN line | Sustained rail injection can reach bus TVS and termination | Fault impedance, duration, both bus polarities, opposite-line/return state and local ground shift; interruption or sustained-safe behavior. |
| PowerPath / regulator failure → essential 3.3 V | Shared MCU/clock and transceiver supply | Independent supply protection/containment and resulting recovery coverage; CAN A/B alone does not remove this common cause. |

For an ideal stiff differential voltage across one 120 Ω termination, `P = V²/120`: 8.4 V produces 0.588 W and 32.164 V produces 8.621 W. These are topology-dependent fault scenarios, not predicted solar operating currents. The solar source may collapse/current-limit; a battery or bench source may not. When both bus ends are terminated, calculate the complete parallel network and dissipation at each end. Small termination resistors cannot be accepted from nominal CAN power alone.

The PESD2CANFD24V-T candidate has 24 V stand-off. A solar fault can exceed it continuously; the pulse rating does not establish sustained survival, fault removal or safe ground current. Select the bus protection only after specifying source impedance/energy and the continuous-fault response. Include connector-adjacent return inductance and both powered/unpowered transceiver states. Consider a suitable higher stand-off CAN protection device or fault isolation as alternatives; prove transient protection with the chosen transceiver and layout before selecting either. The candidate remains outside the controller circuit.

The battery source-switch reference also needs a terminal-by-terminal voltage matrix: its 30 V rating follows the normal battery domain only. A fault applying solar to its downstream terminal could exceed that class. Do not claim that its off-state or reverse-current behavior protects against every cross-domain fault.

## Next implementation gates

1. Obtain accepted cold/hot array limits (thermal range, AM0/irradiance and supplier tolerance or characterization), and reconcile physical Rev A power-stage passives. This work does not diagnose the damaged thermistor circuit.
2. Compare higher-voltage buck candidates against both rails and battery dropout; select complete conversion stages, including capacitors/inductors.
3. Choose an autonomous OV circuit and prove its tolerance/delay window, bias location, turn-off SOA and restart policy inside the RBF boundary.
4. Establish fault-current/energy limits and coordinate BMS, fuse, source/load switches, CAN TVS and termination. Resolve transceiver-supply containment before claiming B-bus recovery after an A-side hardware failure.
5. Test with limited-energy supplies/cell simulators: unloaded cold-Voc startup, hot plug, load release, solar OV, source handover, contact bounce, absent/depleted battery and sustained bus shorts. Capture voltage directly at vulnerable pins, current and temperatures. No bench acceptance has run.
