# W3-02 0b review: W1 day source, connection-taking

Reviewer: fresh Claude reviewer (did not author). Date 2026-10-21.
Reviewed: commit `d208faef` (code and tests) and handoff `724c0832`, read through git objects only. Nothing was run in `AssetOpsV1-review2`.
Authority: `main:.agent/W3-02-build-spec.md`, closure 4 (the "W1 day source" first paragraph and the `0b` row), closure 5, and the body lines it keeps in force (26, 28, 45, 151, 153).

## Verdict: REVISE

The core work is sound. Both signatures match the spec. Neither function opens or commits a transaction. `read()` is unchanged, the day reduction is correct, and the cutoff checks are correct. Three Medium findings block acceptance. M1 and M2 are mechanical fixes. M3 needs an Architect ruling, or an explicit deferral to commit 1.

## Checks run

These ran in a throwaway detached worktree of `d208faef` under my scratchpad. `PYTHONPATH` pointed at that worktree's `backend` and `contracts`, because the venv's editable install resolves to the main checkout. The base was `assetops_test`, with harness run-owned clones. The worktree has since been removed.

- Focused tests: `test_w302_w1_day_reduction.py`, `test_w302_w1_claim_limit_on_postgres.py`, `test_s3_claim_limit_postgres.py`, `test_s3_claim_limit_vocabulary.py` and `test_w301_w1_snapshot_helpers_postgres.py`. Result: **32 passed, 0 skipped, 51 s.**
- Trap mutation 1: `claim_limit_snapshot_on` calls the public `revision_detail()`, which goes through `_snapshot`. Result: **2 failed, 1 passed.** The trap catches this. The third test passes `revision_id=None`, so it never reaches the detail call.
- Trap mutation 2: `claim_limit_snapshot_on` calls `self._run(lambda c2: self._revision_detail(c2, ...))`, a second connection and transaction. Result: **3 passed.** The trap misses this (see M1).
- Not run: `tools/check-architecture.ps1`, `check-agent-workflow.ps1` and `check-all.ps1`. I was not to run anything in the review2 worktree, so the handoff's "11/11 guards" is unverified. I also did not run the S3 dispatch read and assessment files the handoff cites. No full suite run is due for this commit.

## Contract checks

- **Signatures.** Both are as specified: `ClaimLimitReadService.claim_limit_on(c, tenant_id, site_id, day, revision_id, known_at)` and `PostgresAssessmentStore.claim_limit_snapshot_on(c, tenant_id, site_id, day, revision_id, known_at)`.
- **No own transaction.** Both functions use only `c`, through `select_dispatch_days_on`, `_transaction_time` (`SELECT now()`) and `_revision_detail`. Neither calls `read()` or `claim_limit_snapshot()`, and neither commits.
- **`read()` unchanged.** The diff only appends: a Protocol method, new methods and module functions. `test_s3_claim_limit_postgres` passes.
- **Day reduction.**
  - State precedence is CONTRADICTORY, then UNKNOWN, then all-FULL gives FULL, then any NONE gives NONE, else LIMITED.
  - Zero intervals, or an unavailable day, gives UNKNOWN.
  - A single ceiling needs every interval to have one identical `(ceiling, statement)`, a current positive claim, and a Candidate or Necessary ceiling. Otherwise `current_ceiling` is null and each interval ceiling stays in `interval_ceilings`.
  - The row cites the sorted union of interval revision IDs. The window revision is kept apart.
  - Gaps keep only the admitted codes that have a concrete `role`, grouped by `(domain, gap_code, missing_role)`. Role-less window reasons never become gaps.
- **Cutoff.** The at-cutoff selection comes from the reviewed W3-01 helper. A revision, interval or run recorded after `known_at`, or cited Evidence accepted after it, gives `available=False` with `HISTORICAL_SELECTION_UNAVAILABLE` and no ceiling. The model and lineage refusals mirror `read()`, and the interval cited-ID lineage check is stricter than `read()`'s.

## Findings

**M1 (Medium, missing test strength). The no-second-transaction trap only covers `_snapshot`.**
- Where: `backend/tests/test_w302_w1_claim_limit_on_postgres.py:45-51`.
- What is wrong: the trap patches only `PostgresAssessmentStore._snapshot`. The store has other transaction entry points: `_run` (lines 228-240, used by many public reads) and `_connect_engine().begin()` (line 931). Mutation 2 above opened a second transaction through `_run`, and all 3 tests still passed. The closing `assert c.in_transaction()` does not catch a mid-read commit either, because the next `execute` auto-begins a new transaction.
- Fix: in `reads`, also patch `_connect_engine` to raise (the test store never needs its own engine), or assert `owned._engine is None` at the end. Optionally record `txid_current()` on `c` before and after the read and assert the two are equal. The code itself is correct today. This finding is about the gate the `0b` row names.

**M2 (Medium, correctness, unrequested scope). The single-INTERVAL `revision_id` mode reports a current reused interval as HISTORICAL.**
- Where: `backend/assetops_backend/analytics/claim_limit_read.py:409-436`.
- What is wrong:
  - `run` is `revision["run"]`, the revision's creating `analytic_run_id`.
  - `selected_here` requires the selected run to be that creating run (line 432).
  - `_persist` reuses an interval revision whose basis is unchanged (`rev_id = latest[0]`), and that revision keeps its old run. So when a later selected run links that same interval revision, interval mode returns HISTORICAL and UNKNOWN. The revision is in fact in the current selection.
  - Its accepted set also comes from the old run.
- Why it matters: `read()` decides currentness by membership alone, so the two disagree. The window-revision mode is unaffected, because a window basis includes `input_sha256` and is therefore 1:1 with its run. This is the mode Lane B uses.
- Fix (mechanical): drop interval mode, refusing a non-window `revision_id` with 422. Or decide membership against the selected run's revisions and use the selected run's evidence. Add a reuse test.

**M3 (Medium, acceptance; needs the Architect). A selection at an old explicit cutoff still carries a current claim.**
- Where: spec closure 4 says "Historical selection keeps IDs but no current claim". Body line 26 says "explicit old cutoff HISTORICAL … Historical rows retain exact IDs without current claims". Line 151 maps HISTORICAL to `readiness:UNKNOWN`.
- What is wrong: at a past `known_at` whose at-cutoff status is CURRENT, `reduce_day` returns FULL or LIMITED, can set `current_ceiling` with `ceiling_source: W1_CLAIM_LIMIT`, and emits gaps. The F06 test asserts `LIMITED` at the earlier cutoff.
- Handoff reading 3 discharges that sentence only for revisions that are outside the at-cutoff selection.
- Fix: one of two options, and choosing between them is the ruling needed.
  - Option A: `claim_limit_on` compares `known_at` with the transaction time (as `select_dispatch_days_on` already does), marks old-cutoff intervals HISTORICAL, nulls the current values, and keeps the IDs and `historical_ceiling`.
  - Option B: the Architect rules that commit 1 nulls current claims for historical mode, and records that `reduce_day` output is "as of cutoff", not "current".

**Low (non-blocking)**
- **L1. Non-selected intervals feed CONTRADICTORY and gaps.**
  - `interval_state` returns CONTRADICTORY even for a HISTORICAL interval (line 474). `reduce_day` also takes gaps from non-selected (HISTORICAL) intervals (lines 505-508).
  - Spec lines 28 and 151 say "selected" CONTRADICTORY and gaps come from "selected" reasons.
  - This is unreachable on the estate path, which always passes the day's window revision. Gate both on CURRENT or selected currentness.
- **L2. Gap and body domain is `"dispatch"`.** The W3-01 wire value is `mini_grid` (spec line 400). Commit 1 must map it, or `0b` should emit the wire value. Mechanical.
- **L3. A CONTRADICTORY day can keep a ceiling.** A day can be CONTRADICTORY and still carry a `current_ceiling`, when the conflict lies outside the claim-carrying segments. Note this for the Architect: the "Conflicting records" row display may need to suppress it.
- **L4. Weak assertions.** Test line 98 guards the single-ceiling assertion with `if r["current_ceiling"] is not None` (it may assert nothing). Line 165 accepts `UNKNOWN or CONTRADICTORY`. The gap-equality assertion recomputes the same filter. These are non-vacuous overall, but each can be tightened to exact values.
- **L5. Refusals raise instead of returning UNKNOWN.** The 404, 422 and 409 refusals are raised, not mapped. Closure 4 wants reconstruction failure to be UNKNOWN with `HISTORICAL_SELECTION_UNAVAILABLE`. Commit 1 must catch `ClaimLimitRefusal`, or the estate read fails. Record this in the commit-1 handoff.

## Handoff readings

| # | Reading | Class |
| --- | --- | --- |
| 1 | `revision_id` is the window revision (all its INTERVAL revisions projected) or one interval | Window mode: **mechanical**, and the correct reading for Lane B. Interval mode: unrequested and defective (M2), **mechanical** to drop or fix |
| 2a | Any non-CURRENT interval is UNKNOWN | **Mechanical** (spec literal, line 151) |
| 2b | A role-tagged CONFLICTING reason gives CONTRADICTORY, even when not CURRENT | **Architect.** W1 has no CONTRADICTORY source state, so deriving one from any conflicted span (which then wins the whole day) is a semantic choice. "Even when not CURRENT" conflicts with "selected CONTRADICTORY" (L1) |
| 3 | A revision outside the at-cutoff selection is HISTORICAL rather than refused | **Mechanical** (it matches `read()`). Using it to discharge "Historical selection keeps IDs but no current claim" is **Architect** (M3) |
| 4 | Window reasons are separate and never gaps; gap domain is `"dispatch"` | Exclusion: **mechanical**. Domain value: **mechanical** mapping (L2) |
| 5 | NOT_EVALUATED spans become `GENERATOR_UNOBSERVED` with each span's role | **Architect** (non-blocking). One unobserved generator yields up to five separate "Generator state not observed" gap groups (one per role). Whether to collapse them to `generator_state` is a product call |
| 6 | Row key `GENERATOR_SUPPORT@YYYY-MM-DD` and placeholders are left to commit 1 | **Mechanical** (the `0b` row scopes this commit to projection and reduction) |

## Residual risk

- The guards are unverified by me.
- The S3 dispatch read and assessment files were not rerun.
- M2's reuse path has no fixture. I established it by reading `_persist` and `_revision_detail`.
