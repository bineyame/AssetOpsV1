# 3B4 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`),
checked against `main` at `eca96644d`. D-3B4.1 to D-3B4.15 are applied by `spec.md` rev 1. D-3B4.3/.5 and D-3B4.11
settle what an operator will see and who sets it, so they are logged for the owner in
`specs/OWNER-AWAY/decisions-2026-11-21.md` (rows 27 and 28). None widens an authorisation: one migration (precedent
0056), one name added to an existing writer's table list (spec-level, OWNER-AWAY row 5), no new writer block, no
database, no purchase. Nothing is held for the owner.

## D-3B4.1 One mechanism, `STRUCTURE_DEVIATION`; the Finding's leaf is its pin

- **Ruling.** Every observer Finding has mechanism `STRUCTURE_DEVIATION` and names its leaf in its key
  (`structure:<KEY>:<factor>:<month>:<UP|DOWN>`). No `PINS` row and no outcome-map entry; `pin_of_key` reads the leaf
  back, and the start-up check proves every observed leaf is a leaf row of its registry (D-3B4.2). Its category is its
  leaf's home (OD-21).
- **Why.** The pin rule is "one registry row per mechanism names the factor it observes". A mechanism per factor would
  add 19 pins and 19 outcome-map entries carrying nothing beyond the factor ID, on a literal 3B5 removes; a new leaf
  would need a new mechanism. With the leaf in the key, the observer is one mechanism over every factor and a new
  factor is observed by declaring its direction (W6, `fundamental-mechanics-first`).
- **Reverse.** Per-factor mechanisms in `PINS` and `ENTRIES`; the key keeps its leaf.

## D-3B4.2 A declared adverse direction per observed leaf, beside the registry, checked against the bridge

- **Ruling.** `structure/observe/rules.py` `OBSERVED` (structure → leaf → `UP`/`DOWN`) and `NOT_OBSERVED` (every other
  leaf → reason) together cover every leaf once. Start-up refuses a leaf in neither or both, an observed node, a
  declared, calendar or option-only leaf, a direction that disagrees with the sign the bridge roots give the leaf, and
  an unreached leaf outside Protect (`check.check_observed`, six codes).
- **Why.** Protect measures are not reached by any money root, so the direction must be declared somewhere; one
  declaration for every leaf is one mechanism. Where the bridge does reach the leaf, the sign is derived and the check
  makes the declaration agree, so a later structure change cannot leave a stale direction. Kept off `FactorRow` (as
  `TARGET_RULE`, `CARRY_AT_TARGET` and `BRIDGE_ROOTS` are), so no registry version moves, no stored snapshot needs a
  rebuild, and 3B4 cannot collide with 4a's or 3B6's rows. Exhaustive cover forces a ruling for each new leaf.
- **Reverse.** Move the direction onto `FactorRow` with a registry version.

## D-3B4.3 What is observed in MINI_GRID: leaves only, evidenced ones, 19 of 31

- **Ruling.** The 19 leaves of spec §2.1. Not observed: the declared leaves (a declared value moving is a setting, not
  a deviation), the option-only leaves (no observed side), the calendar, `hours_per_day` (an exposure rate inside a
  product; `reduced_days` carries the risk) and `field_visits` and `liability` (under no money root and not Protect, so
  no kind of the owner's rule applies). Nodes are never observed.
- **Why.** Design §4: a Finding is pinned to the most specific factor, never a parent total whose change its children
  explain, and the observer "raises a deviation on the leaf that carries it, not again on each total above". Its
  acceptance tests ask for exactly this: Mto's unbilled charges on unmapped meters "and not again on billed kWh or
  revenue". **Owner to weigh in** (row 27).
- **Reverse.** Move a leaf between the tables; the check re-proves it.

## D-3B4.4 The kind is derived: bottom line, cash, or Protect; no opportunity yet

- **Ruling.** `PROTECT` for a leaf whose home is Protect; `BOTTOM_LINE` when the first bridge root (contribution)
  reaches it; else `CASH` (reached from collected only). No opportunity Finding is raised.
- **Why.** Q-A1's three kinds, read from the structure rather than declared twice. The opportunity kind needs a
  customer's own record (a letter of intent, a route offer) and no such record kind exists; raising one on headroom
  alone is what the design forbids. Risk `R-NO-OPPORTUNITY`.
- **Reverse.** A record kind and a fourth kind when the first such record is held.

## D-3B4.5 The rule, and what is compared

- **Ruling.** Raised iff both sides are values in one currency, the gap is adverse by direction, and `abs(gap) >
  band`; band 0 with no tolerance, `pct/100 × abs(actual of_factor)` with one, not computable when that actual is
  missing (`TOLERANCE_NOT_AVAILABLE`, not raised). The target is 5a's as given, assumptions included; the actual is
  the un-carried actual.
- **Why.** The design: "with no tolerance set, every adverse deviation is raised (Architect's call)". The pack's
  Kisiwa line ("20 L, inside the 2% tolerance (about 48 L): reported, not investigated") fixes the band as a share of
  the month's actual `diesel_l`. Unknown is never zero, so an unknown band is never 0. The carried actual would turn a
  missing invoice into a gap of zero by construction; the un-carried one says the record is missing. Against an
  assumed target (leak at zero, P5) the deviation is the owner-approved target's; the claim names the target's
  evidence so a screen can say so. Risk `R-ASSUMED-TARGET`. **Owner to weigh in** (row 27).
- **Reverse.** Exclude assumed targets (one state more), or use the carried actual.

## D-3B4.6 Which tolerance is in force

- **Ruling.** A Site declaration `SET` for the leaf, latest by `(recorded_at, id)` among those with `valid_from <=
  month` and recorded by the run's instant, wins; `CLEARED` returns to the row's default; else none.
- **Why.** 3B1 R12: the row's value is the structure default and a Site's declared value overrides it. Month-dated so
  a tolerance set today does not silently rewrite closed months unless the person says from when.

## D-3B4.7 Today's Finding store, one new domain; one run per Site-month, one assessment per revision

- **Ruling.** Findings go into `finding`/`finding_revision`, domain `structure`, by the Finding store; the migration
  adds one arm to each of 0056's two CHECKs and a bounds CHECK. Each revision cites an `assessment_revision` of an
  `analytic_run` (`structure-observer-1`) written by the assessment store, as fuel's Findings do.
- **Why.** "Code only; Findings use today's store" (reuse matrix): identity, revisions, lifecycle and the recurrence
  link already exist there. The NOT NULL citations are the store's lineage contract; fuel (0056) is the precedent for
  a domain that is not a dispatch episode. A second store would split "a Finding" into two models.
- **Reverse.** Drop the arm (downgrade refuses while rows exist).

## D-3B4.8 Lifecycle and recurrence

- **Ruling.** Spec §4.3's table. A month's Finding opened while the previous month's Finding of the same leaf and
  direction is `SUPPORTED` sets `recurs_after_finding_id` to it.
- **Why.** The existing transitions say exactly what happened (a changed figure, a deviation gone, a basis no longer
  readable, a return), and the existing creation link is the thread across months without touching chain threads.

## D-3B4.9 Today's readers leave the domain out; the threads stage skips it

- **Ruling.** Four reads change (spec §4.4): the thread sources query, the dispatch fence count, `finding_detail` and
  `rows`. Others are class A (by id, domain, mechanism or analytic) and unchanged.
- **Why.** The sweep found that `0044`'s trigger feeds every revision to the threads stage, whose `finding_source`
  raises `KeyError` on an unmapped domain and would leave the Site's events unconsumed for ever; the by-id route would
  show the code as a title. No screen shows these Findings until their words exist (D-3B4.13). The fence already
  counts fuel, cold and EV revisions, which is a wider class left as risk `R-FENCE-FUEL`, not changed here.
- **Reverse.** Remove each predicate when a slice gives the domain its reader.

## D-3B4.10 Input: a served, current snapshot of a closed month

- **Ruling.** The observer reads `SnapshotRead.portfolio` and refuses `NO_SNAPSHOT`, `REBUILD_NEEDED`,
  `SNAPSHOT_NOT_CURRENT` and `MONTH_OPEN`, writing nothing.
- **Why.** The snapshot is what every screen reads (OD-23), so a Finding agrees with the figure beside it. An open
  month's actuals are partial; every DOWN leaf would read adverse mid-month. A stale snapshot would raise on old
  records.

## D-3B4.11 Tolerance declarations: a record, by command naming the person

- **Ruling.** `structure_tolerance` (append-only; joins `$findingTables`, the Finding store writing it with a plain
  INSERT). `declare_tolerance` names the person (`--as`), the finance lead for a leaf with a money dimension, the Site's
  manager (grant bound to that Site) for the rest; `recorded_by_script` true.
- **Why.** Design §4 "Who": the finance and commercial lead sets money tolerances, the operations or Site manager
  operational ones, each recorded with person and time. 3A7's Q1 default (figures entered by command with `--as`) is
  the precedent until the settings screen (`3C0b`). The setting governs Findings, so it sits under the Finding store's
  writer in the same shape: joining a list is spec-level (row 5); a new writer block would be the owner's. **Owner to
  weigh in** (row 28).
- **Reverse.** Move the table to another writer's list, or a screen replaces the command; the rows stay.

## D-3B4.12 The claim and the basis

- **Ruling.** Spec §2.2 and §4.3: the claim holds the condition in the leaf's unit, its tolerance and evidence, the
  snapshot cited and `also_pinned`; never money. The basis excludes instants and ids.
- **Why.** "What a Finding may claim: its condition, in its factor's unit and period ... never an outcome value of its
  own" (design §4); the bridge carries the money once. "Does re-running the observer on unchanged records add no
  revision?" needs a basis that a rebuilt snapshot does not move.

## D-3B4.13 No served text

- **Ruling.** The Finding's `title` holds the mechanism code and `limitations` is empty; both commands print codes and
  JSON, stderr the code alone; no message key. The words come as SC-1 statements with the first slice that shows these
  Findings.
- **Why.** D-SC1.28: no hand-built text before SC-1a. With none added, 3B4 is not held by SC-1a's merge (as 3B2,
  D-3B2.8). D-I18N.1: words render at read from structured input, never stored.

## D-3B4.14 Sequencing with 4a and 3B6

- **Superseded in part by D-3B4.25:** only the `check.py` edit waits; units 2 to 4 do not.

- **Ruling.** Unit 1's new files may start on the handshake alone; its `check.py` edit and units 2 to 4 start after 4a
  and 3B6 merge. 3B4 never edits `registry.py`, row files or `sources.py`. `permissions.py` gains two keys at the end of
  `COMMAND_ROLES` (3A7 adds one; a textual merge only). The migration number follows gate A/B (D-3C2.9).
- **Why.** All three slices edit `check.py`; 4a and 3B6 also edit the registry and sources. Ordering after them costs
  nothing: 3B4 follows both in the pull order (row 4).

## D-3B4.15 Size 3.5 units, no split

- **Ruling.** Units 1.0 + 1.25 + 0.75 + 0.5.
- **Why.** Over the plan's 2.5 by the store's domain arm and reader sweep (D-3B4.7, D-3B4.9) and the tolerance record
  (D-3B4.11), both needed for the gate. Under 6 units.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation, checked against `main` at `12a0c6356`. Every question of
`handshake.md` (R1 to R4, I1 to I6, the pre-flight notes) is answered once below; `spec.md` rev 2 and
`reviewer-guide.md` rev 2 carry each. No owner-level call arises (no new row in OWNER-AWAY; rows 27 and 28 stand), no
authorisation is widened: still one migration, one guard name, no new writer block, no database, no purchase. Nothing
is held. Verified against code: R1 `rows_mini_grid.py:106`; I1 `check.py:25`, `evaluate.py:22`, `targets/rules.py:15`;
I2 `structure_snapshot/model.py:48`, `store.py:33`; I3 `accounts/service.py:255`, `accounts/model.py:80`,
`build_structure_snapshot.py:79`; I4 `postgres_finding_store.py:263-277`; I5 `0009_finding_store.py:82-83`.

## D-3B4.16 `COVER` is about the tables, `LEAF` about the row; they no longer overlap (R1)

- **Ruling.** `COVER`: a leaf of the registry in neither table or in both; an entry (of either table) that is not a row
  of the registry; a reason not in `REASONS`; a `NOT_OBSERVED` entry that is a node (that table lists leaves only).
  `LEAF`: an `OBSERVED` entry that is a node. A node of the registry is therefore `LEAF`'s, never `COVER`'s, so P2
  (`billed_kwh` added to `OBSERVED`) raises `STRUCTURE_OBSERVE_LEAF` and test 3's `LEAF` plant is the same table.
- **Why.** The reviewer is right: as written `COVER` ("not a leaf ID of the registry") caught a node before `LEAF`, which
  made `LEAF` dead code for every real node and P2's expected code wrong. Splitting by what is wrong (a name that is no
  row, versus a row of the wrong shape) gives each of the six codes a table that only it fires on, which test 3 asserts
  (each planted table raises its code and no earlier one).
- **Reverse.** Merge `LEAF` into `COVER`.

## D-3B4.17 Every plant fails a named assertion; four reader predicates, four plants (R2)

- **Ruling.** Reviewer guide rev 2 has plants P17 (`_fence` counts structure), P18 (`rows` `finding`/`finding_revision`
  selects unfiltered) and P19 (`rows` assessment, evidence or merge select unfiltered), each failing a named assertion
  of test 13, so every one of the four predicates of D-3B4.9 has a plant. Test 13 asserts the five keys of
  `rows()` one by one. The audit of the other plants found two that could not fail as named and fixes them: P10
  (`snapshot_as_of` in the basis) cannot be planted in `basis()`, which sees no snapshot, so it is planted where the
  service computes the basis (over the claim) and fails test 11's rebuilt-snapshot step only; P9 (the carried actual)
  was named for test 6, which runs on an uncarried side by construction, so it is re-planted in `observe_site`
  (D-3B4.26) and fails the new test 6b. Plants P20 to P23 cover D-3B4.19, D-3B4.20, D-3B4.21 and a dropped basis field.
- **Why.** "Each plant fails its named test" (§9 Q8) is only worth what each plant can reach; a plant that cannot fail
  proves nothing (W2).

## D-3B4.18 "No money" means no bridge value and no effect of acting; the claim's key set is literal (R3)

- **Ruling.** A Finding never holds a bridge value, an effect of acting, a priced line or a currency total it
  computed. A money-unit leaf's own `actual`, `target`, `gap` and `band`, in that leaf's unit and currency
  (`outstanding`, `in_transit`, `om`, `staff`, `tariff`, `productive_tariff`, `diesel_price`: 278.00 USD), are the
  condition and stay. The claim's key set is the 25 keys of spec §4.3 (`format` and the 24 listed), no others; test 11 asserts it as a literal set
  (not "no key containing money"), and P15 plants a `money` or `effect` key.
- **Why.** Design §4: a Finding claims "its condition, in its factor's unit and period"; for a money leaf that is a
  money figure. The old wording contradicted §1. The bridge carries the money once.

## D-3B4.19 A Site may declare 0 %; band 0 then needs no `of_factor` actual (R4)

- **Ruling.** `declare_tolerance set` accepts `0 <= pct <= 100` (the DB regex already admits 0). Band: `pct = 0`
  gives `Decimal(0)` without reading the `of_factor` actual (a band known to be zero is not unknown); otherwise as
  §2.2. So a Site can zero a structure default (`unexplained_l`'s 2 %) and every adverse deviation is raised again,
  the design's own meaning of no tolerance. The row's default stays `pct > 0` (3B1's `STRUCTURE_TOLERANCE`, unchanged).
  The basis writes `pct` normalised (`0.0`, `0.00` and `0` are one value, as are `5` and `5.00`).
- **Why.** `CLEARED` returns to the default, so without 0 no Site could ask for strictness on a leaf that has a
  default; refusing it was an accident of copying the row's rule, not a design. Honest semantics: a declared 0 is a
  stated choice, source `SITE`, recorded with person and time, and distinct from an absent declaration.
- **Reverse.** `0 < pct`; the strict Site then has no route on defaulted leaves.

## D-3B4.20 No import cycle: `observe.rules` imports nothing that imports `check` (I1)

- **Ruling.** `structure/observe/__init__.py` is a docstring only. `observe/rules.py` imports only `structure.registry`,
  `structure.expressions` and `structure.attribution.rules` (stdlib-only modules, no path back to `check`) and never
  `targets.rules`, `evaluate`, `check` or `observe.observe`. `check.py` imports `observe.rules` at the top;
  `check_observed` reads `TARGET_RULE` through a function-local `from assetops_backend.structure.targets import rules`
  (at call time `check` is fully loaded, so the `check -> targets.rules -> evaluate -> check` loop cannot close at
  import). Only `observe/observe.py` (not imported by `check`) imports `evaluate`. Test 1b runs three fresh
  interpreters (`python -I -c "import ..."`), importing `structure.check`, then `structure.observe.rules`, then
  `structure.evaluate` first; each must succeed; P21 (a top-level `targets.rules` import in `observe/rules.py`) fails it.
- **Why.** Verified: `evaluate.py:22` imports `StructureError` from `check`, and `targets/rules.py:15` imports
  `evaluate`. Designing the module graph out beats a lazy import in `check_observed` for `observe.rules` itself, which
  would hide a cycle until call time; the one lazy import left is the single unavoidable one, and the test makes it
  load-bearing.

## D-3B4.21 `input_evidence_sha256` is the Site row's stored `payload_sha256`, read through the store (I2)

- **Ruling.** The value is `SnapshotRow.payload_sha256` of the Site's snapshot row (the row whose id is the served
  `SiteMonthSnapshot.snapshot_id`), obtained by `store.get(tenant_id, [site.snapshot_id])[0]` on the public
  `StructureSnapshotStore` protocol (`structure_snapshot/store.py:33`). `StructureObserver` takes that `store` as a
  constructor argument beside `snapshots`; no edit to `structure_snapshot/`. It never enters `basis`. A missing row is
  `StructureError("STRUCTURE_COMPOSE", ...)` (cannot happen for a served snapshot). The portfolio row's digest is not
  used. Test 11 asserts the revision's value equals the Site row's; P23 (the portfolio's) fails it.
- **Why.** The decoded snapshot has no digest (`model.py:48` is on the row); recomputing from canonical form would
  invent a second definition of the digest. The Site row is the evidence this Site's figures came from; the portfolio
  row also covers other Sites, so a change at another Site would move it.

## D-3B4.22 3B4 depends on neither 3A6 nor 3A7; the exact public calls (I3)

- **Ruling.** Tenant: `store.tenant_sites(slug) -> (tenant_id, sites) | None` of the snapshot store, as
  `build_structure_snapshot.py:79` does (on `main`); `None` is `UNKNOWN_TENANT`, and the Site by code is in `sites`
  (`SiteRef.site_id`, `.site_type`). Person: `AccountService.onboard_person(email) -> OnboardPerson | None`
  (`accounts/service.py:255`, 3A3, on `main`): refuse `PERSON_NOT_FOUND` when it is `None`, `active` is false, or
  `tenant_id` differs from the tenant's; its `roles` is `frozenset[(role, site_id | None)]`. Admission: the first role of
  `roles_of(key)` for which a pair exists, a `SITE_MANAGER` pair counting only when its `site_id` equals the Site's.
  The accounts service is built by `accounts.composition.build_account_service(url)` unless injected (as
  `load_emulated_exports.py:146`). `main(argv, *, observer=None, accounts=None)` takes both. `AccountService.tenant_by_slug`
  is not used (it does not exist on `main`). `--as EMAIL` is this command's own flag; 3A7's precedent is a convention, not a
  dependency. So no gate on 3A6 or 3A7; a textual merge on `permissions.py` only (D-3B4.14). If 3A6 or 3A7 adds a
  shared helper before 3B4 merges, switching to it is a packet note, not a question.
- **Why.** Every call named exists on `main`; the spec's "from 3A6" was the only dependency and it was not needed.
- **Reverse.** Wait for 3A6/3A7 and use their helpers.

## D-3B4.23 `rows()` filters all five selects (I4)

- **Ruling.** In `rows()`: `finding` and `finding_revision` add `AND domain <> 'structure'`; `finding_revision_assessment`,
  `finding_revision_evidence` and `finding_merge` add `AND finding_revision_id IN (SELECT id FROM finding_revision WHERE
  tenant_id = :t AND site_id = :s AND domain <> 'structure')`, so no list holds a link to a revision another list
  removed. Test 13 asserts `rows()` holds no structure key in any of its five lists (P18, P19). `finding_detail`'s child
  selects are scoped by the Finding id and need no change; `_index_lineage`, the chain reads and the consequence/action
  stores read by revision or Finding id (class A, re-swept including the child tables, not only `FROM finding`).
- **Why.** The pre-flight is right: `finding_revision_assessment` is Site-wide in `rows()` and would dangle. The class is
  "every Site-wide select over the Finding tables"; the sweep now names all five tables, not the two the grep found.

## D-3B4.24 The bounds CHECK is dropped (I5)

- **Ruling.** No `finding_revision_structure_bounds`. `episode_start` and `episode_end` are `NOT NULL`
  (`0009_finding_store.py:82-83`) and `finding_revision_bounds` already orders them. The migration is the two recreated
  CHECKs plus the table; test 10 loses that assertion; the downgrade restores two CHECKs only.
- **Why.** A CHECK that cannot fail proves nothing and adds a downgrade step.

## D-3B4.25 Sequencing: only the `check.py` edit waits for 4a and 3B6 (I6)

- **Ruling.** Units 1 (the new files and their tests), 2 and 3 start on the handshake alone (plus gate A's migration
  number). Units 2 to 4 touch the Finding and assessment stores, `chain/adapters`, `permissions.py` and the guard, none
  of which 4a or 3B6 edits. Only the `check.py` edit (`check_observed`, its call in `check_all`, `OBSERVE_CODES`) and the
  tests that need it (1, 1b, 3) wait: one commit, last of the build, after `git merge-base --is-ancestor` shows both
  merged; the lane is not idle meanwhile. Until then `observe.rules` is exercised by tests 2 and 4 to 9. With 3B6
  merged, `REGISTRIES` holds COLD and EV keys that `OBSERVED` does not name: intended (spec §10: their targets do not
  exist), not a `KEY` fault (`KEY` runs over `OBSERVED`'s keys). A COLD or EV Site in a served snapshot is returned in
  `excluded` with reason `STRUCTURE_NOT_OBSERVED`, never observed and never an error (spec §5.1).
- **Why.** Supersedes D-3B4.14's "units 2 to 4 start after 4a and 3B6 merge": the dependency is on one file's text.

## D-3B4.26 Pre-flight notes accepted; the actual side is chosen in one place

- **Ruling.** (a) Signs agree; the registry has no `family` attribute: `SOURCE` reads `row.filled_by.family` and
  `row.absent`, `KIND` reads `row.home` (may be `None`, which is not Protect). (b) The sweep's unlisted readers are
  class A or harmless, as reported; added to §4.4's note, including the 0022 trigger being `mini_grid` only (the cold
  one is its own trigger, no change). (c) F2's world is pure (`new_world()` uses a memory store); `READ_AT` is imported
  from `test_3a4_commercial_months`. `observe.py` gains `observe_site(site: SiteMonthSnapshot, declarations)` =
  `observe(site.actual, site.targets.structure, declarations)`, the one place the actual side is chosen, called by the
  service; test 6b feeds it Kisiwa's real inputs and targets (`test_5b_attribution._kisiwa()`) where `om` is carried by
  `site_bridge` and must read `ACTUAL_NOT_AVAILABLE`.
- **Why.** The un-carried actual (D-3B4.5) needs a pure seam a test can reach; the service could not otherwise be
  planted without a database.

## Size (re-estimate)

Unchanged at 3.5 units (1.0 + 1.25 + 0.75 + 0.5), no split. Added: `observe_site`, the `rows()` child selects, the
Site-row digest read, the `excluded` reason, seven more plants (P17 to P23), tests 1b and 6b. Removed: the bounds CHECK, the
`tenant_by_slug`/3A gate work. They offset inside each unit (unit 2: migration smaller, `rows()` larger; unit 4 holds
the plants). If the builder's mid-build count exceeds 0 for a reason these answers should have settled, it is a packet
finding, not a re-size.
