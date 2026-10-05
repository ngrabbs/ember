# Connector models

`ESQ-126-39-G-D.step` is the unchanged CADENAS/PARTsolutions STEP AP214
model embedded in `hardware/eps/kicad/eps.kicad_pcb`, extracted on 2026-10-04.
The file identifies the exact Samtec ESQ-126-39-G-D and records a generation
date of 2026-04-18 and **CC BY-ND 4.0** in its header.

- Creator: CADENAS (PARTsolutions); connector manufacturer: Samtec.
- Product: https://www.samtec.com/products/esq-126-39-g-d
- License: https://creativecommons.org/licenses/by-nd/4.0/
- SHA-256: `74b4283cfed5c8c78ba292e10f46646105e2a2c046924ea6af4397359437c229`
- Model geometry and original header are unmodified. KiCad supplies placement
  transforms externally in the footprint association.

The local ESQ footprint uses `${KIPRJMOD}/lib/3dmodels/ESQ-126-39-G-D.step`,
unit scale, rotation X=-90/Y=0/Z=-90 degrees, and offset Z=2.54 mm. Its origin
is centered on the 2x26 pad array. This places the socket above the PCB and
the tails below it. Body height above the mounting surface is 11.049 mm;
tail length from that surface is 12.192 mm. Tail protrusion below the PCB
is that length minus the board thickness.

Both H1/H2 models were verified in the complete board STEP export, including
all 104 pin centers against their PCB pad positions. See
`../../../verification/evidence/header_3d_alignment_2026-10-04.json`.
