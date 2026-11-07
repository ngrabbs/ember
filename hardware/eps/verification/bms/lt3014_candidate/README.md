# LT3014 isolated-bus post-regulator: stock package acceptance

2026-10-24. Exact candidate **LT3014IS5#TRPBF**, stock `Regulator_Linear:LT3014xS5`, passes the development physical-map gate with unchanged stock `Package_TO_SOT_SMD:TSOT-23-5_HandSoldering`. A new independent disposable fixture was built through Konnect after explicit release. **No real EPS circuit or library changes; full supply and assembly qualification remain open.** UCC/TLV and earlier UART/BMS evidence are unchanged.

## Primary source and inspection

[ADI LT3014 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/3014fd.pdf), `3014fd`, Rev D / LT0808, downloaded through official Chrome PDF viewer after curl returned HTTP/2 INTERNAL_ERROR. The 16-page PDF remains `/tmp/ember-lt3014.pdf`; exact hash/bytes in `source.json`. Pages **2, 3, 7–11 and 14** were rendered at 2× with pypdfium2 and actually opened. These include the full table columns, pin functions, adjustable application, capacitor/thermal/reverse-fault sections and S5 package. Page4 Note10 continuation was read: I grade is guaranteed over the full −40..125°C junction range; E grade's characterization assurance is different. S5 ordering p2 explicitly includes the selected I-grade tape/reel suffix.

## Electrical limits and conditions

- Full-temperature marked ADJ reference row: **1.180..1.260 V**, typical1.220 V, at 3.3<VIN<80 V and100 µA<ILOAD<20 mA, ADJ tied to OUT for the table test. The single25°C row is1.200..1.240 V at3.3 V/100 µA. Divider-scaled 3.3 V output accuracy must use the full marked row, resistor tolerance/TCR and bias-current conditions; do not substitute ±1%.
- Rated20 mA output, minimum input voltage3.3 V maximum at20 mA. Guaranteed full-temperature dropout maxima are250/360/450/570 mV at100 µA/1/10/20 mA. These use the3.3 V divider test in Note4, including5 µA divider load. The350 mV headline at20 mA is typical.
- GND-current maxima20/30/100/450/1000 µA at0/100 µA/1/10/20 mA output, all full-temperature marked. Note6 tests dropout as worst-case ground current; it decreases slightly at higher input voltage. SHDN current is separate where relevant. Do not interpolate an unqualified whole-load maximum from the typical curve.
- Shutdown off-to-on threshold2 V max; on-to-off0.25 V min (both typical1.3 V), full-temperature marked. Tie unused SHDN to IN or defined logic high. It may be driven by5 V logic or open collector with pullup. AtSHDN=0 V, current flows **out** of the pin:1 µA typical/4 µA max; at6 V0 typical/1 µA max. Shutdown IQ1 typical/4 µA max atVIN6 V.
- Input reverse leakage ≤6 mA atVIN−80 V, OUT0, full-temperature marked; input reverse-voltage protection is not zero leakage. Output short duration is indefinite within thermal/absolute limits. Current limit70 mA typical at7 V input/OUT0, and25 mA minimum full-temperature at the separate3.3 V/−0.1 V regulation-loss test. This is not a selected downstream fault-current limit.
- COUT **≥0.47 µF effective**, ESR≤3 Ω. Larger output capacitance improves load transient response; load bypass counts toward it. Verify ceramic DC-bias, temperature, tolerance and aging rather than using nominal value. Input bypass0.1–10 µF is advised; required when more than6 inches from the main filter capacitor. This local regulator still needs actual input/source and load-step checks.
- Output noise115 µVrms is **typical25°C**,10 Hz–100 kHz,20 mA and0.47 µF. Ripple rejection60 dB minimum/70 typical has **no full-temperature dot** and applies7 V average input,0.5 Vpp at120 Hz/20 mA. Do not treat it as guaranteed high-frequency attenuation of the UCC burst/switching spectrum.

## Reverse and fault scope

Actual p8/p11 explicitly cover an output held up while IN is grounded, at intermediate voltage or open; the output acts as though a diode were in series and blocks reverse flow to the input. The state of SHDN does not change this behavior. This is materially different from TLV767's unrestricted reverse-current path and can avoid its external bypass-diode issue.

However, **numeric reverse-output current2 µA typical/4 µA max is a25°C test atOUT=ADJ=1.22 V with grounded IN**, not a3.3 V/all-temperature guarantee. Figure4 is typical25°C withOUT=ADJ; p11 says input current typically falls below2 µA withOUT>IN. Preserve those qualifications. Output-to-ground reverse leakage and external divider current still discharge a held-up output; they are not a direct raw/system ground bridge or proof of zero current measurement error.

No external reverse-protection diode is required by the described normal reverse-output scenario. That does **not** establish independent output overvoltage protection: p11 states pulling ADJ below reference while powered causes current limit and an **unregulated high output**. Divider open/short, pass-device failure, input OV, startup/load transients and ISO1540 maximum/minimum supply remain system gates. ADJ absolute clamp±7 V; when external output forcing would exceed that clamp, limit ADJ current to<5 mA. Normal maximum junction125°C remains mandatory despite thermal limiting; dissipation includes IOUT×(VIN−VOUT)+IGND×VIN, not only pass loss.

## Stock physical map

S5 top-view p2 has1–3 down the left,4–5 up the right; stock front-view pad coordinates agree. The physical package drawing p14 has pin1 lower left and the three leads along the bottom; rotate it90° clockwise to the stock orientation. It is **TSOT-23**,1.00 mm maximum height, no EP/NC/mechanical contacts. The DFN pin map/EP9 does not apply.

| Physical S5 lead | Stock symbol name/type | Stock pad | Front X/Y mm |
|---|---|---|---|
| 1 IN | VIN / power_in | 1 | −1.1375 / −0.95 |
| 2 GND | GND / power_in | 2 | −1.1375 / 0 |
| 3 SHDN active low | ~SHDN / input | 3 | −1.1375 / +0.95 |
| 4 ADJ | ADJ / input | 4 | +1.1375 / +0.95 |
| 5 OUT | VOUT / power_out | 5 | +1.1375 / −0.95 |

`symbol.json`, `default_sot_footprint.json`, `tsot_footprint.json` and `handsolder_footprint.json` are saved Konnect readbacks. Symbol default is `Package_TO_SOT_SMD:SOT-23-5`; the existing **TSOT-23-5** candidate has the same five raw copper/paste/mask pad objects, no drills,1.325×0.60 mm roundrect ratio0.25, but the correct thin-package identity. Selecting it would be a stock assignment change, not custom authoring. Exact MFG P/N and package fields would need addition on a future instance; the generic symbol does not supply them.

**Stock land/courtyard differences:** ADI p14 recommends pad1.22 mm along-lead ×0.62 mm cross-lead, row centers±1.31 mm after normalization; stock normal pads are1.325×0.60 at±1.1375. ADI maximum body width1.75 mm exceeds the stock F.Fab1.60 mm nominal body; stock body-band courtyardX±1.05 gives only0.175 mm margin to maximum body,0.075 mm below the0.25 mm construction target. This remains a physical acceptance issue, not silently passed.

Existing `Package_TO_SOT_SMD:TSOT-23-5_HandSoldering` is another unchanged stock option: five pads2.0×0.65 atX±1.71/Ysame, full rectangular courtyard±2.96×±1.70; maximum-body margin and pad-to-courtyard0.25 mm are satisfied, with larger area/long toe. ItsF.Fab width1.76 mm covers the stated body maximum. Neither option is the exact ADI recommended land; mask/paste/assembly/thermal/3D acceptance remains open. Do not author a custom derivative under this read-only task.

## Disposable gate and bounded verification

The new `fixture/lt3014_check.kicad_pro/.kicad_sch/.kicad_pcb` contains one unwired stock symbol and one actual placed footprint. Konnect confirmed the exact PCB was the sole managed open document on `ipc:///tmp/kicad/api.sock` before placement; it was placed at50/50 mm, Value set to the exact MPN, saved, then all five live pads queried from IPC. `live_after_save.json`, raw native saved pads and the library query agree on all five numbers, coordinates, dimensions, shape/radii, layers and zero drills. `instance_fields.json` verifies MFG P/N/manufacturer/package/temperature/datasheet/footprint across the saved symbol; `instance_pins.json` and `physical_map.csv` join all five physical leads. These fields were added using the dedicated annotation operation after the field-update tool reported absent custom fields; required metadata was not silently omitted.

Actual **separate visual inspection**: `symbol.png` full B page, `symbol_detail.png`, `board_copper_detail.png` (whole placed part including silk/courtyard), `board_fab_detail.png` and `board_paste_detail.png` were opened. Pin-1 triangle/chamfer and numbering direction agree with the source orientation. Identification is clear; exact MFG P/N is visible as Value and explicit adjacent callout. Auxiliary fields remain stored with the known S11 display-control limitation, not a full presentation-policy pass. The supplied larger stock lands and courtyard are retained, not converted to exact ADI geometry. `board_numbered_detail.png` adds **query-derived numeric overlay** to the actual saved-board copper export; it is not native fab-number artwork. Raw exported SVGs and full one-page `fixture.pdf` remain available.

**Separate electrical fixture check:** direct CLI `fixture.xml` has one physical part and five distinct singleton pin nets. ERC has9 expected errors:5 unconnected pins,2 undriven power inputs and2 undriven signal inputs; zero warnings. No fake NC, wires or PWR_FLAGs were added. These results verify a package fixture, not a functioning regulator circuit. Host Fontconfig warnings during CLI execution are unrelated to ERC and do not indicate annotation cleanliness failure.

Run `verify_fixture.py` with the bundled Python runtime. It checks raw list lengths/counters before dictionaries, all saved/live/library geometry, symbol map/fields, CLI endpoints/ERC and every one of157 tracked main/BMS/UART baseline files byte-for-byte. Its exact Git protected-path guard permits only the three new fixture sources and works before/after commit relative to the captured basis. `native_source_sha256.json` binds current saved fixture sources to the evidence. GUI close returned an AX timeout, but `board_closed.json` confirms zero open boards/requested_open=false; the expected post-close AS_UNHANDLED response is not a transport failure. The scratch project normalized to KiCad meta3 before final hashes. Locks, PRL, history and backups are excluded from evidence hashing. No real integrated circuit placement or production PCB synchronization was performed.
