# 2a rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`. Handshake
answers are added below under "Handshake answers (round 1)" and folded into `spec.md`.

## D-2A.1 The format lives in `assetops_contracts.canonical`, standard library only

- **Ruling.** One package in the neutral contracts, as D-DS1.1 recommended.
- **Why.** The store (backend) and the generator (simulator) must share one definition, and the dependency-direction
  guard forbids either importing the other (`tools/checks/dependency-direction.ps1`). The contracts package is the
  only place both may import, and it has no dependencies by design (`contracts/pyproject.toml`).

## D-2A.2 The package is a protected seam; a change is a new format version

- **Ruling.** From this unit on, what counts as a valid version-1 record, and every leaf ID and unit, change only by a
  version 2 beside version 1.
- **Why.** Records are stored with their format version (`3A1`). Editing version 1 in place would silently change
  what earlier intake accepted. Design D1 expects a version 2 when the first operator sample is pinned.

## D-2A.3 Leaf IDs are the manifest's `factor_map` keys; filling rules stay in the registry

- **Ruling.** The 73 IDs are exactly the `factor_map` keys of the three structure keys. `filled_by` and `absent` are
  not in the catalogue.
- **Why.** `integration-design.md` §3 names `factor_map` as the starting set, and the evaluator and the independent
  model already use these names, so the registry's parity with the demonstration (3B) needs no renaming. Filling
  rules are the registry row's fields (`decision-loop-specification.md` §3), which `3B1` and `3B6` declare; putting
  them here would give two owners.
- **Shared IDs.** `staff`, `outstanding`, `liability` and `period_days` appear in two verticals with the same quantity
  and unit, so each is one ID ("a quantity has one ID"). `om`, `maint` and `maintenance` stay three IDs: renaming
  them would break evaluator parity, and whether they are one quantity is a version-2 question.

## D-2A.4 Six dimensions; counts dimensionless; nights are days

- **Ruling.** `KWH`, `L`, `MONEY`, `DAY`, `HOUR`, `MINUTE`. Counts (assets, buses, chargers, crates, batches, visits)
  are dimensionless. A night, a bus-night and a missed departure are `DAY`.
- **Why.** The registry's start-up check refuses a structure whose units do not compose (`decision-loop-specification.md`
  §3). Checked against every manifest node: with counts as dimensions, `asset_days_total - asset_days_out_of_service`
  and `nights_in_period = record.nights | period_days` would not compose. With these six they do, except where a
  literal `0` or `1` sits inside `min`, `max` or a subtraction (`shortfall_backed`, `buses_short_per_night`,
  `contribution = 0 - cost_to_serve`). How a literal takes a unit is the expression language's rule, so `3B1` rules
  it, not the format.

## D-2A.5 A budget line may name a node

- **Ruling.** `BUDGET_LINE.factor_id` is any ID with the factor-ID syntax. The currency rule is enforced here only for
  catalogue leaves; nodes are checked at intake against the registry.
- **Why.** B2 accepts a target declared above leaf level and stops attribution there (`decision-loop-specification.md`
  §5). The format cannot know node IDs before `3B1` exists.

## D-2A.6 `SERVICE_TICKET` is an operational record; `BUDGET_LINE` replaces the old `PLAN_LINE`

- **Ruling.** The service ticket's canonical body is defined here, with store family OPERATIONAL_RECORD. The
  operator's budget lines are kind `BUDGET_LINE`.
- **Why.** The manifest's `leaf_sources` and `integration-design.md` §4 put tickets with the version-chained
  operational records, not the money store. `PLAN_LINE` in `integration-source-to-canonical-design.md` §6.1 predates
  OD-6, under which "plan" names only the new construct. `integration-design.md` §3 already says `BUDGET_LINE`.
- **Not in version 1:** QA inspection notes and the asset register. No leaf reads them (the asset register fills a
  DECLARED leaf through Site configuration). They come with a version 2 if a leaf needs them.

## D-2A.7 Readings and fuel records keep their formats

- **Ruling.** `EXISTING_FORMATS` points at `source_envelope_v4` and `operational_records`. Neither changes.
- **Why.** First write wins suits telemetry, and the fuel records' version chain already works. The design changes
  only bills and their kin (`integration-design.md` §4).

## D-2A.8 `world/leaves.py` switches in DS1b, not here

- **Ruling.** 2a does not edit the simulator.
- **Why.** DS1's history must stay byte-identical, and `world/leaves.py`'s money set differs from this catalogue's
  (it holds `energy_cost` and `total`, which are nodes or stated totals, and lacks the option-only leaves
  `collection_cost` and `handling`). DS1b makes the switch with its parity test. Keeping 2a inside `contracts/` also
  keeps it clear of DS1m.

## D-2A.9 Exact decimal text, with the DS1 magnitude bound

- **Ruling.** Decimals are JSON strings in plain notation, at most 32 characters, with the adjusted exponent within
  [-12, 12]. No JSON number is accepted for a decimal.
- **Why.** The design requires exact amounts (`integration-design.md` §3, "exact decimal text"), and the strategy's
  scale foundation forbids floats (strategy §7). The bound is the one DS1 already ruled, so the generator and the
  format refuse the same inputs.
