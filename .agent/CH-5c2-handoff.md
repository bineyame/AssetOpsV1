# CH-5c2 handoff (PARTIAL; context cap reached) - branch `task/CH-5c2-store-safety`, head `036973c70`

Spec: `AssetOpsV1-plan2\.agent\build-sheet-CH-5c.md` §8.6 + §8.7; pre-flight `.agent/CH-5c2-preflight.md`.
Env: `scratchpad/ch5c2/env.sh` pattern (absolute PYTHONPATH of this worktree; plan2 venv). Clone
`assetops_chainclone_ch5c2_test` untouched so far. No DB test run yet (lane 2 `chain_clone.py settle ch9m` was running).

## Landed (2 commits on `55219fd1f`)
- `ba0f5cf04`:
  - `read_scope.py`: `clock()`, `read_instant()` (identity seam on every DB read-instant capture), `within()`,
    `since()`, `ReadScope.boundaries`, `COMPOSING` contextvar + `composing()`.
  - C1 rewrites: `estate/coverage.py:387,411`, `estate/portfolio.py:573`, `chain/read.py:245,262`,
    `analytics/cold_reads.py:65` (UNKNOWN when `window_to > now`; **beyond §3**: Known Deviation),
    `postgres_assessment_store.py` FUTURE_NOTE (~2200) + clock defaults -> `read_scope.clock()` (2071, 2768),
    `actions/verification.py` `current_state` `now < later_end` (~966; **beyond §3**), `actions/service.py utc_now`
    -> `read_scope.clock()` (so `site_index.py:164 read_at` and `verification.py:982` go through the seam).
  - Q4: `objectives/adapters/postgres_objective_store.py current()`: historical SQL `recorded_at <= :k` (no now());
    live = all revisions, head picked in Python with `within(recorded_at, None, at)`.
  - DB captures wrapped in `read_scope.read_instant(...)`: estate read, evidence-money read (both now
    `clock_timestamp()`, L2), mini_depth 347/407, work_read 383, global_read 182, domain_action_index 193,
    assessment `_window_snapshot` 966, thread_sources 189 (`now` select list).
  - `response_store.py`: `_state` (DB W, then Sites `(id, code, timezone)`, then `F` appended as `|f:<hex>`), F
    re-read at (c); `valid_until(boundaries, now, zones, live=)` (live boundary = `b > at and at >= now - 1 s`;
    midnight cap; -1 s; historical w/o live marks -> None); M1 (whole post-compose store block in `try`, unstored,
    no ETag); L1 (no ETag on race/unstored; insert returns inserted routes, conflict -> `race`); `mode()`
    on/off/compose (default **on**); compose mode = composes under `COMPOSING`, stores nothing (`composed`).
  - `postgres_response_store.py`: lookup `valid_until IS NULL OR valid_until > greatest(clock_timestamp(), :now)`
    (`:now` = `read_scope.clock()`: Known Deviation, needed so a moved app clock misses); insert writes
    `valid_until`, returns rowcount set.
  - `chain/adapters/file_inputs.py` + `config/chain/file-inputs-v1.json` (symbolic bases resolved at read time;
    `roots()`, `prefixes()` for F4, `file_state()`); F = 5.9 ms for KOBO-001 on the worktree `var/` (F3 <= 20 ms;
    re-measure on the clone path).
  - `composition.build_response_store` wires `files=file_state`, `compose_only`.
  - `file_code_version._files`: + `host/**/*.py`, `contracts/**`.
  - `0048_chain_response_expiry` (on 0047): `valid_until` column, BEFORE TRUNCATE refusal (`ledger_append_only`).
  - `tests/test_ch5c_store_off.py` updated to default-on (17 pass, L0). `conftest.py:60` keeps tests off.
- `036973c70`: `scheduling/run.py` `tick --no-prebuild` + `prebuild` command; `demo_combined.tick` F5 order;
  `chain_watermark_guard.py` L3 (`schema.` names, comma FROM lists via `_ALIAS`/`_NEXT`), `CLOCK_SQL`,
  `clock_in_predicate()` (verified by hand: select-list capture passes, `WHERE ... now()` fails).

## Remaining, in order
1. W6 CLI `_run` (`tools/chain_watermark_guard.py:~150`): use `ASSETOPS_RESPONSE_STORE=compose`; in the listener,
   when `read_scope.COMPOSING.get()` is set and `clock_in_predicate(statement)` -> record `clock_predicates`;
   F4 audit hook (`sys.addaudithook`, active only when `COMPOSING` set): `open`/`os.listdir`/`os.scandir` path not
   under `file_inputs.prefixes()`, the code_version set (backend/assetops_backend, backend/migrations, config,
   host, contracts, MANIFEST_ENV files), `sys.prefix`, `sys.base_prefix`, `site.getsitepackages()` -> violation;
   any `socket.connect` -> violation. Record violations, never raise. Executed-module capture via
   `sys.monitoring` PY_START while composing; compare with committed `config/chain/stored-composer-modules-v1.json`
   (fail on unlisted; `--modules-out` writes the observed list for a reviewed diff, Q5). `ok` must include them.
2. L0 static clock guard (new test, e.g. `tests/test_ch5c2_clock_guard.py`): over the module list, no
   `datetime.now`/`utcnow`/`date.today`/`time.time` outside `read_scope.py`; SQL clock functions only in a named
   allowlist (read-instant captures above + writer lines, each with a reason). Prove with a planted `datetime.now()`.
   Note `postgres_assessment_store.py` has writer `clock_timestamp()` lines 405-559 and `_transaction_time` 1057.
3. L4 guard rule owning `chain_input_change` as trigger-written only (find the `event_outbox` rule in
   `tools/checks/`); L2 test: TRUNCATE refused; under `session_replication_role = replica` allowed (rolled back).
4. Tests (new `tests/test_ch5c2_store_safety_postgres.py`, reuse `test_ch5c_response_store_postgres.py` helpers):
   M1 failing port for lookup / re-check / insert; L1 conflict -> no ETag; valid_until stored and moved-clock miss
   (`monkeypatch.setattr(read_scope, "clock", ...)`; board path uses `read_scope.clock()`; estate `k` is the DB
   instant -> patch `read_scope.read_instant` too); F6 (new Performance report / FAILED report on the board, S2
   report on the summary: see `test_out_b4_board_postgres.py:120 _evidence_root`); C4 sweep; Q4 parity (old SQL vs
   new `current()`, live + historical); F4 L2 over every stored route (planted file read + planted listdir).
   Existing `test_ch5c_response_store_postgres.py` uses the old 4-arg lookup indirectly via `ResponseStore`: rerun.
5. Q1 packet classification: `verification.py` 149/379/547/784/903 (writers / non-stored detail routes),
   `site_index.py:164 read_at` (output field: mask or prove absent from stored bodies), `analytics/service.py:151`,
   `sites/cutover.py:209`, `gateway_api.py:109`. The Q4 mask list (`WALL` in the store test) may need `read_at`.
6. Docstrings: `chain/watermark.py` (code_version scope, F), `response_store.py` module doc (F, valid_until).
7. Migration: check `git log main` for CH-9 (0048/0049); if merged, re-point to `0050` on `0049_mini_service_v2`.
8. L3 clone pass: prebuild -> `fresh` -> idle tick -> W6 CLI -> drop clone; guards one at a time (10-min cap);
   packet `.agent/review-packet-CH-5c2.md`; set task status.

## Risks
- `within`/`since` registrations against a test-injected fixed clock are treated as historical (dropped).
- `file_inputs` resolves bases via `importlib` from config strings (seam guard may want a static import).
- The suite was not run beyond the L0 file; the rewrites are semantics-preserving by construction only.
