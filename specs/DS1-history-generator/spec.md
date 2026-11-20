# DS1: generator core and the July to September history (implementer spec)

Status: **handshake closed** (round 1 answered in `rulings.md`, "Handshake answers (round 1)"). Architect spec **rev 2**,
2026-11-20. DS1a may start. Branch `task/DS1-spec`. Review depth: discovery (W5): a new generator, a new schema and
money figures.

Companion files: `reviewer-guide.md` (rev 2), `rulings.md` (D-DS1.1 to D-DS1.14, and the round-1 answers to R1-R25 and
P1-P16), `handshake.md`.

Sources:
- owner:
  - "A, start DS1 now" (`owner/owner-start-ds1-2026-11-20.md`);
  - U9 and strategy Q1, Q2 and Q7 (`owner/owner-answers-uiux-datastrat-d7-2026-11-20.md`);
  - "merge wave 2c, and defaults for DS1" (`owner/owner-merge-wave2c-ds1-defaults-2026-11-20.md`);
- data and build strategy §3, §6, §8, §9 and Appendix F (branch `task/data-build-strategy`);
- UI/UX guide Appendix A2 (`Docs/design-system/uiux-guide.md`);
- the pack on `task/pack-recreate-integrate` at `46b62c92b` or later: rev 16.13, the empty-state record
  (the design Architect's empty-state ruling, pack commit `46b62c92b`), `Docs/demo-sprint/product-direction-layer4/`, written `P/` below. Tag
  `pack-freeze-2026-11-19` is never moved or edited.

`USER_REVIEW_REQUIRED: true` (new figures on the Portfolio overview; the owner sees them at the walkthrough).

## 0. Before you start

1. Stay off ports 5490 and 8990, Docker and every database. DS1 needs **no database**.
2. Python: `PYTHONPATH=simulator:contracts /opt/assetecon/AssetOpsV1/.venv/bin/python` from the worktree root, written
   `PY` below. The venv's editable install otherwise imports `main`'s simulator (P10).
3. Every command that starts a browser goes through `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh -- <command>` (§9.4).
   Pure-Python tests and the pack scripts run directly. No full suites.
4. Three tasks, three branches (§3). Each ends with a commit, a packet in this folder (`packet-DS1a.md`,
   `packet-DS1p.md` or `packet-DS1m.md`) and the count of mid-build questions.
5. W2 order: in each task, commit the tests or checks first and show them failing in the packet.

## 1. What exists, and what DS1 adds

**Exists, and stays.**
- The pack's world is one month, October 2026. `P/demo-site-scenario-manifest.yaml` holds each Site's October `period`
  (plan, actual, coverage, bridge) as declared inputs, and (rev 16.13) `empty_states:`, the record behind every empty
  leaf.
- `P/evaluate_structure.py` evaluates every node bottom-up and writes `P/derived-values.json` and
  `P/missing-records.json`. `P/independent_model.py` recomputes the figures with no shared code, and
  `P/check_manifest.py` compares the two.
- The mock-up embeds the figures through `interactive-mockup-vNEXT/tools/gen_fixtures.py`.
- The ledger span 2026-07 to 2026-10 is declared (`time_scales.ledger_history`) but empty, so every trend slot honestly
  says "Trend not available yet".

**DS1 adds**, without changing any October input or figure:
1. A generator core in tested repo code: the view without private expectations, scope digests, seeds by scope, exact
   allocation, a canonical writer and golden digests.
2. Three history months for the nine Sites, generated from declared rules into `P/history.json`.
3. Those months evaluated through the same structures, as `derived-values.json` key `history`. The mock-up's
   `uxHistory` already reads it. Every node DS1 cannot know carries its `missing` record; none reads as zero (R7).

*Serves the objective:* an executive sees whether a gap is new or has been building, which a single month cannot show.
Every point is computed the way October is, from inputs labelled *Simulated*.

## 2. Rulings on the five questions (reasons in `rulings.md`)

1. **`2a` is not built** (D-DS1.1). DS1 works at month grain, with no dependency on it. The record and envelope writers
   are DS1b (1 unit, after `2a`). `world/leaves.py` is the single mapping point for `2a`'s IDs.
2. **Code home** (D-DS1.2): `simulator/assetops_simulator/world/`, not `assetops_backend`.
3. **Branches** (D-DS1.3, rev 2): see §3.
4. **Realism**: §5 and §6.
5. **After-recalculation figures** belong to `3B7b` (D-DS1.9). The `rolling:` record is the Thika invoice of 96.00,
   received 09:40; the request time is 10:00 story time.

From the audit:
- The series runs July to October.
- Sites are keyed by manifest name.
- The Site tiles are UI-lane work (D5, §9.3).
- The product series read is `3B7a`.
- History nodes carry the rev 16.13 `missing` record (D-DS1.12).

## 3. Tasks, branches, bases and order (D-DS1.3, rev 2)

| Task | Branch | Base | Files it may touch | Units |
| --- | --- | --- | --- | ---: |
| **DS1a** generator core | `task/DS1a-world-generator` | `main` (`d58c6d2e1` or later) | `simulator/assetops_simulator/world/**`, `simulator/tests/world/**`, `tools/world_history.py`, `.gitattributes`, this folder's packet | 1.5 |
| **DS1p** pack history | `task/DS1-pack-history` | `task/pack-recreate-integrate` head (`46b62c92b` or later), then `git merge main` before the first commit | `P/demo-site-scenario-manifest.yaml` (append `history:` only), `P/history.json` (new), `P/evaluate_structure.py`, `P/independent_model.py`, `P/check_manifest.py`, `P/derived-values.json` (regenerated), `.gitattributes`, packet | 2 |
| **DS1m** mock-up | `task/DS1-mockup-trends` | `main` after the pack branch (with DS1p) merges to `main` | `interactive-mockup-vNEXT/fixtures.js`, `index.html` (regenerated), `tools/ux_interaction_check.cjs` (one assertion, R20), the gate outputs, `.agent/mock-departure-register.md` (one row), packet | 0.5 |

**Why DS1p sits on the pack branch.**
- `46b62c92b` edits the manifest, the evaluator and `check_manifest.py`, the same three files as DS1p. Its `empty_states`
  block is also an input DS1p needs (§8.1 step 4).
- Building on it avoids a three-way conflict later. DS1p's hunks are disjoint from it:
  - the manifest append goes after `checks:`;
  - `observe_side` sits in the M2 loop, which `46b62c92b` did not touch;
  - the history checks are a new function.
- The `merge main` brings `main`'s two check fixes (`7e53f2ede`, `d58c6d2e1`), so a fresh worktree starts green.
- DS1p merges into `task/pack-recreate-integrate`.

**Consequence, stated plainly.** The trend reaches the mock-up on `main` only when the pack branch merges to `main`, and
that merge waits on the owner's pack review. DS1a and DS1p do not wait on it.

**Order.**
1. DS1a: build, review, merge to `main`.
2. DS1p: start when DS1a's tests pass (no merge needed). Produce `history.json` with the DS1a worktree's
   `tools/world_history.py`.
3. DS1m: after the pack merge.

**Generated files.** A generated file is never hand-merged: on a conflict, take either side and regenerate.
`fixtures.js` and `index.html` are rebuilt by the branch that merges last.

**`task/data-build-strategy`.** It gets the amendment text in D-DS1.1, from the coordinator.

## 4. The generator core (DS1a)

### 4.1 Package layout

`simulator/assetops_simulator/world/` uses the standard library only. It has no `float`, no randomness, no clock and no
environment reads.

| Module | Holds |
| --- | --- |
| `view.py` | `ManifestView.from_document(doc)`, `view_digest(view)` (§4.2) |
| `canonical.py` | `canonical_bytes(obj)`, `sha256_hex(b)`, `file_bytes(obj)`, `write_canonical_file(obj, path)` (§4.5) |
| `scope.py` | `scope_input`, `scope_digest`, `seed`, `unit_interval` (§4.3) |
| `allocate.py` | `allocate(total, weights)`, `split_to_days(total, days, weight)` (§4.4) |
| `leaves.py` | `MONEY_LEAVES`; the single mapping point for `2a` |
| `months.py` | `days_in(month)`, `period_end(month)`, `day_class(date, day_classes)`, `MONTH_ABBR` (a literal table, `"07": "Jul"` … `"10": "Oct"`; never `strftime`) |
| `history.py` | `generate_scope(view, tenant, site, month, *, jitter=True) -> dict` and `generate_history(view) -> dict` (§6) |
| `__init__.py` | `GENERATOR = "assetops_simulator.world/1"` |

**`tools/world_history.py`** is the only YAML reader. It starts with
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simulator"))`. Its `--manifest` argument takes a `.yaml`
manifest, or a `.json` view (chosen by suffix; `from_document` is idempotent on a view). Commands:
- `view --manifest M --out F` writes the view's file bytes.
- `generate --manifest M --out H` writes the history file.
- `check --manifest M --history H` exits 0 on identical bytes. Otherwise it prints `DS1_CHECK_DIFF <scope_key>` for the
  first differing scope (or `DS1_CHECK_DIFF meta`) and exits 1.

### 4.2 The view without private expectations (Appendix F, row 1)

`ManifestView.from_document(doc)` builds a new dict by **allowlist**:
- top level: `manifest_version`, `as_of`, `accounting_period`, `currency`, `timezone_default`, `history`;
- per tenant (list order kept): `tenant`, `vertical`, `prices`, `energy_model`, `capacity_crates_per_room`, `sites`;
- per Site: `site`, `code`, `physical`, `tariff`, and `period` reduced to `plan`, `actual` and `coverage`.

Rules:
- **Absent keys are omitted**, never written as `null` (P3).
- **Floats become decimal strings** with `repr(x)` (`3420.0` becomes `"3420.0"`, `0.25` becomes `"0.25"`). An `int`
  stays an `int`. A `str` stays a `str`. A `bool`, a `date` or any other type is refused with
  `ValueError("VIEW_TYPE <path>")` (P2).
- Numeric reads in the engine go through `Fraction(Decimal(str(x)))`, never `Fraction(x)` on a float.
- The private block's name, case-insensitive, appears nowhere in `world/**` or `tools/world_history.py`, including
  comments and docstrings. Call the view "the view" in code (T3b).
- `view_digest = sha256_hex(canonical_bytes(view))`.

### 4.3 Scope digests and seeds (R11)

- `scope_key = "<tenant>/<site>/<month>"`.
- `scope_input` is:
  `{"generator", "month", "history_global": {months, anchor_period, seasons, day_classes, families, money_leaves},
  "rules": <the merged rules for this Site, §6.1>, "tenant": {tenant, vertical, energy_model?, capacity_crates_per_room?},
  "site": {site, code, physical?, period}}`.
  - `?` means omitted when absent.
  - Prices and tariffs are **not** inputs: no rule reads them, so a price change re-seeds nothing.
- `scope_digest = sha256_hex(canonical_bytes(scope_input))`.
- `seed(scope_digest, scope_key, stream) = sha256_hex(f"{scope_digest}|{scope_key}|{stream}".encode())`; the stream is
  the family name.
- `unit_interval(h) = Fraction(int(h[:8], 16) % 2001 - 1000, 1000)`.

### 4.4 Exact allocation; units (R9)

- Arithmetic is in `Fraction`. Each leaf is rounded once, with `ROUND_HALF_EVEN`:
  - a quantity leaf to an integer unit (kWh, L, crate-days, kW);
  - a money leaf to integer cents.
- Inside the engine, `H[x]` holds the rounded values (money in cents). Money from `O[x]` is multiplied by 100 before
  rounding.
- **Units, and the strategy's text.** Month-grain quantities are integer units. Integer milli-units start with DS2's day
  split, which divides these totals. The history's month leaves are generated by declared rule, because no constraint
  for them exists in the manifest. The strategy's "the generator never invents a total" holds for manifest-fixed figures.
  The D-DS1.1 amendment says so.
- **`allocate(total: int, weights: list[Fraction]) -> list[int]`**, largest remainder:
  1. Refuse `ValueError("ALLOCATE_BAD_INPUT")` if `total < 0`, any weight is negative, or the weights sum to 0.
  2. `part_i = floor(total * w_i / Σw)`.
  3. Give the leftover units one each, by the largest remainder; ties go to the lower index.
- **`split_to_days(total: int, days: list[date], weight: Callable[[date], Fraction]) -> list[int]`** is `allocate` over
  `days` in the order given. It is not used by the history; it is tested for DS2 and DS3.
- `leaves.MONEY_LEAVES = frozenset({energy_cost, in_transit, liability, maint, maintenance, om, outstanding, staff,
  total})`. It must equal `history.money_leaves`, or the engine refuses with `HISTORY_MONEY_LEAVES`.

### 4.5 Canonical bytes, the file, golden digests, the fixture

- `canonical_bytes(obj) = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`.
  It raises `TypeError("CANONICAL_FLOAT")` on any float anywhere in `obj`.
- `file_bytes(obj) = (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=1) + "\n").encode("utf-8")`.
- `simulator/tests/world/golden/history_v1.json`:
  `{"file_sha256", "view_digest", "scopes": {scope_key: sha256_hex(canonical_bytes(block))}}`.
  - It is rewritten only under `--update-golden`, an option in `simulator/tests/world/conftest.py`. Tests read it with
    `request.config.getoption("--update-golden", default=False)`.
  - The commit names the changed input.
- `simulator/tests/world/fixtures/view_v1.json` is the `view` output of a **scratch copy** of the manifest at DS1p's
  base commit, with §5 appended byte for byte (P9). The packet names that commit.
  - DS1p appends the same bytes, so `history.json` has the same `view_digest`, and its SHA-256 equals
    `golden.file_sha256`.
- `.gitattributes` (DS1a): `simulator/tests/world/**/*.json text eol=lf` (R24).

### 4.6 Generation flow

`generate_history(view)`:
1. **Validate** `history`:
   - months: **exactly three** (the lists are read by position; review L3), consecutive calendar months; each day count equals the calendar's; `anchor_period` is the month after the
     last; the anchor is not in the set. Iterate in sorted order (R22). Refusal: `HISTORY_MONTHS`.
   - families and the rule grammar (§6.1);
   - every `sites:` override key names a real tenant and Site (`HISTORY_RULE_UNKNOWN`);
   - `money_leaves` (§4.4).
2. **For each tenant and Site** in view order, and each month in sorted order, call
   `generate_scope(view, tenant, site, month)`. It returns:
   `{"scope_digest", "period_days", "period_end", "plan": {…}, "actual": {…}, "coverage": {each key of October's
   coverage: "RECORDED"}}`.
3. **Assemble** §7.1.

`generate_scope` runs the same validation as `generate_history` (so it never raises a bare `KeyError`), except month-set
membership: it does not check that the month belongs to the set. T9 uses that to generate `2026-10`, with
`jitter=False`.

## 5. The `history:` block (DS1p appends it verbatim; DS1a's fixture uses the same bytes)

The weights and trends are the owner-decided defaults (Q1, Q2), except two changes from round 1:
- the mini-grid `generator` season weights, retuned so October's rainy month needs the most generator fuel (R10);
- Embakasi's `max_kw`, which uses the new length-free `level` rule (P5).

```yaml
history:   # U9 (owner, 20 Nov): July-September 2026 history of the three demo operators. GENERATOR INPUTS ONLY: seasons,
           # day classes, family weights and per-leaf rules. Leaf values are generated by assetops_simulator.world into
           # history.json; every node, total and series is evaluated by evaluate_structure.py (D-DS1.4). Every history
           # leaf is Simulated (D-DS1.10). A leaf outside the generated scope is MISSING with cause NOT_IN_HISTORY (D-DS1.12).
  version: 1
  months: {"2026-07": 31, "2026-08": 31, "2026-09": 30}
  anchor_period: "2026-10"
  shape_source: synthetic
  money_leaves: [energy_cost, in_transit, liability, maint, maintenance, om, outstanding, staff, total]
  label: {provenance: demo-simulated, evidence: Simulated}
  missing_cause: NOT_IN_HISTORY   # the record behind a history leaf DS1 does not generate (rev 16.13 vocabulary plus this one value)
  seasons: {"2026-07": cool_dry, "2026-08": cool_dry, "2026-09": warm_dry, "2026-10": short_rains}
  day_classes: {WD: [1, 2, 3, 4, 5], SA: [6], SU: [7]}   # ISO weekday
  families:   # day weight = season x day class; jitter = amplitude of the seeded month factor
    demand:        {season: {cool_dry: "0.96", warm_dry: "1.00", short_rains: "1.00"}, day: {WD: "1.00", SA: "0.97", SU: "0.90"}, jitter: "0.02"}
    generator:     {season: {cool_dry: "0.98", warm_dry: "0.93", short_rains: "1.00"}, day: {WD: "1.00", SA: "0.97", SU: "0.90"}, jitter: "0.02"}   # October's short rains need the most generator fuel
    solar_surplus: {season: {cool_dry: "0.80", warm_dry: "1.10", short_rains: "1.00"}, day: {WD: "1.00", SA: "1.00", SU: "1.00"}, jitter: "0.06"}
    cooling:       {season: {cool_dry: "0.97", warm_dry: "1.02", short_rains: "1.00"}, day: {WD: "1.00", SA: "1.00", SU: "1.00"}, jitter: "0.01"}
    flat:          {season: {cool_dry: "1", warm_dry: "1", short_rains: "1"}, day: {WD: "1", SA: "1", SU: "1"}, jitter: "0"}
  rules:   # keyed by the tenant's own `vertical`; per side: leaf -> rule (spec §6.1)
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
    EV_DEPOT:
      plan:   {kwh: per_day, peak_kwh: share kwh anchor anchor anchor, offpeak_kwh: rest kwh peak_kwh, max_kw: fixed, maintenance: fixed}
      actual: {kwh: fleet_kwh, peak_kwh: share kwh anchor anchor anchor, offpeak_kwh: rest kwh peak_kwh,
               kwh_2200_2400: share offpeak_kwh anchor anchor anchor, kwh_0000_0500: rest offpeak_kwh kwh_2200_2400,
               max_kw: fixed, maintenance: plan_value}
  sites:   # per-Site overrides, merged by side into the vertical table (the override wins and may add keys)
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
      actual: {peak_kwh: share kwh 0.36 0.43 0.49, max_kw: level flat 0.92 0.95 0.98}        # peak charging creeping toward October's 0.55
```

## 6. The rule engine

### 6.1 Grammar and semantics

**Notation.**
- A rule is space-separated tokens. Numbers are decimal text, read as `Fraction`.
- Three-value lists are Jul, Aug, Sep.
- `O[x]` is October's value of `x` on the same side. `H[x]` is the history value already generated in this scope and
  side.
- `d` is the month's days and `d₀ = days_in(anchor_period)`. The literal 31 never appears (R25a).

**Rules.**

| Rule | Value | Unit |
| --- | --- | --- |
| `per_day` | `O[leaf] * d / d₀` | leaf's |
| `fixed` | `O[leaf]` | leaf's |
| `plan_value` | October **plan** value of the leaf; `HISTORY_NO_PLAN_VALUE` if absent | leaf's |
| `zero` | `0` | leaf's |
| `scale f` | `O[leaf] * R(f)` (volume) | leaf's |
| `trend f a b c` | `O[leaf] * a * R(f)` (volume) | leaf's |
| `level f a b c` | `O[leaf] * a * S(f)` (an intensive leaf: a peak or a rate) | leaf's |
| `occupancy a b c` | `o * capacity_crates_per_room * d`; `o` is a, or for `anchor` `O[crate_days] / (capacity_crates_per_room * d₀)`; `HISTORY_BOUND` if `o > 1` | integer |
| `cold_kwh f a b c` | numeric `e`: `(base_kwh + k_kwh_per_crate_day * H[crate_days]) * e`, so the excess ratio is exactly `e - 1` (R10); `anchor`: `(…) * e₀ * S(f)`, where `e₀ = O[kwh] / (base_kwh + k_kwh_per_crate_day * O[crate_days])` | integer |
| `ratio x` | `O[leaf] * H[x] / O[x]` | leaf's |
| `share x a b c` | `allocate(H[x], [s, 1 - s])[0]`; `s` is a, or for `anchor` `O[leaf] / O[x]` | integer |
| `rest x y` | `H[x] - H[y]` | integer |
| `sum x y` | `H[x] + H[y]` | money (cents) |
| `fleet_kwh` | `physical.buses * physical.kwh_per_bus_night * d` | integer |
| `fleet_nights` | `physical.buses * d` | integer |

**Which rules carry season and jitter (R5).**
- `R(f)`: `scale` and `trend` only. `S(f)`: `level`, and `cold_kwh … anchor`.
- All other rules have no season and no jitter. So EV kWh follow the fixed fleet exactly, and Embakasi's gap moves only
  through peak share and `max_kw`.
- The `cold_kwh` model term keeps the manifest's monthly `base_kwh` unscaled (`form: kWh_month = 1550 + 0.25 x
  crate_days`). Changing that form is an energy-model change, not DS1's.

**Merging and generation.**
- **Rules** = the vertical table for the tenant's `vertical`, merged by side with the Site's override. A missing
  vertical table is refused with `HISTORY_RULE_UNKNOWN`.
- **Generated leaves** = keys of October's side that have a merged rule. Other October keys (totals, `peak_share`,
  `occupancy_pct`, `note`, and factor-map fallbacks such as `billed_kwh` or `diesel_l` on a mini-grid actual) are not
  written.
- **Order**: a rule naming another leaf runs after it; otherwise leaves run in sorted key order.

**Refusals.** All are `ValueError("<CODE> <scope_key> <leaf>")`:
- `HISTORY_RULE_UNKNOWN`: an unknown rule word, a missing vertical table, or an override for an unknown Site;
- `HISTORY_RULE_ARITY`: the wrong token count;
- `HISTORY_RULE_REF`: a rule names a leaf this side does not generate (R13);
- `HISTORY_RULE_CYCLE`;
- `HISTORY_FAMILY_UNKNOWN`;
- `HISTORY_BOUND`: a negative leaf, or occupancy over 1;
- `HISTORY_ANCHOR_ZERO`: a zero denominator in any `anchor`, `ratio`, `W(f, anchor)` or capacity (R3);
- `HISTORY_MONTHS`;
- `HISTORY_MONEY_LEAVES`;
- `HISTORY_NO_PLAN_VALUE`;
- `HISTORY_FIELD history <field>`: a required `history` field is absent, or the `history` block itself
  (`HISTORY_FIELD history history`) (review L4; fix-round item 3);
- `HISTORY_NUMBER <scope_key|history> <field>`: a number that is not a finite decimal (NaN, Infinity, or text that is not
  a decimal) (review L4), or one whose `Decimal` `adjusted()` exponent is outside [-12, 12] or whose text exceeds 32
  characters, checked before any `Fraction` conversion (fix-round item 4).

An **absent** input value (`energy_model`, `physical`, room capacity, an October leaf an `anchor` names) is
`HISTORY_RULE_REF`. `HISTORY_ANCHOR_ZERO` is only for a value that is present and zero.

Refusals found before any scope, refusals that match no listed defect, and lists read for a month outside the set:
see `rulings.md` "Mid-build answers" (MB1, MB2). Those texts are part of the spec.

### 6.2 Seasonality from day types (P5)

- `W(f, m) = Σ over m's dates of season_f[seasons[m]] * day_f[day_class(date)]`.
- `J(f) = 1 + jitter_f * unit_interval(seed(scope_digest, scope_key, f))`.
- **`R(f) = W(f, m) / W(f, anchor) * J(f)`**: a volume, which carries the month's length.
- **`S(f) = (W(f, m) / d) / (W(f, anchor) / d₀) * J(f)`**: a shape, free of the month's length.
- With `jitter=False`, `J = 1`. October then reproduces itself (T9).

### 6.3 What the history may show, and what it may not (D-DS1.7, rev 2)

**May show:**
- seasonal, weekday and seeded variation;
- the declared trends;
- chronic patterns at October's rate. Kobo's generator running after dawn is present from July, consistent with the Sep 29
  verification baseline.

**May not show**, each enforced:
- **No October-dated incident** (Kisiwa 30 Oct, Mto 28 Oct and 3 Oct, Mto's late settlement, Thika 6 Oct, Ruiru 6 Oct).
  These are `zero` rules (enforced by check H2), and the view drops observations, incidents and entitlements.
- **No unknown read as zero** (R7, D-DS1.12):
  - a leaf whose own record October takes from `observations.october`, and which DS1 does not generate, is **missing**
    with cause `NOT_IN_HISTORY`, never 0. Examples: `major_assets`, `field_visits`, `reduced_days`,
    `cooling_minutes_unavailable`, `excursion_*`, `backup_unproven_days`, `charger_out_days`;
  - every node resting on such a leaf is left out of `periods.nodes` and listed in `missing.blocks` (checks H4 and H11).
    These are the Protect and O2 measures; no outcome rests on them;
  - if an outcome node would be blocked, the evaluator refuses with `HISTORY_OUTCOME_UNOBSERVED`.
- **No missing invoice.** Coverage is all `RECORDED`. October's late invoices carry the plan value as a received record
  (`plan_value`).
- **No residual above tolerance**: mini-grid `unexplained_l` is at most 2% of the evaluated `diesel_l` node (check H5).
- **No bridge rows** (D-DS1.6, owner-decided).
- **No Finding, option, decision, plan item, Action or right.** The evaluator runs M2 only on history. A drift that would
  meet a Finding's condition, such as Kirinyaga above 5% from August, is a trend point only (Q3).
- **Prices and tariffs are October's** (no price history is declared).

## 7. The history file `P/history.json` (D-DS1.5)

### 7.1 Schema `assetops.history/1`

```json
{
 "meta": {"schema": "assetops.history/1", "generator": "assetops_simulator.world/1", "shape_source": "synthetic",
          "view_digest": "<sha256>", "anchor_period": "2026-10", "months": ["2026-07", "2026-08", "2026-09"],
          "money_unit": "cents", "money_leaves": ["energy_cost", "…sorted…"],
          "label": {"provenance": "demo-simulated", "evidence": "Simulated"}, "missing_cause": "NOT_IN_HISTORY"},
 "tenants": {"<tenant>": {"<manifest site name>": {"2026-07": {
     "scope_digest": "<sha256>", "period_days": 31, "period_end": "2026-07-31",
     "plan": {"<leaf>": 0}, "actual": {"<leaf>": 0}, "coverage": {"<line>": "RECORDED"}}}}}
}
```

- Every value is an `int` or a `str`. Money is in cents.
- `period_end` is an ISO date string.
- The file sits beside the manifest. `.gitattributes` (DS1p): `Docs/demo-sprint/product-direction-layer4/history.json
  text eol=lf` and the same for the manifest.

### 7.2 Labels (D-DS1.10, rev 2: R8 accepted)

- **Every history leaf and series is *Simulated*** (`demo-simulated`). A rule-generated month total is not a record
  from a source, so *Emulated* is not true of it. *Emulated* arrives with DS1b's source-shaped records.
- *Recorded* is never an evidence word.
- `RECORDED` in `coverage` is the coverage state "the record exists", as in October, not an evidence class.

## 8. The pack (DS1p)

### 8.1 `P/evaluate_structure.py`

1. **`observe_side(S, FM, vert, t, s_, record, obs, incident, entitlement, period_days, period_end, as_of) -> (result,
   ctx, factors)`** is the M2 per-side `try` block, unchanged in logic (P6, R2).
   - October passes `s_.get("incident", {})`, `s_.get("entitlement", {})` and today's other values.
   - The `k == "actual"` assignments (`site_ctx`, `site_struct`, `site_base`, `site_vert`, `site_tenant`, `_rights`)
     stay in the October loop.
2. **`load_history(path) -> dict | None`** reads `history.json` beside the manifest and returns `None` if absent.
   - Money leaves become `Decimal(cents) / 100`.
   - It refuses with `HISTORY_STALE` if `meta.anchor_period != doc["accounting_period"]`, or if the tenant and Site set
     differs from the manifest's.
3. **`evaluate_history(doc, hist, out) -> dict`** runs M2 only. For each Site, month and side it calls `observe_side`
   with:
   - `obs = {}`, `incident = {}`, `entitlement = {}`;
   - the block's `period_days` and `period_end`;
   - `as_of = doc["as_of"]`;
   - the Site's `factor_sources`.

   Every date leaf resolves against the block's `period_end` (R6). A side whose status differs from October's, or a
   stated total of `None`, is refused with `HISTORY_NOT_EVALUATED <scope>` (R2).
4. **`missing`, per side** (D-DS1.12): a list of entries in the rev 16.13 shape, `{leaf, record_kind, source_family,
   cause, carried_as, blocks[]}`, built from `empty_states.leaf_sources`:
   - **(a)** For each factor-map leaf whose leftmost alternative names a key that October's actual takes from
     `observations.october`: `cause = history.missing_cause`, `carried_as = null`, and `blocks` = `ancestors(S[vert],
     [leaf])` (the rev 16.13 helper).
   - **(b)** Every other entry `missing_records()` would give for an observed side, applied to the history record.
     Refactor its per-side part into a helper both call. `missing-records.json` stays byte-identical.
   - Nodes named in any (a) entry's `blocks` are removed from `periods.<side>.nodes` and listed under `"not_observed"`
     (sorted).
   - If `contribution` or `cost_to_serve` would be removed: refuse with `HISTORY_OUTCOME_UNOBSERVED`.
5. **Output**: in `__main__` only. After `main(path)` and before writing, set `res["history"] = evaluate_history(...)`
   when the file exists. `main()` and the variants' recursion do not change.

```json
"history": {"<tenant>": {
  "kind": "contribution | cost", "evidence": "Simulated",
  "months": ["2026-07", "2026-08", "2026-09", "2026-10"],
  "portfolio": {"<kind>": [{"m": "Jul", "p": "2026-07", "v": 0.0}, "…4"], "gap": ["…4"]},
  "sites": {"<manifest site name>": {"<kind>": ["…4"], "gap": ["…4"],
            "periods": {"2026-07": {"plan": {"status": "evaluated", "nodes": {}, "not_observed": [], "missing": []},
                                    "actual": {"…": "same keys"}}}}}}}
```

- `kind` is `cost` iff `chain_model[mapped vertical].revenue == "NOT_APPLICABLE"`.
- The `<kind>` series is the **actual** side's outcome (P12): `nodes.contribution` or `nodes.cost_to_serve`, or else
  `stated_total`.
- `gap` is actual minus plan for contribution, and plan minus actual for cost.
- The October point is copied from `out["sites"]`. Portfolio points are Decimal sums.
- `m` comes from `MONTH_ABBR`, never `strftime` (R25b). `v` is `money()`.

### 8.2 `P/independent_model.py` (R12, R16)

`compute_history(manifest_path) -> dict` is separate from `compute()`. It:
- reads `history.json` and converts cents to Decimal itself;
- evaluates each Site, side and month with its own `side_records`/`base_ctx`/`eval_leaves` path, with `period_days` and
  `period_end` from the block and `incident`, `entitlement` and `observations` absent;
- returns status, outcome and the evaluable nodes, plus its own list of not-observed nodes, computed by walking its own
  structure parse from the leaves fed by observations;
- returns Site and portfolio series, October included, computed from its own October sides.

It shares no code with the evaluator.

### 8.3 `P/check_manifest.py`: checks H1-H11 (renamed from P1-P10 to avoid clashing with the pre-flight's numbers)

They run when `history.json` exists, in one function `history_checks(doc, dv, root)`, after the existing checks. Only
these checks consume `compute_history`. `documents()` excludes `doc["history"]` from its walk.

| ID | Check |
| --- | --- |
| H1 | `period_days` and `period_end` are the calendar's |
| H2 | Leaf sets: for an evaluated October side, history keys == the **first-present** `record.*` alternative of each factor-map leaf, among the keys of October's `period` side (observations excluded) (P1); for a non-decomposed side, history keys == October keys. Status equals October's. Every `zero`-rule incident leaf is 0 |
| H3 | Independent == evaluator for every Site, side and month: status, outcome, and every node both list |
| H4 | Not observed: the evaluator's `not_observed` per side equals the independent model's; no such node appears in `nodes`; each has a `missing` entry with cause `NOT_IN_HISTORY` naming it in `blocks` |
| H5 | Mini-grid `unexplained_l <= 0.02 * nodes.diesel_l`. Cold, for `anchor` kWh rules: `abs(kwh - kwh_model) <= 0.05 * kwh_model`. Cold: `crate_days <= capacity * period_days`. EV: `buses_short_per_night == 0` |
| H6 | Series: every Site point (October included) and every portfolio sum equals the independent model's; each portfolio point is the Σ of its Sites; `gap` follows its rule (R16) |
| H7 | Labels: every `evidence` value in `history.json` and `derived["history"]` is `Simulated`; no value anywhere equals `Recorded`; coverage values are all `RECORDED` |
| H8 | October unchanged: `derived-values.json` minus `history`, dumped as the evaluator dumps, has the SHA-256 of the base commit's file (the constant is recorded in the check), and `missing-records.json` is byte-identical to the base's. Lifetime: the next slice that changes October replaces the constants in its own diff (R14) |
| H9 | Baseline: the run prints `N checks passed (H history checks)` and 0 failed; N − H equals the baseline count in DS1p's packet, taken in place on its base after `merge main` |
| H10 | Manifest: the SHA-256 of the bytes before the line `history:` equals the base manifest's SHA-256, and the rest parses to exactly one top-level key, `history`. Same lifetime rule as H8 |
| H11 | Freshness (R15): an independent 20-line re-implementation of §4.2 (allowlist, float `repr`, canonical bytes) recomputes `view_digest` from the manifest and equals `meta.view_digest`. A manifest edit without regenerating fails here |

Each check is shown to fail on a planted case in the packet (W2; R25c order: `compute_history` and H1-H11 committed
before `evaluate_history`).

## 9. The mock-up (DS1m)

### 9.1 Regenerate

From `interactive-mockup-vNEXT/`, run `python3 tools/gen_fixtures.py` and then `node build.mjs`. Then run
`git diff --exit-code -- ../derived-values.json ../history.json ../missing-records.json`. It must exit 0, because DS1m
changes no pack output (R17).

### 9.2 Expected change, citing the mock

- Portfolio overview: KPI tile 1 (in `uxOverview`, "Contribution", or "Charging and depot cost" for Metro Bus) and tile 2
  ("Gap to target") show the 64×16 sparkline of Jul to Oct and "<change> against Sep".
- This holds for all three operators. No screen code changes. Re-resolve the call sites by function name (`uxOverview`,
  `uxHistory`) and record the head used (P15).
- The period menu keeps "September 2026: not available yet" (R21). Choosing September *as the period* is still not
  available; the packet says so. No register row.

### 9.3 `MOCK DEVIATION D5` (temporary, build order)

The Site page KPI tiles keep "Trend not available yet" (`uxTrendNA()` without arguments) while
`DERIVED.history[t].sites` holds their series. The resolving unit is the UI lane's Site trend wiring. Add one row to
`.agent/mock-departure-register.md`.

### 9.4 Gates (R18, R19, R20; coordinator ruling on browser tools)

Every browser-driven command runs through the slot. From `interactive-mockup-vNEXT/`, with
`/opt/assetecon/tools/pw/env.sh` sourced and `HS=/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh`:

| Gate | Command | Pass |
| --- | --- | --- |
| G1 | `node tools/vocab_check.cjs`, `node tools/plan_switch_check.cjs`, `node tools/render_text.cjs`, `node tools/copy_check.cjs` (jsdom, run directly); `$HS -- node tools/ux_interaction_check.cjs` | 0 hits |
| G1+ | R20, added to `ux_interaction_check.cjs` (gate tooling, not screen code). For each operator: exactly two `.ux-overview svg.ux-spark`, text matching `/against Sep/`, and the last point of each series equals the tile's headline (`T.actual`, `T.variance`) | passes; fails with `DERIVED.history` deleted (planted) |
| G2 | `$HS -- node tools/design_lint.cjs` | 0 hits |
| G3 | `$HS -- tools/run-audit.sh --shots`, if its state list covers the 18 states below; otherwise `$HS -- node /opt/assetecon/tools/pw/shot.cjs` per state. Output to `/opt/assetecon/evidence/DS1/<run>/` | below |

**G3 states**: route `#/portfolio` for `lakeside`, `harvest` and `metro` (the operator selected as the mock-up selects
it, `sessionStorage l4-op`), at 1280×720, 1440×900 and 390×844, light and dark (the mock-up's own theme attribute; the
packet names it).

**G3 pass, per shot:**
- page errors are 0;
- each `.ux-kpi .ux-trend` on the overview is visible and not clipped by its tile;
- at 1280×720 and 1440×900 it is inside the first viewport;
- at 390×844, "not clipped" only.

`tools/layout-evidence.mjs` (product frontend) does not apply; G3 is DS1m's layout evidence.

## 10. Tests and commands

**DS1a**: `PY -m pytest simulator/tests/world -q`. Tests come first. No test imports engine internals to compute an
expected value.

| ID | Test |
| --- | --- |
| T1 | Determinism: `generate` in two processes, from two working directories, with `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`; identical bytes |
| T2 | Golden: per-scope and file digests match; a mismatch names every scope |
| T3 | Private block: (a) the fixture view plus a top-level private block, `checks:`, a private key inside a Site, and changed `bridge`, `variance`, `fuel_balance`, `coverage_note` and `energy_per_crate_day` keys in a period, each holding values that would change figures if read: identical output (R4). (b) Case-insensitive grep for the private block's name in `world/**` and `tools/world_history.py` finds nothing. (c) Each view key set == allowlist ∩ the source's keys; no other key |
| T4 | Scope isolation: change Mwea's July occupancy, and only Mwea's three blocks change. Change Kisiwa's diesel price, and nothing changes |
| T5 | Allocation: sum preserved; tie to the lower index; refusals; exhaustive over totals 0..50 with 1 to 4 weights in {0,1,2,3}; `split_to_days` over 31 days |
| T6 | No floats: the output holds only int/str/dict/list; `canonical_bytes` refuses a float; the view refuses a bool (`VIEW_TYPE`); greps in `world/**` find none of `\bfloat\(`, `^\s*(import|from)\s+(random|time|secrets)\b`, `\.(now|today|utcnow)\(`, `os\.environ|getenv` (R23) |
| T7 | Months: 31, 31, 30; period ends; day classes Jul 23/4/4, Aug 21/5/5, Sep 22/4/4, Oct 22/5/4 |
| T8 | Each refusal code in §6.1 raised by one planted case (one `HISTORY_ANCHOR_ZERO` case per rule), asserting the full text `<CODE> <scope> <leaf>`; also two months only, NaN, a missing `label`, `generate_scope` alone with no `jitter`; unknown leaf skipped |
| T9 | `generate_scope(…, "2026-10", jitter=False)` returns October's leaf for every `scale`, `trend 1`, `level 1` and `anchor` rule |
| T10 | CLI: `check` exits 0 on the generated file, and 1 with `DS1_CHECK_DIFF <scope>` after a one-byte change; `--manifest` accepts the `.json` fixture |

DS1a also runs fast check-all once at the end, through its own slot.

**DS1p**: `PY P/evaluate_structure.py && PY P/check_manifest.py` (0 failed; H1-H11 pass), and, from the DS1a worktree,
`PY tools/world_history.py check --manifest <DS1p>/P/demo-site-scenario-manifest.yaml --history <DS1p>/P/history.json`
exits 0.

**DS1m**: §9.

## 11. Decision queue: decided

The owner took every default, and D-DS1.6, on 20 Nov (`owner/owner-merge-wave2c-ds1-defaults-2026-11-20.md`).

| # | Question | Decided |
| --- | --- | --- |
| Q1 | Story trends (Mwea occupancy 56/49/42%; Kirinyaga energy +5/+10/+17%; Embakasi peak share 36/43/49%) | As in §5. Rev 2 makes the generated figures equal these: Kirinyaga's excess is exactly `e - 1` (R10), and Embakasi's `max_kw` is length-free (P5) |
| Q2 | Plans carry seasonality? | No: `per_day` |
| Q3 | "Since August" on October Findings? | No |
| Q4 | Evidence word on the trend tile? | Not in DS1 |
| Q5 | Thika invoice for `3B7b` | 96.00 against the 80.00 estimate; received 2026-11-06T09:40+03:00; recalculation requested 2026-11-06T10:00+03:00 story time (`UX_RECALC_TIME`) |

**New, for the design Architect** (default applied; it does not block DS1): the cause value `NOT_IN_HISTORY` extends the
rev 16.13 cause vocabulary. It is declared in `history.missing_cause`, and `empty_states` is not edited.

## 12. Scope limits

Not in DS1:
- the record and envelope writers (DS1b);
- day shapes and milli-units (`DS2`);
- any database (`DS3`);
- the snapshot store and its month-series read, whose node stores `missing` unchanged (`3B7a`);
- the after-recalculation state (`3B7b`);
- history bridges (`5c`);
- Site trend wiring (UI lane);
- the T1 inventory's browser-tool regex (a T1 follow-up, coordinator);
- `plan_model.py` (day-7 re-cut: DS1, DS1b, `3B7a`, `3B7b`).
