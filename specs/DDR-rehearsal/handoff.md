# DDR handoff (PARTIAL, phase 1 of the build)

**Superseded by phase 2 (2026-11-21): every "Next" item below is done; see `packet.md`.**

Builder (Claude), 2026-11-21, branch `task/DDR-rehearsal`, worktree `/opt/assetecon/AssetOpsV1-ddr`, head after
`fb587c24d`. Stopped at the context budget (standing brief), not at a blocker. Every R and I question of rounds 1 and
2 is answered (rulings.md R1-R17, I1-I6, P1-P3, A1). 3C2 unit 2 is **not** on `main` yet (no `StoreAgreedActions` in
`deep_dive/composition.py`; branch `task/3C2-unit2-store-actions` has no commits beyond main at 3e77a8575).

## Done (committed)

- `backend/tests/fixtures/ddr/`: `make_board_budget.py` (rewrites `build_workbook`'s zip: fixed order, 2026-07-02,
  deflate 9, `create_system` 0, no extras; all cells inlineStr; BB-16 has no Site cell), `ddr-board-budget.xlsx`
  (sha256 `2f629a1fc77a087932dbf565969b67ddd290395dcfb010a214782dd62576ad75`), `ddr-board-budget.profile.json`
  (sha256 `3752d604dbffefabf46095b2d45810273b8ba38eb23217d6ed6c4c4539ec82ff`), `ddr-board-budget.expected.json`
  (16 records typed from spec §3.3, `kind` BUDGET_LINE included as 3A6's form). Not yet admitted against a database:
  the first Postgres run of S2 proves the profile reads the sample.
- `portfolio_history` in the port, memory store and Postgres adapter (`structure_snapshot/store.py`,
  `adapters/postgres_structure_snapshot_store.py`, `_PORTFOLIO_HISTORY`).
- Runbook sections 6 to 12 (D-DDR.15), intro, shell variables, `_test` names (D-DDR.12), both copies identical
  (edit script was scratch). ON1 runbook table (`test_on1_served_tenant.py` §3): EXPECTED, `_parsers`, VALUES,
  KEY_DIR. Deviation MB1 (`mid-build-questions.md`): `source_profile list` added, so EXPECTED has 13 entries.
- `rehearsal_check.py`: docstring, `build_parser`, `Fail`, `GATES`, `STEPS` only.
- `backend/tests/test_ddr_rehearsal_check.py`: test 7 and test 6's memory half.
- Runs: `pytest tests/test_on1_served_tenant.py -k runbook` 7 passed; `tests/test_ddr_rehearsal_check.py` 2 passed.
  Plants: P8 (unsorted history) fails test 6; P14 (clock time) fails test 7; P16 (admit after load) fails test 9.

## Next

1. `rehearsal_check.main(argv, *, services=None)`: exit-2 codes (NO_DATABASE, NO_KEY_DIR, BAD_MONTH,
   EXPECT_UNREADABLE, UNKNOWN_TENANT), ten gates, §2.4 codes, `READ_FAILED` per gate. Keep every literal one token
   (UPPER_SNAKE or key) to stay clear of SC-1 rule (g) and rule (i) (no dict of 2+ Capitalised values; `"Amina"`,
   `"Peter"` live in the expect file, not the module).
2. `lakeside-2026-10.expect.json`. World B has **no full literal** in 5c's test (only partial asserts at
   `test_5c_deep_dive_view.py:321-329`); the full body is World A's `fixtures/5c/deep_dive_lakeside_2026-10.json`
   (compared whole at `:268`). Transcribe the `screen` by hand from that file + World B's asserts (`:324-329`) + §3.4's
   differences (names, KISIWA/KOBO/MTO order, notice, status line, SETUP in the fuel text, the not-available row).
   Expect this to raise mid-build questions where §3.4 and the fixture disagree.
3. `test_ddr_rehearsal_postgres.py` tests 1, 3, 4, 5, 6 (Postgres half); tests 8(a)-(g) in the no-DB file; the
   remaining plants (P1-P7, P9-P13, P15, P17) in a scratch copy.
4. When `main` holds 3C2 unit 2: merge main, run G10 and test 1's S11/S12. Then fast check-all, the packet,
   `Status: in_review`, the state entry.

## Anchors (from the survey; all under `backend/assetops_backend/`)

- Accounts: `accounts/composition.py:21` `build_account_service(url)` (dispose `._store.dispose()`);
  `accounts/service.py:129` `tenant_by_slug`, `:260` `onboard_person(email)` -> `OnboardPerson(person_id, ..., roles)`;
  grants via the store `people(tenant_id)` -> `PersonView(person_id, display_name, email, status, grants)`,
  `GrantRow(... role, site_code, by_service, ...)` (`accounts/model.py:52,71`).
- Sites: `commercial/store.py:104` `site_rows(tenant_id)` -> `SiteRow(site_id, site_code, site_type "MINIGRID")`.
- Keys: `commercial/pseudonym.py:126-138` `PseudonymKeyMissing/Erased/Unusable`, `PseudonymKeys.key(tenant_id)`;
  `commercial/composition.py:31` `FileKeyStore(dir)`.
- Uploads: `commercial/store.py:64` `held_uploads(tenant_id)` -> `HeldUpload(upload_id, reader, waiting, submitted_by,
  ...)`; the decision via `store.upload(tenant_id, upload_id)` -> `UploadRecord.decision.decided_by/decided_at`;
  `commercial/composition.py:143` `build_commercial_reads(url)` -> `CommercialReads(months, store, dispose)`.
- Profiles: `commercial/store.py:81` `source_profile_latest(tenant_id, profile_id)` -> `ProfileRow(version, status,
  profile_sha256, sample_sha256, admitted_by, ...)`.
- Statements: `commercial/store.py:95` `accounts_statements(tenant_id)` by `(recorded_at, id)` -> `StatementRow(period,
  site_id, revenue, fuel_cost, recorded_at, recorded_by, recorded_by_script, result_at_record)`;
  `structure/reconciliation.py:343` `CommercialReconciliation(reads.months, reads.store)`, `:363 check(...).opens`.
- Snapshots: `structure_snapshot/composition.py` `build_structure_snapshot(url)` -> `(builder, read, store, dispose)`;
  `read.portfolio(tenant_id, month)` -> `Served(state, snapshot, as_of, freshness(current, reasons))`; `asked` is on the
  decoded snapshot (`structure_snapshot/model.py:76`), not on `SnapshotRow`.
- Inputs: `structure/composition.py:40` `build_structure_read(url).read.site_inputs(site, month)` -> `leaves`
  (`in_transit`, `diesel_price`), `stated`; `collected` is computed (`read.site(...).values["collected"]`);
  `structure/targets/composition.py:22` `build_target_read(url).read.site(...)` -> `SiteTargets.checks`
  (`TargetCheck(factor_id, stated, computed, currency, agrees)`).
- Screen: `deep_dive/composition.py:32` `build_deep_dive_read(url)` -> `(read, dispose)`; `deep_dive/read.py:43`
  `month(TenantRef, month, names)`; route `deep_dive_api.py:44-64`; `sites/cutover.py:50,71,90`.
- Actions: `actions/composition.py:229` `build_agreed_actions(url, clock=)` -> `(service, dispose)`;
  `actions/agreed.py:262 for_tenant` -> `AgreedActionView(title, site_code, factor_id, owner_name, created_by_name,
  due_on, ...)`; `record_action.py:70 main(argv, *, services=None, clock=None)`.
- Steps: `source_profile.py:149 main(argv, *, profiles, accounts)`; `load_emulated_exports.py:276`;
  `onboard_operator.py:126`; `reconcile_month.py:206`; `build_structure_snapshot.py:104`.
- Harness: `tests/pg_harness.py:392 empty_tables(engine, roots)`; pattern `tests/test_on1_onboarding_postgres.py:17-62`
  (env via monkeypatch, `from test_s1_bindings_postgres import engine, store`); exports via subprocess as
  `tests/test_3a3_load_emulated.py:93-101`; SC-1 from a test as `tests/test_3c2_agreed_actions.py:432-436,481-483`.

## Risks

- MB1 open. The §3.4 screen transcription (no World B full literal) is the largest remaining unit and the likeliest
  source of further mid-build questions. `collected` is computed, not a leaf: G4 reads it through `read.site`.
