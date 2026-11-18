# FIX-COLD-DRAIN review

Reviewer: fresh Claude Reviewer, not the author. Branch `task/FIX-COLD-DRAIN-tick`, head `a91da360a`, base `ce5df006c`.
I reviewed from a `git archive a91da360a` snapshot and did not edit the worktree. Spec: plan2
`.agent/build-sheet-FIX-COLD-DRAIN.md`, including the P3 ruling (b). Packet: `.agent/FIX-COLD-DRAIN-packet.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The three Low findings are optional polish and do not block the merge. The merge
is still gated, as the sheet says, on the full backend `-Tier all` run, the frontend suite and check-all.

## What I verified

- **Tick order and fencing** (`scheduling/tick.py:331-413`).
  - The order is s3, cold_assess, ev_assess, mini, opportunity, s4, consequence, cold_consequence, ev_consequence.
  - `stage("S3")` is re-checked before each assessment child (`:344`) and `stage("CONSEQUENCE")` before each drain
    (`:403`). The existing markers are reused, so the 0030 CHECK is untouched.
  - A lost claim returns before the next child, writes no counts and does not release, as F3 requires.
- **Children** (`scheduling/stages.py:207-292`).
  - Each new child is a `STAGES` entry, so `StageRunner` starts it as a killable subprocess with `PGOPTIONS`.
  - `TestTickCost::test_measure_a_real_child_tick_over_one_and_four_sites` uses the real `StageRunner`, so all four
    new children ran as real subprocesses there. I also ran `cold_assess` and `ev_assess` by hand as subprocesses with
    `PGOPTIONS`; both returned `STAGE_RESULT {"code": "OK", ...}`.
  - First failure is kept with `failure = failure or (...)` and later children still run. This matches the
    MINI/OPPORTUNITY rule.
  - The workers are unedited: the diff has no changes in `financials/` or `analytics/assessment_worker.py`.
  - The `analytics/composition.py` `**kw` passthrough keeps the defaults. T2 checks that both workers' default lease
    is still 300 s.
- **Head-count summing.**
  - A non-OK child adds 0, and a group whose every child failed writes nothing (`recorded` flag, `:337/:354`,
    `:396/:413`). T5 covers all three cases.
  - Known deviation 3 (s3 FAILED but a cold/EV child OK, so the head records only the OK children's counts) follows
    the sheet's "non-OK adds 0". No reader in `health.py` or the frontend uses these columns; the only reader is
    `site_head`.
- **Limits and lease maths.**
  - The defaults give 120+120+120+120+60 + 2·120 + 2·60 + 60 = 960.
  - `0 < domain_assess_seconds < DOMAIN_JOB_LEASE_SECONDS (300)` is enforced. The two new bounds are part of the
    statement-timeout check, and `domain_jobs_per_site` is part of the `< 1` check.
  - `tick_lease_seconds` picks up the new Site lease.
- **Ruling (b).**
  - A failed item leaves the drain stage OK with `failed` counted, and no Site failure is raised (P3 asserts
    `first.failure is None`).
  - A Site failure `COLD_CONSEQUENCE`/`EV_CONSEQUENCE` comes only from a non-OK code (T3: FAILED, TIMEOUT,
    CONSEQUENCE_CLAIMED, on each of the four children).
- **Tests.**
  - P1: tick 1 leaves the job DONE, every work item SUCCEEDED and an excursion revision. The spied `money_pending`
    verdicts are all false and the Portfolio status is not PENDING. Tick 2 adds zero attempts, revisions, runs and
    assessments.
  - P3 shows the same read can say PENDING, so P1 is not vacuous. It also proves `deferred == 1` before
    `retry_due_at` and success at attempt 2 once due.
  - P2: assess-then-drain in one tick, the guard is not PENDING_RECOMPUTE/STALE_BASIS, and the head is
    ESTIMATED / ELIGIBLE_COMPLETE_INTERVALS.
  - P4: the interpretation is acceptable, since a pre-change baseline cannot run in the same test. See L1.
- **F3 literal** (`test_s4_schedule_health_postgres.py:109`).
  - `("MINI","CLAIM_LOST") -> ("S3","CLAIM_LOST")` is a correct consequence of the drain. The claim stolen during
    `s3` is now caught by the new re-check before `cold_assess`, which uses the existing `S3` marker.
  - The safety property is still asserted unchanged: the call list is exactly `["discover","s3"]`, and the thief
    holds the claim. So the change hides no regression. The record_s3 write it skips would have been fenced out by the
    token anyway.
- **Other literal changes** (w402, w402 postgres, w403). Each change is an order list, the 960 lease, or a shifted
    index, and follows directly from the new children.
- **Register.** R623 (D3, resolved) and R624 (D5, open; excluded-lifecycle cold/EV-only Site, and per-domain health
  counts) are present and match the sheet's U4. The sheet's "R620 if still free" is satisfied by taking the next free
  ID.
- **Planted breaks.** Both were caught.
  - Dropping `ev_consequence` from the drain loop: 15 failures in `test_fix_cold_drain_stage.py` (T1, T3, T4[9], T5).
  - Replacing the claim re-check before the drains with `if False:`: 5 failures (T1, T4[8], T4[9], the w402 order
    test and the w403 order test).

## Findings

**L1 (Low, test strength).** At `backend/tests/test_fix_cold_drain_tick_postgres.py:214`, P4 asserts
`site.failure is None or site.failure[0] not in {COLD_*, EV_*}`. On a healthy mini-only Site, that would still pass
if `s3`, `mini`, `opportunity`, `s4` or `consequence` started failing, which is the regression the "byte-identical"
check is meant to catch. Fix: assert `site.failure is None and site.result == "COMPLETED"`, if the fixture allows it.
This is a preference, not an acceptance gap.

**L2 (Low, cosmetic).** Some lines run past the module's 120-column style.
- `test_w402_mini_stage.py:112,127` and `test_w403_opportunity_stage.py:42,56` are 141-column order lists.
- The `stages.py:3` usage docstring has a run of stray spaces (`stages         discover|...`).

No lint config enforces line length (I found none), so nothing fails.

**L3 (Low, residual).** The 60 s Site-lease slack is unchanged. Each visit now also makes four more `set_stage` calls
and two more `db_now` round trips. These are milliseconds against 60 s, so it is acceptable, but the slack is now
shared by nine children instead of five.

## Checks run (my own results)

- Pure tests: `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py` and `test_w403_opportunity_stage.py`, 38
  passed in 5.1 s.
- Postgres tests (`assetops_test`, plan2 venv, snapshot PYTHONPATH): `test_fix_cold_drain_tick_postgres.py`,
  `test_w402_mini_stage_postgres.py` and `test_s4_schedule_health_postgres.py`, **18 passed** in 1481 s.
  - P1 66 s, P2 78 s, P3 61 s, P4 140 s.
  - The machine was loaded by the other lane's `-Tier all` run.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-architecture.ps1`: **FAILED for me**, on both the snapshot and the worktree. Rule 8 (in
  `tools/checks/configuration-persistence.ps1`) reported "found no INSERT INTO cold_/ev_consequence_*" in
  `financials/adapters/postgres_consequence_store.py`.
  - The INSERTs are present: grep finds them at `:966`, `:983` and `:1076`.
  - Neither that file nor the check changed in this diff.
  - The set of missing tables varied between runs: 4, then 6, then 6.

  I read this as a load-dependent or environmental guard problem that predates the slice, not a defect in it. It is
  still unverified by me. The packet's "check-all 11/11" should be re-confirmed on an idle machine before the merge.

## Not verified

- Full backend `-Tier all`. It is still pending, as the packet says, and it is a merge gate.
- The packet's scoped run (exit 124 at the 60-minute cap, 7 tests in `test_w601e` never ran) was on `418e9bf7a`, not
  the head. The F3 fix after it was rerun only in a focused run.
- The frontend suite. There is no frontend change.
- The `cold_consequence`/`ev_consequence` children run by hand as subprocesses. The shared `assetops_test` DB was at
  `0009_finding_store` with no consequence tables when I tried, so something else is resetting it to an older head
  concurrently. Their subprocess path is covered by `TestTickCost`, which passed.

## Residual risk (beyond the packet)

- **Shared test DB.** `assetops_test` is being re-migrated by something outside this review; I saw `0009` with 31
  tables mid-session.
  - Any tick test that runs on a partially migrated schema now runs `cold_consequence`/`ev_consequence` against
    missing tables. Those children return UNAVAILABLE, and the Site becomes FAILED with `COLD_CONSEQUENCE`.
  - A test that asserts `COMPLETED`, or `failure is None`, on such a schema would now fail. Before this slice it
    passed, because mini-only stages never touched cold or EV tables.
  - The scoped 177-file run found only F3, so no such test is known. Watch `-Tier all` for this pattern rather than
    treating it as flake.
- **Leftover rows.** The packet's leftover-rows risk is real but bounded: each replay resets its DB, and the
  per-Site limits cap the work.
- **EV idempotency.** P2 has no second-tick check for EV; only cold (P1) is checked. The worker's replay semantics are
  unchanged, so the risk is low.
