# DS3: the bulk loader for the generated world's inputs (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`;
pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4, rows 10 to 12 for the calls made here). `delivery-plan.md`
§2 row `DS3`: "Bulk loader: COPY into staging, set-based writes into input stores, the table allowlist and label
refusals; the real-path slice and its parity test" (3 units; depends on `DS1b`, `3A2`; feeds `DS4`, then `WK`).
Design source: data and build strategy §4 and §8 (branch `task/data-build-strategy`, `Docs/engineering/data-and-build-strategy.md`;
not on `main`). Lane A tail (`two-week-build-plan.md` §0.2 days 6-7). **3 units.** Discovery review (W5): a second
write path into the evidence ledger. Non-screen; no user-facing text (D-DS3.7). A **heavy database job**: one at a
time machine-wide (row 4), through `tools/heavy-slot.sh --db`.

- **What it is.** Today every reading enters the evidence ledger one envelope at a time, in a savepoint each
  (`postgres_evidence_ledger.py:530-584`), which is most of the walkthrough build's two hours. DS3 adds one bulk
  admission inside the ledger's own writer: the same parse, the same claims and configuration checks, the same pure
  `decide`, then one set-based statement per table per batch. A parity test proves that the bulk path stores the same
  rows as central ingestion for two Kobo days. Commercial records keep their one path, `3A2`'s intake, driven by the
  existing loader (D-DS3.2). A world command loads a tenant directory by both.
- **Builds on (merged on `main` at `39e1682de`):** `evidence/ledger_service.py` (`BatchIngestionService.submit`,
  `_check_claims`, `_refuse`, `_drive`), `evidence/ledger.py` (`decide(basis, ordinal, text)`, `basis_from_snapshot`,
  `recompute_window`, `Accepted`, `Rejected`, `GatewayPrincipal`, `BatchHandle`), `evidence/adapters/postgres_evidence_ledger.py`
  (`open_batch`, `decide_chunk`, `_persist`, `_coalesce_job`, `_lock_slot`, `_site_type_on`, `RECOMPUTE_DOMAIN`,
  `COLD_RECOMPUTE_DOMAIN`, `COLD_ROLE_NAMES`), `assetops_contracts.ingestion_batch_v2` (`parse_canonical_batch_v2_text`,
  `MAX_BATCH_BYTES`), `database_target.py` (`database_target`, `is_operator_name`), `load_emulated_exports.py`
  (`main(argv, *, uploads, accounts)`; `--dir --tenant --submit-as [--accept-as]`), migration `0005_evidence_ledger`
  (`accepted_evidence_message_unique` on `(site_id, gateway_id, source_id, message_id)`), `0001` `gateway` table,
  `backend/tests/test_s2_evidence_ledger_postgres.py` (`Kit`, `converted_enabled`), `backend/tests/pg_harness.py`.
- **Decisions:** `rulings.md` (D-DS3.1 to D-DS3.8). **Reviewer guide:** `reviewer-guide.md`. **Handshake:** `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question, and no other heavy database job holds the machine (row 4: DS3, DS4
  and WK one at a time). No unmerged dependency (`DS1b`, `3A2` are merged).
- **Branch** `task/DS3-bulk-loader` off `main`; worktree `/opt/assetecon/AssetOpsV1-ds3`; symlink
  `frontend/node_modules` from the main checkout.
- **Databases (authorised set only; nothing else).** Every Postgres test through `tools/heavy-slot.sh --db -- pwsh
  -NoProfile -File tools/run-host-tests.ps1 -- <file>`, on `pg_harness`-owned clones of `ASSETOPS_TEST_DATABASE_URL`:
  `<stem>_pt<run>_ds3seed_test`, `<stem>_pt<run>_ds3real_test`, `<stem>_pt<run>_ds3bulk_test` (names from
  `pg_harness.database_name(stem, run, tag)`, tags `ds3seed`, `ds3real`, `ds3bulk`; the harness drops them). The
  unit-3 measurement runs on `<stem>_pt<run>_ds3bench_test`, the same way. No `<prefix>_audit*` database is needed.
  Never the walkthrough database, ports 5490 or 8990, Docker, or a database outside `assetopsv1-postgres-1`.
- **Read:** `rulings.md`; `ledger_service.py` (whole, 238 lines); `postgres_evidence_ledger.py:88-175`, `:284-360`,
  `:440-690`; `ledger.py:57-160`, `:268-300`, `:334-500`; `tools/checks/configuration-persistence.ps1:700-720`,
  `:815-845`, `:1255-1300`, `:1720-1760` (the ledger rules this unit must keep); `load_emulated_exports.py`;
  `test_s2_evidence_ledger_postgres.py:54-160`; `test_s3_dispatch_assessment_postgres.py:51-100` (`Feeder`).
- **Pre-flight (handshake, before code).** Print `Kit(...).principal.mode`, the device ids `Kit.doc["bindings"]`
  holds and each binding's valid period for the seed of §3. The bulk path admits SIMULATED batches only (D-DS3.6), so
  the parity slice needs a SIMULATED gateway: if the converted Kobo gateway is LIVE, say so as a handshake question
  (the Architect then names the SIMULATED seed); do not change the registration.
- **Files.** New: `backend/assetops_backend/evidence/bulk_load.py`, `backend/assetops_backend/load_world_inputs.py`,
  `backend/tests/test_ds3_bulk_load.py` (no database), `backend/tests/test_ds3_bulk_load_postgres.py`,
  `backend/tests/test_ds3_parity_postgres.py`. Edited: `evidence/adapters/postgres_evidence_ledger.py` (one method,
  one read, one extracted helper, statement constants), `evidence/ledger_service.py` (one extracted method). No
  migration, no guard edit, no simulator or contracts change.

## 1. Outcome and why

The walkthrough database must be built in minutes from the generated world, and a "clean, good" database must be
provably the same as one fed through the real intake (owner, strategy question 4: "the parity test proves the bulk
rows equal the real path's on a fixed slice, every build"). DS3 delivers the bulk path and its proof; `DS4` builds the
template ladder and the world commands on it and re-benchmarks.

Gate questions: does a batch admitted in bulk store exactly the rows central ingestion stores for the same bytes
(receipt times and generated IDs apart)? Is anything other than a SIMULATED batch, or a batch with a rejected
ordinal, a published slot or a colliding message, refused before a row is written? Does the bulk path write only the
four input tables, through the ledger's one writer, and is it unreachable from HTTP?

## 2. Design

### 2.1 Shared admission (`evidence/ledger_service.py`; a pure extraction, no behaviour change)

Extract submit's steps 2 to 5 (size, parse, claims, batch-ID conflict, binding set, basis) into
`BatchIngestionService.admit(principal, raw, received_at, refuse) -> Admission`, where `Admission` is a frozen
dataclass `(batch, text, basis, existing: BatchHandle | None)` and `refuse(principal, external_batch_id, digest,
received_at, status, kind, field, detail) -> Exception` builds the exception to raise. `submit` calls
`self.admit(principal, raw, received_at, self._refuse)` and continues exactly as today (open, drive, receipt). Every
existing S2 test passes unchanged; that is the extraction's proof.

### 2.2 The bulk admission in the ledger's one writer (`postgres_evidence_ledger.py`)

```python
@dataclass(frozen=True)
class BulkAdmitted:
    external_batch_id: str; total: int; already_loaded: bool

class BulkAdmissionRefused(Exception):          # .code in BULK_REFUSALS, .detail
BULK_REFUSALS = frozenset({"BULK_PUBLISHED_BATCH", "BULK_BATCH_EXISTS_DIFFERENT", "BULK_BATCH_IN_PROGRESS",
                           "BULK_MESSAGE_COLLISION"})

def gateway_principal(self, site_id: UUID, gateway_id: UUID) -> GatewayPrincipal | None
    # SELECT tenant_id, site_id, id, mode FROM gateway WHERE site_id = :site AND id = :g AND disabled_at IS NULL
def bulk_admit(self, principal: GatewayPrincipal, *, external_batch_id: str, payload_sha256: str, source_id: str,
               source_mode: str, basis: AcceptedAsBasis, batch_text: str, decisions: Sequence[Accepted],
               received_at: datetime, completed_at: datetime) -> BulkAdmitted
```

`bulk_admit`, in **one** transaction (`self._run(work, write=True)`):
1. `_lock_slot(c, tenant, site, external_batch_id)` (the slot lock `open_batch` takes).
2. An `evidence_publication` row for the slot: `BULK_PUBLISHED_BATCH` (a registered run's batch is bound to its
   publication only by the real path, `open_batch:342-352`; D-DS3.4).
3. An `ingestion_batch` row for the slot: same `payload_sha256` and `COMPLETED`: return `BulkAdmitted(..., True)`
   and write nothing (a re-run of a world load is idempotent); same digest, `IN_PROGRESS`: `BULK_BATCH_IN_PROGRESS`;
   another digest: `BULK_BATCH_EXISTS_DIFFERENT`.
4. `decided_at = self._decision_instant(c)`, once (S4-07's rule; one instant for the batch); `site_type =
   _site_type_on(c, tenant, site)`.
5. `INSERT INTO ingestion_batch (...)` as `open_batch`'s statement, with `status 'COMPLETED'`, `processed_count`,
   `accepted_count` and `total_count` = `len(decisions)`, `duplicate_count`, `rejected_count`, `conflict_count` 0,
   `completed_at`, and `ON CONFLICT ON CONSTRAINT ingestion_batch_external_unique DO NOTHING RETURNING id` (no row
   returned: `BULK_BATCH_IN_PROGRESS`; the lock makes it unreachable, the arbiter keeps the guard's allowed shape).
6. `accepted_evidence`: **one** `INSERT INTO accepted_evidence (<the 42 columns of _persist, same order>) SELECT ...
   FROM unnest(CAST(:id AS uuid[]), CAST(:ordinal AS integer[]), ...) AS s(...) ON CONFLICT ON CONSTRAINT
   accepted_evidence_message_unique DO NOTHING RETURNING id`. Each column's value per ordinal is exactly what
   `_persist` binds for that `Accepted` (same expressions, the batch row's `gateway_id`, `source_id`, `received_at`,
   `foundation_revision_id`, `binding_set_revision_id`, `source_mode`); ids are `uuid4()` per ordinal, generated in
   Python as today. Fewer ids returned than decisions, or an `IntegrityError` on any unique index (event or EV START
   identity): roll back and raise `BULK_MESSAGE_COLLISION` (D-DS3.5).
7. `ingestion_disposition`: one `INSERT ... SELECT ... FROM unnest(...)` of `(batch_id, ordinal, tenant_id, site_id,
   message_id, 'ACCEPTED', accepted_evidence_id, NULL, decided_at)`.
8. Recompute jobs: `self._enqueue_admitted(c, row, site_type, admitted, decided_at)` (§2.3), once for the batch.
9. Return `BulkAdmitted(external_batch_id, len(decisions), False)`.

Statements are module-level `text()` constants (`_BULK_BATCH_SQL`, `_BULK_EVIDENCE_SQL`, `_BULK_DISPOSITION_SQL`), one
literal each, so `tools/checks/configuration-persistence.ps1` reads their targets: no `COPY`, no `MERGE`, no DDL, no
`DO UPDATE`, only the existing `DO NOTHING` arbiters (D-DS3.1). The guard passes unchanged; check-all is the proof.

### 2.3 One enqueue rule (`_enqueue_admitted`; extracted from `decide_chunk`, no behaviour change)

`_enqueue_admitted(c, row, site_type, admitted: Sequence[tuple[Accepted, UUID]], decided_at)` holds exactly
`decide_chunk`'s lines from "W2-00 ruling 5" to the cold `_coalesce_job` call: v3 accepted decisions feed
`recompute_window` and `_coalesce_job(..., RECOMPUTE_DOMAIN)` with the first new id as cause; v4 decisions bound to a
`COLD_ROLE_NAMES` role at a `COLDCHAIN` Site feed the cold domain. `decide_chunk` collects `(decision, evidence_id)`
for its ACCEPTED ordinals and calls it once per chunk, as today; `bulk_admit` calls it once per batch. The S2, S3 and
W2-03 tests pass unchanged.

### 2.4 The bulk service (`evidence/bulk_load.py`)

```python
BULK_LOAD_REFUSALS = frozenset({"BULK_NOT_SIMULATED", "BULK_UNKNOWN_GATEWAY", "BULK_REJECTED_ORDINAL",
                                "BULK_DATABASE_NOT_PERMITTED"}) | BULK_REFUSALS
class BulkLoadRefused(Exception):            # .code, .external_batch_id (or None), .detail
@dataclass(frozen=True)
class BulkLoaded:
    batches: int; already_loaded: int; envelopes: int
class BulkEvidenceLoad:
    def __init__(self, ledger: PostgresEvidenceLedger, *, clock: Callable[[], datetime] = utc_now) -> None
    def load(self, raws: Sequence[bytes]) -> BulkLoaded
def permitted_database(url: str) -> bool     # D-DS3.6
```
`load` handles the batches in the given order; each batch is its own transaction; the first refusal stops the load
(earlier batches stay, a re-run skips them, step 3 of §2.2). Per batch:
1. Parse the claims only (`parse_canonical_batch_v2_text`; a parse failure is the `kind` of `BatchRejected`, through
   step 3's `refuse`); `source_mode != "SIMULATED"`: `BULK_NOT_SIMULATED` (D-DS3.6).
2. `principal = ledger.gateway_principal(UUID(batch.site_id), UUID(batch.gateway_id))`; None: `BULK_UNKNOWN_GATEWAY`.
3. `admission = BatchIngestionService(ledger).admit(principal, raw, received_at, refuse)` where `refuse` returns
   `BulkLoadRefused(kind, external_batch_id, detail)` and **records nothing** (no `batch_refusal` row: a refused bulk
   load is a build defect, reported by the command, never product evidence). `received_at = clock()` once per batch.
4. `decisions = [decide(admission.basis, i, text) for i, text in enumerate(batch.envelopes)]`; any `Rejected`:
   `BULK_REJECTED_ORDINAL` with its ordinal and kind (D-DS3.5: the generated world is clean; disorder is planted
   through the real path).
5. `ledger.bulk_admit(principal, ..., decisions=decisions, received_at=received_at, completed_at=clock())`; a
   `BulkAdmissionRefused` becomes `BulkLoadRefused` with the same code.

`permitted_database(url)`: `database_target(url).name` ends `_test`, or contains `_audit` after a non-empty prefix
(`re.fullmatch(r"[a-z0-9_]+_audit[a-z0-9_]*", name)`), and `not is_operator_name(name)`; a `DatabaseTargetUnclear`
is false.

### 2.5 The world command (`python -m assetops_backend.load_world_inputs`)

`build_parser()` public; `main(argv, *, ledger=None, load_exports=None) -> int`. Arguments: `--world DIR` (one
directory per tenant slug, each holding the tenant's DS1b canonical files `<tenant>.<source_type>.json` and a
`telemetry/` folder of Batch V2 files `*.batch.json`), `--submit-as EMAIL`, `--accept-as EMAIL`, optional `--tenant
SLUG` (one tenant only). Steps: no `DATABASE_URL`: `NO_DATABASE`; `permitted_database` false:
`BULK_DATABASE_NOT_PERMITTED` (before any connection); then per tenant in sorted order: (a) commercial: when the
directory holds a `*.json` file outside `telemetry/`, call `load_emulated_exports.main(["--dir", d, "--tenant",
slug, "--submit-as", s, "--accept-as", a])` (D-DS3.2; its own refusals and exit codes pass through: a non-zero exit
stops the command with that code); (b) telemetry: `BulkEvidenceLoad(ledger).load(raws)` over the folder's files in
sorted name order. Output on success: one JSON line per tenant, `{"tenant", "commercial_exit", "batches",
"already_loaded", "envelopes"}`, exit 0. A `BulkLoadRefused` writes `<CODE> <external_batch_id or -> <detail>\n` to
stderr and exits 2; `NO_DATABASE` exits 2; a database error exits 3. The command reads no oracle, writes no file.

**Unreachable from HTTP:** no module named `main.py` or `*_api.py` imports `bulk_load`, `load_world_inputs` or calls
`bulk_admit`; `bulk_admit` has exactly one caller (`bulk_load.py`); test 9.

## 3. The parity slice (fixtures; hand-written in the tests, W2)

**Seed.** On `ds3seed`: `converted_enabled(store, engine)` and `Kit(engine, ...)` as `test_s3_dispatch_assessment_postgres.py`
`site`; nothing ingested. Then `CREATE DATABASE <ds3real> TEMPLATE <ds3seed>` and `CREATE DATABASE <ds3bulk>
TEMPLATE <ds3seed>`, so both hold the same Site, gateway, sources and binding set with the same ids.

**Two Kobo days.** The rows of `test_s3_dispatch_assessment_postgres.interval_rows` written out for 6 and 7 October
2026, 00:00 to 23:45 UTC every 15 minutes: `generator-controller/status` RUNNING from 06:00 to 08:00 and STOPPED
otherwise, the three feeders `residential-meter`, `clinic-meter`, `mill-meter` at 10, `battery-pcs-controller/
state-of-charge` at 80 (to 06:00), 60 (06:00 to 08:00) and 80 after. Sealed once with the seed's `Kit`, one batch per
device per day (`Kit.seal(texts, device_id=...)`), `source_mode` SIMULATED, epoch `epoch-1`, sequences per
`Feeder.deliver`. The same list of batch bytes `B` feeds both paths. The test writes the expected counts by hand:
5 devices × 2 days = 10 batches; 192 envelopes per device (96 per day) except the generator status (96 per day as
well) = 960 envelopes. If `Kit` names devices differently, the pre-flight records the real names and the counts follow.

**Real path:** on `ds3real`, `BatchIngestionService(PostgresEvidenceLedger(url)).submit(kit.principal, b)` for each
`b` in `B`, each 200 and COMPLETED. **Bulk path:** on `ds3bulk`, `BulkEvidenceLoad(PostgresEvidenceLedger(url)).load(B)`.

**Equal rows** (each a sorted list of tuples, compared exactly):
- `accepted_evidence`: every column except `id`, `batch_id`, `received_at`, keyed by `(source_id, message_id)`;
- `ingestion_batch`: every column except `id`, `received_at`, `completed_at`, keyed by `external_batch_id`;
- `ingestion_disposition` joined to its batch and evidence: `(external_batch_id, ordinal, message_id, decision,
  evidence message_id)`, ignoring `batch_id`, `accepted_evidence_id`, `decided_at`;
- `evidence_rejection`, `batch_refusal`, `batch_publication_link`: zero rows on both.
**Recompute jobs** (D-DS3.3): on both, every accepted reading's `interval_start` or `source_time` lies inside some
PENDING `RECOMPUTE_DOMAIN` job window of the Site; the bulk path has at most one job per batch and at most as many
as the real path.

## 4. Tests (written first)

**No database** (`backend/tests/test_ds3_bulk_load.py`):
1. `permitted_database`: `assetops_test` true; `assetops_pt1a_ds3bulk_test` true; `assetops_ds3_audit1121` true;
   `assetops_polish_walk1113` false; `assetops_op_kobo` false; `assetops_op_kobo_test` false; `_audit` false; a URL
   with a `dbname` query false (unclear).
2. The command's refusals with injected fakes: no `DATABASE_URL` (`NO_DATABASE`, exit 2); a non-permitted URL
   (`BULK_DATABASE_NOT_PERMITTED`, exit 2, the fake ledger never constructed); a commercial loader stub returning 4
   (the command exits 4 and loads no telemetry); success prints one line per tenant with exactly the five keys.
3. Seams (an `ast` scan): `bulk_admit` is called only in `evidence/bulk_load.py`; no `main.py` or `*_api.py` imports
   `bulk_load` or `load_world_inputs`; `bulk_load.py` imports no `simulator`, `host` or `commercial` module; the three
   `_BULK_*` statements' targets (`(?i)\b(?:INTO|UPDATE)\s+([a-z_]+)`) are a subset of `{"ingestion_batch",
   "accepted_evidence", "ingestion_disposition"}` and contain no `COPY`, `MERGE`, `DO UPDATE`, `CREATE`, `TRUNCATE`;
   `_BULK_EVIDENCE_SQL`'s column list equals `_persist`'s INSERT column list, in order (both parsed from the module).

**Postgres, pooled** (`backend/tests/test_ds3_bulk_load_postgres.py`, on the seed fixture of §3 in one clone):
4. One generator-status day (96 envelopes) loads: one `ingestion_batch` COMPLETED with counts 96/96/0/0/0, 96
   `accepted_evidence` rows, 96 dispositions ACCEPTED, one PENDING dispatch job covering the day; `BulkLoaded(1, 0, 96)`.
5. The same bytes again: `BulkLoaded(1, 1, 96)`, no row added (counts before and after).
6. Refusals, each on a fresh clone and each leaving every ledger table's row count unchanged: a LIVE batch
   (`Kit.seal(..., mode="LIVE")`; `BULK_NOT_SIMULATED`); an unknown gateway id (`BULK_UNKNOWN_GATEWAY`); a batch with
   one envelope outside the binding's valid period (`BULK_REJECTED_ORDINAL`, ordinal named; the real path would store
   a rejection); the same batch ID with other bytes after a load (`BULK_BATCH_EXISTS_DIFFERENT`); an
   `evidence_publication` row inserted for the slot through `register_publication` first (`BULK_PUBLISHED_BATCH`); a
   second batch reusing one message id of a loaded batch (`BULK_MESSAGE_COLLISION`, and the second batch's
   `ingestion_batch` row absent: one transaction); a malformed body (`BatchRejected`'s kind, no `batch_refusal` row).
7. A load stopped by a refusal at its third batch: batches one and two stay COMPLETED; a re-run after removing the
   bad batch reports them as `already_loaded` and loads the rest.

**Parity** (`backend/tests/test_ds3_parity_postgres.py`): 8. §3 in full: the hand counts, every equal-rows list
equal, the recompute-job property; the test drops its three clones in `finally`.

**Regression:** every `test_s2_*`, `test_s3_dispatch_assessment_postgres.py`, `test_w203_*` (cold enqueue),
`test_s405_publication_postgres.py`, `test_3a3_*` loader tests; the persistence guard unchanged and passing;
check-all once at the end; `select-tests --base main` before review.

## 5. Unit 3: the measurement for DS4 (packet only)

On `<stem>_pt<run>_ds3bench_test`, one script run in the slot pool (`tools/heavy-slot.sh --db`), not a test: seal
14 Kobo days (the §3 rows, 6 to 19 October) and load them once by `submit` and once by `load` into two clones; record
wall time, rows per table and `pg_total_relation_size` before and after for each, and the statements per table
(`pg_stat_statements` if enabled, else a SQLAlchemy `before_cursor_execute` counter). The packet states the numbers
with the machine idle and the slot held; DS4 replaces strategy §4's targets with them. No figure here is a gate.

## 6. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.5) | §2.1 extraction; §2.2 `bulk_admit`, `gateway_principal`; §2.3 extraction; §2.4 service; tests 3 (static), 4 to 7; S2/S3/W2-03 regression | 1 to 2 |
| 2 (1.0) | §2.5 command; tests 1, 2; §3 parity, test 8 | 1 |
| 3 (0.5) | §5 measurement; check-all; packet | 0 to 1 |

Total 3.0. Packet `specs/DS3-bulk-loader/packet.md`: the clone names used and dropped, the parity counts, §5's
numbers, residual risk `R-TRUST` (the command is a trusted tool: it admits batches with no gateway credential, behind
the permitted-database and SIMULATED refusals), the mid-build count.

## 7. Done (questions; each can fail)

1. Do the real path and the bulk path store the same rows for two Kobo days (test 8), IDs and receipt times apart?
2. Is every refusal of tests 2 and 6 given before any row is written, with nothing recorded as product evidence?
3. Does a re-run load nothing new and say so (tests 5, 7)?
4. Does the bulk path write only `ingestion_batch`, `accepted_evidence`, `ingestion_disposition` and `recompute_job`,
   in the ledger's one writer, with the persistence guard unchanged and passing?
5. Is the bulk path unreachable from any HTTP module, and do commercial records still enter only through `3A2`'s
   intake (D-3A3.1)?
6. Do the S2, S3 and W2-03 suites pass unchanged after the two extractions?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 8. Out of scope

`COPY` into staging (D-DS3.1; `DS7` or `DS4` asks the owner for a writer block only if §5's numbers miss the
target); bulk commercial writes (D-DS3.2); the template ladder, `world build|clone|reset`, the build manifest and
golden digests (`DS4`); generating telemetry (`DS2`, next fortnight; DS4 decides the world's telemetry source);
estimates for lines not received (D-DS3.8); disorder tests on telemetry (real path); rejections in bulk.

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | `COPY` into staging, as the strategy says, or set-based `INSERT ... SELECT FROM unnest` in the one writer? | The latter (D-DS3.1; OWNER-AWAY row 10): no guard change; the same one-statement-per-table property |
| Q2 (owner) | Bulk commercial writes? | No: the intake loader (D-DS3.2; row 10; D-3A3.1) |
| Q3 | The "field gateway" half of the real-path slice | Central ingestion of the gateway's own Batch V2 bytes here; the field gateway's sealing stays proved by the Modbus and TEL acceptance tests (OD-22); DS4's world build runs the Lab gateway for its slice |
| Q4 (owner) | Lines the generated world marks `ESTIMATED_NOT_RECEIVED` | Not loaded and not estimated: "Not available yet" naming the record (D-DS3.8; row 11) until a declared-estimate unit is queued |
