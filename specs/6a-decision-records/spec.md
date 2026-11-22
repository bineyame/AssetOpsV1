# 6a: decisions, options and their records (implementer spec)

**Status: in_review (units 1 to 3 built; `packet.md`).** Was: rev 2, handshake answered (`handshake.md`; D-P6.20 to D-P6.29). P6 approved by the owner, 22 Nov 2026 ("accept all p6 defaults",
`owner/owner-accept-p6-defaults-2026-11-22.md`); every default is decided (§10) and logged as D-P6.1 to D-P6.19
(`specs/6-decision-valued/rulings.md`). Architect (Claude), 2026-11-21 rev 0, 2026-11-22 rev 1 and rev 2. Lane 3 (`delivery-plan.md` §2,
row `6a`). **3.25 units**, three commits. Discovery review (W5): new schema, a person rule, the record every money
figure of step 6 hangs on. `USER_REVIEW_REQUIRED: true` (it fixes what a decision is; no screen).

- **Owner proposal (approved):** `specs/6-decision-valued/P6-proposal.md`. **Rulings:** `specs/6-decision-valued/rulings.md`.
  **Reviewer guide:** `reviewer-guide.md` (this folder).
- **What it is.** Step 6's records: a **decision** on a Site's factor, opened by the Finding there (when there is one),
  with its **options**, always including **no action**; each option's **one-off cost** stated by a person; the
  **evaluation runs** `6c` writes (values, effects, dispositions); and the **choice** the executive makes, under their
  name, freezing the run they saw. Three commands write them (prepare, state a one-off, choose); one read serves `6f`
  and the IA's Decisions list (D-P6.8). 6a computes no value: `6c` does.
- **The mechanism it sits in** (owner, decisions inside the outcome mechanism): outcome `contribution` → driver
  `candidate_l` (a 3B1 factor) → evidence (the Finding pinned to it by 3B2, `structure/pins.py`
  `GENERATOR_SUPPORT_CANDIDATE`) → **lever** `generator_stop_reserve` (new here) → options and the choice (here) →
  action (the agreed Action of 3C2, linked here; the carrier of `6d`) → verify (`6e`, `8a`).
- **Builds on (merged on `main`):** `3B1` (`structure/registry.py` `FactorRow.levers`, deferred to step 6 by
  `structure/check.py:21`), `3B2` (`structure/pins.py`), `3C0a` (`operator_account`, `AccountService.onboard_person`,
  `ledger_append_only()`), `3C1a` (`accounts/permissions.py` `COMMAND_ROLES`, `roles_of`), `3A6`
  (`AccountService.tenant_by_slug`), `3C2` (`agreed_action`, migration `0070`; the command pattern of
  `record_action`), SC-1a (statements; D-3C2.14's pattern), `0K4d` (`runs/replay_study.py` `KOBO_GRID`, read by
  test 1 only).
- **Mock:** non-screen. It supplies what vNEXT `#/decision/kobo-generator` shows in its option rows (option, the
  no-action row) and its "Who decides" panel (the recommendation's source run, the chooser's name and time, the linked
  Action), and the rows of the IA's Decisions list (IA-P spec, "The list defs"; it replaces 5c's L2 panel "Decisions",
  MD2) (D-P6.8). `6f` builds those screens; 6a adds no route and changes no served string (D-P6.9).

## 0. Before you start (gates; each is a hard stop)

- **Gate P (owner): met.** P6 approved, 22 Nov 2026; §10 holds the decided answers (D-P6.13 to D-P6.19).
- **Gate A (migration number).** Read `main`'s head (`git show main:backend/migrations/versions/`). At this writing it
  is `0071_person_on_actions`, so the file is `0072_decision_records.py`, `revision = "0072_decision_records"`,
  `down_revision = "0071_person_on_actions"`. Write the head and number in the packet. Gate B (merge preparation):
  renumber on top of any newer head and run `alembic heads` (one head), as 3C2 §0.
- **Gate S (seams).** `git grep -n "PINS" main -- backend/assetops_backend/structure/pins.py` shows the map, and
  `git grep -n "def tenant_by_slug" main -- backend/assetops_backend/accounts/service.py` one line.

## 1. Outcome and why

After the deep-dive, the analyst prepares Kobo's generator decision for October 2026:
`python -m assetops_backend.prepare_decision --tenant lakeside-power --as wanjiru@lakeside-power.example --site KOBO-001 --lever
generator_stop_reserve --period 2026-10 --current stop_soc_pct=90,reserve_soc_pct=30`. It writes one decision with
14 options: no action, plus the 13 other points of the lever's grid. The site manager states each option's one-off
cost. `6c` values the options. The executive chooses one option, or none, and the choice is kept with their name and
the run they saw. Gate questions: does every decision hold exactly one no-action option, enforced by the database?
Can only the executive choose, and only once per decision? Is the run behind a choice frozen? Does a re-run of
prepare write nothing new? Is every record append-only?

## 2. Unit 1: migration `0072_decision_records`

The 0062 and 0070 style: one raw `UPGRADE` string through `op.execute`; no column defaults; every write's values come
from the adapter. `WS(col)` below stands for the whole-second check of 0070:
`CHECK (date_trunc('second', col AT TIME ZONE 'UTC') = col AT TIME ZONE 'UTC')`. `ID_RE` is
`'^[a-z][a-z0-9_]{0,63}$'`.

```sql
ALTER TABLE agreed_action ADD CONSTRAINT agreed_action_tenant_id_unique UNIQUE (tenant_id, id);

CREATE TABLE decision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NOT NULL,
    structure_key text NOT NULL CHECK (structure_key IN ('MINI_GRID', 'COLD_CHAIN', 'EV_DEPOT_CAPTIVE')),
    lever_id text NOT NULL CHECK (lever_id ~ ID_RE),
    purpose_factor_id text NOT NULL CHECK (purpose_factor_id ~ ID_RE),
    finding_id uuid NULL,
    period text NOT NULL CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    horizon_months integer NOT NULL CHECK (horizon_months BETWEEN 1 AND 60),
    current_settings jsonb NOT NULL CHECK (jsonb_typeof(current_settings) = 'object'),
    rule_version text NOT NULL CHECK (rule_version = 'decision-prepare-1'),
    prepared_by_person_id uuid NOT NULL,
    prepared_role text NOT NULL CHECK (prepared_role = 'ANALYST'),
    prepared_by_script boolean NOT NULL,
    prepared_at timestamptz NOT NULL WS(prepared_at),
    CONSTRAINT decision_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id, finding_id) REFERENCES finding (tenant_id, site_id, id),
    FOREIGN KEY (tenant_id, prepared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE UNIQUE INDEX decision_once ON decision (tenant_id, site_id, lever_id, period, finding_id) NULLS NOT DISTINCT;
CREATE INDEX decision_tenant ON decision (tenant_id, prepared_at DESC, id DESC);

CREATE TABLE decision_option (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    option_key text NOT NULL CHECK (option_key ~ '^[a-z0-9][a-z0-9-]{0,63}$'),
    generator text NOT NULL CHECK (generator IN ('NO_ACTION', 'SETTING_GRID')),
    settings jsonb NOT NULL CHECK (jsonb_typeof(settings) = 'object'),
    position integer NOT NULL CHECK (position >= 0),
    CONSTRAINT decision_option_no_action_key CHECK ((generator = 'NO_ACTION') = (option_key = 'no-action')),
    CONSTRAINT decision_option_no_action_first CHECK ((generator = 'NO_ACTION') = (position = 0)),
    CONSTRAINT decision_option_tenant_id_unique UNIQUE (tenant_id, id),
    CONSTRAINT decision_option_key_unique UNIQUE (decision_id, option_key),
    CONSTRAINT decision_option_position_unique UNIQUE (decision_id, position),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id)
);

CREATE TABLE option_one_off (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    option_id uuid NOT NULL,
    amount numeric(14, 2) NOT NULL CHECK (amount >= 0),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    crew_visits integer NOT NULL CHECK (crew_visits >= 0),
    basis text NOT NULL CHECK (char_length(basis) BETWEEN 1 AND 200 AND basis = btrim(basis)),
    declared_by_person_id uuid NOT NULL,
    declared_role text NOT NULL CHECK (declared_role IN ('SITE_MANAGER', 'FINANCE_AND_COMMERCIAL_LEAD')),
    declared_by_script boolean NOT NULL,
    declared_at timestamptz NOT NULL WS(declared_at),
    CONSTRAINT option_one_off_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, declared_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_one_off_latest ON option_one_off (option_id, declared_at DESC, id DESC);

CREATE TABLE option_evaluation_run (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    evaluator_version text NOT NULL CHECK (evaluator_version ~ '^option-evaluator-[0-9]+$'),
    outcome text NOT NULL CHECK (outcome IN ('RECOMMENDED', 'NO_ACTION_BEST', 'RANKING_INCOMPLETE', 'NOTHING_ADMITTED')),
    study_sha256 text NULL CHECK (study_sha256 IS NULL OR study_sha256 ~ '^[0-9a-f]{64}$'),
    study_identity jsonb NULL CHECK (study_identity IS NULL OR jsonb_typeof(study_identity) = 'object'),
    known_at timestamptz NOT NULL WS(known_at),
    run_by_person_id uuid NOT NULL,
    run_role text NOT NULL CHECK (run_role = 'ANALYST'),
    run_by_script boolean NOT NULL,
    run_at timestamptz NOT NULL WS(run_at),
    CONSTRAINT option_evaluation_run_study_pair CHECK ((study_sha256 IS NULL) = (study_identity IS NULL)),
    CONSTRAINT option_evaluation_run_tenant_id_unique UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id),
    FOREIGN KEY (tenant_id, run_by_person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX option_evaluation_run_latest ON option_evaluation_run (decision_id, run_at DESC, id DESC);

CREATE TABLE option_evaluation (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    run_id uuid NOT NULL,
    option_id uuid NOT NULL,
    disposition text NOT NULL
        CHECK (disposition IN ('COMPARISON', 'RECOMMENDED', 'CONDITIONAL', 'ACCEPTABLE', 'DEFERRED', 'REJECTED')),
    reason_code text NULL CHECK (reason_code IS NULL OR reason_code ~ '^[A-Z][A-Z0-9_]{0,63}$'),
    rank integer NULL CHECK (rank IS NULL OR rank >= 1),
    monthly_change numeric NULL,
    horizon_change numeric NULL,
    one_off_id uuid NULL,
    value numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    source_class text NOT NULL CHECK (source_class IN ('SIMULATED', 'EMULATED', 'RECORDED')),
    evidence_class text NOT NULL
        CHECK (evidence_class IN ('RECORDED', 'MEASURED', 'DECLARED', 'DERIVED', 'ESTIMATED', 'MODELLED')),
    missing jsonb NOT NULL CHECK (jsonb_typeof(missing) = 'array'),
    assumed jsonb NOT NULL CHECK (jsonb_typeof(assumed) = 'array'),
    admission jsonb NULL CHECK (admission IS NULL OR jsonb_typeof(admission) = 'object'),
    dawn jsonb NULL CHECK (dawn IS NULL OR jsonb_typeof(dawn) = 'object'),
    CONSTRAINT option_evaluation_value_or_missing CHECK ((value IS NULL) = (jsonb_array_length(missing) > 0)),
    CONSTRAINT option_evaluation_value_currency
        CHECK (value IS NULL OR currency IS NOT NULL OR disposition = 'COMPARISON'),
    CONSTRAINT option_evaluation_comparison
        CHECK (disposition <> 'COMPARISON' OR (value = 0 AND rank IS NULL AND one_off_id IS NULL)),
    CONSTRAINT option_evaluation_recommended_first CHECK (disposition <> 'RECOMMENDED' OR rank = 1),
    CONSTRAINT option_evaluation_tenant_id_unique UNIQUE (tenant_id, id),
    CONSTRAINT option_evaluation_once UNIQUE (run_id, option_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES option_evaluation_run (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, one_off_id) REFERENCES option_one_off (tenant_id, id)
);
CREATE UNIQUE INDEX option_evaluation_one_recommended ON option_evaluation (run_id) WHERE disposition = 'RECOMMENDED';

CREATE TABLE option_effect (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    evaluation_id uuid NOT NULL,
    factor_id text NOT NULL CHECK (factor_id ~ ID_RE),
    position integer NOT NULL CHECK (position >= 0),
    change_per_month numeric NULL,
    unit text NOT NULL CHECK (char_length(unit) BETWEEN 1 AND 32),
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    missing jsonb NOT NULL CHECK (jsonb_typeof(missing) = 'array'),
    CONSTRAINT option_effect_change_or_missing CHECK (CASE WHEN jsonb_typeof(missing) = 'array'
        THEN (change_per_month IS NULL) = (jsonb_array_length(missing) > 0) END),   -- D-P6.32
    CONSTRAINT option_effect_once UNIQUE (evaluation_id, factor_id),
    FOREIGN KEY (tenant_id, evaluation_id) REFERENCES option_evaluation (tenant_id, id)
);

CREATE TABLE decision_choice (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    decision_id uuid NOT NULL,
    option_id uuid NULL,
    run_id uuid NOT NULL,
    agreed_action_id uuid NULL,
    chosen_by_person_id uuid NOT NULL,
    chosen_role text NOT NULL CHECK (chosen_role = 'OPERATOR_EXECUTIVE'),
    chosen_by_script boolean NOT NULL,
    chosen_at timestamptz NOT NULL WS(chosen_at),
    CONSTRAINT decision_choice_once UNIQUE (decision_id),
    FOREIGN KEY (tenant_id, decision_id) REFERENCES decision (tenant_id, id),
    FOREIGN KEY (tenant_id, option_id) REFERENCES decision_option (tenant_id, id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES option_evaluation_run (tenant_id, id),
    FOREIGN KEY (tenant_id, agreed_action_id) REFERENCES agreed_action (tenant_id, id),
    FOREIGN KEY (tenant_id, chosen_by_person_id) REFERENCES operator_account (tenant_id, id)
);
```

- **Exactly one no-action option, by the database.** `decision_option_key_unique` and the `option_key` check give at
  most one. At least one: `CREATE FUNCTION decision_has_no_action() RETURNS trigger` (plpgsql) raises
  `'decision % has no no-action option'` (SQLSTATE `23514`) unless a `decision_option` with `decision_id = NEW.id AND
  generator = 'NO_ACTION'` exists; `CREATE CONSTRAINT TRIGGER decision_has_no_action AFTER INSERT ON decision
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION decision_has_no_action()`.
- **Every run covers every option, by the database.** `run_covers_options()` raises (SQLSTATE `23514`) unless the
  count of `option_evaluation` rows of `NEW.id` equals the count of `decision_option` rows of `NEW.decision_id`;
  a deferred constraint trigger `option_evaluation_run_complete AFTER INSERT ON option_evaluation_run`.
- **Cross-row checks in code, not SQL** (the adapter's transaction): an evaluation's option belongs to its run's
  decision; a choice's option and run belong to its decision; the `one_off_id` belongs to the evaluation's option.
  Each refuses `RECORD_INVALID` in both stores and has a test (D-P6.30).
- **Constraint names (handshake R4).** Every table-level and multi-column CHECK is named as above; column checks keep
  Postgres's `<table>_<column>_check`. Test 6 asserts each name; the packet lists them.
- **jsonb shapes (D-P6.27).** `settings` and `current_settings`: `{axis: decimal string}`. `missing`: a list of
  `[record_kind, source_family, factor_id or null]`. `assumed`: a list of factor ids. `admission`, `dawn`: 6c §3.5's
  objects, fractions `"n/d"` in lowest terms, integers as numbers. `MissingInput` round-trips exactly (test 7).
- **Append-only.** For each of the seven new tables: `<t>_immutable BEFORE UPDATE OR DELETE ... FOR EACH ROW` and
  `<t>_no_truncate BEFORE TRUNCATE ... FOR EACH STATEMENT`, both `EXECUTE FUNCTION ledger_append_only()`.
- **Downgrade.** `LOCK TABLE` all seven `IN ACCESS EXCLUSIVE MODE`; refuse with `RAISE EXCEPTION 'Downgrade of
  0072_decision_records refused: decision rows exist'` when any of the seven holds a row; else drop, in reverse order,
  the triggers, both functions, the indexes, the tables and `agreed_action_tenant_id_unique` (never
  `ledger_append_only()`).

## 3. Unit 2: levers, the records module and its rules

### 3.1 `structure/levers.py` (pure; read by `check.py` at start-up)

```python
@dataclass(frozen=True)
class SettingAxis:
    name: str                       # ID_RE; e.g. "stop_soc_pct"
    values: tuple[Decimal, ...]     # the grid along this axis, in the order tried; whole numbers for a key template
    unit: str                       # "%"

@dataclass(frozen=True)
class Lever:
    lever_id: str                   # ID_RE
    structure_key: str              # a key of REGISTRIES
    purpose_factor: str             # a row of that registry: the factor whose change is the lever's purpose
    generator: str                  # "SETTING_GRID" (the only generator in 6a)
    axes: tuple[SettingAxis, ...]
    key_template: str               # e.g. "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}"
    changes: tuple[str, ...]        # the leaves an option of this lever changes by a delta (6c; D-P6.3)

LEVERS: Mapping[str, Lever] = MappingProxyType({
    "generator_stop_reserve": Lever(
        "generator_stop_reserve", "MINI_GRID", "candidate_l", "SETTING_GRID",
        (SettingAxis("stop_soc_pct", tuple(Decimal(v) for v in (90, 85, 80, 75, 70, 65, 60)), "%"),
         SettingAxis("reserve_soc_pct", (Decimal(30), Decimal(25)), "%")),
        "stop-{stop_soc_pct}-reserve-{reserve_soc_pct}",
        ("candidate_l", "battery_throughput_kwh")),
})

def grid(lever: Lever) -> tuple[Mapping[str, Decimal], ...]   # first axis outermost, each in `values` order
def option_key(lever: Lever, point: Mapping[str, Decimal]) -> str   # template filled with format(v, "f") of whole v
```
- The grid is 0K4d's `KOBO_GRID` (`runs/replay_study.py:50-52`, on `main`), axis for axis, in the same order. Test 1
  writes the 13 keys as literals and also proves the grid equal to `KOBO_GRID` (`Fraction` against `Decimal` values).
- `rows_mini_grid.py`: the `candidate_l` row gains `levers=("generator_stop_reserve",)`. No other row changes. **No
  version bump** (handshake I4): `levers` changes no value, expression or source, and a bump would fail every stored
  v4 snapshot; the module docstring records "6a: `candidate_l` lists its lever; version unchanged (no value changes)".
- `check.py` replaces the "Deferred (D-3B1.6): levers (step 6)." docstring line with `check_levers(levers=None,
  registries=None, pins=None)`, run by `check_all()` between `check_pins()` and `check_observed()`, on the no-argument
  path only (it is cross-registry; `check(reg)` stays per-registry). It refuses with `StructureError("STRUCTURE_LEVER",
  structure_key, lever_id)` on fourteen branches, in this order (test 2 has one case each):
  1. a `FactorRow.levers` entry naming no `LEVERS` key;
  2. a lever whose `structure_key` is not in `REGISTRIES`;
  3. a `purpose_factor` that is not a row of that registry;
  4. a purpose factor's row that does not list the lever;
  5. a `changes` entry that is not a leaf of that registry;
  6. an axis name not `ID_RE`;
  7. an empty `values`;
  8. a repeated value in `values`;
  9. axes whose `unit` differ (D-P6.12);
  10. a template whose `{names}` differ from the axis names;
  11. a non-whole value under a template;
  12. two grid points with one key;
  13. a filled key outside the `option_key` form `^[a-z0-9][a-z0-9-]{0,63}$`;
  14. **OD-25 (D-P6.23):** a lever whose purpose factor's `home.category` differs from that of **any** pinned factor
      (`structure/pins.py` `PINS`) that lists the lever; test 2 also has a two-pin case (one agreeing, one not).
  The last rule is how a decision's heading cannot disagree at run time.

### 3.2 `decisions/records.py` (pure apart from the injected store and accounts)

New package `backend/assetops_backend/decisions/`. Codes only, no served text (D-0K4.19). Words come from §3.4.

```python
NO_ACTION_KEY = "no-action"
RULE_VERSION = "decision-prepare-1"
HORIZON_DEFAULT = 12                                    # D-P6.15 (owner default #3)
COMMANDS = {"prepare": "decision.prepare", "one_off": "decision.one_off", "choose": "decision.choose"}
DISPOSITIONS = ("COMPARISON", "RECOMMENDED", "CONDITIONAL", "ACCEPTABLE", "DEFERRED", "REJECTED")
RUN_OUTCOMES = ("RECOMMENDED", "NO_ACTION_BEST", "RANKING_INCOMPLETE", "NOTHING_ADMITTED")
SOURCE_CLASSES = ("SIMULATED", "EMULATED", "RECORDED")   # weakest first

@dataclass(frozen=True)
class DecisionRow: id; tenant_id; site_id; structure_key; lever_id; purpose_factor_id; finding_id: UUID | None
    period: str; horizon_months: int; current_settings: Mapping[str, Decimal]; rule_version: str
    prepared_by_person_id; prepared_role: str; prepared_by_script: bool; prepared_at: datetime
@dataclass(frozen=True)
class OptionRow: id; tenant_id; decision_id; option_key: str; generator: str; settings: Mapping[str, Decimal]
    position: int
@dataclass(frozen=True)
class OneOffRow: id; tenant_id; option_id; amount: Decimal; currency: str; crew_visits: int; basis: str
    declared_by_person_id; declared_role: str; declared_by_script: bool; declared_at: datetime
@dataclass(frozen=True)
class EffectRow: factor_id: str; position: int; change_per_month: Decimal | None; unit: str
    currency: str | None; missing: tuple[MissingInput, ...]
@dataclass(frozen=True)
class MissingInput: record_kind: str; source_family: str; factor_id: str | None
    # e.g. ("battery_wear_rate_assumption", "DECLARED", "wear_rate"); ("ONE_OFF", "DECISION", None)
@dataclass(frozen=True)
class EvaluationRow: id; option_id; disposition: str; reason_code: str | None; rank: int | None
    monthly_change: Decimal | None; horizon_change: Decimal | None; one_off_id: UUID | None; value: Decimal | None
    currency: str | None; source_class: str; evidence_class: str; missing: tuple[MissingInput, ...]
    assumed: tuple[str, ...]; admission: Mapping[str, Any] | None; dawn: Mapping[str, Any] | None
    effects: tuple[EffectRow, ...]
@dataclass(frozen=True)
class RunRow: id; tenant_id; decision_id; evaluator_version: str; outcome: str; study_sha256: str | None
    study_identity: Mapping[str, Any] | None; known_at: datetime; run_by_person_id; run_role: str
    run_by_script: bool; run_at: datetime; evaluations: tuple[EvaluationRow, ...]   # option position order
@dataclass(frozen=True)
class ChoiceRow: id; tenant_id; decision_id; option_id: UUID | None; run_id; agreed_action_id: UUID | None
    chosen_by_person_id; chosen_role: str; chosen_by_script: bool; chosen_at: datetime
@dataclass(frozen=True)
class DecisionBundle: decision: DecisionRow; site_code: str; site_name: str; options: tuple[OptionRow, ...]
    one_offs: Mapping[UUID, OneOffRow]; run: RunRow | None; choice: ChoiceRow | None   # latest one-offs and run
    names: Mapping[UUID, str]       # person id -> display name, for every person id in the bundle
class DecisionRefused(Exception):   # .code, .exit (2, or 3 for DECISIONS_UNAVAILABLE)

class DecisionStore(Protocol):
    def site(self, tenant_id: UUID, site_code: str) -> SiteRef | None             # chain/ports.py SiteRef
    def site_by_id(self, tenant_id: UUID, site_id: UUID) -> SiteRef | None        # D-P6.20; read by 6c
    def finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID) -> str | None   # its mechanism
    def find_decision(self, tenant_id, site_id, lever_id, period, finding_id) -> DecisionRow | None
    def add_decision(self, row: DecisionRow, options: tuple[OptionRow, ...]) -> tuple[DecisionRow, bool]
    def decision(self, tenant_id: UUID, decision_id: UUID) -> tuple[DecisionRow, tuple[OptionRow, ...]] | None
    def add_one_off(self, row: OneOffRow) -> OneOffRow
    def latest_one_offs(self, tenant_id, decision_id) -> Mapping[UUID, OneOffRow]   # by option id
    def add_run(self, run: RunRow) -> RunRow                                         # 6c's writer
    def latest_run(self, tenant_id, decision_id) -> RunRow | None
    def agreed_action_site(self, tenant_id, action_id) -> UUID | None | Literal[False]   # False: no such Action
    def add_choice(self, row: ChoiceRow) -> tuple[ChoiceRow, bool]
    def choice(self, tenant_id, decision_id) -> ChoiceRow | None
    def for_tenant(self, tenant_id, period_from: str | None, period_to: str | None
                   ) -> tuple[DecisionBundle, ...]   # newest first by (prepared_at, id); periods inclusive

class DecisionService:
    def __init__(self, store, accounts: AccountService, *, clock, new_id=uuid4, levers=LEVERS) -> None
    def prepare(self, *, tenant_slug, as_email, site_code, lever_id, period, current: Mapping[str, Decimal],
                finding_id: UUID | None, horizon_months: int = HORIZON_DEFAULT) -> Prepared
    def state_one_off(self, *, tenant_slug, as_email, decision_id, option_key, amount: Decimal, currency,
                      crew_visits: int, basis: str) -> OneOffRow
    def choose(self, *, tenant_slug, as_email, decision_id, option_key: str | None,
               agreed_action_id: UUID | None) -> Chosen
    def for_tenant(self, tenant_id, *, period_from: str | None = None, period_to: str | None = None
                   ) -> tuple[DecisionView, ...]                         # D-P6.8
```
`MemoryDecisionStore` (in `records.py`, used by unit tests) re-implements every identity rule, both deferred
checks (raising `DecisionRefused("RECORD_INVALID")`) and the newest-first order. The clock follows D-3C2.10: one
`clock()` call per service method, made UTC and whole-second; a naive datetime raises `ValueError`.

### 3.3 The rules, in order (the first that fails refuses; codes and exits)

Common steps C1-C3 for every command: (C1) `tenant_by_slug` None → `UNKNOWN_TENANT`; (C2) the person is
`onboard_person(as_email)`, of this tenant and `active`, else `PERSON_NOT_FOUND`; (C3) the person's first held role
holds some role of `roles_of(command)`, at any Site, else `PERSON_ROLE_REQUIRED`; for prepare and choose that role
is the recorded role. For `state_one_off` the recorded role is fixed after O1 (D-P6.24, below).

**prepare** (`decision.prepare`: `(ANALYST,)`): C1-C3; (P1) `period` not `YYYY-MM` → `BAD_PERIOD`; `horizon_months`
outside 1-60 → `BAD_HORIZON`; (P2) `store.site` None → `SITE_NOT_FOUND`; (P3) `lever_id` not in `levers` →
`LEVER_UNKNOWN`; the lever's `structure_key` is not `SITE_TYPE_TO_STRUCTURE.get(site.site_type)`
(`structure/read.py`) → `LEVER_SITE_TYPE`;
(P4) `finding_id` given: `store.finding` None → `FINDING_NOT_FOUND`; its mechanism's pin (`pins.pin_of`) is None or
its factor's row does not list the lever → `FINDING_NOT_ON_LEVER`; (P5) `current`'s keys differ from the axis names →
`BAD_CURRENT`; (P6) the re-run: `find_decision` found → compare `current` to the stored `current_settings` axis by
axis, numerically (`Decimal("90") == Decimal("90.0")`), and `horizon_months` to the stored one: equal → return it with
`already_prepared=True`, writing nothing; different → `ALREADY_PREPARED_OTHER`;
(P7) write the decision, the no-action option (`position` 0, `settings = current`) and one `SETTING_GRID` option for
each grid point not equal to `current`, at positions 1, 2, … in grid order, in one transaction. A `current` that is
not a grid point is allowed: then every grid point is an option.

**state_one_off** (`decision.one_off`: `(SITE_MANAGER, FINANCE)`; D-P6.18): C1-C3; (O1) `decision` None → `DECISION_NOT_FOUND`;
(O1b, D-P6.24) the recorded role is the first role in `roles_of("decision.one_off")` order that the person holds and
that covers the decision's Site (FINANCE covers every Site; SITE_MANAGER only a granted Site), else
`PERSON_ROLE_REQUIRED`; (O2) no option with that key → `OPTION_NOT_FOUND`; the no-action option → `NO_ACTION_ONE_OFF` (doing nothing costs 0
by rule, D-P6.18); (O3) `amount` negative, more than 2 decimals or over 12 integer digits → `BAD_AMOUNT`; `currency` not
`^[A-Z]{3}$` → `BAD_CURRENCY`; `crew_visits` negative → `BAD_CREW_VISITS`; `basis` empty after U+0020 strip, over 200
characters or with a refused character category (3C2's `clean_title` rule) → `BAD_BASIS`; (O4) append. A later
statement for the same option is a new row; the latest by `(declared_at, id)` is current. A run records the row it
used (`one_off_id`).

**choose** (`decision.choose`: `(EXECUTIVE,)`; D-P6.13): C1-C3; (H1) `decision` None → `DECISION_NOT_FOUND`; (H2)
`store.choice` found: the same option (or none) and action → return it, `already_chosen=True`; else
`ALREADY_CHOSEN`; (H3) `latest_run` None → `NOT_EVALUATED`; (H4) `option_key` given and not an option →
`OPTION_NOT_FOUND`; its evaluation in the latest run is `COMPARISON` → `CHOOSE_NONE_INSTEAD` (choosing no action is
`--none`); `REJECTED` → `OPTION_REJECTED` (a rejection is overridden only by a recorded change to its rule, never at
the choice); (H5) `agreed_action_id` given (with an option or with `--none`; keeping things as they are may still have
an agreed Action): `agreed_action_site` False → `ACTION_NOT_FOUND`; its Site is None (a tenant-wide Action) or not the
decision's Site → `ACTION_SITE_MISMATCH`; (H6) write `ChoiceRow(option_id or None, run_id = latest run's id, …)`.
Choosing an option whose value is missing, or a `DEFERRED` one, is allowed: people decide, and the value is
information (D-P6.5).

Store errors in any step → `DECISIONS_UNAVAILABLE` (exit 3), except a refused record (SQLSTATE class 22 or 23,
not a resolved identity conflict, and the cross-row checks) → `RECORD_INVALID` in both stores (D-P6.30, D-P6.31).
Every other refusal exits 2.

### 3.4 Words: `i18n/statements/en/decision.py` (D-P6.7)

One SC-1 statement, `decision.refused`, as `i18n/statements/en/agreed_action.py`'s `agreed_action.refused`
(D-3C2.14): a `code` slot (`type: state`, its `values` every code below, `exhaustive: code`) and one variant per code,
`id` the code in lower case, `when: {is: [code, <CODE>]}`. A key per code (`decision.refused.<code>`) is refused by
`KEY_FORM`. No digit or number word sits in a template (D-SC1.21): each is a slot, `count` or `example`, named below.
`records.py` joins `ADOPTED`. 6c adds its codes to this statement (6c §4).

| Code | Sentence (slots in braces) |
|---|---|
| `UNKNOWN_TENANT` | No operator has that name. |
| `PERSON_NOT_FOUND` | The person is not an active person of this operator. |
| `PERSON_ROLE_REQUIRED` | This person's role does not allow this step. |
| `BAD_PERIOD` | Write the month as YYYY-MM, like {period_example}. (`example` "2026-10") |
| `BAD_HORIZON` | Write the horizon as {least} to {most}. (`count` 1, `bare`; `count` 60, noun `month`: "as 1 to 60 months") |
| `SITE_NOT_FOUND` | This operator has no Site with that code. |
| `LEVER_UNKNOWN` | No change of that kind is known. |
| `LEVER_SITE_TYPE` | That kind of change does not apply to this Site's type. |
| `FINDING_NOT_FOUND` | This Site has no finding with that reference. |
| `FINDING_NOT_ON_LEVER` | That finding is not about what this change acts on. |
| `BAD_CURRENT` | Give today's value for each setting of this change. |
| `ALREADY_PREPARED_OTHER` | This decision was prepared with other current settings. |
| `DECISION_NOT_FOUND` | This operator has no decision with that reference. |
| `OPTION_NOT_FOUND` | This decision has no option with that name. |
| `NO_ACTION_ONE_OFF` | Doing nothing costs nothing to put in place. |
| `BAD_AMOUNT` | Write the amount as a number with at most {places} decimals, like {amount_example}. (`count` 2, `bare`; `example` "90.00") |
| `BAD_CURRENCY` | Write the currency as {letters} capital letters, like USD. (`count` 3, `bare`) |
| `BAD_CREW_VISITS` | Write the crew visits as a whole number. |
| `BAD_BASIS` | Say in up to {chars} what the cost is based on. (`count` 200, noun `character`, as 3C2) |
| `ALREADY_CHOSEN` | This decision already has a recorded choice. |
| `NOT_EVALUATED` | The options have not been valued yet. |
| `CHOOSE_NONE_INSTEAD` | To keep things as they are, choose none. |
| `OPTION_REJECTED` | This option was rejected and cannot be chosen. |
| `ACTION_NOT_FOUND` | This operator has no agreed Action with that reference. |
| `ACTION_SITE_MISMATCH` | That Action is for another Site. |
| `BAD_UUID` | Write the reference as it was printed. |
| `NO_DATABASE` | Set DATABASE_URL to the operator's database. |
| `RECORD_INVALID` | This record does not fit the decision it names, so nothing was stored. (D-P6.30) |
| `DECISIONS_UNAVAILABLE` | The decisions store cannot be reached right now. |

A `count` slot's unit word ("characters") follows the catalogue's count form as `agreed_action.refused`'s `most` does;
the pre-flight confirms each slot type against `i18n/catalogue.py` and names any change in the packet.

### 3.5 The read (`for_tenant`; what `6f` and the IA's Decisions list consume; D-P6.8)

```python
@dataclass(frozen=True)
class OptionView: option_key: str; generator: str; settings: Mapping[str, Decimal]; position: int
    one_off: OneOffView | None; evaluation: EvaluationRow | None        # from the latest run
@dataclass(frozen=True)
class OneOffView: amount: Decimal; currency: str; crew_visits: int; basis: str; declared_by_name: str
    declared_at: datetime
@dataclass(frozen=True)
class DecisionView: decision_id: str; site_code: str; site_name: str; lever_id: str; purpose_factor_id: str; home_category: str
    finding_id: str | None; period: str; horizon_months: int; prepared_by_name: str; prepared_at: datetime
    state: str                     # NOT_VALUED | WAITING | CHOSEN | UNDER_WAY | KEPT_AS_IS (rule below)
    decides_role: str              # "OPERATOR_EXECUTIVE": roles_of("decision.choose")[0]
    recommended: RecommendedView | None                                 # the latest run's RECOMMENDED row, else None
    options: tuple[OptionView, ...]                                     # position order; no action first
    run: RunSummary | None; choice: ChoiceView | None
@dataclass(frozen=True)
class RecommendedView: option_key: str; value: Decimal; currency: str
@dataclass(frozen=True)
class RunSummary: run_id: str; outcome: str; run_at: datetime; run_by_name: str; source_class: str  # weakest of
                                                                                                     # its evaluations
@dataclass(frozen=True)
class ChoiceView: option_key: str | None; chosen_by_name: str; chosen_at: datetime; run_id: str
    agreed_action_id: str | None
```
`home_category` (OD-25): the pinned factor's `home.category` when `finding_id` is set (the Finding's mechanism through
`pins.pin_of`), else the purpose factor's. Names, never emails. Newest first by `(prepared_at, id)`.
- **`state`**, in order: a choice with `option_id` null → `KEPT_AS_IS`; a choice with `agreed_action_id` set →
  `UNDER_WAY`; any other choice → `CHOSEN`; no choice and a run → `WAITING`; no run → `NOT_VALUED`. (IA-P's row words
  "Waiting for a choice" for `NOT_VALUED` and `WAITING`, "Under way" for `UNDER_WAY`; 6f words the rest.)
- **Period filter:** `period_from` and `period_to` (each `YYYY-MM` or None, inclusive) bound `decision.period`; a bad
  shape raises `DecisionRefused("BAD_PERIOD")`; `period_from > period_to` gives `()`. 6f passes the top bar's range.
- No HTTP route and no screen change in 6a (D-P6.8, D-P6.9).

## 4. Unit 3: the adapter, the commands, the guard

- `decisions/adapters/postgres_decision_store.py`: SQLAlchemy `text()` statements, as 3C2 §2.4. `add_decision`: one
  transaction under `pg_advisory_xact_lock(hashtextextended('decision:' || CAST(:tenant_id AS text), 0))`; the
  identity read with `IS NOT DISTINCT FROM` for `finding_id`; then `INSERT INTO decision` and one `INSERT INTO
  decision_option` per option; on `IntegrityError` with `decision_once`, roll back and return the stored row with
  `True`. `add_run`: one transaction: the run, its evaluations, their effects (plain `INSERT ... VALUES`). `add_choice`:
  the same lock and identity pattern with `decision_choice_once`. Numerics are passed as `str(Decimal)` and read back as
  `Decimal`; jsonb values bind as `CAST(:name AS jsonb)` (the form of every adapter on `main`), in §2's shapes.
  `site_by_id`: `SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t AND id = :s`. It reads `site`
  (with `name` for the read), `finding` (`mechanism` only), `agreed_action` (`site_id` only) and `operator_account`
  (names), and no other table.
- `decisions/composition.py`: `build_decisions(database_url) -> DecisionsService(service, dispose)`, the only importer
  of the adapter. `decisions/decisions_composition.py` re-exports the two names for the commands, `6c` and `6f`.
- `accounts/permissions.py` `COMMAND_ROLES` gains `"decision.prepare": (ANALYST,)`, `"decision.one_off":
  (SITE_MANAGER, FINANCE)`, `"decision.choose": (EXECUTIVE,)` (and `6c` adds `"decision.evaluate": (ANALYST,)`).
- Three commands, each `build_parser()` public and `main(argv, *, services=None, clock=None) -> int`, refusing
  as `<CODE> <sentence>\n` on stderr through `sys.stderr.write`, exit 2 or 3, and printing one JSON line on success:
  - `python -m assetops_backend.prepare_decision --tenant SLUG --as EMAIL --site CODE --lever ID --period YYYY-MM
    --current NAME=VALUE[,NAME=VALUE...] [--finding UUID] [--horizon N]` → keys `decision_id, site_code, lever_id,
    period, horizon_months, home_category, options` (a list of `{option_key, settings}` in position order),
    `prepared_by, already_prepared`.
  - `python -m assetops_backend.state_one_off --tenant --as --decision UUID --option KEY --amount 90.00 --currency
    USD --crew-visits 0 --basis TEXT` → `decision_id, option_key, amount, currency, crew_visits, basis, declared_by,
    declared_at`.
  - `python -m assetops_backend.choose_option --tenant --as --decision UUID (--option KEY | --none) [--action UUID]`
    → `decision_id, option_key` (null for none), `run_id, agreed_action_id, chosen_by, chosen_at, already_chosen`.
  Flag values (handshake I8): argparse takes every value as `str`; the command maps a malformed value to the
  service's code before any store call: `--current` (not `NAME=VALUE[,...]` with decimal values) → `BAD_CURRENT`;
  `--amount` → `BAD_AMOUNT`; `--crew-visits` → `BAD_CREW_VISITS`; `--horizon` → `BAD_HORIZON`; `--period` →
  `BAD_PERIOD`; a UUID flag → `BAD_UUID`; no `DATABASE_URL` → `NO_DATABASE` (exit 2, 3C2's `REFUSAL_EXIT`).
  `--option` with `--none`, or neither, is argparse's own error (exit 2). `--none` with `--action` is allowed (H5).
  Output forms (D-P6.27): `settings` and `amount` decimal strings (`"70"`, `"90.00"`); times
  `%Y-%m-%dT%H:%M:%SZ` (`record_action.py:50`); `prepared_by`, `declared_by`, `chosen_by` display names;
  `home_category` the code (`OPTIMIZE_COST`).
- Guard: `tools/checks/configuration-persistence.ps1` gains one writer block for the seven tables as 3C2 §2.6: the
  adapter is the sole runtime writer, plain `INSERT ... VALUES` only, no `UPDATE`, `DELETE` or `TRUNCATE`. The block
  holds seven per-table INSERT patterns, each required at least once (anti-vacuity, as the event-store block), and its
  VALUES pattern admits exactly one nested form, `CAST(:name AS jsonb)`:
  `VALUES\s*\((?:[^()]|CAST\(:\w+\s+AS\s+jsonb\))*\)`. The advisory-lock `SELECT` and the reads are not writes. Shown
  failing once with an `UPDATE decision_choice` planted in the adapter, and once with an `INSERT INTO decision` in
  another module.

## 5. Fixtures (hand-written; the tests write these literals, W2)

3C2 §4's people and Sites, from `backend/tests/lakeside_people.py`, a plain helper module that 3C2's `World`
(`tests/test_3c2_agreed_actions.py:101-140`) moves into; 3C2's two test files import it and still pass unchanged
(handshake I7). 6a extends it with the decision store; the Postgres people come from 3C2's `onboarded` fixture. tenant `lakeside-power`; Sites KISIWA-001,
KOBO-001, MTO-001 (MINIGRID) and, in the memory store, FRIDGE-001 (COLDCHAIN); Amina OPERATOR_EXECUTIVE; Joseph
FINANCE_AND_COMMERCIAL_LEAD; Wanjiru ANALYST; Peter SITE_MANAGER KOBO-001; Halima SITE_MANAGER KISIWA-001; David
SITE_MANAGER MTO-001; Musa FIELD_TECHNICIAN; tenant `other-op` with Zara. Emails `<name>@lakeside-power.example`.
Clock `2026-11-24T09:00:00Z`; `new_id` gives `UUID(int=1)`, `UUID(int=2)`, … .

- **F-P1** Wanjiru prepares KOBO-001 `generator_stop_reserve` 2026-10, current `stop_soc_pct=90,reserve_soc_pct=30`, no Finding:
  14 options. Position 0 `no-action` {90, 30}; then in order `stop-90-reserve-25`, `stop-85-reserve-30`,
  `stop-85-reserve-25`, `stop-80-reserve-30`, `stop-80-reserve-25`, `stop-75-reserve-30`, `stop-75-reserve-25`,
  `stop-70-reserve-30`, `stop-70-reserve-25`, `stop-65-reserve-30`, `stop-65-reserve-25`, `stop-60-reserve-30`,
  `stop-60-reserve-25` (positions 1-13). `home_category` = `candidate_l`'s home category (Optimize).
  `horizon_months` 12. Re-run: same id, `already_prepared` true, row counts unchanged.
- **F-P2** current `stop_soc_pct=72,reserve_soc_pct=30` (not a grid point): 15 options, `no-action` {72, 30} first.
- **F-P3** (memory store) Wanjiru prepares KOBO-001 2026-10 with a stored `GENERATOR_SUPPORT_CANDIDATE` Finding: a
  second decision beside F-P1, `finding_id` set, `home_category` `OPTIMIZE_COST`.
- **F-P4** the same with a stored `UNEXPLAINED_FUEL` Finding → `FINDING_NOT_ON_LEVER` (its pin `unexplained_l` lists
  no lever). **F-P5** a random UUID → `FINDING_NOT_FOUND`.
- **F-P6** re-runs of F-P1 with `stop_soc_pct=90.0` (equal: `already_prepared`), with `reserve_soc_pct=25`, and with
  `--horizon 6` (each `ALREADY_PREPARED_OTHER`).
- **F-O1** Peter states `stop-70-reserve-30`: 90.00 USD, 0 crew visits, basis "Technician sets the controller on a
  routine visit". A second statement of 120.00 at 09:05 is the current one.
- **F-C1** after a run stored by the test (each option `ACCEPTABLE` except `no-action` `COMPARISON` and
  `stop-60-reserve-25` `REJECTED`, outcome `RANKING_INCOMPLETE`), Amina chooses `stop-70-reserve-30` with the agreed
  Action of 3C2's fixture R1 (KOBO-001): stored; re-run `already_chosen` true; Amina choosing `stop-80-reserve-30` →
  `ALREADY_CHOSEN`.
- Refusals, one fixture each: Peter prepares → `PERSON_ROLE_REQUIRED`; Wanjiru prepares on FRIDGE-001 →
  `LEVER_SITE_TYPE`; Musa states a one-off → `PERSON_ROLE_REQUIRED`; David states a one-off on the KOBO-001 decision →
  `PERSON_ROLE_REQUIRED` (his grant is MTO-001's); Joseph states it → stored (FINANCE covers every Site); a one-off on
  `no-action` → `NO_ACTION_ONE_OFF`; David states a one-off on a missing decision → `DECISION_NOT_FOUND`; Hassan
(SITE_MANAGER MTO-001 and FINANCE_AND_COMMERCIAL_LEAD, added to the helper) states it on KOBO-001 → stored, role
`FINANCE_AND_COMMERCIAL_LEAD`; Zara chooses or states a one-off on Lakeside's decision → `PERSON_NOT_FOUND`; Amina chooses
  `stop-60-reserve-25` → `OPTION_REJECTED`; chooses before any run → `NOT_EVALUATED`; links an agreed Action recorded
  with `--site MTO-001` → `ACTION_SITE_MISMATCH`, and one with no Site → `ACTION_SITE_MISMATCH`; Amina chooses
  `--none --action <R1>` on a fresh decision → stored, `state` `KEPT_AS_IS`.

## 6. Tests (written first)

1. Levers: `grid()` and `option_key()` give F-P1's 13 keys in order (literals); the grid equals `KOBO_GRID`.
2. `check_levers()` refuses each of the ten rules (one planted registry or lever per rule, each its own case);
   `check_all()` calls it on the real registries and passes.
3. Prepare: F-P1 to F-P6, P1 to P5's refusals (memory store).
4. One-offs: F-O1 (latest wins), O1 to O3's refusals, David's and Hassan's cases.
5. Choose: F-C1, H1 to H5's refusals (the Site-less Action included); choosing none stores `option_id` null; `--none
   --action`; `site_by_id` found and missing (memory store).
6. Migration (Postgres, through the slot pool): every check, unique and FK above on a hand row (each violation asserted
   by constraint name); `decision_has_no_action` refuses a decision committed alone; `option_evaluation_run_complete`
   refuses a run missing one option; each table's UPDATE, DELETE and TRUNCATE refused; the downgrade refuses with rows
   and succeeds empty; one `alembic heads`.
7. Adapter (Postgres): F-P1 to F-C1 end to end; the prepare race (two threads, one row; the lock removed in a scratch
   copy, the index catch still holds); `for_tenant` newest first with names; `state` through all five values
   (F-P1 `NOT_VALUED`, after the run `WAITING`, F-C1 `UNDER_WAY`, a choice without an Action `CHOSEN`, `--none`
   `KEPT_AS_IS`); `recommended` null under F-C1's `RANKING_INCOMPLETE` run; the period filter (2026-10 to 2026-10
   holds F-P1; 2026-11 to 2026-12 gives none); another tenant's decisions are absent; `site_name` read; `site_by_id`;
   one row of each jsonb column stored and read back exactly (D-P6.27). The same cases run on the memory store in test 5.
8. Commands: each JSON line's exact keys and values for F-P1, F-O1, F-C1; every refusal's stderr line and exit; no `@`
   on stdout or stderr; the catalogue validator passes `decision.refused` (one key, every code a variant); one case per
   malformed flag (handshake I8).
9. Seams: `decisions/records.py` imports no adapter; `structure/levers.py` imports only `decimal`, `dataclasses`,
   `types`, `collections.abc`; nothing under `decisions/` imports `runs/` (6c amends this to D-P6.28's allowlist).

**Plants** (each fails its named test; shown once in a scratch copy, the run in the packet): drop the deferred trigger
(6); let prepare include the current point as an option (3, F-P1 count 15); let a site manager choose (5); store the
first one-off instead of the latest (4); read the decision's heading from the lever when a Finding is set (3,
`home_category` with a planted Protect pin); an `UPDATE` in the adapter (guard); a lever with a non-leaf in
`changes` (2); a key per code `decision.refused.bad_period` (8, `KEY_FORM`); `UNDER_WAY` read before `KEPT_AS_IS`
(7, a `--none` choice with an Action is planted in the memory store).

## 7. Done (questions; each can fail)

1. Does the database refuse a decision with no no-action option, and a second one?
2. Does prepare write the grid minus today's setting, in grid order, after no action, once?
3. Can only an analyst prepare, a site manager (on that Site) or finance lead state a one-off, and only the executive
   choose, once?
4. Is the choice tied to the latest run, and is every row append-only?
5. Does the decision's heading follow the Finding's factor when there is one (OD-25), and can a lever never disagree
   with it (start-up check)?
6. Does `for_tenant` give names, never emails, newest first, within the period bounds, with the state, who decides
   and the recommended option, and no value computed by 6a?

## 8. Out of scope

Values, effects, dispositions (`6c`); bounds as rows and costed bounds (`6b`, which adds `CONDITIONAL`); the carrier
that applies the setting (`6d`); the verification family (`6e`); the screen (`6f`); option generators other than the
setting grid (`6g`, `9c`); plan items and release thresholds (`7a`); reopening a choice.

## 9. Units and dependencies

| Commit | Scope | Units |
|---|---|---:|
| 1 | Migration `0072` and test 6 | 1.0 |
| 2 | `structure/levers.py`, `check_levers`, the registry row, `decisions/records.py` with the memory store, statements; tests 1-5, 9 | 1.25 |
| 3 | Adapter (`site_by_id` included), composition, three commands, permissions, seven-pattern guard, the people helper move; tests 7, 8 | 1.0 |
| | **6a** | **3.25** |

Depends on: owner P6 (gate P, met 22 Nov); `main` holding 3B1, 3B2, 3C0a, 3C1a, 3A6, 3C2, SC-1a, 0K4d (all merged;
0K4d only for test 1). Unblocks
`6b`, `6c`, `6d`, `7a`, `9a`.

## 10. Decisions (rev 1; P6 approved 22 Nov, every answer decided)

| # | Question | Decided | Ruling |
|---|---|---|---|
| Q1 | Who chooses (P6 #1) | The executive only (`decision.choose`: EXECUTIVE), by name and time; "none" valid | D-P6.13 (owner) |
| Q2 | Who prepares | The analyst, by command; the system's own preparation from a Finding comes with `6f` | Architect, rev 0 default kept |
| Q3 | Horizon (P6 #3) | 12 months, stored per decision | D-P6.15 (owner) |
| Q4 | One choice per decision | Yes; a change of mind is a new decision for a later period | Architect, rev 0 default kept |
| Q5 | Choosing an unvalued option | Allowed and recorded | D-P6.5 |
| Q6 | One-off of doing nothing (P6 #6) | 0 by rule, never stated | D-P6.18 (owner) |
| Q7 | Who states a one-off (P6 #6) | Site manager on that Site, or finance lead, with a basis | D-P6.18 (owner) |
| Q8 | Today's settings | Stated by the analyst on prepare (`--current`), checked by `6c` against the study's baseline | Architect, rev 0 default kept |
| Q9 | The agreed Action link | Optional on the choice; same Site | Architect, rev 0 default kept |

Open for the owner, with defaults applied (`rulings.md` queue): none that changes 6a.
