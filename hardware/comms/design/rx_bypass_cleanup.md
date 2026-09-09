# RX bypass cleanup

Saved 2026-09-09. Four legacy 0.55 mm vias associated with C77/C79 were replaced with 0.6 mm diameter / 0.3 mm drill vias. The C79 ground via was moved out of its solder pad, the C79 supply via moved clear of its pad, and the C77 supply via moved away from the pad edge. The remaining supply via was resized at its original position. C77/C79 ground pads now have explicit dogbones to the new common ground via at (160.35,125.9); that via contacts filled L2 and bottom GND.

The local supply wiring and inner-layer feeder endpoints were rebuilt to match the new via positions. Seventeen reviewed copper items were removed and eighteen added. Footprint positions, metadata and every pad net remain unchanged, as does all retained copper. New via sizes, drills and nets were read back after save. New copper has no DRC findings. All 2,975 previous RX/adjusted-bias RF return-plane samples still pass.

Main-board result: 141 footprints, 738 copper items; 501 errors, 202 warnings, 101 unconnected items (previously 509/204/102). This is local cleanup, not a fabrication release. L16 selection/land pattern, global rail budget and remaining RF/IF routing remain open.
