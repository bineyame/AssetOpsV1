# OPS-01 slice review - backend test-suite turnaround

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/OPS-01-backend-test-speed`, HEAD `f5ebfb21`, diff against main `1c7595de`. Inputs: `tasks/OPS-01-backend-test-speed.md`, `.agent/OPS-01-review-packet.md`, `.agent/OPS-01-phase-1-handoff.md`, `.agent/OPS-01-phase-2-handoff.md`.

## Verdict

**ACCEPT.** No High or Medium findings. Three Low items and one Info item are listed below as carries. None needs a fix before merge.

This review includes the full run the packet lacked: one `-n 2` full suite on the final revision `f5ebfb21`, which also covers `b4fe2f24`.

## Checks run (by this reviewer, on `f5ebfb21`)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| Serial `--collect-only -q` (private base `assetops_ops01rv_test`) | 2129 node IDs |
| **Full suite**: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=...`, keep-awake running, 20-min cap, no other pytest process running | **2129 passed in 456.7 s (7.6 min)**, exit 0. JUnit: cases 2129, skipped 0, failed 0 |
| JUnit node IDs vs serial collection (exact, not UUID-normalised) | missing 0, extra 0 |
| `test_pg_harness.py` serially | 13 passed |
| `test_pg_harness.py` + `test_s1_foundation_postgres.py` + `test_s3_demo_configuration.py`, `-n 2 --dist loadfile` | 28 passed |
| `-n 2 --collect-only` with the URL set | 2129 collected; no database created |
| `test_s1_bindings_postgres.py` with `ASSETOPS_TEST_CLEANUP=truncate` (fallback path) | 16 passed |
| After every run: `pg_database` listing | no `assetops_ops01rv_pt*` database left. The private base was dropped at the end |

**Not verified by me:**

- Peak `pg_stat_activity` sessions for my run. My sampler process died with its parent shell and recorded nothing. The packet's 32-41 is unconfirmed by me, though my run had the same workers and modules.
- `-n 3`. I made no run.
- The crashed-worker path end to end. It is covered only by the `cleanup_run` unit test and by code reading.
- Concurrent full runs. They are not claimed.

## Focus answers

1. **Coverage honesty.** No test was removed, skipped, deselected or weakened. Every changed test file only moves the database reset into `pg_harness` and adds disposal. `START_FIRST` reorders whole modules on workers only; it deselects nothing. Exact ID equality between the collection and the JUnit report confirms that.
   - `test_s3_performance_cutover.py:258`: the two fixed UUIDs keep the test's meaning. The site is `FOREIGN-9`, and `FakeReads.run()` returns None for any id, so any UUID gives the same 404 path as before.
2. **DELETE-based `empty_tables()`.**
   - The emptied set is the recursive closure of referencing tables (`conrelid` where `confrelid` is in the closure, `contype='f'`). That is exactly the set `TRUNCATE ... CASCADE` reaches.
   - The proof test is not vacuous. It asserts that Postgres's own `truncate cascades to table` notices are non-empty and equal to the closure minus the roots. The implementer's mutation run also showed it failing when the recursion was removed.
   - Semantics:
     - Sequences: neither TRUNCATE (without `RESTART IDENTITY`) nor DELETE resets them.
     - Triggers: row triggers and RI triggers are off under `replica`. The only constraint trigger (`0011:316`, `DEFERRABLE INITIALLY DEFERRED`) is an AFTER INSERT trigger, so it is irrelevant to DELETE and disabled under replica anyway.
     - Trigger modes: no `ENABLE ALWAYS` or `ENABLE REPLICA` trigger exists, and there is no `ON TRUNCATE` trigger.
     - Statistics: no test reads planner or storage statistics (grep for `pg_stat_user`, `reltuples` and `EXPLAIN` found nothing).
     - Future migrations: the closure is computed at call time from `pg_constraint`, so new FK-referencing tables are included automatically. See L2 for the remaining edges.
3. **Isolation and lifecycle.**
   - Routing:
     - Workers route in `pytest_configure` from `workerinput`, before collection.
     - The controller routes nothing and only stashes the run id.
     - Names are length-checked.
     - `route()` refuses a non-`_test` base, and the unrouted path still hits `_guard` before `_reset_in_place`.
     - `--collect-only` and an unset URL provision nothing.
   - Template and cleanup:
     - The template build runs under a session advisory lock on the base database. Its "complete" marker is `datallowconn = false`, and a half-built template is rebuilt.
     - Workers drop only their own database. The controller's `cleanup_run` matches `^<stem>_pt<run>_..._test$` with the run id equal to its own, and it runs when any worker provisioned or reported nothing.
   - The orphan sweep skips any run that has a lease session (`application_name`) or a session on its databases. A lease exists before a run creates its first database. It never touches names outside the run-owned pattern.
4. **Connection ownership.**
   - Each process holds one NullPool admin connection.
   - Fixtures yield and dispose their engines. `gc.collect()` was kept.
   - The server allows `max_connections=100`. The packet's measured peaks (32-41) leave room for one run. There is no production pool change.
5. **Role guidance.**
   - `assetops-reviewer.md`, `assetops-implementer.md`, `ROLE_CONFIG.md` and `TESTING.md` match the packet's testing-guide contract: focused per phase, one full suite per slice on the final revision, reviewers cite same-revision evidence and rerun only for a finding (or for missing or other-revision evidence), keep-awake, a 2x cap, one at a time, and `check-all` kept separate.
   - The reviewer edit keeps the requirement to verify that the cited revision is the one under review, so review quality is not weakened.
   - Every file named in the `TESTING.md` area commands exists.
6. **Final revision run.** Done; see above. `b4fe2f24` is covered.

## Findings

- **L1 (Low, carry).** `backend/tests/pg_harness.py:88-101` and `conftest.py:107-117`. With `ASSETOPS_TEST_TEMPLATE=0` under `-n 2`, workers are unrouted and both would `_reset_in_place` the same database concurrently. `TESTING.md` says the fallback is serial-only, but nothing enforces it.
  - Why it matters: a misused escape hatch gives confusing failures, not data loss, because the database is still `_test`-guarded.
  - Fix: have `pytest_configure` call `pytest.exit` / `UsageError` when `TEMPLATE_SWITCH=0` and the run is an xdist worker or controller.
- **L2 (Low, carry).** `pg_harness.py:321-354`. The equivalence holds while every closure table is in `public` with a lowercase name; `_quote` asserts `[a-z0-9_]+` and `relname` drops the schema. A future table in another schema, a quoted mixed-case name, or an `ON TRUNCATE` / `ENABLE ALWAYS` trigger would break or diverge. The first two fail loudly; a trigger would diverge silently.
  - Fix: optionally select `oid::regclass` instead of `relname`. The packet already names the trigger caveat as residual risk.
- **L3 (Low, carry).** `test_pg_harness.py:139-164` creates fixed names `<stem>_ptdead0001_*` and `<stem>_pta11e0002_gw0_test` with no lease session. A concurrently starting run on the same base could sweep them mid-test and fail the test. This is not reachable under the one-at-a-time policy.
  - Fix: open the test's admin connection with `application_name=assetops-test-run:a11e0002` (and `dead0001` does not matter).
- **Info.** The packet's base (`52189ec7`) and the dispatch base (`1c7595de`) differ only by coordinator records (`7e218f9d`, `52189ec7`, including `.agent/next-work-2026-10-14n.json`, 11k lines). There is no code effect.

## Normal command: `-n 2` or `-n 3`

**Keep `-n 2` as the normal command.** It now has three clean full runs on this host (461 s and 506 s from the implementer, 457 s here), all with zero skips and exact ID parity. `-n 3` has one run (390 s, peak 41). Its approximately 70 s gain is modest against wider contention on the timing-sensitive S4 tick, health and drain cases on a disk-bound Docker Desktop. Revisit `-n 3` only after a second clean run and a peak-session check, as `TESTING.md` already says.

## Residual risk (beyond the packet)

- Only one reviewer full run was made, and its peak sessions were not captured by me.
- The timing-sensitive S4 cases were stable in three `-n 2` runs (and one `-n 3` run), but they have not been exercised under a disk stall with two workers.
