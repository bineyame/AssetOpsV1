# S4-06 review - equal-start future price succession

Reviewer: fresh independent Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review2`, branch
`task/S4-06-price-succession` at `7f7039cb`; diff `7c72c6b3..7f7039cb` (code commit `16fd46e3`, closeout docs-only).
Judged against `tasks/S4-06-price-succession.md` (incl. coordinator note), Architect S4-02 Q1, plan review S4-06
section (L1/L2 carries) and registry node `I-price-equal-start-succession`.

## Verdict

**ACCEPT.** No High or Medium findings. Merge precondition (not a finding against the code): the same-revision
real-Postgres full suite owed by the packet must complete on a quiet machine before merge.

## What was checked

Code (`backend/assetops_backend/financials/assumptions.py` `plan_assignments`, SUCCESSION branch):

- Equality admitted only for the sole open-ended overlap: `len(hit) != 1 or only.valid_to is not None or not
  only.valid_from <= valid_from` still refuses bounded and multiple overlap with `SUCCESSION_OVERLAP_NOT_PERMITTED`;
  `valid_from < recorded_at` still refuses with `SUCCESSION_NOT_FUTURE` before the overlap test, so an equal-start
  replacement is always of a future (scheduled) assignment, never a backdated rewrite.
- At equality the plan is `close=(only.id,)`, `insert=(own,)`: no left remainder, so no `[t, t)` row (which the
  0010 `valid_range` CHECK would refuse anyway). Later-start branch unchanged byte-for-byte apart from the message.
  INITIAL and CORRECTION branches untouched.
- Writer (`postgres_assumption_store.publish`) unchanged: advisory xact lock, idempotency before prior check,
  DB `clock_timestamp()` after the lock, close-then-insert at one `at`. Closing first satisfies the 0010 set-once
  `recorded_to` trigger (later than the latest `recorded_from`), and `[recorded_from, recorded_to)` half-open ranges
  mean the GiST exclusion sees no overlap between the closed old row (`recorded_to = at`) and the new row
  (`recorded_from = at`). Rule-8 ownership untouched (no new write form; no guard change).
- Migration 0011 `financial_consequence_dirty_on_assumption` fires AFTER INSERT on the revision table, independent of
  the assignment plan, and for SUCCESSION enqueues `[valid_from, NULL)`: the equal-start replacement dirties exactly
  the replaced span. Verified by inspection; no test asserts the work row for the equal-start case (residual, below).
- Datetime equality: both sides are tz-aware with microsecond precision (Postgres `timestamptz` round-trips
  microseconds), so `==` is exact.

Tests (`TestPlan` 3 new; `TestEqualStartSuccession` 5 new): cover acceptance 1-3 and both plan-review carries.
Read for teeth rather than counted: the boundary test asserts both recorded bounds of the closed row against the
succession's `recorded_at`, IDs and values at `recorded_at - 1us` / `recorded_at` / `+1 day`, and row counts after
retry, key reuse and stale prior; the race uses a barrier with two independent stores; bounded and two-overlap
refusals check counts unchanged; the CORRECTION-tail case (L2) checks the replaced row cites v1 while the head is v2
and the final shape is v1/v2/v3 with 5 rows; the earlier-price case (L1) is non-vacuous (separate earlier revision,
inside/touching/crossing/after windows, pre-publication cutoff). The packet's three mutations (`<=`->`<`, equality
branch removed, store prior check removed) cover the load-bearing lines; I had no doubt sufficient to spend another.

## Checks run (this review)

- Interpreter `AssetOpsV1\.venv`, `assetops_backend.__file__` = `AssetOpsV1-review2\backend\assetops_backend\__init__.py`.
  Private base `assetops_s406rev_test` (created, dropped afterwards; no run DBs left).
- `pytest test_s4_assumption_publication.py test_s4_assumptions_postgres.py`: **56 passed** (16.5 s).
- `pytest test_s4_fuel_cost.py test_s4_consequence_recompute_postgres.py test_s4_consequence_store_postgres.py`:
  **63 passed** (102 s).
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `tools/check-all.ps1`: 8/9 passed; **Screen ledger FAIL: missing tool `AssetOpsV1-review2\.venv\Scripts\python.exe`**
  - environmental (this worktree has no `.venv`); the slice touches no screen/frontend file. Not verified here; the
  implementer reports 9/9 in their tree.
- Full backend suite: not run (per dispatch). The packet honestly records its run on `16fd46e3` as **not completed**
  (stopped at the 20-minute cap at 53%, no JUnit). No same-revision full-suite evidence exists.
- Frontend: not applicable (no frontend change).

## Findings

None at High or Medium.

- **Low L1 (process, merge precondition)** - `.agent/S4-06-review-packet.md` "Checks run": same-revision full-suite
  evidence is missing. Run the task's full command on `16fd46e3` (or the merge revision) on a quiet machine with JUnit
  zero skipped/failed before merging, and cite it. The packet already states this; repeated so it is not lost.

## Residual risk not named by the packet

- No test asserts that an equal-start SUCCESSION writes a `financial_consequence_work` row with
  `affected_from = start, affected_to = NULL`. The trigger is change-kind keyed on the revision insert and is
  unchanged, so the risk is low; worth one assertion if this area is next touched.
- The new conflict message text changed ("shorten or replace"); nothing asserts it, and codes are unchanged, so no
  client contract moved.
