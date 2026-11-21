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

- **Ruling.** Unit 1's new files may start on the handshake alone; its `check.py` edit and units 2 to 4 start after 4a
  and 3B6 merge. 3B4 never edits `registry.py`, row files or `sources.py`. `permissions.py` gains two keys at the end of
  `COMMAND_ROLES` (3A7 adds one; a textual merge only). The migration number follows gate A/B (D-3C2.9).
- **Why.** All three slices edit `check.py`; 4a and 3B6 also edit the registry and sources. Ordering after them costs
  nothing: 3B4 follows both in the pull order (row 4).

## D-3B4.15 Size 3.5 units, no split

- **Ruling.** Units 1.0 + 1.25 + 0.75 + 0.5.
- **Why.** Over the plan's 2.5 by the store's domain arm and reader sweep (D-3B4.7, D-3B4.9) and the tolerance record
  (D-3B4.11), both needed for the gate. Under 6 units.
