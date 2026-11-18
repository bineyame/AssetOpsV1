# FIX-COLD-DRAIN review packet

Task: [tasks/FIX-COLD-DRAIN-tick.md](../tasks/FIX-COLD-DRAIN-tick.md). Spec: plan2 `.agent/build-sheet-FIX-COLD-DRAIN.md` U1-U4
(Architect ruling (a) on DEMO-A CO-6). Branch `task/FIX-COLD-DRAIN-tick` from main `ce5df006c`. USER_REVIEW_REQUIRED: false
(no UI); merge needs a fresh review ACCEPT plus `-Tier all` (scheduling is shared plumbing).

Reviewer: `git diff main...HEAD -- ':!.agent'`.

## Outcome delivered

The scheduled tick now assesses and drains cold and EV work. Per Site, under the Site claim:
`s3 -> cold_assess -> ev_assess -> mini -> opportunity -> s4 -> consequence -> cold_consequence -> ev_consequence`.
On a real deployment or under `serve`, cold and EV days are assessed and their money settles: P1 shows the Portfolio day
is no longer money-pending after one tick.

## Files materially changed

- `backend/assetops_backend/scheduling/stages.py`: the stage children `cold_assess`, `ev_assess`, `cold_consequence` and
  `ev_consequence`, plus `DOMAIN_JOB_LEASE_SECONDS=300`, all registered in `STAGES`. The docstring now names them.
- `backend/assetops_backend/scheduling/tick.py`: the new `TickLimits` fields, their validation and the lease sum. `_site`
  wiring (claim re-check before each new child, first-failure retention, summed head counts). Module docstring order.
- `backend/assetops_backend/analytics/composition.py`: `build_cold_assessment_worker` and `build_ev_assessment_worker`
  now take a `**kw` passthrough (`clock`, `lease`); the defaults are unchanged.
- New tests: `backend/tests/test_fix_cold_drain_stage.py` (T1-T5) and `backend/tests/test_fix_cold_drain_tick_postgres.py` (P1-P4).
- Literal updates. Each one follows directly from the drain (coordinator-approved pre-flight list):
  - `test_w402_mini_stage.py`:
    - the FakeRunner gains 0-count OK defaults for the four new stages (its dict lookup would raise `KeyError`);
    - Site lease `600 -> 960`, in both the limits check and `("claim", 960)`;
    - the two call-order lists and the stage-marker list;
    - the `runner.calls[1] -> [3]` index;
    - lose-claim lists `MINI -> ["s3","cold_assess","ev_assess"]` and `S4 -> [..., "mini","opportunity"]`.
  - `test_w403_opportunity_stage.py`: the lease sum expression and `600 -> 960`; the two call-order lists, the marker list
    and `runner.calls[2] -> [4]`; the lose-claim list `["s3","mini"] -> ["s3","cold_assess","ev_assess","mini"]`.
  - `test_w402_mini_stage_postgres.py:146`: the call order.
  - `test_s4_schedule_health_postgres.py` `test_f3_a_lost_site_claim_stops_the_site_before_its_next_stage`: the scoped run
    found this one; my pre-flight grep missed it because it asserts a failure tuple. The claim stolen during `s3` is now
    found at the re-checked `S3` claim before `cold_assess`: `("MINI", "CLAIM_LOST") -> ("S3", "CLAIM_LOST")`.
    Its call list `["discover", "s3"]` is unchanged. Commit `06189ef67`.
- Records: register R623 (D3, resolved) and R624 (D5, open) in `.agent/mock-departure-register.md`; `.ai/CODE_STATE.md`;
  `.ai/ACTIVE_CONTEXT.md`; the task file.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| U1 four stage children, worker semantics unchanged, `consequence` shape | met | `stages.py` `_domain_assess`, `_domain_consequence`; workers unedited |
| U1 `analytic_id` literal pre-flight | met | cold selection writes `assessment.analytic_id` (`cold-excursion`, `cold-start-response`; `postgres_assessment_store.py:1310-1320`); EV `ev-session/1` |
| U2 limits, validation, lease sum | met | T2 |
| U2 order, claim re-check, first failure, later children run | met | T1, T3, T4 |
| U2 summed `record_s3` / `record_consequence` | met | T5, P1 (head = stage sums), P4 |
| P1 cold: job DONE, every work SUCCEEDED, excursion revision, Portfolio not pending, tick 2 no change | met | `test_p1_...` |
| P2 EV: assess then drain in one tick; guard not PENDING_RECOMPUTE/STALE_BASIS; head exists | met | `test_p2_...` (head ESTIMATED / ELIGIBLE_COMPLETE_INTERVALS) |
| P3 retry (ruling (b)): tick 1 OK, `failed==1`, one FAILED attempt; early tick no attempt, `deferred==1`; once due, success | met | `test_p3_...`; also shows the P1 read can say PENDING (non-vacuity) |
| P4 mini-only Site unchanged apart from four 0-count OK keys | met (interpreted) | `test_p4_...`; see Known deviations 1 |
| U4 records | met | R623, R624, CODE_STATE, ACTIVE_CONTEXT |

## Checks run

- Pure tests: `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py` and `test_w403_opportunity_stage.py`, run as
  separate commands: 19 passed and 19 passed.
- Postgres on the host (`assetops_test`, in-process runner): `test_fix_cold_drain_tick_postgres.py` 4 passed in 364 s.
- **Scoped selector set** (`tools/select-tests.py --base main`, 177 of 293 files):
  - Command: `tools
un-backend-suite-in-container.ps1 -Tier fast -Targets '<selected>'`, run `20261031-165013-79278c` on
    revision `418e9bf7a`, 4 workers, `postgres-test`.
  - **Result: exit 124 (HANG).** pytest passed the derived 60-minute cap with 2032 of 2039 collected tests run: 2031
    passed and 1 failed.
    - The 1 failure was `test_s4_schedule_health_postgres.py::...::test_f3_a_lost_site_claim_stops_the_site_before_its_next_stage`,
      a literal that follows from the drain, fixed in `06189ef67`.
    - The 7 tests left unrun were all in `test_w601e_operational_index.py`.
  - check-all ran on the same machine for part of this window (its estate guard self-tests alone took 12.5 min), so the
    machine was not idle.
- Rerun, focused, after the fix: `test_s4_schedule_health_postgres.py::TestPhase1ReviewCarries` plus
  `test_w601e_operational_index.py`, 15 passed (195 s).
- `tools\check-all.ps1 -Python <plan2 .venv>`: All 11 guards passed (architecture seams, agent workflow, estate guard
  self-tests, navigation truthfulness and the rest).
- Not run:
  - A clean scoped rerun: the full `-Tier all` run below supersedes it.
  - The frontend suite: there is no frontend change.

- Review fold-in (review ACCEPT, plan2 `.agent/FIX-COLD-DRAIN-review.md`):
  - L1: P4 now asserts `site.result == "COMPLETED" and site.failure is None`.
  - L2: the long lines are wrapped, and the `stages.py` usage docstring is fixed.
  - Rerun of the three stage files and the P-file: 42 passed (254 s).
- check-all rerun on an idle machine (no `ops03` container, before the full run), revision `185485221`:
  - All 11 guards passed, including Architecture seams (rule 8, the statement-level writer guard), with no missing
    consequence INSERTs.
  - The reviewer's rule-8 failures were under load, so they look like load flakiness rather than a defect in this slice.
- **Full backend `-Tier all`**:
  - Command: `toolsun-backend-suite-in-container.ps1 -Tier all`, run `20261031-191430-4386b3`, revision `185485221`,
    4 workers, `postgres-test`, derived 2x cap.
  - Wall time: 3339 s (pytest 3336 s, 55:36). Exit 0.
  - JUnit: tests 4591, failures 0, errors 0, skipped 0, so zero skips.
  - No failure of the reviewer's residual-risk pattern (a tick test expecting COMPLETED on a shared DB whose schema is
    behind) appeared.
  - It also covers the 7 `test_w601e` tests the capped scoped run left unrun.

## Known deviations

1. **P4 "byte-identical".** There is no baseline to compare against, because the old tick can't run inside the same test.
   Interpreted as the coordinator accepted:
   - the four new keys are present, each a 0-count `OK` with empty outcomes;
   - the head's `s3_processed`/`s3_deferred` and `consequence_processed`/`consequence_deferred` equal the `s3` and
     `consequence` stage counts alone;
   - the mini stage processes 10;
   - the head returns to IDLE with no claim token.
2. **Item failures (Architect Q1, ruling (b)).** A failed cold or EV consequence item keeps the drain stage `OK` (`failed`
   counted) and retries under the worker's `retry_due_at`, with no Site back-off. A Site failure `COLD_CONSEQUENCE` /
   `EV_CONSEQUENCE` arises only from a non-OK drain code (`FAILED`, `TIMEOUT`, `CONSEQUENCE_CLAIMED`), proven in T3.
3. **Head counts when a whole group fails.** If every child of a group failed (e.g. all of `s3`, `cold_assess` and
   `ev_assess`), no head count is written, so the earlier counts stand. This keeps the old behaviour for a failed `s3`.
   One small change follows: when `s3` fails but a cold/EV child is OK, the head now records the OK children's counts.

## Residual risk

- **Child processes.** Each visited Site now starts four more killable child processes (Python start-up plus imports,
  about 1-3 s each on this host). In a deployment with `tick_seconds=240` and `max_sites=20`, fewer Sites may be visited
  per tick, and the rest stay DEFERRED to the fair cursor. The tests use the in-process runner, so they don't measure this.
- **R624 (open).** An excluded-lifecycle Site whose only work is cold or EV is not discovered, and `health.py` shows no
  per-domain cold/EV counts.
- **Leftover rows.** Ticks in other Postgres tests now also work any leftover cold/EV rows of Sites in the shared test DB.
  This is bounded by `domain_jobs_per_site` and the consequence item limit.

## User-review focus

None (non-UI). Reviewer focus:
- `_site`'s re-check-before-child, and where the head counts are recorded;
- P3 against ruling (b);
- the P4 interpretation.
