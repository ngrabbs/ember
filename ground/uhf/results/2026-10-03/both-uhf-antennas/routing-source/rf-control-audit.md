# RF control audit — implementation gate

Source: clean SDRB commit cd93c99f8d041ea1e106f6ac1e84429d77d282e5 and hardware/inventory/sdrb-v02.net.xml. No target programming or GPIO writes performed.

## Electrical issue to resolve first

The six RF-switch control nets connect directly to bank 35, whose VCCO is +3.3V in the netlist. Skyworks SKY13588-460LF datasheet 203512D, pages 2–3, specifies an operating logic-high range of 1.65–3.00V and an absolute maximum of 3.30V. Consequently a direct LVCMOS33 high is not a qualified interface and has no absolute-maximum margin at nominal 3.3V. Reduced drive strength does not establish a safe output voltage. Do not change the whole bank supply or select a mismatched I/O standard as a workaround.

The netlist resolves the likely intended interface: all six 10k resistors connect to +1V8. Implement open-drain behavior: drive 0 for low, tri-state for high. Never actively drive 3.3V high. Validate input/output buffer configuration, configuration-time pulls and actual measured high voltage before qualification. Rework is not currently indicated by this audit.

Reference: https://www.skyworksinc.com/-/media/SkyWorks/Documents/Products/2201-2300/SKY13588_460LF_203512D.pdf

## Control mapping

| Function | Control V1 / V2 | FPGA balls | Probe on control-connected resistor pads | Schematic sheet |
|---|---|---|---|---|
| RX1 U10 | U10_V1 / U10_V2 | E20 / E19 | R73 / R72 | 2 |
| RX2 U11 | U11_V1 / U11_V2 | G21 / G20 | R75 / R74 | 2 |
| TX U12 + U1, shared | U12_V1 / U12_V2 | A17 / A16 | R92 / R91 | 3 |
| TX power IC4 | Xmit Path Power Enable | D20 | IC4 pin 3, only if accessible | 3 |

The RF controls have 10k pull-ups to +1V8, confirmed by netlist connectivity for R72/R73/R74/R75/R91/R92 pin 2. High-impedance controls therefore tend toward 11 (J3), not shutdown. Verify actual population and voltage. IC4 EN/UVLO has no external pull-down in that netlist. Audit its default separately; do not assume the PA is disabled before FPGA configuration.

Truth table (V1 first, V2 second): 00 shutdown; 10 J2; 01 J1; 11 J3. RX1 J2 connects U6 BFCN-2360+, J1 U8 BFCN-5750+, J3 U4 RLP-470+. RX2 uses U7, U5, U9 respectively. These are schematic path names, not measured passbands. TX 10 selects direct shared Path B, 01 Path A, 11 Path C; do not enable amplification during first GPIO tests.

## Implementation sequence

1. Confirm bench power/cable state before touching the target. With probes clear, retain the working r3 SD image as recovery.
2. Measure bank 35 supply and each control voltage in the existing baseline. Arrange probes while powered down and discharged; coordinate power-up and record readings. No need to probe BGA balls: use the resistor pads above. Verify a reliable board ground before interpreting readings.
3. Validate the open-drain control interface and PA default behavior. Confirm physical population/rework on each board independently.
4. Extend the one canonical hardware generator with a selectable RF-control profile, preserving the proven PS settings. Use six named open-drain controls (output data fixed at zero, direction/tri-state selects low versus release) and keep PA enable forced low for the initial profile. Decide EMIO versus AXI GPIO after confirming reset/output-enable behavior. Keep IC2 controls outside this change. Correction from the AD9361 audit: B15 selects the reference clock; F18 controls the separate J6 analog channel.
5. Build in a new output directory; capture constraints, DRC/timing, bitstream, XSA and hashes. Rebuild matching FSBL/boot artifacts and DT. Do not mix a new bitstream with an undocumented old handoff.
6. Add named Linux GPIO ownership with all-off startup and persistent line requests. Line release/process exit may restore pull-up-selected J3, so a process lifetime alone is not a shutdown guarantee; address this in the controller/reset design. Route changes must pass through 00, with adequate shutdown/startup settling; a conservative millisecond dwell is suitable for the initial manual test, not precise RF timing.
7. First test low levels and boot/reset behavior, then each valid RX route with PA held off. Record actual pin voltages and later RF-path measurements separately. Only then qualify TX power and AD9361 operation.

Status: schematic/datasheet audit only. No new bitstream built or loaded; no routes or PA behavior qualified.
