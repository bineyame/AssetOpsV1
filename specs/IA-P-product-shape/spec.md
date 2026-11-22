# IA-P: the real app on the agreed shape (implementer spec)

Status: live, **rev 2** (2026-11-22: the Overview follows the top-bar range, owner Q2; `spec-period.md`), handshake next.
Architect (Claude). Rev 1 was merged earlier on 2026-11-22.
Owner request: `owner/owner-merge-on-accept-ia-shape-k10-2026-11-22.md`. The owner reviews once the product is close to the
shape, then iterates. UI slices merge on review ACCEPT, with one combined walkthrough at the end.

**Decisions:** `rulings.md`, D-IAP.1 to D-IAP.23 (rev 2: D-IAP.15 on). **Binding parts:** this file and `spec-period.md`. **Reviewer guide:** `reviewer-guide.md`. `USER_REVIEW_REQUIRED: true`.
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
- this spec's §2, `spec-period.md` P.1 (every unit) and the §6 card of your unit.

## 0. Existing, then new

**What exists today and stays.** The live product (`frontend/src`) already has the reads an executive needs:
- the estate Portfolio read (`/api/estate/portfolio`): placement queue, value cards, objectives, progress;
- the Finding, Action, Evidence and Financials roots;
- the month read built by 5c (`/api/portfolio/month`, `DeepDiveMonth.tsx`): contribution against target for one calendar
  month, the bridge, cash, the four outcome cards, every figure with its evidence word;
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
             Sites               Overview = the range's months (5c):   [Financials][Evidence][Setup]
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
- the outcome and its drivers are on the Overview (5c's bridge, for the whole months in the range);
- the choices waiting are in Decisions and in "Waiting for you";
- the Actions are in Actions, and what changed is in Results.

That loop is the value beyond a monitoring tool (the demo objective). A person stays in it: AssetOps proposes, and the team
chooses and acts under their own names (6a and 3C2 record who).

## 1. Outcome

An operator executive opens the served app and sees:
- the approved menu;
- a three-tab Portfolio whose Overview shows contribution against target for the whole months in the top-bar range;
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
| ASSURANCE | Results | `/results` | live | `book` | P1 unavailable, P3b live |
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
| `/portfolio` (old Overview: cards, pulse, top three) | `/portfolio` is 5c's screen on the range (§3). Cards go to Outcomes L3, the top three to Overview L2 (Decisions rows), the pulse is retired (D-IAP.12) | kept, re-housed | P3b |
| `/portfolio/month?month=YYYY-MM` | `/portfolio?from={first day}&to={last day}` of that month; `month` dropped; it wins over a range in the address; an invalid or absent month goes to `/portfolio` (D-IAP.18) | alias | P3b |
| `/portfolio/act-first` (`?lens=`) | `/decisions` (`lens` kept as the Finding-type facet) | alias | P2 |
| `/portfolio/outcomes` | `/portfolio/outcomes` (L2 Sites rows from P4) | kept | P3b, P4 |
| `/portfolio/opportunity` | `/portfolio/demand-and-capacity` | alias | P3b |
| `/portfolio/changes` | `/results` | alias | P3b |
| `/portfolio/scope` | `/evidence` (its second section, "Scope & coverage") | alias | P3b |
| any other `/portfolio/:tab` | `/portfolio` (today's rule) | kept | — |
| `/sites` | `/sites` (the Sites list; its figures follow the range, D-IAP.19) | kept, rebuilt as a list | P4 |
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
| — | `/decisions` (new list), `/results` (new page), `/portfolio/demand-and-capacity` (new tab), `/evidence/records` (new tab) | new | P2, P3b, P1 |

The Plan (`/plan`) and the inbox have no route. The Plan is an unavailable rail item. The inbox is a drawer opened from the
top bar (IA-1 §4.3: "no address until IA-2d").

## 3. The Overview: 5c's screen on the top-bar range (D-IAP.2, D-IAP.15 to D-IAP.19)

**Owner, 2026-11-22.**
- Q1: "Month is the Overview". `/portfolio` renders 5c's screen, and there is no fourth tab.
- Q2: "Follow the date range". The Overview follows the top-bar range like every other page. Rev 1's month exception
  (D-IAP.2's SR-4c month span, and the server's default month) is withdrawn (D-IAP.15).

**The period rule** (`spec-period.md` P.1, binding). Contribution against target is kept per whole calendar month. So the
Overview counts the whole, closed months inside the range. Each month it cannot count is named on the page, and nothing is
cut by day. E2 (`GET /api/portfolio/period?from=&to=`) resolves the range on the server and returns a mode:

| Mode | When | What the Overview renders (hub shape, 5c classes) |
|---|---|---|
| `month` | exactly one served whole month | 5c's month screen for E2's month, unchanged in L1 to L3. The header's ‹ › links come from E2's `nav` and set the range to that month (`from` and `to` replaced, every other parameter kept). E2's `notes` sit under the header |
| `period` | two or more | the period hub (`spec-period.md` P.5). L1 is the headline and the four tiles, summed. L2 is the Decisions rows and Actions in hand. L3 is "Month by month" (one row per month, its link setting the range to that month) and "By outcome" (MD-IAP-10) |
| `none` | no served whole month (a 7-day range, "This month", a range inside one month, or a store with no snapshot) | the header, E2's `notes`, the link "Show {month}" (E2's `suggest`, setting the range to the latest served month), then L2. L1 and L3 are omitted (MD-IAP-11). No figure is invented |

**Consequences.**
- **The top-bar note (SR-4c; D-IAP.18).** The Overview declares `useDeclareRangeSpan(shown.from, shown.to)` only when E2's
  `shown` is not null, that is, when the months counted differ from the range. The bar then says "This page shows part of
  it". When the range is exactly whole months, or in mode `none`, nothing is declared and the bar says "All pages". The
  browser does no date arithmetic for this: `shown`, `nav` and `suggest` carry their days from the server.
- **Fresh entry (D-IAP.21; owner may veto, Q9).** When the address has no range and no session range is stored,
  `entryRange('/portfolio')` gives "Last month" (a WARM-1 preset), not "Last 7 days". The front page then opens on figures.
  Every other page's entry stays "Last 7 days".
- **Overview L2.** 5c's "Decisions" panel (MD2) becomes the Decisions list's rows for the range: capped at 6, no tools,
  then "View all {n}" to `/decisions` with the range (IA-2b §6). "Actions in hand" stays beside them, from the month body in
  mode `month` and from the period body in mode `period`.
- **The old Overview's content.** The four range category cards (with 1a's scope line) move to Outcomes L3, and the top
  three becomes Overview L2. The pulse is retired: each of its links now has a menu item or tab. The coverage line and the
  scope disclosure move to Evidence & records › Coverage.
- **One figure.** A month row's gap is that month's Overview tile 2, string for string. The period's tile 2 is their exact
  sum. For the same range, E1's `total.gap` is the Overview's tile 2 (gate S1, on a one-month and a two-month range).
- **No tenant or no read:** E2's 503 text with "Try again". A store with no snapshot is mode `none`, with the months'
  `missing` sentence.

**The page by Site-type range matrix** (the owner's range rule; every page follows the range for every Site type):

| Page | Mini-grid | Cold-chain | EV charging |
|---|---|---|---|
| Overview (E2 and 5c) | counted per whole month | named as not compared (5c's `out` reason and "Compared for k of n Sites") | the same as cold-chain |
| Outcomes L1 and L2, Sites list (E1) | rows with figures for the same months | a row reading "Not available yet" | the same |
| Outcomes L3, Demand & capacity, Decisions, Findings, Actions, Results, Evidence | the range, as today | the range | the range |

## 4. What each surface reads (D-IAP.8, D-IAP.9, D-IAP.17, D-IAP.20)

### 4.1 The reads per surface

Every read below exists except E1 and E2. E0 adds one field to an existing body.

| Surface | Reads (client · endpoint) | Notes |
|---|---|---|
| Overview | E2 `portfolioPeriodClient.fetchPeriod(from, to)` · `GET /api/portfolio/period`; in mode `month`, `fetchDeepDiveMonth(served[0])` · `GET /api/portfolio/month`; `estateClient.portfolio` · `GET /api/estate/portfolio` (the range, lens `all`, every page) | figures come only from E2 and the month read; the rows only from the placement queue |
| Outcomes | E1 `GET /api/portfolio/sites?from=&to=` (the range); `estateClient.portfolio` (the range: E0 `waiting_by_site`, and L3 with `getOutcomeSummary`) | L1 headline (or E1's notes) and L2 rows from E1; L3 range cards as today |
| Demand & capacity | `estateClient.portfolio` (the range) | `OpportunityPanel` as today |
| Decisions list | `estateClient.portfolio` (the range, lens `all`, every page) | one row per placed Finding (D-IAP.3) |
| Findings list | `estateClient.findings` (the range, lens `all`, state `all`, every page) + the Decisions read (same key, shared cache) | "Its decision" joins on `finding_id` |
| Actions list | `estateClient.actions` (the range, every page) | |
| Sites list | `siteDirectoryClient` · `GET /api/sites`; E1 (the range); E0 | the rows come from E1, in E1's order; E1's notes under the header |
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

### 4.3 E1: `GET /api/portfolio/sites?from=&to=` (new; D-IAP.9, D-IAP.20)

E1 is specified in `spec-period.md` P.8 (binding): the Sites rows for the same months as the Overview, ordered on the
server, with their statements and tests. It moved there in rev 2 because it shares E2's resolver.

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

## 6. Units (each 1 to 3 commits; the app works after each; D-IAP.13, D-IAP.22)

Two parts, one branch each, one discovery review per part:
- **IA-P1** is P1, P2, P3a and P3b (5.75 units), on `task/IA-P1-frame-portfolio`.
- **IA-P2** is P4 to P7 (5.0 units), on `task/IA-P2-sites-site-inbox`, branched from IA-P1's merge.

**Range pages (D-IAP.19; a class fix).** Each unit that lands a page whose content follows the range adds it to
`RANGE_PAGES` and `FILLED_PAGES` (`ui/sharedRange.ts`): P1 `/evidence/records`, P2 `/decisions`, P3b `/results` and P4
`/sites`. The shared-range test asserts the bar says "All pages" on each one.

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
  - `ui/sharedRange.ts` (`/evidence/records` as a range page);
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
  - `iaRoutes.ts` (Decisions live);
  - `ui/sharedRange.ts` (`/decisions` as a range page).
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

### P3a: E2, the period read (1.5 units; IA-P1)

- **Files:**
  - `deep_dive/period.py` (new: `Period`, `MonthServed`, `month_days`, `resolve`, `header`, `period_view`);
  - `deep_dive/read.py` (`period`);
  - `deep_dive_api.py` (the route);
  - `i18n/statements/en/portfolio_period.py` (new);
  - the fixtures `frontend/src/estate/__tests__/fixtures/iap/period-month-2026-10.json`, `period-period-2026-09-10.json`
    and `period-none-2026-11.json`, written from the view (test 10 keeps them current).
- **Tests first:** `spec-period.md` P.7, tests 1 to 10.
- **Plants:**
  - `dayscut` (`resolve` counts a PARTIAL month) fails test 1;
  - `onefig` (a month row's gap formatted again instead of taken from `V_m.tiles()[1]`, with one rounding changed) fails
    test 3;
  - `handbuilt` (an f-string sentence in `period.py`) fails the SC-1 guard.
- `view.py`'s month view and its tests are unchanged. `git diff` there is empty.

### P3b: the Portfolio hub on the range (1.75 units; IA-P1)

- **Files:**
  - `estate/portfolioWords.ts` (three tabs: overview `null`, outcomes `outcomes`, demand `demand-and-capacity`);
  - `estate/PortfolioTabs.tsx` (draws `SectionTabs`; carries the address range);
  - `estate/portfolioPeriodClient.ts` (new; `fetchPeriod(from, to)`; a body whose `schema` is not `portfolio-period-1` is
    an error);
  - `estate/PortfolioOverview.tsx` (new; the `/portfolio` frame):
    - it reads E2 for the address range and renders by mode (§3);
    - it declares `shown` (SR-4c);
    - it shows "Preparing the figures…" while loading, and E2's refusal texts with "Try again";
  - `estate/DeepDiveMonth.tsx`:
    - it takes `month`, `nav` and `notes` as props and no longer reads `?month=`;
    - the header links come from `nav` (§3);
    - the notes are `<p class="dd-period" role="note">` in the header;
    - L2's Decisions panel becomes `HomeList` decisions, `{tools: false, tiles: false, cap: 6}` for the range, with "View
      all {n}" to `/decisions` and the range;
    - its tile, outcome-card and actions-panel markup is exported as `DdTiles`, `DdOutcomes` and `DdActions`. L1 and L3
      are otherwise unchanged;
  - `estate/PortfolioPeriod.tsx` (new; the period body):
    - the header with `<b>{period_words}</b>` and the notes;
    - L1 `dd-lead` and `DdTiles`;
    - L2 as in the month;
    - L3 "Month by month": a `<table>`, the first cell `<th scope="row"><Link>{month_words}</Link></th>` (one target per
      row, setting the range to that month), the other cells text with the gap word as a chip; then `DdOutcomes`;
  - `ui/sharedRange.ts` (`entryRange(pathname?)` gives `lastmonth` for `/portfolio` with no stored range; `/results`
    joins `RANGE_PAGES` and `FILLED_PAGES`);
  - `estate/EstatePortfolio.tsx`, `estate/Results.tsx`, `estate/EstateEvidence.tsx`: as in rev 1 (the Overview branch,
    pulse and `TopThree` removed; outcomes and demand kept; `ProgressPanel` and the scope section moved verbatim);
  - `App.tsx` (`/portfolio` → `PortfolioOverview`; `/portfolio/:tab` for outcomes and demand; `/results`; the aliases of
    §2.4 for P3b, `/portfolio/month` with its `to` function using `month_days`' frontend twin `monthDays(code)` in
    `sharedRange.ts`);
  - `tools/deep_dive_gates.cjs` (URL argument; it also answers `/api/portfolio/period*` with `period-month-2026-10.json`
    and `/api/estate/portfolio*` with the IA-P fixture; the checks are unchanged);
  - the DDR runbook's S7 line, which now reads `/portfolio?from=2026-10-01&to=2026-10-31`.
- **Tests first:**
  - `estate/__tests__/portfolioHub.test.tsx`:
    - the three tabs keep the range;
    - mode `month` reads the month read for `served[0]`, not for the range's `to`;
    - the nav links equal E2's `nav` days;
    - mode `period` renders one link per month row and no `[data-portfolio-card-value]`;
    - mode `none` renders the notes and the suggest link, and no L1 or L3;
    - the L2 rows are the Decisions rows for the range, at most 6, then "View all {n}";
    - `/portfolio/month?month=2026-10` → `/portfolio?from=2026-10-01&to=2026-10-31`, also when the address held another
      range;
    - the span is declared exactly when `shown` is not null;
    - `entryRange('/portfolio')` with an empty session is last month, and `entryRange('/findings')` is 7 days;
  - `DeepDiveMonth.test.tsx`: the decisions-panel and nav assertions are updated (named in the packet); every other
    assertion is kept;
  - `Results.test.tsx`; the `estateEvidence` scope section.
- **Plants:**
  - `fourtab` (a fourth tab) fails `portfolioHub` and gate H1;
  - `window` (the tabs lose the range) fails `portfolioHub`;
  - `twofig` (the old category cards rendered on the Overview) fails gate H2;
  - `browsermonth` (the month read for the range's `to` month) fails `portfolioHub`;
  - `span` (`shown` ignored) fails `portfolioHub` and gate H6.
- **Gates added:**
  - **H1** three tabs in §2.2's order;
  - **H2** in every mode, the Overview has at most 6 blocks and holds no `[data-portfolio-card-value]`;
  - **H3** `deep_dive_gates.cjs` passes at `/portfolio?from=2026-10-01&to=2026-10-31`;
  - **H4** `/portfolio?from=2026-09-01&to=2026-10-31` (mode `period`): the hub regions, R4 at 390, the bar's "All pages",
    and each month row landing on its month;
  - **H5** `/portfolio?from=2026-11-15&to=2026-11-21` (mode `none`): the notes are visible, and "Show October 2026" lands on
    October's range and renders the month;
  - **H6** `/portfolio?from=2026-10-01&to=2026-11-21`: the bar's tag is `data-shared-range-focus="inside"`.
- **Shots:** the three tabs and the Overview in each mode, `/results` and `/evidence` with the scope section, at the three
  widths, light and dark.
- **IA-P1's review follows P3b.**

### P4: the Sites list, Outcomes, E0 and E1 (2.0 units; IA-P2)

- **Files:**
  - backend: `deep_dive/sites.py`, `deep_dive/read.py` (`sites`), `deep_dive_api.py` (route),
    `i18n/statements/en/portfolio_sites.py`, `estate/portfolio.py` (E0);
  - frontend: `estate/portfolioSitesClient.ts` (new; schema check `portfolio-sites-1`), `estate/sitesList.tsx` (new),
    `shell/SitesFrame.tsx` (renders the Sites list; the directory table and the Lifecycle column are removed),
    `estate/EstatePortfolio.tsx` (outcomes: L1 E1 headline; L2 `HomeList` sites `{tools: false, tiles: false}` with "Show
    all" to `/sites?show=all`; L3 `CategoryCards`, then `ObjectivesPanel` inside `Disclosure` "Each Site's objectives"),
    `estate/estateClient.ts` (E0 type), `ui/sharedRange.ts` (`/sites` as a range page). In mode `none` the Sites tiles
    "Below target" and "Gap to target" read "Not available yet", the target facet is not offered, and E1's notes show
    under the header. Outcomes L1 shows them in place of the headline.
- **Tests first:** §4.2's and `spec-period.md` P.8's backend tests (1 to 8); `estate/__tests__/sitesList.test.tsx`:
  - World A's E1 fixture: the rows in E1 order; the gap tile "−$852.00" equals the Overview's tile 2 string; the target
    facet; "Not available yet" rows last; the Outcomes rows = the Sites list rows;
  - World P's fixture: the gap tile "−$1,704.00";
  - mode `none`: the tiles and the notes.
- **Plants:**
  - `sum` (one Site effect altered in the view) fails test 4;
  - `order` (registry order) fails test 1;
  - `browsersort` (the frontend sorts by gap) fails `sitesList` (the order must be E1's);
  - `handbuilt` (an f-string sentence in `sites.py`) fails the SC-1 guard.
- **Gates added:** **S1** `/sites` tile "Gap to target" = `/portfolio` tile 2, by text, at 2026-10-01 to 2026-10-31 and at
  2026-09-01 to 2026-10-31.
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
| MD-IAP-3 | Demand & capacity L1 `uxChain` | D1 | no portfolio demand-to-capacity read; the region is omitted (an empty slot omits its region); L3 as the mock | P3b |
| MD-IAP-4 | Inbox "For you", and the plan row | D1 | who decides is not recorded (6a); there is no plan | P6 |
| MD-IAP-5 | Scope on the Overview (the month read has no scope) | D5 | a chip says the page shows every Site. Resolving unit: a scoped month read (to be specified) | P7 |
| MD-IAP-6 | Actions list tiles | D2 | today's four server figures kept as a caption line under the list tiles (extended, not dropped) | P2 |
| MD-IAP-7 | Outcomes L3 `uxInsight` ("Sites that look alike") | D1 + D2 | no live source (D1); the range category cards and the objectives matrix sit there instead (D2, flagged: Q8) | P3b, P4 |
| MD-IAP-8 | Site paths `/setup`, `/operations` (IA route names) | D2 | today's segments kept, labels changed (Q5) | P5 |
| MD-IAP-9 | Group words "Mini-grids", "Cold rooms", "EV depots" | D4 | the live product's domain words, as the Type column has always read | P4, P7 |
| MD-IAP-10 | Overview L3 "Where the gap comes from" and cash, on a range of two or more months | D2 | "Month by month" stands in their place: each month's row opens that month's full bridge and cash (one click). A summed bridge is Q10 | P3b |
| MD-IAP-11 | Overview L1 and L3 on a range with no served whole month | D1 | figures exist only per whole month; the page states why and links to the latest served month. Nothing is cut by day | P3b |

5c's MD2 and MD7 close in P3b (the month is the Overview).

## 8. Size, and the effect on the world ladder and the WK and DDR serves (D-IAP.22)

**Size: 10.75 units, about 18 commits** (rev 1 was 8.5; rev 2 adds E2 and the three modes).
- IA-P1 is 5.75 units: P1 1.0, P2 1.5, P3a 1.5, P3b 1.75.
- IA-P2 is 5.0 units: P4 2.0, P5 1.0, P6 0.75, P7 1.25.
- Each part is under the 6-unit cap.
- Opus does the first builds; Sonnet does the fix rounds. There is one discovery review per part (W5: each part now adds
  money figures and an endpoint).

**The world ladder.** `tools/world.py` keys the world on `CODE_PATHS` (`backend/assetops_backend`, …), not on `frontend/`.
- P3a (E2) and P4 (E0, E1) change `backend/assetops_backend`. So each part's merge stales the L2 template, naming the
  `code` part.
- The coordinator rebuilds the current rung once after each part merges, before the next WK run. If both parts merge
  before a WK run, one rebuild covers both. There is no migration.

**WK.** The walk pages (`backend/conversions/walk-layer4-v1.json`) all still land:
- `/portfolio` with no range opens on last month (D-IAP.21);
- `/portfolio/month?month=2026-10` aliases to `/portfolio?from=2026-10-01&to=2026-10-31`;
- `/sites`, `/sites/{code}`, `/findings`, `/actions`, `/evidence` and `/financials` stay.

New reads on those pages: E2 and the estate portfolio read on `/portfolio`, and E1 on `/sites`. None returns 500 on a
NO_SNAPSHOT tenant (mode `none`, `spec-period.md` P.7 test 6, E1 test 3). P7 adds `/decisions`, `/results`,
`/portfolio/outcomes` and `/portfolio/demand-and-capacity` to `pages`, which changes the walk definition only. S4's census
is unaffected: E0 enlarges stored `chain_response` bodies, which may grow (D-WK.16).

**DDR.** S7's browser path `/portfolio/month?month=2026-10` aliases to the October range, and the month API body is
unchanged (E1 and E2 are separate routes). The runbook's step text reads `/portfolio?from=2026-10-01&to=2026-10-31` after
P3b.

## 9. Decision queue (W3; the defaults apply now)

| # | Question (owner) | Default | Why |
|---|---|---|---|
| Q3 | Until decision records exist (6a, awaiting P6), Decisions lists the Findings waiting for an agreed Action | **Yes**, labelled MD-IAP-2 | Act first's reviewed queue moves to its approved home instead of an empty list |
| Q4 | Plan in the menu before a plan record exists | **"Not available yet"** | a mock plan shown live would present modelled figures as the operator's |
| Q5 | Site paths keep `foundation` and `work` under the new labels | **Keep** | 30+ addresses and their tests unchanged; the labels are what people see |
| Q6 | Decisions keeps the mock's Due and Who decides columns, reading "Not available yet" | **Keep** | the mock is the layout spec; the gap is honest and closes with 6a |
| Q7 | "Waiting for you" before who decides is recorded | **Badge and "In your portfolio" from the waiting decisions; "For you" not available yet** | the control earns its place now; nothing is attributed to a person falsely |
| Q8 | Outcomes L3 holds the range category cards (with 1a's line) and the objectives matrix | **Yes** (D2) | reviewed content is kept and placed where outcomes live; the mock's insight block has no source |

| Q9 | A fresh entry to the Portfolio (no range in the address or the session) opens on "Last month", not "Last 7 days" | **Yes** (D-IAP.21) | the front page opens on figures; a 7-day range holds no whole month. Without it, the page opens on the notes and "Show {month}" |
| Q10 | On a range of two or more months, Overview L3 shows "Month by month" with each month's bridge one click away, not a bridge summed across months | **Month by month** (MD-IAP-10) | each figure stays the one the month's accounts hold; a summed bridge would need a cross-month split rule (prices and rates do not add across months) |

Q1 and Q2 are answered (owner, 2026-11-22; D-IAP.15) and are removed from this queue. I would like the owner to weigh in on
Q9 and Q10 at the walkthrough. Everything else can stand on the defaults.

## 10. Done (questions; each can fail)

1. Does the rail equal §2.1, and does every §2.4 address land on its home with the range kept (R1, R2, `iaRouteMap`)?
2. Does the Portfolio show exactly three tabs, with no old category card on the Overview? Does the Overview follow the
   range in all three modes (H3 to H6), with each uncounted month named? Does `deep_dive_gates.cjs` pass at the October
   range?
3. Is each list drawn by the one component? Do the tiles equal the list, and does the address restore the view? Does each
   row have one target?
4. Do E1 and E2 return World A's and World P's literals exactly, with the Sites gap tile = the Overview's tile 2, string
   for string, on one-month and two-month ranges?
5. Are there six Site tabs on every vertical, with object pages showing three-part crumbs?
6. Does the inbox badge equal the Decisions waiting tile?
7. Does every page pass at 390 (no sideways scroll), light and dark, with fonts on the scale?
8. Does every plant in §6 fail its named check, and is every MOCK DEVIATION in §7 registered? Is the mid-build count 0?

## 11. Scope limits

- IA-P does not build the content of IA-2c (Asset pages, Assets & cover), IA-2d (drawer addresses, Finding and Action record
  pages in the IA shape) or IA-2e (statement, Settings). Their routes stay as today until the mock's units land and are
  ruled for the real app.
- IA-P builds no plan, no decision record and no person attribution, and no bridge summed across months (Q10).
- The only backend changes are E0, E1 and E2.
- No reviewed figure, word or read changes, except where §3 and §6 name the move.

**Packet:** `specs/IA-P-product-shape/packet-IA-P1.md` and `packet-IA-P2.md`. Each holds the shots by path, every plant's
failing output, the register rows and the mid-build count.
