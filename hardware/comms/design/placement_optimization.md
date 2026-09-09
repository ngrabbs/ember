# TX/RX placement optimization — 2026-09-09

Checkpoint before optimization: `11fb9a1`. The optimized changes are saved in the working tree; no push was performed.

Moved 12 components: U8, L15, C71, C76, TP14, C55, L12, C56, C60, L13, C64, C67. U8 and its bias/bypass network now sit beside the TX output filter. The RX input filter follows a compact, ordered row rather than a long wraparound path. TP14 follows the revised PA-input route. Switch-control wiring uses the back layer, freeing a direct top-layer RX path. Moved the amplifier ground-via structure with U8 and removed obsolete local power stubs. Repositioned affected reference labels.

## Routing comparison

These are summed physical copper lengths for the specified nets, including branches; they are not simulated electrical delay or measured RF loss.

| Routing group | Before | After | Change |
|---|---:|---:|---:|
| TX PA output and bias network | 25.07 mm | 8.63 mm | 65.6% shorter |
| TX filter output to PA input, including TP14 | 4.57 mm | 6.98 mm | 2.41 mm longer |
| Combined TX PA input/output routing | 29.64 mm | 15.61 mm | 47.3% shorter |
| RX switch through input filter to LNA | 38.69 mm | 22.57 mm | 41.7% shorter |

The PA input tradeoff is deliberate: a modest increase there removes a much larger output detour. The unchanged LNA/mixer and clock/baseband placement sets a lower bound on remaining inter-stage distances. This is a targeted improvement of the major RF detours, not a claim of a globally optimal layout or a full RF qualification.

## Validation

- Saved-board DRC: **0 active errors, 120 warnings, 0 unconnected items**.
- Existing pair-specific H3/H4 overlap exception retained; no new exclusions.
- Native schematic netlist: all **181 nets** match the PCB, with no changed pad-net assignments.
- **1,245 ground-plane samples** beneath the changed RF centerlines and trace edges: all covered on In1.Cu.
- Changed RF routing stays on F.Cu at the existing 0.358 mm width, with pour-only setbacks rebuilt at 1.1 mm from trace edges.
- Fixed header/connector placements, board outline, component values and schematics preserved.
- No signal routing introduced on the In1 ground-reference layer.

Remaining work includes the previously listed DRC warnings, schematic annotation cleanup and RF bench qualification, including the L16 prototype constraint. The routing comparison visualization omits pours and most mechanical detail to make the paths visible; use KiCad source files for fabrication.
