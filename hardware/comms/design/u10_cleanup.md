# U10 ground and C57 clearance cleanup — 2026-09-09

Removed the two redundant standalone ground vias at (169.89358,124.71184) and (169.88114,122.1594), which overlapped the U10 footprint's plated ground holes. The native footprint holes at (169.9546,124.6736) and (169.9546,122.1336) retain their 0.508 mm drills and verified connections to L2 and bottom ground. U10 geometry and all pad nets are unchanged.

Moved C57 to (171.5,127.15), 90 degrees, clearing U10's courtyard. Replaced seven obsolete short connection segments with four segments joining the same retained nets. Adjusted C57, TP15, R20 and R21 labels. Values, metadata, other footprint positions and retained copper signatures were verified unchanged. C57 was read back via live Konnect after reopening. Front copper render inspected; sampled previously accepted RF ground coverage still passes all 5,355 sample positions.

Final board: 136 footprints, 762 copper items. DRC **450 errors / 150 warnings / 77 unconnected** (previously 451 / 166 / 77). No findings reference U10, C57 or newly added copper. Existing TP15/R20 and R20/R21 courtyard overlaps plus TP15 silk clipping remain. Refill also reported shorting findings on unchanged legacy C30/L9 and unnamed copper; those need the legacy RX cleanup rather than being attributed to the C57 reroute.

The 3D viewer warning corresponds to pre-existing invalid-outline DRC findings: the arc near (105.5936,64.9936) and segment near (100.5136,92.2536) produce tiny segments and a self-intersection. Prioritize outline repair next, preserving intended mechanical dimensions and revalidating fill/DRC afterward. Board is not ready for fabrication.
