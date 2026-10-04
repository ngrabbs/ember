# Stock substitution qualification — 2026-10-03

Status: all 11 substitutions applied through Konnect, synchronized using native KiCad F8, and saved. DRC: 0 errors, 0 unconnected, 1 existing H1/H2 silkscreen warning. BOM: 153 placements, all 147 purchasable placements have valid LCSC Part #; zero PCB field mismatches. Before/after pad coordinates, nets, track geometry and component positions are identical. Native synchronization proposed only these 11 field changes and U12 value change (0 warnings/errors); 209-net/556-pad baseline connectivity parity has zero mismatches. Native ERC was not rerun in this pass; final release validation remains required.

## Sources and suitability

- U12: TI TLV73330PDBVR, C882826, DBV SOT-23-5, live stock 1,003. TI SBVS235C (July 2019), pin table PDF p4; package DBV0005A 4214839/K (08/2024), PDF pp36–38. https://www.ti.com/lit/ds/symlink/tlv733p.pdf . 3.0 V, 300 mA; accepts 5 V input/enable, stable with the existing 1 uF output capacitor. The +3V0 load is U11 PE4259, U13 SN74LVC1G17, 10k bleed R37 and bypass capacitors, not the Pico or PA. Existing input capacitance retained. No rail topology changes.
- D12/D13: Lite-On LTST-C190KGKT, C125094, top-view 0603, live stock 613,210. Manufacturer BNS-OD-FC002/A4, downloaded via JLCPCB C125094; package and cathode drawing PDF p2. Body 1.6 × 0.8 mm, bottom solder terminals about 0.4 × 0.7 mm. Two unnumbered physical terminals; cathode mark explicitly establishes KiCad pad 1. Existing 1k resistors R26/R31 give roughly 1.3/3 mA at typical 2 V Vf, below 20 mA. Brightness is not guaranteed equal to the former side-view LED.
- L12/L13/L19–L24: Murata LQW15AN10NG00D, C90642, 0402 wirewound nonmagnetic, live stock 33,826. Murata O05E Nov 25 2013, catalog pp184–185 (PDF pp1–2), https://doc.platan.ru/pdf/datasheets/murata/LQW15AN_00.pdf . 10 nH ±2%, 500 mA, DCR <=0.17 ohm, Q >=25 at 250 MHz, SRF >=5.5 GHz. Body 1.0 × 0.6 mm (±0.1), two interchangeable unnumbered ends. D suffix denotes paper-tape packaging.

## Physical mapping acceptance

All footprints are top-side, unmirrored in the disposable test, SMD F.Cu/F.Paste/F.Mask, no drill, duplicate leads or mechanical pads. Coordinates below are relative to footprint origin, in mm, +Y down. U12 retains the existing SOT-23-5 footprint; new TLV733 symbol has identical numbered pin coordinates/types to TLV755.

| Datasheet physical lead | Function | Symbol pin / type | Footprint pad | X,Y | Drawing evidence |
|---|---|---|---|---|---|
| TI 1 | IN | 1 IN / power_in | 1 | -1.1375,-0.95 | DBV top view, upper left from index area |
| TI 2 | GND | 2 GND / power_in | 2 | -1.1375,0 | DBV top view, left middle |
| TI 3 | EN | 3 EN / input | 3 | -1.1375,+0.95 | DBV top view, lower left |
| TI 4 | NC | 4 NC / no_connect | 4 | +1.1375,+0.95 | DBV top view, lower right |
| TI 5 | OUT | 5 OUT / power_out | 5 | +1.1375,-0.95 | DBV top view, upper right |
| Lite-On marked cathode (unnumbered) | K | Device:LED 1 K / passive | 1 | -0.7875,0 | PDF p2 bottom-terminal cathode mark; placed top view mark at left |
| Lite-On opposite terminal (unnumbered) | A | Device:LED 2 A / passive | 2 | +0.7875,0 | Opposite cathode, PDF p2 |
| Murata first end (unnumbered) | interchangeable | Device:L 1 / passive | 1 | -0.485,0 | PDF p1 side/bottom views; no polarity |
| Murata opposite end (unnumbered) | interchangeable | Device:L 2 / passive | 2 | +0.485,0 | PDF p1 side/bottom views; no polarity |

Counts: regulator 5/5/5 physical/symbol/pads; LED 2/2/2; inductor 2/2/2. Standard pad sizes: SOT 1.325 × 0.6; LED 0.875 × 0.95; inductor 0.56 × 0.62 mm. Disposable symbols placed/rendered and read back; disposable footprints placed through Konnect on a saved closed scratch board after releasing its editor lock, exported and visually inspected. Pin-1 SOT chamfer and LED cathode bar agree with mapping; footprint courtyard and fab outlines present. The real board retains identical footprints, locations and routing.

## RF screening

Murata exact LQW15AN10NG00.s2p v45, downloaded 2026-10-03 from https://www.murata.com/en-eu/tool/data/sparameterdata/sparameter-inductor . Model header specifies series mode, 50 MHz–20 GHz, 50 ohm S RI. Checked S11+S21=1; converted Z=100*S11/S21 and interpolated complex Z. Raw vendor model retained only in local scratch.

Current saved-board geometry was read through KiCad pcbnew. Existing rf_filter_vendor.py screening network was reused with the Murata impedance substituted. At 435 MHz Coilcraft model Z=0.6252+j27.4363 ohm; Murata Z=0.5972+j27.3257 ohm. The reactance change is -0.40%. At 435/437 MHz modeled filter S21 improves 0.11–0.14 dB across RX, TX output, TX preselector and LO. This supports substitution, not a measured response or full EM qualification. Ideal capacitors and nominal 50 ohm traces remain model assumptions. Existing filter tuning/bench verification requirement remains; no capacitor changes.

## Mixer decision

User explicitly elected to retain ADE-1+ C2942210 despite the six-piece stock snapshot. Need two nominal; stock and assembly allowance must still pass the actual order preview. Nothing has been purchased or reserved.
