# KiCad schematic design policy

**Scope:** every EMBER KiCad schematic build, edit, and review.
**Imported:** 2026-10-06 from `kicad-design.agent.md`; source SHA-256: `2cf8fd1a86e6cac0e9fdf754d5bef10b6f56cdb455f9f8f9e2238374e3077049`.

This is the canonical repository policy. The imported agent frontmatter was removed because it is not a Codex tool configuration; the preflight now uses runtime tool discovery. S01–S11 and the acceptance gates retain the imported requirements.

Read this entire document before schematic work, together with the board's design contracts and [net naming](net_naming.md). This policy supersedes older drawing, label-scope, and prospective naming guidance and generic skill/template defaults. Preserve accepted physical pin maps, board requirements, and existing interface contracts. Existing rail/pair names are legacy interfaces: do not rename them or merge ground domains without an explicit migration and impact review. New or explicitly migrated fixed rails use voltage-first names; variable inputs need an agreed convention. Historical guides and validation reports describe their recorded revision, not proof of compliance with this policy.

Maintain requirements here; link to them from board guides rather than copying them. The original Downloads file is an import source, not a runtime dependency.

## Mission and scope

Work step by step with the user on schematics, libraries, PCB stackup, design rules, placement, and routing. This file establishes schematic policy. Detailed librarian/component-creation, PCB stackup, PCB rules, PCB placement, and PCB layout/routing workflows remain future work; establish their requirements with the user before beginning those stages.

**This design policy is self-contained and reusable across projects.** Do not depend on a roadmap, example schematic, previous conversation, local reference design, or another agent being present. All presentation requirements are specified below. Discover the current project's paths, libraries, installed tools, and requirements at runtime; never import component choices, reference designators, coordinates, or circuit topology from an unrelated project. Public documentation links are research references, not local prerequisites.

**A schematic is an engineering document for humans, not merely a netlist.** Electrical correctness and visual readability are separate acceptance gates. Never replace readable circuits with scattered symbols and label-only connectivity.

Apply the user's explicit design requirements. These rules take precedence over generic Konnect templates or bundled stylistic guidance. If an operation cannot meet them, report the limitation; do not silently substitute a different representation. Ask only for decisions that materially affect correctness or the current stage. Do not advance into PCB mutation without the user's request to begin that stage.

Schematic-only work may modify schematic files, required project net-class/ERC settings, and explicitly needed project libraries. Leave existing PCB geometry, stackup, placement, routing, firmware, fabrication outputs, assembly exports, and packaging untouched. Review renders and validation reports are permitted.

## KiCad 9/10 and Konnect preflight

1. Identify the requested KiCad major/minor version, project/root schematic, saved file versions, available libraries, and open editor state before design-file mutation. Do not assume the newest installed executable is the intended one.
2. Use the Konnect MCP server for KiCad operations. Discover the current environment's actual server identifier, tools, and schemas; never fabricate tool names, parameters, or support claims. This Markdown policy does not enable tools or install a server. All changes to `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `.kicad_sym`, `.kicad_mod`, `sym-lib-table`, and `fp-lib-table` must go through Konnect; never edit them with text/file-writing tools.
3. When available, start with `get_installation_info`, `load_user_config`, `load_project_config`, and `get_effective_config`. Use `list_toolboxes` and `load_toolset` to load only relevant toolsets. The installed server's returned capabilities take precedence over an online catalog.
4. Konnect's currently published requirements specify **KiCad 10** for its supported workflow and PCB IPC backend. KiCad 9 is a target for these design conventions, NOT a claimed supported Konnect backend. For KiCad 9, establish an explicitly supported, tested path for the exact operation; otherwise stop that operation and explain the blocker. Do not quietly switch to KiCad 10 or a legacy server.
5. When compatibility with both versions is required, preserve a KiCad 9-compatible source and validate opening/export/ERC with each intended version on copies. Do not save over that source with KiCad 10. Never fake backward compatibility by changing a version header.
6. If Konnect is unavailable, continue requirements/policy work but report that KiCad execution is blocked. Do not compensate by generating unverified schematic files, ad-hoc regex rewrites, or a replacement backend. An agent definition does not install or connect the server.
7. Preserve existing UUIDs, project-instance records, annotation, hierarchy, fields, and unrelated settings. Establish a recoverable source backup/checkpoint before substantial mutation; a PDF snapshot is not a source backup. Avoid concurrent GUI/file writes: arrange saving and closing/reloading as needed for Konnect's file-backed schematic edits.

## Schematic rules

### S01 — Ground symbols, always downward

- Never use local, global, or hierarchical net labels to represent `GND` or other ground nets. Use an actual ground symbol with its graphic pointing downward and its connection at the top.
- Wire ground pins to nearby ground symbols or a short local ground bar terminating in a downward symbol. Do not drag ground wires across the page.
- Keep intentionally distinct domains such as `GND`, `GNDA`, isolated return, or chassis ground distinct. Use the appropriate ground symbol and verify the resolved net; never short domains just to make the drawing simpler.
- Ground symbols provide their own net naming and connection scope. No redundant ground labels are needed for page crossings.

### S02 — Voltage-first power symbols, always upward

- Represent supply rails with actual power symbols pointing upward, not ordinary/global/hierarchical labels.
- Use voltage-first names: `3V3`, `5V0`, `1V8`, `12V0`. A distinguished rail uses `<voltage>_<purpose>`, such as `3V3_MCU`, `1V8_VDDA`, or `5V0_USB`.
- Do not use generic `VCC`, `VDD`, or `VSS` as supply-net names. Manufacturer pin names can remain unchanged.
- In KiCad 9/10, a power symbol's **Value determines its net name**. Prefer reusing an appropriate stock upward power symbol and setting its Value to the exact rail name. Renaming only the visible graphic or adding decorative text is not sufficient. Confirm the resulting netlist name.
- Keep short local supply bars above the supported circuits. Show decoupling capacitors wired between the appropriate rail and downward ground symbols near their associated IC/power unit.
- Do not assign the same name to independent regulator outputs or rails separated by filters simply because they have the same nominal voltage. Use distinguishing suffixes where they are different nets.
- Never invent a voltage for an unknown or variable input. Record its range and ask for a naming convention before assigning that rail. Agree negative and variable-rail naming with the user when such rails occur; the upward supply-symbol requirement still applies.
- Power symbols do not prove a rail is driven. Add `PWR_FLAG` only where an actual power source exists but ERC cannot infer it, including externally supplied ground or downstream passive filtering when applicable. Never scatter flags to hide faults.

### S03 — No four-way junctions

- Never create a four-way connected wire junction. Offset one branch so the connection becomes two separated T-junctions, with visible junction dots.
- Keep those T-junctions visibly separated, not coincident or nearly coincident.
- Minimize unconnected wire crossings by repositioning symbols and choosing clearer wire paths. Where a crossing cannot reasonably be avoided, it must be unambiguously unconnected with no junction dot; never place a label anchor there.
- In project ERC settings, set **Four connection points are joined together** to Error where supported, preserving unrelated severities. A clean ERC result does not replace geometric/visual checking.

### S04 — ANSI B pages, split by function when needed

- Use ANSI B, landscape: 17 × 11 inches (431.8 × 279.4 mm), KiCad paper size `B`. Do not substitute A3 or enlarge the page to avoid organizing the circuit.
- Keep a small sensor, a few connectors, and an LDO together on one sheet when they fit comfortably.
- Split designs with several substantial subcircuits into meaningful functional sheets: power, processing, sensors/analog, interfaces, etc. Keep each circuit and its local support components together.
- Comfortably fitting means readable fields at normal print scale, useful whitespace, clear wire channels, and all content inside the drawing frame and outside the title block. Do not reduce text or cram components to force one page.
- Name and number sheets coherently; ensure every child belongs to the root schematic. Never deliver disconnected standalone page files as if they formed one project.
- With the user's global-label policy, unique functional child sheets can use a flat electrical hierarchy. Do not reuse a child sheet with the same global signal names for independent channels: globals would short the channels together. Obtain approval for a hierarchical interface policy before repeated-sheet reuse.

### S05 — Label scope is intentional; wires come first

- For signals actually crossing schematic pages, use **global labels** at their page-crossing endpoints, consistently named on every participating page. Enable readable inter-sheet references when supported.
- For signals confined to one page, use **local labels** when a name is useful. A connector going off-board is not itself a schematic page crossing.
- Do not use global labels for signals that stay on one page. Do not introduce hierarchical labels/sheet-pin interfaces instead of this policy without user approval.
- Use real wires for nearby components and circuit topology: resistor dividers, filters, feedback loops, pull-ups, termination, protection, regulator input/output networks, and decoupling. A local label on a continuous wire can identify the net without breaking the drawing.
- Disconnected local-label connections are allowed only where a long wire would genuinely worsen readability, not as a default way to connect every pin. Keep the reader's signal path apparent.
- Ground and power rules S01/S02 override this signal-label policy, including page crossings.
- Never invoke label-at-every-pin helpers across an entire IC or circuit. In Konnect, `connect_to_net`, `batch_connect_to_net`, and `connect_passthrough` produce label/stub connections; use them only for an individually justified label connection, never for ground/power or as a substitute for drawing a circuit.

### S06 — Human-readable composition

- Plan the sheet layout before adding wires. Arrange inputs/sources toward the left, processing centrally, and outputs/loads toward the right where practical; rails above, grounds below.
- Use functional blocks, aligned related symbols, consistent spacing, and concise headings. Keep reference/value fields legible, associated with the correct part, and clear of wires, pins, symbols, and other text.
- Place local support parts beside the circuit they support: decoupling, reset/boot networks, crystals and load capacitors, feedback, protection, pull-ups, and termination. Show their topology with wires rather than collecting detached labeled parts in an unrelated corner.
- Use a 50 mil / 1.27 mm electrical grid for symbols, pins, and wire endpoints. Finer grids are for text/graphics only. Verify exact pin coordinates after rotation or mirroring; never estimate an IC's pin locations from its body center.
- Prefer horizontal/vertical wires with simple bends. Never route wires through symbol bodies or fields. Keep distinct parallel wires visually separated and remove dangling/duplicate segments.
- Expose a visible electrical wire segment between connected symbol-pin endpoints, including power and ground symbols. Never join components pin-to-pin with zero wire length, or put a power/ground symbol directly on another component pin.
- Never place any component pin or power/ground symbol anchor directly on a branching junction. Pull the symbol away and connect it by a visible wire stub. Use at least one 50 mil / 1.27 mm grid interval of exposed wire as a minimum starting point, increasing it when needed for legibility. Measure from the actual pin endpoint, not from the symbol body; a drawn pin is not exposed wire. Preserve connectivity and separate T-junctions when doing this.
- Keep wires in the normal green schematic wire style for this workflow; do not use red symbol-pin graphics or decorative green lines as a substitute for electrical wires. Net-class assignments must not obscure the distinction between wires and pins.
- Draw I2C pull-ups near the controller/master (the originating interface block), wired into the local SDA/SCL paths with the correct supply. I2C is bidirectional: this is a schematic presentation preference, not a claim that it has a unique electrical source. For multiple masters or external pull-ups, identify the intended pull-up location and check total parallel pull-up loading rather than duplicating them automatically.
- Draw required AC-coupling series capacitors near the transmitter/source and in the actual signal path, with paired capacitors aligned for differential signals. Follow a protocol/device's documented receiver-side placement exception when required and explain it. Do not add AC coupling to interfaces that do not require it, such as USB 2.0 or CAN merely for presentation.
- Draw ESD protection beside the connector it protects, with the connector-to-protection-to-internal-circuit path apparent and short local ground connections. Do not collect ESD devices beside the MCU or behind off-page labels away from their connector. Schematic proximity documents intent but does not prove physical PCB proximity.
- Fetch and inspect the manufacturer's relevant typical-application/reference schematic before claiming to follow it. Preserve recognizable functional organization while adapting to this policy; cite the datasheet revision/section and explain material circuit deviations.
- Library-first does not justify an unreadable drawing, but do not arbitrarily renumber/rearrange library pins to improve it. Explain any needed symbol variant and obtain approval for its construction/review requirements; do not assume a librarian agent exists.
- Render and visually inspect **every sheet**, at page view and circuit-detail view, after substantial layout changes and before completion. Viewing only coordinates, XML, a netlist, or an overlap score is not visual inspection.

### S07 — Search KiCadLib before making parts

- Search the user's configured `KiCadLib` library first. Resolve its real library-table nickname/path; do not assume it is installed or mistake its absence for a search result.
- Search appropriate installed official KiCad symbol and footprint libraries before creating a new part. Verify candidates against the exact manufacturer's device/package variant, pin numbers/functions/electrical types, and footprint pad mapping.
- Reuse suitable existing components. Do not create a new resistor, capacitor, connector, power symbol, IC, or footprint merely because that is easier to automate.
- Library reuse includes custom property values AND their display properties, not just the symbol outline, Value, and Footprint. Inspect the selected library definition's complete fields before placement; compare the saved placed instance against it afterwards. Do not assume a placement tool copied custom fields, visibility, font, justification, or field anchors merely because it copied the correct `lib_id`.
- Preserve the exact library field names, including `MFG P/N` and `PackageSize`, and normalize aliases only deliberately. Do not silently replace them with duplicate `MPN`/`Package` fields or blank generic fields. Apply the required visibility and orientation-aware presentation in S11 even if library fields are hidden by default.
- Do not modify global or vendor libraries in place. Needed custom parts belong in a registered project library using portable paths, unless the user explicitly chooses another library workflow.

### S08 — New parts are bright-green review candidates

- Any newly authored custom symbol is **unreviewed**, not implicitly approved. This includes authored symbol variants; simply changing a stock power symbol's Value is not authoring a new part.
- Set its supported symbol-body graphic outlines to bright green (`#00FF00`) and use a visible bright-green review field/callout identifying **CUSTOM — REVIEW REQUIRED**. Avoid opaque fills that conceal pins or text. Keep all units recognizable as review candidates.
- KiCad documentation describes custom colors on symbol graphics and fields. Verify the target KiCad version AND installed Konnect authoring schema can preserve/render these properties. Do not assume a single per-symbol color property colors all pins/text.
- If the available tool path cannot set the green body graphics, report that requirement as blocked and obtain approval for an alternative such as a green review enclosure/callout. Do not silently claim the symbol itself is green or change the global theme, DNP flag, or simulation status as a workaround.
- Record the library identifier, instances, datasheet source, and review status. Keep an unreviewed marker until the user approves it. Never alter electrical connectivity just to mark a part for review.
- Detailed symbol/footprint construction rules must be agreed with the user before authoring a missing part. A future librarian/component-creation agent may supply them, but its existence is not a prerequisite for using this file. Until construction rules and approval are established, continue independent work using verified library components where possible.

### S09 — Schematic intent drives net classes

- Define and assign actual project net classes for the interfaces present: `I2C`, `UART`, `USB`, `PCIE`, `CAN_BUS`, `SPI`, `POWER`, `RF`, and any justified analog/clock/special classes. Avoid unused placeholder classes.
- Refine broad classes when physical requirements differ, e.g. `USB2`, `USB3`, `CAN_PHY`, or `POWER_HIGH_CURRENT`. MCU-side CAN TX/RX must not inherit the differential physical-bus rules; similar distinctions apply to other transceivers.
- Persist definitions and assignments in KiCad project settings, with supported schematic directives or label `Net Class` fields when appropriate. A comment saying “USB” or a net name prefix is not a net-class assignment.
- Konnect currently documents `create_netclass`, `get_netclasses`, and `assign_net_to_class` in `pcb_routing`. These operate on the project settings; loading that toolset does NOT authorize PCB routing or geometry changes. Inspect installed schemas before use and read back saved assignments.
- Use exact assignments or carefully bounded patterns based on **resolved full net names**, including local sheet-path prefixes. Verify matched membership, intended downstream segments across series parts, both members of every pair, and absence of unintended matches.
- Where multiple classes apply, document priority and check effective properties. Preserve existing approved definitions and assignments.
- Record interface speed/generation, topology, polarity, impedance target and source, rail current/voltage, isolation needs, and length/skew requirements when known. Mark unknowns as TBD for stackup/rules work.
- Do not guess fabrication clearances, impedance geometry, current-carrying widths, or length budgets merely from protocol names. Net-class widths/gaps are routing defaults, not automatically enforced min/max DRC bounds. During an explicitly authorized PCB rules stage, convert approved requirements into enforceable constraints; do not assume a separate rules agent is installed.

### S10 — Differential-pair naming

- KiCad recognizes paired nets sharing a base name and ending in `+`/`-` or `P`/`N`. Use **`_P` / `_N` consistently for new pairs**: `USB2_D_P` / `USB2_D_N`, `PCIE_TX0_P` / `PCIE_TX0_N`, or `CLK_P` / `CLK_N`.
- Keep lane, direction, endpoint, and segment identifiers **before** the final polarity suffix. After a series element, use another matched base such as `USB2_D_CONN_P` / `USB2_D_CONN_N`; do not append `_CONN` after `_P`/`_N`.
- Both members must have the same resolved base/sheet path and complementary polarity. Never mix suffix styles or assume `DP`/`DM` or `CAN_H`/`CAN_L` will be automatically recognized.
- Preserve manufacturer pin naming and verify polarity mapping against the datasheet, including CAN H/L mapping when using P/N net aliases. Do not infer electrical equivalence from suffixes alone.
- Keep paired signals adjacent and visually parallel; draw local termination, coupling, and protection components with actual wires. A schematic bus graphic is not required to make a differential pair.
- Verify resulting pair names in KiCad's exported connectivity and, when the PCB stage is authorized, native pair recognition. Naming alone does not establish impedance, skew, or correct physical routing.
- Do not silently rename existing approved nets and break external design references; propose the pair rename and verify its impact first.

### S11 — Component information and orientation-aware field presentation

Required visible fields, in addition to Reference and Value:

| Component | Visible information |
| --- | --- |
| Resistor | `Tolerance`, `Power`, `PackageSize` |
| Capacitor | `Tolerance`, `PackageSize`, `Voltage`, `Dielectric` |
| Inductor | Rated current; chip-style inductors also show `PackageSize` such as 0402/0603 |
| IC or connector | `MFG P/N` (the exact selected manufacturer's part number) |

- Use the library's existing current-rating field where present; distinguish rated/RMS current from saturation current rather than conflating them. Retain both if available and relevant. Preserve all other sourcing metadata even when hidden.
- Read required values from the selected library part and verify suitability against manufacturer data. A generic passive symbol needs verified part metadata; its Value alone does not specify tolerance, package, rating, or dielectric. A generic connector symbol/footprint is not a manufacturer part number. Select an actual connector and verify its mechanical/pad mapping. Never fabricate ratings or part numbers; flag missing information as a completion blocker and resolve it before claiming the requirement passes.
- Display field VALUES without their field-name prefixes, using a compact, consistent parameter block beside the part. Keep Reference, Value, and MFG P/N legible; do not display Value twice when it already equals MFG P/N. Preserve the named MFG P/N property for BOM/metadata use regardless.
- Choose the presentation layout by the symbol's **rendered orientation**, not by reference designator, circuit role, or a library-specific rotation number. The following layouts are complete requirements; no example file is needed.
- **Vertical capacitor** (pins above/below): Reference at upper right, Value below/left, compact right-hand parameter stack in visual top-to-bottom order **Dielectric → Tolerance → Voltage → PackageSize**.
- **Horizontal capacitor** (pins left/right): Reference centered above and Value centered below; **Dielectric above the left pin, Tolerance below the left pin, Voltage above the right pin, PackageSize below the right pin**. All auxiliary text reads horizontally. Keep these four fields clear of the plates and exposed green wire extensions beyond the pin endpoints; use this orientation-specific arrangement rather than rotating the vertical capacitor's right-hand stack wholesale.
- **Vertical rectangular resistor** (pins above/below): Reference at upper right, Value inside the resistor body along its long axis, compact right-hand parameter stack in visual top-to-bottom order **PackageSize → Power → Tolerance**.
- **Horizontal rectangular resistor** (pins left/right): Reference centered above, Value inside the body along its long axis, and a compact horizontal parameter row below in visual left-to-right order **PackageSize → Power → Tolerance**, with enough separation to read each field distinctly. Keep the parameter text horizontally readable.
- For nonrectangular resistor symbols, inductors, ICs, and connectors, retain the same separation between identification and auxiliary information: Reference above or upper right, Value near the body, and the required ratings/MFG P/N in an adjacent readable block. Do not force Value into a body that cannot contain it legibly or alter a verified symbol solely to fit text.
- Use **0.5 mm Arial** for extra passive parameters, with Reference/Value normally **1.27 mm**. Treat that compact extra-field style as an explicit user preference, not permission to shrink the rest of the schematic. Verify font availability and actual print-scale legibility; if substitution or clipping changes the result, report it and use an approved fallback. Do not turn normal sourcing fields green merely because they are custom properties; green review marking is for newly authored symbols under S08.
- Position fields relative to each symbol's actual body and pin bounds, with an orientation-specific layout for 0/90/180/270 degrees and mirrored placements. Keep auxiliary text upright/readable while the passive Value may follow the body's long axis. Reapply the visual left/right/top/bottom layout after rotation or mirroring; do not blindly transform every field or reuse absolute coordinates from another placement. Adjust spacing for longer values and MFG P/N strings.
- Preserve deliberate field placements, `show_name`, font/size, justification, and visibility. Disable autoplacement for manually arranged fields where supported so later updates do not overwrite the approved layout. Do not run a blanket Reference/Value reset over these styles, and do not assume that resetting those two fields also fixes custom fields.
- Verify the installed Konnect schemas support the needed field operations; some may support values/positions but not custom font size or all text effects. Report unsupported presentation operations rather than silently dropping parameters or claiming that a dictionary of field values also set their visual style.
- After placing, rotating, mirroring, or updating a symbol, read back ALL required fields and render the instance at detail scale. Check values, visibility, ordering, angles, association, and overlaps. For multi-unit ICs, show MFG P/N at least once clearly beside the principal unit and preserve consistent metadata across every unit without crowding each gate.

## Execution loop and acceptance gates

1. **Inspect:** read existing sheets/settings and relevant manufacturer material; identify missing requirements and compatibility blockers.
2. **Plan:** briefly describe the functional blocks, B-sheet allocation, local wire paths, inter-page signals, rails/grounds, and classes. Pause for genuinely consequential decisions, not each routine placement.
3. **Build one coherent block:** search libraries, place on grid, query transformed pin coordinates, then wire. Prefer `connect_pins`, `batch_connect_pins`, and explicit `add_wire`/`batch_add_wire` paths; automatic H/V paths still require crossing/overlap review.
4. **Read back:** confirm actual saved coordinates, complete library/custom fields and required display settings, net names, labels, and project assignments. Check installed capabilities before using `move_connected`; it may be unimplemented. `move_schematic_component` and rotation tools do not maintain connected wires automatically. Re-query and reconnect after any move/rotation as required, preserving exposed wire stubs and orientation-aware field layouts.
5. **Validate electrical structure:** check intended pin-to-net connections and shorts across the full root hierarchy, dangling items, no-connects, annotation, power drive, and footprint mapping. Use KiCad CLI netlist/ERC as authoritative evidence; a Konnect name-summary or per-sheet connectivity report is not proof of complete cross-sheet connectivity.
6. **Validate presentation independently:** inspect actual rendered pages and details. Available tools may include `render_schematic_png`, `get_schematic_view`, `export_schematic_svg`, `check_schematic_overlaps`, and `get_schematic_layout`. A returned image path must actually be opened/inspected. Geometry checks may exclude free text and cannot prove field readability.
7. **Correct and repeat:** fix presentation as well as electrical defects without suppressing checks to manufacture a pass. For presentation-only changes, compare intended connectivity before/after to catch accidental rewiring.
8. **Finish only with evidence:** record ERC counts, unresolved warnings/exclusions, sheets rendered/inspected, applicable-version validation, net-class membership checks, and custom-part review blockers. If rendering, version validation, or connectivity checking could not run, state **not verified**, not “complete/clean.”

### Completion checklist

- [ ] All ground connections use downward ground symbols; no ground net labels.
- [ ] All supplies use upward power symbols with verified voltage-first net names.
- [ ] No connected four-way junctions; crossings are minimized and unambiguous.
- [ ] B sheets fit comfortably, with coherent functional partitioning and hierarchy.
- [ ] Global labels only for inter-page signals; local labels for same-page signal names.
- [ ] Local circuit topology and support components use readable actual wires.
- [ ] Pin/wire endpoints are on the electrical grid and physically connected.
- [ ] Reference/value fields and annotations are legible and nonoverlapping.
- [ ] Required passive ratings/package/dielectric fields and IC/connector MFG P/N are preserved, verified, visible, and arranged correctly for each orientation.
- [ ] Visible green electrical wire separates symbol-pin endpoints; no component/power/ground anchors sit directly on a branching junction.
- [ ] I2C pull-ups and required AC-coupling capacitors are drawn by their source/interface block, and ESD protection is drawn beside its connector; any justified exceptions are documented.
- [ ] KiCadLib and official libraries were searched before custom-part escalation.
- [ ] New custom symbols have verified bright-green review graphics and explicit pending review, or an approved documented alternative.
- [ ] Present interfaces/rails have persisted, verified net-class assignments; unknown numerical constraints are recorded.
- [ ] Every differential segment has matched `_P`/`_N` naming and verified polarity.
- [ ] Full-hierarchy ERC/connectivity evidence and actual visual inspection are available.
- [ ] No unrelated PCB or output mutations occurred.

Report changes, validation evidence, and remaining decisions briefly. Never equate a clean ERC/DRC result with engineering approval or visual quality.

## References

- [Konnect project and requirements](https://github.com/mixelpixx/Konnect)
- [Konnect tool directory](https://github.com/mixelpixx/Konnect/blob/main/tool-directory.md)
- [KiCad 9 schematic manual: power symbols](https://docs.kicad.org/9.0/en/eeschema/eeschema.html#power-symbols)
- [KiCad 9 schematic manual: symbol graphics](https://docs.kicad.org/9.0/en/eeschema/eeschema.html#symbol-graphics)
- [KiCad 9 schematic manual: net classes](https://docs.kicad.org/9.0/en/eeschema/eeschema.html#schematic-netclasses)
- [KiCad 9 PCB manual: differential pairs](https://docs.kicad.org/9.0/en/pcbnew/pcbnew.html#routing-differential-pairs)

Use version-matched documentation for the installed release; these references do not certify runtime support. Re-check Konnect compatibility as releases change.