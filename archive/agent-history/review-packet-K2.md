# Review packet: DIESEL-K2 (fuel delivery and tank dip records, migration 0054)

**Task:** the K2 card, `.agent/build-sheet-DIESEL-1.md` §9c.2 (ruling DIESEL-1-R3c, commit e6e3bedd1).
**Branch:** `task/DIESEL-K2-fuel-records`, from main `099b57c96`. **DB:** `assetops_k2_test` and its harness clones only.

## Outcome delivered

- `FUEL_DELIVERY` and `TANK_DIP` are posted through the existing `POST .../work/operational-records`. Each names its tank in the optional `asset_id` key.
- The five new 422 refusals carry the card's literal messages, in the card's order: `WORK_RECORD_ASSET_REQUIRED`, `_ASSET_NOT_ALLOWED`, `_ASSET_NOT_TANK`, `_QUANTITY_INVALID` and `_TICKET_REQUIRED`.
- Canonical hash: `asset_id` is added to `canon` only for a fuel kind, so the four existing kinds hash byte-equal. The `operational-record-1` response is unchanged.
- Migration `0054_operational_fuel_records` (down_revision `0053_fuel_cost_2`) is exactly the card's SQL. Its downgrade refuses with `RuntimeError("0054 downgrade requires no FUEL_DELIVERY or TANK_DIP operational records")`.
- The as-known read for K3:
  - `work/fuel_records.py` has `FUEL_KINDS`, the frozen `FuelRecord`, `FuelRecordsPort` and `check_window`.
  - `work/adapters/postgres_fuel_records.py` has `select_fuel_records(c, ...)` on the caller's connection, and `PostgresFuelRecords`, one REPEATABLE READ READ ONLY transaction per call.
  - The selection is the `_OPERATIONAL` root/head shape, with membership decided by the head's kind, tank and occurrence.
- Frontend:
  - `REC_KIND_LABEL` gains "Fuel delivery" and "Tank dip".
  - `FuelRecordKind` is added, and `GlobalOperationalRow.kind` is widened to include it.
  - Chips, `KIND_ZERO`, `GLOBAL_OPERATIONAL_KINDS` and the backend `RECORD_KINDS` are unchanged. This is MOCK DEVIATION MD-FUEL-K2-1: no chip is added, and `?kind=FUEL_DELIVERY` keeps the existing invalid-filter refusal.

## Files materially changed

- `backend/assetops_backend/work/service.py`: kinds, optional keys, `_fuel_asset` (step 2), in-transaction tank checks, insert of `asset_id`.
- `backend/assetops_backend/work/model.py`: five codes in `MESSAGES` and `STATUS`.
- `backend/assetops_backend/work/adapters/postgres_work_store.py`: `_Tx.asset_type`, plus the `asset_id` column on the insert.
- `backend/assetops_backend/work/fuel_records.py` and `backend/assetops_backend/work/adapters/postgres_fuel_records.py` (new).
- `backend/migrations/versions/0054_operational_fuel_records.py` (new).
- `tools/checks/configuration-persistence.ps1`: the new adapter is added to the rule-8 `$pgReaders` list. It is a named reader, and the SQL-write refusal still applies to it.
- `frontend/src/work/WorkRequestRecord.tsx` and `frontend/src/work/globalWorkClient.ts`.
- Tests:
  - `backend/tests/test_k2_fuel_records.py` (L0, new);
  - `backend/tests/test_k2_fuel_records_postgres.py` (L2, new);
  - `frontend/src/work/__tests__/operationalRecords.test.tsx` and `workRequestRecord.test.tsx`;
  - head and catalog enumerations in `test_fuel_cost_v2_postgres.py` and `test_w401_migration_postgres.py` (see Known deviations).

## Hash pin (existing kinds byte-equal)

- I wrote `k2_pin.py` in the session scratchpad. It posts `oprec(occurred_at="2026-11-01T00:55:00Z")` (OPERATOR_LOG) through `WorkService` on a fake transaction, with tenant `...0001`, site `...0002` and id `...00aa`.
- I ran it on the K2 worktree at `099b57c96` with a clean tree (`git status --porcelain` empty) before any edit.
- Result: `payload_sha256 = 078d5fcc2e16d8e3aff4c26f6f9044cbff296f9a33dd1d95d81436c9b9a23a1d`.
- The same body through the K2 code gives the same hash. `test_k2_fuel_records.py::test_operator_log_hash_equals_main_pin` pins it and also pins the full response body.

## Acceptance criteria (card §9c.2)

| Item | Status |
|---|---|
| Two kinds on the existing route, with `asset_id` | Met (L0 and L2 `test_post_delivery_and_dip`) |
| Closed shape: optional = correction triple + `asset_id` | Met (`test_kind_tuples`) |
| Refusal order, step 2 | Met. One L0 test per step, plus cross-step ordering cases (asset before period/quantity, quantity before ticket, ticket before UUID) |
| In-transaction: unknown or foreign asset gives `WORK_LINK_SCOPE_INVALID`; non-tank gives `WORK_RECORD_ASSET_NOT_TANK` | Met (L0 and L2 `test_asset_scope_and_type`) |
| Hash byte-equal for existing kinds; response unchanged | Met (pin above) |
| Migration 0054 SQL, index, downgrade refusal and restore | Met (L2 up/down/up checks constraint text and diffs; refused-downgrade test) |
| CHECKs hold below the service | Met (raw inserts violate `fuel_asset`, `fuel_quantity`, `delivery_ticket` and `asset_fk`) |
| `fuel_records`: half-open window, recorded after K absent, correction head and root, moved occurrence drops, OPERATOR_LOG never appears, argument checks | Met (`test_fuel_records_as_known`, `test_fuel_records_window_arguments`) |
| Global list returns fuel rows; `?kind=FUEL_DELIVERY` refused like any unsupported kind | Met (`test_global_operational_records_list`) |
| Frontend labels; no chip; reading line unchanged | Met (two vitest additions) |
| No forbidden guard words | Met (grep of all changed paths is empty) |

## Checks run

Environment for every run below:
- Python: `AssetOpsV1-plan2\.venv`.
- PYTHONPATH: the worktree's `backend;contracts;tools;simulator;gateway;host;field;backend\tests`. `assetops_backend` and `assetops_contracts` both resolve into the K2 worktree.
- Postgres URL: `ASSETOPS_TEST_DATABASE_URL=...127.0.0.1:55432/assetops_k2_test`, harness-cloned per module.
- Free RAM was 3.98 GB or more before each Postgres step, and only one heavy step ran at a time.

| Check | Revision | Result |
|---|---|---|
| L0 `tests/test_k2_fuel_records.py`, no DB | b4865a03e | 15 passed |
| L2 `tests/test_k2_fuel_records_postgres.py` | 4515e7b8a tree | 8 passed (26 s) |
| `test_w401_work_service_postgres`, `test_w401_work_api`, `test_w401_migration_postgres`, `test_w401_work_read_postgres`, `test_w401_site_indexes_postgres` | b4865a03e | 29 passed, 1 failed. The failure was `test_0027_parent_scoped_fks...`, with `all_indexes` 46 against 45: the 0054 index. This is deviation 1. |
| `test_w401_migration_postgres` + all `test_w601*` (a, b, c, e) + `test_fuel_cost_v2_postgres.py::TestMigration0053` | 4515e7b8a | 73 passed (14 min 0 s) |
| vitest `operationalRecords.test.tsx` + `workRequestRecord.test.tsx` | b4865a03e | 36 passed |
| `tsc --noEmit` | b4865a03e | exit 0 |
| `tools/check-architecture.ps1` | 4515e7b8a | passed |
| `tools/check-agent-workflow.ps1` | 4515e7b8a | passed |
| `tools/check-navigation-truthfulness.ps1` | 4515e7b8a | passed |
| `node tools/checks/frontend-hardwiring.mjs` | b4865a03e | passed; totals api 12, href 24, lit 70, cmp 51, code 3 |

The `$pgReaders` entry is non-vacuous:
- With the line removed, `check-architecture.ps1` exits 1 and reports three violations: "Database driver imported outside ... in backend/assetops_backend/work/adapters/postgres_fuel_records.py:15/16/17".
- I then restored the file with `git checkout`, and `git status` was clean.

Not run, as the dispatch instructed: the full suites, prepare, `test_demo_combined_postgres`, the production build and layout evidence. The UI change is two label strings and no layout.

## Known deviations

1. **`test_w401_migration_postgres.py` `INDEX_TOTAL`** changes from `11 + 27 + 7` to `11 + 27 + 7 + 1`.
   - The test counts every index on the eleven W4 tables, and the card's index `operational_record_asset` adds one.
   - This is a catalog enumeration, not a behaviour change. It is the same class as the card's allowance for tests that enumerate migration heads or the kind CHECK text, but it is not literally named in that allowance.
   - The reviewer should confirm it.
2. **`test_fuel_cost_v2_postgres.py`** pinned `0053_fuel_cost_2` as the single head, and after its refused downgrade.
   - These now read `alembic_head()`. The `down_revision` assertion is unchanged.
   - This is a head enumeration, which the card allows. The test was not in the card's list, but it would fail on main after merge.
3. **Rule-8 guard list.** `postgres_fuel_records.py` is added to `$pgReaders`, which the card did not mention. Without it, rule 8 rejects the driver import. The guard is extended, not loosened: the SQL-write refusal still applies to the module.

## Residual risk

- `FUEL_KINDS` is defined in both `service.py` and `fuel_records.py`, because the card names both places. An L0 test asserts they are equal.
- Validation order: body text, idempotency key and `case_id` shapes are checked during canonicalisation, after step 2. A fuel body with a missing `asset_id` and an invalid body text therefore gets `WORK_RECORD_ASSET_REQUIRED`, not `WORK_INPUT_INVALID`. This is consistent with the card's step list, which does not include those shapes in step 1.

## User-review focus

- Deviations 1 to 3.
- MD-FUEL-K2-1: fuel rows appear only under All, labelled "Fuel delivery" and "Tank dip".
