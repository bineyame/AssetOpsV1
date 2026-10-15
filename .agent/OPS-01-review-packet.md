# OPS-01 review packet - backend test-suite turnaround

## Task

`tasks/OPS-01-backend-test-speed.md` (Status `in_review`). Branch `task/OPS-01-backend-test-speed`, base main `52189ec7`. Slice diff: `git diff 52189ec7..HEAD`; phase 2 alone: `git diff af7c48d2..HEAD`. USER_REVIEW_REQUIRED: false; independent review required. Detail: `.agent/OPS-01-phase-1-handoff.md`, `.agent/OPS-01-phase-2-handoff.md`.

## Outcome delivered

The full real-Postgres backend suite now takes about 8 minutes, down from 41-80. The normal command is `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder`, which ran in 7.7 and 8.4 min. The serial template path takes 30.8 min, and the pre-OPS-01 harness took 41.4-80.3 min. No test was dropped, skipped or retried. Every module still starts on a fresh, migrated database: the harness migrates a template once per run and clones it per module. Per-test cleanup uses DELETE over the TRUNCATE CASCADE closure. Each xdist worker has its own database. One full suite runs at a time, documented in `backend/TESTING.md`.

## Files materially changed

- `backend/tests/pg_harness.py` (new): routing, template, clone, sweep, cleanup, `cleanup_run`, `empty_tables`, `dispose`.
- `backend/tests/conftest.py`: routing (serial, xdist controller and worker), worker basetemp early return, `START_FIRST` ordering, session cleanup.
- `backend/tests/test_pg_harness.py` (new): 10 pure tests and 3 Postgres tests.
- `backend/tests/test_s1_foundation_postgres.py`, `test_s1_bindings_postgres.py`, `test_s4_finding_store_postgres.py`, `test_s2_gateway_access_postgres.py`, `test_s3_demo_configuration.py`: engine and store fixtures use the harness, then yield and dispose (phase 1).
- `backend/tests/test_s3_performance_cutover.py:258`: fixed UUIDs so the node IDs are deterministic.
- `backend/pyproject.toml`: `pytest-xdist==3.8.0`.
- `backend/TESTING.md` (new) and the link from `backend/README-db.md`.
- `tools/keep-awake-during-tests.ps1`.
- Role guidance:
  - `.claude/agents/assetops-reviewer.md` and `.claude/agents/assetops-implementer.md`.
  - `.ai/ROLE_CONFIG.md`.
- Records:
  - `.ai/ACTIVE_CONTEXT.md` and `.ai/CODE_STATE.md`.
  - `tasks/README.md`.

## Acceptance criteria and carries

| Item | Status |
| --- | --- |
| Substantial wall-time reduction on this host | Met. Two `-n 2` runs took 7.7 and 8.4 min, against the phase-1 serial run of 30.8 min and the old-code runs of 41.4 and 80.3 min. The parallel runs were not back-to-back with a serial run; see the deviations. |
| No dropped, skipped, weakened or selected tests | Met. Collection matches serial exactly: 2128 node IDs, with 0 missing and 0 extra in every parallel JUnit. No IDs were removed relative to the baseline (UUID-normalised). The added IDs are all in `test_pg_harness.py`. |
| Migration, process, concurrency and advisory-lock coverage preserved | Met. These tests are unchanged and passed in all three runs. Module-scope fixtures stay on one worker under loadfile. |
| Phase 1 (template clone, guide, baseline) | Met; see the phase-1 handoff. |
| Phase 2: xdist routing, loadfile, connection budget, normal command | Met. Peak sessions were 35 and 32 at `-n 2` and 41 at `-n 3`, against `max_connections` of 100. |
| Phase 2: role edits and Codex prompt check | Met. No current Codex prompt template hard-codes a full suite. |
| Two parallel runs; serial-vs-parallel node and outcome diff; zero DB skips from JUnit | Met. All 2128 passed in each run, 0 skipped and 0 failed. |
| Concurrent full runs | Not attempted. The one-at-a-time policy is documented instead. |
| M2: route before collection, run id via `workerinput`, names of 63 characters or fewer, `_test` guard, lazy provisioning, run-owned drops, orphan sweep | Met. Workers route in `pytest_configure`. `--collect-only`, unit-only and unset-URL runs create nothing. |
| M3: disposal before re-clone, no pool cap, `gc.collect()` kept | Met. Inline stores are still disposed only by GC; see the residual risks. |
| M4: exact coverage | Met. The per-node phase-1 JUnit files were not kept; that serial run passed every test (see the deviations). |
| M5: back-to-back A/B | Met in phase 1: 30.8 vs 41.4 min. Phase 2 has no back-to-back serial run. |
| M8: loadfile, flake inventory, no retries | Met. There were no flakes in the three parallel runs. The policy for a future flake is written in TESTING.md. |
| L1-L6 | Met. xdist is pinned and installed. Workers take `<controller basetemp>/<gwN>` and return early. The controller's basetemp fallback runs unchanged before xdist spawns its workers. |

## Checks run

- Full-suite runs, each with keep-awake and a cap:

  | Run | Workers | Wall | Result |
  | --- | --- | --- | --- |
  | p2a | `-n 2` | 461 s | 2128 passed |
  | p2b | `-n 2` | 506 s | 2128 passed |
  | p3a | `-n 3` | 390 s | 2128 passed |

  - All three ran on code equal to `b695552e`.
  - JUnit showed 0 skipped and 0 failed in each.
  - The run artifacts are in the implementer scratchpad and are not committed.
- `test_pg_harness.py` on the final revision: 13 passed serially and 13 passed with `-n 2`.
- Ordering check: `-n 1 -v` confirms that `START_FIRST` modules run first.
- Mutation proofs, each reverted afterwards:
  - worker routing: 3 cases
  - TRUNCATE equivalence
  - `assert_at_head`
- Database watch during a focused `-n 2` run: one template, two worker databases, and all of them dropped at the end. No `assetops_ops01p2_pt*` databases remain.
- `tools/check-all.ps1`: 9/9 passed on `f5c215c0`. `check-agent-workflow.ps1` passed after closeout.
- Layout evidence: not applicable (backend tooling).

## Known deviations

- **Template ownership.** The brief says "controller makes the template". The first worker that needs the template builds it under an advisory lock instead, and the controller only drops it. This keeps M2's lazy provisioning: a controller cannot tell before collection whether any Postgres module is selected.
- **`test_s3_performance_cutover.py` change.** This edits a product test file outside the harness. It was required, because xdist refuses to run when workers collect different random IDs.
- **No serial run in the phase-2 window.** The serial path is unchanged in behaviour, and the run budget allowed no serial run. So the parallel-vs-serial ratio pairs this window with phase 1's run.
- **Final commit not covered by a full run.** The full runs predate `b4fe2f24`, which changed one line in `cleanup_run` and added one harness test. Those were covered only by focused runs.
- **Phase-1 JUnit artifacts were not kept.** The serial per-node outcome is inferred from new2 passing every test.

## Residual risk

- Disk stalls in Docker Desktop still make timing-sensitive S4 cases fragile:
  - tick hung-stage and claims replay
  - health skew and overlap race
  - drain and work deadlines

  None of them flaked here; phase 1 saw tick flakes on old code under a stall.
- `-n 3` has one clean run only.
- Concurrent full runs are unproven.
- Inline stores are still disposed by GC, so peak sessions can rise if tests grow.
- The DELETE cleanup bypasses row triggers, as TRUNCATE also does. A future TRUNCATE trigger would break that equivalence; the harness test compares the cascade sets, not triggers.

## User-review focus

No owner UI checkpoint. For the reviewer:

- Cleanup and isolation: the routing and cleanup paths in `conftest.py` and `pg_harness.py`. Check the advisory-locked template build, and check that the controller cleans up after a crashed worker.
- Cleanup equivalence: the DELETE-vs-TRUNCATE argument.
- Role edits: their wording.

Reuse this packet's full-run evidence rather than rerunning. Run focused `test_pg_harness.py` serially and with `-n 2`, plus one Postgres module with `-n 2`.
