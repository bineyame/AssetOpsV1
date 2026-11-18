# S4-03 phase 2 - Architect questions (batch 1)

Raised by the phase 2 Implementer, 2026-10-13. Each has a fail-closed default that is already built; work continued on the default. None blocks phase 3.

## Q1 - Old assessment-keyed Finding page's Evidence tab

The task requires `/findings/{site}/{assessment}/evidence` (T028, `FINDING_TAB_ROUTE_PATH`) to redirect to or reuse the S4-03 read. No API maps a T028 assessment ID to a durable Finding ID (`AssessmentSummary.finding_id` is the assessment ID, not a Finding UUID). The only bridge is by day: `GET /api/sites/{site}/finding-windows/{day}`, already used by Dispatch.

Default built (`LegacyFindingEvidence`, `frontend/src/sites/SiteFindingEvidence.tsx`): read the saved Findings recorded for the assessed window's UTC day. With exactly one, redirect (replace) to that Finding's Evidence view, which is the latest version at read time and is labelled so. With several, offer a choice. With none, or if the read is refused, show a plain state that links the site's records page. The old per-segment evidence list (`FindingEvidence`) is removed, so there is no second Evidence source.

Question: is a day-level match acceptable, or should the backend expose an exact assessment-revision to Finding lookup (later slice)?

## Q2 - Lineage link words

The brief says to render broken links "with `lineage.words`". The read's words are engineering text: "envelope", "binding set revision", "cited_evidence_sha256". The product vocabulary guard (`frontend/src/test/productVocabulary.ts`) bans "envelope", "binding" and "mapping".

Default built: a frontend `LINK_WORDS` map gives plain words keyed by the same link names. The read's `lineage.words` is the fallback for an unknown link name, so a new link is still named and never hidden.

Question: should the backend's `BROKEN_WORDS` be reworded to product language at source instead (phase 3 or closeout)?

## Q3 - "Selected window" context on the Evidence view

Default built: the Evidence view keeps these in the address, and each survives reload and back/forward:

- the site and Finding (path)
- `revision_id`
- the record page (`offset`)
- the selected record (`record`)

Moving between Finding sections keeps `revision_id` only. The Finding root's `view=analysis` and the Evidence `offset` and `record` are per-view. A per-assessment-window filter is not offered.

Question: confirm, or name a window filter for phase 3.
