# DS3 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Reviewer (Claude), 2026-11-21, after reading `spec.md`, `reviewer-guide.md` and `rulings.md` at `main` `e844e9d18`.
All five touch what the plants and tests can prove; none is about COPY, commercial parity or estimates (ruled).

**R1 (done). Two codes for one condition: same batch ID, other bytes (§2.1, §2.2 step 3, §2.4 step 3, test 6,
guide P-table).** `admit` keeps submit's unlocked conflict check (`ledger_service.py:117-121`), whose `refuse`
callback becomes `BulkLoadRefused(kind="BATCH_ID_CONFLICT")`. §2.2 step 3 raises `BULK_BATCH_EXISTS_DIFFERENT` only
under the slot lock, so on a plain re-load with other bytes `admit` answers first and test 6's "(`BULK_BATCH_EXISTS_DIFFERENT`)"
cannot pass. Expected: the Architect names one code per condition. Either test 6 expects `BATCH_ID_CONFLICT` and
`BULK_BATCH_EXISTS_DIFFERENT` stays only for the lost race (and gets its own test or is dropped from
`BULK_REFUSALS`), or `admit` skips that check for the bulk caller. Done changes with it: test 6's asserted code.

**R2 (done). `admit` does not route every refusal through `refuse` (§2.1, §2.4 step 3, §7 item 2).** `_check_claims`
raises `BatchRefused` directly with no `refuse` call and no row (`ledger_service.py:194-215`): `MODE_MISMATCH`
(gateway LIVE, batch SIMULATED), `GATEWAY_NOT_REGISTERED`, `SOURCE_NOT_AFFILIATED`, `SOURCE_DISABLED`. As written
they leave `BulkEvidenceLoad.load` as a raw `BatchRefused`, so the command's "a `BulkLoadRefused` writes ... exits 2"
does not cover them, and `gateway_principal`'s `disabled_at IS NULL` turns a disabled gateway into the misleading
`BULK_UNKNOWN_GATEWAY`. Expected: `load` catches `BatchRefused` and re-raises `BulkLoadRefused(code=kind)` with the
batch ID, records nothing; test 6 gains a disabled source (or LIVE-gateway) case and asserts unchanged row counts; the
spec says in one line that a disabled gateway is `BULK_UNKNOWN_GATEWAY` on purpose, or reads `registered_scope`
for the real reason.

**R3 (done). "Writes only the four tables" is not what the database does (§2.2, §3, §7 item 4, guide check 6).**
Triggers fire on the bulk statements as on the real path: `enqueue_mini_depth` (deferred constraint trigger on
`accepted_evidence`, `0029_w4_mini_depth.py:305`, reads `ingestion_disposition` at commit) writes mini-depth jobs and
`recompute_job` rows in other domains, and `financial_consequence_dirty_on_evidence` (`0012_...:129`) writes
`financial_consequence_work`. Kobo is MINIGRID, so these fire in the parity run, and §3's job comparison covers
`RECOMPUTE_DOMAIN` only; `Kit.counts` already filters `domain = 'dispatch'` for this reason (`test_s2_...:135-139`).
Expected: §7 item 4 reads "the bulk statements target only the three ledger tables plus `recompute_job` through
`_coalesce_job`; triggers fire as on the real path", and §3 adds: the non-dispatch `recompute_job` rows (by domain and
window coverage) and the `financial_consequence_work` count are equal on both paths, or are stated out of scope with
a reason. Tests 4, 5, 6 count `recompute_job` with the dispatch filter.

**R4 (done). Parity proves only v3 MINIGRID readings (§3, §2.3, test 8, plants P1, P10).** The bulk statement binds
seven v4-only columns (`record_kind`, `event_id`, `correlation_id`, `session_id`, `connector_id`, `actor`, `outcome`)
and `_enqueue_admitted` has a cold branch, yet test 8 and tests 4 to 7 use v3 Kobo envelopes only; a wrong v4 binding
(or a swapped column in those seven) passes every DS3 test, and P10 is caught only by the W2-03 regression, which
never runs the bulk path. The generated world has cold-chain and EV Sites. Expected: add one small v4 slice to test 8
(a COLDCHAIN Site, a few cold-role v4 envelopes and one EV event record, compared by the same equal-rows lists, with
the cold `recompute_job` coverage), or the Architect rules v4 bulk loading out in §8 and refuses a v4 batch in bulk
(`BULK_NOT_V3`) until DS4. Done changes: the parity test's scope.

**R5 (done). Where DS4's walkthrough database will be named (§2.4 `permitted_database`, D-DS3.6, guide P9).** The
permitted set is `*_test` and `<prefix>_audit*`, and `permitted_database` checks the name only: `database_target`
accepts any host, so a `_test` database on another host passes, and the walkthrough database (`assetops_polish_walk...`,
test 1 case) is refused, which is right under RULES §7 but means DS4 must build it under an `_audit` or `_test` name and
copy or serve it. Expected: the spec states that the world command is not the tool that loads the served walkthrough
database, names the `_audit` database DS4 builds into, and either adds a host check (the container's host or
`localhost`/`127.0.0.1`) to `permitted_database` with a test 1 case, or says in one line why the name alone is enough.

## Implementer pre-flight questions

Implementer (Claude), 2026-11-21, checking `spec.md` against `main` `e844e9d18` (read only; no database was
connected, nothing was run against Postgres).

**Pre-flight result (no answer needed).**
- **Converted Kobo gateway is SIMULATED.** `backend/tests/fixtures/s1/kobo-001.yaml:11` `source: mode: SIMULATED`
  -> `foundation_service.py:207` `mode=record.source.mode` on the gateway row -> `postgres_foundation_store.py:458-466`
  inserts it (`gateway.mode`; immutable by the 0005 trigger) -> `binding_alignment.py:108` puts `gateway.mode` into the
  pinned snapshot -> `test_s2_evidence_ledger_postgres.py:77-81` `Kit.principal.mode = doc["gateway"]["mode"]` and
  `:111` `Kit.seal` defaults `source_mode` to it. So `Kit(...).principal.mode == "SIMULATED"`; no Architect seed
  is needed, and the LIVE refusal in test 6 uses `Kit.seal(..., mode="LIVE")`.
- **Devices.** `conversions/kobo-001-bindings.json` holds 10 bindings over 8 devices (`pv-inverter-controller`,
  `pv-irradiance-sensor`, `battery-pcs-controller` x2 signals, `generator-controller` x2 signals, `fuel-level-sensor`,
  `residential-meter`, `clinic-meter`, `mill-meter`); every `valid_from`/`valid_to` is null, so the period is the
  Foundation's `2026-09-29T11:57:49Z` (kobo-001.yaml). 6 and 7 October lie inside it. The five devices of §3 exist;
  the hand counts (10 batches, 960 envelopes) hold at 96 per device per day. (§3's sentence "192 per device except the
  generator status (96 per day as well)" is muddled; the sum is right.) `MAX_BATCH_ENVELOPES` is 256 and
  `MAX_BATCH_BYTES` 1 MiB (`ingestion_batch_v2.py:63-64`), so 96-envelope batches fit.
- **Seams that match `main`:** `_persist` is `postgres_evidence_ledger.py:530-584` with exactly 42 insert columns;
  `open_batch` `:297-360`; `decide_chunk` `:440-523` (the enqueue lines to extract are `:478-488` and `:512-520`); `_lock_slot`
  `:108`; `unnest(CAST(:ids AS uuid[]))` already at `:1200`; `ledger_service.py` is 238 lines with `submit` at `:99`;
  `database_target.is_operator_name` is a case-insensitive `assetops_op` prefix. The guard's extractor
  (`tools/checks/sql_statements.py`) reads module-level `text("...")` constants (I ran it on a scratch copy holding
  three such constants shaped as §2.2 describes: it returns the `INSERT INTO accepted_evidence ... SELECT ... FROM
  unnest(...) ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING` clause whole), and
  `configuration-persistence.ps1:1259-1263, 1291, 1723, 1731, 1747` accept it: targets are ledger tables, the arbiter
  is one of the three allowed, no `VALUES` rule applies to ledger tables. I could not run the full guard on the plant
  (the scratch copy is not a git repository), so "no guard change" is checked by reading, and stays a gate at the
  first commit (run `check-architecture.ps1` before any test).

**I1 (done). The commercial step cannot read a tenant directory that holds `telemetry/` (§2.5, D-DS3.2).**
`load_emulated_exports._files` iterates the whole directory and raises `EXPORT_FILE_UNKNOWN` (exit 2) for anything
that is not a regular file or a name `<slug>.<key>.csv` / `<slug>.<source_type>.json` / `unwritten.json`
(`load_emulated_exports.py:77-98`; a subdirectory fails `not path.is_file()` at `:87`). §2.5's layout (the tenant's
canonical files and a `telemetry/` folder in one directory, `--dir d`) would stop every tenant at the commercial step.
Also, its exit codes 2 (refused before submission) and 3 (a submission refused) collide in meaning with this
command's own 2 (bulk refusal) and 3 (database error). Expected: the world layout puts the two in sibling folders
(`<world>/<tenant>/commercial/` for `--dir`, `<world>/<tenant>/telemetry/`), the commercial step runs when
`commercial/` exists, and the spec says commercial exit codes pass through unchanged and that the command's own codes
are reported on stderr by prefix. Test 2's stub then asserts the `--dir` it receives.

**I2 (done). Three extra clones are outside what `pg_harness` provides and cleans (§0 Databases, §3 Seed, test 8).**
`pg_harness.database_name(stem, run, tag)` is public, but creating a database from a template (`_create`, `_admin`,
`_quote`, `_stem`; `pg_harness.py:184-205, 250`) is private, and `cleanup()` serially drops only the worker and the
template (`:398-418`); extra tags are dropped only by `cleanup_run` (xdist controller) or by `sweep_orphans` at the
next run's template build (`:288`). So "the harness drops them" is false in a serial run; test 8's `finally` is the
only drop. Also every module-level `URL`, `Kit`, `converted_enabled(store, engine)` and `ingestion()` read the one
routed `ASSETOPS_TEST_DATABASE_URL`, so seeding `ds3seed` and loading `ds3real` and `ds3bulk` needs per-database
stores, and `CREATE DATABASE ... TEMPLATE ds3seed` needs zero sessions on the seed (dispose first). §0's file list
edits no `pg_harness.py`. Expected: add `pg_harness.py` (one public `clone_database(tag, template)` and a drop that also
registers the name for `cleanup`) and `test_pg_harness.py` to the edited files, or the Architect rules the tests
may call the private helpers; and the tests take URLs from a small fixture rather than the module `URL`. Done changes:
the file list and the "harness drops them" sentence.

**I3 (done). Which `IntegrityError`s are collisions (§2.2 step 6, test 6, P5).** The spec maps "any `IntegrityError` on
any unique index" to `BULK_MESSAGE_COLLISION`. `_persist` treats only `_COLLISION_INDEXES` as typed and re-raises
every other violation (`postgres_evidence_ledger.py:575-578`); a foreign-key or CHECK failure (for instance
`ingestion_batch_counts`, whose `processed = accepted + ...` and `COMPLETED <=> completed_at` constraints the one-row
`COMPLETED` insert must satisfy at once) is a build defect, not a collision. Expected: `_constraint(error) in
_COLLISION_INDEXES` becomes `BULK_MESSAGE_COLLISION`, anything else propagates unchanged and is asserted by a test of
a deliberately wrong count (the batch row `processed_count` off by one fails the CHECK and rolls back).

**I4 (done). Where the unit-3 script lives and how it is routed (§5, §0 Files, §6 unit 3).** §5 is "one script, not a
test", on `<stem>_pt<run>_ds3bench_test`, but no file is listed, `pg_harness.route()` runs only under pytest's
`conftest`, and the guard's allowed databases are named by RULES §7. Expected: the script is a `slow`-marked pytest
module not committed (or a committed `backend/tests/ds3_bench.py` added to §0 Files) that gets its URL the same way
as I2, writes its numbers to the packet only, and drops `ds3bench` in `finally`; the packet records the slot label.

**I5 (not done-changing). Test 6 fixtures the helpers do not give (§4 test 6).** `Kit.seal` cannot set the gateway ID
(unknown-gateway case) and `Kit.envelope` fixes the source from the binding; I will call `seal_batch_v2` directly for
those two cases, and use `test_s405_publication_postgres.py`'s publication helper for `BULK_PUBLISHED_BATCH`. Expected
answer: yes, tests may use `seal_batch_v2` and that helper; no spec change.

## Architect answers

Architect (Claude), 2026-11-21: every question answered once in `rulings.md` "Handshake answers (round 1)":
R1, R2 D-DS3.9; R3 D-DS3.10; R4 D-DS3.11; R5 D-DS3.12; I1 D-DS3.13; I2 D-DS3.14; I3 D-DS3.15; I4 D-DS3.16; I5
D-DS3.17; the guard gate D-DS3.18; size D-DS3.19 (4.0 units). Folded into `spec.md` rev 2 and `reviewer-guide.md`
rev 2. No question is open; the handshake is closed.
