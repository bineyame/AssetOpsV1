# S3-01u — Assessed-day discovery and full Evidence access

Status: outline follow-up; not activated and not an S4-01 technical prerequisite
USER_REVIEW_REQUIRED: true
Depends on: merged S3-01 selected dispatch read and S2 accepted Evidence API
Branch when activated: task/S3-01u-dispatch-usability
Planner: Codex, 2026-10-12

## Visible outcome

Performance > Dispatch still opens on today's UTC day, but can discover Site-scoped assessed days and jump explicitly to the latest assessed day. A selected run/revision's Evidence drawer can page through the complete accepted record set instead of stopping at the first 60. Current status and freshness remain labelled; the shortcut never silently changes the default day.

## Acceptance and review

- Read assessed days for the authenticated Site from persisted selected S3 assessment records with stable cursor/order, selected model/revision and source/analytic watermark. Empty or lagging discovery is explicit. The latest-assessed shortcut names its target day and freshness before navigation; date picker and URL/reload preserve selection.
- Evidence drill-down shows total accepted records, page size and cursor; every page stays on the exact selected run/revision and accepted ID set, with deterministic ordering and no duplicates/skips across reload. Preserve full IDs/lineage even when the visible page is partial. A stale, failed or absent result does not invent an interval or record.
- Exercise an assessed historical day, today's unassessed default, multiple pages beyond 60, no records, a late revision and foreign-Site authorization. Compare app/mock desktop and narrow navigation and keyboard behavior; run focused backend/frontend tests and normal guards. Independent review and owner checkpoint close this usability carry.

This packet does not change S3 classification, S4 Finding prerequisites or S2 accepted-evidence truth. Q21's stable fixture specification versus environment-bound run IDs remains a documentation practice at the next S3 fixture touch.
