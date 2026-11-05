# CH-5c handoff 4: partial. Steps 1-5 of the builder-4 brief are built; resume at L3 (step 6/7)

Builder 4 stopped at about 105k context, with lane 2's `mechanism_dataset.py build --variant close` running (PIDs
17108/13872, not ours), so no L3 job was started. Branch `task/CH-5c-perf`, worktree `AssetOpsV1-ch5c`. Spec: sheet
§8 (CH5c-R4) and §8.4 (CH5c-R5). Scratch env `...\scratchpad\ch5c\env.sh` (PYTHONPATH, `$PY`, `$S`, `$CLONE`);
A bundles `bA`, `bB`; app work dir `$S/work` (keys.json). Handoff 3's facts for the packet (tenant-wide rows, Q5
env list, replica mode, R4 engines) still hold; they are not repeated here.

## Commits (on top of handoff 3's `c5e9ebdee`)
- `2cfcb90c5` u4:
  - `chain/response_store.py`: `ResponseStore.serve(StoredRoute, compose)` under R5-1 (a)-(c). (a) one RR
    transaction: `read_watermark` first, then the tenant's `site` rows filtered by the route's admission predicate
    (or the board's fixed Site), then the lookup. (b) compose in `read_scope.fresh` (new, `read_scope.py`). (c) the
    watermark re-read in a new transaction; equal: insert on its own `begin()`, `ON CONFLICT DO NOTHING`; else serve,
    log `stored_route_race`, no store. Bytes = `render()` (JSONResponse rendering), `ETag` = sha256(route, key, W,
    version); header `X-AssetOps-Stored: hit|stored|race|unstored`. A lookup or insert failure never fails a request.
    `request_key` = canonical JSON {route, tenant, sorted admitted Site ids, parsed request}; `parsed_key` is every
    `EstateRequest` field after defaulting (known_at None stays None).
  - `read_watermark(c, t, None)` is the tenant-wide count (estate routes); the board passes its own Site.
  - Wiring: `estate_portfolio_api.py` (one compose stores both the Portfolio and scope-ids, `_bodies`),
    `outcome_api.py` (board key: site, domain, parsed day/from/to, known_at, pin; summary: auth+parse first, admit
    = `admitted` and `disclosed`), `estate_api.py` (Findings index only, now under `perf.route`, Q7), `main.py`
    (`build_response_store(database_url())`, None with `ASSETOPS_RESPONSE_STORE=off`).
  - `backend/tests/conftest.py` sets `ASSETOPS_RESPONSE_STORE=off` by default (tests monkeypatch composers between
    identical requests); the store tests build it explicitly.
  - Pre-build: `chain/prebuild.py` (`paths()` = the 20 listed requests + a scope-ids per Portfolio; `run()` drives
    them through `create_app` via TestClient, then `prune()`), stage `prebuild` in `scheduling/stages.py`,
    `ScheduleTick(prebuild=True)` only from the `scheduling.run tick` CLI, after the Site loop; `TickLimits.prebuild_seconds=120`
    (in `tick_lease_seconds`); `report.prebuild` in `as_json` and the tick perf line with share of `tick_seconds`.
  - `test_ch5c_response_store_postgres.py` (6): stored bytes served/equal render/equal a store-less compose after
    the Q4 fields; data change recomposes; `lens=all&limit=50` hits; admission in key; **R5-1(e) race** (served,
    nothing stored; proved non-vacuous by disabling the after-check: fails `'stored' == 'race'`, reverted); prune.
  - `test_w303_portfolio_scope_snapshot_postgres`: expected dicts gain `link_ref`.
- `7549dcc4a`: two more `evidence_prompt` dicts gain `link_ref`. **Latent on main:** the 3 tests fail on plan2
  main `fd03ae6b0` with the same `link_ref` diffs (181 s run, `$S/w303main.log`); on the branch the 3 pass (other 7
  passed in handoff 3). Owned test update; no assertion weakened (literal refs, plus kind/view pins for the footer).
- `ab409950b`: `tools/chain_response_probe.py` (`prebuild`, `fresh`, `watermarks [--out|--compare]`, `wmtime`);
  `tools/chain_perf_probe.py --store on|off` with EX-3 budgets printed; the W6 guard sets the store off.

## Tests run (localised, `ASSETOPS_TEST_DATABASE_URL=...55432/assetops_test`)
- `test_ch5c_response_store_postgres`: 6 passed, 9 s. `test_w303_portfolio_api` + `test_cov_partial_portfolio`:
  18 passed, 1 skipped (DB env unset in that run). `test_w301_estate_api`: 11. `test_out_b4_{route,main_binding,
  imports,window}`: 21. `test_ch0_tick_timing`, `test_ch1b_drain`, `test_w402_mini_stage`: 44. w303 3 tests: pass.
- After u4: `test_ch5c_watermark_postgres` + `test_ch5c_w6_guard_postgres` + `test_qw1_perf`: 22 passed, 11 s.
- Not yet re-run after u4:
  `test_s4_schedule_tick_postgres.py` (tick ctor changed: new kwarg, default off).

## Next (in order)
1. Check lane 2 is idle (`mechanism_dataset|chain_clone|chain_coherence`). Re-run `test_s4_schedule_tick_postgres`.
2. **R4 driver** (not measured): inject `connect_args={"prepare_threshold": 0}` vs default on the three read
   engines (handoff 3 anchors), warm probe on the clone; under 5% gain → drop and report (Q6).
3. **L3 on `assetops_chainclone_ch5c_test` (at 0044).** Run with `ASSETOPS_RESPONSE_STORE=off` in the shell for the
   settles (the settle env pops the cursor keys, so the tick's prebuild stage cannot match the served code_version;
   pre-build through `chain_response_probe.py prebuild` instead, which uses `$S/work/keys.json`):
   1. `tools/chain_clone.py settle ch5c` at 0044 (seconds = before); `alembic upgrade head` on the clone; settle
      again (seconds = after: the trigger cost).
   2. Guard CLI `tools/chain_watermark_guard.py --database-url $CLONE --work $S/work`: ok, `event_consumption_read`.
   3. A/B vs `bA` (collect a B bundle with `chain_coherence.py collect`, diff with `$S/diff.py`), scope-ids vs main
      ids (§8.3), COH 0 new.
   4. `chain_response_probe.py prebuild` (seconds, states), then `fresh` (all equal), `wmtime` (50 ms stop).
   5. Idle-tick: `watermarks --out $S/wm0.json`; two settles' tick step (or `scheduling.run tick`) with no new data;
      `watermarks --compare $S/wm0.json`. Any move: STOP, report the table(s) from `chain_input_change` rows added
      (`SELECT table_name, count(*) ... WHERE change_id > <max before>`) and the columns written.
   6. `chain_perf_probe.py --store off` (uncached) and `--store on` after prebuild (first = cold, hit = warm);
      Portfolio bytes against 100 KB.
   7. `late_fill(KOBO-001, D7)` + consume; Kobo watermark moves, Cold's not; `prebuild` seconds (re-warm); `fresh`.
4. Guards: check-all with `-Python <plan2 python>`. Packet `.agent/review-packet-CH-5c.md` (W1 Known Deviation:
   uniform W2 triggers also on append-only tables; the tenant-wide table list; Q5 env list; latent w303; tests off
   by default). `tools/chain_clone.py drop ch5c`.

## Risks
- `prebuild.run` uses `assetops_backend.main.create_app`, while the server is `host/lab_app.build_app`; `fresh`
  compares against `lab_app`, which catches any divergence.
- The tick's prebuild env must equal the server's (`code_version` hashes the cursor keys); the settle env differs.
- `ScheduleTick` callers other than the CLI get no pre-build (default off).
