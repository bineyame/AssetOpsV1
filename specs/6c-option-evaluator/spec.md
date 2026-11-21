# 6c: options valued against doing nothing (the evaluator; implementer spec)

**Status: DRAFT, awaiting owner P6.** Not build authority. Every default is *proposed* (§11) and none is logged in
`.ai/decisions/`. Architect (Claude), 2026-11-21, rev 0. Lane 3 (`delivery-plan.md` §2, row `6c`). **3.0 units**,
three commits. Discovery review (W5): a money figure and a new mechanism. `USER_REVIEW_REQUIRED: true` (these are the
figures the executive will choose by; no screen).

- **Owner proposal:** `specs/6-decision-valued/P6-proposal.md`. **Reviewer guide:** `reviewer-guide.md` (this folder).
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
- **Builds on:** `6a` (merged: records, `DecisionStore.add_run`, `LEVERS`); `0K4d` (**merged, gate K**:
  `runs/admission.py`, and the study file shape of `tools/kobo_replay_study.py` `outcome_json`, `admission_json`);
  `3B3` (`structure/evaluate.py`, `structure/expressions.py`, `registry.parsed_text`); `3B7a` and the read
  (`structure/composition.py` `build_structure_read(url).read.site_inputs(site, month, known_at)`).
- **Mock:** non-screen. It supplies vNEXT `#/decision/kobo-generator`'s option values, the rejected option's reason,
  the recommendation, and each option's "Effect under each heading" (the effects carry their factor; `6f` reads each
  factor's home category). The mock's +$2,916.00 "design estimate" and "reserve rejected at dawn" are restated by
  0K4m (D-0K4.15, D-0K4.29). `6f` labels any remaining gap MOCK DEVIATION D4.

## 0. Before you start (gates)

- **Gate P (owner).** P6 approved, with §11's answers recorded. Then rev 1.
- **Gate 6a.** `git grep -n "def add_run" main -- backend/assetops_backend/decisions/records.py` gives one line.
- **Gate K.** `git show main:backend/assetops_backend/runs/admission.py` exists (0K4d merged).
- **Pre-flight (in the packet, before code):** (1) `evaluate()` accepts a negative `extra_l` on a MINI_GRID leaf map
  (no sign check in `_check_leaf`); if it refuses, stop and ask. (2) The 0K4d study file's case keys hold every key
  in §3.1. (3) Every registry in `REGISTRIES` has a `contribution` row.

## 1. Outcome and why

`python -m assetops_backend.evaluate_options --tenant lakeside-power --as wanjiru@lakeside-power.example --decision
<6a's Kobo decision> --study /opt/assetecon/evidence/0K4d/kobo-61d/study.json` writes one run. For each of the 13
settings it holds the litres saved a month, the extra battery use, the fuel money saved, and the wear cost. It also
holds the value over 12 months net of the one-off, or the input that is missing; whether 0K4d's rule admits the
setting; and the setting's dawn readings. The run's outcome is one of: a recommendation; "doing nothing is best";
"ranking incomplete" (naming what is missing); or "nothing admitted". Gate questions: does every value come from the
structure re-evaluated with the option's changes, against no action, on the same leaves? Is a missing input never a
zero, while an unchanged factor's effect is exactly zero? Does a not-admitted setting never rank? Does the same code
value a cold-room and an EV option with no vertical branch?

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

def difference(registry: Registry, base: Mapping[str, LeafValue], option: Mapping[str, LeafValue],
               changed: frozenset[str]) -> Mapping[str, Delta]
```
- `base` is the period's leaf map (every leaf of the registry). `option` is `base` with each `changed` leaf replaced.
  Both are first evaluated whole: `v0 = evaluate(registry, base)`, `v1 = evaluate(registry, option)`.
- **Scope:** the result holds the changed leaves and every node that is in `OUTCOME_FACTOR`'s dependency closure and
  references a changed leaf, directly or through other nodes, in registry order. Any other node is left out.
- **The rule, per expression `e`** (in `evaluate`'s context, `Context(prec=34, rounding=ROUND_HALF_EVEN)`, nothing
  quantised). `d(e)` is a value or MISSING(leaves):
  - a changed leaf: `v1 − v0` (the option's value minus the no-action value; both are present, since an OPTION_ONLY
    leaf is NEUTRAL on the base);
  - an unchanged leaf or a literal: `0`, needing no value;
  - a node reference: `d` of its expression;
  - `−a`: `−d(a)`. `a ± b`: `d(a) ± d(b)`. MISSING if either is.
  - `a × b`: `t1 + t2`, where `t1 = 0` if `d(a) == 0`, else `d(a) × val1(b)`; and `t2 = 0` if `d(b) == 0`, else
    `val0(a) × d(b)`.
  - `a ÷ b`, and `min`, `max`, `ceil`, `floor`: `0` when every operand's `d` is exactly `0`. Otherwise it is
    `val1(e) − val0(e)`.
  - `val0(x)` and `val1(x)` fold the sub-expression on that side from `v0` and `v1` (a reference reads its
    `FactorValue.value`). If any value needed is `None`, the result is MISSING, naming that value's missing leaves (a
    leaf names itself; a node names its `missing_leaves`).
  - "Exactly 0" compares numerically: `Decimal("0.00") == 0`. A zero change needs no value of the other operand. That
    is the only short cut, and it holds because nothing changed. It is not a missing value read as zero.
- `used`, `evidence`, `origins`: every factor whose value a `val0` or `val1` read, plus the changed leaves.
  `evidence` is the weakest by `EVIDENCE_ORDER`. `currency` is the one currency of the money leaves used. If two
  differ, the change is MISSING with the missing leaves `("currency",)`. That is a planted case, and no fixture has
  it in real data.
- **Parity test (W2):** a private `_fold(expr, values)` computes `val0` and `val1`. For every node of all three
  registries, on a leaf map where every leaf has a value, `_fold(parsed_text(row.expression), v)` equals
  `evaluate(...)[node].value`.

## 3. Commit 2: the study, the admission, the evaluator

### 3.1 `decisions/study_input.py` (pure; reads one study file)

```python
@dataclass(frozen=True)
class CaseInput:
    case_id: str; settings: Mapping[str, Fraction]          # {"stop_soc_pct": .., "reserve_soc_pct": ..}
    avoided_l: Fraction; added_throughput_kwh: Fraction
    measures: AdmissionMeasures                              # runs/admission.py (§3.2)
    file_admission: tuple[bool, str | None, tuple[tuple[str, bool], ...]]   # admitted, first failing, parts
    file_limits: Mapping[str, Fraction]                      # part name -> limit, absolute parts only
    worst_dawn_soc_pct: Fraction; dawn_days_below: int; new_dawn_days_below: tuple[str, ...]
@dataclass(frozen=True)
class StudyInput:
    sha256: str; identity: Mapping[str, Any]; input_class: str; days: int
    baseline: CaseInput; cases: Mapping[str, CaseInput]      # by case_id, file order kept
def read_study(path: Path) -> StudyInput                    # raises StudyRefused(code)
```
- A number is `{"exact": "n/d", ...}` → `Fraction(int(n), int(d))`. Only `exact` is read. `reading` is ignored.
- **Header keys read** (all required): `input_class` (in `INPUT_CLASSES`), `evidence_class` (`MODELLED`), `commit`,
  `model`, `season`, `season_inputs_digest`, `trajectory_digests`, `assumptions`, `admission_rule`, `status`,
  `window_start`, `days`, `baseline`, `cases`. `identity` is these keys except `baseline` and `cases`, plus
  `"ignored_cases"` (§3.3), as stored on the run.
- **Case keys read** (baseline the same, without `admission`): `case_id`, `stop_soc_pct`, `reserve_soc_pct`,
  `avoided_l`, `added_throughput_kwh`, `unserved_kwh`, `reserve_breach_steps`, `max_starts_in_a_day`,
  `longest_days_without_full_charge`, `worst_dawn_soc_pct`, `dawn_days_below`, `new_dawn_days_below`, `admission`
  (`admitted`, `first_failing_part`, `parts[].name`, `parts[].passed`, `parts[].limit`).
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
`__all__` gains the two names.

### 3.3 `decisions/models.py` (the lever models; the only place a factor or field name of a lever's model is written)

```python
DAYS_PER_MONTH = 30          # 0K4d's "a month = window × 30 / days"
SETTING_GRID_CHANGES: Mapping[str, tuple[tuple[str, str, int], ...]] = MappingProxyType({
    # lever_id -> (changed leaf, study case field, sign)
    "generator_stop_reserve": (("extra_l", "avoided_l", -1), ("battery_throughput_kwh", "added_throughput_kwh", 1)),
})
ORIGIN_OF_INPUT = MappingProxyType({"RECORDED": "field-integrated", "EMULATED": "source-emulated",
                                    "SIMULATED": "demo-simulated"})
def setting_changes(lever: Lever, case: CaseInput, days: int) -> Mapping[str, Decimal]
    # leaf -> sign × field × 30 / days, as Decimal(num) / Decimal(den) in evaluate's context
def option_leaf(value: Decimal, input_class: str) -> LeafValue
    # LeafValue(value, "MODELLED", ("replay-study",), None, None, None, (ORIGIN_OF_INPUT[input_class],))
```
- Matching (each mismatch refuses `STUDY_GRID_MISMATCH`, naming the key): every `SETTING_GRID` option's
  `option_key` is a `case_id`, and that case's settings equal the option's settings. Cases matching no option are
  allowed only if their settings equal the decision's `current_settings`; they are listed in
  `identity["ignored_cases"]`. Any other extra case is refused.
- The study's baseline settings must equal the decision's `current_settings`, else `STUDY_BASELINE_MISMATCH`.
- `SETTING_GRID_CHANGES[lever]`'s leaves must equal `lever.changes` (a start-up assertion in the module's test).

### 3.4 `decisions/evaluate.py` (pure; no structure key and no factor id is written in it)

```python
EVALUATOR_VERSION = "option-evaluator-1"
TIE = Decimal("0.9")                       # within 10 % of the best value (D-0K4.29 keeps the 10 % as 6c's)
@dataclass(frozen=True)
class OptionInput:
    option: OptionRow; changes: Mapping[str, LeafValue] | None   # None for no action
    admission: tuple[AdmissionPart, ...] | None                  # None: no admission rule for this generator
    dawn: Mapping[str, str] | None; one_off: OneOffRow | None
def evaluate_options(registry: Registry, base: Mapping[str, LeafValue], decision: DecisionRow,
                     lever: Lever | None, inputs: tuple[OptionInput, ...]) -> tuple[str, tuple[EvaluationRow, ...]]
    # (run outcome, one EvaluationRow per option in position order); ids filled by the caller
```
**Per option** (one `difference()` call each, with `changed = set(changes)`):
1. `monthly_change = d[OUTCOME_FACTOR].change`; `currency = d[...].currency`. `horizon_change = monthly_change ×
   decision.horizon_months`. `value = horizon_change − one_off.amount` (no action's one-off is 0 by rule; 6a Q6).
   `missing`, in this order: `d[OUTCOME_FACTOR]`'s missing leaves, each as `MissingInput(leaf.missing.record_kind,
   leaf.missing.source_family, leaf)` from the base leaf; then `("ONE_OFF", "DECISION", None)` when no one-off is
   stated; then `("ONE_OFF_CURRENCY", "DECISION", None)` when its currency differs from `currency`. Any missing input
   leaves `value` `None`. A missing one-off leaves `monthly_change` and `horizon_change` set.
2. `effects`: one `EffectRow` per `Delta` in the result, in its order. `unit` is `str(row.unit)`.
3. `source_class`: `SIMULATED` if `demo-simulated` is in the outcome's `origins`; else `EMULATED` if
   `source-emulated` is; else `RECORDED`. `evidence_class` is the outcome's `evidence`. `assumed` lists the used
   leaves whose base `missing.carried_as` is `ASSUMPTION`, in registry order.
4. `admission`, `dawn`: stored as given (decimal strings, §3.5).

**Dispositions, in this order:**
- **R0.** No action is `COMPARISON`, with value 0, monthly and horizon changes 0, `currency` `None`, `evidence_class`
  `DERIVED`, `source_class` the weakest across the other options (`RECORDED` when there are none), and no effects.
- **R1.** Admission given and not admitted: `REJECTED`, reason `NOT_ADMITTED_` plus the first failing part in upper
  case (`NOT_ADMITTED_STARTS`). Its value is still computed and stored, but it is never ranked.
- **R2.** `value` is `None`: `DEFERRED`, reason `VALUE_NOT_AVAILABLE`.
- **R3.** `value <= 0`: `DEFERRED`, reason `NOT_WORTH_MORE_THAN_NO_ACTION`.
- **R4.** Otherwise the option is a candidate.

**The run's outcome:**
- Every option except no action is `REJECTED`: `NOTHING_ADMITTED`.
- Else, if any admitted option is R2 because its value is missing: `RANKING_INCOMPLETE`. Every candidate is
  `ACCEPTABLE` with reason `RANKING_INCOMPLETE` and no rank.
- Else, with no candidate: `NO_ACTION_BEST`.
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

The dawn readings never enter a rule above (D-0K4.9; P6 #4 proposed).

### 3.5 The study path's inputs (`decisions/run.py`, `EvaluationService.evaluate`)

Per `SETTING_GRID` option: `changes = {leaf: option_leaf(v, study.input_class) for leaf, v in
setting_changes(...)}`. `admission = judge(baseline.measures, case.measures)` is recomputed. It must equal the file's
`admitted`, `first_failing_part` and each part's `passed`, and the file's limits must equal `AdmissionRule()`'s
(starts 6, full charge `7 − 1`), else `STUDY_ADMISSION_MISMATCH`. Stored as `{"admitted", "first_failing_part",
"parts": [{"name", "case_value", "baseline_value", "limit", "judged", "passed"}]}` (fractions as `"n/d"`).
`dawn = {"worst_soc_pct", "margin_points"` (worst − 35), `"days_below", "new_days_below"}`.

## 4. Commit 3: the command and the run

`EvaluationService(decisions: DecisionService's store, accounts, structure_read, *, clock, new_id, levers=LEVERS,
registries=REGISTRIES).evaluate(*, tenant_slug, as_email, decision_id, study_path: Path | None) -> RunRow`. The steps
run in order, and the first that fails refuses:
- **E0.** The common steps C1 to C3 of 6a §3.3, with command `decision.evaluate`: `(ANALYST,)`, added to
  `COMMAND_ROLES`.
- **E1.** No such decision: `DECISION_NOT_FOUND`.
- **E2.** The lever's generator is `SETTING_GRID` and there is no study path: `STUDY_REQUIRED`.
- **E3.** `read_study`, and the §3.3 matching.
- **E4.** `known_at = now` (one clock read). `base = structure_read.site_inputs(site_ref, decision.period,
  known_at).leaves`. Any exception: `STRUCTURE_UNAVAILABLE` (exit 3).
- **E5.** The latest one-offs: `store.latest_one_offs`.
- **E6.** `evaluate_options`.
- **E7.** `store.add_run(RunRow(...))`, with study identity and sha256 set.

Every call writes a new run, because a valuation is dated. The latest run is the one a choice binds (6a H3).

Command: `python -m assetops_backend.evaluate_options --tenant SLUG --as EMAIL --decision UUID [--study PATH]`.
Its main, its refusal output and its exit codes follow 6a §4. Success prints one JSON line with these keys: `run_id`,
`decision_id`, `outcome`, `source_class`, and `options`. `options` holds one entry per option in position order:
`option_key`, `disposition`, `reason_code`, `rank`, `monthly_change`, `horizon_change`, `value`, `currency`,
`missing` (a list of `[record_kind, source_family, factor_id]`), and `admitted` (true, false or null). Figures are
decimal strings, unrounded. Rounding is `6f`'s (5c §2.1's formats). SC-1 statements
`decision.refused.<code>` (6a §3.4's module) gain:
- `STUDY_REQUIRED`: "Give the season re-run for this kind of change (--study)."
- `STUDY_UNREADABLE`: "The season re-run file cannot be read."
- `STUDY_NOT_CALIBRATED`: "The season re-run did not match the Site's own run, so it cannot value anything."
- `STUDY_LABELS_INVALID`: "The season re-run is not labelled as a model on simulated, emulated or recorded readings."
- `STUDY_BASELINE_MISMATCH`: "The season re-run starts from other settings than this decision's."
- `STUDY_GRID_MISMATCH`: "The season re-run does not hold exactly this decision's settings."
- `STUDY_ADMISSION_MISMATCH`: "The season re-run's service checks do not match the rule."
- `STRUCTURE_UNAVAILABLE`: "The month's figures cannot be read right now."

## 5. Fixtures (hand-written; the tests write these literals, W2)

**Leaf helper** (tests only): `leaves_for(registry, given)` gives every leaf of the registry:
- each `given` leaf as written;
- each OPTION_ONLY leaf NEUTRAL at its neutral;
- each CALENDAR leaf DERIVED;
- every other leaf NOT_AVAILABLE, with `Missing(fb.kind, fb.family, "NOT_RECEIVED", None, (), fb.words, None)`.

A priced or declared leaf has origins `("unknown",)`, as `sources.py` gives today.

**F1, a Kobo-shaped decision (MINI_GRID, synthetic study, injected lever `test_stop_reserve`).**
- The lever: axes `stop_soc_pct` (90, 80, 70, 60) and `reserve_soc_pct` (30, 25); template and `changes` as
  `generator_stop_reserve`. The current settings are {90, 30}, so the decision has 7 options plus no action. Period
  2026-10, horizon 12.
- Each option's one-off: 90.00 USD, 0 crew visits, stated by Peter.
- Base leaves: `diesel_price` 1.25 USD (ESTIMATED, carried ASSUMPTION). `wear_rate` is NOT_AVAILABLE in F1a and 0.05
  USD DECLARED in F1b.
- The study file is `backend/tests/fixtures/decisions/study-f1.json`. Its header: `input_class` SIMULATED,
  `evidence_class` MODELLED, `commit` "f1" repeated 20 times, `model` "mini-grid/8", `season` "v2", digests "a" × 64
  and "b" × 64, `assumptions` ["fixture"], `admission_rule` ["fixture"], `status` CALIBRATED, `window_start`
  "2026-08-31T21:00:00Z", `days` 60.
- Its baseline (`case_id` "baseline", settings {90, 30}): unserved 0, breaches 0, most starts 2, longest without a
  full charge 4. Every case: unserved 0, breaches 0, dawn worst 34.5 with 4 days below and no new day, unless the
  table says otherwise.

| Case (window of 60 days) | avoided L | added kWh | most starts | longest no full charge | file admission |
|---|---:|---:|---:|---:|---|
| `stop-90-reserve-25` | 10 | 0 | 3 | 5 | admitted |
| `stop-80-reserve-30` | 360 | 20 | 3 | 5 | admitted |
| `stop-80-reserve-25` | 380 | 40 | 7 | 5 | not (`starts`) |
| `stop-70-reserve-30` | 400 | 100 | 3 | 5 | admitted |
| `stop-70-reserve-25` | 420 | 160 | 3 | 5 | admitted |
| `stop-60-reserve-30` | 300 | 200 | 3 | 5 | admitted |
| `stop-60-reserve-25` | 500 | 300 | 3 | 8 | not (`full_charge`) |

**F1b expected** (a month is the window × 30 / 60; wear 0.05). The effects of `stop-70-reserve-30`, in registry
order: `extra_l` −200, `battery_throughput_kwh` 50, `diesel_l` −200, `fuel_cost` −250.00, `battery_wear` 2.50,
`cost_to_serve` −247.50, `contribution` 247.50. Run outcome `RECOMMENDED`, with the near set at `≥ 3012.00 × 0.9 =
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

Every option: `source_class` SIMULATED, `evidence_class` MODELLED, `assumed` ["diesel_price"].

- **F1a** (wear missing):
  - `stop-90-reserve-25` is as F1b (−15.00, DEFERRED). Its throughput change is exactly 0, so no wear value is
    needed.
  - Every other option has value `None`, with `missing` `[["battery_wear_rate_assumption", "DECLARED",
    "wear_rate"]]`. Its `fuel_cost` effect is still set: −250.00 for `stop-70-reserve-30`. Its `battery_wear`,
    `cost_to_serve` and `contribution` effects are `None`.
  - The two not admitted are REJECTED. The other four are DEFERRED, `VALUE_NOT_AVAILABLE`.
  - Run outcome `RANKING_INCOMPLETE`, with no candidate.
- **F1c** (F1b without `stop-60-reserve-30`'s one-off): that option is DEFERRED, `VALUE_NOT_AVAILABLE`, `missing`
  `[["ONE_OFF", "DECISION", null]]`. Its monthly change is 182.50 and its 12-month change 2190.00. The three other
  candidates are ACCEPTABLE, `RANKING_INCOMPLETE`, with no rank. Run outcome `RANKING_INCOMPLETE`.
- **F1d** (F1b with every one-off 4000.00): every admitted value is ≤ −898.00, so the run outcome is
  `NO_ACTION_BEST`.
- **F1e** (F1b with every case's file admission false on `starts`, and most starts 7): run outcome `NOTHING_ADMITTED`.
- **F1g** (grid edge): F1b, with the injected lever's stop axis cut to (90, 60), so the options are
  `stop-90-reserve-25`, `stop-60-reserve-30` and `stop-60-reserve-25`. The study file is `study-f1g.json`: F1's
  header and baseline, and only those three cases. `stop-60-reserve-30` is RECOMMENDED, `AT_GRID_EDGE`.
- **Refusal fixtures:**
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
- The option changes `model_factor` to 0.9 (MODELLED, `field-integrated`). One-off 400.00 USD.
- Expected effects: `model_factor` −0.1, `kwh_model` −500, `kwh` −500, `energy` −100.00, `cost_to_serve` −100.00,
  `contribution` 100.00. 12 months 1200.00, value 800.00, RECOMMENDED, rank 1, `source_class` RECORDED.
- **C1b:** `base_kwh` NOT_AVAILABLE. Value `None`, missing names `base_kwh`, outcome `RANKING_INCOMPLETE`.

**E1, an EV depot (EV_DEPOT_CAPTIVE; one option `night-schedule`).**
- Base: `peak_kwh` 5000, `kwh_0000_0500` 2000, `peak_price` 0.30 USD, `night_price` 0.10 USD (all RECORDED,
  `observed-financial`). Every other leaf is from the helper.
- The option changes `peak_kwh` to 4000 and `kwh_0000_0500` to 3000 (MODELLED, `field-integrated`). One-off 0.00 USD.
- Expected effects, in registry order: the two leaves −1000 and +1000; `scheduled_kwh_night`, `supplied_kwh_night`,
  `buses_short_per_night` and `departures_missed` 0; `peak_cost` −300.00; `night_cost` 100.00; `energy_cost`
  −200.00; `penalties` 0; `cost_to_serve` −200.00; `contribution` 200.00.
- 12 months 2400.00, value 2400.00, RECOMMENDED. `cost_per_departure_met` and `departures_met` are not in the result
  (they are outside the outcome's closure).

**K1, the real file's shape.** `backend/tests/fixtures/decisions/kobo-61d-study.json`: 0K4d's
`/opt/assetecon/evidence/0K4d/kobo-61d/study.json`, keeping only §3.1's keys. Its provenance goes in a sibling `.md`:
the source path and the source's sha256.
- With the real lever and current settings {90, 30}: 13 options match, and `stop-90-reserve-30` is ignored and listed.
- Admission is recomputed equal on all 14 cases.
- `stop-70-reserve-30`'s `extra_l` is `−Fraction(file exact) × 30 / 61` exactly, and it reads −212.75 at 2 decimals
  (0K4d packet §2).
- With F1a's base leaves, the outcome is `RANKING_INCOMPLETE`.

## 6. Tests (written first)

1. `difference`:
   - the parity test;
   - the F1b, C1 and E1 effects as literals;
   - a missing operand named, and an unchanged factor exactly 0;
   - the currency plant.
2. `read_study`: every refusal, K1's identity, and `ignored_cases`.
3. `judge`: equal to `admit`'s parts on 0K4d's own test cases. 0K4d's two test files pass unchanged.
4. `evaluate_options`: F1a to F1g, C1, C1b and E1, every field of every row as a literal.
5. `EvaluationService` with the memory store: F1b end to end, with the stored run equal to test 4's rows; every refusal.
6. Postgres: F1b's run through 6a's adapter; the run's deferred completeness check holds; one `alembic heads`.
7. The command: the F1b JSON line, exact; each refusal's stderr and exit; no `@`.
8. No vertical code and no design value:
   - `decisions/evaluate.py` and `structure/difference.py` hold no registry structure key and no factor id literal
     (an AST scan of string constants against every registry's ids, except `OUTCOME_FACTOR`);
   - `decisions/` holds no numeric literal outside `TIE`, `DAYS_PER_MONTH`, and 0 and 1 (an AST scan);
   - the R5 regex of 0K4d (`\b(210|2,?916|68)\b`, `\b(20|150) ?L\b`) has no hit under `decisions/`.
9. Seams:
   - `decisions/evaluate.py` imports `structure.difference`, `structure.registry`, `runs.admission` (types only) and
     `decisions.records`, and nothing under `runs/` that replays;
   - nothing imports `simulator` or `host`;
   - `structure/difference.py` imports only `structure.*` and the standard library.

**Plants** (each fails its named test; shown once in a scratch copy, with the run in the packet):
- read a missing wear rate as 0 (4: F1a's values appear);
- rank a REJECTED option (4: F1b rank 1 becomes `stop-60-reserve-25`);
- drop the near-set rule (4: F1b's Recommended becomes `stop-70-reserve-25`);
- use the dawn days as a gate (4: F1b dispositions change);
- multiply `d(a) × val0(b)` in place of `val1(b)` (1: a planted case where the price also changes);
- skip the admission recomputation (5: the mismatch fixture passes);
- write `"MINI_GRID"` in `evaluate.py` (8);
- monthly as × 30 / 61 hard-coded (4: F1 uses 60 days).

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

## 8. Out of scope

Costed and hard bounds as rows (`6b`). Applying the setting (`6d`). Verifying it (`6e`). The screen and its words and
rounding (`6f`). Revenue-side options and quotes (`6g`). The plan's set search across decisions (`7c`). Sensitivity
and break-even (0K4d restated these as "Not available yet (`6c`)"; proposed for a later unit, §11 Q6). A study stored
in the database (§11 Q5). Running the replay from the command.

## 9. Units and dependencies

| Commit | Scope | Units |
|---|---|---:|
| 1 | `structure/difference.py`, parity, C1, E1 (tests 1, 9 in part) | 1.0 |
| 2 | `study_input.py`, `admission.py` measures, `models.py`, `evaluate.py`, F1a-F1g (tests 2-4, 8) | 1.25 |
| 3 | `run.py`, the command, permissions, statements, K1, Postgres (tests 5-7) | 0.75 |
| | **6c** | **3.0** |

Depends on: owner P6; `6a` merged; `0K4d` merged (gate K); `0K1` (merged, behind 0K4d). Unblocks `6f`, `6g`, `7c`, `9c`.
The critical path for P6's first figure is P6 → 6a (3.0) → 6c (3.0). `6d` and `6e` (2.5 each) build beside 6c after 6a.

## 10. Reviewer handshake

Reviewer and implementer pre-flight run together, as one round (RULES §4, item 6). Their answers go in `rulings.md`
here, at rev 1.

## 11. Decision queue (W3; every default *proposed*, none decided)

| # | Question | Proposed default | Alternative |
|---|---|---|---|
| Q1 | Battery wear rate missing (P6 #2) | Value "Not available yet", naming it; fuel money still an effect | The owner states a typical LFP rate, labelled assumed with its basis (D-0K4.27 class); +0.5 unit for a declared-assumption command |
| Q2 | 12 months from a 61-day replay (P6 #3) | 12 × the window's average month (× 30 / days), stated | Monthly only until a full-year replay; `horizon_change` and `value` null |
| Q3 | Choosing among admitted settings (P6 #4) | Best value; within 10 %, nearest today's; dawn never decides | Dawn days below break near-ties; or no Recommended, the top three shown |
| Q4 | A missing value among admitted (P6 #5) | No Recommended (`RANKING_INCOMPLETE`) | Recommend among the valued, flagged |
| Q5 | Where the study lives | A file, its sha256 and identity stored on the run | A `replay_study` table (+0.75 unit) |
| Q6 | Sensitivity and break-even | Not in 6c | Price −20 % and break-even litres in 6c (+0.5 unit) |
| Q7 | Sign of an avoided litre | `extra_l` takes the signed change (negative is less running), its row words unchanged | A new OPTION_ONLY leaf `avoided_l` (registry change, 3B3 review) |
| Q8 | The source label | Weakest of the inputs used: SIMULATED, then EMULATED, then RECORDED | Two labels, the replay's and the price's |
