# Root sheet filename repair

2026-10-24, based on `98f5064`. Real Konnect MCP presentation edits repair the
Controller and CAN child-sheet filename associations in the EPS root. The
Controller caption sits inside the bottom of its own block to avoid the nearby
UART heading. The CAN caption sits beneath its block. Exact filenames, sheet
UUIDs, instance paths, page numbers, names and body geometry are preserved.

`verify.py` checks all 229 other tracked native files unchanged, exact MCP
item nodes outside the two permitted field presentations/autoplacement flags,
and identical whole-root CLI XML except export date. The design remains
345 physical parts, 186 nets, 933 endpoints and 14 sheets. Fresh ERC remains
6 errors and 2 warnings; this repair does not resolve any electrical fault.
All 13 child SVGs match exactly after removing only the SVG title export time.

Actual visual evidence is separate: the root page and changed-caption details
were opened and inspected, including a rejected initial Controller position
too close to the UART heading. `visual_review.json` binds those images. The
unchanged child sheets retain their earlier visual-review evidence; no fresh
full-design acceptance is claimed. Source cutoff, protection/SOA, unfinished
MCU pins, S11 fields elsewhere, mechanical fit and PCB work remain open.

`tools.json` and `installation.json` identify the discovered schemas and serving
local Konnect binary. `dryrun.json`, `apply.json` and `refine.json` record real
MCP calls; all native mutations went through that server. Its existing stdio
driver is outside the repository; no server installation/configuration or
source patch was needed. Do not replay this checkpoint after later authorized
native changes: reproduce it at its recorded commit.
