# 3B4: the structure observer, deviations stored as Findings (implementer spec)

Status: rev 2 (handshake round 1 answered, D-3B4.16 to D-3B4.26; coding may start under §0), Architect (Claude), 2026-11-21, written on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`; pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4; the
owner-level calls made here are rows 27 and 28 there). `delivery-plan.md` §2 row `3B4`: "Structure observer: deviations
stored as Findings under the owner's rule and outside the factor's tolerance (OD-3)" (step 3B, CH1, lane 2, 2.5 units,
depends on `3B3`, `3C1a`; page P3B, approved 20 Nov; non-screen). **3.5 units** (1.0 over the plan: today's Finding
store needs a domain arm and four readers that list Findings must leave the new domain out, D-3B4.9; the per-Site
tolerance needs a record, D-3B4.11; no split). Discovery review (W5): a new mechanism on a shared store, a migration
and a writer's table list. Non-screen; **adds no served text** (codes and typed values only, D-3B4.13, so D-SC1.28
does not hold it). `USER_REVIEW_REQUIRED: false`.

- **What it is.** After the analyst builds a closed month's snapshot (`3B7a`), one command reads it and, for every
  Site, compares each observed leaf's actual with its target. A deviation becomes a Finding in today's Finding store
  only when it is adverse by the leaf's declared direction and outside the leaf's tolerance; a favourable or neutral
  movement stays in the figures. A re-run on unchanged figures writes nothing; a changed figure revises the same
  Finding; a deviation that has gone is withdrawn on record. A second command lets the finance lead (money leaves) or
  the Site manager (operational leaves) declare a Site's tolerance, recorded with their name and time.
- **Design source:** `decision-loop-specification.md` §4 ("The structure observer", its acceptance tests) and §3
  (`tolerance`); `decisions-register.md` OD-3 ("yes configurable tolerance should dictate this"), Q-A1 (the owner's
  rule); `reuse-and-gap-matrix.md` line 45 ("Code only; Findings use today's store"; "Favourable movement raises
  nothing; unset tolerance raises every adverse deviation"); P3B ("`3B4` the observer").
- **Gate question it answers** (`delivery-plan.md` §3 step 3B): "Is a deviation raised as a Finding only under the
  owner's rule and outside its tolerance (OD-3)?" And part of "Does every stored Finding mechanism resolve to the factor
  it observes, through one registry row?" for the new mechanism (D-3B4.1).
- **Owner rules kept:** unknown is never zero (a side or a tolerance that cannot be read raises nothing and says so by
  code; it is never read as 0); people set tolerances, the system raises Findings (design §4 "Who"); a Finding claims
  its condition in its factor's unit, never money and never the value of acting; one mechanism for every factor (W6).
- **Builds on (merged on `main` at `eca96644d`):** `3B1` (`structure/registry.py` `REGISTRIES`, `FactorRow`,
  `Tolerance`, `HOMES`, `parsed_text`; `structure/check.py` `check_all`, `check_pins`, `StructureError`), `3B2`
  (`structure/pins.py` `PINS`), `3B3` (`structure/evaluate.py` `SiteStructure`, `FactorValue`, `EVIDENCE_ORDER`;
  `structure/expressions.py` `Bin`, `Neg`, `Ref`), `5a` (`structure/targets/read.py` `SiteTargets`), `5b`
  (`structure/attribution/rules.py` `BRIDGE_ROOTS`), `3B7a` (`structure_snapshot/read.py` `SnapshotRead.portfolio`,
  `structure_snapshot/model.py` `Served`, `PortfolioMonthSnapshot`, `SiteMonthSnapshot`; `structure_snapshot/codec.py`
  `canonical`, `digest`; `structure_snapshot/composition.py` `build_structure_snapshot`), the Finding store
  (`analytics/adapters/postgres_finding_store.py` `PostgresFindingStore`, its fuel methods `fuel_apply`,
  `_insert_fuel_finding`, `_insert_fuel_revision` as the pattern), the assessment store
  (`analytics/adapters/postgres_assessment_store.py` `transaction`, `fuel_balance_persist` as the pattern), `3C0a`/`3C1a`
  (`accounts/permissions.py` `COMMAND_ROLES`, `roles_of`, `FINANCE`, `SITE_MANAGER`; `AccountService.onboard_person`,
  whose `roles` are `(role, site_id)` pairs, 3A3), `structure_snapshot/store.py` `tenant_sites` and `get`,
  `commercial/months.py` `month_bounds`. Nothing from `3A6` or `3A7` (D-3B4.22).
- **Not what the brief assumed.** (1) Today's Finding store is not mechanism-neutral: two CHECKs admit four domains
  only, every Finding cites an analytic run and an assessment revision, and the chain-event trigger of `0044`
  feeds every new revision to the threads stage, whose `finding_source` raises `KeyError` on an unmapped domain and
  would block that Site's event queue (sweep, §4.4). (2) A tolerance "declared by the Site" (3B1 R12) has no record
  yet. Both are built here; neither is deferred.
- **Decisions:** `rulings.md` (D-3B4.1 to D-3B4.26; rev 2 answers are under "Handshake answers (round 1)"). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start (D-3B4.25):** the handshake has no open question; units 1 to 3 then start, with no wait for `4a` or `3B6`
  (3B4 never edits `structure/registry.py`, any row file or `structure/sources.py`, D-3B4.2). Only the `check.py` edit
  (§2.3: `OBSERVE_CODES`, `check_observed`, its call in `check_all`) and the tests that need it (1, 1b, 3) wait for
  both to merge (`git merge-base --is-ancestor <merge> main` for each; say so in the packet): one commit, the last of
  the build, before unit 4. Until then unit 1 writes `structure/observe/` and tests 2 and 4 to 9. No gate on `3A6` or
  `3A7` (D-3B4.22).
- **Unit 2 (gate A, the migration number):** read `main`'s head (`git show main:backend/migrations/versions/`,
  the highest file and its `revision`); the file is `00NN_structure_finding.py`, NN the next number, `down_revision`
  that head (D-3C2.9's rule). 0067 to 0070 are taken; if all four have merged this is `0071` on `0070`. **Gate B (merge
  preparation):** if `main`'s head moved, renumber on top of it and run `alembic heads` (one head); log it in the
  packet; it is not a mid-build question.
- **Branch** `task/3B4-observer` off `main`; worktree `/opt/assetecon/AssetOpsV1-3b4`; symlink `frontend/node_modules`
  from the main checkout.
- **Databases:** Postgres tests on `*_test` only, through `tools/heavy-slot.sh --db -- pwsh -NoProfile -File
  tools/run-host-tests.ps1 -- <file>`. Never ports 5490 or 8990, the walkthrough database or Docker. One migration.
  One guard line (§5.5), spec-level under OWNER-AWAY row 5 ("joining an existing table list under the same writer and
  shape"). No new writer block.
- **Read:** `rulings.md`; `structure/check.py` (whole), `structure/pins.py`, `structure/rows_mini_grid.py`,
  `structure/attribution/rules.py`, `structure/attribution/bridge.py:1-80` (the shapes `_terms` accepts),
  `structure/targets/rules.py`, `structure_snapshot/read.py`, `structure_snapshot/model.py`,
  `structure_snapshot/composition.py`, `build_structure_snapshot.py` (the command pattern),
  `analytics/adapters/postgres_finding_store.py:100-140`, `:260-320`, `:730-845`,
  `analytics/adapters/postgres_assessment_store.py:1394-1397`, `:1615-1680`, `fuel_balance/findings_service.py`,
  `fuel_balance/composition.py`, `chain/threads.py:25-45`, `:125-141`, `chain/adapters/postgres_thread_sources.py:20-60`,
  `:137-166`, `migrations/versions/0056_unexplained_fuel_finding.py` (whole), `0009_finding_store.py:33-110`,
  `load_emulated_exports.py:100-120`, `accounts/permissions.py:30-80`; tests `test_k4a_fuel_finding_postgres.py:120-280`,
  `test_5b_attribution.py:420-520`.
- **Pre-flight (report in the handshake):** (a) compute the structural signs of §2.2 for `MINI_GRID` and print, per
  leaf, its sign set; every leaf of `OBSERVED` must agree with §2.1's direction (a disagreement is a handshake
  question, not a fix). (b) Run the sweep of §4.4 again (and over the child tables `finding_revision_assessment`, `finding_revision_evidence`, `finding_merge`, D-3B4.23) on `main` (`grep -rn "FROM finding\b\|JOIN finding \|FROM
  finding_revision\|JOIN finding_revision" backend/assetops_backend`) and list any reader not in §4.4's table with its
  class. (c) In the 5b test world (`test_5b_attribution._world()`, pure; `READ_AT` is imported there from `test_3a4_commercial_months`), print Kobo's October actual and target values and
  evidence for the 19 observed leaves; §6 fixture F2 states what is expected.

## 1. Outcome and why

For a closed month, every adverse deviation of an observed leaf outside its tolerance is a Finding in today's store,
pinned to that leaf, with its condition in the leaf's unit; nothing else is. At Kobo in October (pack figures):
outstanding bills 278.00, adjustments 45 kWh, necessary running +30 L, candidate running 330 L and unexplained fuel
120 L (outside its 2 % band of 23.6 L); billed kWh above target raises nothing, and at Kisiwa 20 L of unexplained fuel
inside its 48 L band raises nothing.

Why it converts: monitoring tools alarm on readings. This raises a Finding only where the operator's own month moved
against their own target by more than they said they tolerate, on the exact factor the bridge prices. The executive's
reasons to act are the bridge's lines, and the tolerance is theirs to set (OD-3).

## 2. Unit 1: what is observed, and the rule (pure)

### 2.1 `structure/observe/rules.py` (D-3B4.2, D-3B4.3, D-3B4.4)

```python
UP, DOWN = "UP", "DOWN"                      # the adverse direction: a rise is adverse, a fall is adverse
MECHANISM = "STRUCTURE_DEVIATION"            # D-3B4.1: the one mechanism
OBSERVER_ANALYTIC = "structure-observer-1"   # not ANALYTIC_ID, and not under analytics/ (analytic-declaration guard)
OBSERVER_MODEL = "structure-observer-1/v1"
OBSERVER_MATCHER = "structure-observer/1"
DOMAIN = "structure"
KINDS = ("BOTTOM_LINE", "CASH", "PROTECT")   # D-3B4.4; derived, never declared
#: D-3B4.3: structure key -> leaf -> adverse direction. MINI_GRID order is the registry's leaf order.
OBSERVED: Mapping[str, Mapping[str, str]]
#: D-3B4.3: every other leaf of the structure -> why it is not observed. OBSERVED and NOT_OBSERVED cover every leaf once.
NOT_OBSERVED: Mapping[str, Mapping[str, str]]
REASONS = ("DECLARED_SOURCE", "OPTION_ONLY", "CALENDAR", "EXPOSURE_RATE", "NO_OWNER_RULE_KIND")
```

`OBSERVED["MINI_GRID"]` (19, in registry leaf order):

| Leaf | Dir | Leaf | Dir | Leaf | Dir |
|---|---|---|---|---|---|
| `delivered_kwh` | DOWN | `in_transit` | UP | `om` | UP |
| `unexplained_loss_kwh` | UP | `outstanding` | UP | `staff` | UP |
| `adjustments_kwh` | UP | `necessary_l` | UP | `reduced_days` | UP |
| `unmapped_kwh` | UP | `candidate_l` | UP | `unserved_critical_kwh` | UP |
| `tariff` | DOWN | `unexplained_l` | UP | `customer_hours_interrupted` | UP |
| `productive_kwh` | DOWN | `diesel_price` | UP | `dawn_days_below` | UP |
| `productive_tariff` | DOWN | | | | |

`NOT_OBSERVED["MINI_GRID"]` (12): `technical_loss_kwh`, `wear_rate`, `major_assets`, `standby_kw`, `lost_unit_kw`
DECLARED_SOURCE; `extra_l`, `battery_throughput_kwh`, `collection_cost` OPTION_ONLY; `period_days` CALENDAR;
`hours_per_day` EXPOSURE_RATE; `field_visits`, `liability` NO_OWNER_RULE_KIND.

`signs(registry, root) -> Mapping[str, frozenset[int]]` (pure): the sign with which each leaf enters `root`, walking
`registry.parsed`: `Bin` `+` passes `s` to both sides, `Bin` `-` passes `s` left and `-s` right, `Neg` passes `-s`, a
`Ref` to a node recurses into that node's expression with `s`, a `Ref` to a leaf records `s`, and `Bin` `*` whose two
sides are both `Ref` passes `s` to each (quantities and prices are non-negative). Any other shape (`Call`, `/`, `Num`,
`*` with a non-`Ref` side) records nothing below it. `reached(registry, key) -> Mapping[str, frozenset[int]]`: the
union over `BRIDGE_ROOTS[key]`; `first_root_leaves(registry, key)`: the leaves `signs(registry, BRIDGE_ROOTS[key][0])`
names. `kind_of(registry, key, leaf)`: `PROTECT` when the row's home category is `HOMES["protect"]`; else
`BOTTOM_LINE` when the leaf is in `first_root_leaves`; else `CASH`.

### 2.2 `structure/observe/observe.py` (D-3B4.5, D-3B4.6)

```python
@dataclass(frozen=True)
class ToleranceInForce:
    source: str                     # "SITE" (a declaration), "STRUCTURE" (the row's Tolerance), "NONE"
    of_factor: str | None
    pct: Decimal | None
    declaration_id: UUID | None     # SITE only

@dataclass(frozen=True)
class FactorObservation:
    factor_id: str
    direction: str                  # UP or DOWN
    kind: str                       # KINDS
    state: str                      # STATES, below
    unit: str                       # str(row.unit)
    currency: str | None            # the actual's, for a money unit; else None
    actual: Decimal | None
    target: Decimal | None
    gap: Decimal | None             # actual - target; None unless both are values in one currency
    band: Decimal | None            # None unless the tolerance could be computed
    tolerance: ToleranceInForce
    actual_evidence: str
    target_evidence: str
    sources: tuple[str, ...]        # sorted union of the actual's and the target's sources
    origins: tuple[str, ...]        # the actual's origins

STATES = ("ACTUAL_NOT_AVAILABLE", "TARGET_NOT_AVAILABLE", "CURRENCY_MISMATCH", "NO_GAP", "FAVOURABLE",
          "TOLERANCE_NOT_AVAILABLE", "INSIDE_TOLERANCE", "RAISED")
NOT_COMPUTED = ("ACTUAL_NOT_AVAILABLE", "TARGET_NOT_AVAILABLE", "CURRENCY_MISMATCH", "TOLERANCE_NOT_AVAILABLE")

def in_force(registry, factor_id, site_declaration: ToleranceInForce | None) -> ToleranceInForce
def observe(actual: SiteStructure, target: SiteStructure,
            declarations: Mapping[str, ToleranceInForce]) -> tuple[FactorObservation, ...]
def observe_site(site: SiteMonthSnapshot, declarations: Mapping[str, ToleranceInForce]) -> tuple[FactorObservation, ...]
    # = observe(site.actual, site.targets.structure, declarations): the one place the actual side is chosen (D-3B4.26)
def basis(o: FactorObservation, structure_key: str, month: str) -> str   # sha256 hex
```

- `observe` refuses `StructureError("STRUCTURE_COMPOSE", key, site_code)` unless both sides share site code, month,
  key and version; it reads `REGISTRIES[key]` and returns one observation per leaf of `OBSERVED[key]`, in that order
  (a key not in `OBSERVED`: `StructureError("STRUCTURE_OBSERVE_KEY", key, "-")`).
- `in_force`: a `SITE` declaration given for the leaf wins; otherwise the row's `tolerance` as `STRUCTURE`; otherwise
  `NONE`. (`declarations` holds only `SET` declarations in force; a `CLEARED` one is simply absent, so the row's default
  applies again, D-3B4.6.)
- The state, first match wins, every step in `Context(prec=34, rounding=ROUND_HALF_EVEN)`, nothing quantised:
  1. actual value `None`: `ACTUAL_NOT_AVAILABLE`; 2. target value `None`: `TARGET_NOT_AVAILABLE`; 3. money unit and
  the two currencies differ: `CURRENCY_MISMATCH`; 4. `gap == 0`: `NO_GAP`; 5. `UP` and `gap < 0`, or `DOWN` and
  `gap > 0`: `FAVOURABLE`; 6. band: `NONE` gives `Decimal(0)`; a tolerance with `pct == 0` gives `Decimal(0)` without reading `of_factor`
  (D-3B4.19); otherwise `pct / 100 * abs(actual[of_factor].value)`, and an `of_factor` actual of `None` is
  `TOLERANCE_NOT_AVAILABLE`; 7. `abs(gap) <= band`: `INSIDE_TOLERANCE`; 8.
  `RAISED`. Strictly outside: a gap equal to its band is inside.
- The target side is 5a's as given (a declared line, or a labelled assumption such as leak at zero); it is never
  replaced. The actual side is the un-carried actual (`site.actual`, never `site_bridge(...).actual`), so a cost line not received reads
  `ACTUAL_NOT_AVAILABLE`, never a gap against its own budget line (D-3B4.5).
- `basis`: `codec.digest(codec.canonical({...}))` over `structure_key`, `month`, `factor_id`, `direction`, `kind`,
  `state`, `unit`, `currency`, `actual`, `target`, `gap`, `band` (decimals as `format(d, "f")`, `None` as null),
  `tolerance` (`source`, `of_factor`, `pct` normalised so `5` and `5.00` agree; never its id), `actual_evidence`, `target_evidence`, `sources`, `origins`.
  No instant and no snapshot id enter it, so a rebuilt snapshot with the same figures has the same basis.

### 2.3 The start-up check (`check.py`; D-3B4.2; the last commit of unit 1, after 4a and 3B6 merge)

Add `OBSERVE_CODES = ("STRUCTURE_OBSERVE_KEY", "STRUCTURE_OBSERVE_COVER", "STRUCTURE_OBSERVE_LEAF",
"STRUCTURE_OBSERVE_SOURCE", "STRUCTURE_OBSERVE_DIRECTION", "STRUCTURE_OBSERVE_KIND")` and
`check_observed(observed=None, not_observed=None, registries=None) -> None` (a `None` reads the real table at call
time, as `check_pins`; this module imports `structure.observe.rules` as a module at the top; `check_observed` reads `TARGET_RULE` through a
function-local import of `structure.targets.rules`; `observe/rules.py` imports only `registry`, `expressions` and
`attribution.rules`, never `check`, `evaluate`, `targets.rules` or `observe.observe`, and `observe/__init__.py` holds a
docstring only: D-3B4.20, test 1b).
`check_all()` with no argument calls it after `check_pins()`; `check_all(registries=X)` does not. Code-major, each
over keys in `OBSERVED` order, then leaves in table order; the error names `(code, key, leaf)`:
- `KEY`: a key of `OBSERVED` absent from `REGISTRIES`, `BRIDGE_ROOTS` or `TARGET_RULE`, or `OBSERVED` and
  `NOT_OBSERVED` with different keys (leaf `-`);
- `COVER`: a leaf of the registry in neither table or in both, an entry of either table that is no row of the registry,
  a `NOT_OBSERVED` entry that is a node, or a reason not in `REASONS`;
- `LEAF`: an `OBSERVED` entry whose row is a node (so a node is `LEAF`'s, never `COVER`'s, D-3B4.16);
- `SOURCE`: an `OBSERVED` leaf whose `row.filled_by.family` is `DECLARED` or `CALENDAR`, or whose `row.absent` is
  `OPTION_ONLY` or `NEVER_EMPTY`;
- `DIRECTION`: a direction not in `(UP, DOWN)`; or `reached` gives `{-1}` and the direction is `DOWN`, `{1}` and
  `UP`, or both signs;
- `KIND`: a leaf `reached` does not name whose `row.home` (may be `None`) is not in `HOMES["protect"]`.

## 3. Unit 1: the pin (D-3B4.1)

No row is added to `PINS` and no entry to `outcome_map.ENTRIES`; `check_pins` is unchanged and still passes. The
observer's Finding names its leaf in its key (§4.2), and `observe.rules.pin_of_key(finding_key) -> tuple[str, str]`
returns `(structure_key, factor_id)`, refusing `ValueError` for a key that does not match `KEY_PATTERN` (§4.2). The
Finding's category is its leaf's home category (OD-21), read at call time from `REGISTRIES`. Its claim lists
`also_pinned`: the `PINS` mechanisms on the same leaf (`candidate_l`: `GENERATOR_SUPPORT_CANDIDATE`; `unexplained_l`:
`UNEXPLAINED_FUEL`), so a screen can open the month's deviation to those episodes without counting either twice.

## 4. Unit 2: the store

### 4.1 Migration `00NN_structure_finding` (D-3B4.7, D-3B4.11)

- Recreate `finding_domain_subject` and `finding_revision_domain_minutes` exactly as `0056` left them
  (`DOMAIN_SUBJECT_0056`, `DOMAIN_MINUTES_0056`, copied as literals) plus one arm each:
  `OR (domain = 'structure' AND subject_asset_id IS NULL AND generator_asset_id IS NULL)` and
  `OR (domain = 'structure' AND candidate_minutes IS NULL AND necessary_minutes IS NULL AND indeterminate_minutes IS NULL)`.
  0056's `_domain_checks` shape. No bounds CHECK: `episode_start` and `episode_end` are already `NOT NULL` (D-3B4.24).
- The tolerance declarations, append-only:

```sql
CREATE TABLE structure_tolerance (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    structure_key text NOT NULL CHECK (structure_key ~ '^[A-Z][A-Z_]{1,39}$'),
    factor_id text NOT NULL CHECK (factor_id ~ '^[a-z][a-z0-9_]{0,63}$'),
    state text NOT NULL CHECK (state IN ('SET', 'CLEARED')),
    of_factor text NULL CHECK (of_factor IS NULL OR of_factor ~ '^[a-z][a-z0-9_]{0,63}$'),
    pct text NULL CHECK (pct IS NULL OR pct ~ '^[0-9]{1,3}(\.[0-9]{1,2})?$'),
    valid_from text NOT NULL CHECK (valid_from ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    recorded_at timestamptz NOT NULL,
    recorded_by uuid NOT NULL,
    recorded_role text NOT NULL CHECK (recorded_role IN ('FINANCE_AND_COMMERCIAL_LEAD', 'SITE_MANAGER')),
    recorded_by_script boolean NOT NULL,
    CONSTRAINT structure_tolerance_set CHECK ((state = 'SET') = (of_factor IS NOT NULL AND pct IS NOT NULL)),
    CONSTRAINT structure_tolerance_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id)
);
CREATE INDEX structure_tolerance_site ON structure_tolerance (tenant_id, site_id, factor_id, recorded_at);
CREATE TRIGGER structure_tolerance_immutable BEFORE UPDATE OR DELETE ON structure_tolerance
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
- Downgrade: lock `finding, finding_revision, structure_tolerance`; refuse (`"00NN downgrade requires no structure
  Findings or tolerance declarations"`) while any `domain = 'structure'` Finding or revision or any tolerance row
  exists; else drop the trigger, index and table and restore the two 0056 CHECKs.

### 4.2 The assessment store: `structure_persist` (D-3B4.7)

`PostgresAssessmentStore.structure_persist(c, tenant_id, site_id, month, window: tuple[datetime, datetime], run_basis:
str, as_of: datetime, factor_id: str, result: dict, basis: str, now) -> dict` on the caller's connection, returning
`{"revision_id", "run_id"}`:
- the run: reuse the `analytic_run` with `(site, OBSERVER_ANALYTIC, OBSERVER_MODEL, window, input_sha256 =
  run_basis)` if it exists (`analytic_run_basis_unique`), else insert one: `knowledge_cutoff` = `as_of`,
  `cohort_status` `'COMPLETE'`, `cohort_sha256` `sha256_json([])`, `cohort` `'[]'`, `configuration_sha256` =
  `run_basis`, `foundation_revision_ids` and `binding_set_revision_ids` `'[]'`, `role_coverage` and `watermarks`
  `'{}'`, `selection` `'EXPLICIT'`, `job_id` NULL, `status` `'COMPLETED'`, `started_at` = `completed_at` = `now`; no
  `analytic_run_evidence` row;
- the assessment revision: `assessment_key` = `f"{factor_id}:{month}"`, `revision_no` = that key's max + 1,
  `claim_level` `'COMPLETE'`, `result` = `result` (the claim of §4.3), `evidence_ids` `'[]'`, `basis_sha256` = `basis`,
  window as above; and its `analytic_run_assessment` row, scope `'WINDOW'`.
`run_basis` is `sha256_json` of the Site-month's sorted `(factor_id, basis)` pairs.

### 4.3 The Finding store: `structure_held`, `structure_apply`, tolerances (D-3B4.8, D-3B4.11)

Key: `KEY_PATTERN = r"structure:(?P<key>[A-Z][A-Z_]+):(?P<factor>[a-z][a-z0-9_]*):(?P<month>[0-9]{4}-[0-9]{2}):(?P<dir>UP|DOWN)"`,
written `f"structure:{key}:{factor}:{month}:{direction}"`.

`structure_apply(c, tenant_id, site_id, structure_key, month, window, observation, *, basis, claim, input_evidence_sha256, persist, now) ->
UUID | None`: `persist` is a callable `(c) -> {"revision_id", "run_id"}` the service binds to `structure_persist`, called
only when a revision is written. The latest revision of the key's Finding (`structure_held`: `(finding_id, lifecycle,
basis_sha256)` or None) and the observation's state decide, first match wins:

| Held | Observation state | Write (transition / lifecycle) |
|---|---|---|
| none | `RAISED` | open the Finding; `OPENED` / `SUPPORTED` |
| none | any other | nothing |
| `SUPPORTED`, same basis | `RAISED` | nothing |
| `SUPPORTED` | `RAISED` | `SUPPORT_CHANGED` / `SUPPORTED` |
| `NO_LONGER_SUPPORTED` or `UNCONFIRMED` | `RAISED` | `REOPENED` / `SUPPORTED` |
| `SUPPORTED` or `UNCONFIRMED` | `NO_GAP`, `FAVOURABLE`, `INSIDE_TOLERANCE` | `NO_LONGER_SUPPORTED` / `NO_LONGER_SUPPORTED` |
| `SUPPORTED` | in `NOT_COMPUTED` | `UNCONFIRMED` / `UNCONFIRMED` |
| anything else | anything else | nothing |

- The Finding row: `domain` `'structure'`, `mechanism` `MECHANISM`, `analytic_id` `OBSERVER_ANALYTIC`,
  `generator_asset_id` and `subject_asset_id` NULL, `anchor_start` = the month's start (`window[0]`),
  `anchor_assessment_revision_id` = the first `persist` revision, `cohort_sha256` NULL, `matcher_version`
  `OBSERVER_MATCHER`, `split_from_finding_id` NULL, `recurs_after_finding_id` = the Finding of the same Site, key,
  leaf and direction for the previous month when its latest lifecycle is `SUPPORTED`, else NULL (D-3B4.8),
  `opened_at` = `created_at` = `now`.
- The revision: `domain` `'structure'`, `claim_level` `'COMPLETE'`, `title` = `MECHANISM` (a code, never words,
  D-3B4.13), `mechanism`, `matcher_version`, `analytic_id`, `model_version` `OBSERVER_MODEL`, `assessment_revision_id`
  and `analytic_run_id` from `persist`, `window_assessment_revision_id` NULL, `episode_start`/`episode_end` = `window`,
  the three minutes NULL, `claim` (below), `limitations` `'[]'`, `basis_sha256` = `basis`, `support_sha256` =
  `sha256_json(list(observation.sources))`, `cited_evidence_sha256` = `sha256_json([])`, `input_evidence_sha256` = the
  Site snapshot row's `payload_sha256`, read by the service through `store.get(tenant_id, [site.snapshot_id])` and
  passed in (D-3B4.21; never in `basis`); one `finding_revision_assessment` row (`'WINDOW'`, primary). No
  `finding_revision_evidence` row.
- `claim` (`format` 1; decimals as strings in plain notation): `structure_key`, `structure_version`, `factor_id`,
  `home` (category code), `objective`, `kind`, `month`, `direction`, `state`, `unit`, `currency`, `actual`, `target`,
  `gap`, `band`, `tolerance` (`source`, `of_factor`, `pct`, `declaration_id`), `actual_evidence`, `target_evidence`,
  `sources`, `origins`, `also_pinned`, `snapshot_id`, `snapshot_as_of`, `tolerance_known_at`: exactly these 25 keys with `format` (D-3B4.18). "No money" means no
  bridge value, no effect of acting and no priced line; a money-unit leaf's own `actual`, `target`, `gap` and `band`, in
  its unit and currency, are the condition and stay.
- Tolerances: `tolerance_append(row) -> UUID` (one plain INSERT; `recorded_at` from the store's `clock_timestamp()`);
  `tolerances(tenant_id, site_id) -> tuple[ToleranceRow, ...]` every row `ORDER BY recorded_at, id`. The service picks,
  per leaf, the latest row with `valid_from <= month` and `recorded_at <= known_at`; `SET` gives a `SITE`
  `ToleranceInForce`, `CLEARED` gives none.

### 4.4 The readers that must leave the domain out (D-3B4.9; the sweep, W6)

| Reader (path:symbol) | Today with a `structure` row | Change |
|---|---|---|
| `chain/adapters/postgres_thread_sources.py` `_FINDING_SOURCES` (and `_FINDING_SOURCES_BY_ID`, built from it) | `finding_source` raises `KeyError` (`SUBJECT_COLUMN`); the `finding.revised` event from `0044` is never consumed and blocks the Site's later events; the backfill aborts | add `AND f.domain <> 'structure'` before the `ORDER BY`; the event is consumed with nothing placed |
| `analytics/adapters/postgres_finding_store.py` `_fence` (revision count) | an observer write moves the dispatch fence: a spurious re-plan and `SELECTION_MOVED_DURING_READ` | count `WHERE ... AND domain <> 'structure'` |
| `postgres_finding_store.py` `finding_detail` | `GET /api/sites/{site_code}/findings/{id}` renders it as a dispatch Finding (minutes "None", the code as title) | the first `SELECT * FROM finding` adds `AND domain <> 'structure'` (the route answers its not-found) |
| `postgres_finding_store.py` `rows` (CLI `finding-rows`, `finding-reads`), five selects | dumped; `finding-reads` would read each through `finding_detail` and fail on None; the Site-wide `finding_revision_assessment` list would hold links to revisions the other list removed | `finding` and `finding_revision` add `AND domain <> 'structure'`; `finding_revision_assessment`, `finding_revision_evidence` and `finding_merge` add `AND finding_revision_id IN (SELECT id FROM finding_revision WHERE tenant_id = :t AND site_id = :s AND domain <> 'structure')` (D-3B4.23) |

`thread_sources._FINDING_LIFECYCLE` (a whole-Site scan consumed only through a thread's occurrences, which a structure Finding never has) loads the row and never uses it, and `work/adapters/postgres_work_read.py`
`_pin` degrades to no pin; both are left unchanged (named in the packet). Every other read is by id, by a named
domain, mechanism or analytic, or by an Action's origin (the sweep's class A, 57 statements). The `financial_consequence_dirty` trigger is narrowed to `mini_grid` (0022, not widened by 0056), the cold one is its own trigger; the EV assessment trigger for `ev-session/1` only.

### 4.5 The guard (one line)

`tools/checks/configuration-persistence.ps1`: `$findingTables` gains `'structure_tolerance'` (the Finding store
writes it with a plain INSERT; it is then insert-only, never upserted, and no other module writes it). No other
guard edit.

## 5. Unit 3: the service and the two commands

### 5.1 `structure/observe/service.py`

`StructureObserver(snapshots: SnapshotRead, store: StructureSnapshotStore, findings, assessments, clock)` with
`run(tenant_id, month) -> RunResult` (`RunResult(month, snapshot_id, as_of, sites: Mapping[str, SiteResult],
excluded: Mapping[str, tuple[str, ...]])`, `SiteResult(states: Mapping[str, str], written: tuple[Written, ...])`,
`Written(factor_id, transition, finding_id, revision_id)`):
1. `served = snapshots.portfolio(tenant_id, month)`; refuse with `ObserveRefused(code)`, nothing written:
   `NO_SNAPSHOT` (state `NO_SNAPSHOT`), `REBUILD_NEEDED` (state `REBUILD_NEEDED`), `SNAPSHOT_NOT_CURRENT`
   (`freshness.current` false), `MONTH_OPEN` (the portfolio row or any Site snapshot has `closed_at_build` false).
2. `known_at = clock()` once (UTC). Per Site in `served.snapshot.asked` order that is in `served.snapshot.sites`: read
   its tolerances (`findings.tolerances`), `observe_site(site, declarations)`, then in one
   `assessments.transaction()`: `pg_advisory_xact_lock(hashtext('structure-observe:' || site_id || ':' || month))`,
   then `findings.structure_apply` per observation, in `OBSERVED` order. One Site's failure rolls back that Site only and
   propagates after the earlier Sites committed.
   A Site whose `site.actual.structure_key` is not a key of `OBSERVED` is not observed: it is returned in `excluded`
   with `("STRUCTURE_NOT_OBSERVED",)` and nothing is written for it (D-3B4.25).
3. Sites in `served.snapshot.sites_excluded` are returned in `excluded` with their reasons, unchanged.

`structure/observe/composition.py` `build_structure_observer(database_url) -> Wiring` (`Wiring(observer, store,
findings, dispose)`; the commands use `store.tenant_sites` and `findings.tolerances`): the
snapshot service from `structure_snapshot.composition.build_structure_snapshot`, `analytics.composition`
`build_finding_store` and `build_postgres_assessment_store` (as `fuel_balance/composition.py` does), the clock
`datetime.now(timezone.utc)`; a failure disposes what was built.

### 5.2 `python -m assetops_backend.observe_structure run --tenant SLUG --month YYYY-MM`

`build_parser()` public; `main(argv, *, observer=None, accounts=None)`. Exit 2 before any work: `NO_DATABASE`,
`BAD_MONTH`, `UNKNOWN_TENANT` (`store.tenant_sites(slug)` is `None`, as `build_structure_snapshot.py:79`; no `AccountService` call, D-3B4.22); exit 3 an `ObserveRefused` (its code); exit 0 one JSON
line `{"month", "snapshot_id", "as_of", "sites": {code: {"states": {factor: state}, "written": [{"factor_id",
"transition", "finding_id", "revision_id"}]}}, "excluded": {code: [reasons]}}`. stderr carries the code alone (no
sentence, D-3B4.13). Runbook line (in the packet): after `build_structure_snapshot build` for a closed month, run
`observe_structure run` for that month.

### 5.3 `python -m assetops_backend.declare_tolerance {set,clear,show}`

- `set --tenant SLUG --site CODE --factor F --of OF --pct P --from YYYY-MM --as EMAIL`; `clear --tenant --site --factor
  --from --as`; `show --tenant --site --month YYYY-MM` (one JSON line: per observed leaf
  `{"factor_id", "source", "of_factor", "pct", "declaration_id"}` in force now).
- Refusals, exit 2, nothing written, in this order: `NO_DATABASE`, `UNKNOWN_TENANT`, `SITE_UNKNOWN` (not the tenant's,
  or its type has no structure), `FACTOR_NOT_OBSERVED` (not in `OBSERVED[key]`), `OF_FACTOR_UNIT` (`--of` not a row of
  the registry, or its unit differs from the leaf's: 3B1's `STRUCTURE_TOLERANCE` rule), `PCT_INVALID` (not
  `^[0-9]{1,3}(\.[0-9]{1,2})?$`, or not `0 <= pct <= 100`; 0 is accepted and gives band 0, D-3B4.19), `BAD_MONTH`, `PERSON_NOT_FOUND` (`AccountService.onboard_person(email)` is `None`, not `active`, or its `tenant_id` is not the
  tenant's; D-3B4.22), `PERSON_ROLE_REQUIRED`: the command key is `structure.tolerance.money` when the leaf's unit
  has a money dimension (`outstanding`, `in_transit`, `om`, `staff`, `tariff`, `productive_tariff`, `diesel_price`),
  else `structure.tolerance.operational`; the admitting role is the first of `roles_of(key)` for which `OnboardPerson.roles` holds a `(role, site_id)` pair,
  and a `SITE_MANAGER` pair counts only when its `site_id` is this Site's.
- `accounts/permissions.py` `COMMAND_ROLES` gains, at the end: `"structure.tolerance.money": (FINANCE,)` and
  `"structure.tolerance.operational": (SITE_MANAGER,)`.
- Success, exit 0: `{"state": "SET"|"CLEARED", "declaration_id", "factor_id", "of_factor", "pct", "valid_from",
  "recorded_by", "recorded_role", "recorded_by_script": true}`.

## 6. Fixtures (the pack's own figures; the tests write the expected values, W2)

- **F1, the pack sides (pure).** For Kobo, Kisiwa and Mto: leaves from `derived-values.json`
  `sites.lakeside-power/<Site>.actual.nodes` (evidence `RECORDED`, source `pack:actual`, currency `USD` on money
  units) and `.plan.nodes` (evidence `DECLARED`, source `pack:plan`), every MINI_GRID leaf; both sides evaluated with
  `evaluate(REGISTRIES["MINI_GRID"], leaves)`; no declarations unless a test says so. Expected, written in the test
  (all other observed leaves `NO_GAP`):

| Site | `RAISED` (leaf: gap, kind) | `FAVOURABLE` | `INSIDE_TOLERANCE` |
|---|---|---|---|
| Kobo | `adjustments_kwh` 45 BOTTOM_LINE; `outstanding` 278 CASH; `necessary_l` 30, `candidate_l` 330, `unexplained_l` 120 (band 23.6) BOTTOM_LINE | `delivered_kwh` (+550) | none |
| Kisiwa | `adjustments_kwh` 30; `outstanding` 270 CASH; `necessary_l` 80; `reduced_days` 2 PROTECT | `delivered_kwh` (+450) | `unexplained_l` 20 (band 48) |
| Mto | `unexplained_loss_kwh` 120, `adjustments_kwh` 40, `unmapped_kwh` 140, `necessary_l` 20 BOTTOM_LINE; `in_transit` 150, `outstanding` 120 CASH; `reduced_days` 4 PROTECT | `delivered_kwh` (+400) | none |

- **F2, the 5b test world (pure, real reads; a memory store, no database).** `test_5b_attribution._world()` and its `reads` (`READ_AT` is imported there from `test_3a4_commercial_months`); Kobo October at
  `READ_AT`: `outstanding` `RAISED`, gap `278.00`, kind `CASH`; every observed leaf whose actual the world does not
  supply reads `ACTUAL_NOT_AVAILABLE`, never `RAISED` (pre-flight (c) lists which; a difference from this is a
  handshake question).
- **F3, the Postgres world.** One tenant, one MINIGRID Site `KOBO-001` (Africa/Nairobi), months `2026-10` and
  `2026-11`, a fake `SnapshotRead` returning F1's Kobo sides as `SiteMonthSnapshot`s (`closed_at_build` true,
  `freshness.current` true) and a fake `StructureSnapshotStore` whose `get` returns a `SnapshotRow` with a known
  `payload_sha256` per Site snapshot id (the portfolio row's differs), a fixed clock; one FINANCE person and one SITE_MANAGER bound to `KOBO-001`, one
  SITE_MANAGER bound to another Site.

## 7. Tests (written first)

`backend/tests/test_3b4_observer.py` (no database):
1. `OBSERVED` and `NOT_OBSERVED` equal the test's own literal tables of §2.1; `check_all()` passes (no argument) (waits
   for 4a and 3B6, §0).
1b. Import order (waits with 1): three fresh interpreters, `python -I -c "import assetops_backend.structure.check"`, then
   `...structure.observe.rules`, then `...structure.evaluate`, each first; all exit 0 (D-3B4.20). With 3B6 merged, `check_all()`
   still passes though `REGISTRIES` holds keys `OBSERVED` does not name.
2. `signs` on MINI_GRID gives `{-1}` for every UP leaf of the table reached from a root and `{1}` for every DOWN leaf,
   from a literal expected map; the four Protect leaves and `hours_per_day` are not reached.
3. Each `check_observed` code fires on one planted table and on no earlier code (one per code: `KEY` an `OBSERVED` key
   with no registry; `COVER` `dawn_days_below` removed from both, and a `NOT_OBSERVED` entry that is no row; `LEAF`
   `billed_kwh` added to `OBSERVED`; `SOURCE` `technical_loss_kwh` moved to `OBSERVED`; `DIRECTION` `outstanding` DOWN;
   `KIND` `field_visits` added as UP).
4. F1: every Site's states, gaps and kinds as §6's table; `band` 23.6 and 48 exact; no `RAISED` observation has
   `FAVOURABLE` direction (the rule's halves both asserted).
5. Tolerance: Kobo `necessary_l` with a SITE `ToleranceInForce(of_factor="diesel_l", pct=5)` is `INSIDE_TOLERANCE`
   (band 59), with `pct=2` `RAISED` (23.6); Kisiwa `unexplained_l` with `of_factor="unexplained_l", pct=100` (band
   20 = gap) is `INSIDE_TOLERANCE`; Mto with `delivered_kwh` actual removed and `unexplained_loss_kwh` declared
   `of_factor="delivered_kwh", pct=1` is `TOLERANCE_NOT_AVAILABLE`; a SITE declaration beats the row's default;
   `pct=0` (D-3B4.19): Kobo `necessary_l` gives band 0 and `RAISED` (gap 30), also with its `diesel_l` actual removed
   (band known, not `TOLERANCE_NOT_AVAILABLE`); Kisiwa `unexplained_l` with `pct=0` over the row's 2 % is `RAISED` (gap 20,
   band 0).
6. Unknown is not zero: Kobo with `om` actual removed reads `ACTUAL_NOT_AVAILABLE` (not a gap of −600); a target
   `None` reads `TARGET_NOT_AVAILABLE`; a currency pair `USD`/`KES` reads `CURRENCY_MISMATCH`.
6b. The un-carried actual (D-3B4.26): `observe_site` on a `SiteMonthSnapshot` built from Kisiwa's real inputs and targets
   (`test_5b_attribution._kisiwa()`, where `om` is carried by `site_bridge`) reads `om` `ACTUAL_NOT_AVAILABLE`, while
   `site_bridge(inputs, targets).actual` holds a value for it.
7. `basis` ignores instants and snapshot ids and changes with any listed field (one field at a time); `pct` `5` and
   `5.00` give one basis.
8. F2 as §6.
9. `pin_of_key` round-trips a written key and refuses three malformed ones; the claim's `also_pinned` for
   `candidate_l` and `unexplained_l` as §3; `check_pins()` unchanged.

`backend/tests/test_3b4_observer_postgres.py` (F3, `*_test`):
10. The migration: the two CHECKs equal 0056's plus the arms (the `test_k4a_fuel_finding_postgres.py:205` shape);
    a structure row with a subject asset is refused; downgrade refuses with a row and succeeds without.
11. Lifecycle: October run opens 5 Findings (OPENED/SUPPORTED) with the claim of §4.3; a second run writes nothing;
    a rebuilt snapshot with the same figures (new `as_of`, new id, new row digest) writes nothing; `candidate_l` 340 gives
    SUPPORT_CHANGED; a SITE tolerance on `necessary_l` (5 % of `diesel_l`) gives NO_LONGER_SUPPORTED; `clear` then
    re-run gives REOPENED; `outstanding` actual removed gives UNCONFIRMED; November's `candidate_l` Finding has
    `recurs_after_finding_id` = October's; each revision's `input_evidence_sha256` equals the Site row's `payload_sha256`
    (not the portfolio's); each claim's key set equals §4.3's 25 keys exactly (a literal set).
12. Each run writes one `analytic_run` per Site-month basis and one `assessment_revision` per revision written.
13. Readers: with structure Findings stored, the threads stage (`scheduling/stages.py` `chain_threads`) consumes the
    `finding.revised` events, places nothing and raises nothing; `finding_detail` returns None for a structure id;
    `rows()` holds no structure row or link in any of its five lists (`findings`, `revisions`, `assessments`, `evidence`,
    `merges`, each asserted); `_fence`'s revision count is unchanged by an observer run (one assertion per reader
    predicate, D-3B4.17).
14. Refusals: `NO_SNAPSHOT`, `REBUILD_NEEDED`, `SNAPSHOT_NOT_CURRENT`, `MONTH_OPEN`, each writing nothing.
15. Tolerance command: FINANCE sets `outstanding`; FINANCE on `necessary_l` is `PERSON_ROLE_REQUIRED`; the bound
    SITE_MANAGER sets `necessary_l`; the other Site's SITE_MANAGER is `PERSON_ROLE_REQUIRED`; each other refusal of
    §5.3 once (`PCT_INVALID` for `100.5`, `abc` and `-1`; `0` accepted); `show` reads the declaration in force; the row is insert-only (an UPDATE raises).

Regression, run in the build: `test_3b1_structure_registry.py`, `test_3b2_findings_pinned.py`,
`test_3b3_structure_evaluate.py`, `test_5b_attribution.py`, `test_k4a_fuel_finding_postgres.py`, the chain threads
tests (`python tools/select-tests.py --base main` names them), and the 3B7a snapshot tests.

## 8. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.0) | §2, §3; pre-flight (a); tests 2, 4 to 9 now; tests 1, 1b, 3 and the `check.py` edit last, after 4a and 3B6 merge | 2 |
| 2 (1.25) | §4 (migration, two stores, the four readers with their five `rows()` selects, the guard line); pre-flight (b); tests 10 to 13 | 2 |
| 3 (0.75) | §5 (service, composition, two commands, two roles); tests 14, 15; pre-flight (c) and test 8 if not done | 1 to 2 |
| 4 (0.5) | the `check.py` commit if not yet made; regression; plants (reviewer guide, 23); check-all; packet | 1 |

Total 3.5 (D-3B4.15; re-estimated after the handshake, unchanged). Packet `specs/3B4-observer/packet.md`: the sweep table of §4.4 re-run, gate A/B numbers, the
plants run, the runbook line, residual risks `R-FENCE-FUEL` (D-3B4.9), `R-NO-OPPORTUNITY` (D-3B4.4), `R-ASSUMED-TARGET`
(D-3B4.5), the mid-build count.

## 9. Done (questions; each can fail)

1. Is a Finding written only for an observed leaf whose deviation is adverse by its declared direction and strictly
   outside its tolerance, with every other state writing nothing (tests 4, 5, 11)?
2. Does every observed direction agree with the sign the bridge roots give it, and does start-up refuse a planted
   disagreement, an observed node, a declared or option-only leaf, an unplaced kind and an uncovered leaf (tests 2, 3)?
3. Unknown is not zero: is a missing actual, target, currency or tolerance basis a named state that never raises, and
   is a cost line not received never a gap (tests 5, 6)?
4. Does a re-run on unchanged figures write nothing, even from a rebuilt snapshot, and does each change write exactly
   the transition of §4.3's table (test 11)?
5. Is each Finding in today's store, domain `structure`, pinned by its key to one registry leaf, with its claim in the
   leaf's unit and no money (tests 9, 11; the claim's key set a literal)?
6. Does no reader of today's Findings show, count or choke on a structure Finding, `rows()` included in all five lists (test 13, §4.4 re-run)?
7. Is a tolerance declared only by the finance lead (money) or the Site's manager (operational), recorded with person
   and time, and read by month and as known (test 15)?
8. Are the only guard change `$findingTables`' new name, the only migration `00NN_structure_finding`, and no served
   text added (`git diff main...HEAD -- backend/assetops_backend/i18n` empty)? Does each plant fail its named test?
   Mid-build count 0?

## 10. Out of scope

Opportunity Findings from a customer's record (no such record kind exists; D-3B4.4); observing nodes or cold and EV
structures (their targets do not exist: `TARGET_RULE` is MINI_GRID only); the daily automatic run (`3B7b`); words for
these Findings and any screen (`3B5`, `5c` or a later slice, as SC-1 statements); a tolerance screen (`3C0b`'s
Organisation settings); money on a Finding; linking the monthly Finding to its analytic episodes beyond `also_pinned`;
`R-FENCE-FUEL`'s wider fence fix.

## 11. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Which leaves are observed, and is every adverse deviation raised while no tolerance is set, including against an assumed target such as leak at zero? | §2.1's 19 leaves; yes, every adverse one (the design's call), against 5a's target as shown; the operator narrows it by tolerance (D-3B4.3, D-3B4.5; OWNER-AWAY row 27). **Owner to weigh in** |
| Q2 (owner) | Who sets a tolerance, and how in this fortnight? | The finance lead for money leaves, the Site manager for operational ones, by command naming the person (3A7 Q1's precedent), from a month on (D-3B4.11; row 28) |
| Q3 | One mechanism, or one per factor? | One, `STRUCTURE_DEVIATION`, its leaf in its key (D-3B4.1) |
| Q4 | Where does the adverse direction live? | `observe/rules.py`, checked against the bridge's signs; not on `FactorRow` (D-3B4.2) |
| Q5 | Are structure Findings shown on today's screens? | No, until a screen slice adds their words as SC-1 statements (D-3B4.9, D-3B4.13) |
| Q6 | `liability` (customer compensation) is not under contribution in P3B's structure, so it cannot be a bottom-line Finding | Not observed (`NO_OWNER_RULE_KIND`); queued as a structure question for the owner with 3B5 |
