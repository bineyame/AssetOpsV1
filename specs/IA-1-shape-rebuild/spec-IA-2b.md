# IA-2b: the list shape (implementer spec, rev 1)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away row 46). Rulings D-IA.61 to D-IA.66 in `rulings-5.md`;
reviewer entry `reviewer-guide-IA-2b.md`. This file is IA-2b's card for `spec.md` §5 (the IA-2 plan's "IA-2b" row), written
as a separate file so it does not collide with IA-2a's open edits to `spec.md` §5.1. `spec.md` §0, §6, §7 and §8 apply whole;
where this file is more specific it governs. Handshake format: `.ai/RULES.md` §4 (one combined round, questions in
`handshake.md` under "IA-2b", mid-build questions in `mid-build-questions.md` under "IA-2b").

**Read first:** the proposal page `Docs/design-system/ia-proposal/index.html` §4 figure "2 · Home list" (tiles "count · count ·
at stake"; "Filters · sort · search · scope chip"; rows; "Show all 42"; "row → page or drawer") and §3's rules ("One
drill-down grammar", "Wayfinding", "One store, many scopes", "Nothing unbuilt is reachable", "The scope picks the Sites"),
and its "The same shape at 3, 30 and 300 Sites" figure; `rulings.md` D-IA.9, D-IA.10, D-IA.25, D-IA.27; `rulings-2.md`
D-IA.34; `rulings-4.md` (on IA-2a's branch) D-IA.54 to D-IA.59; the owner's standing UI brief
(`owner/owner-ui-standing-brief-2026-11-20.md`).

## 1. Outcome

An operator executive opens Decisions, Findings, Actions or Sites from the menu and sees one home list per object, drawn by
one component: up to four count tiles that equal the list, one row of filters, sort, search and the scope, at most 10 rows
then "Show all {n}", and rows that each open one thing. The address holds the whole view, so Back and a shared link restore
it. The Portfolio's Outcomes tab is that component (the Sites list) without its controls. The hubs' queues become the same
rows, scoped and capped, with "View all {n}"; the plan links to its released Actions (G1's last unmeasured surface).

## 2. Split, base and the stop point (D-IA.61)

| Part | Units | Landing ID | Delivers | Depends on the owner's IA-2a walkthrough? |
|---|---|---|---|---|
| IA-2b1 | 1 to 3 | `IA-2b1` | the component, the four home lists live, aliases, the scope menu on lists, crumbs, search index, the Outcomes fold | No: it reads IA-2a's state and release words only through the one-source helpers, so a change there flows in by construction |
| IA-2b2 | 4 and 5 | `IA-2b2` | hub queues as the component (one-target rows, "View all {n}"), the plan's link to its released Actions, G1's surface | **Yes** (see the stop) |

**Size:** 5 units (about 8 commits), within the 6-unit cap. One branch, two reviews (one per part, discovery depth, W5).

**Base.** `task/IA-2b-list` in `/opt/assetecon/AssetOpsV1-ia2b`, branched from the head of IA-2a's latest accepted fix
round (`task/IA-2a-plan` after the D-IA.58 to D-IA.60 round merges into it; at this writing its answers are on
`task/IA-2a-review2-answers` `b2fb5de65`). Each later IA-2a fix round is merged in, never rebased. IA-2b never merges before
IA-2a; once IA-2a merges, merge `main` in. Touch `vNEXT/` only (plus its `tools/`, `walkthroughs.md`, this folder and
`.agent/mock-departure-register.md`). Evidence `/opt/assetecon/evidence/IA-2b/<unit>/`. Browser checks through
`tools/heavy-slot.sh` as `spec.md` §0. Never ports 5490 or 8990, or Docker.

**The stop point (owner's IA-2a walkthrough).** Unit 4 does not start until (a) the owner has walked IA-2a and the coordinator
has recorded the verdict in a verbatim owner file, and (b) any IA-2a change it asks for is merged into this branch. Units 4
and 5 change what the owner is walking or has just walked: the plan's L1 (a new link line, identical on the four tabs, D-IA.43),
the Overview and Site queue rows the walkthrough passes through, and the hub's one primary ("Decide" leaves the rows, D-IA.65).
If the owner changes the plan's L1, its tab grammar, its state or release words, or asks to keep a "Decide" button on the
hubs, unit 4's card is re-ruled first (`rulings-5.md`), not patched in the build.

**The 5c rule** (RC6; `owner/owner-start-ia2a-2026-11-21.md`): 5c takes the UI lane the moment its gates hold. Finish the
commit in hand, run the fast check-all, push, and write `Stopped after <unit/commit> at <sha>; resume at <next>` at the top of
`packet-IA-2b1.md` (or `-2b2`). Every commit boundary leaves the screens as they are and every gate green.

## 3. The component (D-IA.62)

### 3.1 The model (pure, `ia-shapes.js`)

`iaListModel(def, items, q, scope)` returns `{ rows, shown, hidden, n, groups }`:
1. **Scope:** keep items with `def.site(item)` in the scope (`all`; `group:<g>` by `iaVertical`; `site:<k>`). Lists with no
   `site` ignore scope (none in IA-2b).
2. **Facets:** for each `def.facets[i]` with a value in `q[f.key]` that is one of its option values, keep items with
   `f.of(item) === value`. A value that is not an option is ignored (the D-IA.35 L4 rule, made general).
3. **Search:** `q.q` split on whitespace, lower-cased; keep items whose `def.text(item)` (lower-cased, tags stripped) contains
   every word (the palette's rule, `uxPaletteFill`).
4. **Sort:** `def.sorts` entry named by `q.sort`, else the first; stable, ties in store order.
5. **Cap:** 10 unless `q.show === 'all'`. Ranking: items with `def.keep(item)` true first, then the rest, each in sort order;
   `shown` = the first 10 of that ranking **displayed in sort order**; `hidden` the rest in sort order (D-IA.34, generalised).
   `n = rows.length` (after filters, before the cap).
6. **Groups** (D-IA.27, generalised): when `def.group` exists and `rows` holds more than 10 items in more than one group, the
   table renders one `tbody` per group (its word and count), sort within group, and the cap applies per group.

`iaListHref(key, ctx, change)` (pure) writes the canonical address: `#/<key>` then the parameters in this fixed order, each
only when not its default: `scope` (omitted for `all`), the facets in `def.facets` order, `sort` (omitted for the first),
`q` (omitted when empty), `show=all`. `change` overrides; a facet change or a search drops `show`.

### 3.2 The markup (shape `list`)

```html
<section data-shape="list" data-ia-list="{key}">
  <div data-level="L1"><div class="heroes ux-kpis">{tiles}</div></div>
  <div data-level="L2">{tools}{table or empty state}{more}</div>
</section>
```

- **Tiles:** `uxKpi(label, '<span data-qty="{key}:{qty}:{query}" data-qty-role="{total|part}">{value}</span>')` per §4.
  `{query}` is the canonical query without `show` (so a key is per view). At most 4 (`shape_check` item 1).
- **Tools:** `<form class="ia-list-tools" data-ia-list-tools="{key}" role="search" aria-label="Filter and sort {plural}">`,
  in this order: one `<label>{facet label} <select name="{facet}"><option value="">All</option>{options}</select></label>` per
  facet whose options number at least 2 in the scope; `<label>Sort <select name="sort">{sorts}</select></label>`;
  `<label>Search <input type="search" name="q" value="{q}"></label><button type="submit" class="button">Search</button>`;
  when the scope is not `all`, `<span class="ia-chip">{group word or Site name} · <a href="{iaListHref(key, ctx, {scope:'all'})}">All sites</a></span>`;
  when any facet or `q` is set, `<a class="ux-link" href="{the address with scope only}">Clear filters</a>`. Each control's
  value is the address's. No control is drawn when the store in scope holds fewer than 3 items (as `uxQueue`'s tools).
- **Table:** `<div class="table-wrap"><table class="ia-list ux-stack" id="ia-list-{key}">` with `<thead>` from the def's
  column words, one `<tr data-row="{row key}">` per shown item, first cell `<th scope="row"><a class="ia-row-go" href="{target}">{title}</a>{small}</th>`, every other cell `<td data-label="{column}">` holding text only (labels as
  `status-pill` spans, never buttons or links). **One target per row** (D-IA.9): the row's only interactive element is that
  link; `ia.css` stretches it over the row (`.ia-list tbody tr{position:relative}.ia-row-go::after{content:"";position:absolute;inset:0}.ia-list tbody tr:focus-within{outline:2px solid var(--focus,#2563eb);outline-offset:-2px}`).
  An item with no live target renders its title as text (no stretched link).
- **More:** the def's hidden line when it has one (decisions: `iaCapMore(hidden ids)`), then, when `hidden` is non-empty,
  `<p class="ux-more"><a class="ux-link" href="{iaListHref(key, ctx, {show:'all'})}" data-qty="{key}:n:{query}" data-qty-role="total">Show all {n}</a></p>`.
- **Empty:** store empty in scope: `<p class="ux-empty" role="status">{def.none}</p>`; filters leave nothing:
  `<p class="ux-empty" role="status">Nothing matches these filters. <a class="ux-link" href="{scope only}">Clear filters</a></p>` (tools still drawn).

### 3.3 Behaviour (one listener, `ia-routes.js`)

- A `change` on a `select` in `[data-ia-list-tools]`, or a `submit` of the form (default prevented), sets
  `location.hash = iaListHref(key, ctx, { [name]: value })`. Before that it stores `IA_LIST_KEEP = { name, y: scrollY }`.
- After the render that follows, `iaBind` restores `scrollTo(0, IA_LIST_KEEP.y)` (instant) and focuses
  `[data-ia-list-tools] [name="{name}"]` (`preventScroll`), then clears `IA_LIST_KEEP`. A list change is not a tab switch
  (D-IA.58 does not run). A link (Show all, Clear filters, the chip) is an ordinary navigation: top of page.
- **The scope menu on a list** (`iaScopeEntries`): on a `list` route every entry keeps the list's facets, sort and `q`
  (drops `show`); the Site entries scope the list (`#/{key}?scope=site:{k}&…`) instead of opening the Site. Other shapes
  are unchanged.

### 3.4 Format (D-IA.59)

Counts are whole numbers. Money on a list: a total shown beside its parts takes cents only if a part needs them: the Sites
gap tile is the sum of the rows' rendered whole-dollar gaps when that sum equals the whole-dollar rounding of the exact sum;
otherwise the tile and every row gap render with cents. `qty_check`'s format assertion covers it.

## 4. The four lists (D-IA.63)

Routes: `{ id, shape: 'list', object, home, unit: 'IA-2b1', tab: null, tabGroup: null, title, crumbs: [[H1]], render: ctx => shapeList(ctx, key) }`.
H1 and document title: the menu label. Stores: each def reads the one source the hubs and plan read; none is copied.

| List · object · home | Store (one source) | Row target (one) | Columns (`data-label` words) |
|---|---|---|---|
| `decisions` · decision · Decisions | `iaDecIds(op, {kind:'all'})` (ATTN order) | `decision/{id}` | Decision (`uxTitle(d.q, site)`, small: the issue labels joined " · ") · Site · State (`uxDecState(id).label`) · At stake (`uxStake(id)`) · Due (`fdate(due)` or "No deadline") · Who decides (`who(op, deciderOf(id).p)`) |
| `findings` · finding · Findings | `uxFindingRows(op)` | its decision, `decision/{x.d.id}` (interim: `finding/:id` is IA-2d's; D5) ; none when no decision | Finding (`x.text`) · Site · Heading (`LENS[x.heading][0]`) · Its decision (`x.st.label`, or "No decision yet") |
| `actions` · action · Actions | `WF(op).actions` | the decision whose `opts` holds `a.item`, else `plan` (interim: `action/:id` is IA-2d's; D5) | Action (`a.action`, small: `itemShort(op, a.item)`) · Owner (`who`) · Due (`fdate(a.due)`, small `dueWords`) · State (the label of `actionState(op, a, planCaseIds(op).includes(a.item))`) |
| `sites` · site · Sites | `iaOutcomeRows(op)` | `site/{key}` | D-IA.27's six: Site · Group · Contribution (cost: "Cost per required departure met") · Gap to target · Largest driver against target · Waiting for a choice |

Row keys: decision id; finding `f.id`; action `{item}-{i}` (i, 1-based, within its item's Actions in store order); Site key.
`def.site`: decision `decById(id).site`; finding the key of `x.site`'s Site; action the Site of its item
(`uxSiteActions`'s rule); Site its key. `def.text`: the row's rendered text. `def.keep`: decisions `iaWaiting`; others none.
`def.group`: Sites only (`iaVertical`).

| List | Facets (key · label · options) | Sorts (first is default) | Tiles (label · value · qty role) |
|---|---|---|---|
| decisions | `state` · State · waiting "Waiting for a choice", approval "Awaiting approval", draft "With the plan sent back to draft", underway "Under way" (`uxStateCount`'s rule); `due` · Due · week, month, later, none (`UX_URG` words, `uxUrgency(due)`) | `priority` "Priority" (store order) · `due` "Due date" (no deadline last) · `stake` "At stake" (`uxStakeParts(id).num` descending) | "Decisions" · n · total; "Waiting for a choice" · count of `iaWaiting` rows · own key `decisions:waiting` |
| findings | `heading` · Heading · `LENS` keys present, words `LENS[k][0]` | `priority` "Priority" · `site` "Site" | "Findings" · n · total; "Decision waiting for a choice" · count with `x.st` waiting · own key |
| actions | `state` · State · released, waiting, returned (`RELEASE_WORD`); `version` · Plan version · the one option `uxPlanState(op).version`, "Version {n}" (keeps the Actions of `planApprovedIds(op)` when Approved, else of `planItemsV1(op)`) | `due` "Due date" · `item` "Plan item" | "Actions" · n · total; "Released", "Waiting" · parts; "Returned" · part, only when above 0. Parts sum to n |
| sites | `target` · Target · below "Below target" (cost "Over target"), on "On or above target" (cost "On or under target") | `gap` "Gap to target" (D-IA.27's order) · `name` "Name" | "Sites" · n · total; "Below target" (cost "Over target") · own key; "Gap to target" · the sum of shown-and-hidden rows' gaps · total, each row's gap cell `data-qty` part of it |

`def.none`: "No decisions in this scope.", "No Findings in this scope.", "No Actions in this scope.", "No Sites in this scope.".

`MOCK DEVIATION` D2 (register row, packet line): Decisions, Findings and Actions have no "at stake" tile. Stakes of separate
decisions are valued on different bases and some are alternatives, so a sum is not a true figure (honest numbers); the
Sites list keeps it as the gap to target, whose rows add up.

## 5. Wiring in IA-2b1 (D-IA.64)

- **Outcomes fold.** `portfolio/outcomes` L2 becomes `iaListBody('sites', ctx, { tools: false, tiles: false })` (the same
  rows, columns, sort, cap, groups and Show all as the Sites list; Show all leads to `sites?scope=…&show=all`). Its L1
  headline and L3 stay. `iaOutcomeTable` is deleted; `iaOutcomeRows`, `iaOutcomeScope`, `iaOutcomeHeadline` stay.
- **Aliases** (`IA_ALIASES`): `'portfolio/act-first': 'decisions'`; `'findings-cost': 'findings?heading=optimize'`,
  `'findings-risks': 'findings?heading=protect'`, `'findings-opportunities': 'findings?heading=grow'`. An alias value may
  carry a query: `iaLiveAlias` tests `iaLanded` on the value's path; `iaCanon` writes the value's query, then the href's
  own parameters not already set. `shape_check` item 7 reads the value's path.
- **Crumbs and the rail.** The decision page's first crumb "Decisions" becomes a link to `decisions`; a Site hub's "Sites"
  becomes a link to `sites` (D-IA.9's "home list › Site › object"). The rail's four items go live with `IA-2b1`.
- **Search index** (`iaPaletteFilter`, IA code): from `IA-2b1` it appends, after the reviewed entries, one entry per Finding
  `[x.text, 'Finding · {Site}', its row target]` and per Action `[a.action, 'Action · {owner name}', its row target]` (rows
  without a live target are not indexed), and `['Decisions', 'Go to', 'decisions']`, `['Sites', 'Go to', 'sites']`.
- **The legacy screens** `sites`, `findings`, `actions` and `portfolio/act-first` stay registered and byte-identical for the
  review select; IA routes take precedence once landed (as `plan` and `portfolio` do).

## 6. Wiring in IA-2b2, after the stop (D-IA.65)

- **Parts splits, byte-identical** (`parts_identity`): `uxOverviewParts` adds `qHead` (today's panel head string) and
  `uxSiteParts` adds `qHead` and `acts` (the "Actions in hand" aside) and `stickyBare` (the sticky without its "Decide"
  link); `uxOverview`, `uxSitePage` and every existing part keep today's bytes.
- **Overview L2:** `{qHead}{iaListBody('decisions', ctx, { tools: false, tiles: false, cap: 6 })}{iaCapMore(hidden)}<p class="ux-more"><a class="ux-link" href="#/decisions" data-qty="decisions:n:" data-qty-role="total">View all {n}</a></p></section></div>`
  in the reviewed panel wrapper; `cap` overrides 10 and drops "Show all" in favour of "View all". The heading's count and split are unchanged.
- **Site hub L2:** the same with `cap: 3`, `?scope=site:{k}`, beside `acts`; the sticky is `stickyBare`.
- **Primary:** the hubs have no page primary (rows are links; a state is a label, D-IA.9). `shape_check` item 1 allows none.
  This closes R749, R750 and R751.
- **The plan's link** (L1, identical on the four tabs, after the clause): when the version holds a released Action,
  `<p class="ia-plan-acts"><a class="ux-link" href="#/actions?state=released&version={n}">Released Actions of version {n} ({r})</a></p>`,
  `r` = the Actions list's count at that address (`data-qty` total of `actions:n:state=released&version={n}`). `ia.css`
  `.ia-plan-acts{margin:var(--s2,8px) 0 0}`.
- **G1:** surface `released Actions of the plan version`, route `actions?state=released&version={n}`, limit 2, via `any`;
  the check asserts the found href's values, not only its keys.

## 7. Copy (exact; nothing else is new)

Route titles "Decisions", "Findings", "Actions", "Sites". Tile labels, facet labels and options, sort words, column words and
`def.none` strings as §4. Tools: "All", "Sort", "Search", "Clear filters", "All sites", the form's `aria-label` "Filter and
sort decisions|Findings|Actions|Sites". "Show all {n}", "View all {n}", "Nothing matches these filters.", "No deadline",
"No decision yet", "Version {n}", "Released Actions of version {n} ({r})", palette kinds "Finding · {Site}", "Action · {owner}".
Every other word is a reused function's. No date or month is typed: months come from `fdate`, `iaMonth()` or `periodWords()`
(D-IA.57).

## 8. Gates and plants that must fail (D-IA.66)

§6 of `spec.md` applies whole. Checks are written first (W2), dormant until `IA-2b1` (or `IA-2b2`) is landed, run under
`IA_FORCE_LANDED`; `ia_gates` fails a dormant output once landed (D-IA.49's rule).

| Check | Asserts | Plants (each must fail) |
|---|---|---|
| `tools/list_shape_check.cjs` (new, jsdom) A: synthetic | `iaListModel` on a 25-item store in 3 groups: scope all/group/site; a facet; an invalid facet value ignored; search words ANDed; sort stable, ties in store order; cap 10, `show=all` uncapped; keep-first with display in sort order; groups only above 10 in more than one group; `iaListHref` order and defaults | `LIST_PLANT=cap`, `keep`, `scope`, `search`, `sort`, `invalid`, `group`, `canon` |
| B: live, every operator × the four lists × default, each facet value, each sort, `q` = the first row's first word, each scope entry, `show=all`; actions also after Approve and Send back | one `[data-shape="list"]`; tile 1 = shown + hidden rows = the "Show all" n; every row has exactly one interactive element and it is live; each control's value equals the address; the same address booted fresh gives byte-identical L2; the row set equals the check's own computation from the stores (ATTN, `HC.findings`, `WF(op).actions`, `OPS[op].sites`, `uxDecState` keys, `RELEASE` codes, `LENS`; never `iaListModel` or a def) | `LIST_PLANT=tile` (tile counts shown rows), `rowctl` (a button in each decision row), `restore` (the facet ignored on first render), `own` (findings drop the last store item) |
| C: the scope menu on a list | entries keep facets, sort and `q`; Site entries scope the list | `LIST_PLANT=scopemenu` |
| `outcomes_table_check.cjs` (retargeted to the component) | its cases A to D unchanged in meaning; the Outcomes rows equal the Sites list's rows at the same scope | `OUT_PLANT` set kept, each still failing |
| `shape_check.cjs` | item 7 reads alias value paths; item 12 the "Decisions" crumb is a link to `#/decisions`; new item 15: every list route's tools and links never self-link (item 6 covers L2) | `SHAPE_PLANT=aliasq` (a query-carrying alias stays unlinked), `deccrumb` |
| `qty_check.cjs` | list tiles, row gaps and "Show all"/"View all" register by `data-qty`; parts sum; one format per key (D-IA.59) | `QTY_PLANT=sitegap` (one row gap dropped), `listcents` (the tile rounded, rows with cents) |
| `click_depth_check.cjs` | each list ≤ 1 via the rail; (2b2) released Actions of the version ≤ 2 via the plan, values asserted | `G1_PLANT=listrail` (rail item unlanded), (2b2) `planacts` (the plan's link dropped) |
| (2b2) `count_check.cjs` hub block, retargeted | rows shown + `data-ia-more` = the heading's count; "View all" n = that count = the target list's tile 1; waiting decisions shown or counted on an inbox line | the IA-1b plants kept (`capsel`, `capmore`, `phone`, `choose`) failing on the new rows; new `viewall` (n from the shown rows) |
| (2b2) `parts_identity.cjs` | the new parts; every earlier job identical | — |
| `ia_shots.cjs` (heavy) | the four lists × 3 operators × 390 × 844, 1280 × 720, 1440 × 900, light and dark: no sideways scroll; the tools row wraps inside the page; tile rows fill (D-IA.56); after a select change at 390 the control keeps its place (±4 px) and has focus | `SHOTS_PLANT=listkeep` (no restore) |
| `copy_check.cjs` | §7's strings | `COPY_PLANT=list` |

`after_render_check` and `shape_check` items 1 to 6 cover the new routes by construction.

## 9. Units and commits

| Unit | Part | Commits | Content | Visible change |
|---|---|---|---|---|
| 1 | 2b1 | 1 to 2 | The checks first: `list_shape_check` A to C, the `shape_check`, `qty_check`, `click_depth`, `copy_check` rows and the runner's rows, dormant, forced under `IA_FORCE_LANDED=IA-2b1` | none |
| 2 | 2b1 | 1 | `iaListModel`, `iaListHref`, `iaListBody`, `shapeList`, the listener and focus keep, `ia.css`; not live. Synthetic plants fail | none |
| 3 | 2b1 | 2 | (a) the four defs and routes (`unit: 'IA-2b1'`), the Outcomes fold with `outcomes_table_check` retargeted, aliases, crumbs, scope menu, search index; (b) the flip: `'IA-2b1'` into `IA_LANDED`; `walkthroughs.md` (the four lists); register rows; shots; `packet-IA-2b1.md` | the four home lists, the Outcomes table as the Sites rows |
| — | stop | — | **The owner's IA-2a walkthrough** (§2). Review of IA-2b1 runs meanwhile | — |
| 4 | 2b2 | 2 | The parts splits; hub queues as the component with "View all"; `stickyBare`; `count_check` retargeted (plants failing first) | the hubs' queue rows |
| 5 | 2b2 | 1 | The plan's link, G1's surface, the flip of `'IA-2b2'`, shots, `packet-IA-2b2.md` | the plan's link line |

## 10. Done, deviations, packet

**IA-2b1 is done when**, beyond §6: the four lists are live from one shape and one component; every plant of §8's 2b1 rows
fails in `ia_gates`; Outcomes shows the Sites rows; the aliases resolve with their queries; every list view restores from
its address; G1 prints each list at 1. **IA-2b2 is done when** the hubs' rows have one target, "View all {n}" equals the
target list's tile, G1 prints the released Actions of the version at ≤ 2, `parts_identity` holds, and every 2b2 plant fails.

**`MOCK DEVIATION`s** (rows after the base's last, each a packet line): D2, no "at stake" tile on three lists (§4); D5,
resolving IA-2d, Finding and Action rows open their decision (or the plan) until `finding/:id` and `action/:id` exist; D5,
resolving IA-2c, no Assets, Incidents and Maintenance lists (the figure's other home lists). Closed by IA-2b2: R749, R750,
R751 (the packet names the commit).

**Packets** `packet-IA-2b1.md`, `packet-IA-2b2.md` (`spec.md` §8's list), plus the stop line if any, the list counts per
operator (tiles, rows, Show all), the `qty_check` keys added, and the count of mid-build questions.
