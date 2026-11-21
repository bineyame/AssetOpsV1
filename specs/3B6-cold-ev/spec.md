# 3B6: cold-room and captive-EV structures, declared and tested from the start (implementer spec)

Status: in_review (built 21 Nov on `task/3B6-cold-ev`, packet `packet.md`); rev 2 (handshake round 1 answered, `rulings.md` D-3B6.13 to D-3B6.24), Architect (Claude), 2026-11-21, written on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`; pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4; the
owner-level calls made here are logged there as rows 21, 22 and 26). `delivery-plan.md` §2 row `3B6`: "Cold-room and
captive-EV structures declared and tested from the start (revenue not applicable, never zero)" (step 3B, construct
B1, lane 2, 1.5 units, depends on `3B1`, page P3B, approved 20 Nov; non-screen). Build plan §0.2 day 10 to 11 (lane B
tail), §0.3 "Lands". **2.75 units** (1.25 over the plan: the Site-type map reaches six readers that assumed one structure, D-3B6.6, "not applicable" needs a declared mechanism, D-3B6.3, and the handshake added a shared-ID guard, a reader reorder and honest-record tests, D-3B6.17, D-3B6.18, D-3B6.24; no split). Discovery review (W5): two new
structures on the shared core and a change to how portfolio reads exclude a Site. Non-screen; adds no user-facing text
(D-SC1.28 does not hold it; D-3B6.12). `USER_REVIEW_REQUIRED: false`.

- **What it is.** The pack declares three outcome structures (`demo-site-scenario-manifest.yaml` `structures`,
  `factor_map`, `home_categories.nodes`, `empty_states.leaf_sources`). `3B1` built the mini-grid one as code rows;
  `3B3` evaluates it; `3B2` pins Findings to it. 3B6 declares the other two, `COLD_CHAIN` (a cold room: crate-days ×
  rate − cost to serve) and `EV_DEPOT_CAPTIVE` (a captive depot judged on cost per required departure met, revenue
  *not applicable*), as rows on the same records with **no vertical-specific code** in the evaluator, the check or the
  read. It makes cold-room and EV Sites readable through `StructureRead.site`, every leaf honest about its source
  (calendar figures computed; everything else "Not available yet" naming its record, never 0), declares that revenue does not apply to a captive depot (declared, checked and queryable; no read shows it until `3B5`, D-3B6.14), moves the three cold and EV Finding mechanisms from pending to pinned, and makes
  every reader that assumed one structure exclude a Site of another structure by name rather than drop it or crash.
- **Design source:** `structure-specification.md` §3 and §3.1 (leaves, nodes, portfolio composition, empty leaves);
  `layer4-transformation-design.md` §2 (line 375: "A captive EV depot is judged on cost per required departure met,
  with revenue *not applicable*, never zero"; line 252: Grow for a captive depot); manifest `chain_model.EV_DEPOT_CAPTIVE`
  (`revenue: NOT_APPLICABLE`), tenant `metro-bus` `business_model`; P3B ("`3B6` cold rooms and captive EV depots.
  Declared on the same core, with no vertical-specific code").
- **Gate question it answers** (`delivery-plan.md` §3 step 3B): "Does a captive EV depot show revenue as *not
  applicable*, never zero?" At the data level only (test 5a: a declared, checked, queryable fact, never a row or a 0); no read carries it, so the screen-level answer is `3B5`'s (D-3B6.14, owner row 26). And for step 6's later gate ("Does the same evaluator pass a cold-room and an EV fixture with
  no vertical code?") it supplies the fixtures: the pack's six cold and EV Sites evaluated to the cent (§5).
- **Owner rules kept:** unknown is never zero (every cold and EV leaf without a provider reads "Not available yet"
  naming its record); not applicable is not zero and not unknown (a third, declared state, D-3B6.3); one mechanism
  across verticals (W6, `fundamental-mechanics-first`); claim only what was tested.
- **Builds on (merged on `main` at `28263c47b`):** `2a` (`assetops_contracts/canonical/factors.py` `LEAF_FACTORS`,
  `leaves_of`, `STRUCTURE_KEYS`, `FACTOR_ID_PATTERN`; `units.py` `DAY`, `HOUR`, `KWH`, `KW`, `MINUTE`, `MONEY`, `ONE`),
  `3B1` (`structure/registry.py` `FactorRow`, `FilledBy`, `Home`, `Registry`, `HOMES`, `REGISTRIES`;
  `structure/check.py` `check`, `check_all`, `_CHECKS`, `CODES`, `StructureError`; `structure/rows_mini_grid.py` `_leaf`,
  `_node`), `3B2` (`structure/pins.py` `PINS`, `PENDING_PINS`, `DOMAIN_OF_STRUCTURE`, `parity`; `check.check_pins`),
  `3B3` (`structure/evaluate.py` `evaluate`, `compose`, `LeafValue`, `Missing`; `structure/read.py`
  `SITE_TYPE_TO_STRUCTURE`, `NOT_DECLARED`, `StructureRead.site`, `.portfolio`, `site_count`; `structure/sources.py`
  `SOURCE_STATE`, `ProductLeafSource.leaf`, `_period_days`), `4b` (`structure/money.py` `CommercialLeafSource.leaf`),
  `4d` (`structure/litres/source.py` `LitreLeafSource.leaf`), `5a` (`structure/targets/read.py` `TargetRead.site`,
  `.portfolio`; `targets/rules.py` `TARGET_RULE`), `5b` (`structure/attribution/read.py` `BridgeRead`), `3B7a`
  (`structure_snapshot/build.py` `SnapshotBuilder.build`, `structure_snapshot/read.py` `SnapshotRead.site`,
  `structure_snapshot/model.py`).
- **Not what the brief assumed.** The delivery plan says 1.5 units. Adding cold and EV to `SITE_TYPE_TO_STRUCTURE`
  changes six readers that filter Sites with `SITE_TYPE_TO_STRUCTURE.get(type) is None` while composing only
  `MINI_GRID`: left alone, a cold Site would vanish silently from every mini-grid portfolio read (neither composed nor
  excluded), and `TargetRead.site` would raise `KeyError`. That class is fixed here (D-3B6.6), not deferred.
- **Decisions:** `rulings.md` (D-3B6.1 to D-3B6.24). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question (round 1 answered in `rulings.md`; the reviewer and implementer
  confirm in `handshake.md`), and `4a` has merged (it edits `structure/registry.py`, `structure/check.py`,
  `structure/sources.py`, `structure/money.py` and the 3b1/3b3 tests, which 3B6 edits too; branch after it). If a lane
  is free before 4a merges, unit 1 may build **only** (D-3B6.19): `rows_cold_chain.py` and `rows_ev_depot.py`; the
  `not_applicable` field and `applicability` in `registry.py` (outside the `REGISTRIES` literal); `check.py` (§2.4);
  and tests 1, 2, 3 over `Registry` objects built from the row files and over test-local mappings. It does **not**
  touch the `REGISTRIES` literal, `pins.py` (a pin refuses at start-up without its registry entry), `sources.py`,
  `money.py`, the readers, test 7, or the `test_3b1:91-92` and `test_3b3:377,664` rows: those wait for 4a's merge into
  the branch. Nothing of 3B6 merges to `main` before 4a. Not a heavy database job. No other gate: 3B1, 3B2, 3B3, 5a,
  5b and 3B7a are merged.
- **Branch** `task/3B6-cold-ev` off `main`; worktree `/opt/assetecon/AssetOpsV1-3b6`; symlink `frontend/node_modules`
  from the main checkout.
- **Databases:** none needed; every test of this slice runs without a database. If a regression file named in §6.3 is a
  Postgres file, run it through `tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- <file>`
  on `*_test` only. Never ports 5490 or 8990, the walkthrough database or Docker. **No migration. No guard edit.**
- **Read:** `rulings.md`; `structure/registry.py` (whole), `structure/rows_mini_grid.py` (whole), `structure/check.py`
  (whole), `structure/pins.py` (whole), `structure/read.py` (whole), `structure/sources.py:30-160`,
  `structure/money.py:160-180`, `structure/litres/source.py:35-45`, `structure/targets/read.py:95-110` and `:185-210`,
  `structure/attribution/read.py:30-50`, `structure_snapshot/build.py:75-125`, `structure_snapshot/read.py:50-65`,
  `structure_snapshot/model.py:70-95`; `assetops_contracts/canonical/factors.py`; the manifest blocks
  `structures.COLD_CHAIN` and `.EV_DEPOT_CAPTIVE` (lines 833-866), `factor_map` (902-950), `home_categories.nodes`
  (1423-1508), `empty_states.leaf_sources` (1672-1721); `tests/test_3b1_structure_registry.py:1-140`,
  `tests/test_3b3_structure_evaluate.py:1-140`, `tests/test_3b2_findings_pinned.py:100-150`.
- **Pre-flight (before any test is written; report in the handshake):** (a) write the two row files (§2.2) in a
  scratch copy and run `check_all()`; any refusal is a handshake question, not a fix to the check (run in round 1: both pass, D-3B6.23). (b) Print
  `pins.parity()` with the three new pins of §3: it must return exactly today's one entry (`UNEXPLAINED_FUEL`). (c) Run the three W6 greps of §4.4 and list every hit; a hit outside the allowed set is a handshake question.
- **Files.** New: `backend/assetops_backend/structure/rows_cold_chain.py`, `structure/rows_ev_depot.py`; tests
  `backend/tests/test_3b6_cold_ev_structures.py` (no database). Edited, and only these: `structure/registry.py`
  (§2.1, §2.3), `structure/check.py` (§2.4), `structure/pins.py` (§3), `structure/read.py` (§4.1), `structure/sources.py` and `structure/money.py` (§4.2), `structure/targets/read.py` and `structure/attribution/read.py` (§4.3), `structure_snapshot/build.py`, `structure_snapshot/read.py`,
  `structure_snapshot/model.py` (comment only) (§4.3), `structure/__init__.py` (docstring only), and the test lines the
  W6 sweep names (§6.4).

## 1. Outcome and why

For a cold room and a captive EV depot, the structure read returns every factor of its declared structure for a
Site-month, each with its value or with "Not available yet" naming the record that would fill it; a captive depot's revenue is *declared not applicable* (a checked fact `applicability()` answers; it is never a row, never 0 and never "Not available yet"; no read shows it until `3B5`, D-3B6.14); and a portfolio read names each
Site of another structure as excluded, with its reason, instead of dropping it.

Why it converts: an operator executive of a cold-room or depot business sees the same shape as a mini-grid operator's
(outcome, headings, leaks, evidence words) from day one, so cold and EV become the records slices `9d` and `9e` filling
leaves, not new screens or new code. Today, with no cold or EV records connected (RC5: the first deep-dive is
mini-grid), only the calendar figures carry values (every other leaf names a record that is stored today, or says it is not connected, D-3B6.13); the honest reading of everything else is "Not available yet".

**On a typical cold or EV operator's exports** nothing is read this fortnight: the cold storage ledger, rate card and
electricity bill (`9d`) and the fleet roster, utility time-of-use bill and service contract (`9e`) have no intake. Each
leaf names exactly that record. What 3B6 proves is that when they arrive, the pack's figures come out of the same
evaluator to the cent (§5.1).

## 2. Unit 1: the two structures and their check (pure)

### 2.1 `Registry` gains `not_applicable` (`registry.py`; D-3B6.3)

- `Registry` gains a fourth field `not_applicable: tuple[str, ...] = ()` (after `rows`; the default keeps every
  existing `Registry(key, version, rows)` call valid). It lists factor IDs a reader of another structure may ask this
  structure for, which this structure declares do not apply to its business. It is not a row and carries no value. **Interface note (D-3B6.14):** `applicability()` is the only supported way to tell "revenue does not apply" from "revenue is not in this structure"; a reader (`3B5`) must call it and must not infer either from a missing key. It has no caller outside tests today: no read record carries it.
- Three module constants and one function in `registry.py`:

```python
APPLIES, NOT_APPLICABLE, NOT_IN_STRUCTURE = "APPLIES", "NOT_APPLICABLE", "NOT_IN_STRUCTURE"

def applicability(reg: Registry, factor_id: str) -> str:
    """APPLIES when `factor_id` is a row of `reg`; NOT_APPLICABLE when `reg.not_applicable` names it;
    NOT_IN_STRUCTURE otherwise. Pure; never raises for an unknown ID."""
```

- Add all four names to the module's exports (the module has no `__all__` today; add none if `rows_mini_grid` style
  is kept: they are imported by name).
- `REGISTRIES` becomes, in this order (D-3B6.1):

```python
REGISTRIES: Mapping[str, Registry] = MappingProxyType({
    "MINI_GRID": Registry("MINI_GRID", <its version when 3B6 merges, unchanged>, _MINI_GRID_ROWS),
    "COLD_CHAIN": Registry("COLD_CHAIN", 1, _COLD_CHAIN_ROWS),
    "EV_DEPOT_CAPTIVE": Registry("EV_DEPOT_CAPTIVE", 1, _EV_DEPOT_ROWS, not_applicable=("revenue",)),
})
```

  imported after the records, as `_MINI_GRID_ROWS` is (`from assetops_backend.structure.rows_cold_chain import ROWS as
  _COLD_CHAIN_ROWS`, `from assetops_backend.structure.rows_ev_depot import ROWS as _EV_DEPOT_ROWS`). The mini-grid entry is not touched: it keeps the version it has when 3B6 merges (3 on `main`, 4 after 4a; D-3B6.19), and no 3B6 test asserts it.

### 2.2 The rows (`rows_cold_chain.py`, `rows_ev_depot.py`; D-3B6.1, D-3B6.2)

Each file has the shape of `rows_mini_grid.py`: a module docstring naming 3B6 and the manifest blocks, the same two
private builders `_leaf(...)` and `_node(...)` (copied signatures: `composes` a required keyword; `_node` takes no
`stated_by` here because no cold or EV row states, D-3B6.2), and one literal tuple `ROWS`. Order: the leaves in
`leaves_of(key)` order, then the nodes in the manifest's `structures[key]` order. Every literal is written here and
never read from the catalogue or the manifest (W2; the parity test compares them):

- **Leaf** `factor_id`, `unit` (the catalogue's unit, as a `units.py` constant), `home` (`home_categories.nodes[key]`,
  through `HOMES`), `FilledBy(family, kind, words)` and `absent` (`empty_states.leaf_sources[key]`, `words` only where
  the manifest gives one), `composes` (§2.2.1), and `neutral` for each OPTION_ONLY leaf (§2.2.1).
- **Node** `factor_id`, `expression` (verbatim from `structures[key]`), `unit` (§2.2.2), `home`, `composes`.
- No `tolerance` on any row (D-3B6.9) and no `levers` (step 6).

**COLD_CHAIN: 36 rows, 23 leaves then 13 nodes.** Leaf order is `leaves_of("COLD_CHAIN")`: `outstanding`, `staff`,
`liability`, `period_days`, `crate_days`, `rate`, `contract_crate_days`, `contract_rate`, `base_kwh`,
`k_kwh_per_crate_day`, `model_factor`, `excess_kwh`, `elec_price`, `maint`, `handling`, `uncovered_nights`,
`backup_unproven_days`, `excursion_crates`, `excursion_days`, `batches_exposed`, `cooling_minutes_unavailable`,
`minutes_per_day`, `capacity_crate_days`. Nodes in manifest order: `revenue`, `received`, `kwh_model`, `kwh`, `energy`,
`cost_to_serve`, `contribution`, `nights_without_backup_cover`, `days_backup_start_unproven`,
`occupied_total_crate_days`, `crate_days_without_excursion`, `chamber_minutes`, `cooling_available_minutes`.

**EV_DEPOT_CAPTIVE: 42 rows, 23 leaves then 19 nodes.** Leaf order is `leaves_of("EV_DEPOT_CAPTIVE")` (the catalogue's
table order, `chargers_in_service` to `penalty_rate`). Nodes in manifest order, `deliverable_kwh_night` to
`contribution`. No `revenue` row (D-3B6.3); `contribution` is `0 - cost_to_serve` as the manifest states.

#### 2.2.1 Leaf `composes` and `neutral` (the test writes this table again, W2)

| Structure | `NONE` leaves (every other leaf is `SUM`) | OPTION_ONLY `neutral` |
|---|---|---|
| COLD_CHAIN | `rate`, `contract_rate`, `k_kwh_per_crate_day`, `model_factor`, `elec_price`, `minutes_per_day`, `period_days` | `contract_crate_days` 0, `contract_rate` 0, `model_factor` 1, `handling` 0 |
| EV_DEPOT_CAPTIVE | `charger_kw`, `import_limit_kw`, `window_h`, `kwh_per_bus_night`, `nights_in_period`, `max_kw`, `peak_price`, `offpeak_price`, `night_price`, `demand_rate`, `penalty_rate` | `covered_bus_nights` 0, `extra_missed_departures` 0 |

The neutral values are the manifest's `factor_map` literals (`"0"`, `"1"`) as `Decimal("0")`, `Decimal("1")`. `NONE`
follows 3B3's rule (D-3B3.14): every unit with a denominator (forced by `STRUCTURE_COMPOSES`), plus a ratio
(`model_factor`), a declared peak (`max_kw`, kW) and the calendar.

#### 2.2.2 Node units and `composes` (the test writes this table again, W2)

| Structure | Node | Unit | Composes |
|---|---|---|---|
| COLD | `revenue`, `received`, `energy`, `cost_to_serve`, `contribution` | MONEY | SUM |
| COLD | `kwh_model`, `kwh` | KWH | SUM |
| COLD | `nights_without_backup_cover`, `days_backup_start_unproven`, `occupied_total_crate_days`, `crate_days_without_excursion` | DAY | SUM |
| COLD | `chamber_minutes`, `cooling_available_minutes` | MINUTE | SUM |
| EV | `deliverable_kwh_night`, `scheduled_kwh_night`, `supplied_kwh_night`, `required_kwh_night` | KWH/DAY | NONE |
| EV | `buses_short_per_night` | ONE | NONE |
| EV | `departures_required`, `departures_missed`, `nights_below_required`, `charger_days_out_of_service`, `departures_met` | DAY | SUM |
| EV | `peak_cost`, `offpeak_cost`, `night_cost`, `demand_cost`, `energy_cost`, `penalties`, `cost_to_serve`, `contribution` | MONEY | SUM |
| EV | `cost_per_departure_met` | MONEY/DAY | NONE |

`buses_short_per_night` is `NONE` because it is a `ceil` of a per-night rate: a sum of ceilings across depots is not the
ceiling of their sum. `cost_per_departure_met` is a ratio: the portfolio's Σ cost ÷ Σ departures (spec §3) is not built
here (D-3B6.8).

### 2.3 `structure/__init__.py`

Docstring only: name `rows_cold_chain` and `rows_ev_depot` beside `rows_mini_grid`. No import change.

### 2.4 The check (`check.py`; D-3B6.3, D-3B6.4)

1. **`STRUCTURE_NOT_APPLICABLE`**, a per-registry code appended **last** to `_CHECKS` (after `STRUCTURE_MONEY_HOME`,
   so every existing index in `CODES` is unchanged). `_not_applicable(ctx)` refuses, naming the offending ID as
   `factor_id`, the first of: an entry that is not a `str` or does not `fullmatch` `FACTOR_ID_PATTERN`; an entry seen
   earlier in the same tuple; an entry that is a row of this registry (`ctx.units` holds every row ID). Iterate
   `ctx.reg.not_applicable` in order.
2. **Cross-registry, in `check_all`:** after every registry of the checked set has passed `check`, each entry of each
   registry's `not_applicable` must be a row of at least one *other* registry in the same checked set; else
   `StructureError("STRUCTURE_NOT_APPLICABLE", key, entry)`. Registries in mapping order, entries in tuple order. (A
   checked set holding `EV_DEPOT_CAPTIVE` alone therefore refuses: it names a factor no checked structure has. That is
   the honest answer, D-3B6.3.)
3. **Carried L2 (`3B1` rulings, "L2, carried to 3B6"):** in `check_all`, before `check(reg)` for each `(key, reg)` of
   the mapping, `key != reg.structure_key` raises `StructureError("STRUCTURE_CATALOGUE", key, "-")`.
4. `check_all` order is therefore: for each entry, L2 then `check`; then the cross-registry not-applicable pass; then,
   with no argument only, `check_pins()` (unchanged). Update the module docstring (3B6 added `STRUCTURE_NOT_APPLICABLE`
   and the key check).

Nothing else in `check.py` changes; in particular `_catalogue`, `_composes`, `_neutral`, `_category` and
`_money_home` are already generic over the structure key (pre-flight (a) proves the two new registries pass them).

## 3. Unit 1: the pins (`pins.py`; D-3B6.5)

`PINS` gains three entries; `PENDING_PINS` becomes `MappingProxyType({})` (kept, empty, for the next structure):

| Mechanism | Structure | Factor | Home (from the row) |
|---|---|---|---|
| `COLD_START_FAILURE` | `COLD_CHAIN` | `uncovered_nights` (leaf) | Protect P1 |
| `COLD_EXCURSION` | `COLD_CHAIN` | `excursion_crates` (leaf) | Protect P1 |
| `EV_INTERRUPTION` | `EV_DEPOT_CAPTIVE` | `chargers_in_service` (leaf) | Protect P1 |

All three are leaves, so `STRUCTURE_PIN_TOTAL` cannot refuse them; each outcome-map literal's first moved outcome is
PROTECT_ASSET in the pin's domain (`outcome_roles`, probed on `main`), so `parity()` still returns exactly the one
`UNEXPLAINED_FUEL` entry (D-3B2.4). Update the `PENDING_PINS` comment ("3B6 moved the three into `PINS`; empty until
another structure has pending mechanisms").

## 4. Unit 2: reading cold and EV Sites

### 4.1 The Site-type map and the portfolio read (`read.py`; D-3B6.6, D-3B6.7)

- `SITE_TYPE_TO_STRUCTURE = {"MINIGRID": "MINI_GRID", "COLDCHAIN": "COLD_CHAIN", "EV_CHARGING": "EV_DEPOT_CAPTIVE"}`
  (literal, still a `MappingProxyType`; D-3B6.7 for the EV entry, owner row 21). Update its comment.
- New exported constants: `OTHER_STRUCTURE = ("STRUCTURE_OTHER_KEY",)` (the reason a Site declared under another
  structure is left out of a portfolio of this one) and `KEY_NOT_READ = "STRUCTURE_KEY_NOT_READ"` (the code a Site-level
  reader that supports only some structures raises). `NOT_DECLARED` stays, for a type with no structure.
- New exported function, the one exclusion rule every portfolio reader uses (W6):

```python
def sites_excluded(sites: Sequence[SiteRef], structure_key: str) -> Mapping[str, tuple[str, ...]]:
    """Every Site not composed under `structure_key`, in the order given: NOT_DECLARED for a type with no
    structure, OTHER_STRUCTURE for a type declared under another key. A MappingProxyType."""
```

- `StructureRead.portfolio(tenant_id, sites, month, known_at=None, *, structure_key: str = "MINI_GRID")`: a key not in
  `REGISTRIES` raises `StructureError(NOT_DECLARED[0], structure_key, "-")`; refusals (duplicate, other tenant) as
  today but naming `structure_key`; `per_site` holds the Sites whose type maps to `structure_key`; `excluded =
  sites_excluded(sites, structure_key)`. Every existing caller passes no key and gets today's mini-grid behaviour, with
  a cold or EV Site now excluded as `OTHER_STRUCTURE` instead of `NOT_DECLARED`.
- `StructureRead.site` and `.site_inputs` need no change: they look the key up per Site and fold by that registry.
- No cross-structure total (D-3B6.8): a portfolio composes one structure key.

### 4.2 Leaf sources (`sources.py`; D-3B6.10, D-3B6.11)

`SOURCE_STATE` gains two maps, each with every leaf of its registry and nothing else (the test checks the key sets).
The states, as of 21 Nov 2026 (D-3B6.13; each HELD leaf names the stored record in the third column, and test 5c checks
that record's token is in its file):

| Structure | State | Leaves |
|---|---|---|
| COLD | `PROVIDED` | `period_days`, `minutes_per_day` |
| COLD | `OPTION_ONLY` | `contract_crate_days`, `contract_rate`, `model_factor`, `handling` |
| COLD | `HELD_NOT_CALCULATED` | `cooling_minutes_unavailable`: role `compressor_state` (`sites/binding_roles.py:162`, read by `analytics/cold.py:54`) |
| COLD | `NOT_CONNECTED` (16) | `outstanding`, `staff`, `liability`, `crate_days`, `rate`, `base_kwh`, `k_kwh_per_crate_day`, `excess_kwh`, `elec_price`, `maint`, `uncovered_nights`, `backup_unproven_days`, `excursion_crates`, `excursion_days`, `batches_exposed`, `capacity_crate_days` |
| EV | `PROVIDED` | `nights_in_period` |
| EV | `OPTION_ONLY` | `covered_bus_nights`, `extra_missed_departures` |
| EV | `HELD_NOT_CALCULATED` | `chargers_in_service`: roles `ev_connector_state` and `ev_connector_fault` (`sites/binding_roles.py:204,208`); `import_limit_kw`: property `ev-site-import-limit` (`sites/models.py:224`, `sites/ev_foundation.py:431`); `chargers_installed`: the `EV_CHARGER` components of the declared Foundation (`sites/ev_foundation.py`, `ev_foundation_document`) |
| EV | `NOT_CONNECTED` (17) | `charger_kw` (per-charger `ev-charger-max-power`, no rule for one Site rating), `charger_out_days` (no ticket record with fault and restore times), `window_h`, `buses`, `kwh_per_bus_night`, `peak_kwh`, `kwh_2200_2400`, `kwh_0000_0500`, `max_kw`, `peak_price`, `offpeak_price`, `night_price`, `demand_rate`, `maintenance`, `short_nights`, `spare_bus_nights`, `penalty_rate` |

HELD means the record kind has a stored form and an intake today and the figure is not calculated from it yet; a Site
that holds no such record reads the same words. A work case (`work/model.py`) is a free-text incident or request with no
failed-start, witnessed-test or fault-and-restore field, so a leaf whose manifest record is a work case or service
ticket is `NOT_CONNECTED`.

`STATED_STATE` is unchanged (no cold or EV row states). `COMMERCIAL_LEAVES`, `LITRE_LEAVES`, `ASSUMPTION_WORDS` and
`PRICE_KEYS` are unchanged.

`ProductLeafSource.leaf` gains two calendar branches beside `period_days`, reached only for a `PROVIDED` state:
- `minutes_per_day` → `LeafValue(Decimal(1440), "DERIVED", ("calendar",), None, None, None)` (D-3B6.11);
- `nights_in_period` → exactly `_period_days(ctx)` (the Site-local days of the month).

No other change to `ProductLeafSource`: `NOT_CONNECTED` and `HELD_NOT_CALCULATED` already build `Missing` from the
row's own `filled_by`; `OPTION_ONLY` already returns `row.neutral` as `NEUTRAL`. **Shared factor IDs (`R-SHARED-ID`, D-3B6.18).** `COMMERCIAL_LEAVES` and `money._ROWS` are keyed by factor ID and COLD shares `staff` and `outstanding` with the mini-grid, so the day `9d` flips a COLD leaf to `PROVIDED` it would be judged with mini-grid rows. Prevented now: `sources.py` gains `COMMERCIAL_KEYS = frozenset({"MINI_GRID"})` (beside `COMMERCIAL_LEAVES`; added to `__all__`), and `CommercialLeafSource.leaf` (`money.py:169`) serves a `_ROWS` leaf only when `state == PROVIDED and key in COMMERCIAL_KEYS`, else falls back; `ProductLeafSource` reads a PROVIDED commercial-leaf ID as `NOT_CONNECTED` (its existing branch). `9d` adds its structure to `COMMERCIAL_KEYS` together with its own rows. `LitreLeafSource` (IDs `necessary_l`, `candidate_l`, `unexplained_l`) and, after 4a, `EnergyLeafSource` share no ID with a cold or EV leaf; test 6 asserts that by state, not by ID (it cannot be by ID for `staff`). Nothing else changes in the two sources: a cold or EV leaf is never `PROVIDED` there (except the calendar, which passes through), so both fall through to `ProductLeafSource` and never read a commercial or litre store (test 6 proves it with raising fakes).

### 4.3 The readers that support only the mini-grid structure (D-3B6.6)

| File | Today | 3B6 |
|---|---|---|
| `structure/targets/read.py` `TargetRead.site` | `TARGET_RULE[key]` → `KeyError` for a cold Site | right after the key lookup (before `_month`, before the budget-lines read): `if key not in TARGET_RULE: raise StructureError(KEY_NOT_READ, key, site.site_code)` |
| `structure/targets/read.py` `TargetRead.portfolio` | excludes `get(type) is None` as `NOT_DECLARED`; drops other keys | `sites_excluded(sites, key)` |
| `structure_snapshot/build.py` `build` | `excluded[code] = NOT_DECLARED` for any key ≠ MINI_GRID | `excluded[code] = sites_excluded(sites, key)[code]` for each Site not composed |
| `structure_snapshot/read.py` `SnapshotRead.site` | refuses only `get(type) is None` | also refuses a key other than `SITE_TYPE_TO_STRUCTURE["MINIGRID"]` with `StructureError(KEY_NOT_READ, key, site.site_code)` (snapshots are built only for MINI_GRID) |
| `structure_snapshot/model.py` | comment "a type with no structure: NOT_DECLARED" | comment names `OTHER_STRUCTURE` too; no code change |
| `structure/attribution/read.py` `BridgeRead.site` | evaluates `self._actual.site_inputs(...)` (every leaf through the providers) as an argument, then `self._targets.site(...)` | evaluate `self._targets.site(site, month, k)` first (a local), then `site_inputs`: the refusal comes before any read (D-3B6.17) |
| `structure/attribution/read.py` `BridgeRead.portfolio` | follows `TargetRead.portfolio`; reads `site_inputs` for Sites of its key only | no change; `sites_excluded` comes from the target composition (test 8 shows it) |

`structure/litres/source.py`, `structure/attribution/{site,carry,rules,portfolio}.py`,
`structure/targets/{lines,rules}.py`, `structure_snapshot/{codec,untracked}.py` need no change (each is reached only for
a mini-grid key, or looks the registry up by the stored key); the packet states this per file.

### 4.4 The W6 greps (pre-flight (c); packet table; D-3B6.22)

Three greps, narrowed to the readers of the Site-type map (the old `"MINIGRID"` literal grep returned about 60 hits,
about 40 of them other uses of the literal in `chain/`, `sites/`, `scheduling/` and `site_outcomes/`):

- **G1** `grep -rn 'SITE_TYPE_TO_STRUCTURE' backend/assetops_backend`: every hit lies in `structure/` or
  `structure_snapshot/` (on `main`: 25 hits, 8 files). Each is listed in the packet as "changed" (§4.1 to §4.3) or with
  the reason it is safe.
- **G2** `grep -rn 'build_structure_read\|build_target_read\|build_bridge_read\|StructureRead(\|TargetRead(\|BridgeRead(' backend/assetops_backend`:
  no hit outside `structure/` and `structure_snapshot/` (on `main`: none), so no consumer outside assumes one structure.
- **G3** `grep -rn 'NOT_DECLARED\|REGISTRIES\["MINI_GRID"\]' backend/assetops_backend/structure backend/assetops_backend/structure_snapshot`
  (on `main`: 27 hits): each in the packet as "changed" or safe.

A hit outside G1's or G2's directories, or a G1 or G3 hit that is neither named in §4.1 to §4.3 nor listed safe in the
implementer's pre-flight (`structure/read.py:61`, `structure/sources.py:144`, `structure/attribution/portfolio.py:21,103`,
`structure/attribution/read.py:43`: safe; `structure/money.py:165-169` (`leaf`): changed, D-3B6.18; `:174` (`stated`): safe, `STATED_STATE` has no cold or EV key), is a handshake question.

## 5. Fixtures (the pack's own figures; the tests read the pack, never the code under test, W2)

### 5.1 The six Sites, evaluated (test 4)

Leaves for one Site and side are built exactly as `test_3b3_structure_evaluate.pack_leaves` builds them (the test file
defines its own copy, `cold_ev_leaves(site, side, key)`): the value from `derived-values.json`
`sites[<tenant>/<site>][<side>].nodes[<leaf>]`, MEASURED on `actual` and `november_to_date`, DECLARED on `plan`,
OPTION_ONLY leaves `NEUTRAL`, currency `USD` on the test's own money list, origins `("source-emulated",)`.
- Money leaves (the test's own literal): COLD `rate`, `contract_rate`, `elec_price`, `staff`, `maint`, `liability`,
  `handling`, `outstanding`; EV `peak_price`, `offpeak_price`, `night_price`, `demand_rate`, `maintenance`,
  `penalty_rate`.
- Sides evaluated (13): `harvest-cold/Room A · Mwea`, `/Room B · Thika`, `/Room C · Kirinyaga` × {actual, plan};
  `metro-bus/Embakasi` × {actual, plan}; `metro-bus/Kasarani` × {actual, plan, november_to_date}; `metro-bus/Ruiru` ×
  {actual, november_to_date}. **Skipped, as a literal with its reason:** `metro-bus/Ruiru` plan (a stated total with no
  factor behind it; its nodes are absent from `derived-values.json`, manifest `home_categories.residuals`).
- Expected: every node of the registry equals the pack's value quantised to 0.01 (`ROUND_HALF_EVEN`); the evaluator's
  value is quantised only for the comparison. Hand checks the test also writes as literals: Mwea actual
  `contribution` −12.00, `kwh_model` 2635.00, `chamber_minutes` 44640; Thika actual `contribution` 454.00,
  `crate_days_without_excursion` 8560; Embakasi actual `cost_to_serve` 22744.80, `cost_per_departure_met` 36.69
  (22744.8 / 620), `contribution` −22744.80; Ruiru actual `charger_days_out_of_service` 26.

### 5.2 The two portfolios (test 4b)

`compose(REGISTRIES["COLD_CHAIN"], {three rooms' actual SiteStructure})` and the same for the three depots: every
`SUM` factor's value equals `derived-values.json` `portfolio[<tenant>].actual.sums[<factor>]` to the cent; every `NONE`
factor is in `not_composed` and absent from `values`. Literals: harvest-cold `contribution` 946.00, `revenue` 4588.00,
`excursion_crates` 120; metro-bus `cost_to_serve` 41705.12, `departures_met` 1302, `charger_out_days` 26. (The pack
sums prices and per-night rates too; those pack sums are not compared, which the test states.)

### 5.3 The product read (tests 5, 6)

A cold Site `SiteRef(TENANT, uuid4(), "COLD-THIKA", "COLDCHAIN", "Africa/Nairobi")` and an EV Site `SiteRef(...,
"EV-RUI", "EV_CHARGING", "Africa/Nairobi")`, month `2026-10`, `known_at` 2026-11-06T00:00Z, read through
`StructureRead(ProductLeafSource(<snapshot fake that fails if called>, <price fake that fails if called>, now))`.
Expected for `2026-10`, per leaf: `PROVIDED` calendar leaves `period_days` 31, `minutes_per_day` 1440, `nights_in_period` 31, DERIVED; the same read is repeated for `2026-02`, `2026-11` and `2028-02` (D-3B6.15: 28, 30, 29 days; COLD `chamber_minutes` 40320, 43200, 41760), so a constant month length fails;
OPTION_ONLY leaves their neutral as `NEUTRAL`; `NOT_CONNECTED` leaves `value None`, `NOT_AVAILABLE`, cause
`NOT_CONNECTED`, `record_kind`/`source_family`/`record_words` equal to the manifest's `kind`/`family`/`words`;
`HELD_NOT_CALCULATED` leaves (COLD 1, EV 3) the same with cause `NOT_CALCULATED_YET`. Nodes: COLD `chamber_minutes` 44640 (DERIVED);
COLD `cooling_available_minutes` None (it rests on `cooling_minutes_unavailable`); every money node (`revenue`,
`received`, `energy`, `cost_to_serve`, `contribution`) value None, never 0, each `missing_leaves` naming at least one
leaf; EV `departures_required` None; EV `contribution` None.

## 6. Tests (written first; `backend/tests/test_3b6_cold_ev_structures.py`, no database)

### 6.1 New

1. **Parity with the manifest (T1),** per key: node IDs and expressions equal `structures[key]`; leaf set equals
   `factor_map[key]`; each leaf's `filled_by` and `absent` equal `empty_states.leaf_sources[key]` (`words` included);
   each row's home equals `home_categories.nodes[key]` through the test's own home map (3B1's `OWN_HOME_MAP` copied);
   the home rows not in the registry are exactly COLD `{"cover_not_claimable"}` and EV `{"cover_not_claimable"}`; row
   order is `leaves_of(key)` then the manifest's node order; row counts 36 (23 + 13) and 42 (23 + 19); versions 1;
   each registry's `not_applicable` equals the IDs the manifest's `chain_model[key]` marks `NOT_APPLICABLE` (EV
   `("revenue",)`, COLD and MINI_GRID `()`), read from the pack, not from the code.
2. **Units and composes (T2):** `check_all()` passes; each node's composed unit (`unit_of(parse(expr), declared)`)
   and declared unit equal §2.2.2's table, written as literals; each row's `composes` equals §2.2.1 and §2.2.2; each
   OPTION_ONLY leaf's `neutral` equals the manifest literal and §2.2.1.
3. **The check (T3),** one plant per new refusal, each asserting the full text. Per-registry refusals go through
   `check(reg)` directly (so removing one line of `_not_applicable` fails here): `not_applicable=("Revenue",)` (pattern)
   → `STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/Revenue`; `("revenue", "revenue")` → refuses the second;
   `("cost_to_serve",)` → `.../cost_to_serve` (a row of its own). Mapping-level refusals go through
   `check_all(registries=...)`: `("revenu",)` on EV with `{MINI_GRID, COLD, EV}` → `.../revenu`; EV alone →
   `STRUCTURE_NOT_APPLICABLE EV_DEPOT_CAPTIVE/revenue`; `{"COLD_CHAIN": REGISTRIES["EV_DEPOT_CAPTIVE"]}` →
   `STRUCTURE_CATALOGUE COLD_CHAIN/-` (L2). `CODES[-1] == "STRUCTURE_NOT_APPLICABLE"` and `CODES[:-1]` equals the
   15-code literal of `main`. `create_app()` refuses a planted not-applicable typo as `ConfigurationError`. Each of the
   five code lines it exercises is the target of a code plant (guide P20 to P24).
4. **The six Sites (T4)** of §5.1, parametrised over the 13 sides; the skip set equals its literal.
4b. **The two portfolios (T4b)** of §5.2.
5. **The gate, at the data level: revenue declared not applicable, never zero (T5a):** for the EV registry and the EV
   Site read of §5.3 and the Embakasi actual side of §5.1: `"revenue"` is not a row and not a key of `values`;
   `applicability(EV, "revenue") == NOT_APPLICABLE`; `applicability(EV, "tariff") == NOT_IN_STRUCTURE`;
   `applicability(MG, "revenue") == applicability(COLD, "revenue") == APPLIES`; no `FactorValue` of any EV side has
   value 0 under `revenue`, `received` or `collected` (there are none); EV `contribution` equals −`cost_to_serve` on
   every evaluated side. The test's docstring says no read carries applicability (D-3B6.14).
5b. **The product read (T5b)** of §5.3: `set(SOURCE_STATE[key]) == {leaf IDs of REGISTRIES[key]}` for both keys; the
   test's own copy of §4.2's table equals `SOURCE_STATE` (state counts COLD 2/4/1/16, EV 1/2/3/17); each leaf and node
   as §5.3 states, for all four months of D-3B6.15; no `FactorValue` of either Site has value 0 except the OPTION_ONLY
   leaves' neutral 0 and nodes that rest only on them and the calendar (asserted by name: none in COLD or EV today, so
   the set is empty).
5c. **Held records exist (T5c):** the test holds, as its own literal, one `(file, token)` per HELD leaf: COLD
   `cooling_minutes_unavailable` → (`sites/binding_roles.py`, `"compressor_state"`); EV `chargers_in_service` →
   (`sites/binding_roles.py`, `"ev_connector_state"`) and (`..., "ev_connector_fault"`); `import_limit_kw` →
   (`sites/ev_foundation.py`, `"ev-site-import-limit"`); `chargers_installed` → (`sites/ev_foundation.py`,
   `"EV_CHARGER"`). It fails when a token is not in its file, and when the set of HELD leaves in `SOURCE_STATE` is not
   exactly the literal's leaves (so a leaf cannot become HELD without a cited record).
6. **The composed chain does not touch other stores, and shared IDs cannot route (T6):** (a) `CommercialLeafSource(
   <months fake raising>, <store fake raising>, LitreLeafSource(<inputs fake raising>, ProductLeafSource(...), now))`
   (after 4a: wrapped in `EnergyLeafSource(<inputs fake raising>, <that chain>, now)`, as `structure/composition.py`
   builds it, D-3B6.20) reads the cold and EV Sites of §5.3 with results equal to test 5b's; no fake is called. (b)
   For each key of COLD and EV, no leaf whose ID is in `COMMERCIAL_LEAVES | LITRE_LEAVES | set(money._ROWS)` (after 4a
   `| ENERGY_LEAVES`) has state `PROVIDED` or `PROVIDED_ELSE_ASSUMED` (state, not ID: `staff` is shared). (c) With
   `SOURCE_STATE` patched (in `sources` and in `money`, which imports it by name) so COLD `staff` is `PROVIDED`, the
   chain of (a) reads `staff` as `NOT_CONNECTED` naming the COLD row's `filled_by`, and no fake is called (D-3B6.18).
7. **Pins (T7):** `PINS` equals the test's literal of five (two mini-grid, three of §3); `PENDING_PINS == {}`;
   `check_all()` passes; `parity()` returns exactly the `UNEXPLAINED_FUEL` entry; each new pin's
   `pinned_category` is PROTECT_ASSET.
8. **The readers (T8):** with a fake `LeafSource`: `StructureRead.portfolio(T, [KOBO, cold, ev, hydro], m)` excludes
   `cold` and `ev` as `OTHER_STRUCTURE` and `hydro` (type `"HYDRO"`) as `NOT_DECLARED`, in that order;
   `portfolio(..., structure_key="COLD_CHAIN")` over `[cold_a, cold_b, KOBO]` composes the two rooms and excludes
   KOBO as `OTHER_STRUCTURE`; `structure_key="NOPE"` raises `STRUCTURE_NOT_DECLARED NOPE/-`; `TargetRead.site(cold)`
   raises `StructureError` code `STRUCTURE_KEY_NOT_READ`, `factor_id` the Site code (never `KeyError`), with the
   budget-lines fake failing if called; `BridgeRead.site(cold)` raises the same with the actual side's `site_inputs`
   fake and the lines fake both failing if called (D-3B6.17); `TargetRead.portfolio(T, [KOBO, cold], m)` and
   `BridgeRead.portfolio(T, [KOBO, cold], m)` exclude `cold` as `OTHER_STRUCTURE` and compose KOBO, the `site_inputs`
   fake called for KOBO only; `SnapshotRead.site(T, cold, m)` raises `STRUCTURE_KEY_NOT_READ`;
   `SnapshotBuilder.build` over `[KOBO, cold]` with fakes stores `excluded == {"COLD-...": OTHER_STRUCTURE}` (use the
   3B7a test world's fakes, `tests/test_3b7a_structure_snapshot.py`). `test_5b_attribution.py` runs in the build.

### 6.2 Regression (named files, run in the build)

`test_3b1_structure_registry.py`, `test_3b2_findings_pinned.py`, `test_3b3_structure_evaluate.py`,
`test_3b3_structure_read_postgres.py`, `test_4b1_stated_nodes.py`, `test_4d_litre_split.py`, `test_5a_targets.py`,
`test_5b_attribution.py`, `test_3b7a_site_inputs_seam.py`, `test_3b7a_structure_snapshot.py`, and 4a's two test files.
Then check-all.

### 6.3 The W6 sweep (pins that change by design; the packet lists each with its old and new literal)

| File:line on `main` | Old | New | Why |
|---|---|---|---|
| `test_3b1_structure_registry.py:92` | `set(REGISTRIES) == {"MINI_GRID"}` | `== {"MINI_GRID", "COLD_CHAIN", "EV_DEPOT_CAPTIVE"}` | D-3B6.1 |
| `test_3b2_findings_pinned.py` `DESIGN_PINS`, `DESIGN_PENDING` | two pins; three pending | five pins; `{}` | §3 |
| `test_3b2_findings_pinned.py` T1 manifest-row test | matches `r["factor"] == factor_id` | also matches a row whose factor is a node that is exactly the pin's leaf (`structures[key][r["factor"]] == factor_id`); `COLD_EXCURSION` in a literal `NO_MANIFEST_ROW` with its reason | D-3B6.5 |
| `test_3b2_findings_pinned.py:258-259` | drops `EV_INTERRUPTION` from `PENDING_PINS` | drops it from `PINS` (monkeypatched), same expected text | §3 |
| `test_3b2_findings_pinned.py` `OWN_SITE_STRUCTURE` | three mini-grid Sites | adds the six cold and EV Sites | D-3B2.9 extended |
| `test_3b3_structure_evaluate.py:681`, `:705` | `("STRUCTURE_NOT_DECLARED",)` for a COLDCHAIN Site | `("STRUCTURE_OTHER_KEY",)` | D-3B6.6 |
| `test_5a_targets.py:544` | code `STRUCTURE_NOT_DECLARED` | `STRUCTURE_KEY_NOT_READ` | D-3B6.6 |
| `test_5a_targets.py:674`, `:676` | `("STRUCTURE_NOT_DECLARED",)` | `("STRUCTURE_OTHER_KEY",)` | D-3B6.6 |
| `test_5b_attribution.py:813` | `("STRUCTURE_NOT_DECLARED",)` | `("STRUCTURE_OTHER_KEY",)` | D-3B6.6 |
| `test_3b7a_structure_snapshot.py:234`, `:285` | `("STRUCTURE_NOT_DECLARED",)` | `("STRUCTURE_OTHER_KEY",)` | D-3B6.6 |

Found by the class grep `grep -rn 'STRUCTURE_NOT_DECLARED\|PENDING_PINS\|set(REGISTRIES)' backend/tests`; a literal
changed for any other reason is a finding. `test_3b3_structure_evaluate.py:783` stays (it asserts no
`NOT_DECLARED` reason within one structure). Each changed test keeps one assertion that a Site of an undeclared type still reads `NOT_DECLARED` (test 8 adds it).

**No literal changed, behaviour widened (packet lists both, D-3B6.21):** `test_3b2_findings_pinned.py:234` (its planted `Registry("NOT_MINI_GRID_KEY", ...)` now refuses at L2, `STRUCTURE_CATALOGUE X/-`, same code in `CODES`; the comment is retitled to say L2) and `test_4b1_stated_nodes.py` `_valued_cases` (about 60 cold and EV cases join through `REGISTRIES`; a failing case is a finding on the row, not a test edit). **Not touched by 3B6:** the mini-grid version line `test_3b1_structure_registry.py:91` and `test_3b3_structure_evaluate.py:377,664` are 4a's (3 to 4); 3B6 edits `:92` only.

Stored snapshots: `rules_digest` covers every module the build imports (`structure_snapshot/adapters/code_digest.py`),
so after this merge every stored snapshot reads "rebuild needed" until the analyst rebuilds it, as after every
structure slice (D-4A.25). No migration; 3B6 touches no stored row.

## 7. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.0) | §2 (registry field and function, two row files, the check), then (after 4a, §0) the `REGISTRIES` literal and §3 pins; pre-flight (a) and (b); tests 1, 2, 3, 7; the 3B1 and 3B2 lines of §6.3 | 1 to 2 |
| 2 (1.0) | §4 (map, `sites_excluded`, codes, portfolio key, sources, `COMMERCIAL_KEYS` guard, the readers, `BridgeRead.site` reorder); pre-flight (c); tests 4, 4b, 5, 5b, 5c, 6, 8; the remaining lines of §6.3 | 1 to 2 |
| 3 (0.75) | regression §6.2; plants (reviewer guide P1 to P30, each shown failing once on a scratch copy); check-all; packet | 1 |

Total 2.75 (D-3B6.12, D-3B6.24). Packet `specs/3B6-cold-ev/packet.md`: the sweep table, the W6 grep table (§4.4), the stored-
snapshot statement, the plants run, residual risks `R-EV-PUBLIC` (D-3B6.7), `R-DST-MINUTES` (D-3B6.11),
`R-CROSS-KEY` (D-3B6.8), `R-SHARED-ID` (D-3B6.18: closed by the guard and test 6; stays listed until `9d`), the "no literal changed, behaviour widened" list (D-3B6.21), the mid-build count.

## 8. Done (questions; each can fail)

1. Do the cold-room and captive-EV structures reproduce the manifest row for row (expressions, leaves, sources,
   absences, homes, order), and does `check_all()` pass with them at start-up (tests 1, 2)?
2. Does the same evaluator give the pack's figures to the cent for the 13 cold and EV sides and the two portfolios'
   summed factors, with no vertical-specific code in `evaluate.py`, `check.py` or `read.py` (tests 4, 4b; `git diff` of `evaluate.py` empty)? Do the calendar leaves hold for four month lengths (test 5b)?
3. Is a captive depot's revenue *declared* not applicable (checked at start-up, answered by `applicability()`), never a row, never 0 and never "Not available yet", and is any other unknown ID `NOT_IN_STRUCTURE` (test 5a)? The question does not ask that a read shows it: none does until `3B5` (D-3B6.14).
4. Does a cold or EV Site read today show the calendar figures and "Not available yet" naming each record for every
   other leaf, with every money node unknown and never 0, without touching a commercial or litre store, with every HELD leaf naming a record that exists and no shared factor ID able to route a cold or EV leaf through mini-grid rows (tests 5b, 5c, 6)?
5. Is every Site of another structure named in a portfolio read with `STRUCTURE_OTHER_KEY`, every undeclared type
   with `STRUCTURE_NOT_DECLARED`, and does every mini-grid-only Site reader (`TargetRead.site`, `BridgeRead.site`, `SnapshotRead.site`) refuse a cold or EV Site by code before any read, never a `KeyError` and never a silent drop (test 8, §6.3)?
6. Are the three cold and EV mechanisms pinned, `PENDING_PINS` empty, and `parity()` unchanged (test 7)?
7. Are the persistence and architecture guards unchanged and passing, with no migration and no user-facing text?
8. Is every pin of §6.3 changed only for its stated reason, and does each plant of the reviewer guide (P1 to P30) fail its named test? Mid-build count 0?

## 9. Out of scope

Cold and EV record intake, observers and providers (`9d`, `9e`: storage ledger, rate card, electricity bill, fleet
roster, utility time-of-use bill, service tickets, contract penalty terms); the room-capacity property behind
`capacity_crate_days` (D-3B6.10); target sides for cold and EV (`TARGET_RULE` stays MINI_GRID; `5a` extends it with
`9d`/`9e`); the bridge for cold and EV; snapshots of cold and EV Sites (`3B7a` builds MINI_GRID only); a
cross-structure portfolio total and the portfolio ratio `cost_per_departure_met` (D-3B6.8, queued); a public-charging
structure (D-3B6.7); the rights nodes `cover_not_claimable` (as for MINI_GRID, D-3B1.5); the potential entries
(`idle_capacity`, `spare_deliverable_energy`) and the EV residual row (`5b`); tolerances (`3B4`); any screen text.

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Which structure does an `EV_CHARGING` Site take, given the only EV structure declared is the captive depot? | `EV_DEPOT_CAPTIVE` (D-3B6.7; OWNER-AWAY row 21); a public-charging structure gets its own key and the map becomes a declared Site property when the first public-charging operator is onboarded |
| Q2 (owner) | A portfolio of Sites of two verticals: one cross-vertical total, or one composition per structure? | One per structure, each other-structure Site named (D-3B6.8; row 22); a cross-structure sum of the shared money nodes is queued with trigger "the first tenant with two verticals" |
| Q3 | How is "revenue not applicable" carried? | A registry-level declared list with a check, read by `applicability()`; not a row, not a value (D-3B6.3) |
| Q4 | Where do the three cold and EV Findings pin? | On the leaves `uncovered_nights`, `excursion_crates`, `chargers_in_service` (D-3B6.5); the pack's node `nights_without_backup_cover` is a bare rename, refused by `STRUCTURE_PIN_TOTAL` |
| Q5 | `capacity_crate_days` (the pack assigns its source to 3B6) | Declared, `NOT_CONNECTED`; its Foundation property and reader go with `9d`, when something reads it (D-3B6.10) |
| Q6 | `minutes_per_day` in a zone with daylight saving | The declared 1440 (the manifest's literal); every demo and pilot zone has no DST; risk `R-DST-MINUTES` (D-3B6.11) |
| Q7 | Portfolio `cost_per_departure_met` (Σ cost ÷ Σ departures) | Not composed (`NONE`); queued with the cross-structure total (D-3B6.8) |
| Q8 | What makes a leaf `HELD_NOT_CALCULATED` rather than `NOT_CONNECTED`? | A stored record with an intake in the code today, named and checked by test 5c; otherwise `NOT_CONNECTED` (D-3B6.13) |
| Q9 (owner, logged) | What does 3B6 claim about "revenue not applicable"? | Declared, checked and queryable; no read shows it until `3B5` (D-3B6.14; row 26) |
| Q10 | A COLD leaf shares a factor ID with the mini-grid (`staff`, `outstanding`) | A structure-key guard in `CommercialLeafSource` plus a state assertion in test 6 (D-3B6.18) |
