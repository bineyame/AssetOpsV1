# Architect request — work order for the owner's absence (2026-10-15, ~12:30 to 22:00 EAT)

You are the AssetOps Architect (Codex), acting on the owner's behalf for sequencing decisions. Owner delegation (verbatim) is in `.agent/owner-autonomy-2026-10-15.md`: continue towards completing Wave 1, the Architect makes calls on the owner's behalf; the owner does pending walkthroughs at 22:00.

## State

- main `ad2a96d0` (plus coordinator records). Done since S4: S4-02 family, S4-02c, S4-02d, OPS-01 (full backend suite ~8 min with `-n 2`).
- **LR-01** (`I-late-reading-series-and-money-limit`) is on `task/LR-01-late-reading-series-and-money-limit`: phase 1 built and reviewed (F1 fix folded into phase 2), phase 2 building now. USER_REVIEW_REQUIRED true, so its **merge waits for the owner at 22:00**.
- Latest next-work before LR-01 activation: `.agent/next-work-2026-10-15a.json` (top `I-late-reading-series-and-money-limit` 2.02, second `I-action-store` 2.016). `tasks/README.md` is the queue; registry `frontend/docs/architecture/v69-dependency-registry-pilot.json` (W1 `exit_requires`, `real_pilot_requires`). Backlog carries `.ai/MILESTONE_REVIEW_BACKLOG.md`.
- Owner-absent rule: UI slices (USER_REVIEW_REQUIRED) may be planned, built and fresh-reviewed but not merged; they may stack on unmerged branches. Non-UI work may merge after a fresh review. Process rules: size-scaled phases (S = one build + one review; M = at most two phases), Codex Planner writes packets with a code-reality check, fresh Claude reviews, only High/Medium findings block. One Postgres-heavy build at a time on this machine, plus at most one reviewer on focused tests.

## Decide

1. **Ordered work list for the window** (about 9 hours of agent time; one build stream plus planning/review in parallel). For each item: node/task, why now, whether it is UI (held) or non-UI (mergeable), what it stacks on, and its gate. Candidates include, but are not limited to: S5-01 Site Overview (stacked on LR-01; needs `I-site-overview-read`/`-ui`), `I-action-store` / S6-01 track (packet is an outline; `A-action-lifecycle` resolved), `I-stored-demo-provenance` (W1 exit requirement), `I-price-equal-start-succession`, the S4-02d I3 evidence-owner `decided_at` packet, the F-B statement-level guard, OPS-01 Low carries, A-finding-index/S4-04.
2. **Any contested next-work choices** (gap <= 5%) you foresee in that list: rule them now so the coordinator need not come back.
3. **Planner work to start now in parallel** (packets to write or refine while LR-01 phase 2 builds).
4. Anything that must wait for the owner regardless.

Write `.agent/architect-autonomy-2026-10-15-answers.md` with the ordered list and rulings, and append a short decision `D-2026-10-15-owner-absence-work-order` to `.ai/DECISIONS.md` (UTF-8, ASCII hyphens). No code, no packets. Print a short summary.
