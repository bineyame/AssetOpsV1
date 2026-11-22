# 6c: options valued against doing nothing (the evaluator; implementer spec)

**Status: in_review (built 22 Nov 2026 on `task/6c-option-evaluator`). Rev 2, handshake answered (`handshake.md`; D-P6.20 to D-P6.29); ready to build after 6a.** P6 approved by the owner, 22 Nov 2026 ("accept all p6 defaults",
`owner/owner-accept-p6-defaults-2026-11-22.md`); every default is decided (§11) and logged as D-P6.1 to D-P6.19
(`specs/6-decision-valued/rulings.md`). Architect (Claude), 2026-11-21 rev 0, 2026-11-22 rev 1 and rev 2. Lane 3 (`delivery-plan.md` §2, row `6c`). **3.0 units**,
three commits. Discovery review (W5): a money figure and a new mechanism. `USER_REVIEW_REQUIRED: true` (these are the
figures the executive will choose by; no screen).

- **Owner proposal (approved):** `specs/6-decision-valued/P6-proposal.md`. **Rulings:** `specs/6-decision-valued/rulings.md`.
  **Reviewer guide:** `reviewer-guide.md` (this folder).
- **What it is.** One command, run by the analyst, values every option of a 6a decision against no action, by the
  design's one rule (design §2.4, `decision-loop-specification.md` §6 "Value";
  `domain-and-decision-models.md` §4.1):
  `value(option) = Σ over the horizon [outcome(structure | option's factor changes) − outcome(structure | no
  action)] − (one-off under the option − under no action)`. The outcome is each registry's `contribution`. It ranks
  the settings that 0K4d's rule admits, and writes one 6a evaluation run: every option's value or the inputs it
  lacks, its effects factor by factor, its disposition and rank.
- **The residual risk it answers** (0K4d review, item 3): on the simulated controller the admission rule finds "no
  harm" for all 14 settings, so the rule cannot choose. The choice rests here, on value, with the dawn readings stored
  beside each setting as information, never as a gate (D-0K4.9).
- **The owner's rules on every figure** (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`, D-0K4.11):
  one figure per quantity, computed by the model from the stored inputs and labelled by source (SIMULATED until the
  replay runs on the operator's records). No hand-entered or design value anywhere: no figure in this spec is an
  expected output of the product's data; the fixtures' figures are test inputs and their hand-computed results. A
  missing input gives no value and names its record ("Not available yet" in `6f`). A change of exactly zero is zero.
- **The world-month rule** (D-0K4.38, D-P6.2): a study's amounts reach the decision's month only when the study is a
  simulation on that Site's own record (frame `SITE_RECORD`). A declared season (every study on disk today, 0K4d's
  `kobo-61d` included) values nothing: its admission and dawn information are stored, its values read "Not available
  yet". Kobo stays Simulated (`owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`); its values arrive with 0K4f.
- **Builds on:** `6a` (to merge first: records, `DecisionStore.add_run`, `LEVERS`); `0K4d` (**on `main`, gate K**:
  `runs/admission.py`, and the study file shape of `tools/kobo_replay_study.py` `outcome_json`, `admission_json`);
  `3B3` (`structure/evaluate.py`, `structure/expressions.py`, `registry.parsed_text`); `3B7a` and the read
  (`structure/composition.py` `build_structure_read(url).read.site_inputs(site, month, known_at)`).
- **Mock:** non-screen. It supplies vNEXT `#/decision/kobo-generator`'s option values, the rejected option's reason,
  the recommendation, and each option's "Effect under each heading" (the effects carry their factor; `6f` reads each
  factor's home category). The mock's +$2,916.00 "design estimate" and "reserve rejected at dawn" are restated by
  0K4m (D-0K4.15, D-0K4.29). `6f` labels any remaining gap MOCK DEVIATION D4.

## 0. Before you start (gates)

- **Gate P (owner): met.** P6 approved, 22 Nov 2026; §11 holds the decided answers.
- **Gate 6a.** `git grep -n "def add_run" main -- backend/assetops_backend/decisions/` shows at least the Protocol's
  line and the adapter's; `git grep -n "def site_by_id" main -- backend/assetops_backend/decisions/` likewise
  (D-P6.20; if absent, 6c adds it in commit 3 and the packet names 6a's files touched).
- **Gate K: met.** `git show main:backend/assetops_backend/runs/admission.py` exists (0K4d merged).
- **Pre-flight (in the packet, before code; answered from `main` by D-P6.11, confirm each):** (1) `evaluate()` takes a
  leaf map whatever its sign (`_check_leaf` has no sign check); the evaluator passes deltas to `difference`, never to
  `evaluate`, so no negative leaf is built. (2) The 0K4d study file's case keys hold every key in §3.1 (they do,
  `avoided_l_by_month` and `added_throughput_kwh_by_month` with `days` included). (3) Every registry in `REGISTRIES`
  has a `contribution` row (all three do).

## 1. Outcome and why

`python -m assetops_backend.evaluate_options --tenant lakeside-power --as wanjiru@lakeside-power.example --decision
<6a's Kobo decision> --study PATH` writes one run. For each of the 13 settings it holds the change in candidate litres
a month, the added battery use, the fuel money saved and the wear cost; the value over 12 months net of the one-off,
or the input that is missing; whether 0K4d's rule admits the setting; and the setting's dawn readings. The run's
outcome is one of: a recommendation; "doing nothing is best"; "ranking incomplete" (naming what is missing); or
"nothing admitted". With today's study (`/opt/assetecon/evidence/0K4d/kobo-61d/study.json`, a declared season) the
run is "ranking incomplete": all 14 settings pass the service checks, and every value names
`SITE_MONTH_SIMULATION` (D-P6.2). When 0K4f writes a simulation of Kobo's own October, the same command values them.
Gate questions: does every value come from the structure re-evaluated with the option's changes, against no action, on
the same leaves? Is a missing input never a zero, while an unchanged factor's effect is exactly zero? Does a
not-admitted setting never rank? Does a declared season never value anything? Does the same code value a cold-room and
an EV option with no vertical branch?

## 2. Commit 1: the difference through the structure (`structure/difference.py`; pure)

```python
OUTCOME_FACTOR = "contribution"
@dataclass(frozen=True)
class Delta:
    factor_id: str
    change: Decimal | None              # option side − no-action side, monthly; None when an input is missing
    unit: Unit
    currency: str | None                # of the money leaves used; None for a non-money row
    missing_leaves: tuple[str, ...]     # registry order; () when change is not None
    used: tuple[str, ...]               # factor ids whose values the change needed, registry order
    evidence: str                       # weakest (evaluate.weakest) of the used values and the changed leaves
    origins: tuple[str, ...]            # ORIGIN_ORDER order, of the used values and the changed leaves

@dataclass(frozen=True)
class LeafChange:                       # D-P6.3: a delta on a leaf, never a replacement value
    delta: Decimal | None               # option side minus no-action side, monthly; None when it cannot be known
    evidence: str                       # e.g. "MODELLED"
    sources: tuple[str, ...]            # e.g. ("replay-study",)
    origins: tuple[str, ...]            # ORIGIN_ORDER order
    missing: tuple[str, str] | None     # (record_kind, source_family) when delta is None, else None

def difference(registry: Registry, base: Mapping[str, LeafValue],
               changes: Mapping[str, LeafChange]) -> Mapping[str, Delta]
```
- `base` is the period's leaf map (every leaf of the registry). `changes`' keys are leaves of the registry, each in
  the lever's `changes` (or the option's declared changes, C1, E1). `v0 = evaluate(registry, base)` with no `stated`
  map (D-P6.4: the counterfactual runs through the expressions; a stated record such as the month's fuel invoices
  would make every effect 0). There is no second `evaluate` call: the option side is folded by `val1` below.
- **Scope:** the result holds the changed leaves and every node that is in `OUTCOME_FACTOR`'s dependency closure and
  references a changed leaf, directly or through other nodes, in registry order. Any other node is left out.
- **The rule, per expression `e`** (in `evaluate`'s context, `Context(prec=34, rounding=ROUND_HALF_EVEN)`, nothing
  quantised). `d(e)` is a value or MISSING(leaves):
  - a changed leaf: its `delta`, needing no value (MISSING naming the leaf when `delta` is None);
  - an unchanged leaf or a literal: `0`, needing no value;
  - a node reference: `d` of its expression;
  - `−a`: `−d(a)`. `a ± b`: `d(a) ± d(b)`. MISSING if either is.
  - `a × b`: `t1 + t2`, where `t1 = 0` if `d(a) == 0`, else `d(a) × val1(b)`; and `t2 = 0` if `d(b) == 0`, else
    `val0(a) × d(b)`.
  - `a ÷ b`, and `min`, `max`, `ceil`, `floor`: `0` when every operand's `d` is exactly `0`. Otherwise it is
    `val1(e) − val0(e)`.
  - `val0(x)` folds the sub-expression from `v0` (a reference reads its `FactorValue.value`). `val1(x)` folds it on
    the option side: a changed leaf is `base value + delta` (None when either is None), any other leaf or node its
    `v0` value, a node over a changed leaf folded again from its expression. If any value needed is `None`, the
    result is MISSING, naming that value's missing leaves (a leaf names itself; a node names its `missing_leaves`;
    a changed leaf with no `delta` names itself). A MISSING operand and a missing value it needs both name their
    leaves, as one union in registry order. So `val1(b)` is folded even when `d(a)` is MISSING, and what it reads
    counts in `used` (F1h's `diesel_price`).
  - "Exactly 0" compares numerically: `Decimal("0.00") == 0`. A zero change needs no value of the other operand. That
    is the only short cut, and it holds because nothing changed. It is not a missing value read as zero.
- `used`, `evidence`, `origins`: every factor whose value a `val0` or `val1` read, plus the changed leaves (each
  changed leaf contributes its `LeafChange.evidence` and `origins`).
  `evidence` is the weakest by `EVIDENCE_ORDER`. `currency` is the one currency of the money leaves used. If two
  differ, the change is MISSING with the missing leaves `("currency",)`, which §3.4 step 1 maps to
  `MissingInput("CURRENCY_MISMATCH", "STRUCTURE", None)`. That is a planted case, and no fixture has it in real data.
- **Parity test (W2):** a private `_fold(expr, values)` computes `val0` and `val1`. For every node of all three
  registries, on a leaf map where every leaf has a value, `_fold(parsed_text(row.expression), v)` equals
  `evaluate(...)[node].value`.

## 3. Commit 2: the study, the admission, the evaluator

### 3.1 `decisions/study_input.py` (pure; reads one study file)

```python
FRAMES = ("SITE_RECORD", "DECLARED_SEASON")
@dataclass(frozen=True)
class MonthAmount:
    month: str; days: int; value: Fraction                   # one `*_by_month` entry
@dataclass(frozen=True)
class CaseInput:
    case_id: str; settings: Mapping[str, Fraction]          # {"stop_soc_pct": .., "reserve_soc_pct": ..}
    by_month: Mapping[str, tuple[MonthAmount, ...]]          # study field -> entries, file order
    measures: AdmissionMeasures                              # runs/admission.py (§3.2)
    file_admission: tuple[bool, str | None, tuple[tuple[str, bool], ...]]   # admitted, first failing, parts
    file_limits: Mapping[str, Fraction]                      # part name -> limit, absolute parts only
    worst_dawn_soc_pct: Fraction; dawn_days_below: int; new_dawn_days_below: tuple[str, ...]
@dataclass(frozen=True)
class StudyInput:
    sha256: str; identity: Mapping[str, Any]; input_class: str; days: int
    frame: str; frame_tenant: str | None; frame_site_code: str | None     # D-P6.2
    baseline: CaseInput; cases: Mapping[str, CaseInput]      # by case_id, file order kept
def read_study(path: Path) -> StudyInput                    # raises StudyRefused(code); header identity only
```
- A number is `{"exact": "n/d", ...}` → `Fraction(int(n), int(d))`. Only `exact` is read. `reading` is ignored.
- **Header keys read** (all required): `input_class` (in `runs/replay_study.py` `INPUT_CLASSES`), `evidence_class`
  (`MODELLED`), `commit`, `model`, `season`, `season_inputs_digest`, `trajectory_digests`, `assumptions`,
  `admission_rule`, `status`, `window_start`, `days`, `baseline`, `cases`. **Optional:** `frame`. Absent, or with a
  `kind` other than `SITE_RECORD`, the frame is `DECLARED_SEASON`; `SITE_RECORD` requires `tenant` and `site_code`
  strings, else `STUDY_UNREADABLE`. `read_study`'s `identity` is the required keys except `baseline` and `cases`, plus
  `"frame"` (`{"kind", "tenant", "site_code"}`, the last two null for a declared season). `run.py` adds
  `"ignored_cases"` and `"months_averaged"` (§3.3) before `add_run`; the stored identity has all of them.
- **Types (one key-to-type table in the module; a wrong type is `STUDY_UNREADABLE`):** `{"exact"}` objects:
  `stop_soc_pct`, `reserve_soc_pct`, `unserved_kwh`, `worst_dawn_soc_pct`, each `*_by_month` entry's `value`, each
  admission part's `limit` (or null). JSON integers: top-level `days`, entry `days`, `reserve_breach_steps`,
  `max_starts_in_a_day`, `longest_days_without_full_charge`, `dawn_days_below`. Strings: `case_id`, `month`, the header
  labels, `commit`, `model`, `season`, `season_inputs_digest`, `window_start`, `status`. A list of date strings:
  `new_dawn_days_below`. Objects: `trajectory_digests` (string values), `frame`. Lists of strings: `assumptions`,
  `admission_rule`. Booleans: `admitted`, `passed`.
- **Case keys read** (baseline the same, without `admission`): `case_id`, `stop_soc_pct`, `reserve_soc_pct`,
  `avoided_l_by_month`, `added_throughput_kwh_by_month` (each entry `month` `YYYY-MM`, `days` int, `value` number),
  `unserved_kwh`, `reserve_breach_steps`, `max_starts_in_a_day`, `longest_days_without_full_charge`,
  `worst_dawn_soc_pct`, `dawn_days_below`, `new_dawn_days_below`, `admission` (`admitted`, `first_failing_part`,
  `parts[].name`, `parts[].passed`, `parts[].limit`). The window totals `avoided_l`, `added_throughput_kwh` and
  `scaled_to_30_days` are not read.
- Refusals: unreadable file, JSON or key, or a wrong type → `STUDY_UNREADABLE`. `status` ≠ `CALIBRATED` →
  `STUDY_NOT_CALIBRATED`. Labels outside the sets → `STUDY_LABELS_INVALID`. `sha256` is taken over the file's bytes.

### 3.2 `runs/admission.py`: measures, so the rule judges without a projection (0K4d's module; behaviour unchanged)

```python
@dataclass(frozen=True)
class AdmissionMeasures:
    unserved_kwh: Fraction; reserve_breach_steps: int; max_starts_in_a_day: int
    longest_days_without_full_charge: int
    @classmethod
    def of(cls, case: CaseOutcome) -> "AdmissionMeasures"
def judge(baseline: AdmissionMeasures, case: AdmissionMeasures,
          rule: AdmissionRule = AdmissionRule()) -> tuple[AdmissionPart, ...]   # ADMISSION_PARTS order
```
`admit()` builds its parts as `judge(AdmissionMeasures.of(baseline), AdmissionMeasures.of(case), rule)`. Nothing
else in `admit` changes. 0K4d's `test_0k4d_admission` and `test_0k4d_v8_study` pass unchanged (run both).
`__all__` gains the two names and `DAWN_LIMIT_PCT = Fraction(35)`, which becomes `admit`'s `dawn_limit_pct` default
(D-P6.22); 6c imports it for `margin_points` and writes no 35.

### 3.3 `decisions/models.py` (the lever models; the only place a factor or field name of a lever's model is written)

```python
SETTING_GRID_CHANGES: Mapping[str, tuple[tuple[str, str, int], ...]] = MappingProxyType({
    # lever_id -> (changed leaf, study by-month field, sign)                       D-P6.3
    "generator_stop_reserve": (("candidate_l", "avoided_l_by_month", -1),
                               ("battery_throughput_kwh", "added_throughput_kwh_by_month", 1)),
})
SITE_MONTH_MISSING = ("SITE_MONTH_SIMULATION", "SIMULATION")                     # D-P6.2
ORIGIN_OF_INPUT = MappingProxyType({"RECORDED": "field-integrated", "EMULATED": "source-emulated",
                                    "SIMULATED": "demo-simulated"})
def full_months(case: CaseInput, fields: tuple[str, ...]) -> tuple[str, ...]
    # months whose entry, in every field, has days == calendar.monthrange's days; file order
def setting_changes(lever: Lever, case: CaseInput, study: StudyInput, *,
                    grid_changes=SETTING_GRID_CHANGES) -> Mapping[str, LeafChange]       # D-P6.21
    # SITE_RECORD: leaf -> LeafChange(sign × mean of the field's full-month values, "MODELLED", ("replay-study",),
    #   (ORIGIN_OF_INPUT[study.input_class],), None), the mean as Decimal(num) / Decimal(den) in evaluate's context
    # DECLARED_SEASON: leaf -> LeafChange(None, "MODELLED", ("replay-study",), (origin,), SITE_MONTH_MISSING)
```
- **The month rule (D-P6.2, D-P6.15).** For a `SITE_RECORD` study the monthly change is the mean of the case's full
  months: the sum of their values over their count, with no × 30 / days scaling. The run's
  `identity["months_averaged"]` lists those months (the baseline's full months; every case must have the same set,
  else `STUDY_UNREADABLE`). For a `DECLARED_SEASON` study no `*_by_month` value is read, whatever its months are called,
  and `months_averaged` is `[]`.
- **Frame checks (SITE_RECORD; at E3, §4):** `frame_tenant` ≠ the tenant's slug or `frame_site_code` ≠ the decision's
  Site code → `STUDY_FRAME_MISMATCH`; the decision's `period` not among the full months → `STUDY_MONTH_NOT_COVERED`.
- Matching (each mismatch refuses `STUDY_GRID_MISMATCH`, naming the key): every `SETTING_GRID` option's
  `option_key` is a `case_id`, and that case's settings equal the option's settings. Cases matching no option are
  allowed only if their settings equal the decision's `current_settings`; they are listed in
  `identity["ignored_cases"]`. Any other extra case is refused.
- The study's baseline settings must equal the decision's `current_settings`, else `STUDY_BASELINE_MISMATCH`.
- `grid_changes[lever_id]`'s leaves must equal `lever.changes`, for every entry passed in (a start-up assertion in
  `EvaluationService.__init__` and the module's test). Tests inject `{"test_stop_reserve":
  SETTING_GRID_CHANGES["generator_stop_reserve"]}` (D-P6.21); product code passes the default only.

### 3.4 `decisions/evaluate.py` (pure; no structure key and no factor id is written in it)

```python
EVALUATOR_VERSION = "option-evaluator-1"
TIE = Decimal("0.9")                       # within 10 % of the best value (D-P6.16; D-0K4.29 keeps the 10 % as 6c's)
@dataclass(frozen=True)
class OptionInput:
    option: OptionRow; changes: Mapping[str, LeafChange] | None  # None for no action
    admission: tuple[AdmissionPart, ...] | None                  # None: no admission rule for this generator
    dawn: Mapping[str, str] | None; one_off: OneOffRow | None
def evaluate_options(registry: Registry, base: Mapping[str, LeafValue], decision: DecisionRow,
                     lever: Lever | None, inputs: tuple[OptionInput, ...]) -> tuple[str, tuple[EvaluationRow, ...]]
    # (run outcome, one EvaluationRow per option in position order); ids filled by the caller
```
**Per option** (one `difference(registry, base, changes)` call each):
1. `monthly_change = d[OUTCOME_FACTOR].change`; `currency = d[...].currency`. `horizon_change = monthly_change ×
   decision.horizon_months` (D-P6.15). `value = horizon_change − one_off.amount` (no action's one-off is 0 by rule;
   D-P6.18).
   `missing`, in this order: `d[OUTCOME_FACTOR]`'s missing leaves, each as `MissingInput(change.missing[0],
   change.missing[1], leaf)` when it is a changed leaf with no delta (D-P6.2), else `MissingInput(leaf.missing.record_kind,
   leaf.missing.source_family, leaf)` from the base leaf; then `("ONE_OFF", "DECISION", None)` when no one-off is
   stated; then `("ONE_OFF_CURRENCY", "DECISION", None)` when its currency differs from `currency`. Any missing input
   leaves `value` `None`. A missing one-off leaves `monthly_change` and `horizon_change` set. **Zero change
   (D-P6.29):** when the change is exactly 0 and `currency` is None (no money leaf read), the option's currency is the
   one-off's and no `ONE_OFF_CURRENCY` is added.
2. `effects`: one `EffectRow` per `Delta` in the result, in its order. `unit` is `str(row.unit)`.
3. `source_class` (D-P6.25): `SIMULATED` if `demo-simulated` is in the outcome's `origins`; else `EMULATED` if
   `source-emulated` is; else `RECORDED`, which means "no simulated or emulated input": `unknown`,
   `observed-financial`, `field-integrated` and `bench-tested` all read RECORDED. The evidence class carries the rest:
   `evidence_class` is the outcome's `evidence`. `assumed` lists the used leaves whose base `missing.carried_as` is
   `TARGET` or `ASSUMPTION` (`evaluate`'s `_ASSUMED`), in registry order.
4. `admission`, `dawn`: stored as §3.5 gives them.

**Dispositions, in this order:**
- **R0.** No action is `COMPARISON`, with value 0, monthly and horizon changes 0, `currency` `None`, `evidence_class`
  `DERIVED`, `source_class` the weakest across the other options (`RECORDED` when there are none), and no effects.
- **R1.** Admission given and not admitted: `REJECTED`, reason `NOT_ADMITTED_` plus the first failing part in upper
  case (`NOT_ADMITTED_STARTS`). Its value is still computed and stored, but it is never ranked.
- **R2.** `value` is `None`: `DEFERRED`, reason `VALUE_NOT_AVAILABLE`.
- **R3.** `value < 0`: `DEFERRED`, reason `NOT_WORTH_MORE_THAN_NO_ACTION`. `value == 0`: `DEFERRED`, reason
  `WORTH_THE_SAME_AS_NO_ACTION` (D-P6.5: doing nothing wins a tie).
- **R4.** Otherwise the option is a candidate.

**The run's outcome:**
- Every option except no action is `REJECTED`: `NOTHING_ADMITTED`.
- Else, if any admitted option is R2 because its value is missing: `RANKING_INCOMPLETE` (D-P6.17). Every candidate is
  `ACCEPTABLE` with reason `RANKING_INCOMPLETE` and no rank.
- Else, with no candidate: `NO_ACTION_BEST` (D-P6.19; 6f says "Doing nothing is worth more than any setting tried",
  or, when every admitted value is exactly 0, 6f's tie words).
- Else `RECOMMENDED`:
  - `V` is the best candidate value, and the near set is the candidates with `value >= V × TIE`.
  - The Recommended option is the near-set member with the least `distance`, then the higher value, then `option_key`
    ascending. `distance` is the sum over the lever's axes of `|setting − current|`, or 0 when the lever is `None`
    (options with declared changes, as C1 and E1).
  - It takes rank 1. Its reason is `AT_GRID_EDGE` when, on some axis, it differs from current and sits at that
    axis's extreme in the direction of the change (the axis minimum when lower than current, the maximum when
    higher). Otherwise the reason is `None`.
  - Every other candidate is `ACCEPTABLE`, ranked 2, 3, … by value descending, then `option_key` ascending.
- `CONDITIONAL` is never written (it is 6b's costed bound).

The dawn readings never enter a rule above (D-0K4.9; D-P6.16).

### 3.5 The study path's inputs (`decisions/run.py`, `EvaluationService.evaluate`)

Per `SETTING_GRID` option: `changes = setting_changes(lever, case, study)` (§3.3; under a declared season every
change has no delta and names `SITE_MONTH_SIMULATION`). `admission = judge(baseline.measures, case.measures)` is
recomputed, in the study's own frame. It must equal the file's `admitted`, `first_failing_part` and each part's
`passed`, and the file's limits must equal `AdmissionRule()`'s (starts 6, full charge `7 − 1`), else
`STUDY_ADMISSION_MISMATCH`. Stored as `{"admitted", "first_failing_part", "parts": [{"name", "case_value",
"baseline_value", "limit", "judged", "passed"}]}`. `dawn = {"worst_soc_pct", "margin_points"`
(worst − `DAWN_LIMIT_PCT`), `"days_below", "new_days_below", "days"` (the study's `days`, so 6f can say "of 61 simulated days")`}`. Every
fraction in `admission` and `dawn` is `"n/d"` in lowest terms; integers are JSON numbers (D-P6.27).

## 4. Commit 3: the command and the run

`EvaluationService(decisions: DecisionService's store, accounts, structure_read, *, clock, new_id, levers=LEVERS,
registries=REGISTRIES, grid_changes=SETTING_GRID_CHANGES).evaluate(*, tenant_slug, as_email, decision_id, study_path: Path | None) -> RunRow`. The steps
run in order, and the first that fails refuses:
- **E0.** The common steps C1 to C3 of 6a §3.3, with command `decision.evaluate`: `(ANALYST,)`, added to
  `COMMAND_ROLES`.
- **E1.** No such decision: `DECISION_NOT_FOUND`.
- **E2.** The lever's generator is `SETTING_GRID` and there is no study path: `STUDY_REQUIRED`.
- **E3.** In order: `read_study` (`STUDY_UNREADABLE`, `STUDY_NOT_CALIBRATED`, `STUDY_LABELS_INVALID`); the Site by
  `store.site_by_id` (D-P6.20; None → `DECISIONS_UNAVAILABLE`, exit 3); for SITE_RECORD, `STUDY_FRAME_MISMATCH` then
  `STUDY_MONTH_NOT_COVERED`; `STUDY_BASELINE_MISMATCH`; `STUDY_GRID_MISMATCH`; the admission recomputation over every
  case, ignored cases included (`STUDY_ADMISSION_MISMATCH`, §3.5). All before E4: a bad file never reads the
  structure.
- **E4.** `known_at = now` (one clock read). `base = structure_read.site_inputs(site_ref, decision.period,
  known_at).leaves`, with E3's `SiteRef`. Any exception: `STRUCTURE_UNAVAILABLE` (exit 3).
- **E5.** The latest one-offs: `store.latest_one_offs`.
- **E6.** `evaluate_options`. A `StructureError` raised inside refuses `STRUCTURE_UNAVAILABLE` (exit 3); nothing is
  written.
- **E7.** `store.add_run(RunRow(...))`, with study identity and sha256 set. A refused run is `RECORD_INVALID` (exit 2) in both stores
  (D-P6.30, D-P6.31); 6c's tests expect that code.

Every call writes a new run, because a valuation is dated. The latest run is the one a choice binds (6a H3).

Command: `python -m assetops_backend.evaluate_options --tenant SLUG --as EMAIL --decision UUID [--study PATH]`.
Its main, its refusal output and its exit codes follow 6a §4. Success prints one JSON line with these top-level keys, in
order: `run_id`, `decision_id`, `outcome`, `source_class`, `frame` (`{"kind", "tenant", "site_code"}`, the last two
null for a declared season), `months_averaged`, `options`. `options` holds one entry per option in position order:
`option_key`, `disposition`, `reason_code`, `rank`, `monthly_change`, `horizon_change`, `value`, `currency`,
`missing` (a list of `[record_kind, source_family, factor_id]`), and `admitted` (true or false; null for `no-action`). Figures are decimal strings rounded half-even once from the stored figure (D-P6.6):
money (`monthly_change`, `horizon_change`, `value`) to cents, any other quantity to 6 places; the stored rows stay
unrounded. Display formats stay `6f`'s. The codes join 6a's one statement `decision.refused` (6a §3.4, D-P6.7) as
variants, with these sentences (the words "simulation" per D-0K4.50; no digit in a template):
- `STUDY_REQUIRED`: "Give the simulation for this kind of change (--study)."
- `STUDY_UNREADABLE`: "The simulation file cannot be read."
- `STUDY_NOT_CALIBRATED`: "The simulation did not match the Site's own run, so it cannot value anything."
- `STUDY_LABELS_INVALID`: "The simulation is not labelled as a model on simulated, emulated or recorded readings."
- `STUDY_BASELINE_MISMATCH`: "The simulation starts from other settings than this decision's."
- `STUDY_GRID_MISMATCH`: "The simulation does not hold exactly this decision's settings."
- `STUDY_ADMISSION_MISMATCH`: "The simulation's service checks do not match the rule."
- `STUDY_FRAME_MISMATCH`: "The simulation is of another Site's record."
- `STUDY_MONTH_NOT_COVERED`: "The simulation does not cover the whole of this decision's month."
- `STRUCTURE_UNAVAILABLE`: "The month's figures cannot be read right now."

## 5. Fixtures (hand-written; the tests write these literals, W2)

**Leaf helper** (tests only): `leaves_for(registry, given)` gives every leaf of the registry:
- each `given` leaf as written;
- each OPTION_ONLY leaf NEUTRAL at its neutral;
- each CALENDAR leaf DERIVED with a value and no origins: `period_days` and `nights_in_period` the month's days (31
  for 2026-10), `minutes_per_day` 1440;
- every other leaf NOT_AVAILABLE, with `Missing(fb.kind, fb.family, "NOT_RECEIVED", None, (), fb.words, None)`.

A priced or declared leaf has origins `("unknown",)`, as `sources.py` gives today.

**F1, a Kobo-shaped decision (MINI_GRID, synthetic study, injected lever `test_stop_reserve`).**
- The lever: axes `stop_soc_pct` (90, 80, 70, 60) and `reserve_soc_pct` (30, 25); template and `changes` as
  `generator_stop_reserve`. The current settings are {90, 30}, so the decision has 7 options plus no action. Period
  2026-10, horizon 12.
- Each option's one-off: 90.00 USD, 0 crew visits, stated by Peter.
- Base leaves: `diesel_price` 1.25 USD (ESTIMATED; `Missing(..., cause "NOT_RECEIVED", carried_as "ASSUMPTION",
  blocks (), ...)`, currency `USD`). `wear_rate` is NOT_AVAILABLE in F1a and 0.05
  USD DECLARED in F1b.
- The study file is `backend/tests/fixtures/decisions/study-f1.json`. Its header: `input_class` SIMULATED,
  `evidence_class` MODELLED, `commit` "f1" repeated 20 times, `model` "mini-grid/8", `season` "v2",
  `season_inputs_digest` "a" × 64, `trajectory_digests` `{"site": "b" × 64}`, `assumptions` ["fixture"], `admission_rule` ["fixture"], `status` CALIBRATED, `window_start`
  "2026-09-30T21:00:00Z", `days` 31, `frame` `{"kind": "SITE_RECORD", "tenant": "lakeside-power", "site_code":
  "KOBO-001"}`. Each case's two `*_by_month` lists hold one entry, `month` "2026-10", `days` 31; the baseline's are 0.
- Its baseline (`case_id` "baseline", settings {90, 30}): unserved 0, breaches 0, most starts 2, longest without a
  full charge 4. Every case: unserved 0, breaches 0, dawn worst 34.5 with 4 days below and no new day, unless the
  table says otherwise.

| Case (October, 31 days) | avoided L | added kWh | most starts | longest no full charge | file admission |
|---|---:|---:|---:|---:|---|
| `stop-90-reserve-25` | 5 | 0 | 3 | 5 | admitted |
| `stop-80-reserve-30` | 180 | 10 | 3 | 5 | admitted |
| `stop-80-reserve-25` | 190 | 20 | 7 | 5 | not (`starts`) |
| `stop-70-reserve-30` | 200 | 50 | 3 | 5 | admitted |
| `stop-70-reserve-25` | 210 | 80 | 3 | 5 | admitted |
| `stop-60-reserve-30` | 150 | 100 | 3 | 5 | admitted |
| `stop-60-reserve-25` | 250 | 150 | 3 | 8 | not (`full_charge`) |

**F1b expected** (the month is October's own entry, `months_averaged` ["2026-10"]; wear 0.05). The effects of
`stop-70-reserve-30`, in registry order: `candidate_l` −200, `battery_throughput_kwh` 50, `diesel_l` −200,
`fuel_cost` −250.00, `battery_wear` 2.50, `cost_to_serve` −247.50, `contribution` 247.50. The base `candidate_l` is
NOT_AVAILABLE (the helper) and is never needed (D-P6.3). Run outcome `RECOMMENDED`, with the near set at `≥ 3012.00 × 0.9 =
2710.80`.

| Option | monthly | 12 months | value | disposition | rank | reason |
|---|---:|---:|---:|---|---:|---|
| `no-action` | 0 | 0 | 0 | COMPARISON | — | — |
| `stop-90-reserve-25` | 6.25 | 75.00 | −15.00 | DEFERRED | — | NOT_WORTH_MORE_THAN_NO_ACTION |
| `stop-80-reserve-30` | 224.50 | 2694.00 | 2604.00 | ACCEPTABLE | 3 | — |
| `stop-80-reserve-25` | 236.50 | 2838.00 | 2748.00 | REJECTED | — | NOT_ADMITTED_STARTS |
| `stop-70-reserve-30` | 247.50 | 2970.00 | 2880.00 | RECOMMENDED | 1 | — (distance 20) |
| `stop-70-reserve-25` | 258.50 | 3102.00 | 3012.00 | ACCEPTABLE | 2 | — (distance 25) |
| `stop-60-reserve-30` | 182.50 | 2190.00 | 2100.00 | ACCEPTABLE | 4 | — |
| `stop-60-reserve-25` | 305.00 | 3660.00 | 3570.00 | REJECTED | — | NOT_ADMITTED_FULL_CHARGE |

Every `SETTING_GRID` option: `source_class` SIMULATED, `evidence_class` MODELLED, `assumed` ["diesel_price"],
`currency` USD; money effects carry `USD`, others null. `no-action`: SIMULATED, `DERIVED`, `assumed` [], `missing` [],
no effects.

- **F1a** (wear missing):
  - `stop-90-reserve-25` is as F1b (−15.00, DEFERRED). Its throughput change is exactly 0, so no wear value is
    needed.
  - Every other option has value `None`, with `missing` `[["battery_wear_rate_assumption", "DECLARED",
    "wear_rate"]]`. Its `fuel_cost` effect is still set: −250.00 for `stop-70-reserve-30`. Its `battery_wear`,
    `cost_to_serve` and `contribution` effects are `None` (D-P6.14).
  - The two not admitted are REJECTED. The other four are DEFERRED, `VALUE_NOT_AVAILABLE`.
  - Run outcome `RANKING_INCOMPLETE`, with no candidate.
- **F1c** (F1b without `stop-60-reserve-30`'s one-off): that option is DEFERRED, `VALUE_NOT_AVAILABLE`, `missing`
  `[["ONE_OFF", "DECISION", null]]`. Its monthly change is 182.50 and its 12-month change 2190.00. The three other
  candidates are ACCEPTABLE, `RANKING_INCOMPLETE`, with no rank. Run outcome `RANKING_INCOMPLETE`.
- **F1d** (F1b with every one-off 4000.00): every admitted value is ≤ −898.00, so the run outcome is
  `NO_ACTION_BEST`.
- **F1e** (F1b with every case's file admission false on `starts`, and most starts 7): run outcome `NOTHING_ADMITTED`.
  `stop-60-reserve-25` (longest 8) fails `full_charge` too: its file parts say so, first failing `starts`.
- **F1f** (exact tie; F1b with `stop-90-reserve-25`'s one-off 75.00): its value is 0.00, `DEFERRED`,
  `WORTH_THE_SAME_AS_NO_ACTION`, no rank; every other row as F1b (D-P6.5).
- **F1h** (declared season; F1b's base and one-offs, the study `study-f1h.json` = F1's without the `frame` key):
  every `SETTING_GRID` option's value, monthly and 12-month changes are `None`, with `missing`
  `[["SITE_MONTH_SIMULATION", "SIMULATION", "candidate_l"], ["SITE_MONTH_SIMULATION", "SIMULATION",
  "battery_throughput_kwh"]]`; the two not admitted are REJECTED as in F1b; the other five DEFERRED,
  `VALUE_NOT_AVAILABLE`; each `SETTING_GRID` row SIMULATED, MODELLED, `assumed` ["diesel_price"] (read by `val1`,
  §2); `admission` and `dawn` stored as in F1b; `months_averaged` []; run outcome
  `RANKING_INCOMPLETE` (D-P6.2). Its 2026-10 entries are present and never read.
- **F1i** (`setting_changes` only): a SITE_RECORD case with `avoided_l_by_month` September (30 days) 100 and October
  (31 days) 200, and an August entry of 12 days 999: the `candidate_l` delta is −150 exactly, `months_averaged`
  ["2026-09", "2026-10"] (August is partial and left out). Its `added_throughput_kwh_by_month` holds the same months
  and days (values 0, 0, 0).
- **F1j** (zero change, D-P6.29): F1b with a case `stop-90-reserve-25` of 0 L and 0 kWh: value −90.00, currency USD,
  `DEFERRED`, `NOT_WORTH_MORE_THAN_NO_ACTION`, no `ONE_OFF_CURRENCY`; every other row as F1b.
- **F1g** (grid edge): F1b, with the injected lever's stop axis cut to (90, 60), so the options are
  `stop-90-reserve-25`, `stop-60-reserve-30` and `stop-60-reserve-25`. The study file is `study-f1g.json`: F1's
  header and baseline, and only those three cases. `stop-60-reserve-30` is RECOMMENDED, `AT_GRID_EDGE`.
- **Refusal fixtures:**
  - F1 with the frame's `site_code` "MTO-001": `STUDY_FRAME_MISMATCH`.
  - F1 with October's entries at 30 days (partial): `STUDY_MONTH_NOT_COVERED`.
  - F1 with the baseline stop 85: `STUDY_BASELINE_MISMATCH`.
  - Case `stop-70-reserve-30` deleted: `STUDY_GRID_MISMATCH`.
  - An extra case `stop-75-reserve-30`: `STUDY_GRID_MISMATCH`.
  - An extra case `stop-90-reserve-30`: ignored and listed.
  - `stop-70-reserve-30`'s file admission set to false: `STUDY_ADMISSION_MISMATCH`.
  - `status` NOT_CALIBRATED: `STUDY_NOT_CALIBRATED`.
  - No `--study`: `STUDY_REQUIRED`.
  - Joseph runs it: `PERSON_ROLE_REQUIRED`.

**C1, a cold room (COLD_CHAIN; core `evaluate_options` only; one option `repair-chiller`, no admission).**
- Base: `base_kwh` 3000 (DECLARED), `k_kwh_per_crate_day` 2 (DECLARED), `crate_days` 1000 (RECORDED,
  `observed-financial`), `elec_price` 0.20 USD (RECORDED, `observed-financial`).
- The option's change: `model_factor` by −0.1, to 0.9 from its neutral 1 (`LeafChange`, MODELLED, `field-integrated`;
  D-P6.3). One-off 400.00 USD.
- Expected effects: `model_factor` −0.1, `kwh_model` −500, `kwh` −500, `energy` −100.00, `cost_to_serve` −100.00,
  `contribution` 100.00. 12 months 1200.00, value 800.00, RECOMMENDED, rank 1, `source_class` RECORDED (the declared
  leaves' origin `unknown` reads RECORDED, D-P6.25), `evidence_class` MODELLED, `assumed` []; money effects `USD`.
- **C1e** (plant fixture): C1 with `crate_days` of origin `source-emulated`: `source_class` EMULATED.
- **C1b:** `base_kwh` NOT_AVAILABLE. Value `None`, missing names `base_kwh`, outcome `RANKING_INCOMPLETE`;
  `source_class` RECORDED, `evidence_class` MODELLED, `assumed` [].

**E1, an EV depot (EV_DEPOT_CAPTIVE; one option `night-schedule`).**
- Base: `peak_kwh` 5000, `kwh_0000_0500` 2000, `peak_price` 0.30 USD, `night_price` 0.10 USD (all RECORDED,
  `observed-financial`). Every other leaf is from the helper.
- The option's changes: `peak_kwh` by −1000 (to 4000) and `kwh_0000_0500` by +1000 (to 3000) (`LeafChange`, MODELLED,
  `field-integrated`). One-off 0.00 USD.
- Expected effects, in registry order: the two leaves −1000 and +1000; `scheduled_kwh_night`, `supplied_kwh_night`,
  `buses_short_per_night` and `departures_missed` 0; `peak_cost` −300.00; `night_cost` 100.00; `energy_cost`
  −200.00; `penalties` 0; `cost_to_serve` −200.00; `contribution` 200.00.
- 12 months 2400.00, value 2400.00, RECOMMENDED, `source_class` RECORDED, `evidence_class` MODELLED, `assumed` []. `cost_per_departure_met` and `departures_met` are not in the result
  (they are outside the outcome's closure).

**K1, the real file's shape.** `backend/tests/fixtures/decisions/kobo-61d-study.json`: 0K4d's
`/opt/assetecon/evidence/0K4d/kobo-61d/study.json` (sha256 `c52e475554e6d4e2c713b7d8face961426c8d27b991315cb95bb974eccc78b61`
on 22 Nov), keeping only §3.1's keys. Its provenance goes in a sibling `.md`: the source path and the source's sha256.
It has no `frame` key, so it is a declared season.
- With the real lever and current settings {90, 30}: 13 options match, and `stop-90-reserve-30` is ignored and listed.
- Admission is recomputed equal on all 14 cases; every case is admitted (0K4d packet §2).
- With F1b's base leaves (wear present): every one of the 13 `SETTING_GRID` rows is `DEFERRED`,
  `VALUE_NOT_AVAILABLE`, value `None`, F1h's two `missing` entries, admission `admitted` true, SIMULATED, MODELLED,
  `assumed` ["diesel_price"]; `no-action` `COMPARISON`; run outcome `RANKING_INCOMPLETE`. `stop-70-reserve-30`'s dawn:
  `worst_soc_pct` "6611/190", `margin_points` "-39/190", `days_below` 4, `days` 61 (the file's `reading` 34.795 is
  never read).
- Plant: read the file's `2026-10` entry for `stop-70-reserve-30` (242.444 L) as the month; test 4's K1 case fails.

## 6. Tests (written first)

1. `difference`:
   - the parity test;
   - the F1b, C1 and E1 effects as literals;
   - a missing operand named, and an unchanged factor exactly 0;
   - the currency plant.
2. `read_study` and `models`: every refusal, K1's identity (frame `DECLARED_SEASON`), F1's frame, `ignored_cases`,
   F1i's `months_averaged` and delta.
3. `judge`: equal to `admit`'s parts on 0K4d's own test cases. 0K4d's two test files,
   `backend/tests/test_0k4d_admission.py` and `host/tests/test_0k4d_v8_study.py`, pass unchanged.
4. `evaluate_options`: F1a to F1j, C1, C1b, C1e, E1 and K1, every field of every row as a literal.
5. `EvaluationService` with the memory store (F1's lever injected with `grid_changes`, D-P6.21): F1b end to end, with
   the stored run equal to test 4's rows and the stored identity complete; every refusal in E3's order, each with the
   structure read not called; a `StructureError` in E6 refuses `STRUCTURE_UNAVAILABLE`, nothing written.
6. Postgres: F1b's run through 6a's adapter; the run's deferred completeness check holds; one `alembic heads`.
7. The command: the F1b JSON line, exact; each refusal's stderr and exit; no `@`.
8. No vertical code and no design value:
   - `decisions/evaluate.py` and `structure/difference.py` hold no registry structure key and no factor id literal
     (an AST scan of string constants against every registry's ids, except `OUTCOME_FACTOR`);
   - 6c's modules (`decisions/study_input.py`, `models.py`, `evaluate.py`, `run.py`, `structure/difference.py`;
     D-P6.22) hold no numeric literal outside `TIE`, the signs ±1 of `SETTING_GRID_CHANGES`, and 0 and 1 (an AST
     scan); no `30`, no `35` and no division by `days` (D-P6.2). 6a's `records.py` holds rules and is out of scope;
   - the R5 regex of 0K4d (`\b(210|2,?916|68)\b`, `\b(20|150) ?L\b`) has no hit under `decisions/`.
9. Seams:
   - D-P6.28's allowlist: under `decisions/`, only `study_input.py`, `models.py`, `evaluate.py` and `run.py` import
     `runs.admission` and `runs.replay_study`, and only names in their `__all__` or constants (6c amends 6a's test 9);
   - nothing imports `simulator` or `host` directly, and after `import assetops_backend.decisions.run` no
     `simulator*` or `host*` module is in `sys.modules`;
   - `structure/difference.py` imports only `structure.*` and the standard library.

**Plants** (each fails its named test; shown once in a scratch copy, with the run in the packet):
- read a missing wear rate as 0 (4: F1a's values appear);
- rank a REJECTED option (4: F1b rank 1 becomes `stop-60-reserve-25`);
- drop the near-set rule (4: F1b's Recommended becomes `stop-70-reserve-25`);
- treat a zero value as a candidate (4: F1f's `stop-90-reserve-25` ranks);
- read a declared season's month entries (4: F1h's values appear);
- pass `SiteInputs.stated` to the difference (1: a planted stated `fuel_cost` makes F1b's fuel effect 0);
- use the dawn days as a gate (4: F1b dispositions change);
- multiply `d(a) × val0(b)` in place of `val1(b)` (1: a planted case where the price also changes);
- skip the admission recomputation (5: the mismatch fixture passes);
- read `unknown` as the weakest class (4: C1 becomes SIMULATED), or ignore `source-emulated` (4: C1e stays RECORDED);
- write `"MINI_GRID"` in `evaluate.py` (8);
- the month as the window × 30 / days (2: F1i gives −147.54, 300 L × 30 / 61, not −150);
- the K1 plant above (4).

## 7. Done (questions; each can fail)

1. Is every value the structure's `contribution` under the option minus under no action, over the horizon, less the
   one-off, with nothing typed in by hand?
2. Is every missing input named, never read as zero, and does an unchanged factor's effect stay exactly zero?
3. Is a setting the rule does not admit rejected with its first failing part, and never ranked?
4. Among admitted settings, is the Recommended the nearest to today's within 10 % of the best? Is a ranking with a
   missing value withheld? Is "doing nothing is best" stated when it is?
5. Is each figure labelled SIMULATED, EMULATED or RECORDED by its inputs, with the assumed inputs listed?
6. Do a cold-room and an EV option go through the same code, with no structure named in it?
7. Is the study's identity stored, and does its admission agree with 0K4d's rule?
8. Does a declared season value nothing, and does a Site-record simulation value the mean of its full months, with no
   scaling and nothing from another Site (D-P6.2)?

## 8. Out of scope

Costed and hard bounds as rows (`6b`). Applying the setting (`6d`). Verifying it (`6e`). The screen and its words and
rounding (`6f`). Revenue-side options and quotes (`6g`). The plan's set search across decisions (`7c`). Sensitivity
and break-even (0K4d restated these as "Not available yet (`6c`)"; a later unit, §11 Q6). A study stored in the
database (§11 Q5). Running the simulation from the command. Writing the `frame` header into study files (0K4f): its acceptance
derives `frame` from the replay's input (the Site's stored readings), never from a flag or `StudyFrame`, and records a
`site_readings_digest` (D-P6.26; 6c's packet names this residual risk).

## 9. Units and dependencies

| Commit | Scope | Units |
|---|---|---:|
| 1 | `structure/difference.py`, parity, C1, E1 (tests 1, 9 in part) | 1.0 |
| 2 | `study_input.py`, `admission.py` measures and `DAWN_LIMIT_PCT`, `models.py`, `evaluate.py`, F1a-F1j, C1e (tests 2-4, 8) | 1.25 |
| 3 | `run.py`, the command, permissions, statements, K1, Postgres (tests 5-7) | 0.75 |
| | **6c** | **3.0** |

Depends on: owner P6 (met 22 Nov); `6a` merged; `0K4d` (on `main`, gate K); `0K1` (on `main`). Unblocks `6f`, `6g`,
`7c`, `9c`. Order: P6 → 6a (3.0) → 6c (3.0); `6d` and `6e` (2.5 each) build beside 6c after 6a (D-P6.10). Kobo's first
value also needs 0K4f's Site-record study (D-P6.2).

## 10. Reviewer handshake

Reviewer and implementer pre-flight run together, as one round (RULES §4, item 6). Their answers go in `rulings.md`
here, at rev 1.

## 11. Decisions (rev 1; P6 approved 22 Nov, every answer decided)

| # | Question | Decided | Ruling |
|---|---|---|---|
| Q1 | Battery wear rate missing (P6 #2) | Value "Not available yet", naming `wear_rate`; fuel effects still computed | D-P6.14 (owner) |
| Q2 | 12 months from a re-run (P6 #3) | 12 × the average of the Site-record study's full months, stated (`months_averaged`); a declared season values nothing | D-P6.15 (owner), D-P6.2 |
| Q3 | Choosing among admitted settings (P6 #4) | Best value; within 10 %, nearest today's; dawn never decides | D-P6.16 (owner) |
| Q4 | A missing value among admitted (P6 #5) | No Recommended (`RANKING_INCOMPLETE`) | D-P6.17 (owner) |
| Q5 | Where the study lives | A file, its sha256 and identity stored on the run | Architect, rev 0 default kept |
| Q6 | Sensitivity and break-even | Not in 6c | Architect, rev 0 default kept |
| Q7 | Sign of an avoided litre | A delta on `candidate_l` (−avoided), as the pack's option layer; `extra_l` untouched | D-P6.3 (replaces the rev 0 default) |
| Q8 | The source label | Weakest of the inputs used: SIMULATED, then EMULATED, then RECORDED | Architect, rev 0 default kept |
| Q9 | Nothing beats doing nothing (P6 #7) | `NO_ACTION_BEST`; 6f's sentence "Doing nothing is worth more than any setting tried"; a tie is `WORTH_THE_SAME_AS_NO_ACTION` | D-P6.19 (owner), D-P6.5 |

Open for the owner, defaults applied (`rulings.md` queue): Q1, Kobo's litres "Not available yet" until 0K4f.

## 12. Rev 3 amendments (review rulings D-P6.34 to D-P6.41, 22 Nov 2026; they override the text above where it differs)

- **§2 `Delta`** gains `zero_denominators: tuple[str, ...]` (registry order, () by default): the nodes whose fold met a
  zero denominator (D-P6.37).
- **§3.4 step 1, missing names (closed list, D-P6.37):** a changed leaf with no delta (its `LeafChange.missing`); a
  base leaf with a missing record (its record kind and family); `CURRENCY_MISMATCH`/`STRUCTURE`/None; `ONE_OFF`,
  `ONE_OFF_CURRENCY`/`DECISION`/None; `ZERO_DENOMINATOR`/`STRUCTURE`/node only for a tagged zero denominator (or a `v0`
  problem kind starting `ZERO_DENOMINATOR:`). Any other node is named by its `missing_leaves` through the leaf rule,
  deduplicated, registry order. A name outside this list raises.
- **§3.4 step 1, `horizon_change`** is computed in `evaluate`'s context (prec 34, ROUND_HALF_EVEN) (D-P6.41).
- **§3.4 step 2, effect currency (D-P6.34):** a money-unit effect whose change is exactly 0 and whose `Delta.currency`
  is None takes the option row's `currency`; a missing money effect, or a zero one on an option with no currency,
  stays null.
- **§3.4 step 3, `assumed` (D-P6.36):** the used leaves carried as `TARGET`/`ASSUMPTION` plus each used node's
  `FactorValue.assumed_leaves`, one list in registry order without repeats.
- **§3.5 / §4 E2-E3, generators (D-P6.38):** `option_inputs` branches on `NO_ACTION` and `SETTING_GRID` by name; any
  other generator refuses `LEVER_UNKNOWN` at E3 before the study and the structure read. `STUDY_REQUIRED` when the
  lever's generator is `SETTING_GRID` and no study is given.
- **§4, the structure read (D-P6.41):** the catch around `site_inputs` is `(StructureError, StoreUnavailable)`;
  `build_evaluation` wraps the read in a `decisions/adapters/` class mapping `SQLAlchemyError` to `StoreUnavailable`
  and takes keyword-only `levers`, `grid_changes` (production defaults). Every other exception propagates.
- **§5 F1j (D-P6.35):** `stop-90-reserve-25`'s `assumed` is [] (no price read); its zero money effects carry USD
  (D-P6.34). **§5 F1b:** "money effects carry USD" holds for every valued money effect; F1a's missing
  `battery_wear` stays null.
- **§6 (D-P6.40, D-P6.41):** test 1 adds (a) a planted registry with a changed leaf through `/`, `ceil` and `min`
  with a non-zero change: base a = 250, b = 100, c = 300, d(a) = +100; `a / b` changes 1, `ceil(a / b)` changes 1,
  `min(a, c)` changes 50 (literals); (b) `a × b` with both changed and b's base NOT_AVAILABLE: change MISSING naming b
  (and test 4: the row's `missing` names b by its record kind); (c) the option-only neutral short cut. Test 4 adds:
  F1b with one option's one-off in EUR (`missing` [["ONE_OFF_CURRENCY", "DECISION", null]], value None, `DEFERRED`
  `VALUE_NOT_AVAILABLE`, run `RANKING_INCOMPLETE`); one injected-changes case each for the near set at exactly
  `V × TIE`, a distance tie (higher value wins), `AT_GRID_EDGE` above current, R0's weakest class across mixed
  options; D-P6.36's node-assumption case; D-P6.37's zero-denominator and node-missing names; and every effect row
  as a literal (no helper arithmetic). Test 5 adds the `TypeError` and `StoreUnavailable` reads; test 6 adds
  `build_evaluation` end to end (D-P6.41); E2/E3 add D-P6.38's two cases. The plant list adds the eight of D-P6.40.
- **Deviations accepted (D-P6.39):** the months check in E3 after the frame check; `admit_person` lifted,
  `cli.run(build=)`, `StudyRefused`; `read_study(path, read_bytes)`, `EvaluationService(read_bytes=)`.
- **§9:** fix round 0.75 units; 6c is **3.75 units**.
