# DS3 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-DS3.1 to D-DS3.8 are applied by `spec.md` rev 1. D-DS3.1, D-DS3.2 and D-DS3.8 change what the owner-accepted
strategy text says, so each is logged for the owner in `specs/OWNER-AWAY/decisions-2026-11-21.md` (rows 10 to 12).

## D-DS3.1 Set-based `INSERT ... SELECT FROM unnest` inside the ledger's one writer, not `COPY` into staging

- **Ruling.** The bulk path is a method of `PostgresEvidenceLedger`, writing each table with one literal set-based
  statement per batch and only the existing `DO NOTHING` arbiters. No `COPY`, no staging table, no second writer.
- **Why.** `tools/checks/configuration-persistence.ps1` holds three rules the strategy's wording would break: "No
  product writer runs MERGE or COPY" (`:1260-1263`), only the ledger writer writes ledger tables (`:1723`), and the
  ledger runs no DDL (`:1747`, so no staging table). Changing them is a guard change the owner approves (OWNER-AWAY
  row 5), and the delegation does not widen authorisations. Putting the loader under `tools/`, outside the guard's
  scan, would be working around a safety check (`.ai/RULES.md` §7). The property the strategy wanted, "constraints,
  append-only triggers and change triggers still fire, once per statement instead of once per row", holds for a
  set-based `INSERT ... SELECT` exactly as for `INSERT ... SELECT FROM staging`; `unnest` of array parameters is
  already used in this adapter (`:1200`). Unit 3 measures it; if DS4 finds it misses the build target, the COPY writer
  block goes to the owner then, with numbers.
- **Reverse.** The owner approves a COPY writer block; only `_BULK_EVIDENCE_SQL` changes.

## D-DS3.2 Commercial records keep one path: `3A2`'s intake, through the existing loader

- **Ruling.** The world command calls `load_emulated_exports.main` per tenant for the DS1b canonical files. DS3 adds no
  commercial write and no commercial parity half.
- **Why.** D-3A3.1 (merged): "No emulator, seed, bootstrap or bulk loader calls `CommercialRecords.ingest` ... This
  binds `DS3` too". A second commercial path would store raw references where the intake stores pseudonyms and turn
  one record sent both ways into `INTAKE_VERSION_CONFLICT`. Volumes are small (D-3A1 Q2; the strategy measured 8,100
  rows), so the intake costs seconds. With one path, a parity test on it would compare a path with itself.

## D-DS3.3 Parity is row equality on the four input tables; recompute jobs by coverage

- **Ruling.** Rows are equal column by column, generated IDs and receipt and decision instants apart. Recompute jobs
  are compared by what the pipeline needs: every accepted reading inside a PENDING job window, the bulk path with no
  more jobs than the real path.
- **Why.** The real path coalesces jobs per 64-ordinal chunk (`decide_chunk`, `_coalesce_job`), so it may hold several
  touching windows where the bulk path, deciding a batch at once, holds one. Both feed the same day windows to the
  assessment; demanding equal job rows would force the bulk path to imitate chunking, which is not a property of the
  evidence.

## D-DS3.4 A batch already published for a registered run is refused in bulk

- **Ruling.** `BULK_PUBLISHED_BATCH` when an `evidence_publication` row exists for the slot.
- **Why.** The link between a registered run's publication and its batch is made only "in the admission transaction
  that inserts the batch; never afterwards" (`open_batch`); the bulk path does not write provenance (the guard keeps
  `batch_publication_link` to `open_batch`'s literal INSERT). Registered runs go through the real path.

## D-DS3.5 The bulk path admits clean batches only

- **Ruling.** Any `Rejected` ordinal, any message, event or session collision refuses the whole batch
  (`BULK_REJECTED_ORDINAL`, `BULK_MESSAGE_COLLISION`) in one transaction.
- **Why.** Duplicates, conflicts and rejections are typed by the real path's ordered reread (`_collision`), which a
  set-based statement cannot reproduce without copying it. The generated world is clean by construction; the disorder
  tests (DUP-1 to CLOCK-1) are planted through the real path, where they are tested.

## D-DS3.6 Label and database refusals

- **Ruling.** Only `source_mode` SIMULATED batches; only databases named `*_test` or `<prefix>_audit*` and never an
  operator database (`database_target`, `is_operator_name`), checked before any connection.
- **Why.** Strategy §4 and §8: the bulk loader "refuses any reading that is not SIMULATED"; `.ai/RULES.md` §7 names the
  permitted databases. The command is a trusted tool with no gateway credential (residual risk `R-TRUST`), so the two
  refusals are what keep it off live and operator data.

## D-DS3.7 No user-facing text

- **Ruling.** The command's stderr lines are developer diagnostics (code, batch, detail); nothing is served.
  D-SC1.28 does not engage.

## D-DS3.8 Lines not received are not estimated by DS3

- **Ruling.** DS3 loads what DS1b wrote. A line DS1b lists `ESTIMATED_NOT_RECEIVED` (Kisiwa O&M, Thika maintenance,
  Kasarani maintenance) has no record and no estimate: the structure read shows it as missing, "Not available yet"
  with the record that would fill it. D-3A1.7's "declarations beside the store" are queued as their own unit (a
  declared estimate with its declarer), not built here.
- **Why.** An estimate is not a record (D-DS1B.7); no store for declared estimates exists on `main`, and building one is
  a new schema outside DS3's three units. The owner's rule "a cost line not sent reads 'Not available yet', or
  *Estimated* where the operator states an estimate, never 0" (build plan §0.4) holds: no estimate has been stated
  through any path, so "Not available yet" is the honest reading.
- **Reverse.** Queue the declared-estimate unit ahead of WK; DS3 needs no change.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, answering `handshake.md` R1-R5 and I1-I5, each checked against `main` `3bdf3c81d`.
Folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. D-DS3.11 narrows what DS4 can bulk-load, so it is logged
for the owner (`specs/OWNER-AWAY/decisions-2026-11-21.md` row 13). Nothing here widens an authorisation; no guard
changes. The rev 1 index lines for D-DS3.1, .2 and .8 cited rows 9 to 11; the rows are 10 to 12 (corrected).

## D-DS3.9 One refusal order, one code per condition; the real path's claim refusals pass through (R1, R2)

- **Ruling.** The bulk path checks in one fixed order (spec §2.4 table) and names each condition once.
  "Same batch ID, other bytes" is `BATCH_ID_CONFLICT` wherever it is found: from `admit`'s unlocked check (the
  normal case, test 6) and from `bulk_admit`'s recheck under the slot lock (the lost race, tested by calling
  `bulk_admit` directly). `BULK_BATCH_EXISTS_DIFFERENT` is dropped. `_check_claims` raises `BatchRefused` without
  calling `refuse` (`ledger_service.py:194-215`); `BulkEvidenceLoad.load` catches `BatchRefused` around `admit` and
  raises `BulkLoadRefused(code=error.kind, external_batch_id=batch.batch_id, detail=error.detail)`, recording
  nothing. `gateway_principal` drops `disabled_at IS NULL`: a disabled gateway gets its principal and
  `registered_scope` names the real reason, `GATEWAY_DISABLED` (`postgres_evidence_ledger.py:179-199`).
  `BULK_UNKNOWN_GATEWAY` then means only "no such gateway at that Site". An `existing` COMPLETED batch with the same
  digest is `already_loaded` without deciding; `existing` IN_PROGRESS is `BULK_BATCH_IN_PROGRESS`.
- **Why.** Two codes for one condition make a test depend on timing and a reader guess which check spoke. Reusing
  the real path's code keeps one vocabulary for one fact. Reading `registered_scope` gives the true cause for free,
  where a filter in `gateway_principal` would hide it.

## D-DS3.10 The bulk statements target three ledger tables and `recompute_job`; triggers fire as on the real path, and parity counts every table (R3)

- **Ruling.** Spec §7 item 4 is restated: the bulk statements target only `ingestion_batch`, `accepted_evidence`,
  `ingestion_disposition`, and `recompute_job` through `_coalesce_job`; the database triggers fire on them exactly
  as on the real path. Those triggers on `main` are: `enqueue_mini_depth` (deferred, `0048`; `recompute_job` in the
  mini domains), `enqueue_ev_assessment` (deferred, `0025`; EV `recompute_job`), `ev_consequence_dirty_accepted`
  (`0026`; EV consequence work), `financial_consequence_dirty_on_evidence` (`0012:129`; `financial_consequence_work`)
  and the statement-level `*_cic_ins` change-log triggers (`0047`; `chain_input_change`). Parity covers them as a
  class, not one by one: test 8 takes a **census** of every base table of the schema (row count after the load
  minus the seed's) on both databases. Every table's delta is equal on both paths, except two whose rows are, by
  design, per statement or per chunk: `recompute_job`, compared per domain (dispatch and cold by D-DS3.3's coverage
  rule; every other domain, written per Site-local hour or per window by a trigger, by the exact set of
  `(domain, window_start, window_end, status)`), and `chain_input_change`, compared by its set of distinct
  `(tenant_id, site_id, table_name)` with the bulk count at most the real one. A table with a non-zero delta that
  the test does not name fails with its name. The parity seed's binding sets are relabelled `minigrid-roles-4`
  (test-only, as `test_w200_source_events_postgres.v4_roles4` does) so the mini-depth trigger writes jobs on both
  paths and the comparison is not empty. `financial_consequence_work` and the EV consequence work need Finding or
  assessment revisions, which the seed has none of: their deltas are 0 on both paths, asserted by the census; the
  limit is stated, not hidden. Tests 4, 5 and 6 count `recompute_job` with `domain = 'dispatch'`, as `Kit.counts`
  does.
- **Why.** Listing today's triggers would go stale with the next migration; the census catches a new one the day
  it lands (W6). Change-log and chunk-coalesced rows legitimately differ in count (one per statement or chunk);
  what the readers need, the scopes invalidated and the windows covered, is compared exactly.
- **Reverse.** Name a further table in the census's per-table rules when a trigger with per-statement rows is added.

## D-DS3.11 Bulk loading is proved for MINIGRID Sites, v3 and v4; other Site types are refused until their parity slice exists (R4)

- **Ruling.** Test 8 adds a v4 slice at the parity Site: one batch of test_w200's v4 shapes (a `START_RESULT`
  event, an `EV_SESSION_START`, a chamber-probe point and an EV interval delta, through `patched_v4`), compared by
  the same equal-rows lists; the seven v4-only columns are therefore compared. The cold enqueue branch needs a
  `COLDCHAIN` Site, which no ledger-only fixture on `main` provides (W2-03's cold Sites come through the gateway
  chain and registered publications, which D-DS3.4 refuses in bulk). So `bulk_admit` refuses a batch at a Site
  whose `_site_type_on` is not `MINIGRID`: `BULK_SITE_TYPE_UNPROVEN`, before any write. The cold branch stays in the
  shared `_enqueue_admitted` (W2-03 regression covers it through `decide_chunk`). DS4 lifts the refusal per Site
  type by adding that type's parity slice (a seed, a slice, the census), never by deleting the check.
- **Why.** The bulk path should load only what parity proves (owner, 2026-11-13: the walkthrough runs only on a
  clean, good database). Building a cold and an EV ledger seed now adds a fixture DS4 must build anyway with the
  world's real Sites. Until then cold and EV telemetry reach the walkthrough through the real path, slower, not
  wrong. Owner-level because it shapes DS4's build time: OWNER-AWAY row 13.
- **Reverse.** Add the COLDCHAIN and EV_CHARGING parity slices in DS3 (about +0.75 unit) and drop the refusal.

## D-DS3.12 Name and place: the permitted database is also on the container's host and port; the world command never loads the served walkthrough database (R5)

- **Ruling.** `permitted_database(url, environ=None)` also requires `target.host` in `{"127.0.0.1", "localhost"}` and
  `target.port == int(env.get("ASSETOPS_PG_PORT", "55432"))` (the port `docker-compose.yml:21` publishes for
  `assetopsv1-postgres-1`); a missing port is false. The command is not the tool that loads the served walkthrough
  database: DS4 builds into `assetops_ds4_audit<MMDD>` (permitted by name, host and port). Whether the walkthrough
  serve may point at a built `_audit` database, or a copy is made into its name, is DS4's question to the owner; it
  is **held**, not decided here.
- **Why.** RULES §7 names the databases *in `assetopsv1-postgres-1`*; the name alone does not say which server. The
  check costs one line and closes the gap. Writing to the walkthrough database outside its own serve is forbidden
  (RULES §7), so the build target must be an `_audit` name.

## D-DS3.13 World layout: `commercial/` and `telemetry/` as sibling folders; the command's exit codes are its own (I1)

- **Ruling.** `<world>/<tenant>/commercial/` (passed as `--dir` to `load_emulated_exports.main`) and
  `<world>/<tenant>/telemetry/` (`*.batch.json`); each step runs when its folder exists; anything else in a tenant
  directory is `WORLD_LAYOUT_UNKNOWN` (exit 2), checked for every tenant before any connection. Exit codes: 0 done;
  2 a refusal of this command (`NO_DATABASE`, `BULK_DATABASE_NOT_PERMITTED`, `WORLD_LAYOUT_UNKNOWN`, any
  `BulkLoadRefused`); 3 a database error; **4 the commercial step failed**, with stderr
  `COMMERCIAL_EXIT <tenant> <loader exit>` after the loader's own lines; telemetry is not loaded for that tenant or
  later ones.
- **Why.** `_files` refuses a subdirectory (`load_emulated_exports.py:87`), so one folder cannot hold both. Passing
  the loader's 2 and 3 through would make 2 and 3 mean two things; one code for "the commercial step failed" plus
  its exit on stderr keeps both facts.

## D-DS3.14 `pg_harness` gets a public clone helper and drops what it clones (I2)

- **Ruling.** `pg_harness.py` gains `clone_database(tag, template_url=None) -> str` (a `*_test` name from
  `database_name(stem, run, tag)`, created from the run template or from `template_url`'s database, registered in
  `_state["extra"]`; asserts zero sessions on the source first, naming the count) and `drop_database(url)` (DROP
  ... WITH (FORCE), unregisters). `cleanup()` also drops every registered extra. `test_pg_harness.py` gains the
  create, register, drop and cleanup cases. DS3's Postgres tests take URLs only from module fixtures built on
  `clone_database`, never the module `URL` (used only for the skip), and build their own engine, store, ledger and
  service per URL; the seed's engines are disposed before cloning from it.
- **Why.** Tests calling private helpers would couple to internals; a public helper with registered cleanup makes
  "the harness drops them" true serially as well as under xdist (`cleanup_run` already drops by the owned pattern).

## D-DS3.15 Only listed unique indexes are collisions; any other integrity failure propagates (I3)

- **Ruling.** In `bulk_admit`, fewer ids returned than decisions, or `_constraint(error) in _COLLISION_INDEXES`, is
  `BULK_MESSAGE_COLLISION`; any other `IntegrityError` (a foreign key, a CHECK) propagates unchanged after the
  rollback (the command's exit 3). Tested by calling `bulk_admit` with one decision whose
  `binding.binding_revision_id` is a random UUID (`accepted_evidence_binding_fk`): an `IntegrityError`, not a
  `BulkAdmissionRefused`, and every table's row count unchanged.
- **Why.** The same rule as `_persist` (`postgres_evidence_ledger.py:575-578`): a build defect must not read as clean
  data's collision. A foreign-key case is reachable without a plant; a miscounted batch row is not.

## D-DS3.16 The measurement is a committed, opt-in test module (I4)

- **Ruling.** `backend/tests/test_ds3_bench_postgres.py`, marked `slow` and skipped unless `ASSETOPS_DS3_BENCH=1`;
  run through `tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- <file>` with `-s`. URLs
  from `clone_database` (tags `ds3bseed`, `ds3breal`, `ds3bbulk`), dropped in `finally`; numbers printed as one JSON
  line, copied into the packet with the slot label. It asserts nothing about time.
- **Why.** The harness routes only under pytest, and a committed module lets DS4 re-run the same measurement.

## D-DS3.17 Test 6 may seal with `seal_batch_v2` and use S4-05's publication helper (I5)

- **Ruling.** Yes, for the unknown-gateway and foreign-source cases, and `test_s405_publication_postgres.py`'s
  publication helper for `BULK_PUBLISHED_BATCH`. No spec change beyond naming them.

## D-DS3.18 The persistence guard is a first-commit gate, run for real

- **Ruling.** The first commit holds the three `_BULK_*` constants. Before any Postgres test, the builder runs
  `pwsh -NoProfile -File tools/check-architecture.ps1` in the branch worktree and records its exit and the
  Configuration-persistence line in the packet. A non-zero exit stops the build and goes to the Architect; any
  guard change is held for the owner (OWNER-AWAY row 5), never made in DS3.
- **Why.** The pre-flight read the guard on a scratch copy outside git; only the real run on the branch proves
  "no guard change".

## D-DS3.19 Size 4.0 units, no split

- **Ruling.** Unit 1 2.0 (extractions, `bulk_admit`, the service, the harness helper, tests 3 to 7), unit 2 1.5 (the
  command, tests 1 and 2, parity with census and v4 slice), unit 3 0.5 (measurement, check-all, packet). Under the
  6-unit split rule.

## Mid-build answers (round 1; spec rev 3)

Architect (Claude), 2026-11-21, on the owner's delegation. Answers `mid-build-questions.md` Q1 to Q3. No owner approval
is needed: Q1 trims a fixture to what the real path accepts, Q2 states a parity rule, Q3 narrows a permission.

## D-DS3.20 The v4 slice is the three shapes the real path accepts; a refused `v4.delta` is a refusal case, not a slice member (Q1)

- **Ruling.** Option (a). `V = kit.seal([v4.event(100001, "START_RESULT", "evt-1", "FAILED"), v4.start(100002,
  "start-1"), v4.point(100003)])`: three ordinals, all accepted on the real path (asserted). The slice exists to prove
  the seven v4-only columns; those are all carried by these three. No EV connector channel is bound: a connector-meter
  energy channel belongs to EV Sites, and bulk loading is MINIGRID-only (D-DS3.11). "Both paths refuse identically"
  is not available as a parity assertion: the real path stores a rejection and accepts the rest of the batch, the bulk
  path refuses the whole batch and writes nothing (D-DS3.5), so a `v4.delta` batch is a refusal case in test 6: a batch
  `[v4.delta(...)]` on the MINIGRID Site raises `BulkLoadRefused(BULK_REJECTED_ORDINAL)` with the ordinal and
  `MAPPING_INCOMPATIBLE` in its detail, and the ledger holds no row for it (counts unchanged). Test 6 does not call
  the real path for this case.
- **The xfail goes.** `..._with_the_v4_slice` loses its `xfail`; its body becomes the single parity test's v4 half
  (or stays a second test; builder's choice) and must pass. P15 is shown failing as soon as the slice is in.
- **Why.** The spec's own rule ("if not, a mid-build question, not a change of shapes") sent this here; the builder
  was right to ask. A permanent xfail would stand in for this decision, and the dropped shape adds no column.

## D-DS3.21 `event_outbox` parity is the event cover, not the row count (Q2)

- **Ruling.** `event_outbox` joins `chain_input_change` as the census's second per-statement table. Over the rows new
  since the baseline, grouped by `(tenant_id, site_id, source, type)`, on both paths: (1) the set of groups equal;
  (2) bulk count at most real; (3) the subject cover equal per group, where the cover is computed by the test from
  the JSON by its own query: the union of every `roles`, `asset_ids`, `analytic_ids` array; the set of every `domain`,
  `status`, `key` scalar; the least start and greatest end over `span`, `window`, `valid` and each pair of `windows`.
  The idempotency key and the payload are not compared (they hold per-statement min, max and count by design,
  `0044_chain_events.py:2-3, 36`). A non-equal cover fails the test with the group's name and both covers; it is
  never loosened to pass: it goes to the Architect as a High finding (a consumer would then miss a day or a measure).
  The recompute-job and `chain_input_change` rules are unchanged. `test_the_census_names_every_table_the_load_writes`
  loses its `xfail` and now passes with this rule.
- **Do downstream consumers see a difference that matters?** No, if (3) holds. The consumers (`chain/events.py`
  `resolve`, read through `postgres_event_store.py`) turn an event into (day, measure) pairs from `subject` only
  (roles, asset ids, domain, span, windows, valid) and select by `(site, type)`; none reads the key or a row count,
  and the processed-record is per event id. One event with the union span resolves to the same (day, measure) set as
  many events whose spans it covers, provided one batch's span has no gap days; a batch spanning a gap would make
  bulk resolve a day the real path did not. A cover is the least and greatest, so the test cannot see a gap; the
  Kobo days have none, and the loader's input batches are one device-day (the world generator's shape, DS1). The
  limit is stated in the packet; a world batch spanning more than one day is DS4's to check against this rule.
- **Why.** Equal row counts cannot hold by construction (D-DS3.10's reason). What a consumer takes from the table
  is the set of Sites, types and subjects, so that is what parity compares.

## D-DS3.22 `permitted_database` refuses the walkthrough database, by a narrower allow and an explicit deny (Q3)

- **Ruling.** Two layers, both in `permitted_database` (spec §2.4); the first is the control, the second a tripwire
  that keeps the property if the allow pattern is ever widened. A name is permitted only if, with the host and port
  rule (D-DS3.12) and `not is_operator_name`, it (i) is not denied: `re.search(r"walk|serve", name)` refuses; and (ii)
  matches one of: `re.fullmatch(r"[a-z0-9_]+_audit[a-z0-9_]*", name)`, or `re.fullmatch(r"[a-z0-9_]+_pt[0-9a-f]+_[a-z0-9]+_test",
  name)` (a name `pg_harness.database_name` makes: DS3's own clones). A bare `*_test` name is no longer permitted, so
  `assetops_test` (the shared run template) and `assetops_polish_walk1113_test` are both refused, and so is any other
  database in the container. The command's own target is `assetops_ds4_audit<MMDD>` (DS4); tests use clones.
- **Test 1 (changed).** `assetops_test` false; `assetops_polish_walk1113_test` false (the live walkthrough database,
  `.ai/NOW.md` §3); `assetops_polish_walk1113` false; `assetops_walk_audit1121` false (the deny layer); `assetops_other_test` false;
  `assetops_pt1a_ds3bulk_test` true; `assetops_ds3_audit1121` true; `assetops_ds4_audit1125` true; the existing host,
  port, operator and unclear-target cases unchanged. Builder updates any other test that relied on a bare
  `_test` name being permitted.
- **Plants.** P24: the allow pattern widened back to "ends `_test`": test 1 fails on `assetops_polish_walk1113_test`.
  P25: the deny removed: test 1 fails on `assetops_walk_audit1121`.
- **Why.** The standing rule (RULES §7, and the coordinator's instruction) is that the walkthrough worktree and its
  database are not touched without the coordinator; a name rule that admits it is a safety hole, and "writes only to
  databases it owns or is named for" (a clone pattern or `_audit`) is the narrow form of the allow. This narrows
  what the command may do; it widens nothing, and the held DS4 question (D-DS3.12) is unchanged.

## D-DS3.23 The 11 pre-existing failures do not block DS3

- **Ruling.** `test_s4_evidence_decided_at_postgres` (10) and `test_s2_rejection_placement` (1) fail identically on
  `main` at `8eff70625` (`base-main.log`) and are outside DS3's files (`git diff main...HEAD`): they are not a DS3
  finding and do not hold review or merge. The coordinator routes them to their own task; the reviewer counts them as
  "11 failed, same as main" and checks no new failure beyond them.
- **Why.** Blocking a slice on failures it did not cause stops progress for no safety gain, and the identical
  failing set on `main` is the evidence that DS3 did not introduce them.
