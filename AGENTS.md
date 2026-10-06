# EMBER agent instructions

Before any KiCad schematic design, edit, or review, read the entire [schematic policy](hardware/conventions/kicad_schematic_policy.md), [net-naming conventions](hardware/conventions/net_naming.md), and the relevant board's design/interface contracts. This applies to every agent, including delegated agents. The policy governs presentation and acceptance gates; older examples and generic skill defaults must not override it. Preserve accepted physical pin maps and existing interface names unless an explicit migration is authorized.

Use Konnect for all KiCad source, project-setting, and library mutations. If unavailable, continue documentation/requirements work and report design execution as blocked. Discover installed capabilities instead of assuming a tool or version is supported. Schematic scope permits needed net-class/ERC settings and project libraries, but PCB work requires its own authorization.

For a delegated schematic task, pass the repository/worktree root, exact policy path, target project/root schematic, relevant board contracts, and mutation boundary. Require the recipient to read the policy before work. Keep one design mutation owner; review agents gather evidence without editing the design.

Report electrical and visual evidence separately. Inspect every rendered sheet at page and detail scales; do not claim completion from ERC, netlists, or overlap scores alone. Preserve existing annotation, hierarchy, metadata, and unrelated files.
