# 6f: the Decisions screen (implementer spec, with its reviewer guide)

**Status: rev 1 (D-P6.51 to D-P6.58: the union is withdrawn, the list is records only, lever words come from 6h).
Handshake Q1 answered by the owner ("Build 6h"); Q2-Q8 accepted.** Architect (Claude), 2026-11-22. Demo-critical.
**Rulings:** `rulings.md` (this folder), D-P6.42 to D-P6.58 (D-P6.43 withdrawn, D-P6.44 amended). **Owner rulings it applies:** D-P6.8, D-P6.9, D-IAP.3, D-P6.13 to D-P6.19, D-P6.37 and the 6f split (`specs/6-decision-valued/rulings.md` queue Q3, owner:
"6f1 (Decisions rows, read-only page) after 6c; 6f2 (the choice) after 6b/6d"). `USER_REVIEW_REQUIRED: true` (UI,
evidence interpretation, demo narrative). W5: **discovery review** (money figures on screen, a new read and route).

**Parts.** **6f1** (this spec, binding): the Decisions list's source and the read-only decision page, **3.75 units** in
three units. **6f2** (the choice on screen): its structure is fixed in §11; its unit card is written after the 6b and
6d specs, so their bounds and Action carrier fold in (D-P6.42). Each part is under the 6-unit cap.

**Read first (by section):** this spec; `rulings.md`; 6a `spec.md` §2, §3.5; 6c `spec.md` §3.4, §3.5, §12; IA-P
`spec.md` §2.3 "Object pages", §4.1, §4.2, §5.2 ("The list defs", decisions row), §6 P6 and P7; IA-1 `spec.md` §4.1,
§4.2; 5c `spec.md` §2.3 (the records a gap needs).

## 0. Governing sources

- **Mock (governs, `.ai/RULES.md` §6):** vNEXT `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`
  `#/decision/kobo-generator`, the decision shape of IA-1 §4.1: `uxDecisionSlots` in `loop-ux.js` (sticky bar; L1
  `head` = meta line, stepper, "How this works"; L1 `rec` = the recommendation card; L2 `cards` = option cards; L3
  `secs` = six answer-titled sections; drawers "Evidence and records", "The Actions", "How this works"). The list is
  IA-P's `decisions` def (IA-2b §4) as built on `task/IA-P1-frame-portfolio`. Visual tokens:
  `frontend/mockups/v72/foundation-sheet.html`. Departures: §9.
- **Owner rules cited on this screen:**
  - UI standing brief (`owner/owner-ui-standing-brief-2026-11-20.md`): the right control per content (cards to
    compare a few, a table for all, drawers for evidence, disclosure for reasoning), one interaction grammar (the
    IA-P list component, the IA-1 decision shape), exposure that scales (14 options, 3 to 300 Sites), simplicity by
    design, every number honest with its basis.
  - The decision page brief (`owner/owner-decision-page-redesign-2026-11-20.md`): the question in one line, the
    recommendation with one number, option cards with the same numbers, reasoning collapsed, evidence in a drawer,
    a slim status line.
  - Missing data is stated as missing: "Not available yet", naming the record that would fill it
    (`owner/owner-V-01a-round2-feedback-2026-10-12.md`; `.ai/RULES.md` §1). A missing value is never 0; a computed 0
    is 0.
  - One model-computed figure per quantity, labelled by its source
    (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`). The page computes nothing: every figure is a
    stored 6c figure rounded once for display (D-P6.6). Kobo's values read "Not available yet" until 0K4f
    (`owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`).
  - Decisions inside the outcome mechanism (outcome `contribution` → driver → evidence (the Finding) → lever →
    options and the choice → Action → verify): the page shows each link (§5.4 "What it changes", the Finding in the
    evidence drawer, the Action, "How we will check it worked").
  - The four outcome categories (`owner/owner-summary-confirmations-2026-11-19.md`): every decision carries its
    heading (`home_category`, OD-25 and `owner/owner-decision-heading-rule-2026-11-19.md`), and every effect row its
    factor's heading.
  - Client-facing plain language, no system vocabulary (`owner/owner-T028-presentation-direction-2026-10-04.md`):
    §6.4's banned-word test.
  - Range output consistent across Site types (`owner/owner-range-output-rule-2026-11-12.md`): §8's matrix.

## 1. Existing, then new

**Today on `main` (after IA-P1):** the Decisions list (`/decisions`) shows one row per placed Finding (D-IAP.3),
"Who decides" and "Due" read "Not available yet" (MD-IAP-2), and a row opens the Finding's recommendation view. 6a
stores decisions, options, one-offs and choices; 6c values every option against doing nothing and stores the run.
Nothing on screen reads those records.

**6f1 adds:**
1. Two reads: `GET /api/decisions?from=&to=` (the list rows) and `GET /api/decisions/{decision_id}` (the page view),
   built on the server from 6a's read, with every served string an SC-1 statement (D-P6.45).
2. The Decisions list's source becomes the **decision records** of the range (D-P6.8, D-P6.52). 6h gives every
   Site type its levers, so every Site type keeps rows; a row says who decides, its state and what is at stake. The
   waiting counts (E0, the tile, the inbox badge) count the records waiting (D-P6.44 as amended).
3. The decision page `/decisions/:decisionId`, read-only, in the IA-1 decision shape (§5). The choice acts are 6f2's
   (MOCK DEVIATION D5, MD-6F-1).

What stays: the placed-Finding rows and their targets, IA-P's list component and words, 5c's tile 4 ("Plan value, 12
months" stays "Not available yet", D-P6.9), every 6a/6c record and rule.

## 2. Gates (hard stops)

- **G-IAP:** IA-P1 and IA-P2 merged on `main` (the list component, `estateReadCache`, the Overview L2 rows, E0 in
  `estate/portfolio.py`). IA-P3 may build beside 6f1: whichever lands second runs the W6 sweep of §4.4.
- **G-6c:** 6c merged (it is: `591458c38`).
- **G-6h:** 6h merged before U2 builds (D-P6.52); U1 and U3 may build on 6h's spec'd shapes before it merges.
- Builders pre-flight against `main` and the mock and batch questions with the reviewer's (§12).

## 2a. Rev 1 amendments to Units 1 and 3 (D-P6.51 to D-P6.58; binding over the rev 0 text below)

- **Lever words come from 6h.** `title`, `question` and `option_label` are read from `decision_lever.*`
  (6h spec §5.4); the three rows of §3.4 move there unchanged for the generator lever. `LEVER_WORDS` keeps only the
  generator's axis names (`stop_axis`, `reserve_axis`); for a `STATED_OPTIONS` lever the option label is
  `decision_lever.option_label` of the option key, and doing nothing is `decision_lever.no_action` of the lever's
  `no_action_words`. Test 1's start-up assertion becomes: every `LEVERS` key has a `decision_lever.title` variant.
- **"Setting" words for named options.** Each row of §3.4 that says "setting" gains an `OPTION` twin with "option"
  in its place (`at_stake` `LOSS_OPTION`, `TIE_OPTION`, `MIXED_OPTION`; `outcome_note` `INCOMPLETE_OPTION`,
  `LOSS_OPTION`, `TIE_OPTION`, `MIXED_OPTION`; `reason` `RANKING_INCOMPLETE_OPTION`; `why_rule` `OPTION`: "Each
  option is valued against doing nothing, over the same figures that make up the month's contribution. The one worth
  the most is recommended; among the options within a tenth of it, the one first in the list."). The view picks the
  twin when the lever's generator is `STATED_OPTIONS`. Noun `count` uses `option`.
- **New variants:**
  - `missing`: `OPTION_STUDY` "Not available yet: needs {study}" (`decision_lever.study`, site, decision month) ·
    `OPTION_RECORD` "Not available yet: needs {record}" (`decision_lever.record` of `<LEVER>__<LEAF>`) ·
    `OPTION_RECORD_CURRENCY` "Not available yet: a stated record is in another currency than the one-off cost".
  - `at_stake` `BOUNDS` "Valued; no option recommended until the limits are checked" · `outcome_note` `BOUNDS` "No
    option is recommended until the limits for this decision are checked; each option's value and what it protects
    are shown." · `eyebrow` uses `NONE` · `disposition` `CONDITIONAL` "Valued; limits not checked yet" · `reason`
    `BOUNDS_NOT_CHECKED` "Its limits are checked once bounds are set."
  - `limits_answer` `NO_CHECKS` "These options have no service checks; their limits are checked once bounds are set"
    (when no option has an admission); `checks` and `check_cell` read `NOT_CHECKED` for those options.
  - `horizon_basis` `STATED` "Over {horizon}: {horizon_count} times the month's change".
  - `verify_items` `NOT_SET` "Not available yet: how this kind of change will be checked is set with its verification."
    for every lever but `generator_stop_reserve` (D-P6.50 stands for the generator).
  - `source` `RECORDED_STATED` "From {site}'s own records and the documents stated for each option" when any shown
    option reads an option record (6h4).
- **States (§5.3)** gain `BOUNDS_NOT_CHECKED`: the rec card uses `eyebrow` `NONE` and `outcome_note` `BOUNDS`; cards in
  display order with `CONDITIONAL` after the baseline.
- **Fixtures (§6.1)** gain **F6-N** (6h N1, Mwea, recommended), **F6-T** (6h T1, Thika, bounds) and **F6-S** (6h S1,
  Embakasi, missing study); test 1 asserts their pages as literals; `decision_page_*.json` adds the three.

## 3. Unit 1: the server read (1.5 units; `task/6f1-decisions`)

### 3.1 6a's store and read gain three things (records.py, memory store, adapter)

- `DecisionStore.bundle(tenant_id: UUID, decision_id: UUID) -> DecisionBundle | None`: one decision's bundle, the
  shape `for_tenant` builds (latest one-offs, latest run, choice, names). Adapter: the same statements as `for_tenant`
  filtered on `decision.id`; memory store likewise.
- `DecisionStore.name_of(tenant_id: UUID, person_id: UUID) -> str | None` (closes 6a review F5, D-P6.33).
- `DecisionService.view(tenant_id, decision_id: UUID) -> DecisionView | None` (None when absent or another
  tenant's). `RunSummary` gains `frame_kind: str` (`identity["frame"]["kind"]`, `DECLARED_SEASON` when absent),
  `months_averaged: tuple[str, ...]`, `study_days: int | None` (`identity["days"]`), `study_input_class: str | None`;
  `DecisionView` gains `site_id: str`, `structure_key: str`, `current_settings: Mapping[str, Decimal]`. Additive; the
  CLI output of 6a/6c is unchanged.
- The adapter stays the only reader of the seven tables; no write is added. Test 7 (6a's Postgres file) gains one
  case each for `bundle` and `name_of`.

### 3.2 `decision_page/` (new package; the page and list views; pure but for the injected services)

Not under `decisions/` (D-P6.28's import allowlist stays as it is); it may import `runs.admission.DAWN_LIMIT_PCT` and
`ADMISSION_PARTS`, `deep_dive.tables.RECORD_KEYS` and `deep_dive.words.record_chain` (one home for the records a gap
needs), `structure.registry.REGISTRIES`, `structure.levers.LEVERS`, `decisions.decisions_composition` names.

- `decision_page/tables.py` (the only place a lever's axis names or a reason code's words are mapped):
  - `LEVER_WORDS = {"generator_stop_reserve": LeverWords(title="GENERATOR_STOP_RESERVE", stop_axis="stop_soc_pct",
    reserve_axis="reserve_soc_pct")}`; a start-up assertion: every `LEVERS` key has an entry (test 1).
  - `EXTRA_RECORD_KEYS = {"wear_rate": ("BATTERY_WEAR",)}` (vocabulary `record` gains `BATTERY_WEAR`:
    "a battery wear cost stated for the Site").
  - `DOMAIN_OF = {"MINI_GRID": "MINIGRID", "COLD_CHAIN": "COLDCHAIN", "EV_DEPOT_CAPTIVE": "EV_CHARGING"}`.
  - `ORIGIN_OF = {"SIMULATED": "demo-simulated", "EMULATED": "source-emulated", "RECORDED": "field-integrated"}`
    (6c `models.ORIGIN_OF_INPUT`, re-exported, not retyped).
  - `CARD_CAP = 7`.
- `decision_page/view.py`: `list_rows(views, executive_name) -> list[dict]` and `page(view, *, executive_name,
  agreed: AgreedActionView | None, latest_run_id) -> dict`. They round once (D-P6.6: money to cents, quantities to 6
  places before formatting) and render every string through `i18n.served`/`render` (§3.4). They never add, subtract
  or compare figures except: the sign of a stored value (for the no-action variants), `value == best value` (the why
  answer), counts of rows by disposition, and the dawn limit as `DAWN_LIMIT_PCT` (no arithmetic on stored figures).
- `decision_page/read.py` `DecisionPageRead(decisions: DecisionService, agreed: AgreedActionService, accounts:
  AccountService)`: `rows(tenant, from_day, to_day)` (period filter = the months of `from` and `to`, inclusive) and
  `one(tenant, decision_id)`. The executive's name: `accounts.executive_of(slug)` then `DecisionStore.name_of`
  (D-P6.47).
- `decision_page/composition.py` `build_decision_page(database_url) -> (DecisionPageRead, dispose)` from
  `build_decisions`, `build_agreed_actions`, `build_account_service`, disposing all on failure (5c's pattern).
- `decision_page_api.py` (5c's `deep_dive_api.py` pattern; mounted in `main.py` after the deep-dive router):

| Route | 200 body | Refusals (`{"code","text"}`, `Cache-Control: no-store`) |
|---|---|---|
| `GET /api/decisions?from=YYYY-MM-DD&to=YYYY-MM-DD` | `{"rows": [Row], "total_count": n}`, newest `prepared_at` first | 503 `DECISIONS_UNAVAILABLE` (no database, no served tenant, store fault); 401 `PERSON_REQUIRED` (real-data switch on, no person of the tenant); 422 `BAD_RANGE` (a missing or malformed day, or `from > to`) |
| `GET /api/decisions/{decision_id}` | the Page (§3.3) | 503, 401 as above; 404 `DECISION_NOT_FOUND` (malformed UUID, absent, another tenant's) |

  The refusal texts are `decision_page.refused` variants (§3.4). Tenant: `request.app.state.site_registry.tenant()`
  only (never a query parameter), as 5c.

### 3.3 The served shapes

**Row** (list): `decision_id`, `site_id`, `site_code`, `site_name`, `domain` (`DOMAIN_OF`), `finding_id` (or null),
`period`, `state` (6a code), `heading` `{code, word}` (`home_category`, vocabulary `heading` label), `title`
(`decision_page.title`), `at_stake` `{text, evidence}` (§3.4 `at_stake`), `decides` (text: the chooser's name when a
choice exists, else the executive's name, else `decision_page.decides_role`), `target` `"/decisions/{decision_id}"`.

**Page:** every value is served text unless named a code.

```
{ decision_id, site_id, site_code, site_name, domain, finding_id, period, state (code), outcome (run outcome code|null),
  source_class (code|null), title, question, heading {code, word},
  meta {month, decides, due}, pill, steps {items: [text], current: int},
  rec {eyebrow, heading, figure {text, evidence}|null, chip|null, chip_title|null, cost|null, notes: [text],
       choice|null, act},
  cards {heading, note, items: [Card]},                      // display order (D-P6.48)
  sections: [Section × 6],                                   // keys why, change, limits, cost, verify, all, this order
  evidence {lines: [text]}, how: text, actions {items: [text]}|null,
  sticky {title, figure|null, pill} }
Card { option_key, label, badge, badge_kind, result, result_chip|null, cost, checks, dawn|null, why|null,
       is_rec, is_base, is_chosen }       // badge_kind: recommended|acceptable|deferred|rejected|baseline|notvalued|chosen
Section { key, label, answer, body }
  why    body {paragraphs: [text], changes_heading, changes: [text]}
  change body {caption, rows: [{factor, heading, change}], month_link}       // month_link: text; the client adds the href
  limits body {columns: [text × 5], rows: [{option, cells: [text × 4], dawn}]}
  cost   body {rows: [{option, cost}]}
  verify body {items: [text]}
  all    body {columns: [text × 6], rows: [{option, result, cost, checks, dawn, standing}]}   // position order, never cut
```

**Rules that pick the texts:**
- **Option label** (`decision_page.option_label`): no action → `NO_ACTION`; else compare the option's settings with
  `current_settings` on `LEVER_WORDS` axes: only stop differs → `STOP`; only reserve lower/higher → `RESERVE_DOWN` /
  `RESERVE_UP`; both → `STOP_RESERVE_DOWN` / `STOP_RESERVE_UP`. Settings are `Percent(value / 100, DECLARED)`, 0
  places.
- **Card display order (D-P6.48):** no action; the recommended; `ACCEPTABLE` by rank; `DEFERRED`; `REJECTED`; ties in
  position order. No run: position order. The client shows the first `CARD_CAP`, then "Show all {n} options".
- **Result** (card, table, sticky): a value → `result` (signed money "over {horizon}"); missing → the first `missing`
  entry's sentence (§3.4 `missing`); no action → `decision_page.disposition` `COMPARISON` ("The baseline"); no run →
  "Not valued yet". `result_chip` = `source_chip` when the option's `source_class` is not `RECORDED` and the result is a
  value.
- **Rec card by outcome:** `RECOMMENDED` → eyebrow `REC`, heading = the option label, figure = `rec_figure`, cost =
  `one_off` of that option, notes = [`grid_edge`] when its reason is `AT_GRID_EDGE`. Any other outcome, or no run →
  eyebrow `NONE`/`NOT_VALUED`, heading `rec_heading`, figure null, notes = [`outcome_note`, then (for
  `RANKING_INCOMPLETE`) the first missing sentence of the first `VALUE_NOT_AVAILABLE` option in position order, then
  `can_choose`]. `NO_ACTION_BEST` picks `LOSS` (every admitted value < 0), `TIE` (every admitted value = 0) or `MIXED`.
- **Choice line** (`rec.choice`): `CHOSEN`/`UNDER_WAY` → `choice` `CHOSEN`; `KEPT_AS_IS` → `KEPT`; plus `stale` when
  `choice.run_id` ≠ the latest run's id. `rec.act` = `act_unavailable` in 6f1 (MD-6F-1).
- **Pill** (`decision_page.pill`): `NOT_VALUED` → `NOT_VALUED`; `WAITING` with `RECOMMENDED` → `WAITING`; `WAITING`
  otherwise → `NO_REC`; `CHOSEN`, `UNDER_WAY`, `KEPT_AS_IS` as named.
- **Steps** (`decision_page.step`, no "Verified" step, IA-1 §4.1): items `[first, CHOSEN, ACTION]` (first = `REC`,
  `NO_REC` or `NOT_VALUED` as the pill); `KEPT_AS_IS` → `[first, KEPT]`. `current`: 0 for `NOT_VALUED`/`WAITING`; 2
  for `CHOSEN` and `UNDER_WAY` (the client marks 0..current−1 done and `current` with `aria-current="step"`; for
  `UNDER_WAY` the third item reads `ACTION_DONE`); 1 for `KEPT_AS_IS`.
- **Checks** (`decision_page.checks`): `admission` null and no action → `BASE`; null otherwise → `NOT_CHECKED`;
  admitted → `PASS`; else `FAIL` with the first failing part's word. Limits table cells: one per `ADMISSION_PARTS`
  part, `check_cell` `PASS`/`FAIL`/`NOT_CHECKED`.
- **Dawn** (`decision_page.dawn`): from `dawn` (fractions `"n/d"`): `worst` = `Percent(worst_soc_pct / 100)` 1 place,
  `days` = `KOfN(days_below, days, "day")`, `limit` = `Percent(DAWN_LIMIT_PCT / 100)` 0 places; null when `dawn` is
  null.
- **Effects** (`change` rows): the effects of the recommended option, else of the first non-`REJECTED` option in
  position order, else none (`caption` says which option). Unit `L` → `Quantity(v, "L")` 1 place signed; `KWH` →
  `Quantity(v, "kWh")` 1 place signed; `MONEY` → `Money(v, currency)` signed; any other unit raises (a code defect;
  test 1 proves the generator lever's units are these three). Missing → the effect's first missing sentence.
  `factor` = vocabulary `factor` label; `heading` = the factor row's `home.category` label.
- **Evidence lines** in order: `valued_by`; `source` (variant by `source_class` × `frame_kind`); `horizon_basis`
  (`MONTHS` when `months_averaged` is non-empty, else `NO_MONTHS`); `prepared_by`; `assumed` when the union of every
  option's `assumed` is non-empty (vocabulary factor labels, registry order). The client adds the Finding line (§5.5).
- **`actions`**: `UNDER_WAY` → one item `action_line` from the agreed Action (3C2's view by id); else null.
- **Figures carry evidence:** `Money`/`Quantity` facts take `Evidence(evaluation.evidence_class, ORIGIN_OF[source_class])`,
  so `served` returns the evidence words beside the text (5c's form).

### 3.4 Words: `i18n/statements/en/decision_page.py` (SC-1; keys `decision_page.<name>`; D-P6.45)

No digit, `%` or currency symbol in a template (`check_literal`, D-SC1.21): every number is a slot. Slot types:
`name` (Site, person, option label, basis), `money`, `quantity`, `percent`, `count` (nouns `month`, `day`, `option`,
`setting`; vocabulary `noun` gains `option` and `setting`), `k_of_n`, `month`, `day`, `word` (factor, heading,
record chain), `items`, `state` (variant selector, exhaustive). Money: SC-1 `money` with `signed` for a change
against doing nothing, unsigned for a one-off.

| Key | Variants (selector) → text |
|---|---|
| `title` | `GENERATOR_STOP_RESERVE` → "{site} generator stop setting" |
| `question` | `GENERATOR_STOP_RESERVE` → "What should we do about the {site} generator stop setting?" |
| `option_label` | `NO_ACTION` "Keep the current generator settings" · `STOP` "Stop the generator at {stop_to} battery instead of {stop_from}" · `RESERVE_DOWN` "Lower the battery reserve from {reserve_from} to {reserve_to}" · `RESERVE_UP` "Raise the battery reserve from {reserve_from} to {reserve_to}" · `STOP_RESERVE_DOWN` "Stop the generator at {stop_to} battery instead of {stop_from}, and lower the reserve from {reserve_from} to {reserve_to}" · `STOP_RESERVE_UP` (same with "raise") |
| `result` | "{value} over {horizon}" |
| `rec_figure` | "{value} over {horizon}, against doing nothing" |
| `one_off` | `STATED` "costs {amount}" · `ZERO` "no one-off cost" · `MISSING` "one-off cost not stated yet" |
| `one_off_detail` | `STATED` "{amount} one-off, stated by {person} on {day}: {basis}" · `MISSING` "Not stated yet" · `BASE` "Nothing to put in place" |
| `missing` | `SIMULATION` "Not available yet: needs a simulation of {site}'s own {month}" · `RECORDS` "Not available yet: needs {records}" · `FACTOR` "Not available yet: needs a record of {factor}" · `ONE_OFF` "Not available yet: needs the one-off cost of this change, stated by the Site manager or the finance lead" · `ONE_OFF_CURRENCY` "Not available yet: the one-off cost is in another currency than the month's figures" · `CURRENCY_MISMATCH` "Not available yet: the month's figures are in more than one currency" · `ZERO_DENOMINATOR` "Not available yet: {factor} cannot be worked out, because a figure it divides by is zero" |
| `at_stake` | `VALUE` "{value} over {horizon}" · `LOSS` "Doing nothing is worth more than any setting tried" · `TIE` "Every setting tried is worth the same as doing nothing" · `MIXED` "No setting tried is worth more than doing nothing" · `INCOMPLETE` (the `missing` sentence, as a nested statement) · `NONE_ADMITTED` "No setting tried passes the service checks" · `NOT_VALUED` "Not valued yet" |
| `eyebrow` | `REC` "We recommend" · `NONE` "No option recommended" · `NOT_VALUED` "Not valued yet" |
| `rec_heading` | `VALUED` "Each option valued against doing nothing" · `NOT_VALUED` "The options, not valued yet" |
| `outcome_note` | `INCOMPLETE` "No option is recommended until every setting that passes the service checks has a value: {unvalued} have no value yet." · `LOSS` "Doing nothing is worth more than any setting tried." · `TIE` "Every setting tried is worth the same as doing nothing." · `MIXED` "No setting tried is worth more than doing nothing." · `NONE_ADMITTED` "No setting tried passes the service checks." · `NOT_VALUED` "The options have not been valued yet. Each will be valued against doing nothing." |
| `can_choose` | `ANY` "{who} can still choose one, or none." · `NONE_ONLY` "{who} can still choose to keep things as they are." |
| `grid_edge` | "This is the furthest setting tried in that direction." |
| `disposition` | `RECOMMENDED` "Recommended" · `ACCEPTABLE` "Acceptable" · `DEFERRED` "Deferred" · `REJECTED` "Rejected" · `COMPARISON` "The baseline" · `NOT_VALUED` "Not valued yet" · `CHOSEN` "Chosen" |
| `reason` | `NOT_ADMITTED_ENERGY_NOT_SERVED` "Fails a service check: more demand would go unserved." · `NOT_ADMITTED_RESERVE_BREACHES` "Fails a service check: the battery would fall below its reserve more often." · `NOT_ADMITTED_STARTS` "Fails a service check: more generator starts than the maker allows." · `NOT_ADMITTED_FULL_CHARGE` "Fails a service check: the battery would not reach a full charge every week." · `NOT_WORTH_MORE_THAN_NO_ACTION` "Worth less than doing nothing." · `WORTH_THE_SAME_AS_NO_ACTION` "Worth the same as doing nothing." · `RANKING_INCOMPLETE` "Not ranked until every setting has a value." (`VALUE_NOT_AVAILABLE` shows its `missing` sentence; `AT_GRID_EDGE` shows `grid_edge`) |
| `checks` | `PASS` "Passes every service check" · `FAIL` "Fails: {part}" · `NOT_CHECKED` "Not checked" · `BASE` "The comparison" |
| `part` | `energy_not_served` "energy served" · `reserve_breaches` "reserve kept" · `starts` "starts within the maker's limit" · `full_charge` "regular full charge" |
| `check_cell` | `PASS` "Passes" · `FAIL` "Fails" · `NOT_CHECKED` "Not checked" |
| `dawn` | "Lowest charge at dawn {worst} ({days} below {limit}; information, not a limit)" |
| `source_chip` | `SIMULATED` "Simulated" · `EMULATED` "Emulated" |
| `cards_heading` | "The options, against doing nothing" |
| `cards_note` | `PLAIN` "Each result over {horizon}" · `SIMULATED` "Each result over {horizon}; simulated figures are marked Simulated" |
| `pill`, `step` | `NOT_VALUED` "Not valued yet" · `WAITING` "Waiting for a choice" · `NO_REC` "No option recommended" · `CHOSEN` "Chosen" · `UNDER_WAY` "Chosen: Action under way" · `KEPT_AS_IS` "Kept as it is"; `step` adds `REC` "Recommended" · `ACTION` "Action agreed" · `ACTION_DONE` "Action under way" · `KEPT` "Kept as it is" |
| `meta` | `DECIDES` "Decides: {who}" · `DUE` "Due: not available yet" · `MONTH` "{month}" |
| `decides_role` | "The operator's executive" |
| `choice` | `CHOSEN` "Chosen by {person} on {day}: {option}." · `KEPT` "Kept as it is by {person} on {day}." · `STALE` "The options have been valued again since this choice." |
| `act_unavailable` | "Choosing on this page: not available yet." |
| `sec_label` | `WHY` "Why we recommend it" · `WHY_NONE` "Why no option is recommended" · `CHANGE` "What it changes" · `LIMITS` "Limits and cover" · `COST` "Cost and who pays" · `VERIFY` "How we will check it worked" · `ALL` "All options in detail" |
| `why_answer` | `BEST` "It is worth the most against doing nothing." · `NEAR` "It is within a tenth of the best value and the closest to today's settings." · `NONE` "{rejected} of {options} are rejected or deferred" (`k_of_n`, noun `option`) · `NOT_VALUED` "The options have not been valued yet" |
| `why_rule` | "Each setting that passes the service checks is valued against doing nothing, over the same figures that make up the month's contribution. The one worth the most is recommended; among the settings within a tenth of it, the one closest to today's settings. The dawn readings are shown beside each setting and never decide." |
| `changes_heading` | "What would change the recommendation" |
| `sensitivity` | "Not available yet: how much each input would have to move to change the choice is not worked out yet." |
| `change_answer` | "Each option changes {factors}" (`items` of factor `in_sentence`, `LEVER.changes` order) |
| `change_caption` | `REC` "{option}: change a month against doing nothing" · `FIRST` "{option} (the first setting that passes): change a month against doing nothing" · `NONE` "No setting passes, so no change is shown" |
| `month_link` | "See {month} on the Overview" |
| `limits_answer` | `REC_ALL` "The recommendation keeps every service check" · `REC_SOME` "The recommendation keeps every service check; {failing} fail one" · `ALL` "Every setting tried keeps every service check" · `SOME` "{failing} fail a service check" · `NOT_VALUED` "Not checked yet" (`failing`: `count`, noun `setting`) |
| `limits_columns` | `OPTION` "Option" · and the four `part` words capitalised as separate variants (`ENERGY` "Energy served", `RESERVE` "Reserve kept", `STARTS` "Starts within the maker's limit", `CHARGE` "Regular full charge") · `DAWN` "Dawn (information)" |
| `cost_answer` | `STATED` "{amount} one-off, stated by {person}" · `ZERO` "No one-off cost" · `MISSING` "One-off cost not stated yet" · `CARDS` "Each option's cost is on its card" |
| `verify_answer` | "Working and money are checked separately, once the change is made" |
| `verify_items` | `WORKING` "Working: generator running after the battery is full falls as predicted, on comparable days before and after the change, and every service check still holds." · `MONEY` "Money: the fuel invoices after the change are set against the days before it, and reported apart from the working check." · `STATE` "Not started: the checks begin once the change is made." |
| `all_answer` | `PLAIN` "{options} against doing nothing" · `WITH_REJECTED` "{options} against doing nothing; {rejected} rejected or deferred, each with its reason" |
| `all_columns` | `OPTION` "Option" · `RESULT` "Result" · `COST` "One-off cost" · `CHECKS` "Service checks" · `DAWN` "Dawn (information)" · `STANDING` "Standing" |
| `valued_by` | "Valued on {day} by {person}" |
| `source` | `SIMULATED_SEASON` "Simulated: from a simulation of a declared season of {days}, not your recorded data" · `SIMULATED_SITE` "Simulated: from a simulation on {site}'s own recorded readings" · `EMULATED` "Emulated: from an emulated source, not measured on site" · `RECORDED` "From {site}'s own records" |
| `horizon_basis` | `MONTHS` "Over {horizon}: {horizon_count} times the average of {months} ({month_list})" · `NO_MONTHS` "Over {horizon}: not worked out, because the simulation is not of {site}'s own months" |
| `prepared_by` | "Prepared on {day} by {person}" |
| `assumed` | "Assumed, not recorded: {factors}" |
| `action_line` | "{title}, owned by {person}, due {day}: {state}" |
| `how` | "AssetOps values each option against doing nothing, with the same figures that make up the month's contribution, and recommends one. {who} chooses an option, or none, and the choice is kept under their name with the time. The change is then made through an Action and checked against the days before it." |
| `refused` | `DECISIONS_UNAVAILABLE` "Decisions cannot be read right now." · `PERSON_REQUIRED` (reuse `person.person_required`) · `BAD_RANGE` "Choose a date range with a start and an end." · `DECISION_NOT_FOUND` "This decision is not available." |

- The `missing` variant for an entry `[kind, family, factor]` (D-P6.46): `SITE_MONTH_SIMULATION` → `SIMULATION` (site,
  decision month); `ONE_OFF`, `ONE_OFF_CURRENCY`, `CURRENCY_MISMATCH`, `ZERO_DENOMINATOR` → their own (factor from
  vocabulary); any other entry with a factor → `RECORDS` when `RECORD_KEYS ∪ EXTRA_RECORD_KEYS` has the factor
  (`record_chain` of its keys), else `FACTOR`. An entry outside this list raises.
- Wording checks before coding: every template passes `check_literal` and the banned-word test (§6.4); a clash comes
  back to the Architect.

## 4. Unit 2: the list on the records (0.5 unit; gate G-6h)

### 4.1 E0 counts the records waiting (`estate/portfolio.py`; D-P6.44 as amended by D-P6.52)

- A port `DecisionWaiting` beside E0: `waiting(tenant_id, period_from, period_to) -> Mapping[str, int]` (records in
  `NOT_VALUED` or `WAITING`, by `site_code`), from `DecisionService.for_tenant` over the same months; composed in
  `main.py` from `build_decisions`; `None` without a database.
- `summary.waiting_count` = Σ `waiting`; `summary.waiting_by_site` = `waiting`. Port `None` or a store fault: both
  fields `null` (the cells read "Not available yet"), never a partial count or the placed-Finding count.
- Tests (`backend/tests/test_6f_e0_records.py`, pure): two waiting records on two Sites and one `CHOSEN` give 2 and
  `{A: 1, B: 1}`; a fault gives `null`; port `None` gives `null`.

### 4.2 The client (`estate/decisionsClient.ts`, `estate/estateReadCache.tsx`)

- `createDecisionsClient(fetch)`: `list({from, to})` and `one(decisionId)`, each `EstateResult`-shaped (`loaded` |
  `refused {code, text}`), with the §3.3 types (`DecisionListRow`, `DecisionPage`).
- `EstateReadKind` gains `"decisions"`; the cache wraps the list body as `AllPages` with `truncated: false`.

### 4.3 The list on the records (`estate/homeLists.tsx`; D-P6.52)

`DecisionItem` = `{ key, title, small, siteName, siteCode, domain, state, stake, decides, target, findingId }`,
`rowKey` `d:{decision_id}`, from the decisions read only: `title` = `row.title`; `small` = `row.heading.word`; `state`
= `waiting` (`NOT_VALUED`, `WAITING`), `chosen`, `underway`, `kept`; `stake` = `row.at_stake.text`; `decides` =
`row.decides`; `target` = `/decisions/{id}`. Order: the read's order (newest `prepared_at` first). `DECISION_STATE_WORD`
gains `chosen` "Chosen" and `kept` "Kept as it is"; the State facet lists `waiting`, `underway`, `chosen`, `kept`.
Columns unchanged; "Due" stays "Not available yet" (MD-6F-3). A refused read → IA-P's refusal. An empty range →
IA-P's empty state, "No decisions for this range."
`useDecisionItems(range)` returns `{items, state: "loading" | "unavailable" | "ready", waitingTotal}`.

### 4.4 Every consumer reads the hook (W6 sweep)

Class: "a surface that builds decision rows from the placed Findings". Sweep with `grep -rn "decisionItems("
frontend/src` and fix every hit to `useDecisionItems`: the Decisions list page, the Overview L2 rows (IA-P2,
`cap: 6`), the inbox and search when present. The Findings list's "Its decision" joins `findingId` (several records →
the newest `period`); no record → "Not available yet". The packet lists the grep before and after.

### 4.5 Tests

`estate/__tests__/decisionsList.test.tsx` with `__fixtures__/decisions_list.json`: keys in order (literal list);
states map to the four keys; the State facet "Chosen" shows exactly the chosen record; the tile equals E0
`waiting_count` (literal); "Its decision" reads the record's word, else "Not available yet"; "Who decides" shows the
served name. Plants: `placed` (Finding rows added back to the list); `count` (tile counts placed Findings).

## 5. Unit 3: the decision page (1.5 units)

### 5.1 Route and frame

- `/decisions/:decisionId` in `App.tsx`; `iaRoutes.ts` `IA_HOMES` gains `{pattern: /^\/decisions\/[0-9a-f-]{36}$/,
  home: "Decisions", tabGroup: null}` (an object page, IA-P §2.3: no tab row). Breadcrumb `[Decisions (link
  /decisions with the range)] › [site_name (link /sites/{site_code})] › [title]`. Document title = H1.
- `estate/DecisionPage.tsx`, `estate/decisionPage.css` (tokens only), `estate/decisionPageWords.ts` (chrome words
  only, §5.6). The page reads `decisionsClient.one(id)` (not range-filtered: an object page shows its own month; its
  links keep the shared range).

### 5.2 The shape (`data-shape="decision"`, IA-1 §4.1; levels as the mock)

| Mock slot | Live element | Content |
|---|---|---|
| `sticky` | `<div class="dp-sticky" role="region" aria-label="This decision">` shown once the rec card scrolls under the top bar (mock `uxStickyTick`; at ≤ 600 px at the bottom, page padding reserved) | `sticky.title`, `sticky.figure`, `sticky.pill`; no act (MD-6F-1) |
| L1 `head` | `<h1>` (`question` when `state` is `NOT_VALUED`/`WAITING`, else `title`); meta line `<p class="dp-meta">` with `site_name`, `meta.month`, `meta.decides`, `meta.due`, the pill (`StatusPill`); `<ol class="dp-steps" aria-label="Where this decision is">`; the "How this works" opener (link button) | §3.3 rules |
| L1 `rec` | `<section class="panel dp-rec" aria-labelledby>`: eyebrow, `<h2>` heading, figure (`<p class="dp-rec-n"><b>`) + chip (`chip_title` as its accessible description) + " · " + cost; notes as `<p class="dp-note">`; `choice`; the act line (`rec.act`, plain text, no button); the "Evidence and records" opener | one hero number only (mock "The hero number") |
| L2 `cards` | `<section id="dp-cards">` heading + note, then a grid of `<article class="dp-card">` (h3 label, badge by `badge_kind`, `<dl>` Result · One-off cost · Service checks, dawn as `<p class="dp-dawn">` when set, `why` as `<p>`); first `CARD_CAP` (7) then `<button>` "Show all {n} options" / "Show fewer" (focus moves to the first newly shown card) | `is_rec` and `is_base` and `is_chosen` styles as the mock `is-rec`, `is-base`, `is-chosen` |
| L3 `secs` | six `<details class="panel dp-sec">` (the shared `Disclosure`), closed by default; `<summary>` = label + answer (answer visible when closed) | bodies: why (paragraphs, sub-heading, list); change (caption, table Factor · Heading · Change a month, the month link to `/portfolio?from={first day}&to={last day}` of `period`); limits (table, 5 columns, never cut); cost (list); verify (list); all (table, every option, never cut) |
| drawers | `[data-ia-drawers]`: "Evidence and records", "How this works", "The Actions" (only when `actions` is set; opened from the act line's "See the Actions" link) | one dialog pattern: `aria-modal`, focus to Close, Escape and scrim close, focus returns (IA-P P6's pattern) |

### 5.3 States

| State | What shows |
|---|---|
| Loading | the breadcrumb's first crumb, an H1 skeleton and the status "Loading the decision…" (`role="status"`) |
| 404 | `<h1>` "Decision not available", the served text, link "Back to Decisions" |
| 503 / 401 | the served text and "Try again" (re-reads) — IA-P's refusal look |
| `NOT_VALUED` | rec card `NOT_VALUED`; cards in position order, each "Not valued yet"; sections answer `NOT_VALUED` where given |
| `WAITING` × `RECOMMENDED` / `NO_ACTION_BEST` / `RANKING_INCOMPLETE` / `NOTHING_ADMITTED` | §3.3 rules (fixtures F6-C, F6-D1..3, F6-B, F6-E) |
| `CHOSEN`, `UNDER_WAY`, `KEPT_AS_IS` | the chosen card `is_chosen` with badge "Chosen"; the choice line; `UNDER_WAY` adds "See the Actions" and the drawer |

### 5.4 Behaviour and quality bar

- Text-only cells; the server sends every string; the client formats nothing (no number, date or currency code is
  built in TS).
- 390 px: cards one column, tables stack as label/value pairs (`data-label`, the list component's rule), no
  horizontal page scroll; 768: cards two columns; 1440: cards up to four.
- WCAG 2.2 AA: one H1, headings in order, the steps list with `aria-current`, drawers trap focus, the sticky bar never
  hides a focused control (scroll padding = its measured height, the mock's rule), contrast in light and dark.
- `Docs/design-system/uiux-guide.md` G2 to G4 apply (G2: no colour literal outside tokens).

### 5.5 The Finding line (client join)

In "Evidence and records", after the served lines: with `finding_id` set, the placed row of the same id from the
cached portfolio read for the shared range → "The Finding behind it: {title}" linking through `findingLinkLive`/
`linkFor` (IA-P1's rule); not in the range → "The Finding behind it is outside this date range."; `finding_id` null
→ "Opened from the setting itself, with no Finding behind it."

### 5.6 Chrome words (`decisionPageWords.ts`; every other string is served)

"Decisions" (crumb), "Show all {n} options", "Show fewer", "Evidence and records", "How this works", "The Actions",
"See the Actions", "Close", "Loading the decision…", "Decision not available", "Back to Decisions", "Try again",
"Valued decisions cannot be read right now.", the three Finding-line sentences of §5.5, "Change a month",
"Heading", "Factor" (the change table's columns; "Factor" is a column word, exempt from §6.4 by name).

## 6. Fixtures and checks (W2: written first; literals derived by hand)

### 6.1 Backend fixtures (memory store; `backend/tests/lakeside_people.py` world)

6a's world: tenant `lakeside-power`, KOBO-001 named "Kobo", Amina OPERATOR_EXECUTIVE, Wanjiru ANALYST, Peter
SITE_MANAGER KOBO-001; clock `2026-11-24T09:00:00Z`; ids `UUID(int=n)`. Every decision is F-P1 (14 options, current
stop 90 / reserve 30, period 2026-10) unless named. Runs are stored by the test with `add_run` (literal rows).

- **F6-A** no run → `NOT_VALUED`.
- **F6-B** (Kobo today) run `DECLARED_SEASON`, `SIMULATED`, `days` 61, `months_averaged` []: positions 1-11
  `DEFERRED VALUE_NOT_AVAILABLE`, `missing` `[["SITE_MONTH_SIMULATION","SIMULATION","candidate_l"],
  ["SITE_MONTH_SIMULATION","SIMULATION","battery_throughput_kwh"],["ONE_OFF","DECISION",null]]` (position 8
  `stop-70-reserve-30` has F-O1's one-off, so no `ONE_OFF`); positions 12-13 `REJECTED NOT_ADMITTED_STARTS`; outcome
  `RANKING_INCOMPLETE`; `dawn` on every setting `{"worst_soc_pct": "312/10", "margin_points": "-38/10",
  "days_below": 11, "new_days_below": 2, "days": 61}` except position 8 `"289/10"`, `"-61/10"`, 14, 5, 61.
  Expected: at stake and the rec note's missing sentence "Not available yet: needs a simulation of Kobo's own
  {month 2026-10}"; `outcome_note` with `unvalued` = 11 of 11 settings; position 12's checks "Fails: starts within
  the maker's limit".
- **F6-C** run `SITE_RECORD`, `SIMULATED`, `months_averaged` ["2026-10"], one-offs stated by Peter (0.00 USD, basis
  "Set on the controller during a routine visit") on every setting except position 8 (F-O1: 120.00 current):

  | Pos | Option | monthly | horizon | value | disposition | rank |
  |---|---|---|---|---|---|---|
  | 1 | stop-90-reserve-25 | 12.00 | 144.00 | 144.00 | ACCEPTABLE | 11 |
  | 2 | stop-85-reserve-30 | 60.00 | 720.00 | 720.00 | ACCEPTABLE | 10 |
  | 3 | stop-85-reserve-25 | 65.00 | 780.00 | 780.00 | ACCEPTABLE | 9 |
  | 4 | stop-80-reserve-30 | 110.00 | 1320.00 | 1320.00 | ACCEPTABLE | 8 |
  | 5 | stop-80-reserve-25 | 112.00 | 1344.00 | 1344.00 | ACCEPTABLE | 7 |
  | 6 | stop-75-reserve-30 | 160.00 | 1920.00 | 1920.00 | ACCEPTABLE | 5 |
  | 7 | stop-75-reserve-25 | 158.00 | 1896.00 | 1896.00 | ACCEPTABLE | 6 |
  | 8 | stop-70-reserve-30 | 208.513 | 2502.156 | 2382.156 | RECOMMENDED | 1 |
  | 9 | stop-70-reserve-25 | 205.00 | 2460.00 | 2460.00 | ACCEPTABLE | 2 |
  | 10 | stop-65-reserve-30 | 200.00 | 2400.00 | 2400.00 | ACCEPTABLE | 3 |
  | 11 | stop-65-reserve-25 | 190.00 | 2280.00 | 2280.00 | ACCEPTABLE | 4 |
  | 12 | stop-60-reserve-30 | 210.00 | 2520.00 | 2520.00 | REJECTED NOT_ADMITTED_STARTS | — |
  | 13 | stop-60-reserve-25 | 215.00 | 2580.00 | 2580.00 | REJECTED NOT_ADMITTED_STARTS | — |

  Position 8's effects, in order: `candidate_l` −250 L; `battery_throughput_kwh` +410 KWH; `diesel_l` −250 L;
  `fuel_cost` −237.50 USD; `battery_wear` +28.987 USD; `cost_to_serve` −208.513 USD; `contribution` +208.513 USD.
  Expected: `rec_figure` value 2382.16 (half-even of 2382.156), `why_answer` `NEAR` (2382.156 < 2460.00, the best);
  cards order: no action, pos 8, then ranks 2..11 (pos 9, 10, 11, 6, 7, 5, 4, 3, 2, 1), then 12, 13; the first 7
  shown; `limits_answer` `REC_SOME` failing 2 settings; `cost_answer` `STATED` 120.00 by Peter; `battery_wear`
  shown as +28.99.
- **F6-D1/D2/D3** `SITE_RECORD`; every admitted value −12.00 (D1, `LOSS`), 0.00 (D2, `TIE`), or −12.00 on positions
  1-5 and 0.00 on 6-11 (D3, `MIXED`); dispositions per 6c R3; outcome `NO_ACTION_BEST`.
- **F6-E** all 13 `REJECTED` (positions 1-4 `NOT_ADMITTED_ENERGY_NOT_SERVED`, 5-8 `_RESERVE_BREACHES`, 9-11
  `_STARTS`, 12-13 `_FULL_CHARGE`); `NOTHING_ADMITTED`; `can_choose` `NONE_ONLY`.
- **F6-F** F6-C then Amina chooses `stop-70-reserve-30` → `CHOSEN`. **F6-G** the same with 3C2's agreed Action R1
  (title "Lower the generator stop setting at Kobo to 70% battery charge", owner Peter, due 2026-12-15) →
  `UNDER_WAY`, `actions` one line. **F6-H** `--none` → `KEPT_AS_IS`, steps `[REC, KEPT]`. **F6-I** F6-F then a newer
  run → the `STALE` line.
- **F6-J** F-P3 (with the `GENERATOR_SUPPORT_CANDIDATE` Finding) → heading `OPTIMIZE_COST`, `finding_id` served.
- **F6-K** the executive's name: Amina (no choice) → `decides` "Amina"; with no executive → "The operator's executive".

### 6.2 Frontend fixtures (`frontend/src/estate/__tests__/fixtures/`)

`decisions_list.json` (three rows, built from F6-C, F6-A at period 2026-09 with no Finding, and F6-G covering the
placed Finding of IA-P1's list fixture with the lowest server position) and `decision_page_*.json` (the page JSON of
F6-A, B, C, D1, E, G, H), generated once by `backend/tests/test_6f_decision_page.py --write-fixtures` and committed;
the frontend tests assert on their served strings and never recompute them.

### 6.3 Tests (written first)

1. `backend/tests/test_6f_decision_page.py` (pure): per fixture, the full Page as a literal dict (key texts written by
   hand as strings, the SC-1 glyphs confirmed at pre-flight); every `LEVERS` key in `LEVER_WORDS`; the generator
   lever's effect units are L, KWH, MONEY; each `missing` variant once; an unknown missing kind raises; rounding
   (2382.156 → 2382.16; 28.987 → 28.99).
2. `backend/tests/test_6f_decisions_api.py` (TestClient, memory services): both routes; each refusal code and status;
   `no-store`; another tenant's id → 404; real-data switch on without a person → 401; `from > to` → 422; the period
   filter (a 2026-09 decision is outside 2026-10-01..2026-10-31).
3. `backend/tests/test_6f_e0_records.py` (§4.1). 4. 6a test 7 cases (§3.1). 5. `decisionsList.test.tsx` (§4.5).
6. `estate/__tests__/DecisionPage.test.tsx`: each fixture renders its served H1, pill, steps, rec card, cards (7 then
   all), six summaries with their answers, drawers' focus cycle; no `<button>` or link whose name starts "Choose";
   404/503 states; the Finding line's three cases; no text node that is not in the fixture or §5.6.
- **Plants** (each shown failing its named test in the packet): `zero` (a missing value rendered as $0.00) fails 1;
  `round2` (rounding before × horizon in the view) fails 1; `tie` (`TIE` text for `MIXED`) fails 1; `cap` (all cards
  shown) fails 6; `choose` (a Choose button) fails 6; `swap`, `nocover`, `tailfirst` fail 5; `e0` (records not
  counted) fails 3.

### 6.4 Copy checks

- Banned words in every served string of the fixtures and §5.6 (case-blind, whole word): replay, study, lever,
  disposition, evaluation, evaluator, leaf, node, scenario, binding, emulator, COMPARISON, run (as a word; the
  vocabulary label "Diesel run while solar and battery could carry the load" is exempt by exact string), and any
  `UPPER_SNAKE` token. Test 1 and test 6 run it.
- "Not available yet" appears only with what would fill it (each `missing` variant) or as IA-P's cell word.

## 7. Gates (the packet shows each)

- **D1** `/decisions/{F6-C id}` at 1440, 768 and 390, light and dark: no horizontal scroll; the sticky bar appears
  after the rec card scrolls; shots to `/opt/assetecon/evidence/6f1/<run>/`.
- **D2** `/decisions` with the records fixture: the tile = E0; every row opens `/decisions/:id`; on the DD world, a
  row for every Site with a decision in the range, all three Site types.
- **D3** keyboard: every disclosure, "Show all", each drawer open and close with focus returned.
- IA-P gates L1-L3 and `navigation-truthfulness` stay green; `uiux-guide` G2-G4; `check-all` fast mode.

## 8. Page × Site-type matrix (range rule)

| Surface | Mini-grid (Kobo, Kisiwa, Mto) | Cold chain (Mwea, Thika, Kirinyaga) | EV (Embakasi, Kasarani, Ruiru) |
|---|---|---|---|
| Decisions list (range) | a record row per prepared decision | a record row per prepared decision (6h levers) | a record row per prepared decision (6h levers) |
| Decision page | `/decisions/:id` for each record | `/decisions/:id` for each record | `/decisions/:id` for each record |
| Overview L2 rows, inbox, search | the records | the records | the records |
| Findings "Its decision" | record word, else "Not available yet" | as mini-grid | as mini-grid |
| Sites list "Waiting for a choice" (E0) | records waiting | records waiting | records waiting |

Each Site type with data in the range shows rows the same way, with the same columns; a valued decision appears
where its records exist (6h), and an unvalued option names the record it needs.

## 9. Mock deviations (rows in `.agent/mock-departure-register.md` in the unit named)

| ID | Element | Cat. | Reason · resolving unit | Unit |
|---|---|---|---|---|
| MD-6F-1 | "Choose this", "Choose another option", "Choose this instead", the sticky act, the choose dialog | D5 | the choice on screen is 6f2; "Choosing on this page: not available yet." · 6f2 | U3 |
| MD-6F-2 | option cards: first 7 in display order, then "Show all {n} options" | D2 | 14 options; the full table (L3) is never cut (standing brief: exposure that scales) · flag to owner (Q3) | U3 |
| MD-6F-3 | meta "Due" and the list's Due | D1 | a decision has no due date until plan items · 7a | U2, U3 |
| MD-6F-4 | "What it changes" without the month's figure of the purpose factor | D1 | not stored with the valuation; link to the month on the Overview · queued (6f2 may read it) | U3 |
| MD-6F-5 | "What would change the recommendation" | D1 | sensitivity not worked out · not scheduled | U3 |
| MD-6F-6 | "Limits and cover": service checks only, no cover or costed bounds | D1 | this lever has no rights; bounds as rows are 6b's · 6b | U3 |
| ~~MD-6F-7~~ | withdrawn (D-P6.52): 6h gives every Site type levers; unvalued options are 6h's MD-6H-4 | — | — | — |
| MD-6F-8 | stepper tail "Action agreed" (no "Awaiting approval → Actions released") | D1 | no plan record (D-IAP.1) · 7a | U3 |
| MD-6F-9 | the mock's Kobo options (battery storage, its figures) | D4 | the live grid's 13 settings and 6c's own figures (D-0K4.15) | U3 |

MD-IAP-2 narrows to "Due" (Who decides is lit for records); its register row is updated in U2.

## 10. Done (questions; each can fail)

1. Does `/decisions` show the decision records of the range for every Site type, and only records?
2. Do the tile, the inbox badge and E0 `waiting_count` give the same number on the records fixture?
3. Does a record row say who decides by name, its state, and what is at stake, all served?
4. Does `/decisions/:id` ask the question, show one recommendation with one number and its basis (or say plainly why
   none), the options as cards with the same three facts, and the six sections with answers visible when closed?
5. Is every missing figure "Not available yet" naming what would fill it, and never 0?
6. Is every figure a stored 6c figure rounded once, with its source chip when simulated?
7. Does each effect show its heading among the four outcome categories, and the decision its own?
8. Is there no Choose control, and does the act line say so?
9. Does the page work at 390 px with no sideways scroll, by keyboard, in light and dark?
10. Does no served string carry a banned word or code?

## 11. 6f2: the choice on screen (structure fixed; unit card after the 6b and 6d specs)

- **What it adds:** the mock's acts — "Choose this", "Choose another option", "Choose this instead", the sticky act —
  each opening the choose dialog (mock `uxChooseDialog`: What happens · Result against doing nothing · Actions ·
  Recorded under), then "Confirm the choice". Write: `POST /api/decisions/{id}/choice` `{option_key | null,
  run_id}` by the signed-in person through a principal form of 6a's `DecisionService.choose` (H rules unchanged;
  `OPERATOR_EXECUTIVE` only; a `run_id` not the latest refuses so the executive never confirms on figures they did
  not see). No Undo toast: a choice is append-only (`decision_choice_once`); the dialog is the safeguard (MOCK
  DEVIATION D6 at 6f2). The inbox "For you" lights for the executive (MD-IAP-4 closes).
- **Folds in from 6b and 6d:** `CONDITIONAL` cards and bounds rows in "Limits and cover" (6b); the Action that applies
  the setting and its link from the choice (6d). Estimate 2.0 units.

## 12. Reviewer guide and handshake

**Check, and how:**
- Contract: the API bodies against §3.3 key by key (test 2 dumps); every served string against §3.4 (a table-driven
  test over the statement file).
- Figures: no arithmetic on stored figures in `decision_page/` (read the view; plant `round2`); missing never 0
  (plant `zero`); rounding literals of F6-C.
- List: records only (plants `placed`, `count`); E0 = tile = badge.
- Mock: each §5.2 row against `uxDecisionSlots`; every departure has a §9 row and a register row; an unlabelled
  departure is High.
- Copy: §6.4 run; no system words; every sentence plain.
- Range matrix: §8 on the fixtures (cold and EV rows present on `/decisions`).
- Done = §10 answered yes with evidence by path, all tests and plants as listed, gates D1-D3 shown.

**Handshake questions (owner or reviewer; default applied now, W3):**

| # | Question | Default |
|---|---|---|
| Q1 | The list: union of records and uncovered Findings, or a pure swap to records (D-P6.8's wording)? | **Owner: "Build 6h".** Records only (D-P6.52); 6h gives every Site type levers |
| Q2 | Who decides before a choice | the current executive's name; the role words only when none is onboarded (D-P6.47) |
| Q3 | Fourteen options: cards | 7 cards in display order, then "Show all"; the full table below (MD-6F-2) |
| Q4 | Card order | baseline, recommended, by rank, deferred, rejected (D-P6.48) |
| Q5 | "How we will check it worked" before 6e | the approved method (P6 §3) with "Not started" (D-P6.50) |
| Q6 | Money display | cents, signed against doing nothing (SC-1's money form, D-P6.45) |
| Q7 | List order | newest prepared first (the read's order; D-P6.52 replaces D-P6.43's rule) |
| Q8 | 6f2 timing and scope | after the 6b and 6d specs, as the owner accepted; includes "For you" (D-P6.42) |
| R1 | Do IA-P3's inbox and search exist when 6f1 builds? | whichever lands second runs §4.4's sweep |
| R2 | SC-1 glyphs (minus sign, currency symbol) in the literals | confirmed at pre-flight from `formats.money`; literals fixed once in `rulings.md` |

**Size:** U1 1.5 + U2 0.5 + U3 1.5 + the rev 1 words 0.25 = **3.75 units** (6f2 about 2.0, carded later). Order: IA-P1 → IA-P2 and 6h → 6f1 (U1 →
U2 → U3, each reviewed before the next builds on shared code) → 6f2 after 6b/6d.

## 13. Out of scope

The choice and any write (6f2); bounds rows (6b; `CONDITIONAL` is rendered, never decided, here); applying and verifying (6d, 6e); plan value and
plan items (7a, 7c; tile 4 stays "Not available yet"); levers for every Site type (6h); sensitivity; 0K4f's
study (Kobo's values arrive with it, no 6f change needed).
