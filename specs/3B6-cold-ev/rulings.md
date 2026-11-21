# 3B6 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`),
checked against `main` at `28263c47b`. D-3B6.1 to D-3B6.12 are applied by `spec.md` rev 1. D-3B6.7 and D-3B6.8 settle
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

- **Ruling.** 2.5 units (plan 1.5; +0.5 for D-3B6.6, +0.5 for D-3B6.3 and the pack fixtures). No split. Every new
  string is a code; D-SC1.28 does not hold 3B6.
- **Why.** Spec §7.

## Handshake answers (round 1)

(None yet.)
