# OPS-01 phase 2 handoff

Branch `task/OPS-01-backend-test-speed`, phase 2 on top of `af7c48d2`. Not merged. Slice packet: `.agent/OPS-01-review-packet.md`.

## Changes (commits db277780, b695552e, 9c01b069, b4fe2f24, f5c215c0, closeout)

- `backend/pyproject.toml`: `pytest-xdist==3.8.0` in dev extras; installed in the shared `.venv` (with `execnet-2.1.2`).
- `backend/tests/pg_harness.py`:
  - `new_run_id()`; `route(tag, run=None)`. With `run` (an xdist worker) it routes to `<stem>_pt<run>_<gwN>_test`, sets `ASSETOPS_TEST_SHARED_TEMPLATE=1`, and takes the base from `ASSETOPS_TEST_DATABASE_BASE_URL` when nested in a routed run. Serial behaviour is unchanged.
  - `_ensure_template()`: serial path builds as before (`_build_template`). Shared path holds `pg_advisory_lock(hashtext('assetops-test-run:template:<run>'))` on the base DB, builds only if the template is missing or `datallowconn` is still true (half-built), then unlocks. Lock is on the base DB, so the drain/work tests' `pg_locks ... AND database = <their db>` checks never see it.
  - `cleanup()`: a worker drops only its own DB. `cleanup_run(run)`: controller drops every `<stem>_pt<run>_*_test` (template plus any crashed worker's DB). `provisioned()`.
- `backend/tests/conftest.py`: worker `pytest_configure` routes from `workerinput` and returns before basetemp (L1; xdist gives workers `<controller basetemp>/<gwN>`). Controller (`numprocesses` set, no `workerinput`) stores a run id, routes nothing. `pytest_configure_node` and `pytest_testnodedown` are `optionalhook`s. Workers report `provisioned` via `workeroutput`; the controller calls `cleanup_run` if any worker provisioned or died without output. `pytest_collection_modifyitems` (workers only) stable-sorts the `START_FIRST` modules (the two S4 Finding modules) to the front; with `--no-loadscope-reorder` xdist hands modules out in collection order, so they start first. Verified with `-n 1 -v`: `test_s4_finding_read_postgres` ran before `test_pg_harness`.
- `backend/tests/test_s3_performance_cutover.py:258`: two `uuid4()` parametrize values replaced by fixed UUIDs. Without this xdist refuses to run (`Different tests were collected between gw0 and gw1`; first p2a attempt aborted after 5 s on this). Test meaning unchanged (unknown run/revision -> 404).
- `backend/tests/test_pg_harness.py`: +3 pure routing tests, +1 Postgres test (`cleanup_run` drops all of its run, nothing of another run). 2125 -> 2129 node IDs on the final revision.
- Role guidance: `.claude/agents/assetops-reviewer.md` (focused files; cite implementer same-revision full evidence; full rerun only for a finding, then keep-awake, 2x cap, one at a time), `.claude/agents/assetops-implementer.md` (Verify: guide, full once per slice, keep-awake, 2x cap, record evidence), `.ai/ROLE_CONFIG.md` (new bullet after "Hand off at about 120k context"). No current Codex prompt template hard-codes a full suite (grep of `.ai`, `.claude`, `tools`; only historical `.agent` logs do).
- `backend/TESTING.md`: parallel routing, deterministic-ID rule, normal command `-n 2 --dist loadfile --no-loadscope-reorder`, serial fallback, timing rows, caps (20 min parallel, 90 min serial), flake policy, one-at-a-time policy.

## Timing (full suite, private base `assetops_ops01p2_test`, `--durations=30`, keep-awake running)

| Run | Revision | Workers | Wall | Peak client sessions | JUnit |
| --- | --- | --- | --- | --- | --- |
| phase-1 new2 (reference) | phase 1 | serial | 30.8 min | 22 | 2125 passed, 0 skipped |
| p2a | 9c01b069 tree (b695552e code) | `-n 2` | **7.7 min** (461 s) | 35 | 2128 passed, 0 skipped, 0 failed |
| p2b | same | `-n 2` | **8.4 min** (506 s) | 32 | 2128 passed, 0 skipped, 0 failed |
| p3a | same | `-n 3` | 6.5 min (390 s) | 41 | 2128 passed, 0 skipped, 0 failed |

- `-n 2` vs phase-1 serial: about -74% (median 8.0 vs 30.8 min). Not back-to-back: no serial run in this window (the serial path is unchanged, so the brief allowed none). The two big Finding tests took 39-75 s here vs 53-950 s across phase-1 runs, so this window was quiet; disk stalls would lengthen all runs.
- `max_connections` 100; peak 41 at `-n 3`. Concurrent full runs not attempted; one-at-a-time documented.
- Aborted attempt: the first p2a stopped at collection (5 s, no tests run) on the random parametrize IDs above.

## Coverage (M4)

- Serial `--collect-only -q` at b695552e: 2128 IDs. Each parallel JUnit (rebuilt to node IDs, UUIDs normalised): 2128 cases; missing 0, extra 0; all passed; 0 skipped. Against phase 1 (2125): +3 IDs, all `test_pg_harness.py` (the three pure routing tests); the final commit adds a fourth (`TestAgainstPostgres::test_the_controller_drops_every_database_of_its_run_and_nothing_else`).
- The phase-1 per-node JUnit files were not kept; phase-1 new2 was all-pass, so the per-node serial outcome is "passed" for every phase-1 ID.

## Flakes (M8)

None. The tick hung-stage (33-41 s), health overlap race, drain and work-lock tests passed in all three parallel runs. No retries exist.

## Proofs

- Mutations (committed first, reverted with `git checkout`): removing `SHARED_ENV` set -> worker routing test fails; ignoring `BASE_ENV` for nested workers -> nested test fails; dropping the run filter in `cleanup_run` -> controller test fails.
- Laziness: `-n 2` unit-only selection and `--collect-only` created no database. Focused `-n 2` run watched every 4 s: one `tpl` (datallowconn false) plus `gw0`, `gw1`; all gone afterwards. After every full run: 0 `assetops_ops01p2_pt*` databases.
- `tools/check-all.ps1`: 9/9 passed on f5c215c0.

## Final-revision caveat

The three full runs were on code equal to b695552e. The later commit changed only `cleanup_run`'s base-URL choice (prefers `ASSETOPS_TEST_DATABASE_BASE_URL`, equal to the URL in a normal controller) and added one harness test; `test_pg_harness.py` passed serial (13) and `-n 2` (13) on it. No further full run was made (run budget).

## Recommended normal command

`pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=...` (proven twice). `-n 3` was 16% faster in one run; adopting it needs a second clean run - coordinator's call.
