# Integrated EPS Rev B — essential 3V3 checkpoint

2026-10-23, based on controller integration commit **d8d5580**. [Native project](../../../rev_b/eps_rev_b.kicad_pro) now has a B root plus unique Controller, CAN interfaces and Essential 3V3 children. The reviewed 16-part buck was rebuilt through Konnect with U400, L400, R400/R401 and C400–C411; no new custom parts, historical study changes or PCB synchronization occurred. The preceding [27-part evidence](../integration/README.md) remains immutable.

**This is a development circuit integration, not complete EPS essential-power acceptance.** Source/interlock hardware, charger, BMS and autonomous 3V3 output overvoltage cutoff are absent. SYS_PWR_PERMITTED means an explicitly external bounded permitted source at this checkpoint. #FLG0400/#FLG0401 model that external input/return; #FLG0402 models the real buck output after L400. They neither create a second rail source nor implement missing hardware protection. The two former undriven power/return ERC errors disappear for these stated reasons.

## Circuit and unresolved operating limits

The exact reviewed topology and parts are preserved: LMR51635XDDCR (400 kHz X variant), XAL6060-562MEC 5.6 µH, two 2.2 µF/100 V input ceramics, 100 nF bypass/bootstrap, eight GRM32ER71E226KE15L 22 µF/25 V output ceramics and 31.6 kΩ/10.2 kΩ TNPW0603 feedback. EN is wired to VIN for autonomous startup. No input bulk or external UVLO network was added. The [standalone selection and calculations](../../essential_3v3/native/README.md) remain the engineering authority; integration does not improve their qualification status.

The output bank is 176 µF nominal and conditionally requires at least 96 µF effective after bias, temperature and aging. That floor is not proof of acceptable load-step behavior or CAN's 3.0 V minimum. Controller/CAN nominal bypass totals another 13.2 µF on the same +3V3 node; its physical effective range and the combined loop/startup response remain unqualified. Real MCU/IHU/CAN mode currents, IHU controlled ramp, shared fault current, source impedance, hot inductance and board thermal performance require closure. The 2 A target is steady sizing, not accepted abrupt load capability.

Operating VIN minimum is 4.3 V; internal rising UVLO is 4.25 V maximum and falling threshold is 3.8 V typical. The 5–35 V development envelope and 4.5 V sensitivity do not approve a minimum battery cutoff or weak-solar startup. No independent UV supervisor or anti-chatter design exists; repeated collapse/restart remains possible.

**A failed-short high-side switch can expose MCU/CAN and the 25 V bank to approximately 35 V. Autonomous 3V3 output overvoltage containment is absent.** Upstream solar OV isolation does not contain this regulator failure. This remains a blocking engineering issue for full essential-power acceptance, prominently stated on the actual buck sheet.

## Electrical verification

Run `python3 hardware/eps/verification/rev_b/buck_integration/verify_buck_integration.py`. [Verified result](verified.json) asserts the complete **43-part, 40-net** graph equals the union of the preceding controller checkpoint and six explicitly mapped buck nets. All 36 previous controller net endpoint sets survive; only +3V3/GND gain the expected buck nodes. All 43 exact values, library identities, footprints, datasheets and exported metadata sets match their reviewed sources. Existing controller symbol UUIDs are preserved.

[Reference crosswalk](reference_crosswalk.csv) has 72 total entries: the existing 48 plus 24 buck entries (16 physical, five power symbols, three flags). [Buck endpoint crosswalk](buck_endpoint_crosswalk.csv) records both mapped buck endpoints and complete root endpoints, including shared rails. [Blueprint/package/pin readback](rebuild_readback.json), [metadata](fields_readback.json), [full-root XML](eps_rev_b.xml), [BOM](bom.csv).

Fresh full-root [CLI ERC](erc.json): **16 errors, 3 warnings**. Errors are the same 16 unfinished MCU pins; warnings are isolated local REC5_RESET/REC5_FAULT/SRC_FAULT labels awaiting protection integration. No new NC flags suppress them. All 18 historical source/project/table hashes and all 20 previous evidence-file hashes remain unchanged. The 51 buck wire segments are orthogonal and on the 1.27 mm grid, with zero four-way intersections and no pin/power anchors on branches. Eight persisted classes assign all 24 functional nets; numerical geometry remains unqualified routing defaults.

The reused LMR pin/pad map is 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 CB; six unique SMD pads and no exposed pad/drill. Manufacturer DDC lands retain 1.1×0.6 mm at x=±1.35 and y=−0.95/0/+0.95. Stock XAL6060 pads retain 1.43×5.5 mm at x=±2.02; L400.1 is SW and .2 is +3V3. No package numbering or construction changed. Custom default metadata/presentation limitations remain recorded.

## Actual rendered inspection

All four full-page PNGs were opened and inspected: [root](eps_rev_b.png), [controller](controller.png), [CAN](can_interfaces.png), [buck](essential_3v3.png). The buck [input/switching](input_switching_detail.png), [output bank](output_detail.png) and [feedback](feedback_detail.png) details were also opened. Circuit topology, visible wire stubs, local support, feedback and capacitor bank remain readable without observed body/wire/text collisions. Root sheet boxes were resized into three columns; their existing file-name labels retain API-managed positions below their boxes. [Full four-page PDF](eps_rev_b.pdf).

S03 native four-way severity still defaults ignored without an exposed persistence setter. S08 original review-marker coverage for reused custom symbols remains unresolved. S11 required visible field styling remains unsupported despite complete saved values. Root pagination prints Id4/4 rather than1/4; no root-instance-page setter is exposed. Logical connectors and two DNP terminations remain physically unselected. The blank generated PCB/prl remain excluded; no board stage has begun.
