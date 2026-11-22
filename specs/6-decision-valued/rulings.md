# Step 6 rulings (D-P6.1 to D-P6.19): decisions valued against doing nothing, 6a and 6c

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

- **Ruling.** 6a 3.0 u (1.0, 1.25, 0.75) and 6c 3.0 u (1.0, 1.25, 0.75), as drafted; both under the 6-unit cap. Order:
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

## Decision queue (W3; defaults applied, owner answers in a batch)

| # | Question | Default applied | Why the owner should weigh in |
|---|---|---|---|
| Q1 | Kobo's fuel saved: P6 said it shows today; D-0K4.38 and your 21 Nov rule say "Not available yet" until 0K4f simulates Kobo's own October | "Not available yet" for litres and value; service checks shown; default #2 applies from 0K4f (D-P6.2) | Your P6 acceptance and your 21 Nov rule differ on Kobo today |
| Q2 | 5c's tile "Plan value, 12 months" before a plan record exists | Stays "Not available yet" until 7a/7c (D-P6.9) | The tile's line says "once decisions are recorded" |
| Q3 | Step 6 is invisible until 6f (after 6b and 6d) | Split 6f: 6f1 (Decisions rows and a read-only decision page from this read) right after 6c; 6f2 (the choice) after 6b/6d | Visible usefulness first (owner, 18 Nov) |
