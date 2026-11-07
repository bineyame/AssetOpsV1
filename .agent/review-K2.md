# Review: DIESEL-K2 (fuel delivery and tank dip records, migration 0054)

**Reviewer:** independent first review (Claude, fresh context). **Branch:** `task/DIESEL-K2-fuel-records`, worktree `AssetOpsV1-k2`.
**Diff reviewed:** `git diff 099b57c96...HEAD` (head `e9879740b`). **Spec:** `.agent/build-sheet-DIESEL-1.md` §9c.2.

## Verdict: ACCEPT

The slice matches the K2 card. I found one Low test gap and no High or Medium findings. The Low does not block the merge. It can be closed on the branch or carried into K3's card.

## Findings

### L1 (Low, test gap): head-based kind and tank membership in `fuel_records` is untested

- **Where:** `backend/assetops_backend/work/adapters/postgres_fuel_records.py:33` (`h.kind IN (...) AND h.asset_id = :a`) and `backend/tests/test_k2_fuel_records_postgres.py:263-277`.
- **What is wrong.** The card says to keep a record whose **head** has a fuel kind and `asset_id = tank`. The code does this. No test fails if the query reads the root's kind and tank instead. I mutated a copy of the package to `r.kind IN (...) AND r.asset_id = :a`, and `test_fuel_records_as_known` still passed. Every other mutation I tried was caught (see below).
- **Why it matters.** `post_operational_record` does not stop a correction from changing `kind` or `asset_id` (`service.py:474-530`, `_successor` checks only the lineage). So these cases are reachable:
  - a dip recorded on tank A and corrected to tank B;
  - a TANK_DIP corrected to an OPERATOR_LOG ("not a dip").
  If a later edit read the root's kind or tank, K3 would keep counting that dip on tank A, or would keep a record that is no longer a fuel record. The fuel balance would be wrong, and no test would show it.
- **Fix.** In `test_fuel_records_as_known`, add one correction that moves a dip to a second tank, or changes it to OPERATOR_LOG. Then assert the record leaves the tank-A read after the correction's `recorded_at` and stays before it. Kobo has one `fuel-tank`, so changing the kind is the cheaper case.
- **Classification:** test gap only. The behaviour is correct today.

## What I verified (not taken from the packet)

1. **API against the card.**
   - Closed shape: optional keys = correction triple + `asset_id`.
   - `OPERATIONAL_KINDS` and `FUEL_KINDS` are as listed.
   - The five codes are in `MESSAGES` with the card's literal text (compared character for character), all 422.
   - Step-2 order in `_fuel_asset` (`service.py:535-552`): asset required, then not allowed, then `period_end`, then quantity/unit L/delivery > 0, then ticket, then UUID.
   - `"asset_id" in body` refuses a present-but-null key on non-fuel kinds, as the card requires.
   - In-transaction order: retry, occurrence, case scope, then `asset_type` None gives `WORK_LINK_SCOPE_INVALID`, and a type other than `FUEL_TANK` gives `WORK_RECORD_ASSET_NOT_TANK`.
   - `canon["asset_id"]` is set only when `asset_id is not None`, which happens only for fuel kinds.
   - The response is unchanged.
2. **The hash pin is real.**
   - I exported `099b57c96` with `git archive` (the `backend/assetops_backend`, `backend/tests`, `backend/conversions` and `contracts` trees) to a scratch directory.
   - I ran the same `oprec(occurred_at="2026-11-01T00:55:00Z")` body through **main's** `WorkService` on a fake transaction.
   - Result: `078d5fcc2e16d8e3aff4c26f6f9044cbff296f9a33dd1d95d81436c9b9a23a1d`. This equals `OPERATOR_LOG_SHA` in `test_k2_fuel_records.py:27`, and main's response body equals the pinned one.
   - Mutating K2's code to always add the `asset_id` key fails the pin test.
3. **Migration 0054.**
   - The SQL matches the card. The `_in()` helper produces the identical literal lists.
   - `down_revision = "0053_fuel_cost_2"`.
   - The downgrade takes an ACCESS EXCLUSIVE lock, refuses with the card's literal while fuel rows exist, then drops in reverse order and restores the four-kind CHECK under the same name.
   - The L2 tests cover all of this, and they passed for me: up/down/up on an empty table with exact constraint text and a diff of columns, indexes and constraints; the refused downgrade; the single head; raw inserts violating all three CHECKs and the FK.
   - `main` (`3b09aea6c`) has no new migration since `099b57c96` and no change to any K2-touched file. `git merge-tree main HEAD` is clean.
4. **`fuel_records` read.** The SQL is the `_OPERATIONAL` root/head shape (`postgres_global_read.py:73-82`), with membership moved to the head's kind, tank and occurrence. Argument checks run in both entry points. Mutation results on `test_fuel_records_as_known`:

   | Mutation | Result |
   |---|---|
   | `< :hi` → `<= :hi` | killed |
   | `>= :lo` → `> :lo` | killed |
   | `p.recorded_at <= :k` → `<` | killed |
   | head occurrence → root occurrence | killed |
   | head ordering reversed | killed |
   | head kind/tank → root kind/tank | **survived** (L1) |

5. **L0 mutations on the service, all killed:**
   - no zero-delivery refusal;
   - null `asset_id` allowed on non-fuel kinds;
   - ticket check before quantity;
   - non-tank type check skipped.
6. **Frontend.**
   - The `REC_KIND_LABEL` entries are "Fuel delivery" and "Tank dip".
   - `FuelRecordKind` is added and `GlobalOperationalRow.kind` is widened.
   - Chips, `KIND_ZERO`, `GLOBAL_OPERATIONAL_KINDS` and backend `RECORD_KINDS` are unchanged.
   - MD-FUEL-K2-1 is labelled in `globalWorkClient.ts` and `WorkRequestRecord.tsx`.
   - The new vitest asserts the five chips exactly, no raw kind text, and no "Reading:" line.
   - None of theft, stolen, stole, siphon or pilfer appears in any added line.
7. **Deviations.**
   - (1) `INDEX_TOTAL + 1`: a catalog count of the new partial index. No behaviour assertion changed. Accepted.
   - (2) `test_fuel_cost_v2_postgres`: only the head pins move to `alembic_head()`, which is the project's CH1a-R D6 pattern. `down_revision == PREVIOUS` is kept. Accepted.
   - (3) Rule-8 `$pgReaders`: I read the guard (`configuration-persistence.ps1:1040-1050`). Membership only admits the driver import. The `-not $isWriter` SQL-write refusal still applies, so the guard is extended, not loosened. Accepted.
8. **Regression to W401/W601 and existing records.**
   - Existing kinds store `asset_id` NULL, which MATCH SIMPLE leaves unchecked. Their hash is pinned.
   - No other backend reader enumerates kinds except the two filter `RECORD_KINDS` tuples, which are intentionally unchanged.
   - `recKindLabel` falls back to the raw kind, so it cannot crash.

## Checks I ran (worktree code, imports verified to resolve into `AssetOpsV1-k2`)

Python: `AssetOpsV1-plan2\.venv`. DB: `assetops_k2_test` and its harness clones only. Free RAM was 3.85 to 4.23 GB before each Postgres step.

| Check | Result |
|---|---|
| `tests/test_k2_fuel_records.py` (L0) | 15 passed, 0.44 s |
| `tests/test_k2_fuel_records_postgres.py` (L2) | 8 passed, 27 s |
| `test_w401_migration_postgres.py`, `test_fuel_cost_v2_postgres.py::TestMigration0053`, `test_w401_work_service_postgres.py`, `test_w401_work_api.py` | 25 passed, 295 s |
| `test_w601e_operational_index.py` | 12 passed, 174 s |
| Pin recomputed on `099b57c96` (scratch export) | equals the committed literal |
| L0 mutations (5) / L2 read mutations (6) | 5/5 killed / 5/6 killed (L1) |
| `npx.cmd tsc --noEmit` | exit 0 |
| vitest `operationalRecords.test.tsx` + `workRequestRecord.test.tsx` | 36 passed (vitest ran in this session) |
| `tools/check-architecture.ps1` | passed. A first run without `ASSETOPS_GUARD_PYTHON` failed because the worktree has no `.venv` and the rule-8 extractor could not start. That is environmental and unrelated to K2. It passed with the variable set to the plan2 venv. |
| `tools/check-agent-workflow.ps1` | passed |

**Not run (dispatch):**
- full suites, prepare, `test_demo_combined_postgres`;
- `test_w401_work_read_postgres`, `test_w401_site_indexes_postgres`, `test_w601a/b/c`;
- the production build and layout evidence. The UI change is two label strings, with no layout change.

For the files I did not run, I rely on the implementer's run, which the packet records at `4515e7b8a`. HEAD differs from that revision only by the packet commit.

## Residual risk (not in the packet)

- **Cross-kind corrections are allowed.** An OPERATOR_LOG root corrected into a FUEL_DELIVERY becomes a fuel record. Its `code` and `root_recorded_at` then come from the log, so K3's `DELIVERY_RECORDED_LATE` would measure lateness from the log's first recording. This conforms to the card. K3's card should state whether that is intended.
- **The read does not use the partial index.** `operational_record_asset` is not used by the read's lateral per-root scan, because tank and occurrence are filtered on the head. That is fine at demo scale (one Site, tens of records per night), but it scales with all of a Site's operational records for every K3 call.
- **The hash pin covers one OPERATOR_LOG body.** MANUAL_READING and correction bodies share the same `canon` path and are not pinned separately. The always-add mutation shows the single pin is enough to catch the plausible regression.
