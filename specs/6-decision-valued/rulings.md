# Step 6 rulings (D-P6.1 to D-P6.41): decisions valued against doing nothing, 6a and 6c

Architect (Claude), 2026-11-22. They apply the owner's acceptance of the seven P6 defaults ("accept all p6 defaults",
`owner/owner-accept-p6-defaults-2026-11-22.md`) to `6a-decision-records/spec.md` and `6c-option-evaluator/spec.md`,
both rev 1. They fold in what changed since the drafts of 21 Nov: D-0K4.38 to D-0K4.56, the owner's one-figure rule
(`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`), 0K4d's admission code, the 5c screen and the IA-P
spec, all on `main`, and the owner's Kobo answer (`owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`: Kobo stays
Simulated). Code read on `main` at `a26444647`. D-P6.13 to D-P6.19 are the owner's seven defaults, one each.

## D-P6.1 P6 is approved; the specs move to rev 1

- **Ruling.** P6 is approved (owner, 22 Nov 2026). Gate P of 6a and 6c is met. Each accepted default is a rule with a
  test (D-P6.13 to D-P6.19), and each spec cites it where it applies. The specs are ready for the handshake.
- **Why.** A default restated as a rule with a test cannot drift.

## D-P6.2 The world-month rule governs the valuation: a study values a setting only on the Site's own record

- **Ruling.**
  - A study file declares its frame. `frame: {"kind": "SITE_RECORD", "tenant": <slug>, "site_code": <code>}` is a
    simulation run on the Site's own recorded readings (for Kobo, its Simulated record; the label stays SIMULATED).
    Anything else, or no `frame` key, is `DECLARED_SEASON`. Every study on disk today, 0K4d's `kobo-61d` included,
    has no `frame` key.
  - **SITE_RECORD.** The tenant and Site must be the decision's, and the study's `*_by_month` lists must hold a full
    entry (its `days` = the month's calendar days) for the decision's `period`, else refused. A setting's monthly
    change is the mean of its full-month entries (D-P6.15). Partial months are left out. No × 30 / days scaling.
  - **DECLARED_SEASON.** No study amount reaches the month's leaves. Each changed leaf is missing,
    `MissingInput("SITE_MONTH_SIMULATION", "SIMULATION", <leaf>)`, so the values are missing and the run is
    `RANKING_INCOMPLETE` (D-P6.17) or `NOTHING_ADMITTED`. The admission and the dawn information are still computed
    and stored, in the study's own frame (its days). A season month labelled like the decision's month is never read:
    0K4d's file has a `2026-10` entry (242.444 L for stop 70), and a plant proves it is ignored.
  - **Kobo today:** litres, added battery use and value read "Not available yet" (6f's words, D-0K4.50: "needs a
    simulation of Kobo's own October"); both settings show their service checks. This lasts until 0K4f writes a
    SITE_RECORD study.
- **Why.** D-0K4.38: an amount of a replayed season's running "is never applied to the world's record of another
  month". 212.751 L comes from a season burning about 1,442 L a month; Kobo's October burns 1,060. The draft's
  × 30 / days put that figure on Kobo's October, the forbidden case. A missing frame reads as the weaker case, so an
  old file can never value anything. The run stores the file's sha256 and identity.
- **Effect on P6.** The proposal's "for Kobo today the fuel saved can be shown" no longer holds; queue Q1.
- **Seam for 0K4f.** Its study writer adds the `frame` header and keeps the `*_by_month` lists with their `days`.
- **Reverse:** read declared seasons too. That breaches D-0K4.38.

## D-P6.3 The generator lever changes `candidate_l` by a delta, as the pack's option layer does

- **Ruling.** An option's changes are deltas on leaves (`LeafChange`, 6c §2), never replacement values.
  `generator_stop_reserve` changes `candidate_l` by −(avoided litres a month) and `battery_throughput_kwh` by +(added
  throughput a month); `Lever.changes = ("candidate_l", "battery_throughput_kwh")`. On the option side a changed
  leaf's value is base + delta, missing when the base is, and needed only where a product has another changing operand.
- **Why.** The pack's layer reads `candidate_l: "candidate_l - avoided_candidate_l"` with `option_money_factors`
  `[candidate_l, battery_throughput_kwh]` (manifest lines 996, 1584); one figure per quantity asks the product to
  move the same factor. The effect reads "candidate running falls by N L". With a delta the base `candidate_l` is never
  needed, since `fuel_cost` reads d(`diesel_l`) × `diesel_price`; Kobo's split is blank on the product (D-0K4.45).
- **Reverse:** `extra_l` takes a signed change (draft Q7).

## D-P6.4 The difference reads expressions, never stated records

- **Ruling.** `structure/difference.py` folds every node from its expression on both sides and passes no `stated` map
  to `evaluate` (`SiteInputs.stated` is not read).
- **Why.** A stated node holds the observed actual (`fuel_cost` is the month's invoices, 4b1). Stated on both sides,
  every fuel effect would be 0. The counterfactual runs through the mechanism.
- **Reverse:** none sound.

## D-P6.5 Candidates within one decision; an exact tie goes to doing nothing

- **Ruling.** A setting is a candidate when admitted and valued; a computed zero is a value (D-0K4.41). Only a value
  above 0 is a candidate. Below 0: `DEFERRED`, `NOT_WORTH_MORE_THAN_NO_ACTION`. Exactly 0: `DEFERRED`,
  `WORTH_THE_SAME_AS_NO_ACTION`. The executive may choose any option not `REJECTED`, or none. N5's cross-decision rule
  stays 7c's.
- **Why.** Doing nothing is always available and costs nothing, so it wins ties; D-P6.19's sentence is true only of a
  strict loss.

## D-P6.6 Precision: stored unrounded; output money at cents, quantities at six places

- **Ruling.** Stored unrounded (`numeric`, `evaluate`'s `Context(prec=34, ROUND_HALF_EVEN)`). Each output (the JSON
  line, later 6f's read) rounds half-even once from the stored figure: money (`monthly_change`, `horizon_change`,
  `value`, money effects) to cents, other quantities to 6 places. The monthly change is never rounded before
  × `horizon_months`. Display formats stay 6f's.
- **Why.** D-0K4.42's rule for the pack's evaluator; the product and the pack round alike.

## D-P6.7 Refusal words: one statement per command family, numbers through slots

- **Ruling.** 6a adds one SC-1 statement `decision.refused` with a `code` slot (`type: state`, exhaustive), one variant
  per code, as `i18n/statements/en/agreed_action.py`. Every number or example in a sentence is a slot (D-SC1.21). 6c
  adds its codes to the same statement. Sweep: both specs' refusal tables and any later step-6 command.
- **Why.** `KEY_FORM` (`i18n/catalogue.py`) allows two segments, so the drafts' `decision.refused.<code>` keys fail
  the validator.

## D-P6.8 The read follows the target IA's Decisions list; 6a and 6c add no route

- **Ruling.** `DecisionService.for_tenant(tenant_id, *, period_from=None, period_to=None)` serves codes and names.
  Each decision carries `state` (`NOT_VALUED`, `WAITING`, `CHOSEN`, `UNDER_WAY`, `KEPT_AS_IS`), `decides_role`
  (`OPERATOR_EXECUTIVE`), `finding_id`, `home_category`, `recommended` (option, value, currency, or null), the options
  and the choice. IA-P's row (spec "The list defs", decisions): State "Waiting for a choice" = `NOT_VALUED` or
  `WAITING`, "Under way" = `UNDER_WAY` (6f words the others); Who decides = `decides_role`, then the chooser's name;
  At stake = `recommended`; the Findings list's "Its decision" joins on `finding_id`. No HTTP route or screen change in
  6a or 6c; 6f adds the route and swaps the list's interim source (placed Findings, D-IAP.3) for this read.
- **Why.** IA-P on `main` moves 5c's "Decisions" panel into the Overview's Decisions rows and makes `/decisions` a
  WORK item, with 6f replacing the interim source. 6f is then a source swap, not a panel inside the retired `dd-queue`.
- **Reverse:** 6a serves 5c's panel directly; rework once IA-P lands.

## D-P6.9 Where step 6 lands on screen

- **Ruling.** The IA Decisions rows (5c's MD2) are lit by 6f from this read. 5c's tile 4 "Plan value, 12 months" (MD1)
  is not lit by step 6; it stays "Not available yet" until 7a and 7c. 6a and 6c change no served string.
- **Why.** The tile is the plan's value across decisions within budget and crew visits (7c); a sum of chosen options
  would be a second "plan value" figure. Queue Q2.

## D-P6.10 Sizes, order and gates

- **Ruling.** 6a 3.0 u (1.0, 1.25, 0.75) and 6c 3.0 u (1.0, 1.25, 0.75), as drafted (6a 3.25 u at rev 2, commit 3
  1.0, after the handshake); both under the 6-unit cap. Order:
  6a reviewed and merged, then 6c; 6d and 6e may build beside 6c after 6a. Gates P and K are met; gate A is read at
  build (head `0071_person_on_actions`). The handshake runs before each slice's first commit.
- **Why.** The frame rule replaces the × 30 / days path rather than adding to it; the read's state and period filter are
  small. The coordinator keeps the sizes.

## D-P6.11 Pre-flight answered from the code

- **Ruling.** `evaluate._check_leaf` has no sign check. All three registries have `contribution`. `runs/admission.py`
  exposes `admit`, `AdmissionRule` (starts 6, full charge every 7 days, limit 7 − 1) and `ADMISSION_PARTS`. The study
  JSON carries `avoided_l_by_month` and `added_throughput_kwh_by_month` with `days`. `site_tenant_id_unique`,
  `finding_site_unique` and `operator_account UNIQUE (tenant_id, id)` exist; `agreed_action` has none, so 6a adds one.
  `check.py` still defers levers (D-3B1.6); the cross-registry checks run in `check_all()`. `SITE_TYPE_TO_STRUCTURE`
  is `structure/read.py`'s. 0K4d's tests are `backend/tests/test_0k4d_admission.py` and
  `host/tests/test_0k4d_v8_study.py`.
- **Why.** The drafts' pre-flight items, answered once by reading `main`.

## D-P6.12 A lever's axes share one unit

- **Ruling.** `check_levers` refuses a lever whose axes differ in `unit` (`STRUCTURE_LEVER`).
- **Why.** The near-set tie-break sums `|setting − current|` across axes, meaningful only in one unit.

## D-P6.13 Default #1: the operator's executive chooses, by name and date; "none" is valid

- **Ruling.** `decision.choose` is `(EXECUTIVE,)`; the choice keeps the person and the time; `--none` stores a null
  option. Rule: 6a §3.3 H; test 5.

## D-P6.14 Default #2: battery wear cost not stated → value "Not available yet", fuel saved shown

- **Ruling.** With `wear_rate` missing, an option's value is missing and names `wear_rate`; its fuel effects stay
  computed. Rule: 6c §3.4; F1a. It applies once the litres exist (D-P6.2 for Kobo).

## D-P6.15 Default #3: 12 × the re-run's average month, saying so

- **Ruling.** `horizon_months` 12 on every decision. The monthly change is the mean of the SITE_RECORD study's full
  months (D-P6.2), priced on the decision month's leaves; the 12-month change is 12 × it. The run stores the basis
  (`identity["months_averaged"]`) for 6f to state. Rule: 6a §2, 6c §3.3.

## D-P6.16 Default #4: highest value; within 10 %, nearest today's setting; dawn shown, never decides

- **Ruling.** The near set is candidates with value ≥ best × 0.9; the least distance from today's settings wins, then
  the higher value, then `option_key`. Dawn readings are stored and enter no rule. Rule: 6c §3.4; F1b, plants.

## D-P6.17 Default #5: no recommendation until every passing setting has a value

- **Ruling.** Any admitted option with a missing value makes the run `RANKING_INCOMPLETE`; no rank is given. Rule:
  6c §3.4; F1a, F1c.

## D-P6.18 Default #6: one-off stated by the site manager or finance lead, with a basis; doing nothing costs 0

- **Ruling.** `decision.one_off` is `(SITE_MANAGER, FINANCE)`, a site manager only on that Site; a basis is required.
  Doing nothing costs 0 by rule and cannot be stated (`NO_ACTION_ONE_OFF`). Rule: 6a §3.3 O; test 4.

## D-P6.19 Default #7: "Doing nothing is worth more than any setting tried"

- **Ruling.** When no admitted, valued option beats doing nothing, the run is `NO_ACTION_BEST`; 6f renders the owner's
  sentence. An exact tie is D-P6.5's. Rule: 6c §3.4; F1d.

## D-P6.20 6a's store reads a Site by id (handshake 6a I1, 6c I2)

- **Ruling.** `DecisionStore.site_by_id(tenant_id, site_id) -> SiteRef | None` in 6a's Protocol, memory store and
  adapter. 6c's E3 (frame check) and E4 (`site_inputs`) use it.
- **Why.** `DecisionRow` holds `site_id` only; without it 6c would edit 6a's three layers after 6a merged.

## D-P6.21 The setting-grid model is injectable (6c I1)

- **Ruling.** `setting_changes(..., *, grid_changes=SETTING_GRID_CHANGES)`; `EvaluationService(..., grid_changes=...)`.
  The start-up assertion (leaves equal `lever.changes`) runs over every entry passed in.
- **Why.** F1's injected lever must run end to end; the real map stays the only one in product code.

## D-P6.22 The no-figure scan covers 6c's modules; the dawn limit is a named constant (6c I3)

- **Ruling.** Test 8's numeric-literal scan covers `decisions/study_input.py`, `models.py`, `evaluate.py`, `run.py` and
  `structure/difference.py`; 6a's `records.py` holds rules (bounds, exits), not figures, and is out of scope by name.
  `runs/admission.py` gains `DAWN_LIMIT_PCT = Fraction(35)` as `admit`'s default; 6c imports it.
- **Why.** The scan exists to catch design figures; a 35 written into 6c would be a second home for the limit.

## D-P6.23 OD-25 at start-up: any disagreeing pin refuses (6a R2)

- **Ruling.** `check_levers` refuses a lever whose purpose factor's home category differs from that of any pinned
  factor that lists it.
- **Why.** One disagreeing pin is enough for `home_category` to disagree at run time.

## D-P6.24 A one-off's role: held at C3, covering the Site after the decision is read (6a I2)

- **Ruling.** C3 checks a held role of the command at any Site. After the decision is read, the recorded role is the
  first in `roles_of` order covering its Site (FINANCE every Site, SITE_MANAGER granted Sites), else
  `PERSON_ROLE_REQUIRED`.
- **Why.** The Site is known only after the decision is read; refusal order must be total.

## D-P6.25 The source label speaks for simulation and emulation only (6c R3)

- **Ruling.** `source_class` is SIMULATED when a `demo-simulated` origin is used, else EMULATED when `source-emulated`
  is, else RECORDED, which means "no simulated or emulated input" (`unknown` included). The evidence class carries
  declared, estimated and modelled inputs.
- **Why.** The chip warns of model-world inputs. Reading `unknown` as weakest would mark every priced Site SIMULATED,
  untrue the other way. Reverse: an `UNKNOWN` class (6a schema change).

## D-P6.26 The SITE_RECORD frame must be earned by 0K4f (6c R1)

- **Ruling.** 6c trusts the header. 0K4f's acceptance (its spec, when written) requires: the writer derives `frame`
  from the replay's input (the Site's stored readings by tenant and Site), never from a flag, never from
  `StudyFrame`; and the study records `site_readings_digest` for a later check. 6c's packet names the residual risk.
- **Why.** A stamped header on 0K4d's season file would value Kobo's October, D-0K4.38's forbidden case.

## D-P6.27 Storage and output forms (6a I5, I9; 6c I4, R6)

- **Ruling.** jsonb: `missing` a list of `[record_kind, source_family, factor_id|null]`; `assumed` a list of factor
  ids; `admission` and `dawn` 6c §3.5's objects with fractions `"n/d"` in lowest terms and integers as numbers;
  `settings` decimal strings. JSON lines: decimal strings (money two places), times `%Y-%m-%dT%H:%M:%SZ`, names for
  people, codes for categories; 6c's top-level keys `run_id, decision_id, outcome, source_class, frame,
  months_averaged, options`.
- **Why.** 6c and 6f read what 6a stores; one form each, written once.

## D-P6.28 The slices' import rules (6c R4)

- **Ruling.** Under `decisions/`, only `study_input.py`, `models.py`, `evaluate.py` and `run.py` import
  `runs.admission` and `runs.replay_study`, and only names in their `__all__` or constants. Importing `decisions.run`
  loads no `simulator*` or `host*` module. 6c amends 6a's test 9 to this allowlist.
- **Why.** 6a's blanket ban and 6c's need collided; the real seam is "never runs a simulation".

## D-P6.29 A zero change takes the one-off's currency (6c I5)

- **Ruling.** When the outcome's change is exactly 0 and reads no money leaf, the option's currency is its one-off's,
  and no `ONE_OFF_CURRENCY` is added. With no one-off, `ONE_OFF` is missing as usual.
- **Why.** Otherwise a valued option is refused by 6a's currency check or wrongly reads as missing.

## D-P6.30 A refused record is `RECORD_INVALID`, exit 2, one variant of `decision.refused` (6a review F1, F4)

- **Ruling.** The adapter's cross-row checks refuse `RECORD_INVALID`: in `add_run`, an evaluation's option not of
  `run.decision_id`, or a `one_off_id` whose option is not the evaluation's; in `add_choice`, an `option_id` not of
  `decision_id`, or a `run_id` of another decision. Both stores make all four checks, read inside the write's
  transaction before any insert. `RECORD_INVALID` joins `REFUSAL_EXIT` at exit 2 and `decision.refused` (D-P6.7) as
  variant `record_invalid`: "This record does not fit the decision it names, so nothing was stored." It has no number,
  so no slot. Tests: one case per check in test 5 (memory) and test 7 (Postgres), and the statement case renders it.
- **Why.** One name for the class "the parts of a record do not belong together"; the operator cannot fix it by
  retrying, so it is not exit 3, and a code outside the statement crashes `cli.refuse` (F4's `StatementError`).

## D-P6.31 One error for a refused record in both stores (6a review Q2, F4)

- **Ruling.** The Postgres adapter maps a driver error of SQLSTATE class 22 (data) or 23 (integrity) that is not an
  identity conflict it already resolves (the re-run unique keys) to `DecisionRefused("RECORD_INVALID")`; every other
  `SQLAlchemyError` stays `StoreUnavailable` → `DECISIONS_UNAVAILABLE` (exit 3). This covers both deferred triggers,
  every FK and CHECK. The memory store already raises `RECORD_INVALID` for the same cases. Sweep: every `decisions/`
  writer, now and in 6c (E7 `add_run`); test 7 adds one Postgres case each for a deferred trigger and a CHECK showing
  exit 2. Fixed on the 6a branch with F1, before 6c builds.
- **Why.** A 6c test on the memory store must expect what production raises, and an invalid record must never tell an
  operator to retry.

## D-P6.32 `option_effect_change_or_missing` is guarded on the array type (6a review Q1, F3)

- **Ruling.** `CONSTRAINT option_effect_change_or_missing CHECK (CASE WHEN jsonb_typeof(missing) = 'array' THEN
  (change_per_month IS NULL) = (jsonb_array_length(missing) > 0) END)`. A non-array `missing` gives NULL there, and
  `option_effect_missing_check` refuses it by name; test 6b asserts that name in place of `SHADOWED`. Names unchanged.
- **Why.** The named check should fire; the migration is immutable after merge, so only now is it free.

## D-P6.33 F2 is fixed now; F5 is queued (6a review)

- **Ruling.** F2 in this fix round: after `add_choice` returns `already=True`, apply H2's comparison (`ALREADY_CHOSEN`
  when the stored choice differs) and print the stored choice's option key. F5 is queued as a 6a follow-up: a
  `name_of(tenant_id, person_id)` store read so each command makes one small read and names the row just written;
  deviation 3 stands until then.
- **Why.** F2 can misreport an executive's choice and is a few lines; F5 is cost and rare naming, not correctness.

## D-P6.34 A money effect that is exactly 0 carries the option's currency (6c review Q1, deviation 1)

- **Ruling.** When an `EffectRow`'s unit is a money unit, its change is exactly 0 and its `Delta.currency` is None (no
  money value read), `evaluate.py` sets its currency to the option row's `currency` (after D-P6.29). A money effect
  whose change is missing keeps currency null (F1a's `battery_wear`), and so does a zero money effect of an option
  whose own currency is None. Non-money rows stay null. §5's "money effects carry USD" stands, with that exception.
- **Why.** D-P6.29's class extended from the option row to its effect rows: the stored row is what 6f and 7c read, and
  a null currency on a valued 0 would read as "currency unknown". It is a label on an exact 0, not a figure.

## D-P6.35 F1j's zero row lists no assumed input (6c review Q2, deviation 2)

- **Ruling.** Accepted as built. §5 F1j says `stop-90-reserve-25`'s `assumed` is [] (nothing changed, so no price was
  read); "every other row as F1b" means the other options.
- **Why.** §3.4 step 3 literally; listing an assumption the figure did not read would overstate it.

## D-P6.36 `assumed` includes a used node's assumed leaves (6c review Q3, deviation 3)

- **Ruling.** `assumed` is the union, in registry order without repeats, of each used leaf whose base
  `missing.carried_as` is `TARGET` or `ASSUMPTION` and each used node's `FactorValue.assumed_leaves` from `v0`. New
  test 4 case: a planted registry where the outcome reads a node resting on an ASSUMPTION leaf; `assumed` names that
  leaf. No fixture literal changes (no fixture reads such a node).
- **Why.** Evidence, origins and currency already propagate from a used node's value; an assumption under a node is
  still an assumption under the figure the executive chooses by.

## D-P6.37 A missing value is named by its cause, never a catch-all (6c review Q4, L3, deviation 4)

- **Ruling.** `ZERO_DENOMINATOR`/`STRUCTURE`/node is written only for a zero denominator: the difference fold tags it
  (a new `Delta.zero_denominators: tuple[str, ...]`, registry order, () by default) and a `v0` node whose `problem`
  kind starts `ZERO_DENOMINATOR:` reads the same. A node with no value for any other reason is named by its own
  `missing_leaves`, each through the leaf rule (§3.4 step 1), deduplicated in registry order. A name that resolves to
  none of these raises (a code defect, not a missing input). §3.4 gains the closed list of `MissingInput` names
  6c writes; 6f's spec carries `ZERO_DENOMINATOR`'s "Not available yet" text. No `ONE_OFF_CURRENCY` when the option
  has no currency stands (its change is already missing).
- **Why.** "Missing is never zero" includes naming: the executive and 6f must see the record that is missing, and a
  mislabelled cause sends the operator to the wrong record.

## D-P6.38 Each generator is branched on by name; an unmodelled one refuses (6c review Q5, L2, deviation 5)

- **Ruling.** `option_inputs` branches on `NO_ACTION` (no changes, no study) and `SETTING_GRID` (the grid model)
  explicitly. A decision whose options carry any other generator refuses `LEVER_UNKNOWN` (6a's code, exit 2) at E3,
  before the study is read and before the structure read. E2's `STUDY_REQUIRED` is raised when the lever's generator
  is `SETTING_GRID` and no study is given. Tests: E2 on the lever's generator; an option with a planted generator outside those two refuses
  `LEVER_UNKNOWN` with the structure read not called.
- **Why.** A generator with no model must not read "worth the same as doing nothing" (a missing value shown as 0).
  `LEVER_UNKNOWN` is the existing class "the evaluator has no model for this lever"; a new code would add a statement
  variant for the same meaning. 6g or 6b adds its branch with its model.

## D-P6.39 Deviations 6 to 8 accepted (6c review Q6)

- **Ruling.** As built: the months check inside E3 after the frame check (6); 6a's `admit_person` lift, `cli.run(build=)`
  and `StudyRefused` (7); `read_study(path, read_bytes)` and `EvaluationService(read_bytes=)` (8). Recorded in the spec
  (rev 3 amendments).
- **Why.** Each is the order or the seam the spec's own rules and the persistence guard require.

## D-P6.40 Every spec'd rule has a plant; test 4 is literal (6c review Q7, M1, L1, L4)

- **Ruling.** §6's plant list gains eight, each failing its named test and shown failing in the fix packet: the
  non-zero `/`, `min`, `max`, `ceil`, `floor` change replaced by 0 (1); a changed leaf with a missing base read as base
  0 (1); `ONE_OFF_CURRENCY` never added (4); R0's source class strongest instead of weakest (4); the near set `>` for
  `>=` (4); a distance tie broken by the lower value (4); `AT_GRID_EDGE`'s upper branch removed (4); the option-only
  neutral short cut removed (1). Test 4's expected effect rows are literals, with no helper arithmetic (L4).
- **Why.** The class is "a spec'd rule whose break no test sees"; the fix is a plant per rule, not three tests.

## D-P6.41 Only a declared failure reads as STRUCTURE_UNAVAILABLE; the composition is tested end to end (6c Q8)

- **Ruling.** `run.py`'s catch around `site_inputs` narrows to `(StructureError, StoreUnavailable)`. `build_evaluation`
  passes the structure read through a wrapper in `decisions/adapters/` that maps a `SQLAlchemyError` to
  `StoreUnavailable`; `decisions/run.py` imports no SQLAlchemy. Any other exception propagates (a traceback, never exit
  3). Sweep: every `except Exception`/`BaseException` in 6c's modules is narrowed to named errors, or re-raises after
  cleanup (`build_evaluation`'s dispose stays). `build_evaluation` gains keyword-only `levers` and `grid_changes`
  passed to `EvaluationService` (production defaults; D-P6.21's seam through the composition). `horizon_change` is
  computed in `evaluate`'s 34-digit context.
- **Tests.** Test 5: a read raising `TypeError` propagates as `TypeError`, nothing written; one raising
  `StoreUnavailable` refuses `STRUCTURE_UNAVAILABLE`, exit 3, nothing written. Test 6 gains `build_evaluation(URL, ...)`
  end to end on ON1's onboarded Lakeside `KOBO-001`, period 2026-10, F1's test lever, grid and `study-f1.json`, with
  the one-offs of test 6: the stored run's outcome and each row's `value`, `missing` and `assumed` as literals derived
  by hand from what ON1 stores for KOBO-001 (the derivation written in the packet), then `dispose()`.
- **Why.** A wiring fault must surface as a fault, not as "the month's figures cannot be read right now"; the real
  composition is the one path no test ran.

## Decision queue (W3; owner answers in)

| # | Question | Answer |
|---|---|---|
| Q1 | Kobo's fuel saved before 0K4f | Owner, 22 Nov: "Not available yet (Recommended)" (`owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`); D-P6.2 stands |
| Q2 | 5c's tile "Plan value, 12 months" before a plan record | Default applied: "Not available yet" until 7a/7c (D-P6.9); no owner answer yet |
| Q3 | 6f split | Owner accepted: 6f1 (Decisions rows, read-only page) after 6c; 6f2 (the choice) after 6b/6d |
