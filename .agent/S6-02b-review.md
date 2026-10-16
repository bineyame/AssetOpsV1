# S6-02b slice review - verification UI + reserve-aware public replay

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision reviewed: `b1f1ba97`
(`task/S6-02b-verification-ui`), diff `git diff cdb09767..HEAD -- ':!.agent'`. Code identical to `64d2feb3`.

## Verdict: ACCEPT (no High or Medium findings)

Five Low findings. Fix them on the branch or carry them to the W1 pass, at the coordinator's discretion. The merge
stays held for the owner walkthrough.

## Is the VERIFIED replay genuine? Yes

- **New version; v1-v4 untouched.** `mini-grid` v5 is appended at the end of
  `simulator/assetops_simulator/packs/mini_grid.py` (lines 1138-1207) and `backend/assetops_backend/runs/profiles.py`
  (+`MINI_GRID_V5_MODEL`). No v1-v4 object is edited. `decide_v5` wraps v4's `decide`, lowering only the start
  threshold to `min(start, reserve + 5)`. `test_mini_grid_v5.py` checks three things: v4's coupling is still `decide`;
  v5 equals v4 step-for-step on the template reserve for both scenarios; and v4 ignores a 25 % reserve while v5 does
  not. The v1 manifest (v4, INCONCLUSIVE) is still replayed beside v2.
- **Windows declared before the runs.** Commit `87dba01b` holds the v2 manifest with its windows, scenario, model and
  run timing, and `"expected": {"pending": ...}`. Commit `2ab56ce0` changes only the `expected` block
  (`git diff 87dba01b 2ab56ce0` on the manifest). The windows are not changed.
- **Bands and evaluator unchanged.** The diff touches no file under `backend/assetops_backend/actions/`. The only
  backend product change is the profile registration.
- **No manufactured readings and no private truth.** The replay uses the same path as v1: `_draft`, a real gateway
  publish, S2 batch acceptance, then S3/S4 and the Action API. The generator ON spans pinned in `expected` are
  assertions only, never evidence.
- **Two distinct registered runs; 12/12 slots.** The test asserts that the later run ID differs from the baseline
  run ID, the source class is REGISTERED_SIMULATION, run digests are distinct, the pair is PASS, both windows are
  complete, and the Candidate seconds are 3600 -> 0. I reran it, and it passed.
- **Unloaded generator.** The fact is stated plainly in the manifest's `why_verified`, in the phase-1 handoff and in
  the owner walkthrough ("not fuel burned; no savings are claimed"). The product pages make no fuel or savings claim:
  I grepped the new UI files for fuel/saving/diesel and found only the no-savings notice. Product pages do not
  mention "unloaded", which is acceptable because they claim only avoidable generator *time*.

## UI correctness: met

The checks below were confirmed by reading `frontend/src/sites/SiteActionVerification.tsx`, `verificationClient.ts`,
`recommendationVerification.tsx`, `SiteRecommendation.tsx`, `SiteFoundationChange.tsx` and `SiteAction.tsx`,
together with the S6-02a read code.

- **Default view.** With no selector, the view shows the latest current state. When the current state differs from
  the latest outcome (REASSESSMENT_PENDING, or PENDING under a superseding plan), the outcome is not shown as the
  result. It is offered only as a link that opens under a Historical label (`SiteActionVerification.tsx:428-448`).
- **Explicit selectors.** `outcome_id`, `plan_revision_id`, `recorded_at` and `event_id` persist through every
  section link (`operatorSiteRoutes.ts`, `SiteAnalyticsFrames.tsx`) and are labelled Historical.
- **Conflicting selectors.** These give the typed `VERIFICATION_SELECTOR_CONFLICT`, either client-side before any
  read or from the server's 422. A plan/outcome mismatch is also refused.
- **State source.** The state comes from `current_state` / `verification_state` and from the `verification` block on
  the Action, Recommendation and Change reads. It is never taken from `state.outcome`, which survives only as a
  fallback for older servers (F5).
- **Resolution.** RESOLVED and RESOLUTION_WITHDRAWN are shown as activity, with the "not permanent" note.
- **Holds.** `PRIOR_TRIAL_GUARDRAIL_FAILED` and `PRIOR_TRIAL_REASSESSMENT_OVERLAP` have their own headings and
  other-Finding text, link to the outcome or withdrawn outcome, and leave Accept disabled.
- **No writes.** The verification client has GET reads only, and the UI writes no verdict or event.
- **Test-scoped fakes.** The pinned clock and the window/source fakes exist only in `tools/s602b_test_scoped_cases.py`
  (monkeypatching at serve time). Product code is untouched. Both tools refuse `*_test` databases and any name that
  is not `assetops_s602b*`. `drop` is gated on the marker.

## Deviation 1: the inconclusive case has no on-page label. Acceptable (Low, see F2)

The page does not present itself as a Lab run. Its source reads "Source not established", and the trial notice says
"Lab or authored test data". The walkthrough doc, the `links`/`serve` output (`[inconclusive] TEST-SCOPED`), the
separate port 5467 and the capture claims all label it. Adding product copy only to label a test case would be
worse. The residual gap is that a screenshot of that page alone does not say "test-scoped".

## Registry (deviation 2): keeping both nodes open is correct

`I-sim-verification-cases` requires target miss, guardrail fail and incomplete/late variants from **Lab runs**.
`D-verification-window` requires the same variants "through normal ingestion". Only the pass is a Lab replay; the
other variants are evaluator-builder cases. Both nodes therefore stay `open`, as `D-2026-10-16-s602a-replay`
directs.

S6-02b's own nodes (`I-S6-02b`, `I-verification-plan-ui`, `I-verification-ui`, `I-action-evidence-ui`) do not
require those two nodes. They can resolve on owner acceptance, because the ruling's gate (a genuine public positive
replay) is now met.

`I-S6-02` does require `D-verification-window`, so it cannot close on S6-02b alone. That contradicts the task text
("close I-S6-02 only after fresh review and owner acceptance"). It needs an Architect call: either accept
test-scoped non-pass variants for `D-verification-window`, or name a follow-on that produces Lab non-pass runs. This
is a coordination item, not a finding.

## Findings

**F1 (Low; acceptance gap, partial). `frontend/src/sites/SiteActionVerification.tsx:344-359`.** On the Plan and
Evidence views with a `recorded_at` or `event_id` cutoff, the strip shows only the state *at the cutoff*
(`verification_state` is computed with `at=recorded_at`; `actions/verification.py:488,554`). The real current state
is not read. The banner nonetheless says "The current state is shown separately", which is not true on those two
views; only a link is given.

- *Why it is Low.* VERIFIED is never presented as current. The strip is labelled "State at the selected time" under
  Historical, and the Verification view (which reads the outcome's `current_state`) is correct.
- *Example.* For the withdrawn case reached from a History event link, Plan or Evidence would show "Target met within
  every limit" with no current INCONCLUSIVE beside it.
- *Fix.* When the selection is explicit on Plan or Evidence, also read the history (or the unselected outcome) and
  show its `current_state` beside the at-cutoff state. Add a test that asserts both.

**F2 (Low). Test-scoped labelling of the inconclusive case (deviation 1).**

- *Where.* `tools/s602b_test_scoped_cases.py:13-18` and `.agent/S6-02b-owner-walkthrough.md:52-53`.
- *What.* The page carries no "test-scoped" text.
- *Fix (optional, no product copy).* In the walkthrough, tell the owner that this example's Action Overview shows the
  origin Finding's prepared-data notice, if it does, or make the capture claim assert the walkthrough label.

**F3 (Low; acceptance gap, lineage display). `SiteActionVerification.tsx:1031-1285` (Evidence view).** The task's
Evidence view asks for clock/cohort and "selected assessments/FindingRevision" per window. The view does not render
any of the following:

- `target.*.assessment_revision_ids`;
- per-day `cohort_status` / `cohort_sha256`;
- source `runs` (run identity digests);
- the plan's `origin_finding_revision_id`.

Some of this lineage is reachable elsewhere: S3 day selections (run ID and window revision IDs) for both windows are
in the Plan view's Dig deeper, and the origin Finding version is on the Action Overview. The packet's "Evidence ...
exact IDs: Met" overstates this. *Fix:* add those fields to each Evidence window's Dig deeper.

**F4 (Low; presentation). `SiteActionVerification.tsx:218-220`.** The conflict panel prints `Code:
VERIFICATION_SELECTOR_CONFLICT` in the default reading, outside "Dig deeper". *Fix:* move it into a Dig deeper
disclosure or keep it only as a `data-*` attribute.

**F5 (Low; honesty, latent). `frontend/src/sites/verificationWords.ts:221-222`.** `sourceWords` maps any
unrecognised source state to "Field readings". No field source class exists: the backend emits only
AUTHORED_DEMONSTRATION, REGISTERED_SIMULATION, MIXED and UNKNOWN. An unexpected value would therefore be labelled as
real-equipment data. *Fix:* the default should read "Source not recognised".

## Checks I ran (this worktree, `b1f1ba97`)

- **Postgres DB.** Private `assetops_s602brev_test`, dropped afterwards; no `assetops_s602brev*` database remains.
- **v5 model and catalog.** `pytest host/tests/test_mini_grid_v5.py backend/tests/test_scenario_fingerprints.py
  backend/tests/test_run_binds_scenario_to_site.py`: **58 passed** in 16 s.
- **S6 verification files.** `pytest test_s6_verification_rules.py, _verdict.py, _plan_postgres.py,
  _evaluator_postgres.py, _holds_postgres.py` (real Postgres): **78 passed** in 367 s.
- **Public replay.** `pytest host/tests/test_s6_verification_replay.py -k v2` (real Postgres; manifest test plus the
  full replay): **2 passed** in 208 s. **VERIFIED reproduced.** The v1 parametrisation was not rerun.
- **Types.** `npx.cmd tsc --noEmit`: clean (exit 0).
- **Focused frontend tests.** `npx.cmd vitest run siteActionVerification.test.tsx siteAction.test.tsx
  siteFoundationChange.test.tsx`: **57 passed** (3 files). Vitest ran under this sandbox.
- **Guards.** `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed.

## Not verified by me

- The full `npm.cmd test` and `npm.cmd run build`: not run.
- The full backend suite: not run. I cite the implementer's run at `45405421`, whose code is identical: 2518 passed,
  JUnit 0 failed / 0 skipped, 1526 s.
- The walkthrough `prepare` / `serve` / `capture` (78/78 claims, 36 screenshots) and the
  `tools/layout-evidence.mjs` run: not rerun; Chrome and the dev servers are needed. The packet records both as run
  with the precondition met.
- Served REASSESSMENT_PENDING: shown in fixture tests only (packet deviation 3).

## Residual risk not in the packet

- **Recommendation Money panel.** It is an S5 feature that the app-vs-mock table lists for the replay's
  Recommendation. It may show a fuel or cost figure for the baseline Finding, whose generator ran unloaded. The owner
  should read it as the Finding's estimate, not as a trial saving. I did not check what it renders for this replay.
- **Predeclaration evidence.** Commit order is the only proof the windows came first. In-process kernel runs (the
  "34.6 %" dip in the scenario comments) informed the scenario's design before the verification replay. The ruling
  allows this, since it asks for the scenario and windows to be chosen before evaluation, and the windows themselves
  are a fixed 06:00-07:00 UTC on both run days.
- **Inconsistent provenance wording.** Two words exist for the same source class: REGISTERED_SIMULATION reads
  "Generated test data" in `sourceProvenance.tsx` but "Registered Lab trial data" in `verificationWords.ts`. This is
  noted for the W1 copy pass, not raised as a finding.
