# 6h: named-option levers for every Site type (implementer spec, with its reviewer guide)

**Status: in_review (built; packet.md).** Spec rev 1, handshake answered (W4); Architect (Claude), 2026-11-22. Demo-critical.
**Rulings:** `specs/6f-decisions-screen/rulings.md` D-P6.51 to D-P6.58; this folder's `rulings.md` D-P6.59 to D-P6.67
(the handshake, `handshake-review.md`). **Owner:** "Build 6h (Recommended)" and 6h Q3
"Yes, +1.0 u" (`owner/owner-6f-q1-levers-2026-11-22.md`). **Why:** `specs/6f-decisions-screen/assessment-levers.md`.
`USER_REVIEW_REQUIRED: true` (it fixes what a decision is for cold-chain and EV Sites). W5: **discovery review**
(new generator, migration, money figures).

**Size: 4.25 units, four units, one slice** (`task/6h-levers`; D-P6.67): 6h1 lever model and migration (1.0), 6h2
evaluator branch (1.0), 6h3 catalogue, words and the class check (1.25), 6h4 option records (1.0). Under the 6-unit
cap. The owner approved 3.75 u; +0.25 is the lever words moved here from 6f (D-P6.58) and the protective-lever rule
(D-P6.57); +0.25 is the handshake's fixes in 6h2 (D-P6.60 to D-P6.62 and the parity golden). 6f1 stays 3.75 u.

**Rev 1 changes (D-P6.59 to D-P6.67):** `backup_cover` moves `uncovered_nights` only (§5.1, §5.4, T1); an option's
unrecorded leaves are named (§4.3); evidence and source class include changed leaves (§4.3, T1e); `LeafChange` carries
a currency and `OPTION_RECORD_CURRENCY` is gone (§4.2, §4.3); grid checks run for `SETTING_GRID` only (§3.2); G4 defined
(§2); one change rule, record minus base (§4.2); `KEEP_SETTINGS` (§3.1, §5.4); three existing tests named and a parity
test added (§10.2); plant list corrected (§10.3); live constraint names confirmed (§3.4); `option_inputs` signature
(§4.1); mini-grid `_node` gains `levers` (§5.2).

**Read first (by section):** this spec; 6a `spec.md` §3.1 to §3.3 (levers, tables, prepare); 6c `spec.md` §3.4, §3.5,
§4; `structure/levers.py`; `structure/check.py` `_lever_fault`, `check_levers`; `decisions/records.py` `prepare`,
`state_one_off`; `decisions/run.py`; `decisions/evaluate.py`; `structure/difference.py` `difference`;
`backend/tests/option_fixtures.py`.

## 0. Governing sources

- **Mock:** non-screen. It supplies the decisions vNEXT shows for every Site
  (`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/loop-decisions.js`, `DEC`): each anchored on the
  factor its options change, doing nothing among the options. 6f renders them. Departures in §9.
- **Design pack:** `demo-site-scenario-manifest.yaml`, the decision table (`id`, `finding_factor`, `lever`, `heading`)
  and each Site's `options`. Read by grep only.
- **Owner rules applied:** fundamental mechanics first (one mechanism, every Site type, no vertical branch); fix model
  faults in the model; missing data reads "Not available yet", naming the record; one model-computed figure per
  quantity (an option record states a document's term, never a computed result); extend aligned constructs (the lever,
  the one-off, the option-only leaves of 3B6); decisions inside the outcome mechanism (Finding → factor → lever →
  options → choice → Action → verify).

## 1. Existing, then new

**Today:** one lever (`generator_stop_reserve`, `SETTING_GRID`), valued from a dispatch replay. Cold-chain and EV
registries already declare option-only leaves (`contract_crate_days`, `contract_rate`, `model_factor`, `handling`;
`covered_bus_nights`, `extra_missed_departures`) with no lever to move them. 6c's core already values cold and EV
changes (fixtures C1, E1).

**6h adds:**
1. A second generator, `STATED_OPTIONS`: a lever lists named options, each with the leaves it moves (6h1).
2. For each changed leaf, its source: `STUDY` (a replay of the Site's own month) or `RECORD` (a document's term) (6h1).
3. The evaluator branch for named options: a leaf is changed from its option record when held, else missing and named
   (6h2). Protective levers make no recommendation until bounds exist (6b), and their purpose factor's change is shown.
4. Nine levers as catalogue data, their words, and the start-up rule that every pinned Finding has a decision path
   (6h3).
5. The option record: a person states a document's term for an option (contract, quote, rota, roster cover), as the
   one-off is stated today (6h4). This lights Mwea's contract and the Thika and Kasarani stopgaps.

**What stays:** `generator_stop_reserve` and its study path, every 6a/6c rule and record, the one-off, the choice.

## 2. Gates (hard stops)

- **G1** 6a and 6c on `main` (met: `591458c38`). Migration head `0072_decision_records`; 6h writes `0073`. If another
  slice took `0073` first, renumber and say so in the packet.
- **G2** The handshake (§12) answered before the first commit.
- **G3** No screen change: 6h serves records and statements; 6f renders them.
- **G4** (a done condition, not a stop; D-P6.64) 6h is done on K2 (unit fixture, 630.00). On the DD world Kasarani is
  valued only once DD's EV inputs for 2026-11 read (Q11); until then its page names the missing November record. When
  they read, the manifest's `KAS-OEM-STOPGAP` (cover `nights: 2`, penalty 120.00, one-off 90.00) gives **150.00** (the
  manifest's `modelled_12m_change`); DD6.2 asserts it, or reports the figure if DD's November gives fewer than two
  missed departures before cover.

## 3. Unit 6h1: the lever model, prepare and the migration (1.0 unit)

### 3.1 `structure/levers.py`

```python
@dataclass(frozen=True)
class LeverOption:
    key: str                        # _OPTION_KEY; never "no-action"
    kind: str                       # OPTION_KINDS
    changes: tuple[str, ...]        # non-empty subset of Lever.changes, in Lever.changes order

@dataclass(frozen=True)
class ChangeSource:
    kind: str                       # "STUDY" | "RECORD"

OPTION_KINDS = ("REPAIR", "CAPEX", "SUPPLIER_REMEDY", "SCHEDULE", "DEMAND_CONTRACT", "CAPACITY_USE",
                "DEMAND_CONNECTION", "INVESTIGATION")
GENERATORS = ("SETTING_GRID", "STATED_OPTIONS")
NO_ACTION_WORDS = ("KEEP_SETTINGS", "KEEP", "WAIT_FOR_REMEDY")   # how doing nothing reads (6f, D-P6.58, D-P6.66 N1)

@dataclass(frozen=True)
class Lever:                        # existing fields unchanged, in order; new fields keyword with defaults
    ...
    options: tuple[LeverOption, ...] = ()
    change_sources: Mapping[str, ChangeSource] = MappingProxyType({})
    bounds_required: bool = False   # D-P6.57: a protective lever; no recommendation until 6b's bounds
    no_action_words: str = "KEEP"
```

`generator_stop_reserve` gains `change_sources = {"candidate_l": STUDY, "battery_throughput_kwh": STUDY}` and
`no_action_words = "KEEP_SETTINGS"` (data only; its path is unchanged). The nine new rows are §5.

### 3.2 `check_levers` / `_lever_fault` gain branches 15 to 22 (after 14, in this order; each refuses
`StructureError("STRUCTURE_LEVER", structure_key, lever_id)`)

15. `generator` not in `GENERATORS`.
16. `set(change_sources) != set(changes)`, or a source kind not in (`STUDY`, `RECORD`).
17. `SETTING_GRID` with `options` non-empty, or `STATED_OPTIONS` with `axes` non-empty, `options` empty or
    `key_template` non-empty.
18. An option key fails `_OPTION_KEY`, equals `no-action`, or repeats within the lever.
19. An option `kind` not in `OPTION_KINDS`.
20. An option's `changes` empty, not a subset of `Lever.changes`, or not in `Lever.changes` order.
21. `no_action_words` not in `NO_ACTION_WORDS`.
22. `bounds_required` true while the purpose row's home category is not `protect`.

Existing branches (D-P6.63): 1 (a row's lever names no lever), 2 to 5 (structure, purpose row, purpose lists the
lever, changes are leaves) and 14 (pin home category) run for every lever. 6 to 13 (axes, template, integral values,
grid keys) run only when `generator == "SETTING_GRID"`: wrap them in one `if`, order unchanged. An unknown generator
skips 6 to 13 and is refused at 15. The class rule of §5.3 is a separate function
(`check_lever_paths`).

### 3.3 `DecisionService.prepare` (`decisions/records.py`)

- P5 for `STATED_OPTIONS`: `current` must be `{}`, else `BAD_CURRENT`. (`SETTING_GRID` unchanged.)
- P7 for `STATED_OPTIONS`: options are no action (position 0, `settings {}`), then `lever.options` in catalogue order,
  each `OptionRow(..., option_key=o.key, generator="STATED_OPTIONS", settings={}, position=i)`.
- `prepare_decision.py`: `--current` becomes optional (default empty); for a `SETTING_GRID` lever an empty current
  still refuses `BAD_CURRENT` (P5 unchanged).
- `MemoryDecisionStore` mirrors every rule.

### 3.4 Migration `0073_named_option_levers.py`

```sql
ALTER TABLE decision_option DROP CONSTRAINT decision_option_generator_check;
ALTER TABLE decision_option ADD CONSTRAINT decision_option_generator_check
    CHECK (generator IN ('NO_ACTION', 'SETTING_GRID', 'STATED_OPTIONS'));
ALTER TABLE option_evaluation_run DROP CONSTRAINT option_evaluation_run_outcome_check;
ALTER TABLE option_evaluation_run ADD CONSTRAINT option_evaluation_run_outcome_check
    CHECK (outcome IN ('RECOMMENDED', 'NO_ACTION_BEST', 'RANKING_INCOMPLETE', 'NOTHING_ADMITTED',
                       'BOUNDS_NOT_CHECKED'));
-- option_record: §6.1 (written in this migration so 6h is one head)
```

The names above are the live 0072 names (H4, checked by the reviewer with `pg_constraint` on a 0072 test DB:
`decision_option_generator_check`, `option_evaluation_run_outcome_check`). The packet lists them as read on the build's
test DB; a different name there stops the build and comes back to the Architect. `downgrade` restores both checks (refusing if a row holds a new value) and drops
`option_record`. `RUN_OUTCOMES` gains `BOUNDS_NOT_CHECKED`.

## 4. Unit 6h2: the evaluator branch (0.75 unit)

### 4.1 `decisions/run.py`

- E2: `STATED_OPTIONS` with a `study_path` refuses the new code `STUDY_NOT_FOR_LEVER` (exit 2). With none, the run
  reads no study (`study_sha256`, `study_identity` null; `months_averaged` empty).
- E3: `modelled = (NO_ACTION, SETTING_GRID, STATED_OPTIONS)`. D-P6.38 stands for anything else.
- E5 also reads `latest_option_records(tenant_id, decision_id)` (6h4; before 6h4 lands, an empty mapping).
- `option_inputs` (D-P6.66 N5) becomes `option_inputs(options, lever, study: StudyInput | None, by_key, admissions,
  one_offs, *, base: Mapping[str, LeafValue] | None = None, records: Mapping[tuple[UUID, str], OptionRecordRow] =
  MappingProxyType({}), grid_changes=SETTING_GRID_CHANGES)`. The defaults keep every 6c call unchanged. It gains the
  branch, keyed by generator name, before the existing `!= SETTING_GRID` refusal:

```python
if option.generator == STATED_OPTIONS:
    if base is None:
        raise RuntimeError("6h: a STATED_OPTIONS option needs the base")   # a caller fault, never a user refusal
    out.append(OptionInput(option, stated_changes(lever, option, base, records), None, None, one_offs.get(option.id)))
    continue
```

- For a `STATED_OPTIONS` lever the run passes `study=None`, `by_key={}`, `admissions={}`; E3's study block is skipped;
  `RunRow.study_sha256` and `study_identity` are None (0072's pair check holds); `months_averaged` is `()`.

### 4.2 `decisions/models.py` `stated_changes(lever, option, base, records) -> Mapping[str, LeafChange]`

For each leaf in the catalogue option's `changes` (in that order):
- source `STUDY` → `LeafChange(None, "MODELLED", (), (), ("OPTION_STUDY", "SIMULATION"))`.
- source `RECORD`, no record held → `LeafChange(None, "DECLARED", (), (), ("OPTION_RECORD", "DECISION"))`.
- source `RECORD`, record held (6h4; `records[(option.id, leaf)]`, keyed by option **and** factor) → the stated level
  minus the no-action level, which is always the base leaf's value (D-P6.66 N10, D-P6.65: the decision month's leaf;
  an option-only leaf's base is its `neutral`, filled by the sources):
  - a base leaf whose value is None → `LeafChange(None, "DECLARED", (), (), (base[leaf].missing.record_kind,
    base[leaf].missing.source_family))` (missing is never 0);
  - else `LeafChange(record.value - base[leaf].value, "DECLARED", ("option_record",), (record.origin,), None,
    currency=record.currency)` in the structure's decimal context (`_context()`, as `setting_changes`).
- A record in another currency than the base or the one-off is caught downstream by the existing `CURRENCY_MISMATCH`
  (difference) and `ONE_OFF_CURRENCY` (evaluator) through `LeafChange.currency` (D-P6.62). There is no
  `OPTION_RECORD_CURRENCY`.

### 4.3 `structure/difference.py` and `decisions/evaluate.py` (D-P6.57)

- `difference(registry, base, changes, *, also: tuple[str, ...] = ())`: the scope is each changed leaf, plus every
  node in the closure of `OUTCOME_FACTOR` or of a factor in `also` that rests on a changed leaf, plus
  `OUTCOME_FACTOR` itself always. A factor in scope resting on no changed leaf has change 0 (no missing).
  `evaluate_options` passes `also=(lever.purpose_factor,)` when the lever is given. Existing callers pass nothing; every
  6c fixture already reaches `OUTCOME_FACTOR`, so their results are byte-identical (test 8).
- `LeafChange` gains `currency: str | None = None` as its last field (D-P6.62). In `_Difference.delta` the currency
  collection reads `part.currency` for every part, `LeafChange` included (drop the `not isinstance(part, LeafChange)`
  guard; a `LeafChange` with currency None adds nothing, so 6c is unchanged).
- `_value_option` (D-P6.60, D-P6.61), generic, no generator named:
  - after the outcome's `_missing_inputs` and before the `ONE_OFF` check, for each leaf of `item.option`'s changed
    leaves in `changes` order whose `delta` is None, append `_leaf_input(leaf, changes, base)` unless an equal
    `MissingInput` is already in the list. Any missing input makes `value` None (existing line).
  - the row's evidence: `weakest((out.evidence, *[c.evidence for c in changes.values() if c.delta is not None]))`; if
    that is `NEUTRAL`, `weakest([c.evidence for c in changes.values()])`.
  - the row's source class: `_source_class(_origin_union(out.origins, *[c.origins for c in changes.values() if
    c.delta is not None]))` (`_origin_union` from `structure/evaluate.py`; export it in `__all__`).
- After R1 to R4, when `lever.bounds_required`: outcome `BOUNDS_NOT_CHECKED`; every non-baseline row with a value is
  `CONDITIONAL`, `reason_code "BOUNDS_NOT_CHECKED"`, rank null; rows without a value stay `DEFERRED`
  `VALUE_NOT_AVAILABLE`. A rejected row (R1) stays rejected (named options carry no admission, so none arises today).
  The outcome is `BOUNDS_NOT_CHECKED` even when no option is valued (D-P6.66 N9; Kisiwa, Ruiru `charger_restore`).
- `D-P6.46`'s closed map gains `OPTION_STUDY`, `OPTION_RECORD` (6f words, §7).

## 5. Unit 6h3: the catalogue, its words and the class check (1.25 units)

### 5.1 The nine levers (`LEVERS`, after `generator_stop_reserve`; all `STATED_OPTIONS`)

Each row: `lever_id`, structure, `purpose_factor`, `changes` (registry order), options (key, kind, changes), sources,
`bounds_required`, `no_action_words`. `key_template` is `""` and `axes` `()` for every named-option lever.

| lever_id | Structure | Purpose (home) | Changes · source | Options: key (kind) → changes | Bounds | No action |
|---|---|---|---|---|---|---|
| `backup_cover` | COLD_CHAIN | `nights_without_backup_cover` (protect P1) | `uncovered_nights` R (D-P6.59) | `stopgap-and-claim` (SUPPLIER_REMEDY) → `uncovered_nights`; `self-repair` (REPAIR) → `uncovered_nights` | true | WAIT_FOR_REMEDY |
| `chamber_efficiency` | COLD_CHAIN | `excess_kwh` (optimize O1) | `model_factor` R, `excess_kwh` R | `repair` (REPAIR) → `excess_kwh`; `replace` (CAPEX) → both | false | KEEP |
| `storage_contract` | COLD_CHAIN | `contract_crate_days` (grow G3) | `contract_crate_days` R, `contract_rate` R, `handling` R | `storage-contract` (DEMAND_CONTRACT) → all three | false | KEEP |
| `charging_schedule` | EV_DEPOT_CAPTIVE | `peak_kwh` (optimize O1) | `peak_kwh` S, `kwh_2200_2400` S, `kwh_0000_0500` S, `max_kw` S, `extra_missed_departures` S | `deadline-aware` (SCHEDULE) → all; `cheapest-window` (SCHEDULE) → all | false | KEEP |
| `charger_restore` | EV_DEPOT_CAPTIVE | `departures_missed` (protect P1) | `covered_bus_nights` R, `extra_missed_departures` R | `stopgap-and-claim` (SUPPLIER_REMEDY) → `covered_bus_nights`; `local-repair` (REPAIR) → `extra_missed_departures`; `reschedule` (SCHEDULE) → `extra_missed_departures` | true | WAIT_FOR_REMEDY |
| `fleet_capacity_use` | EV_DEPOT_CAPTIVE | `buses` (grow G2) | `buses` R | `absorb-part` (CAPACITY_USE) → `buses`; `absorb-all` (CAPACITY_USE) → `buses`; `add-chargers` (CAPEX) → `buses` | false | KEEP |
| `generator_redundancy` | MINI_GRID | `obligation_hours_without_redundancy` (protect P1) | `reduced_days` R | `repair` (REPAIR), `replace` (CAPEX), `add-storage` (CAPEX), each → `reduced_days` | true | KEEP |
| `productive_demand` | MINI_GRID | `productive_kwh` (grow G3) | `productive_kwh` R | `new-connection` (DEMAND_CONNECTION) → `productive_kwh` | false | KEEP |
| `fuel_reconciliation` | MINI_GRID | `unexplained_l` (optimize O1) | `unexplained_l` R | `investigate` (INVESTIGATION) → `unexplained_l` | false | KEEP |

R = `RECORD`, S = `STUDY` (D-P6.55). The implementer confirms each purpose and changed leaf against the live
registry rows before writing; a name that differs comes back to the Architect (no renaming in code).

### 5.2 Registry `levers` entries (data; registry versions unchanged, as 6a)

| Structure | Row | `levers` gains |
|---|---|---|
| COLD_CHAIN | `nights_without_backup_cover`, `uncovered_nights` (pin COLD_START_FAILURE), `excursion_crates` (pin COLD_EXCURSION) | `backup_cover` |
| COLD_CHAIN | `excess_kwh` | `chamber_efficiency` |
| COLD_CHAIN | `contract_crate_days` | `storage_contract` |
| EV_DEPOT_CAPTIVE | `peak_kwh` | `charging_schedule` |
| EV_DEPOT_CAPTIVE | `departures_missed`, `chargers_in_service` (pin EV_INTERRUPTION) | `charger_restore` |
| EV_DEPOT_CAPTIVE | `buses` | `fleet_capacity_use` |
| MINI_GRID | `obligation_hours_without_redundancy` | `generator_redundancy` |
| MINI_GRID | `productive_kwh` | `productive_demand` |
| MINI_GRID | `unexplained_l` (pin UNEXPLAINED_FUEL) | `fuel_reconciliation` |

Helpers (D-P6.66 N4): `rows_cold_chain.py` and `rows_ev_depot.py` `_leaf` and `_node` each gain the keyword
`levers: tuple[str, ...] = ()`, passed to `FactorRow(..., levers=levers)` as `rows_mini_grid._leaf` does;
`rows_mini_grid._node` gains the same keyword (for `obligation_hours_without_redundancy`, a node). Leaf rows above:
`uncovered_nights`, `excursion_crates`, `excess_kwh`, `contract_crate_days`, `peak_kwh`, `chargers_in_service`,
`buses`, `productive_kwh`, `unexplained_l`; node rows: `nights_without_backup_cover`, `departures_missed`,
`obligation_hours_without_redundancy`. The modules' docstrings drop "or a lever (step 6)". Registry versions are
unchanged (MINI_GRID stays 4). The two existing tests that assert the old listing change as §10.2 item 9 says.

### 5.3 The class rule (D-P6.53): `check_lever_paths`

`structure/check.py` gains `PENDING_LEVERS: Mapping[str, str] = MappingProxyType({})` (mechanism → the slice that
closes it) and `check_lever_paths(pins=None, registries=None, levers=None, pending=None)`: for each `PINS` mechanism in
order, the pinned row's `levers` must be non-empty, or the mechanism must be in `PENDING_LEVERS`; else
`StructureError("STRUCTURE_LEVER_PATH", structure_key, mechanism)`. A `PENDING_LEVERS` key whose pinned row lists a lever
refuses with that pin's structure key; a `PENDING_LEVERS` key that is not a `PINS` key refuses with structure key `""`
(D-P6.66 N12). Called in `check_all` on the line after `check_levers()` and added to `__all__`; 6a's
`test_2_the_real_data_passes_and_check_all_runs_it` stays green unchanged (the real data passes).

### 5.4 Lever words: `i18n/statements/en/decision_lever.py` (SC-1, keys `decision_lever.<name>`; D-P6.58)

One home for every lever's words, the generator lever's included; 6f's `title`, `question` and `option_label` rows
move here (6f amendment, §7). No digit, `%` or currency symbol in a template.

| Key | Variants |
|---|---|
| `title` (slot `site`) | `GENERATOR_STOP_RESERVE` "{site} generator stop setting" · `BACKUP_COVER` "{site} stock cover while the backup is restored" · `CHAMBER_EFFICIENCY` "{site} electricity above what occupancy explains" · `STORAGE_CONTRACT` "{site} storage contract" · `CHARGING_SCHEDULE` "{site} charging schedule" · `CHARGER_RESTORE` "{site} departures while a charger is restored" · `FLEET_CAPACITY_USE` "{site} extra buses on spare charging" · `GENERATOR_REDUNDANCY` "{site} evening supply on one generator" · `PRODUCTIVE_DEMAND` "{site} new daytime demand" · `FUEL_RECONCILIATION` "{site} fuel the model cannot explain" |
| `question` (slot `site`) | "What should we do about the {title}?" built per variant with the same words as `title` (ten variants, written out in the file) |
| `no_action` | `KEEP_SETTINGS` 6f's "Keep the current generator settings" · `KEEP` "Keep things as they are" · `WAIT_FOR_REMEDY` "Wait for the supplier's remedy" |
| `option_label` | generator: 6f's six variants move here unchanged · `STOPGAP_AND_CLAIM` "Put a stopgap in place and claim the repair from the supplier" · `SELF_REPAIR` "Repair it ourselves" · `REPAIR` "Repair it" · `REPLACE` "Replace it" · `STORAGE_CONTRACT` "Sign the storage contract" · `DEADLINE_AWARE` "Charge on a schedule that meets every departure" · `CHEAPEST_WINDOW` "Charge in the cheapest window only" · `LOCAL_REPAIR` "Have it repaired locally" · `RESCHEDULE` "Change the charging schedule around the fault" · `ABSORB_PART` "Take part of the offered buses" · `ABSORB_ALL` "Take all the offered buses" · `ADD_CHARGERS` "Add chargers" · `ADD_STORAGE` "Add battery storage" · `NEW_CONNECTION` "Connect the new customer" · `INVESTIGATE` "Investigate the fuel records" |
| `record` (slot `site`; one variant per lever and RECORD leaf, `<LEVER>__<LEAF>`) | `BACKUP_COVER__UNCOVERED_NIGHTS` "the rota: the nights it leaves uncovered" · `CHAMBER_EFFICIENCY__EXCESS_KWH` "the repair quote and the electricity above the model after the repair" · `CHAMBER_EFFICIENCY__MODEL_FACTOR` "the replacement's rated efficiency" · `STORAGE_CONTRACT__CONTRACT_CRATE_DAYS` "the storage contract's crate-days a month" · `STORAGE_CONTRACT__CONTRACT_RATE` "the storage contract's rate" · `STORAGE_CONTRACT__HANDLING` "the contract's handling cost a month" · `CHARGER_RESTORE__COVERED_BUS_NIGHTS` "the cover arranged: bus-nights charged elsewhere" · `CHARGER_RESTORE__EXTRA_MISSED_DEPARTURES` "the restore date and the departures it would miss" · `FLEET_CAPACITY_USE__BUSES` "the route offer: buses in the fleet" · `GENERATOR_REDUNDANCY__REDUCED_DAYS` "the repair or supply quote and its restore date" · `PRODUCTIVE_DEMAND__PRODUCTIVE_KWH` "the customer's signed demand a month" · `FUEL_RECONCILIATION__UNEXPLAINED_L` "the investigation's result" |
| `study` (slots `site`, `month`) | `CHARGING_SCHEDULE` "a charging replay of {site}'s own {month} under this schedule" |

A selector is the lever id or option key upper-cased with `-` → `_`. A key the catalogue names with no variant fails
test 7 (§10.2: every selector the catalogue names has its variant), so a new lever cannot ship without words.

## 6. Unit 6h4: option records (1.0 unit; owner Q3)

### 6.1 Table (in migration 0073)

```sql
CREATE TABLE option_record (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    option_id uuid NOT NULL,
    factor_id text NOT NULL CHECK (factor_id ~ ID_RE),
    value numeric(20, 6) NOT NULL,
    unit text NOT NULL CHECK (char_length(unit) BETWEEN 1 AND 32),
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    origin text NOT NULL CHECK (origin IN ('observed-financial', 'source-emulated')),
    document text NOT NULL CHECK (char_length(document) BETWEEN 1 AND 200 AND document = btrim(document)),
    basis text NOT NULL CHECK (char_length(basis) BETWEEN 1 AND 200 AND basis = btrim(basis)),
    declared_by_person_id uuid NOT NULL,
    declared_role text NOT NULL CHECK (declared_role IN ('SITE_MANAGER', 'FINANCE_AND_COMMERCIAL_LEAD')),
    declared_by_script boolean NOT NULL,
    declared_at timestamptz NOT NULL WS(declared_at),
    CONSTRAINT option_record_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, declared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_record_latest ON option_record (tenant_id, option_id, factor_id, declared_at DESC, id DESC);
```

Immutable and untruncatable by the 0072 trigger pattern. The newest record per (option, factor) is the one read.

### 6.2 `DecisionService.state_option_record(*, tenant_slug, as_email, decision_id, option_key, factor_id, value,
unit, currency, document, basis, emulated: bool) -> OptionRecordRow`

Permission `decision.option_record`: `(SITE_MANAGER, FINANCE)` in `accounts/permissions.py`; `records.COMMANDS` gains
`"option_record": "decision.option_record"`. Role as the one-off (D-P6.24) through `_covering_role(roles, site_id,
command)`, which reads `roles_of(command)`; the one-off call passes `COMMANDS["one_off"]` (D-P6.66 N8; behaviour
unchanged). `declared_by_script` is true from the CLI, as the one-off. Steps, first failure refuses (exit 2):
R1 `DECISION_NOT_FOUND`; R1b `PERSON_ROLE_REQUIRED`; R2 `OPTION_NOT_FOUND`; R3 `NO_ACTION_RECORD` (no action);
R4 `RECORD_NOT_ON_OPTION` (generator not `STATED_OPTIONS`, or the factor not in the catalogue option's `changes`, or its
source not `RECORD`); R5 `BAD_RECORD_UNIT` (`unit != str(registry.row(factor).unit)`); R6 `BAD_VALUE` (not finite,
more than 14 integer digits or 6 places); R7 `BAD_CURRENCY` (`registry.row(factor).unit.has_money_dimension` and
currency missing or malformed, or no money dimension and a currency; `contract_rate`, MONEY/DAY, needs one); R8 `BAD_DOCUMENT` / `BAD_BASIS` (`clean_title` fails); R9 write
(`origin = "source-emulated"` when `emulated`, else `"observed-financial"`).
Store: `add_option_record`, `latest_option_records(tenant_id, decision_id) -> Mapping[tuple[UUID, str],
OptionRecordRow]`, in both stores. CLI `backend/assetops_backend/state_option_record.py` on the `state_one_off.py`
pattern: `--tenant --as --decision --option --factor --value --unit [--currency] --document --basis [--emulated]`;
one JSON line. `decision.refused` gains the six codes with plain sentences (`NO_ACTION_RECORD` "Doing nothing has no
records to state."; `RECORD_NOT_ON_OPTION` "That option does not change that figure, or its change comes from a
simulation."; `BAD_RECORD_UNIT` "The unit does not match that figure's unit."; `BAD_VALUE` "Give a number with at most
six decimal places."; `BAD_DOCUMENT` "Name the document, in 1 to 200 characters."; `STUDY_NOT_FOR_LEVER` "This kind of
change is not valued from a simulation file.").

### 6.3 Meaning (D-P6.58)

A record states the leaf's level a month under the option, as the document gives it (the contract's crate-days, the
rota's uncovered nights, the cover's bus-nights), never a computed difference. The model computes the change and
every node; one figure per quantity.

## 7. Seams to other slices

- **6f** (amended in its spec): renders named options with `decision_lever.*` words; records-only list; new
  `missing`, `at_stake`, `outcome_note`, `disposition`, `reason`, `horizon_basis` variants (6f spec §3.4 rev 1).
- **DD6.2** (+0.25 u, DD's): WK `prepare` creates these decisions through `prepare_decision.py`, `state_one_off.py`,
  `state_option_record.py --emulated` and `evaluate_options.py`, as the manifest's people:

| Site | Lever | Period · horizon | Finding | Records (option: factor = value, document) | One-offs |
|---|---|---|---|---|---|
| Kobo | `generator_stop_reserve` | 2026-10 · 12 | GENERATOR_SUPPORT_CANDIDATE | (study, 0K4f) | as DD |
| Kisiwa | `generator_redundancy` | 2026-10 · 12 | none | none (values wait for quotes) | none |
| Mto | `productive_demand` | 2026-10 · 12 | none | none (6g) | none |
| Mwea | `storage_contract` | 2026-10 · 4 | none | `storage-contract`: `contract_crate_days` = 4500, `contract_rate` = 0.18 USD, `handling` = 100.00 USD; "Draft storage contract, Mwea Horticulture Aggregators" | 270.00 USD, 1 crew visit, "sales 150 + ethylene curtain 120" |
| Thika | `backup_cover` | 2026-10 · 1 | COLD_START_FAILURE | `stopgap-and-claim`: `uncovered_nights` = 0, "Night manual-start rota and SMS alarm relay" | 100.00 USD, 0, "SMS alarm relay and night rota labour" |
| Kirinyaga | `chamber_efficiency` | 2026-10 · 12 | none | none | none |
| Embakasi | `charging_schedule` | 2026-10 · 12 | none | none (study, D-P6.55) | none |
| Kasarani | `charger_restore` | 2026-11 · 1 | EV_INTERRUPTION | `stopgap-and-claim`: `covered_bus_nights` = the roster's covered nights (manifest `nights`), "Depot roster: short buses charged at Ruiru" | 90.00 USD, 0, "bus-nights charged at Ruiru: driver overtime and energy" |
| Ruiru | `fleet_capacity_use`; `charger_restore` | 2026-10 · 12; 2026-10 · 1 | none; EV_INTERRUPTION | none | none |

  Every value above is the manifest's record (grep the option id); DD6.2 reads them from the manifest, never retypes.
- **6g** shrinks to Mto's option records and the quotes emulator (≈3.25 u); **9c** to remedy records and notice
  deadlines (≈3.0 u); both use this generator. **6b** lifts `BOUNDS_NOT_CHECKED` for protective levers.

## 8. Page × Site-type matrix (range rule; what 6f will show from these records)

| Surface | Mini-grid (Kobo, Kisiwa, Mto) | Cold chain (Mwea, Thika, Kirinyaga) | EV (Embakasi, Kasarani, Ruiru) |
|---|---|---|---|
| Decisions list (October) | a record row per Site | a record row per Site | Embakasi, Ruiru (two); Kasarani's is November |
| Decision page | options named; Kobo values "needs a simulation of Kobo's own October" until 0K4f; Kisiwa and Mto name their quotes | Mwea valued and recommended; Thika valued, "No option recommended until the limits are checked"; Kirinyaga names its quote | Embakasi names the charging replay; Kasarani valued once November reads (G4: 150.00), until then names the November record; Ruiru names the route offer |
| Findings "Its decision" | the record's word | the record's word (Thika) | the record's word (Kasarani, Ruiru connector) |

Same columns and shape for every type; a value appears where its record exists; nothing is invented.

## 9. Mock deviations (rows in `.agent/mock-departure-register.md`)

| ID | Element | Cat. | Reason · resolving unit |
|---|---|---|---|
| MD-6H-1 | "Wait" options (THIKA-EPC-WAIT, KAS-OEM-WAIT) shown as doing nothing ("Wait for the supplier's remedy") | D4 | doing nothing is always the comparison (6a); waiting is that comparison · none |
| MD-6H-2 | MWEA-COMPRESSOR not under Mwea's contract decision | D4 | a compressor changes efficiency: it is `chamber_efficiency`'s `replace`, so the contract is valued alone · none |
| MD-6H-3 | Rights-anchored decisions (kobo-battery, mto-inverter, kisiwa-om, thika-insurance) absent | D1 | no rights row in the structure · 9a0, 9c |
| MD-6H-4 | Values for Kisiwa, Mto, Kirinyaga, Embakasi, Ruiru options | D1 | their records or replay not held · 6g, 9c, the EV replay (D-P6.55) |

## 10. Fixtures and tests (W2: written first; literals derived by hand)

### 10.1 Fixtures (`backend/tests/option_fixtures.py` gains)

- **N1 Mwea contract** (COLD_CHAIN, period 2026-10, horizon 4). Base: `crate_days` 4340, `rate` 0.20 USD,
  `k_kwh_per_crate_day` 0.25, `elec_price` 0.20 USD (RECORDED, `observed-financial`); others from `leaves_for`.
  Records: `contract_crate_days` 4500, `contract_rate` 0.18 USD, `handling` 100.00 USD (origin
  `observed-financial`). One-off 270.00 USD. Expected effects, registry order: `contract_crate_days` +4500,
  `contract_rate` +0.18, `handling` +100.00, `revenue` +810.00, `kwh_model` +1125, `kwh` +1125, `energy` +225.00,
  `cost_to_serve` +325.00, `contribution` +485.00. Effect currencies (D-P6.62; `Delta.currency` is set on
  `MONEY^1` rows only, as today; amended by D-P6.88: the `contract_rate` effect row stores its record's USD): `handling`, `revenue`, `energy`, `cost_to_serve`, `contribution` USD;
  `contract_rate` (MONEY/DAY, a price row) USD (D-P6.88); `contract_crate_days`, `kwh_model`, `kwh` None. Monthly 485.00; horizon
  1940.00; value 1670.00 USD; `RECOMMENDED` rank 1; outcome `RECOMMENDED`; `source_class` RECORDED.
  **N1e**: records `--emulated` → `source_class` EMULATED. **N1m**: no `handling` record → value null, missing
  `[OPTION_RECORD, DECISION, handling]`, outcome `RANKING_INCOMPLETE`. **N1k**: `contract_rate` record 0.18 **KES** →
  `contribution` change null, missing `[CURRENCY_MISMATCH, STRUCTURE, null]`, value null.
- **T1 Thika stopgap** (COLD_CHAIN, 2026-10, horizon 1, `backup_cover`). Base `uncovered_nights` 26 (RECORDED,
  `observed-financial`). Record `stopgap-and-claim`: `uncovered_nights` 0. One-off 100.00 USD. Effects:
  `uncovered_nights` −26, `nights_without_backup_cover` −26 (purpose closure), `contribution` 0 (currency USD from the
  one-off, D-P6.29/D-P6.34). Monthly 0; value −100.00 USD; evidence `DECLARED`; `source_class` RECORDED; `CONDITIONAL`
  `BOUNDS_NOT_CHECKED`; `self-repair` (no record, no one-off) `DEFERRED` `VALUE_NOT_AVAILABLE`, missing
  `[OPTION_RECORD, DECISION, uncovered_nights]`, `[ONE_OFF, DECISION, null]` (D-P6.59, D-P6.60), evidence `DECLARED`;
  outcome `BOUNDS_NOT_CHECKED`. **T1o**: `self-repair` with a one-off 50.00 USD and no record → still value null, missing
  `[OPTION_RECORD, DECISION, uncovered_nights]` only (the D-P6.60 plant reads −50.00). **T1e**: the stopgap record
  `--emulated` → `source_class` EMULATED, evidence `DECLARED` (D-P6.61). **T1b**: T1 plus a `self-repair` record
  `uncovered_nights` = 10, declared after the stopgap's → `self-repair` effects `uncovered_nights` −16,
  `nights_without_backup_cover` −16, `contribution` 0, missing `[ONE_OFF, DECISION, null]`, value null; the stopgap
  still −26 and −100.00 (records are read per option and factor, D-P6.66 N10).
- **K2 Kasarani stopgap** (EV, 2026-11, horizon 1, `charger_restore`). Base (RECORDED, USD): `chargers_in_service` 4,
  `charger_kw` 50, `import_limit_kw` 400, `window_h` 7, `peak_kwh` 0, `kwh_2200_2400` 18000, `kwh_0000_0500` 27000,
  `nights_in_period` 30, `buses` 11, `kwh_per_bus_night` 140, `short_nights` 8, `spare_bus_nights` 2,
  `penalty_rate` 120.00. Derivation: deliverable 1400, scheduled 1500, supplied 1400, required 1540, short 1, missed
  max(8 − 2 − 0, 0) = 6. Record `stopgap-and-claim`: `covered_bus_nights` 6. One-off 90.00 USD. Effects:
  `covered_bus_nights` +6, `departures_missed` −6, `penalties` −720.00, `cost_to_serve` −720.00, `contribution`
  +720.00. Value 630.00; `CONDITIONAL` `BOUNDS_NOT_CHECKED`; outcome `BOUNDS_NOT_CHECKED`.
- **S1 Embakasi** (`charging_schedule`, no one-off): both options missing the five `[OPTION_STUDY, SIMULATION, <leaf>]`
  in registry order, then `[ONE_OFF, DECISION, null]`; outcome `RANKING_INCOMPLETE`.
- **P1 prepare** for each of the nine levers on a Site of its type: option keys and positions as §5.1; a lever of
  another type refuses `LEVER_SITE_TYPE`; a non-empty `current` refuses `BAD_CURRENT`.

### 10.2 Tests

1. `test_6h_levers.py` (pure): the real `LEVERS` pass `check_levers` and `check_lever_paths`; one planted fault per
   branch 15 to 22 and per `check_lever_paths` rule, each refusing with the named code and key.
2. `test_6h_prepare.py`: P1; idempotent re-prepare; memory store parity.
3. `test_6h_evaluate.py`: N1, N1e, N1m, N1k, T1, T1o, T1e, T1b, K2, S1 literals; `STUDY_NOT_FOR_LEVER`; the
   existing F1/K1/C1/E1 tests unchanged and green.
4. `test_6h_option_record.py`: R1 to R9 each refusing; the newest record wins; role and person recorded.
5. `test_6h_migration_postgres.py`: upgrade and downgrade on a test DB; the new checks accept and refuse; immutability.
6. `test_6h_run_postgres.py`: N1 and T1 end to end through `build_evaluation` on ON1's Lakeside-style world with a
   cold Site of the test fixtures (or the DD world when merged), outcome and values as literals.
7. `test_6h_words.py`: every lever, option, record and study selector has its `decision_lever` variant; every
   template passes `check_literal` and the banned-word test.
8. `test_6h_parity.py` (D-P6.67; pure, memory store): byte-for-byte parity of what is meant to stay unchanged.
   **First commit of the slice, before any 6h code change:** `backend/tests/capture_6h_parity.py` writes
   `backend/tests/golden/6h_parity.json` from the base commit's code: (a) `difference(...)` for every call in
   `test_6c_difference.py` (F1b, F1a, zero throughput, no-delta, base candidate, C1, C1b, E1, product of two operands,
   currency plant, OPS, PRODUCT, NEUTRAL, DIVISION both calls), each `Delta` serialised field by field (Decimals as
   `str`, tuples as lists); (b) `evaluate_options` for every call in `test_6c_evaluate.py` with the generator lever
   (`TEST_LEVER` grid and `REAL_LEVER` on F1, K1) and with `lever=None` (C1, E1), the outcome and every `EvaluationRow`
   field with fixed ids; (c) `prepare` of `generator_stop_reserve` on the Site `test_6a_decisions.py`'s prepare tests use (option keys,
   positions, settings). The test recomputes each with the 6h code and asserts `json.dumps(..., sort_keys=True)` equal. If a row
   differs in evidence or source class only, the builder stops and returns to the Architect (D-P6.61's premise);
   any other difference is a 6h fault. The golden is never refreshed inside the slice.
9. **Existing tests that change (D-P6.66 N3; each changed as written, none loosened):**
   - `test_6c_difference.py::test_1_stated_records_are_never_read`: the signature assertion becomes
     `["registry", "base", "changes", "also"]`, and it also asserts `also` is keyword-only with default `()` (still no
     stated map).
   - `test_3b6_cold_ev_structures.py::test_1_order_counts_and_version` (line 171): `r.levers == ()` becomes: the
     mapping `{factor_id: r.levers for r in reg.rows if r.levers}` equals the §5.2 rows for that structure as a literal;
     `tolerance` and `stated_by` stay asserted None.
   - `test_6a_decisions.py::test_1_the_registry_row_lists_the_lever_and_no_other_does`: the listing literal becomes
     every §5.2 row (`("MINI_GRID", "candidate_l"): ("generator_stop_reserve",)` plus the twelve rows of the table),
     `REGISTRIES["MINI_GRID"].version == 4` kept.
   Every other existing test passes untouched (6a's planted lever cases refuse as today, D-P6.63).

### 10.3 Plants (each fails its named test; shown failing in the packet)

`stated` delta = record value instead of record − base (3, T1, T1b); records looked up by factor alone, newest of any
option, instead of (option, factor) (3, T1b: the stopgap reads −16) (replaces rev 0's option-only plant, which could
never fail; D-P6.66 N10); missing base read as 0 (3); `OUTCOME_FACTOR` not forced into scope (3, T1 KeyError); `also`
dropped (3, T1 effects); `bounds_required` ignored (3, T1/K2 rank 1); D-P6.60's changed-leaf misses removed (3, T1o
reads −50.00); D-P6.61 evidence from `out` only (6, T1 insert refused on Postgres; 3, T1e reads RECORDED);
`LeafChange.currency` not collected (3, N1 `revenue` currency None; N1k reads a value); grid branches 6 to 13 run for
every lever (1, the real `LEVERS` refused); branch 16 removed (1); `check_lever_paths` skipped for a pin with no lever
(1); oldest record read instead of newest (4); `--emulated` ignored (3, N1e); `STUDY_NOT_FOR_LEVER` removed (3); a 6c
result changed (8).

## 11. Done (questions; each can fail)

1. Does every Site type have at least one lever, and every pinned Finding a decision path, checked at start-up?
2. Do the same functions prepare and value a mini-grid, a cold-room and an EV decision, with no structure named in
   them?
3. Does Mwea's contract read 1670.00 over 4 months on N1, computed by the model from the contract's terms?
4. Does a protective decision (Thika, Kasarani) show its value and purpose-factor change but no recommendation?
5. Does an option without its record say which record, and never read 0?
6. Is Kobo's generator path, and every 6c result, byte-for-byte unchanged (test 8 against the base commit's golden)?
7. Does an option's own unrecorded leaf make its value null even when its leaf is outside `contribution` (T1o)?

## 12. Reviewer guide and handshake

**Reviewer focus:** the change rule (§4.2: record minus base, per option and factor, missing base named); the parity
golden captured before any change (test 8); the forced scope in `difference` (no existing
figure moves: run 6c's tests); `BOUNDS_NOT_CHECKED` never ranks; the class check's coverage; words exhaustive;
migration reversible; no figure typed into code (every literal in §5 is a name, not a value).

**Handshake: answered** (`handshake-review.md`; rulings D-P6.59 to D-P6.67 in this folder's `rulings.md`). H1 to H5
stand with the follow-ups below; B1 to B5 and N1 to N12 are folded into the sections above.

| # | Question | Default |
|---|---|---|
| H1 | Kasarani is valued on November; DD's EV Site inputs for 2026-11 may not read until Q11 (monthly cold and EV figures) | Gate G4 (§2, D-P6.64): 6h is done on K2 (unit); on the DD world Kasarani's page names the missing November record until Q11 reads, then reads 150.00 (DD6.2 asserts); the coordinator tells the owner the value waits on Q11 |
| H2 | Thika's `uncovered_nights` base for October | Read from the structure as recorded (26 on the manifest); if missing, the page names it (missing is never 0). The no-action level is that month's leaf, so the page shows uncovered nights −26, not nights to the supplier's restore (D-P6.65; owner asked to weigh in; the packet states it) |
| H3 | The generator lever's words move to `decision_lever` before 6f1 builds | Yes; 6f1 consumes them (D-P6.58) |
| H4 | Constraint names in 0072 differ from `<table>_<column>_check` | Checked: the live names are `decision_option_generator_check` and `option_evaluation_run_outcome_check` (§3.4); list them in the packet |
| H5 | `excursion_crates` lists `backup_cover` (an excursion's response is a cover decision) | Yes; another excursion cause gets its own lever later, added to the same row |

## 13. Out of scope

Bounds as rows (6b); remedy records and notice deadlines (9c); quotes emulator and Mto's records (6g); the EV
charging replay (queued by D-P6.55; it must amend E2, which refuses a study for every `STATED_OPTIONS` lever, so that
`charging_schedule` is valued from the replay: D-P6.66 N11); rights rows (9a0); the choice on screen (6f2); auto-prepare
from a Finding (D-P6.56); a forward no-action level from the supplier's restore date (9c, D-P6.65); a revenue or
contract term for Ruiru's `fleet_capacity_use` (the slice that values it; today its options can only read worse than
doing nothing).
