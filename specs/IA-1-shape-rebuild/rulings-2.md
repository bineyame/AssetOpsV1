# IA-1 rulings, continued

Architect (Claude), 2026-11-20. `rulings.md` is at the 15k-token cap (RULES §9); later answers are here. Index lines are in
`.ai/decisions/index-rulings-10.md`.

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
