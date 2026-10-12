# Architect request: G-01/G-02 activation rule and packet tidy (2026-10-13)

The mock-gap planning branch merged to main with review carries F1-F5 (`.agent/mock-gap-planning-review.md`). Owner confirmation (verbatim): "confirm gap catalogue and orphan guard now, defer ranking to W1 exit" (`.agent/owner-mock-gap-confirmation-2026-10-12.md`). V-01b is currently the single active task.

Rule and apply in one pass (work only in this worktree; leave edits uncommitted):
1. **F1 activation rule:** G nodes reach no panel, so next-work never selects them and the loop only activates on `select`. Define how G-01, then G-02, G-03..G-05 are activated (e.g. outside competitive ranking at the next free single-active slot, like PRE-S3-04; their relation to a ≤5%/notice contest; whether they precede or follow the next ranked selection after V-01b), including G-03's V-01b merge gate. Record it in `.ai/DECISIONS.md` (amend `D-2026-10-12-mock-gap-closure-mechanism` or a short new decision), `tasks/README.md`, `.ai/COORDINATOR_LOOP.md` if needed, and the registry `outside_ranking` (or equivalent) so next-work reports them honestly. Owner already confirmed "now" for G-01's content; say whether the slot ordering needs owner input (default: no).
2. **F2 (G-01):** settle whether the checker requires `gap_ids` on every non-core portion at G-01 close or only enrolled batches; name the first real tagged placement used for the Vitest non-vacuity check and screenshot pair.
3. **F3 (G-01):** require a fixture proving next-work decision/scores are unchanged when `mock_gaps` entries exist.
4. **F4 (G-02):** remove the stale "absent from this worktree" sentence; note the V-01a/V-01b merge dependency proxies.
5. **F5:** tidy the decision entry to the usual `Decision: \`D-...\`` form and confirmed wording.
Run the registry checker, delivery fixtures and `tools/check-all.ps1 -Python python`. Write `.agent/architect-G-activation-answers.md` with a short summary.
