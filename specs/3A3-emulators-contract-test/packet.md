# 3A3 packet: emulated native exports and the source contract test

Implementer (Claude, fresh), 2026-11-20. Branch `task/3A3-emulators` (dispatch name; spec §0 says `-contract`), base
`main` 3b3916d4f (RC4-F1 merged). Spec rev 2, rulings D-3A3.1-12. Mid-build questions: **1** (Q1, F3's spec gap; ruled D-3A3.13). `USER_REVIEW_REQUIRED:
false` (non-screen; Q1 `--accept-as` stays "owner to weigh in", not blocking).

Module paths (worktree `PYTHONPATH`): `assetops_backend` `/opt/assetecon/AssetOpsV1-3a3/backend/assetops_backend/__init__.py`,
`assetops_contracts` `.../AssetOpsV1-3a3/contracts/assetops_contracts/__init__.py`, `assetops_simulator`
`.../AssetOpsV1-3a3/simulator/assetops_simulator/__init__.py`.

## Files (spec §7 q9 list only)
`contracts/assetops_contracts/native/{__init__,layouts_v1}.py`; `commercial/{readers,uploads,composition,model,store}.py`,
`commercial/adapters/postgres_commercial_store.py`; `accounts/{model,store,service}.py`,
`accounts/adapters/postgres_account_store.py`; `i18n/messages.py` (`# 3A3` block); `load_emulated_exports.py`;
`simulator/.../world/exports.py`; `tools/world_history.py`; fixtures `backend/tests/fixtures/3a3/` (4 CSV + 4 hand-written
JSON); tests `contracts/tests/test_3a3_native_layouts.py`, `backend/tests/{source_contracts,test_3a3_source_contract,
test_3a3_single_writer,test_3a3_load_emulated,test_3a3_load_emulated_postgres}.py`, `simulator/tests/world/test_3a3_exports.py`;
`test_3a2_commercial_upload_service.py` (`read` signature only); `test_3c0a_accounts_service.py` (`tenant_slug`). No migration.

## Done questions (§7)
1. Yes: contracts 1 (four goldens read to the hand-written records, rows (2,3,4), render to the same bytes).
2. Yes: contracts 2-4, C3-C5, C8 (file-level `UPLOAD_FILE_REFUSED` "the file"/"row 4"; row-level codes with header field).
   `field_for` is empty: every blanked required header's first 2a refusal labels as that header (probed all 37).
3. Yes: S2; C1-C10 pass for all four cases.
4. Yes: E2-E7 (literals by hand). E7 pins (fixture `view_v1.json`; the runbook YAML
   `Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml` gives the same bytes):
   billing `7111a18fdf8ed36ad19c7339e1266395d70065886008b2839cbc0bacd4e16534`,
   collections `8b3cd80a03eaf2fa06f8f393189ca353bbd593ad6418b90551b4a3fd1a6352c3`,
   expenses `320c5442ccde0a97876b276cac63a722620f890041d3dc4413d20c3d84d2366d`,
   budget `5b03eb3e849031311c40bc13accd13c278867ddbf81bb0443e0c34d1c3bfcb7e`.
5. Yes: S1 (plus seven inline planted sources); `build_commercial_records` deleted.
6. Yes: L1 (3 operator names, 4 unclear URLs, `PGDATABASE`); spies untouched; no-connect fixture self-tested.
7. Yes: S4, C9.
8. Yes: all 21 plants fail their named tests (below).
9. Yes.

## Checks (revision 575a50e05 unless noted)
- Focused + regression, no DB: 3A3 service/S1/loader + 3A2 service/API + 3A1 + 3A4 + RC4-F1 + 3C0a + 3C1a: `467 passed` (47.7 s).
- `tools/checks/neutral_tests.py`: simulator/tests 503 passed, contracts/tests 33 passed.
- Postgres (`heavy-slot.sh --db` + `run-host-tests.ps1`, routed `*_test`): 3A3 P1-P3 + 3A2 + 3A4 + 3A1 Postgres files
  `65 passed` (26.4 s).
- `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed; fast check-all at 575a50e05: "All 40 guards passed
  (blocking; 0 advisory, 0 warned)", 1 m 34 s.
- Plants V1-V20 + V1b: plant, run named test(s), `git checkout`; each fails (`plants.log` in the scratchpad; V8 fails
  as the module fixture's `EMU_REVENUE` error). Tree clean after.

## Fix round r1 (review `review.md`; rulings D-3A3.13, D-3A3.14; head `40abd7e7b`)
- F3: budget prices = plan money / plan quantity, exact or `EMU_PLAN_PRICE <tenant>/<site> <factor>`; `PLAN_FIELD_ABSENT`
  and `PLAN_PRICE_UNDEFINED` listed; no read of `tenant.prices`. E8 plan-price case, new E10. E7 hashes unchanged.
- F1: `HeldUpload.submitted_by` (`_HELD` and mirror); `PERSON_SAME_FOR_BOTH` for a waiting upload the acceptor
  submitted (L6 new case). F6: the path is the reader ID (`_path` deleted); L5 gains the `profile-x` case.
- F2: C8 short-row and NUL-row cases for every case, C1 record count, C3 optional-header complement, `mapped=None`
  allowed only where the layout maps nothing (billing). F4: S1 flags any import of `build_commercial_uploads`
  outside `BUILD_CALLERS` (plant `builder-alias`). F5: L1 composition-path case (switch on, operator URL).
- Residual fixed: a DS1b record with no or a foreign `site_code` is listed `SITE_NOT_IN_TENANT` (E9 plants both).
- Plants, each failing as intended: V-F3a (E8 plan-price, E10), V-F3b (same), V-F3c (E8 plan-price), L6 (drop the
  check), L5 (restore canonical-vs-native), S1 (drop alias import rule), reviewer's plant A (C8 x4).
- Runs (worktree PYTHONPATH, paths verified): 3A3 focused 167 passed (14.6 s); 3A2 api/service, 3A4 months, RC4-F1,
  3c0a service, contracts/tests 216 passed (27.7 s); `heavy-slot.sh --db` run-host-tests `test_3a3_load_emulated_postgres.py`
  4 passed (10 s, routed `*_test`); fast check-all 40 guards passed (84 s).

## Known deviations
- D1. Fuel delivery days use `days_in(month) // m`, not the literal `31 // m`: DS1 R25a's guard (test_core T6) bans the
  literal 31 in world modules. Identical for October.
- D2. Withdrawn (review r1 F3): budget `tariff` and `diesel_price` are now plan money / plan quantity (D-3A3.13).
- D3. A non-whole plan money value raises `EMU_PRICE <tenant>/<site> <field>` (the spec names no code for it).
- D4. L2/L5 obtain the emulator's files by running `tools/world_history.py exports|records` in a child process: the
  dependency-direction guard bans `assetops_simulator` imports anywhere under `backend/`, tests included.
- D5. A rejected-row placeholder `{"format_version": 1}` is also used for `NATIVE_VALUE` (spec fixes it for
  `NATIVE_ROW`/`NATIVE_CHARACTER` only), so a refused row can never shadow a later row's ID as a 2a duplicate.
- D6. Five commits plus small follow-ups, not four (unit 3 fix for D1, test wraps, D4).

## Residual risk
- S1 does not see `importlib`/string-built names or a module handed a records service without importing the package
  (D-3A3.12).
- `ALREADY_WAITING` reads the waiting upload on the organisation path; a same-SHA upload waiting on a Site path would
  answer 404 → exit 3 (the loader only ever submits on the organisation path).
- D-3A3.10 residual (an emulated file hand-sent to an operator server is stamped `observed-financial`) stands as ruled.

## Review focus
`read_layout` rule C and `render_layout` agreement checks; `_check`'s reader-refusal override and out-of-range 500;
loader step order (2 before any composition; 5b one read); `exports.py` receipts walk and `written` filter.
