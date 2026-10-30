# OUT-D phase handoff (partial: U1-U3 done, resume at U4)

Branch `task/OUT-D-declared-objectives`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outD`, head `994a5462`
(base main `833e7c95`). Sheet (binding, self-contained): `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-OUT-D.md`.
Architect rulings: `.agent/decisions-while-owner-away-2026-10-30.md` (Q1 below).

## Landed
- U1 `81e95e59`: `backend/migrations/versions/0038_out_objectives.py` (sheet SQL verbatim via constants);
  `backend/tests/test_out_d1_schema_postgres.py` (23 passed: catalog, 19 named CHECK refusals, site FK, trigger
  UPDATE/DELETE, downgrade 0035 / upgrade head). 20 head-literal test files -> `"0038_out_objectives"`;
  `test_w504_ev_intent_postgres.py` keeps `get_revision(MIGRATION).down_revision == PARENT` with
  `MIGRATION = "0035_w5_ev_work"`. Nothing under tools/ named the literal.
- U2 `16639d83`: `outcomes/objectives.py` (POLICY, MET/MISSED/NOT_JUDGED, VERDICT_LABEL/CHIP, CONTRIBUTOR_LABEL,
  `Measure(key,outcome,kind,comparison,unit,window_rule,target_zero,target_any,zero_only)`, MEASURES, `target_text`,
  CHAMBER_RANGE_MEASURE/TARGET, ObjectiveFact, Reading, judge). `outcomes/status.py` -> `outcome-status/2`,
  `outcome_state(..., objective=None, objectives_ok=True)` rules 4c/7/7b/7c. Tests: `test_out_d2_objectives.py`;
  with b1_status + a1: 67 passed (b1 goldens untouched). Ruling Q1: only `energy_cost_per_km` is VALUE (and the only
  money); the other five LEADING; `zero_only` only on `backup_start_failures`.
- U3 `1e2e0d02` + `994a5462`: `objectives/model.py` (Declaration, validate -> 422 OBJECTIVE_INVALID, payload_sha256,
  target_string, SYSTEM_DECLARER), `objectives/adapters/postgres_objective_store.py` (`declare(tenant_id, decl,
  principal, channel) -> (row, inserted)`: advisory lock + head FOR UPDATE, 404 SITE_NOT_FOUND, 409
  IDEMPOTENCY_KEY_REUSED / OBJECTIVE_PRIOR_MISMATCH; `current(tenant_id, site_id, known_at)`; `tenant_id(slug)`,
  `site_id(tenant_id, code)`, `revision_id(...)`, `dispose()`), `objectives/composition.py`
  (`build_objective_store(url) -> store | None`), `declare_objective.py` (`main(argv, store=None)`; `fixture --file
  [--site]`, `declare ...`; skipped line for unimported Sites; exit 3 on refusal), `backend/conversions/demo-objectives.json`.
  Tests `test_out_d3_declare.py` + `test_out_d3_objective_store_postgres.py`: 17 passed.
  Guard `tools/checks/configuration-persistence.ps1`: `$objectiveWriter`/`$objectiveTables`/`$objectiveInsertsSeen`
  (pgWriters, actionForbidden line rule, statement rules, anti-vacuity) **and** an `objectives` configuration-domain
  entry (994a5462; adapter-isolation rule demanded it; KNOWN DEVIATION vs "no other rule changes" - tightening).
  Probes in `tools/writer_guard_probes.py`: `objective_insert_from_foreign_writer`, `objective_update_in_owned_writer`
  CAUGHT; control ALLOWED. Non-vacuity: removing the store INSERT fails check-architecture on both counters (reverted).
- check-all: 11/11 at the U2 head on a clean tree (estate self-tests 4 passed). check-architecture passes at 994a5462;
  **full check-all at 994a5462 not yet run** (held by coordinator during OUT-W's full suite).
- Per-unit review of U1-U3: a fresh reviewer is running (coordinator).

## Resume: U4 (only after coordinator says OUT-W merged; `git merge main` first; read.py summary() conflicts)
Anchors at 833e7c95 (re-check after merge):
- `site_outcomes/read.py`: `POLICY_VERSIONS` :33 (add `"objectives": objectives.POLICY`), `BoardServices` :66 (add
  `objectives: Any = None`), `_need` :110, `_shared` :145 (add `"objectives"` lambda per sheet), ports built in
  `mini_ports` :181, `cold_ports` :235, `ev_ports` :250 (pass `objectives=shared["objectives"]`), board wire :326
  (add top-level `"objectives"` list), `summary()` (objective_site_count).
- `site_outcomes/composition.py:47-73` `build_outcome_board_service`: add `objectives=build_objective_store(database_url)`,
  dispose it in `dispose()`.
- `site_outcomes/board.py`: `SiteFacts` :184 (add `objectives`, `readings`, `objectives_ok`); `_row` :368 calls
  `outcome_state` at :372-374 (pass verdict / objectives_ok); contributors built at the `row.update` (~:497) - append
  "Declared objective" contributors after domain contributors; NOT_MEASURED early return :386-388 stays.
- Composers: `mini.py` `MiniPorts` :99, `compose` :234 (`dispatch` read :250, `_dispatch_minutes` :361, Assure
  `FIXED["plan_target"]` :50/:574, SiteFacts :325); `cold.py` `ColdPorts` :77, compose :87, overview :96, objective block
  read :118, excursion `by_mech` :110-111, `_backup` :230-239, SiteFacts :157; `ev.py` `EvPorts` :58, compose :83,
  denominator :130-133, SiteFacts :202. Each Ports gets `objectives: Callable[[], list[dict]] = lambda: []` LAST.
- Then U5 (record Kobo 2026-10-21 dispatch avoidable/unclear and depth unserved_kwh first), U6, closeout
  (packet `.agent/OUT-D-packet.md` force-add, CODE_STATE, task file in_review, ACTIVE_CONTEXT, register R580-R586).
- Heavy jobs (full vitest, container suite, captures) need a coordinator go. pytest helper:
  `C:\Users\assef\AppData\Local\Temp\claude\C--Users-assef-Bineyame-AssetOpsV1\809ecc09-3853-48b6-b795-60539b50a963\scratchpad\pt.ps1 <tests>`
  (sets PYTHONPATH and the *_test URL). Write .py files with the Write tool or bash, never PowerShell Set-Content (BOM breaks the SQL extractor).
