# AR-3 + AR-6 packet (ANY-2 core): Portfolio coverage on rows; board work lists in one read

Branch `task/ANY-2-AR3-AR6` (worktree `AssetOpsV1-ar3`) from `task/ANY-1-rows` `b1ca93b83`. Card: sequence
revision 4 (`architect-sequence-client-scope-2026-11-11.md` ~l.35). Spec: `architect-answer-any-range-speed-2026-11-10.md`
AR-3, AR-6; D-ANY.1-6. **Phase: code + no-DB tests only (done).** Postgres, backfill, parity and timing: Thursday
after 12:30 (steps below). USER_REVIEW: none of its own; merges only after ANY-1 merges (card rule).

Commits: `0ea0bcdbc` (AR-3), `38a7c748e` (AR-6), then this packet.

## AR-3 Portfolio coverage on rows

| Item | Where |
|---|---|
| Kind `dispatch.day`, grain `s3_day`, MINIGRID; inputs = `DISPATCH_ROLES`, analytic `dispatch`, job domain `dispatch`, Foundation | `config/chain/event-register-v1.yaml` |
| s3_day resolution: an s3_day kind's events dirty the UTC days of their spans widened by the S3 bracket (6 h = `assessment_inputs.BRACKET`), clamp `today + 1`; measures and other kinds unchanged (local days) | `chain/events.py` `resolve`, `_s3_days`, `S3_BRACKET` |
| Row = one per (Site, UTC day D): period = `day_window(D)`, `local_day` = D (the "dispatch day with D's date" DATA-12 matches on); body = the exact `select_dispatch_days_on` day dict minus `known_at`, type-tagged (`$dt`/`$date`/`$uuid`/`$dec`) so coverage receives the same Python values; state = S3 status or `UNAVAILABLE` | `chain/dispatch_day_rows.py` (`encode/decode`, `body_of`, `DispatchDayKindBuilder`) |
| Builder input: `PostgresAssessmentStore.dispatch_day_now(t, s, D)` = `select_dispatch_days_on` for D, own read-only REPEATABLE READ, k = `clock_timestamp()` (live) | `analytics/adapters/postgres_assessment_store.py` |
| Serve path: `coverage.dispatch_days(...)` asks `dispatch_rows_provider` (`DispatchDayRows`): None while `dispatch.day` not in `ASSETOPS_PERIOD_READ_KINDS` (kill switch, today's compose); else ONE period read per Site (rows, then PENDING-at-k; live dirty marks); explicit k (historical basis or continuation page) reads `computed_at <= k`. `_mini_grid_basis` reads only this; DATA-12 day-grade rules, match pass, Finding index unchanged | `estate/coverage.py`, `chain/dispatch_day_rows.py` `DispatchDayRows` |
| PENDING at k: stored facts + one synthetic outstanding job (`PENDING_JOB`) -> Site PENDING_RECOMPUTE, job state PENDING. Absent row: a day with nothing stored by k (no selection, UNASSESSED, no job; reason `NOT_BUILT`) -> an unchecked day, logged/counted live by the reader | same |
| Wiring: `period_kind_builders` -> `dispatch_day_builders(inputs)` (over `inputs.dispatch.store`); `build_dispatch_day_rows(url)` -> provider injected in `main.py` (lazy engines, disposed on shutdown) | `chain/composition.py`, `main.py` |

## AR-6 work lists in one read

| Item | Where |
|---|---|
| `WorkIndexService.read_many(t, s, code, [(kind, ListRequest)], access_basis)`: N list reads in ONE snapshot; `read` = one-request case (shared `_page`) | `work/site_index.py` |
| Board `work` port: the first first-page `incidents` call prefetches the board's 4 first pages (incidents over the 31-day work window + `visits.record_windows`) via `read_many`; each later matching first-page call is served from it; cursors and misses read as before; batch failure or a service without `read_many` -> the 4 single reads unchanged. No compose file changed; `Reads` still records 4 `work_index` reads | `site_outcomes/read.py` `_shared` |
| Per-snapshot memo in `_ReadTx`: `site_name`, and cold/EV pins (`_cold_ev`, no window input) keyed by the full pinned row + cutoff, deep-copied out | `work/adapters/postgres_work_read.py` |

## Checks run (no DB, 2026-11-11 evening)

- `pytest test_ar3_dispatch_day_rows test_any1_period_read test_ch1b_drain test_ch1b_register tools/checks/test_event_register`: 118 passed.
- `pytest test_*cov*.py test_estate_*.py` (non-Postgres): 47 passed, 1 skipped.
- `pytest test_ar6_work_batch` + 18 board/work no-DB files (`site_outcome|out_b|work_index|site_index|outc_|visits|board`): 272 passed.
- `create_app()` without a database: provider None; `build_dispatch_day_rows` with a dummy URL constructs without connecting.
- `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = plan2 venv) on `38a7c748e`: "Architecture check passed." exit 0.
- Non-vacuity (committed first, reverted with `git checkout`): coverage ignoring the provider + `S3_BRACKET = 0` + board
  port without prefetch: 14 failed / 16 passed in the two new test files; after revert 30 passed, tree clean.

## Known deviations

1. Grain interpretation: "on DATA-12 graded local days" is implemented as rows keyed by the UTC dispatch day whose date is the local day DATA-12 matches (`local_day` column = D); coverage keeps DATA-12's local-day grade rules. Spec grain `s3_day` kept.
2. The body keeps compose's diagnostic English `status_reasons`/`unavailable_reasons`/job `last_error` (keys outside `WORD_FIELDS`, never rendered by coverage); D-I18N.1 applies to rendered words.
3. Historical reads serve rows "as built" (D-ANY.5): a k between data recording and the row build reads absent; a historical job nuance (compose reports LEASED as PENDING, FAILED as unavailable at k) is not re-derived from rows.
4. `evidence_money.mini_grid_rows` (AR-4's file) still calls `snap.dispatch_days`, so until AR-4 switches it to `coverage.dispatch_days` (one line) the Portfolio still composes the days once per request there: **the AR-3 Portfolio speed gain is partial until then.**
5. AR-6 prefetch is triggered by the incidents first page (all three composers call it first); the 4 bodies share one read instant instead of four.
6. No parity cases added to `period_read_parity.py` tonight (another agent is changing it on `task/ANY-1-rows`); the AR-3 cases are listed below to add after the rebase.
7. Rows are read per Site (not one statement across Sites); with AR-2's `_UNCONSUMED_AT` low-water bound (`29e390fba`, on `task/ANY-1-AR2`) after the rebase.

## Thursday (after 12:30, one Postgres job at a time; never client6, never demo3_full)

1. Rebase onto main after ANY-1 (+AR-2) merge. Conflicts expected: `chain/composition.py` (`period_kind_builders` = AR-2 mini kinds + `dispatch_day_builders`; AR-2's `period_kind_versions()` must add `{"dispatch.day": dispatch_day_rows.BUILDER_VERSION}`), register `kinds:` (both), `test_ch1b_drain.py`/`test_ch1b_register.py`/`test_any1_period_read.py` (union: a `feeder_demand` reading marks productive_kwh + 4 mini kinds + dispatch.day; foundation fixture adds both). If AR-2's `tools/demo_combined.py` builds rows after drain-2, add `--kind dispatch.day` with `--from` one day before the first story day (a UTC+3 local week touches the UTC day before).
2. Postgres tests (new `backend/tests/test_ar3_dispatch_day_rows_postgres.py`, own `*_test` DB, routed run DBs): seeded mini-grid Site with dispatch selections; build rows via `period_backfill build --kind dispatch.day`; (a) live coverage from rows == compose coverage (byte-equal `site_coverage`); (b) k between revision 1 and 2 serves revision 1; k before revision 1 = absent; (c) late accepted reading: PENDING before drain, equal to compose after drain; (d) `dispatch_day_now` == `select_dispatch_days_on` live for the same day. AR-6: `read_many` == 4 `read`s on the work-index Postgres fixture (`test_*work*postgres*`).
3. Backfill client4: `python -m assetops_backend.chain.period_backfill build --site <each MINIGRID site> --kind dispatch.day --from <first data UTC day - 1> --to <S + 1> --quiet`; record wall time.
4. Parity on client4 (baseline args, `--kinds dispatch.day`, then with the AR-2 kinds together if merged): 0 MISMATCH, `any.between_revisions.site_period_read` PASS. Add then: a Site-local week Portfolio (`from=<D-1>T21:00Z`, 7 days) on `/api/estate/portfolio` and `/api/estate/findings`, and a cursor page.
5. Timing: `perf_budget.py --any-range --report` with kinds empty vs `--kinds dispatch.day` (Portfolio cases); Cold and EV boards cold, main vs branch (AR-6 target < 1 s). Report before/after here.
6. Guards: `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`; adjacent no-DB files above.
7. Demo: keep `dispatch.day` out of `ASSETOPS_PERIOD_READ_KINDS` until its rows are built on that DB (an unbuilt DB reads every day absent -> unchecked).

## Thursday night results (2026-11-12, Postgres phase, Sonnet implementer)

Env: venv of plan2; `PYTHONPATH` = this worktree's `contracts;backend;simulator` (the venv otherwise imports the
`AssetOPsV1` checkout's contracts and fails); host+tools added for parity. DB `assetops_ar3_test` (private), client4.

1. **Merge** `git merge main` (ANY-1 + AR-2): conflicts in `chain/composition.py` (union: `period_kind_builders` =
   `dispatch_day_builders` + AR-2 mini kinds; `period_kind_versions()` now also `dispatch.day: dispatch-day-rows-1`,
   used by `build_dispatch_day_rows`' reader; `__all__` union), `config/chain/event-register-v1.yaml` (one `kinds:` with
   the 4 mini kinds + `dispatch.day`), `test_any1_period_read.py`, `test_ch1b_drain.py`, `test_ch1b_register.py`
   (union: 5 kinds + `dispatch.day`; marked 6; `sorted(...)` order). Merge-follow fixes: `test_ar2_mini_period_rows.py`
   version map includes `dispatch.day`; `test_ch5c2_clock_guard.py` allowlists `dispatch_day_now.work` (row builder's
   own read instant, worker not a stored compose).
2. **No-DB** (`ASSETOPS_TEST_DATABASE_URL` unset, all non-`*postgres*` backend test files, 21 min under load):
   5768 passed, 148 skipped, 17 failed. Of the 17: 3 were this branch's merge effects (the two fixes above) and are
   fixed; the rest are `test_k8_estate_fuel.py` x14 + `test_fetch_seam_contract.py` x1 which **fail identically on
   main (plan2 `da0c584c7`)** when the two files run together (order pollution) and pass singly here (k8: 21 passed).
   Focused set after merge: ar3 + any1 + ch1b + event_register + ar6: 123 passed.
3. **Postgres, one file at a time** (`assetops_ar3_test`, routed run DBs):
   - NEW `test_ar3_dispatch_day_rows_postgres.py`: 2 passed (61-71 s). (a) live rows == `select_dispatch_days_on` and
     `dispatch_day_now` == it; (b) k before any build = every day absent (`NOT_BUILT`), k between two builds serves
     the first, live serves the second (non-vacuous: the two compose results differ); (c) an unconsumed event reads
     PENDING from the rows (asserted), after drain + rebuild == compose; (d) kill switch empty -> provider None.
     Compared through `encode` minus `known_at`, on the S4 F06 fixture (not through `site_coverage` byte-equality:
     coverage keeps the unchanged DATA-12 pass over the same day dicts).
   - NEW `test_read_many_equals_single_reads_at_one_instant` (in `test_w401_site_indexes_postgres.py`, placed before
     the cold chain test): passed; the rest of that file without the cold test: 5 passed (110 s).
   - `test_any1_period_read_postgres.py`: 4 passed (51 s). `test_ar2_mini_period_rows_postgres.py`: 3 passed (903 s
     under heavy machine load, 15 min).
   - **Pre-existing failures, same on main (plan2 `da0c584c7`)**: every cold/EV-chain-fixture test
     (`test_w401_site_indexes_postgres::test_cold_ev_pinned_list_fence_and_reselection`, 12 failed + 5 errors in
     `test_w301_estate_index_postgres.py`, incl. the `pair`-fixture mini-grid ones) stop at `run(built)`
     `assert outcomes ...` with `outcomes == []` (cold worker finds no pending job). Verified the cold_ev test fails
     identically on main. Not this branch's scope; noted for the coordinator. The w301 mini-grid page-two tests that
     would exercise coverage over a real Site are therefore not runnable here.
4. **Backfill client4** (`DATABASE_URL` client4, `--kind dispatch.day --from 2026-10-10 --to 2026-11-09 --quiet`):
   KOBO-001 31/31 written 29.3 s (36 s wall); KISIWA-001 31/31 written 11.4 s (16 s wall).
5. **Direct parity + timing on client4** (`scratchpad/probe_dd.py`, both Sites, `2026-10-11..2026-11-09`, 29 days,
   `ASSETOPS_PERIOD_READ_KINDS=dispatch.day`): rows == `select_dispatch_days_on` for all 29 days on both Sites
   (0 differing); rows read 360 ms (KOBO-001) / 127 ms (KISIWA-001) vs compose 20.4 s / 5.5 s.
6. **Full parity harness on client4 (`--kinds dispatch.day`): NOT COMPLETE.** Started 03:07, killed by PID at 03:47
   (40 min, past the 2x-of-13-min cap): the machine was running several other lanes' pytest/parity jobs (a second
   parity started 03:37), so wall time is not representative. First attempt failed immediately with
   `ModuleNotFoundError: lab_app` (needs `host` and `tools` on `PYTHONPATH`; fixed in the command). No result either way.
   `perf_budget.py --any-range` not run. See resume point.
7. check-all: see below (appended when finished).

Known deviation (new): none beyond 1-7 above; note 4 (AR-4's `evidence_money` still composes) unchanged.

Resume point: rerun parity when the machine is quiet:
`cd AssetOpsV1-ar3; PYTHONPATH=<ar3>/contracts;backend;simulator;host;tools; ASSETOPS_PREBUILT_ROUTES=<e3c>/var/polish_client4/prebuilt-routes.json;
python tools/checks/period_read_parity.py --database-url <client4> --work <e3c>/var/polish_client4 --story <same>/story.json
--seed 20261111 --random 16 --kinds dispatch.day` (client4 already has the dispatch.day rows), then perf_budget.
