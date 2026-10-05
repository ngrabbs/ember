# PV panel Rev D — KiCad

Open `pv_panel.kicad_pro` with KiCad 10. The project contains the recovered
schematic, routed PCB, project-local footprint libraries, and solar-module
STEP model. Diode and connector models are embedded in the board and footprints.

The recovered schematic follows the routed PCB's six nets and eleven named
components. The original free pads and mounting holes remain board-only items.
Footprints are linked to the recovered symbols; their placed geometry is retained
in individual project-local library variants.

## Onshape exports

- `exports/pv_panel_rev_D_presentation.step` includes colored components, solar-cell
  detail, copper, pads, soldermask, and silkscreen.
- `exports/pv_panel_rev_D_mechanical.step` provides simpler board/component geometry.

Both files use millimeters and a board-centered XY origin. They reopen as valid
OpenCascade shapes; an actual Onshape import has not been tested.

## Geometry and assumptions

- Board outline: nominally 82.5 × 98 mm, with the original rounded corners.
- Mounting holes: four 3 mm drills at the original positions, spaced 76.2 × 91.6 mm.
- Board thickness: 0.41116 mm from the original layer stack. Confirm against
  physical hardware for precise fitting.
- Solar modules: nominal 70 × 23 × 1.2 mm bodies based on the
  [ANYSOLAR product table](https://anysolar.biz/products/gen3/), with an assumed
  0.15 mm stand-off. Surface detail is illustrative; dimensions represent nominal
  geometry rather than a tolerance envelope.
- Original diode and connector bodies are retained as package representations;
  their geometry has not been certified against the fitted manufacturers' drawings.
- Screws, mating cables, and solder fillets are not modeled.

## Recovery changes

Removed zero-length outline segments, repaired PV2 pad 1's net assignment,
restored the original 10 mil zone clearance, refilled the ground zones, removed
isolated copper and a tiny dangling track stub, and corrected through-hole paste
settings and silkscreen collisions. Corner copper rings were reduced from 6.4 mm
to 5 mm to satisfy the existing 0.5 mm edge-clearance rule; drill diameters,
mounting centers, and the outline are unchanged.

The native schematic import had scale and connectivity defects, so the working
schematic was reconstructed with standard KiCad symbols and checked against the
PCB pin connectivity. The archived sources disagree on diode population: the
older drawing omits D1 and labels CR1–CR5 as RBR1MM60ATR, while the PCB includes
D1=SB140 and labels CR1–CR5 as STPS1L30MF. This project follows the PCB. Confirm
the intended/fitted diode part numbers before fabrication.

## Validation

The saved project passes KiCad DRC, ERC, and schematic parity with zero findings.
All six nets match pin-for-pin across the eleven named components. Both STEP
exports contain valid CAD shapes (58 solids for mechanical, 129 for presentation),
and top/bottom renders were visually inspected. These checks cover the recovered
design and mockup export; hardware qualification remains a separate activity.
