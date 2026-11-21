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
