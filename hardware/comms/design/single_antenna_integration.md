# Single-antenna RF integration

## Implemented schematic

One shared UHF antenna, 437 MHz TX / 435 MHz RX, half duplex. J9 is the only antenna connector. The new `RF_Switch.kicad_sch` sheet is linked from the overview. Old PCB J5 remains to be removed with its obsolete feed routing during PCB work; do not restore a separate RX antenna port.

Signal flow: J9 / ANT → C102 DC block → U11 common port; U11 RF1 → TX_OUT; U11 RF2 → RX_IN. TX_OUT and RX_IN are internal circuit nets. Existing C94 and C55 isolate DC on the TX and RX branches.

| Part | Selected implementation |
|---|---|
| U11 | pSemi PE4259, order 4259-63, SC-70-6 |
| U12 | TLV75530PDBVR, 3.0 V LDO from +5V, EN tied to input |
| U13 | SN74LVC1G17DBVR, noninverting buffer powered by +3V0 |
| C102 | 100 pF C0G/NP0, 50 V, 0402 antenna DC block; initial RF value |
| C103 / C104 | 1 µF, 16 V X7R, 0603 LDO input/output; purchasing selection must retain >0.47 µF effective capacitance |
| C105 / C106 | 100 nF local bypass for buffer / RF switch |
| R35 / R36 | 10 kΩ input and switch-control pull-downs |
| R37 | 10 kΩ rail bleed/minimum load |

Pin map acceptance is recorded in `rf_switch_pinmap.md`. Library and disposable schematic/PCB instances were queried and rendered. The custom switch symbol was enlarged after a visual check, then checked again. The real schematic has explicit package assignments and exact IC MPN fields.

## Control and power

Use the existing TX_ACTIVE signal on **J6 pin 14 / Pico GP10**, which already drives D10. Its two local labels were converted to global labels so the RF sheet connects to the same GPIO. GP22 remains spare. J6/J7/J8 remain identical DNP headers as requested.

At valid supply voltage, low selects RX (RF2), high selects TX (RF1). Default pull-downs select RX once the supplies settle. No receive state is guaranteed when unpowered or during rail ramps: firmware must keep the transmitter inactive then.

A nominal 3.3 V rail sits at the PE4259 operating maximum. The 3.0 V regulator provides margin (nominal ±1% through 85°C, ±1.5% over the regulator's wider range; verify actual rail at the switch). The buffer accepts the Pico's 3.3 V input while producing switch-rail logic levels, and supports partial power-down. This avoids relying on a divider to protect a switch whose supply is off. Buffer maximum specified power-off leakage of 10 µA produces 0.1 V across R36=10 kΩ at VDD=0; powered behavior and rail transients still require bench verification. R37 also provides a 0.3 mA load and discharge path.

Firmware sequence: stop TX drive; select the new path; allow settling; then enable TX only if supply and operating mode permit it. Start with a conservative 10 µs switching guard interval for bench bring-up, then validate across power and temperature. The PE4259's 1.5 µs switching figure is typical, not a guaranteed worst-case limit; do not present 10 µs as a proven timing bound. The part is limited to 25 kHz control switching.

## Verification

- Full native KiCad netlist: **124 components, 181 nets, 433 pin nodes**.
- All 401 previous pin nodes are preserved. Only the intended two node-name changes occur: D10.2 and J6.14 move from local `/Digital Control/TX_ACTIVE` to global `TX_ACTIVE`.
- Confirmed ANT = J9.1 + C102.1; RFC = C102.2 + U11.5; TX_OUT = C94.2 + U11.1; RX_IN = C55.1 + U11.3.
- Confirmed TX_ACTIVE = J6.14 + D10.2 + R35.1 + U13.2; buffered control = U13.4 + R36.1 + U11.4.
- New sheet: zero floating wire endpoints, unconnected required pins, shorts, or orphan items in Konnect checks.
- Native ERC: **zero active errors and zero active warnings**, with the same two excluded transistor/power-flag warnings and four ignored checks. Two colliding auto-generated power references were corrected to #PWR0501/#PWR0502.
- The existing CLI/native export discrepancy persists. The project explicitly declares top-level instance UUID `c034ea61-6551-4f92-af2a-65337e5cc22a`, distinct from root document UUID `34355200-1bb0-4506-ab43-0e1897ffed50`. Native saves use the project instance UUID. This is evidence of a KiCad 10 top-level-sheet context mismatch in tooling; do not blindly rewrite the UUIDs or delete alleged dangling wires. Native connectivity remains authoritative for PCB updates.

## PCB integration and placement — 2026-09-09

Native synchronization added exactly 11 footprints with zero reported errors. The six warnings concern legacy unknown-net vias and Y1 pad 4. All 124 schematic references are now present on the board; 20 legacy footprints remain. No existing footprint moved during synchronization.

Removed legacy J5 and the four explicitly traced /RX_IN and /TX_OUT antenna-feed segments. J9 remains in its original position and is the sole antenna connector. Placed the switch, regulator, buffer and eight passives below J9; moved C55/C94 from the unplaced group to the switch branches. No RF routes were added in this step. Protection and tuning remain open.

Initial placement touched two existing ground vias and KiCad assigned them to signal nets. Moved the parts clear, restored both vias to GND, and verified those assignments after refill/save. Also preserved nine legacy track/via net names cleared during synchronization. Compared every retained track to checkpoint 87e689c: geometry is unchanged, and the only remaining net-name changes are four segments of the intended TX_ACTIVE rename. Every other existing pad net is unchanged except J6.14 and D10.2. Saved evidence is in `rf_switch_pcb_validation.json`.

Final DRC reports **626 errors, 268 warnings, 158 unconnected items** across the board. There are zero listed DRC violations involving the 13 RF parts placed in this step, excluding the separately reported unconnected items. This is placement acceptance only, not routing or fabrication acceptance. The previous pre-RF checkpoint had 631 errors, 273 warnings and 140 unconnected items.

## Still required

- Select and audit low-capacitance **bidirectional** antenna ESD protection with sufficient RF voltage headroom; it is not installed yet. Do not use a simple unidirectional clamp that forward-conducts on the RF negative swing.
- Validate C102 impedance, self-resonance, voltage/power margin, and common-port tuning at 435/437 MHz using exact purchasing parts and VNA measurements. The pSemi evaluation-board tuning capacitor is layout-dependent; its published insertion loss must not be assumed for this board without matching work.
- Route the placed switch circuit: controlled-impedance RF branches with a solid ground return, local ground vias, regulated power and control. PCB synchronization and initial placement are complete; J5 and its antenna feed, plus the old TX feed into J9, have been removed.
- Verify TX-to-RX leakage at actual TX power, receiver survivability, switching transients, and PA disable behavior. No hot-switching acceptance is implied.
- Update remaining overview/connector prose that still describes VHF or separate TX/RX antennas.
- Complete remaining RF identities, LNA choke, LO drive, PCB DRC and assembly review before fabrication.

## Primary sources

- [pSemi PE4259 DOC-03694-5.01, July 2026](https://www.psemi.com/pdf/datasheets/pe4259ds.pdf)
- [TI TLV755P SBVS320D, September 2024](https://www.ti.com/lit/gpn/TLV755P)
- [TI SN74LVC1G17 SCES351Y, October 2025](https://www.ti.com/lit/gpn/sn74lvc1g17)
- [Raspberry Pi Pico pinout](https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008309-DS-1-Pico-R3-A4-Pinout.pdf?disposition=inline)
- [KiCad 10 schematic editor: top-level sheets](https://docs.kicad.org/10.0/en/eeschema/eeschema.html)

## Implemented D15 — 2026-09-09

D15 is wired across ANT/GND on RF_Switch and synchronized through the native UUID-based PCB update. Pad 1 = GND; pad 2 = ANT. F.Cu position (131.5, 139.65) mm, rotation 90 degrees; pad 1 center (131.5, 140.05), pad 2 center (131.5, 139.25). J9 remains the only antenna connector. The RF conductors and local ground connection still require routing.

Native ERC after insertion: zero active errors/warnings, existing two exclusions and four ignored checks unchanged. Konnect reports zero floating wires, unconnected required symbol pins, shorts and orphan items on RF_Switch. Final refilled PCB DRC: 626 errors, 268 warnings, 159 unconnected items; no violations involving D15 or C102. All 633 retained track/via objects match the pre-D15 geometry and net names after restoring nine legacy net names cleared by synchronization. Board contains 145 footprints including the 20 retained legacy items. Not fabrication-ready.
