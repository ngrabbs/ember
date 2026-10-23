# Current-part courtyard budget — 2026-10-23

This read-only check combines the 77 physical parts in the recovery integration
checkpoint with the 83 parts in the reviewed protection study. It is not the
complete EPS BOM and does not demonstrate board fit.

Konnect `get_footprint_info(include_graphics=true)` read back all 24 assigned
footprint types through the Rev B project libraries. The saved readbacks include
pad geometry and courtyard graphics. `python3 calculate.py` reproduces the JSON
and CSV results without accessing or changing CAD sources.

Of 160 parts, 155 have assigned footprints. Their courtyard bounding rectangles
sum to **3600.78 mm²**, about **41.7%** of an illustrative 96 × 90 mm rectangle.
Bounding rectangles overestimate irregular courtyards; this sum is neither a
minimum-area bound nor a placement utilization result. No packing, rotation,
placement, routing, thermal clearance or mechanical interference was evaluated.

Largest contributors:

| Group | Count | Summed rectangle area (mm²) |
| --- | ---: | ---: |
| Panasonic F bulk capacitors | 7 | 730.80 |
| TO-252 protection MOSFETs | 8 | 621.60 |
| 1210 ceramic capacitors | 36 | 529.92 |
| XAL1510 rail inductor | 1 | 268.71 |
| SMB diodes | 6 | 197.10 |

The five unassigned parts are logical debug/CAN connector placeholders and DNP
termination resistors. Full stack headers, charger/BMS and support circuitry,
RBF switches/connectors, pack protection additions, CAN branch containment and
managed payload circuits are not included. Board mounting holes, connector
keepouts, thermal copper, switching-loop geometry and routing channels also
consume space. The large bulk capacitors and protection devices justify an
early placement study after schematic review, rather than assuming area alone
proves fit.

The reported 16 mm upper standoff is a mechanical input, not a verified component
height envelope. Actual reference planes, the next board's underside protrusions,
battery-holder geometry and tolerances remain to be checked. A nominal 10.2 mm
capacitor body height does not establish final clearance.

No PCB synchronization, placement, stackup or routing was performed for this check.
