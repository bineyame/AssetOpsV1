# S6-02b phase 2 handoff (PARTIAL - stopped near the context cap)

Branch `task/S6-02b-verification-ui`, worktree `AssetOpsV1-review5`. Phase 1: see `.agent/S6-02b-phase-1-handoff.md`.
Phase 2 commits: `b25d91d4` (UI + tests), `08d2d127` (walkthrough tool + evidence script, partial). Not merged.

## Landed (b25d91d4) - UI complete, focused tests green

- Routes: `shell/operatorSiteRoutes.ts` `ACTION_CHILD_VIEWS` = plan, execution, evidence, verification, history;
  `siteActionHref` carries `event_id`, `recorded_at`, `plan_revision_id`, `outcome_id` (`ActionHrefSelector`).
  Frame `shell/SiteAnalyticsFrames.tsx` `SiteActionFrame` reads all four and carries them in every section link.
- `sites/verificationClient.ts` (plan/evidence/outcome/history reads, typed bodies); `actionClient.ts` exports `read`,
  adds `verification` to Action/Change/Recommendation bodies and S6-02a hold fields.
- `sites/SiteActionVerification.tsx` `ActionVerification`: selection rules (`selectorConflict`: event_id or recorded_at
  with an exact plan/outcome -> typed `VERIFICATION_SELECTOR_CONFLICT`; plan vs outcome-of-other-plan -> conflict;
  event_id alone -> the Action read's `cutoff_recorded_at`); default = latest current state (PENDING /
  REASSESSMENT_PENDING show no outcome as current, link the prior outcome); explicit selection -> "Historical" +
  separate current state; outcome panels (three interim labels, GUARDRAIL_FAIL block with metric/value/threshold/
  unit/evidence IDs, Could-not-conclude with known failures in a disclosure), metrics table, Activity (applied change,
  RESOLVED / RESOLUTION_WITHDRAWN, withdrawable note, later Finding as new episode), Outcome list; Plan view
  (criteria, half-open windows, later selection pending with missing day, Dig deeper IDs); Evidence view (requirements,
  comparability, per-window 12-slot table, problems in words, source per window, all IDs in Dig deeper).
- Words: `sites/verificationWords.ts` (labels, reasons, problems, sources; vocabulary-guard safe).
- `sites/recommendationVerification.tsx`: `DeclaredSuccessPanel`, `EvidenceNeededPanel` (recommendation:2-3),
  `LaterEffectPanel`, `DecisionPathPanel` (changes:1#b, changes:2). `SiteRecommendation.tsx` holds on all three
  typed codes, different-Finding notice, outcome / withdrawn-outcome links. `SiteFoundationChange.tsx` and the Action
  Overview read the `verification` block (F5). `actionPresentation.outcomeWords` uses plain labels.
- CSS: `ui/primitives.css` end (`.site-verification`, `.verify-*`). `test/settled.ts` loading sentences added.
- Tests: `sites/__tests__/siteActionVerification.test.tsx` (14, fixture-driven, derived bodies listed in its header);
  `siteAction.test.tsx` / `siteFoundationChange.test.tsx` updated for the new tabs and F5 (57 pass together).
  `npx.cmd tsc --noEmit` clean. `tools/check-all.ps1` passed (9 guards) before the UI commit.

## Partial (08d2d127) - walkthrough

- `tools/s602b_verification_walkthrough.py`: guards (`assetops_s602b*`, not `_test`; `var/s602b*`), marker, two DBs
  (`<db>` replay, `<db>_cases`), `prepare` (git-archive tree; REPLAY script = the replay test's steps via
  `test_s6_verification_replay` helpers into the private DB, writes `<work>/replay.json`), `links`, `serve` (two APIs
  port / port+1; prints two `npm.cmd run dev` commands web / web+1), `capture` (runs the .mjs), `drop`.
  NOT YET RUN. `prepare` step 4 calls `tools/s602b_test_scoped_cases.py <url> <work>` which DOES NOT EXIST yet.
- `tools/s602b-verification-evidence.mjs`: replay claims (current VERIFIED, historical selector across child link +
  reload, plan, dense evidence + table scrollers, conflict, recommendation, change) + per-case claims driven by
  `<work>/cases.json` `{cases: {name: {label, action, expect: {current_state, outcome?, label?, failed?, resolution?,
  prior_link?}, recommendation?: {finding, revision, state, other_finding}}}}`. Syntax-checked only.

## Resume here

1. Write `tools/s602b_test_scoped_cases.py` (Explore findings): builders live in
   `backend/tests/test_s6_verification_evaluator_postgres.py` (`bound_plan` :95, `complete_windows` :110 - patches
   `verification_rules.window_evidence` + AUTHORED provenance port; `late_reading` :83, `store_accept` :185) over
   `CaseRunner` (`test_s4_finding_store_postgres.py:79`, roles-2 KOBO-001, F01 2026-10-06 / F02 2026-10-08) and
   `verifying` (`test_s6_verification_plan_postgres.py:60`). Cases: target miss (:526), guardrail fail + F02
   PRIOR_TRIAL_GUARDRAIL_FAILED (:503), inconclusive real roles-2 path (:204), VERIFIED -> late reading -> overlap on
   F02 -> RESOLUTION_WITHDRAWN -> re-settled INCONCLUSIVE (:412). Holds are battery-scoped, so ONE DB PER CASE
   (4 DBs: extend the tool from one `_cases` DB to `_c1.._c4` and one API per DB, or serve them one at a time).
   Set `ASSETOPS_TEST_DATABASE_URL` before importing (module-level URL); migrate with `pg_harness._alembic`;
   never call `fresh_database` (it needs `_test`).
2. Known served-read hazards for those cases (decide and record in Known Deviations): the served clock is real now
   (2026-10-16) but the fixture rows are recorded 2026-10-29..11-02, so `current_state` reads REASSESSMENT_PENDING
   (FOUNDATION_CHANGED) and `/evidence` recomputes the real incomplete roles-2 windows with UNKNOWN source. Stored
   outcomes/metrics/history/holds read unchanged. Options: serve the cases API via a small wrapper that pins the
   verification clock and the same test-scoped window/source fakes (label it TEST-SCOPED), or capture the case
   screens by explicit `outcome_id` (Historical) and record that current state/evidence differ. Ask the coordinator
   if unsure; the replay (real VERIFIED) is unaffected (its windows are 2026-10-13/15).
3. Run prepare/serve/capture end to end (copy `var/sites/*.yaml` per the brief if the full suite needs them),
   `node tools/layout-evidence.mjs` for the Evidence slots or record `not run`, then `drop`.
4. Final proof per the brief (tsc, full `npm.cmd test`, registry checker, check-all, ONE full backend suite with the
   memory/pytest checks, the two host tests), then closeout: review packet, owner walkthrough, task Status
   in_review, ACTIVE_CONTEXT, CODE_STATE. Leave `I-sim-verification-cases` / `D-verification-window` open.

## Open risks

- Bash tool in this environment mis-parses quoted heredocs containing apostrophes; write files with the Write tool.
- Evidence-view link to the Site Evidence inspector uses accepted evidence IDs (`siteEvidenceAcceptedRecordHref`);
  test-scoped IDs from the contract are not UUIDs (links resolve to "not found" in tests only).
- Full `npm.cmd test` not yet run on the new revision.
