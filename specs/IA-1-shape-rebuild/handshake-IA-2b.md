# IA-2b handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec-IA-2b.md`, `reviewer-guide-IA-2b.md` and `rulings-5.md` (D-IA.61 to D-IA.66), and the
Implementer, after a pre-flight of the spec against IA-2a's code, write their questions here in one batch. Numbered R1... and
I1...; each cites the spec section, says what is unclear and the answer expected, and is marked **(done)** when its answer
changes what counts as done. The Architect answers each once (in `rulings-5.md`, "Handshake answers") and folds the answers
into the spec and guide. Coding starts when no question is open.

Checked against: `task/IA-2a-plan` (read with `git show`; `ia-routes.js`, `ia-shapes.js`, `loop-ux.js`, `loop-portfolio.js`,
`tools/qty_check.cjs`, `ia_gates.cjs`, `click_depth_check.cjs`, `ia_shots.cjs`), rulings-4 on `task/IA-2a-review2-answers`,
and the owner's standing UI brief. Nothing was run. Live counts below are from the fixtures' `sites:` lines, not a run.

## Reviewer questions

**R1 (done). Every list is drawn with all its controls even where the content is three rows (§3.2 Tools, §4; D-IA.62; owner brief "right control per content", "simplicity by design").**
Each operator has exactly 3 Sites (`OPS[op].sites`), each operator is one vertical, and the tools rule is "no control when
fewer than 3 items in scope" (`uxQueue`'s). So the Sites list draws a Target select, a Sort select, a search box and a Search
button over 3 rows; the scope menu's group entry equals "All sites"; and `def.group` and group `tbody`s can never occur live
(only block A's synthetic store reaches them). The same may hold for Findings and Actions per operator (the packet should
count them). The brief's test is whether each control earns its place at the sizes the product shows. Expected: a per-list
threshold (a control only where the list has more rows than fit, or more than N; the Sites list under 10 draws no tools), or
an explicit ruling that one component draws one toolbar and the demo's size is the demo's. If a threshold, `list_shape_check`
B must assert tools present/absent by list size, and the shots matrix covers both.

**R2 (done). "Gap to target" tile: what the sum is, whether it can be added, and what the hidden rows do to the reconciliation (§3.4, §4 tiles; D-IA.54, D-IA.59).**
(a) The tile is "the sum of shown-and-hidden rows' gaps" with each row's cell `data-qty` part of it. A capped list (more than
10 Sites) renders only 10 gap cells, so on screen parts do not sum to the total; `qty_check` sums what is rendered. Expected:
say which it is (hidden rows' parts rendered `hidden`, as D-IA.59 counts hidden text, or the total reconciled only when
uncapped), and add the synthetic case to `qty_check`. (b) Signed gaps net overs against unders (a Site 4,000 under and one
4,000 over give a tile of 0). The spec refuses an "at stake" sum for decisions because stakes cannot honestly be added;
whether net gap can be is a claim about the Sites, not the code. Expected: either the tile equals a figure the Overview already
states (the guide's Q2 says "at scope all it equals the Overview's gap tile"; the spec does not say so; it should, as a
cross-screen D-IA.54 assertion) or the tile is dropped for a count ("Below target"), as for the other lists. (c) The fallback
"otherwise every row gap renders with cents" changes the row's gap on the list but not on the Site hub, which still shows
whole dollars for the same figure; D-IA.59 is per screen, so allowed, but the packet should name it.

**R3 (done). Sorting Decisions by "At stake" re-introduces the sum D2 refuses (§4 sorts, D2; D-IA.63 "no money tile").**
`uxStakeParts(id).num` is 0 for "Not valued" and for no-figure rows, and the values are on different bases and some are
alternatives; "descending" therefore ranks unlike things and files "Not valued" in the middle of a signed range. D2's own
reason (stakes are not commensurable) also removes the honest basis for ordering by them. Expected: drop that sort, or sort
only the valued rows (Not valued and "Not available yet" last, stated as such in the sort's label, e.g. "Largest stake first
(valued only)"), with a plant (a Not valued decision sorted into the middle) in block A/B.

**R4 (done). Controls that filter without being visible, and rows that open nothing (§3.2, §4 Actions "Plan version", Findings row target; D-IA.9 "one target per row", "nothing unbuilt is reachable").**
(a) "Plan version" has one option, and a select is drawn only for facets with at least 2 options, so no control shows the
version filter; yet `?version={n}` (the plan's link, G1) filters the list. A person sees "Actions 5" and no word that this is
version 1's; "Clear filters" appears with no filter named. Expected: the active filter is always named (a chip like the scope's,
"Version 1 · All versions"), or the facet is not a filter but part of the title. (b) "An item with no live target renders its
title as text": a Finding with no decision (spec §4: "none when no decision") is a row that opens nothing, against the
Outcome's "rows that each open one thing". Expected: say how many Findings per operator have no decision (if zero, delete the
branch and add a check; if not, how the row signals it, since text in a first cell that is a link everywhere else breaks the
grammar). (c) Two Findings on one decision, and each Action of one item, give several rows with one target: say so in the
walkthrough text so the owner is not surprised.

**R5 (done). Counts are not asserted by the check the spec relies on (§3.4, §8 `qty_check` row; D-IA.54).**
`qty_check.cjs` at IA-2a's head reads `moneys(e.textContent)`: a `data-qty` whose text has no `$` contributes nothing, so
"Released + Waiting (+ Returned) = Actions", "Show all {n}" = tile 1 and "View all {n}" = the target list's tile would pass
whatever they said. The "format assertion" (D-IA.59) is not in `qty_check` at that head either (`grep -i "decimal\|format"`
finds none), and rulings-4 puts it in IA-2e. Expected: the spec states that IA-2b1's unit 1 adds both to `qty_check` (a count
mode: integers read from the element, parts sum, equal keys equal across routes; the format mode for money) with plants
(`QTY_PLANT=counts`: Returned dropped from the parts; the existing `sitegap`, `listcents`), or states they are `list_shape_check`
B's job and removes them from the `qty_check` row. Either way the plants must fail on a live number, not on a synthetic one.

**R6 (done). The shots matrix names the default view only (§8 `ia_shots` row; D-IA.58 "every state and non-default case").**
The row covers 4 lists × 3 operators × 3 sizes × 2 themes, no sideways scroll, tile fill, and the select-keeps-place check at
390. D-IA.58's standing rule is every state and non-default case: Actions after Approve and after Send back and in Lakeside
6500/No (Returned appears), each facet value, a search with no result (the empty state with tools), `show=all` (a long list at
390), a scoped view with the chip, a Site with no target (the "Not available yet" cells), and the tools absent (under 3).
Block B of `list_shape_check` covers those as markup, not as layout (a stacked table at 390 with `show=all`, a chip and a
long select label wrapping inside the page). Expected: the matrix adds those non-defaults at 390 and one wide size, with a
count printed per case class (as the "81 switches" count was), and plants for the two layout cases not yet covered
(`SHOTS_PLANT=listwrap`: the tools row `nowrap`; `emptytools`: the empty state without its tools).

**R7. Can every plant fail? Two plants whose failure may be vacuous (§8).** (a) `LIST_PLANT=restore` (facet ignored on
first render) is caught only if block B boots the same address fresh and compares to the controlled path; if the comparison is
fresh vs fresh it passes. Expected: say the comparison is fresh boot vs the in-page change. (b) `SHOTS_PLANT=listkeep` (no
restore) fails only if the restore is observable: see I1, where the shipped `hashchange` handler may undo the restore in
production, so the plant would pass the real page and fail only the plant. (c) `LIST_PLANT=own` (findings drop the last store
item) fails only if the check's own computation of findings reads `HC.findings` independently; the guide's grep covers
`iaListModel`/`uxFindingRows` but not the facet maps (`LENS`, `RELEASE_WORD`), which the spec lets the check reuse.
Expected: the check carries its own word tables or asserts them against a literal list.

**R8. The IA-2b1 / IA-2b2 split and the stop (§2, D-IA.61).** The split is on the right seam (IA-2b1 reads IA-2a only through
the one-source helpers). One gap: IA-2b1 lands the Actions list and its `version` facet, whose option reads
`uxPlanState(op).version` and the approved-ids rule, and the Decisions list's `state` words (`uxStateCount`), all of which the
owner's walkthrough can change (state or release words). The spec says that flows in "by construction"; it does so only if the
facets and the tiles read those helpers at render and the check computes from stores, not from the words. Expected: confirm
the facet options are computed from the helper at render (not a `RELEASE_WORD` copy), and that the stop line's re-rule list
(§2) adds "the Actions list's State and Plan version facets" to the plan L1, tab grammar, release words and the hubs'
"Decide". Not (done): a one-line addition to §2.

## Implementer pre-flight

Checked: `task/IA-2a-plan` head (the mock's `ia-routes.js`, `ia-shapes.js`, the `tools/` named above) against spec §3 to §9.

**I1 (done). The scroll/focus keep is overwritten by the shipped `hashchange` handler (§3.3).**
`index.html`/`loop-core.js` registers `hashchange → stage.view…; render(); window.scrollTo(0,0)`. `iaBind(route)` runs inside
`render()` (via `iaInsert`), so the spec's `scrollTo(0, IA_LIST_KEEP.y)` in `iaBind` happens before the handler's
`scrollTo(0,0)` and loses. D-IA.58's tab switch sidesteps this in a later `hashchange` listener (`iaTabSwitch`) that runs after. 
Also, a `change`/`submit` that writes the same hash fires no `hashchange`, so `IA_LIST_KEEP` is never cleared and the next
unrelated render restores a stale position. Expected answer: the restore moves to a `hashchange` listener registered after
the router's (as `iaTabSwitch`), reads and clears `IA_LIST_KEEP` there, and the listener on `change`/`submit` clears it when
`iaListHref(...) === location.hash`; unit 2's plant and the 390 shot then fail on the real order. Done means the shot asserts
position with the router's handler present, not in isolation.

**I2 (done). The format assertion and the count mode do not exist in `qty_check` (§3.4, §8).** See R5. The implementer
reads `qty_check.cjs` as money-only with no decimals comparison; `QTY_PLANT=listcents` and `sitegap` have nothing to extend.
Expected: unit 1's card gains "qty_check: count mode and format mode", about 1 commit. Confirm the unit count stays at 5
(it is a size question: with R5, R6 and R2 added, about 5.5 units; if above 6 the cap forces a split of unit 3).

**I3 (done). `iaOutcomeRows` does not carry what the component needs (§3.1, §4 Sites, §5).**
`iaOutcomeRows` returns `gapHtml` as a `figS(...)` string, `gap` as a number and `resultHtml` etc., with no `data-qty`, no
row key (`key` is the Site), and a pre-built cell for each column; `iaOutcomeTable` caps with the in-place `uxCapNote`
button and `data-ux-over hidden` rows (hidden rows are in the DOM), the opposite of §3.2's link and absent rows. The fold must
change `iaOutcomeRows` (keep it, per §5) or wrap it; the figure's `fig()` and `figS()` wrappers carry node-explanation links
inside the cell, which collides with "every other cell holds text only" and "the row's only interactive element is that
link" (§3.2). Expected: say whether the gap and result figures keep their `fig`/`figS` explainers inside list cells (then
"one target" needs a carve-out for in-cell definitions, as the hubs' tiles have, and `list_shape_check` B's "exactly one
interactive element" must name it), or render as plain text in the list (then the Outcomes tab loses its explanations;
`outcomes_table_check` A to D change in meaning).

**I4 (done). The facet and key words the defs need are not single sources yet (§4).**
(a) `uxDecState` has keys `choose`, `none`, `approval` (with a `draft` flag), `released`, plus a "chosen in this demonstration"
variant; the State facet's four options (waiting, approval, draft, underway) need `of(item)` to read `draft`, and "underway"
to be `released`; `uxStateCount`'s rule is a string-building function, not a classifier, so a def would copy it. Expected:
extract one classifier in IA code (`iaDecStateKey(id)`), used by the facet, the tile and the check's independent computation.
(b) `actionState(op, a, inCase)` logs `console.error` when the release rule and the stated release differ and returns a pill
string, not a code: the facet's `of` must read `releaseOf`/`releaseShown`, not parse the pill's `data-release`; and the
"returned" state depends on `planCaseIds(op)`, which changes on Approve/Send back, so the Actions list must re-render on the
plan's state change (the plan's actions already do; the list is a second subscriber to check). (c) `uxFindingRows` returns
`site` as the stripped name, so `def.site` needs name to key (`OPS[op].sites.find(k => SK[k].name === site)`; Room A to C
Sites are stripped). Expected: confirm (a) to (c) and name the helpers added.

**I5. Alias values with a query (§5).** `iaLiveAlias` returns a path (`t`), and callers use it as a path; `iaCanon` appends the
href's query `h.slice(i)` after it. A query-carrying alias value (`findings?heading=optimize`) passes through `iaLanded(t)` with
the query in the path and fails to match any route, so every consumer (`iaLive`, `iaCanon`, `iaPaletteFilter`, `shape_check`
item 7, the crawl) has to split the value first. Also an alias key with params (`'site/:site/economics'`) returns a function;
the spec's rule (value's query, then the href's parameters "not already set") needs the same merge for function values.
Expected: one helper `iaAliasTarget(path)` returning `{ path, query }`, used by all callers, and a `SHAPE_PLANT=aliasq` that
breaks the helper, not one caller. Not (done): a build detail the plant already covers once the helper is single.

**I6. IA-2b1 dormancy and the OWN map (§8).** `ia_gates.cjs`'s `OWN` map lists the checks whose "dormant" output is BAD once
landed; the new checks (`list_shape_check`) and the new rows of existing ones must be added with `IA-2b1` and `IA-2b2` keys, and
`iaStart`/`IA_G1_SURFACES` read `IA_LANDED.has(...)` per unit (the rail items unlanded until `IA-2b1`, per `IA_RAIL`'s `unit`).
The spec says units 1 to 3 flip `IA-2b1` in the last commit; but `IA_RAIL`'s Decisions/Findings/Actions/Sites items are
currently `unit: 'IA-2b'` or similar (not read here; confirm), so the rail's unit names change with the spec's `IA-2b1`.
Expected: a one-line note in unit 3's card to rename the rail units, and `shape_check` item 11 (rail items name a route that is
landed or unavailable) in the dormancy list.

**I7. Cap per group, "Show all" and the address, as the model's first pitfalls (§3.1 items 5-6).** The spec's step 5 ranks
`keep` first then caps; step 6 caps "per group" in a grouped list: two rules for one cap, undefined when the keep set is split
across groups. And `show=all` is one parameter for all groups, so a grouped "Show all" link cannot expand one group. With 3
Sites per operator this never occurs live. Expected: state it explicitly (cap per group, `show=all` expands all) and keep the
synthetic plant `group`, or defer groups (R1) and delete step 6 until a store reaches it (the owner's brief prefers less).

## Answers

(Architect: answer each once here, under "Handshake answers (round 1)" in `rulings-5.md`; fold into `spec-IA-2b.md` and
`reviewer-guide-IA-2b.md`. A question marked **(done)** that is answered without changing the "done" list is a ruling not to
change it, stated as such.)

**Answered, round 1 (Architect, 2026-11-21):** in `rulings-5.md` under "Handshake answers (round 1)", folded into
`spec-IA-2b.md` rev 2 and `reviewer-guide-IA-2b.md` rev 2. No question is open.

| Q | Ruling | Changes "done"? |
|---|---|---|
| R1 | D-IA.67: the controls grow with the list (none under 3, Sort to 10, the full toolbar above), as in the mock's 3/30/300 figure; the scale case is proven by a fixture (block D, S8) | yes |
| R2 | D-IA.68: the gap tile stays, as the operator's own gap (`EQUAL` with `overview-gap`); hidden rows become a remainder part; the cents fallback is fixture-only | yes |
| R3 | D-IA.69: the stake sort is dropped; no list sorts or sums a figure that cannot be added | yes |
| R4 | D-IA.70: chips name every state that no control shows; 0 rows without a target, so the branch is deleted and the check fails on one; several rows to one target are stated | yes |
| R5, I2 | D-IA.71: `qty_check` gains its count and format modes now, as unit 2, with plants on live numbers | yes |
| R6 | D-IA.72: classes S1 to S9, counts per class, plants `listkeep`, `listwrap`, `emptytools` | yes |
| R7 | D-IA.73: fresh boot against the in-page path; S9 with the router present; B's literal tables | ruling only |
| R8 | D-IA.74: confirmed; the re-rule list grows | ruling only |
| I1 | D-IA.75: `iaListRestore` after the router's `hashchange`, keyed to its hash and cleared on every change | yes |
| I3 | D-IA.76: list cells hold text only; the explainers stay on the Site hub | yes |
| I4 | D-IA.77: `iaDecStateKey`, `iaActionStateKey`, `iaFindingSite` | yes |
| I5 | D-IA.78: `iaAliasTarget` | ruling only |
| I6 | D-IA.79: the rail units are renamed in unit 4(a); the `OWN` rows | ruling only |
| I7 | D-IA.80: one cap per list, groups as the display (amends D-IA.27's per-group cap) | yes |
| size | D-IA.81: from 5 units to 6 (about 10 commits); the split and the stop hold | — |
