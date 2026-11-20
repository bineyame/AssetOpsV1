# 3A1: the commercial record store (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1 (`.ai/RULES.md` §4). Lane A (sources and money). The
structure is page P3A (`structure-page-P3A.md`, approved by the owner on 20 Nov). Decisions and their reasons are in
`rulings.md` (D-3A1.1 to D-3A1.7). The reviewer's guide is `reviewer-guide.md`. Questions go in `handshake.md` before
code and in `mid-build-questions.md` during the build.

Non-screen. 3 units. Discovery review (W5): a new schema, money records and a store seam.

## 0. Before you start

- **Branch** `task/3A1-commercial-record-store` off `main`, after this spec branch merges. Worktree
  `/opt/assetecon/AssetOpsV1-3a1`.
- **Gate.** Code starts when the handshake has no open question.
- **Python.** The shared `.venv` imports `main`'s packages through its editable installs, so set this tree's
  packages first and check where each package actually loads from:
  ```bash
  cd /opt/assetecon/AssetOpsV1-3a1
  export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
  PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
  $PY -c "import assetops_backend, assetops_contracts; print(assetops_backend.__file__, assetops_contracts.__file__)"   # both under the worktree
  ```
  The packet records that output.
- **Read:**
  - `rulings.md`;
  - P3A;
  - `specs/2a-canonical-format/spec.md` §6 (the record, its refusals and `parse_batch`);
  - `Docs/demo-sprint/product-direction-layer4/integration-source-to-canonical-design.md` §6.1, searched rather than
    read whole;
  - for style: `backend/migrations/versions/0061_reading_upload.py` and `0062_operator_accounts.py`;
  - `backend/assetops_backend/reading_upload/` (service, adapter);
  - `backend/assetops_backend/accounts/adapters/postgres_account_store.py` (the Site lookup at `:60`);
  - `tools/checks/configuration-persistence.ps1` (the account writer block that 3C0a added);
  - `backend/TESTING.md` §"The heavy-tool slot pool" and §"The test database".
- **Databases.** Use only `*_test` databases on `assetopsv1-postgres-1`, through the harness: set
  `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test`. Every
  Postgres test file runs through `tools/heavy-slot.sh --db -- <command>`; the coordinator asked for `--db` on every
  database run in this wave. Never touch ports 5490 or 8990, the walkthrough DB or Docker.
- **The migration** is written as `0063_commercial_records` (`down_revision = "0062_operator_accounts"`). `3C1` also
  adds a migration. Whichever merges second is renumbered at merge preparation (RULES; `delivery-plan.md` §2).
- **Collisions.** These are in other lanes:
  - `3B1` writes no migration and no backend store.
  - `3C1` edits command routes and work and action migrations. It shares only the migration head (above) and
    `tools/checks/configuration-persistence.ps1`; add your block after the account writer's block, and merge `main`
    before review.
  - The UI lanes and DS1m edit only mock-up files.

## 1. Outcome and why

A store holds every commercial record an operator sends: bills, payments, settlements, adjustments, expenses, budget
lines, storage movements, meter reads and assignments, rosters, departures, tariffs and contracts. One record per
source record, every correction a new revision, nothing overwritten. A canonical batch (`2a`) goes in through one
service call, which reports per record what happened. `3A2` (the file intake over HTTP), `3A4` (amounts by month),
DS3 (the bulk loader) and the structure read build on it. P3A's rules 1, 3 and 4 hold in this store, and rule 6
(one canonical record per Site, month and field) holds for DS1b's records through their stable record IDs.

## 2. Records: migration `0063_commercial_records`

`TABLES = ("commercial_intake", "commercial_record", "commercial_record_revision", "commercial_rejection")`. Use a raw
string, `UPGRADE = r"""..."""`, with exactly this SQL:

```sql
CREATE TABLE commercial_intake (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    source_type text NOT NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NOT NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    provenance text NOT NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                                   'field-integrated', 'observed-financial')),
    produced_at timestamptz NOT NULL,
    batch_sha256 text NOT NULL CHECK (batch_sha256 ~ '^[0-9a-f]{64}$'),
    state text NOT NULL CHECK (state IN ('STORED', 'REFUSED')),
    refusal_code text NULL CHECK (refusal_code ~ '^[A-Z][A-Z_]{0,39}$'),
    refusal_path text NULL CHECK (refusal_path IS NULL OR char_length(refusal_path) <= 300),
    record_count int NOT NULL CHECK (record_count >= 0),
    new_count int NOT NULL CHECK (new_count >= 0),
    revised_count int NOT NULL CHECK (revised_count >= 0),
    unchanged_count int NOT NULL CHECK (unchanged_count >= 0),
    refused_count int NOT NULL CHECK (refused_count >= 0),
    entered_by text NOT NULL CHECK (entered_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    entered_at timestamptz NOT NULL,
    CHECK ((state = 'REFUSED') = (refusal_code IS NOT NULL)),
    CHECK (new_count + revised_count + unchanged_count + refused_count = record_count),
    UNIQUE (tenant_id, id)
);
CREATE INDEX commercial_intake_tenant_at ON commercial_intake (tenant_id, entered_at DESC);
CREATE TABLE commercial_record (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,
    kind text NOT NULL CHECK (kind IN ('CHARGE', 'RECEIPT', 'SETTLEMENT', 'ADJUSTMENT', 'EXPENSE', 'BUDGET_LINE',
        'STORAGE_MOVEMENT', 'CUSTOMER_METER_READ', 'METER_ASSIGNMENT', 'FLEET_ROSTER', 'DEPARTURE',
        'TARIFF_SCHEDULE', 'CONTRACT_DOCUMENT')),
    source_system text NOT NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    source_record_id text NOT NULL CHECK (char_length(source_record_id) BETWEEN 1 AND 200),
    first_recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK (site_id IS NOT NULL OR kind IN ('BUDGET_LINE', 'CONTRACT_DOCUMENT')),
    UNIQUE (tenant_id, source_system, source_record_id),
    UNIQUE (tenant_id, id)
);
CREATE TABLE commercial_record_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    record_id uuid NOT NULL,
    site_id uuid NULL,
    kind text NOT NULL,
    revision_no int NOT NULL CHECK (revision_no >= 1),
    source_version text NOT NULL CHECK (char_length(source_version) BETWEEN 1 AND 64),
    intake_id uuid NOT NULL,
    record_sha256 text NOT NULL CHECK (record_sha256 ~ '^[0-9a-f]{64}$'),
    canonical text NOT NULL,
    provenance text NOT NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                                   'field-integrated', 'observed-financial')),
    recognition_period text NULL CHECK (recognition_period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    occurred_at timestamptz NULL,
    settled_at timestamptz NULL,
    effective_from date NULL,
    effective_to date NULL,
    amount numeric NULL,
    currency text NULL CHECK (currency ~ '^[A-Z]{3}$'),
    quantity numeric NULL,
    unit text NULL CHECK (unit IN ('kWh', 'kW', 'L', 'crate', 'crate_day')),
    status text NULL CHECK (status ~ '^[A-Z][A-Z_]{0,39}$'),
    supersedes_revision_id uuid NULL REFERENCES commercial_record_revision (id),
    recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, record_id) REFERENCES commercial_record (tenant_id, id),
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    CHECK ((amount IS NULL) = (currency IS NULL)),
    CHECK ((quantity IS NULL) = (unit IS NULL)),
    CHECK ((revision_no = 1) = (supersedes_revision_id IS NULL)),
    CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from),
    UNIQUE (record_id, source_version),
    UNIQUE (record_id, revision_no)
);
CREATE INDEX commercial_revision_read ON commercial_record_revision
    (tenant_id, site_id, kind, recognition_period, record_id, revision_no DESC);
CREATE TABLE commercial_rejection (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    intake_id uuid NOT NULL,
    record_index int NOT NULL CHECK (record_index >= 0),
    source_record_id text NULL CHECK (source_record_id IS NULL OR char_length(source_record_id) BETWEEN 1 AND 200),
    code text NOT NULL CHECK (code ~ '^[A-Z][A-Z_]{0,39}$'),
    path text NOT NULL CHECK (char_length(path) BETWEEN 1 AND 300),
    recorded_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    UNIQUE (intake_id, record_index)
);
```

Then `CREATE TRIGGER <table>_immutable BEFORE UPDATE OR DELETE ON <table> FOR EACH ROW EXECUTE FUNCTION
ledger_append_only();` for all four tables. The downgrade follows 0061: lock the tables, refuse with
`RAISE EXCEPTION 'Downgrade of 0063_commercial_records refused: commercial records exist'` if any table has a row,
then drop the tables in reverse order. There are no column defaults; the adapter writes every value and every time
from the service clock. The tables do **not** join the chain change log (D-3A1.6).

## 3. Rules

These are checked in this order, inside one transaction per intake. The transaction first takes
`SELECT pg_advisory_xact_lock(hashtextextended('commercial:' || CAST(:tenant_id AS text), 0))`.

1. **Bytes to batch.** `loads_canonical(data)` then `parse_batch(obj)`. An envelope refusal (`CanonicalRefused` with a
   `json.` or `batch.` path) makes the intake REFUSED: one `commercial_intake` row with `refusal_code` and
   `refusal_path`, all counts 0, nothing else written.
2. **Tenant.** `batch.tenant_code` must equal the tenant's `slug`. Otherwise the intake is REFUSED with
   `INTAKE_TENANT_MISMATCH` at path `batch.tenant_code` (P3A rule 3).
3. **Per record**, in input order. A refused record writes one `commercial_rejection` row (code, path, and its
   `source_record_id` if it parsed) and never stops the others (P3A rule 4):
   - a format refusal from `parse_batch` keeps its own code and path;
   - a kind whose store family is OPERATIONAL_RECORD (`SERVICE_TICKET`) is `INTAKE_NOT_COMMERCIAL record.kind`;
   - a `site_code` not found by `site_code_key = lower(:code)` in the tenant is `INTAKE_SITE_UNKNOWN
     record.site_code`.
4. **Identity** (D-3A1.2). The key is (tenant, `source_system`, `source_record_id`), with `source_system` taken from
   the batch. A record seen before must keep its kind and Site; otherwise it is refused `INTAKE_KIND_CHANGED
   record.kind` or `INTAKE_SITE_CHANGED record.site_code`.
5. **Revision** (D-3A1.3), keyed by the record's `source_version`:
   - first sight of the record: write it and revision 1 (`NEW`);
   - a new `source_version`: write revision `max + 1`, superseding the latest (`REVISED`);
   - a known `source_version` with the same `record_sha256` (`record_digest`): write nothing (`UNCHANGED`), so a
     repeated file adds nothing (P3A rule 1);
   - a known `source_version` with a different digest: `INTAKE_VERSION_CONFLICT record.source_version`.
6. **Stored columns.**
   - `canonical` is `to_canonical_json(record).decode()`.
   - The clocks, amount, quantity and status come from the parsed record; `amount` and `quantity` are stored as
     `Decimal`.
   - `provenance` comes from the batch.
   - `recorded_at` is the service clock, the same for the whole intake.
7. **Dry run.** Steps 1 to 5 run and give the same outcomes, the store's state included, and nothing is written. The
   lock is still taken, so the answer reflects committed state.

## 4. Code: package `backend/assetops_backend/commercial/`

| File | Holds |
|---|---|
| `model.py` | `OUTCOMES = ("NEW", "REVISED", "UNCHANGED", "REFUSED")`; frozen dataclasses `RecordOutcome(index, outcome, source_record_id, record_id, revision_no, code, path)`, `IntakeResult(intake_id, state, refusal_code, refusal_path, outcomes: tuple[RecordOutcome, ...], dry_run)`, `RevisionRow` (every column of `commercial_record_revision` plus `source_system` and `source_record_id`); `IntakeRefused(Exception)` is not used (refusals are results) |
| `store.py` | `CommercialStore` (Protocol) with the methods of §4.1 |
| `service.py` | `CommercialRecords(store, *, clock)`, with `ingest(tenant_id, data: bytes, *, entered_by: str, dry_run: bool = False) -> IntakeResult` running §3 |
| `composition.py` | `build_commercial_records(database_url) -> CommercialRecords`, the only importer of the adapter |
| `adapters/postgres_commercial_store.py` | `PostgresCommercialStore(url)`, SQLAlchemy `text()` statements as the reading-upload and account adapters do, with the engine built `hide_parameters=True` (D-2A.11's class: no record value in an error) |

No route and no `create_app` change: `3A2` mounts the HTTP intake.

### 4.1 Store port

- `tenant_slug(tenant_id) -> str | None`
- `site_ids(tenant_id, codes: set[str]) -> dict[str, UUID]` (by `site_code_key`)
- `existing(tenant_id, source_system, ids: set[str]) -> dict[str, ExistingRecord]`, where
  `ExistingRecord(record_id, kind, site_id, versions: dict[str, str])` maps each source version to its digest, and
  the record also carries its latest revision ID and number
- `write_intake(intake_row, records, revisions, rejections, *, dry_run) -> None` runs one transaction: the advisory
  lock, then a re-read of `existing` inside it (§3 is re-decided under the lock; the service passes a callable
  `decide(existing) -> plan`), then the inserts, or no inserts on a dry run
- `latest_revisions(tenant_id, *, site_id=None, kind=None, recognition_period=None) -> tuple[RevisionRow, ...]`: the
  highest revision per record, sorted by `(site_id, kind, recognition_period, source_system, source_record_id)`
- `record_history(tenant_id, record_id) -> tuple[RevisionRow, ...]`: ascending `revision_no`
- `intake(tenant_id, intake_id) -> IntakeResult | None`: the outcomes rebuilt from revisions and rejections

The in-memory test store implements the same port, with a `threading.Lock` per tenant.

## 5. Guard

Register `$commercialWriter = "$backendRoot/commercial/adapters/postgres_commercial_store.py"` in
`tools/checks/configuration-persistence.ps1`, after the account writer's block and in the same statement-shape style.
- It is the sole runtime writer of the four tables.
- It runs one plain `INSERT INTO <table> (...) VALUES (...)` per table (no `ON CONFLICT`, no `SELECT` source), and no
  UPDATE, DELETE or TRUNCATE.
- Each shape has an owner statement (anti-vacuity).
- Show the guard failing on a planted `UPDATE commercial_record_revision`, and on an INSERT into `commercial_record`
  from a second module (RULES §7).

## 6. Tests

**No database** (not pooled), `backend/tests/test_3a1_commercial_service.py`, using the in-memory store:
- each of §3's outcomes;
- an envelope refusal and a tenant mismatch: REFUSED, nothing written;
- a SERVICE_TICKET (`INTAKE_NOT_COMMERCIAL`);
- an unknown Site;
- a changed kind and a changed Site;
- the same file twice (all `UNCHANGED`, no new rows);
- a corrected row with a new `source_version` (`REVISED`, revision 2 supersedes 1);
- the same `source_version` with different content (`INTAKE_VERSION_CONFLICT`);
- a dry run that equals the real run's outcomes and writes nothing;
- the fixture `backend/tests/fixtures/canonical_v1_examples.json` (2a's 17 batches) ingested into a world of the
  three demo tenants and their Site codes, with every commercial record `NEW` and the one SERVICE_TICKET refused;
- DS1b's batches: run `world_history.py records` on the fixture view into a scratch directory, then ingest them
  twice: the first run is all `NEW`, the second all `UNCHANGED`. This is P3A rule 6's base: one record per Site,
  month and field, by its stable ID.

**Postgres** (pooled, `--db`), `backend/tests/test_3a1_commercial_postgres.py`:
- the tables, triggers and indexes exist;
- UPDATE and DELETE are refused on all four tables;
- each CHECK fails on a planted row;
- the site foreign key and the null-Site rule hold;
- the uniqueness keys hold;
- the adapter round-trips every port method;
- `latest_revisions` returns revision 2 after a correction, and `record_history` returns both;
- a lock proof in the 3C0a R2 shape: the test holds the tenant's commercial lock and starts two `ingest` calls of the
  same new record in threads; after 0.5 s both are still alive; the test releases the lock; the result is one `NEW`
  and one `UNCHANGED`, never two records;
- downgrade is refused when there are rows, and down then up works on an empty clone.

**Regression beside them:** `backend/tests/test_pg_harness.py` and `backend/tests/test_up1_reading_upload_postgres.py`.

Commands:
```bash
$PY -m pytest backend/tests/test_3a1_commercial_service.py -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh --db -- $PY -m pytest backend/tests/test_3a1_commercial_postgres.py backend/tests/test_pg_harness.py backend/tests/test_up1_reading_upload_postgres.py -q
pwsh -NoProfile -File tools/check-all.ps1      # fast mode, once, at the end
python3 tools/select-tests.py --base main      # "full" because of the migration: not run while building; the merge's full tier runs it
```

## 7. Done (questions)

1. Does a canonical batch go in through one call, with every record's outcome reported, and a refused record never
   stopping the others?
2. Does the same file twice add nothing, a corrected row add a revision that supersedes the old one, and a
   conflicting row get refused?
3. Is another tenant's batch refused, and is every write append-only in the database?
4. Do 2a's 17 example batches and DS1b's batches ingest as specified?
5. Is the lock proven by the test, and does the guard catch a second writer?
6. Is nothing changed outside this list and the finish bookkeeping:
   - the migration;
   - `backend/assetops_backend/commercial/**`;
   - the two test files;
   - the guard block;
   - the packet?

Packet: `specs/3A1-commercial-record-store/packet.md`, with the module-path output and the mid-build question count.

## 8. Out of scope

- The HTTP intake, native files, raw rows and acceptance by a person (`3A2`).
- Emulators and the contract test (`3A3`).
- Amounts by month and superseded reads (`3A4`).
- Labels (`3A5`).
- Bulk COPY loading, and carrying `ESTIMATED_NOT_RECEIVED` and coverage (`DS3`, D-3A1.7).
- The chain change log (D-3A1.6).
- Partitioning (strategy Appendix E).

## 9. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | The revision table's uniqueness on `(record_id, source_version)` has no time column, against strategy §7's partition-ready rule (D-3A1.5) | Accepted. At partition time the uniqueness moves to the identity table. Partitioning is post-pilot |
| Q2 | Intakes serialise per tenant | Yes. Demo and pilot volumes are small; DS3's bulk path is separate |
