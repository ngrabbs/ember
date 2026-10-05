# EMBER documentation review

**Integration update — October 5, 2026:** this review records the original
LTE-branch publication scope. Main now also includes the separate EPS Rev B,
payload and SDRB/UHF checkpoints. The LTE/main reconciliation retains those
changes and updates the operator guides for published native EPS cadence and
`ember-uhf`. Original exclusions and test counts below remain historical.
See [integration verification](lte-main-reconciliation.md) for combined checks.


[Documentation home](../README.md) · [Operator guides](../user/README.md)

Initial review October 4, 2026; publication selection October 5, 2026. This audit establishes a navigable documentation
inventory, corrects verified drift in architecture/implementation summaries,
and provides user guides for the implemented IHU and Yamcs interfaces. It
preserves mission proposals and dated bench evidence instead of presenting them
as current implementation or flight acceptance.

## Scope and review depth

- [Repository inventory](inventory.md): every first-party Markdown/text document
  in this checkout, with classification, disposition and linked findings.
- Workspace copies were separately inventoried locally, including newer hardware
  and EPS Rev B work. Machine-specific inventories remain local and are not part
  of this PR.
- [Detailed findings](findings.json): evidence, correction, status and remaining
  work for each specific issue.
- [Verification record](verification.md): checks performed and their limits.

This publication is based on `feature/lte-m-bench` at `4b5ccfa`. It adds only
documentation and a documentation-audit helper. That base supplies the CAN/LTE
code referenced by these guides and has not yet reached `main`; the PR therefore
targets the published LTE/CAN branch. Existing telemetry walkthrough/navigation
from PR #8 is preserved. After the base reaches `main`, these changes can follow.

The broader local audit also saw uncommitted SDRB/UHF/cadence, newer payload and
hardware work. Those changes, their copied runbook snapshot, local workspace
inventories, and loose archived files are excluded here. Operator instructions
are narrowed to the source/configuration in this PR's base. No active worktree
was overwritten, and no firmware, radio configuration or CAD change is included.

Every repository document received content/status triage and local file-link
and code-fence checks. Specific implementation claims listed below were checked
against local source/configuration and linked test evidence. Large hardware
instructions, numerical budgets, CAD, rendered PDF/Word artifacts, external
vendor links, remote checkouts and live services were **not requalified**. Their
remaining review is explicit; “keep” means preserve useful documentation, not
approve its engineering content.

## Corrections and remaining work

| Finding | Result | State |
|---|---|---|
| F01 | Replace SPI-first/current-CAN-later summaries with separate legacy, bench and production transport scope | Corrected |
| F02 | Update FreeRTOS IHU/Yamcs status and identify the separate CAN application | Corrected |
| F03 | Distinguish proposed mission commands from the four implemented Yamcs bench commands | Corrected; mission draft retained |
| F04 | Index implemented wire contracts and native/wrapper/LTE provenance | Corrected |
| F05 | Document selected FreeRTOS runtime and production CAN integration boundary | Corrected |
| F06 | Reconcile CAN README introduction with published native EPS/LTE milestones and date old images | Corrected; unpublished cadence deferred |
| F07 | Link Walter bench implementation and later LTE delivery evidence | Corrected; initial vendor review retained |
| F08 | Date old host synchronization and build reconciliation claims | Archived in place |
| F09 | Close eight unfinished fenced examples in operations drafts | Corrected |
| F10 | Repair the missing startup reference | Corrected; UHF snapshot repairs remain local |
| F11 | Separate superseded cellular payload concept from the tracked telemetry experiment | Corrected |
| F12 | Identify EPS regulation/revision discrepancy and remove unsupported blanket validation claim | Scope clarified; engineering reconciliation open |
| F13 | Update generic repository/transport status with recorded bench milestones | Corrected |
| F14 | Resolve active mission versus engineering-model/experimental payload scope | Open; retain records |
| F15 | Reconcile detailed design instructions/budgets against active CAD and current parts | Open; engineering review required |
| F16 | Identify placeholders and the older VHF filter context | Retained as planning/reference; artifact review before archival |
| F17 | Write UART, CAN USB console and Yamcs command/response guides | Completed; source/evidence verification recorded |

## What owns the answer

| Question | Authority |
|---|---|
| What commands does this IHU image accept? | Its source command table/dispatcher; user guide provides the walkthrough |
| What Yamcs bench commands/fields exist? | `ground/ember/dictionary.json`; generated MDB and matching endpoint dispatcher |
| What can this Yamcs instance command? | Its configured telecommand link and selected endpoint, not just a visible MDB command |
| What should flight modes/commands eventually do? | Operations drafts pending agreement/implementation |
| Which stack pin names/numbers are allocated? | `system/interfaces/cskb_pinmap.md`; allocation is separate from routed-board verification |
| Which hardware revision is actually being built? | Active design worktree, revision-specific exports and validation record; reconcile branches before copying claims |
| What passed a hardware test? | The dated result, image/source identity and conditions in its evidence record |
| What remains to implement? | Owning subsystem checklist; root TODO links to it |

## Archive and consolidation decisions

Archiving here means marking a document historical at its existing path and
linking the maintained reference. No unique technical record or measurement
was deleted, and no active worktree was archived.

| Material | Decision | Reason |
|---|---|---|
| Loose workspace `docs/operations/` copies | Archived in place with links to repository drafts | Three divergent duplicates should not compete with maintained navigation; original bodies preserved |
| October 1 `development_baseline.md` | Archived in place | A dated reconciliation record cannot establish current branch synchronization |
| Local supervision service snapshot, excluded from this PR | Retain as historical test snapshot and point to its maintained local runbook | Initially identical duplicate with broken copied links; preserve tested profile |
| Before-cleanup workspace snapshots | Retain outside current documentation navigation | Explicit before-cleanup snapshot; do not reintroduce obsolete placement/routing narratives |
| Existing comms legacy releases, history, BOM and verification records | Keep as evidence/history | Configuration-specific provenance remains useful; not current fabrication approval |
| Superseded S-band alternatives and old inhibit discussion | Keep historical | Already identify supersession; preserve rationale and failed hypotheses |
| Active hardware/EPS Rev B and telemetry worktrees | Keep independent; reconciliation backlog | Contain newer/unique and uncommitted work; whole-tree replacement would lose context |
| Older VHF filter folder and thin planning READMEs | Retain pending artifact review | A short/old document alone does not prove its underlying data can be discarded |

The historical and verification directories already perform useful archival
roles. Prefer a status notice and authority link over another mass file move.
The original audit changed local prose only. This publication commits the
selected documentation and audit helper; hardware, CAD and services are unchanged.

## Engineering reconciliation backlog

1. **Merge documentation corrections by topic across branches.** The hardware
   and telemetry branches have unique material. Carry these prose changes via
   reviewed Git changes, preserving their existing edits. The local workspace audit records the differences;
   it does not declare every branch current.
2. **Reconcile EPS Rev A, older module target and Rev B plan.** Establish which
   design and assembled unit each guide describes. Check regulator identity,
   protection/thermistor policy, sense values, rail results and temperature limits
   against the owning branch and exported evidence.
3. **Recheck hardware and budgets by configuration.** Reconcile source exports,
   mechanical allocation, RF frequency/modulation context, stackup, power/orbit
   assumptions and acceptance criteria. CAD verification must use the project’s
   Konnect/export workflow; this prose review did not modify protected CAD files.
4. **Decide experimental project scope.** Resolve whether S-band and Jetson carrier
   remain active workstreams within the current mission. Then update top-level
   scope and navigation or archive with explicit successor links.
5. **Complete operator validation on the intended deployment.** Confirm installed
   IHU image/build options, terminal ownership, instance/link configuration and
   fresh UI screenshots. Existing October 1–3 evidence supports the guides;
   a source review cannot establish the live state on October 4.
6. **Finish documentation artifacts and operational gaps.** Add the missing startup
   diagram after behavior agreement; replace test placeholders with executable
   procedures; define archive retention/backups and verify restoration. RF
   commanding, full flight mode/authorization and production RTOS/CAN A/B
   integration remain implementation work, not prose gaps.

## Keep the inventory current

From the repository root:

```sh
python3 tools/documentation_audit.py --date 2026-10-05
python3 tools/documentation_audit.py --check
```

Substitute the review date on a later run. An optional `--workspace` argument
can produce a private local inventory of existing worktrees; do not commit its
machine-specific output. The first
command refreshes generated inventories; the second only checks local file links
and unmatched triple-backtick fences. Neither validates external URLs, heading
anchors, Markdown rendering, engineering values, deployed configuration or
hardware. Update `findings.json` when a reviewed correction or remaining decision
changes; generated dispositions otherwise reflect content triage.
