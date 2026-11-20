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
