# EPS Rev B physical SWD development integration

2026-10-24. Authorizes one coherent development schematic block **after the disposable Tag-Connect/TMUX1511/TPS3839 package maps are accepted and root hands integration back to the sole design owner**. The operator approved TMUX1511 construction under the [exact rules](rev_b_swd_tmux1511_library_rules.md). This contract does not waive electrical, layout or qualification gates.

## Purpose and boundary

Replace five-pin logical J100 with the standard six-contact Tag-Connect no-leg SWD service footprint. Use one independently supply-qualified, bidirectional TMUX1511PWR path for each of SWDIO, SWCLK, NRST and VTref. A TPS3839K33DBZR supervisor controls all switch selects from permitted essential+3V3. No firmware command, MCU reset state or bootable image is required to connect the debugger when supply is valid. Do not tie switch enables to MCU_NRST or directly to a ramping supply. Initial debug clock is100 kHz; higher rates require waveform/turnaround verification.

Main scope is controller sheet, root hierarchy/project classes and a new unique ANSI B SWD Service sheet. All other existing parts/metadata/UUIDs and native boards remain unchanged. J100 is an explicitly retired **logical** five-pin instance; replacing its symbol may require a new UUID under the same reference, recorded in a crosswalk. It is not an accepted physical connector whose map may silently change. Preserve every other existing physical UUID, field and unrelated object. No real PCB synchronization or custom footprint authoring is authorized by this handoff.

Existing controller-local `/Controller/EPS_SWDIO`, `/Controller/EPS_SWCLK`, `/Controller/EPS_NRST` intentionally migrate to global `EPS_SWDIO`, `EPS_SWCLK`, `EPS_NRST` for actual page crossings. Controller endpoints remain U100.24/25/6 and C112.1 on NRST; their functions are unchanged. Keep C112 and its100 nF reset bypass. There is **no existing external NRST10 kΩ pullup** in the305-part graph; add one here. R105 is the oscillator-enable pullup and must remain unchanged. No stack pin or signal is allocated or renamed.

## Exact development circuit

Reserved additions are U1200,U1201,R1200–R1208,C1200,C1201; first verify they are unused. J100 retains its reference but receives the physical six-contact map. All local topology uses actual wires with visible stubs and separated T-junctions. Supplies are upward+3V3 power symbols (existing interface name); GND symbols downward. Preserve actual net-class assignments for unchanged nets and explicitly classify every new resolved segment.

| Reference | Exact candidate | Connection/role |
| --- | --- | --- |
| U1200 | TMUX1511PWR, approved review symbol and unchanged stock TSSOP-14 | Four active-high bidirectional switches;VDD14=+3V3,GND7=GND;SEL1/2/3/4 pins1/4/10/13=local SWD_SUPPLY_OK |
| U1201 | TPS3839K33DBZR, verified stock TPS3839DBZ symbol/stock SOT-23 | GND1=GND;RESET2=SWD_SUPPLY_OK;VDD3=+3V3. Qualifies supply, not MCU reset |
| R1200 | TNPW0603330RBEEA,330 Ω | EPS_SWDIO→S1(pin2);D1(pin3)→J100.2 |
| R1201 | Same330 Ω | EPS_SWCLK→S2(pin5);D2(pin6)→J100.4 |
| R1202 | Same330 Ω | EPS_NRST→S3(pin9);D3(pin8)→J100.3 |
| R1203 | TNPW060310K0BEEA,10 kΩ | +3V3→EPS_SWDIO target-side pullup |
| R1204 | Same10 kΩ | +3V3→EPS_NRST target-side pullup |
| R1205 | TNPW060347K0BEEA,47 kΩ | EPS_SWCLK→GND target-side pulldown |
| R1206 | Same10 kΩ | SWD_SUPPLY_OK→GND, defined select pulldown |
| R1207 | Same10 kΩ | +3V3→GND, explicit service-interface rail bleed |
| R1208 | Same10 kΩ | 3V3_SWD_VTREF→GND on the probe side |
| C1200,C1201 | GRM188R72A104KA35D,100 nF | Local+3V3/GND bypass at switch and supervisor respectively |

U1200 S4(pin12) connects directly to permitted+3V3;D4(pin11) connects to 3V3_SWD_VTREF and J100.1. Represent this distinct switched reference with an upward power symbol whose Value is3V3_SWD_VTREF and assign POWER class. VTref is target-voltage sense, **not an external target power input**. Do not insert an unreviewed high-value series resistor that prevents the specified probe load from receiving a valid reference. J100.5=GND. J100.6=SWO is genuinely unused and receives a truthful NC; do not allocate a spare GPIO or connect it to supply.

The six PCB contacts are1VTref,2SWDIO,3NRST,4SWCLK,5GND,6unusedSWO. This swaps physical3/4 relative to the logical placeholder's old SWCLK3/NRST4. Stock `Connector:Conn_ARM_SWD_TagConnect_TC2030-NL` and `Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical` may be used only with the accepted exact map. Record external cable identity `TC2030-CTX-NL` clearly; the target has contacts/holes, no soldered connector. Use native in-BOM exclusion if supported, retaining on-board inclusion and required pads; otherwise document the assembly/BOM limitation. A generic Population field is not native exclusion.

Resistors use accepted0603 stock lands,0.1%,25 ppm/°C,0.110 W at70 °C with manufacturer derating above70 °C. Capacitor metadata must preserve exact tolerance/voltage/package/dielectric. Query these fields and real library sources before placement; existing accepted values/metadata are not a license to fabricate an MPN or rating. All five custom switch units retain the approved bright-green review enclosure/callout. No authoring or electrical-type change to standard supervisor/connector symbols.

## Development operating conditions and open gates

Use a3.3 V debugger that supplies **no target power**, probe signal maximum3.6 V, loaded VOH≥2.4 V/VOL≤0.4 V, VTref load≤1 mA and stated digital input leakage≤10 µA. Treat these as a service-interface requirement until the actual probe/adapter is verified. Ground is common. Limit total assumed cable/pad load to50 pF plus the switch's6 pF maximum on-capacitance for the initial timing screen. Initial100 kHz does not prove arbitrary cable or higher-speed operation. Use at least10 ms NRST assertion after the switch supply has qualified, pending actual STM32/probe verification. Verify SWDIO bidirectional turnaround and NRST connect-under-reset; retain MCU boot/option-byte recovery access.

The chosen supply qualifier is a development component. TI gives K33 falling threshold2.857–2.974 V over−40..85 °C, hysteresis29 mV **typical**, release120–350 ms and assertion20 µs **typical only**. Its high/low drive checks must include all four SEL inputs, internal pulls and external10 kΩ. Do not equate its nominal assertion time with a guaranteed rapid-collapse bound or use typical hysteresis as a guaranteed rising threshold. The proposed Microchip alternative did not improve the missing maximum-delay guarantee.

TMUX1511 powered-off±2 µA is specified atVDD=0; it does not guarantee the same leakage throughout a nonzero/brownout rail. At valid supply the switch is bidirectional and can pass above-rail signals within its published limits, so supply qualification matters. The330 Ω resistors limit service-path current and affect timing; they are not galvanic isolation or an accepted full-EPS inhibit. Static pull/load checks must include actual STM32/probe bounds. No bleed arithmetic alone proves all-path zero-power isolation.

Remaining electrical acceptance: full all-path leakage and bias equilibria, slow/fast supply collapse and recovery with both driven/off probe, threshold/hysteresis timing, input injection/pin stress, ESD/overvoltage/ground offsets, cable edges/turnaround and reset sequencing. Physical acceptance: exact stock-land deviations, TMUX7.70×5.90 mm and TPS3.86×4.04 mm reservations, Tag-Connect alignment-hole/contact/central keepout, no contact paste,0.508 mm other-signal clearance, service-cable insertion and underside clip clearance. The16 mm clear stack gap does not prove a plugged-in debug cable fits. Unplug service cables for flight; this does not replace the electrical back-power audit.

## Verification and handoff

Before main integration, accept all exact package maps through raw queries, disposable saved footprint counts and actually inspected schematic and layer details. Then export the full updated root with KiCad CLI, assert every intended terminal/net set, old-object preservation except the explicit J100 replacement and signal migrations, truthful NC and metadata. Confirm all new functional nets match exactly one intended persisted class. Keep the seven genuinely unfinished MCU pins and three prior intentional ERC joins explicit. The faithful bidirectional fourth switch channel also produces two specific supply-path type joins: S4 pin12 to the existing+3V3 source flag and D4 pin11 to a legitimate switched-VTref source flag. Add that downstream flag only to describe the actual enabled+3V3→TMUX path that ERC cannot infer. Expected development ERC is10 errors/2 warnings: seven unfinished MCU pins and three prior intentional joins remain errors; the two specific switch supply joins are warnings under unchanged native settings. Do not weaken the approved S/D types or add new exclusions to force a lower count.

Render/inspect every full-root sheet and circuit details separately from electrical verification. Record S03/S11/field/pagination limitations truthfully. Verify the actual root PDF and new hierarchy child, not disconnected standalone pages alone. Update the current area/BOM inventory only from the new exported graph; preserve historical checkpoint sources/manifests at their recorded basis. Return a saved verified development checkpoint and root-readable visual/electrical evidence before real PCB work.
