# TX startup and reset review — October 3, 2026

Status: hardware mute implemented in the schematic and routed PCB on October 3, 2026. Firmware sequencing and prototype measurements remain open.

## Problem addressed (before the change)

Native exported netlist (208 nets, 544 nodes) confirms:

- Y2 CLK0 on pin 10 feeds U7 input 1 through the clock coupling network. CLK1 on pin 9 supplies the separate receive LO chain.
- U7 output 4 connects directly to C73 pin 2 on `/TX Chain/RF_TX_BPSK_145`; C73 pin 1 feeds Q3's base.
- TX_ACTIVE joins J6 pin 14 (Pico GP10), R35 pin 1 and U13 pin 2. R35 is the 10 kΩ pull-down. U13 drives the PE4259 through SW_CTRL_3V0.
- TX_ACTIVE low selects receive. It does not disable U7, Q3 or the TX amplifier.

A powered Si5351 retains its programmed configuration during a separate Pico reset. Its MSOP-10 package has no external output-enable pin. Holding BPSK_DATA constant still passes a carrier through the XOR when its clock is running. Thus switch defaulting to RX is not equivalent to muting the TX source.

## Implemented hardware change

Added **U14, Texas Instruments SN74LVC1G08DBVR (JLCPCB C7666)**, a 3.3 V AND gate between U7 output 4 and C73 pin 2. Pin 1 receives U7's modulated carrier on `/TX Chain/RF_TX_BPSK_RAW`; pin 2 receives existing TX_ACTIVE; pin 4 drives C73 on `/TX Chain/RF_TX_BPSK_145`. Pin 3 is GND and pin 5 is +3V3. R35's existing 10 kΩ pull-down remains. No additional Pico GPIO is needed, and the separate CLK1 receive path is unchanged.

Added **C115, Samsung CL05B104KO5NNNC (JLCPCB C1525)**, 100 nF, 16 V X7R, 0402, between +3V3 and GND near the local gate supply. The uncached stock observations were 70,877 gates and 35,496,429 capacitors; these are not reservations. The [symbol/footprint pin-map acceptance](tx_mute_pin_map.md) was completed before insertion and checked again against the native production netlist and PCB pads.

U7 moved locally to fit U14. The gate's carrier input trace is approximately 2.49 mm; its output retains the short C73 approach. Clock, I²C and local supply routes were adjusted and zones refilled. The clock feed now includes a bottom-layer segment and must be checked with the actual load during bring-up. H1/H2 and all four mounting-hole placements are unchanged.

| TX_ACTIVE | U7 output | Gate output |
|---|---|---|
| Low | Either state / running carrier | Low |
| High | Modulated carrier | Modulated carrier |

The low-state truth table provides the intended digital mute while supplies are valid. It does not establish zero RF feedthrough or behavior below the specified supply range. Gate delay is specified up to 3.6 ns at 3.3 V ±0.3 V and 15 pF, -40 to 85 °C. This is **not a guaranteed 145.667 MHz bandwidth specification**. The actual Q3/coupling-network load, waveform, gain and disabled leakage must be checked on the prototype. Keep the added route short and provide rework access. A firmware hang with GP10 stuck high is not covered by a simple GPIO-controlled gate; watchdog reset must restore the GPIO to its pulled-down state.

## Required sequencing and firmware work

1. Boot/reset: let R35 hold TX_ACTIVE low; explicitly initialize GP10 low before other board activity. Keep BPSK data static. Do not transmit automatically at boot.
2. Initialize Si5351 with outputs disabled, configure the PLLs/dividers, check status, then enable only the receive LO as needed. Keep CLK0 disabled until an explicit TX request.
3. Enter TX: confirm CLK0 is disabled, set TX_ACTIVE high, allow the switch to settle, then enable CLK0 and start the intended modulation. On I2C failure, lower TX_ACTIVE and report failure.
4. Exit TX: disable CLK0 and stop modulation before selecting RX. If I2C shutdown fails, lower TX_ACTIVE anyway so the hardware gate blocks the continuing carrier.
5. Verify cold start, Pico RUN reset, watchdog reset during TX, failed/stuck I2C, and repeated TX/RX transitions using a load and measurement equipment before antenna use.

PE4259's 1.5 µs switching time is **typical at 1 GHz**, not a guaranteed maximum for this assembly. A conservative firmware guard interval needs validation on the prototype; do not treat 1.5 µs as a release limit.

Current firmware findings: `si5351_init()` writes output-enable register 3 to 0xFC at the end, enabling both CLK0 and CLK1. The application self-test only probes the Si5351 and does not call this initializer. It therefore does not clear a clock state left running before a Pico reset. The clock bring-up executable calls the initializer and has explicit output-enable controls. Update this behavior during the new dual-CAN firmware port; do not claim that changing an unused initializer alone fixes current application startup.

## Sources and evidence

- [Si5351 manufacturer datasheet, configuration and programming sequence](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si5351-B.pdf).
- [TI gate datasheet, DBV pin map, switching limits and truth table](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf).
- [JLCPCB exact TI part](https://jlcpcb.com/partdetail/TexasInstruments-SN74LVC1G08DBVR/C7666).
- [Konnect sourcing response](evidence/tx_inhibit_candidate_stock_2026-10-03.json).
- [PE4259 datasheet](https://www.psemi.com/pdf/datasheets/pe4259ds.pdf).

## Saved validation

- Native schematic ERC: **0 errors**, two existing MCP25625 library-difference warnings, four ignored tests.
- Saved PCB DRC: **0 non-excluded errors, 0 unconnected items, 11 existing warnings**; existing fixed-interface exclusions remain.
- Native netlist: **209 nets, 551 nodes**; 556 PCB pad-map entries checked with **zero assignment mismatches**. Mute input, output, enable and supply node sets were explicitly asserted.
- RF ground-plane screen: 20,587 samples; 189 misses remain confined to the existing antenna signal PTH opening. This screen does not establish impedance or clock-edge integrity.

[Validation evidence](evidence/tx_hardware_mute_validation_2026-10-03.json) · [C115 stock response](evidence/tx_mute_bypass_stock_2026-10-03.json).

Firmware was not changed. Power sequencing, watchdog behavior and prototype waveform/leakage measurements remain required. This change does not close the other fabrication release gates.
