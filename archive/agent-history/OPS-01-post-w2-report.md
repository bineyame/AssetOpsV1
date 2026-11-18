# OPS-01 post-W2 test-speed follow-up - report

Scope: `.agent/post-W2-sequence.md:54` ("OPS-01 in Step 1"). Branch `task/OPS-01-post-w2-speed` from main `6c53b3c5`.
Tests and repo config only; no production code or semantics changed. Host: Windows, Docker Desktop Postgres 16.4,
`max_connections = 100`. Base DB `ops01pw_test` (created and dropped by this task).

## Stable command

```powershell
& $py -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml
```

Unchanged from OPS-01 phase 2. Expected wall for the W2-expanded suite (3268 tests): 50-60 min. Cap: 120 min.
`backend/TESTING.md` Timing records this.

## Measured first (main `6c53b3c5`, same command, per-test timing plugin in scratch, not committed)

| Run | Result |
| --- | --- |
| baseline | stopped at its 30-min cap at 83% (no hang: still progressing); peak 60 run sessions / 66 server-wide |
| prof1 | stopped at a 60-min cap while still in the W2 EV modules (progressing); peak 65 / 103 server-wide (another lane ran concurrently) |

Projected baseline about 60-70 min. Neither run hung. The xdist "node down" lines in those logs come from the cap
killing the run.

## Bottlenecks found and removed (reproducible, harness-only)

1. **The refusal tests waited 130 s for a connection that was refused.** Refusal tests point a store at
   `127.0.0.1:1`. On Windows, psycopg waits its 130 s default connect timeout before it raises `ConnectionTimeout`
   (measured 130.0 s; a raw socket gets the refusal in 2 s). The four tests that lacked it now pass
   `?connect_timeout=2`, as `test_w204_cold_reads.py:346` already did. Each still asserts the same 503. The affected
   tests are `test_s6_site_action_index_postgres.py:225`, `test_s7_source_health_postgres.py:230`,
   `test_w203_cold_reads_postgres.py:151` and `test_w206_ev_reads_postgres.py:232`. The fix removed about
   650 s of worker time. For example, `test_typed_errors_and_unknown_200` went from 278 s to 20 s.
2. **The replay chains re-parsed every shipped scenario YAML on every read.** That costs about 3 s per catalogue
   read, with 2-3 reads per chain and about 100 chains per run. The new `backend/tests/scenario_cache.py` reads the
   real product repository once per process and keeps only successful answers. All definitions are frozen
   dataclasses. It is used by `test_w202_cold_replay_postgres.py` and `test_w205b_ev_replay_postgres.py`, plus
   the modules that import their `chain` fixture.
3. **The EV golden-file tests failed on a CRLF checkout.** They are deterministic, not flaky.
   `test_w205b...::test_six_registered_replays[*]`, `test_w206_ev_vector_artifact` and
   `test_w206_ev_vector_cases.py::test_vector_file_has_exactly_the_six_cases` compare committed file bytes. The
   system git sets `core.autocrlf=true`, so a Windows checkout wrote those files with CRLF and all 8 tests failed.
   A new `.gitattributes` makes `contract-fixtures/w2/ev/*.json` and `backend/tests/fixtures/w2/ev-w206-vectors.json`
   check out with LF. The index bytes were already LF, so they are unchanged. **Other worktrees must re-checkout
   these files** (delete them, then `git checkout --`) to pick this up.

Measured but not adopted: `ASSETOPS_TEST_SYNCHRONOUS_COMMIT=off` made no difference on a chain test (noise-level).

## What is left in the 56-58 min (product-path work, out of scope)

- The cold/EV replay chains take about 30 s each. Most of that is evidence-ingest round trips: about 10k per chain,
  at 1.23 ms each from the host through the Docker Desktop port forward. Inside the container a round trip takes
  0.17 ms (pgbench).
- `test_s4_schedule_health_postgres.py::TestStaleWithoutJob` waits 120 s of wall clock by design (carry R-2).
- The two workers stay balanced to within about 3 min of each other (busy 2839 s and 3041 s).

## Acceptance evidence (test code at `fc23fb19`; the later commit changes only docs and this report)

| Run | Wall | JUnit (cases / skipped / failed) | Peak `pg_stat_activity` (run / server) |
| --- | --- | --- | --- |
| acc1 | 57.7 min (3459 s) | 3268 / 0 / 0 | 62 / 68 |
| acc2 | 56.4 min (3384 s) | 3268 / 0 / 0 | 67 / 73 |

The intermediate run `after1` at `ca2e4aef` took 51 min, with 8 CRLF failures that fix 3 removed. Both clean runs
stayed well under their 100-min cap, and neither failed.

- **Node IDs:** `--collect-only` before (`6c53b3c5`) and after are identical (3268, `diff` empty). In both JUnit
  files every ID is unique. No ID was added or removed.
- **Coverage kept:** migration upgrade/downgrade, process and lock tests are intact. All of them are in the
  unchanged collection and passed in both runs: the W2 migration modules, S4 drain child process, tick advisory
  locks, and health.
- **Cleanup and isolation:** each worker has its own database, as before. No `ops01pw_pt*` databases were left
  after any run, including the two that hit the cap: the next run's orphan sweep removed them. Peak connections
  stayed under the 100 limit.
- **Guards:** `tools/check-all.ps1` passes all 10 guards.

## Files

`backend/tests/scenario_cache.py` (new), `.gitattributes` (new), the four refusal-test URLs, the two chain modules'
repository wiring, and `backend/TESTING.md` (Timing table, expected time and cap, unreachable-DB rule).
