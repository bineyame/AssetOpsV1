# S4-03 — Site Finding index, evidence and history

Status: outline (L); refine after Finding detail review, before activation
USER_REVIEW_REQUIRED: true
Depends on: S4-01 Finding revision; `A-finding-index` decision before Site list and positive Overview
Branch when activated: task/S4-03-site-finding-index-history

## Visible outcome

`sitefindings:1` shows a Site/window Finding list with separate honest empty and positive persisted-row cases. Finding Evidence and History child views select an exact Finding revision. Positive `mini:3` consumes this same Site index; S5-01 owns its Overview presentation.

## Acceptance

- Decide `A-finding-index`, then review `I-finding-index` and `I-site-findings-ui` against a scoped zero-row/watermark fixture and a persisted row fixture with stable Finding/revision links. Both variants are required for W1 core completion.
- `I-finding-evidence-read/ui` traces selected FindingRevision to assessment and accepted envelope/source IDs. `I-finding-history-read/ui` preserves earlier revisions, knowledge cutoff and the late-evidence append path; absent history is explicit.
- Reload each Site/window/revision and compare app/mock `sitefindings`, `finding-evidence` and `finding-history` at desktop and narrow widths, including keyboard and drill-down behavior. No global Findings index follows from this packet.

Independent review and owner checkpoint close the packet. S4-01 detail does not by itself close these paths.
