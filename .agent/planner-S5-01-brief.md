# Planner brief — refine S5-01 Site Overview (selected window)

You are the AssetOps Planner (Codex). The Architect's work order (`.agent/architect-autonomy-2026-10-15-answers.md`, decision `D-2026-10-15-owner-absence-work-order`) puts S5-01 next after LR-01 and asks you to refine it now. Refine `tasks/S5-01-site-overview.md` (currently a 38-line outline) into an implementation-ready packet on this branch (`plan/autonomy-2026-10-15`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning`). No code. The coordinator commits.

## Read

- Work order item 2 and "Planner work" item 1 in the answers file above.
- Decisions `D-2026-10-14-s5-selected-window-overview`, `D-2026-10-14-s402c-late-sequence-and-s5-money`, `D-2026-10-15-lr01-source-time-cohort` in `.ai/DECISIONS.md`; `.agent/architect-A-S5-overview-answers.md`.
- Backlog `.ai/MILESTONE_REVIEW_BACKLOG.md`: "A-S5-overview review carries" (S5-01 Planner carries P1-P9), "S4-02c carries", "S4-02d carries" (S5-01 seam carries), "LR-01" if present.
- Registry nodes `I-site-overview-read`, `I-site-overview-ui`, `I-S5-01` and panels `mini:1#a`, `mini:2#a`, `mini:4#a` (`frontend/docs/architecture/v69-dependency-registry-pilot.json`, `v69-panel-contracts.json`), the mockup `frontend/mockups/v69/` mini screens.
- LR-01 packet `tasks/LR-01-late-reading-series-and-money-limit.md`. LR-01 code is NOT on main: it is being built on branch `task/LR-01-late-reading-series-and-money-limit`. Read it with `git show task/LR-01-late-reading-series-and-money-limit:<path>` / `git log` from this worktree to cite the actual eligibility names; mark any LR-01 symbol "from LR-01 (unmerged, stacked)".
- S4-02d seam `backend/assetops_backend/scheduling/upstream.py`, the existing `site_window_projection`/`SiteWindowSummary` code, and the exemplar packet `tasks/S4-02d-analytic-finding-worker-schedule.md`; `backend/TESTING.md`.

## Requirements

1. Code-reality check: every function, table, column, route, component, test and tool cited `path:line` and verified; new things marked new.
2. Cover P1-P9 and the S4-02d S5 seam carries explicitly (selected UTC day; which Finding the money card shows; Unknown/pending/stale/failed and no-amount states with wire fields; CURRENT for a scoped read; `source_open` gate; `S3_UNASSESSED` days as a gap; one seam instance per process; shared LR-01 `money_eligibility` consumed, no UI-only predicate; Finding list shown unavailable, not empty; no unsupported mock claims; demonstration labels reused from S4-02b).
3. M, at most two phases; the last phase's review is the slice review. Focused tests per phase; one full suite at slice end (`backend/TESTING.md`). USER_REVIEW_REQUIRED true with a reproducible owner walkthrough (serve mode, 1440/390 browser evidence) that can run on the LR-01-stacked branch.
4. Branch: `task/S5-01-site-overview` stacked on the reviewed LR-01 head; merge held for the owner.
5. Update `tasks/README.md` row and keep the registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Status must start `implementation-ready`.

Keep it tight (aim under ~250 lines). Print a short summary: phases, open questions (with recommendations, for the Architect), code-reality gaps.
