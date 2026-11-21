# IA-1 and IA-2 rulings, continued (rulings-3.md is near the 15k cap)

## IA-2a review answers (round 1)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away row 44). Answers `review-IA-2a-r1.md` M1, M2, L1 to L4;
spec §5.1 rev 6. Brief: right control per content, one interaction grammar, honest numbers; W6 (the class, then the sweep).

### D-IA.54 Two figures for one quantity on one screen reconcile on that screen (M1)

- **Rule (every live IA route).** When a screen shows a total and a part of it (same quantity, object and period), the
  rest of the total is stated beside the part, with its reason, so the shown figures add up. Two totals of one quantity agree.
  The reviewed legacy pages stay byte-identical and are out of scope.
- **The plan's instance.** `iaPlanHead` gains, right after `p.ap.releases`, `iaPlanReleased(op)`: the items of
  `planCaseIds(op)` with `releaseOf(op,id).at` true; `''` when none. Markup:
  `<p class="ia-plan-released" data-qty="plan-spend" data-qty-role="part">Already released when {its Action was|their Actions were} created, within the release thresholds: {itemProse(op,id)} ({usd(releaseOf(op,id).spend)}), joined "; "}.</p>`.
  It shows in every state (in Draft too: it is true then). `planScreen` is unchanged; `ia.css` gains
  `.ia-plan-released{margin:var(--s2,8px) 0 0}`. Lakeside, Harvest and Metro each show one item: KOB-STOPSOC ($90), THIKA-EPC-STOPGAP ($100), KAS-OEM-STOPGAP ($90).
- **The check** `tools/qty_check.cjs` (jsdom, a row in `ia_gates`), every live route × 3 operators × the plan states
  (as proposed, approved, sent back) × default and the non-default cases of D-IA.50. Per screen it groups figures by key:
  IA-built markup declares `data-qty` / `data-qty-role` (`total`|`part`); reviewed markup is declared in the check's own
  `QTY` table by selector (row 1: `plan-spend`, total = the money in the band's first `.ux-kpi-v`, part = the money before
  " of one-off spend" in `.approval-releases`). Assert: parts sum to the total where the total and every part are shown;
  totals of one key are equal; a `QTY` row whose selector finds nothing on a route that row names fails (never dormant).
  In Draft the line has no money: the clause alone, ≤ the total. Plants: `QTY_PLANT=clause` (clause omitted; fails on all
  three operators), `QTY_PLANT=wait` (clause sums the waiting items instead; fails everywhere the line has money).
  `plan_shape_check` (D-IA.52 R9) counts `.ia-plan-released` once per plan route where the set is non-empty.
- **Sweep (W6).** The builder lists, in the packet, every live route that shows one quantity twice (route, the figures,
  reconciled or registered), including the Overview's plan tile. A pair found gets a `QTY` row and, if unreconciled, an
  IA-only clause of this form; a pair needing a change to reviewed bytes is a mid-build question, not a fix.
- **Copy** (§5.1.6): the clause above, exactly.

### D-IA.55 A tab switch shows its tab: the strip moves to the top when the tab's content would start below the fold (M2)

- **Rule (every tab group: Plan, Portfolio, Site).** L1 stays identical (D-IA.43). On a hash change whose old and new
  routes share a `tabGroup`, the frame, in a `requestAnimationFrame` after render (so after `screens.js`'s
  `scrollTo(0,0)`), finds the tab content's first box (the first descendant of the first `[data-level="L2"]` with a
  non-empty `getClientRects()`). If its top at scroll 0 is greater than `innerHeight − 48`, it scrolls (instant, not
  smooth) so the tab strip's top is at the viewport's top. Otherwise scroll stays 0, so 1440 × 900 and 1280 × 720 keep
  R14's Approve in view. Then, if focus is on `body`, the active tab takes focus (`preventScroll`). First load and the
  deep links are not switches: they open at the top. Width is not in the rule; the fold is.
- **Markup.** `iaTabsHtml` wraps its output in `<div data-ia-tabs>`; `ia.css` gains `[data-ia-tabs]{display:contents}`; the
  scroll target is that wrapper's first child. One listener in `ia-routes.js` (`iaTabSwitch(e.oldURL, e.newURL)`).
- **Rejected:** a compact L1 on phone tabs (a second header form, breaking "L1 identical"; two grammars).
- **Check** (`ia_shots`, heavy slot): every group with more than one landed tab (Portfolio; Plan; Site on one Site of
  each type) × 3 operators × 390 × 844, 1280 × 720, 1440 × 900: from the first tab click each other tab, then last to
  first, then Back once. After two frames: the content's first box has at least 48 px inside the viewport; the active
  tab is wholly in view; focus is on it after a click; on the plan routes at 1440 and 1280 `scrollY` is 0. Plants:
  `SHOTS_PLANT=tabnoscroll` (no listener; fails at 390 on Plan and Portfolio), `tabscrollall` (no fold test; fails the
  `scrollY` clause at 1440).

### D-IA.56 A tile row fills its row (L1)

Class: every `.heroes.ux-kpis` in the IA frame, not the plan's alone. `ia.css` gains
`@media (min-width:1280px){.ia-frame .heroes.ux-kpis:has(>:last-child:nth-child(3)){grid-template-columns:repeat(3,minmax(0,1fr))}.ia-frame .heroes.ux-kpis:has(>:last-child:nth-child(2)){grid-template-columns:repeat(2,minmax(0,1fr))}}`
and `@media (max-width:1279px){.ia-frame .heroes.ux-kpis>:last-child:nth-child(odd){grid-column:1/-1}}` (two tracks below
1280: an odd last tile spans the row). Check (`ia_shots`, every live route, the three widths): the last tile's right edge
is within 2 px of the row's content right edge. Plant `SHOTS_PLANT=tilefill` (rules removed; fails on Harvest at 1440
and 390). The packet lists every IA route whose row changed, with a shot.

### D-IA.57 The lows: hand_typed, the case link, the state index (L2 to L4)

- **L2: fix now.** The hit is in this diff, and the mock-up's rule is that dates come from the composer, not typed:
  `rightsM` uses `` `Rights measures by contract and period (as of ${fdate(AS_OF)})` `` (same rendered string;
  `parts_identity` must stay 282/282). The packet's "pre-existing on `main`" line is corrected. Class: the scanner does
  not read quoted literals inside templates. The builder runs a one-off count of typed dates inside templates in
  `vNEXT/` and reports it; extending `hand_typed_scan.py` is a backlog item (coordinator), not this round.
- **L3: ratified, amending D-IA.51.** "Change the case" points to `#sw-h` where the switches are on the page (Items,
  Left out) and to `#/plan` where they are not (Review, History): the link goes to the control, the rule D-IA.36 sets for
  in-page links. L1 is identical except that one `href`. `plan_shape_check` asserts the `href` per tab before it
  normalises it, so the normalising can hide nothing else. A packet line says so.
- **L4.** Keep both sides: `DS3` row 172 (main), `IA-2a` row 173 (renumbered 177 at the main merge; done on `task/IA-2a-review-answers`).

**Fix size.** One round, about 1 unit, 2 commits: (1) D-IA.54 clause, `qty_check` and its sweep; D-IA.57 L2 and L3;
(2) D-IA.55 listener and D-IA.56 rules with their `ia_shots` clauses and plants (heavy slot). A continuation builder on
Sonnet; a fresh Claude reviewer at verification depth. Merge still held for the owner's walkthrough.

## IA-2a review answers (round 2)

Architect (Claude), 2026-11-21, owner away (delegated; owner-away row 45). Answers `review-IA-2a-r2.md` M3, the figure-format
note, L5 to L7; spec §5.1 rev 7. Brief: one interaction grammar, honest numbers, deliberate hierarchy; W6 (the class, then the sweep).

### D-IA.58 A tab switch puts the tab's content on the screen, whatever L1's height: land the content, not the strip (M3; amends D-IA.55)

- **Why D-IA.55's rule fails.** "Strip to the top" assumes the content is one short L1 below the strip. L1 grows with state (case
  line, notice, a longer release line, the clause); in Lakeside 6500/No at 390 it is taller than the screen, so the content is 140 px
  below the fold with the strip at the top. No scroll target *at the strip* can work; the target must be the content.
- **Rule (every tab group, every width, every case and state).** L1 stays identical. The fold test is unchanged: if the content's
  first box (D-IA.55's definition) at scroll 0 starts above `innerHeight − 48`, scroll stays 0 (1440 and 1280 × 720 keep Approve in view).
  Otherwise the frame scrolls (instant) so the first box's top sits at `stickyBottom + var(--s2)`, where `stickyBottom` is the
  bottom edge the fixed context bar (`.ux-dsticky`) will have once scrolled, measured as `iaInPage` measures it (D-IA.36: one
  measure, reused; not a new constant). The strip is then above the screen, one swipe up; the active tab keeps focus
  (`preventScroll`), the sticky bar names the page. This replaces "scrolls so the tab strip's top is at the viewport's top"; the rest of
  D-IA.55 (markup, wrapper, focus, first load not a switch) stands.
- **Rejected: a sticky tab strip under 760 px** (the reviewer's suggestion). It stacks a second fixed layer under `.ux-dsticky`
  (two bars eat about 110 px of a 844 px phone), needs its own offset for in-page scrolls (D-IA.36) and every other fixed element,
  and adds a header form for one page type. Reconsider at the W1 UI pass if the owner finds the strip lost on a phone; the
  rule above does not depend on it. **Rejected:** compact L1 (D-IA.55); shortening Lakeside's L1 (it grows again with the next note).
- **Check (`ia_shots`, heavy slot), widened from the default case to every case and state.** The tab set runs every group with more
  than one landed tab × 3 operators × 390 × 844, 1280 × 720, 1440 × 900 × **the plan states (as proposed, approved, sent back) × the
  default and the non-default cases of D-IA.50** (Portfolio and Site have one state each). Per switch, after two frames: the content's
  first box has at least 48 px inside the viewport **and its top is not under the sticky bar**; the active tab is focused after a click;
  at 1440 and 1280 `scrollY` is 0 on the plan's default case in the as-proposed state. The packet's "81 switches" count is re-stated.
  Plants: `tabnoscroll` and `tabscrollall` stay and still fail; new `SHOTS_PLANT=tabstrip` (the D-IA.55 strip-to-top
  rule): fails at 390 in Lakeside 6500/No on all four tabs. Class sweep (W6): any scroll target in `ia-routes.js` that aims at a box
  other than the one the user needs to see; the builder lists them.
- **Fix size.** About 0.3 unit: one listener edit, the gate's case loop and one plant (below).

### D-IA.59 One rendered form per quantity on a screen and in its drawers and definitions (figure-format rule; "+$6,089" vs "Net +$6,088.50")

- **Rule (class: every money, count and percentage quantity on every live route).** A quantity has one precision per screen, shared by
  its total, its parts, its definition text and any drawer or collapsed detail on that screen. Money: whole dollars when every figure of
  the quantity is whole dollars; if any part has cents, cents appear on every figure of that quantity there, the total included
  (the tile reads "+$6,088.50"). Rounding parts to fit a rounded total is not allowed unless the rounded parts still sum to the
  rounded total, and then it is applied to all of them. The sign or label ("Net", "+") is not part of the form.
- **Enforcement.** `qty_check.cjs` gains a second assertion, **format**: for each `QTY` key on each screen, the rendered strings
  of every figure of the key (read from `textContent`, so collapsed and hidden definitions count) have the same number of decimals.
  Strings are compared, not values. A plant `QTY_PLANT=cents` (cents stripped from the tile) fails on every operator with such a part.
  IA-built markup declares `data-qty` from the start; reviewed markup is registered by selector.
- **Where it lands: not IA-2a.** The two figures are reviewed bytes on `main` (the tile's `def`, `planGroups`); changing them moves
  `parts_identity`'s baseline and is a reviewed-bytes change under D-IA.54. They sit in hidden content and are not a wrong number
  (they agree once rounded). **Unit: IA-2e**, in its reconciliation gate and final sweep, with the registration of the plan pair
  (`plan-gain`: tile, `planGroups` Net) and the sweep of every other quantity on a live route that shows more than one form. The
  owner may be told at the walkthrough if they open that definition.
- **For IA-2b (note for its spec).** The list component's figures (row sums, "View all" counts, the Outcomes table's totals against
  the hub tiles) follow this rule from the start, with `data-qty` on each, and its `qty_check` rows (format included) land in IA-2b.
  Only the reviewed-bytes registration waits for IA-2e.

### D-IA.60 The lows: QTY registration, the clause's type, the packet (L5 to L7)

- **L5: the registry is made true now.** `qty_check` `QTY` gains rows for the Overview gap (`overview-gap`: $852 = $827 + $25, its own
  key, per D-IA.54) and the Items sum (`plan-items`: the "in all" total against the item rows, a separate key; Harvest's "$620 in all"
  is the same key on Harvest). Each row fails if its selector finds nothing on a route it names (never dormant); plants
  `QTY_PLANT=gap` (the $25 removed) and `items` (one row dropped). The "+$6,089 / Net" pair waits for D-IA.59 (IA-2e). The packet's
  "registered in `qty_check`'s QTY table" sentence is corrected to what is there.
- **L6: hierarchy.** `.ia-plan-released` takes the release line's type (size, weight, colour tokens copied from
  `.approval-releases`), no copy change. `ia_shots` plan clause `releasedtype`: its computed font-size and colour equal the release
  line's at 390 and 1440; plant `SHOTS_PLANT=releasedtype` (rule removed) fails.
- **L7: the packet.** Three corrections: line 65's "pre-existing on `main`" (fixed in code, count 0); the one-off count of typed
  dates inside templates in `vNEXT/` that D-IA.57 asked for; the D-IA.56 list of changed tile rows names a shot each.

**Fix size.** One small round, about 0.5 unit, 1 commit (M3 listener and widened gate with `tabstrip`; D-IA.60 rows, rule and
plants; packet corrections), a Sonnet continuation builder, heavy slot for `ia_shots` tabs and plan clauses. A fresh Claude reviewer at
verification depth reads M3 and L5 to L7 only. Merge still held for the owner's walkthrough; name M3's old state as closed only after
Lakeside 6500/No at 390 passes on all four tabs.
