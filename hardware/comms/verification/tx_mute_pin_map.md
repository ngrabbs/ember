# TX mute pin-map acceptance — 2026-10-03

Texas Instruments **SN74LVC1G08DBVR**, DBV / SOT-23-5. TI SCES217AA (August 2026), pin configuration p.3 and DBV package drawing. Source: https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf

Symbol `74xGxx:74LVC1G08`; footprint `Package_TO_SOT_SMD:SOT-23-5`.

| Lead | Function | Symbol pin / type | Footprint pad | Local X/Y mm | View / direction | Evidence |
|---|---|---|---|---|---|---|
| 1 | A | 1 / input | 1 | -1.1375 / -0.95 | top, CCW from upper-left key | TI p.3, disposable query |
| 2 | B | 2 / input | 2 | -1.1375 / 0 | top, CCW | TI p.3, disposable query |
| 3 | GND | 3 / power_in | 3 | -1.1375 / 0.95 | top, CCW | TI p.3, disposable query |
| 4 | Y | 4 / output | 4 | 1.1375 / 0.95 | top, CCW | TI p.3, disposable query |
| 5 | VCC | 5 / power_in | 5 | 1.1375 / -0.95 | top, CCW | TI p.3, disposable query |

Five physical leads, five electrical symbol pins, five electrical pads; no duplicate pads, exposed pad, mechanical pads or drills. Front copper/mask/paste SMD pads. Queried symbol and footprint, placed disposable U1, read back all pins/pads, and inspected rendered schematic and enlarged front copper/silk/fab/courtyard. Upper-left silk triangle and fab bevel identify lead 1; three left and two right pads match the top-view lead geometry and 0.95 mm pitch. Accepted for this exact TI DBV part. Scratch evidence: `work/mute-acceptance` in the task workspace. Production placement was checked again after native schematic synchronization: all five U14 pad assignments match the exported native schematic netlist, with zero board-wide assignment mismatches. See [saved validation](evidence/tx_hardware_mute_validation_2026-10-03.json).
