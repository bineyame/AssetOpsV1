# 3B6 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`),
checked against `main` at `28263c47b`. D-3B6.1 to D-3B6.12 are applied by `spec.md` rev 1 and D-3B6.13 to D-3B6.24 (handshake round 1) by rev 2. D-3B6.7 and D-3B6.8 settle
what a cold or EV operator will see, so each is logged for the owner in `specs/OWNER-AWAY/decisions-2026-11-21.md`
(rows 21 and 22). None widens an authorisation: no migration, no guard change, no database, no purchase.

## D-3B6.1 Two registries on the shared records, version 1 each

- **Ruling.** `COLD_CHAIN` (36 rows) and `EV_DEPOT_CAPTIVE` (42 rows) are literal tuples in `rows_cold_chain.py` and
  `rows_ev_depot.py`, built with the same `FactorRow`, `FilledBy` and `Home`, in `leaves_of(key)` order then the
  manifest's node order, and checked by the same `check`. The mini-grid registry is untouched.
- **Why.** P3B: "Declared on the same core, with no vertical-specific code." The evaluator, the check and the read are
  already generic over the key (3B1's review: "the expression language covers the three manifest structures, so 3B6
  needs no language change"); a row file per structure keeps W2's parity test simple.
- **Reverse.** Drop an entry from `REGISTRIES`; its Sites read `NOT_DECLARED` again.

## D-3B6.2 No cold or EV row states a total

- **Ruling.** No `stated_by` on any cold or EV row; `STATED_STATE` is unchanged.
- **Why.** A stated node needs the record that states it and its reader (D-4B.1); cold invoices and the utility bill
  are `9d` and `9e`. Declaring a `stated_by` with no reader would serve nothing.

## D-3B6.3 "Not applicable" is a declared list on the registry, read by `applicability()`

- **Ruling.** `Registry.not_applicable` (default empty) names IDs that do not apply to this business; EV declares
  `("revenue",)`. `applicability(reg, id)` returns `APPLIES`, `NOT_APPLICABLE` or `NOT_IN_STRUCTURE`. The check refuses
  a malformed, repeated or own-row entry (`STRUCTURE_NOT_APPLICABLE`, per registry) and an entry no other checked
  registry has as a row (cross-registry, in `check_all`).
- **Why.** The gate asks that a captive depot show revenue as *not applicable*, never zero. A row with value 0 would be
  the zero the gate forbids; a missing row alone cannot be told from "not in this structure". A declared third state,
  checked like every other declaration, is honest and costs no evaluator change. Only `revenue` is declared because it
  is the one the pack declares (`chain_model.EV_DEPOT_CAPTIVE.revenue: NOT_APPLICABLE`); the screen that reads it
  (`3B5`, `5c`'s successors) words it as an SC-1 statement.
- **Reverse.** Empty the list; `revenue` reads `NOT_IN_STRUCTURE`.

## D-3B6.4 The registry key must equal its `structure_key` (3B1's L2)

- **Ruling.** `check_all` refuses `STRUCTURE_CATALOGUE <key>/-` when a mapping key differs from its registry's key,
  before checking that registry.
- **Why.** Carried from 3B1's review (L2): with three registries a mis-keyed entry would quietly serve the wrong
  structure to every reader that looks a Site's key up.

## D-3B6.5 The three Findings pin to leaves under Protect

- **Ruling.** `COLD_START_FAILURE` → `uncovered_nights`; `COLD_EXCURSION` → `excursion_crates`; `EV_INTERRUPTION` →
  `chargers_in_service`. `PENDING_PINS` is empty. 3B2's manifest-row test accepts a row whose factor is a node that is
  exactly the pin's leaf, and lists `COLD_EXCURSION` as having no manifest row.
- **Why.** D-3B2.2 left the factors to 3B6 and named "nights without backup cover", "chargers in service" and
  "crate-minutes above limit". The first is a node `= uncovered_nights` (a bare rename), which `STRUCTURE_PIN_TOTAL`
  refuses by D-3B2.12, so the Finding sits on the leaf it actually observes, same heading. "Crate-minutes above limit"
  has no row; `excursion_crates` (crates held above their limit) is the most specific observed factor of an excursion.
  Each lands under Protect, as the outcome-map literal reads them, so `parity()` gains no divergence.
- **Reverse.** Re-pin in `PINS`; one literal each.

## D-3B6.6 One exclusion rule for every portfolio reader; mini-grid-only Site readers refuse by code

- **Ruling.** `read.sites_excluded(sites, key)` gives `STRUCTURE_NOT_DECLARED` for a type with no structure and
  `STRUCTURE_OTHER_KEY` for a type under another key; `StructureRead.portfolio`, `TargetRead.portfolio` and the snapshot
  build use it. `TargetRead.site` and `SnapshotRead.site` refuse a key they do not read with `STRUCTURE_KEY_NOT_READ`.
- **Why.** W6: six readers filter with `get(type) is None` while composing only MINI_GRID. Mapping cold and EV without
  this would drop those Sites silently from every mini-grid portfolio (neither composed nor excluded) and crash
  `TargetRead.site` with `KeyError`. The old reason would also be false: the Site is declared, under another structure.
- **Cost.** About 0.5 unit and the test lines of spec §6.3.

## D-3B6.7 An `EV_CHARGING` Site takes the captive-depot structure (owner row 21)

- **Ruling.** `SITE_TYPE_TO_STRUCTURE["EV_CHARGING"] = "EV_DEPOT_CAPTIVE"`. When a public-charging operator is
  onboarded, a public-charging structure (revenue applies) gets its own key and the choice becomes a declared Site
  property; until then the risk `R-EV-PUBLIC` is in the packet. **Owner to weigh in.**
- **Why.** The pack declares one EV structure, the captive depot, and the one EV operator in the demonstration world is a
  captive fleet (`metro-bus`). No screen reads an EV structure this fortnight (RC5), so a public site mis-read as
  captive could not reach a user before the public structure exists. A Site property now would need a Foundation read in
  the structure read with no second value to choose.
- **Reverse.** Remove the entry; EV Sites read `NOT_DECLARED`.

## D-3B6.8 One composition per structure; no cross-structure total this fortnight (owner row 22)

- **Ruling.** A portfolio read composes one key (`structure_key`, default MINI_GRID) and names every other-structure
  Site. No cross-structure sum, and no portfolio ratio for `cost_per_departure_met`. Both are queued with trigger "the
  first tenant with Sites of two verticals" (the ratio: the first EV portfolio screen).
- **Why.** Every demonstration and pilot operator has one vertical; `compose` sums factor IDs within one registry, and a
  cross-structure sum would need a rule for shared IDs whose leaves differ (`staff` means the same record in both, but
  `revenue` has different children). Building that with no reader would be untested scope.
- **Reverse.** A composition over the shared `SUM` money nodes (`contribution`, `cost_to_serve`): about 1 unit.

## D-3B6.9 No tolerances on cold or EV rows

- **Ruling.** No `Tolerance` on any cold or EV row.
- **Why.** The manifest declares none for these structures; tolerances are used by `3B4`, which reads the mini-grid
  rows only this fortnight.

## D-3B6.10 `capacity_crate_days` is declared, not yet provided

- **Ruling.** The row is declared as the manifest states (DECLARED, room capacity, MISSING); its state is
  `NOT_CONNECTED`. The Foundation property (crates per room) and its reader go with `9d`. Pack divergence: the manifest
  lists slice `3B6` for it.
- **Why.** No property holds a room's crate capacity today (`sites/models.py` has thermal and cooling capacity only), and
  nothing reads idle capacity this fortnight (RC5). A property with no reader is the case D-4A.18 declined.
- **Reverse.** Add the property and a provider: about 1 unit, with `9d` or before it.

## D-3B6.11 Calendar leaves: `minutes_per_day` is 1440, `nights_in_period` is the month's local days

- **Ruling.** `minutes_per_day` reads `Decimal(1440)` DERIVED; `nights_in_period` reads the Site-local days of the
  month, as `period_days`.
- **Why.** Both are the manifest's literals (`"1440"`, `period_days`). A month with a daylight-saving change has one
  day of 1380 or 1500 minutes; no demonstration or pilot zone has one (risk `R-DST-MINUTES`).

## D-3B6.12 Size 2.5 units in three units; no user-facing text

- **Ruling.** 2.5 units, superseded in size by D-3B6.24 (2.75) (plan 1.5; +0.5 for D-3B6.6, +0.5 for D-3B6.3 and the pack fixtures). No split. Every new
  string is a code; D-SC1.28 does not hold 3B6.
- **Why.** Spec §7.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the same delegation; every answer checked against `main` at `f75321b92`. Questions
are in `handshake.md` (R1 to R6 reviewer, I1 to I4 implementer); each is answered once here and folded into `spec.md`
rev 2 and `reviewer-guide.md` rev 2. No authorisation widened: no migration, no guard edit, no database, no purchase.
The one owner-level call (what the gate answer claims, and the size) is `specs/OWNER-AWAY/decisions-2026-11-21.md`
row 26.

## D-3B6.13 A `HELD_NOT_CALCULATED` leaf cites a stored record that exists today (R5)

- **Ruling.** HELD means the record kind has a stored form and an intake in the code today (a binding role or a
  Foundation property), and the figure is not calculated from it yet. Anything else is `NOT_CONNECTED` ("Not available
  yet, record not connected"). Verified against `main`:
  - COLD `cooling_minutes_unavailable` stays HELD: role `compressor_state` (`sites/binding_roles.py:162`, read by
    `analytics/cold.py:54`).
  - COLD `backup_unproven_days` moves to `NOT_CONNECTED`, with `uncovered_nights` (same manifest record, "work case
    (failed start, witnessed test)"): a work case (`work/model.py`) is a free-text incident or request with no
    failed-start or witnessed-test field, and `mini_depth/rules.py:843` states no witnessed-test record exists.
  - EV `chargers_in_service` stays HELD: roles `ev_connector_state` and `ev_connector_fault`
    (`sites/binding_roles.py:204,208`; `analytics/ev_availability.py:24`).
  - EV `import_limit_kw` stays HELD: property `ev-site-import-limit` on the feed (`sites/models.py:224`,
    `sites/ev_foundation.py:431`).
  - EV `chargers_installed` stays HELD, now citing its real record: the `EV_CHARGER` components of the declared
    Foundation (`sites/ev_foundation.py`, `ev_foundation_document`, `component_type == "EV_CHARGER"`). It is a count of
    stored components, not a field.
  - EV `charger_kw` moves to `NOT_CONNECTED`: the Foundation holds `ev-charger-max-power` per charger; the leaf is one
    rating for the Site (`NONE`) and no rule picks one when chargers differ.
  - EV `charger_out_days` moves to `NOT_CONNECTED`: no ticket record with fault and restore times exists (work cases as
    above).
  Result: COLD 2 PROVIDED, 4 OPTION_ONLY, 1 HELD, 16 NOT_CONNECTED; EV 1 PROVIDED, 2 OPTION_ONLY, 3 HELD, 17
  NOT_CONNECTED. A new test (5c) holds, as the test's own literal, one `(file, token)` per HELD leaf and fails when the
  token is not in the file.
- **Why.** The state tells a reader a record is held; a state that names a record that is not there is a false
  statement (R5). The safe default is the weaker claim.
- **Reverse.** Move a leaf to HELD in `SOURCE_STATE` and 5c's table when its record has a stored form.

## D-3B6.14 What 3B6 claims about "revenue not applicable" (R4; owner row 26)

- **Ruling.** `applicability()` has no caller outside tests and nothing in `SiteStructure`, `PortfolioStructure` or
  `site_count` carries it, so 3B6 claims only: revenue is *declared* not applicable for the captive depot, the
  declaration is *checked* at start-up, and `applicability(reg, id)` is the *queryable* answer. No read shows it until
  `3B5`. Interface note (spec §2.1): `applicability()` is the only supported way to tell "revenue does not apply" from
  "revenue is not in this structure"; a reader must call it and must not infer either from a missing key. The gate
  question's "show revenue as not applicable" is answered at the data level (test 5a), and at the screen level by
  `3B5`; the spec says so.
- **Why.** A claim the build cannot show to a reader fails the review's own honesty bar; a read carrying it would add
  a field to three read records and six readers for no consumer.
- **Reverse.** When 3B5 needs it on a record, add the field then, from `applicability()`.

## D-3B6.15 The calendar test uses four month lengths (R1)

- **Ruling.** Test 5b reads both Sites for `2026-02` (28), `2026-10` (31), `2026-11` (30) and `2028-02` (29): each of
  `period_days` and `nights_in_period` equals the month's length and `chamber_minutes` (cold) equals length x 1440
  (40320, 44640, 43200, 41760), all DERIVED. The expected lengths are the test's own literals.
- **Why.** A constant 31, 30 or 28 passes any one month; four lengths, one a leap February, fail every constant.

## D-3B6.16 Plants are named against the test that catches them, by class (R2)

- **Ruling.** The guide separates *data plants* (a mutation of the real rows or `REGISTRIES`: they fail tests 1, 2 and
  start-up, not test 3, which passes its own mapping to `check_all`) from *code plants* (a line removed from
  `check.py` or a source: they fail test 3, 5b, 6 or 8). Test 3 asserts per-registry refusals through `check(reg)`
  and the mapping-level ones through `check_all(mapping)`. Code plants added: L2 removed (P20), cross-registry pass
  removed (P21), own-row refusal removed (P22), repeat refusal removed (P23), pattern refusal removed (P24),
  `nights_in_period` constant (P19), guard removed from `CommercialLeafSource` (P26), HELD record absent (P27),
  `BridgeRead.site` order (P29), portfolio inclusion (P30). P16 stays "test 2 only" (`buses_short_per_night` is not
  forced by `STRUCTURE_COMPOSES`; run on a scratch copy). Test 1 also reads the manifest's `chain_model` for the
  not-applicable list, so P3 and P5/P6 fail a real-data check too.
- **Why.** A plant that names a test that cannot catch it proves nothing; checked one by one in the reviewer guide.

## D-3B6.17 `BridgeRead.site` refuses before it reads (R3)

- **Ruling.** `BridgeRead.site` evaluates `self._targets.site(...)` first, then `self._actual.site_inputs(...)`: one
  line moved, so a cold or EV Site raises `STRUCTURE_KEY_NOT_READ` before any leaf is read. The spec's "no change" row
  becomes "order of two calls". `TargetRead.site` raises before it reads the budget lines. Test 8 adds
  `BridgeRead.site(cold)` (inputs fake and lines fake raise if called), `TargetRead.portfolio([KOBO, cold])` and
  `BridgeRead.portfolio([KOBO, cold])` (cold excluded as `OTHER_STRUCTURE`; the inputs fake called for KOBO only).
  `test_5b_attribution.py` runs in the build; a changed expectation from the reorder is a finding.
- **Why.** The alternative (allow the providers to be called for a refused Site) reads every cold leaf for nothing.

## D-3B6.18 Shared factor IDs cannot route a cold or EV leaf through mini-grid rows (R6)

- **Ruling.** Risk `R-SHARED-ID` (`COMMERCIAL_LEAVES` and `money._ROWS` are keyed by factor ID; COLD shares `staff`
  and `outstanding`). Prevented in code and in the test: (a) `sources.COMMERCIAL_KEYS = frozenset({"MINI_GRID"})`;
  `CommercialLeafSource.leaf` serves a `_ROWS` leaf only when its structure key is in it, else it falls back (and
  `ProductLeafSource` reads a PROVIDED commercial leaf as `NOT_CONNECTED`); `9d` extends the set with its own rows.
  (b) Test 6 asserts that no COLD or EV leaf in `COMMERCIAL_LEAVES | LITRE_LEAVES | money._ROWS` (and, after 4a,
  `ENERGY_LEAVES`) has state `PROVIDED` or `PROVIDED_ELSE_ASSUMED`, and that a COLD `staff` forced to `PROVIDED` still
  reads `NOT_CONNECTED` with every fake raising.
- **Why.** A guard and an assertion fail on different mistakes: P10 (state set) fails (b)'s assertion; P26 (guard
  removed) fails (b)'s dispatch test.

## D-3B6.19 Sequencing with `4a` (I1)

- **Ruling.** `MINI_GRID` keeps the version it has when 3B6 merges (3 on main, 4 after 4a); no 3B6 test asserts a
  mini-grid version (test 1 asserts the new two, version 1). Before 4a merges, unit 1 may build only: the two row
  files, the `Registry.not_applicable` field with `applicability`, the check (`check.py`), and tests 1, 2, 3 written
  over `Registry` objects made from the row files and over test-local mappings. After 4a merges into the branch, and
  not before: the `REGISTRIES` literal, `pins.py` (a pin needs its registry entry or `check_pins` refuses at
  start-up), `sources.py`, `money.py` and the readers, test 7, and the `test_3b1:91-92` and `test_3b3:377,664` rows.
- **Why.** Both slices edit the `REGISTRIES` literal, `sources.py` and those test lines; the order removes the
  conflict. 3B6 itself still starts only after 4a merges (spec §0); this says what a free lane may do first.

## D-3B6.20 Test 6 is the production chain (I2)

- **Ruling.** After 4a merges, test 6's chain is `EnergyLeafSource(<inputs fake raising>, CommercialLeafSource(...,
  LitreLeafSource(..., ProductLeafSource(...))), now)`, as `structure/composition.py` builds it; no fake is called.
  Before 4a it is Commercial over Litre over Product. 4a's `_state` keys by `SITE_TYPE_TO_STRUCTURE`, so a cold or EV
  Site reaches the fallback unchanged (the assertion of D-3B6.18 covers `ENERGY_LEAVES`).

## D-3B6.21 Two existing tests widen without a literal change (I3)

- **Ruling.** Listed in the packet under "no literal changed, behaviour widened": `test_3b2_findings_pinned.py:234`
  (its planted `Registry("NOT_MINI_GRID_KEY", ...)` now refuses at L2 `STRUCTURE_CATALOGUE X/-`, the same code, so
  it passes but no longer tests its comment; the builder retitles the comment to say L2, and adds nothing) and
  `test_4b1_stated_nodes.py` `_valued_cases` (about 60 cold and EV cases join; a failing case is a finding on the
  row, not a test edit; the file is already in §6.2).

## D-3B6.22 The W6 grep is narrowed to the readers of the map (§4.4, I4)

- **Ruling.** Greps: (G1) `grep -rn 'SITE_TYPE_TO_STRUCTURE' backend/assetops_backend`: every hit must lie in
  `structure/` or `structure_snapshot/` (run on `main`: 25 hits, 8 files, all inside); (G2) `grep -rn
  'build_structure_read\|build_target_read\|build_bridge_read\|StructureRead(\|TargetRead(\|BridgeRead(' backend/assetops_backend`:
  no hit outside those two directories (run on `main`: none); (G3) `grep -rn 'NOT_DECLARED\|REGISTRIES\["MINI_GRID"\]'
  backend/assetops_backend/structure backend/assetops_backend/structure_snapshot` (27 hits on `main`, each listed in the packet). A
  hit outside G1 or G2's allowed set is a handshake question. The old `"MINIGRID"` literal grep is dropped: its
  outside-hits (`chain/`, `sites/`, `scheduling/`, `site_outcomes/`) are other uses of the literal, not readers of the
  map. Implementer pre-flight (c) found no hit needing a change beyond `structure/money.py` (D-3B6.18) and
  `structure/attribution/read.py` (D-3B6.17).

## D-3B6.23 Implementer pre-flight and pack figures accepted (I4)

- **Ruling.** Pre-flight (a), (b) and the pack figures are accepted as run (36 and 42 rows; `check_pins` passes;
  `parity()` returns exactly `UNEXPLAINED_FUEL`; every `SUM` factor equals the pack). The `§6.3` line numbers are
  confirmed; the packet need not repeat them.

## D-3B6.24 Size 2.75 units (owner row 26)

- **Ruling.** 2.75 units (+0.25: `money.py` guard, `BridgeRead` reorder, test 5c, the four-month calendar test, ten
  more plants in the guide). Three units: 1.0, 1.0, 0.75. No split.
- **Why.** Spec §7.
