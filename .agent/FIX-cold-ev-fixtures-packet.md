# FIX-cold-ev-fixtures - diagnosis packet

Branch `task/FIX-cold-ev-fixtures` from main `f482cc3f8`. Outcome: **environment-only cause; no code change.**

## Cause

The cold/EV chain fixtures (`backend/tests/test_w202_cold_replay_postgres.py` `Chain._gateway`) start the gateway
as a subprocess (`gateway/tests/test_gateway_process.py:59`, `python -m assetops_gateway serve`). The reporting
lane's PYTHONPATH (and this brief's: contracts;backend;backend\tests;simulator;tools;host) omits `gateway`, so
both the test process and the gateway subprocess import `assetops_gateway` through the plan2 venv's editable
install, which points at the stale `C:\Users\assef\Bineyame\AssetOPsV1` checkout (detached at 056a34b82,
2026-10-17). That old gateway `service.py` parses every lab report with the older public-report contract, which
rejects the newer `actor` field: each report is HELD as `INVALID_REPORT` / `actor` / "not a field of a public
device report". The stage stays `HELD` (93 held reports, 0 envelopes), release is blocked (`STAGE_HELD`), nothing
is uploaded, no `recompute_job` is enqueued, so `run_pending` returns `[]`.

## First bad commit

None. Bisect was not needed: the same test also fails at 11-07 main `f7c045bee` with the same PYTHONPATH, and it
passes on main with `gateway` added. The trigger is the drift between the stale checkout's gateway and the current
contracts/simulator, not one merge.

## Evidence

- Repro (worktree PYTHONPATH without `gateway`): `test_cold_ev_pinned_list_fence_and_reselection` FAILED, `AssertionError: []`.
- Instrumented run (debug prints since reverted): release `release_blockers: ['STAGE_HELD']`, `held_report_count: 93`;
  held admissions `{'kind': 'INVALID_REPORT', 'field': 'actor', ...}`; DB: 0 `accepted_evidence`, 0 `recompute_job`, 0 rejections.
- `python -c "import assetops_gateway"` without `gateway` on PYTHONPATH resolves to `C:\Users\assef\Bineyame\AssetOPsV1\gateway\...`.

## Results with `gateway` on PYTHONPATH (DB `assetops_fixcold_test`)

- `test_w401_site_indexes_postgres.py -k cold_ev`: 1 passed (81 s).
- `test_w301_estate_index_postgres.py` (full): 21 passed, 0 failed, 0 errors (486 s, wall 490 s).
- `test_w401_site_indexes_postgres.py` (full): 5 passed, 0 failed (125 s, wall 129 s).

## Remedy

Run Postgres files through `tools/run-host-tests.ps1` (it puts backend, contracts, simulator, gateway, host and
field first on PYTHONPATH and refuses stale import origins, backend/TESTING.md "Commands"), or include
`<worktree>\gateway;<worktree>\field` when setting PYTHONPATH by hand. Lane briefs that give a PYTHONPATH list
should include `gateway` and `field`.
