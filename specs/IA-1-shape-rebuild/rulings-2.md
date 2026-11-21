# IA-1 rulings, continued

Architect (Claude), 2026-11-20. `rulings.md` is at the 15k-token cap (RULES §9); later answers are here. Index lines are in
`.ai/decisions/index-rulings-10.md` (to D-IA.35) and `index-rulings-12.md` (D-IA.36 on).

## IA-1b mid-build answers

Answered against `task/IA-1b-hub` at `aa9eb82f7`. Question in `mid-build-questions.md`.

### D-IA.31 A drawer's focus trap holds over what Tab really reaches (answers Q1)

- **Class.** The trap's first and last are computed from a set that is not the set Tab reaches. `offsetParent !== null`
  keeps links inside a closed `<details>` (Chromium), and the set changes whenever a link becomes text (`iaUnlink`, every
  unbuilt address under D-IA.16, now and in IA-1c). Waiting for IA-2d would fix this one drawer by accident and leave the
  class: the next unlinked last link breaks the trap again. IA-1b fixes it now.
- **Ruling: the reviewed code that may change, and nothing else.**
  - `loop-ux.js`, the drawer `keydown` listener (the one opening `const d = document.querySelector('.ux-drawer[data-open="true"]')`):
    only its `Tab` branch. Its `Escape` branch, `uxOpen`, `uxClose` and the click listener stay byte-identical.
  - One new page-global function in `loop-ux.js`, declared as a function declaration (so a plant can reassign it, as
    the palette plant does `iaPaletteFilter`), placed just above the listener:
    `function uxTabbable(x)` returns true only when all hold:
    1. `x.getClientRects().length > 0` (rendered; replaces `offsetParent`, which also misreads fixed-position elements);
    2. `getComputedStyle(x).visibility !== 'hidden'`;
    3. `!x.closest('[inert], [hidden], [aria-hidden="true"]')`;
    4. `!x.matches('[tabindex="-1"]')`;
    5. `!x.closest('details:not([open]) > :not(summary)')` (nothing inside a closed `details` but its own `summary`;
       this also covers nested closed `details`).
  - The `Tab` branch: the selector stays as it is; the filter becomes `.filter(uxTabbable)`. Wrap rule:
    `Tab` when `document.activeElement` is `last` **or is not in `f`** goes to `first`; `Shift+Tab` when it is `first`
    **or is not in `f`** goes to `last`; both `preventDefault()`. Otherwise the browser moves focus. With an empty `f`,
    `preventDefault()` and focus the drawer's Close (`.ux-x`), so focus never leaves an open drawer.
  - `index.html` is rebuilt from the module as for every vNEXT change. No other reviewed function changes.
- **Checks (uxi, `ux_interaction_check.cjs`).**
  - **Retarget "overview drawer &lt;k&gt;"** (block 1): after opening, press `Tab` 30 times then `Shift+Tab` 30 times,
    `waitForTimeout(12)` each, and assert after **every** press that `document.activeElement.closest('#uxd-<op>-<k>')`
    is non-null (today it checks only the end state). Run for all three operators (`lakeside`, `harvest`, `metro`), the four
    headings each.
  - **New "drawer trap sweep"**: for each operator, on `#/portfolio`, `#/portfolio/outcomes`,
    `#/portfolio/demand-and-capacity` and the operator's first Site Overview, every visible `[data-ux-drawer]` opener (one per
    drawer id) gets the same 30 + 30 walk with the same per-press assertion, then `Escape` returns focus to the opener. One
    line per route and operator, naming the first drawer that leaks.
  - **New "drawer trap unlinked last"** (the class, independent of the live link set): on Lakeside `#/portfolio`, open the
    Assure drawer, then in the page replace every `a[href]` after the Close button with `iaUnlink`'s text form (run
    `iaUnlink` on the drawer body with those hrefs treated as unbuilt, or substitute the exact markup it renders:
    the element carrying `data-ia-to`), and append `<details><summary>More</summary><a href="#/plan">x</a></details>` at the
    end of the drawer body, closed. The walk must stay inside, and `Shift+Tab` from Close must land on that `summary`.
    It holds whether or not IA-2d relinks Scope & coverage.
- **Plant that must fail: `UXI_PLANT=trap`.** In the page, `uxTabbable = x => x.offsetParent !== null` (the pre-fix
  filter). Runs "drawer trap unlinked last" and the Lakeside "overview drawer assure" walk only (its host), and must FAIL on
  both; the uxi plant runner exits non-zero if either passes. Record its first failing line in the packet's plant table.
- **Sweep of the class.** `offsetParent` decides focus in one other place, `uxFocusAction` (`loop-ux.js`): it picks a target
  to focus after an act, not a trap's bounds; a hidden target falls back to the page's `h1`, so focus does not escape. Not
  this class; unchanged. Any later trap (palette, popover) uses `uxTabbable`.
- **Count.** Q1 stays counted (1); the template defect is that the spec named `iaUnlink` but not the reviewed code that
  depends on the live link set. Spec §7's reused-code list must, from IA-1c, name each reviewed function that reads the
  focusable or link set of a page it changes.
- **Why.** A trap is correct only if its bounds are computed over what Tab can reach; matching that set (and wrapping
  from any position outside it) holds whatever the last element is. The unlinked synthetic case keeps the proof once the
  real link returns.

## IA-1b review answers (r1)

Answered against `task/IA-1b-hub` at `aa9eb82f7` and `.agent/review-IA-1b-r1.md`. **M1** is D-IA.31 (above), unchanged.
Everything below lands in IA-1b's fix round unless marked queued; every new or changed gate is listed with a plant that
must fail it, and each plant joins `ia_gates.cjs`'s `IA-1b` list (its first failing line goes in the packet's plant table).
Reviewed functions that change are named here; spec §7's reused-code list reads these rulings as part of it.

### D-IA.32 G1 counts opening a closed disclosure as a click (answers M2, measurement)

- **Class.** Content the reader counts as on the page is not on screen until a click. D-IA.21 closed it for drawers;
  a closed `<details>` is the same class (and D-IA.31's `uxTabbable` already treats it so for focus). D-IA.10's "a
  navigation … opens a drawer" now reads "opens a drawer or a closed disclosure".
- **Ruling (`click_depth_check.cjs`, `readEdges`).**
  - A third node kind: `<owner>#details=<k>`, where `<owner>` is the page or drawer node whose region holds the
    `details`, and `<k>` is its `id` if it has one, else its 0-based index among all `details` of that owner root in
    document order. Only a `details` **without `open`** at insertion (after `iaFinish`) is a node; an open one is
    transparent (its contents read as the owner's).
  - Its `summary` is the owner's edge to it (label: the summary's text, first 40 characters). An element whose nearest
    closed `details` ancestor is D (other than D's own `summary`) is an edge of D's node, never of the owner. Nesting
    recurses: a closed `details` inside D is a node reached from D. A drawer inside a closed `details` keeps its own
    node; its opener is read where the opener sits.
  - **Fixture test, extended:** the region also holds `<details><summary>S</summary><a href="#/fixture-c">C</a>
    <button type="button" data-ux-drawer="fixture-e">E</button></details>` and `<details open><summary>O</summary><a
    href="#/fixture-f">F</a></details>`, plus `<div class="ux-drawer" id="fixture-e"></div>` outside both. Expected,
    in addition to today's: `page -> page#details=0`, `page#details=0 -> fixture-c`, `page#details=0 ->
    page#drawer=fixture-e`, `page -> fixture-f`; and never `page -> fixture-c` or `page -> page#drawer=fixture-e`.
- **Plants that must fail.**
  - `G1_PLANT=details`: the reader ignores `details` (today's behaviour). The fixture test fails.
  - `G1_PLANT=closed` (the reviewer's plant, on the live app): the Overview's plan tile link "Review the plan" is
    wrapped in `<details><summary>More</summary>…</details>`. `portfolio › plan` reads depth 2 and fails its limit of 1.
- **Sweep.** With the new reader and before D-IA.33, record every G1 surface's depth on all three operators in the
  packet. Expected: only the driver surfaces move (+1, to 4). Any other surface past its limit stops the round and
  comes to the Architect; no number is adjusted to fit.

### D-IA.33 The Site Overview opens "What is driving the gap" (answers M2, the journey)

- **Ruling.** On the hub's Site Overview (`site/:site`) the first section, "What is driving the gap", renders open;
  the other six stay closed. The journey is then Outcomes tab (1), Site row (2), the largest driver's opener (3),
  within D-IA.10's limit of 3, with the answer itself ("{driver} {figure} is the largest") at depth 2.
  - `uxSecA(label, answer, body, open = false)`: when `open` is true the `details` tag gains ` open`; with the default
    every existing call renders byte-identical.
  - `uxSiteParts(sk, P, qMax, openFirst = false)`: passes `open = true` to the first section only when `openFirst`.
    `shapeHubSite` passes `true`; `uxSitePage` passes nothing, so `parts_identity` holds as today (37 + 3 sticky only).
- **Rejected.** Raising the limit to 4 (G1 is the owner's "2–3 clicks"); linking Outcomes column 5 straight to the
  drawer (needs drawer addresses, IA-2d); moving the driver openers into the summary (a second rendering of the board).
- **Why.** The owner counts the answer, not the evidence; the Finding on the largest adverse driver is an answer
  surface (D-IA.10), and the section that holds it is the page's reason to exist. Progressive disclosure keeps the
  evidence sections closed.
- **Gate.** G1 with D-IA.32's reader passes with every driver surface at 3. Plant `G1_PLANT=siteclosed`:
  `shapeHubSite` passes `openFirst = false`; the driver surfaces read 4 and fail.
- **`MOCK DEVIATION`**, D2 improvement, final. Register row **R752**: `site/*` · "What is driving the gap" closed at
  load (reviewed Site page) · Open at load on the hub; the other six sections stay closed · D2 · G1 (owner, 20 Nov):
  the Site's answer within 3 clicks; the section holds it · none (final) · IA-1b.

### D-IA.34 A capped queue keeps every decision waiting for a choice, and says what it leaves out (answers M3)

- **Class.** A cap that cuts by position hides whatever ranks low in that order, including what needs a choice,
  and the counts beside it then disagree with the rows. One rule for every capped decision queue (Overview top 6,
  Site top 3; IA-2b's lists inherit it).
- **Ruling.**
  - **Selection** (new, pure, `ia-shapes.js`): `iaQueueCap(ids, cap)` takes the merged decision ids in the reviewed
    order (`uxMergeRows(rows).map(m => m.d)`) and returns `{ shown, hidden }`: the ids with `iaWaiting` first, then
    the rest, each part in reviewed order; `shown` is the first `cap` of that ranking, **displayed in reviewed order**;
    `hidden` is the remainder, in reviewed order. With `cap = Infinity`, `shown` is the input unchanged.
  - **The line** (new, pure): `iaCapMore(hidden)` returns `''` when `hidden` is empty, else `<p class="ux-cap-more"
    data-ia-more="{N}">And {N} more: {parts}.</p>`, where `{parts}` is `uxStateCount(hidden)` with its leading
    "{n} decision(s): " removed (for example "And 2 more: 2 awaiting approval."). From IA-1c, when `hidden` holds a
    waiting decision, the line ends with ` ` + `uxOpener('ia-inbox', 'Open Waiting for you', 'ux-link')` (the inbox
    lists every waiting decision, D-IA.24).
  - **Where:** `uxSiteParts` replaces its `slice(0, qMax)` selection with `iaQueueCap` (identity at `Infinity`, so
    `uxSitePage` is unchanged) and appends `iaCapMore(hidden)` after the queue list inside the queue panel;
    `uxOverviewParts(op, rank = false)` does the same for its top 6 only when `rank` is true, and `shapeHubOverview`
    passes `true`. The legacy `uxOverview(op)` keeps today's bytes. The panel heading counts, the split, the sticky
    pill and the queue's `ux-qcount` are unchanged.
  - **On the demo data:** Lakeside's Overview shows its 3 waiting decisions, `mto-losses` among them, and "And 2 more:
    …"; Mto shows both waiting decisions and "And 1 more: …". The primary and the sticky "Decide" stay "the first
    `choose` row among those shown".
  - **The invariant (IA-1b):** no waiting decision is hidden by a cap while the inbox is unlanded; from IA-1c a hidden
    waiting decision is allowed only with the inbox opener on the line.
- **Gate (`count_check.cjs`, all operators and its three states).** On the Overview and every Site: rows shown +
  `data-ia-more` = the heading's count; every id with the check's own waiting rule is a shown row (IA-1b) or counted
  on a line that carries the inbox opener (from IA-1c); the line's parts equal the hidden rows' states. Synthetic
  (jsdom, in the same check): `iaQueueCap` on Mto's ids with `cap = 1` shows the first waiting id and hides the other,
  and `iaCapMore` of that hidden set reads "And 3 more: 1 waiting for a choice, …" with the parts the check computes.
- **Plants that must fail.** `COUNT_PLANT=capsel`: `iaQueueCap` takes the first `cap` in reviewed order (Lakeside's
  `mto-losses` is hidden). `COUNT_PLANT=capmore`: `iaCapMore = () => ''`.
- **Register.** Yes, the Site cap needs a row: it removes rows the reviewed Site page showed. **R751**: `site/*` queue
  panel · every decision at the Site (reviewed Site page) · the top 3 by `iaQueueCap`, with "And {N} more: …" · D5 ·
  "View all {n}" to `decisions?scope=site:<key>` is IA-2b's · IA-2b · open. **R749** is amended in the same commit:
  its "what is shown" cell adds "the top 6 by `iaQueueCap`, with 'And {N} more: …'".
- **Why.** "What needs me" is G1's first journey; a count of 2 beside one visible row is the honesty class the
  standing brief names. Ranking inside the cap keeps the budget at any scale; keeping every waiting row whatever the
  cap would not. Display order stays the reviewed priority order, so the queue's sort and grouping still mean what
  they say.

### D-IA.35 The review's Lows: all fixed in IA-1b; one sweep queued (answers L1 to L5)

- **L1, fix now. Checks retargeted to live routes, each shown failing first (P16).**
  - `plan_switch_check.cjs` residual: read Ruiru's Site page (`#/site/ruiru`, Metro), the "What is driving the gap"
    summary answer; assert it contains `{usdW(residual, true)} not attributed yet`, with `residual` computed by the
    check as today (not a literal). Plant `PS_PLANT=resid` (new env in that check): in the page, `uxSiteBoard`
    wrapped to strip `; … not attributed yet` from `answer`. Must fail.
  - uxi "EV board": on Metro `#/portfolio/demand-and-capacity`, assert one row whose text holds "Revenue", "charging
    is a cost centre" and "Not applicable", and no "Grow revenue Not measured yet" anywhere. Plant `UXI_PLANT=evrev`:
    after render, that row's "Not applicable" text node is replaced by "Not measured yet". Must fail.
- **L2, fix now. The three text-accepting retargets expire with IA-1c.** uxi reads `landedC = IA_LANDED.has('IA-1c')`
  from the page and passes `textOk = !landedC` into the three evaluations (drill-down `done`, drivers `got`, queue
  `firstPrim`); the `.ia-unlinked[data-ia-to^="decision/"]` form counts only when `textOk`. Plant `UXI_PLANT=expiry`:
  the check forces `landedC = true`. On the IA-1b head all three must fail. IA-1c's card keeps the plant and drops it
  only once its decision links are live (it then passes on the real links).
- **L3, fix now. Column 5 against the board, one source.** `count_check.cjs`, per operator and Site with a target:
  the check computes the most negative non-residual `vr` from `uxSiteDriversShown(sk)` itself (not through
  `iaLargestAdverse`), asserts that the Site page's board has an opener with that label whose `data-board-v` equals
  it, and that the Outcomes row's column 5 shows that label and `usdW(vr, true)`; with no negative driver, column 5
  shows the "no driver" cell and no board row has a negative `data-board-v`. Plant `COUNT_PLANT=adverse` (the
  reviewer's: `iaLargestAdverse` picks the smallest adverse driver). Must fail; if no demo Site has two adverse
  drivers it cannot, and the round stops and asks.
- **L4, fix now. The headline reads the table's rows; a scope never empties by address.**
  - New pure `iaOutcomeScope(rows, scope)` holds the one filter; `iaOutcomeTable` and `shapeHubOutcomes` both call
    it (the headline is `iaOutcomeHeadline(iaOutcomeScope(rows, ctx.scope), …)`). `OUT_PLANT=scope` now rewrites
    `iaOutcomeScope`'s source.
  - The scope parser resolves `group:<g>` only when the operator has a Site in group `g`, and `site:<k>` only for the
    operator's Sites (D-IA.28's class); anything else is `all`, and the scope switch shows "All sites".
  - `iaOutcomeHeadline` with `m = 0` reads "No Site in this scope has a target in {month}" (both kinds).
  - **Gates.** `outcomes_table_check` case C also asserts the headline over the scoped rows ("{n} of 7 …"), and a
    case E (no row with a target) asserts the new sentence. Plants: `OUT_PLANT=headline` (`shapeHubOutcomes` passes
    all rows to the headline; checked live on Lakeside `#/portfolio/outcomes?scope=site:mto` against the rendered
    rows) and `SHAPE_PLANT=foreignscope` (the parser accepts any group: Lakeside `?scope=group:cold` renders 0 rows,
    and shape_check asserts 3). Each must fail.
- **L5, fix now for Outcomes; the class sweep queued to IA-2b.** At width ≤ 760 px `table.ia-outcomes` stacks into
  labelled cards with the options table's rules (`ux.css`, `table.ux-opts` block), generalised under one class
  `ux-stack` that both tables carry; every `td` gets `data-label` = its column header. Gate: `ia_shots.cjs` at 390,
  every `table.ux-stack` cell has `scrollWidth <= clientWidth + 1` and the table no wider than its container.
  Plant `SHOTS_PLANT=stack` removes the media rule. Must fail. **Queued (IA-2b, the list component):** every other
  wide data table on an IA route gets the same class and the same 390 gate; IA-2b's card lists them.
- **Not changed.** The Overview scope switch changing nothing while each operator has one group (review residual
  risk) is correct and stays; IA-2b's lists are where scope bites.

### Owner questions (W3; defaults applied)

- **OQ-IA.3 The Site page opens on its drivers, and capped queues rank waiting decisions first.** **Default:** both, as
  D-IA.33 and D-IA.34 rule; the owner sees them at the G2 stop. The alternatives (all sections closed; queues cut in
  priority order with a "View all" from IA-2b) put the largest driver at 4 clicks and hide a waiting decision.

## IA-1c review answers (r1)

Answered against `task/IA-1c-decision` at `c139ac40b` and `.agent/review-IA-1c-r1.md`. Everything lands in IA-1c's fix
round, before the G2 stop. Module paths are under `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`.
Every new or changed gate names a plant that must fail it; a plant of a check `ia_gates.cjs` runs joins its `IA-1c` list,
and a plant of `ia_shots.cjs` or uxi is run once by the round. Each plant's first failing line goes in the packet's plant
table. No reviewed function in `loop-ux.js` changes in this round; no copy is added (spec §7).

### D-IA.36 An in-page link scrolls on the page it is on; it is never a route (answers M1)

- **Class.** The router reads every hash as an address, so any link of the form `#<id>` (an in-page anchor) leaves the
  page for not-found. Today: "See the options" and "Choose another option" (`loop-ux.js`, `#uxcards-<id>`); any later
  section with an `#id` link fails the same way. One rule in the IA router, not a fix in the reviewed card.
- **Ruling (`ia-routes.js`, new code; the reviewed card markup stays byte-identical).**
  - `function iaInPage(a)` (a function declaration, so a plant can reassign it). Returns `false` unless all hold: the
    link's `getAttribute('href')` starts with `#`, is not `#` alone and does not start with `#/`; and
    `document.getElementById(decodeURIComponent(href.slice(1)))` is an element inside `#app`. Then it scrolls that
    element to the top of the view (`scrollIntoView({ block: 'start', behavior: 'auto' })` under
    `prefers-reduced-motion: reduce`, else `'smooth'`), gives it `tabindex="-1"` if it is not focusable, focuses it with
    `{ preventScroll: true }` and returns `true`.
  - One listener, registered once in `ia-routes.js`: `document.addEventListener('click', e => { … }, true)`. It acts
    only on a primary click with no modifier (`e.button === 0`, no Ctrl, Meta, Shift or Alt) on `e.target.closest('a[href^="#"]')`;
    when `iaInPage(a)` returns `true` it calls `e.preventDefault()`. The hash, the route, its `?scope=` query and
    `location.search` (`?state=`) are unchanged, so no `hashchange` fires and Back is unaffected.
  - A link whose `#<id>` names no element falls through as today (not-found); the gate below makes that a defect.
    A typed or pasted `#<id>` address is not a page and shows not-found, as today.
  - If the sticky bar covers the target's heading after the scroll (uxi below measures it), `ia.css` gives the target's
    class (`.ux-ocards`) `scroll-margin-top` equal to the sticky bar's rendered height; nothing else.
- **Gates.**
  - `shape_check.cjs`, on every live route of the three operators in its three states: every `a[href^="#"]` is either
    a `#/` link whose path is landed (as the crawl already asserts) or names an element `id` present in the page.
    First failing line names the route and the href.
  - uxi, new "in-page link": Metro `#/decision/ruiru-connector?state=no-recommendation` (via `location.search`), at 1440
    and 390: click "See the options"; assert the hash path is still `decision/ruiru-connector`, the H1 is unchanged, no
    "Page not found", `document.activeElement.id === 'uxcards-ruiru-connector'`, and that section's `h2` top is at or
    below the sticky bar's bottom and within the viewport.
- **Plants that must fail.** `SHAPE_PLANT=anchor`: an `<a href="#nowhere">x</a>` appended to the decision's L1 region on
  `#/decision/kisiwa-om`. `UXI_PLANT=anchor`: in the page, `iaInPage = () => false` (the not-found lands).
- **Why.** An anchor is a position on a page, not a page; the router telling them apart once fixes every present and
  future anchor. §7 is kept: the reviewed card is unchanged and the router is IA code.

### D-IA.37 The top bar is one row from 761 px up: controls collapse in a fixed order, never truncate (answers M2)

- **Class.** Each width band got its own patch (the reviewed `mockups.css` hide at ≤ 1100, IA-1c's ellipsis, the
  761 to 1199 wrap, the 761 to 1023 inbox label), so the bar changes shape four times and a label reads as overflow.
  Any breakpoint list also fails on content it was not tuned for (a long Site name in the scope switch, D-IA.40). One
  content-measured rule replaces them.
- **Ruling.**
  - **Two forms of the search control.** Full: icon and "Search Sites, decisions and Findings". Icon: the same button,
    its `aria-label` and Ctrl K unchanged, `.ia-search-t` visually hidden with the clip pattern the inbox label uses,
    `padding: 0 8px`. No new copy.
  - **The collapse order** (`ia.css` keyed on `data-fit` on `.ia-frame .topbar`): `0` all full; `1` the search in icon
    form; `2` also the inbox label visually hidden (icon and badge stay); `3` also the avatar hidden. The scope switch,
    the period chip and the theme toggle never collapse or truncate.
  - **The measure** (`ia-routes.js`, `function iaFitTopbar()`, a function declaration): only when `innerWidth >= 761`;
    set `data-fit="0"`, then step up while the bar does not fit, stopping at `3`. Fits means `tb.scrollWidth <=
    tb.clientWidth + 1`, with the bar `flex-wrap: nowrap` and every item `flex: none` at ≥ 761 (nothing can shrink, so
    overflow is the only way it can fail). Called at the end of `iaRender`, on `resize` (one `requestAnimationFrame`
    per burst), and once on `document.fonts.ready`. Below 761 it removes `data-fit` and the phone rules hold as reviewed
    (two rows by design; search hidden at ≤ 600).
  - **Removed from `ia.css`:** the searchbox `flex:0 1 auto;min-width:96px;overflow:hidden`, the `.ia-search-t` ellipsis
    rule, the 761 to 1199 wrap media rule and the 761 to 1023 inbox-label media rule. **Added:** at ≥ 761,
    `.ia-frame .topbar .searchbox{display:flex}` (over the reviewed ≤ 1100 hide, which stays for legacy screens).
  - If level 3 does not fit at some width the bar overflows and the gate fails; the round stops and asks. No width,
    gap or label is tuned to pass.
- **Gate (`ia_shots.cjs`, the width sweep).** Widths 761, 800, 900, 1023, 1024, 1100, 1101, 1199, 1200, 1280, 1366, 1440,
  1600, 1920; routes `portfolio`, `plan`, `x-unknown` and, per operator, the decision whose Site name is longest; light.
  At every width ≥ 761: `oneLine` (today asserted only at ≥ 1200), no item past the window, and no truncated control
  (for each visible `.ia-search-t`, `.ux-scope-sw>summary`, period summary and `.ia-inbox-label`, `scrollWidth <=
  clientWidth + 1`). At 1440 on `#/portfolio`, every operator: `data-fit="0"` (the full search is shown where it fits).
- **Plants that must fail.** `SHOTS_PLANT=fit`: `iaFitTopbar = () => {}` and re-render (no collapse; the bar overflows
  at 761 to about 1330). `SHOTS_PLANT=truncate`: a style tag `.ia-frame .topbar .searchbox{max-width:140px;overflow:hidden}
  .ia-frame .topbar .ia-search-t{overflow:hidden;text-overflow:ellipsis}` (the truncation check bites alone).
- **`MOCK DEVIATION`**, D2 improvement. Register row **R754**: frame top bar, every IA route · the search box (shown
  ≥ 1101, hidden ≤ 1100) · the search in icon form wherever the full box does not fit beside the other items, from
  761 up · D2 · one collapse rule keeps search present and the bar one row at every width · none (final) · IA-1c.
- **Why.** The owner's standing brief asks for controls that read chosen; one ordered collapse is chosen, four bands
  are not. Search collapses first because its icon is universally read and its label is the longest; the inbox label
  next, because its count stays; the avatar last, as on the phone.

### D-IA.38 A drill-down page keeps its breadcrumb at every size (answers M3 and Q2: option a)

- **Class.** The reviewed `ux.css` rules hide `.canvas .breadcrumbs` at ≤ 600 and at ≥ 1024 with height ≤ 820, written
  for hub routes that have the rail item and tabs as their way up. A drill-down page (no tab, no lit rail item) has
  only its crumbs, so hiding them strands it. Today that is `decision`; IA-2's `record` and `asset` shapes are the same.
- **Ruling.** `iaFrame` sets `data-ia-crumbs="keep"` on `.canvas` when `route.shape` is `decision`, `record` or `asset`.
  `ia.css`: `.ia-frame .canvas[data-ia-crumbs="keep"] .breadcrumbs{display:flex}` (the base display), and at ≤ 600
  `margin-bottom: var(--s1)` (the reviewed short-height spacing). The reviewed `ux.css` rules and `uxDecisionSlots`
  are unchanged; the meta line's Site name stays text (option b would add a second link to the same place).
- **Gates.**
  - `shape_check.cjs`, every `decision/*` route of the three operators in its three states: the crumbs are exactly
    "Decisions" as text, then a link `#/site/<d.site>` reading `SK[d.site].name`, then the subject as text, and
    `.canvas` carries `data-ia-crumbs="keep"`.
  - `ia_shots.cjs`, the decision set (15 × 1440, 1280×720, 390 × light, dark) and the D-IA.37 sweep's decision routes:
    the Site crumb link has `getClientRects().length > 0`, a computed `display` and `visibility` that show it, and its box
    lies inside the viewport width.
  - G1 is unchanged: it measures from the Portfolio; the way back is a page property, checked above.
- **Plants that must fail.** `SHAPE_PLANT=sitecrumb` (the reviewer's plant C): the route's crumbs return the Site as
  text. `SHOTS_PLANT=crumbs`: the keep rule deleted from the sheet in the page (1280×720 and 390 fail).
- **Count.** Q2 stays counted (2). Template defect, extending D-IA.31's: spec §7's reused-code list must, from IA-2,
  also name each reviewed CSS rule that hides or moves an element the spec makes load-bearing (here the crumb).
- **Why.** Wayfinding must not depend on viewport height; 1280×720 is the common laptop. Keeping the crumbs is the
  existing control in its existing place, and the shape rule covers IA-2's drill-downs before they are built.

### D-IA.39 The act log and the decision's Site crumb are gated (answers L1)

- **Site crumb:** D-IA.38's `shape_check` item and `SHAPE_PLANT=sitecrumb`.
- **Act log (`count_check.cjs`, its after-act state, every operator).** After the act, "Since you last looked" in the
  inbox holds exactly one row with `data-ia-row="log:0"`, its href `#/decision/<the chosen id>`; the For-you and
  In-your-portfolio sets lose that id (as today). After Undo, no `log:` row names that id and the sets are restored.
- **Plant that must fail.** `COUNT_PLANT=nolog` (the reviewer's plant B): in the page, `uxActDo` is wrapped so that
  after the original runs, `uxMock().log.shift()` removes the entry it wrote.
- **Why.** P7's 25 assertions lived in scratch; the act log is D-IA.24's record of what the user did, and an ungated
  record decays silently.

### D-IA.40 A route about one Site's object is scoped to that Site (answers L2)

- **Class.** `iaCtx` defaults the scope to the Site only when the route has `:site`; a decision belongs to one Site
  but reads "All sites". IA-2's records and assets belong to one Site the same way.
- **Ruling (`ia-routes.js`).** New `function iaParamSite(params)` returns `params.site`, else the Site of
  `decById(params.dec)` when `params.dec`, else `null` (IA-2 adds its object parameters here). `iaCtx` defaults to
  `site:${iaParamSite(params)}` when that is non-null, else `all`. An explicit `?scope=` still wins and D-IA.35's
  validation is unchanged. On a decision the switch reads `<operator> · <Site name>` and lights that Site's entry;
  its entries are built as on the Site page (spec §2.3), unchanged.
- **Gate (`shape_check.cjs`).** On every `site/*` and `decision/*` route of the three operators: the scope summary text
  starts with `${OPS[op].name} · ${SK[site].name}`, and the lit entry is that Site.
- **Plant that must fail.** `SHAPE_PLANT=decscope`: `iaParamSite = p => p.site || null`.
- **Why.** The scope names what the page is about; the Site page and its decisions must agree. D-IA.37's sweep
  covers the longer label this puts in the bar.

### Owner questions (W3; defaults applied)

- **OQ-IA.4 The top bar collapses search to its icon where it does not fit; a decision always shows its way to its
  Site.** **Default:** as D-IA.37 and D-IA.38 rule; the owner sees both at the G2 stop. The alternatives (the bar
  wrapping to two rows between 761 and 1199; crumbs hidden on short laptop screens) read patched and strand a decision.

## IA-1c fix-round answer

Answers the packet's "Known deviation: D-IA.37's own stop condition is hit" (`packet-IA-1c.md`, head `ae29ce0b4`):
at level 3 the bar still runs past the window at 761, 800 and 900 (inbox and theme off screen at 761). Measured, not
tuned: the period chip alone is about 298 px, the scope switch about 200 px, beside a 174 to 204 px rail. Module paths
as above. Brief: `owner/owner-ui-standing-brief-2026-11-20.md` (right control per content, one interaction grammar,
simplicity by design).

### D-IA.41 The top bar's collapse ends in a form that always fits: the period's short form, then the two-row bar (amends D-IA.37)

- **Class.** D-IA.37's order ends at a level that only fits when the content is short enough, so any long label
  (a Site name in the scope switch, D-IA.40; the period sentence) overflows with nothing left to give. A collapse
  order is only a rule if its last level fits by construction. The phone already has that form (two rows, reviewed);
  the narrow desktop must end in the same form, not in a third one.
- **Ruling: two more levels, same order, same measure.** `data-fit` gains `4` and `5`:
  - `0` to `3` as D-IA.37 rules (search icon, then inbox label, then avatar).
  - `4`: also the period in short form: the clock icon and "October 2026"; the sentence " · Figures as of …" is
    visually hidden with the clip pattern the inbox label uses. The menu still opens from the same summary.
  - `5` (final): also the bar in two rows, the reviewed phone arrangement (`ia.css` lines 20 and 48: `.right`
    `display:contents`, the inbox `margin-left:auto`, the period `order:1`). The scope switch may shrink here and
    its label wraps between words: `.ia-frame .topbar[data-fit="5"] .ux-scope-sw{flex:0 1 auto;min-width:0}` and its
    `summary{white-space:normal;overflow-wrap:normal;word-break:normal}`. Height as the phone's: `height:auto;
    min-height:54px`; padding stays the width's own.
- **The period's short form needs a split, not new copy.** `ia-shapes.js` gets `function iaPeriodChip(op)`, the
  template of `periodChip` (`loop-core.js`, unchanged) with one change: the text after "October 2026" sits in
  `<span class="ia-period-asof"> · ${snapText(op)}</span>`. Its text content is byte-identical (render_text unchanged);
  the `snap-pending` span is emitted exactly as `periodChip` emits it. The frame calls
  `uxPeriodMenuHtml(ctx.op, iaPeriodHtml(ctx.op))` through `function iaPeriodHtml(op)` (a declaration, so a plant can
  reassign it): `uxPeriodMenuHtml(op, iaPeriodChip(op))` with the open menu's current item `<small>current period</small>`
  replaced by `<small>current period · ${snapText(op)}</small>`, at every level (one menu form, not a state-dependent
  one). That join of two existing strings is the only text change; no new words. `uxPeriodMenuHtml` stays unchanged.
  So the figures' time is on screen in the chip wherever it fits, and one click away (in the period's own menu,
  where a period is chosen) where it does not: the right control for it.
- **The measure (`iaFitTopbar`).** At `innerWidth >= 761`: set `0`, step while it does not fit, through `4`; if `4`
  does not fit, set `5` and stop (no test: `5` is the final form). Fits stays `scrollWidth <= clientWidth + 1` with
  nowrap and `flex:none` for `0` to `4`. Below 761 it sets `data-fit="5"` (no measure): the phone is the final form,
  so phone and narrow desktop are one form keyed one way. The `[data-fit="5"]` rules are written as second selectors
  on the existing `@media (max-width:760px)` IA rules, not copies.
- **Search is never hidden.** Inside `.ia-frame`, the search shows in icon form at every width (`data-fit >= 1`
  rules), superseding the reviewed `ux.css` hide at ≤ 600 for IA routes: `.ia-frame .topbar[data-fit="5"] .searchbox
  {display:flex}`. The avatar stays hidden at `3` and up (it is identity, not a control). The reviewed rules stay
  for legacy screens.
- **Rejected: the narrower rail** (option b). It moves a second element's band (the rail is full at 761 to 1023 and
  icons at 1024 to 1279), changes every page's content width, and still guarantees nothing for a long Site name.
  Recorded for IA-2 as a separate question (the rail's icon form below 1024), not taken here.
- **Stop condition.** Only a single unbreakable word wider than the window can now overflow; if the sweep finds one,
  the round stops and asks. No width, gap or label is tuned to pass.
- **`MOCK DEVIATION`**, D2 improvement, two register rows (builder adds them to `.agent/mock-departure-register.md`):
  **R755** frame top bar, every IA route · the period chip with its full sentence at every width · the period in
  short form (icon and month) where the bar does not fit at level 3; the sentence stated in the period menu's current
  item at every width · D2 · the collapse ends in a form that fits; the time stays one click away · none (final) · IA-1c.
  **R756** frame top bar, every IA route · one row from 761 (D-IA.37); search hidden ≤ 600 · two rows wherever level 4
  does not fit, the phone's arrangement; search in icon form at every width · D2 · one final form for phone and narrow
  desktop; every control reachable 390 to 1920 · none (final) · IA-1c.
- **Gates (`ia_shots.cjs`, the D-IA.37 sweep, widened).** Widths 390, 600, 601, 760 added to the fourteen; same routes
  (portfolio, plan, x-unknown, each operator's longest-Site decision), light. Clauses, each with its own BAD reason:
  - **past** (every width): no top-bar item's box left of 0 or right of `innerWidth`; no document horizontal scroll.
  - **reach** (every width): each of the scope summary, `.searchbox`, the period summary, `.ia-inbox` and
    `.theme-toggle` has a box at least 16 px wide, lies wholly inside the viewport, and `elementFromPoint` at its
    centre is it or inside it. BAD reason names the control ("inbox not reachable").
  - **trunc** (every width, from D-IA.37, now also below 761): no visible `.ia-search-t`, scope summary, period summary
    or `.ia-inbox-label` with `scrollWidth > clientWidth + 1`.
  - **midword** (every width): the scope summary's computed `overflow-wrap` and `word-break` are `normal` and its
    `text-overflow` is not `ellipsis`.
  - **rows**: `data-fit` 0 to 4 means `oneLine`; `5` means the item centres fall in exactly two bands; below 761
    `data-fit` is `5`.
  - **order**: per operator and route, `data-fit` never rises as the width rises.
  - **full**: `data-fit="0"` at 1440 on `#/portfolio` for every operator (kept) and at 1920 on every swept route.
  - **asof** (1440 and 390, every operator, `#/portfolio`): open the period menu; its `[aria-current="true"]` item's
    text contains `snapText(op)`.
- **Plants that must fail** (each run once; first failing line into the packet's plant table):
  - `SHOTS_PLANT=fit` and `SHOTS_PLANT=truncate`: kept as D-IA.37 rules them.
  - `SHOTS_PLANT=wrap`: the `[data-fit="5"]` selectors deleted from the sheet in the page, plus
    `.ia-frame .topbar .ux-scope-sw>summary{padding-right:240px}` (a stand-in for a long Site name) → **past** at 761.
  - `SHOTS_PLANT=longname` is the control and **must pass**: the same padding alone, every width 390 to 1920.
  - `SHOTS_PLANT=phonesearch`: `@media (max-width:600px){.ia-frame .topbar .searchbox{display:none!important}}` →
    **reach** at 390 ("search not reachable").
  - `SHOTS_PLANT=midword`: the padding plus `.ia-frame .topbar .ux-scope-sw>summary{overflow-wrap:anywhere}` →
    **midword** at 390.
  - `SHOTS_PLANT=asof`: `iaPeriodHtml = op => uxPeriodMenuHtml(op, iaPeriodChip(op))` and re-render → **asof**.
- **Why.** The brief asks for simplicity by design and one grammar: a collapse that ends in the phone's own form is
  one rule from 390 to 1920, and every control is reachable because the last form fits by construction rather than by
  measurement luck. The period's sentence is status, not the control: the control (the month) stays in the bar, the
  status goes where the period is chosen.

### D-IA.42 The builder's two changes beyond D-IA.37 and D-IA.36: one confirmed, one confirmed with a correction

- **`iaFitTopbar` runs before the after-render guard observes: confirmed.** D-IA.37 said "at the end of `iaRender`";
  the fit is part of the render, and `ia-shapes.js` calls it before `__iaInserted`. The guard's allow-list is not
  widened for `data-fit`. A re-fit on `resize` or `document.fonts.ready` is a response to an event, outside the
  guard's no-event window, and writes only `data-fit` on `.topbar`. **Plant that must fail:** `AR_PLANT=fitlate` in
  `after_render_check.cjs`: `iaBind` wrapped to call `iaFitTopbar()` again in a `setTimeout(…, 0)` after insertion →
  "attributes data-fit on header". It joins `ia_gates.cjs`'s IA-1c list.
- **The scroll margin from a measured `--ia-sticky-h`: confirmed, corrected in two places.** Measuring the sticky bar
  by showing it for one synchronous read (no paint) is the only way to get a rendered size for an element shown only
  after the scroll; the `is-on` toggle is the class the guard already allows. Corrections: (1) the variable is the
  shown bar's **bottom edge** in the viewport (`Math.ceil(getBoundingClientRect().bottom)`), not its height, so a bar
  that starts below the top bar (`--ux-sticky-top`, now taller at level 5) is covered; (2) the `+ 8` leaves the
  script: the gap is the token, `.ux-ocards{scroll-margin-top:calc(var(--ia-sticky-h,0px) + var(--s2))}`. On a
  phone (≤ 600, the bar at the bottom) the variable is `0px` as now. **Plant that must fail:** `UXI_PLANT=stickyh`:
  `iaInPage` sets `--ia-sticky-h` to `0px` → the uxi "in-page link" assertion that the section's `h2` top is at or
  below the sticky bar's bottom fails at 1440.
- **Why.** Both follow the measured-not-typed rule (r3 L4, D-IA.17): a fit that ran after insertion would be a
  post-render rewrite, and a margin from a height alone is a typed assumption about where the bar starts.

### Owner questions (W3; defaults applied)

- **OQ-IA.5 Where the top bar cannot fit on one row it becomes two rows, as on the phone; the period shows its month
  and states the figures' time in its menu.** **Default:** as D-IA.41 rules; the owner sees 800 and 390 at the G2
  stop. Alternatives rejected: a narrower rail at 761 to 1023 (a second band patch, no guarantee); truncating the
  scope or period label (the brief: never truncate a label).

## IA-2a design (after the G2 stop)

Architect (Claude), 2026-11-21. The owner saw G2 ("UI looks ok for now", `owner/owner-snapshot-guard-and-g2-2026-11-21.md`)
and asked to start IA-2a while the UI lane waits for 5c (`owner/owner-start-ia2a-2026-11-21.md`). Read on `main` at
`93fda5edc`. Folded into `spec.md` §5.1 (rev 4). Brief: `owner/owner-ui-standing-brief-2026-11-20.md`.

### D-IA.43 The plan is one object page with four tab routes; its header is the same on every tab

- **Class.** The interim (D-IA.20) is one long page in which the plan's header, its working list, what it leaves out,
  how it will be judged and what happened to it are all siblings, and the approval panel repeats the band. That is the
  owner's "very elaborate text, links, grids" on a page whose job is one act (approve). A tab-per-concern split fixes
  it only if the header that carries the act is identical everywhere, so the act is never a tab away.
- **Ruling.**
  - Routes `plan` (Items), `plan/left-out`, `plan/review`, `plan/history`; tab group `Plan` (spec §5.1.1). Tabs are
    routes, as on the Portfolio hub: one grammar for views of one object (D-IA.9). Back restores the tab.
  - The H1 and subtitle are the plan's on every tab (the object's name; the tab is the view). Because tabbed routes
    then share an H1, a route may set `docTitle`; the three new tabs set "{Tab} · {title}" so each document title
    differs (WCAG 2.4.2). This is the class rule for every later tabbed object (Site tabs in IA-2c, Action and Asset
    pages): `shape_check` item 10 holds it for every tab group.
  - L1 (stepper, band, release line, version notice, thresholds opener) is identical on the four tabs, and the sticky
    repeats the primary on every tab. `plan_shape_check` compares L1 across tabs, including after a non-default case.
  - The placement is spec §5.1.2's table. What the plan holds (Items), what it does not (Left out: options left out,
    values listed beside, Actions returned to their creator), how it will be judged (Review), what happened to it
    (History).
  - "Try another case" sits in the side panel of Items and Left out only: those are the tabs whose content the case
    changes. Review (the proposed version's items against observed) and History (the record) do not depend on it and
    take the full width. The L1 always shows the case on screen, because that is what Approve acts on (the reviewed
    rule, review r4 M4), and its version notice says so when the case is not the proposed one.
  - The approval panel leaves the page: its state block and meters repeat the band, its Opened and Proposed facts are
    History's rows, its release line and version notice move into L1, its thresholds into a drawer, and its recording
    note is what the Approve dialog already says ("Recorded under"). **R757** D2.
- **Why.** Right control per content: a view is a tab, a rule read beside its parent is a drawer, the act stays where
  the eye starts. Simplicity by removing repeats, not by hiding: every fragment of the reviewed page is placed exactly
  once (`plan_shape_check`'s placement and "no `.approval`" assertions).

### D-IA.44 The plan's stepper: four steps, from the one state source

- **Ruling.** `iaPlanSteps(state)` maps `DRAFT` 0, `PROPOSED` 1, `REVISED` 1 (a revised version is proposed again),
  `APPROVED` 2, `CLOSED` 3, and throws on any other state; the words are `STATE_WORD`'s. `iaPlanStepper(op)` reads
  `uxPlanState(op).state` only and uses the `uxDecStatus` markup and its CSS (`.ux-dsteps`), with `aria-label` "Where
  this plan is". A plan sent back is a Draft again: nothing is marked done; the chip says "Draft, sent back by …" and
  History holds the send-back. "Closed" is never current while the period is open (no data or act closes a plan in
  the demonstration); it is shown as the next step after Approved, never invented.
- **One state source (review r4 M1, D-IA.24).** Every IA-2a builder reads state through `uxPlanState(op)` and the
  one-source helpers named in the `loop-portfolio.js` comment (`planApprovedIds`, `planReleasedItem`, `releaseShown`,
  and the functions that call them). `PSTATE()` only for what no act changes: `period`, `opened`, `proposed` and the
  proposed `version`. `uxMock().plan` is never read directly. Reviewer sweep: grep the diff for `PSTATE()` and
  `uxMock()`.
- **Gate.** `count_check` plan block (spec §5.1.8): stepper, chips, inbox row, badge and History agree in four
  states, from the check's own reading of `sessionStorage['l4-mock']` and the manifest. Plants `COUNT_PLANT=planstep`
  (stepper reads `PSTATE()`: after Approve it still says Proposed) and `planhist`.

### D-IA.45 The meters: the budget tile's bar, and one crew tile with its bar per month

- **Class.** The band shows the crew figure without a meter, and the approval panel shows meters in a second
  component (`meter()`), so one plan carries two meter forms and the crew limit's state is visible only lower down.
- **Ruling.** L1 has one meter form, `uxMeterBar` inside a `uxKpi` tile: the reviewed spend tile (its bar unchanged),
  then `iaCrewTiles` (one tile per month with a stated crew limit, spec §5.1.3), then the value tile. The bar's
  `is-near` and `is-full` states are the reviewed ones (Lakeside's November reads 3 of 3, full). The period has at most
  two months, so L1 holds at most 4 tiles (shape_check item 1). A month with no stated limit has no tile, as
  `crewByMonth` filters it today; with no month at all the band's own crew tile stays.
- **Gate.** `plan_switch_check` (retargeted; its intent unchanged): budget and crew figures per switch case against
  the evaluator's switch cases and the manifest, computed by the check's own code. Plant `PSW_PLANT=crewtile`.

### D-IA.46 What stays byte-identical: four splits, proven in three plan states

- **Ruling.** The splits of spec §5.1.5 (`planParts` finer keys, `approvalParts`, `uxPlanBandParts`,
  `whatChangedParts`) return today's strings; their joins are the reviewed functions, unchanged in output. The list of
  untouched functions in §5.1.5 has no line in the diff. The one non-split change to reviewed code is `screens.js`
  `render()` writing `s.docTitle || s.title` (D-IA.43); for every route without `docTitle` the title is unchanged.
- **Proof.** `parts_identity.cjs` adds, per operator: `planScreen()` × every switch case × the plan states {none;
  approved: `uxMockSet({ plan: { [op]: { state: 'APPROVED', by: <executive>, at: 'now', version: 1, ids: planCaseIds(op) } } })`;
  sent back: `{ state: 'DRAFT', by: <executive>, at: 'now', reason: 'Too much spend', giveWay: <first item's label> }`}
  × both previews; `whatChangedScreen()` × the three states × both previews. The plan states matter because
  `approvalParts`, `uxPlanBandParts` and `whatChangedParts` branch on state.
- **Why.** The reviewed plan page passed four review rounds; moving its parts must not re-open them.

### D-IA.47 Review and History: reviewed content and the act log, nothing claimed

- **Review** is `whatChangedParts(op).review` as reviewed: each version-1 item, its predicted change, owner, state,
  Action owners, "Observed change: Not yet" and "Review: Not yet", with its note that the review runs when the period
  ends. **R759** D1: an honest gap inside the mock's structure; "review against observed" fills only from Results'
  verdicts (IA-2d).
- **History** (spec §5.1.4) lists, newest first, this tab's approvals and send-backs from the act log (D-IA.24, the
  same entries and row form as the inbox's "Since you last looked"), then the proposal and the opening from the
  manifest. Its note says the acts are shown in this demonstration only (the act log is per browser tab). The
  proposal figure's "L4 versions" drawer is not built: the list is the versions. **R760** D5, resolving IA-2d (entry
  addresses).
- **Caps (D-IA.34's scope).** No plan list is capped by position: an item, an option left out, a returned Action or a
  review row is never hidden, because a plan is a commitment and its spend must add up on screen. The one `ul.list` that
  can exceed 7 is History, capped by `uxCapLists` with "Show all {n}"; it holds no waiting item, so D-IA.34's ranking has
  nothing to keep. `plan_shape_check` asserts no `[data-ux-over]` on Items, Left out and Review (plant `cap`).

### D-IA.48 Gates, plants and the clean stop

- **Gates.** Spec §5.1.8's table, each new or changed assertion shown failing on its plant first (§6). Three rules
  the builder would otherwise have to decide:
  - **Dormant checks.** Unit 2's assertions on plan tabs run only when `IA_LANDED` has IA-2a and print
    `IA-2a not landed; dormant` otherwise, as G1 did before its origin landed (spec §2.5). Their plants run from the flip.
  - **A short tab and the sticky bar.** uxi requires the sticky bar to show once the band scrolls under the top bar.
    On a tab too short to scroll the band away, the requirement is that the band's Approve stays in the viewport at the
    bottom scroll position; the assertion reads `(sticky on and its act present) or (band Approve in view at the
    bottom)`, and both halves are measured, never assumed (a page that can scroll the band away must show the bar).
  - **Hosts.** `PSW_PLANT=release` and `leftout` run where the case differs from the proposal and returns Actions:
    Lakeside 6500/No (2 returned), Harvest No (1), Metro No (1).
- **Size.** 3 units, 5 commits (spec §5.1.9). Under the 6-unit cap; one discovery review at the end.
- **The clean stop.** Every commit boundary before the flip (3b) leaves every screen as it is on `main` and every gate
  green. On 3A7's merge the builder finishes the commit in hand, runs fast check-all, pushes and writes the stop line in
  the packet; the lane goes to 5c. Recommended stop: the end of unit 2. 5c changes no `vNEXT/` file.
- **Why.** The owner's priority rule (5c first the moment it can start) needs a stop that costs nothing: no
  half-visible shape, no gate red, no re-review on resume.

### Owner questions (W3; defaults applied)

- **OQ-IA.6 The plan's Approve stays in the band under the meters, not in the title row.** **Default:** as R758 (it is
  inside the first screen at 1440 and 1280, and the sticky bar repeats it). The alternative, page actions in the title
  row, is a frame change for every shape; it is worth a look at the IA-2 walkthrough, with the decision page, which has
  the same pattern.
- **OQ-IA.7 "Try another case" only on the tabs it changes (Items, Left out).** **Default:** as D-IA.43. The alternative
  is the switches on all four tabs (one fixed side panel), at the cost of a what-if control beside the record and the
  review it does not change.
