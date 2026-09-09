# U8 bias and output routing — 2026-09-09

U8 RFOUT (pin 3), L15 pad 2 and C84 pad 1 are now connected with 0.358 mm F.Cu routing. The obsolete +5 V track ending on C84 pad 1 was removed. L15, C71 and C76 were moved beside U8, with a 0.3 mm local +5 V connection and a 0.3 mm In2.Cu feeder from the existing switch supply via. New vias are 0.6/0.3 mm. The signal route has a top-pour-only clearance rule area; L2 remains the RF ground reference.

Seventeen old copper items were removed and 27 added. All retained copper geometry/net assignments, all footprint pad nets, and all other footprint placements were verified unchanged. The board has 141 footprints and 701 copper items. Local DRC reports no violations involving the new copper or moved bias parts. Full DRC: 569 errors, 249 warnings, 127 unconnected items. All 1,365 sampled points under the RF centerline, trace edges and wider return area hit filled L2 GND. No missing connection is reported for U8 RFOUT, L15, C71, C76 or C84; U8 input TX_437 remains unconnected.

## Existing L15 identity and limits

The original release BOM maps L5 (now L15) to Murata LQW2BASR22J00L, LCSC C337958. Retain the existing 220 nH value and 0805 footprint for this layout pass. The [Murata datasheet](https://www.farnell.com/datasheets/1888721.pdf) specifies ±5%, 400 mA rated current, 0.7 ohm maximum DCR and 820 MHz minimum self-resonance. At 106 mA, DCR implies up to 74.2 mV drop and 7.9 mW dissipation. These are DC checks, not proof of RF impedance or stability at 437 MHz.

C71 remains 100 nF and C76 remains 10 uF. The implemented network is not the complete ADI evaluation-board bias/bypass network. RF stability, gain, output power and supply decoupling must be qualified on the bench. The original component values were not silently replaced with broadband evaluation-board values.

The new approximately 30 mm inner feeder uses 0.3 mm width and the documented 15.2 um copper thickness: approximately 0.11 ohm at room temperature, or 14 mV at an assumed 120 mA branch design current. This estimate excludes the existing upstream feeder, connector losses, vias and temperature rise. Recalculate the complete rail budget and qualify the board thermally.

## Remaining work

- Review U8 ground-tab copper and thermal stitching against the ADI layout guidance.
- Clean up and route the pre-amplifier TX filter into U8 pin 1; its TX_437 connection remains open.
- Audit U10 identity/pin mapping and continue RX filter placement/routing.
- Resolve remaining board-wide errors and unconnected items; this board is not fabrication-ready.

## Application and recovery

The isolated native KiCad preview was rendered, inspected and checked before application. The PCB editor exited unexpectedly during the live native application. The saved main board was verified byte-identical to its pre-application backup. With the editor closed, the validated preview was loaded and saved to the main board through KiCad's native API, then reopened. Saved-board checks and a live Konnect pad query passed. The reopened standalone PCB editor uses its own IPC socket (api-78670.sock for this session), rather than the project manager's default socket. No source files were edited as text.

## Ground stitching update

Four 0.6 mm diameter / 0.3 mm drill through vias were added at (150.65,139.35), (151.65,139.35), (150.65,140.35), (151.65,140.35) mm, with two 0.5 mm-wide F.Cu connections from the tab copper. The vias are outside the solder land; no via-in-pad fabrication process is assumed. One millimeter via spacing satisfies the project's hole-spacing rule. All new items are GND; every via contacts filled L2 and bottom GND. The saved render was inspected. Local DRC has no violations involving the six added items, and all 701 pre-existing copper items were verified unchanged. Current total: 707 copper items, 569 errors, 249 warnings, 127 unconnected items. See `u8_ground_validation.json`.

This implements nearby ground-layer stitching consistent with ADI's page 12 guidance. It does not establish the datasheet evaluation board's thermal resistance for this board, and it does not replace verification of solder coverage, board-specific heat flow and temperature under operating load. Thermal qualification remains open.

Input inspection confirms C101 is the final series coupling capacitor into TX_437; C100 is a shunt capacitor. C98 (1.6 pF series coupling between the two input-filter resonators) remains off-board. Existing TX_437 copper connects C101/TP14 but leaves U8 pin 1 open. The next routing pass must review legacy copper, place C98, complete the resonator connections and then connect C101 to U8.
