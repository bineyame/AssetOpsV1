# IA-P: the real app on the agreed shape (implementer spec)

Status: live, rev 1, spec written; handshake next. Architect (Claude), 2026-11-22.
Owner request: `owner/owner-merge-on-accept-ia-shape-k10-2026-11-22.md`. The owner reviews once the product is close to the
shape, then iterates. UI slices merge on review ACCEPT, with one combined walkthrough at the end.

**Decisions:** `rulings.md`, D-IAP.1 to D-IAP.14. **Reviewer guide:** `reviewer-guide.md`. `USER_REVIEW_REQUIRED: true`.
**Mock (governs, `.ai/RULES.md` §6):** vNEXT (`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`)
as built by IA-1a/1b/1c, IA-2a and IA-2b1:
- `ia-routes.js` `IA_RAIL`, `IA_TAB_GROUPS`, `IA_ALIASES`;
- the shapes in `specs/IA-1-shape-rebuild/spec.md` §2.3, §3, §4 and `spec-IA-2b.md` §3 and §4;
- the proposal page `Docs/design-system/ia-proposal/index.html` §3, §4 and §6.

Visual style: `frontend/mockups/v72/foundation-sheet.html` tokens. Standing brief: `owner/owner-ui-standing-brief-2026-11-20.md`
(the right control per content, one interaction grammar, exposure that scales, simplicity by design, honest numbers).

**Read first:**
- `rulings.md`;
- IA-1 `spec.md` §1, §2.2 (registry, aliases, rail), §3.1 and §3.2, §4.3;
- `spec-IA-2b.md` §1, §3 and §4 (on `main` once IA-2b1 merges; until then `git show task/IA-2b1-lists:specs/IA-1-shape-rebuild/spec-IA-2b.md`);
- 5c `spec.md` §3.1, §5.1 to §5.3;
- this spec's §2 and the §6 card of your unit.

## 0. Existing, then new

**What exists today and stays.** The live product (`frontend/src`) already has the reads an executive needs:
- the estate Portfolio read (`/api/estate/portfolio`): placement queue, value cards, objectives, progress;
- the Finding, Action, Evidence and Financials roots;
- the month read built by 5c (`/api/portfolio/month`, `DeepDiveMonth.tsx`): contribution against target, the bridge,
  cash, the four outcome cards, every figure with its evidence word;
- 8 Site tabs over three verticals, the shared date range (SR-1) and its span declaration (SR-4c, `ui/rangeFocus.tsx`).

Every one of these is reused. No read is rewritten.

**What is wrong with the arrangement.** The served app still has the pre-IA arrangement:
- a 7-tab Portfolio (Overview, The month, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage), where
  the month and the Overview each show a portfolio summary;
- a rail without Decisions or Results;
- 8 Site tabs;
- no inbox.

So the executive meets two front pages and the same content in two places. The owner approved IA (D-IA.1 to D-IA.3) puts each
object in one home.

**What IA-P adds.** It is a re-housing, not a rebuild:

```
 MENU (rail)                     PORTFOLIO (/portfolio)                SITE (/sites/:id)
 Operations  Portfolio           [Overview][Outcomes][Demand & cap.]   [Overview][Operations][Performance]
             Sites               Overview = the month (5c), hub:       [Financials][Evidence][Setup]
             Assets & cover (-)    L1 headline + 4 tiles
 Intell.     Findings              L2 Decisions rows (6) + Actions     LISTS: one component (IA-2b)
 Work        Decisions  <- new     L3 bridge · cash · by outcome       /decisions /findings /actions /sites
             Plan (-)            Outcomes = Sites rows + by outcome    tiles = list, address = view,
             Actions             Demand & capacity = opportunity       10 then "Show all n", 1 target/row
             Incidents
             Maintenance         TOP BAR: scope · search · period · Waiting for you (n) · theme
 Assurance   Results    <- new
             Evidence & records  (-) = "Not available yet", as the rail does today
 Business    Financials
 Admin       Settings (-)
```

**Mechanism to value.** The executive's loop stays outcome → drivers → evidence → lever → action → verify. IA-P puts each
step at one address:
- the outcome and its drivers are on the Overview (the month bridge);
- the choices waiting are in Decisions and in "Waiting for you";
- the Actions are in Actions, and what changed is in Results.

That loop is the value beyond a monitoring tool (the demo objective). A person stays in it: AssetOps proposes, and the team
chooses and acts under their own names (6a and 3C2 record who).

## 1. Outcome

An operator executive opens the served app and sees:
- the approved menu;
- a three-tab Portfolio whose Overview is the month;
- live lists of decisions, Findings, Actions and Sites in the menu;
- six Site tabs on every vertical;
- a "Waiting for you" control.

Every pre-IA address still lands on its content: on the same page, or through one alias to the new home. No screen is lost
(§2.4 is the complete map, and the route-map test enforces it).

## 2. The target route map

### 2.1 The menu (`shell/OperatorShellLayout.tsx` `operatorRailItems`; D-IAP.5)

The groups, the order and the labels follow D-IA.1 (vNEXT `IA_RAIL`). The group keys keep today's casing.

| Group | Item | Route | State after IA-P | Icon | Unit |
|---|---|---|---|---|---|
| OPERATIONS | Portfolio | `/portfolio` | live | `grid` | (kept) |
| OPERATIONS | Sites | `/sites` | live | `site` | (kept; the list from P4) |
| OPERATIONS | Assets & cover | — | unavailable (IA-2c) | `asset` | P1 (relabel from "Assets") |
| INTELLIGENCE | Findings | `/findings` | live | `finding` | (kept; the list from P2) |
| WORK | Decisions | `/decisions` | live | `decide` (new) | P1 unavailable, P2 live |
| WORK | Plan | — | unavailable: no plan record (D-IAP.1) | `clock` | P1 |
| WORK | Actions | `/actions` | live | `action` | (kept; the list from P2) |
| WORK | Incidents | `/incidents` | live | `incident` | (kept) |
| WORK | Maintenance | `/maintenance` | live | `work` | (kept) |
| ASSURANCE | Results | `/results` | live | `book` | P1 unavailable, P3 live |
| ASSURANCE | Evidence & records | `/evidence` | live | `evidence` | P1 (relabel from "Evidence") |
| BUSINESS | Financials | `/financials` | live | `money` | (kept) |
| ADMIN | Settings | — | unavailable (IA-2e) | `gear` | (kept) |

- "Operational records" leaves the rail. It becomes the Records tab of Evidence & records (P1).
- `RailIcon` gains `decide: "M12 3v6 M12 9l-6 6v6 M12 9l6 6v6"`.
- The Lab stays in the workspace footer, unchanged.

### 2.2 Tab groups

| Group | Tabs (label · route) | Shape |
|---|---|---|
| Portfolio | Overview `/portfolio` · Outcomes `/portfolio/outcomes` · Demand & capacity `/portfolio/demand-and-capacity` | hub (5c classes) |
| Evidence & records | Coverage `/evidence` · Records `/evidence/records` | page |
| Site | Overview · Operations · Performance · Financials · Evidence · Setup (§2.3) | the Site's pages |

One tab component draws every group: `ui/SectionTabs.tsx`, the `site-tabs` link row with `aria-current="page"` and no ARIA
tablist (as `PortfolioTabs` does today). Every tab link carries the address's shared range: `from`, `to` and `known_at`
(D-IAP.4; this fixes 5c's default-window tabs).

### 2.3 The Site's six tabs (D-IAP.7)

`CANONICAL_OPERATOR_SITE_TABS` becomes six entries. The paths keep today's segments (D-IAP.4, Q5).

| Tab | Href (canonical) | Pages that light it (old tab → new) | Section links line (P5) |
|---|---|---|---|
| Overview | `siteDetailHref` (EV: `/ev`) | Overview | — |
| Operations | `siteWorkHref` | Work: `/work`, `/work/incidents`, `/work/maintenance` | (the Work page's own sub-tabs, unchanged) |
| Performance | `sitePerformanceHref` | Performance, `/performance/:capabilityId`; Health `/health` | "In Performance: {the page's sub-tabs} · Health" |
| Financials | `siteFinancialsHref` (EV: `/ev/financials`) | Financials, assumptions, scenarios, prices, opportunities, EV assumptions and scenarios | (unchanged) |
| Evidence | `siteEvidenceHref` (EV: `/ev/evidence`) | Evidence, EV evidence and analysis; Uploads `/uploads` | "In Evidence: Records · Uploads" |
| Setup | `siteFoundationHref` | Foundation, `/foundation/:view`, `/foundation/changes[/:id]`; Assets `/assets[/:assetId]` | "In Setup: Foundation · Changes · Assets" |

- **Findings leaves the Site row.** `/sites/:siteId/findings` aliases to `/findings?scope=site:{siteId}`, after P5's parity
  test (§6, P5).
- **Object pages.** A Finding detail (every `/sites/:id/findings/:fid[/:view]`, the fuel Finding and the domain-action
  verifications) and a Site Action detail (`/sites/:id/actions/:aid[/:view]`) are object pages (D-IA.9). They draw no Site
  tab row. Their breadcrumb is `[home list (link)] › [Site name (link to the Site Overview)] › [title]`. The home list is
  "Decisions" on the `recommendation` and `alternatives` views, "Findings" on every other Finding view, and "Actions" on an
  Action.
- **The section links line.** `<nav class="site-sections" aria-label="{Tab} sections">` holds the "In {Tab}:" text and the
  links. It sits under the tab row on every page that lights Performance, Evidence or Setup. The current link carries
  `aria-current="page"`.

### 2.4 Every current route, and its home (D-IAP.4; nothing is lost)

"Kept" means the same address and content, re-housed (a new tab, rail item or crumb). An alias is a client redirect with
`replace`. It keeps the query (the range included), it keeps the sub-path where marked `/*`, and it lands in the named unit.

| Current address | New home | How | Unit |
|---|---|---|---|
| `/` | `/portfolio` (D-IA.15: the start is the Portfolio) | alias | P1 |
| `/portfolio` (old Overview: cards, pulse, top three) | `/portfolio` is the month (§3). Cards go to Outcomes L3, the top three to Overview L2 (Decisions rows), the pulse is retired (D-IAP.12) | kept, re-housed | P3 |
| `/portfolio/month` | `/portfolio` (keeps `?month=`) | alias | P3 |
| `/portfolio/act-first` (`?lens=`) | `/decisions` (`lens` kept as the Finding-type facet) | alias | P2 |
| `/portfolio/outcomes` | `/portfolio/outcomes` (L2 Sites rows from P4) | kept | P3, P4 |
| `/portfolio/opportunity` | `/portfolio/demand-and-capacity` | alias | P3 |
| `/portfolio/changes` | `/results` | alias | P3 |
| `/portfolio/scope` | `/evidence` (its second section, "Scope & coverage") | alias | P3 |
| any other `/portfolio/:tab` | `/portfolio` (today's rule) | kept | — |
| `/sites` | `/sites` (the Sites list) | kept, rebuilt as a list | P4 |
| `/sites/:id` and every Site sub-route | the same address, lit under its §2.3 tab | kept | P5 |
| `/sites/:id/findings` | `/findings?scope=site:{id}` | alias (after the parity test) | P5 |
| `/sites/:id/configuration` | today's redirect, unchanged | kept | — |
| `/findings` | `/findings` (the list) | kept, rebuilt as a list | P2 |
| `/findings/cost`, `/findings/risks`, `/findings/opportunities` | `/findings?lens=cost`, `?lens=risks`, `?lens=opportunities` | alias | P2 |
| `/findings/:siteId/:assessmentId[/:tab]` | the same (legacy Finding detail; lit under Findings) | kept | — |
| `/actions` | `/actions` (the list) | kept, rebuilt as a list | P2 |
| `/incidents`, `/maintenance`, `/maintenance/preventive`, `/maintenance/requests/*` | the same | kept | — |
| `/operational-records` | `/evidence/records` | alias | P1 |
| `/evidence` | `/evidence` (Coverage tab, H1 "Evidence & records") | kept, re-housed | P1 |
| `/financials` | the same | kept | — |
| `/simulator-lab/*` | the same (workspace footer) | kept | — |
| `*` | `RouteNotAvailableFrame` | kept | — |
| — | `/decisions` (new list), `/results` (new page), `/portfolio/demand-and-capacity` (new tab), `/evidence/records` (new tab) | new | P2, P3, P1 |

The Plan (`/plan`) and the inbox have no route. The Plan is an unavailable rail item. The inbox is a drawer opened from the
top bar (IA-1 §4.3: "no address until IA-2d").

## 3. Where 5c's month view lives (D-IAP.2)

**Recommendation: the month is the Portfolio Overview, at `/portfolio`.** `/portfolio/month` aliases to it, keeping
`?month=`, so the DDR and WK addresses still land.

**The reason.** The governing mock's Overview is this screen. 5c was built to vNEXT `#/portfolio`'s hub shape, and its
MD7 names "IA-2's live rebuild of the Overview" as its resolving unit. Two front pages would show the portfolio's
contribution against target twice, which breaks the owner's one-figure rule and the three-tab IA.

**The alternative.** Keep "The month" as a fourth Portfolio tab and leave today's range Overview. That costs one unit
less, but it keeps two summaries and needs a D2 departure from the three tabs.

**Consequences** (each ruled in D-IAP.2 and D-IAP.12):
- **The period.** The Overview shows a calendar month, not the top-bar range. It declares the month's span through the
  existing SR-4c hook: `useDeclareRangeSpan('{month}-01', '{month}-{last day}')`. So the top bar names the month, and the
  range stays in the address for every other page.
  - The month comes from `?month=`, and otherwise from the server's default (the previous closed month).
  - The month links (‹ ›) stay where 5c put them, in the hub header.
  - This is an exception to the owner's range rule on one page. The owner decides it: queue Q2.
- **Overview L2.** 5c's "Decisions" panel (MD2, "Not available yet") becomes the Decisions list's rows: capped at 6, no tools,
  then "View all {n}" (IA-2b §6). They are read for the month's bounds. "Actions in hand" stays beside them.
- **The old Overview's content.** The four range category cards (with 1a's scope line) move to Outcomes L3. The top three
  becomes Overview L2. The pulse is retired, because each of its links now has a menu item or tab. The coverage line and
  the scope disclosure move to Evidence & records › Coverage.
- **On a database with no served month** (NO_SNAPSHOT, or no tenant), the Overview shows 5c's own `state_text` under the
  header and tab row, and the L2 Decisions rows still render. Nothing is invented.

## 4. What each surface reads (D-IAP.8, D-IAP.9)

### 4.1 The reads per surface

Every read below exists except E1. E0 adds one field to an existing body.

| Surface | Reads (client · endpoint) | Notes |
|---|---|---|
| Overview | `deepDiveMonthClient.fetchDeepDiveMonth(month)` · `GET /api/portfolio/month`; `estateClient.portfolio` · `GET /api/estate/portfolio` (the month's bounds, lens `all`, every page) | figures are only the month's; the rows are only the placement queue's |
| Outcomes | E1 `GET /api/portfolio/sites?month=`; `estateClient.portfolio` (the range: E0 `waiting_by_site`, and L3 with `getOutcomeSummary`) | L1 headline and L2 rows from E1; L3 range cards as today |
| Demand & capacity | `estateClient.portfolio` (the range) | `OpportunityPanel` as today |
| Decisions list | `estateClient.portfolio` (the range, lens `all`, every page) | one row per placed Finding (D-IAP.3) |
| Findings list | `estateClient.findings` (the range, lens `all`, state `all`, every page) + the Decisions read (same key, shared cache) | "Its decision" joins on `finding_id` |
| Actions list | `estateClient.actions` (the range, every page) | |
| Sites list | `siteDirectoryClient` · `GET /api/sites`; E1 (the month of the range's `to`, else the server default); E0 | the rows come from E1, in E1's order |
| Results | `estateClient.portfolio` (the range) `progress` | `ProgressPanel`, moved verbatim |
| Evidence & records | Coverage: `estateEvidenceMoney` (as today) + `estateClient.portfolio` (`scope_disclosure`, footer, coverage line); Records: `globalWork` operational records (as today) | |
| Site tabs | unchanged per page | |
| Inbox | the Decisions read for the range (shared cache), plus `progress.rows` | one read; refreshed when the range changes |
| Search | on open: `/api/sites`, the Decisions, Findings and Actions reads (shared cache) | lazy |

**The shared cache** (`estate/estateReadCache.tsx`). It is a React context in `OperatorShellLayout`. It holds one
promise per `(read, from, to, known_at)`, read across every page (`loadAllPages`, below), so moving between lists, the inbox
and search does not re-read. It is dropped when the range changes.

**`loadAllPages(read, query)`.**
- It follows `next_cursor` with `limit: 50` up to 20 pages (1,000 rows).
- Beyond that, the list renders the rows it has and the line "Showing the first 1,000. Narrow the date range to see the rest."
- The tile still shows the server's `total_count`.

### 4.2 E0: waiting counts (additive; `/api/estate/portfolio`)

- **Fields** (`estate/portfolio.py`, beside `placement_counts`, over the same `members`, the composed `portfolio_row`s):
  - `summary.waiting_count` counts the members whose `action_id` is None;
  - `summary.waiting_by_site: {site_code: int}` gives the same per Site, for Sites with at least one member.
  - Both are `null` when `finding_known` is false.
- **The client.** `estateClient.ts`: `waiting_count?: number | null` and `waiting_by_site?: Record<string, number> | null`
  (absent on an older or stored body).
- **Tests** (`backend/tests/test_iap_waiting_counts.py`, pure, on the composed rows of `test_cc_placement_postgres.py`'s
  world, copied as literals):
  - `waiting_by_site` sums to `waiting_count`;
  - one Site's count is written as a literal;
  - a member with a matched Action is not counted;
  - `finding_known` false gives `null`.
- **The frontend.**
  - The Decisions tile "Waiting for a choice" counts the list's `waiting` rows, and `homeLists.test` asserts it equals
    `waiting_count`. When the read is truncated (§4.1), the tile shows `waiting_count`.
  - The Sites row's "Waiting for a choice" is `waiting_by_site[code]`, and 0 when the Site has no member.
  - When the field is absent, the cell is "Not available yet".

### 4.3 E1: `GET /api/portfolio/sites?month=YYYY-MM` (new; D-IAP.9)

**Where.**
- The pure view: `backend/assetops_backend/deep_dive/sites.py`, `sites_view(*, month: str, served, standing: Standing,
  sites: Sequence[SiteRef], now) -> dict`.
- The read: `DeepDiveRead.sites(tenant, month, sites)`, with the same month parsing, served read and standing read as
  `month()`.
- The route: in `deep_dive_api.py`, on the same router.
  - The refusals are the month route's: 503 `DEEP_DIVE_UNAVAILABLE`, 401 `PERSON_REQUIRED` on real data, 422 `BAD_MONTH`.
  - 200 sets `Cache-Control: no-store`.
- `SiteRef(code, name, domain)` comes from `registry.imported_sites()`, in registry order.
- No migration and no new store.

**The JSON** (`schema` `portfolio-sites-1`; keys in this order):

| Key | Value |
|---|---|
| `schema`, `month`, `month_words` | as 5c (`W.render_month`) |
| `state`, `state_text` | `served.state`; 5c's state text, or null |
| `as_of_text` | 5c's `as_of` sentence, or null |
| `headline` | `{"text", "evidence"}` from `portfolio_sites.headline`, or null when not SERVED |
| `columns` | `["Site", "Group", "Contribution", "Gap to target", "Largest driver against target", "Waiting for a choice"]` |
| `rows` | one per `SiteRef` (below) |
| `total` | `{"gap": W.amount(R.effect, R.currency, "SIGNED") or null, "word": tile 2's word or null}`. `R` is 5c's root row |
| `without_target` | `{"count": k, "text": portfolio_sites.without_target or null}` |

**A row** is `{"site_code", "site", "group", "contribution", "gap", "gap_word", "driver", "driver_heading", "below"}`:

- `group` comes from `portfolio_sites.group`: domain MINIGRID "Mini-grid", COLDCHAIN "Cold-chain", EV_CHARGING "EV
  charging". These are the live `DOMAIN_WORD`s; a test pins equality with a fixture copy.
- **Compared** (the Site is in `R`'s k, so it has an actual and a target):
  - `contribution` is `portfolio_sites.contribution` ("{actual} against a target of {target}", money as `W.amount`);
  - `gap` is the Site root's effect, signed;
  - `gap_word` is 5c's figure word through `money_word` with the standing;
  - `below` is `effect < 0`;
  - `driver` and `driver_heading`: among the Site's `STEPS` rows with an effect below 0, the most negative (ties in `STEPS`
    order). `driver` is `"{W.factor_label(step)} {W.amount(effect, cur, 'SIGNED')}"` and `driver_heading` is
    `W.heading_label(home)`. With none below 0, `driver` is `portfolio_sites.no_driver` and `driver_heading` is null.
- **Not compared** (any other Site):
  - `contribution`, `gap` and `driver` are `W.text("NOT_AVAILABLE")` ("Not available yet");
  - `gap_word` and `driver_heading` are null, and `below` is false.
- **Order.** Compared rows by effect ascending (exact Decimal; ties in `snap.asked` order), then the rest in registry order.
- **One figure** (owner, 2026-11-21). The compared rows' effects sum exactly to `R.effect`. `total.gap` is the Overview's
  tile 2 value, string for string. A test fails if either breaks; a break is fixed in the bridge, never in this view.

**Statements** (`i18n/statements/en/portfolio_sites.py`, SC-1 pure literal data, the 1a pattern, `"rephrase": "never"`):
- `portfolio_sites.headline` has slots `below` (count), `compared` (count) and `month` (month name), and variants:
  - `some` when `below` > 0: "{below} of {compared} Sites are below target in {month}";
  - `none`: "Every Site is on or above target in {month}" (IA-1 §3.3; contribution kind only, D-IAP.9).
- `portfolio_sites.contribution`: "{actual} against a target of {target}".
- `portfolio_sites.no_driver`: "No driver widens the gap".
- `portfolio_sites.without_target`, slot `count`: "{count} Sites without a target are not in this figure", and "1 Site
  without a target is not in this figure" when the count is 1.
- `portfolio_sites.group`, slot `domain` (state): "Mini-grid", "Cold-chain" and "EV charging".

The catalogue check and the hand-built-sentence guard (SC-1) must pass. No sentence is built outside the renderer.

**Tests** (`backend/tests/test_iap_portfolio_sites.py`; written first, W2; pure, on 5c World A and D's fixtures). Every
string is exact:
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
2. A `SiteRef` for a COLDCHAIN Site appended: its row is last, with "Not available yet" ×3 and group "Cold-chain". `count` 1
   with "1 Site without a target is not in this figure".
3. NO_SNAPSHOT: header keys only. `rows` still lists every Site, each not compared. `headline` and `total.gap` are null.
4. The sum check: a fabricated `Served` whose Site effects do not sum to `R.effect` raises `AssertionError("SITES_SUM")`.
5. The route: 200 with schema; 422 on `month=2026-13`; 503 when the read is absent; 401 on real data with no person. These
   reuse `test_deep_dive_api.py`'s app fakes.
6. The headline `none` variant (a world with every effect ≥ 0), and Kisiwa's heading words equal `W.heading_label`.

## 5. Shared rules (every unit)

### 5.1 The route registry (`frontend/src/shell/iaRoutes.ts`; D-IAP.4)

- **`IA_LANDED`.** `const IA_LANDED = new Set<string>([...])`. Each unit adds its ID (`IA-P1` to `IA-P7`) in its last
  commit.
- **`IA_HOMES`.** `{ pattern: RegExp, home: RailLabel | null, tabGroup: 'Portfolio' | 'Evidence & records' | 'Site' | null }[]`.
  It holds one entry per §2.4 address family. `railHomeOf(pathname)` returns the first match's `home`, and replaces
  `railActiveLabel`.
- **`LEGACY_ROUTES`.** `{ from: string; to: string | ((params, search) => string); unit: string; prefix?: true }[]`, with
  the §2.4 aliases. It is live only when its unit is landed.
- **`LegacyRedirect`.** It renders `<Navigate replace>` to `to`, merging the original search: the target's own query first,
  then the original's parameters not already set. App.tsx mounts it once per live entry, before the target's route.
- `tools/checks/navigation-truthfulness.ps1` pins the new rail call form `activeLabel={railHomeOf(pathname)}` and the new
  item list. Show that it fails on a planted extra live item first.

### 5.2 The list component (`ui/HomeList.tsx`, `ui/homeListModel.ts`, `ui/homeList.css`; D-IAP.6)

It is IA-2b §3 transcribed to React, with the live tokens. Markup:

```
<section data-shape="list" data-home-list="{key}">
  <div data-level="L1"><div class="hl-tiles">{≤ 4 tiles}</div></div>
  <div data-level="L2">{chips}{tools}{table | empty}{more}</div>
</section>
```

- **The model.** `homeListModel(def, items, q, scope)` is pure. It returns `{rows, shown, hidden, n, ns, tier, groups}`,
  with IA-2b §3.1's steps 1 to 7 and its numbers:
  - tier 0 below 3 items, 1 up to 10, 2 above 10;
  - cap 10, unless `show=all`;
  - keep-first, displayed in sort order;
  - groups only above 10 rows in more than one group.
- **The address is the view.** The parameters are, in order:
  - the shared range `from`, `to` and `known_at`, untouched;
  - then `scope`, the facets in def order, `sort`, `q` and `show=all`, each only when not its default.
  - `homeListHref(key, params, change)` writes it. A facet or search change drops `show`.
  - A control writes with `navigate(href)` and keeps its focus and place, as IA-2b §3.3: a ref holds `{name, top}` and a
    layout effect restores scroll and focus.
- **Chips, tools, empty states and words.** These follow IA-2b §3.2 and §7 word for word: "Show all {n}", "View all {n}",
  "Clear filters", "All sites", "Clear search", `Matching “{q}”`, "Nothing matches these filters.", the `aria-label`s "Filter
  and sort {plural}" and "Sort {plural}", and the chips row's "In this view".
- **One target per row.** The first cell is `<th scope="row"><Link class="hl-go">{title}</Link>{small}</th>`. Every other
  cell is `<td data-label>` and holds text only. `.hl-go::after` stretches over the row, and `tr:focus-within` draws the
  outline.
  - A row whose server ref is absent draws its title as text, with `<small>Detail not available yet</small>`, and no link.
    It is counted and shown, never dropped.
- **At 390 px.** Each row stacks as label and value pairs (`data-label`), the tools wrap, and nothing scrolls sideways.
- **Options.** `tools: false`, `tiles: false` and `cap: number`. With `cap`, "Show all" becomes "View all {n}", linking to
  the list's own route with the range and scope.

**The list defs** (`estate/homeLists.tsx`: decisions, findings, actions; `estate/sitesList.tsx`: sites).

| List | Row key · title (small) · target | Columns after the first | Facets (key · label · options · way out) | Sorts | Tiles |
|---|---|---|---|---|---|
| decisions | `finding_id` · `row.title` (small: `PLACEMENT_GROUP_LABEL[row.placement.group]`) · `link_refs.finding` with the view `recommendation` | Site (`site_name`) · State (`decisionStateKey`: `waiting` "Waiting for a choice" when `action_id` is null, else `underway` "Under way") · At stake (the consequence text today's `FindingRow` renders, by the same function) · Due ("Not available yet") · Who decides ("Not available yet") | `state` · State · waiting, underway · "All states"; `lens` · Finding type · cost "Cost", risks "Risks", opportunities "Opportunities" (from `lens_flags`) · "All findings" | `priority` "Priority" (server order) · `site` "Site" | "Decisions" (`total_count`); "Waiting for a choice" (rows `waiting`; asserted equal to E0 `waiting_count`) |
| findings | `finding_id` · `title` (small: `finding_label`) · `link_refs.finding` | Site · Heading (the `categories.items` labels joined " · ", else "Not available yet") · Its decision (the Decisions row with the same `finding_id`: its State word, else "No decision open") | `lens` · Finding type · (as above) · "All findings"; `state` · State · `EstateStateFilter` words as `findingIndex.tsx` shows them · "All states" | `priority` "Priority" · `site` "Site" | "Findings" (`total_count`); "Decision waiting for a choice" (rows whose decision is `waiting`) |
| actions | `action_id` · `action_title` (small: `success_criterion`) · `link_refs.action` | Owner (`owner`, else "Not recorded") · Due (today's `actionIndex.tsx` date words, else "No deadline") · State (today's `application_state` words) | `state` · State · the three `application_state` words · "All states" | `due` "Due date" (ISO string order, no date last) · `site` "Site" | "Actions" (`total_count`); one part per `application_state` present (the parts sum to n) |
| sites | `site_code` · `site` · `/sites/{code}` | Group · Contribution · Gap to target (with `gap_word` as `<small>`) · Largest driver against target (`driver`, small `driver_heading`) · Waiting for a choice (E0 `waiting_by_site`, §4.2) | `target` · Target · below "Below target", on "On or above target" (by E1 `below`; not compared in neither) · "Above and below target" | `gap` "Gap to target" (E1 order) · `name` "Name" | "Sites" (rows); "Below target" (rows `below`); "Gap to target" (`total.gap`, with `without_target.text` under it) |

- **`def.site`** (for scope) is the row's `site_code`. The scope groups are the domains, with the words of `DOMAIN_WORD`.
- **`def.none`:** "No decisions in this range.", "No Findings in this range.", "No Actions in this range.", "No Sites in this
  scope.".
- **Actions.** Today's four server summary figures (`open_actions`, `due_overdue`, `verification_window`,
  `verified_in_30_days`) stay as one caption line under the tiles, with today's words. MOCK DEVIATION D2, MD-IAP-6.

### 5.3 Pages and states

- **Headers.**
  - Lists: `PageHeader` with the menu label as title and no subtitle.
  - Results: title "Results" and the subtitle "What changed in this review".
  - Evidence & records: title "Evidence & records", with each tab keeping today's subtitle.
  - Portfolio: title "Portfolio" (5c's H1, used on all three tabs).
- **Loading.** Lists show the tiles' labels and a "Loading {plural}…" status. A refusal shows today's `EstateRefusal`, with
  its copy and its retry.
- **Fonts and colour.** Font sizes are on the guide's scale (12, 13, 14, 16, 20, 24, 32 px). There is no colour literal
  outside token blocks (G2), and every page is clean in light and dark.
- **No horizontal page scroll** at 390 on any IA-P page.
- **Copy.** Every new string is in this spec. Any other word is a reused constant. Never type a month: it comes from the
  server or `formatDayTime`.

## 6. Units (each 1 to 3 commits; the app works after each; D-IAP.13)

Two parts, one branch each, one discovery review per part:
- **IA-P1** is P1 to P3 (3.75 units), on `task/IA-P1-frame-portfolio`.
- **IA-P2** is P4 to P7 (4.75 units), on `task/IA-P2-sites-site-inbox`, branched from IA-P1's merge.

**Every unit runs:**
- `tsc`;
- focused `vitest` (the named files plus `select-tests.py --base main`);
- the fast check-all;
- `tools/iap_gates.cjs` (below).

Heavy tools go through `tools/heavy-slot.sh`. Screenshots are taken at 1440 × 900, 768 × 1024 and 390 × 844, light and
dark, with `/opt/assetecon/tools/pw` (`source env.sh`), on `vite preview --strictPort --port 5573`. They go to
`/opt/assetecon/evidence/IA-P/<unit>/`. Never use ports 5490, 8990, 8991, 8992 or Docker. Every "plant" is a one-line source
edit that the named check must fail on. The builder shows each failing in the packet, then reverts it.

**`tools/iap_gates.cjs <base-url> [--plant NAME]`** (new in P1; extended by each unit; the `deep_dive_gates.cjs` pattern).
It answers `/api/*` from fixtures in `frontend/src/estate/__tests__/fixtures/iap/` through `page.route`. Checks per landed
unit:
- **R1** the rail's groups, items, order and live or unavailable states equal §2.1;
- **R2** every live `LEGACY_ROUTES` entry lands on its target with the query kept;
- **R3** each landed page's `data-shape` regions;
- **R4** at 390 the page width equals the viewport;
- **R5** no page error;
- **R6** no visible text under 12 px.

Each later unit adds its own checks.

### P1: the frame (1.0 unit; IA-P1)

- **Files:**
  - `shell/OperatorShellLayout.tsx` (items per §2.1, `railHomeOf`);
  - `shell/iaRoutes.ts` (new);
  - `ui/RailIcon.tsx` (`decide`);
  - `ui/SectionTabs.tsx` (new);
  - `App.tsx` (the `/evidence/records` route, `LegacyRedirect` mounting, `/` alias);
  - `estate/EstateEvidence.tsx` and `work/OperationalRecords.tsx` (header "Evidence & records" plus the tab row);
  - `tools/checks/navigation-truthfulness.ps1`.
- **Tests first:**
  - `shell/__tests__/iaRoutes.test.ts`: `railHomeOf` for one path per §2.4 family; `LEGACY_ROUTES` landed filtering; the
    search merge;
  - `shell/__tests__/iaRouteMap.test.ts`: reads `App.tsx` and `operatorSiteRoutes.ts` raw and fails on any route path that
    is not a live route, a live alias, a Lab route or `*`. This is the no-screen-lost check. It grows each unit;
  - the existing rail tests, updated to §2.1.
- **Plants:**
  - `rail` (Decisions made live in P1) fails R1 and `navigation-truthfulness`;
  - `alias` (`/operational-records` entry dropped) fails R2 and `iaRouteMap`;
  - `routemap` (a new `<Route path="/x">`) fails `iaRouteMap`.
- **Shots:** `/portfolio` (the rail), `/evidence`, `/evidence/records`; 390 with the menu open.

### P2: the list component and three lists (1.5 units; IA-P1)

- **Files:**
  - `ui/HomeList.tsx`, `ui/homeListModel.ts`, `ui/homeList.css` (new);
  - `estate/homeLists.tsx` (new);
  - `estate/estateReadCache.tsx` (new, mounted in `OperatorShellLayout`);
  - `estate/findingIndex.tsx` and `estate/actionIndex.tsx` (their frames render the list; the old tables and lens tabs are
    removed; reused cell-word functions are kept and exported);
  - `shell/EstateRootFrames.tsx` (`EstateDecisionsFrame`);
  - `App.tsx` (the `/decisions` route; the aliases `/portfolio/act-first`, `/findings/cost|risks|opportunities`);
  - `estate/portfolioWords.ts` (`act-first` leaves `PORTFOLIO_TABS`);
  - `iaRoutes.ts` (Decisions live).
- **Tests first:**
  - `ui/__tests__/homeListModel.test.ts`: IA-2b §8 Block A on a synthetic 25-item store. It covers tiers at 2, 3, 10, 11
    and 25; a facet; an invalid value ignored; words ANDed; stable sort; cap; keep-first; groups; href order;
  - `estate/__tests__/homeLists.test.tsx`: the live defs on fixture bodies. It covers:
    - tile 1 = shown + hidden = "Show all n";
    - the controls by tier;
    - one interactive element per row;
    - a row without a ref shown as text;
    - the "waiting" count = E0 `waiting_count`;
    - each control's value = the address;
    - a fresh mount at an address = the in-page result.
- **Plants:**
  - `tile` (tile 1 counts the shown rows) fails `homeLists`;
  - `rowctl` (a button in a decisions row) fails `homeLists` and gate L2;
  - `restore` (the sort is ignored on first render) fails `homeLists`;
  - `cap` (cap 11) fails `homeListModel`;
  - `dropref` (a row without a ref is skipped) fails `homeLists`.
- **Gates added:**
  - **L1** each list's `data-shape="list"`;
  - **L2** one interactive element per row, and Tab moves one stop per row;
  - **L3** `/portfolio/act-first?lens=cost` lands on `/decisions?lens=cost`, showing the chip "Cost · All findings".
- **Shots:** each list at 1440, 768 and 390, light and dark; `/decisions` with one facet set.

### P3: the Portfolio hub (1.25 units; IA-P1)

- **Files:**
  - `estate/portfolioWords.ts` (three tabs: overview `null`, outcomes `outcomes`, demand `demand-and-capacity`);
  - `estate/PortfolioTabs.tsx` (draws `SectionTabs`; carries the address range);
  - `estate/DeepDiveMonth.tsx` (rendered at `/portfolio`; declares the month span; L2's Decisions panel becomes
    `HomeList` decisions, `{tools: false, tiles: false, cap: 6}` over the month's bounds, with "View all {n}" to
    `/decisions?from={first}&to={last}`; the header, L1 and L3 are unchanged);
  - `estate/EstatePortfolio.tsx`:
    - its Overview branch, pulse and `TopThree` are removed;
    - `outcomes` renders `ObjectivesPanel` (L2) then `CategoryCards` (L3) until P4;
    - `demand` renders `OpportunityPanel`;
    - the `act-first`, `changes` and `scope` branches move out;
  - `estate/Results.tsx` (new; `ProgressPanel` moved verbatim);
  - `estate/EstateEvidence.tsx` (the second section "Scope & coverage": `PortfolioCoverage` line, `ScopeDisclosure`,
    `ContextFooter`, moved verbatim);
  - `App.tsx` (`/portfolio` → the month frame; `/portfolio/:tab` kept for outcomes and demand; `/results`; the aliases
    `/portfolio/month`, `/portfolio/opportunity`, `/portfolio/changes`, `/portfolio/scope`).
- **Tests first:**
  - `estate/__tests__/portfolioHub.test.tsx`: the three tabs with the range kept; Overview = the month body; L2 rows = the
    Decisions rows for the month's bounds, at most 6, then "View all {n}"; `/portfolio/month?month=2026-10` →
    `/portfolio?month=2026-10`; NO_SNAPSHOT shows `state_text` and the rows;
  - `DeepDiveMonth.test.tsx`: the decisions-panel assertions are updated (named in the packet); every other assertion is
    kept;
  - `Results.test.tsx`; `estateEvidence` scope section.
- **Plants:**
  - `fourtab` (a fourth tab) fails `portfolioHub` and gate H1;
  - `window` (the tabs lose the range) fails `portfolioHub`;
  - `twofig` (the old category cards rendered on the Overview) fails gate H2.
- **Gates added:**
  - **H1** three tabs in §2.2's order;
  - **H2** the Overview has at most 6 blocks and holds no `[data-portfolio-card-value]`;
  - **H3** `deep_dive_gates.cjs` passes at `/portfolio?month=2026-10` (its URL argument changed; the checks unchanged).
- **Shots:** the three tabs, `/results` and `/evidence` with the scope section, at the three widths, light and dark.
- **IA-P1's review follows P3.**

### P4: the Sites list, Outcomes, E0 and E1 (1.75 units; IA-P2)

- **Files:**
  - backend: `deep_dive/sites.py`, `deep_dive/read.py` (`sites`), `deep_dive_api.py` (route),
    `i18n/statements/en/portfolio_sites.py`, `estate/portfolio.py` (E0);
  - frontend: `estate/portfolioSitesClient.ts` (new; schema check `portfolio-sites-1`), `estate/sitesList.tsx` (new),
    `shell/SitesFrame.tsx` (renders the Sites list; the directory table and the Lifecycle column are removed),
    `estate/EstatePortfolio.tsx` (outcomes: L1 E1 headline; L2 `HomeList` sites `{tools: false, tiles: false}` with "Show
    all" to `/sites?show=all`; L3 `CategoryCards`, then `ObjectivesPanel` inside `Disclosure` "Each Site's objectives"),
    `estate/estateClient.ts` (E0 type).
- **Tests first:** §4.2 and §4.3's backend tests; `estate/__tests__/sitesList.test.tsx` (World A's E1 fixture: the rows in
  E1 order; the gap tile "−$852.00" equals the Overview's tile 2 string; the target facet; "Not available yet" rows last;
  the Outcomes rows = the Sites list rows).
- **Plants:**
  - `sum` (one Site effect altered in the view) fails test 4;
  - `order` (registry order) fails test 1;
  - `browsersort` (the frontend sorts by gap) fails `sitesList` (the order must be E1's);
  - `handbuilt` (an f-string sentence in `sites.py`) fails the SC-1 guard.
- **Gates added:** **S1** `/sites` tile "Gap to target" = `/portfolio` tile 2, by text.
- **Shots:** `/sites`, `/portfolio/outcomes` at the three widths, light and dark.

### P5: the Site's six tabs (1.0 unit; IA-P2)

- **Files:**
  - `shell/operatorSiteTabs.tsx` (six entries; `OperatorSiteTabLabel` is the six; the old-label map `SITE_TAB_OF` is
    `Foundation`→`Setup`, `Health`→`Performance`, `Work`→`Operations`, and the rest are equal; EV overrides are re-keyed);
  - every frame's `current` prop through `SITE_TAB_OF`;
  - `ui/SiteSections.tsx` (new; the §2.3 line);
  - the Finding and Action detail frames (no tab row; breadcrumbs per §2.3);
  - `App.tsx` (the `/sites/:id/findings` alias, after the parity test).
- **Tests first:**
  - `shell/__tests__/operatorSiteTabs.test.tsx`: six labels in order on MINI, COLD and EV; each §2.3 page lights its tab;
  - `estate/__tests__/siteFindingsParity.test.ts`: for the three verticals' fixtures, every Finding the Site index lists
    for a window appears in the Findings list at `scope=site:{id}` for the same window.
  - **If the parity test fails for a vertical, stop that part and raise `SPEC_AMBIGUITY`.** Do not ship the alias for it.
- **Plants:**
  - `seventab` (Findings kept in the row) fails `operatorSiteTabs` and gate T1;
  - `crumb` (a Finding page keeps the tab row) fails gate T2.
- **Gates added:**
  - **T1** six tabs on one Site per vertical;
  - **T2** object pages: the crumb has three parts, and no tab row.
- **Shots:** one Site per vertical: Overview, Setup and a Finding page, at the three widths, light and dark.

### P6: "Waiting for you" (0.75 unit; IA-P2)

- **Files:** `shell/WaitingForYou.tsx` (new) and `OperatorShellLayout.tsx` (the control in the top bar, after the range
  bar).
- **The control** follows IA-1 §4.3:
  `<button type="button" class="ia-inbox" aria-haspopup="dialog" aria-controls="ia-inbox">`, then the icon `action`, the
  label "Waiting for you" (visually hidden at 390) and the badge.
  - The badge is the count of the Decisions read's `waiting` rows, with the hidden text ", {n} waiting". It is absent at 0.
- **The drawer** is a dialog, `aria-modal`, titled "Waiting for you". Focus moves to Close; Escape and the scrim close it;
  focus returns to the control. Its sections:
  1. **"For you"**: "Not available yet" (who decides is not recorded until the decision records, 6a; MD-IAP-4).
  2. **"In your portfolio"**: each `waiting` decision, as `<a href=decision target>{title} <small>{Site} ·
     {placement word}</small></a>`, in server order. It is capped at 10, then "View all {n}" to
     `/decisions?state=waiting`. Empty: "Nothing else is waiting for a choice".
  3. **"Since you last looked"**: the first 3 `progress.rows` with the words `ProgressPanel` uses, then "See all in
     Results" to `/results`. Empty: "No change recorded in this range".
- **Tests first:** `shell/__tests__/waitingForYou.test.tsx` covers the badge = the Decisions tile "Waiting for a choice";
  the empty states; the focus cycle.
- **Plants:**
  - `badge` (the badge counts every row) fails it;
  - `focus` (no focus return) fails it.
- **Gates added:** **W1** the badge text = the `/decisions` waiting tile; at 1280 the top bar is on one line.
- **Shots:** the drawer open at the three widths, light and dark.

### P7: scope and search (1.25 units; IA-P2)

- **Files:** `shell/ScopeSwitch.tsx` and `shell/SearchPalette.tsx` (new); `OperatorShellLayout.tsx` (the order is
  Scope · Search · range bar · Waiting for you); `backend/conversions/walk-layer4-v1.json` (pages extended, §8).
- **Scope** (IA-1 §2.3 item 1; IA-2b §3.3):
  - The button reads "All sites ▾", or "{domain word} ▾", or "{Site name} ▾".
  - The menu lists "All sites", one entry per domain present, then the Sites.
  - On a list, an entry writes `scope=` and keeps the facets, sort and `q`. On a Site page or a hub, a Site entry opens
    `/sites/{code}`, and a group or all keeps `scope=` in the address.
  - The Overview and Demand & capacity show the chip "This page shows every Site" when scope is not all (MD-IAP-5).
- **Search:**
  - The button is "Search Sites, decisions and Findings", opened with Ctrl K or ⌘ K, as a dialog with one input.
  - The entries are Sites (`name`, "Site", `/sites/{code}`), Decisions (`title`, "Decision · {Site}"), Findings
    (`title`, "Finding · {Site}") and Actions (`action_title`, "Action · {owner or Site}"), plus every live rail item
    (label, "Go to").
  - Words are ANDed, case-blind. The first 20 matches show, in that kind order. Arrow keys move, Enter opens, Escape closes.
- **Tests first:**
  - `shell/__tests__/scopeSwitch.test.tsx` covers a list scope kept with its facets, and a Site entry on a list scoping it;
  - `shell/__tests__/searchPalette.test.tsx` covers the AND rule, the cap of 20, only live targets, and the keyboard.
- **Plants:**
  - `scopedrop` (the facets dropped on a scope change) fails `scopeSwitch`;
  - `deadlink` (an unavailable rail item indexed) fails `searchPalette`.
- **Gates added:** **K1** the Ctrl K open and close cycle with focus returned.
- **Shots:** the scope menu and the palette, at the three widths, light and dark.
- **IA-P2's review follows P7.**

## 7. Mock deviations (each gets a row in `.agent/mock-departure-register.md` in its unit)

| ID | Element (mock) | Category | Note | Unit |
|---|---|---|---|---|
| MD-IAP-1 | Plan rail item and the `plan` shape (IA-2a) | D1 | no plan record in the live product; the item is unavailable, as the rail's rule is. It resolves when a plan record exists (not specified yet) | P1 |
| MD-IAP-2 | Decisions list rows (IA-2b §4 `decisions`) | D1 | rows are placed Findings (D-IAP.3). Due and Who decides read "Not available yet"; State has two of the four words. Resolving unit: 6f (on 6a) | P2 |
| MD-IAP-3 | Demand & capacity L1 `uxChain` | D1 | no portfolio demand-to-capacity read; the region is omitted (an empty slot omits its region); L3 as the mock | P3 |
| MD-IAP-4 | Inbox "For you", and the plan row | D1 | who decides is not recorded (6a); there is no plan | P6 |
| MD-IAP-5 | Scope on the Overview (the month read has no scope) | D5 | a chip says the page shows every Site. Resolving unit: a scoped month read (to be specified) | P7 |
| MD-IAP-6 | Actions list tiles | D2 | today's four server figures kept as a caption line under the list tiles (extended, not dropped) | P2 |
| MD-IAP-7 | Outcomes L3 `uxInsight` ("Sites that look alike") | D1 + D2 | no live source (D1); the range category cards and the objectives matrix sit there instead (D2, flagged: Q8) | P3, P4 |
| MD-IAP-8 | Site paths `/setup`, `/operations` (IA route names) | D2 | today's segments kept, labels changed (Q5) | P5 |
| MD-IAP-9 | Group words "Mini-grids", "Cold rooms", "EV depots" | D4 | the live product's domain words, as the Type column has always read | P4, P7 |

5c's MD2 closes in P3, and MD7 closes in P3 (the month is the Overview).

## 8. Size, and the effect on the world ladder and the WK and DDR serves

**Size: 8.5 units, about 14 commits.**
- IA-P1 is 3.75 units: P1 1.0, P2 1.5, P3 1.25.
- IA-P2 is 4.75 units: P4 1.75, P5 1.0, P6 0.75, P7 1.25.
- Each part is under the 6-unit cap.
- Opus does the first builds; Sonnet does the fix rounds. There is one discovery review per part (W5: P4 has a money figure
  and a new endpoint).

**The world ladder.** `tools/world.py` keys the world on `CODE_PATHS` (`backend/assetops_backend`, …), not on `frontend/`.
- P1 to P3 and P5 to P7 do not change the key.
- P4 changes `backend/assetops_backend` (E0, E1, statements), so the L2 template is refused as stale, naming the `code`
  part. The coordinator rebuilds the current rung once after P4 merges, before the next WK run. There is no migration.

**WK.** The walk pages (`backend/conversions/walk-layer4-v1.json`) all still land:
- `/portfolio` is now the month;
- `/portfolio/month?month=2026-10` aliases to `/portfolio?month=2026-10`;
- `/sites`, `/sites/{code}`, `/findings`, `/actions`, `/evidence` and `/financials` stay.

New reads on those pages: E1 on `/sites`, and the estate portfolio read on `/portfolio`. Neither returns 500 on a
NO_SNAPSHOT tenant; test 3 proves it. P7 adds `/decisions`, `/results`, `/portfolio/outcomes` and
`/portfolio/demand-and-capacity` to `pages`. That changes the walk definition only, not the world key. S4's census is
unaffected: E0 enlarges stored `chain_response` bodies, which may grow (D-WK.16).

**DDR.** S7's browser path `/portfolio/month?month=2026-10` aliases to the Overview, and the month API body is unchanged
(E1 is a separate route). The runbook's step text should read `/portfolio?month=2026-10` after P3; that is a one-line runbook
edit in P3.

## 9. Decision queue (W3; the defaults apply now)

| # | Question (owner) | Default | Why |
|---|---|---|---|
| Q1 | Where the month lives | **The Portfolio Overview** (§3) | the mock's Overview is this screen; one figure for the portfolio. Alternative: a fourth tab "The month" |
| Q2 | The Overview shows a closed month, not the top-bar range (the one page excepted from the range rule) | **Yes**; the top bar names the month there (SR-4c) | targets and management accounts exist per month; a partial range would show a figure the accounts cannot reconcile |
| Q3 | Until decision records exist (6a, awaiting P6), Decisions lists the Findings waiting for an agreed Action | **Yes**, labelled MD-IAP-2 | Act first's reviewed queue moves to its approved home instead of an empty list |
| Q4 | Plan in the menu before a plan record exists | **"Not available yet"** | a mock plan shown live would present modelled figures as the operator's |
| Q5 | Site paths keep `foundation` and `work` under the new labels | **Keep** | 30+ addresses and their tests unchanged; the labels are what people see |
| Q6 | Decisions keeps the mock's Due and Who decides columns, reading "Not available yet" | **Keep** | the mock is the layout spec; the gap is honest and closes with 6a |
| Q7 | "Waiting for you" before who decides is recorded | **Badge and "In your portfolio" from the waiting decisions; "For you" not available yet** | the control earns its place now; nothing is attributed to a person falsely |
| Q8 | Outcomes L3 holds the range category cards (with 1a's line) and the objectives matrix | **Yes** (D2) | reviewed content is kept and placed where outcomes live; the mock's insight block has no source |

I would like the owner to weigh in on Q1 and Q2 at the walkthrough. Everything else can stand on the defaults.

## 10. Done (questions; each can fail)

1. Does the rail equal §2.1, and does every §2.4 address land on its home with the range kept (R1, R2, `iaRouteMap`)?
2. Does the Portfolio show exactly three tabs, the Overview the month, with no old category card on it, and does
   `deep_dive_gates.cjs` pass at `/portfolio?month=2026-10`?
3. Is each list drawn by the one component? Do the tiles equal the list, and does the address restore the view? Does each
   row have one target?
4. Does E1 return World A's rows exactly, with the Sites gap tile = the Overview's tile 2, string for string?
5. Are there six Site tabs on every vertical, with object pages showing three-part crumbs?
6. Does the inbox badge equal the Decisions waiting tile?
7. Does every page pass at 390 (no sideways scroll), light and dark, with fonts on the scale?
8. Does every plant in §6 fail its named check, and is every MOCK DEVIATION in §7 registered? Is the mid-build count 0?

## 11. Scope limits

- IA-P does not build the content of IA-2c (Asset pages, Assets & cover), IA-2d (drawer addresses, Finding and Action record
  pages in the IA shape) or IA-2e (statement, Settings). Their routes stay as today until the mock's units land and are
  ruled for the real app.
- IA-P builds no plan, no decision record and no person attribution.
- The only backend changes are E0 and E1.
- No reviewed figure, word or read changes, except where §3 and §6 name the move.

**Packet:** `specs/IA-P-product-shape/packet-IA-P1.md` and `packet-IA-P2.md`. Each holds the shots by path, every plant's
failing output, the register rows and the mid-build count.
