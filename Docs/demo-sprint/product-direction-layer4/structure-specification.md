# Structure specification (the contract every figure is computed under)

**Layer 4 companion artifact 12 · rev 13 · AssetOps Architect (Claude) · 17 Nov 2026** · rev 13.1 (19 Nov): naming only, under the design's OD-6 (rev 16.7). No rule, path or meaning changed, so the independent model written from rev 13 stays valid.

The owner's twelfth message asked for this order of work: write the whole structure specification first, then make the data, code and screens conform to it. This document is that specification. It contains no figures.

Two programs implement it, written separately:

- `evaluate_structure.py` produces `derived-values.json`.
- `independent_model.py` was written from this document and the manifest alone, by a helper that never read the evaluator.

`check_manifest.py` compares three things against `independent_model.py` and never imports the evaluator: the evaluator's output, the manifest's stated copies and the documents' tagged figures.

Anything that affects a figure or a choice and is **not** derived under this specification is a declared input, and it is listed in `derivation-register.md`.

Terms: *record path* means a dotted path into the site's context (§2.3). *Expression* means the language of §2.4.

---

## 1. Declared inputs (the only things not derived)

| Class | Meaning | Where in the manifest | Flag carried |
|---|---|---|---|
| Structure declaration | the node expressions of each vertical and the record-to-leaf map | `structures`, `factor_map`, site `factor_sources` | the spec itself (M1) |
| Record | an observed fact, a contract term or a dated event | tenant and site records (period, observations, physical, tariff, prices, incident, entitlement, decision rows) | coverage class (RECORDED, ESTIMATED) |
| Quote | a price, lead time or duration offered by a supplier or contractor | option `params` and `cost_lines`, with `basis` | `basis` |
| Replay design value | a figure a calibration replay must reproduce before it is relied on | option `params` with `design_value: K\|M\|E`, and physical fields marked as spike outputs | "design value" label wherever shown |
| Assumption | a value with no record or quote | option `params` with `assumption:` | "assumption" label |
| Policy declaration | the operator's obligation bounds and how each decision treats them | `evaluation.bounds`, `plan.decisions[].kind / hard / fallback / optional` | reason text; owner question where open (Q15) |
| Owner or person decision | budget, crew limits, switches, horizon | tenant `portfolio_constraints`, `plan.budget`, `plan.switches` | switch shown on screen |
| Presentation | labels, names, ordering, narrative text with no figure | rows' `reason`, names, routes | none needed |

---

## 2. Time, contexts and expressions

### 2.1 Time

- **`as_of`** is the decision date.
- **The accounting period** has `evaluation.period_days` days and ends on `evaluation.period_end`. A period record may declare its own `period_end` (November to date does).
- **The Protect reporting horizon** ends on `evaluation.horizon_end`. Protect effects of options are stated from `as_of` up to and including this date.
- **The value (money) horizon** of a tenant ends at `as_of` + `portfolio_constraints.horizon_months` months − 1 day. A whole number of years is added to the year. Money effects that depend on a restore date run to that date, capped at the value horizon.
- **Business days** are Monday to Friday. There is no holiday calendar.

### 2.2 Sides evaluated per site

The side `plan` is a Site's **target** side. Its key stays as a machine-only exception to the design's OD-6, under which "plan" means only the portfolio's plan of §6 (design "Words used here", Architect's call).

| Side | Record |
|---|---|
| `plan` | `period.plan` |
| `actual` | `period.actual`, merged with `observations.october`; where a field appears in both, the observation wins |
| `november_to_date` | `observations.november_to_date`, where present |

A side whose leaves cannot all be resolved is reported as "not decomposed: stated total" with the record's `contribution`, or failing that its `total`. It is never reported as evaluated.

### 2.3 Context available to expressions

The context holds:

- `record` (the side's record);
- `prices` and `energy_model` (the tenant's);
- `physical`, `tariff`, `incident`, `entitlement` and `observations` (the site's);
- `tenant`, `site`, `as_of`, `period_days` and `period_end`;
- for an option: `row` (the option's decision row, found by `id` in the site's `decision.options`, `entitlement.options` or `entitlements[].options`) and `restore_date` (§4.2).

### 2.4 Expression language

- Numbers and names. A name resolves to an option parameter first, then a structure node, then a factor, then a context path.
- `+ - * /` and unary `-`.
- `min`, `max`, `ceil`, `floor`.
- `days_incl(a, b)` = (b − a) + 1 days. `days_between(a, b)` = b − a days.
- `nights_listed(list, from, to)`: the number of dates d in the list with from ≤ d < to. If `to` is missing there is no upper limit.
- Paths: `a.b`, `a[0]`, `a['key']`.
- `x | y`: the value of x, or y if x cannot be resolved.

All arithmetic is decimal. Reported money and quantities are rounded half-even to 0.01. Percentages and ratios are rounded to the decimals the measure declares.

---

## 3. Factors and layers (M1, M2)

- **Leaves.** For a site of vertical V, each leaf is `factor_map[V][leaf]`, unless the site declares `factor_sources[leaf]`, which then replaces it. The leaf is evaluated in the side's context.
- **Nodes.** Each node is `structures[V][node]`, evaluated over the leaves and the other nodes. The evaluation order is any order consistent with the references. Every node and every leaf is reported for each evaluated side.
- **Portfolio composition per side.**
  - If every site of the tenant is evaluated, each node is the sum over the sites. When the sums contain `departures_met` and `cost_to_serve`, `cost_per_departure_met` = Σ cost to serve / Σ departures met.
  - Otherwise, the tenant's total is the sum of the stated totals, and the sites that are not decomposed are listed. When the side's records state `departures_required`, `cost_per_departure_required` = that total / Σ departures required (amended after the independent build).
- **Operations measures (O2).** For each `portfolio.operations.measures[]` entry that has a `numerator`:
  - per site: numerator / denominator × `scale`;
  - portfolio: Σ numerators / Σ denominators × `scale`;
  - both rounded to `decimals` (default 2);
  - if the entry has no `denominator`, the portfolio figure is the sum of the numerators.

---

## 4. Rights and restore (M3)

### 4.1 Rights

A right is every `entitlement` and `entitlements[]` entry of a site, and every `incident.entitlement` mapping, keyed by `asset`. Its fields are:

- `eligibility`;
- `claim_state`;
- `cover_value`;
- `notice_deadline` or `notice_term`. Every right whose claim has not been notified must carry one of the two.

**Covered.** A right is *covered* when eligibility = POTENTIALLY_COVERED and claim_state ∉ {DENIED, REJECTED}.

**Notified.** A claim is *notified* when claim_state ∈ {NOTIFIED, ACKNOWLEDGED, ACCEPTED, DENIED, REJECTED}.

**State at `as_of`.** A covered, un-notified right whose `notice_deadline` is before `as_of` is LAPSED for every option. This is a state, so it is not counted as any option's loss.

**Deciding options.**
- An option *touches* a right when one of these holds:
  - one of its cost lines is `covered_by` the right;
  - its restore is `performed_under` the right;
  - it lists the right in `voids_rights`, `set_rights` or `files_notice`.
- Every option of a plan decision that contains a touching option also decides that right.
- Nothing else decides a right. There is no hand-placed key.

**Per option, applied in this order:**
1. `set_rights` sets eligibility.
2. `voids_rights` sets eligibility to VOIDED. If the right was covered, its `cover_value` is lost.
3. For a covered, un-notified right with a `notice_deadline` that this option decides: if the option files no notice (`files_notice[right]`, a date spec) or files after the deadline, the right becomes LAPSED and its `cover_value` is lost.

**Rights nodes (per option and per reference).** These are added to the option's nodes:

| Node | Value |
|---|---|
| `claimable_cover` | Σ cover of covered rights at the site |
| `unclaimable_cover` | Σ cover of INSUFFICIENT_EVIDENCE rights |
| `cover_lost` | the cover lost under the option |
| `cover_not_claimable` | `unclaimable_cover` + `cover_lost` |

### 4.2 Restore dates

**Spec fields.**
- `date` is `as_of`, a context path, or `none`.
- `plus` adds whole days, as a list of parameters or paths.
- `business_days` adds business days after the `plus` days.
- `performed_under: right`: if that right is not covered, the spec named in `if_not_covered` replaces it. These are the operator's own procurement drivers (a quote or an assumption). If `if_not_covered` is absent, the date is `none`. The replacement may declare `crew_visits`, which then replaces the option's crew visits: the operator's own technician now does the work (amended in rev 13 after perturbation RC).

**Day counts.**

| Parameter | If restored | If `none` |
|---|---|---|
| `days_to_restore` | (min(restore, horizon_end + 1 day) − as_of) days | days from as_of to horizon_end inclusive |
| `value_days_to_restore` | the same, capped at the value horizon end | days from as_of to the value horizon end inclusive |

**Parameter order.** Parameters are resolved in declared order. A parameter that reads `restore_date` is resolved after the restore date.

---

## 5. Option evaluation (M3)

1. **Forward baseline.** The option starts from the site's `actual` leaves. The leaves listed in `evaluation.forward_baseline[V]` are then reset to their declared expressions, because options look forward from `as_of`.
2. **Reference.**
   - If `reference_option` is given, it is that option's evaluated nodes, with the same overrides, and that option's operator one-off.
   - Otherwise, it is the baseline after `reference_factors`, with the site's rights at `as_of`, and one-off 0.
3. **Option factors.** Start from the baseline. Apply `reference_factors`, then `changes` in declared order: each change is an expression over the factors so far, the nodes and the parameters. Then apply any sensitivity `factors` overrides.
4. **Money.**
   - Δ = contribution(option) − contribution(reference). `months` defaults to 1.
   - For each cost line, the amount is an expression. The operator share is 0 if the line's `covered_by` right is covered under the option, and 1 otherwise.
   - One-off = Σ amount × share.
   - **Value = Δ × months − (one-off − reference one-off).**
5. **Valued in money.** An option is valued in money when Δ ≠ 0, it is not a `comparator`, and it is not `is_reference`.
6. **Bounds.** For each `evaluation.bounds[V]` entry whose node exists, violation = max(node − limit, 0). The limit is an expression.
7. **Reported.**
   - The `evaluation.protect_nodes[V]` nodes for the option and for the reference.
   - The rights nodes, `cover_lost`, LAPSED rights and right states.
   - The restore date and the parameters.
   - Crew visits, from the option's `crew_visits` (an expression or a value) or else the row's `crew_visits`. If neither exists, crew visits are unknown; they are never defaulted.
   - The `option_detail[V]` nodes.
8. **Sensitivities.** Re-run the option with the sensitivity's `params` and `factors` overrides. The sensitivity value is Δ × months − (one-off − reference one-off), computed from that run.

---

## 6. The plan's items: the allocator

### 6.1 Candidates

Each decision in a plan is protective, valued or comparator. Comparators are evaluated and listed, never chosen.

- **Protective decision.** The candidates are the options whose violation over the decision's `hard` bounds is 0.
  - If there are none and the decision declares `fallback: least_violation`, every option is a candidate.
  - If there are none and no fallback is declared, the plan is infeasible.
  - Exactly one option is taken.
- **Valued decision.** The candidates are the options valued in money (or with an evaluable value) whose hard violation is 0, with the same fallback rule.
  - "No option" is also a candidate when the decision is `optional` (the default) or has no candidate.
  - A non-optional decision must take one of its options.

### 6.2 Feasibility of a combination

A combination (one candidate per decision, in declared order) is feasible when all of these hold:

1. **Budget.** Σ operator one-off ≤ the budget, which is the case's `budget` switch if present, else the plan's budget (`budget`).
2. **Crew visits.** Σ crew visits ≤ the tenant's `portfolio_constraints[plan.crew_limit]`.
3. **Switch requirements.** Every option with `requires_switch: s` has switch s true in the case.
4. **Dated dependencies.** Every option with `requires_restore` meets it:
   - the option of the named decision taken in the same combination has a restore date r (no option, or no restore, fails);
   - r + `plus_business_days` business days ≤ the deadline;
   - the deadline is `by`, replaced by `by_if_switch[s]` when switch s is true in the case.

### 6.3 Choosing the plan

- **Figures of the plan.** Spend = Σ operator one-off of the items. Valued option costs = Σ operator one-off of the valued-in-money items. Not valued in money = spend − valued option costs, a money figure (amended, ambiguity A20).
- **Ranking.** The plan is the feasible combination with the greatest key: (− total violation, value, − spend).
  - Total violation is summed over the decisions that are on their fallback.
  - Value is the sum of valued-in-money options' values.
  - Ties go to the combination found first when decisions are enumerated in declared order, with options in declared order and "no option" first.
- **Protective choices** are read from the chosen combination.
  - Each is "meets its hard bounds", or "least violation within the plan" with the violation.
  - A trade-off is reported when another option of the decision has a smaller violation.
- **Admissible** (per option) means a hard violation of 0 under its decision. Options in no decision are admissible.

### 6.4 Cases, downside and sensitivities

- **Cases.** Every combination of switch values, in declared order. The key joins the values with "/". Booleans are written `True` and `False`; numbers as written in the manifest (amended after the independent build, ambiguity A18).
- **Switch sensitivity.** A switch value mapped in `switch_sensitivity` replaces every option's value with that sensitivity's value.
- **Downside drops.** Each re-runs the default case without the listed options.
- **Sensitivity values.** For each sensitivity of the default plan's valued options that is not already a downside or a switch sensitivity: the sum over those options, using the sensitivity where the option has one and its value otherwise.
- **Switch-sensitivity values.** For each switch value mapped in `switch_sensitivity`, the value of the case with that switch value and every other switch at its first value. It is reported under the sensitivity's name.
- **Downside.** The minimum of the downside drops, the sensitivity values and the switch-sensitivity values (amended after the independent build, ambiguity A19).

### 6.5 Owner-question variants

For each `owner_question_variants[q][v].patch`:

- apply the `set` and `remove` operations to a copy of the declared inputs;
- re-evaluate the plans;
- report each case's value, spend, items and visits, and the value and spend change against the applied variant.

---

## 7. Conformance of documents and screens

- **Tagged figures.**
  - A figure tagged `<!--fig:path-->` in a document equals the value at that path, with the sign written before it. `fig:-path` means the negated value.
  - A record figure tagged `<!--rec-->` is a money record of the manifest.
  - Every written occurrence of a plan's or an option's evaluated money figure (with or without cents) and of an O2 percentage in a figure-bearing document is tagged.
- **Rendered manifest strings.** A string in the manifest that is rendered on screen and states a figure the structure computes carries it as a `{fig:path}` placeholder, which the screen fills from the evaluation. The checker rejects such a string that states the figure as a literal.
- **Screen code.** The screen code holds no literal equal to an evaluated figure, except the entries of a per-file, per-literal allow-list, each with a reason.
