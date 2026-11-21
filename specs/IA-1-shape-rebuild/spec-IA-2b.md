# IA-2b: the list shape (implementer spec, rev 2)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away rows 46 and 47). Rulings D-IA.61 to D-IA.66, and the
handshake's answers D-IA.67 to D-IA.81 (rev 2), are in `rulings-5.md`. The reviewer entry is `reviewer-guide-IA-2b.md`. This
file is IA-2b's card for `spec.md` §5 (the IA-2 plan's "IA-2b" row). It is a separate file so that it does not collide with
IA-2a's open edits to `spec.md` §5.1. `spec.md` §0, §6, §7 and §8 apply whole; where this file is more specific, it governs.
Handshake: round 1 is in `handshake-IA-2b.md` and answered. Mid-build questions go in `mid-build-questions.md` under "IA-2b".

**Rev 2 changes (handshake round 1):**
- Controls grow with the list (D-IA.67), and chips name every view state that no control shows (D-IA.70).
- The Sites gap tile equals the Overview's tile, and hidden rows show as a part (D-IA.68).
- The "At stake" sort is dropped (D-IA.69).
- `qty_check` gains a count mode and a format mode as unit 2 (D-IA.71), and the shots matrix is widened (D-IA.72).
- The keep runs after the router (D-IA.75), list cells hold text only (D-IA.76), and the helpers are named (D-IA.77, D-IA.78).
- There is one cap per list (D-IA.80). The work is now 6 units (D-IA.81).

**Read first:** the proposal page `Docs/design-system/ia-proposal/index.html`:
- §4's figure "2 · Home list": tiles "count · count · at stake"; "Filters · sort · search · scope chip"; rows; "Show all 42";
  "row → page or drawer".
- §3's rules: "One drill-down grammar", "Wayfinding", "One store, many scopes", "Nothing unbuilt is reachable", "The scope
  picks the Sites".
- Its "The same shape at 3, 30 and 300 Sites" figure. It governs the control tiers: "3 Sites · sort: gap"; "30 Sites ·
  filter · sort · group heads · Show all 30"; "300 Sites · scope · search · Show all 42".

Also read `rulings.md` D-IA.9, D-IA.10, D-IA.25 and D-IA.27; `rulings-2.md` D-IA.34; `rulings-4.md` (on IA-2a's branch) D-IA.49,
D-IA.50 and D-IA.54 to D-IA.60; and the owner's standing UI brief (`owner/owner-ui-standing-brief-2026-11-20.md`).

## 1. Outcome

An operator executive opens Decisions, Findings, Actions or Sites from the menu and sees one home list per object, drawn by
one component:
- up to four count tiles that equal the list;
- controls that grow with the list: none under 3 rows, Sort up to 10, and filters, sort and search above 10;
- a chip for each view state that no control shows;
- at most 10 rows, then "Show all {n}";
- rows that each open one thing.

The address holds the whole view, so Back and a shared link restore it. The Portfolio's Outcomes tab is the same component
(the Sites list) without its controls. The hubs' queues become the same rows, scoped and capped, with "View all {n}". The plan
links to its released Actions, the last G1 surface not yet measured.

**At the live size** (IA-2a's head: 3 Sites per operator in one vertical; Decisions 8 / 3 / 4, Findings 9 / 4 / 7, Actions
6 / 3 / 2), every list is drawn with Sort only, and Metro's Actions have no controls. No list is capped or grouped. The scale
case (filters, search, groups, "Show all") is proven on a fixture (D-IA.67).

## 2. Split, base and the stop point (D-IA.61, D-IA.81)

| Part | Units | Landing ID | Delivers | Depends on the owner's IA-2a walkthrough? |
|---|---|---|---|---|
| IA-2b1 | 1 to 4 | `IA-2b1` | `qty_check`'s count and format modes; the component; the four home lists live; aliases; the scope menu on lists; crumbs; the search index; the Outcomes fold | No. It reads IA-2a's state and release words only through the one-source helpers, at render (D-IA.74) |
| IA-2b2 | 5 and 6 | `IA-2b2` | hub queues as the component (one-target rows, "View all {n}"); the plan's link to its released Actions; G1's surface | **Yes** (see the stop) |

**Size:** 6 units, about 10 commits (D-IA.81). IA-2b1 is 4 units (about 4.3 of effort) and IA-2b2 is 2. Each part is under
the 6-unit cap, and the whole is at it. One branch, two reviews: one per part, at discovery depth (W5).

**Base.**
- Branch `task/IA-2b-list` in `/opt/assetecon/AssetOpsV1-ia2b`, from the head of IA-2a's latest accepted fix round:
  `task/IA-2a-plan` once the D-IA.58 to D-IA.60 round has merged into it. At this writing that head is `b2fb5de65`, which
  carries the answers, while the build round is under way.
- Each later IA-2a fix round is merged in, never rebased. IA-2b never merges before IA-2a. Once IA-2a merges, merge `main` in.
- Touch only `vNEXT/`, its `tools/`, `walkthroughs.md`, this folder and `.agent/mock-departure-register.md`.
- Evidence goes in `/opt/assetecon/evidence/IA-2b/<unit>/`. Browser checks run through `tools/heavy-slot.sh`, as in
  `spec.md` §0. Never use ports 5490 or 8990, or Docker.

**The stop point (the owner's IA-2a walkthrough).** Unit 5 does not start until:
- (a) the owner has walked IA-2a and the coordinator has recorded the verdict in a verbatim owner file; and
- (b) any IA-2a change that verdict asks for is merged into this branch.

Units 5 and 6 change what the owner is walking or has just walked: the plan's L1 (a new link line, identical on the four tabs,
D-IA.43), the Overview and Site queue rows the walkthrough passes through, and the hub's one primary ("Decide" leaves the rows,
D-IA.65). The card concerned is re-ruled first (`rulings-5.md`), not patched in the build, if the owner changes any of these:
- the plan's L1 or its tab grammar;
- its state or release words;
- the Decisions list's State facet words, or the Actions list's State and Plan version facets (D-IA.74);
- or asks to keep a "Decide" button on the hubs.

IA-2b1 reads all of these at render, so a re-rule that touches it lands before IA-2b1 merges.

**The 5c rule** (RC6; `owner/owner-start-ia2a-2026-11-21.md`): 5c takes the UI lane the moment its gates hold. Finish the
commit in hand, run the fast check-all, push, and write `Stopped after <unit/commit> at <sha>; resume at <next>` at the top of
`packet-IA-2b1.md` (or `-2b2`). Every commit boundary leaves the screens as they are and every gate green.

## 3. The component (D-IA.62, D-IA.67, D-IA.70, D-IA.80)

### 3.1 The model (pure, `ia-shapes.js`)

`iaListModel(def, items, q, scope)` returns `{ rows, shown, hidden, n, ns, tier, groups }`:
1. **Scope:** keep items with `def.site(item)` in the scope (`all`; `group:<g>` by `iaVertical`; `site:<k>`). `ns` = the
   items in scope. A list with no `site` ignores the scope (none in IA-2b).
2. **Tier** (D-IA.67): `tier` is 0 when `ns` < 3, 1 when 3 ≤ `ns` ≤ 10, and 2 when `ns` > 10.
3. **Facets:** for each `def.facets[i]` with a value in `q[f.key]` that is one of its option values, keep the items with
   `f.of(item) === value`. A value that is not an option is ignored (the D-IA.35 L4 rule, made general). A facet applies
   whatever the tier; a facet the tier does not draw is shown as a chip (§3.2).
4. **Search:** split `q.q` on whitespace and lower-case it. Keep the items whose `def.text(item)` (lower-cased, tags
   stripped) contains every word (the palette's rule, `uxPaletteFill`).
5. **Sort:** the `def.sorts` entry named by `q.sort`, else the first. The sort is stable, with ties in store order.
6. **Cap (one per list, D-IA.80):** 10, unless `q.show === 'all'`.
   - Ranking: items with `def.keep(item)` true come first, then the rest, each in sort order.
   - `shown` = the first 10 of that ranking, **displayed in sort order**; `hidden` = the rest, in sort order (D-IA.34,
     generalised).
   - `n = rows.length`, after filters and before the cap.
7. **Groups** (D-IA.27 as amended by D-IA.80): when `def.group` exists and `rows` holds more than 10 items in more than one
   group, the shown rows are drawn in group blocks, groups in order of first appearance in the sort and rows in sort order
   within a group. `groups` = `[{ g, n_g }]`, where `n_g` is the group's rows before the cap. A group with no shown row keeps
   its head. There is one "Show all {n}", and `show=all` expands every group.

`iaListHref(key, ctx, change)` (pure) writes the canonical address: `#/<key>`, then these parameters in this fixed order, each
only when it is not its default:
- `scope` (omitted for `all`);
- the facets, in `def.facets` order;
- `sort` (omitted for the first);
- `q` (omitted when empty);
- `show=all`.

`change` overrides. A facet change or a search drops `show`. Every writer of a list address uses it (aliases included,
D-IA.78).

### 3.2 The markup (shape `list`)

```html
<section data-shape="list" data-ia-list="{key}">
  <div data-level="L1"><div class="heroes ux-kpis">{tiles}</div></div>
  <div data-level="L2">{chips}{tools}{table or empty state}{more}</div>
</section>
```

- **Tiles:** one `uxKpi(label, '<span data-qty="{key}:{qty}:{query}" data-qty-role="{total|part}"{ data-qty-kind="count"}>{value}</span>')`
  per tile in §4. Count tiles carry `data-qty-kind="count"` (D-IA.71). `{query}` is the canonical query without `show`, so a
  key is per view. At most 4 tiles (`shape_check` item 1).
- **Chips** (D-IA.70): `<p class="ia-list-chips" aria-label="In this view">`, drawn when it holds at least one chip. Each
  chip is `<span class="ia-chip">{word} · <a class="ux-link" href="{the address without it}">{way out}</a></span>`, in this
  order:
  - the scope, when it is not `all` (word: the group word or the Site name; way out "All sites");
  - each set facet whose select is not drawn (word: the option's word; way out: the facet's `all`, §4);
  - `q`, when the search box is not drawn (word `Matching “{q}”`, way out "Clear search");
  - then, when 2 or more of the facets and `q` are set, `<a class="ux-link" href="{the address with the scope only}">Clear filters</a>`.
- **Tools** by tier (D-IA.67). Tier 0: none. Tier 1: the form with Sort only. Tier 2, in this order:
  - one `<label>{facet label} <select name="{facet}"><option value="">All</option>{options}</select></label>` per facet whose
    options number at least 2 in the scope;
  - `<label>Sort <select name="sort">{sorts}</select></label>`;
  - `<label>Search <input type="search" name="q" value="{q}"></label><button type="submit" class="button">Search</button>`.

  The form is `<form class="ia-list-tools" data-ia-list-tools="{key}" role="search" aria-label="Filter and sort {plural}">`,
  and at tier 1 its `aria-label` is "Sort {plural}". Each control's value is the address's. The tools and chips rows wrap
  inside the page: `ia.css` `.ia-list-tools,.ia-list-chips{display:flex;flex-wrap:wrap;gap:var(--s2,8px);align-items:end}`.
- **Table:** `<div class="table-wrap"><table class="ia-list ux-stack" id="ia-list-{key}">`.
  - The `<thead>` comes from the def's column words.
  - Grouped (§3.1 step 7): one `<tbody data-group="{g}">` per group, headed by
    `<tr class="ia-list-group"><th colspan="{cols}" scope="rowgroup">{group word} <span class="ux-count" data-qty="{key}:n:{query}" data-qty-role="part" data-qty-kind="count">{n_g}</span></th></tr>`.
  - One `<tr data-row="{row key}">` per shown item. The first cell is
    `<th scope="row"><a class="ia-row-go" href="{target}">{title}</a>{small}</th>`.
  - Every other cell is `<td data-label="{column}">` and holds **text only**: labels as `status-pill` spans; figures as text,
    or as data-attribute spans (`figA`); never a button or a link (D-IA.76).
  - **One target per row** (D-IA.9): the row's only interactive element is that link. `ia.css` stretches it over the row:
    `.ia-list tbody tr{position:relative}.ia-row-go::after{content:"";position:absolute;inset:0}.ia-list tbody tr:focus-within{outline:2px solid var(--focus,#2563eb);outline-offset:-2px}`.
  - Every store item has a live target (D-IA.70 b); the check fails when one does not.
- **More:** first the def's hidden line, when it has one (decisions: `iaCapMore(hidden ids)`; Sites: the remainder, §4). Then,
  when `hidden` is non-empty,
  `<p class="ux-more"><a class="ux-link" href="{iaListHref(key, ctx, {show:'all'})}" data-qty="{key}:n:{query}" data-qty-role="total" data-qty-kind="count">Show all {n}</a></p>`.
- **Empty:**
  - When the store is empty in scope: `<p class="ux-empty" role="status">{def.none}</p>`.
  - When the filters leave nothing: `<p class="ux-empty" role="status">Nothing matches these filters. <a class="ux-link" href="{scope only}">Clear filters</a></p>`.
    The tier's tools and the chips are still drawn (the tier is set by `ns`, not by the rows left).

### 3.3 Behaviour (`ia-routes.js`, D-IA.75)

- **Write.** One delegated listener handles a `change` on a `select` in `[data-ia-list-tools]` and a `submit` of the form
  (the submit's default is always prevented). It computes `h = iaListHref(key, ctx, { [name]: value })`.
  - When `'#/' + h === location.hash`, it does nothing.
  - Otherwise it stores `IA_LIST_KEEP = { hash: '#/' + h, name, top }`, where `top` is the control's
    `getBoundingClientRect().top`, then sets `location.hash`.
- **Restore.** `iaListRestore` is a `hashchange` listener registered in `ia-routes.js` **after** `iaTabSwitch`'s, and so
  after the router's `render(); window.scrollTo(0,0)`, because listeners run in registration order (verified in
  `index.html`). It runs synchronously, in the router's task. It takes `keep = IA_LIST_KEEP` and sets `IA_LIST_KEEP = null`
  on **every** `hashchange`. Then, if `keep && location.hash === keep.hash`, it finds
  `el = [data-ia-list-tools] [name="{keep.name}"]`. When `el` exists, it runs
  `scrollTo({ top: scrollY + el.getBoundingClientRect().top - keep.top, behavior: 'instant' })` and
  `el.focus({ preventScroll: true })`.
- `iaBind` is unchanged: no restore runs inside `render()`. A list change is not a tab switch: list routes have no
  `tabGroup`, so D-IA.58 does not run. A link (Show all, Clear filters, a chip) is an ordinary navigation and lands at the top
  of the page.
- **The scope menu on a list** (`iaScopeEntries`): on a `list` route, every entry keeps the list's facets, sort and `q` and
  drops `show`. The Site entries scope the list (`#/{key}?scope=site:{k}&…`) instead of opening the Site. Other shapes are
  unchanged. The group entry stays as IA-1b ruled (D-IA.67).

### 3.4 Format (D-IA.59, D-IA.68)

Counts are whole numbers. Money on a list follows D-IA.59: one rendered form per key on a screen.
- The Sites gap key's parts are the shown rows' rendered gaps plus the remainder (§4).
- When their sum equals the whole-dollar rounding of the exact total, every figure of the key is whole dollars, and the tile
  is that sum.
- Otherwise the tile, every row gap and the remainder render with cents.

Live, the sums equal the rounding on all three operators, so the fallback is reached only by the fixture `sites30`.
`qty_check`'s format mode checks it (D-IA.71).

## 4. The four lists (D-IA.63, rev 2)

Routes: `{ id, shape: 'list', object, home, unit: 'IA-2b1', tab: null, tabGroup: null, title, crumbs: [[H1]], render: ctx => shapeList(ctx, key) }`.
H1 and the document title are the menu label. Each def has `items(op)`, which reads the one source the hubs and the plan read.
It is not cached, so the fixture can replace it in a booted window (D-IA.67). No store is copied.

| List · object · home | Store `items(op)` (one source) | Row target (one, always live) | Columns (`data-label` words) |
|---|---|---|---|
| `decisions` · decision · Decisions | `iaDecIds(op, {kind:'all'})` (ATTN order) | `decision/{id}` | Decision (`uxTitle(d.q, site)`, small: the issue labels joined " · ") · Site · State (`uxDecState(id).label`) · At stake (`uxStake(id)`: words stay words) · Due (`fdate(due)` or "No deadline") · Who decides (`who(op, deciderOf(id).p)`) |
| `findings` · finding · Findings | `uxFindingRows(op)` | its decision, `decision/{x.d.id}` (interim: `finding/:id` is IA-2d's; D5). Every live Finding has one (D-IA.70 b) | Finding (`x.text`) · Site · Heading (`LENS[x.heading][0]`) · Its decision (`x.st.label`) |
| `actions` · action · Actions | `WF(op).actions` | the decision whose `opts` holds `a.item`, else `plan` (interim: `action/:id` is IA-2d's; D5) | Action (`a.action`, small: `itemShort(op, a.item)`) · Owner (`who`) · Due (`fdate(a.due)`, small `dueWords`) · State (`actionState(op, a, planCaseIds(op).includes(a.item))[0]`) |
| `sites` · site · Sites | `iaOutcomeRows(op)` (with D-IA.76's text fields) | `site/{key}` | D-IA.27's six: Site · Group · Contribution (cost: "Cost per required departure met"; `result` text) · Gap to target (the `figA` span with `data-qty`, `gapText`) · Largest driver against target (`driver` text) · Waiting for a choice |

- **Row keys:** the decision id; a Finding's `f.id`; an Action's `{item}-{i}` (i is 1-based within its item's Actions, in
  store order); the Site key.
- **`def.site`:** for a decision, `decById(id).site`; for a Finding, `iaFindingSite(op, x)` (D-IA.77); for an Action, the
  Site of its item (`uxSiteActions`'s rule); for a Site, its key.
- **`def.text`:** the row's rendered text. **`def.keep`:** decisions use `iaWaiting`; the others have none.
  **`def.group`:** Sites only (`iaVertical`).

**Helpers (D-IA.77, `ia-shapes.js`):**
- `iaDecStateKey(id)` returns `waiting`, `draft`, `approval` or `underway`, with `IA_DEC_STATE_WORD` beside it.
- `iaActionStateKey(op, a)` returns `returned`, `released` or `waiting`.
- `iaFindingSite(op, x)` returns the key of the Finding's Site.

Every option and word is computed at render (D-IA.74).

| List | Facets (key · label · options · way out) | Sorts (the first is the default) | Tiles (label · value · qty role) |
|---|---|---|---|
| decisions | `state` · State · `iaDecStateKey`: waiting "Waiting for a choice", approval "Awaiting approval", draft "With the plan sent back to draft", underway "Under way" · "All states"; `due` · Due · week, month, later, none (`UX_URG` words, `uxUrgency(due)`) · "Any due date" | `priority` "Priority" (store order) · `due` "Due date" (no deadline last). **No stake sort** (D-IA.69) | "Decisions" · n · total, count; "Waiting for a choice" · the count of `iaWaiting` rows · its own key, count |
| findings | `heading` · Heading · the `LENS` keys present, words `LENS[k][0]` · "All headings" | `priority` "Priority" · `site` "Site" | "Findings" · n · total, count; "Decision waiting for a choice" · the count with `x.st` waiting · its own key, count |
| actions | `state` · State · `iaActionStateKey`: released, waiting, returned (`RELEASE_WORD`) · "All states"; `version` · Plan version · the one option `uxPlanState(op).version`, "Version {n}" (keeps the Actions of `planApprovedIds(op)` when Approved, else of `planItemsV1(op)`) · "All versions" | `due` "Due date" · `item` "Plan item" | "Actions" · n · total, count; "Released" and "Waiting" · parts, count; "Returned" · part, count, only when above 0. The parts sum to n |
| sites | `target` · Target · below "Below target" (cost "Over target"), on "On or above target" (cost "On or under target") · "Above and below target" (cost "Over and under target") | `gap` "Gap to target" (D-IA.27's order) · `name` "Name" | "Sites" · n · total, count; "Below target" (cost "Over target") · its own key, count; "Gap to target" · the parts' sum (§3.4) · total, money, plus the line "{k} Sites without a target are not in this figure" when k > 0 |

- **Sites remainder** (D-IA.68): when `hidden` is non-empty, the More line starts with
  `<p class="ux-more">Not shown: {h} Sites, gap to target <span data-qty="sites:gap:{query}" data-qty-role="part">{the hidden rows' gap}</span>.`
  It is followed by the "Show all {n}" link, in the same paragraph.
- **The Sites gap tile is the operator's own gap.** At scope all and unfiltered, `sites:gap:` equals the Overview's
  `overview-gap` (`qty_check`'s `EQUAL` table). Each Site's gap is actual minus target for one measure, basis and month, so the
  gaps add.

`def.none`: "No decisions in this scope.", "No Findings in this scope.", "No Actions in this scope.", "No Sites in this scope.".

`MOCK DEVIATION` D2 (a register row and a packet line): Decisions, Findings and Actions have no "at stake" tile and no stake
sort. Stakes of separate decisions are valued on different bases and horizons, and some are alternatives, so neither a sum nor
an order is a true figure (honest numbers). The Sites list keeps the tile as the gap to target, whose rows add up.

## 5. Wiring in IA-2b1 (D-IA.64, D-IA.76, D-IA.78, D-IA.79)

- **Outcomes fold.** The `portfolio/outcomes` L2 becomes `iaListBody('sites', ctx, { tools: false, tiles: false })`: the
  same rows, columns, sort, cap, groups, remainder and Show all as the Sites list. Show all leads to `sites?scope=…&show=all`.
  - No chips are drawn here: the Outcomes tab's scope is the topbar's.
  - Its L1 headline and L3 stay.
  - `iaOutcomeTable` is deleted. `iaOutcomeRows` (with D-IA.76's `result`, `gapText` and `driver` fields), `iaOutcomeScope`
    and `iaOutcomeHeadline` stay.
  - The in-cell `fig()` buttons leave the table. Each figure's explanation is on the Site hub, the row's target.
- **Aliases** (`IA_ALIASES`): `'portfolio/act-first': 'decisions'`; `'findings-cost': 'findings?heading=optimize'`,
  `'findings-risks': 'findings?heading=protect'`, `'findings-opportunities': 'findings?heading=grow'`.
  - `iaAliasTarget(path)` returns `{ path, query }` (a function value is called first), and it is the only splitter in the
    product.
  - `iaLiveAlias` tests `iaLanded` on its path.
  - `iaCanon` writes the value's query, then the href's own parameters that are not already set, in `iaListHref`'s order when
    the target is a list.
  - `iaLive`, `iaCanon` and `iaPaletteFilter` call the helper. `shape_check` item 7 and the crawl split with their own code.
- **Crumbs and the rail.** The decision page's first crumb, "Decisions", becomes a link to `decisions`. A Site hub's "Sites"
  becomes a link to `sites` (D-IA.9's "home list › Site › object"). The rail's Sites, Findings, Decisions and Actions items
  change `unit: 'IA-2b'` to `'IA-2b1'` in unit 4(a), and they go live with the flip in 4(b).
- **Search index** (`iaPaletteFilter`, IA code): from `IA-2b1` it appends these entries after the reviewed ones:
  - one per Finding, `[x.text, 'Finding · {Site}', its row target]`;
  - one per Action, `[a.action, 'Action · {owner name}', its row target]`;
  - `['Decisions', 'Go to', 'decisions']` and `['Sites', 'Go to', 'sites']`.
- **The legacy screens** `sites`, `findings`, `actions` and `portfolio/act-first` stay registered and byte-identical for the
  review select. Once landed, the IA routes take precedence (as `plan` and `portfolio` do).

## 6. Wiring in IA-2b2, after the stop (D-IA.65)

- **Parts splits, byte-identical** (`parts_identity`): `uxOverviewParts` adds `qHead` (today's panel head string).
  `uxSiteParts` adds `qHead`, `acts` (the "Actions in hand" aside) and `stickyBare` (the sticky without its "Decide" link).
  `uxOverview`, `uxSitePage` and every existing part keep today's bytes.
- **Overview L2:**
  `{qHead}{iaListBody('decisions', ctx, { tools: false, tiles: false, cap: 6 })}{iaCapMore(hidden)}<p class="ux-more"><a class="ux-link" href="#/decisions" data-qty="decisions:n:" data-qty-role="total" data-qty-kind="count">View all {n}</a></p></section></div>`,
  in the reviewed panel wrapper. `cap` overrides 10 and replaces "Show all" with "View all". The heading's count and split are
  unchanged.
- **Site hub L2:** the same, with `cap: 3` and `?scope=site:{k}`, beside `acts`. The sticky is `stickyBare`.
- **Primary:** the hubs have no page primary: the rows are links, and a state is a label (D-IA.9). `shape_check` item 1
  allows none. This closes R749, R750 and R751.
- **The plan's link** (in L1, identical on the four tabs, after the clause). When the version holds a released Action:
  `<p class="ia-plan-acts"><a class="ux-link" href="#/actions?state=released&version={n}">Released Actions of version {n} (<span data-qty="actions:n:state=released&version={n}" data-qty-role="total" data-qty-kind="count">{r}</span>)</a></p>`.
  `r` is the Actions list's count at that address (one count, wrapped alone, D-IA.71). `ia.css`:
  `.ia-plan-acts{margin:var(--s2,8px) 0 0}`. The link lands on Actions with the chips "Released · All states" and
  "Version {n} · All versions" (D-IA.70).
- **G1:** the surface `released Actions of the plan version`, route `actions?state=released&version={n}`, limit 2, via `any`.
  The check asserts the found href's values, not only its keys.

## 7. Copy (exact; nothing else is new)

- Route titles: "Decisions", "Findings", "Actions", "Sites".
- Tile labels, facet labels, options and ways out, sort words, column words and the `def.none` strings: as in §4.
- Tools: "All", "Sort", "Search", "Clear filters", "All sites", "Clear search", `Matching “{q}”`. The form's `aria-label` is
  "Filter and sort decisions|Findings|Actions|Sites" at tier 2 and "Sort decisions|Findings|Actions|Sites" at tier 1. The
  chips row's `aria-label` is "In this view".
- "Show all {n}", "View all {n}", "Nothing matches these filters.", "No deadline", "Version {n}", "Not shown: {h} Sites, gap
  to target {gap}.", "{k} Sites without a target are not in this figure", "Released Actions of version {n} ({r})".
- The palette kinds: "Finding · {Site}", "Action · {owner}".
- "No decision yet" is removed (D-IA.70 b).

Every other word is a reused function's. No date or month is typed: months come from `fdate`, `iaMonth()` or `periodWords()`
(D-IA.57).

## 8. Gates and plants that must fail (D-IA.66, rev 2)

§6 of `spec.md` applies whole. The checks are written first (W2) and are dormant until `IA-2b1` (or `IA-2b2`) is landed. They
run under `IA_FORCE_LANDED`, and `ia_gates` fails a dormant output once landed (D-IA.49's rule). The `OWN` map gains `IA-2b1`
(`list_shape_check`, `outcomes_table_check`, `shape_check`, `qty_check`, `click_depth_check`, `copy_check`) and `IA-2b2`
(`count_check`, `parts_identity`, `click_depth_check`, `qty_check`). `shape_check` item 11 is in the dormancy list (D-IA.79).
Every plant listed below fails in `ia_gates`, and its output names where.

| Check | Asserts | Plants (each must fail) |
|---|---|---|
| `tools/list_shape_check.cjs` (new, jsdom). Block A, synthetic (the only block that calls the model) | `iaListModel` on a 25-item store in 3 groups: scope all, group and Site; the tier at 2, 3, 10, 11 and 25 items; a facet; an invalid facet value ignored; search words ANDed; sort stable, with ties in store order; cap 10, `show=all` uncapped; keep-first with display in sort order; groups only above 10 in more than one group, one cap, `n_g` summing to n; `iaListHref`'s order and defaults | `LIST_PLANT=cap`, `keep`, `scope`, `search`, `sort`, `invalid`, `group`, `canon`, `tier` |
| Block B, live: every operator × the four lists × the default view, each facet value (by address), each sort, `q` = the first row's first word, each scope entry and `show=all`; Actions also after Approve and after Send back, and in Lakeside 6500/No | <ul><li>one `[data-shape="list"]`</li><li>tile 1 = the shown rows + the hidden rows = the "Show all" n</li><li>the tier's controls and no others (D-IA.67)</li><li>a chip for each set state that no control shows (D-IA.70)</li><li>every row has exactly one interactive element and it is live; every store item has a target</li><li>each control's value equals the address</li><li>the in-page path and a fresh boot of the same address give a byte-identical L2 (D-IA.73 a)</li><li>the sort lists equal the literals (D-IA.69)</li><li>the product's word tables equal B's literal tables (D-IA.73 c)</li><li>`iaActionStateKey` agrees with each pill's `data-release`; `IA_DEC_STATE_WORD` appears in `uxStateCount`'s output</li><li>the row set equals B's own computation from the stores and the reviewed classifiers (never `iaListModel`, `IA_LIST_DEFS`, `iaDecStateKey`, `iaActionStateKey`, `iaFindingSite`, `uxFindingRows` or `iaOutcomeRows`)</li><li>the count of live screens that took the cents fallback is printed (expected 0)</li></ul> | `LIST_PLANT=tile` (the tile counts the shown rows), `rowctl` (a button in each decision row), `restore` (the address's sort and facets ignored on first render; fails on the sort, live), `own` (Findings drop the last store item), `stakesort` (the stake sort added back), `notarget` (one Finding's decision removed in the window) |
| Block C: the scope menu on a list | the entries keep the facets, sort and `q`; the Site entries scope the list | `LIST_PLANT=scopemenu` |
| Block D (new): the fixture (`tools/list_fixture.cjs`, `sites30` and `decisions25`, injected through `items(op)` in the window, rendered by the real route) | <ul><li>tier 2's controls</li><li>group heads 18, 7 and 5 summing to tile 1</li><li>one "Show all 30"</li><li>the remainder line + the shown gaps = the tile</li><li>the cents fallback on every figure of the key</li><li>the no-target Site last, with the tile's line</li><li>the chips and "Clear filters" at 2 set filters</li><li>the empty state with its tools</li></ul> | `LIST_PLANT=remainder` (the line dropped); `tier` and `group` also fail here |
| `outcomes_table_check.cjs` (retargeted to the component) | its cases A, C and D unchanged in meaning; B per D-IA.80 (12 in groups of 7 and 5 give 10 shown, heads 7 and 5, "Show all 12"); no button and no second link in a row; the Outcomes rows equal the Sites list's rows at the same scope | the `OUT_PLANT` set kept, each still failing |
| `shape_check.cjs` | item 7 reads alias value paths with its own split; item 12: the "Decisions" crumb is a link to `#/decisions`; new item 15: every list route's tools, chips and links never self-link (item 6 covers L2) | `SHAPE_PLANT=aliasq` (`iaAliasTarget` leaves the query in the path), `deccrumb` |
| `qty_check.cjs`, unit 2 (D-IA.71) | the existing money rules; **count mode** (`data-qty-kind="count"`: one integer per element, the parts sum, equal keys are equal across routes); **format mode** (per screen and key, one number of decimals over IA `data-qty` figures; keys with a reviewed `QTY` member printed as "format deferred to IA-2e" with a count); **`EQUAL`** `sites:gap:` = `overview-gap` | `QTY_PLANT=counts` (Returned part dropped), `tilecount` (the Actions tile counts released rows only), `sitegap` (one row's gap part dropped), `listcents` (rows with cents, tile whole), `gapnet` (the tile sums the shortfalls only; Metro) |
| `click_depth_check.cjs` | each list is ≤ 1 via the rail; (2b2) the released Actions of the version are ≤ 2 via the plan, with the values asserted | `G1_PLANT=listrail` (a rail item unlanded), (2b2) `planacts` (the plan's link dropped) |
| (2b2) `count_check.cjs` hub block, retargeted | the rows shown + `data-ia-more` = the heading's count; "View all" n = that count = the target list's tile 1; waiting decisions shown or counted on an inbox line | the IA-1b plants kept (`capsel`, `capmore`, `phone`, `choose`), failing on the new rows; new `viewall` (n from the shown rows) |
| (2b2) `parts_identity.cjs` | the new parts; every earlier job identical | — |
| `ia_shots.cjs` (heavy), the list set (D-IA.72) | classes S1 to S9 with a count printed per class. In every shot: no sideways scroll; the tools and chips rows' children end inside the page; tile rows fill (D-IA.56); stacked at 390. S9: the control's top within ±4 px, and focus on it, after a change at 390 with the router present | `SHOTS_PLANT=listkeep` (`iaListRestore` not registered; fails S9 live), `listwrap` (`nowrap` on the tools and chips rows; fails S8 at 390), `emptytools` (the empty state without its sort and chips; fails S4 on all three) |
| `copy_check.cjs` | §7's strings | `COPY_PLANT=list` |

`after_render_check` and `shape_check` items 1 to 6 cover the new routes by construction.

## 9. Units and commits (rev 2)

| Unit | Part | Commits | Content | Visible change |
|---|---|---|---|---|
| 1 | 2b1 | 2 | The checks first: `list_shape_check` A to D and `tools/list_fixture.cjs`; the `shape_check`, `outcomes_table_check`, `click_depth` and `copy_check` rows; `ia_gates`' `OWN` and plant rows. All dormant, and forced under `IA_FORCE_LANDED=IA-2b1` | none |
| 2 | 2b1 | 1 | `qty_check`'s count mode, format mode and `EQUAL` table, with the five plants (D-IA.71). They run on IA-2a's routes now; the list plants are shown failing once unit 4 lands, under force | none |
| 3 | 2b1 | 1 | `iaListModel`, `iaListHref`, `iaListBody`, `shapeList`, chips and tiers, the listener and `iaListRestore`, `iaAliasTarget`, `ia.css`. Not live. The synthetic plants fail | none |
| 4 | 2b1 | 2 | (a) the four defs and routes (`unit: 'IA-2b1'`), the three classifiers, `iaOutcomeRows`' text fields, the Outcomes fold with `outcomes_table_check` retargeted, the aliases, crumbs, the scope menu, the search index, and the rail units renamed; (b) the flip: `'IA-2b1'` into `IA_LANDED`; `walkthroughs.md` (the four lists, the tiers at the live size, several rows to one target, where the Outcomes explanations went); the register rows; the shots (S1 to S9); `packet-IA-2b1.md` | the four home lists; the Outcomes table as the Sites rows |
| — | stop | — | **The owner's IA-2a walkthrough** (§2). The review of IA-2b1 runs meanwhile | — |
| 5 | 2b2 | 2 | The parts splits; the hub queues as the component with "View all"; `stickyBare`; `count_check` retargeted (plants shown failing first) | the hubs' queue rows |
| 6 | 2b2 | 1 | The plan's link, G1's surface, the flip of `'IA-2b2'`, the shots, `packet-IA-2b2.md` | the plan's link line |

## 10. Done, deviations, packet

**IA-2b1 is done when**, beyond §6:
- the four lists are live from one shape and one component, with the tier controls and chips of D-IA.67 and D-IA.70;
- every plant in §8's 2b1 rows fails in `ia_gates`;
- `qty_check` runs its count and format modes and the `EQUAL` row on live numbers;
- Outcomes shows the Sites rows, with no button in a row;
- the aliases resolve with their queries;
- every list view restores from its address, and the control keeps its place in Chromium with the router present;
- the fixture proves the scale case;
- G1 prints each list at 1.

**IA-2b2 is done when** the hubs' rows have one target, "View all {n}" equals the target list's tile, G1 prints the released
Actions of the version at ≤ 2, `parts_identity` holds, and every 2b2 plant fails.

**`MOCK DEVIATION`s** (rows after the base's last, each a packet line):
- D2: no "at stake" tile and no stake sort on three lists (§4).
- D2: Search drawn from 11 items with the filters (the 30-Site frame shows filter and sort only, D-IA.67).
- D2: the Sites "Not shown" remainder beside "Show all" (D-IA.68).
- D5, resolving in IA-2d: Finding and Action rows open their decision (or the plan) until `finding/:id` and `action/:id`
  exist.
- D5, resolving in IA-2c: no Assets, Incidents and Maintenance lists (the figure's other home lists).

Closed by IA-2b2: R749, R750 and R751 (the packet names the commit).

**Packets** `packet-IA-2b1.md` and `packet-IA-2b2.md` carry `spec.md` §8's list, plus:
- the stop line, if any;
- the list counts per operator (tiles, rows, tier, Show all) and the rows per target;
- the `qty_check` keys added, and the count of keys whose format is deferred;
- the count of live cents fallbacks (expected 0);
- the shot counts per class;
- the count of mid-build questions.
