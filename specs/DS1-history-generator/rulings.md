# DS1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-6.md`. The owner
is informed through the coordinator; the owner is asked to weigh in on D-DS1.6 and on queue items Q1 and Q5 (`spec.md`
§11).

## D-DS1.1 `2a` is not built; DS1 is cut so it does not need it

- **What `2a` is.** "Canonical format version 1 per source type, and the leaf factor IDs, as code the store and the
  registry share" (`delivery-plan.md:65` in the pack; Lane 2, 1.5 units, no dependency, phase P2).
- **Is it built?** No. There is no canonical-format or leaf-factor module in `backend/`, `contracts/` or `simulator/`,
  no branch, and no `.ai/state` entry.
- **What DS1 needs from it.** Only the record- and envelope-level writers need `2a`'s format. The history is month
  grain, keyed by the manifest's own leaf keys, which are what the evaluator reads.
- **Ruling.**
  - DS1 is built now with no dependency (§3: DS1a, DS1p, DS1m).
  - **DS1b** (1 unit, after `2a`) adds the canonical record and envelope writers. It unblocks `DS3` and `3A3`.
  - `world/leaves.py` is the single mapping point `2a` replaces.
  - Recommendation for `2a`'s spec: put the format in `assetops_contracts`, so that the store (backend) and the
    generator (simulator) share it without crossing the import seam.
- **Estimate.** DS1 is **3 units** (1.5 + 1 + 0.5), against the strategy's 2.5. The strategy counted the history as "one
  more scope", but the evaluator, independent-model and mock-up work it needs is real. DS1b adds 1 unit. Strategy §9 row
  amendment, for the coordinator on `task/data-build-strategy`: "`DS1` | generator core at month grain and the July to
  September history | 3 | none | `DS1b`, `DS2`, history on screen" and "`DS1b` | canonical record and envelope writers
  | 1 | `2a`, `DS1` | `3A3`'s values, `DS3`".
- **Day-7 re-cut.** `plan_model.py` must add `DS1`, `DS1b`, `3B7a` and `3B7b`. None of them is in it or in the two-week
  plan today (placeholder audit item 3).

## D-DS1.2 The generator lives in `simulator/assetops_simulator/world/`

- **Pushback on "product code".** The generator writes inputs that stand in for sources. RULES §1 keeps the simulator out
  of the product, and the dependency-direction guard (`tools/checks/dependency-direction.ps1`) already bans imports in
  both directions between `assetops_backend` and the simulator.
- **Effect.** Placing the generator under the simulator gives it tests and guards, and makes the product unable to
  import it. The only YAML reader is `tools/world_history.py`.

## D-DS1.3 Three branches; nothing generated is merged from two sides

- DS1a goes on `main`. DS1p goes on `task/pack-recreate-integrate` at `d9329b582`. DS1m goes on `task/uiux-guide`, after
  merging DS1p into it.
- **Why there is no conflict.** The file sets are disjoint from what the pack and UI branches changed after the freeze
  (checked with `git diff --stat pack-freeze-2026-11-19` against both branches). The generated mock-up files are rebuilt
  only on the UI branch.
- The tag `pack-freeze-2026-11-19` is never touched. U9 is the owner's authority for this one pack change.

## D-DS1.4 History inputs are rules, not values; leaves are generated; totals are evaluated

- The manifest's `history:` block holds seasons, day classes, family weights and per-leaf rules. It holds no leaf, node
  or total figure.
- **A side October states only as a total stays stated** (Ruiru's plan). That stated total is the operator's plan
  record, built by the rule `sum` from its stated lines. It is not an evaluated figure. Every other total, and every
  series point, comes from the evaluator.

## D-DS1.5 `history.json` carries `meta` plus `tenants`, money in integer cents

- **Pushback on A2's top-level `{tenant: …}`.** The labels, generator version, digests and money unit must travel with
  the data, and they would collide with tenant keys at the top level.
- **Money in integer cents** keeps the file free of floats and decimal text. The evaluator converts on load to
  `Decimal`.

## D-DS1.6 History months carry no bridge rows (owner to weigh in)

- **Pushback on A2's "plus `coverage` and `bridge`".** A bridge row attributes a variance to a driver. October's rows are
  declared inputs that `check_manifest` verifies. For history they would have to be typed by hand, which A2 forbids, or
  computed by an attribution engine, which is `5c`.
- No screen reads a history bridge, and the gap trend needs only the variance, which is evaluated.

## D-DS1.7 What history may and may not show

See `spec.md` §6.3. In short:
- **May show:** seasonal and seeded variation, the declared story trends, and chronic patterns at October's rate.
- **May not show:** an October-dated incident, a missing record, a Protect deviation, a fuel residual above tolerance, a
  bridge, or any Finding, option, decision, plan item, Action or right.
- Each "may not" is a check (P2, P4, P5, P7, P10) or is impossible by construction (the view drops observations,
  incidents and entitlements; the evaluator runs only M2 on history).

## D-DS1.8 The series is July to October, keyed by manifest Site name

- Four points, so the tile's "against <previous month>" reads "against Sep". The October point is copied from the
  evaluated October output, never re-evaluated, so it equals the October figure on every screen.
- **Site keys are the manifest names**, as in `DERIVED.sites`. The mock-up maps through `siteM(sk).site`. This answers
  the audit's request to map Site keys: the mapping stays where the screens already do it.

## D-DS1.9 Harvest Cold's after-recalculation figures go to `3B7b`

- **Why not DS1.** They revise October in response to a new record, while DS1's acceptance is "October byte-identical".
  They depend on the snapshot pair (before and after) that `3B7a` and `3B7b` define. And their input exists nowhere:
  there is no Thika invoice amount at manifest lines 472, 1570 or 1577.
- **Ruling for `3B7b`:**
  - add the invoice as the first manifest `rolling:` entry (the section `DS6` later extends), in story time:
    `{at: "2026-11-06T09:40:00+03:00", kind: EXPENSE, site: "Room B · Thika", period: "2026-10", leaf: maint, amount: <Q5>}`;
  - the evaluator emits an `after_recalculation` block for that portfolio, with `as_of` set to the request time in story
    time;
  - the mock-up's *Recalculate now* reads that block instead of saying the figures are unchanged;
  - `ux_interaction_check.cjs:218` changes with it. That is `3B7b`'s gate.
- The default amount and request time are queue item Q5.

## D-DS1.10 Evidence words: Simulated or Emulated; coverage `RECORDED` is not one

- Money leaves are *Emulated*; every other leaf is *Simulated*. *Recorded* never appears as an evidence word.
- `RECORDED` in `coverage` keeps October's meaning, "the record exists". It is not an evidence class. A reviewer must not
  read it as a breach.

## D-DS1.11 Where the product reads the history

- The product's series read is `3B7a`'s: `structure_snapshot` at period kind month, read as a series.
- Loading the generated history into the input stores is `DS3`, after `DS1b`.
- DS1 does not depend on the audit's gap 1 (`missing: {record_kind, source_family, blocks[]}`), because no history
  record is missing. `3B7a` does need it.
