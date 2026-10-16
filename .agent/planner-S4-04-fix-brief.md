# Planner fix round 1 - S4-04

You are the AssetOps Planner (Codex). Amend `tasks/S4-04-site-finding-index.md` (and `tasks/README.md`, `backend/TESTING.md` references only as packet text) on `plan/S4-04-refine` in this worktree. No code; the coordinator commits.

Inputs: plan review `.agent/S4-04-plan-review.md` (RETURN M1; L1-L5) and Architect rulings `.agent/architect-S4-04-answers.md` / `D-2026-10-15-s404-contract`.

Apply:
1. M1: mark `domain=mini-grid-dispatch` as new; map it to stored `finding.domain='mini_grid'` + `analytic_id='dispatch'` and the S3 `dispatch` discovery basis (cite `analytics/finding_episode.py:68`, `analytics/dispatch.py:27`, `assessment_worker.py:51`); any other domain -> typed 422 (never a CURRENT empty); echo the resolved domain in the response; add the test.
2. Architect rulings: replace the three questions with the ruled route and the two 409s vs 422 malformed cursor; the durable-snapshot rules; fixed-point neighbour closure with the 62-day cap and `INDEX_CONTINUITY_LIMIT`; their phase-1 tests; state `total_count` is null unless `CURRENT`.
3. L2 (coordinator decision): S4-04 builds NO durable snapshot (no migration, no new writer); stale/failed reads return no rows per the ruling's no-snapshot branch. State it.
4. L1: re-verify line citations against the stacked base `task/S5-01-site-overview` (LR-01 shifts some by 1-6 lines; LR-01 changes the `_insert_revision` replay check) using `git show`.
5. L3: name the new focused test file(s) and add them to the packet's TESTING.md update; name the phase-2 layout-evidence script; a skipped run is recorded `not run` with its precondition.
6. L4: add explicit settle/tick steps to the walkthrough for `late` and gate reopen (model: `recover` in `tools/s4_finding_walkthrough.py`).

Keep Status `implementation-ready`; registry valid. Add a "Plan fix round 1" note. Print a short summary.
