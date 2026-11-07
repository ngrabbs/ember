# CAN A/B supply branches — development integration contract

2026-10-24; basis `2d1ff31`, 275 physical parts /146 nets /11 sheets. This contract releases a coherent **development** schematic block once its stock inverter's disposable physical map passes. It does not release PCB placement, guaranteed B-bus survival, hot fault response or flight qualification. The user has authorized completion of EPS and approved the TPS2553 construction; its package is already verified. No new custom part is required.

## Selected scope and topology

Each existing TCAN3413DR gets a separate TPS2553DBVR-1 latch-off switch with 210 kΩ ILIM, followed by a 1 Ω resistor and its existing 1.2 µF nominal local reservoir. Use the post-switch resistor arrangement from the [six completed coupled comparison runs](../verification/controller_rev_b/coupled_branch_screen/README.md). Its intended fault scope is a transceiver/downstream-rail short. A short at TPS OUT before that resistor remains a documented weakness; an internal switch/input fault is not fully contained. Moving the resistor upstream is not selected because that experiment collapses TPS IN below its operating range. Neither experiment establishes a guaranteed maximum initial pulse or healthy shared-source behavior.

The design introduces `3V3_CANA` and `3V3_CANB`. For each channel migrate only TCAN VCC/VIO and that channel's three existing capacitor positive pins from shared `+3V3`. Existing TXD/STB 10 kΩ pullups remain on essential `+3V3`, **on the MCU side** of newly inserted 1 kΩ series signal resistors. Do not put an externally driven pullup on the disabled branch: a GPIO could then feed the off rail through that resistor regardless of IC Ioff. Add a 47 kΩ MCU-side RXD pullup to essential `+3V3` to define recessive when TCAN is unpowered. Add a 10 kΩ branch bleeder; its current fits the existing conservative normal-load allocation, but complete off-state feed/discharge remains unqualified.

Both TPS INs and the control inverters use permitted essential `+3V3`; nothing new is retained upstream of RBF. Returns remain `GND`. All other existing parts, raw returns, charger/BMS supply and interface names are preserved.

## Reset ownership without extra MCU pins

Use **one TI SN74LVC1G14DBVR Schmitt inverter per channel**, stock `74xGxx:SN74LVC1G14DBV`, with stock `Package_TO_SOT_SMD:SOT-23-5_HandSoldering`. Its accepted pin contract must be 1 NC, 2 A, 3 GND, 4 Y, 5 VCC, using exact primary TI top view. Keep the stock generic-land deviation and worst-flash courtyard limitation explicit; reserve at least 4.76 ×4.05 mm for each inverter at layout/area review. No library or footprint authoring is authorized by this contract. Retain actual NC correctly, not as a workaround for an unfinished functional pin.

Connect inverter A to the existing MCU-side `EPS_CAN_A_STB` or `EPS_CAN_B_STB`; Y drives that channel's TPS EN through 1 kΩ. Fit 100 kΩ EN-to-GND at the TPS pin. Existing R102/R104 10 kΩ pullups define MCU reset behavior; they remain on the essential MCU side. Use a 100 nF local bypass at each inverter and TPS input.

| Existing MCU control | TCAN STB through 1 kΩ | TPS EN through inverter | Board behavior |
| --- | --- | --- | --- |
| HIGH or floating with existing pullup, valid supply | HIGH | LOW | Channel disabled; latch-reset command; no CAN wake reception |
| LOW | LOW | HIGH | Channel powers up and enters normal mode after startup |

This deliberately changes the board-local standby command's behavior from powered standby to **branch disable/reset** while preserving its net name and physical pin. Firmware and pin-allocation records must state that semantic change. It consumes no new MCU pins. Both channels are brought into normal mode after initialization, preserving the planned initial fallback operating policy. A disabled channel cannot wake the MCU over CAN. MCU, clock, inverter supply and essential power remain shared/common-cause resources.

FAULT gets a 10 kΩ pullup to essential `+3V3` and an independent bench test point per channel. **Do not allocate nonexistent spare FAULT GPIOs** or claim direct remote switch-fault telemetry. CAN controller state/traffic/heartbeat can report channel unavailability but cannot identify the TPS fault cause conclusively.

## Startup and recovery contract

Keep both controls HIGH while configuring UCPD reset restrictions, GPIOs, clock and FDCAN. Preload HIGH before selecting output mode; configure recessive TXD before requesting power. Then drive each control LOW separately and allow a provisional20 ms settling interval before using that channel. TI lists3 ms TPS turn-on/turn-off under its specified1 µF/100 Ω fixture and1.5 ms TCAN startup after UV release; the real load/capacitance/source must still be qualified. The20 ms interval is a planning choice, not a guaranteed combined startup limit.

On an explicit recovery request through healthy B, hold only A's control HIGH for at least20 ms, then return it LOW with TXD recessive and requalify its clock/controller/traffic. Use the same sequence symmetrically for B. EN cycling clears the latch as specified, but it is **not** proof of complete transceiver power cycling: rail discharge and all leakage/back-power paths remain open. No autonomous endless retry. A reset returning controls to HIGH disables the branches until initialization; diagnostics stay unavailable until communication is re-established.

## Parts and exact electrical boundary

Per channel add2 ICs,10 resistors,2 capacitors and1 test point:30 added physical parts in total. Allocate unused references after querying current inventory; never reannotate existing objects.

| Quantity per channel | Function / exact component |
| --- | --- |
| 1 | Approved TPS2553DBVR-1 project symbol/footprint, existing custom-review enclosure |
| 1 | Stock SN74LVC1G14DBVR, manufacturer/source metadata and verified five-pad stock footprint |
| 1 | ILIM210 kΩ, TNPW0603210KBEEA |
| 1 | Post-switch1 Ω, CRCW12061R00FKEAHP,1%,100 ppm/K,0.75 W P70 |
| 4 | TXD/RXD/STB/EN series1 kΩ, TNPW06031K00BEEA |
| 1 | EN pulldown100 kΩ, TNPW0603100KBEEA |
| 2 | FAULT pullup / branch bleeder10 kΩ, TNPW060310K0BEEA |
| 1 | MCU-side RXD pullup47 kΩ, TNPW060347K0BEEA |
| 2 |100 nF X7R100 V10%, GRM188R72A104KA35D,0603 |
| 1 | FAULT test pad, existing stock test-point convention |

TNPW parts retain0.1%,25 ppm/K,0.11 W general P70 metadata, matching existing family rules. Update per-instance fields through single-component edits when batch operations do not create missing properties; query final saved CLI fields. The exact CRCW ordering token must match the previously accepted selected part, including suffix if the actual existing source record uses one; do not truncate or invent it.

Existing power-terminal migrations are exactly U101.3/.5,C104.1,C105.1,C106.1 to3V3_CANA and U102.3/.5,C107.1,C108.1,C109.1 to3V3_CANB. All negative capacitor and TCAN ground pins stayGND. Keep R101/R102/R103/R104 on+3V3, but their signal sides stay with the original global MCU nets before new series resistors. Existing MCU TX/RX/STB global names stay at the MCU and series-resistor MCU endpoints; TCAN-side segments get distinct local signal names. No CAN_H/L rename, termination change, connector migration or bus protection claim belongs in this block.

Prefer one new unique ANSI B CAN Branch Power child for switch/limit/reset circuits and existing CAN Interfaces for local signal resistors and transceiver bypass. Wire local topology, use globals only for actual page crossings and upward power/downward ground symbols. Assign actual project classes to every new functional net; preserve all existing patterns and report inherited orphan patterns separately. New post-switch source flags, if needed for ERC, must correspond to the real TPS output through the passive resistor.

## Electrical and visual acceptance remain separate

[Static screen](../verification/controller_rev_b/branch_control_screen/calculations.json) checks reset pullup, inverter/EN load, signal margins and resistor currents under declared powered/configured GPIO allocations. RXD high margin is only about68 mV under its conservative cross-corner guard. TI Schmitt threshold rows are discrete supply test points; using adjacent3.0/4.5 V rows is a development guard, **not** a continuous-supply/PVT guarantee. Resolve real MCU conditions, parasitic loading and500 kbit/s timing before electrical release. TCAN Ioff at VCC=VIO=0 does not establish every partial-power or destructive bus-to-logic failure.

Before freezing the native integration, compare all preserved UUIDs/fields and exact endpoint sets, including every allowed migration and new branch. Check the complete root netlist/ERC, all functional net-class memberships and physical maps. Render and inspect every sheet at page/detail scales, with targeted CAN/control views. Retain the existing seven unfinished MCU pins and three intentional joins honestly; do not add fake NCs or ERC suppression. Produce a scoped verifier and immutable evidence hashes, then hand back and freeze before root independent verification. No real PCB synchronization. Hardware/flight qualification remains open.
