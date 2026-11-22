# IA-P rev 2: the Overview on the date range (the period rule and E2; implementer spec, binding)

Status: live, rev 3 (handshake answers, D-IAP.24 to D-IAP.33; P.9 is new), Architect (Claude), 2026-11-22. Part of `spec.md` (its §3 points here). Decisions D-IAP.15 to
D-IAP.23 (`rulings.md`). Owner answers, verbatim: `owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md` (Q1 "Month is
the Overview", Q2 "Follow the date range").

## P.0 Existing, then new

- **Exists and stays.** 5c's month read (`GET /api/portfolio/month?month=`, `deep_dive/view.py`, `DeepDiveMonth.tsx`):
  one served snapshot per calendar month, its bridge, cash and outcome cards, each figure with its word. Its JSON and its
  tests do not change.
- **What changes.** Rev 1 showed one calendar month on the Overview, whatever the top-bar range said. The owner ruled that
  the Overview follows the range like every other page. Contribution against target exists only per whole month (targets
  and management accounts are monthly; there is no daily snapshot). So the Overview counts the whole months inside the
  range and names every month it cannot count. Nothing is cut by day, and no target is split by day.
- **New.** One pure resolver (P.2), one read and route, E2 (P.3 to P.6), one period body for a range of two or more months
  (P.5). E1 (P.8) uses the same resolver, so the Sites list and Outcomes follow the same months.

## P.1 The rule (D-IAP.16)

- The range is the address's `from` and `to` (SR-1 days, `to` included).
- A **whole month** is a calendar month whose first day is on or after `from`, whose last day is on or before `to`, and
  which has closed: the first instant (UTC) of the next month is at or before `now`.
- An **edge** is any other month the range touches: `PARTIAL` when only some of its days are in the range, `OPEN` when all
  its days are in the range but it has not closed.
- A whole month is **served** when its snapshot state is SERVED. Otherwise (NO_SNAPSHOT, REBUILD_NEEDED) it is **missing**.
- **Mode:** `none` with no served month, `month` with one, `period` with two or more.
- **Cap:** more than 24 whole months is refused (422 `RANGE_TOO_LONG`).
- `known_at` does not re-cut the figures: they are the snapshots as served, as 5c shows them today. It still governs every
  list read on the page (the L2 rows).

What the screen shows (`now` = 2026-11-22T00:00Z; every row is a test in P.7):

| Range | Whole months | Edges | Mode | The Overview shows | Top bar (SR-4c) |
|---|---|---|---|---|---|
| 2026-11-15 to 11-21 (Last 7 days) | none | Nov PARTIAL | none | the notes and "Show October 2026"; L2 rows | All pages |
| 2026-11-01 to 11-21 (This month) | none | Nov PARTIAL | none | the same | All pages |
| 2026-10-23 to 11-21 (Last 30 days) | none | Oct, Nov PARTIAL | none | the same | All pages |
| 2026-10-01 to 10-31 (Last month) | Oct | none | month | 5c's October screen | All pages |
| 2026-10-01 to 11-21 | Oct | Nov PARTIAL | month | 5c's October screen and the November note | "Showing 1 Oct – 31 Oct of the range" (the bar's words; `data-shared-range-focus="inside"`) |
| 2026-08-01 to 10-31 | Aug, Sep, Oct | none | period | the period hub (P.5) | All pages |

## P.2 The resolver (`backend/assetops_backend/deep_dive/period.py`, pure)

```python
@dataclass(frozen=True)
class Period:
    first: date
    last: date
    months: tuple[str, ...]                 # whole months, "YYYY-MM", ascending
    edges: tuple[tuple[str, str], ...]      # (month, "PARTIAL" | "OPEN"), ascending

@dataclass(frozen=True)
class MonthServed:
    month: str
    served: Served                          # 3B7a's, as `month()` reads it
    standing: Standing | None               # read only when SERVED (as 5c §4.1)

def month_days(month: str) -> tuple[date, date]
def resolve(first: date, last: date, now: datetime) -> Period
def header(period: Period, read: Sequence[MonthServed], suggest: str | None) -> dict   # P.4's keys `from` to `suggest`
```

- `resolve` raises `ValueError("BAD_RANGE")` when `first > last`, and `ValueError("RANGE_TOO_LONG")` beyond 24 months.
- `header` is shared by E2 and E1, so both state the same months in the same words.

## P.3 The read (`DeepDiveRead.period(tenant, first, last, names)`, `deep_dive/read.py`)

- `p = resolve(first, last, clock())`.
- For each month of `p.months`: `served = snapshots.portfolio(tenant.id, m)`; when SERVED, one
  `reconciliation.standing(tenant.id, None, m, known_at=served.as_of)` (5c §4.1's call, per month).
- **Suggest** (mode `none` only): start at the latest closed month whose first day is on or before `last`; step back one
  month at a time, at most 12 reads, to the first SERVED one. `None` when none is found.
- **Actions:** `actions.for_tenant(tenant.id)` in mode `period` only. In mode `month` the client reads the month route,
  which reads them as today.
- It returns `period_view(...)` (P.4, P.5). `DeepDiveRead.sites` (E1) takes `(tenant, first, last, sites)` and makes the
  same reads.

## P.4 E2's JSON (`schema` `portfolio-period-1`; keys in this order)

| Key | Value |
|---|---|
| `schema` | `"portfolio-period-1"` |
| `from`, `to` | the days as asked |
| `mode` | `"none"`, `"month"` or `"period"` |
| `months` | every whole month, ascending: `{"month", "month_words", "from", "to", "state"}` (`W.render_month`; `month_days`; the snapshot state) |
| `served` | the served months' codes, ascending |
| `period_words` | `portfolio_period.span` over the served months; null in mode `none` |
| `notes` | sentences, in this order: `missing` (when any), `partial` (when any), `open` (when any), `none` (mode `none`) |
| `shown` | `{"from", "to"}`: the first served month's first day to the last served month's last day. Null in mode `none`, and null when it equals `[from, to]` |
| `nav` | mode `month`: `{"previous", "next"}`, each `{"month_words", "from", "to"}` or null, by 5c's `_nav` rule around the served month. Null otherwise |
| `suggest` | mode `none`: `{"text": portfolio_period.suggest, "from", "to"}` of P.3's month, or null. Null otherwise |
| `body` | mode `period`: P.5. Null otherwise |

## P.5 The period body (mode `period`; D-IAP.17)

**Inputs.** `M` are the served months, ascending. `V_m = view._View(served_m, standing_m, names, m)` (5c's own class, reused
as is), and `R_m = V_m.R`.

**Rules.**
- **Sums.** A sum is exact (`Context(prec=34)`) over every `m` in `M`. It is None when any term is None, or when the
  `R_m.currency` values differ. In that case the currency is None and `notices` holds `portfolio_period.currencies`.
  Effects always add, because 5b's rule across Sites holds across months (money on the root). Nothing else is added.
- **The period standing `S`.** `reconciled` is true only when every month's standing is. `S` is the latest month's
  standing when all are reconciled, otherwise the latest unreconciled month's.
- **Words.** `word(value, cur, rows)` is null when the value or the currency is None, otherwise
  `W.word(*W.weakest_of(rows), S, cur)`.

**Keys, in order:**

| Key | Value |
|---|---|
| `as_of_text` | 5c's `as_of` sentence for the latest `served_m.as_of` |
| `status_line` | `as_of_text`, then `standing_short` by `S.reconciled`, then 5c's `status_disagreement` over the distinct disagreeing Sites of every month (the latest month's `asked` order first) |
| `fresh` | `portfolio_period.fresh` naming the months whose `V_m` freshness is not current; null when all are current |
| `headline` | `{"text", "evidence"}`: 5c's headline choice (`W.named` on ΣE, Σgrow, Σoptimize; the same five variants and the `subject`/`verb` words) through `portfolio_period.headline*`; `evidence` `[word(ΣE, cur, R_m…)]` |
| `tiles` | contribution: `W.amount(ΣA, cur)`, word, lines `[W.tile_target(ΣT, share), W.sites(k, n)]` (5c's share rule; `k`, `n` of the latest served month; D-IAP.25), bar `{"actual": str(ΣA), "target": str(ΣT)}` or null. gap: `W.amount(ΣE, cur, "SIGNED")`, word, lines `[W.tile_split(Σgrow, Σoptimize)]` when both are present. plan_spend and plan_value: 5c's tiles 3 and 4 exactly |
| `notices` | `[portfolio_period.currencies]` or `[]` |
| `months` | `{"title": "Month by month", "columns": ["Month", "Contribution", "Gap to target", "Largest driver against target"], "rows"}`. There is one row per whole month (served or missing), ascending |
| `outcomes` | the four cards in `HEADINGS` order (below) |
| `actions` | 5c's `actions` block, built by the same function |

`ΣA`, `ΣT`, `ΣE` are `R_m.actual`, `R_m.target` and `R_m.effect` summed. `Σgrow` and `Σoptimize` are `V_m.group_sums()`
summed.

**A month row.**
- **Served:** `{"month", "month_words", "from", "to", "state": "SERVED", "contribution", "gap", "gap_word", "driver",
  "driver_heading", "sites"}`. `sites` is `W.sites(k_m, n_m)` for that month (D-IAP.25).
  - `contribution` is `portfolio_sites.contribution` over `R_m` ("Not available yet" when either side is None).
  - `gap` and `gap_word` are `V_m.tiles()[1]`'s `value` and `word`, string for string: one figure.
  - `driver` and `driver_heading` follow E1's rule (P.8) over `V_m.rows`' STEPS rows.
- **Missing:** the same keys. `contribution` is 5c's `no_snapshot` or `rebuild` sentence, and the four figure keys are null.

**Cards.**
- **grow, optimize:** `W.amount(Σ group sum, cur, "SIGNED")`, word over every month's steps of that heading. The line is
  `portfolio_period.grow_line` for grow and 5c's optimize line for optimize. `drawer` is null.
- **protect:** 5c's card.
- **assure:** "Reconciled" or "Not yet reconciled" by `S.reconciled`, word null. The line is `portfolio_period.assure_line`.
  The drawer is `{"title": 5c's assure title, "lines": ["{month_words}: {standing_m.text}" for each served month]}`.

## P.6 The route (`deep_dive_api.py`, the same router)

`GET /api/portfolio/period?from=YYYY-MM-DD&to=YYYY-MM-DD`.
- It uses the month route's tenant, its 503 `DEEP_DIVE_UNAVAILABLE`, its real-data 401 `PERSON_REQUIRED` and its store
  503.
- 422 `BAD_RANGE` covers a missing bound, a bound that is not a real day, and `from > to`. 422 `RANGE_TOO_LONG` covers more
  than 24 whole months.
- 200 sets `Cache-Control: no-store`.
- No migration and no new store.

**Statements** (`i18n/statements/en/portfolio_period.py`, SC-1 pure literal data, `"rephrase": "never"`; month slots use
5c's month value):

| Key | English |
|---|---|
| `span` | one: "{month}" · two: "{first} and {last}" · more: "{first} to {last}". Month names alone when every served month is in one year, else with the year ("November 2025 to February 2026") |
| `headline` / `_more` / `_gap` / `_on` / `_na` | 5c's five, with "in {month_name}" read as "across {period}": "Contribution is {abs gap} {below\|above} target across {period}; {subject} {verb} {abs big} of it." · "…across {period}; {subject} {verb} {abs big}, more than the whole gap." · "Contribution is {abs gap} {below\|above} target across {period}." · "Contribution is on target across {period}." · "Contribution across {period} is not available yet." |
| `compared` | "Compared for {k} of {n} Sites." Appended to the headline when `k < n` in any served month (`k`, `n` of the latest served month; D-IAP.25) |
| `missing` | "No figures are served for {months}, so it is not in these figures." · (2 or more) "…, so they are not in these figures." |
| `partial` | "{months} is only partly in this range, so it is not counted: the figures are kept by whole month." · (2) "{months} are only partly in this range, so they are not counted: the figures are kept by whole month." |
| `open` | "{months} has not closed yet, so it has no figures." · (2 or more) "{months} have not closed yet, so they have no figures." |
| `none` | "This range holds no whole month with figures. Contribution against target is kept by whole calendar month." |
| `suggest` | "Show {month_words}" |
| `currencies` | "The months are in different currencies, so they are not added." |
| `fresh` | "Some months' figures are out of date: {months}. Open a month for what changed." |
| `grow_line` | "Revenue against target, over {count} months" |
| `assure_line` | "{k} of {m} months reconciled" |
| `months_title`, columns | as P.5 |
| `{months}` year rule (D-IAP.28) | in `missing`, `partial` and `open`, the month names follow `span`'s rule over the months that sentence names; `suggest` keeps `month_words` with the year |
| errors (`portfolio_period.refused`, E2's and E1's own 422 helper; `_refused` keeps 503) | `BAD_RANGE` "Write the range as two days, YYYY-MM-DD, the first not after the last." · `RANGE_TOO_LONG` "The month figures cover at most 24 months. Narrow the date range." |

`{months}` joins the month words as the catalogue's list form does. The SC-1 catalogue check and the hand-built-sentence
guard pass.

## P.7 Tests (`backend/tests/test_iap_portfolio_period.py`; written first, W2; pure; every string exact)

**World P** is 5c World A's served October store plus a September copy: `replace(served, snapshot=replace(served.snapshot,
month="2026-09"))` (`Served` has no `month` field; in the test's `_world_p()`). The September standing is World A's with
"October 2026" read as "September 2026" in `text` and `details`. `now` is 2026-11-22T00:00Z.

1. **`resolve`.** Each row of P.1's table, by its months and edges. 25 whole months raise `RANGE_TOO_LONG`, and
   `first > last` raises `BAD_RANGE`.
2. **World P, 2026-09-01 to 2026-10-31.**
   - mode `period`; `period_words` "September and October"; `notes` []; `shown` null.
   - headline "Contribution is $1,704.00 below target across September and October; cost and efficiency explain
     $1,510.00 of it.", evidence ["Estimated, not yet reconciled"].
   - tiles[0] "$2,886.00", "Estimated, not yet reconciled", lines ["Target $4,590.00 · 63% of target"], bar
     {"actual": "2886.00", "target": "4590.00"}.
   - tiles[1] "−$1,704.00", lines ["Grow −$194.00 · Optimize −$1,510.00"].
   - months rows September and October, each "$1,443.00 against a target of $2,295.00", "−$852.00", "Fuel cost
     −$755.00", heading "Optimize cost and efficiency".
   - grow "−$194.00" "Emulated, not yet reconciled" "Revenue against target, over 2 months"; assure "Not yet reconciled",
     "0 of 2 months reconciled".
   - The status line ends "Kisiwa's budget disagrees with its own lines."
3. **One figure.** Each served row's `gap` equals `month_view(...)["tiles"][1]["value"]` for its month, and tiles[1]
   equals `W.amount` of the sum of the months' effects.
4. **World P with September NO_SNAPSHOT.** mode `month`; `served` ["2026-10"]; `notes` ["No figures are served for
   September, so it is not in these figures."] (the month words as the catalogue renders them); `nav.previous` is
   September's days; `body` null.
5. **August NO_SNAPSHOT, then World P (2026-08-01 to 2026-10-31).** mode `period`; the totals of test 2; three rows, with
   August's `contribution` being 5c's `no_snapshot` sentence for August 2026 and its figure keys null; `notes[0]` the
   `missing` sentence for August.
6. **Mode `none`, 2026-11-15 to 2026-11-21, over World A.** `notes` ["November is only partly in this range, so it is not
   counted: the figures are kept by whole month.", `none`]; `suggest`
   {"text": "Show " + `W.render_month("2026-10")`, "from": "2026-10-01", "to": "2026-10-31"}; `body` null.
7. **2026-09-01 to 2026-11-21 over World P.** `shown` {"from": "2026-09-01", "to": "2026-10-31"} and the November
   `partial` note.
8. **Currencies.** September's root in KES: tiles 1 and 2 read "Not available yet" with word null, and `notices` is
   [`currencies`].
9. **Route.** 200 with the schema; 422 `BAD_RANGE` on `to=2026-02-30` and on reversed days; 422 `RANGE_TOO_LONG`; 503
   with no read; 401 on real data with no person (`test_5c_deep_dive_api.py`'s fakes).
10. **Fixtures current.** The committed `frontend/src/estate/__tests__/fixtures/iap/period-*.json` bodies equal the view's
    output for tests 2, 4 and 6, so the gates never test a stale body.
11. **World G two months** (D-IAP.25): World G (`served_world(thika=True)`) with a September copy, 2026-09-01 to
    2026-10-31: the headline ends " Compared for 3 of 4 Sites."; tiles[0]'s lines hold "3 of 4 Sites"; each month row's
    `sites` is "3 of 4 Sites".
12. **Degrade, not 500** (I7): World X (currency mismatch) over two months: no raise; the totals read "Not available yet".

## P.8 E1: `GET /api/portfolio/sites?from=YYYY-MM-DD&to=YYYY-MM-DD` (new; D-IAP.9, D-IAP.20)

**Where.**
- The pure view: `backend/assetops_backend/deep_dive/sites.py`, `sites_view(*, period: Period, read:
  Sequence[MonthServed], suggest: str | None, sites: Sequence[SiteRef], now) -> dict` (P.2).
- The read: `DeepDiveRead.sites(tenant, first, last, sites)`, with E2's resolver and per-month reads (P.3).
- The route: in `deep_dive_api.py`, on the same router.
  - The refusals are E2's: 503 `DEEP_DIVE_UNAVAILABLE`, 401 `PERSON_REQUIRED` on real data, 422 `BAD_RANGE`, 422
    `RANGE_TOO_LONG`.
  - 200 sets `Cache-Control: no-store`.
- `SiteRef(code, name, domain)` comes from `registry.imported_sites()`, in registry order.
- No migration and no new store.

**The JSON** (`schema` `portfolio-sites-1`; keys in this order):

| Key | Value |
|---|---|
| `schema` | `portfolio-sites-1` |
| `from` to `suggest` | `period.header(...)`: E2's keys, the same values (P.4) |
| `as_of_text` | 5c's `as_of` sentence for the latest served month, or null in mode `none` |
| `headline` | `{"text", "evidence"}` from `portfolio_sites.headline`, or null in mode `none` |
| `columns` | `["Site", "Group", "Contribution", "Gap to target", "Largest driver against target", "Waiting for a choice"]` |
| `rows` | one per `SiteRef` (below) |
| `total` | `{"gap", "word"}`: the Overview's tile 2 `value` and `word` for the same range (mode `month`: 5c's, from `R`, 5c's root row; mode `period`: P.5's ΣE), or null in mode `none` |
| `without_target` | `{"count": k, "text": portfolio_sites.without_target or null}` |

**A row** is `{"site_code", "site", "group", "contribution", "gap", "gap_word", "driver", "driver_heading", "below",
"months_text"}`:

- `group` comes from `portfolio_sites.group`: domain MINIGRID "Mini-grid", COLDCHAIN "Cold-chain", EV_CHARGING "EV
  charging". These are the live `DOMAIN_WORD`s; a test pins equality with a fixture copy.
- **The months.** In mode `month` a row reads the one served month (`R` is its root row). In mode `period` a row sums
  the served months in which the Site is compared, exactly, by P.5's sum rule:
  - `months_text` is `portfolio_sites.months` ("Compared in {k} of {m} months") when that is fewer than every served
    month, and null otherwise;
  - `gap_word` is the weakest of those months' root words under the period standing;
  - the driver is the most negative of the summed STEPS effects.
  - In mode `none` every row is not compared.
- **Compared** (the Site is in `R`'s k in at least one served month, so it has an actual and a target):
  - `contribution` is `portfolio_sites.contribution` ("{actual} against a target of {target}", money as `W.amount`);
  - `gap` is the Site root's effect, signed;
  - `gap_word` is 5c's figure word through `money_word` with the standing;
  - `below` is `effect < 0`;
  - `driver` and `driver_heading`: among the Site's `STEPS` rows with an effect below 0, the most negative (ties in `STEPS`
    order). `driver` is `"{W.factor_label(step)} {W.amount(effect, cur, 'SIGNED')}"` and `driver_heading` is
    `W.heading_label(home)`. With none below 0, `driver` is `portfolio_sites.no_driver` and `driver_heading` is null.
- **Not compared** (any other Site):
  - `contribution` is `portfolio_sites.no_figures` for a Site whose domain is not MINIGRID (no monthly snapshot exists
    for its type, D-3B6.6; D-IAP.26, MD-IAP-12), and `W.text("NOT_AVAILABLE")` for a mini-grid Site;
  - `gap` and `driver` are `W.text("NOT_AVAILABLE")` ("Not available yet");
  - `gap_word` and `driver_heading` are null, and `below` is false.
- **Order.** Compared rows by effect ascending (exact Decimal; ties in `snap.asked` order), then the rest in registry order.
- **The sum check** (I7) runs only when `R.effect` and every compared effect are present. In the route an
  `AssertionError` is a logged 503 `DEEP_DIVE_UNAVAILABLE`; in tests it raises.
- **One figure** (owner, 2026-11-21). The compared rows' effects sum exactly to `R.effect` (mode `period`: to the sum of
  the months' `R.effect`). `total.gap` is the Overview's tile 2 value for the same range, string for string. A test fails
  if either breaks; a break is fixed in the bridge, never in this view.

**Statements** (`i18n/statements/en/portfolio_sites.py`, SC-1 pure literal data, the 1a pattern, `"rephrase": "never"`):
- `portfolio_sites.headline` has slots `below` (count), `compared` (count) and `period` (`portfolio_period.span`), and
  variants:
  - `some` when `below` > 0: "{below} of {compared} Sites are below target in {period}";
  - `none`: "Every Site is on or above target in {period}" (IA-1 §3.3; contribution kind only, D-IAP.9).
- `portfolio_sites.months`, slots `k` and `m`: "Compared in {k} of {m} months".
- `portfolio_sites.contribution`: "{actual} against a target of {target}".
- `portfolio_sites.no_driver`: "No driver widens the gap".
- `portfolio_sites.no_figures`, slot `domain` (the group word, lower case after the first word as the catalogue gives it):
  "No monthly figures for {domain} Sites yet" ("No monthly figures for cold-chain Sites yet", "… for EV charging Sites
  yet").
- `portfolio_sites.without_target`, slot `count`: "{count} Sites without a target are not in this figure", and "1 Site
  without a target is not in this figure" when the count is 1.
- `portfolio_sites.group`, slot `domain` (state): "Mini-grid", "Cold-chain" and "EV charging".

The catalogue check and the hand-built-sentence guard (SC-1) must pass. No sentence is built outside the renderer.

**Tests** (`backend/tests/test_iap_portfolio_sites.py`; written first, W2; pure, on 5c World A and D's fixtures and
P.7's World P). Every string is exact. Tests 1 to 6 use the range 2026-10-01 to 2026-10-31:
1. **World A.**
   - Rows, in order:
     - Kobo: "$883.00 against a target of $1,445.00", "−$562.00", "Fuel cost −$600.00", heading "Optimize cost and
       efficiency", `below` true;
     - Kisiwa: "−$250.00 against a target of −$65.00", "−$185.00", "Fuel cost −$130.00", heading "Optimize cost and
       efficiency";
     - Mto: "$810.00 against a target of $915.00", "−$105.00", "Revenue −$80.00", heading "Grow revenue".
   - `total.gap` "−$852.00".
   - Headline "3 of 3 Sites are below target in October", evidence ["Estimated, not yet reconciled"].
   - `without_target.count` 0.
   - Each compared row's `gap` equals its Site's `by_site` Gap cell in October's `month_view`, string for string (R9).
2. **World G** (`served_world(thika=True)`): Thika's row is last, group "Cold-chain", contribution "No monthly figures for
   cold-chain Sites yet", gap and driver "Not available yet", `gap_word` null. `count` 1 with "1 Site without a target is
   not in this figure".
3. NO_SNAPSHOT (mode `none`): the header keys, with E2's notes. `rows` still lists every Site, each not compared.
   `headline` and `total.gap` are null.
4. The sum check: a fabricated `Served` whose Site effects do not sum to `R.effect` raises `AssertionError("SITES_SUM")`.
   4b. World X: no raise, and every row's gap reads "Not available yet".
5. The route: 200 with schema; 422 `BAD_RANGE` on `to=2026-02-30`; 503 when the read is absent; 401 on real data with no
   person. These reuse `test_5c_deep_dive_api.py`'s app fakes.
6. The headline `none` variant (a world with every effect ≥ 0), and Kisiwa's heading words equal `W.heading_label`.
7. **World P, 2026-09-01 to 2026-10-31** (mode `period`):
   - Kobo "$1,766.00 against a target of $2,890.00", "−$1,124.00", "Fuel cost −$1,200.00";
   - Kisiwa "−$500.00 against a target of −$130.00", "−$370.00", "Fuel cost −$260.00";
   - Mto "$1,620.00 against a target of $1,830.00", "−$210.00", "Revenue −$160.00";
   - each `months_text` null; `total.gap` "−$1,704.00", equal to E2's tiles[1] for the same range;
   - headline "3 of 3 Sites are below target in September and October".
8. **Partly compared.** World P with Mto's September `SiteMonthSnapshot.targets` emptied (September `R.k` 2 of 3, shown in
   the packet): Mto's row sums October only and reads `months_text`
   "Compared in 1 of 2 months". The compared rows still sum to the period's effect.
9. **Fixtures current** (R8). The committed `fixtures/iap/sites-2026-10.json`, `sites-2026-09-10.json` and
   `sites-none-2026-11.json` equal `sites_view` for tests 1, 7 and 3. The E0 fixture's `waiting_by_site` keys are E1's
   `site_code`s.

## P.9 The long range (D-IAP.24; unit P0)

**The problem.** Every estate, Site, cold, EV, actions and source-health read refuses a window over 31 days
(`estate/scope.py:21` and its siblings), and so does the shared range (`ui/sharedRange.ts:18`). A two-month range, and
so "Month by month" (owner Q10), could not reach the Overview.

**The rule.**
- **The cap.** `RANGE_MAX_DAYS` becomes 731. The bar's refusal text reads "… 731 days at most." A 731-day range holds at
  most 24 whole months, so E2's cap is never the first limit a range hits.
- **Whole-range pages.** `WHOLE_RANGE_PAGES = /^\/(?:portfolio(?:\/outcomes)?|sites)\/?$/`. On these, E2 and E1 read
  the address's whole range.
- **The window.** Every other read takes `readWindow(params): DayRange | null` (`sharedRange.ts`). It keeps `to`, sets
  `from` to `max(from, to − 30 days)` and keeps `known_at`. When the range is 31 days or fewer, the window equals the
  range. It is the only day arithmetic the browser adds, beside `monthDays`.
- **The sweep (a class fix).** Every raw `get("from")`/`get("to")` outside `sharedRange.ts` (35 sites today) and every
  `readSharedRange`/`useSharedRange` caller that builds a request (10 files) moves to `readWindow`. `readSharedRange` keeps
  returning the whole range, for the bar and the whole-range pages.
- **The bar.** When the range is over 31 days, the page is not a whole-range page and the page declared no span itself,
  the bar treats the window as a declared span inside the range: `data-shared-range-focus="inside"`, "Showing {span} of the
  range". No page adds its own declaration for this.
- **Blocks on whole-range pages.** A block fed by a capped read carries `ui/RangePartNote.tsx`:
  `<p class="range-part" role="note">`, with the bar's words for the window, rendered only when the window differs from
  the range. These blocks are Overview L2, Outcomes L3, the Sites list's "Waiting for a choice" column (in the header's
  `<small>`) and the inbox drawer. Search's result list carries the note too.
- **Links** carry the whole range (`from`, `to`), never the window, so moving back to a whole-range page restores it.

**Tests first** (P0):
- `ui/__tests__/readWindow.test.ts`: 7, 31, 32 and 731 days; `known_at` kept; 732 days invalid.
- `ui/__tests__/noRawRangeReads.test.ts`: a static scan of `frontend/src` (tests excluded) that fails on
  `get("from")`, `get('from')`, `get("to")` or `get('to')` outside `sharedRange.ts`.
- `shell/__tests__/sharedRangeBar.test.tsx`: a 61-day range on `/findings` shows the window as "inside", and on
  `/portfolio` shows "All pages" (or E2's `shown`).
- One request test per read family (estate, mini depth, cold, EV, actions, source health): a 61-day address sends the
  31-day window.

**Plants.**
- `rawread` (one call site reverted to `params.get("from")`) fails `noRawRangeReads`.
- `nowindow` (the bar's auto-span removed) fails `sharedRangeBar`.

**Gates.**
- **R7.** `/findings?from=2026-09-01&to=2026-10-31` sends `from=2026-10-01` to `/api/estate/findings`, and the bar's tag
  is "inside".
- **R8.** From that page the rail link to Portfolio carries `from=2026-09-01`.

**Owner Q12.** The labelled window is the interim, not the owner's range rule fully met. A measured task that raises the
31-day read caps is queued after IA-P (default).
