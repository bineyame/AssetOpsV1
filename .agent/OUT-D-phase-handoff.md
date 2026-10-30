# OUT-D phase handoff (partial: U1-U4 done, U5 in progress)

## Update 2026-10-31 (second implementer)
- `f602e7b6` merge main 9ebb3d1c (OUT-W), no conflicts. `91c8d6fd` L1 (zero AT_LEAST refused; target_text always
  substitutes), L2 (Site-level key reuse 409 + IntegrityError backstop, `_same_key` staticmethod), L3 test tag,
  fixture `outcome-status/2`.
- `0f0e8a0d` U4: `site_outcomes/objective_facts.py` (from_rows, chamber_range, catalogue_index, assure_text, COPY);
  `board.py` objective_verdict / objective_verdicts / objective_contributor / objectives_wire (board.py may import only
  outcomes.*); composers' `mini_readings`, `cold_readings`, `ev_readings`; read.py port, wire `objectives`,
  `policy_versions.objectives`, summary `objective_site_count`. Test `test_out_d4_board.py` (15). U4 review requested.
- U5 (uncommitted at time of writing): `PortfolioOutcomes.tsx` `assureDetailText`, `estateClient.ts` type,
  fixtures `objective_site_count: 0`, tests in `estatePortfolio.test.tsx` + `outcomeBoard.test.tsx` (16 related files
  386 passed; `vitest related` itself crashes on a .py import - tooling, used explicit file list).
  `test_out_d5_objectives_postgres.py`: one DB per producer (no combined dataset exists), so the summary count is 1
  per DB, not 3 (Known Deviation). Full-log helper: scratchpad `ptlog.ps1 <log> <tests>` (pt.ps1 truncates to 25 lines).
- Then U6 (captures need coordinator go), register R580-R586, closeout.

## State at f6be0782 (implementer 3): U4 REVISE fixes landed
- M1 `mini.PLAN_NOT_READ` (in COPY) when `objective_rows is None`; test `test_failed_objectives_read_never_says_no_target_declared`.
- M2 board body `objectives_read`; `summary()` counts only Sites with board loaded AND objectives read; new
  `objective_sites_unread = len(sites) - read`; `Boards` fake has an "unread" case. Frontend `assureDetailText`
  (PortfolioOutcomes.tsx) 4 cases, 4 vitests in estatePortfolio.test.tsx; fixture default unread 0. D5 records unread.
- L1 `ObjectiveFact.source_note` (last, default None) -> `objectives_wire`; explainer `EXPLAIN[3]` (OutcomeBoard.tsx).
- Extras: `test_cc1_on_track_with_no_excursion_and_a_complete_window`; mini MG2_LONGER/MG2_UNCLEAR/MG5_UNSERVED
  templates; `ev.interrupted_text` used by `ev_readings` and COPY.
- Checks: d4 17 passed; U4 focused set 221 + C set 54 passed; tsc clean; src/sites+src/estate vitest 1914 passed,
  4 failed = 3 known w1f4 + evEnergy R347 (load flake; 12/12 alone). check-all 11/11 at f6be0782.
- Next: U6 (each heavy step needs coordinator go), then closeout.

## State at da1df531 (implementer 2 stopped on context budget; resume HERE)
Committed: `79c8d40a` U5 frontend; `da1df531` D5 Postgres test (Kobo + cold passed in one run, EV passed on a re-run
after the R577 handling) + register R580-R586 section at the end of `.agent/mock-departure-register.md` + R542 note.
Recorded real data (for the packet): Kobo 2026-10-21 unsettled (STALE_PROJECTION) -> all rows UNKNOWN, MG-2 0
avoidable / 60 unclear, unserved_kwh None, all three Not checked yet, Assure "0 of 3 declared objectives met · 3 not
checked yet", summary count 1, K1 reproducibility holds; GreenHarvest (policy 2-4°C) CC-1 + CC-6 Missed, states
NOT_MEASURED/NEEDS_ATTENTION/NEEDS_ATTENTION/WATCH, count 1; Depot EV-1 Missed ("1 interrupted"), EV-2 no line, board
PARTIAL, summary 409 ESTATE_SELECTION_INCONSISTENT (R577). No On track anywhere (R585).

### U4 review REVISE - Architect rulings to implement next (plan2 `.agent/OUT-D4-review.md`, coordinator message)
- M1: mini `compose` (block "OUT-D U4: declared objectives" before `facts = SiteFacts(`): when `objective_rows is None`
  the `actual_against_plan` text is exactly "Not available yet · declared objectives could not be loaded" (no chip,
  href None); add to mini COPY; test that a failed read never shows "no target declared" (test_out_d4).
- M2: read.py `board()` adds `"objectives_read": comp.facts.objectives_ok`; `summary()` counts only Sites whose board
  loaded AND objectives_read; `objective_site_count` None when no Site read; add `objective_sites_unread` = the rest,
  failed boards included. Update the `Boards` fake in test_out_d4. Frontend: `objective_sites_unread: number | null`
  on `EstateOutcomeSummaryBody`; `assureDetailText` (PortfolioOutcomes.tsx ~:175): unread 0 & n>=1 "targets declared at
  {n} {site|sites}"; unread 0 & n=0 "no targets declared"; unread>=1 & n>=1 "targets declared at {n} {site|sites}, {u}
  {site|sites} not checked"; unread>=1 & n 0/null -> no clause ("No verified result yet · {gap}"). Fixture default
  `objective_sites_unread: 0`; extend `assureNamesDeclaredTargets...` (estatePortfolio.test.tsx). D5: record unread.
- L1: `frontend/src/sites/OutcomeBoard.tsx` "About this view" explainer: append the paragraph "A declared objective is a
  target set for this demonstration so the status can be shown. It is not the customer's target." `objectives_wire`
  carries `source_note` (suggest `ObjectiveFact.source_note: str | None = None` as LAST field; from_rows fills it from
  the row; CC-1 None). Lines still show only "Declared objective".
- Review extras: a cold test with no excursion + complete window -> CC-1 ON_TRACK; record the real
  `objective_site_count` in U5 (done: 1 per DB); L2 tidy COPY formatting in mini/ev and build the EV example texts from
  the template (factor the text in `ev_readings` into a helper and use it in COPY).
- Then check-all, give the coordinator the hash. U6 captures and full suites need the coordinator's go. Closeout:
  create `tasks/OUT-D-declared-objectives.md` (none exists; model on tasks/OUT-W-estate-event-windows.md, Status
  in_review, USER_REVIEW_REQUIRED false for merge), packet `.agent/OUT-D-packet.md` (force-add), CODE_STATE entry after
  "## OUT-W" (~:6088), ACTIVE_CONTEXT line 8.
- Known deviations so far: summary count 3 not provable on one DB (no combined dataset, R535) -> 1 per DB, EV 409
  (R577); verdict helpers in board.py (purity test); U3 guard domain entry; Kobo verdicts all Not checked yet (sheet
  expected Missed; recorded, not forced); `vitest related` crashes on a .py import, so the explicit related-file list was
  used (16 files, 386 passed).

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
