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
