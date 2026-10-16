# S6-02b review packet - Action verification surfaces

Task `tasks/S6-02b-verification-ui.md` (Status `in_review`, USER_REVIEW_REQUIRED true: slice review, then owner
walkthrough `.agent/S6-02b-owner-walkthrough.md`; hold merge). Branch `task/S6-02b-verification-ui` from main
`cdb09767`; not merged. Handoffs `.agent/S6-02b-phase-1-handoff.md`, `.agent/S6-02b-phase-2-handoff.md`.
Reviewer diff: `git diff cdb09767..HEAD -- ':!.agent'`.

## Outcome delivered

- Phase 1 (backend, `87dba01b`, `2ab56ce0`): reserve-aware `mini-grid` v5 (`decide_v5`: start at min(Site start
  threshold, reserve in effect + 5); v1-v4 unchanged and reproducible), scenario `kobo-mini-grid-reserve-trial` v1,
  manifest `backend/conversions/d-verification-window-v2.json` (windows predeclared and committed before the first
  replay). Two registered Lab runs, real gateway, S2 acceptance, S3/S4, Action API: **VERIFIED
  TARGET_AND_GUARDRAILS_PASS** without manufactured readings (Candidate seconds 3600 -> 0; 12/12 slots both windows;
  REGISTERED_SIMULATION with distinct run digests). Why honest: phase-1 handoff.
- Phase 2 UI (`b25d91d4`, `f43be48d`): Action child views Plan / Evidence / Verification under the S6-01b root with
  exact `plan_revision_id` / `outcome_id` / `event_id` / `recorded_at` selectors carried in every section link;
  latest-current default; explicit selection labelled Historical with a separate current state; typed selector
  conflict; three interim labels; GUARDRAIL_FAIL block; RESOLVED / RESOLUTION_WITHDRAWN as activity, never
  permanent; Recommendation success / evidence panels and typed holds; Change later effect from the `verification`
  block (F5). Internal IDs/enums sit in "Dig deeper" disclosures.
- Walkthrough (`08d2d127`, `2057393b`): `tools/s602b_verification_walkthrough.py prepare|links|serve|capture|drop`,
  `tools/s602b_test_scoped_cases.py`, `tools/s602b-verification-evidence.mjs`; layout mode in
  `tools/layout-evidence.mjs` (`64d2feb3`).

## Files materially changed

Simulator/backend: `simulator/assetops_simulator/packs/mini_grid.py`, `backend/assetops_backend/runs/profiles.py`,
`host/execution_adapter.py`, `config/scenarios/kobo-mini-grid-reserve-trial.yaml`,
`backend/conversions/d-verification-window-v2.json`. Frontend: `sites/SiteActionVerification.tsx`,
`sites/verificationClient.ts`, `sites/verificationWords.ts`, `sites/recommendationVerification.tsx`,
`sites/SiteRecommendation.tsx`, `sites/SiteFoundationChange.tsx`, `sites/SiteAction.tsx`, `sites/actionClient.ts`,
`shell/operatorSiteRoutes.ts`, `shell/SiteAnalyticsFrames.tsx`, `ui/primitives.css`. Tests:
`host/tests/test_mini_grid_v5.py`, `host/tests/test_s6_verification_replay.py` (v1 + v2), scenario fingerprint /
binding tests, `sites/__tests__/siteActionVerification.test.tsx` (14). Tools as above. Registry: evidence pointers
only on `I-sim-verification-cases`, `D-verification-window` (both stay `open`).

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Canonical plan/evidence/verification routes, exact selectors, URL survives child links + reload | Met: tests; served claims (Plan child keeps `outcome_id`, reload keeps it; withdrawn case reload) |
| Latest current read state default; PENDING / REASSESSMENT_PENDING shown, prior outcome linked | Met in fixture tests; served current states VERIFIED / INEFFECTIVE / INCONCLUSIVE (the served withdrawn case has re-settled; REASSESSMENT_PENDING is proven in tests only) |
| Historical label, separate current state; withdrawn VERIFIED never current | Met: served withdrawn case (Historical VERIFIED, current INCONCLUSIVE) |
| Typed selector conflict | Met: served `VERIFICATION_SELECTOR_CONFLICT` |
| Plan content (windows, bands, Foundations, target, requirements, policy-trial note, pending binding) | Met (tests; served plan exact ID, old -> new Foundation) |
| Evidence: per-window 12-slot tables, exact IDs, source per window, problems explicit | Met (served 2 x 12 complete, REGISTERED_SIMULATION per window; problem states in fixture tests) |
| Verification: three interim labels, outcome matrix, metrics, GUARDRAIL_FAIL details, limits, no savings | Met (served replay + 4 test-scoped cases; tests) |
| RESOLVED / RESOLUTION_WITHDRAWN as activity, never permanent | Met (served) |
| Prior-trial block incl. different Finding | Met: guardrail case on F02 (`PRIOR_TRIAL_GUARDRAIL_FAILED`, other Finding, link, disabled); overlap `PRIOR_TRIAL_REASSESSMENT_OVERLAP` |
| Recommendation plan link, accepted snapshot pinned; Change later effect, APPLIED not success | Met (served) |
| Public replay genuinely VERIFIED (D-2026-10-16-s602a-replay) | Met (phase 1; rerun at final code) |
| Walkthrough tool prepare/serve/capture/drop on guarded private DBs | Met; run end to end once, then dropped |
| Owner visual acceptance | Pending (owner) |

## Checks run (final code revision `64d2feb3`; later commits are docs/registry/packet only)

- Walkthrough: prepare 5 private DBs (replay VERIFIED `575dae69...`/outcome `001689b9...`; cases target_miss
  INEFFECTIVE TARGET_MISS, guardrail INEFFECTIVE GUARDRAIL_FAIL (below_reserve_seconds, terminal_soc), inconclusive
  INCONCLUSIVE, withdrawn VERIFIED -> withdrawn -> INCONCLUSIVE). Capture at 1440 and 390: **78/78 claims passed**
  (replay 44, target_miss 6, guardrail 10, inconclusive 4, withdrawn 14), 36 screenshots, app-vs-v69 table below.
  Then `drop`: 5 DBs and `var/s602b_owner` removed. (A first capture at `2057393b` passed 74/74 and showed the
  source check as "unknown" before-column; fixed in `f43be48d`.)
- Layout evidence: `ASSETOPS_LAYOUT_S602B_ACTION=<replay action> node tools/layout-evidence.mjs
  http://localhost:5466` - ALL CLAIMS HOLD (Evidence/Plan/Verification at 1440x1000 and 390x900; no page sideways
  scroll; 24 slots in 2 tables; at 390 2 of 2 slot tables overflow inside their own scroller, so the set is real).
- Frontend: `npx.cmd tsc --noEmit` clean; focused 3 files 57 passed; full `npm.cmd test` 1625 passed / 1 failed
  (69 files): `siteFoundationChange.test.tsx` "shows old/new reserve..." could not find the h1 under load
  (130 s parallel run); rerun alone 8/8 passed.
- `tools/check-all.ps1`: all 9 guards passed. Registry checker: valid (234 nodes).
- Host: `host/tests/test_mini_grid_v5.py` + `host/tests/test_s6_verification_replay.py` 13 passed (353 s).
- Full backend suite: see "Full backend suite" below.

### App vs v6.9 (headings as rendered, 1440; 390 identical)

| Screen | Mock | App |
| --- | --- | --- |
| verification:1-3 | Target change, Reserve breaches, Critical service, Final outcome, Target and guardrails evaluated together, Activity evidence, Outcome evidence | Outcome (same four cards), Target and limits evaluated together, Activity evidence, Resolution activity, Outcome evidence |
| action-plan:1 | Success criteria | Success criteria, Windows |
| action-evidence:1 | Evidence requirements | Evidence requirements, Earlier window, Later window |
| recommendation:2-3 | Declare success before evaluating, Evidence needed to verify, Applied configuration record, Later operating evidence | Accepted proposal, Live recomputation, Declare success before evaluating, Evidence needed to verify, Actions on this Finding, Money |
| changes:1#b, 2 | Change and effect, Decision path, Apply and observe, Retain/retune/revert | What changed, Outcome, Later effect, Decision path, Application, Foundation versions |

## Known deviations and decisions

1. **Test-scoped cases (lead-implementer decision).** Target miss, guardrail fail + hold, inconclusive and
   late/withdrawn are S6-02a's evaluator test builders over the roles-2 F01/F02 cases, one guarded
   `assetops_s602b_<db>_<case>` DB each (holds are battery-scoped), served by a wrapper that pins the Action clock to
   the case's recorded end (`pinned_at`) and re-applies the builders' authored window/source fakes. They are not Lab
   runs. Label: the API's source resolution carries `AUTHORED_DEMONSTRATION` (fixture
   `D-verification-window-test-scoped`), rendered "Authored test data (test-scoped example)" and asserted in the
   capture; the inconclusive case uses no fake, so its page carries no data label (source "Source not established")
   and is labelled TEST-SCOPED only in the walkthrough doc, links output and capture claims - gap recorded, no new
   product copy invented. Only the replayed VERIFIED Action is a real served product path.
2. `I-sim-verification-cases` asks for target miss / guardrail fail / inconclusive from Lab runs; only the pass is a
   Lab replay. Node left open for the reviewer/Architect.
3. The served REASSESSMENT_PENDING read state is shown only in fixture tests (the withdrawn case re-settles to
   INCONCLUSIVE before serving).
4. In the replay the earlier-window generator runs unloaded (0 kW): the avoided time is runtime, no fuel or savings
   is claimed (owner doc says so).
5. Mock-fidelity copy refinement is deferred to the W1-conclusion pass per the owner direction.

## Full backend suite

Revision `45405421` (code identical to `64d2feb3`), real Postgres on a private `assetops_s602b_test` base, var/sites
copied from main: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -p no:cacheprovider
--junitxml=<scratchpad>/s602b-junit.xml`, started after the wait for another agent's pytest to end (no other pytest,
3.1 GB free). **2518 passed in 1526 s (25 min 26 s; cap 30 min)**; JUnit tests=2518 failures=0 errors=0
skipped=0. Wall time is about 3x the guide's 8 min under the shared machine's load. Afterwards the base DB and the
copied `var/sites` were removed.

## Residual risk

- One frontend test is load-sensitive under the full parallel run (passed alone).
- Evidence-view links to the Site Evidence inspector use accepted IDs; test-scoped synthetic IDs do not resolve there.
- Replay costs about 4 minutes per manifest in the suite (two manifests).

## User-review focus

Walk `.agent/S6-02b-owner-walkthrough.md`: does the Verification page read clearly for an operator (result,
limits, no-savings note), is "Historical" unmistakable, and do the test-scoped examples read as examples?

## Fix round 1 (Architect D-2026-10-16-s602-closure)

Branch `fix/S6-02b-truth` from `364d7bbe`. Frontend only; no backend change.

- **F1.** On Plan and Evidence views with any explicit selection (cutoff, event, exact plan or outcome), the screen also
  reads `/verification/history` and shows "Actual current state" beside "State at the selected time". The Historical
  banner now says the actual state is shown below, or that it could not be read (or is still being read) and the
  historical state must not be taken as current. A failed read is stated, never hidden. Verification view unchanged
  (its history read already supplies the current state).
- **F5.** `sourceWords` default reads "Source not recognised (treated as unverified)".
- **F3.** The Evidence view reads the plan it belongs to (`/plan?plan_id=`, exact) and each window shows a plain
  summary (assessed days, registered sources, generator-time assessments, source records) and, in Dig deeper: origin
  FindingRevision ID, selected assessment revision IDs, source records, and a per-day table (cohort status and digest,
  run ID, model version, input and configuration digests). Later-window days come from the selection binding named by
  `later_selection_binding_id` (else the last LATER binding recorded by the knowledge cutoff). All fields already come
  from the API; none is missing. Note: the run ID/source runs read "run" in Dig deeper only as IDs; default text avoids
  the banned word. The Evidence read carries `source_resolution.*.runs` (empty in the TEST-SCOPED authored fixture, so
  "none recorded" is shown there).
- **Tests** (`siteActionVerification.test.tsx`, new describe): F1 evidence and plan with a historical VERIFIED beside a
  current INCONCLUSIVE, and the unreadable-current case; F5; F3 summary and IDs.
- **Checks.** `npx tsc --noEmit`: clean. Focused verification file: 18 passed. Full `npm test`: see the final report.
- **Full `npm test` (run 1):** 68/69 files, 1629/1630 tests; one failure, `s404SiteFindingIndex.test.tsx` "changing the
  dates writes a new window..." (S4-04, unrelated, under full-suite load). **Rerun alone:** 15/15 passed.
