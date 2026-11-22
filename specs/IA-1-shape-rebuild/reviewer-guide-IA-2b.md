# IA-2b reviewer guide (rev 2, 2026-11-21): the list shape

**Read:**
- `spec-IA-2b.md` (rev 2);
- `rulings-5.md` D-IA.61 to D-IA.81 (rev 2 adds the handshake answers, D-IA.67 to D-IA.81);
- `spec.md` §6 to §8;
- the proposal page's "2 · Home list" figure, its "3, 30 and 300 Sites" figure and its §3 rules.

**Depth:** discovery (W5), one review per part: IA-2b1 after unit 4, IA-2b2 after unit 6. Round 1 is answered in
`handshake-IA-2b.md`. Mid-build questions go in `mid-build-questions.md`.

**IA-2b1 is done when** (beyond `spec.md` §6 and spec §10):
1. `decisions`, `findings`, `actions` and `sites` are live, shape `list`, through `iaRender`. `IA_LANDED` gains `IA-2b1` in
   the last commit. `iaOutcomeTable` is gone, and `portfolio/outcomes` draws the Sites rows with no button in a row.
2. `ia_gates.cjs` lists every 2b1 plant of spec §8 failing. Run these yourself: `LIST_PLANT=own`, `restore`, `tier`,
   `stakesort` and `remainder`; `QTY_PLANT=counts`, `listcents` and `gapnet`; `OUT_PLANT=cap`. In the heavy slot, run
   `SHOTS_PLANT=listkeep`.
3. `qty_check` prints its count-mode keys, its format-mode keys and the deferred keys (with their count). The `EQUAL` row
   `sites:gap:` = `overview-gap` holds on all three operators.
4. `parts_identity` reports every earlier job identical (2b1 changes no reviewed function).
5. The copy is spec §7 word for word, and `hand_typed_scan` is 0 on the diff.

**First checks.**
- **Diff scope:** `vNEXT/` and the files spec §2 names. No reviewed function changed in 2b1: `git diff` of the `loop-*.js`
  files is empty.
- **Independence (D-IA.73):** grep `list_shape_check` for `iaListModel`, `IA_LIST_DEFS`, `iaDecStateKey`,
  `iaActionStateKey`, `iaFindingSite`, `uxFindingRows`, `iaOutcomeRows` and `iaDecIds`. Only block A (and D, through the
  rendered route) may reach the list's code. B's word tables are literals, asserted against the product's.
- **The keep (D-IA.75):** `iaListRestore` is registered after `iaTabSwitch` in `ia-routes.js`, it clears `IA_LIST_KEEP` on
  every `hashchange`, and `iaBind` has no restore.
- **The fixture is tools-only:** `list_fixture.cjs` is never loaded by `index.html`, and no product route reaches it.

**Probes.**
- **Q1 The address is the view.** On Lakeside Decisions (8 rows, so Sort only):
  - Scroll so that Sort sits mid-screen, then change it. The address changes, the control keeps its place and focus, and
    Back returns.
  - `#/decisions?state=waiting` shows the chip "Waiting for a choice · All states", and the chip's link clears it.
  - A typed `state=nonsense` is ignored.
  - A fresh tab at a copied address gives the same view.

  On the fixture shots (S8), tier 2 has filters, sort and search, and they wrap at 390.
- **Q2 Counts and money.**
  - Tile 1 = the rows plus the hidden rows of "Show all n" (fixture).
  - Actions: Released + Waiting (+ Returned) = Actions, as proposed, after Approve, after Send back, and in Lakeside
    6500/No (Returned appears).
  - Sites: the gap tile equals the sum of the row gaps in one form (D-IA.59). At scope all it equals the Overview's gap tile
    (Lakeside −$852, Harvest −$770, Metro −$3,184, the last netting −$3,204 against +$20).
  - The fixture's remainder line closes the sum.
  - Decisions has no stake sort, and "Not valued" is never a number.
- **Q3 One target.** Tab through a list: one stop per row, and the whole row clicks through. Finding and Action rows open
  their decision (or the plan). No button sits inside a row, the Outcomes tab included.
- **Q4 Scope.** From a list, the scope menu's Site entry scopes the list (it does not open the Site). The chip's "All sites"
  clears the scope, and filters survive a scope change.
- **Q5 Aliases and crumbs.** `#/findings-cost` lands on Findings with the chip "Optimize cost and efficiency · All
  headings". `#/portfolio/act-first` lands on Decisions. A decision's "Decisions" crumb and a Site's "Sites" crumb are links.
- **Q6 Scale (fixture, D-IA.67).**
  - Tiers: 2 items show no controls; 3 and 10 show Sort only; 11 and 30 show the full toolbar.
  - `sites30`: group heads 18, 7 and 5; one "Show all 30"; the cents fallback on every gap figure; the no-target Site last,
    with the tile's line.
  - Waiting items are never hidden by the cap.
  - At 390: no sideways scroll, rows stack with their labels, and the tools and chips wrap.

**IA-2b2 (after the stop) is done when:**
- the stop line in the packet cites the owner file of the IA-2a walkthrough;
- the hub rows are list rows, with "View all {n}" equal to the target list's tile;
- no "Decide" appears in any row or in the Site sticky, unless the walkthrough re-ruled it;
- `parts_identity` holds with the new parts;
- G1 prints "released Actions of the plan version" at ≤ 2, with the href's values asserted, and the link lands with the
  chips "Released · All states" and "Version {n} · All versions";
- the IA-1b count plants still fail on the new rows;
- R749 to R751 are closed.

**Class sweeps (W6).** Look for any of these:
- an IA list or queue that filters outside the address;
- a row with a second interactive element;
- a count shown beside a list that is not the list's length;
- a total beside its parts in two forms;
- a sort or sum over figures that cannot be added (D-IA.69);
- a view state that no control or chip names (D-IA.70);
- a control drawn where the whole list is visible beyond Sort (D-IA.67);
- an alias whose target query is dropped;
- a typed month.

**Risks.**
- The keep must not fight D-IA.58's tab scroll (a list change is not a tab switch, and list routes have no `tabGroup`).
- `iaCanon`'s query merge can double a parameter. The canonical order prevents that only if every writer uses `iaListHref`.
- The Outcomes fold changes its cap from an in-place button to a link, and from per-group to one cap (D-IA.80):
  `outcomes_table_check` must still fail on every `OUT_PLANT`.
- `qty_check`'s format mode must not pass `plan-spend` silently: it is printed as deferred to IA-2e.
