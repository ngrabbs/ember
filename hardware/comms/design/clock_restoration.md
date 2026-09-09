# Clock restoration and via correction

Restored the actual Si5351 Y2 to the former clock footprint location and removed the obsolete U1 identity. Swapped R1/R2 placement to match SCL/SDA, reversed C5/C66 to match supply and ground routing, and restored their ground dogbones. Connected crystal copper to XA/XB. Replaced Y1 Crystal_GND2 with Crystal_GND24, matching Abracon ABM8G pins 2/4 ground (https://abracon.com/Resonators/ABM8G.pdf). Y1 now records the selected 25 MHz part.

Moved C6/C7 outward and rebuilt their short connections; widened undersized clock tracks and ground escapes. Enlarged 95 vias to 0.60 mm with existing 0.30 mm drills.

Y2 standard 0.50 mm pitch / 0.35 mm pad width requires 0.15 mm pad clearance. Its pads carry a 0.15 mm local clearance; board manufacturing floor is 0.15 mm, while all five netclasses retain 0.20 mm clearance. Supported by the 1 oz process capabilities at https://jlcpcb.com/capabilities/pcb-capabilities . No DRC categories or individual errors were excluded.

Verified all unrelated footprint positions and all original pad net assignments (except corrected Y1.4) are unchanged. Clock signal clusters match schematic anchors. Power nets still encounter documented unrelated shorts elsewhere, so the board is not yet electrically clean.

Saved board DRC: 98 errors, 128 warnings, 51 unconnected items. Clock sheet ERC has zero violations.
