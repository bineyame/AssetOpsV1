# DS1: generator core and the July to September history (implementer spec)

Status: **handshake open**. Architect spec rev 1, 2026-11-20. Branch `task/DS1-spec` (off `main`). Review depth:
discovery (W5): a new generator, a new schema and money figures.
Reviewer guide: `reviewer-guide.md`. Rulings: `rulings.md` (D-DS1.1 to D-DS1.11). Handshake: `handshake.md`.

Sources:
- owner: "A, start DS1 now" (`owner/owner-start-ds1-2026-11-20.md`); U9 adopted, strategy Q1, Q2, Q7
  (`owner/owner-answers-uiux-datastrat-d7-2026-11-20.md`);
- data and build strategy §3, §6, §8, §9 (row `DS1`, "History months"), Appendix F (worktree
  `/opt/assetecon/AssetOpsV1-datastrat`, branch `task/data-build-strategy`, `Docs/engineering/data-and-build-strategy.md`);
- UI/UX guide Appendix A2 (branch `task/uiux-guide`, `Docs/design-system/uiux-guide.md`);
- the frozen pack (branch `task/pack-recreate-integrate` at `d9329b582`, `Docs/demo-sprint/product-direction-layer4/`,
  written `P/` below). Tag `pack-freeze-2026-11-19` is never moved or edited;
- the coordinator's placeholder audit of 20 Nov (items 1 to 4, folded in at §2 and in `rulings.md`).

`USER_REVIEW_REQUIRED: true` (new figures on the Portfolio overview; the owner sees the trend at the walkthrough).

## 0. Before you start

1. Code starts only when `handshake.md` says the round is closed.
2. Stay off ports 5490 and 8990, Docker and every database. DS1 needs **no database**: nothing here opens one.
3. Pure-Python tests (no database URL) run directly. Browser captures (G3, §9.3) go through
   `tools/heavy-slot.sh --`. No full suites; the slice-end set is in §10.
4. Three build tasks, three branches (§3). Each task ends with a commit, a packet in this folder
   (`packet-DS1a.md`, `packet-DS1p.md`, `packet-DS1m.md`) and the count of mid-build questions.

## 1. What exists, and what DS1 adds

**Exists, and stays.** The pack's world is one month: October 2026. `P/demo-site-scenario-manifest.yaml` holds each
Site's October `period` (plan, actual, coverage, bridge) as declared inputs. `P/evaluate_structure.py` evaluates every
node bottom-up from them and writes `P/derived-values.json`. `P/independent_model.py` recomputes the same figures with no
shared code, and `P/check_manifest.py` compares the two. The mock-up embeds both through
`interactive-mockup-vNEXT/tools/gen_fixtures.py`. The manifest already declares a ledger span of 2026-07 to 2026-10
(`time_scales.ledger_history`) but carries no July to September values, so every trend slot says "Trend not available
yet" (`loop-ux.js` `uxHistory`, `uxTrend`). That is honest and stays honest until DS1 lands.

**DS1 adds**, without changing any October input or figure:
1. **A generator core** in tested repo code: the oracle-free manifest view, scope digests, seeds by scope, exact
   allocation, a canonical writer, golden digests.
2. **The history**: three months per Site for the nine Sites of the three demo operators, generated from declared rules
   (day types, seasons, story trends), written to `P/history.json`.
3. **Evaluated history**: the evaluator evaluates those months through the same structures and writes
   `derived-values.json` key `history`, which the mock-up's `uxHistory` already reads.

*Serves the objective:* an operator executive sees whether a gap is new or has been building (Mwea's occupancy sliding
since July; Embakasi's peak charging creeping up), which a monitoring tool's single month cannot show. Every point is
computed the way October is, from labelled simulated inputs.

## 2. Rulings on the five questions (reasons in `rulings.md`)

1. **`2a` is not built** (D-DS1.1). `2a` is "canonical format version 1 per source type, and the leaf factor IDs, as code
   the store and the registry share" (`P/delivery-plan.md:65`, Lane 2, 1.5 units, no dependency). No module, branch or
   `.ai/state` entry exists for it. DS1 is cut so it needs nothing from `2a`:
   - **DS1** works at month grain. Its only writer is the history-file writer, keyed by the manifest's own leaf keys.
   - **DS1b** (new, 1 unit, depends on `2a`) adds the record- and envelope-level canonical writers on the `2a` format.
     It unblocks `DS3` and `3A3`. One module (`leaves.py`, §4.4) is the single place `2a`'s leaf factor IDs replace the
     manifest keys.
2. **Code home and branches** (D-DS1.2, D-DS1.3). The generator goes in `simulator/assetops_simulator/world/`, not in
   `assetops_backend`. Pushback on "product code": generated rows are inputs, never product outputs (RULES §1), and the
   dependency-direction guard already forbids simulator-to-backend and backend-to-simulator imports, so the product
   cannot reach the generator by construction. Branches are in §3.
3. **The full design** is §4 to §8.
4. **Realism within what is knowable** is §5 and §6.
5. **Harvest Cold's after-recalculation figures belong to `3B7b`, not DS1** (D-DS1.9). They are an October revision
   triggered by a new record, which DS1's done criterion ("October byte-identical") forbids, and their input (the invoice
   amount) exists nowhere yet. The input goes in a manifest `rolling:` entry in story time; the default is in §11.

**From the placeholder audit:**
- The series runs **July to October** (four points), so "against September" reads right (D-DS1.8).
- Site series are keyed by the **manifest Site name**, as `DERIVED.sites` already is. The mock-up maps its own Site keys
  through `siteM(sk).site`, as `opTotals` does. Pushback: putting mock-up keys in the evaluator would make design-pack
  output depend on screen code.
- The Site tiles' `uxTrendNA()` without arguments (`loop-ux.js:330-331`) is routed by the coordinator to the UI lane.
  Until it lands it is `MOCK DEVIATION D5` (§9.3).
- The product's series read over `structure_snapshot` (period kind month) is **`3B7a`**. Loading the history inputs into
  the stores is **`DS3`** (D-DS1.11).
- Audit gap 1 (`missing: {record_kind, source_family, blocks[]}`) is **not a DS1 dependency**: no history record is
  missing (§6.3).

## 3. Tasks, branches, bases and reconciliation (D-DS1.3)

| Task | Branch | Base | Files it may touch | Units |
| --- | --- | --- | --- | ---: |
| **DS1a** generator core and history generation | `task/DS1a-world-generator` | `main` | `simulator/assetops_simulator/world/**`, `simulator/tests/world/**`, `tools/world_history.py`, this folder's packet | 1.5 |
| **DS1p** pack: history rules, history file, evaluator, checks | `task/DS1-pack-history` | `task/pack-recreate-integrate` at `d9329b582` | `P/demo-site-scenario-manifest.yaml` (append `history:` only), `P/history.json` (new), `P/evaluate_structure.py`, `P/independent_model.py`, `P/check_manifest.py`, `P/derived-values.json` (regenerated) | 1 |
| **DS1m** mock-up regeneration and gates | `task/DS1-mockup-trends` | `task/uiux-guide` head when the UI lane is idle, after merging `task/DS1-pack-history` | `interactive-mockup-vNEXT/fixtures.js`, `index.html` (both regenerated), tool outputs the gates rewrite | 0.5 |

**Order.** DS1a is built first. DS1p's `history.json` is produced by DS1a's CLI run against DS1p's manifest
(`tools/world_history.py generate`, §4.6), so DS1p starts once DS1a's generator passes its tests; it need not be merged.
DS1m starts after DS1p's review.

**Why there are no conflicts.**
- Since the freeze tag, `task/pack-recreate-integrate` changed only five documents and `task/uiux-guide` changed only the
  mock-up and `Docs/design-system/`. Neither touched the manifest, `history.json`, the evaluator, the independent model,
  `check_manifest.py` or `derived-values.json`. DS1p touches only those, and appends to the manifest after `checks:`.
- `fixtures.js` and `index.html` are generated. DS1m regenerates them on the UI branch itself, never on the pack branch,
  so no generated file is ever merged from two sides.
- `task/data-build-strategy` holds one document. DS1 changes no file of it. Its §9 row needs the amendment in
  `rulings.md` D-DS1.1 (DS1 at 3 units, plus DS1b). The coordinator makes it on that branch.
- DS1a merges to `main` after review. DS1p merges into `task/pack-recreate-integrate` (the pack's integration branch),
  under U9, which authorises this pack change. The tag stays where it is.

## 4. The generator core (DS1a)

### 4.1 Package layout

`simulator/assetops_simulator/world/`, importing only the standard library and `assetops_contracts` (it needs none of the
latter today). No `float` anywhere, no `random`, no clock, no environment variables.

| Module | Holds |
| --- | --- |
| `view.py` | `ManifestView`: the oracle-free view (§4.2) and `view_digest` |
| `canonical.py` | `canonical_bytes(obj)`, `sha256_hex(b)`, `write_canonical_file(obj, path)` (§4.5) |
| `scope.py` | `scope_input`, `scope_digest`, `seed`, `unit_interval` (§4.3) |
| `allocate.py` | `allocate(total, weights)` and `split_to_days(total, days, weights)` (§4.4) |
| `leaves.py` | `MONEY_LEAVES`, the label rule, and the single mapping point for `2a` |
| `calendar.py` | month days, period end, day classes |
| `history.py` | the rule engine (§6) and `generate_history(view) -> dict` |
| `__init__.py` | `GENERATOR = "assetops_simulator.world/1"` |

`tools/world_history.py` is the only file that reads YAML (PyYAML, already in the backend environment). Commands:
- `view --manifest M --out F` writes the canonical view of `M`;
- `generate --manifest M --out H` writes the history file;
- `check --manifest M --history H` regenerates in memory and exits 0 when the bytes are identical, or 1 naming the first
  differing scope (`DS1_CHECK_DIFF tenant/site/month`).

### 4.2 The oracle-free view (Appendix F, row 1)

`ManifestView.from_document(doc)` builds a new dict by **allowlist**; nothing else is copied:
- top level: `manifest_version`, `as_of`, `accounting_period`, `currency`, `timezone_default`, `history`;
- per tenant: `tenant`, `vertical`, `prices`, `energy_model`, `capacity_crates_per_room`, `sites`;
- per Site: `site`, `code`, `physical`, `tariff`, and `period` reduced to `plan`, `actual` and `coverage`.

Everything else is dropped: the private expectations, `checks`, `structures`, `factor_map`, `evaluation`, `plans`,
`snapshot`, `demo_workflow`, `home_categories`, `findings_expected`, `decision`, `entitlement(s)`, `incident`,
`observations`, `bridge`, `role_in_story`. The word naming the private block appears **nowhere** in the `world/`
package or in `tools/world_history.py`; a test greps for it (§10, T3). `view_digest` = `sha256_hex(canonical_bytes(view))`.

### 4.3 Scope digests and seeds

- A **history scope** is `(tenant, site, month)`, written `scope_key = "<tenant>/<site>/<month>"`, for example
  `"harvest-cold/Room B · Thika/2026-08"`.
- `scope_input(view, tenant, site, month)` is this dict, built from the view:
  `{"generator": GENERATOR, "month": month, "history_global": {months, anchor_period, seasons, day_classes, families,
  money_leaves, labels}, "rules": <the vertical rules, with this Site's overrides applied>, "tenant": {tenant, vertical,
  prices, energy_model, capacity_crates_per_room}, "site": {site, code, physical, tariff, period}}`.
- `scope_digest = sha256_hex(canonical_bytes(scope_input))`. A change to one Site's inputs or rules changes only that
  Site's three digests (T4).
- `seed(scope_digest, scope_key, stream) = sha256_hex(f"{scope_digest}|{scope_key}|{stream}".encode("utf-8"))`.
- `unit_interval(seed_hex) = Fraction(int(seed_hex[:8], 16) % 2001 - 1000, 1000)`, a value in [-1, 1] in steps of 1/1000.
- Streams used in DS1: the family name (`"demand"`, `"generator"`, `"solar_surplus"`, `"cooling"`, `"flat"`).

### 4.4 Exact allocation, and no floats in money

- Every number from the view enters as `Fraction(Decimal(str(x)))`. Arithmetic is in `Fraction` only.
- **Rounding a leaf**: a quantity leaf rounds to an integer unit; a money leaf (`leaves.MONEY_LEAVES`) rounds to integer
  **cents**. Both use `ROUND_HALF_EVEN` on the exact fraction. Each leaf is rounded once.
- **`allocate(total: int, weights: list[Fraction]) -> list[int]`**, the largest-remainder method:
  1. Refuse (`ValueError("ALLOCATE_BAD_INPUT")`) if `total < 0`, any weight is negative, or all weights are zero.
  2. `exact_i = total * w_i / sum(w)`; `part_i = floor(exact_i)`.
  3. Hand the `total - sum(part)` leftover units one each to the parts with the largest `exact_i - part_i`; ties go to
     the **lower index**.
  4. The parts sum to `total` exactly.
- `split_to_days(total, days, day_weight)` is `allocate` over the days in calendar order. DS1's history does not call
  it; it is tested here because `DS2` and `DS3` build on it.
- `MONEY_LEAVES = {om, staff, outstanding, in_transit, maint, liability, maintenance, energy_cost, total}`. These are
  also the leaves labelled *Emulated* (§7.2).

### 4.5 Canonical writer and golden digests

- `canonical_bytes(obj) = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`.
  It refuses any `float` with `TypeError("CANONICAL_FLOAT")`. Values are `dict`, `list`, `str`, `int` or `None` only.
- The file on disk: `json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1) + "\n"`, UTF-8, LF, no BOM.
- **Golden digests**: `simulator/tests/world/golden/history_v1.json` =
  `{"file_sha256": <sha256 of the file bytes>, "view_digest": ..., "scopes": {scope_key: sha256_hex(canonical_bytes(block))}}`.
  It is regenerated only by `python -m pytest simulator/tests/world -q --update-golden`, a conftest option, and the
  commit message says which input changed and why. A mismatch fails and names every differing scope.
- **The test fixture** `simulator/tests/world/fixtures/view_v1.json` is written by `tools/world_history.py view` from
  DS1p's manifest. So `golden.file_sha256` equals the SHA-256 of `P/history.json`, which ties the two branches together
  (T2, P5).

### 4.6 Generation flow

`generate_history(view)` follows these steps:
1. Validate the `history:` block (§5). A refusal names the code and the path.
2. For each tenant and Site in manifest order, and each month in `history.months` order:
   1. compute `scope_digest`;
   2. generate the `plan` and `actual` sides with the rule engine (§6);
   3. set `coverage` to each key of October's coverage with value `"RECORDED"` (§6.3).
3. Assemble the file (§7) and return it. `generate` writes it with `write_canonical_file`.

## 5. The `history:` block (DS1p appends it to the manifest, verbatim)

Every value below is the Architect's illustrative choice (W3 defaults, queue in §11). They are generator inputs; no
total, node or series figure appears in them.

```yaml
history:   # U9 (owner, 20 Nov): July-September 2026 history of the three demo operators. GENERATOR INPUTS ONLY: seasons,
           # day classes, family weights and per-leaf rules. Leaf values are generated by assetops_simulator.world into
           # history.json; every node, total and series is evaluated by evaluate_structure.py (D-DS1.4).
  version: 1
  months: {"2026-07": 31, "2026-08": 31, "2026-09": 30}
  anchor_period: "2026-10"
  shape_source: synthetic
  money_leaves: [om, staff, outstanding, in_transit, maint, liability, maintenance, energy_cost, total]
  labels: {money: {provenance: source-emulated, evidence: Emulated}, other: {provenance: demo-simulated, evidence: Simulated}}
  seasons: {"2026-07": cool_dry, "2026-08": cool_dry, "2026-09": warm_dry, "2026-10": short_rains}   # East Africa: cool cloudy Jul-Aug, warm dry Sep, short rains from Oct
  day_classes: {WD: [1, 2, 3, 4, 5], SA: [6], SU: [7]}   # ISO weekday of the calendar date
  families:   # weight of a day = season weight x day-class weight; jitter = amplitude of the seeded month factor
    demand:        {season: {cool_dry: "0.96", warm_dry: "1.00", short_rains: "1.00"}, day: {WD: "1.00", SA: "0.97", SU: "0.90"}, jitter: "0.02"}
    generator:     {season: {cool_dry: "1.05", warm_dry: "0.95", short_rains: "1.00"}, day: {WD: "1.00", SA: "0.97", SU: "0.90"}, jitter: "0.02"}
    solar_surplus: {season: {cool_dry: "0.80", warm_dry: "1.10", short_rains: "1.00"}, day: {WD: "1.00", SA: "1.00", SU: "1.00"}, jitter: "0.06"}
    cooling:       {season: {cool_dry: "0.97", warm_dry: "1.02", short_rains: "1.00"}, day: {WD: "1.00", SA: "1.00", SU: "1.00"}, jitter: "0.01"}
    flat:          {season: {cool_dry: "1", warm_dry: "1", short_rains: "1"}, day: {WD: "1", SA: "1", SU: "1"}, jitter: "0"}
  rules:   # per vertical and side: leaf -> rule (grammar: spec §6.1). A leaf in October's side with no rule is refused.
    MINI_GRID:
      plan:   {billed_kwh: per_day, diesel_l: per_day, om: fixed, staff: fixed}
      actual: {delivered_kwh: scale demand, technical_loss_kwh: scale demand, expected_technical_loss_kwh: scale demand,
               unexplained_kwh: scale demand, adjustments_kwh: scale demand, unbilled_mapping_kwh: zero, in_transit: zero,
               outstanding: scale demand, necessary_l: scale generator, candidate_l: scale solar_surplus,
               unexplained_l: scale generator, om: plan_value, staff: fixed}
    COLD_CHAIN:
      plan:   {crate_days: per_day, kwh: per_day, staff: fixed, maint: fixed, liability: fixed}
      actual: {crate_days: occupancy anchor anchor anchor, kwh: cold_kwh cooling anchor anchor anchor,
               outstanding: ratio crate_days, staff: fixed, maint: plan_value, liability: zero}
    EV_DEPOT_CAPTIVE:
      plan:   {kwh: per_day, peak_kwh: share kwh anchor anchor anchor, offpeak_kwh: rest kwh peak_kwh, max_kw: fixed, maintenance: fixed}
      actual: {kwh: fleet_kwh, peak_kwh: share kwh anchor anchor anchor, offpeak_kwh: rest kwh peak_kwh,
               kwh_2200_2400: share offpeak_kwh anchor anchor anchor, kwh_0000_0500: rest offpeak_kwh kwh_2200_2400,
               max_kw: fixed, maintenance: plan_value}
  sites:   # per-Site overrides by side; each states its reason
    lakeside-power/Kobo:
      actual: {unexplained_l: trend generator 0.10 0.10 0.10}   # the above-tolerance residual (120 L) is October's; before it, within tolerance
    harvest-cold/Room A · Mwea:
      actual: {crate_days: occupancy 0.56 0.49 0.42}             # occupancy sliding toward October's 35% (the occupancy root cause)
    harvest-cold/Room B · Thika:
      actual: {crate_days: occupancy 0.68 0.71 0.70}
    harvest-cold/Room C · Kirinyaga:
      actual: {crate_days: occupancy 0.79 0.81 0.80, kwh: cold_kwh cooling 1.05 1.10 1.17}   # efficiency drift toward October's +24%
    metro-bus/Ruiru:
      plan:   {energy_cost: per_day, maintenance: fixed, total: sum energy_cost maintenance, departures_required: fleet_nights}   # October's plan is stated only as a bill total; history keeps that form
    metro-bus/Embakasi:
      actual: {peak_kwh: share kwh 0.36 0.43 0.49, max_kw: trend flat 0.92 0.95 0.98}        # peak charging creeping toward October's 0.55
```

## 6. The rule engine

### 6.1 Rule grammar

A rule is a string of space-separated tokens. Numbers are decimal text parsed to `Fraction`. `anchor` means "the October
value of the same ratio" (defined per rule). Three-value lists are for Jul, Aug, Sep in that order. `O[x]` is October's
value of leaf `x` on the same side. `H[x]` is the history value of `x` already generated for this scope and side. `d` is
the month's days, and `R(f)` is defined in §6.2.

| Rule | Value | Unit |
| --- | --- | --- |
| `per_day` | `O[leaf] * d / 31` | leaf's |
| `fixed` | `O[leaf]` | leaf's |
| `plan_value` | October **plan** value of the leaf; refuse `HISTORY_NO_PLAN_VALUE` if absent | leaf's |
| `zero` | `0` | leaf's |
| `scale f` | `O[leaf] * R(f)` | leaf's |
| `trend f a b c` | `O[leaf] * (a, b or c) * R(f)` | leaf's |
| `occupancy a b c` | `o * capacity_crates_per_room * d`; `o` is a, b or c, or for `anchor` `O[crate_days] / (capacity_crates_per_room * 31)`; refuse `HISTORY_BOUND` if `o > 1` | integer |
| `cold_kwh f a b c` | `(base_kwh + k_kwh_per_crate_day * H[crate_days]) * e * R(f)`; `e` is a, b or c, or for `anchor` `O[kwh] / (base_kwh + k_kwh_per_crate_day * O[crate_days])` | integer |
| `ratio x` | `O[leaf] * H[x] / O[x]` | leaf's |
| `share x a b c` | `allocate(H[x], [s, 1 - s])[0]`; `s` is a, b or c, or for `anchor` `O[leaf] / O[x]` | integer |
| `rest x y` | `H[x] - H[y]` | integer |
| `sum x y` | `H[x] + H[y]` (cents) | money |
| `fleet_kwh` | `physical.buses * physical.kwh_per_bus_night * d` | integer |
| `fleet_nights` | `physical.buses * d` | integer |

- **Which leaves are generated.** Exactly the keys of October's side that have a rule (after the Site's overrides).
  October keys with no rule in the vertical's table (totals such as `revenue`, `contribution`, `metered_kwh`,
  `peak_share`, `occupancy_pct`, `note`) are not written. A vertical-table key that October's side lacks is skipped. An
  October key that is a factor-map leaf but has no rule is caught by DS1p's check P2.
- **Order.** A rule that names another leaf (`cold_kwh`, `ratio`, `share`, `rest`, `sum`) runs after that leaf. Otherwise
  leaves run in sorted key order. A cycle is refused (`HISTORY_RULE_CYCLE`).
- **Refusals**, all `ValueError` with code and scope key: `HISTORY_RULE_UNKNOWN`, `HISTORY_RULE_ARITY`,
  `HISTORY_FAMILY_UNKNOWN`, `HISTORY_BOUND` (a negative leaf or occupancy over 1), `HISTORY_MONTHS` (months not in
  calendar order, a day count that is not the calendar's, or the anchor month inside `months`).
- Rounding follows §4.4; a `share` or `rest` result is already integer.

### 6.2 Seasonality from day types

- `class(date)` is `WD`, `SA` or `SU` by `date.isoweekday()` per `day_classes`.
- `W(f, month) = Σ over the month's dates of season_f[seasons[month]] * day_f[class(date)]`.
- `R(f) = W(f, month) / W(f, anchor_period) * (1 + jitter_f * unit_interval(seed(scope_digest, scope_key, f)))`.
- So October reproduces itself by construction, a month's length and weekday mix enter through the same day weights
  `DS2` will extend, and the jitter is fixed by the scope, never by a run.

### 6.3 What the history may show, and what it may not (D-DS1.7)

**May show:**
- Leaf values move with month length, season, weekday mix and a seeded month factor.
- The declared story trends (§5 `sites:`) show a gap building toward October.
- Existing chronic patterns continue, at October's rate scaled by season. For example, Kobo's generator running after
  dawn is present from July. That is consistent with the verification baseline of Sep 29 to Oct 12 (`P/manifest` Kobo
  `verification_plan`).

**May not show** (each enforced by a check in §8.3):
- **No October incident before its date.** These are October-only and are zero or absent in history: Kisiwa's genset
  failure (30 Oct), Mto's inverter failure (28 Oct), Mto's meter swap (3 Oct, `unbilled_mapping_kwh`), Mto's late
  settlement (`in_transit`), Thika's backup start failure and excursion (6 Oct, `liability`), and Ruiru's connector fault
  (6 Oct). Observations, incidents and entitlements are outside the view, so no date leaf can fire.
- **No missing record.** Every history month's coverage is `RECORDED`. October's missing invoices (Kisiwa O&M, Thika
  service, Kasarani maintenance) are October's late arrivals. Their history months carry the plan value as a received
  record (`plan_value`).
- **No Protect deviation.** Every Protect and outage node evaluates to 0 in every history month.
- **No residual above tolerance.** Mini-grid unexplained litres stay at or under 2% of litres consumed.
- **No bridge rows** (D-DS1.6). A bridge is an attribution. October's are declared and checked; history ones would be
  either typed by hand (forbidden by A2) or computed by an attribution engine, which is `5c`. No screen reads a history
  bridge.
- **No Finding, option, decision, plan item, Action or right for a history month.** The evaluator runs only M2 Observe
  on history (§8). A history month may contain a factor that, evaluated as the current period, would meet a Finding's
  condition. Kirinyaga's energy drift exceeds the 5% tolerance from August. It is shown as a trend point only; no
  Finding is back-dated (queue item Q3).
- **No prices or tariffs other than October's.** No price history is declared, so October's prices and tariff apply
  (Embakasi's night price is `night_october`, correct before 1 Nov).

## 7. The history file `P/history.json` (D-DS1.5)

### 7.1 Schema `assetops.history/1`

```json
{
 "meta": {
  "schema": "assetops.history/1",
  "generator": "assetops_simulator.world/1",
  "shape_source": "synthetic",
  "view_digest": "<sha256>",
  "anchor_period": "2026-10",
  "months": ["2026-07", "2026-08", "2026-09"],
  "money_unit": "cents",
  "money_leaves": ["energy_cost", "in_transit", "liability", "maint", "maintenance", "om", "outstanding", "staff", "total"],
  "labels": {"money": {"provenance": "source-emulated", "evidence": "Emulated"},
             "other": {"provenance": "demo-simulated", "evidence": "Simulated"}}
 },
 "tenants": {
  "<tenant>": {
   "<manifest site name>": {
    "2026-07": {"scope_digest": "<sha256>", "period_days": 31, "period_end": "2026-07-31",
                "plan": {"<leaf>": <int>}, "actual": {"<leaf>": <int>}, "coverage": {"<line>": "RECORDED"}}
   }
  }
 }
}
```

- Lists are sorted where order carries no meaning (`money_leaves`); `months` is calendar order.
- Money leaves are **integer cents**; all other leaves are integer units. There are no floats in the file.
- `meta` plus `tenants` replaces A2's top-level `{tenant: …}` proposal. The labels and digests must travel with the data
  (D-DS1.5). The `period` block's shape (`plan`, `actual`, `coverage`) is A2's, minus `bridge` (D-DS1.6).
- Location: beside the manifest, `Docs/demo-sprint/product-direction-layer4/history.json`, committed. It is an input,
  like the manifest.

### 7.2 Labels (D-DS1.10)

- Each leaf's evidence word is `Emulated` if it is in `money_leaves` (records a commercial source would emit), else
  `Simulated`. *Recorded* is never an evidence word anywhere in the file or the evaluator's history output.
- `RECORDED` in `coverage` is October's existing **coverage** state ("the record exists"), not an evidence class. It stays,
  because the screens already read it that way for October, whose records are equally simulated.
- The evaluator's series carry `"evidence": "Simulated"` (the weakest class of their leaves). The mock-up does not show
  it yet (queue item Q4).

## 8. The evaluator change (DS1p)

### 8.1 `P/evaluate_structure.py`

1. **Extract** the per-side `try` block inside the M2 site loop (`for k, record in sides:` at `d9329b582`) into
   `observe_side(S, FM, vert, t, s_, record, obs, period_days, period_end, as_of) -> dict`, unchanged in logic. October
   calls it with today's arguments. `incident` and `entitlement` come from `s_` for October and are `{}` for history.
2. **Add** `load_history(path) -> dict | None`. It reads `history.json` beside the manifest, or returns `None` if the
   file is absent, and converts each money leaf from cents to `Decimal(cents) / 100`.
3. **Add** `evaluate_history(doc, hist, out) -> dict`. It runs only M2 Observe. For each Site and month:
   - it calls `observe_side` with `record` = the history side, `obs = {}`, `incident = {}`, `entitlement = {}`,
     `period_days = block.period_days`, `period_end = block.period_end`, and the Site's `factor_sources`;
   - it runs no M3 or M4, no operations measures and no owner-question variants.
4. **Output**: in `__main__` only, after `res = main(path)`, set `res["history"] = evaluate_history(...)` when the file
   exists, then write as today. `main()` itself and the variants' recursion are unchanged.
5. **Shape**, per tenant:

```json
"history": {"<tenant>": {
  "kind": "contribution | cost",
  "evidence": "Simulated",
  "months": ["2026-07", "2026-08", "2026-09", "2026-10"],
  "portfolio": {"<kind>": [{"m": "Jul", "p": "2026-07", "v": 0.0}, "...4 points"], "gap": ["...4 points"]},
  "sites": {"<manifest site name>": {"<kind>": ["...4"], "gap": ["...4"],
            "periods": {"2026-07": {"plan": {"status": "evaluated", "nodes": {}}, "actual": {}}}}}
}}
```

   - `kind` is `cost` when `chain_model[vertical].revenue == "NOT_APPLICABLE"`, else `contribution`.
   - A Site's outcome for a side is `nodes.contribution` (or `nodes.cost_to_serve` for cost) when evaluated, else
     `stated_total`. This is exactly `opTotals` in `loop-core.js:207`.
   - `gap` is actual minus plan for contribution, and plan minus actual for cost.
   - Portfolio points are the Decimal sums of the Site points.
   - The **October point** is read from the already-computed `out["sites"]`, never re-evaluated.
   - `m` is the English three-letter month and `p` the period; `v` is `money()` of the Decimal. Floats in this output
     follow the existing `derived-values.json` convention; no float is ever an input.
   - `periods` holds only the history months.

### 8.2 `P/independent_model.py`

Add `Model.history_side(tenant_id, site_name, block, side)`, built on `side_records`, `base_ctx` and `eval_leaves`, with
`period_days` and `period_end` taken from the block and with `incident`, `entitlement` and `observations` absent. It
returns status, outcome and nodes. No code is shared with the evaluator (W2).

### 8.3 `P/check_manifest.py`: new checks P1 to P10, run when `history.json` exists

| ID | Check |
| --- | --- |
| P1 | Each block's `period_days` and `period_end` are the calendar's (31, 31, 30) |
| P2 | Leaf sets: for an October side the evaluator evaluated, history keys == October keys ∩ the factor map's `record.*` names; for a side not decomposed (Ruiru plan), history keys == October keys. Each history side has October's status |
| P3 | Independent model == evaluator for every history Site, side and month: status, outcome, and every node of `contribution`, `cost_to_serve`, `revenue`, `diesel_l`, `kwh`, `energy_cost`, `departures_met` present |
| P4 | Protect zero: `obligation_hours_without_redundancy`, `obligation_hours_without_backup`, `asset_days_out_of_service`, `replayed_dawn_days_below_safeguard`, `nights_without_backup_cover`, `days_backup_start_unproven`, `departures_missed`, `nights_below_required`, `charger_days_out_of_service`, `buses_short_per_night` are 0 wherever present |
| P5 | Fuel: mini-grid `unexplained_l <= 0.02 * diesel_l`, each month. Cold: `abs(kwh - kwh_model) <= 0.05 * kwh_model` for Sites whose `kwh` rule is `anchor`. Cold: `crate_days <= capacity * period_days` |
| P6 | Reconciliation: each portfolio point == Σ its Site points (to the cent); `gap` == the stated difference; the October points == `opTotals` from `out["sites"]` |
| P7 | Labels: every `evidence` value is in {Simulated, Emulated}; no value anywhere in `history.json` or `derived["history"]` equals `Recorded`; coverage values are all `RECORDED` |
| P8 | October unchanged: `derived-values.json` with `history` removed, dumped as today (`indent=1, ensure_ascii=False` plus LF), is byte-identical to the file at `d9329b582` (the check holds that file's SHA-256 as a constant) |
| P9 | Every check that passed before DS1 still passes; the count rises only by the new checks |
| P10 | The manifest diff against `d9329b582` is exactly the appended `history:` block |

## 9. The mock-up (DS1m)

### 9.1 Regenerate

`python3 tools/gen_fixtures.py` then `node build.mjs`, from `interactive-mockup-vNEXT/`. `DERIVED.history` appears, and
`MANIFEST` gains the `history` block. `build.mjs` still refuses the private block.

### 9.2 Expected screen change, citing the mock

- Portfolio overview, KPI tile 1 (`loop-ux.js:290`, "Contribution", or "Charging and depot cost" for Metro Bus): the trend
  slot shows the 64×16 sparkline of Jul to Oct and "<change> against Sep".
- KPI tile 2 ("Gap to target", `loop-ux.js:292-293`): the same, for `gap`.
- All three operators. No other text changes. No code change to the mock-up in DS1m.

### 9.3 `MOCK DEVIATION D5` (temporary, build order)

The Site page KPI tiles (`loop-ux.js:330-331`) still say "Trend not available yet", though `DERIVED.history[t].sites`
holds their series, because they call `uxTrendNA()` without arguments. The resolving unit is the UI lane's Site trend
wiring, routed by the coordinator. Add one row to `.agent/mock-departure-register.md` (category D5, resolving unit
"UI lane: Site trend slots").

### 9.4 Gates (UI/UX guide §10.2)

- **G1**: `vocab_check`, `plan_switch_check`, `render_text`, `copy_check` and `ux_interaction_check`, unchanged, 0 hits.
- **G2**: `design_lint`, 0 hits.
- **G3**: the Portfolio overview at 1280×720, 1440×900 and 390×844, light and dark, for each operator (18 shots), through
  `tools/heavy-slot.sh --`. Evidence goes to `/opt/assetecon/evidence/DS1/<run>/`. Page errors 0; the trend is at or
  above the fold where the tile is.

## 10. Tests and commands

**DS1a**: `python -m pytest simulator/tests/world -q`, no database. The tests are written first (W2), and none imports
`history.py` internals to compute an expected value.

| ID | Test |
| --- | --- |
| T1 | Determinism: two `generate` runs in separate processes give identical bytes |
| T2 | Golden: the per-scope and file digests match `golden/history_v1.json`; a mismatch names every scope |
| T3 | Oracle: (a) a raw document = the fixture view plus a top-level private block, a `checks:` list and a private key inside one Site, each holding values that would change figures if read, gives byte-identical output; (b) the private block's name does not occur in `world/**` or `tools/world_history.py`; (c) the view's key sets equal the allowlist exactly |
| T4 | Scope isolation: changing one Site's override changes exactly that Site's three blocks and digests |
| T5 | Allocation: sum preserved; tie to the lower index; refusals; exhaustive over totals 0..50 with 1 to 4 weights from {0, 1, 2, 3}; `split_to_days` over 31 days |
| T6 | No floats: the output walk finds only `int`, `str`, `dict` and `list`; `canonical_bytes` refuses a float; a static grep finds no `float(` or `random` in `world/**` |
| T7 | Calendar: 31, 31, 30; period ends; the day-class counts of July 2026 are 23, 4, 4 |
| T8 | Rules: each refusal code is raised by a planted case; an unknown leaf is skipped; a cycle is refused |
| T9 | October anchor: for every `scale`, `trend` with factor 1 and zero jitter, and `anchor` rule, generating month = `2026-10` from a test-only view returns October's leaf exactly |
| T10 | CLI: `check` exits 0 on the generated file and 1 naming the scope after a one-byte change |

**DS1p**: `python3 evaluate_structure.py && python3 check_manifest.py` (P1 to P10 pass, plus every existing check), and
`python tools/world_history.py check --manifest <P>/demo-site-scenario-manifest.yaml --history <P>/history.json` from the
DS1a worktree, exit 0.

**DS1m**: §9.4.

**Guards**: fast check-all on DS1a only (a code branch on `main`), once, at the end, through its own slot.

## 11. Decision queue (W3; the defaults apply until the owner answers)

| # | Question | Default applied |
| --- | --- | --- |
| Q1 | Are the story trends right (Mwea occupancy 56, 49, 42%; Kirinyaga energy +5, +10, +17%; Embakasi peak share 36, 43, 49%)? | As in §5; the owner sees them at the walkthrough |
| Q2 | Should plans carry seasonality? | No: plans are a flat daily rate (`per_day`), as small operators budget |
| Q3 | Should an October Finding say "since August" where history shows the condition earlier? | No: Findings stay October's; a later screen slice may add it |
| Q4 | Should the trend tile carry the evidence word (Simulated)? | Not in DS1; the UI lane decides with the Site trend wiring |
| Q5 | The Thika invoice amount for `3B7b`'s after-state | 96.00 (the estimate carried was 80.00), received 2026-11-06T09:40+03:00, recalculated at the request time in story time (default 2026-11-06T10:15+03:00), never the browser clock |

## 12. Scope limits

Not in DS1:
- the record and envelope writers (DS1b);
- shapes beyond the month (`DS2`);
- loading anything into a database (`DS3`);
- the snapshot and its month-series read (`3B7a`);
- the after-recalculation state (`3B7b`);
- history bridges (`5c`);
- Site trend wiring in the mock-up (UI lane);
- `plan_model.py` (the day-7 re-cut adds DS1, DS1b, `3B7a` and `3B7b`, `rulings.md` D-DS1.1).
