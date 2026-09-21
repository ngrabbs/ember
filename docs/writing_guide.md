# Documentation editing guide

[Documentation home](README.md)

Write for a teammate who needs to find an answer and act on it.

1. **Open with the answer.** State what this page defines and whether it is baseline,
   draft, reference, or historical. Do not begin with meeting history.
2. **Give each page one job.** Use `docs/` for explanation, `system/` for shared
   interfaces, and board/software folders for implementation.
3. **Keep one authority.** Link to pin assignments, requirements, and numerical
   limits instead of copying them into several guides.
4. **Separate decisions from proposals.** Preserve TBDs and verification limits.
   A selected component or pin allocation does not mean it has passed testing.
5. **Make the first screen useful.** Prefer a short summary, a small table, and
   links to next steps. Keep reference tables complete; move long rationale and
   old alternatives into linked notes or collapsed history.
6. **Make navigation explicit.** Give each topic folder a short README and each
   page a route back. Use descriptive link labels and relative repository links.
7. **Keep old links working.** When consolidating a page, leave a brief pointer at
   its old path. Update local links when moving detailed material.
8. **Track work once.** Link to the owning checklist or project TODO. Do not create
   another status list in every overview.

Before finishing an edit, check local links, preserve technical values and
qualifiers, and confirm that historical material cannot be mistaken for current
requirements. Do not silently resolve an engineering conflict during a prose edit.
