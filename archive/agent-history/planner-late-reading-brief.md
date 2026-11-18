# Planner brief — late-reading series and money limit (`I-late-reading-series-and-money-limit`)

You are the AssetOps Planner (Codex). The owner chose this task next (`.agent/owner-next-work-2026-10-15.md`, 0.20% contest over `I-action-store`). Write one implementation-ready task packet on this branch (`plan/late-reading-series`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning`, from main `af6f1306`). Do not write code. The coordinator commits your edits.

## Read first (only these, then the code they point to)

- `.ai/DECISIONS.md` decision `D-2026-10-14-s402c-late-sequence-and-s5-money`, and `.agent/architect-S4-02c-answers.md` (Q1 cohort ordering, Q2 Finding limitation and S5 money exclusion, Q3 node placement).
- `.agent/S4-02c-review.md` F1 (the defect: gateway-sequenced late reading -> S3 INDETERMINATE `SEQUENCE_ORDER_INVERTED` / `GENERATOR_SERIES_AMBIGUOUS`, revised Finding SUPPORTED with shrunk episode and OPEN_BOUND only, consequence CURRENT PRICED too low 7.5625 vs 15.8125).
- `.ai/MILESTONE_REVIEW_BACKLOG.md` sections "S4-02c carries", "S4-02c Architect closeout review carries" (late-reading Planner carries L-a..L-f, L1, and the residual risk about the S4-02b Finding money panel), "S4-02d carries" (S5 seam carries), and the owner analysis-input-data item.
- Registry nodes `I-late-reading-series-and-money-limit` and `I-site-overview-read` in `frontend/docs/architecture/v69-dependency-registry-pilot.json`.
- `tasks/README.md`, an exemplar packet `tasks/S4-02d-analytic-finding-worker-schedule.md`, and `backend/TESTING.md`.

## Packet requirements

1. **Code-reality check (mandatory).** Every function, table, column, CLI, guard, fixture and walkthrough tool you name must exist on main today, cited as `path:line`; anything new must be marked new. The walkthrough must be reachable with existing tools plus what the packet builds (the S4-02c late-power walkthrough `tools/s402c_late_power_walkthrough.py` and the S4-02d tick walkthrough `tools/s402d_tick_walkthrough.py` are the natural base).
2. **Cover L-a..L-f and L1 and the residual:** a versioned S3 source-time cohort rule with explicit clock/overlap/epoch limits (state it as a reviewed contract first); reassessment of affected windows that keeps history; the revised S4 Finding carries the series limit and a truthful end reason (not OPEN_BOUND alone); a concrete eligibility signal that S5-01 consumes to withhold the amount (named in both registry nodes); regression over run 1 and an on-time-sequenced late upload; real gateway without validated clock semantics stays limited; and the S4-02b Finding money panel must stop presenting run 1's amount as current.
3. **Open choices go to the Architect as one batched question list** in the packet (a short "Architect questions" section with your recommended answer for each). Do not stall on them: plan around your recommendation, marking what changes if the Architect rules otherwise.
4. **Size and phases (owner-approved speed rules):** M means at most two phases; the last phase's review is the slice review. Focused tests per phase; one full backend suite at the end of the slice (`backend/TESTING.md` normal command, `-n 2`, keep-awake + 2x cap).
5. **USER_REVIEW_REQUIRED:** decide from scope. If any owner-visible copy, panel or state changes (the Finding money panel likely does), set it true and describe the owner walkthrough.
6. Update `tasks/README.md` queue row and the registry node's `task` field to the new packet; keep the registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Status line must start with `outline`, `implementation-ready`, or `refined` (the next-work checker refuses other words).

Keep the packet tight (aim under ~250 lines). When done, print a short summary: packet path, phases, USER_REVIEW_REQUIRED, Architect questions with your recommendations, and any code-reality gaps you found.
