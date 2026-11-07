# Battery-holder geometry identification

2026-10-24. The operator confirms that the previously identified May 2026 STEP
export is the intended export. This resolves the source-selection question; it
does not by itself establish a measured clearance or manufacturing tolerance.

## Local STEP inspection

Source: [`cubesat_eps_rev_b_v0.4.step`](../../../design/cubesat_eps_rev_b_v0.4.step),
20,318,535 bytes; SHA-256
`8a2c58b82846ccdaa0d035bd6143571d50c54ee90a3e1322008fbfcc44b8554a`.
The primary checkout and this worktree have identical bytes. Its header dates
the export to 2026-05-14 10:49:37 and declares millimetre length units.

`inspect_step.py` imports the exact hashed source through Open CASCADE and
records all 451 solids in `solids.json`. The board-like slab (solid 1) spans
X=0–95.975 mm, Y=0–90.180 mm, Z=−0.5537–0 mm, within numerical tolerance.
The complete model extends from Z=−12.3520 to +10.8890 mm. These are **exported
geometry dimensions**, not accepted PCB thickness, header mating depth or
holder clearance. In particular, do not substitute the slab thickness for the
eventual four-layer stackup.

The four tessellated views in `assembly_views.png` were actually opened and
inspected. They show the populated board, stacked headers, connector bodies and
underside pins/components. **The local STEP does not include the printed
battery holder or four cells.** There is no holder solid against which a
minimum underside distance can be calculated from this file alone. A bounding
box is not a component keepout or a collision check.

## Assembled CAD view

The existing Onshape document was refreshed after its saved-document reconnect
notice and inspected in public, view-only mode. The
[`EPS_with_battery` assembly](https://cad.onshape.com/documents/f54077faa9eaef25e1f615dc/w/05a52062e76f7bd3695dddef/e/a140426f51c0f91fdaa76619)
contains `cubesat_eps_rev_b_v0.4 <1>` and `EPS_Battery_Pack <2>`. The expanded
pack lists two `housin_proto_type_bottom_v0.5` instances, two
`housing_proto_type_top_v0.5` instances and four `Part 1` instances. The saved
`onshape_assembly.png` was visually inspected and shows four cylindrical cells
and their end holders beneath the board. This establishes where the missing
assembly geometry is represented; the live assembly revision and print
tolerances are not frozen by the local board-only STEP hash.

The viewer reports view-only access; the inspected assembly-tab context menu
offers only opening another tab. No assembly STEP was downloaded and no CAD
geometry or mates were changed. Red status icons are visible on the board
instance/assembly; no diagnostic meaning or valid mate registration is inferred
from them. A rendered perspective cannot establish the minimum gap.

## Layout consequence and remaining gate

Keep underside component space unallocated until the holder/board assembly can
be exported or measured with known mating registration. Check every underside
body, solder joint, through-hole tail, debug clip, holder rib/fastener and wire
route against that envelope, including print/assembly tolerances and electrical
insulation. The confirmed 16 mm **top** facing-surface gap remains separate.
Schematic development can continue without assuming bottom-side capacity.

Reproduce the local inventory/render with Python 3.12 and
`cadquery-ocp==8.0.1.1.0`, `matplotlib==3.11.2`:

```sh
python3 inspect_step.py
```

This packet changes no KiCad source, PCB placement, CAD source or electrical
connectivity. It makes no ERC, DRC, physical-fit or flight acceptance claim.
