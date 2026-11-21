# IA-2b reviewer guide (rev 1, 2026-11-21): the list shape

Read `spec-IA-2b.md`, `rulings-5.md` D-IA.61 to D-IA.66, `spec.md` §6 to §8, and the proposal page's "2 · Home list" figure
and §3 rules. Depth: discovery (W5), one review per part (IA-2b1 after unit 3, IA-2b2 after unit 5). Questions go in
`handshake.md` under "IA-2b", with the Implementer's pre-flight; mid-build questions in `mid-build-questions.md`.

**IA-2b1 done when** (beyond `spec.md` §6 and spec §10):
1. `decisions`, `findings`, `actions`, `sites` are live, shape `list`, through `iaRender`; `IA_LANDED` gains `IA-2b1` in the
   last commit; `iaOutcomeTable` is gone and `portfolio/outcomes` draws the Sites rows.
2. `ia_gates.cjs` lists every 2b1 plant of spec §8 failing. Run `LIST_PLANT=own`, `LIST_PLANT=restore` and `OUT_PLANT=cap` yourself.
3. `parts_identity` reports every earlier job identical (2b1 changes no reviewed function).
4. The copy is spec §7 word for word; `hand_typed_scan` 0 on the diff.

**First checks.** Diff scope: `vNEXT/` and the files spec §2 names. No reviewed function changed in 2b1 (`git diff` the
`loop-*.js` files: empty). Independence: `list_shape_check` B computes rows from ATTN, `HC.findings`, `WF(op).actions` and
`OPS[op].sites` with its own code (grep it for `iaListModel`, `iaDecIds`, `uxFindingRows`: only block A may call the model).

**Probes.**
- **Q1 The address is the view.** On Lakeside Decisions pick State "Waiting for a choice", sort "Due date", search a word:
  the address changes each time, the control keeps its place and focus; Back steps through each; copy the address into a
  fresh tab: the same view. A typed `state=nonsense` is ignored.
- **Q2 Counts.** Tile 1 = the rows plus "Show all n"'s hidden; Actions: Released + Waiting (+ Returned) = Actions, as
  proposed, after Approve, after Send back, and in Lakeside 6500/No (Returned appears). Sites: the gap tile = the rows' gaps,
  one form (D-IA.59); at scope all it equals the Overview's gap tile.
- **Q3 One target.** Tab through a list: one stop per row; the whole row clicks through; Finding and Action rows open their
  decision (or the plan); no button inside a row.
- **Q4 Scope.** From a list, the scope menu's Site entry scopes the list (it does not open the Site); the chip's "All sites"
  clears it; filters survive a scope change.
- **Q5 Aliases and crumbs.** `#/findings-cost` lands on Findings with Heading "Optimize cost and efficiency"; `#/portfolio/act-first`
  on Decisions; a decision's "Decisions" crumb and a Site's "Sites" crumb are links.
- **Q6 Scale.** The synthetic block's 25-item store: 10 rows, "Show all 25", waiting items never hidden by the cap, groups
  only above 10 in more than one group. At 390: no sideways scroll, rows stack with their labels, the tools wrap.

**IA-2b2 (after the stop) done when:** the stop line in the packet cites the owner file of the IA-2a walkthrough; the hub
rows are list rows with "View all {n}" equal to the target list's tile; no "Decide" in any row or the Site sticky (unless the
walkthrough re-ruled it); `parts_identity` holds with the new parts; G1 prints "released Actions of the plan version" at ≤ 2
with the href's values asserted; the IA-1b count plants still fail on the new rows; R749 to R751 closed.

**Class sweeps (W6).** Any IA list or queue that filters outside the address. Any row with a second interactive element.
Any count shown beside a list that is not the list's length. Any total beside its parts in two forms. Any alias whose
target query is dropped. Any typed month.

**Risks.** The focus keep must not fight D-IA.58's tab scroll (a list change is not a tab switch). `iaCanon`'s query merge
can double a parameter; the canonical order prevents it only if every writer uses `iaListHref`. The Outcomes fold changes
its cap from an in-place button to a link: `outcomes_table_check` must still fail on every `OUT_PLANT`.
