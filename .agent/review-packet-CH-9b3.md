# Review packet: CH-9b3 mill verdict (evaluator, trigger, read, page)

Branch `task/CH-9b3-mill-verdict` (main merged at `24b6e6b59`, main = `5fe2cf42d` with the CH9b3-R rulings). Scope: build
sheet CH-9b "Build units" CH-9b3, as cut by SCOPE-1, pre-flight `.agent/CH-9b3-preflight.md`, rulings CH9b3-R (all 12
defaults accepted, +0.5 for Q5/Q6). Paths: `B/` = `backend/assetops_backend/`. USER_REVIEW_REQUIRED: no (lane-2 unit;
the owner sees the page in the post-W6 walkthrough). Not merged.

## Outcome delivered

- **Evaluator** `MiddayShift.evaluate` + pure `assess` / `assess_plan` / `outcome_rows` (`B/actions/verification_families.py`).
  Decimal and integers only: `10*Σlater*nb >= 11*Σbaseline*nl` (equal day counts, so the means rule). One decisive outcome per
  plan, stored or nothing:
  - VERIFIED `['TARGET_MET']`; INEFFECTIVE `['TARGET_MISS']` (Q1);
  - SHORT baseline, a frozen baseline day no longer COMPLETE, or fewer than 3 later days while the look-ahead is open: nothing
    stored, `not_judged_text` (Q2, Q4); look-ahead closed (Site-local today > effective day + 14) with fewer than 3: INCONCLUSIVE
    `['LATER_SHORT']` (Q2);
  - baseline Σ 0: INCONCLUSIVE `['BASELINE_ZERO']` (Q3), even when later is 0 too.
  - A later day counts only once it has ended (`< today`, Site-local). A COMPLETE row with no `kwh` makes its day not count.
- **Store** (`B/actions/adapters/postgres_action_store.py`): `DOMAIN_OUTCOME_COLUMNS` (derived; `OUTCOME_COLUMNS` unchanged),
  `record_domain_outcome` (advisory lock per domain Action, replay on the plan's existing outcome; no request row, no
  `action_event`; actor `SYSTEM` / `service:verification-evaluator`, job `midday-verification-evaluator`, key
  `midday-outcome-{plan_id}`), `domain_outcomes`, `undecided_domain_plans`. `domain_plan_context` also returns `d.title`.
- **Service** (`B/actions/verification.py`): `evaluate_domain_plan` (story time, DD-1b), `evaluate_site_domain_plans`,
  `domain_summary` (stored outcome read back, never recomputed; live `assess` only for the not-judged text).
- **Trigger** (Q9, `B/scheduling/stages.py` `chain_snapshots`): after the drain, `_evaluate_mill_plans` judges every undecided
  midday plan of a MINIGRID Site via `actions.composition.evaluate_domain_plans`, reusing the stage's `SnapshotReader` and the
  stage's `site_today`. Reported in the stage body as `verification: {code, judged[]}`; any exception → `{"code":"FAILED"}`,
  never a stage failure.
- **Read** (Q5): `GET /api/sites/{code}/domain-work/actions/{id}/verification` in `B/action_api.py` (read-only, `access` scope,
  `access_basis`). `cost_check`/`trial_hours` are `null`. The domain detail read is not touched (CH9b1-R Q5 stands).
- **Lifecycle** (Q10, `B/chain/adapters/postgres_thread_sources.py` `_OUTCOMES`): `COALESCE(o.action_id, o.domain_action_id)`
  and `CASE WHEN o.domain_action_id IS NOT NULL THEN p.effective_from ELSE <_CHANGE_OF> END`.
- **Site index** (Q6, `B/work/site_index.py` `_action_link`): a MINI link with lineage gets
  `/sites/{code}/domain-actions/{id}/verification`; the cold/EV href is unchanged.
- **Page** (Q6/Q7): route `SITE_MILL_VERIFICATION_ROUTE_PATH` (`frontend/src/shell/operatorSiteRoutes.ts`, `App.tsx`),
  `SiteMillVerificationFrame` (`frontend/src/shell/SiteAnalyticsFrames.tsx`, end of file), body `frontend/src/sites/SiteMillVerification.tsx`
  (one `Panel`, one `DataTable`), client `frontend/src/sites/millVerificationClient.ts`. W1 `SiteActionFrame`, its MINIGRID
  dispatch and Kobo ACT-001 are untouched. Register row R700 (MD-CH9b-1).

## Acceptance (CH9b3-R) criterion by criterion

| Ruling | Status | Evidence |
|---|---|---|
| Q1 INEFFECTIVE TARGET_MISS, "Target not met" | Met | L0 `test_just_under_ten_percent_is_ineffective_target_miss`; L2 `test_target_miss_is_ineffective`; vitest INEFFECTIVE |
| Q2 SHORT / later-open store nothing; closed → INCONCLUSIVE LATER_SHORT | Met | L0 short, later-open, day-not-ended, later_short; L2 `test_short_baseline_stores_nothing_and_reads_not_judged` (0 outcome rows), `test_later_short_waits_then_is_inconclusive_once_the_look_ahead_closes` |
| Q3 BASELINE_ZERO "Could not conclude" + line | Met | L0 (later 0 and 4); L2 through the stage helper; vitest |
| Q4 Decimal only; baseline day no longer COMPLETE → not judged | Met | L0 boundary exactly 10% (11.0 vs 10.0) passes, 10.999 fails; `test_a_frozen_baseline_day_no_longer_complete_is_not_judged` |
| Q5 store + `domain_summary` + one read-only GET; `OUTCOME_COLUMNS` and reserve bodies byte-equal | Met | L2 VERIFIED row: `action_id` NULL, `domain_action_id` set, 0 request rows, 3 metrics; replay; `test_ch9b2_reserve_byte_equal_postgres.py` (golden) passes |
| Q6 new path, site_index href, one Panel + one table, no cost/trial cards | Met | L0 `test_site_index_gives_a_mini_action_the_mill_verdict_href_only_with_lineage`; vitest asserts no cost-check/trial-hour text |
| Q7 SCOPE-1 sentence verbatim, then the R7 line; no guardrail text | Met | L2 + vitest VERIFIED assert both strings |
| Q8 new words in the frontend exemption, never `chain/vocabulary.py` | Met | The stored title ("Run the mill at midday") is wrapped `data-vocabulary-exempt="user-owned"` (guard flagged "run"); all other page words pass the w1 scan in every state; `chain/vocabulary.py` untouched |
| Q9 evaluator callable at story time and after the drain; failure never fails the stage | Met | `evaluate_domain_plan` service method; L2 `evaluate_domain_plans` (the stage's call) judges once, then `[]` |
| Q10 COALESCE / effective_from; reserve rows byte-equal | Met | L2 lifecycle row: `action_id` = domain id, `effective_from` = plan's; new `test_lifecycle_outcomes_read_is_byte_equal_for_reserve_rows` (old literal SQL vs new, rows equal, non-empty, `effective_from` non-null) |
| Q11 L2 fixture only | Met | MD-0 mill proof is DD-1b's |
| Q12 R6 | Stated | Occurrences during the later window are not recorded as RECURRED_DURING_CHECK (BL-07); the R3 metric alone decides (`details.recurrence`) |
| L3 | Deferred | As pre-flight (CH-6a2 not on main) |

## Proofs that the tests can fail (each planted, run, reverted with `git checkout`)

- L0 (`scratchpad/mutate.py`): P1 `>=`→`>` fails the boundary test; P2 no BASELINE_ZERO branch fails the zero test; P3 SHORT
  stores an outcome fails the SHORT test; P4a look-ahead always closed fails 4 tests; P4b never closed fails LATER_SHORT;
  P6 miss stored INCONCLUSIVE fails the INEFFECTIVE test and the summary test; P7 MINI href dropped fails the href test.
  (A first P3 "SHORT branch ignored" did not fail: the frozen-day re-check gives the same not-judged result, so the branch is
  defence in depth; the stronger mutation was used.)
- L2: `_OUTCOMES` without COALESCE fails the L2 VERIFIED lifecycle assertion; the reserve branch reading `o.recorded_at` fails
  the reserve byte-equal lifecycle test (2 failed, 6 passed); reverted.
- vitest: NOT_JUDGED headline mutated to "Target met" fails the NOT_JUDGED test; reverted.

## Checks run (localised; no full suite, no demo prepare)

- L0: `test_ch9b3_mill_verdict.py` 13 passed; `test_ch9b2_midday_plan.py` passed.
- L2 (`tools/run-host-tests.ps1`, dev server `assetops_test` base): `test_ch9b3_mill_verdict_postgres.py` 5 passed (32 s).
- Adjacent at `f13efe820`: reserve byte-equal (3, incl. new), ch9b2 plan postgres, ch5c2 clock guard, s6 site action index,
  fix-cold-drain stage, ch1b drain, link lineage, ch0 tick timing: 90 passed; `test_ch9b1_origin_readers.py` failed 8 (the
  `domain_summary` origin check added a 6th origin reference to `actions/verification.py`, allowlist 5). Fixed in `914454c71` by
  checking `domain == "MINI"` only (the freeze already refuses a non-opportunity Action); re-run 9 passed.
- Adjacent Postgres: ch1b outbox, ch2 thread store, w401 site indexes, ch9b1 opportunity actions, w502 domain work links:
  24 passed (250 s).
- Frontend: `millVerification.test.tsx` 7 passed (loading, VERIFIED, INEFFECTIVE, INCONCLUSIVE x2, NOT_JUDGED, NO_PLAN, 404,
  error, client refusals; vocabulary scan in 4 states); `src/shell` + `domainActionVerification` + `src/test`: 62 files,
  1453 passed; `tsc --noEmit` exit 0; hard-wiring ratchet passed (totals api 12, href 24, lit 70, cmp 51, code 3).
- Guards, one at a time: `check-architecture.ps1` passed (242 s); `check-navigation-truthfulness.ps1` passed; chain coherence +
  event register + chain structure 126 passed; `chain.graph check` exit 0; mock-deviation labels 14/14 and repo scan OK;
  missing-claim scan first FAILED (`"Not available yet"` untagged in the table) → the cell now reads "Too few fully checked
  days"; re-run passed. `check-agent-workflow.ps1` passed (after the packet commit).
- Polish clone: see "Clone run".

## Clone run

`assetops_chainclone_ch9b3_test` at `3181552d7`, after lane 1's clone went idle (0 sessions). Work dir: a copy of polC's
`var/polish_full` top-level files in this tree's `var/ch9b3work` (polC read only, never run against):

- create + migrate to head (7 s);
- settle: S2 comparison permitted, tick COMPLETED (102 s), performance permitted;
- W6 `chain_watermark_guard`: requests 46, non-200 0, unresolved [], untracked [], clock_predicates 0, file_violations 0,
  modules 127, unlisted [];
- `chain_response_probe fresh` with `ASSETOPS_RESPONSE_STORE=on`: 43/43 stored bodies equal a fresh compose (221 s);
- backfill b,c,d: b written 9, c LINKED 3, d ACTION_IN_HAND 3 / CHANGE_APPLIED 2 / RESOLVED_MONITORING 1 (the new `_OUTCOMES` on
  the polish reserve rows);
- collect 85 requests, all 200; COH check vs `expected-today.json`: every rule 0 new (COH-2 2/2, COH-7 8/8 expected),
  self-check 10 pass 0 fail;
- dropped (2 settle files removed; `var/ch9b3work` removed). The polish DB has no domain plan, so the stage evaluator judged
  nothing there; the mill proof on the story is DD-1b's (Q11).

## Mock to new (all MOCK DEVIATION D1 R700 = MD-CH9b-1; v70 has no mill verdict page)

| Mock (v70) | New | Why |
|---|---|---|
| No page; the grain-mill trial is a proposal (`index.html:424`, "A grain-mill trial sized at 10 kW for 1 hour") | `/sites/{code}/domain-actions/{id}/verification`: crumbs Actions › code › Verification · site, header "{code} · {title}", one Panel "Verification" | Q5/Q6: the Grow row's "verified" needs a traceable before/after |
| — | Headline "Target met" (VERIFIED) | W1 "Target met within every limit" would claim guardrails (none, BL-09) |
| W1 "Target not met" / "Could not conclude" | Reused for INEFFECTIVE / INCONCLUSIVE | Q1 / Q3 |
| — | "Not judged yet" + server text "Not judged yet: only {n} of 3 fully checked days after the change" (and the CH-9b2 "before" text) | Q2 |
| — | "Midday use rose by at least the declared 10% on fully checked days" | Q7, SCOPE-1 verbatim |
| — | "Midday use before and after the change: {b} → {a} kWh a day on {n} fully checked days each" | Q7, R7 |
| — | "Only {n} of 3 fully checked days after the change in the 14 days allowed, so no verdict is given" | Q2 LATER_SHORT line (builder wording) |
| — | "No midday use was measured before the change, so a 10% rise cannot be measured" | Q3 verbatim |
| — | Table: Measure / Before the change / After the change / Fully checked days (before, after) / Needed to pass ("At least 10% above before: {t} kWh a day"); a missing mean reads "Too few fully checked days" | R7 metrics table |
| — | Loading "Loading the Action's verification." (existing settled sentence); 404 "No such Action for this site."; errors "The verification read could not be reached." / "...answered in an unexpected shape." / "...was refused." | named states, never a thrown error |

## Known deviations

- Q9 trigger is broader than the pre-flight's "only when the drain processed a `productive_kwh` row": every MINIGRID
  `chain_snapshots` run asks for undecided midday plans (one indexed query; nothing when none), which also covers "a
  look-ahead just closed" without a separate clock. The decision is still once per plan.
- The read route lives in `action_api.py` (it owns `VerificationService`), under the `/domain-work/actions/{id}/verification`
  path the pre-flight named; `domain_work_api.py` is untouched.
- The LATER_SHORT line wording is the builder's (the ruling fixed the state, not the sentence).
- `domain_summary` refuses a non-MINI domain Action with 409 `VERIFICATION_FAMILY_UNSUPPORTED`; it does not re-check the
  opportunity origin (origin-reader allowlist), since only an opportunity-origin Action can have a midday plan.

## Residual risk

- The stage evaluator runs in the tick with the wall clock (`datetime.now`) as `known_at`; `stages.py` is not in the
  stored-composer module set (clock guard passed). A stalled snapshot rebuild could let the look-ahead close before a late
  day's snapshot lands, giving LATER_SHORT; it runs after the drain to make that unlikely.
- No HTTP-level test of the new GET (service + client tested separately); the clone collect exercises the app only for the
  existing screens.

## User-review focus

- The "Target met" headline and the LATER_SHORT sentence (both new copy, R700).
- Whether every MINIGRID tick asking for undecided plans is acceptable vs. the narrower trigger.

## Fix round 1 (review ACCEPT, Lows L1-L5)

- L1: `assess` returns `threshold=None` for BASELINE_ZERO; the table shows "At least 10% above before" with no figure.
- L2: new `miss_texts`: on a MISS the shown after (rounded down) and needed (rounded up) gain places until after < needed
  (10.999 vs 11.000), compared as exact Decimals; the R7 line uses the same text. Cent figures kept when already distinct.
  VERIFIED needs no change (monotonic rounding never reads after < needed).
- L3: not-judged `days_before` is the live count of still-COMPLETE baseline days (`days_before_now`), the line's count.
- L4: `test_the_verification_get_over_http_200_404_and_422` (TestClient: 200 VERIFIED, 404 random Action, 404 unknown Site,
  422 bad id). A 409 (non-MINI Action) case is not covered here.
- L5: R700 row lists "No verification plan yet"; space restored in `operatorSiteRoutes.ts`.
- New L0 tests: boundary miss 10.999, far miss keeps cents, zero-baseline no threshold, not-judged count.
- Checks: L0 file 16 passed; Postgres files (`run-host-tests.ps1`, ch9b3 + reserve byte-equal) 9 passed; mill vitest 7 passed;
  `tsc --noEmit` clean; mock-deviation labels OK (157 files).
- Residual risks from review (not fixed): (1) later days chosen by grade at evaluation time, so a late-graded day +1 can be
  excluded for good (pins/site_today record it); (2) no deadline gate on the trigger, a tick can overrun by one small query
  plus a snapshot read; (3) outcomes are final, a later data revision never re-opens one, to be told to the client if a figure
  is corrected.
