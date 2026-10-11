# S4-03 — Finding Evidence and History

Status: outline (S incremental closeout); refine after Finding detail review, before activation
USER_REVIEW_REQUIRED: true
Depends on: S4-01 Finding revision and accepted evidence lineage
Branch when activated: task/S4-03-finding-evidence-history

## Visible outcome

Finding Evidence and History child views select an exact immutable FindingRevision with accepted-source lineage and prior revisions at the chosen knowledge cutoff.

## Acceptance

- `I-finding-evidence-read/ui` traces selected FindingRevision to assessment and accepted envelope/source IDs. `I-finding-history-read/ui` preserves earlier revisions, knowledge cutoff and the late-evidence append path; absent history is explicit.
- Reload each Site/window/revision and compare app/mock `finding-evidence` and `finding-history` at desktop and narrow widths, including keyboard and drill-down behavior. The Finding revision/evidence fixture is `D-finding-revisions` from S4-01.

Independent review and owner checkpoint close the packet. S4-04 owns the Site FindingIndex/list separately.
