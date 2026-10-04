# Ground stitching and RF geometry review — October 3, 2026

## Implemented

Added 100 through-hole GND stitching vias, 0.6 mm copper / 0.3 mm drill:
38 around the RF perimeter, 23 within the RF region, and 39 across the rest
of the board. Nominal targets were 3 mm around the RF boundary, 4 mm within
it, and 8 mm elsewhere; candidates were displaced or omitted for clearance
and existing ground ties. This is a distributed ground fence, not a sealed
RF shield or a guaranteed isolation specification.

Every added via was read back as GND and checked for filled copper contact on
F.Cu, In1.Cu and B.Cu. Konnect initially allowed some auto-net vias to select
+5V; those were replaced and verified. Short 0.05 mm GND anchor tracks keep
67 replacements on their intended net. Final DRC has no dangling vias.

Preserved the new top ground pour, lowered its priority below local power pours,
and set its clearance to 1.1 mm to retain the existing microstrip design intent.
The former priority had disconnected the top +3V3 and +5V zones; continuity is
restored. SMD pads connect directly; PTH pads normally retain thermals (0.3 mm
gap, 0.25 mm spokes). J9 ground pad 2 and H2 ground pads 29/31 have explicit
solid connections where the pour could not form adequate thermal spokes. Those
two header pins may need additional soldering heat. The stitching pass did not
change footprint positions or pad geometry. The subsequent clock cleanup moved
C2 0.10 mm east; all fixed headers and mounting holes remain unchanged.

## RF impedance findings

**Geometry checked; absolute impedance and matching are not signed off.**
The main 435 MHz RF/filter/switch/antenna routes in the sampled RF set use
0.358 mm top-layer traces. This matches the project's nominal 50-ohm target.
The new ground pour has 1.1 mm clearance rather than an uncontrolled close
coplanar gap. Local pads, launches and matching components still create
geometry transitions that a trace-width rule cannot qualify.

The saved outer copper is 0.035 mm, L1-to-In1 dielectric 0.2104 mm with Er 4.4,
and inner copper 0.0152 mm. These values agree with JLCPCB's published
JLC04161H-7628 structure. The saved total thickness is 1.61668 mm including
mask; JLCPCB's current calculator labels this option nominally 1.59 mm ±10%.
The saved core Er is 4.43, whereas the JLCPCB public page lists 4.6; it does
not control the top-to-first-ground geometry but should be reconciled in the
final fabrication stackup. Do not substitute a different stackup at checkout.

The live JLCPCB calculator successfully returned **14.1200 mil = 0.358648 mm**
on October 3 for 4 layers, 1.6 mm, 1 oz outer / 0.5 oz inner, 50-ohm
single-ended non-coplanar, L1 referenced to L2, JLC04161H-7628. The existing
0.358 mm width differs by 0.000648 mm (0.18% of width); it is retained.
This closes the previously unavailable vendor width calculation. It does not
qualify pad launches, nearby copper effects or component matching. Agree the
actual fabrication impedance tolerance and record the exact stackup in the order.
The calculator's displayed 0.5% calculation tolerance is not a fabrication guarantee.

RF return-path cleanup completed:

- Rerouted the C93–C81 connection on TRIPLER_OUT and made TP3 a short branch
  from it. TP3 and the +5V via remain at their original positions. This removes
  the power-via antipad from the sampled RF corridor without relocating the
  crowded decoupling network.
- Replaced CLK0_OUT's 3.714 mm bottom-layer section with a top-layer route,
  removed its two unused transition vias, and simplified the U7 approach.
  Moved C2 0.10 mm east to provide trace clearance; both C2 pads remain connected.
  CLK0_OUT is now entirely F.Cu, 0.358 mm wide, above In1 ground.

Exceptions requiring separate treatment:

- CLK0_OUT is a CMOS clock path, not a 50-ohm antenna port. Its centerline
  has continuous In1 ground coverage. A separate 1,887-point corridor screen
  found 33 outer-edge misses near R3 and the existing I2C_SDA via; none are
  under the new top-layer segment. This remains a local launch/return-path
  discontinuity to consider in waveform validation, not a uniform-line signoff.
- The Si5351 CLK1 fanout has 0.20/0.34 mm sections; the TX mute output has
  approximately 0.526 mm total of 0.20 mm local pad-escape segments. These
  electrically short source/load connections are not uniform 50-ohm lines.
  Do not blindly add 50-ohm termination to CMOS clock/gate outputs.
- RX_IF includes 10.353 mm on the bottom layer, after C99 and the mixer
  termination R34. The baseband circuit does not require this section to be a
  435 MHz, 50-ohm transmission line. See the follow-up review below.
- Lumped filter matching, amplifier stability and antenna match still need
  circuit/model review and prototype measurements. Ground stitching does not
  tune these networks or establish their return loss.

## Ground-return screen and checks

The refreshed In1 ground screen sampled 20,587 points across a ±0.6312 mm RF
corridor. Only the 189 samples at the existing J9 signal PTH launch remain
outside the filled plane. All 38 prior TRIPLER_OUT corridor misses are cleared.
The J9 transition still requires launch review; this sampled geometric check
is not field-solver extraction.

Final saved DRC: **0 errors, 0 unconnected items, 1 warning** (fixed H1/H2
silkscreen overlap), with the five documented courtyard exclusions retained.
Native schematic/PCB parity: 209 nets, 556 pad-map entries, zero mismatches.
This geometric screen is not EM simulation, impedance certification, or
fabrication approval. Saved but not committed; review ZIP unchanged.

[Initial stitching data](evidence/ground_stitching_rf_review_2026-10-03.json).
[Latest RF cleanup validation](evidence/rf_return_cleanup_2026-10-03.json).

## Primary references

- [JLCPCB stackup and dielectric parameters](https://jlcpcb.com/impedance).
- [JLCPCB impedance calculator](https://jlcpcb.com/pcb-impedance-calculator).
- [TI LMH121x RF layout guide](https://www.ti.com/lit/an/snla288/snla288.pdf):
  continuous reference planes, controlled routing geometry and ground stitching.

## Connector and manufacturing follow-up

[J9 drawing, live sourcing and proposed fabrication requirements](j9_launch_and_fabrication_requirements.md)
closes the nominal hole-pattern/lead-reach question and classifies the IF path.
The user confirmed the installed MMCX clears perfectly: this is the top board
with no board above and ample room. Connector clearance is closed. The accepted
order contract remains open.
