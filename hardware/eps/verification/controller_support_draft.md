# Controller support circuit draft

2026-10-04. Added through Konnect to the disposable `package_check` project. The original EPS schematic and board were not edited. This is an electrical concept draft, with passive package suggestions and no final passive MPNs.

The sheet uses `+3V3` to mean essential 3.3 V downstream of hardware source interlocks. Both CAN devices and the oscillator remain on that domain. The final integration must preserve this distinction from managed 3.3 V. This sheet supplies neither the regulator nor RBF isolation.

| References | Proposed value | Purpose |
|---|---|---|
| C1, C2 | 100 nF each | Local MCU VDD/VDDA and VDDIO2 bypassing |
| C3 | 4.7 µF | MCU supply bulk |
| C4 | 1 µF | Additional common MCU supply bulk; optional pending budget/ADC review |
| C5, C6 | 100 nF each | CAN A VCC and VIO bypassing |
| C7 | 1 µF | Proposed CAN A local bulk |
| C8, C9 | 100 nF each | CAN B VCC and VIO bypassing |
| C10 | 1 µF | Proposed CAN B local bulk |
| C11 | 100 nF | Oscillator bypassing |
| C12 | 1 µF | Proposed oscillator local bulk |
| C13 | 100 nF | NRST to ground |
| R2, R4 | 10 kΩ each | CAN A/B TXD recessive pull-ups |
| R3, R5 | 10 kΩ each | CAN A/B standby pull-ups |
| R6 | 10 kΩ | Oscillator enable pull-up |

C1/C2 correspond to distinct physical power pins despite their common rail. C5/C6 and C8/C9 similarly require placement near each respective transceiver supply pin. Schematic proximity is not PCB placement evidence. Non-polarized capacitors use proposed 0603 for 100 nF and 0805 for bulk values; resistors use proposed 0603. Select exact voltage rating, dielectric, tolerance, DC-bias derating, leakage and resistor power/temperature coefficient before BOM acceptance. Added local bulk values are design proposals, not manufacturer minimums.

The MCU GP package combines VDD and VDDA at pin 4, VSS and VSSA at pin 5; VDDIO2 is pin 20. No invented VREF, VBAT or VCAP package pin was added. ST's [AN5096 Rev 4](https://www.st.com/content/ccc/resource/technical/document/application_note/group1/38/aa/e4/3e/35/2f/47/8b/DM00443870/files/DM00443870.pdf/jcr:content/translations/en.DM00443870.pdf), Figure 2 p.4, supports the VDD/VDDA and VDDIO2 bypass arrangement. Its generic separate-VREF diagram must not be copied as extra pins on the KET6 package. [DS13560 Rev 6](https://www.st.com/resource/en/datasheet/stm32g0b1vb.pdf), NRST characteristics (Table 60) and external-reset diagram around pp.98–99, shows internal pull-up and 0.1 µF external capacitor; no external pull-up is fitted in this draft. Preserve NRST reset input/output mode for debugger recovery and test reset behavior under supply ramps and BOR/watchdog reset. PA14 remains SWCLK; boot option bytes are not yet defined or programmed.

TI's [TCAN3413 datasheet](https://www.ti.com/lit/ds/symlink/tcan3413.pdf), section 8.4 p.28 and Table 7-3 p.21, supports local 100 nF bypassing and external bias on control pins. Proposed 10 kΩ pull-ups draw nominally 0.33 mA each when driven low; leakage, reset-state behavior and GPIO drive must still be checked across temperature. Standby inhibits normal transmission until firmware configures TX recessive and initializes clocks, filters and queues. After initialization both channels should use normal mode for the planned B recovery path. Standby wake indication is not normal-frame reception.

The oscillator EN input is pulled up rather than left floating. Source-series damping remains to be added/evaluated, and HSE input levels, capacitive load, startup time and the full CAN timing budget remain open.

This support-only checkpoint is historical; see the [current SWD extension](controller_debug_draft.md) for the latest 13-net verification and ERC status.

## Verification

Saved KiCad netlist comparison passed for 11 named nets with exactly their intended component endpoints: +3V3 (24), GND (17), reset (2), oscillator enable (2), A/B TX and STB (3 each), A/B RX (2 each) and HSE (2). Konnect reports zero floating wire endpoints and zero merged named nets. The rendered A3 sheet was inspected, and capacitor/power-symbol positions were adjusted to remove label clashes.

The CAN symbol now uses `TCAN3413D_DRAFT_v3`, and the oscillator uses `ECS_3225MV_DRAFT_v2`; only schematic ground-pin placement changed to avoid value-field collisions. Both physical pin numbers/functions/types were queried back and remain consistent with the package maps. CAN v2 was an unsuccessful orientation trial and is superseded; use v3 only. Footprint assignments on the placed instances were preserved and are present in the export. The schematic package candidates still need default library metadata before full library acceptance.

**Electrical status: INCOMPLETE.** ERC now reports 26 errors: 25 unconnected pins for remaining MCU/bus interfaces, and one undriven essential-supply error because the source is outside this standalone test. No power flags or no-connect markers were used to hide unfinished circuitry. The 48-error signal-only snapshot is historical. No bench, firmware, supply-fault, final-fit or PCB-layout test has run.

Remaining work: debug/reset access, other MCU interfaces and managed-enable defaults, CAN stack interfaces/termination/protection, source-series clock option, supply branch fault-isolation decision, regulator current budget and final passive choices. The scratch PCB remains a separate package-comparison board and was not synchronized to these additions.

[Verified exported endpoints](evidence/2026-10-04_controller_support_verified.json), [saved netlist](evidence/2026-10-04_controller_support.net), [ERC](evidence/2026-10-04_controller_support_erc.json), [symbol readback](evidence/2026-10-04_controller_support_readback.json).

[Review PNG](previews/controller_support.png) and [review PDF](previews/package_check_controller-support-draft_1791114867.pdf) are included in this checkpoint. The scratch native schematic and PCB are outside this PR; the exported netlist and readback evidence above record the verified connectivity.

Scratch source: `/Users/nick/Documents/ChatGPT/EMBER/eps-rev-b-study/package-check-2026-10-04/package_check.kicad_sch`; inspected render: `controller_support.png` in the same directory.
