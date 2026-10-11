# S4-01 — Stable Finding identity and evidence detail

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S4 Finding + Financials
Depends on: S3-01
Branch: task/S4-01-finding-identity
Planner: Codex, 2026-10-07

## Visible outcome

Open a candidate interval as Site finding/finding-evidence with a durable episode and evidence drawer.

## Persisted object and read contract

Finding and immutable FindingRevision linked to AssessmentRevision; Site Finding read API and episode matching rule. Apply `A-claim-work-routes` for stable detail identity, revision selection and unavailable/forbidden behavior before fixing the UI route.

## Demo acceptance

Exercise extension, adjacent interval within declared tolerance, separated recurrence and late reassessment; same episode revises one Finding, recurrence links a new Finding.

## Missing/conflicting evidence

Indeterminate intervals do not assert an avoidable operational episode.

## Evidence lineage

Drawer traverses FindingRevision to assessment, analytic run and exact AcceptedEvidence/SourceEnvelope IDs.

## Review and refinement

S4-01 owns `I-finding-store/read/ui` and `D-finding-revisions`: exact `finding_revision_id`, `knowledge_at`, episode/recurrence and late-evidence append are its reviewable detail closeout. [S4-03](S4-03-finding-evidence-history.md) owns Finding Evidence/History child views; [S4-04](S4-04-site-finding-index.md) owns the Site list. S4-01 detail does not complete those moved W1 panels.

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Findings index and broad lifecycle UI.
