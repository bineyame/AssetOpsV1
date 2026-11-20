# 5c: the month, explained (the one deep-dive screen; implementer spec)

Status: rev 1, Architect (Claude), 2026-11-20, re-scoped by D-BW1.9 and D-BW1.12. Handshake not started
(`handshake.md`). UI lane, after the IA-1 stop (RC6). **3 units.** `USER_REVIEW_REQUIRED: true` (the screen the
executive sees). Discovery review (W5): money figures on screen.
- **Structure:** P5 (`specs/5a-targets/structure-page-P5.md`, approved 20 Nov) rules 2, 7 and 8; D-5B.10, D-5B.12,
  D-5B.15 (5c inherits them); D-3A7.9 (the standing at the snapshot's "as of"); 3B7a ruling 15 on
  `task/3B7a-snapshot` (n is every Site asked: `len(snapshot.asked)`); RC5 (mini-grid only), RC7 (the owner
  presents; the executive does not sign in), RC9 (the first agreed change is an Action, not valued).
- **Mock (§6 of `.ai/RULES.md`):** vNEXT `#/portfolio` in the hub shape (IA-1b, `specs/IA-1-shape-rebuild/spec.md`
  §3.1 and §3.2 row `portfolio`): L1 the headline and four tiles (`loop-ux.js` `uxOverviewParts` k1 to k4), L2 the
  queue panel, L3 "Where the gap comes from" (`uxBridge`, with "Show as table, by Site") and "By outcome"
  (`uxCats`), drawers only inside sections. Walkthrough `walkthroughs.md` §2 steps 1 to 3: "the month in one line",
  "Cash collected, outside the contribution gap", Assure's "Contribution's bridge by heading". Departures: §7.
- **UI standing brief** (`owner/owner-ui-standing-brief-2026-11-20.md`): one control per content kind (drawer for a
  figure's detail, disclosure for a table), one interaction grammar, scales to 300 Sites (caps, §5.5), simplicity by
  design, every number with its basis. `Docs/design-system/uiux-guide.md` G2 to G4 gate the review.
- **Builds on:** `5b` (`site_bridge`, `portfolio_bridge`, `BridgeRow`, `PortfolioRow`, `lowest`, `BRIDGE_ROOTS`,
  `CARRY_AT_TARGET`), `3B7a` (`SnapshotRead`, `Served`, `PortfolioMonthSnapshot`, `Freshness`; must be merged),
  `3A7` (`CommercialReconciliation.standing`, `money_word`, `build_commercial_reconciliation`; must be merged),
  `3B1` (`REGISTRIES`, `parsed`, `CATEGORIES`), the live frontend's Portfolio (`estate/EstatePortfolio.tsx`,
  `estate/portfolioWords.ts`, `sites/temporarilyUnavailable.ts`), `ON1` (served tenant; `site_registry`).
- **Decisions:** `rulings.md` (D-5C.1 to D-5C.12). **Reviewer guide:** `reviewer-guide.md`.

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
  `deepDiveMonth.css`, `deepDiveMonthClient.ts`, `PortfolioTabs.tsx`. Edited: `main.py` (one router include),
  `App.tsx` (one route), `estate/portfolioWords.ts` (one tab), `estate/EstatePortfolio.tsx` (the tab row moves to
  `PortfolioTabs.tsx`, unchanged markup; a `month` tab redirects).

## 1. Outcome and why

The owner opens `/portfolio/month` on the operator's served tenant and walks the executive through one screen: the
month's contribution against their own target, the gap split by heading, Site by Site, cash apart, every figure with
its evidence word and "not yet reconciled" until a closed month matches their management accounts; Kisiwa's budget
disagreement shown, not hidden; every gap in the data named with the record that would fill it; and the change they
agree recorded as an Action with its owner and due date (RC9). Every figure is the bridge's (D-5B.12). Nothing on the
screen is computed in the browser (D-5C.2).

Gate questions: does the screen show 1,443.00 against 2,295.00, −852.00, 3 of 3, Estimated, for Lakeside's October,
and never 883.00? Is Kisiwa's −60.00 against −65.00 on the screen without opening anything? Does every money figure
read "not yet reconciled" until the standing at the snapshot's "as of" is reconciled? Does every stop name its
records?

## 2. Words and formats (`deep_dive/words.py`; unit 1)

### 2.1 Formats (`Context(prec=34, rounding=ROUND_HALF_EVEN)`)

- **Money** `money(v, cur, signed=False)`: `q = v.quantize(Decimal("0.01"))`; magnitude `f"{abs(q):,.2f}"`; prefix
  `$` for USD, else `f"{cur} "`; negative `"−"` (U+2212) before the prefix; `signed` and positive `"+"`; zero
  `"$0.00"` with no sign; never `-0`.
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
cost · `diesel_l` Diesel used · `necessary_l` Diesel needed to serve the load · `candidate_l` Diesel run while solar
and battery could carry the load · `unexplained_l` Unexplained fuel · `extra_l` Extra diesel from a change ·
`diesel_price` Diesel price · `om` O&M · `staff` Staff · `collection_cost` Collection cost · `battery_wear` Battery
wear · `battery_throughput_kwh` Battery throughput · `wear_rate` Battery wear rate · `collected` Cash collected ·
`in_transit` Paid, in transit · `outstanding` Outstanding.
`lower(label)`: the label unless it starts `O&M`, else its first letter lower-cased.
`HEADINGS = {"GROW_REVENUE": "Grow revenue", "OPTIMIZE_COST": "Optimize cost and efficiency", "PROTECT_ASSET":
"Protect asset and capital", "ASSURE_RETURNS": "Assure performance and returns"}`, keyed by `CATEGORIES`' four names
(test 1 asserts the keys equal `CATEGORIES`; rename the keys to `CATEGORIES`' names if they differ, never the words).

### 2.3 The records that fill a gap (`RECORDS`, this order; `RECORD_KEYS` per leaf; `NOTE_KEYS` per 4d note)

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
| SITE_SETUP | the Site's generator and fuel tank, declared in its setup |
| ANALYSING | the running record's analysis, still in progress |
| MONTH_CLOSE | the month to close |
| BUDGET_LINES | (built: `"a budget line for " + x` or `"budget lines for " + join(xs)`, `xs` the leaves' `lower(label)`) |

`RECORD_KEYS`: `revenue`, `billed_kwh` (BILLING); `adjustments_kwh` (BILLING_ADJUSTMENTS); `delivered_kwh`
(FEEDER_METER); `technical_loss_kwh`, `unexplained_loss_kwh` (FEEDER_METER, METER_REGISTER); `unmapped_kwh`
(METER_REGISTER); `tariff` (TARIFF_SHEET); `productive_kwh` (PRODUCTIVE_LINES); `productive_tariff`
(PRODUCTIVE_TARIFF); `in_transit` (SETTLEMENTS); `outstanding` (RECEIPTS); `necessary_l`, `candidate_l` (EMS,
FUEL_CURVE); `unexplained_l` (EMS, FUEL_CURVE, TANK_DIPS, FUEL_DELIVERIES); `fuel_cost`, `diesel_price`
(FUEL_INVOICES); `om` (OM_INVOICES); `staff` (PAYROLL). `NOTE_KEYS` (an actual leaf whose `missing.note` is one of
these adds its key to the leaf's `RECORD_KEYS`; ANALYSING and MONTH_CLOSE replace them instead): `GENERATOR_OR_TANK_NOT_DECLARED` (SITE_SETUP); `NO_RUNNING_RECORD`, `RUNNING_RECORD_GAP`,
`GENERATOR_USE_INCOMPLETE` (EMS); `FUEL_CURVE_MISSING`, `NO_LOAD_RATE_MISSING` (FUEL_CURVE); `TANK_DIPS_MISSING`,
`TANK_DIPS_CONFLICT` (TANK_DIPS); `DISPATCH_NOT_ASSESSED`, `SPANS_OVERLAP` (ANALYSING); `MONTH_OPEN` (MONTH_CLOSE).

**needs(site_bridge, actual_leaves, target_leaves)**: the record keys of the actual leaves (as `NOTE_KEYS` says),
distinct, in `RECORDS` order, as their words; then, when `target_leaves` is non-empty, the
BUDGET_LINES phrase over them in registry order; all joined with `join`.

### 2.4 The evidence word (D-5C.3; 3A5's rule on this screen only, D-BW1.9)

`word(evidence, origins)`: `NOT_AVAILABLE` → "Not available yet"; `ESTIMATED` → "Estimated"; `MODELLED` →
"Modelled"; otherwise by `weakest_origin(origins)`: `source-emulated` → "Emulated"; `demo-simulated` → "Simulated";
`unknown` or none → "Estimated"; `observed-financial`, `field-integrated`, `bench-tested` → by evidence: `RECORDED`,
`DECLARED` "Recorded", `MEASURED` "Measured", `DERIVED` "Calculated". A **money** figure's word is
`money_word(word, standing)` (3A7) unless it is "Not available yet" (D-5C.4). A figure never shows "Verified".

### 2.5 Sentences (exact; `{…}` filled by §2.1's formats)

| Key | English |
|---|---|
| headline | Contribution is {abs gap} {below\|above} target in {month_name}; {cost and efficiency explain\|Grow revenue explains} {abs big} of it. |
| headline_on | Contribution is on target in {month_name}. |
| headline_na | Contribution for {month_name} is not available yet. |
| headline_k | (appended when k < n) Compared for {k} of {n} Sites. |
| tile1_target | Target {target} · {pct0} of target (the `· …` part only when `pct0` applies) |
| tile1_cost | {pct1} of cost rests on records |
| tile2_split | Grow {grow signed} · Optimize {optimize signed} |
| tile2_rest | All of it split to its drivers \| {abs rest} of it not split to its drivers yet |
| tile3 | label "Plan spend", value "Not available yet", line "No plan has been made yet" |
| tile4 | label "Plan value, 12 months", value "Not available yet", line "Each change is valued against doing nothing once decisions are recorded" |
| disagreement | {site}'s budget states {a\|an} {lower(label)} of {stated}; its budget lines add to {computed}. The target used is {computed}. |
| bridge_title | {Cost and efficiency explain\|Grow revenue explains} {abs big} of the {abs gap} gap. Open a step for what is behind it. |
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
| cash | In {month_name}, {collected} was collected against {expected} expected; {outstanding} is still outstanding and {in_transit} is paid but in transit. |
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
| outcome cards | grow: line "Revenue against target, {sites}"; optimize: "Fuel, O&M and staff against target; cash collected is shown apart"; protect: value "Not available yet", line "Limits, warranties and rights are not set up yet"; assure: value "Reconciled" or "Not yet reconciled", line "{n} budget disagreement(s) · {tile1_cost}" ("No budget disagreement" when 0; "1 budget disagreement", "2 budget disagreements") |
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
    connected: bool; actions: tuple[AgreedAction, ...]     # oldest first

def month_view(*, operator: str, month: str, served: Served, standings: Callable[[UUID | None], Standing],
               actions: AgreedActions, names: Mapping[str, str], now: datetime) -> dict
```
`standings(None)` is the organisation's, `standings(site_id)` a Site's; the caller reads them at `served.as_of`
(D-3A7.9). `names`: Site code to display name (absent: the code).

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
| `standing` | `{"reconciled", "reason", "text"}` of `standings(None)` |
| `headline` | §2.5 from the root row `R = pb.rows["contribution"]["contribution"]`; `grow` = the GROW_REVENUE steps' effects summed, `optimize` the OPTIMIZE_COST ones; `big` the larger in magnitude (ties: optimize) |
| `tiles` | four objects `{"key", "label", "value", "word", "lines", "bar"}`: `contribution` (R's actual; lines tile1_target, `sites(R.k, n)`, tile1_cost; bar `{"actual", "target"}` plain decimals), `gap` (R's effect signed; lines tile2_split, tile2_rest), `plan_spend`, `plan_value` (word null, bar null) |
| `notices` | one `disagreement` sentence per `pb.disagreements` entry, `asked` order |
| `bridge` | `{"title", "totals", "groups", "by_site"}` (§3.2) |
| `cash` | `{"title": "Cash collected, outside the contribution gap", "text", "word", "sites", "table"}` (§3.3) |
| `outcomes` | the four cards, `HEADINGS` order (§2.5) |
| `decisions` | `{"title": "Decisions", "text": decisions}` |
| `actions` | `{"title": "Actions in hand", "connected", "text", "rows"}`: not connected `actions_off`, rows []; connected and none `actions_none`; else text null and one row per Action (oldest first, at most 3, `"more": n − 3` when over) |
| `not_available` | `{"rows": [{"needs", "fills", "sites"}], "not_built": not_built}` (§3.4) |

**tile1_cost** = `(C.actual − Σ carried) / C.actual` with `C = pb.rows["contribution"]["cost_to_serve"]` and `Σ
carried` the actual values of every carried leaf of every included Site (`sb[c].actual.values[leaf].value` for leaf in
`sb[c].carried`); omitted when `C.actual` is None or 0. **tile2_rest** = Σ over included Sites of the effects of
`lowest(sb[c].roots["contribution"])` rows with split `NOT_SPLIT` or kind `RESIDUAL`.

### 3.2 The bridge

- `totals`: `{"actual_label": "Contribution, {month_name}", "actual", "target_label": "Target", "target"}` from R.
- `groups`: per home present among the steps, `CATEGORIES` order: `{"key", "label": HEADINGS[key], "value": Σ step
  effects signed, "steps": [...]}`. A step: `{"key", "label", "value" (effect signed, or "Not available yet" when
  the row is absent or its effect None), "share", "word", "sites", "drawer"}`; `share` against the steps whose effect
  has the gap's sign (`round(|e| / Σ|those| × 100)` half even); `word` §2.4 (money).
- `drawer`: `{"title", "lines", "sites", "carried", "out", "lines_org", "drivers"}`: `lines` drawer_values (when it
  applies), drawer_effect, `sites(k, n)`; `sites` one entry per included Site in `asked` order (at most 10, then
  `"more"`): `{"site", "value": that Site's row effect signed, "text": the stop sentence of that row or of its
  lowest descendants that stop (each once, in tree order, joined by a space), null when none}`; `carried` §2.5 per
  `PortfolioRow.carried` Site; `out` §2.5 per `PortfolioRow.out` entry (target from that Site's own root when it has
  one); `lines_org` `portfolio_line` per `pb.portfolio_lines` line whose factor is the step; `drivers`: the
  portfolio rows whose key is a registry descendant of the step (and `residual:<x>` rows under it), in `pb.rows`
  order: `{"label", "value", "sites", "detail"}` with `detail` "Actual {a} · Target {t}" (qty, price or money by
  unit) when both are present, else null.
- `by_site`: `{"columns": ["Site", "Contribution", "Target", "Gap", <step labels>], "rows", "total"}`: per asked Site
  (at most 10 shown first; `"more"` the rest) its root actual (unsigned), target, gap and step effects (signed), a step
  cell suffixed `" (estimate)"` when that Site's row is `carried`; only MINI_GRID Sites have rows; a Site not in R's k reads its root actual or "Not
  available yet", its own target, then "Not compared" in the other cells; `total`: `sites(R.k, n)`, R's actual,
  target, effect, then each step's effect.

### 3.3 Cash

From `pb.rows["collected"]`: `collected` root (actual, target as `expected`), `in_transit` and `outstanding` rows'
actuals, `revenue`'s actual. `word` §2.4 of the root (money); `sites` of the root. `table`: columns `["Site",
"Billed", "Collected", "In transit", "Outstanding"]`, rows per asked Site from `sb[c].roots["collected"]` (unsigned
money; "Not available yet" for an absent value), total from the portfolio rows.

### 3.4 What is not available yet

Over every included and out Site (asked order), every row of both roots (depth first): the row's `unobserved_actual`
(actual leaves) and `unobserved_target` (target leaves); and every carried leaf (its record key; `fills` gets
" (taken at its budget line meanwhile)"). Group by record key (actual: as `NOTE_KEYS` says; target: one
`BUDGET_LINES` row): `needs` the key's words (BUDGET_LINES: its phrase over all target leaves seen), `fills`
`join` of the leaves' labels in registry order, `sites` `join` of names. Rows in `RECORDS` order. At most 8 rows shown;
the rest behind "Show all {n}" in the screen (the JSON holds all).

### 3.5 Fixtures (hand-computed; the tests write these literals, W2)

**World A.** 5b §5.2's world with its step (3A4 `new_world()`, 4b's `money_leaves_lakeside.json`, 5a's
`targets_lakeside.json` steps 1 and 2, 5b's `attribution_lakeside_mto.json`), snapshot built in memory by 3B7a's
`SnapshotBuilder` at `AS_OF = 2026-11-20T08:00:00Z` over Kobo, Kisiwa, Mto (n = 3), served by `SnapshotRead` with
clock `AS_OF`. `operator` "Lakeside Power"; `names` {KOBO-001 Kobo, KISIWA-001 Kisiwa, MTO-001 Mto}; `now = AS_OF`;
`standings` a literal Standing for every scope: `reconciled` False, `reason` THIS_MONTH_NOT_MATCHED, `text` "Not yet
reconciled: October 2026 (the organisation) does not match the management accounts within 1%. Fuel cost: the accounts
say 5,100.00 USD and the records say 4,995.00 USD, 105.00 less (2.06%), beyond the 51.00 allowed (1%)." (3A7's text
for an organisation statement of revenue 9,700.00 and fuel cost 5,100.00 against recorded 9,688.00 and 4,995.00);
`actions` `AgreedActions(False, ())`.

**Expected A** (every string exact):
- `nav` {"previous": "2026-09", "next": null}; `state` SERVED; `as_of_text` "Figures as of 20 November 2026, 08:00
  UTC."; `fresh` {"current": true, "text": null, "untracked_text": null} (`untracked` is () in this world; a run that
  differs is a mid-build question).
- `headline` "Contribution is $852.00 below target in October; cost and efficiency explain $755.00 of it."
- `tiles[0]` Contribution, "$1,443.00", word "Estimated, not yet reconciled", lines ["Target $2,295.00 · 63% of
  target", "3 of 3 Sites", "91.5% of cost rests on records"], bar {"actual": "1443.00", "target": "2295.00"}.
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
  "3 of 3 Sites"]; sites Kobo "+$38.00", Kisiwa "−$55.00", Mto "−$80.00", each text "Not split further until billing
  adjustments (credit notes), a feeder meter export, a meter register with change dates, the tariff sheet, the
  productive-use tariff and budget lines for energy delivered, tariff and productive-use price."; drivers [].
- fuel_cost drawer lines ["Actual $4,995.00 · Target $4,240.00 · Difference +$755.00", "Effect on contribution
  −$755.00", "3 of 3 Sites"]; sites Kobo "−$600.00", Kisiwa "−$130.00", Mto "−$25.00", each "Not split further until
  the EMS interval export (generator running and output, solar available power, battery charge), the generator's fuel
  curve (litres per kWh; litres per hour idle), tank dips at the start and end of the month and fuel delivery notes."
- om drawer lines ["Actual $1,800.00 · Target $1,800.00 · Difference $0.00", "Effect on contribution $0.00", "3 of 3
  Sites"]; carried ["Kisiwa: no service contractor invoice received; taken at its budget line for the month
  (estimate)."]. staff drawer lines ["Actual $1,450.00 · Target $1,450.00 · Difference $0.00", …]; lines_org ["The
  organisation's budget also states $1,200.00 for staff that no Site carries; it is listed, not added."].
- by_site rows: Kobo "$883.00", "$1,445.00", "−$562.00", "+$38.00", "−$600.00", "$0.00", "$0.00"; Kisiwa "−$250.00",
  "−$65.00", "−$185.00", "−$55.00", "−$130.00", "$0.00 (estimate)", "$0.00"; Mto "$810.00", "$915.00", "−$105.00",
  "−$80.00", "−$25.00", "$0.00", "$0.00"; total "3 of 3 Sites", "$1,443.00", "$2,295.00", "−$852.00", "−$97.00",
  "−$755.00", "$0.00", "$0.00".
- cash text "In October, $8,870.00 was collected against $9,785.00 expected; $668.00 is still outstanding and $150.00
  is paid but in transit."; word "Estimated, not yet reconciled"; rows Kobo "$3,458.00", "$3,180.00", "$0.00",
  "$278.00"; Kisiwa "$4,070.00", "$3,800.00", "$0.00", "$270.00"; Mto "$2,160.00", "$1,890.00", "$150.00",
  "$120.00"; total "3 of 3 Sites", "$9,688.00", "$8,870.00", "$150.00", "$668.00".
- outcomes: grow "−$97.00" "Emulated, not yet reconciled" "Revenue against target, 3 of 3 Sites"; optimize
  "−$755.00" "Estimated, not yet reconciled" (the weakest of its steps); protect; assure "Not yet reconciled", "1
  budget disagreement · 91.5% of cost rests on records".
- `not_available.rows` (needs · fills · sites; all three Sites unless named): billing adjustments (credit notes) ·
  Billing adjustments; a feeder meter export · Energy delivered, Technical losses and Unexplained losses; a meter
  register with change dates · Technical losses, Unexplained losses and Energy on unmapped meters; the tariff sheet ·
  Tariff; the productive-use tariff · Productive-use price; the EMS interval export (…) · Diesel needed to serve the
  load, Diesel run while solar and battery could carry the load and Unexplained fuel; the generator's fuel curve (…) ·
  the same three; tank dips at the start and end of the month · Unexplained fuel; fuel delivery notes · Unexplained
  fuel; the service contractor's invoices · O&M (taken at its budget line meanwhile) · Kisiwa; budget lines for energy
  delivered, tariff and productive-use price · Energy delivered, Tariff and Productive-use price. Sites "Kobo, Kisiwa
  and Mto".

**B (reconciled).** A with `standings` `reconciled` True, `RECONCILED`, "Reconciled: October 2026 (the organisation)
matches the management accounts within 1%.": every ", not yet reconciled" suffix gone; assure "Reconciled".
**C (an agreed change).** A with `AgreedActions(True, (AgreedAction("A-1", "Lower the generator stop setting at Kobo to
70% battery charge", "KOBO-001", "candidate_l", "Peter", "Amina", 2026-11-20T09:30Z, 2026-12-15, "Open"),))`: rows
[{"title": "Lower the generator stop setting at Kobo to 70% battery charge", "owner": "Owner Peter · due 15 December
2026", "agreed": "Agreed by Amina on 20 November 2026", "state": "Open"}], text null. Connected and empty:
"No change has been agreed yet."
**D (Mto's records missing).** 5b §5.2 without its step: headline "Contribution is $747.00 below target in October;
cost and efficiency explain $730.00 of it. Compared for 2 of 3 Sites."; tile1 lines ["Target $1,380.00 · 46% of
target", "2 of 3 Sites", "89.8% of cost rests on records"]; tile2 ["Grow −$17.00 · Optimize −$730.00", "$747.00 of
it not split to its drivers yet"]; revenue drawer `out` one line starting "Mto: not compared until the billing export"
and ending "; its own target is $915.00."; by_site Mto row "Not available yet", "$915.00", then "Not compared" × 5.
**E (out of date).** A, then 3B7a §5's `LATE` invoice ingested at 2026-11-21T09:00Z and the read clock and `now`
2026-11-21T10:00Z, no rebuild: figures as A; `fresh.current` false, text "These figures are out of date: records have
arrived since they were prepared for Kisiwa. They are shown as they were on 20 November 2026, 08:00 UTC."
**G (another type asked).** A with 3B7a §5's `THIKA-001` (COLDCHAIN) asked last: headline A's plus " Compared for 3
of 4 Sites."; tile1 lines[1] "3 of 4 Sites"; every step's `sites` "3 of 4 Sites" and its drawer `out` ["Thika: not a
mini-grid Site, not included."] (`names` gains THIKA-001 Thika); `by_site` lists the three mini-grid Sites only.
**F.** Month 2026-09: NO_SNAPSHOT, `state_text` "The figures for September 2026 have not been prepared yet.", `nav`
{"previous": "2026-08", "next": "2026-10"}. A row with `format` 0 written to the store: REBUILD_NEEDED, "The figures
for October 2026 must be prepared again before they can be shown."

The tests write A as `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json` **by hand from this section** (never
by running `month_view`); unit 3's frontend tests render the same file.

## 4. The read and the route (unit 2)

### 4.1 `deep_dive/read.py`

`DeepDiveRead(snapshots: SnapshotRead, reconciliation: CommercialReconciliation, actions: AgreedActionsPort, clock)`.
`month(tenant: TenantRef, month: str | None, names) -> dict`: `month` None is the calendar month before `clock()`'s
UTC month; a month not fullmatching `[0-9]{4}-(0[1-9]|1[0-2])` raises `ValueError("BAD_MONTH")`; `served =
snapshots.portfolio(tenant.id, month)`; standings memoised per scope within the call: `reconciliation.standing(
tenant.id, site_id, month, known_at=served.as_of)` (D-3A7.9; not read when not SERVED); `actions.for_tenant(tenant.id)`;
`month_view(...)` with `now = clock()`.

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
**Contract for 3C2's spec (binding on it):** `actions/agreed.py` implements `AgreedActionsPort` over 3C2's Action
records (every Action of the tenant created by a person, open or not, oldest first; names from the accounts service;
`state_words` 3C2's own words), with `build_agreed_actions(database_url)`; and a command `python -m
assetops_backend.record_action --tenant SLUG --as EMAIL --title TEXT --owner EMAIL --due YYYY-MM-DD [--site CODE]
[--factor ID]` that prints the Action as one JSON line (exit 0). 3C2 replaces `NotConnectedActions()` in
`deep_dive/composition.py` with it (one line) and adds 5c test 9(c).

## 5. The screen (unit 3; `frontend/src/estate/DeepDiveMonth.tsx`)

### 5.1 Route, tab and client

- `App.tsx`: `<Route path={DEEP_DIVE_PATH} element={<DeepDiveMonthFrame client={deepDive} />} />` with
  `DEEP_DIVE_PATH = "/portfolio/month"`, placed before the `${PORTFOLIO_ROOT_PATH}/:tab?` route.
- `portfolioWords.ts`: `PORTFOLIO_TABS` gains `{ tab: "month", label: "The month", segment: "month" }` right after
  Overview; `PortfolioTab` gains `"month"`. `EstatePortfolio.tsx`: the tab row moves verbatim to
  `PortfolioTabs.tsx` (`<PortfolioTabs current window lens />`); given tab `month` the frame renders `<Navigate
  to="/portfolio/month" replace />`.
- `deepDiveMonthClient.ts`: `fetchDeepDiveMonth(month?: string)` GETs `/api/portfolio/month[?month=…]` through
  `fetchRetrying`; a body whose `schema` is not `deep-dive-month-1` is an error. The URL's `?month=` is the state; the
  month links change it (browser history).

### 5.2 Layout: the hub shape (IA-1b §3.1), live classes

```
<section data-shape="hub" class="dd-month">
  <header> h1 "Portfolio" · <PortfolioTabs current="month"/> · month nav: "‹ {previous words}" · <b>{month_words}</b> · "{next words} ›" (disabled without next) </header>
  L1  <p class="dd-headline">{headline}</p> <p role="status">{standing.text}</p> <p>{as_of_text}</p> [fresh banner] [untracked line]
      <div class="dd-kpis"> 4 tiles: label, value, word chip, lines, bar (tile 1) </div>
  L2  panel "Decisions" {decisions} · panel "Actions in hand" {actions}
  L3  section "Where the gap comes from": title; notices (role="note", visible, never in a drawer); totals with the
        bar; groups as an <ol> (group row: label and value; step rows: button opening the step drawer: label, value,
        share, word, sites); <details> "Show as table, by Site" with the by_site table
      section "Cash collected, outside the contribution gap": text, word, sites, <details> "Show by Site" table
      section "By outcome": four cards
      section "What is not available yet": rows (needs, fills, sites), 8 then "Show all {n}"; not_built line
  drawers: one per step (role="dialog", aria-modal, labelled by its title; focus moves to Close; Escape and the scrim
        close; focus returns to the opener: vNEXT `uxOpen`/`uxClose`)
</section>
```
NO_SNAPSHOT and REBUILD_NEEDED: header, `state_text`, nothing else. Loading: the header and "Preparing the month…".
503: `DEEP_DIVE_UNAVAILABLE` text with "Try again". 401: "Sign in to see this operator's figures."

### 5.3 Rules

- The page renders the JSON's strings and never formats, adds or compares a figure (D-5C.2). The bar's widths are
  the only arithmetic (`actual / max(|actual|, |target|)`).
- Words are text, never colour alone; negative values carry "−"; the word chip has the same text as the JSON.
- Widths: 1440 and 1280 four tiles in a row; 768 two by two; 390 one column, the tables scroll inside their own box
  (no page scroll), drawers full width. Hub height at 1440 for World A at most 2,500 px with every drawer and
  `<details>` closed.
- Caps (scales to 300 Sites): drawer Site lists and by-Site tables show 10 rows, then "Show all {n}"; not-available
  rows 8.
- Styling: `deepDiveMonth.css` with the live product's tokens (`frontend/mockups/v72/foundation-sheet.html`); layout
  values of vNEXT `ux.css`'s `.ux-kpis`, `.ux-kpi`, `.ux-wf*`, `.ux-drawer*` and `.ux-headline` carried over under
  `dd-` names.

## 6. Tests (written first)

**Unit 1, no database** (`backend/tests/test_5c_deep_dive_view.py`):
1. Tables: `FACTOR_LABELS` covers every factor reachable from `BRIDGE_ROOTS["MINI_GRID"]` in the registry; `HEADINGS`
   keys equal `CATEGORIES`; `STEPS` are terms of `contribution` or `cost_to_serve` and with the neutral terms are all.
2. Formats: `money` of −852, 38, 0, 1234567.891 (signed and not); `qty` 1180.000 → "1,180 L"; `pct0` 1443/2295 →
   63%, target ≤ 0 → none; `pct1` 0.91510 → 91.5%; `join` of 1, 2, 3 items.
3. World A against the hand-written JSON, key by key and whole.
4. B, C (and connected empty), D, E, F, G: every literal of §3.5.
5. Words: §2.4 table, every row; a "Not available yet" money figure gets no suffix.
6. One contribution: the tiles, headline, totals and outcome cards never read "$883.00" (Kobo's by-Site row alone
   does); they equal R, and a plant rendering `snap.actual()` fails, and `month_view` never calls `actual()` or `targets()` (spies).
7. Stops: one bridge per reason of 5b §2.1 (built from 5b's unit-1 vectors and test 3's cases), each worded per §2.5.

**Unit 2** (`backend/tests/test_5c_deep_dive_api.py`, TestClient with injected reads; and
`test_5c_deep_dive_postgres.py`, pooled `--db`):
8. API: 200 body equals the fixture for World A; `?month=2026-13` 422; no tenant 503; real-data on without a person
   401, with a person of the tenant 200; `Cache-Control: no-store`.
9. Postgres: World A's records loaded through 3A1's service; 3A7 statements recorded by the finance lead (S1 revenue
   9,700.00, fuel 5,100.00 at 2026-11-19T10:00Z): the standing in the body is A's; (b) S2 (fuel 5,000.00 at
   2026-11-19T12:00Z) and a rebuild: B's words; a statement recorded after the snapshot's `as_of` does not change the
   body until a rebuild (D-3A7.9); (c) written by 3C2 (§4.3).

**Unit 3** (`frontend/src/estate/__tests__/DeepDiveMonth.test.tsx`, vitest):
10. Renders World A's fixture: every string of §3.5 appears; the notice is visible with every drawer closed; the
    standing has role status.
11. A step button opens its drawer (dialog, labelled), focus moves to Close, Escape closes and returns focus.
12. NO_SNAPSHOT, REBUILD_NEEDED, 503 and 401 states; the month links set `?month=`.
13. The Overview's tab row markup is unchanged by the move to `PortfolioTabs.tsx` (outerHTML before and after on the
    existing Portfolio fixture); "The month" is the second tab.
14. Captures (evidence, not committed): 1440, 1280, 390 for World A; one with the fuel cost drawer open at 390; the
    page height check; no horizontal page scroll at 390.

**Regression:** the Portfolio's vitest files, `test_5b_*`, `test_3a7_*`, the 3B7a tests; tsc; check-all once at the
end; `select-tests` before review.

## 7. Mock departures (each gets a row in `.agent/mock-departure-register.md`)

| # | Element | Category | Note |
|---|---|---|---|
| MD1 | k3 plan spend, k4 plan value | D1 | "Not available yet" in the tile, the tile kept (plan not built) |
| MD2 | L2 queue panel "Decisions" | D1 | the panel kept with its honest gap |
| MD3 | "Actions in hand" in the Portfolio's L2 (the Site hub's L2 block) | D2 | flagged to the owner: RC9's Action has no other place on this screen |
| MD4 | waterfall steps at heading level (revenue, fuel cost, O&M, staff) | D1 | drivers (kWh, litres) only where observed, in the step's drawer |
| MD5 | trend lines in k1, k2 | D1 | omitted: no earlier month compared |
| MD6 | Protect card | D1 | "Not available yet" |
| MD7 | the route: a Portfolio tab "The month", not the Overview | D5 | resolving unit: IA-2's live rebuild of the Overview |

## 8. Done (questions; each can fail)

1. Does World A's screen show 1,443.00 against 2,295.00, −852.00, 3 of 3, Estimated, and never 883.00?
2. Is Kisiwa's −60.00 against −65.00 visible with every drawer closed?
3. Does every money figure read "not yet reconciled" until the standing at the snapshot's "as of" is reconciled, and
   does the standing's sentence say what did not match?
4. Does every stop and every Site left out name the records that would fill it, and every carried figure say it is
   an estimate at its budget line?
5. Is n the snapshot's Sites asked, and does each figure carry its own "k of n"?
6. Do Plan, Decisions and Protect read "Not available yet", and is the agreed change shown as an Action with its
   owner and due date once 3C2 is connected?
7. Does the screen work at 390, 1280 and 1440 within the caps, with drawers that keep and return focus?
8. Is nothing computed in the browser, and nothing changed outside §0's list, the fixtures, the tests and the packet?
9. Does each planted violation in the reviewer guide fail its named test?

Packet: `specs/5c-deep-dive-screen/packet.md` (screens by path, the mid-build count).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 (1.25) | §2, §3: words, view; fixture JSON; tests 1 to 7 | 3B7a and 3A7 merged | 1 |
| 2 (0.75) | §4: read, actions seam, route, composition; tests 8, 9 | unit 1 | 1 |
| 3 (1) | §5: the screen; tests 10 to 14; check-all; packet | unit 2 | 1 to 2 |

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
