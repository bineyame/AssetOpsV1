# IA-1 and IA-2 rulings, continued (rulings-4.md is on IA-2a's open branch)

## IA-2b: the list shape (spec `spec-IA-2b.md`)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away row 46). Brief: right control per content, one interaction
grammar, exposure that scales, simplicity by design, honest numbers (`owner/owner-ui-standing-brief-2026-11-20.md`); the mock
is the layout spec (proposal page §4 "2 · Home list"). IA-2a's lessons carried in: totals and parts reconcile on screen
(D-IA.54) in one form (D-IA.59); a view change brings its content into view (D-IA.55, D-IA.58: here, the control keeps its
place); tile rows fill (D-IA.56); composed text only (D-IA.57); every plant must be able to fail.

### D-IA.61 IA-2b covers the list shape only, in two parts, with the stop at the owner's IA-2a walkthrough

- **Which shapes.** Of the eight, IA-2b builds **list** (the home list) and its four instances in the IA-2 plan: Decisions,
  Findings, Actions, Sites. Assets, Incidents and Maintenance are list instances too, but their rows open the asset page and
  its drawers (IA-2c's shape) and their store is IA-2c's timeline; building them here would draw rows with no target. Record
  pages and drawers (IA-2d) and the statement (IA-2e) stay where the plan puts them. The plan's order (list before asset)
  holds because every later shape's home list is this component.
- **Split.** 5 units, under the cap of 6, cut by dependency on the owner rather than by size: **IA-2b1** (units 1 to 3: the
  component, the four lists live, aliases, crumbs, scope menu, search index, the Outcomes fold) and **IA-2b2** (units 4 and 5:
  hub queues as the component, "View all", the plan's link to its released Actions, G1's surface). Two landing IDs, two reviews.
- **The stop point.** IA-2b2 starts only after the owner has walked IA-2a and the verdict is recorded, with any IA-2a change
  merged in. IA-2b2 edits the plan's L1 (identical on four tabs, D-IA.43), rewrites the hub queue rows the walkthrough
  passes through, and removes the hubs' "Decide" button (D-IA.65); each is a choice the owner may change on that walk. IA-2b1
  reads IA-2a only through the one-source helpers (`uxPlanState`, `planApprovedIds`, `releaseShown` via `actionState`,
  `planItemsV1`), so an IA-2a change reaches it by construction and needs no stop.
- **Base.** IA-2a's head after its latest accepted fix round; later rounds merged in; never merged before IA-2a.
- **Rejected:** building IA-2b on `main` (it needs `IA_LANDED` with IA-2a, the tab and quantity rules and `qty_check`);
  building the hub change first (it is the owner-visible part).

### D-IA.62 One list component: the address is the view

- **Model.** `iaListModel(def, items, q, scope)` is pure: scope, facets, search, sort, cap, groups, in that order (spec §3.1).
  A value that is not an option is ignored (D-IA.35 L4's rule for scope, made general). The cap keeps `def.keep` items first
  and displays in sort order (D-IA.34 for every list, not only decision queues).
- **Address.** Every filter, sort, search and "Show all" lives in the hash query (D-IA.9 "filters live in the address"), in
  one canonical order with defaults omitted, so equal views have equal addresses and the crawl's identities stay finite.
  "Show all" is a link to `show=all`, not an in-page reveal: Back restores it and the figure's "Show all 42" is the same
  control at 3 Sites and at 300. This replaces `uxCapNote`'s in-place button on IA lists only (reviewed pages keep theirs).
- **Controls.** Right control per content: a `select` per facet (few known values), a search field with a visible submit
  (free text; Enter), the scope as a chip with one way out, "Clear filters" only when something is set. A select applies on
  change; the page keeps its scroll and the control keeps focus (the D-IA.58 lesson: a view change must leave the person
  looking at what they changed, not at the top of the page). No controls under 3 items in scope (`uxQueue`'s threshold).
- **Rows.** A table (tabular content, `ux-stack` on a phone), one stretched link per row in its first cell, every other cell
  text; states are `status-pill` labels. One target per row (D-IA.9) without losing table semantics.
- **Scope menu on a list.** Entries keep the list's view; a Site entry scopes the list instead of leaving it ("The scope picks
  the Sites ... every list obeys it").
- **Rejected:** client-side filtering without the address (today's `uxApplyQueue`; Back and links lose it); a row of links
  per facet value (does not scale past a handful of values; two grammars); a debounced search that re-renders per keystroke
  (focus and screen-reader churn).

### D-IA.63 The four instances: stores, rows, facets, tiles

- **Stores are the hubs' and the plan's own** (proposal "One store, many scopes"): decisions `iaDecIds`, findings
  `uxFindingRows`, actions `WF(op).actions` with `actionState` against the case on screen (`planCaseIds`), sites
  `iaOutcomeRows`. No list copies or re-derives a state.
- **Row targets.** Decision → its page; Site → its hub. A Finding's and an Action's own pages are IA-2d's; until then their
  row opens the decision they belong to (an Action of a declared item opens the plan). `MOCK DEVIATION` D5, resolving IA-2d.
  Nothing unbuilt is reachable.
- **Tiles.** The figure's "count · count · at stake". Count tiles equal the list (n after filters, before the cap; audit C2.3).
  Actions show its release states as parts that sum to n. Sites keep "at stake" as the gap to target, its rows' gaps adding
  to it in one form (D-IA.54, D-IA.59). Decisions, Findings and Actions have **no** money tile: their stakes are valued on
  different bases and some are alternatives, so no sum is a true figure. `MOCK DEVIATION` D2 (honest numbers over the
  figure's placeholder tile).
- **Facets** are the existing words (`uxStateCount`, `UX_URG`, `LENS`, `RELEASE_WORD`, `iaOutcomeHeadline`); "Plan version"
  has one option, the version shown, so the G1 journey's filter is real and a stale version in a link is ignored, not empty.
- **Why.** Each list answers its question from the same records as every other surface, so two screens cannot disagree.

### D-IA.64 IA-2b1's wiring: the Outcomes fold, aliases with a query, crumbs, the search index

- **Outcomes** L2 is the Sites list's body without tools or tiles (D-IA.27: "IA-2b's list component absorbs this table");
  `iaOutcomeTable` is deleted, its synthetic check retargeted with every plant still failing.
- **An alias value may carry a query** (`findings-cost` → `findings?heading=optimize`, risks → protect, opportunities →
  grow; the lens tabs become a heading filter, proposal §6 row "Findings list and its lens tabs"). `portfolio/act-first` →
  `decisions` (D-IA.25's withdrawn interim alias, now with its real target).
- **Crumbs:** "Decisions" and "Sites" become links to their home lists (home list › Site › object).
- **Search indexes every object with a live target:** Findings and Actions join Sites, decisions and screens in the palette.
- **Legacy** `sites`, `findings`, `actions`, `portfolio/act-first` stay registered and byte-identical.

### D-IA.65 IA-2b2 (after the stop): hub queues are the component; the plan links its released Actions

- **Hub queues.** The Overview (top 6) and each Site (top 3) render the decisions list's rows, scoped and capped, with
  `iaCapMore` and "View all {n}" to `decisions` (`?scope=site:{k}` on a Site). Closes R749, R750, R751.
- **No "Decide" button on the hubs.** A row holds no other control and a state is a label (D-IA.9); the row is the
  decision's link, so "What needs me" stays at depth 1. The Site sticky keeps name, gap and state and loses its "Decide"
  (`stickyBare`, a byte-identical parts split). This amends D-IA.23's hub row ("the queue's first choose row's Decide") and
  D-IA.22's one sticky fix. **Owner to weigh in at the walkthrough** (owner-away row 46): the alternative, if the owner
  wants a call to act, is one "Decide" in the sticky only, never in the rows.
- **The plan's link** "Released Actions of version {n} ({r})" in L1 after the already-released clause, on all four tabs,
  only when r > 0; r is the list's count at that address (one figure, two places, `data-qty`). G1's last unmeasured surface
  (D-IA.29 R37) is then measured at ≤ 2.

### D-IA.66 Gates: written first, dormant until landed, each plant shown failing

- The table in spec §8. Independence: the live block computes its rows from the stores with its own code and never calls
  `iaListModel` or a def; the synthetic block is the only one that calls the model. `IA_FORCE_LANDED=IA-2b1|IA-2b2` and the
  dormant rule as D-IA.49; `ia_gates` gains both units' rows.
- `qty_check` keys are per view (`{list}:{quantity}:{canonical query}`), so a filtered list's total never meets an unfiltered
  one; "View all {n}" and the target list's tile 1 are compared by `count_check`, which visits the target.

## Handshake answers (round 1): IA-2b (`handshake-IA-2b.md` R1 to R8, I1 to I7)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away row 47). Each answer was checked against IA-2a's code at the
head of `task/IA-2a-plan` (`b2fb5de65`), and the live sizes and figures were read from a jsdom boot of that head (nothing was
changed). Live sizes per operator (Lakeside / Harvest / Metro): Sites 3 / 3 / 3, each operator one vertical; Decisions 8 / 3 / 4;
Findings 9 / 4 / 7, every one with a decision; Actions 6 / 3 / 2, on 4 / 3 / 2 plan items. No live list passes 10 rows, so no
live list is capped or grouped. The Sites gaps sum to `opTotals(op).variance` on all three (−$852, −$770, −$3,184.32), and
Metro's sum nets −$3,204 against +$19.68. The spec (rev 2) and the reviewer guide (rev 2) carry every answer.

### D-IA.67 Controls scale with the list, as the mock's "3, 30 and 300 Sites" figure draws them (R1, done)

- **Rule (every list, every size).** Let n_s be the store's items in scope, before facets and search. Under 3: no control.
  3 to 10 (the whole list fits under the cap): **Sort only**, the mock's "3 Sites · sort: gap" frame. Over 10 (rows are
  hidden): facets (each with at least 2 options in scope), Sort and Search, the home list figure's "Filters · sort · search".
  Groups as before (over 10, more than one group). What the address sets but no drawn control shows is named by a chip
  (D-IA.70). One component, one toolbar. The tiers are its size steps, not per-list options.
- **Why.** A filter or search finds a row you cannot see. When the whole list is on the screen, scanning ten rows is quicker
  than a form, and the controls would be clutter (owner brief: "right control per content", "simplicity by design"). The
  mock already draws the controls growing with the list. One toolbar at every size would be the "available, so shown"
  pattern the brief names.
- **Live consequence (stated in `walkthroughs.md`).** Every live list is tier 1 (Sort only), and Metro's Actions (2) have
  none. The facets reach the live screens only through the address (the aliases, the plan's link): each is a chip.
- **The scale case is proven by a fixture, never by a product route.** `tools/list_fixture.cjs` builds synthetic stores
  (`sites30`: 30 Sites in 3 groups of 18, 7 and 5, one without a target, gaps chosen so the whole-dollar rounding of the
  sum misses; `decisions25`: 25 decisions, 6 waiting, several states and due dates). `list_shape_check` block D and
  `ia_shots` inject one into the booted page through the def's `items(op)` seam (`IA_LIST_FIXTURE=sites30|decisions25`,
  in the window only) and render the real route. Block D asserts the tier at 2, 3, 10, 11 and 30 items, groups, the one cap,
  "Show all", the remainder part (D-IA.68), the cents fallback, the no-target Site and the chips. Plant `LIST_PLANT=tier`
  (the full toolbar from 3 items) fails live on every list with at least 3 rows, and in D.
- **`MOCK DEVIATION` D2** (register row): from 11 items Search is drawn with the filters. The mock's 30-Site frame shows
  "filter · sort" only. The home list figure draws them together, and one tier above the cap is simpler than two.
- **Not changed:** the scope menu's group entry (it equals "All sites" while an operator has one vertical). It is IA-1b's,
  and its entries are the same on every route. Changing it on lists alone would split the grammar. It is listed for the W1
  UI pass (owner-away row 47).

### D-IA.68 The Sites gap tile stays: it is the operator's own gap, and hidden rows show as a part (R2, done)

- **(b) Netting is honest here, and stakes are not.** Each Site's gap is actual minus target for one measure, on one basis,
  in one month (contribution, or cost for a cost operator). Gaps therefore add, and their sum is the operator's gap: at
  IA-2a's head it equals `opTotals(op).variance`, the Overview's "Gap to target" tile, on all three operators. A stake is
  measured over a different horizon and kind on each decision, so stakes cannot be added (D-IA.69). The netting is real on
  Metro (−$3,204 and +$20) and correct, because the operator's total cost is over or under its total target by exactly that
  sum. A filtered view's tile is the sum of that view (the "Below target" filter gives the shortfall), keyed per view.
  **Cross-screen assertion:** `qty_check` gains an `EQUAL` table. Its first row says the default Sites view's tile
  `sites:gap:` equals the Overview's `overview-gap` (D-IA.60 L5) within a scenario, string for string. Plant
  `QTY_PLANT=gapnet` (the tile sums only the shortfalls) fails on Metro.
- **Sites without a target** are outside the tile, and the tile says so with one line when there are any in the view:
  "{k} Sites without a target are not in this figure" (`uxKpi`'s lines). This happens only in the fixture.
- **(a) Hidden rows.** Rows over the cap are absent, and "Show all" is a link (D-IA.62). The More line then carries the
  hidden rows' gap as a part, so the screen reconciles (D-IA.54): `Not shown: {h} Sites, gap to target {gap}.` followed by
  the "Show all {n}" link. The gap is `data-qty="sites:gap:{query}" data-qty-role="part"`. This happens only in the fixture
  (block D asserts shown parts + remainder = tile). Plant `LIST_PLANT=remainder` (the line dropped) fails in D.
  `MOCK DEVIATION` D2 (the figure's "Show all 42" carries no figure).
- **(c) Form.** The parts are the shown rows' rendered gaps plus the remainder. When their sum equals the whole-dollar
  rounding of the exact total, every figure is whole dollars. Otherwise every figure of the key on that screen (rows,
  remainder, tile) takes cents. Live, the rendered sums equal the rounding on all three operators (Metro −$3,204 + $0 + $20 =
  −$3,184), so the fallback is reached only by `sites30`. If it ever fires live, the list shows cents while the Site hub shows
  whole dollars for the same Site. D-IA.59 is per screen, so this is allowed. `list_shape_check` prints how many live
  screens took the fallback (expected 0), and the packet names any.

### D-IA.69 No list sorts or sums a figure that is not commensurable; the "At stake" sort is dropped (R3, done)

- **Ruling.** The Decisions sorts are "Priority" (store order) and "Due date". The stakes at IA-2a's head are +$2,916 over
  12 months, $70 possible credit, $64,000 cover kept claimable, −$368 to a restore date, "Not valued: losses are not priced"
  and "No saving claimed". Ordering them by a number assumes they are on one scale, which is the same claim as adding them.
  It would also make "Not valued" a 0. Priority (ATTN) is the product's own ranking, and it already weighs these.
- **Class (W6).** No IA list code reads `uxStakeParts(...).num`. "Not valued" and "Not available yet" are words, never 0.
  `list_shape_check` B holds the sort lists as literals (decisions `priority, due`; findings `priority, site`; actions
  `due, item`; sites `gap, name`) and fails on any other. Plant `LIST_PLANT=stakesort` (the sort added back) fails on
  every operator.

### D-IA.70 Every view state is named on screen, and every row opens one live thing (R4, done)

- **(a) Chips.** Some view states are set by the address but shown by no drawn control: a scope other than all, a facet
  whose select is not drawn (D-IA.67, or a facet with one option like "Plan version"), and `q` when the search box is not
  drawn. Each is a chip with one way out:
  `<span class="ia-chip">{word} · <a class="ux-link" href="{the address without it}">{way out}</a></span>`. The chips sit in
  `<p class="ia-list-chips">` at the top of L2. The scope chip moves there from the tools. Ways out (copy, spec §7): scope
  "All sites"; decisions state "All states", due "Any due date"; findings heading "All headings"; actions state "All
  states", version "All versions"; sites target "Above and below target" (cost "Over and under target"); `q` reads
  `Matching “{q}”`, way out "Clear search". "Clear filters" is drawn only when 2 or more of the facets and `q` are set (one
  chip is its own way out). The empty state keeps its "Clear filters". The plan's G1 link therefore lands on Actions
  showing "Released · All states" and "Version 1 · All versions".
- **(b) Rows with no target.** Zero at IA-2a's head (every Finding has a decision, and every Action has a decision or the
  plan). The text-title branch is deleted. `list_shape_check` B fails when any store item has no live target ("{list}
  item {key} has no target"), so a later store change surfaces as a design question, not as a dead row. Plant
  `LIST_PLANT=notarget` (one Finding's decision removed in the window) fails.
- **(c) Several rows, one target.** Lakeside has 6 Actions on 4 items, and several Findings open one decision.
  `walkthroughs.md` says so, and the packet counts rows per target.

### D-IA.71 `qty_check` gains a count mode and a format mode in IA-2b1, as their own unit (R5, I2, done)

- **Ruling: extend the check now**, so that every count and every money format the lists show is checked live (the honest,
  working check). Unit 2 (new, 1 commit, about 0.5 unit):
  - **Count mode.** IA count figures carry `data-qty-kind="count"`. The value is the one integer in the element's text; none
    or more than one fails ("Released Actions of version 1 (2)" therefore wraps `2` in its own span). Parts sum to the
    total, and totals of a key are equal across a scenario's routes (the existing rules). No `data-qty-kind` means money, so
    IA-2a's markup is unchanged.
  - **Format mode (D-IA.59, IA markup).** Per screen and key, every rendered money string has the same number of decimals.
    It covers keys whose figures are all IA `data-qty`. A key with a reviewed `QTY`-table member (`plan-spend`) is printed
    as "format deferred to IA-2e (D-IA.59)" with its count, never passed silently.
  - **`EQUAL` table** (D-IA.68): `[['sites:gap:', 'overview-gap']]`.
  - **Plants, each failing on a live number** (the output names where): `counts` (the Actions "Returned" part dropped;
    fails where Returned is above 0, at least Lakeside's non-default case); `tilecount` (the Actions tile counts released
    rows only; all three); `sitegap` (one row's gap part dropped; all three); `listcents` (rows with cents, tile whole; all
    three on format, Metro also on sum); `gapnet` (Metro).
- **Not live, so proven elsewhere.** "Show all {n}" and group heads never render live (no list over 10). Block D asserts
  them on the fixture. "View all {n}" is live from IA-2b2 (Lakeside's 8 decisions at the Overview's cap of 6) and is
  checked by `qty_check` and `count_check` there.

### D-IA.72 The shots matrix covers every state and non-default case, with a count per class (R6, done)

`ia_shots` list set, heavy slot, each class printed with its count (as the "81 switches" count). In every shot: no sideways
scroll; every child of the tools and chips rows ends inside the page; tile rows fill (D-IA.56); at 390 the table is stacked
with its labels.

| Class | Cases | Sizes, themes |
|---|---|---|
| S1 default | 4 lists × 3 operators | 390, 1280, 1440 × light, dark |
| S2 each facet value with at least 1 row, by address (chip) | per list and operator | 390, 1440, light |
| S3 each non-default sort | per list and operator | 390, 1440, light |
| S4 a search with no result (`q=zzqx`): empty state, sort and chips kept | 4 × 3 | 390, 1440, light |
| S5 scope = the first Site (chip) | 4 × 3 | 390, 1440, light |
| S6 Actions after Approve and after Send back; Lakeside 6500/No (Returned) | 3 × 2 + 1 | 390, 1440, light |
| S7 no controls (Metro Actions, 2 rows) | 1 | 390, 1440, light |
| S8 fixture: `sites30` default, `show=all`, a facet + `q`, filters leaving nothing; `decisions25` with State "With the plan sent back to draft" | 5 | 390, 1440 × light, dark |
| S9 keeps place at 390: Lakeside Decisions sort change (live), `sites30` facet change and search submit | 3 | 390 |

S9 first scrolls so the control sits at half the viewport's height, then changes it. It asserts the control's top within
±4 px and focus on it. A case whose page cannot scroll that far is printed as skipped with its reason, and the fixture case
always can. Plants: `listkeep` (D-IA.75's listener not registered; fails S9 live), `listwrap` (`nowrap` on the tools and
chips rows; fails S8 at 390), `emptytools` (the empty state without its sort and chips; fails S4 on all three operators).

### D-IA.73 Each plant compares against an independent path (R7)

- **(a) `restore`** is "the address's sort and facets ignored on first render". Block B compares a fresh boot at an address
  with the in-page path to it (the select changed or the form submitted from the default view, then `hashchange` and
  render). L2's `innerHTML` must be byte-identical. Live, that is the sort select. On the fixture, it is a facet and the
  search. The plant fails live.
- **(b) `listkeep`** fails on the shipped order once D-IA.75 holds: S9 runs in Chromium with the router's `hashchange`
  handler present, never in isolation.
- **(c) Own tables.** Block B carries literal tables: the facet options and words, the sort lists, `LENS` headings,
  `RELEASE_WORD`, `UX_URG`, and the decision state words. It first asserts that the product's tables equal them, so a word
  change fails with a named difference and is re-ruled on purpose. B's rows are computed from the stores (ATTN, `DEC`,
  `HC.findings`, `WF(op).actions`, `OPS[op].sites`) and from reviewed one-source classifiers (`uxDecState`, `releaseShown`,
  `planCaseIds`, `planApprovedIds`, `planItemsV1`, `opTotals`). B never calls the list's code: `iaListModel`, `IA_LIST_DEFS`,
  `iaDecStateKey`, `iaActionStateKey`, `iaFindingSite`, `uxFindingRows`, `iaOutcomeRows`. The guide's grep names all of these.

### D-IA.74 IA-2b1 reads IA-2a only at render; the stop's re-rule list grows (R8)

Confirmed as a rule for the build. Every option, word and tile value is computed when the list renders, from the helpers:
the State options from `iaDecStateKey` over the store, the version option from `uxPlanState(op).version`, its ids from
`planApprovedIds`/`planItemsV1`, and the release words read from `RELEASE_WORD`, never copied. The §2 re-rule list adds "the
Decisions list's State facet words, and the Actions list's State and Plan version facets". If the owner's walkthrough
changes any of them, they are re-ruled before IA-2b1 merges, not patched in IA-2b2.

### D-IA.75 The scroll and focus keep runs after the router's `hashchange`, keyed to the address it wrote (I1, done)

- **Verified.** In `index.html` the router's listener (`render(); window.scrollTo(0,0)`) is registered before
  `iaTabSwitch`'s, and listeners run in registration order. A restore inside `render()` (via `iaBind`) is therefore undone.
- **Rule.** (1) The tools listener computes `h = iaListHref(...)`. When `'#/' + h === location.hash` it does nothing (a submit
  is still prevented) and stores nothing. Otherwise it stores `IA_LIST_KEEP = { hash: '#/' + h, name, top }`, where `top` is
  the control's `getBoundingClientRect().top`, then sets `location.hash`. (2) `iaListRestore` is a `hashchange` listener
  registered in `ia-routes.js` after `iaTabSwitch`'s. It runs synchronously, in the router's task, so nothing paints at the
  top first. It reads `IA_LIST_KEEP` and **clears it on every `hashchange`**. When the new hash equals `keep.hash` and the
  control exists, it scrolls (instant) by the control's new top minus `keep.top`, then focuses the control
  (`preventScroll`). (3) `iaBind` is unchanged. A stale keep cannot apply: it is keyed to its hash and cleared at the next
  change. List routes have no `tabGroup`, so `iaTabSwitch` never acts on a list change. The Outcomes fold has no controls.
- **Done** means that S9 passes in Chromium with the router present and that `listkeep` fails there.

### D-IA.76 List cells hold text only; the figures' explainers stay on the Site hub (I3, done)

- `iaOutcomeRows` (IA code) gains plain fields: `result` ("{actual} against a target of {plan}", without the `fig()`
  button), `gapText` (`usdW(gap, true)`) and `driver` (the driver's words and its heading word, as text). The gap cell is
  `<span{figA('gap', key, gap)} data-qty="sites:gap:{query}" data-qty-role="part">{gapText}</span>` (`figA` writes data
  attributes only). `resultHtml`, `gapHtml` and `driverHtml` go with `iaOutcomeTable` unless the builder's grep finds another
  caller, in which case they stay.
- **Why.** The row's one target is the Site hub, where each figure keeps its "show how this is worked out" button, one click
  away. An in-cell button would be a second target in a row that is a link (D-IA.9). No carve-out is made, and B's
  "exactly one interactive element" stands.
- `outcomes_table_check`: A, C and D unchanged in meaning; B per D-IA.80; a new assertion "no button and no second link in a
  row". The Outcomes tab's figure buttons go; `walkthroughs.md` says where the explanations are (owner-away row 47).

### D-IA.77 Three IA classifiers, one each (I4, done)

In `ia-shapes.js`, used by the defs, the tiles and the facets (and never by B, D-IA.73):
- `iaDecStateKey(id)` returns `waiting` (`uxDecState` key `choose` or `none`), `draft` (`approval` with `draft`),
  `approval`, or `underway` (`released`, including the "chosen in this demonstration" variants by their key).
  `IA_DEC_STATE_WORD` holds the four option words beside it. B asserts that each word appears in `uxStateCount`'s output
  for an id of that key.
- `iaActionStateKey(op, a)` returns `returned` when `!planCaseIds(op).includes(a.item)`, else `released` when
  `releaseShown(op, a.item).at`, else `waiting`. This is `actionState`'s rule on the same helpers. B asserts agreement with
  the pill's `data-release` for every Action. The State column shows `actionState(...)[0]`.
- `iaFindingSite(op, x)` maps the stripped name to its key (`OPS[op].sites.find(k => SK[k].name === x.site)`). An unmatched
  name fails B.
- No second subscriber is needed. Approve and Send back run on the plan, and the list reads the stores at each render.

### D-IA.78 One alias helper (I5)

`iaAliasTarget(path)` returns `{ path, query }` or `null` (a function value is called with its params first).
`iaLiveAlias(path)` returns its path when that path is landed. `iaCanon` writes the value's query, then the href's
parameters not already set. When the target is a list route, it writes them through `iaListHref`'s order. `iaLive`,
`iaCanon` and `iaPaletteFilter` call the helper. `shape_check` item 7 and the crawl split the value with their own code
(independence). Plant `SHAPE_PLANT=aliasq` breaks the helper (the query left in the path) and fails item 7 and G1.

### D-IA.79 Dormancy: the rail's units and the `OWN` map (I6)

Confirmed at IA-2a's head: `IA_RAIL`'s Sites, Findings, Decisions and Actions have `unit: 'IA-2b'`. Unit 4(a) renames them
`IA-2b1` (still unlanded until the flip in 4(b)). `ia_gates`' `OWN` gains `'IA-2b1'`: `list_shape_check`,
`outcomes_table_check`, `shape_check`, `qty_check`, `click_depth_check`, `copy_check`; and `'IA-2b2'`: `count_check`,
`parts_identity`, `click_depth_check`, `qty_check`. `shape_check` item 11 is in the dormancy list.

### D-IA.80 One cap per list; groups are how the shown rows are drawn (I7; amends D-IA.27's per-group cap)

- **Rule.** The cap is 10 over the whole list, ranked keep-first then in sort order. The shown rows are drawn in group
  blocks: groups in order of first appearance in the sort, rows in sort order within a group. Each group head shows its
  count in the view (before the cap) as a count part `sites:n:{query}`, and the heads sum to tile 1. A group with no row
  shown keeps its head. There is one "Show all {n}", and `show=all` expands every group.
- **Why.** The mock's 30-Site frame draws "Mini-grids · 18 · Cold rooms · 7 · EV depots · 5 · Show all 30", which is one
  cap and one link with groups larger than 10. A cap per group needs a "Show all" per group, and one address parameter
  cannot hold that.
- `outcomes_table_check` B becomes: 12 Sites in groups of 7 and 5 give 10 shown in two groups headed 7 and 5, then "Show
  all 12". Plant `group` kept.

### D-IA.81 Size: 5 units become 6; the split and the stop hold

- **Added:** `qty_check`'s modes and plants (+0.5, its own unit), the tiers, chips and fixture block D (+0.4), the shots
  matrix (+0.4), and the alias helper, classifiers and text fields (+0.2). **Removed:** the stake sort, the no-target branch
  and the per-group cap (−0.2). Net: about +1.3 units, from 5 units (8 commits) to **6 units (about 10 commits)**.
- **Units:** IA-2b1 = 1 checks first (2 commits), 2 `qty_check` modes (1), 3 the component (1), 4 the four lists live and the
  flip (2), so 4 units and about 4.3 of effort. IA-2b2 = 5 hub queues (2) and 6 the plan's link (1), unchanged at about 2.
  Each part is under the cap of 6, and the whole is at 6, not above.
- **The stop** stays before unit 5 (formerly 4). D-IA.74 confirms that IA-2b1 needs no stop.
