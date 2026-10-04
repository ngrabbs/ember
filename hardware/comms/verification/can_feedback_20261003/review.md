# CAN feedback and schematic cleanup checks — October 3, 2026

Status: INCOMPLETE for fabrication; checks run, synchronization/routing work outstanding. No circuit or routing changes made during this review.

- Editor-native ERC: 0 errors, 2 existing MCP25625 library mismatch warnings; 4 ignored test types. Command-line ERC produced 38 spurious dangling-wire errors and command-line netlist omitted unnamed nets (52 vs 209); do not use these outputs for schematic synchronization. Editor-generated netlist is archived here.
- Saved PCB Konnect DRC: 0 errors, 0 unconnected, 1 existing fixed H1/H2 silk warning.
- Full editor netlist: 209 nets. Compared against 556 PCB pad entries. C69.1 changed from RX_AMP_IN to VREF_RX; R39.1/.2 reversed. The resistor reversal is electrically neutral; the capacitor connection change needs review and PCB synchronization. TX mute net labels removed without node membership changes.
- CAN names changed to CAN_A_H_P / CAN_A_L_N and CAN_B_H_P / CAN_B_L_N in the schematic only. These lack a common differential-pair stem; use CAN_A_P/N and CAN_B_P/N (H=P, L=N) if using native pair recognition.
- MCP25625 SSOP pins 23, 6, 7 are TX0RTS, TX1RTS, TX2RTS, input-only with nominal 100 kohm internal pullups. Actual schematic ties all to +3V3. Active-low does not imply an output capable of shorting this rail; no resistor is required for that claimed failure mode. An external pullup is optional for externally assertable signals, not a correction for a programmable-output hazard.
- Existing CAN trunk traces are 0.2mm wide with long parallel portions at 0.65mm center spacing (0.45mm edge gap). Endpoint fanouts, layer transitions, and termination branches are not consistently symmetric. Total segment length including branches: A H=83.514mm/L=77.719mm; B H=126.529mm/L=128.197mm. These are net totals, not endpoint skew measurements. Reference-plane continuity and controlled differential impedance are not signed off by this check. Plan paired-routing cleanup with common stems and matched layer transitions before release; do not add arbitrary meanders solely to equalize branched net totals.

Sources: Microchip MCP25625 datasheet DS20005282C Table 1-1 and section 3.6.5; TI TCAN4550 layout guidance https://e2e.ti.com/support/interface/f/interface-forum/977249/tcan4550-layout-guide .

The earlier ZIPs predate these schematic edits. Regenerate review/manufacturing deliverables after synchronization and CAN routing validation.
