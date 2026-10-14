# S4-02a phase 1 handoff: assumption store and SYSTEM publication

Branch `task/S4-02a-site-assumptions`, from `ec74ac6`. Commits: `28668d9` (the build) and the follow-up commit that
sharpens the history-rewrite test (see `git log ec74ac6..HEAD`). Phase 1 = packet "Reviewable phases" row 1, plus
contract items 1-2. Nothing from phase 2 has been built.

## What was built (anchors)

- **Migration** `backend/migrations/versions/0010_financial_assumptions.py`, revision `0010_financial_assumptions`,
  down-revision `0009_finding_store` (it is now the alembic head).
  - `financial_assumption_revision` :38. One immutable, authored Site price:
    - key CHECK is `diesel_price_per_litre` only; ISO currency; unit `currency/L`;
    - `numeric` value with `>= 0 AND < 'Infinity'` (this also excludes NaN, because NaN sorts above Infinity);
    - basis enum (no SCENARIO); non-blank source; authored `[valid_from,valid_to)` with `valid_from < valid_to`;
    - server `recorded_at`; `change_kind`, with a reason required if and only if it is CORRECTION;
    - actor kind/id; nullable `author_id`, which must be set if and only if the actor is HUMAN, which in turn requires channel `HUMAN_API`;
    - authorization basis, `provenance` jsonb, `idempotency_key`, `request_sha256`;
    - `prior_revision_id`, which must be NULL if and only if `revision_no = 1`.
    - Uniques: `(tenant,site,key,revision_no)` and the publication key `(tenant,site,key,idempotency_key)`.
    - Append-only through the existing `ledger_append_only()` trigger (:117).
  - `financial_assumption_assignment` :83.
    - Columns: `revision_id` (the price row) and `publication_revision_id` (the publication that recorded this row; a remainder keeps its old `revision_id`).
    - CHECKs keep both ranges non-empty.
    - GiST `EXCLUDE` :103, exactly as the packet item 1 shape.
    - Indexes on the valid axis, the recorded axis, current rows and revision.
  - Set-once `recorded_to` trigger :121/:136 (modelled on `foundation_revision_immutable`): every other column is immutable, and DELETE is refused.
  - Two-table containment trigger :143/:169 (BEFORE INSERT). It requires three things:
    - the assignment's valid range lies inside the revision's authored range;
    - `recorded_from >= revision.recorded_at`;
    - `recorded_from >=` the series' latest `recorded_from`.
- **Pure contract** `backend/assetops_backend/financials/assumptions.py`:
  - `SYSTEM_PUBLISHER` stable service principal :47 (`service:assetops-assumption-publisher`);
  - `Publication` :64;
  - `validate` :92 (typed 422s);
  - `request_sha256` :127 (the exact-retry digest);
  - `plan_assignments` :174 (the change_kind overlap rules and typed 409s).
- **Store (sixth product DB writer)** `backend/assetops_backend/financials/adapters/postgres_assumption_store.py`. `publish` :99 runs in one READ COMMITTED transaction, in this order:
  1. `pg_advisory_xact_lock(hashtextextended('financial_assumption:'||t||s||k))`;
  2. idempotency lookup: identical digest returns the same ID with `replayed=True`; a different digest is 409 `IDEMPOTENCY_KEY_REUSED`;
  3. expected-prior check: 409 `PRIOR_REVISION_MISMATCH`;
  4. `SELECT clock_timestamp()`, which must be later than the series' latest `recorded_from` (409 `RECORDED_TIME_NOT_LATER`);
  5. plan;
  6. insert the revision, set `recorded_to = t` on the closed rows, and insert the new rows at `recorded_from = t`.

  `revisions` :178 and `assignments` :185 return raw rows for phase 2. `site_scope` :87 resolves tenant slug + code.
- **Composition** `backend/assetops_backend/financials/composition.py`. Under adapter isolation, this is the only importer of the store.
- **CLI** `backend/assetops_backend/publish_assumption.py` :102, with `publish` and `fixture` subcommands.
  - There is no actor or author flag. Each run requires an explicit `--site`, source, `--expected-prior <uuid|none>` and `--idempotency-key`.
  - Channels are `SYSTEM_CLI` and `SYSTEM_FIXTURE`. Provenance records service, job, fixture name/version/step and the fixture file's sha256.
  - It exits 3 on a typed refusal, 2 on an unknown Site, tenant or step, and 1 when the store is unavailable.
- **Fixture** `backend/conversions/demo-diesel-price-publications.json`. Its USD values are labelled illustrative.
  - v1: INITIAL, 1.25 from 2026-01-01, open-ended.
  - v2: SUCCESSION, 1.32 from 2027-01-01.
  - v3: CORRECTION, 1.19 over [2026-06-01, 2026-07-01), with a reason.
- **Human write route** `backend/assetops_backend/financial_api.py` :59 `POST /api/sites/{site_code}/financial-assumptions`, wired in `main.py` after the Finding router. Refusal order:
  1. 401 `UNAUTHENTICATED` from the default access `no_verified_principal` :37;
  2. 422 `CLIENT_ACTOR_FORBIDDEN` for any nested key containing actor, author or principal (malformed JSON is 422 `BODY_NOT_JSON`);
  3. 403 or 404 from the seam, or 404 for an unknown Site;
  4. an admitted request still gets 401 `HUMAN_PRINCIPAL_REQUIRED`.

  It never imports `development_access`, and a test asserts this.
- **Guard** `tools/checks/configuration-persistence.ps1`:
  - Rule 8 lists the sixth writer. The store may only INSERT into its two tables, and its only permitted UPDATE is `UPDATE financial_assumption_assignment SET recorded_to = :x WHERE`. No other module may write either table.
  - A database-only `financials` domain is added for adapter isolation. Its `UserRootVar` is `$null`, and the user-root rule now skips null roots (only this domain has one).

## Persisted demo history (as proved by the test after a restart)

The fixture produces six assignment rows:
- v1 `[01-01,∞)`, recorded `[r1,r2)`;
- v1 `[01-01,2027-01-01)`, recorded `[r2,r3)`;
- v2 `[2027-01-01,∞)`, recorded `[r2,∞)`;
- v1 `[01-01,06-01)`, recorded `[r3,∞)`;
- v1 `[07-01,2027-01-01)`, recorded `[r3,∞)`;
- v3 `[06-01,07-01)`, recorded `[r3,∞)`.

`value::text` reads back exactly as `1.25`, `1.32` and `1.19`. Re-running the fixture replays every step: the IDs are the same, no rows are added, and `recorded_to` is unchanged.

## Commands run and results

- `pytest tests/test_s4_assumption_publication.py`: 30 passed. This file covers pure planning, validation and route refusal order.
- `pytest tests/test_s4_assumptions_postgres.py`: 15 passed (DB `assetops_s402a_test`). It covers:
  - the fixture history, with a restart and a replay;
  - history-rewrite refusals;
  - one negative per change_kind, including the INITIAL overlap;
  - retry and idempotency conflict;
  - stale prior;
  - a 4-way prior race (exactly one wins, three get `PRIOR_REVISION_MISMATCH`);
  - a 3-way identical retry (one revision);
  - DB value, containment, exclusion and empty-range guards.
- Full backend: `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_s402a_test ../.venv/Scripts/python.exe -m pytest tests -q` gave **1953 passed** in 573.99s.
- Non-vacuity proofs (each run on committed work and reverted with `git checkout --`):
  - A probe `UPDATE financial_assumption_revision SET value` and an `UPDATE ... assignment SET valid_to` added to the store made check-architecture fail with the "assumption store only inserts..." error.
  - A probe `INSERT INTO financial_assumption_assignment` added to `financial_api.py` failed with "A second product database writer".
  - Disabling the containment check in the migration gave DID NOT RAISE in `test_assignment_outside_its_revision_range_is_refused`.
  - Disabling the set-once check gave DID NOT RAISE in `test_database_refuses_rewrites_of_history`. The test was first sharpened to move a closed `recorded_to` *earlier*, because the original later move was also refused by the exclusion, which made it vacuous for set-once.
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/check-all.ps1`: **All 9 guards passed** (architecture, navigation, agent workflow, registry, delivery fixtures, mock-gap fixtures, missing-claim orphan scan 30 tagged / 12 baselined, scan fixtures, screen ledger). No frontend file changed, so the frontend suite, typecheck and build were not re-run in phase 1, and layout evidence was not run (no UI in this phase).
- Tests that pin the head (`test_s1_bindings_postgres.py:119` and `test_s2_evidence_ledger_postgres.py:445`) now expect `0010_financial_assumptions`.

## Deviations and decisions taken on the fail-closed default

- **Two refusals beyond the packet.** A SUCCESSION that overlaps no current assignment is 409 `SUCCESSION_NOTHING_TO_SUCCEED`, and a CORRECTION that overlaps nothing is 409 `CORRECTION_NOTHING_TO_CORRECT`. In both cases the time has no current price, which the packet calls an INITIAL.
- **Other conventions:**
  - A future open-ended CORRECTION is 409 `CORRECTION_NOT_BACKDATED_OR_BOUNDED`.
  - A CORRECTION may also cover unpriced time beside the time it supersedes.
  - A bounded SUCCESSION leaves the time after its `valid_to` unpriced.
- **CLI location.** The CLI is `assetops_backend/publish_assumption.py` (top level, like `evidence_migration.py`), not inside `financials/`. The persistence guard forbids `pathlib`/file I/O above a domain's adapter layer.
- **Placeholder status code.** The store refuses a non-SYSTEM principal with a 403 code. There is no HUMAN path at all.
- **Fixture expiry.** v2's `valid_from` of 2027-01-01 must still be in the future at publication. After that date the fixture's v2 step is refused (`SUCCESSION_NOT_FUTURE`) and needs a later date. The postgres test that uses `now + 20 days` assumes a date before 2026-12-12.
- **v3's month.** v3 corrects June 2026. The current demo Findings (Oct/Nov 2026) therefore stay on v1. If S4-02b wants a correction over a Finding window, it needs another fixture step.

## Risks

- **The exclusion only bites inside one series.** The plan code, not the database, decides which overlaps a change_kind permits. The database only guarantees that no overlap at any recorded instant ever persists, and that time stays monotonic.
- **Clock regression.** `clock_timestamp()` monotonicity relies on the server clock. A regression is refused (409), never silently written.
- **Shared test database.** The postgres tests import the `engine` and `store` fixtures from `test_s1_bindings_postgres`, which drops and recreates the schema. They therefore need their own `*_test` database, and only one full run at a time.

## What phase 2 needs

- **Read service and routes.** Build a read service over `PostgresAssumptionStore.revisions/assignments`; add SQL-side selection with `valid_at` and `recorded_at` if pagination needs it. Add `GET /api/sites/{code}/financial-assumptions` and `/{revision_id}` in `financial_api.py`, using the scope/401/403/404/503 pattern from `finding_api.open_scope`.
  - Reads may use an access default like the Finding read's, but the write route must keep `no_verified_principal`.
  - Current selection uses `recorded_to IS NULL`; a cutoff `c` uses `recorded_from <= c < recorded_to`. Both are half-open.
  - Wire the store via `financials/composition.build_assumption_store(database_url())`.
- **Walkthrough database.** Publish the demo with `python -m assetops_backend.publish_assumption fixture --site KOBO-001 --file backend/conversions/demo-diesel-price-publications.json` (with `DATABASE_URL` set). Note (S4-02b review L7, 2026-10-14): the fixture now has a v4 step, so without `--step` this also publishes v4; add `--step v1 --step v2 --step v3` for the S4-02a state.
- **Still to build:**
  - the UI (Financials tab flip, Assumptions current/history, disabled edit through `G-assumptions-human-edit`);
  - the Finding bridge (`QUANTITY_UNAVAILABLE`/`UNPRICED`);
  - the Foundation link;
  - layout evidence;
  - the `CODE_STATE`/`ACTIVE_CONTEXT` closeout and the review packet.
