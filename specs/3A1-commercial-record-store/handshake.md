# 3A1 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

Round 1 was written by one fresh Claude reviewer covering both roles, on `main` at `2f5f2ce3c`, with read-only
commands only (no database, server or Docker). The dispatch asked for the pre-flight to be numbered P1 ..., so it is
numbered P rather than I. Severity: **High** means the spec cannot be built or passed as written, **Medium** means a
gap that changes correctness or what counts as done, **Low** means a clarification.

Highs: **R1**, **R6** and **R7**.

## Reviewer questions

### The five questions the Architect expected

**R1 (High, done). §2, §3 rule 1: an envelope refusal cannot be written as the specified REFUSED intake row. Does it
keep the raw bytes or only the SHA?**
- *Why it matters.* Rule 1 says a `json.` or `batch.` refusal writes one `commercial_intake` row. But that row's
  `source_type`, `source_system`, `provenance` and `produced_at` are `NOT NULL` with CHECKs (`spec.md:66-70`). A
  `CANONICAL_TYPE json` (not JSON), `CANONICAL_SOURCE_TYPE batch.source_type` or `CANONICAL_PROVENANCE
  batch.provenance` refusal has no valid value to put there. `parse_batch` raises before it returns any envelope
  (`contracts/assetops_contracts/canonical/records_v1.py:757-781`). So the adapter must either invent values (which
  is a dishonest record) or fail the CHECK (which turns a refusal into a 500). `batch_sha256` (`spec.md:71`) is also
  undefined. `batch_digest` covers only valid records (2a `spec.md:346`) and does not exist for a refused envelope,
  so the column needs its own definition. Design §6.1 says "raw file bytes live with the intake", but this schema
  has no bytes column.
- *Proposed answer.* (a) Make `source_type`, `source_system`, `provenance` and `produced_at` nullable, with
  `CHECK (state = 'REFUSED' OR (source_type IS NOT NULL AND source_system IS NOT NULL AND provenance IS NOT NULL AND
  produced_at IS NOT NULL))`. On a refusal, fill each one only when the envelope got far enough to parse it. (b)
  `batch_sha256` is the SHA-256 of `data` exactly as received, for every intake. (c) Keep the SHA only, never the
  raw bytes. Raw bytes are unvalidated and may hold personal data (R13), and the native file belongs to `3A2`. Add a
  no-DB test for each envelope stage: not JSON, bad `source_type`, bad `provenance`.

**R2 (Low). §4.1 `latest_revisions`: should it filter out REFUSED intakes?**
- *Why it matters.* Rule 1 writes nothing but the intake row for a REFUSED intake (`spec.md:163-165`), so no
  revision can reference one. A filter would be dead code that hides a writer bug instead of exposing it.
- *Proposed answer.* No filter. The adapter test asserts the invariant: no revision joins a REFUSED intake, after
  the full fixture run including the refusals. A DB constraint is not worth a trigger.

**R3 (Low). §2 `amount numeric`, `quantity numeric`: numeric type and scale.**
- *Why it matters.* An unbounded `numeric` keeps the input scale (`1.50` stays `1.50`), and psycopg returns it as
  `Decimal`. 2a bounds every decimal to 32 characters with `adjusted()` in [-12, 12] (2a `spec.md` §6.3), so
  `numeric(p,s)` would only add a rounding risk. The real risk is a float in between: the in-memory store, a
  `float()` in the service, or a JSON round trip of the row.
- *Proposed answer.* Keep the unbounded `numeric`. Make probe P7 a test over every fixture record that carries an
  amount or quantity: `format(row.amount, "f")` equals the record's own decimal text in `canonical`, through both
  stores. Add a no-DB test that greps `backend/assetops_backend/commercial/**` for no `float(`. Body decimals
  (BUDGET_LINE `value`, `rate`, tariff bands) live only in `canonical`. Note for `3A4`: they are parsed with
  `Decimal`, never `json.loads` defaults.

**R4 (Medium, done). §6 lock proof: can it actually fail?**
- *Why it matters.* As written, the proof passes only if (1) the decision is re-made under the lock and (2) the
  re-read sees the other thread's commit. It can fail, or pass for the wrong reason, in three ways:
  - "Both alive after 0.5 s" does not prove the threads are waiting on *the* advisory lock. A pool wait or a slow
    start also leaves them alive. The 3C0a precedent also asserts the count of waiters in `pg_locks`
    (`backend/tests/test_3c0a_accounts_postgres.py:331-358`, `_waiting_on_advisory(...) == 2`).
  - Under REPEATABLE READ, the snapshot is taken by the lock statement itself, before it waits. The re-read then
    misses the winner's commit, and the loser hits `UNIQUE (tenant_id, source_system, source_record_id)`. The
    codebase uses REPEATABLE READ for reads elsewhere (`ev_depth_api.py:6`, `main.py:537`), so this mistake is
    easy to copy.
  - `write_intake(...) -> None` (`spec.md:211`) cannot tell the service what was decided under the lock. So the
    reported outcome is the pre-lock guess (NEW for both threads), even when the store did the right thing (P2).
- *Proposed answer.* The proof asserts `pg_locks` advisory waiters `== 2` as well as `is_alive`. The spec states
  that the writing transaction is READ COMMITTED. `write_intake` returns the plan it applied (P2). The pass
  condition stays "one NEW, one UNCHANGED, one `commercial_record` row, one revision". Add a negative check to the
  packet (RULES §7): with the re-read under the lock removed, the proof fails.

**R5 (Low). §6: DS1b's CLI inside a no-DB test.**
- *Why it matters.* The CLI route is the only one allowed. `tools/checks/dependency-direction.ps1:59-65` scans
  all of `backend/`, tests included, and bans `import assetops_simulator`, so a backend test cannot call
  `build_records` in process. The CLI's other behaviours:
  - it refuses an `--out` inside the repository (`tools/world_history.py:73`);
  - it also writes `unwritten.json` (`:92`), which is not a batch;
  - it puts its *own* tree's `simulator` and `contracts` on `sys.path` (`:5-6`).
  Run read-only on the fixture into a scratch folder, it took 0.13 s and wrote 7 batches with 142 records (84
  BUDGET_LINE, 57 EXPENSE, 1 ADJUSTMENT). No `(tenant, source_system, source_record_id)` key collides across
  batches, and no record lacks a Site.
- *Proposed answer.* Run it with `subprocess.run([sys.executable, <tree>/tools/world_history.py, "records",
  "--manifest", <tree>/simulator/tests/world/fixtures/view_v1.json, "--out", tmp_path / "ds1b"], check=True)`, with
  `<tree>` derived from `Path(__file__)`, never a literal `/opt/assetecon/AssetOpsV1`. Ingest `*.json` except
  `unwritten.json`. Assert 142 NEW, then 142 UNCHANGED, with no rejection.

### Further reviewer questions

**R6 (High, done). §4.1 `intake(tenant_id, intake_id) -> IntakeResult`: the outcomes cannot be rebuilt from what
is stored.**
- *Why it matters.* `IntakeResult.outcomes` holds a `RecordOutcome(index, ...)` per input record (`spec.md:196`),
  but the store does not keep enough to rebuild them:
  - an UNCHANGED record writes nothing;
  - a revision row has no `record_index`;
  - a revision is written once per `(record, source_version)` (`spec.md:133`), so its index belongs to its first
    intake only.

  So `intake()` cannot return the outcomes in input order, or return the UNCHANGED outcomes at all. §6's "the
  adapter round-trips every port method" (`spec.md:256`) then cannot pass for `intake()`.
- *Proposed answer.* `intake()` returns a new `IntakeSummary`: the intake row (state, refusal, the five counts,
  `entered_by`, `entered_at`), the rejection rows in `record_index` order, and the IDs of the revisions that intake
  wrote. Only `ingest` returns the full per-record `IntakeResult`. If `3A2` needs a stored row-by-row account, add
  `record_index int NOT NULL` to the revision table, and say plainly that UNCHANGED rows are counted, not listed.

**R7 (High, done). §4.1 `latest_revisions(..., recognition_period=...)`: is the filter applied before or after
"latest"?**
- *Why it matters.* `recognition_period` is a revision column (`spec.md:115`), so a correction can move a record
  from `2026-10` to `2026-11`. If the period filter runs before picking the highest revision (`WHERE
  recognition_period = :p` then `DISTINCT ON (record_id)`), October still returns revision 1 and November returns
  revision 2. The same money is then counted in both months: exactly the late-record case of P3A rule 2, which
  `3A4` builds on. The index (`spec.md:136-137`) leads with `recognition_period`, which invites the wrong order.
- *Proposed answer.* "Latest" is chosen per record over all of its revisions first. `site_id`, `kind` and
  `recognition_period` then filter the latest rows. Add a test to both stores: revision 1 in October, revision 2 in
  November; `latest_revisions(recognition_period="2026-10")` is empty and November returns revision 2.

**R8 (Medium, done). §3 rule 5 and §6 "the same file twice (all UNCHANGED, no new rows)": does a repeated file
write an intake row?**
- *Why it matters.* Each intake is "one transaction" with its own `commercial_intake` row and counts. A second
  identical file is a STORED intake with `unchanged_count = record_count`. But the test (`spec.md:240`) and probe
  P1 (`reviewer-guide.md:20`, "the row counts do not change") say no new rows at all. The implementer and the
  reviewer will read "adds nothing" differently.
- *Proposed answer.* A repeated file writes one STORED intake row (the account of who sent what, when, D-3A1.4) and
  no `commercial_record`, revision or rejection row. Reword the test and P1 to "no new record, revision or rejection
  row; one intake row with every record UNCHANGED".

**R9 (Medium, done). §3 rules 4-5: two versions of one record in the same batch.**
- *Why it matters.* 2a refuses only a repeated `(source_record_id, source_version)` (2a `spec.md:338`;
  `records_v1.py:797-801`). So `X@1` and `X@2` in one batch are both valid. A `decide(existing)` made against the
  pre-batch state calls both NEW and writes two `commercial_record` rows, which fails the UNIQUE key and loses the
  whole intake. The same applies to `X@1` as a CHARGE and `X@2` as a RECEIPT (kind changed within the batch).
- *Proposed answer.* Records are decided in input order against a running state that includes earlier records of
  the same batch: `X@1` is NEW (revision 1) and `X@2` is REVISED (revision 2, superseding the revision just
  planned); a later kind or Site change in the same batch is refused. Add one no-DB test and one Postgres test.

**R10 (Medium). D-3A1.3: "latest" is arrival order, not the source's order.**
- *Why it matters.* `source_version` is opaque text, and `revision_no` is `max + 1` (`spec.md:179`). Say a
  version-2 export arrives first and a version 1 that was never seen arrives later (a skipped export re-sent). Then
  version 1 becomes revision 2 and the latest, and the older figure wins. Replaying versions already seen is safe
  (UNCHANGED).
- *Proposed answer.* State that the latest revision is the last *received* one, and that the source's version order
  is not interpreted. Record it as a named residual for `3A3`/`3A4`; the contract test can require monotone versions
  per source. Alternatively, refuse `INTAKE_VERSION_STALE` when the batch's `produced_at` is earlier than the latest
  revision's intake `produced_at`. Default: arrival order, documented.

**R11 (Medium). §2: the revision chain and the copied columns are not enforced per record.**
- *Why it matters.* `supersedes_revision_id REFERENCES commercial_record_revision (id)` (`spec.md:125`) lets a
  revision supersede *another record's* (or another tenant's) revision. Nothing ties it to `revision_no - 1`. The
  revision's own `site_id` and `kind` (`spec.md:106-107`) are copied from `commercial_record` without any check that
  they agree, yet `latest_revisions` filters on the copies.
- *Proposed answer.* Add `UNIQUE (record_id, id)` to the revision table and `FOREIGN KEY (record_id,
  supersedes_revision_id) REFERENCES commercial_record_revision (record_id, id)`. Add `UNIQUE (tenant_id, id, kind)`
  on `commercial_record` with `FOREIGN KEY (tenant_id, record_id, kind)` from the revision. `site_id` is nullable,
  so MATCH SIMPLE would skip it; leave it to a Postgres test that compares revision and record `site_id`. Also test
  that revision `n` supersedes revision `n-1` of the same record.

**R12 (Medium). Honest label words: `provenance` is whatever the file says.**
- *Why it matters.* P3A says "Only an operator's own export reads *Recorded*" (`structure-page-P3A.md:55-56`). But
  `provenance` is copied from the batch (`spec.md:187`), so any caller's file can declare `observed-financial`. Also,
  `record_sha256` covers the record without its envelope, so the same version re-sent under a different provenance
  is UNCHANGED and keeps its first label. That label is wrong in either direction.
- *Proposed answer.* 3A1 stores the *declared* provenance and says so in the docstring and in `RevisionRow`.
  `3A2` must cap it by the path (a person's upload of an emulator file can never be `observed-financial`); record
  that as a hand-off in `rulings.md`. In 3A1, the same `source_version` and digest with a different provenance is
  `INTAKE_VERSION_CONFLICT` (or a new `INTAKE_PROVENANCE_CHANGED record.source_version`), never a silent UNCHANGED.

**R13 (Medium). Personal data in stored payloads.**
- *Why it matters.* The data and the tables keep identifiers for good:
  - `canonical` keeps every ref: `payer_ref`, `customer_ref`, `subject.ref`, `authorised_by_ref`, `parties`;
  - 2a says refs are pseudonymised by the source adapter, but "the format does not check that" (2a `spec.md:239`);
  - `commercial_rejection.source_record_id` can hold an unvalidated source key (P4);
  - all four tables are append-only, so a person's data can never be erased.

  `hide_parameters=True` covers SQL errors only, not logs or exception text from the service.
- *Proposed answer.* A ruling: the store holds only pseudonymised refs and never raw bytes (R1). The service and
  the adapter never log `canonical`, refs or raw values. Erasure under a data-protection request is out of scope and
  named as a pilot residual (append-only plus pseudonym-key destruction upstream). Probe P6 also covers a record
  refusal and a tenant mismatch: no ref appears in the result's `path` or in any exception text.

**R14 (Medium). §0 migration numbering against 3C1's `0064_person_on_commands`.**
- *Why it matters.* 3C1 is told to name its migration 0064 (`specs/3C1-person-on-commands/spec.md:40`), but neither
  spec gives 3C1's `down_revision`. If 3C1 merges first on `0062`, "renumber the second" gives either a gap (0063
  missing) or a 0063 whose parent is 0064. The renumber also changes literals this spec pins:
  - the `RAISE` text `Downgrade of 0063_commercial_records refused` (`spec.md:154`);
  - a downgrade target in the test.
- *Proposed answer.* Rule: the first slice to merge takes 0063 on `0062`, and the second takes 0064 on the first.
  Each test derives its downgrade target from the migration module's `down_revision` and the head from
  `pg_harness.alembic_head()` (`backend/tests/pg_harness.py:152`), never a literal. The refusal text is checked
  with a pattern on `refused: commercial records exist`.

**R15 (Low, done). §3 rules 1-2 and 7: small undefined cases.**
- *Why it matters.* Each of these needs one fixed answer before the tests are written:
  - an unknown `tenant_id` (`tenant_slug` returns None);
  - what a tenant mismatch's counts are (record_count 0, or n with `refused_count` n and no rejection rows?);
  - what `IntakeResult.intake_id` is on a dry run, when no row is written;
  - what the in-memory `threading.Lock` per tenant is meant to prove.
- *Proposed answer.*
  - An unknown tenant is a programming error (`LookupError`), not a stored intake, because the tenant FK would
    fail anyway.
  - Both intake refusals write all counts 0.
  - A dry run returns `intake_id=None`.
  - The in-memory lock only makes the fake safe; the concurrency claim rests on the Postgres proof alone.

**R16 (Medium). `mid-build-questions.md` is DS1b's file under a 3A1 title.**
- *Why it matters.* Apart from its heading, it is byte-identical to `specs/DS1b-canonical-writers/mid-build-questions.md`.
  It reads "Count: **2** (builder, 2026-11-20)" and holds DS1b's Q1/Q2 (`mid-build-questions.md:7-26`). The packet
  must record this file's count (`spec.md:290`), so a builder would report 2 questions that are not theirs.
- *Proposed answer.* Reset it to the template with "Count: **0**" before the build branch is cut.

**R17 (Low). Label words: a STORED intake whose every record was refused.**
- *Why it matters.* `state = 'STORED'` with `refused_count = record_count` reads as "stored" when nothing was.
  `3A2` will show this word.
- *Proposed answer.* Keep `STORED` as "the intake was processed and its account kept". `3A2`'s copy says how many
  were stored and how many refused, and never "stored" alone. Record this in `rulings.md` as a hand-off. Nothing in
  3A1 says "accepted" (OD-15 is `3A2`'s).

## Implementer pre-flight questions

**P1 (Low). §0: tests run the worktree's own packages.**
- *Evidence.* The shared `.venv` installs `assetops_backend`, `assetops_contracts`, `assetops_simulator`,
  `assetops_field`, `assetops_gateway` and `fixtures` as editable finders. These append to `sys.meta_path`
  (`.venv/.../__editable___assetops_backend_0_0_0_finder.py:75-76`), so `PYTHONPATH` wins. Checked:
  `PYTHONPATH=<a worktree>/backend` loads that worktree's `assetops_backend`. The `fixtures` finder maps to main's
  `host/fixtures`, but `$PWD/host` on `PYTHONPATH` shadows it. `pg_harness._alembic` reads `BACKEND / "alembic.ini"`
  relative to its own file (`backend/tests/pg_harness.py:136-141`), so the template migrates the worktree's 0063.
  The DS1b subprocess sets its own paths from its file (R5).
- *Proposed answer.* As written. Add `fixtures.__file__` to the packet's module-path line.

**P2 (Medium, done). §4.1 `write_intake`: the signature contradicts the re-decision.**
- *Evidence.* It takes ready-made `(intake_row, records, revisions, rejections)` *and* re-decides under the lock
  through a `decide(existing) -> plan` callable, and it returns `None` (`spec.md:211-213`). Precomputed rows go
  stale once the decision changes, and `None` loses the outcome that the lock proof asserts (R4).
- *Proposed answer.* Use `write_intake(tenant_id, source_system, ids, decide: Callable[[Mapping[str,
  ExistingRecord]], Plan], *, dry_run) -> Plan`. `Plan` holds the intake row, the rows to insert and the
  per-record outcomes. The adapter re-reads `existing` under the lock, calls `decide`, inserts unless `dry_run`, and
  returns the plan. The service builds `IntakeResult` from the returned plan only. An envelope or tenant refusal
  uses the same call with an empty `ids`.

**P3 (Medium). §3 rule 3: "its `source_record_id` if it parsed".**
- *Evidence.* A format refusal from `parse_batch` is a bare `CanonicalRefused(code, path)`
  (`records_v1.py:786-790`), so the ID can only come from the raw object. 2a exports no ref validator (`__all__`,
  `contracts/assetops_contracts/canonical/__init__.py:55-61`). A raw ID over 200 characters, or one that is not a
  string, breaks the rejection CHECK (`spec.md:143`) and crashes the intake.
- *Proposed answer.* `source_record_id` is NULL for every 2a format refusal and is the parsed ID for the `INTAKE_*`
  refusals. `record_index` names the row. This also keeps unvalidated text out of the store (R13).

**P4 (Low). §5 guard: what registration takes.**
- *Evidence.* Registering a writer touches several places in `tools/checks/configuration-persistence.ps1`:
  - a `domains` entry (Package and Composition, beside the accounts one at `:208-216`);
  - a `$pgWriters +=` line (`:1017`, kept on its own line for `tools/checks/test_estate_guard.py`);
  - the `$pgWritesSeen` and `$pgDriverSeen` tables (`:1083-1095`);
  - a shape block and its anti-vacuity loop (`:945-956`, `:1506-1521`, `:1851-1856`).

  The INSERT shape `VALUES\s*\([^()]*\)` allows no parentheses, so a `CAST(:x AS numeric)` in VALUES fails the
  guard. The advisory-lock SELECT is a read.
- *Proposed answer.* As listed. Bind plain parameters (psycopg sends `Decimal` as numeric and `UUID` as uuid). Add
  `tools/checks/test_estate_guard.py` to the focused runs.

**P5 (Low). §6 no-DB world.**
- *Evidence.* 2a's 17 batches use the tenants `lakeside-power`, `harvest-cold` and `metro-bus`, and the Sites
  `KOBO-001`, `KISIWA-001`, `MTO-001`, `COLD-THIKA`, `EV-EMB` and `EV-KAS`; one BUDGET_LINE has no Site. DS1b's
  fixture view adds `MTO-001`, `COLD-MWEA`, `COLD-KIRI` and `EV-RUI` under the same slugs. Every 2a batch and every
  DS1b batch is `source-emulated` (DS1b `spec.md:138`).
- *Proposed answer.* Build one in-memory world with the 3 tenants and all 9 Site codes, used by both fixtures.
  Assert every stored revision's `provenance` is `source-emulated` (R12).

**P6 (Medium, done). §6 regression list: downgrades that cross the new head.**
- *Evidence.* `test_3c0a_accounts_postgres.py:418-424` downgrades from head to `0061_reading_upload`. With 0063 as
  head, that path now runs 0063's downgrade first, and does so on a clone that 3A1 rows could dirty if a fixture is
  shared. The UP-1 file is already on the regression list (`spec.md:263`).
- *Proposed answer.* Add `backend/tests/test_3c0a_accounts_postgres.py` to the pooled regression set. 3A1's own
  downgrade test targets the module's `down_revision` (R14).

**P7 (Low). §4.1 `latest_revisions(site_id=None)`: "no filter" or "portfolio only"? And the sort of NULL Sites.**
- *Evidence.* `site_id` is nullable for BUDGET_LINE and CONTRACT_DOCUMENT (`spec.md:90`, `:98`), and `None` is also the
  default meaning "any". The sort key leads with `site_id`, and SQL and Python order NULL differently.
- *Proposed answer.* `None` means no filter. Add a separate `portfolio_only: bool = False`, or leave the
  portfolio-only read to `3A4`. NULL Sites sort first in both stores (`ORDER BY site_id NULLS FIRST`, with Python
  `(site_id is not None, str(site_id or ""))`), with a test comparing the two stores' order.
