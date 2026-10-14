# Owner instruction: faster turnaround without lowering quality (2026-10-14)

Owner (verbatim): "do item 1 after S4-02d and add the rest based on observation and merit"

Items as proposed by the coordinator:
1. Faster backend test suite (parallel workers with per-worker DBs, template DB instead of re-migrating, full suite once per slice, focused tests per phase, reviewers rerun the full suite only when a finding needs it). -> Owner: run as its own tooling task right after S4-02d, ahead of normal ranking.
2. Process scaled to task size (S: one build + one review; M: at most two phases, last phase review doubles as slice review).
3. Code-reality check by the Codex Planner before plan review (every named function/table/guard exists; walkthrough reachable).
4. Overlap: next phase on a stacked branch during the previous phase's review; plan the next task while the current one builds.
5. Only High/Medium findings block; Low/Info to backlog unless one-line.
6. Mutation checks targeted at core logic and guards, not docs/tools.
7. Fewer concurrent Postgres-heavy agents on this machine.
-> Owner: items 2-7 adopted at the coordinator's judgement, based on observation and merit.
