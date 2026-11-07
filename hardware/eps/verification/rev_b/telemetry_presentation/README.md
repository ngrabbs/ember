# Rail Telemetry native field presentation

2026-10-24, based on `dbfde84`. This bounded repair changes only
`hardware/eps/rev_b/rail_telemetry.kicad_sch` through the real local Konnect MCP
server. The [ADC integration contract](../../../design/rev_b_adc_frontend_integration.md)
and selected part metadata remain unchanged. No circuit, library, project
settings or PCB changes occurred. The earlier ADC integration packet remains
historical at its recorded source state; this packet supersedes its presentation
limitation for this sheet only.

All19 horizontal resistors now show their actual PackageSize, Power and Tolerance
properties in that left-to-right order below the body. All6 vertical capacitors
have upper-right Reference, lower-left Value and a right-hand Dielectric,
Tolerance, Voltage, PackageSize stack. All81 extra parameter fields use0.5mm
Arial; Reference/Value remain1.27mm. `font.json` identifies the installed Arial
font file and hash. The six placed IC units retain exact visible MPN Values
and named MFG P/N metadata without duplicate visible MPNs. The approved green
CUSTOM review callout and all electrical/development cautions are preserved.

The supported MCP field editor applied93 field presentations. Exact UUID-based
batch deletion removed25 redundant parameter annotations; one stale field-tool
limitation footer was replaced with an accurate native-field note. No ordinary
file-writing tool touched KiCad sources. The discovered tool schema and serving
binary provenance are in the preceding [root repair](../root_presentation/README.md).
Exact calls, readbacks and the explicitly removed annotation nodes are retained.

Electrical/preservation evidence: `python3 hardware/eps/verification/rev_b/telemetry_presentation/verify.py`
checks all229 other native files, every existing presentation item outside the
specified fields/26 annotations, all property values, pins, instances and UUIDs.
Whole-root CLI XML is identical after removing export date and sorting the
unordered multi-unit timestamp tokens; no endpoint or metadata is dropped.
The design remains345 parts/186 nets/933 endpoints/14 sheets. ERC remains6
errors/2 warnings with the same settings, positions and diagnostic descriptions;
transient CLI pin-item IDs and export date are excluded from diagnostic comparison.
The other13 page SVGs are exact after stripping only export time in their title.

Visual evidence is independent: the final page, all four channel details,
supply/footer details and montages containing every passive were actually opened
and inspected. `visual_review.json` binds those images to the native source.
The first trial exposed vertical resistor fields; another exposed justification
inversion and overlap on rotated symbols. Final stored90-degree angles and
centered row anchors render upright, separated Package/Power/Tolerance values.
Capacitor fields retain stored0-degree angles. Do not generalize those stored
angles to other symbol orientations. Requested small parameter typography is
preserved; actual-print user acceptance is separate.

`refresh.py` exports XML/ERC/all-sheet SVG and renders with KiCad10/rsvg/Pillow;
it never writes native files. Use the bundled Python runtime with Pillow.
This is a current-sheet presentation repair, not full-root policy acceptance,
accuracy/brownout acceptance, PCB release or hardware/flight qualification.
RBF/deployment, protection/SOA, unfinished MCU functions, managed-load integration,
mechanical constraints and the authorized four-layer PCB remain open.
