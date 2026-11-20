# 3B7a rulings

Architect (Claude), 2026-11-20. Each ruling gives its reason. Index lines: `.ai/decisions/index-rulings-11.md`.
Handshake answers go below, under "Handshake answers (round 1)".

## D-3B7A.1 A snapshot freezes one Site-month; the portfolio row names its Site rows; nothing is ever changed

- **Ruling.** One row per Site-month build holds that Site's inputs, evaluated actual values and target side; one
  portfolio row per build holds the operator-level budget lines and the IDs of the Site rows it composes. Rows are
  append-only (memory store and the 0005 `ledger_append_only()` trigger); the latest by "as of" is served.
- **Why.** OD-23: "a calculated daily snapshot that the UI would use". `3B7b` recalculates only the Sites and periods
  a trigger marks, so the Site row is the unit of recalculation; a portfolio row naming its Site rows lets a later
  partial rebuild compose a new portfolio without recomputing untouched Sites. Append-only keeps every served figure
  reproducible (design §2.8: "every snapshot can be rebuilt from its records").

## D-3B7A.2 One build, one instant: every read at `known_at = as_of`; the stamps are 3A4's under that instant

- **Ruling.** The build takes `as_of` from its clock once and passes it as `known_at` to every read. Each Site row
  carries the `site_month` stamp of its budget-line read (`BudgetLines.stamp`), and the portfolio row the
  `portfolio_month` stamp, both under `known_at`.
- **Why.** A record arriving during a build would otherwise be in one read and not another. 3A4's stamp covers every
  money kind placed in the Site-month (charges, receipts, expenses, budget lines), so one stamp per Site covers both
  sides; under `known_at` it describes exactly what was read, and `CommercialMonths.stale` compares it with the
  current digest, so any later record, correction or move between months marks it (3A4 review L1).

## D-3B7A.3 Out of date has named reasons; the read serves stale values with them, never as current

(Amended at the handshake: a fifth reason, `RULES`, by D-3B7A.11; `RECORDS` also covers a change of the record kinds
a Site holds, by D-3B7A.12.)

- **Ruling.** `RECORDS` (a stamp is stale), `MONTH_CLOSED` (built before the month ended, read after), and
  `STRUCTURE_VERSION` or `FORMAT` (the stored form no longer matches the code). The first two serve the frozen values
  with `current` False; the last two serve no values (`REBUILD_NEEDED`). The served read calls only the store and
  `CommercialMonths.stale`: no evaluation and no month read.
- **Why.** Decisions-register item 19: "a screen must never show an older figure as current". Showing the frozen
  figure with its "as of" and the reason is honest and keeps pages fast (OD-23); a figure in another structure version
  cannot be decoded faithfully. A month read on serve would be the recompute-on-read the snapshot removes.

## D-3B7A.4 Compositions and the bridge are derived on serve from the frozen Site values

- **Ruling.** The snapshot stores each Site's values and the operator-level lines; the portfolio totals (`compose`)
  and `5b`'s gap are computed on serve from them. Owner question Q1 carries this with its default.
- **Why.** Both are arithmetic over the frozen values (no record is read), so the speed OD-23 asks for is kept; a
  stored total could disagree with its stored parts, which the never-sum and weakest-part rules forbid.

## D-3B7A.5 Inputs no stamp covers are listed, not hidden

- **Ruling.** `Freshness.untracked` lists the valued actual leaves whose sources are not commercial records (readings,
  declared prices), excluding option-only neutrals and the calendar. Their changes are detected by `3B7b` (triggers 1
  and 4). Owner question Q2.
- **Why.** A month stamp says nothing about a price setting or a reading; claiming "current" for those figures would
  overstate. The deep-dive's money is records, so on Lakeside the list is empty wherever invoices give the price.

## D-3B7A.6 Rebuilt on command after an accepted import; verification rebuilds at the "as of"

- **Ruling.** `build_structure_snapshot build` is run by the analyst after each accepted import (runbook). `verify`
  rebuilds every payload at the stored `as_of` without writing and names each differing part. The daily run and
  *Recalculate now* are `3B7b`.
- **Why.** Plan §0.3: "the analyst rebuilds the snapshot after each accepted import (`3B7a`); automatic triggers
  follow". Design §2.8: "a check compares it with a fresh evaluation"; at the same `known_at` the commercial reads are
  reproducible, so a difference is a real fault (or an untracked input that changed).

## D-3B7A.7 `StructureRead.site_inputs` is the shared seam with `5b`

(Superseded at the handshake by D-3B7A.10 for who writes it and when; the seam's content is unchanged.)

- **Ruling.** `structure/read.py` gains `SiteInputs`, `evaluate_inputs` and `StructureRead.site_inputs`; `site` becomes
  `evaluate_inputs(site_inputs(...))` with unchanged results. Whichever of `3B7a` unit 1 and `5b` unit 2 merges first
  writes it exactly as 3B7a spec §2.1; the other merges `main`.
- **Why.** The snapshot freezes inputs so it can be verified and so `5b` can carry a missing actual at its target and
  re-evaluate from frozen values; `5b` needs the same inputs on the fresh path. One definition, one place.

## D-3B7A.8 The payload is canonical JSON with exact decimals and a digest

- **Ruling.** Sorted keys, compact separators, UTF-8; every `Decimal` as `str(d)`; times in UTC ISO form; no JSON
  number but `int`s; `payload_sha256` checked on every decode, a mismatch raising (never served).
- **Why.** Exact money (no float, exponent kept) and byte-for-byte verification need one canonical form; the digest
  turns silent corruption into a failure.

## D-3B7A.9 Migration 0066 and its writer

- **Ruling.** One table, `structure_snapshot`, written only by `structure_snapshot/adapters/
  postgres_structure_snapshot_store.py` with one plain INSERT shape, registered in rule 8 as 3A1's writer is; partial
  unique indexes per scope and instant; no column defaults; downgrade refused while rows exist.
- **Why.** The persistence guard's pattern (3A1, 3A2) keeps one writer per table and refuses UPDATE by code review and
  trigger alike.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, against `handshake.md` round 1 (`task/3B7a-5b-handshake` at `9908b6028`). Every
answer is folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. Three new rulings (D-3B7A.10 to D-3B7A.12)
follow the answers. Each gate below names a plant that fails it.

### R1 (High): the seam is one commit, merged to `main` alone, first (D-3B7A.10)

**Answer.** Accepted as asked. The seam (spec §2.1 in `structure/read.py`, plus its test, now
`backend/tests/test_3b7a_site_inputs_seam.py`) is **3B7a unit 0**: one commit on its own branch
`task/3B7a-seam` off `main`, nothing else in the diff. It gets a verification review (fresh Claude reviewer, Sonnet,
RULES §4) and merges to `main` alone. Then 3B7a unit 1 starts from `main`, and **5b unit 2 does not start until the
seam is on `main`** (5b unit 1 needs only `main` and runs in parallel). 5b never writes the seam. "Byte-identical"
is replaced by a check that can fail: **5b's branch has no diff in `structure/read.py`**
(`git diff main...task/5b-attribution -- backend/assetops_backend/structure/read.py` is empty).
**Gate.** 3B7a reviewer-guide V0 (the seam branch touches any file outside `structure/read.py` and the seam test:
refused at the verification review); 5b reviewer-guide first check 1 (plant: one edited line in
`structure/read.py` on the 5b branch; the `git diff` above is non-empty, so the review fails).

### R2 (High): the guard names its own writer (no clash with `$snapshotWriter`)

**Answer.** Accepted. The new block uses `$structureSnapshotWriter`
(`$backendRoot/structure_snapshot/adapters/postgres_structure_snapshot_store.py`), `$structureSnapshotTables =
@('structure_snapshot')` and `$structureSnapshotInsertsSeen` (its own anti-vacuity counter). It is added with one
line of its own after line 1046, `$pgWriters += $structureSnapshotWriter  # 3B7a: on its own line, as the account
writer`, so the estate self-test anchors on lines 1043 to 1046 hold. `$snapshotWriter` and its checks (lines 933,
1211, 1489-1499, 1871-1873) are not touched. Three plants, each shown failing in the packet: (1) an
`UPDATE structure_snapshot` in the new adapter; (2) an `INSERT INTO structure_snapshot` from another module;
(3) the chain day-snapshot rule still fails its own plant (an `UPDATE site_day_snapshot` in
`chain/adapters/postgres_snapshot_store.py`), which shows the old rule was neither redefined nor moved.

**Guard edit: yes, one is needed.** It is additive only (a new block and one `$pgWriters +=` line, as 3A1 and 3A2
did; no existing rule is changed or loosened). It needs the owner's approval through the coordinator before
unit 3 merges; unit 3 may be built and reviewed meanwhile. Default if the owner does not answer before merge
preparation: hold unit 3's merge (units 0 to 2 are unaffected).

### R3 (High): a change of the calculation code marks a snapshot out of date (D-3B7A.11)

**Answer.** The class is "a value changed by code, not by records or the registry". Listing rule tables
(`TARGET_RULE`, `MAIN_OF`, `SOURCE_STATE`, `STATED_STATE`, `READ_AS`) fixes the instances named today and misses the
next one (4a and 4d land kWh and litre readers as code, not as a table). So the snapshot records a digest of **the
code that built it**: `rules_digest`, the sha256 over the source bytes of every `assetops_backend` module in the
static import closure of `structure_snapshot.composition` (spec §2.5). Any merge that changes a module the build
can reach changes the digest. A fifth reason, `RULES`, fires when the stored digest differs from the running one.

`RULES` serves the frozen values, `current` False (like `RECORDS`), not `REBUILD_NEEDED`: the format and the
structure version still decode faithfully, the figures were right under the code that made them, and the reason
says why they may now differ. This over-reports (a refactor with no value change also marks it): that errs on the
side decisions-register item 19 asks for, and the analyst's rebuild clears it. `3B7b` adds "the code changed" to its
triggers (a deploy rebuilds every open month).

**Gate.** Spec test 11: (a) a build with `rules="a"*64` read by a `SnapshotRead` with `rules="b"*64` is `SERVED`,
`current` False, `reasons == ("RULES",)`, values unchanged; (b) the closure contains `structure.targets.rules`,
`structure.sources`, `structure.money`, `structure.registry`, `structure.rows_mini_grid`, `structure.evaluate`,
`commercial.months` and `commercial.composition` (the last is imported inside a function body); (c) on a copy of
the package in `tmp_path`, changing one `TARGET_RULE` entry's text changes the digest. Plants: V15 (the read ignores
`rules_digest`: fails (a)); V16 (the walker reads module-level imports only: fails (b) on
`commercial.composition`; a digest over file names, not bytes: fails (c)).

### R4 (Medium): a first record of a new kind changes what October means (D-3B7A.12)

**Answer.** Accepted: compared on serve. Each Site row stores `held_kinds` (the sorted record kinds the Site holds at
`known_at = as_of`, exactly the set 4b's `CommercialLeafSource._month` computes, through the same
`latest_revisions(tenant_id, site_id=..., known_at=...)`). The served read compares it with the kinds held now,
through a narrow `HeldKinds` port (spec §3.4) beside `months.stale`; a difference adds `RECORDS` and names the
changes in `Freshness.changed_kinds` (`"<site_code>:<kind>"`). This is a freshness check like `stale` (it reads
record kinds, never values), so D-3B7A.3's "no evaluation, no month read" holds.
**Gate.** Spec test 4(d): Mto's first CHARGE, for November, after the build: October Mto `reasons == ("RECORDS",)`,
`stale_stamps == ()`, `changed_kinds == ("MTO-001:CHARGE",)`. Plant V14 (skip the kinds comparison) fails it.

### R5 (Medium): V9 can fail

**Answer.** Accepted. Test 8 adds: a first build over `[KOBO]` at `T`, then a second over `[KISIWA]` at the same
`T`. Kisiwa's Site row does not collide; the portfolio row does; `SnapshotExists` is raised and the row count is
unchanged (no Kisiwa row). Plant V9 (Site rows written before the portfolio row is refused) now fails it.

### R6 (Medium): test 10's imports

**Answer.** Accepted. `structure_snapshot/read.py` may import from `structure.read` exactly `SiteInputs`,
`SITE_TYPE_TO_STRUCTURE` and `NOT_DECLARED`, and `StructureError` from `structure.check`; never `StructureRead`.
Test 10 checks that list. Plant: an import of `StructureRead` in `read.py` fails test 10.

### R7 (Low): test 6's planted row

**Answer.** Accepted: a new id (`UUID(int=900)`), `as_of` one second after the build, the payload re-encoded and
re-digested, put through `store.put`, so it is the latest.

### R8 (Low): `encode_site`'s signature

**Answer.** Accepted: `encode_site(tenant_id: UUID, site: SiteRef, month: str, known_at: datetime, inputs:
SiteInputs, actual: SiteStructure, targets: SiteTargets) -> str`, and `encode_portfolio(tenant_id: UUID, month: str,
structure_key: str, structure_version: int, known_at: datetime, asked: Sequence[str], sites_excluded:
Mapping[str, tuple[str, ...]], portfolio_lines: BudgetLines) -> str`. Test 2 wraps the payload in a hand-built
`SnapshotRow` to call `decode_site(row, site)`.

### R9 (Low): what `verify` rebuilds

**Answer.** `asked` and `sites_excluded` are the build's inputs, not figures: `verify` takes them as stored and
rebuilds each MINI_GRID Site from its stored row (`SiteRef` from the payload's `site_id`, `site_code`, `site_type`,
`timezone`). `"portfolio:sites"` and `"portfolio:sites_excluded"` leave the differences list (they cannot differ).
`Verification` gains `rules_changed: bool` (the row's `rules_digest` differs from the running one), so a difference
after a code change says why.

### R10 (Low): the runbook line

**Answer.** The line goes in the packet (§4.4's text). The coordinator adds it to
`Docs/engineering/operator-deep-dive-runbook.md` once ON1 has merged that file; it is not in this slice's scope.

### R11 (Low): `tenant_sites`

**Answer.** Every Site of the tenant, every lifecycle (October's records do not change when a Site is retired in
December). Both stores sort in Python by `site_code` (the Postgres adapter fetches, then `sorted(..., key=lambda s:
s.site_code)`), so they agree byte for byte.

### Pre-flight P1 to P7

- **P1, P2, P3, P6:** confirmed, no change. Migration 0066 stands; renumber at merge preparation if `ON1b` lands
  first. The new columns (`rules_digest`, `held_kinds`) follow P3: `held_kinds` bound as a Python list, never a cast.
- **P4:** accepted. The seam test (unit 0) counts `site_month` calls through a counting `CommercialMonths` wrapper:
  one per Site-month for `site_inputs` and one for `site`.
- **P5:** noted; no change (same `known_at`, deterministic).
- **P7:** answered by R2 (names) and R6 (imports).

## D-3B7A.10 The seam is one commit of its own, merged to `main` before either slice uses it

- **Ruling.** 3B7a unit 0 is §2.1 and its test, alone, on `task/3B7a-seam`, verification-reviewed and merged to
  `main` before 3B7a unit 1 and 5b unit 2 start. No other branch writes `structure/read.py`.
- **Why.** Slices merge whole after review, so "whichever merges first" cannot happen with two lanes in parallel:
  both would write the seam and the second merge would conflict. One writer and one event make it checkable (an
  empty diff on every other branch).

## D-3B7A.11 A snapshot carries the digest of the code that built it; a different running digest is `RULES`

- **Ruling.** `rules_digest` is the sha256 over the source of every `assetops_backend` module in the static import
  closure of `structure_snapshot.composition`. The served read compares it with the running digest; a difference
  adds `RULES` (frozen values served, `current` False). `REASONS` is `("RECORDS", "MONTH_CLOSED", "RULES",
  "STRUCTURE_VERSION", "FORMAT")`. `3B7b` treats a changed digest as a trigger.
- **Why.** Decisions-register item 19: a figure built under rules since changed must not read as current. The rule
  tables named today are instances; code that lands leaves (4a, 4d) is the next one. The import closure covers the
  class with no list to keep, and erring towards "out of date" is the honest direction.

## D-3B7A.12 The record kinds a Site holds are frozen with it and compared on serve

- **Ruling.** Each Site row stores `held_kinds` at `as_of`; the served read compares it with the kinds held now and
  adds `RECORDS` with `changed_kinds` on a difference.
- **Why.** 4b's "connected" test reads kinds held in any month (D-4B.5), so a Site's first record of a kind changes an
  earlier month's causes, words and (for `5b`) what can be carried, with no change of that month's stamp.

## Mid-build answers (round 1)

Architect (Claude), 2026-11-20, against `mid-build-questions.md` Q1 to Q3 and the packet's "Known deviations"
(`task/3B7a-snapshot` at `0395c17c6`). Folded into `spec.md` rev 3 and `reviewer-guide.md`. New rulings D-3B7A.13 to
D-3B7A.15 follow the answers.

### Q1 (§2.5, §4.2): where the code digest lives (D-3B7A.13)

- **Ruling: option (a).** `structure_snapshot/rules_digest.py` moves to `structure_snapshot/adapters/code_digest.py`,
  same contents (`RULE_ROOTS`, `import_closure`, `rules_digest`), same signatures. Only `structure_snapshot/
  composition.py` imports it, as today; `build.py` and `read.py` keep taking the digest as a string. Tests 10 and 11
  follow the path. No guard rule changes.
- **Why.** Reading source files from disk is technology, exactly what rule 2 keeps below the adapter line; the digest
  is an input the composition reads once and hands down, the same shape as a store. Option (b) would make the guard
  edit non-additive for one file and weaken rule 2's class (the next `pathlib` above the line would cite it). Option (c)
  puts a 3B7a-only module outside its package and outside its domain entry. Precedent: ON1 mid-build Q2.
- **Guard block: unchanged.** Parts (A) to (E) in `packet.md` "Guard" stand word for word as the final text the owner
  approves (Q6). The move changes no line of it: the domain entry already says only the composition imports the
  adapters, and rule 2 already exempts `adapters/`. The builder applies the block to the repo file only after the owner
  approves, then re-runs check-all (0 failures expected) and the four guard plants, and shows (E) failing once (delete
  the adapter's INSERT in a scratch copy): the packet says "not shown failing: (E)", which a reviewer must not accept.

### Q2 (§0, §6): a migration test asserts its own chain link, never "is head" (D-3B7A.14)

- **Ruling.** The class was ruled at 3C1 mid-build Q1 and fixed in 3C1a's L1 (`test_3c1a_person_work_postgres.py`
  asserts `down_revision` through the script directory); it was not given an ID, so it recurred. It is now
  D-3B7A.14.
- **The one-line edit (allowed in 3B7a's scope).** `backend/tests/test_3a2_commercial_upload_postgres.py:280`:
  `assert script.revision == ScriptDirectory.from_config(cfg).get_current_head()` becomes
  `assert (script.revision, script.down_revision) == ("0065_commercial_upload", "0064_person_on_work")`.
  No other line of that file changes; its down-and-up runs as now.
- **Sweep (W6).** `grep -n "get_current_head" backend/tests/*.py` gives three: 3A1:437 compares the database's head
  after upgrade with the directory's head (correct: "the database reached head"); 3A2:280 (above); and **this slice's
  own** `test_3b7a_structure_snapshot_postgres.py:169`, the same defect, fixed the same way:
  `assert (script.revision, script.down_revision) == ("0066_structure_snapshot", "0065_commercial_upload")` (both
  literals change with the number if 0066 is renumbered at merge preparation, P1). The `alembic_head()` uses
  (CH2, CH3, CH9, CH9b1, CC schema, mini depth probe, 3C1a) compare the database with the head: correct, untouched.
  The packet records the sweep; the reviewer checks no other test file is in the diff.

### Q3 (§4.4): `verify` of an id that is not a portfolio snapshot of the tenant

- **Ruling: confirmed.** Exit 2, `UNKNOWN_SNAPSHOT No portfolio snapshot of this organisation has that id.`,
  refused before any rebuild. The same code and words for a Site row's id and for another tenant's snapshot id (no
  hint that the id exists elsewhere, as D-3C1.6). A malformed UUID stays argparse's exit 2. Added to §4.4 and to
  Postgres test 3 (`verify` with a Site row's id).

### Deviation: "1 of 3" and "3 of 3" in §5 (D-3B7A.15)

- **n is every Site asked for.** D-3B3.13 (`SiteCount`: "n is every Site asked for"), the owner's k-of-n answer
  (`owner/owner-k-of-n-sites-2026-11-20.md`) and D-5B.9 (`n = len(asked)`) agree; a Site of a type with no structure
  is asked, counted in n and named in `out` with `STRUCTURE_NOT_DECLARED`. That is the honest reading: the total
  covers k of the Sites the person asked about.
- **Thika is not part of Lakeside.** Lakeside (`lakeside-power`) has three Sites: KOBO-001, KISIWA-001, MTO-001
  (3A1's `SITES`; `tenant_sites` in Postgres test 2). The seed's Thika is `COLD-THIKA` of `harvest-cold`. §5's
  `THIKA-001` is a synthetic cold-chain Site placed under Lakeside's tenant id in the no-database fixture only, to
  exercise whole-Site exclusion. So in that fixture n = 4, and §5's "1 of 3" and "3 of 3" were a spec defect (the
  Architect's), not a build fault.
- **Literals (spec §5, rev 3).** `site_count(actual(), "contribution") == SiteCount(1, 4, out)` with `out` codes
  `("KISIWA-001", "MTO-001", "THIKA-001")` and Thika's reasons `("STRUCTURE_NOT_DECLARED",)`;
  `site_count(targets().structure, "contribution") == SiteCount(3, 4, (("THIKA-001", ("STRUCTURE_NOT_DECLARED",)),))`.
  Tests assert k, n and `out` codes (not k alone): a test that checks k only cannot catch a wrong n, which is the
  defect class here.
- **Real Lakeside: n = 3.** The command builds over `tenant_sites` (three Sites), so every Lakeside snapshot's `asked`
  has three codes, and the Postgres world asks three.
- **5b: no edit.** 5b §5 asks Kobo, Kisiwa, Mto in that order: "1,443.00 against 2,295.00, −852.00, 3 of 3" and the
  "2 of 3" Mto case are right. `task/5b-attribution-u23` needs no change.
- **5c: no spec yet.** It inherits D-3B7A.15 through 5b (D-5B.12): n is `len(snapshot.asked)`, read from the
  snapshot, never recomputed from the Sites with a structure; for Lakeside that is "of 3". Carried to 5c's spec
  as a done question.

### The other two deviations

- **Command test lists Sites by code:** accepted; it is `tenant_sites`'s order (R11), and §5's order is the
  no-database world's.
- **`LATE` and the Mto charge `produced_at` = their ingest instant:** accepted; §5 did not fix it and no figure reads it.

## D-3B7A.13 The code digest is an adapter

- **Ruling.** `structure_snapshot/adapters/code_digest.py` reads the source files; only the composition imports it
  and passes the digest string down. The persistence guard's rule 2 is unchanged.
- **Why.** File reads are technology below the adapter line; a one-file exemption would weaken the rule for the
  next case.

## D-3B7A.14 A migration test asserts its own chain link, never that its migration is head

- **Ruling.** A migration's test names its own `revision` and `down_revision`; "is head" is asserted only of the
  database after an upgrade. Recorded from 3C1 mid-build Q1 and 3C1a's L1, now with an ID.
- **Why.** "Is head" is true only until the next migration lands, so it breaks unrelated slices; the chain link is
  true for good.

## D-3B7A.15 A portfolio's n is every Site asked; Lakeside asks three

- **Ruling.** n = `len(asked)`, Sites of a type with no structure included and named. Lakeside has three Sites; the
  3B7a fixture's `THIKA-001` is synthetic, so that fixture alone has n = 4. 5b's "3 of 3" stands; 5c reads n from
  the snapshot's `asked`.
- **Why.** The owner's k-of-n answer and D-3B3.13 count the Sites asked; checking k alone hid a wrong n.

## Review answers (r1)

### F1 (Medium): the code digest covers every first-party package the build imports

**Answer.** F1 applies D-3B7A.11 to all first-party packages: the ruling's text ("the source of every module the build
can import") already says so, and "every `assetops_backend` module" in R3 was too narrow. The closure follows
`assetops_backend` and `assetops_contracts` (`adapters/code_digest.PACKAGES`); the contracts directory is located
without importing it. Tests 11(b) (closure holds `assetops_contracts.canonical.factors`) and 11(d) (a byte change in
`contracts/.../canonical/factors.py` after a build reads as `RULES`). F2 (test 4(e), held kinds at `as_of`), F3
(`UnknownSnapshot`: only an id that is not a portfolio snapshot of the organisation is `UNKNOWN_SNAPSHOT`; a rebuild
fault propagates) and F4 (composition disposes all three engines when `rules_digest()` raises) are test-backed fixes.
