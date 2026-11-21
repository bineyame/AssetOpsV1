# DS3: the bulk loader for the generated world's inputs (implementer spec)

Status: in_review (built on `task/DS3-bulk-loader`; mid-build Q1-Q3 answered, rev 3: D-DS3.20 to D-DS3.23). Rev 2, Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`;
pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4, rows 10 to 13 for the calls made here). Rev 2 folds the
handshake answers D-DS3.9 to D-DS3.19 (`rulings.md` "Handshake answers (round 1)"); the handshake is closed. `delivery-plan.md`
§2 row `DS3`: "Bulk loader: COPY into staging, set-based writes into input stores, the table allowlist and label
refusals; the real-path slice and its parity test" (3 units; depends on `DS1b`, `3A2`; feeds `DS4`, then `WK`).
Design source: data and build strategy §4 and §8 (branch `task/data-build-strategy`, `Docs/engineering/data-and-build-strategy.md`;
not on `main`). Lane A tail (`two-week-build-plan.md` §0.2 days 6-7). **4 units** (D-DS3.19; rev 1 said 3). Discovery review (W5): a second
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
  `backend/tests/test_s2_evidence_ledger_postgres.py` (`Kit`, `converted_enabled`), `backend/tests/pg_harness.py`,
  `backend/tests/test_w200_source_events_postgres.py` (`patched_v4`, `Builder`, `_delete_as_replica`).
- **Decisions:** `rulings.md` (D-DS3.1 to D-DS3.19). **Reviewer guide:** `reviewer-guide.md`. **Handshake:** `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question, and no other heavy database job holds the machine (row 4: DS3, DS4
  and WK one at a time). No unmerged dependency (`DS1b`, `3A2` are merged).
- **Branch** `task/DS3-bulk-loader` off `main`; worktree `/opt/assetecon/AssetOpsV1-ds3`; symlink
  `frontend/node_modules` from the main checkout.
- **Databases (authorised set only; nothing else).** Every Postgres test through `tools/heavy-slot.sh --db -- pwsh
  -NoProfile -File tools/run-host-tests.ps1 -- <file>`, on `pg_harness`-owned `*_test` clones made by the new
  `pg_harness.clone_database(tag, template_url=None)` (D-DS3.14; names `<stem>_pt<run>_<tag>_test`). Tags: pooled
  module `ds3s` (seed) and `ds3c1` ... `ds3cN` (one per case); parity `ds3pseed`, `ds3preal`, `ds3pbulk`; measurement
  `ds3bseed`, `ds3breal`, `ds3bbulk`. Each test drops its clones in `finally` (`pg_harness.drop_database`), and
  `cleanup()` drops any still registered. No `<prefix>_audit*` database is needed. Never the walkthrough database,
  ports 5490 or 8990, Docker, or a database outside `assetopsv1-postgres-1`.
- **Guard gate (first commit; D-DS3.18).** The first commit holds `_BULK_BATCH_SQL`, `_BULK_EVIDENCE_SQL` and
  `_BULK_DISPOSITION_SQL`. Before any Postgres test, run `pwsh -NoProfile -File tools/check-architecture.ps1` in this
  worktree; record the exit and the Configuration-persistence line in the packet. Non-zero: stop and ask the
  Architect; no edit under `tools/checks/` (a guard change is held for the owner, OWNER-AWAY row 5).
- **Read:** `rulings.md`; `ledger_service.py` (whole, 238 lines); `postgres_evidence_ledger.py:88-175`, `:284-360`,
  `:440-690`; `ledger.py:57-160`, `:268-300`, `:334-500`; `tools/checks/configuration-persistence.ps1:700-720`,
  `:815-845`, `:1255-1300`, `:1720-1760` (the ledger rules this unit must keep); `load_emulated_exports.py`;
  `test_s2_evidence_ledger_postgres.py:54-160`; `test_s3_dispatch_assessment_postgres.py:51-100` (`Feeder`);
  `pg_harness.py:68-80`, `:184-265`, `:390-450`; `test_w200_source_events_postgres.py:55-140`, `:513-575`; migrations
  `0012:95-133`, `0025:300-390`, `0026:199-220`, `0029:170-310`, `0047:60-130` (the triggers of D-DS3.10).
- **Pre-flight (done in the handshake).** The converted Kobo gateway is SIMULATED (`kobo-001.yaml:11` to
  `Kit.principal.mode`); 10 bindings over 8 devices, all valid from the Foundation's `2026-09-29T11:57:49Z`.
- **Files.** New: `backend/assetops_backend/evidence/bulk_load.py`, `backend/assetops_backend/load_world_inputs.py`,
  `backend/tests/test_ds3_bulk_load.py` (no database), `backend/tests/test_ds3_bulk_load_postgres.py`,
  `backend/tests/test_ds3_parity_postgres.py`, `backend/tests/test_ds3_bench_postgres.py` (D-DS3.16). Edited:
  `evidence/adapters/postgres_evidence_ledger.py` (one method, one read, one extracted helper, statement constants),
  `evidence/ledger_service.py` (one extracted method), `backend/tests/pg_harness.py` (two public functions, one
  cleanup line; D-DS3.14), `backend/tests/test_pg_harness.py` (their cases). No migration, no guard edit, no
  simulator or contracts change.

## 1. Outcome and why

The walkthrough database must be built in minutes from the generated world, and a "clean, good" database must be
provably the same as one fed through the real intake (owner, strategy question 4: "the parity test proves the bulk
rows equal the real path's on a fixed slice, every build"). DS3 delivers the bulk path and its proof; `DS4` builds the
template ladder and the world commands on it and re-benchmarks.

Gate questions: does a batch admitted in bulk store exactly the rows central ingestion stores for the same bytes
(receipt times and generated IDs apart)? Is anything other than a SIMULATED batch, or a batch with a rejected
ordinal, a published slot, a colliding message or a Site type parity has not proved, refused before a row is
written? Do the bulk statements target only the ledger's input tables, through its one writer, with every
trigger-written table equal to the real path's, and is the path unreachable from HTTP?

## 2. Design

### 2.1 Shared admission (`evidence/ledger_service.py`; a pure extraction, no behaviour change)

Extract submit's steps 2 to 5 (size, parse, claims, batch-ID conflict, binding set, basis) into
`BatchIngestionService.admit(principal, raw, received_at, refuse) -> Admission`, where `Admission` is a frozen
dataclass `(batch, text, basis, existing: BatchHandle | None)` and `refuse(principal, external_batch_id, digest,
received_at, status, kind, field, detail) -> Exception` builds the exception to raise. `submit` calls
`self.admit(principal, raw, received_at, self._refuse)` and continues exactly as today (open, drive, receipt). Every
existing S2 test passes unchanged; that is the extraction's proof. `admit` keeps calling `_check_claims` (which
raises `BatchRefused` itself, never through `refuse`) and `basis_from_snapshot` by its module-global name, so a test
patch of `ledger_service.basis_from_snapshot` (`patched_v4`) reaches both paths.

### 2.2 The bulk admission in the ledger's one writer (`postgres_evidence_ledger.py`)

```python
@dataclass(frozen=True)
class BulkAdmitted:
    external_batch_id: str; total: int; already_loaded: bool

class BulkAdmissionRefused(Exception):          # .code in BULK_REFUSALS, .detail
BULK_REFUSALS = frozenset({"BULK_PUBLISHED_BATCH", "BULK_BATCH_IN_PROGRESS", "BULK_MESSAGE_COLLISION",
                           "BULK_SITE_TYPE_UNPROVEN"})       # plus "BATCH_ID_CONFLICT", the real path's code (D-DS3.9)

def gateway_principal(self, site_id: UUID, gateway_id: UUID) -> GatewayPrincipal | None
    # SELECT tenant_id, site_id, id, mode FROM gateway WHERE site_id = :site AND id = :g
    # (no disabled filter: a disabled gateway is refused by _check_claims as GATEWAY_DISABLED; D-DS3.9)
def bulk_admit(self, principal: GatewayPrincipal, *, external_batch_id: str, payload_sha256: str, source_id: str,
               source_mode: str, basis: AcceptedAsBasis, batch_text: str, decisions: Sequence[Accepted],
               received_at: datetime, completed_at: datetime) -> BulkAdmitted
```

`bulk_admit`, in **one** transaction (`self._run(work, write=True)`):
1. `_lock_slot(c, tenant, site, external_batch_id)` (the slot lock `open_batch` takes).
2. An `evidence_publication` row for the slot: `BULK_PUBLISHED_BATCH` (a registered run's batch is bound to its
   publication only by the real path, `open_batch:342-352`; D-DS3.4).
3. An `ingestion_batch` row for the slot (rechecked under the lock; `load` has normally answered first, §2.4): same
   `payload_sha256` and `COMPLETED`: return `BulkAdmitted(..., True)` and write nothing; same digest, `IN_PROGRESS`:
   `BULK_BATCH_IN_PROGRESS`; another digest: `BATCH_ID_CONFLICT` (the lost race; one code for one condition,
   D-DS3.9).
4. `decided_at = self._decision_instant(c)`, once (S4-07's rule; one instant for the batch); `site_type =
   _site_type_on(c, tenant, site)`; `site_type != "MINIGRID"`: `BULK_SITE_TYPE_UNPROVEN` (parity proves MINIGRID
   only; DS4 lifts it per type with that type's parity slice, D-DS3.11).
5. `INSERT INTO ingestion_batch (...)` as `open_batch`'s statement, with `status 'COMPLETED'`, `processed_count`,
   `accepted_count` and `total_count` = `len(decisions)`, `duplicate_count`, `rejected_count`, `conflict_count` 0,
   `completed_at`, and `ON CONFLICT ON CONSTRAINT ingestion_batch_external_unique DO NOTHING RETURNING id` (no row
   returned: `BULK_BATCH_IN_PROGRESS`; the lock makes it unreachable, the arbiter keeps the guard's allowed shape).
6. `accepted_evidence`: **one** `INSERT INTO accepted_evidence (<the 42 columns of _persist, same order>) SELECT ...
   FROM unnest(CAST(:id AS uuid[]), CAST(:ordinal AS integer[]), ...) AS s(...) ON CONFLICT ON CONSTRAINT
   accepted_evidence_message_unique DO NOTHING RETURNING id`. Each column's value per ordinal is exactly what
   `_persist` binds for that `Accepted` (same expressions, the batch row's `gateway_id`, `source_id`, `received_at`,
   `foundation_revision_id`, `binding_set_revision_id`, `source_mode`); ids are `uuid4()` per ordinal, generated in
   Python as today. Fewer ids returned than decisions, or an `IntegrityError` with `_constraint(error) in
   _COLLISION_INDEXES` (event or EV START identity): roll back and raise `BULK_MESSAGE_COLLISION` (D-DS3.5). Any
   other `IntegrityError` (a foreign key, a CHECK) is a build defect: it propagates unchanged after the rollback
   (D-DS3.15), as in `_persist:575-578`.
7. `ingestion_disposition`: one `INSERT ... SELECT ... FROM unnest(...)` of `(batch_id, ordinal, tenant_id, site_id,
   message_id, 'ACCEPTED', accepted_evidence_id, NULL, decided_at)`.
8. Recompute jobs: `self._enqueue_admitted(c, row, site_type, admitted, decided_at)` (§2.3), once for the batch.
9. Return `BulkAdmitted(external_batch_id, len(decisions), False)`.

Statements are module-level `text()` constants (`_BULK_BATCH_SQL`, `_BULK_EVIDENCE_SQL`, `_BULK_DISPOSITION_SQL`), one
literal each, so `tools/checks/configuration-persistence.ps1` reads their targets: no `COPY`, no `MERGE`, no DDL, no
`DO UPDATE`, only the existing `DO NOTHING` arbiters (D-DS3.1). The guard passes unchanged: proved at the first
commit by a real run (§0 guard gate, D-DS3.18) and again by check-all.

**What the database writes besides (D-DS3.10).** The statements target only `ingestion_batch`, `accepted_evidence`,
`ingestion_disposition`, and `recompute_job` through `_coalesce_job`. Triggers fire on them as on the real path:
`enqueue_mini_depth` (deferred; mini-domain `recompute_job` per Site-local hour; requires the same-transaction
ACCEPTED disposition, which step 7 inserts before commit), `enqueue_ev_assessment` (deferred; EV `recompute_job`),
`ev_consequence_dirty_accepted` (EV consequence work), `financial_consequence_dirty_on_evidence`
(`financial_consequence_work`) and the statement-level `*_cic_ins` change log (`chain_input_change`, one row per
distinct Site per statement, so fewer rows in bulk). §3's census compares every table.

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
class BulkLoadRefused(Exception):            # .code: a BULK_LOAD_REFUSALS code or a real-path kind passed through
                                             # verbatim (table below); .external_batch_id (or None); .detail
@dataclass(frozen=True)
class BulkLoaded:
    batches: int; already_loaded: int; envelopes: int
class BulkEvidenceLoad:
    def __init__(self, ledger: PostgresEvidenceLedger, *, clock: Callable[[], datetime] = utc_now) -> None
    def load(self, raws: Sequence[bytes]) -> BulkLoaded
def permitted_database(url: str, environ: Mapping[str, str] | None = None) -> bool   # D-DS3.6, D-DS3.12
```
`load` handles the batches in the given order; each batch is its own transaction; the first refusal stops the load
(earlier batches stay, a re-run skips them). Per batch, in this order (the first that holds answers; D-DS3.9):

| # | Step | Refusal code |
|---|---|---|
| 1 | `len(raw) > MAX_BATCH_BYTES`; not UTF-8; `parse_canonical_batch_v2_text` fails | `TOO_LARGE`; `MALFORMED_TEXT`; `BatchRejected.kind` (submit's codes, raised directly) |
| 2 | `batch.source_mode != "SIMULATED"` | `BULK_NOT_SIMULATED` (D-DS3.6) |
| 3 | `ledger.gateway_principal(UUID(site_id), UUID(gateway_id))` is None | `BULK_UNKNOWN_GATEWAY` (no such gateway at that Site) |
| 4 | `admit(principal, raw, received_at, refuse)`; `_check_claims`'s `BatchRefused` caught and re-raised | its `kind`: `MODE_MISMATCH`, `GATEWAY_NOT_REGISTERED`, `GATEWAY_DISABLED`, `SOURCE_NOT_AFFILIATED`, `SOURCE_DISABLED` (`SCOPE_MISMATCH` unreachable: the principal comes from the claims) |
| 5 | `admit`'s own refusals through `refuse` | `BATCH_ID_CONFLICT`, `CONFIGURATION_UNREGISTERED`, a `ConfigurationRefused` kind, `CONFIGURATION_MISMATCH` |
| 6 | `admission.existing`: COMPLETED (same digest by step 5) | none: counted `already_loaded`, nothing decided or written |
| 6 | `admission.existing`: IN_PROGRESS | `BULK_BATCH_IN_PROGRESS` |
| 7 | `decide` per ordinal; any `Rejected` | `BULK_REJECTED_ORDINAL` (ordinal and kind in detail; D-DS3.5) |
| 8 | `ledger.bulk_admit(...)`; its `BulkAdmissionRefused` | same code: `BULK_PUBLISHED_BATCH`, `BATCH_ID_CONFLICT`, `BULK_BATCH_IN_PROGRESS`, `BULK_SITE_TYPE_UNPROVEN`, `BULK_MESSAGE_COLLISION` |

`refuse` returns `BulkLoadRefused(kind, external_batch_id, detail)` and **records nothing** (no `batch_refusal` row: a
refused bulk load is a build defect, reported by the command, never product evidence); every other refusal above
records nothing either. `received_at = clock()` once per batch; `completed_at=clock()` at step 8. Step 4's catch is
`except BatchRefused as error: raise BulkLoadRefused(error.kind, batch.batch_id, error.detail) from None` around
`admit` only.

`permitted_database(url, environ)`: with `target = database_target(url, environ)`: `not re.search(r"walk|serve", target.name)`
(deny; D-DS3.22); and `re.fullmatch(r"[a-z0-9_]+_audit[a-z0-9_]*", target.name)` or
`re.fullmatch(r"[a-z0-9_]+_pt[0-9a-f]+_[a-z0-9]+_test", target.name)` (a `pg_harness.database_name` clone; a bare `_test` name
is no longer permitted, D-DS3.22); and `not is_operator_name(target.name)`; and
`target.host in {"127.0.0.1", "localhost"}` and `target.port == int(env.get("ASSETOPS_PG_PORT", "55432"))` (the port
`docker-compose.yml:21` publishes for `assetopsv1-postgres-1`; D-DS3.12). A `DatabaseTargetUnclear` or a missing port
is false. The command is never the tool that loads the served walkthrough database: DS4 builds into
`assetops_ds4_audit<MMDD>`; how the walkthrough serve reaches it is DS4's question to the owner (held).

### 2.5 The world command (`python -m assetops_backend.load_world_inputs`)

`build_parser()` public; `main(argv, *, ledger=None, load_exports=None) -> int`. Arguments: `--world DIR`, `--submit-as
EMAIL`, `--accept-as EMAIL`, optional `--tenant SLUG` (one tenant only). **Layout (D-DS3.13):** one directory per
tenant slug, holding at most `commercial/` (the tenant's DS1b canonical files, exactly what
`load_emulated_exports --dir` accepts) and `telemetry/` (Batch V2 files `*.batch.json`); anything else in a tenant
directory is `WORLD_LAYOUT_UNKNOWN`. Steps: no `DATABASE_URL`: `NO_DATABASE`; `permitted_database` false:
`BULK_DATABASE_NOT_PERMITTED`; the layout of every selected tenant checked: `WORLD_LAYOUT_UNKNOWN` (all three before
any connection); then per tenant in sorted order: (a) commercial, when `commercial/` exists:
`load_emulated_exports.main(["--dir", <tenant>/commercial, "--tenant", slug, "--submit-as", s, "--accept-as", a])`
(D-DS3.2); (b) telemetry, when `telemetry/` exists: `BulkEvidenceLoad(ledger).load(raws)` over its `*.batch.json`
files in sorted name order. Output on success: one JSON line per tenant, `{"tenant", "commercial_exit", "batches",
"already_loaded", "envelopes"}` (`commercial_exit` null when no `commercial/`), exit 0.

| Exit | Meaning | stderr |
|---|---|---|
| 0 | done | nothing |
| 2 | this command refused: `NO_DATABASE`, `BULK_DATABASE_NOT_PERMITTED`, `WORLD_LAYOUT_UNKNOWN`, any `BulkLoadRefused` | `<CODE> <external_batch_id or -> <detail>` |
| 3 | a database error (including D-DS3.15's propagated `IntegrityError`) | `DATABASE_ERROR <exception class>` (never the URL) |
| 4 | the commercial step returned non-zero; that tenant's telemetry and later tenants are not loaded | the loader's own lines, then `COMMERCIAL_EXIT <tenant> <loader exit>` |

The command reads no oracle, writes no file.

**Unreachable from HTTP:** no module named `main.py` or `*_api.py` imports `bulk_load`, `load_world_inputs` or calls
`bulk_admit`; `bulk_admit` has exactly one caller (`bulk_load.py`); test 9.

## 3. The parity slice (fixtures; hand-written in the tests, W2)

**Seed.** `seed = pg_harness.clone_database("ds3pseed")` (from the run template, at head). On it, with an engine and
store built from `seed` (never the module `URL`): `converted_enabled(store, engine)` and `Kit(engine, ...)` as
`test_s3_dispatch_assessment_postgres.py` `site`; then the Site's current binding sets relabelled
`minigrid-roles-4` with `test_w200_source_events_postgres._delete_as_replica` exactly as `v4_roles4` does (test-only;
it makes `enqueue_mini_depth` write jobs on both paths, D-DS3.10); nothing ingested. Read the census baseline (row
count of every base table of `current_schema()` except `alembic_version`). Dispose every engine on `seed`, then
`real = clone_database("ds3preal", seed)`, `bulk = clone_database("ds3pbulk", seed)`: both hold the same Site,
gateway, sources and binding set with the same ids.

**Two Kobo days.** The rows of `test_s3_dispatch_assessment_postgres.interval_rows` written out for 6 and 7 October
2026, 00:00 to 23:45 UTC every 15 minutes: `generator-controller/status` RUNNING from 06:00 to 08:00 and STOPPED
otherwise, the three feeders `residential-meter`, `clinic-meter`, `mill-meter` at 10, `battery-pcs-controller/
state-of-charge` at 80 (to 06:00), 60 (06:00 to 08:00) and 80 after. Sealed once with the seed's `Kit`, one batch per
device per day (`Kit.seal(texts, device_id=...)`), `source_mode` SIMULATED, epoch `epoch-1`, sequences per
`Feeder.deliver`. The same list of batch bytes `B` feeds both paths. The test writes the expected counts by hand:
5 devices × 2 days = 10 batches; 192 envelopes per device (96 per day) except the generator status (96 per day as
well) = 960 envelopes (the pre-flight confirmed the five devices).

**v4 slice (D-DS3.11).** With `patched_v4(kit, monkeypatch)` active for both loads: one batch `V`, `kit.seal([v4.event(100001,
"START_RESULT", "evt-1", "FAILED"), v4.start(100002, "start-1"), v4.point(100003)])`, appended to
`B` (sequences far above the Kobo days'). The real path must accept all three ordinals (asserted). `v4.delta` is not
a member: central ingestion refuses it on `charger-controller/session-event` (D-DS3.20); it is a test-6 refusal case. The seven v4-only columns are compared by the `accepted_evidence` list below.

**Real path:** on `real`, `BatchIngestionService(PostgresEvidenceLedger(real)).submit(kit.principal, b)` for each
`b` in `B`, each 200 and COMPLETED. **Bulk path:** on `bulk`, `BulkEvidenceLoad(PostgresEvidenceLedger(bulk)).load(B)`
(11 batches, 963 envelopes).

**Equal rows** (each a sorted list of tuples, compared exactly):
- `accepted_evidence`: every column except `id`, `batch_id`, `received_at`, keyed by `(source_id, message_id)`;
- `ingestion_batch`: every column except `id`, `received_at`, `completed_at`, keyed by `external_batch_id`;
- `ingestion_disposition` joined to its batch and evidence: `(external_batch_id, ordinal, message_id, decision,
  evidence message_id)`, ignoring `batch_id`, `accepted_evidence_id`, `decided_at`;
- `evidence_rejection`, `batch_refusal`, `batch_publication_link`: zero rows on both.
**Recompute jobs**, per domain: `RECOMPUTE_DOMAIN` (D-DS3.3): on both, every accepted v3 reading's `interval_start`
or `source_time` lies inside some PENDING dispatch job window of the Site; the bulk path has at most one dispatch job
per batch and at most as many as the real path. Every other domain present on either side (the mini domains,
`ev_*`; trigger-written per hour or window): the sorted list of `(domain, window_start, window_end, status)` equal
on both, ignoring `id`, `cause_evidence_id`, `available_at`, `created_at` (D-DS3.10); the test asserts at least one
mini-domain job exists (the relabel took effect).
**Census** (D-DS3.10): for every base table, `delta = count after - baseline`. Equal on both paths for every table
except `recompute_job` (the rules above), `chain_input_change` (the set of distinct `(tenant_id, site_id,
table_name)` among new rows equal; bulk count at most real) and `event_outbox` (per `(tenant_id, site_id, source, type)`:
the groups equal, bulk count at most real, the subject cover equal; D-DS3.21). Every table with a non-zero delta on either side is in
the test's named list (`ingestion_batch`, `accepted_evidence`, `ingestion_disposition`, `recompute_job`,
`chain_input_change`, and any table the real path's triggers write on this seed, named with its delta as a literal);
an unnamed table fails with its name. No test is `xfail`: the census and the v4 slice both pass. `financial_consequence_work` and the EV consequence work tables have delta 0
on both (no Finding or assessment revisions in the seed; the stated limit).

## 4. Tests (written first)

**No database** (`backend/tests/test_ds3_bulk_load.py`):
1. `permitted_database` (all on `127.0.0.1:55432` with an explicit empty `environ` unless said): `assetops_test`
   false (D-DS3.22); `assetops_pt1a_ds3bulk_test` true; `assetops_ds3_audit1121` true; `assetops_ds4_audit1125` true;
   `assetops_polish_walk1113_test` false (the live walkthrough database); `assetops_walk_audit1121` false; `assetops_other_test` false;
   `assetops_polish_walk1113` false; `assetops_op_kobo` false; `assetops_op_kobo_test` false; `_audit` false; a URL
   with a `dbname` query false (unclear); `assetops_test` on host `10.0.0.5` false; on port 5432 false; with no port
   false; on port 55433 with `environ={"ASSETOPS_PG_PORT": "55433"}` true.
2. The command's refusals with injected fakes: no `DATABASE_URL` (`NO_DATABASE`, exit 2); a non-permitted URL
   (`BULK_DATABASE_NOT_PERMITTED`, exit 2, the fake ledger never constructed); a tenant directory holding a stray
   file (`WORLD_LAYOUT_UNKNOWN`, exit 2, ledger never constructed); a commercial loader stub returning 3 (the command
   exits 4, stderr ends `COMMERCIAL_EXIT <tenant> 3`, no telemetry loaded); the stub receives `--dir
   <world>/<tenant>/commercial`; a tenant with `telemetry/` only (`commercial_exit` null, stub not called); success
   prints one line per tenant with exactly the five keys.
3. Seams (an `ast` scan): `bulk_admit` is called only in `evidence/bulk_load.py`; no `main.py` or `*_api.py` imports
   `bulk_load` or `load_world_inputs`; `bulk_load.py` imports no `simulator`, `host` or `commercial` module; the three
   `_BULK_*` statements' targets (`(?i)\b(?:INTO|UPDATE)\s+([a-z_]+)`) are a subset of `{"ingestion_batch",
   "accepted_evidence", "ingestion_disposition"}` and contain no `COPY`, `MERGE`, `DO UPDATE`, `CREATE`, `TRUNCATE`;
   `_BULK_EVIDENCE_SQL`'s column list equals `_persist`'s INSERT column list, in order (both parsed from the module).
   The caller scan covers `backend/assetops_backend/` only; tests may call `bulk_admit` directly (test 6).

**Postgres, pooled** (`backend/tests/test_ds3_bulk_load_postgres.py`): a module fixture seeds `clone_database("ds3s")`
as §3 without the relabel and without the v4 patch, disposes it, and gives each test (and each case of test 6) a
fresh `clone_database(f"ds3c{n}", seed)`, dropped in `finally`; `recompute_job` is counted with `domain =
'dispatch'` (as `Kit.counts`).
4. One generator-status day (96 envelopes) loads: one `ingestion_batch` COMPLETED with counts 96/96/0/0/0, 96
   `accepted_evidence` rows, 96 dispositions ACCEPTED, one PENDING dispatch job covering the day; `BulkLoaded(1, 0, 96)`.
5. The same bytes again: `BulkLoaded(1, 1, 96)`, no row added (counts before and after).
6. Refusals, each on a fresh clone and each leaving every ledger table's row count unchanged (`ingestion_batch`,
   `accepted_evidence`, `ingestion_disposition`, `evidence_rejection`, `batch_refusal`, dispatch `recompute_job`;
   after a preliminary load where the case needs one, counted after it): a LIVE batch (`Kit.seal(..., mode="LIVE")`;
   `BULK_NOT_SIMULATED`); an unknown gateway id (`seal_batch_v2` directly, D-DS3.17; `BULK_UNKNOWN_GATEWAY`); the
   gateway disabled (`UPDATE gateway SET disabled_at`, as `test_s2_evidence_ledger_postgres.py:360`;
   `GATEWAY_DISABLED`); the source disabled (as `:354`; `SOURCE_DISABLED`); a batch with one envelope outside the
   binding's valid period (`BULK_REJECTED_ORDINAL`, ordinal named; the real path would store a rejection); a batch `[v4.delta(...)]` on the MINIGRID Site
   (`BULK_REJECTED_ORDINAL`, `MAPPING_INCOMPATIBLE` in detail, no row written; D-DS3.20); the same
   batch ID with other bytes after a load (`BATCH_ID_CONFLICT`, from `admit`); the lost race: `ledger.bulk_admit`
   called directly after that load with another `payload_sha256` (`BulkAdmissionRefused`, `BATCH_ID_CONFLICT`); an
   `evidence_publication` row inserted for the slot through `test_s405_publication_postgres.py`'s helper first
   (`BULK_PUBLISHED_BATCH`); the Site set to `COLDCHAIN` before any evidence (`UPDATE site SET site_type`, as
   `test_w402_migration_postgres.py:135`; `BULK_SITE_TYPE_UNPROVEN`); a second batch reusing one message id of a
   loaded batch (`BULK_MESSAGE_COLLISION`, and the second batch's `ingestion_batch` row absent: one transaction);
   `ledger.bulk_admit` called directly with one decision's `binding.binding_revision_id` replaced by a random UUID
   (an `IntegrityError` propagates, not `BulkAdmissionRefused`; D-DS3.15); a malformed body (`BatchRejected`'s kind,
   no `batch_refusal` row).
7. A load stopped by a refusal at its third batch: batches one and two stay COMPLETED; a re-run after removing the
   bad batch reports them as `already_loaded` and loads the rest.

**Parity** (`backend/tests/test_ds3_parity_postgres.py`): 8. §3 in full: the hand counts (11 batches, 963
envelopes), every equal-rows list equal (Kobo days and the v4 batch), the recompute-job rules, the census; the test
drops its three clones in `finally`.

**Harness** (`backend/tests/test_pg_harness.py`, D-DS3.14): `clone_database` returns a `*_test` URL of the owned
pattern, the database exists and is registered; cloning from a source with an open session fails with the session
count named; `drop_database` drops and unregisters; `cleanup()` drops a still-registered clone.

**Regression:** every `test_s2_*`, `test_s3_dispatch_assessment_postgres.py`, `test_w203_*` (cold enqueue),
`test_s405_publication_postgres.py`, `test_3a3_*` loader tests, `test_pg_harness.py`, `test_w200_source_events_postgres.py`;
the persistence guard unchanged and passing (first-commit gate, D-DS3.18); check-all once at the end; `select-tests
--base main` before review.

## 5. Unit 3: the measurement for DS4 (packet only)

`backend/tests/test_ds3_bench_postgres.py` (D-DS3.16): marked `slow`, skipped unless `ASSETOPS_DS3_BENCH=1`; run
once with `-s` through `tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- <file>`. Seed
`clone_database("ds3bseed")` as §3 (no relabel, no v4), then `ds3breal` and `ds3bbulk` from it; seal 14 Kobo days (the
§3 rows, 6 to 19 October) and load them once by `submit` and once by `load`; record wall time, rows per table and
`pg_total_relation_size` before and after for each, and the statements per table (`pg_stat_statements` if enabled,
else a SQLAlchemy `before_cursor_execute` counter); print one JSON line; drop the three clones in `finally`. The packet
copies the line with the slot label, the machine idle; DS4 replaces strategy §4's targets with them. It asserts no
time; no figure here is a gate.

## 6. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (2.0) | first commit: the `_BULK_*` constants and the guard gate run (D-DS3.18); §2.1 extraction; §2.2 `bulk_admit`, `gateway_principal`; §2.3 extraction; §2.4 service; `pg_harness` helper and its tests; tests 3 (static), 4 to 7; S2/S3/W2-03/W2-00 regression | 2 |
| 2 (1.5) | §2.5 command; tests 1, 2; §3 parity with v4 slice and census, test 8 | 1 |
| 3 (0.5) | §5 measurement module and its run; check-all; packet | 1 |

Total 4.0 (rev 1: 3.0; D-DS3.19). Under the 6-unit split rule. Packet `specs/DS3-bulk-loader/packet.md`: the guard gate run (exit and line), the clone names used and dropped,
the parity counts and census deltas, §5's numbers, residual risk `R-TRUST` (the command is a trusted tool: it admits batches with no gateway credential, behind
the permitted-database and SIMULATED refusals), the mid-build count.

## 7. Done (questions; each can fail)

1. Do the real path and the bulk path store the same rows for two Kobo days and one v4 batch (test 8), IDs and
   receipt times apart, with every table's census delta equal or within its stated rule?
2. Is every refusal of tests 2 and 6 given before any row is written, in §2.4's order with one code per condition,
   with nothing recorded as product evidence?
3. Does a re-run load nothing new and say so (tests 5, 7)?
4. Do the bulk statements target only `ingestion_batch`, `accepted_evidence`, `ingestion_disposition`, and
   `recompute_job` through `_coalesce_job`, in the ledger's one writer, with triggers firing as on the real path
   (test 8's census) and the persistence guard unchanged and passing at the first commit and at the end?
5. Is the bulk path unreachable from any HTTP module, and do commercial records still enter only through `3A2`'s
   intake (D-3A3.1)?
6. Do the S2, S3 and W2-03 suites pass unchanged after the two extractions?
7. Is a batch at a non-MINIGRID Site, or an integrity failure that is not a listed collision, refused or propagated
   with nothing written (test 6)?
8. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 8. Out of scope

`COPY` into staging (D-DS3.1; `DS7` or `DS4` asks the owner for a writer block only if §5's numbers miss the
target); bulk commercial writes (D-DS3.2); the template ladder, `world build|clone|reset`, the build manifest and
golden digests (`DS4`); generating telemetry (`DS2`, next fortnight; DS4 decides the world's telemetry source);
estimates for lines not received (D-DS3.8); disorder tests on telemetry (real path); rejections in bulk; bulk loading
at COLDCHAIN and EV_CHARGING Sites (D-DS3.11; DS4 adds their parity slices); loading or serving the walkthrough
database (D-DS3.12; DS4, owner).

## 9. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | `COPY` into staging, as the strategy says, or set-based `INSERT ... SELECT FROM unnest` in the one writer? | The latter (D-DS3.1; OWNER-AWAY row 10): no guard change; the same one-statement-per-table property |
| Q2 (owner) | Bulk commercial writes? | No: the intake loader (D-DS3.2; row 11; D-3A3.1) |
| Q3 | The "field gateway" half of the real-path slice | Central ingestion of the gateway's own Batch V2 bytes here; the field gateway's sealing stays proved by the Modbus and TEL acceptance tests (OD-22); DS4's world build runs the Lab gateway for its slice |
| Q4 (owner) | Lines the generated world marks `ESTIMATED_NOT_RECEIVED` | Not loaded and not estimated: "Not available yet" naming the record (D-DS3.8; row 12) until a declared-estimate unit is queued |
| Q5 (owner) | Bulk-load cold-chain and EV Sites now (add their parity slices, +0.75 unit) or refuse them until DS4 adds the slices? | Refuse (`BULK_SITE_TYPE_UNPROVEN`; D-DS3.11; row 13): bulk loads only what parity proves |
| Q6 (owner, DS4) | How the walkthrough serve reaches a world built into `assetops_ds4_audit<MMDD>` | **Held** for the owner at DS4 (D-DS3.12); no authorisation widened here |

## 10. Rev 3 (mid-build answers)

D-DS3.20: v4 slice is three shapes, `v4.delta` a refusal case. D-DS3.21: `event_outbox` parity is the subject cover per group. D-DS3.22: `permitted_database` allows only `_audit*` and harness clones and denies `walk|serve`; plants P24, P25. D-DS3.23: the 11 pre-existing failures do not block. The envelope count in §3 is 963 (960 Kobo plus the v4 batch's three).
