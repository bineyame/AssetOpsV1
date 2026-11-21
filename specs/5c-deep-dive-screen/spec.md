# 5c: the month, explained (the one deep-dive screen; implementer spec)

Status: in_review (units 1-3 built; screen fix built, 2026-11-21). rev 5, Architect (Claude), 2026-11-21 (rev 2 2026-11-20, re-scoped by D-BW1.9 and D-BW1.12; handshake round 1
answered, `rulings.md` "Handshake answers"). **Rev 3** folds in review round 1 of units 1-2 (`rulings.md` D-5C.19 to
D-5C.25): §2.4 after SC-1f (D-5C.19), the headline's evidence (D-5C.20), nested drivers (D-5C.21), caps on the screen
(D-5C.22), "(at budget)" (D-5C.23), World H's price (D-5C.24) and two record words (D-5C.25). §3.5's literals below
are rev 3's where these rulings touch them; D-4A.12/.20's record changes (PF2) also apply to every A literal that
lists records. **Rev 4** (same day) folds in unit 3's review round 1 (`rulings.md` D-5C.26 to D-5C.28): a figure slot
with no figure has no word (D-5C.26, revises L9), the bridge's step bars served as positions (D-5C.27, closes MD11),
no share without a gap (D-5C.28, M1); the two fix scopes are §11. **Rev 5** (same day, DDR review) rules the cash
sentence (D-5C.29): the bills and the three parts they split into, every cash figure from the cash tree; fix scope §12. UI lane, after the IA-1 stop (RC6). **3.5 units.** `USER_REVIEW_REQUIRED: true` (the screen the
executive sees). Discovery review (W5): money figures on screen.
- **Structure:** P5 (`specs/5a-targets/structure-page-P5.md`, approved 20 Nov) rules 2, 7 and 8; D-5B.10, D-5B.12,
  D-5B.15 (5c inherits them); D-3A7.9 (the standing at the snapshot's "as of"); 3B7a ruling 15 on
  `task/3B7a-snapshot` (n is every Site asked: `len(snapshot.asked)`); RC5 (mini-grid only), RC7 (the owner
  presents; the executive does not sign in), RC9 (the first agreed change is an Action, not valued).
- **Mock (§6 of `.ai/RULES.md`):** vNEXT `#/portfolio` in the hub shape (IA-1b, `specs/IA-1-shape-rebuild/spec.md`
  §3.1 and §3.2 row `portfolio`): L1 the headline and four tiles (`loop-ux.js` `uxOverviewParts` k1 to k4), L2 the
  queue panel, L3 "Where the gap comes from" (`uxBridge`, with "Show as table, by Site") and "By outcome"
  (`uxCats`), drawers only inside sections; IA-1 §3.2's overview budget (at most 6 blocks, headline at most 2 lines,
  2,500 px) binds the live page (D-5C.14). Walkthrough `walkthroughs.md` §2 steps 1 to 3: "the month in one line",
  "Cash collected, outside the contribution gap", Assure's "Contribution's bridge by heading". Departures: §7.
- **UI standing brief** (`owner/owner-ui-standing-brief-2026-11-20.md`): one control per content kind (drawer for a
  figure's detail, disclosure for a table), one interaction grammar, scales to 300 Sites (caps, §5.5), simplicity by
  design, every number with its basis. `Docs/design-system/uiux-guide.md` G2 to G4 gate the review.
- **Builds on:** `5b` (`site_bridge`, `portfolio_bridge`, `BridgeRow`, `PortfolioRow`, `lowest`, `BRIDGE_ROOTS`,
  `CARRY_AT_TARGET`), `3B7a` (`SnapshotRead`, `Served`, `PortfolioMonthSnapshot`, `Freshness`; must be merged),
  `3A7` (`CommercialReconciliation.standing`, `money_word`, `build_commercial_reconciliation`; must be merged),
  `3B1` (`REGISTRIES`, `parsed`, `CATEGORIES`), the live frontend's Portfolio (`estate/EstatePortfolio.tsx`,
  `estate/portfolioWords.ts`, `sites/temporarilyUnavailable.ts`), `ON1` (served tenant; `site_registry`).
- **Decisions:** `rulings.md` (D-5C.1 to D-5C.28). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/5c-deep-dive-screen` off `main` after 3B7a and 3A7 have merged; worktree
  `/opt/assetecon/AssetOpsV1-5c`. Start when the handshake has no open question.
- **Read:** `rulings.md`; 5b `spec.md` §2.2 to §2.4, §4, §5.2 and `rulings.md` D-5B.10 to D-5B.15; 3B7a `spec.md`
  §2.2, §3.3; 3A7 `spec.md` §2.3, §2.6, §2.7; IA-1 `spec.md` §3; vNEXT `loop-ux.js:239-260` and `:313-355`;
  `frontend/src/estate/EstatePortfolio.tsx:830-860`, `estate/portfolioWords.ts:25-47`, `commercial_upload_api.py:60-120`.
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Browser captures through the slot
  pool (`source /opt/assetecon/tools/pw/env.sh`). Never ports 5490 or 8990, the walkthrough database or Docker.
  **No migration.** Evidence to `/opt/assetecon/evidence/5c/<unit>/`.
- **Collisions.** New: `backend/assetops_backend/deep_dive/` (`words.py`, `view.py`, `read.py`, `actions.py`,
  `composition.py`), `backend/assetops_backend/deep_dive_api.py`, `frontend/src/estate/DeepDiveMonth.tsx`,
  `deepDiveMonth.css`, `deepDiveMonthClient.ts`, `PortfolioTabs.tsx`, `tools/deep_dive_gates.cjs`. Edited: `main.py`
  (one router include), `App.tsx` (one route), `estate/portfolioWords.ts` (one tab; `portfolioHref` gives `month` the
  plain path), `estate/EstatePortfolio.tsx` (`PortfolioTabs` moves out verbatim, `counts` optional; a `month` tab
  redirects).

## 1. Outcome and why

The owner opens `/portfolio/month` on the operator's served tenant and walks the executive through one screen: the
month's contribution against their own target, the gap split by heading, Site by Site, cash apart, every figure with
its evidence word and "not yet reconciled" until a closed month matches their management accounts; Kisiwa's budget
disagreement shown, not hidden; every gap in the data named with the record that would fill it; and the change they
agree recorded as an Action with its owner and due date (RC9). Every figure is the bridge's (D-5B.12). Nothing on the
screen is computed in the browser (D-5C.2).

Gate questions: does the screen show 1,443.00 against 2,295.00, −852.00, 3 of 3, Estimated, for Lakeside's October,
and nowhere the uncarried composition 1,693.00 (D-5C.13)? Is Kisiwa's disagreement named in L1 and its −60.00 against
−65.00 on the screen without opening anything? Does every money figure
read "not yet reconciled" until the standing at the snapshot's "as of" is reconciled? Does every stop name its
records?

## 2. Words and formats (`deep_dive/words.py`; unit 1)

### 2.1 Formats (`Context(prec=34, rounding=ROUND_HALF_EVEN)`)

- **Money** `money(v, cur, signed=False)`: `q = v.quantize(Decimal("0.01"))`; magnitude `f"{abs(q):,.2f}"`; prefix
  `$` for USD, else `f"{cur} "`; negative `"−"` (U+2212) before the prefix; `signed` and positive `"+"`; zero is the
  prefix and `"0.00"` with no sign (`"$0.00"`, `"KES 0.00"`); never `-0`.
- **Quantity** `qty(v, unit)`: `v` normalised (no trailing zeros, no exponent: `format(v.normalize(), "f")`), thousands
  commas on the integer part; suffix `" L"` (unit L) or `" kWh"`. **Price** `price(v, cur, per)`: money of `v` to
  4 places when it has more than 2 (`$1.25 per L`, `$0.4321 per kWh`).
- **Share** of a target `pct0(a, t)`: `round(a / t * 100)` half even, `f"{n}%"`, only when `t > 0`. **Percent with
  one decimal** `pct1(x)`: `(x * 100).quantize(Decimal("0.1"))`, `f"{x}%"`.
- **Dates:** month `"October 2026"` (`month_words`), `"October"` (`month_name`); instant `"20 November 2026, 08:00
  UTC"` (`at_words`, the UTC time); day `"15 December 2026"`.
- **Lists** `join(xs)`: `A`, `A and B`, `A, B and C`.
- **Sites** `sites(k, n)`: `"{k} of {n} Sites"` (`"1 of 1 Site"` when `n == 1`).

### 2.2 Labels (`FACTOR_LABELS`; every factor a MINI_GRID bridge can show; test 1 proves it)

`contribution` Contribution · `revenue` Revenue · `billed_kwh` Energy billed · `metered_kwh` Energy metered ·
`delivered_kwh` Energy delivered · `technical_loss_kwh` Technical losses · `unexplained_loss_kwh` Unexplained losses ·
`adjustments_kwh` Billing adjustments · `unmapped_kwh` Energy on unmapped meters · `tariff` Tariff · `productive_kwh`
Productive-use energy · `productive_tariff` Productive-use price · `cost_to_serve` Cost to serve · `fuel_cost` Fuel
cost · `diesel_l` Diesel used · `necessary_l` Diesel not shown to be avoidable (D-5C.16) · `candidate_l` Diesel run while solar
and battery could carry the load · `unexplained_l` Unexplained fuel · `extra_l` Extra diesel from a change ·
`diesel_price` Diesel price · `om` O&M · `staff` Staff · `collection_cost` Collection cost · `battery_wear` Battery
wear · `battery_throughput_kwh` Battery throughput · `wear_rate` Battery wear rate · `collected` Cash collected ·
`in_transit` Paid, in transit · `outstanding` Outstanding.
`lower(label)`: the label unless it starts `O&M`, else its first letter lower-cased.
`HEADINGS = {"GROW_REVENUE": "Grow revenue", "OPTIMIZE_COST": "Optimize cost and efficiency", "PROTECT_ASSET":
"Protect asset and capital", "ASSURE_RETURNS": "Assure performance and returns"}`, keyed by `CATEGORIES`' four names
(test 1 asserts the keys equal `CATEGORIES`; rename the keys to `CATEGORIES`' names if they differ, never the words).

### 2.3 The records that fill a gap (`RECORDS`, this order; `RECORD_KEYS` per leaf; `NOTE_KEYS` per 4d note)

Rev 3: the table below is rev 2's; the records and words served are SC-1's `record` vocabulary as amended by
D-4A.12, D-4A.20, D-4A.24 and D-5C.25 (`BILLING` "the billing export with each line's kWh and tariff", `LOSS_BAND`
"each feeder's expected technical loss as declared in the Site's setup").

| Key | Words |
|---|---|
| BILLING | the billing export |
| BILLING_ADJUSTMENTS | billing adjustments (credit notes) |
| FEEDER_METER | a feeder meter export |
| METER_REGISTER | a meter register with change dates |
| TARIFF_SHEET | the tariff sheet |
| PRODUCTIVE_LINES | productive-use lines in the billing export |
| PRODUCTIVE_TARIFF | the productive-use tariff |
| SETTLEMENTS | the mobile-money settlement statement |
| RECEIPTS | customer receipts |
| EMS | the EMS interval export (generator running and output, solar available power, battery charge) |
| FUEL_CURVE | the generator's fuel curve (litres per kWh; litres per hour idle) |
| TANK_DIPS | tank dips at the start and end of the month |
| FUEL_DELIVERIES | fuel delivery notes |
| FUEL_INVOICES | fuel invoices with litres |
| OM_INVOICES | the service contractor's invoices |
| PAYROLL | payroll lines |
| SITE_SETUP | one generator and one fuel tank declared in the Site's setup (litres are worked out for one of each) |
| ANALYSING | the running record's analysis (still in progress) |
| MONTH_CLOSE | the month to close |
| BUDGET_LINES | (built: `"a budget line for " + x` or `"budget lines for " + join(xs)`, `xs` the leaves' `lower(label)`) |

ANALYSING reads "(still in progress)" in brackets, not after a comma: a record word holds no comma outside brackets (D-5C.25, the no-comma case; fix round 1, KD3).

`RECORD_KEYS`: `revenue`, `billed_kwh` (BILLING); `adjustments_kwh` (BILLING_ADJUSTMENTS); `delivered_kwh`
(FEEDER_METER); `technical_loss_kwh`, `unexplained_loss_kwh` (FEEDER_METER, METER_REGISTER); `unmapped_kwh`
(METER_REGISTER); `tariff` (TARIFF_SHEET); `productive_kwh` (PRODUCTIVE_LINES); `productive_tariff`
(PRODUCTIVE_TARIFF); `in_transit` (SETTLEMENTS); `outstanding` (RECEIPTS); `necessary_l`, `candidate_l` (EMS,
FUEL_CURVE); `unexplained_l` (EMS, FUEL_CURVE, TANK_DIPS, FUEL_DELIVERIES); `fuel_cost`, `diesel_price`
(FUEL_INVOICES); `om` (OM_INVOICES); `staff` (PAYROLL). `NOTE_KEYS` (an actual leaf whose `missing.note` is one of
these adds its key to the leaf's `RECORD_KEYS`; ANALYSING and MONTH_CLOSE replace them instead): `GENERATOR_OR_TANK_NOT_DECLARED` (SITE_SETUP); `NO_RUNNING_RECORD`, `RUNNING_RECORD_GAP`,
`GENERATOR_USE_INCOMPLETE` (EMS); `FUEL_CURVE_MISSING`, `NO_LOAD_RATE_MISSING` (FUEL_CURVE); `TANK_DIPS_MISSING`,
`TANK_DIPS_CONFLICT` (TANK_DIPS); `DISPATCH_NOT_ASSESSED`, `SPANS_OVERLAP`, `SPAN_CLASS_UNKNOWN` (ANALYSING);
`MONTH_OPEN` (MONTH_CLOSE).

**needs(site_bridge, actual_leaves, target_leaves)**: the record keys of the actual leaves (as `NOTE_KEYS` says),
distinct, in `RECORDS` order, as their words; then, when `target_leaves` is non-empty, the
BUDGET_LINES phrase over them in registry order; all joined with `join`.

### 2.4 The evidence word (D-5C.3; 3A5's rule on this screen only, D-BW1.9)

`word(evidence, origins)`: `NOT_AVAILABLE` → "Not available yet"; `ESTIMATED` → "Estimated"; `MODELLED` →
"Modelled"; otherwise by `weakest_origin(origins)`: `source-emulated` → "Emulated"; `demo-simulated` → "Simulated";
`unknown` or none → "Estimated"; `observed-financial`, `field-integrated`, `bench-tested` → by evidence: `RECORDED`,
`DECLARED` "Recorded", `MEASURED` "Measured", `DERIVED` "Calculated". **Rev 3 (D-5C.19):** this order governs
after SC-1f: `DECLARED` with `source-emulated` is "Emulated", with `demo-simulated` "Simulated"; `word()` hands an
observed-origin `DECLARED` to the shared vocabulary as `RECORDED`. Text 5c passes through (3A7's standing) keeps its
own words. A **money** figure's word is
`money_word(word, standing)` (3A7, the organisation's standing for every figure, D-5C.4) unless it is "Not available
yet". Every step, driver (D-5C.16), tile and card value is money. A figure never shows "Verified".

### 2.5 Sentences (exact; `{…}` filled by §2.1's formats)

| Key | English |
|---|---|
| headline | Contribution is {abs gap} {below\|above} target in {month_name}; {subject} {verb} {abs big} of it. |
| headline_more | Contribution is {abs gap} {below\|above} target in {month_name}; {subject} {verb} {abs big}, more than the whole gap. |
| headline_gap | Contribution is {abs gap} {below\|above} target in {month_name}. |
| | `{subject} {verb}`: "cost and efficiency explain" (Optimize) or "Grow revenue explains" (Grow). Named heading (D-5C.15): of Grow and Optimize, those whose sum has the gap's sign (zero has none); `big` the larger in magnitude (ties: Optimize); none: `headline_gap`; `abs big > abs gap`: `headline_more`. |
| headline_on | Contribution is on target in {month_name}. |
| headline_na | Contribution for {month_name} is not available yet. |
| headline_k | (appended when k < n) Compared for {k} of {n} Sites. |
| status_line | {as_of} {standing_short}{ status_disagreement} (each part a sentence; D-5C.14) |
| standing_short | Reconciled with the management accounts. \| Not yet reconciled with the management accounts. (by `standing.reconciled`) |
| status_disagreement | the distinct Sites of `pb.disagreements`, `asked` order: one: "{site}'s budget disagrees with its own lines."; two or three: "The budgets of {join(sites)} disagree with their own lines."; more: "The budgets of {k} Sites disagree with their own lines."; none: omitted |
| tile1_target | Target {target} · {pct0} of target (the `· …` part only when `pct0` applies) |
| tile1_cost | {pct1} of cost from figures received |
| tile2_split | Grow {grow signed} · Optimize {optimize signed} |
| tile2_rest | All of it split to its drivers \| {abs rest} of it not split to its drivers yet (rest with the gap's sign) \| {abs rest} not split to its drivers yet, offsetting the gap (opposite sign) |
| tile3 | label "Plan spend", value "Not available yet", line "No plan has been made yet" |
| tile4 | label "Plan value, 12 months", value "Not available yet", line "Each change is valued against doing nothing once decisions are recorded" |
| disagreement | {site}'s budget states {a\|an} {lower(label)} of {stated}; its budget lines add to {computed}. The target used is {computed}. |
| disagreement_open | ({computed} None) {site}'s budget states {a\|an} {lower(label)} of {stated}; its budget lines do not add up to a figure yet, so the two cannot be compared. |
| bridge_title | {Subject} {verb} {abs big} of the {abs gap} gap. Open a step for what is behind it. · (more) {Subject} {verb} {abs big}, more than the whole {abs gap} gap. Open a step for what is behind it. · (gap) The {abs gap} gap, by heading. Open a step for what is behind it. (same choice as the headline) |
| share | {n}% of what widens the gap \| Offsets it \| No effect |
| drawer_values | Actual {a} · Target {t} · Difference {gap signed} (only for a `SUM` factor with both values) |
| drawer_effect | Effect on contribution {effect signed} |
| carried | {site}: no {CARRY_NOUN} received; taken at its budget line for the month (estimate). (`CARRY_NOUN`: `om` "service contractor invoice", `staff` "payroll line") |
| portfolio_line | The organisation's budget also states {value} for {lower(label)} that no Site carries; it is listed, not added. |
| stop GAP_NOT_AVAILABLE | Not compared until {needs}. |
| stop DETAIL_NOT_AVAILABLE, and every RESIDUAL row (D-5B.15) | Not split further until {needs}. (RESIDUAL rows read "The rest of {lower(parent label)}: {effect signed}. Not split further until {needs}.") |
| stop RECORD_AND_FACTORS_DIFFER | Not split further: the records state {stated} and its parts add to {computed}, {abs diff} apart. (per side that differs: the actual's, then "The target's budget line states …") |
| stop CURRENCY_MISMATCH | Not compared: the actual and the target are in different currencies ({a} and {b}). |
| stop RULE_NOT_DECLARED, PRICE_NOT_DECLARED, SPLIT_INEXACT | Not split further: no rule splits it exactly yet. |
| out STRUCTURE_NOT_DECLARED | {site}: not a mini-grid Site, not included. |
| out NOT_SPLIT | {site}: not split this far. |
| out actual/target leaves | {site}: not compared until {needs}{; its own target is {target}}. |
| cash (rev 5, D-5C.29) | Of {billed} billed for {month_name}, {collected} has been collected, {in_transit} is paid but in transit and {outstanding} is still outstanding. Without `cash_parts`: {collected} has been collected on the bills for {month_name}; the amounts billed, in transit and still outstanding are not available for the same Sites yet. No collected figure: Cash collected in {month_name} is not available yet. |
| fresh | These figures are out of date: {parts joined by "; "}. They are shown as they were on {at_words(as_of)}. Parts: RECORDS "records have arrived since they were prepared" + " for {join(names)}" when Sites are known; MONTH_CLOSED "the month has closed since they were prepared"; RULES "the way they are worked out has changed" |
| untracked | Not checked for later changes: {join("{label} ({join(names)})")}. |
| as_of | Figures as of {at_words(as_of)}. |
| no_snapshot | The figures for {month_words} have not been prepared yet. |
| rebuild | The figures for {month_words} must be prepared again before they can be shown. |
| decisions | Not available yet: no decision has been valued against doing nothing. |
| actions_off | Not available yet: an agreed change is recorded as an Action with its owner and due date. |
| actions_none | No change has been agreed yet. |
| action_row | "{title}" · "Owner {owner} · due {day}" · "Agreed by {created_by} on {day}" · "{state}" |
| not_built | Not built yet: the value of each change against doing nothing, and the limits, warranties and rights under Protect. |
| outcome cards | grow: line "Revenue against target, {sites}"; optimize: "Fuel, O&M and staff against target; cash collected is shown apart"; protect: value "Not available yet", line "Limits, warranties and rights are not set up yet"; assure: value "Reconciled" or "Not yet reconciled", line "{n} budget disagreement(s) · {tile1_cost}" ("No budget disagreement" when 0; "1 budget disagreement", "2 budget disagreements"), drawer title "Reconciliation with the management accounts" |
| errors | `BAD_MONTH` "Write the month as YYYY-MM, like 2026-10." · `DEEP_DIVE_UNAVAILABLE` "The month's figures cannot be read right now." · `PERSON_REQUIRED` 3C0a's `person.person_required` |

## 3. The view (`deep_dive/view.py`; unit 1; pure)

```python
class Standing(Protocol):            # 3A7's MoneyStanding satisfies it
    reconciled: bool; reason: str; text: str
@dataclass(frozen=True)
class AgreedAction:                  # the read 3C2 provides (§4.3)
    action_id: str; title: str; site_code: str | None; factor_id: str | None
    owner_name: str; created_by_name: str; created_at: datetime; due_on: date; state_words: str
@dataclass(frozen=True)
class AgreedActions:
    connected: bool; actions: tuple[AgreedAction, ...]     # newest first, as the port gives them (D-5C.17)

def month_view(*, operator: str, month: str, served: Served, standing: Standing,
               actions: AgreedActions, names: Mapping[str, str], now: datetime) -> dict
```
`standing` is the organisation's, read by the caller at `served.as_of` (D-3A7.9, D-5C.4); it words every money figure.
`names`: Site code to display name (absent: the code). `month_view` keeps the port's order.
**Amended (D-3A7.16, 2026-11-21).** `Standing` also has `details: tuple[str, ...]` (the failing headings' sentences;
`()` unless the reason is `THIS_MONTH_NOT_MATCHED` or `THIS_MONTH_NOT_COMPARABLE`). §3.1: `standing` is `{"reconciled",
"reason", "text", "details"}`; the assure drawer's `lines` are `[standing.text, *standing.details]` plus
`fresh.untracked_text` when not null. §3.5 World A: `text` ends at "...within 1%." and the fuel-cost sentence is the one
entry of `details` (strings in SC-1's forms when 5c converts its words).

**Build.** `served.state` NO_SNAPSHOT or REBUILD_NEEDED: only the header keys (`schema` to `state_text`; §3.1).
SERVED: `snap = served.snapshot`; `sb = {c: site_bridge(s.inputs, s.targets) for c, s in snap.sites.items()}`;
`pb = portfolio_bridge(sb, snap.asked, snap.sites_excluded, snap.portfolio_lines, snap.month, key, version)` (the
snapshot's structure key and version). `n = len(snap.asked)`. Every figure below is a row of `pb.rows` or `sb[c].roots`
(D-5B.12); `snap.actual()` and `snap.targets()` are never read. `STEPS = {"MINI_GRID": ("revenue", "fuel_cost",
"om", "staff")}` (D-5C.5; test 1 proves each is a term of `contribution` or `cost_to_serve` in the registry and that
together with the neutral terms they are all of them). A step's group is its row's `home`.

### 3.1 The JSON (`schema` `deep-dive-month-1`; keys in this order; strings as §2)

| Key | Value |
|---|---|
| `schema`, `operator`, `month`, `month_words` | as named |
| `nav` | `{"previous": month − 1, "next": month + 1 when its end (UTC) is at or before `now`, else null}` |
| `state`, `state_text` | `served.state`; null, or `no_snapshot` / `rebuild` |
| `as_of`, `as_of_text` | ISO `Z`; `as_of` sentence |
| `fresh` | `{"current", "text", "untracked_text"}`: `text` per `fresh` when not current, else null; Sites from `changed_kinds` codes and `stale_stamps` with a `site_id` (mapped through `snap.sites`), in `asked` order; `untracked_text` from `freshness.untracked` (`"<code>:<leaf>"`), null when empty |
| `standing` | `{"reconciled", "reason", "text"}` of `standing` |
| `headline` | `{"text", "evidence"}` (SC-1 `served`; each evidence word through `money_word` with the standing,
as the tiles' words, D-5C.20) §2.5 from the root row `R = pb.rows["contribution"]["contribution"]`; `grow` = the GROW_REVENUE steps' effects summed, `optimize` the OPTIMIZE_COST ones; the named heading per D-5C.15 |
| `status_line` | §2.5 `status_line`: `as_of_text`, `standing_short`, `status_disagreement` (D-5C.14) |
| `tiles` | four objects `{"key", "label", "value", "word", "lines", "bar"}`: `contribution` (R's actual; lines tile1_target, `sites(R.k, n)`, tile1_cost; bar `{"actual", "target"}` plain decimals), `gap` (R's effect signed; lines tile2_split, tile2_rest), `plan_spend`, `plan_value` (word null, bar null). Rev 4 (D-5C.26): every figure slot's `word` is `figure_word(value, currency, ev, origins)`, null exactly when the figure (value or currency) is absent |
| `notices` | one `disagreement` sentence per `pb.disagreements` entry, `asked` order |
| `bridge` | `{"title", "totals", "scale", "groups", "by_site"}` (§3.2; `scale` rev 4, D-5C.27) |
| `cash` | `{"title": "Cash collected, outside the contribution gap", "text", "word", "sites", "table"}` (§3.3) |
| `outcomes` | the four cards, `HEADINGS` order, each `{"key", "label", "value", "word", "line", "drawer"}` (§2.5): grow and optimize value the group's sum signed and word the weakest of its steps' words, null when the sum or `group_cur` is None (rev 4, D-5C.26: revises L9's "Not available yet"); protect and assure word null; `drawer` null except assure: `{"title", "lines"}` with `lines` `[standing.text]` plus `fresh.untracked_text` when not null |
| `decisions` | `{"title": "Decisions", "text": decisions}` |
| `actions` | `{"title": "Actions in hand", "connected", "text", "rows", "more"}`: not connected `actions_off`, rows [], more 0; connected and none `actions_none`; else text null, one row `{"title", "owner", "agreed", "state"}` per Action in the port's order (newest first), at most 3, `more` the rest (0 when none) |
| `not_available` | `{"rows": [{"needs", "fills", "sites"}], "not_built": not_built}` (§3.4) |

**tile1_cost** = `(C.actual − Σ carried) / C.actual` with `C = pb.rows["contribution"]["cost_to_serve"]` and `Σ
carried` the actual values of every carried leaf of every included Site (`sb[c].actual.values[leaf].value` for leaf in
`sb[c].carried`); omitted when `C.actual` is None or 0. **tile2_rest** = Σ over included Sites of the effects of
`lowest(sb[c].roots["contribution"])` rows with split `NOT_SPLIT` or kind `RESIDUAL`; its words by its sign against
the gap (§2.5, D-5C.15).

### 3.2 The bridge

- `totals`: `{"actual_label": "Contribution, {month_name}", "actual", "target_label": "Target", "target"}` from R.
- `scale` (rev 4, D-5C.27): `{"target_at", "actual_at"}` from `bridge_bars`, null when R's effect is None or 0.
- `groups`: per home present among the steps, `CATEGORIES` order: `{"key", "label": HEADINGS[key], "value": Σ step
  effects signed, "steps": [...]}`. A step: `{"key", "label", "value" (effect signed, or "Not available yet" when
  the row is absent or its effect None), "share", "word", "sites", "bar", "drawer"}`; `share` against the steps whose effect
  has the gap's sign (`round(|e| / Σ|those| × 100)` half even), and null for every step when R's effect is None or 0
  (rev 4, D-5C.28); `word` §2.4 (money), null when the value is "Not available yet" (D-5C.26).
- **Bars (rev 4, D-5C.27).** `bridge_bars(effects: Sequence[Decimal | None], gap: Decimal | None) -> tuple[list[dict
  | None], dict | None]`, module-level and pure in `view.py`, called with the steps in JSON order (groups in
  `CATEGORIES` order, steps in group order), each step's effect, or None when its row is absent, its effect is None or
  its row's currency is not R's. Exact Decimal (`prec=34`): when `gap` is None or 0, every bar and the scale are None.
  Else `p = 0`; for each step with effect `e` not None and not 0: `a = p`, `b = p + e / gap × 100`, `p = b` (a None or
  0 step gets None and leaves `p`). `lo = min(0, every a and b)`, `hi = max(100, every a and b)`, `S(x) = (x − lo) /
  (hi − lo) × 100`. A bar: `L = S(min(a, b))`, `W = max(0.8, min(|S(b) − S(a)|, 100 − L))`, `{"left": L, "width": W,
  "tone": "lowers" if e < 0 else "raises"}`. Scale: `{"target_at": S(0), "actual_at": S(100)}`. Every number is
  rounded half even to 0.01 and served as a plain string with two places ("0.00", "11.38", "100.00").
- `drawer`: `{"title", "lines", "sites", "carried", "out", "lines_org", "drivers"}`: `lines` drawer_values (when it
  applies), drawer_effect, `sites(k, n)`; `sites` one entry per included Site in `asked` order (every Site; the screen caps, D-5C.22): `{"site", "value": that Site's row effect signed, "text": the stop sentence of that row or of its
  lowest descendants that stop (each once, in tree order, joined by a space), null when none}`; `carried` §2.5 per
  `PortfolioRow.carried` Site; `out` §2.5 per `PortfolioRow.out` entry (target from that Site's own root when it has
  one); `lines_org` `portfolio_line` per `pb.portfolio_lines` line whose factor is the step; `drivers` (nested, D-5C.21): the
  step's direct parts among the portfolio rows whose key is a registry descendant of the step (and `residual:<x>` rows
  under it), each with its own parts in `children`, a driver's parent being its nearest registry ancestor that is the
  step or has a driver row, `residual:<x>` last among `x`'s children, `pb.rows` order within a level:
  `{"key", "label", "value", "sites", "detail", "word", "children"}` with `value` the row's effect signed, `detail` "Actual {a} ·
  Target {t}" (qty, price or money by unit) when both are present, else null, and `word` §2.4 of the row through
  `money_word` (D-5C.16).
- `by_site`: `{"columns": ["Site", "Contribution", "Target", "Gap", <step labels>], "rows", "total"}`: per asked Site
  (every Site; the screen shows 10, then "Show all {n}", D-5C.22) its root actual (unsigned), target, gap and step effects (signed), a step
  cell suffixed `" (at budget)"` when that Site's row is `carried` (D-5C.23; the step drawer's per-Site row takes the
  same suffix); only MINI_GRID Sites have rows; a Site not in R's k
  reads its root actual or "Not available yet", its own target, then "Not compared" in the other cells; no cell
  carries a word (the section's word is the organisation's, D-5C.4); `total`: `sites(R.k, n)`, R's actual,
  target, effect, then each step's effect.

### 3.3 Cash

From `pb.rows["collected"]` (the cash tree only, rev 5, D-5C.29): the `collected` root's actual, and
`cash_parts(rows)`'s `revenue` (billed), `in_transit` and `outstanding` actuals, given together or not at all (§12).
The root's target is not read. `word` §2.4 of the root (money), null when the root's actual or currency is None (rev 4,
D-5C.26); `sites` of the root. `table`: columns `["Site",
"Billed", "Collected", "In transit", "Outstanding"]`, rows per asked Site from `sb[c].roots["collected"]` (Billed is that tree's `revenue` row,
rev 5; unsigned money; "Not available yet" for an absent value), total from the portfolio rows: collected's root,
then the three parts from `cash_parts` ("Not available yet" each when it is None).

### 3.4 What is not available yet

Shown as the last part of "By outcome" (D-5C.14). Over every included and out Site (asked order), every row of both roots (depth first): the row's `unobserved_actual`
(actual leaves) and `unobserved_target` (target leaves); and every carried leaf (its record key; `fills` gets
" (taken at its budget line meanwhile)"). Group by record key (actual: as `NOTE_KEYS` says; target: one
`BUDGET_LINES` row): `needs` the key's words (BUDGET_LINES: its phrase over all target leaves seen), `fills`
`join` of the leaves' labels in registry order, `sites` `join` of names. Rows in `RECORDS` order. At most 8 rows shown;
the rest behind "Show all {n}" in the screen (the JSON holds all).

### 3.5 Fixtures (hand-computed; the tests write these literals, W2)

**World A.** 5b §5.2's world with its step (3A4 `new_world()`, 4b's `money_leaves_lakeside.json`, 5a's
`targets_lakeside.json` steps 1 and 2, 5b's `attribution_lakeside_mto.json`), read through 3B7a's test reader
`CommercialLeafSource(months, store, fallback())` (no `LitreLeafSource`: the litre leaves read NOT_CONNECTED with no
note; P3), snapshot built in memory by 3B7a's `SnapshotBuilder` at `AS_OF = 2026-11-20T08:00:00Z` over Kobo, Kisiwa,
Mto (n = 3), served by `SnapshotRead` with clock `AS_OF`. `operator` "Lakeside Power"; `names` {KOBO-001 Kobo,
KISIWA-001 Kisiwa, MTO-001 Mto}; `now = AS_OF`; `standing` the literal Standing `reconciled` False, `reason`
THIS_MONTH_NOT_MATCHED, `text` "Not yet reconciled: October 2026 (the organisation) does not match the management
accounts within 1%. Fuel cost: the accounts say 5,100.00 USD and the records say 4,995.00 USD, 105.00 less (2.06%),
beyond the 51.00 allowed (1%)." (3A7's text for an organisation statement of revenue 9,700.00 and fuel cost 5,100.00
against recorded 9,688.00 and 4,995.00); `actions` `AgreedActions(False, ())`.

**Expected A** (every string exact):
- `nav` {"previous": "2026-09", "next": null}; `state` SERVED; `as_of_text` "Figures as of 20 November 2026, 08:00
  UTC."; `fresh` {"current": true, "text": null, "untracked_text": null} (`untracked` is () in this world).
- `headline` {"text": "Contribution is $852.00 below target in October; cost and efficiency explain $755.00 of it.",
  "evidence": ["Estimated, not yet reconciled"]} (D-5C.20).
- `status_line` "Figures as of 20 November 2026, 08:00 UTC. Not yet reconciled with the management accounts. Kisiwa's
  budget disagrees with its own lines."
- `tiles[0]` Contribution, "$1,443.00", word "Estimated, not yet reconciled", lines ["Target $2,295.00 · 63% of
  target", "3 of 3 Sites", "91.5% of cost from figures received"], bar {"actual": "1443.00", "target": "2295.00"}.
  (1,443 / 2,295 = 62.88 %; (8,245 − 700) / 8,245 = 91.51 %.)
- `tiles[1]` Gap to target, "−$852.00", "Estimated, not yet reconciled", lines ["Grow −$97.00 · Optimize −$755.00",
  "$852.00 of it not split to its drivers yet"] (Kobo +38 − 600, Kisiwa −55 − 130, Mto −80 − 25).
- `tiles[2]`, `tiles[3]` per §2.5.
- `notices` ["Kisiwa's budget states a contribution of −$60.00; its budget lines add to −$65.00. The target used is
  −$65.00."]
- `bridge.title` "Cost and efficiency explain $755.00 of the $852.00 gap. Open a step for what is behind it."; totals
  "Contribution, October" "$1,443.00", "Target" "$2,295.00".
- groups: Grow revenue "−$97.00": revenue "−$97.00", "11% of what widens the gap", "Emulated, not yet reconciled",
  "3 of 3 Sites". Optimize cost and efficiency "−$755.00": fuel_cost "−$755.00", "89% of what widens the gap",
  "Emulated, not yet reconciled"; om "$0.00", "No effect", "Estimated, not yet reconciled"; staff "$0.00", "No
  effect", "Emulated, not yet reconciled"; each "3 of 3 Sites".
- revenue drawer lines ["Actual $9,688.00 · Target $9,785.00 · Difference −$97.00", "Effect on contribution −$97.00",
  "3 of 3 Sites"]; sites Kobo "+$38.00", Kisiwa "−$55.00", Mto "−$80.00", each text "Not split further until the billing
  export with each line's kWh and tariff, a feeder meter export, a meter register with change dates, the customer
  meter reads for the month, each feeder's expected technical loss as declared in the Site's setup, the
  productive-use tariff and budget lines for energy delivered, tariff and productive-use price." (D-4A.12/.20,
  D-5C.25); drivers [].
- fuel_cost drawer lines ["Actual $4,995.00 · Target $4,240.00 · Difference +$755.00", "Effect on contribution
  −$755.00", "3 of 3 Sites"]; sites Kobo "−$600.00", Kisiwa "−$130.00", Mto "−$25.00", each "Not split further until
  the EMS interval export (generator running and output, solar available power, battery charge), the generator's fuel
  curve (litres per kWh; litres per hour idle), tank dips at the start and end of the month and fuel delivery notes.";
  drivers [].
- om drawer lines ["Actual $1,800.00 · Target $1,800.00 · Difference $0.00", "Effect on contribution $0.00", "3 of 3
  Sites"]; sites Kobo "$0.00", Kisiwa "$0.00 (at budget)", Mto "$0.00" (D-5C.23); carried ["Kisiwa: no service contractor invoice received; taken at its budget line for the month
  (estimate)."]. staff drawer lines ["Actual $1,450.00 · Target $1,450.00 · Difference $0.00", …]; lines_org ["The
  organisation's budget also states $1,200.00 for staff that no Site carries; it is listed, not added."].
- Rev 4 (D-5C.27): `bridge.scale` {"target_at": "0.00", "actual_at": "100.00"}; step `bar`s: revenue {"left":
  "0.00", "width": "11.38", "tone": "lowers"} (97 / 852 = 11.3850 %), fuel_cost {"left": "11.38", "width": "88.62",
  "tone": "lowers"} (11.3850 % to 100 %), om null, staff null (effect 0). D-5C.28 changes no A share.
- by_site rows: Kobo "$883.00", "$1,445.00", "−$562.00", "+$38.00", "−$600.00", "$0.00", "$0.00"; Kisiwa "−$250.00",
  "−$65.00", "−$185.00", "−$55.00", "−$130.00", "$0.00 (at budget)", "$0.00"; Mto "$810.00", "$915.00", "−$105.00",
  "−$80.00", "−$25.00", "$0.00", "$0.00"; total "3 of 3 Sites", "$1,443.00", "$2,295.00", "−$852.00", "−$97.00",
  "−$755.00", "$0.00", "$0.00".
- cash text (rev 5, D-5C.29) "Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in
  transit and $668.00 is still outstanding."; word "Estimated, not yet reconciled"; rows Kobo "$3,458.00", "$3,180.00", "$0.00",
  "$278.00"; Kisiwa "$4,070.00", "$3,800.00", "$0.00", "$270.00"; Mto "$2,160.00", "$1,890.00", "$150.00",
  "$120.00"; total "3 of 3 Sites", "$9,688.00", "$8,870.00", "$150.00", "$668.00".
- outcomes: grow "−$97.00" "Emulated, not yet reconciled" "Revenue against target, 3 of 3 Sites", drawer null;
  optimize "−$755.00" "Estimated, not yet reconciled" (the weakest of its steps), drawer null; protect "Not available
  yet", word null, drawer null; assure "Not yet reconciled", word null, "1 budget disagreement · 91.5% of cost from
  figures received", drawer {"title": "Reconciliation with the management accounts", "lines": [A's standing text]}.
- `actions` {"title": "Actions in hand", "connected": false, "text": "Not available yet: an agreed change is recorded as
  an Action with its owner and due date.", "rows": [], "more": 0}.
- `not_available.rows` (needs · fills · sites; all three Sites unless named; rev 3 with D-4A.12/.20 and D-5C.25):
  the billing export with each line's kWh and tariff · Billing adjustments, Energy on unmapped meters and Tariff; a
  feeder meter export · Energy delivered, Technical losses and Unexplained losses; a meter register with change dates
  · Unexplained losses and Energy on unmapped meters; the customer meter reads for the month · Unexplained losses and
  Energy on unmapped meters; each feeder's expected technical loss as declared in the Site's setup · Technical losses
  and Unexplained losses; the productive-use tariff · Productive-use price; the EMS interval export (…) · Diesel not shown to be
  avoidable, Diesel run while solar and battery could carry the load and Unexplained fuel; the generator's fuel curve
  (…) · the same three; tank dips at the start and end of the month · Unexplained fuel; fuel delivery notes ·
  Unexplained fuel; the service contractor's invoices · O&M (taken at its budget line meanwhile) · Kisiwa; budget lines
  for energy delivered, tariff and productive-use price · Energy delivered, Tariff and Productive-use price. Sites
  "Kobo, Kisiwa and Mto".

**A2 (a budget that cannot be added).** A with Kisiwa's check replaced, at the view, by `TargetCheck("contribution",
Decimal("-60.00"), None, "USD", False)`: `notices` ["Kisiwa's budget states a contribution of −$60.00; its budget lines
do not add up to a figure yet, so the two cannot be compared."]; `status_line` unchanged.
**B (reconciled).** A with `standing` `reconciled` True, `RECONCILED`, "Reconciled: October 2026 (the organisation)
matches the management accounts within 1%.": every ", not yet reconciled" suffix gone (the headline's `evidence` ["Estimated"]); `status_line` "Figures as of 20
November 2026, 08:00 UTC. Reconciled with the management accounts. Kisiwa's budget disagrees with its own lines.";
assure "Reconciled", its drawer lines [B's text].
**C (an agreed change).** A with `AgreedActions(True, (AgreedAction("A-1", "Lower the generator stop setting at Kobo to
70% battery charge", "KOBO-001", "candidate_l", "Peter", "Amina", 2026-11-20T09:30Z, 2026-12-15, "Open"),))`: rows
[{"title": "Lower the generator stop setting at Kobo to 70% battery charge", "owner": "Owner Peter · due 15 December
2026", "agreed": "Agreed by Amina on 20 November 2026", "state": "Open"}], text null, more 0. Connected and empty:
text "No change has been agreed yet.", rows [], more 0. **C4:** four Actions `A-4`, `A-3`, `A-2`, `A-1` (newest first,
created 11:00Z, 10:30Z, 10:00Z, 09:30Z, titles "Change 4" to "Change 1", otherwise as C): rows "Change 4", "Change 3",
"Change 2"; more 1.
**D (Mto's records missing).** 5b §5.2 without its step: headline "Contribution is $747.00 below target in October;
cost and efficiency explain $730.00 of it. Compared for 2 of 3 Sites."; `tiles[0]` value "$633.00", lines ["Target
$1,380.00 · 46% of target", "2 of 3 Sites", "89.8% of cost from figures received"]; tile2 ["Grow −$17.00 · Optimize
−$730.00", "$747.00 of it not split to its drivers yet"]; revenue drawer `out` one line starting "Mto: not compared
until the billing export" and ending "; its own target is $915.00."; by_site Mto row "Not available yet", "$915.00",
then "Not compared" × 5. No "$883.00" in `tiles`, `headline`, `bridge.totals` or `outcomes` (D-5C.13).
**E (out of date).** A, then 3B7a §5's `LATE` invoice ingested at 2026-11-21T09:00Z and the read clock and `now`
2026-11-21T10:00Z, no rebuild: figures as A; `fresh.current` false, text "These figures are out of date: records have
arrived since they were prepared for Kisiwa. They are shown as they were on 20 November 2026, 08:00 UTC."
**G (another type asked).** A with 3B7a §5's `THIKA-001` (COLDCHAIN) asked last: headline A's plus " Compared for 3
of 4 Sites."; tile1 lines[1] "3 of 4 Sites"; every step's `sites` "3 of 4 Sites" and its drawer `out` ["Thika: not a
mini-grid Site, not included."] (`names` gains THIKA-001 Thika); `by_site` lists the three mini-grid Sites only.
**H (Kobo's litres; D-5C.16).** A read through `CommercialLeafSource(months, store, LitreLeafSource(FakeInputs,
fallback(), lambda: AS_OF))`, `FakeInputs` as 4d §5's bridge (4d's KOBO-OCT for KOBO-001, V11 for the others). Every
key equals A's except:
- `tiles[1].lines[1]` "$252.00 of it not split to its drivers yet" (Kobo's −600.00 is split to leaves).
- fuel_cost drawer `sites`: Kobo "−$600.00", text null; Kisiwa "−$130.00" and Mto "−$25.00", each "Not split further
  until the EMS interval export (generator running and output, solar available power, battery charge), the
  generator's fuel curve (litres per kWh; litres per hour idle), tank dips at the start and end of the month, fuel
  delivery notes and one generator and one fuel tank declared in the Site's setup (litres are worked out for one of
  each)."
- fuel_cost drawer `drivers` (nested, D-5C.21; each {key, label, value, sites, detail, word, children}): [{"diesel_l",
  "Diesel used", "−$600.00", "1 of 3 Sites", "Actual 1,180 L · Target 700 L", "Modelled, not yet reconciled", children
  [{"necessary_l", "Diesel not shown to be avoidable", "−$37.50", "1 of 3 Sites", "Actual 730 L · Target 700 L",
  "Modelled, not yet reconciled", []}, {"candidate_l", "Diesel run while solar and battery could carry the load",
  "−$412.50", "1 of 3 Sites", "Actual 330 L · Target 0 L", "Modelled, not yet reconciled", []}, {"unexplained_l",
  "Unexplained fuel", "−$150.00", "1 of 3 Sites", "Actual 120 L · Target 0 L", "Modelled, not yet reconciled", []}]},
  {"diesel_price", "Diesel price", "$0.00", "1 of 3 Sites", null, "Modelled, not yet reconciled", []}] (D-5C.24: a
  price does not add across Sites, so no detail; its effect is Modelled litres times the price difference).
- `fresh.untracked_text` "Not checked for later changes: Diesel not shown to be avoidable (Kobo), Diesel run while
  solar and battery could carry the load (Kobo) and Unexplained fuel (Kobo)." (labels in registry order), which is
  also the assure drawer's second line.
- `not_available.rows`: the EMS and fuel-curve rows' sites "Kisiwa and Mto"; the tank-dips and delivery-notes rows'
  sites "Kisiwa and Mto"; a new row after the service contractor's invoices: "one generator and one fuel tank declared
  in the Site's setup (litres are worked out for one of each) · Diesel not shown to be avoidable, Diesel run while
  solar and battery could carry the load and Unexplained fuel · Kisiwa and Mto".
**F.** Month 2026-09: NO_SNAPSHOT, `state_text` "The figures for September 2026 have not been prepared yet.", `nav`
{"previous": "2026-08", "next": "2026-10"}. A row with `format` 0 written to the store: REBUILD_NEEDED, "The figures
for October 2026 must be prepared again before they can be shown."
**Bars** (rev 4, D-5C.27; `bridge_bars` direct, effects in order, gap last): V1 (+50.00, −150.00; −100.00): [{"0.00",
"33.33", raises}, {"0.00", "100.00", lowers}], scale {"33.33", "100.00"}. V2 (−1.00, −999.00; −1000.00): [{"0.00",
"0.80", lowers}, {"0.10", "99.90", lowers}], scale {"0.00", "100.00"}. V3 (None, −852.00; −852.00): [None, {"0.00",
"100.00", lowers}], scale {"0.00", "100.00"}. V4 (−97.00, −755.00; None): [None, None], scale None. V5 (+5.00, −5.00; 0.00): [None, None], scale
None. V6 (−150.00, +50.00; −100.00): [{"0.00", "100.00", lowers}, {"66.67", "33.33", raises}], scale {"0.00",
"66.67"}. H's bars and scale equal A's.
**World X** (the generated currency-mismatch world, `deep_dive_worlds.world_x()`, rev 4): every step `share` null and
no "Offsets it" (D-5C.28); every `bar` and `bridge.scale` null (R's effect None); the contribution and gap tiles, the
revenue step and the Optimize card serve `word` null beside "Not available yet" (D-5C.26); no served `word` reads
"Not available yet".
**Lead vectors** (view-level, October, USD; D-5C.15): L1 gap −100.00, Grow +200.00, Optimize −300.00: "Contribution is
$100.00 below target in October; cost and efficiency explain $300.00, more than the whole gap." and title "Cost and
efficiency explain $300.00, more than the whole $100.00 gap. Open a step for what is behind it."; L2 −100.00, −120.00,
+20.00: "…; Grow revenue explains $120.00, more than the whole gap."; L3 −10.00, 0.00, 0.00: "Contribution is $10.00
below target in October." and title "The $10.00 gap, by heading. Open a step for what is behind it."; L4 +50.00,
+30.00, +20.00: "Contribution is $50.00 above target in October; Grow revenue explains $30.00 of it."; rest +40.00
against gap −100.00: "$40.00 not split to its drivers yet, offsetting the gap".

The tests write A as `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` **by hand from this section** (never
by running `month_view`); unit 3's frontend tests and the gates script render the same file (the gates' second view
is A with `headline` set in memory to D's, the longest headline).

## 4. The read and the route (unit 2)

### 4.1 `deep_dive/read.py`

`DeepDiveRead(snapshots: SnapshotRead, reconciliation: CommercialReconciliation, actions: AgreedActionsPort, clock)`.
`month(tenant: TenantRef, month: str | None, names) -> dict`: `month` None is the calendar month before `clock()`'s
UTC month; a month not fullmatching `[0-9]{4}-(0[1-9]|1[0-2])` raises `ValueError("BAD_MONTH")`; `served =
snapshots.portfolio(tenant.id, month)`; when SERVED, one `reconciliation.standing(tenant.id, None, month,
known_at=served.as_of)` (the organisation's; D-3A7.9, D-5C.4; no Site standing is read); `actions.for_tenant(
tenant.id)`; `month_view(...)` with `now = clock()`. `build_deep_dive_read(url)` (`deep_dive/composition.py`) builds
3B7a's snapshot read, 3A7's `(reconciliation, dispose)` and the actions port (`NotConnectedActions()` until 3C2
connects), and its `dispose` disposes all three (P4).

### 4.2 `deep_dive_api.py`: `GET /api/portfolio/month?month=YYYY-MM`

- Tenant: `app.state.site_registry.tenant()`; None or the read absent (no `DATABASE_URL`): 503 `DEEP_DIVE_UNAVAILABLE`.
  Names: `{s.site_code: s.name for s in registry.imported_sites()}`.
- **Real data (D-5C.7):** when `commercial_upload_settings(url).real_data` is on, `person_from_request(request,
  accounts)` must give a person of that tenant, else 401 `PERSON_REQUIRED`. Off (emulated rehearsal and demo): no
  person needed (RC7).
- `ValueError("BAD_MONTH")`: 422. A store fault (the `unavailable` errors the commercial router uses): 503.
- 200: the view JSON, `Cache-Control: no-store`. Refusals: `{"code", "text"}`.
- `create_app`: `app.include_router(build_deep_dive_router(...))` right after the commercial upload router, with
  `build_deep_dive_read(url)` (composition; disposed on shutdown as the other compositions are).

### 4.3 `deep_dive/actions.py`: the seam 3C2 fills (D-5C.8)

```python
class AgreedActionsPort(Protocol):
    def for_tenant(self, tenant_id: UUID) -> AgreedActions: ...
class NotConnectedActions:            # until 3C2 merges
    def for_tenant(self, tenant_id: UUID) -> AgreedActions: return AgreedActions(False, ())
```
**Contract with 3C2 (3C2 spec §2 and §3 adopt it; D-3C2.5):** 3C2's `actions/agreed.py` reads its agreed-Action
records only (every agreed Action of the tenant, open or overdue, **newest first** by `(created_at, id)`; the S6-01a
finding Actions are never read, D-5C.17; owner and creator by display name; `state_words` "Open" or "Overdue"), built
by `actions/agreed_composition.py`'s `build_agreed_actions(database_url)`; and a command `python -m
assetops_backend.record_action --tenant SLUG --as EMAIL --title TEXT --owner EMAIL --due YYYY-MM-DD [--site CODE]
[--factor ID]` that prints the Action as one JSON line (exit 0). In its unit 2, after both have merged, 3C2 adds
`StoreAgreedActions` to this file (mapping its views to `AgreedAction`), replaces `NotConnectedActions()` in
`deep_dive/composition.py` with it (one line) and adds 5c test 9(d).

## 5. The screen (unit 3; `frontend/src/estate/DeepDiveMonth.tsx`)

### 5.1 Route, tab and client

- `App.tsx`: `<Route path={DEEP_DIVE_PATH} element={<DeepDiveMonthFrame client={deepDive} />} />` with
  `DEEP_DIVE_PATH = "/portfolio/month"`, placed before the `${PORTFOLIO_ROOT_PATH}/:tab?` route.
- `portfolioWords.ts`: `PORTFOLIO_TABS` gains `{ tab: "month", label: "The month", segment: "month" }` right after
  Overview; `PortfolioTab` gains `"month"`; `portfolioHref` gives `month` the plain `/portfolio/month` (no `?window=`
  or lens). `EstatePortfolio.tsx`: `PortfolioTabs` (today `EstatePortfolio.tsx:827-859`) moves verbatim to
  `PortfolioTabs.tsx`, with `counts` optional (no badge when absent) and nothing else changed; the Overview passes its
  `counts` as today; the month page passes `current="month"`, no `counts`, and the Portfolio's default `window` and
  `lens` (the values `EstatePortfolio` uses when the URL has none). Given tab `month` the frame renders `<Navigate
  to="/portfolio/month" replace />`.
- `deepDiveMonthClient.ts`: `fetchDeepDiveMonth(month?: string)` GETs `/api/portfolio/month[?month=…]` through
  `fetchRetrying`; a body whose `schema` is not `deep-dive-month-1` is an error. The URL's `?month=` is the state; the
  month links change it (browser history).

### 5.2 Layout: the hub shape (IA-1b §3.1; D-5C.14), live classes

```
<section data-shape="hub" class="dd-month">
  <header> h1 "Portfolio" · <PortfolioTabs current="month"/> · month nav: "‹ {previous words}" · <b>{month_words}</b> · "{next words} ›" (disabled without next) </header>
  <div data-level="L1">
    <div class="dd-lead"> <p class="dd-headline">{headline}</p> <p role="status" class="dd-status">{status_line}</p> [<p class="dd-fresh">{fresh.text}</p>] </div>
    <div class="dd-kpis"> 4 tiles: label, value, word chip, lines, bar (tile 1) </div>
  </div>
  <div data-level="L2">
    <div class="dd-queue"> panel "Decisions" {decisions} · panel "Actions in hand" {actions} </div>
  </div>
  <div data-level="L3">
    <section "Where the gap comes from">: title; notices (role="note", visible, never in a drawer); totals with the
        bar; the scale row (rev 4: two marks, omitted when `scale` is null); groups as an <ol> (group row: label and
        value; step rows: button opening the step drawer: label, value, share, word, sites, and the step track with
        its bar, D-5C.27); <details> "Show as table, by Site"; the step drawers </section>
    <section "Cash collected, outside the contribution gap">: text, word, sites, <details> "Show by Site" table </section>
    <section "By outcome">: four cards (the Assure card's value is a button opening its drawer); h3 "What is not
        available yet": rows (needs, fills, sites), 8 then "Show all {n}"; not_built line; the Assure drawer </section>
  </div>
</section>
```
- Blocks (a visible direct child of a level region, outside drawers): L1 2, L2 1, L3 3: **6**, IA-1b's budget.
  `[data-shape="hub"] > [data-level] { display: contents }` in `deepDiveMonth.css`. Drawers stay inside their
  sections (IA-1 §3.2 row `portfolio`: none at top level), so the `[data-ia-drawers]` region is omitted (an empty
  slot omits its region).
- Drawers: role="dialog", aria-modal, labelled by its title; focus moves to Close; Escape and the scrim close; focus
  returns to the opener (vNEXT `uxOpen`/`uxClose`). A driver row in a step drawer shows label, value, word chip,
  sites and detail.
- NO_SNAPSHOT and REBUILD_NEEDED: header, `state_text`, nothing else. Loading: the header and "Preparing the month…".
  503: `DEEP_DIVE_UNAVAILABLE` text with "Try again". 401: "Sign in to see this operator's figures."

### 5.3 Rules

- The page renders the JSON's strings and never formats, adds or compares a figure (D-5C.2). The tile bar's widths
  are the only arithmetic (`actual / max(|actual|, |target|)`).
- **Step bars (rev 4, D-5C.27).** Each step button gains a track (`.dd-wf__track`, vNEXT `.ux-wf-track`: 20 px high,
  `position: relative`, a 1 px left rule in `--border-strong`) as the row's last grid column
  at widths above 600 px, and as a full-width row under the label and value at 600 px and below (ux.css `:451`). Inside
  it, when `bar` is not null, `<span class="dd-wf__bar dd-wf__bar--{tone}" style={{ left: `${bar.left}%`, width:
  `${bar.width}%` }}>` (12 px high, top 4 px, radius 2 px; `lowers` filled with `--status-red-text`, `raises` with
  `--status-green-text`); a null `bar` leaves the track empty. Above the `<ol>`, when `scale` is not null, `<div
  class="dd-wf__scale" aria-hidden="true">` (ux.css `:597-601` under `dd-` names, aligned with the track column) with
  two marks at `left: ${scale.target_at}%` ("{totals.target_label} {totals.target}") and `${scale.actual_at}%`
  ("{totals.actual_label} {totals.actual}", the end mark, `translateX(-100%)`). Track, bar and scale are
  `aria-hidden`. No `Number(`, `parseFloat` or arithmetic on these strings.
- **No figure (rev 4, D-5C.26).** A figure slot's value takes the modifier `dd-na` (the muted style of today's
  `dd-kpi__value--na`, renamed) when its `word` is null: tiles, steps, drivers; an outcome card when `word` and
  `drawer` are both null. No test on a key or on a text.
- **Drawers (rev 4, L1, L2).** While a drawer is open: Escape and the Tab cycle are handled on `document` (vNEXT
  `uxOpen`), so they work wherever focus is; "Show all {n}" inside a drawer moves focus to the first newly shown row
  (`tabIndex={-1}`); `body` carries `dd-locked` (`overflow: hidden`), removed on close and on unmount. `inert` on
  other regions is not required (the drawers sit inside their sections; `aria-modal` holds).
- Words are text, never colour alone; negative values carry "−"; the word chip has the same text as the JSON.
- Widths: 1440 and 1280 four tiles in a row; 768 two by two; 390 one column, the tables scroll inside their own box
  (no page scroll), drawers full width.
- **Hub gates (D-5C.14; `tools/deep_dive_gates.cjs`, test 15):** the three `data-level` regions present; at most 6
  blocks; the headline at most 2 lines at 1440 × 900 and 1280 × 720 (`round(height / line-height)`), for A and for A
  with D's headline; L1's bottom within the viewport at 1440 × 900 and 1280 × 720, and the headline and status line
  within it at 390 × 844; the hub at most 2,500 px tall at 1440 with every drawer and `<details>` closed; the status
  line visible and holding `status_line`'s text; at 390 the page width equals the viewport; 0 page errors; no visible
  text under 12 px; every font size on the guide's scale (12, 13, 14, 16, 20, 24, 32 px).
- Caps (scales to 300 Sites; D-5C.22): the JSON holds every Site row; the screen shows drawer Site lists and by-Site
  tables 10 rows, then a button "Show all {n}" (`n` the array's length) that shows the rest in place; not-available
  rows 8; Actions 3 (capped by the server, `more`).
- Drivers (D-5C.21): one `<ul>` per level; a driver's `children` in a nested `<ul>` inside its `<li>`, indented one
  spacing token; every level shown, no control.
- Styling: `deepDiveMonth.css` with the live product's tokens (`frontend/mockups/v72/foundation-sheet.html`); layout
  values of vNEXT `ux.css`'s `.ux-kpis`, `.ux-kpi`, `.ux-wf*`, `.ux-drawer*` and `.ux-headline` carried over under
  `dd-` names; font sizes on the scale; no colour literal outside the token blocks (G2).

### 5.4 `tools/deep_dive_gates.cjs`

`node tools/deep_dive_gates.cjs <base-url> <fixture.json> [--plant NAME]` (Node with `/opt/assetecon/tools/pw/env.sh`
sourced; run through the slot pool). The builder serves `frontend/dist` with `npx vite preview --strictPort --port
5571` (never 5490 or 8990; stopped by PID). The script answers `/api/portfolio/month*` with the fixture through
`page.route`, opens `<base-url>/portfolio/month?month=2026-10` at 1440 × 900, 1280 × 720 and 390 × 844, each light and
dark, plus A with D's headline at 1440 and 1280 light; runs §5.3's checks on each; runs G2's static part over
`frontend/src/estate/deepDiveMonth.css` (every `px` font size on the scale; no `#hex`, `rgb(`, `hsl(` outside `:root`
and dark token blocks); prints one JSON line per view and exits 1 on any failure. **Plants** (`--plant`, applied by
`page.evaluate` after render or to the CSS text read): `block` (a visible `<div>` appended to L3), `headline` (the
headline's text repeated three times), `levels` (`data-level` removed from L2), `height` (a 3,000 px element inside
the bridge section), `fold` (an 800 px element at the top of `.dd-lead`), `status` (`.dd-status` hidden), `scroll` (a
600 px-wide element in L1, at 390), `lint` (`font-size: 11px` and `color: #123456` appended to the CSS text). Each
plant must make the script exit 1 naming its check.

## 6. Tests (written first)

**Unit 1, no database** (`backend/tests/test_5c_deep_dive_view.py`):
1. Tables: `FACTOR_LABELS` covers every factor reachable from `BRIDGE_ROOTS["MINI_GRID"]` in the registry; `HEADINGS`
   keys equal `CATEGORIES`; `STEPS` are `revenue` plus the non-neutral terms of `cost_to_serve`, and with the neutral
   terms they are all of `cost_to_serve`'s terms; `NOTE_KEYS` covers every 4d `NOTES` entry.
2. Formats: `money` of −852, 38, 0 (USD and KES), 1234567.891 (signed and not); `qty` 1180.000 → "1,180 L"; `pct0`
   1443/2295 → 63%, target ≤ 0 → none; `pct1` 0.91510 → 91.5%; `join` of 1, 2, 3 items.
3. World A against the hand-written JSON, key by key and whole. Rev 3: the headline's `evidence` is the payload's own
   word for each figure it states: for A, B, D and L1 to L4, `set(headline.evidence)` equals {`tiles[1].word`} plus the
   named heading's outcome card `word` when one is named, null words left out (D-5C.20; rev 4, D-5C.26).
4. A2, B, C (connected empty, C4), D, E, F, G, H and the lead vectors: every literal of §3.5 (rev 3: H's drivers
   nested, D-5C.21; a flattened list fails).
5. Words: §2.4 table, every row (rev 3: the `DECLARED` rows with each origin, run on `main` with SC-1f, D-5C.19); a
   "Not available yet" money figure gets no suffix. Statement case (D-5C.25): no `record` entry holds a comma outside
   brackets.
6. One contribution (D-5C.13): World A's JSON holds no "$1,693.00"; World D's `tiles`, `headline`, `bridge.totals` and
   `outcomes` hold no "$883.00"; both equal R; `month_view` never calls `actual()` or `targets()` (spies).
7. Stops: one bridge per reason of 5b §2.1 (built from 5b's unit-1 vectors and test 3's cases), each worded per §2.5.

**Unit 2** (`backend/tests/test_5c_deep_dive_api.py`, TestClient with injected reads; and
`test_5c_deep_dive_postgres.py`, pooled `--db`):
8. API: 200 body equals the fixture for World A; `?month=2026-13` 422; no tenant 503; real-data on without a person
   401, with a person of the tenant 200; `Cache-Control: no-store`.
9. Postgres, one settable clock injected as 3A7's `months.clock()`, the snapshot builder's and the read's: World A's
   records loaded through 3A1's service; S1 (finance lead; revenue 9,700.00, fuel 5,100.00) recorded at
   2026-11-19T10:00Z; the snapshot built at 2026-11-19T11:00Z; (a) read at 11:30Z: `standing` and every money word are
   A's, `as_of` "2026-11-19T11:00:00Z"; (b) S2 (fuel 5,000.00) recorded at 12:00Z, after `as_of`; read at 12:30Z: still
   A's words (D-3A7.9); (c) rebuilt at 13:00Z, read at 13:30Z: B's words. (3C2 adds the connected-Actions case, 3C2
   spec §5.)

**Unit 3** (`frontend/src/estate/__tests__/DeepDiveMonth.test.tsx`, vitest; and the gates):
10. Renders World A's fixture: every string of §3.5 appears; the notice is visible with every drawer closed; the
    status line has role status and names Kisiwa; the Assure card opens its drawer with A's standing text.
11. A step button opens its drawer (dialog, labelled), focus moves to Close, Escape closes and returns focus; the
    fuel-cost drawer of World H's JSON (A with §3.5 H's changes, written by hand) shows each driver's word chip, and
    the three parts of Diesel used sit inside its list item (D-5C.21). Caps (D-5C.22): A with `by_site.rows` and the
    revenue drawer's `sites` repeated in memory to 12 shows 10 and "Show all 12", then 12 after the click;
    `not_available.rows` at 9 shows 8 and "Show all 9".
12. NO_SNAPSHOT, REBUILD_NEEDED, 503 and 401 states; the month links set `?month=`.
13. The Overview's tab row markup (with counts) is unchanged by the move to `PortfolioTabs.tsx` (outerHTML before and
    after on the existing Portfolio fixture); "The month" is the second tab and links to `/portfolio/month`.
14. G3 captures (evidence, not committed, `/opt/assetecon/evidence/5c/unit3/`): World A at 1280 × 720, 1440 × 900 and
    390 × 844, each light and dark (six shots), plus the fuel-cost drawer open at 390; `Docs/design-system/tools/
    measure_screen.cjs` on each view, its JSON kept; 0 page errors; page width equal to the viewport; L1 at or above
    the fold; no text under 12 px.
15. `tools/deep_dive_gates.cjs` passes on World A's fixture, and each of its eight plants makes it exit 1 (shown once
    each, output in the evidence folder). Rev 4 (L5): the two D-headline views run for `--world A` only.

**Rev 4 additions** (D-5C.26 to D-5C.28):
- Unit 1 (backend fix): 3 and 4 take A's and H's bars and scale and the "Bars" vectors V1 to V6; 4 i World X (from
  `backend/tests/deep_dive_worlds.py`): shares null, no "Offsets it", bars and scale null; a gap-0 vector's shares null
  (D-5C.28); class case 16: in every figure slot of A, B, D, G, H, X and the 4 i currency worlds, `word is None` iff
  the figure is absent, and no `word` equals "Not available yet" (D-5C.26). Plants that must fail: `or Decimal(0)`
  restored; L9's card word restored; a bar computed from the rounded share instead of the effect.
- Unit 3 (screen fix): 10 gains A's bars (revenue `left: 0.00%; width: 11.38%`, fuel cost `11.38%` and `88.62%`, O&M
  and staff tracks empty) and the two scale marks; World X: no bar, no scale, no word chip reading "Not available
  yet", the contribution and gap tiles, the revenue step and the Optimize card carry `dd-na`, the Assure card does
  not. 11 gains L1 (A's revenue drawer with 12 Sites: after "Show all 12" focus is on row 11 inside the dialog; Escape
  then closes and returns focus to the opener) and L2 (`body` has `dd-locked` while open, not after). 17 (L4,
  backend, no database): `test_5c_screen_worlds_fresh.py` builds World H and World X in memory through
  `deep_dive_worlds` and compares them byte for byte with the committed frontend fixtures, failing with "rerun
  make_screen_worlds.py".

**Regression:** the Portfolio's vitest files, `test_5b_*`, `test_3a7_*`, the 3B7a tests; tsc; check-all once at the
end; `select-tests` before review.

## 7. Mock departures (each gets a row in `.agent/mock-departure-register.md`)

| # | Element | Category | Note |
|---|---|---|---|
| MD1 | k3 plan spend, k4 plan value | D1 | "Not available yet" in the tile, the tile kept (plan not built) |
| MD2 | L2 queue panel "Decisions" | D1 | the panel kept with its honest gap |
| MD3 | "Actions in hand" in the Portfolio's L2 (the Site hub's L2 block) | D2 | flagged to the owner: RC9's Action has no other place on this screen |
| MD4 | waterfall steps at heading level (revenue, fuel cost, O&M, staff) | D1 | drivers (kWh, litres) only where observed, in the step's drawer, each with its word |
| MD5 | trend lines in k1, k2 | D1 | omitted: no earlier month compared |
| MD6 | Protect card | D1 | "Not available yet" |
| MD7 | the route: a Portfolio tab "The month", not the Overview | D5 | resolving unit: IA-2's live rebuild of the Overview. The live Portfolio's six tabs against vNEXT's three predate 5c; "The month" makes seven (not a new departure) |
| MD8 | L1's status line (as of, reconciliation in a few words, budget disagreements by Site); the full reconciliation sentence and "not checked for later changes" in the Assure card's drawer | D2 | flagged to the owner (D-5C.14): the mock's L1 has the headline and tiles only |
| MD9 | "What is not available yet" as the last part of "By outcome" | D1 | honest gaps inside the mock's section; keeps the overview at 6 blocks |
| MD10 | L1 headline with its evidence word (R766) | D2 | D-5C.20; no word when the headline states no figure |
| MD11 | the bridge's per-step bars (R767) | D1 | **resolved, rev 4** (D-5C.27): bars served as positions, drawn as the mock |

## 8. Done (questions; each can fail)

1. Does World A's screen show 1,443.00 against 2,295.00, −852.00, 3 of 3, Estimated, and nowhere the uncarried
   composition (1,693.00 in A; 883.00 in D's tiles, headline, totals and cards)?
2. Is Kisiwa's disagreement named in L1's status line, and its −60.00 against −65.00 visible with every drawer closed?
3. Does every money figure read "not yet reconciled" until the organisation's standing at the snapshot's "as of" is
   reconciled, and does the Assure drawer say what did not match?
4. Does every stop and every Site left out name the records that would fill it, and every carried figure say it is
   an estimate at its budget line?
5. Is n the snapshot's Sites asked, and does each figure carry its own "k of n"?
6. Do Plan, Decisions and Protect read "Not available yet"; with `NotConnectedActions` does "Actions in hand" read "Not
   available yet" naming the Action; and does World C's row render from an injected port (newest first, at most 3)?
7. Does the headline name only a heading that widens the gap, and say when it is more than the whole gap?
8. Does every driver carry its word, with Modelled litres reading "Modelled"?
9. Does the live page meet the hub gates (regions, 6 blocks, headline 2 lines, fold, 2,500 px, 390) and G3, with
   drawers that keep and return focus?
10. Is nothing computed in the browser, and nothing changed outside §0's list, the fixtures, the tests and the packet?
11. Does each planted violation in the reviewer guide fail its named test, and is the mid-build count 0?

Packet: `specs/5c-deep-dive-screen/packet.md` (screens by path, the mid-build count).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 (1.5) | §2, §3: words, view; fixture JSON; tests 1 to 7 | 3B7a and 3A7 merged; 4d unit 2 for World H (until then H's case is skipped by name, never removed) | 1 |
| 2 (0.75) | §4: read, actions seam, route, composition; tests 8, 9 | unit 1 | 1 |
| 3 (1.25) | §5: the screen, the gates script; tests 10 to 15; check-all; packet | unit 2 | 1 to 2 |

**What the owner sees, and when:** unit 3 built on day 8 and reviewed by day 10; the owner walks it on day 11 on the
rehearsed Lakeside tenant (DDR), served by the coordinator, then decides the merge (`two-week-build-plan.md` §0.2).

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Where the screen lives in the live product before IA-2 rebuilds the Overview | A Portfolio tab "The month" (`/portfolio/month`), MD7 |
| Q2 (owner) | An operator's real figures before the sign-in page exists (RC4 with RC7) | On a real-data server the route needs a signed-in person of the tenant (D-5C.7); this fortnight the owner presents on the rehearsed (emulated) tenant |
| Q3 (owner) | "Actions in hand" on the Portfolio (MD3, D2) | Kept: the agreed change is the deep-dive's outcome |
| Q4 | The waterfall's steps | Headings (D-5C.5); drivers in the drawer |
| Q5 | Words for emulated and simulated figures | "Emulated", "Simulated"; never "Recorded" (D14, D-5C.3) |
| Q6 (owner) | "Not yet reconciled" on cash and estimated figures too | Yes: 3A7 marks every money figure (D-5C.4) |
| Q7 (owner) | L1 carries a status line (as of, reconciliation, budget disagreements) and the full reconciliation sentence moves to the Assure drawer (MD8) | Yes (D-5C.14): the executive sees the three facts before scrolling within the hub budget |
| Q8 | Site-level reconciliation words on the by-Site rows | No: one organisation standing for the screen (D-5C.4 amended); Site statements are not part of the deep-dive |
| Q9 | A 5b or 5c rule change marking served figures out of date | Not this fortnight (D-5C.18): rebuild after every deploy; 3B7b adds the roots |
| Q10 | SC-1's inline and `served` paths ignore `Evidence.reconciled` (only `with` honours it) | Queued to SC-1's next unit: `figure_word` becomes the one path. Nothing reads wrong today (no producer sets `reconciled` on an inline or served figure); 5c maps its own words (D-5C.20) |
| Q11 (owner) | The carried cell's label | " (at budget)" (D-5C.23; OWNER-AWAY row 61); 5b's carry rule unchanged |
| Q12 (owner) | A figure with none: "Not available yet" as the value and again as its chip? | Once, as the value, muted, no chip (D-5C.26; OWNER-AWAY row 68; revises L9) |
| Q13 (owner) | The bridge without per-step bars (MD11) for the walkthrough? | No: bars as the mock, served as positions, before the walkthrough (D-5C.27; OWNER-AWAY row 69) |
| Q14 | A step's share when the gap is not available or 0 | None shown (D-5C.28, M1) |

## 11. Rev 4 fix scopes (D-5C.26 to D-5C.28)

**Backend fix** (Status: in_review, 2026-11-21, branch `fix/5c-backend-r5`, `packet-backend-fix-r5.md`) (new branch off `main`, about 0.5 unit, one commit; Sonnet per the fix-round rule; files in
`backend/` only):
1. `deep_dive/view.py` `shares()`: return `{}` when `self.R.effect` is None or 0; delete `or Decimal(0)` (D-5C.28).
2. `view.py` `figure_word(value, currency, ev, origins)`: None when `value` or `currency` is None, else `W.word(ev,
   origins, standing, currency)`. Used for tiles[0] (R.actual), tiles[1] (R.effect), steps (row.effect, row.currency;
   row absent: None), drivers (row.effect, row.currency), grow and optimize cards (group sum, `group_cur`; the L9 line
   `:597-598` goes), cash (root.actual, root currency) and the headline's `evidence` (D-5C.20's path, unchanged in
   effect). `words.py`: `word(..., currency: str)`, `NO_CURRENCY` deleted (D-5C.26).
3. `view.py` `bridge_bars` per §3.2; each step gains `bar` (key order `key, label, value, share, word, sites, bar,
   drawer`); `bridge` gains `scale` after `totals`. Schema stays `deep-dive-month-1` (the screen has not merged).
4. `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` edited by hand with A's bars and scale (W2, never by
   running `month_view`).
5. `backend/tests/deep_dive_worlds.py` (new, test support, no database): `world_h()` (`view("H")`) and `world_x()`
   (the World X `site_bridge` patch now in the screen branch's `make_screen_worlds.py`, applied and undone inside the
   function), with public `in_kes` and `gone` moved from `test_5c_deep_dive_view.py`. `test_4_i_currency_card_word_
   beside_no_figure` uses `world_x()` and now asserts the card's `word` null.
6. Tests per §6 "Rev 4 additions", unit 1. Then focused tests, `test_5b_*`, `test_3a7_*`, check-all (fast) through
   the slot. Review: a fresh reviewer, verification depth on D-5C.26 to D-5C.28.

**Screen fix** (on `task/5c-unit3-screen` after the backend fix merges, about 0.5 unit, one or two commits):
1. Merge `main`. Rewrite `make_screen_worlds.py` to call `deep_dive_worlds.world_h()` and `world_x()` only (no
   private helpers, no patch of its own); regenerate both frontend fixtures.
2. L4: `backend/tests/test_5c_screen_worlds_fresh.py` (§6 item 17). It lands here because the generator and the files
   it checks exist only on this branch.
3. D-5C.26's page rule (`dd-na`), `startsWith("plan")` deleted (L3).
4. D-5C.27's track, bar and scale (§5.3), the `DeepDiveMonth` types gaining `bar` and `scale`; register row R767 set
   to resolved (D-5C.27).
5. L1 and L2 (§5.3 "Drawers"). L5 (§6 item 15).
6. Tests per §6 "Rev 4 additions", unit 3; vitest, tsc, vite build; gates on A, X and H (the hub height and the 390
   width with the track rows); the shots of test 14 retaken for A at 1440 and 390 and X at 1440; check-all once.
   Re-review: a fresh reviewer, verification depth on these items; the merge waits for the owner's walkthrough.

## 12. Rev 5 fix scope (D-5C.29, the cash sentence)

**Backend fix** (new branch `fix/5c-cash-r6` off `main`; about 0.25 unit, one commit; Sonnet per the fix-round rule;
files in `backend/` only; tests first). The screen prints `cash.text` and the table verbatim, so no frontend code
changes. The screen branch (`task/5c-unit3-screen`) regenerates its two frontend fixtures with
`make_screen_worlds.py` when it next merges `main`.

1. `deep_dive/view.py`, module level, pure and public:
   `cash_parts(rows: Mapping[str, PortfolioRow]) -> tuple[PortfolioRow, PortfolioRow, PortfolioRow] | None`.
   It returns `(rows[T.REVENUE], rows[T.IN_TRANSIT], rows[T.OUTSTANDING])` only when all of these hold:
   - root = `rows[T.CASH]` has `actual` and `currency` not None;
   - each part is present, with `actual` not None and `currency == root.currency`;
   - each part has `{c for c, _ in part.out} == {c for c, _ in root.out}`;
   - `root.actual == revenue.actual - in_transit.actual - outstanding.actual`.

   Otherwise it returns None. Import `PortfolioRow` from `structure.attribution.portfolio`.
2. `view.py` `MonthView.cash()`:
   - `parts = cash_parts(rows)`.
   - Sentence: `W.cash(self.month, m(root), tuple(m(p) for p in parts) if parts else None)`.
   - Total, in column order Billed, Collected, In transit, Outstanding: `[W.sites(root.k, self.n), a(parts[0]),
     a(root), a(parts[1]), a(parts[2])]`; when `parts` is None, `[W.sites(root.k, self.n), a(None), a(root),
     a(None), a(None)]` (`a(None)` is already "Not available yet").
   - Per Site, Billed is `_find(cash_root, T.REVENUE)` (the cash tree), replacing `_find(roots[T.ROOT],
     T.REVENUE)`. `self.rows.get(T.REVENUE)` and the root's `target` are no longer read in `cash()`.
3. `deep_dive/words.py`: `cash(month, collected: Money | None, parts: tuple[Money, Money, Money] | None)`, where
   `parts` is (billed, in_transit, outstanding). It passes the slots `billed`, `in_transit` and `outstanding`
   only when `parts` is given. The `expected` slot is deleted.
4. `i18n/statements/en/deep_dive.py` `deep_dive.cash` (evidence `served`, unchanged). Slots: `month`; `collected`
   (money, absent NOT_AVAILABLE); `billed`, `in_transit` and `outstanding` (money, optional). Variants in this
   order:
   - `not_available`, when collected is absent: unchanged.
   - `cash`, when billed, in_transit and outstanding are all present: "Of {billed} billed for {month}, {collected}
     has been collected, {in_transit} is paid but in transit and {outstanding} is still outstanding."
   - `collected_only`, the last variant, with no `when`: "{collected} has been collected on the bills for {month};
     the amounts billed, in transit and still outstanding are not available for the same Sites yet."
5. `backend/tests/statement_cases/deep_dive.py`:
   - case `cash`: collected 9000.00, billed 9700.00, in_transit 200.00, outstanding 500.00, which gives "Of
     $9,700.00 billed for October, $9,000.00 has been collected, $200.00 is paid but in transit and $500.00 is
     still outstanding."
   - a new case `collected_only`: collected 9000.00, which gives "$9,000.00 has been collected on the bills for
     October; the amounts billed, in transit and still outstanding are not available for the same Sites yet."
     The case's evidence is the same EV as `cash`.
6. Fixture `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`, edited by hand (W2): `cash.text` reads "Of
   $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in transit and $668.00 is still
   outstanding." The table is unchanged.
7. Tests, written first, in `backend/tests/test_5c_deep_dive_view.py`:
   - (a) Test 3's literal is World A's new text.
   - (b) **Class test** `test_cash_sentence_reconciles`, over A, D, E, G, H, X and the five `CURRENCY_WORLDS`.
     Parse the money tokens of `cash.text` in order (`(?:KES |\$)[\d,]+\.\d\d`). With four tokens (b, c, t, o), b
     == c + t + o, and the table total's cells [1:5] are the same four strings in column order. With one token
     (the `collected_only` variant) or none (`not_available`, as in X), total [1], [3] and [4] read "Not available
     yet". Two or three tokens fail. "expected" appears nowhere in the payload.
   - (c) Literals:
     - D and the `sides` world: "Of $7,528.00 billed for October, $6,980.00 has been collected, $0.00 is paid but
       in transit and $548.00 is still outstanding." Total ["2 of 3 Sites", "$7,528.00", "$6,980.00", "$0.00",
       "$548.00"].
     - Subset world: the same sentence in KES, and total ["2 of 3 Sites", "KES 7,528.00", "KES 6,980.00", "KES
       0.00", "KES 548.00"]. Before the fix its Billed total read "Not available yet". Mto's row is ["Mto", "Not
       available yet", "$1,890.00", "Not available yet", "Not available yet"]: the plant removes Mto's cash
       tree's rows.
   - (d) `cash_parts` vectors on hand-built `PortfolioRow`s:
     - collected 100, revenue 120, in transit 0, outstanding 10 (does not reconcile) gives None;
     - the same with outstanding 20 gives the three rows;
     - outstanding whose `out` holds a Site the root's does not gives None;
     - a part in KES under a USD root gives None;
     - a missing `in_transit` row gives None.
8. Plants (each applied to `view.py`, run on the view file, reverted with `git checkout`):
   - C1: the sentence's billed slot fed `root.target`. Test (b) fails (9,785 ≠ 9,688) and so does (a).
   - C2: the identity check deleted from `cash_parts`. Test (d)'s first vector fails.
   - C3: the total's Billed back to `self.rows.get(T.REVENUE)`. Test (c)'s subset total fails.
   - C4: the per-Site Billed back to the contribution tree. Test (c)'s Mto row fails.
9. Checks: the focused set of the r5 packet (`test_5c_deep_dive_view.py`, `test_5c_deep_dive_api.py`, `test_5b_*`,
   `test_3a7_*`), the statement catalogue load (`test_sc1_statements.py`; the deep-dive cases run in `test_5c_deep_dive_view.py`), and check-all (fast) through the slot. Packet
   `specs/5c-deep-dive-screen/packet-backend-fix-r6.md`. Review: a fresh reviewer, verification depth on D-5C.29.

**Done (questions).** Does every cash sentence the view can produce either state four figures where billed equals
collected + in transit + outstanding, or state one figure? Do the sentence and the total row print the same four
strings? Does any cash figure come from outside the cash tree? Does "expected" appear anywhere?
