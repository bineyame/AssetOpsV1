# Architect request - LR-01 known deviations (delegated, owner absent)

You are the AssetOps Architect (Codex). LR-01 is built on branch `task/LR-01-late-reading-series-and-money-limit` (head `3b360af5`; read code with `git show 3b360af5:<path>`). Its review packet (copied here as `.agent/LR-01-review-packet-snapshot.md`) lists five Known Deviations for you:

1. Migration `0015_finding_returning_basis.py` drops `finding_revision_basis_unique` (from 0009) so that revoking an attestation can return a Finding to an earlier basis with a new revision; duplicate protection becomes latest-revision-only under the Site lock and matcher fence.
2. The S5 seam turns ELIGIBLE into PENDING_REASSESSMENT while its own S3/S4/schedule blockers stand (incl. stopped schedule); the Finding/Financials API check does not read schedule health.
3. Withholding is conservative: any generator series limit on the Finding's asset within episode +/- 6 h withholds money, even if it does not touch the Candidate tail.
4. The packet's "Finding money panel" is the Financials bridge (the Finding page has no money panel; it only gains the SERIES_LIMIT statement).
5. Consequence reads built without the eligibility argument show no current amount (tests pass an explicit ELIGIBLE stub).

Context: `D-2026-10-15-lr01-source-time-cohort`, `.agent/architect-LR-01-answers.md`, packet `tasks/LR-01-late-reading-series-and-money-limit.md`.

Rule on each (accept/amend/reject, with any required change), short. Write `.agent/architect-LR-01-deviations-answers.md` and amend `D-2026-10-15-lr01-source-time-cohort` in `.ai/DECISIONS.md` with a short addendum (UTF-8, ASCII hyphens). No code. Print a short summary.
