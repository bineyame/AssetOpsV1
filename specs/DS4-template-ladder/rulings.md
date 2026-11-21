# DS4 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-DS4.1 to D-DS4.15 are applied by `spec.md` rev 1. D-DS4.1, D-DS4.2 and D-DS4.12 change what owner-accepted text
says or what a queue trigger means, so each is logged for the owner in `specs/OWNER-AWAY/decisions-2026-11-21.md`
(rows 33 to 35); D-DS4.13 is held there (row 36). A previous Architect deferred DS4 until the telemetry question was
answered; this file answers it first.

## D-DS4.1 The world's telemetry comes only from the world generator's telemetry writer; this fortnight there is none

- **Ruling.** World telemetry is Batch V2 files under `<world>/<tenant>/telemetry/`, written by the world generator
  from the seed manifest (simulator windows and day shapes reconciled to the manifest's day totals: `DS2`), sealed
  with the world Site's own binding set, SIMULATED, loaded by `load_world_inputs` under DS3's refusals and D-DS4.9's
  gap rule. Never the walkthrough build's Lab runs, a test fixture, or a copy of any database. Its precondition is a
  gateway, sources and a published binding set at each world Site, declared through the product's import and
  conversion path; no unit owns that, so one is queued (spec §9 Q2, about 1.5 units, before DS2's writer). Until both
  land, the definition and every build manifest say `"telemetry": {"source": "none", "reason": "DS2_NOT_BUILT"}`, and
  every telemetry-fed leaf reads "Not available yet" naming its record (the product's existing `NOT_CONNECTED` /
  `NOT_RECEIVED` states). The 13 Nov walkthrough database keeps today's telemetry stories meanwhile.
- **Why (the survey, spec §2).** (1) The walkthrough build's telemetry (`demo_combined.py` and its children) is the
  simulator through a real gateway, but at Sites that are not the world's (`COLD-LAB-001`, `EV-LAB-001`, a Kobo in
  tenant `demo`), with the walkthrough story's totals rather than the manifest's: Kobo's litres from it would
  contradict the October fuel invoices (1,180 L) and the independent model (330 L candidate, 120 L unexplained), which
  the owner's honesty rule and release test "Identities" forbid; and its runs are registered publications, refused in
  bulk (D-DS3.4), so it would keep today's row-by-row cost. (2) The harness's Kobo days are hand-written flat rows: in
  the world they would show invented operation. (3) ON1's Sites have no gateway, sources or binding set, so no
  reading can be accepted at them by either path (`gateway_principal` is None): this is decisive, whatever the source.
  (4) The pipeline drain consumes telemetry and produces none. (5) The walkthrough database's rows are outputs, and
  RULES §7 forbids touching it. The re-cut already moved DS2 out ("shapes add realism, not money", build plan §0.3),
  and the fortnight's money gate needs no telemetry (DDR: Kobo −562.00 as +38.00 and −600.00). Owner-level because the
  world walkthrough will show Kobo's fuel line unsplit (−600.00, its candidate −412.50 and unexplained −150.00 "Not
  available yet") where the pack's figures show them split: row 33, **owner to weigh in**.
- **Reverse.** Queue the Site-configuration unit and DS2's telemetry writer earlier; the ladder needs no change (the
  definition's `telemetry.source` widens and L2 gains its drain steps, D-DS4.11).

## D-DS4.2 Cold-chain and EV parity slices move to the unit that first writes their telemetry

- **Ruling.** D-DS3.11's "until DS4 adds that type's parity slice" becomes "until the unit that first writes
  cold-chain or EV telemetry into a world adds it" (a seed, a slice, the census, as D-DS3.11 says). DS4 adds none;
  `BULK_SITE_TYPE_UNPROVEN` stays.
- **Why.** Bulk loads only what parity proves; with no world telemetry (D-DS4.1) a cold or EV slice would prove a path
  nothing uses this fortnight, on a seed DS4 would have to invent (no ledger-only COLDCHAIN fixture exists on `main`,
  D-DS3.11's own reason). Row 34.
- **Reverse.** Add the two slices in DS4 unit 2 (about +0.75 unit) and drop the refusal for those types.

## D-DS4.3 The ladder is a tool (`tools/world.py`) that drives the product's own commands; no migration, no writer, no guard change

- **Ruling.** `tools/world.py` orchestrates subprocesses of the product's commands and issues only database-level DDL;
  build manifests are JSON files outside the repository (`<state>/manifests/`). It writes no product table.
- **Why.** A template is a database; its record belongs with the tool that made it, and a table would need a
  migration and a writer block in `configuration-persistence.ps1` (an owner approval, OWNER-AWAY row 5) for tooling
  state. Driving the product's commands means every world row passed the same intake, onboarding and snapshot rules
  an operator's does (the owner's "clean, good" rule), and DS3's review note is met: the world goes through
  `load_world_inputs`, which checks `permitted_database`. `tools/demo_combined.py` is the precedent for a tool that
  creates and drops its own databases.
- **Reverse.** Move the manifest into a table under its own writer block, with the owner's approval.

## D-DS4.4 Names, connections and freezing

- **Ruling.** Rungs `<prefix>_audit_l0|l1|l2_<key12>`, clones `<prefix>_audit_c_<label>`, prefix
  `assetops_[a-z0-9]{1,24}` (default `assetops_world`); every name passes `permitted_database` (so the walkthrough and
  serve names are refused, D-DS3.22) before any statement. DDL runs on an AUTOCOMMIT connection to the server's
  `postgres` maintenance database and is limited to `CREATE DATABASE` (optionally from a template, `STRATEGY
  FILE_COPY`), `ALTER DATABASE ... WITH ALLOW_CONNECTIONS false`, `DROP DATABASE` (never `FORCE`) and reads of
  `pg_database` and `pg_stat_activity`. A rung is frozen (`ALLOW_CONNECTIONS false`) before its manifest is written;
  the tool never connects to a frozen template. Steps run in a built environment (spec §3.5), never the parent's.
- **Why.** The strategy proposed `assetops_<world>_l1_<digest8>_test`, but D-DS3.22 permits a `_test` name only in the
  harness clone form, and `load_world_inputs` refuses anything else; `_audit` names are permitted by RULES §7 and by
  the loader. `postgres` holds no AssetOps data (`demo_combined.py` uses `assetops` the same way). A frozen template
  cannot be dirtied between clones (the harness's rule, `pg_harness.py:268`). `FORCE` would end a walkthrough's
  session; refusing is the safe default. A built environment keeps a stray `PGDATABASE` or a real-data switch from
  following a step (RC4-F1).
- **Reverse.** Allow `FORCE` on bench names only, if stuck sessions ever block the bench.

## D-DS4.5 Keys, the clean tree and staleness

- **Ruling.** Key parts as spec §3.2 (L0: the migrations tree; L1: L0's key, the definition's bytes, the inputs
  digest, five code trees; L2: L1's key, the step list), hashed as canonical JSON. The build refuses a dirty tree over
  every keyed path, the manifest, the derived values and the onboarding files. A rung is reused only at its exact key;
  `clone`, `reset` and `check` use only the current L2 and otherwise name the first changed part.
- **Why.** "Rebuilt only when its key changes ... a stale template is refused, never used" (strategy §4). The intake,
  onboarding and snapshot code shape the stored rows, so the code is in L1's key, not only L2's as the strategy
  wrote; git tree ids are exact and free on a clean tree, which the strategy already requires for the walkthrough.
  Naming the part tells the coordinator what to rebuild.
- **Reverse.** Narrow `code` to the packages whose files the steps import, if rebuilds become a cost.

## D-DS4.6 The world this fortnight: Lakeside, October, from the emulated exports

- **Ruling.** The definition (`backend/conversions/world-layer4-v1.json`) builds each tenant with an onboarding file
  (Lakeside only) from `world_history.py exports` (October, native CSVs) through `onboard_operator` and
  `load_world_inputs`; L2 runs `build_structure_snapshot build` (by `service:world-build`) and `observe_structure run`
  per tenant and month. Harvest Cold and Metro Bus are listed `NO_ONBOARDING_FILE`. History months and DS1b canonical
  files are not loaded.
- **Why.** RC5 (owner default): the first deep-dive is mini-grid only; ON1 wrote one onboarding file; the exports
  writer refuses other verticals (`NOT_ON_PATH_VERTICAL`). The runbook says a rehearsal tenant takes the emulated
  files only, and a canonical file of a source type already held from a native export is `EXPORT_PATH_SWITCHED`.
  The snapshot build is a computation, so a service names it honestly; people's records come from onboarding. No
  screen reads July to September from the stores this fortnight.
- **Reverse.** Add a tenant to the definition when its onboarding file exists (the key changes, L1 rebuilds).

## D-DS4.7 The real-path slice runs inside `world check`, at the harness Site, never in the world

- **Ruling.** `world check` C5 runs `backend/tests/test_ds3_parity_postgres.py` (two Kobo days and the v4 batch through
  central ingestion and the bulk path, compared row by row and by census). The world holds no slice rows. Commercial
  records have one path (D-DS3.2), so the strategy's billing and settlement half is the world's own load.
- **Why.** The strategy put the slice into L1 ("the bulk-loaded world plus the real-path slice"), but the slice is a
  fixture Site in tenant `demo` with hand rows: in the world it would be a stray tenant with invented operation. The
  owner's purpose ("the parity test proves the bulk rows equal the real path's ... every build", question 4) is met by
  running the same proof at the same code every check. Reusing the DS3 test file keeps one parity implementation.
- **Reverse.** When world telemetry exists, add a slice of the world's own batches to C5 (two of its Kobo days through
  central ingestion on a check clone of L1 against the bulk rows in L2).

## D-DS4.8 `world check` and what "clean, good" means

- **Ruling.** C1 inputs regenerate byte-equal; C2 census equals the build's; C3 every snapshot rebuilds (`verify`); C4
  the independent model's values (`derived-values.json`, actual and plan) equal the snapshot's to the unit, a missing
  product value never counting as equal and at least one value equal; C5 parity; C6 the gap rule on every world batch;
  C7 every recorded step exited 0. All run; any FAIL is exit 4 and `passed: false` in the L2 manifest; clones carry
  `check_passed`. The walkthrough's "clean, good" database is a clone of an L2 whose check passed (owner, strategy
  question 4: "yes").
- **Why.** These are the four things the owner accepted (parity, golden digests, oracle, snapshot rebuild) plus two
  that make them trustworthy: the census catches a template changed after its build, and C7 catches a manifest
  recorded over a failed step. "Unknown is not zero" applies to the check itself. A mismatch found on the real world
  is a product finding routed to its unit, never a loosened rule.
- **Reverse.** Drop C2 if templates are ever made read-only by the server itself.

## D-DS4.9 The gap-day rule sits in the bulk load, at the Site's local days (D-DS3.21)

- **Ruling.** `BulkEvidenceLoad` refuses a batch whose envelopes' Site-local days (interval start, else source time,
  at `site.timezone`) are not contiguous: `BULK_BATCH_GAP_DAYS`, step 3a, nothing written; `PostgresEvidenceLedger.
  site_timezone` reads the zone beside `gateway_principal`.
- **Why.** D-DS3.21: the outbox's statement-level event carries a cover (least start, greatest end), so a batch with a
  gap resolves days the real path did not. The limit belongs to bulk admission, so the class is fixed there (W6), for
  every caller, not only in the ladder. Days are Site-local because the chain resolves Site-local days; a UTC rule
  passes a batch with a local gap (spec T8's case).
- **Reverse.** Split such batches by day instead of refusing them, once a writer produces multi-day batches.

## D-DS4.10 Keys of the pseudonymised identities

- **Ruling.** The coordinator makes the key root (runbook step 3's rule); L1 creates `<key-root>/<L1 database>/`
  (0700) and its tenants' keys through onboarding; L2 and clones use the same directory. `drop` of an L1 erases its
  tenants' keys through `pseudonym_key erase` before the database, and only once no child exists.
- **Why.** A clone holds the same tenant ids, so it needs the same key, and a key is never copied (runbook step 3).
  Erasing with the last database that holds the records keeps step 7's rule.
- **Reverse.** One key root per world instead of per L1.

## D-DS4.11 The re-benchmark: what is measured, and what the numbers mean

- **Ruling.** `world bench` measures a cold ladder per step, three clones, one late commercial record end to end, and
  the telemetry pipeline (bulk load, enrol, ticks to drained, per stage) on the bench slice of 14 Kobo days; records
  an option change and a contract-term edit as `NOT_BUILT`; reports a projection for the world with telemetry,
  labelled as one. Spec §4 states what each number includes. No figure is a gate.
- **Why.** Delivery §5: "measures each stage per Site and per day, and the change kinds"; the strategy: "DS4 measures
  them per Site and per day". The world has no telemetry, so the only honest per-Site-day pipeline figure is on the
  slice that has it; saying which operations do not exist yet is the "claim only what was tested" rule.
- **Reverse.** Re-run `world bench` at the first world telemetry and replace the projection with the measurement.

## D-DS4.12 DS7's trigger is read on the projection, reported to the owner

- **Ruling.** DS7 ("only if DS4's re-benchmark measures the L2 template build above 45 minutes") is triggered when
  `projected_l2_seconds > 2700`, reported in the packet as a projection with its basis; it is re-read by `world
  bench` on the first world with telemetry.
- **Why.** The L2 of a telemetry-free world measures nothing DS7 speeds up (the matcher, idle stages, parallel Sites,
  batch size all act on the telemetry pipeline); read literally, the trigger could never fire this fortnight while the
  13 Nov figure (62 s per mini-grid Site-day) projects hours for the strategy's world. Owner-level (it changes how an
  owner-accepted trigger is read): row 35, **owner to weigh in**.
- **Reverse.** Read the trigger literally, on B1's L2 total, and decide DS7 at the first world with telemetry.

## D-DS4.13 Serving a world database: held for the owner

- **Ruling.** Not decided (D-DS3.12's held question, continued). DS4 builds nothing that serves or copies a world
  database; the tool refuses every `walk` or `serve` name. Options for the owner: (a) the walkthrough serve points at a
  checked clone `assetops_world_audit_c_<label>` with the L1 key directory as `ASSETOPS_PSEUDONYM_KEY_DIR`; (b) the
  coordinator copies the checked L2 into a walkthrough name (`CREATE DATABASE assetops_polish_walk<MMDD>_test TEMPLATE
  <L2>`, seconds) and serves that, with the same key directory. **Recommendation: (b)**: the agents' tool can then never
  write a walkthrough name, the walkthrough keeps its naming and its "do not touch" rule, and the copy is the
  coordinator's one command. Row 36.
- **Why.** The delegation never widens database authorisations; serving the owner's walkthrough from a new kind of
  name is the owner's call.

## D-DS4.14 Size: 2.75 units in three units, no split

- **Ruling.** Unit 1 1.25 (the tool and its ladder), unit 2 0.75 (check, gap rule), unit 3 0.75 (bench and real runs).
  Plan 2.5; +0.25 for the gap rule (D-DS3.21) and the pipeline bench. Under the 6-unit rule.

## D-DS4.15 No user-facing text

- **Ruling.** Every output is a code or a JSON line for the coordinator; nothing is served; D-SC1.28 does not hold
  DS4.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Each answer was checked against `main` at `5a3987dcd`
(read only; no database touched). D-DS4.16 to D-DS4.24 are applied by `spec.md` rev 2 and `reviewer-guide.md` rev 2.
Rows 40 (held) and 41 of `specs/OWNER-AWAY/decisions-2026-11-21.md` log the owner-level parts.

## D-DS4.16 C4 checks a total contract: every factor of every side is named equal, recorded zero or blank (R1, R2)

- **Ruling.** Spec §2.1 gives a table of all 47 mini-grid factors for each side (actual, plan), the same at Kisiwa,
  Kobo and Mto, each one class: `E` (must equal `derived-values.json` exactly), `Z` (must be exactly 0: the world's
  record is not carried by any native layout and the product reads the held kind as zero) or `B` (must be blank:
  value `None`, with a `missing` for a leaf or non-empty `missing_leaves` for a node). Actual: 18 `E`, 1 `Z`
  (`adjustments_kwh`), 28 `B`; plan: 36 `E`, 11 `B`. `tools/world.py` holds it as the literal `C4_CONTRACT`. C4 FAILs
  on: an `E` not equal (a `None` is never equal), a `Z` not 0, a `B` with a value, a payload factor the contract
  lacks, or a contract factor the payload lacks. There is no `unchecked` and no "at least one equal". The detail lists
  every `B` factor with the record its `missing` names, which is the honesty list the packet shows the owner. The
  nine telemetry-fed blanks are `delivered_kwh`, `technical_loss_kwh`, `unexplained_loss_kwh`, `metered_kwh`,
  `necessary_l`, `candidate_l`, `unexplained_l`, `diesel_l` and `unserved_critical_kwh`. `dawn_days_below` and the
  other obligation and asset-day factors are blank on every database today, telemetry or not.
- **What the code shows (corrections to the question).** `cost_to_serve` and `contribution` keep their values.
  `fuel_cost` is stated by the fuel invoices (`rows_mini_grid.py`, `stated_by` EXPENSE (FUEL)), and a stated value
  governs its expression (`evaluate.py` `_stated_node` row 1, D-4B.1), so a blank `diesel_l` does not reach them.
  `battery_wear` is 0 because a neutral throughput times anything is 0 (`neutral_zero`). `metered_kwh` is not stated:
  no layout carries `CUSTOMER_METER_READ`, so it falls back to its expression on `delivered_kwh` and is blank.
  `adjustments_kwh` reads 0 against the pack's 45 / 30 / 40, because the billing layout carries no ADJUSTMENT
  (`records.py` has no writer for it; `unwritten.json`) and `energy/rules.py` `adjustments` takes the held CHARGE
  kind as a recorded zero (D-4A.8). That is the `Z` class, and row 41 reports it to the owner.
- **Confirmation and turnaround (R2).** The table is my reading of the code. Unit 1's spike (D-DS4.18) prints the real
  class of every factor before C4 is coded. Any difference stops the builder, and the coordinator sends it to the
  Architect, who answers in the same working session in one of two ways. (a) The table was wrong: a spec edit that
  cites the code line. (b) The product is wrong: a finding with an ID, routed to its unit, and added to
  `C4_KNOWN_FINDINGS` (empty by default; only the Architect adds to it). The builder never edits either list. Unit 2
  closes on T9's fakes and T12. T12 asserts that C4 PASSes, or, when `C4_KNOWN_FINDINGS` is non-empty, that C4's FAIL
  lines are exactly the known ones. A known finding is still a FAIL, so while one is open the real world's
  `check_passed` stays false and WK does not start from it.
- **Why.** Blanks that are named make the honesty claim testable (the owner's "unknown is not zero"). A contract that
  covers every factor cannot be passed by a silent extra blank or by an unearned number. One table holds for all three
  Sites because every Site carries the same record kinds.
- **Reverse.** When DS2's telemetry lands, the nine `T` rows become `E` (the contract is versioned with the definition).

## D-DS4.17 The batch-cover rule compares the envelopes' resolved days with the cover's, using the consumer's own day functions (R3, I1, I6; amends D-DS4.9)

- **Ruling.** The new step **7a** runs in `BulkEvidenceLoad._one` after step 7 (every ordinal accepted) and before
  step 8 (the write). Each accepted envelope gives a span `[interval_start or source_time, interval_end or
  source_time]`, read from `Accepted.envelope` (`envelope_span`). `cover_gap` then checks two grains, each with
  `chain.events`'s own functions. Site-local: `local_days(start, end, tz)`. UTC with the S3 bracket:
  `local_days(start - S3_BRACKET, max(end, start) + S3_BRACKET, "UTC")`. For each grain, the union of the envelopes'
  day sets must equal the day set of the cover `(min start, max end)` that the outbox statement event carries
  (`0044_chain_events.py`: min of `COALESCE(interval_start, source_time)`, max of `COALESCE(interval_end,
  source_time)`, one event per tenant and Site per statement). If they differ, the batch is refused with
  `BULK_BATCH_GAP_DAYS <batch id> "<grain> cover <first>..<last> differs at <day>"`. An instant that does not parse,
  or that has no offset, is refused with `BULK_BATCH_TIME_UNREADABLE <batch id> "ordinal <n> <field>"`, never a
  traceback. Both codes join `BULK_LOAD_REFUSALS`. `PostgresEvidenceLedger.site_timezone(site_id) -> str` uses
  `scalar_one()`, with no cache and no `None` branch (I6: after step 3 the Site exists and `site.timezone` is NOT NULL).
- **What it settles.** (a) A multi-day interval with another envelope inside it passes, because its span covers those
  days. (b) An interval across local midnight counts both days. (c) An envelope that step 7 rejects is refused as
  `BULK_REJECTED_ORDINAL` first, because 7a runs later. (d) A batch already COMPLETED returns `already_loaded` at
  step 6, before 7a. And a new case the question did not name: a point reading exactly at local midnight as the
  batch's last instant. The cover's end is exclusive, so the cover misses that day while the real path resolves it.
  That batch is refused: bulk would leave the day unmarked. Step 7 writes nothing (`admit` and `decide` only read),
  so 7a after it still writes and records nothing.
- **Why.** D-DS3.21's condition is "the cover resolves the same days as the real path's events". The exact test is to
  compare the two day sets with the functions the consumer uses. A rule of its own, such as a start day or a UTC day,
  would be a second definition that can disagree with the consumer (W6). The UTC grain is included because `s3_day`
  measures resolve UTC days (`events.py` `_s3_days`). A zone more than 6 hours from UTC can open a UTC gap inside
  contiguous local days.
- **Reverse.** Split such batches by day instead of refusing them, once a writer produces multi-day batches.

## D-DS4.18 Unit 1 starts with a spike on an onboarding-only tenant; any surprise stops the unit (I2)

- **Ruling.** Before any code, the builder runs the L1 and L2 steps by hand, through `tools/heavy-slot.sh --db`, on
  the scratch database `assetops_ds4t<8 hex>_audit_spike`, with a temporary 0700 key directory and the exports in a
  temporary directory. It records each exit code, `structure_snapshot` = 4, the observe exit, and every factor's class
  on each side for each Site, compared with spec §2.1. It also checks that a second hand-built L1, made after
  `pseudonym_key erase` of the first tenant into the same key directory, still applies (a new tenant id; a tombstone
  does not block it). Both databases are dropped. The builder stops and asks the Architect, without adapting the L2
  steps or the table, if `build` raises, `observe` exits non-zero, the count is not 4, a class differs, or the second
  apply fails. The Architect answers within the session (D-DS4.16's turnaround). Meanwhile the builder may go on with
  §3.1 to §3.4, which do not depend on L2. The spike's printout goes into the packet. About 0.25 unit.
- **Why.** No test on `main` builds a snapshot or runs the observer over a Site with no gateway, sources or binding set
  (the reviewer's and the implementer's reading, confirmed: only the ON1 tests use the Lakeside file). The ladder is
  only worth building if that holds.

## D-DS4.19 The key root and the state directory: contents, secrecy, creation and cleanup (R4, I3; amends D-DS4.10)

- **Ruling.** `/opt/assetecon/keys` and `/opt/assetecon/keys/world` (mode 0700) hold, for each L1 database, a directory
  `<L1 database>/` (0700). It contains one `<tenant_id>.key` per tenant (0600, 32 random bytes, written by onboarding
  through `create_key_file`) and, after an erase, that tenant's tombstone. Each key is a secret even though the data
  is synthetic, because it re-links pseudonyms to customer identifiers in that world (the runbook step 3 rule). It is
  never committed (it lives outside the repository, and the tool refuses a root inside it), never copied (clones share
  the directory), never opened by the tool (the tool only creates the directory, checks its mode and owner, and passes
  the path), and never printed or logged. Stdout, stderr, manifests, the bench report, evidence and the packet carry
  the `key_dir` path only, never a file name under it or any content. `/opt/assetecon/worlds` (0700) is `--state`.
  The tool creates `manifests/`, `inputs/` and `tmp/` in it (0700) under an existing directory, and refuses a missing
  one, one inside the repository, or one with mode `& 0o077` set (`WORLD_STATE_INVALID`). It holds no secret, but
  nothing in it is committed. An existing `<L1 database>/` directory is accepted only if its mode is 0700 and the user
  running the tool owns it, else `WORLD_KEY_ROOT_INVALID`. It may hold tombstones from a dropped L1 of the same name.
  **Cleanup:** `drop` of an L1 erases each tenant's key, then reports `key_dir` and `"keys_left": 0` (a count of
  `*.key`, no names). The tool removes `tmp/exports-<pid>` in `finally`. Only the coordinator removes a key directory
  (`rm -r`), and only once `world list` shows no manifest that names it. It may prune `inputs/<digest12>` folders that
  no manifest names. **Creation:** only the coordinator creates the three directories (`install -d -m 700
  /opt/assetecon/keys /opt/assetecon/keys/world /opt/assetecon/worlds`), and only with the owner's say-so. This is
  **held for the owner** (row 40). Units 1 and 2 go ahead on temporary directories. Unit 3's real runs wait for it.
- **Why.** Creating a key root is a new secret-bearing place on the server, which is the owner's call. The tool never
  needs to read a key, so it is given no way to leak one.
- **Reverse.** One key root per world instead of per L1 (D-DS4.10's reverse).

## D-DS4.20 C5 and B5 run DS3's tests under a base database of their own, never the shared `assetops_test` (I4)

- **Ruling.** One helper, `harness_run(test, extra_env)`, serves both C5 and B5. It creates an empty
  `assetops_w<c5|b5>_pt<8 hex>_base_test` (`CREATE DATABASE`, no template). The name passes `permitted_database`
  (the harness-clone form) and fits in 63 bytes with the harness's own `_pt<run>_<tag>_test` suffix. The helper runs
  `pwsh -NoProfile -File tools/run-host-tests.ps1 -- <test>` with this child environment: `E` without `DATABASE_URL`,
  `ASSETOPS_TENANT_SLUG` or `ASSETOPS_PSEUDONYM_KEY_DIR`; plus `ASSETOPS_TEST_DATABASE_URL` (that base), and
  `ASSETOPS_TEST_PYTHON`, `ASSETOPS_HEAVY_SLOT` and `ASSETOPS_HEAVY_DB` copied when they are set. The harness migrates
  its own template under the base. When the child is done, the helper drops any
  `assetops_w<..>_pt<hex>_base_pt[0-9a-f]+_[a-z0-9]+_test` left behind and then the base, with no sessions and never
  `FORCE`. A leftover that is still in use makes C5 FAIL with its name. `pwsh` is not on `E["PATH"]`: C5 FAILs with
  `pwsh not found` (B5 records it). The heavy-slot markers are the same ones the tool's own `require` passed, so the
  nested run sits inside the same slot.
- **Why.** The harness uses its base for its lease, its advisory lock and a sweep of orphans, so the shared
  `assetops_test` would be touched and other runs' orphans swept. A base of its own keeps the check self-contained,
  and the existing `*_test` authorisation covers it, so nothing is widened.

## D-DS4.21 `check_passed` holds only while everything the check read is unchanged (R5)

- **Ruling.** The L2 `check` block records `check_inputs`: the blob ids (`git rev-parse HEAD:<p>`) of the derived
  values, the manifest, and the check code (`tools/world.py`, `backend/tests/test_ds3_parity_postgres.py`,
  `backend/tests/test_ds3_bulk_load_postgres.py`, `backend/tests/pg_harness.py`, `tools/run-host-tests.ps1`), in that
  order. `clone`, `reset` and `list` report `check_passed` as `check.passed` only when today's ids equal them.
  Otherwise they report `null` with `check_stale: "<first differing part>"`. The clean-tree check (§3.2) covers these
  paths for every command that computes a key. Everything else the check reads is already in the L2 key.
- **Why.** "Clean, good" is exactly that flag. It must not outlive a change to the oracle or to the check itself.

## D-DS4.22 Every subprocess on a rung or a clone gets that L1's key directory (I5)

- **Ruling.** Yes. Every L1 and L2 step, C3's `verify`, and B3's steps on clone `bl` get the manifest's `key_dir` as
  `ASSETOPS_PSEUDONYM_KEY_DIR`. C4 reads payloads in-process and needs no key. C5 and B5 get none (D-DS4.20).

## D-DS4.23 T4 adds the operator prefix and the substring labels (R6)

- **Ruling.** Prefix `assetops_opx` (`is_operator_name`) and labels `observe` and `reserve` (substring `serve`) are
  refused with `WORLD_NAME_NOT_PERMITTED` before any admin statement.

## D-DS4.24 Size: 3.5 units in three units, no split (amends D-DS4.14)

- **Ruling.** Unit 1 is 1.5 (+0.25: the spike). Unit 2 is 1.25 (+0.2 for the total C4 contract and its tests, +0.1
  for the cover rule and the unreadable-time refusal, +0.1 for `harness_run`, +0.1 for check staleness). Unit 3 stays
  0.75. That is under the 6-unit rule.
