# IA-2a packet: the plan shape (in review)

**Complete: units 1 to 3 built; 3(b) flipped at `a4737f102` (`IA_LANDED` has IA-2a); `main` merged at `af7847ac2`. Ready for the
discovery review.** The earlier clean stop after 3(a) (`dfaeef262`, builder's context budget) is resolved; 3(b) was built by builder 3.

Branch `task/IA-2a-plan` (worktree `/opt/assetecon/AssetOpsV1-ia2a`). Module path:
`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`. Evidence: `/opt/assetecon/evidence/IA-2a/` (`unit2/`, `3a/`).
Mid-build questions: **2** (Q3, Q4), both answered by the coordinator as naming only (`PS_PLANT`; a new block in `copy_check`); the
spec's "shape_check item 10" is item 14 (items 10 to 13 exist).

Commits: `554863783` unit 1 (splits, `parts_identity` states) · `c5af13ced` unit 2 (checks, stub, forced runs) · `ef7d098ad` 3(a)
builders, routes, `docTitle`, `ia.css` · `76b739121` uxi page default and M1 route order · `ce3d81d16` `ia_gates` names a crash's
error line · `dfaeef262` handoff. · `8f9067bca` 3(b) prep (walkthroughs, R771 to R774, state entry) · `a4737f102` **the flip** (IA_LANDED gains
IA-2a, `plan` renders `shapePlan`, `shapePlanInterim` deleted; built) · `af7847ac2` merge of `main` (`index-2.md`: both sides kept, IA-2a
renumbered 172).

## Built
- Unit 2: `plan_shape_check.cjs` (new) and `tools/fixtures/plan_stub.js`; `count_check` plan block (60 combinations, 15 boots;
  `planstep`, `planhist`, `planver`); `shape_check` item 14 (distinct document titles per tab group, live now: Portfolio passes;
  `doctitle`); G1 `plan tab: Left out|Review|History` (2, via any) and plan items' decisions limit 3, reported (`plantabs`);
  `plan_switch_check` IA path under `PS_PLANT` (`crewtile`, `release`, `leftout`); `copy_check` IA-2a block (`COPY_PLANT=plan`);
  `ia_shots` plan clause with `approvefold` (`SHOTS_ONLY=plan`); uxi plan block retargeted, forced-capable (`planans`, `planwait`).
  Every one prints `IA-2a not landed; dormant` unforced.
- 3(a): `ia-shapes.js` `iaPlanSteps`, `iaPlanStepper`, `iaCrewTiles`, `iaPlanBand`, `iaPlanCaseLabel`/`iaPlanCaseLine`, `iaPlanHead`,
  `iaPlanHistory`, `shapePlan`; `ia-routes.js` plan `tab: 'Items'`, `tabGroup: 'Plan'`, renders `shapePlan` when IA-2a is in
  `IA_LANDED` (forced in a check's window) else the interim; three tab routes (unit IA-2a) with `docTitle`; `IA_TAB_GROUPS.Plan`;
  `iaScreen` sets `docTitle`; `screens.js` `render()` writes `s.docTitle||s.title`; `ia.css` three rules.

## Gates
- `ia_gates.cjs --force IA-2a` at `dfaeef262` (heavy slot, 3805 s): **`ia_gates: 76 runs, landed IA-1a, IA-1b, IA-1c, forced IA-2a,
  all as expected`**, 0 BAD (`/opt/assetecon/evidence/IA-2a/3a/gates.log`). Every IA-2a plant failed on the builders (first lines):

| plant | first failing line |
|---|---|
| PLAN tabs | `#/plan (default case): tabs read "Items, Left out, Review"` |
| PLAN place | `heading "Left out of the plan, and why" counted 1, expected 0` (on Items) |
| PLAN l1 | `#/plan/history: .approval-releases counted 0, expected 1` |
| PLAN approval | `#/plan: .approval-releases counted 2, expected 1` |
| PLAN thr | `thresholds drawer: 0 found` |
| PLAN stepdone | `is-done on [], expected [0] (state PROPOSED)` |
| PLAN cap | `History shows 1 rows, expected 2` (caught on History only: Items, Left out, Review hold no capped list, D-IA.52 R7) |
| PLAN revised | `iaPlanSteps(REVISED) gives … cur 0` |
| PLAN sticky | `sticky's Approve act approve-plant, the band's approve-plan` |
| COUNT planstep / planhist / planver | stepper "Proposed" after Approve / History first row "proposed" / log:0 version on the non-default case |
| SHAPE doctitle | `in the Plan group the tabs "Items" and "Left out" share the document title` |
| G1 plantabs | `plan tab: Left out: depth ∞ > 2` |
| PS crewtile / release / leftout | `L1 2 crew tiles, found 1` / `approval releases 4 items, $2,460` / `not Returned to its creator` |
| COPY plan | `#/plan · as proposed: "Approve this quickly before the window closes."` |
| UXI planans / planwait | `Left out 2 answer-titled sections, NOT all answered` / `plan/history after Approve: "… Version 1, awaiting approval"` |

- Unit 2 against the stub (forced, before the builders; "written and mutation-tested", not "plants failing on the real shape",
  D-IA.49): the same plants all failed; `COPY_PLANT=plan` 36 stray strings; `SHOTS_PLANT=approvefold` 48 of 72 bad
  (`the band's Approve ends at 1490 past the first viewport 900`). Logs `/opt/assetecon/evidence/IA-2a/unit2/`.
- Forced, base runs pass on the builders: plan_shape PASS (L1 tiles Lakeside 4, Harvest 3, Metro 3; period 2026-11 to 2026-12);
  count plan block 60/60; G1 plan tabs 2 each, plan items reported (1 or 2 measured, under 3); plan_switch 793/0; uxi PASS;
  copy block 4802 strings, 0 stray (new strings per list entry: tab 108, step 96, stepper name 36, crew value 48, crew meter 48,
  case line 48, History 63). `ia_shots SHOTS_ONLY=plan` forced on the stub: 97 measured, 0 bad; band Approve bottom 590 at 1440.
## 3(b): after the flip (unforced, at `a4737f102`, heavy slot, pw env; logs `/opt/assetecon/evidence/IA-2a/3b/`)
- **`ia_gates`: `76 runs, landed IA-1a, IA-1b, IA-1c, IA-2a, all as expected (3575.6 s)`**, 0 BAD, no "dormant" line (`gates.log`).
  Every IA-2a plant still fails after the flip, with the same first lines as the table above (PLAN 9 of 9, COUNT 3, SHAPE doctitle,
  G1 plantabs, PS 3, UXI 2, COPY plan); every earlier unit's plant fails too.
- `ia_shots` full: **601 measured, 0 bad** (505 s; approvefold measured live). `parts_identity` against `main`'s build: **282 cases,
  282 byte-identical** (10 s). uxi **386 PASS, 0 FAIL** (574 s). count_check PASS (61 s). G3 36 of 36. plan_switch **793 passed,
  0 failed**. shell_check 0 fails (45 routes crawled). design_lint 0 fails. render_text 237 renders, 0 script errors. vocab 0 hits.
  copy: IA-2a block 4802 strings, 0 stray. hand_typed exit 0, 1 hit when first run (`rightsM`, "Rights measures by contract and period (as of 6 Nov)", a typed date in this diff); fixed in code in r1 (`fdate(AS_OF)`), count 0 now. check_manifest 7572 passed, 0 failed.
  check-architecture and check-agent-workflow pass. After the merge: `check-decision-index.py` OK; `specs/INDEX.md` 7949 bytes;
  fast check-all at `af7847ac2`: **All 40 guards passed** (82 s wall; 615 s with the slot wait).
- Layout evidence (`tools/layout-evidence.mjs`): not run, needs a served URL (no server started, by brief); `ia_shots` measures.

## Shots against the owner's standing UI brief (`owner/owner-ui-standing-brief-2026-11-20.md`)
Looked at, in `/opt/assetecon/evidence/IA-2a/3b/shots/`: Lakeside's four tabs at 1440, Items at 1280 and Items and History at 390,
Harvest Items 1440, Metro Left out 1440. One grammar holds: tabs switch content, the stepper and tiles are read-only, Approve and
Send back are buttons, the thresholds a drawer link. For the reviewer and the IA-2 walkthrough:
1. **Tabs change nothing in the first screen at 390 and at 1280 × 720** (`lakeside-plan-390-light.png`,
   `lakeside-plan-history-390-light.png`, `lakeside-plan-1280-light.png`). L1 (stepper, 4 tiles, act row, release line) fills the
   viewport, so a tab switch only moves the underline; the tab body starts below the fold. This is spec §5.1.2's "same L1 on every
   tab". Possible follow-up: compact L1 on the non-Items tabs, or scroll to the tab body on a switch.
2. **Two spend figures side by side without saying why they differ** (honest numbers): tile "$3,750 of $5,000" against the release
   line "$3,660 of one-off spend" (Lakeside), $720 against $620 (Harvest `harvest-plan-1440-light.png`), $1,590 against $1,500
   (Metro). Both are reviewed copy (parts reused byte for byte), not new; worth one line or a footnote naming the difference.
3. **Three tiles leave an empty fourth column** at 1440 for Harvest and Metro (one crew limit), so the row looks unfinished
   (`harvest-plan-1440-light.png`, `metro-plan-left-out-1440-light.png`).
4. Smaller: Review shows "Not yet" as plain text under Observed change and as a chip under Review (`lakeside-plan-review-1440-light.png`);
   History rows run the actor into the label ("Version 1 proposed The system · 6 Nov", `lakeside-plan-history-1440-light.png`); the
   Items L2 heading repeats the H1 ("The plan for November and December: items and their Actions"); at 1280 × 720 the crumb and the
   "version 1, proposed" subtitle are hidden by the IA-1c fit rule (the chip in the act row still carries the version).
None blocks the spec's acceptance; 1 and 2 are judgement calls for the owner.


## Notes for review
- `IA_FORCE_LANDED` re-renders after load (the bundle ends in `render();`, so "before the first render" needs a product change).
- D-IA.51: the Approve dialog has no case-label function; `iaPlanCaseLabel` uses the reviewed switches' own legends and checked
  options from `switches(op)`.
- `plan_shape_check` item 10 compares against `planScreen()` with `plainWords` applied, as `render()` applies it to the page.
- uxi needed two runner fixes: a default page path and no state shots without an out dir (`ia_gates` passes no arguments; the
  second is in the packet commit, after the gate run, which left a stray `undefined/` folder, deleted).
- Two forced uxi runs crashed with "Target crashed" during the /tmp quota incident (05:30 to 05:40 UTC); the rerun passed.
- The 3(b) prep patch applied cleanly at `fcaf77399`; `.agent/` is gitignored but the register is tracked (staged by path).
- Done-when item 1 says IA-2a is added "in the last commit": the flip is the last product commit; the merge and this packet follow.

`MOCK DEVIATION`s (register rows, `8f9067bca`): R771 D2 (no approval panel), R772 D2 (Approve in the band's act row),
R773 D1 (Review "Not yet"), R774 D5 (History: no per-version drawer, no address per entry).

`USER_REVIEW_REQUIRED: true` (UI/UX: the plan page changed shape). Hold the merge for the owner's IA-2 walkthrough after review.

## Fix round r1 (D-IA.54 to D-IA.57; rulings-4.md, spec §5.1 rev 6, reviewer guide rev 5)

Commits on `task/IA-2a-plan`: `09a06c300` commit 1 (D-IA.54 released-at-creation clause and `qty_check`; D-IA.57 rightsM date from fdate,
case-link href asserted per tab); `e5ccb0137` commit 2 (D-IA.55 `iaTabSwitch` listener, `[data-ia-tabs]` wrapper, phone margin tweak;
D-IA.56 tile-row fill CSS; `ia_shots` tabs set, `tilefill` measure and plants); `ab3746a44` copy_check lists the already-released clause
(spec §5.1.6; 36 strings matched; the first gate run failed on it, fixed, gates rerun whole).

Gates (heavy slot, pw env, at `ab3746a44`, logs `/opt/assetecon/evidence/IA-2a/r1/gates/`, shots `/opt/assetecon/evidence/IA-2a/r1/shots/`), all green:
build; `ia_gates` unforced 79 runs all as expected (3710 s); `ia_shots` 611 measured, 0 bad (530 s); uxi PASS (584 s); count_check PASS; qty_check PASS
(270 screens); G3 36 of 36; plan_switch 793 passed, 0 failed; shell_check, design_lint, render_text (237 renders), vocab, copy (0 not listed);
hand_typed 0 hits; check_manifest 7572 passed, 0 failed; parts_identity against main's `index.html` 282 cases identical; check-all fast: 40 guards passed (113 s).
Plants (each fails): `tabnoscroll` 66 of 76 bad, `tabscrollall` 69 of 79 bad (SHOTS_ONLY=tabs); `tilefill` 48 of 72 bad (SHOTS_ONLY=plan: the
3-tile plan rows of Harvest and Metro are the rows that were short; the hub routes have only 4-tile rows, so the plant is invisible there);
`QTY_PLANT=clause` and `wait` each fail all three operators (run directly: `qty-plant-*.log`). Tab-switch set: 81 switches, 0 bad.

Sweep of reconciled figures (D-IA.54): plan band $3,750 = $3,660 + $90 reconciled; Overview plan tile $3,750 alone, equal across routes;
Overview gap $852 = $827 + $25 reconciled. Plan Items "$1,520 in all" and Harvest "$620 in all" are a different quantity (the shown items'
sum), reviewed markup, registered in `qty_check`'s QTY table. **For the reviewer, "honest numbers":** Items "+$6,089" (tile) against
"Net +$6,088.50" (reviewed bytes) is the same figure rounded; not changed, and not yet registered: the pair waits for D-IA.59 in IA-2e.

Known Deviations: (1) the phone margins of the plan's L1 notes are tightened (`.ia-plan-released/rules/case`, max-width 600) so Lakeside's plan
at 390 does not start 8 px past the fold once the strip is at the top; (2) Portfolio Demand and capacity has no L2, so the listener and the
check fall back to the first `[data-level]` box.

## Fix round r2 (D-IA.58, D-IA.60; rulings-4.md, spec §5.1 rev 7, reviewer guide round 3)

Commit on `task/IA-2a-plan`: `25decf048` (one commit; main merged first at `b2fb5de65`, `check-decision-index.py` OK). D-IA.59 (figure format) is not in this
round: it lands in IA-2e.

**D-IA.58 (M3).** `iaStickyH()` is `iaInPage`'s sticky-bar measure, extracted (one measure, two callers). `iaTabSwitch`: when the content's first box at scroll 0 starts
below `innerHeight - 48`, the frame scrolls (instant) so that box sits at `iaStickyH() + var(--s2)`; otherwise it stays at 0. No sticky tab strip; focus rule unchanged.
Gate (`ia_shots` `SHOTS_ONLY=tabs`, forced on the stub): Portfolio, Plan, Site x 3 operators x 390/1280/1440; Plan x 3 states (proposed, approved, sent back) x default and
non-default case (D-IA.50: Lakeside 6500/No, Harvest aggregation No, Metro TOU No): **306 switches, 0 bad** (`tabs-clean.log`). It checks 48 px inside, content not under the
sticky bar, focus on the active tab, scrollY 0 on the default proposed plan at 1440/1280. Plants, all fail: `tabstrip` 10 of 306 bad (Lakeside proposed non-default at 390
on all four tabs: content 116 px below the fold), `tabnoscroll` 120, `tabscrollall` 40 (r2-lows rerun, L9: each plant now keeps the focus line, so it fails on its scroll check, none on focus; clean run 306 switches, 0 bad; `/opt/assetecon/evidence/IA-2a/r2-lows/tabs-*.log`). Lakeside 6500/No at 390 passes on all four tabs (shots
`/opt/assetecon/evidence/IA-2a/r2/tabshots/`, `lakeside-case-plan*-390.png`; each operator's default at 390 and Lakeside at 1280 and 1440 beside them).
Scroll-target sweep (class, W6): in `ia-routes.js` and the other scripts the only programmatic scrolls are `iaInPage` (the linked element, below the bar), `iaTabSwitch`
(first box, below the bar), `screens.js` hashchange `scrollTo(0,0)` (top), `rerenderKeep` in `loop-core.js` (restores the same offset). None aims at another box.

**D-IA.60.** L5: `qty_check` QTY gains `overview-gap` (total `.ux-kpi-v` of "Gap to target", parts the tile's Grow/Optimize line; $852 = $25 + $827) and `plan-items`
(the "in all" total in the tile's definition against the valued item rows' one-off costs: Lakeside $1,520 = $90 + $230 + $1,200, Harvest $620 = $350 + $270, Metro $1,590),
each failing if its selector finds nothing on a route it names. Plants `QTY_PLANT=gap` (fails Lakeside, the only operator with a Grow part) and `items` (fails all three).
The "+$6,089 / Net" pair waits for IA-2e. (r2-lows, L10: `ia_gates` `qty_check` now lists `gap` and `items` beside `clause` and `wait`; run with the new `GATES_ONLY=qty_check` filter, a partial run not the gate: clean pass, `clause`, `wait`, `gap`, `items` each fail as expected, 345 s, `r2-lows/gates-qty.log`.) The r1 sentence "registered in QTY" is corrected: what is registered is plan-spend, overview-gap and plan-items.
L6: `.ia-plan-released` takes the release line's font-size and colour tokens (`--fs-sm`, `--text-2`, as `.approval-releases`); `ia_shots` `releasedtype` measures it against the
release line at every plan run (18 clauses measured; the sets are the runs of the `plan` route that show the clause); plant `SHOTS_PLANT=releasedtype` fails 18 of 73. L7: line 65's hand_typed
sentence is corrected (fixed in code, count 0). One-off count of typed day-month dates inside template literals in `vNEXT/` (regex count, `loop-*.js`, `ia-*.js`, `screens.js`,
`outcomes.js`, `portfolio.js`): 34, none in `ia-*.js` (loop-decisions 11, loop-portfolio 8, screens 7, loop-core 3, outcomes 2, loop-ux/init/protect 1 each); 161 lines carry a
day-month string in any literal; extending the scanner is the coordinator's backlog item.
D-IA.56 changed tile rows (3-tile rows; 4-tile rows unchanged): Harvest and Metro, on all four plan routes. Shots: `harvest-plan-1440-light.png`, `metro-plan-1440-light.png`,
`harvest-plan-390-light.png`, `metro-plan-390-light.png` (and the three other plan tabs per operator, same names with `-left-out`, `-review`, `-history`), in `r2/gates/shots/`.

**Gates** (heavy slot, logs `/opt/assetecon/evidence/IA-2a/r2/gates/`, `summary.txt`), all green: build; `ia_shots` full **612 measured, 0 bad** (649 s); qty_check PASS (270 screens, 60 s);
count_check PASS; uxi PASS (588 s); G3 36 of 36; plan_switch 793 passed, 0 failed; shell_check, design_lint 0; render_text 237 renders 0 errors; vocab 0; copy 4838 strings 0 stray;
hand_typed count 0; check_manifest 7572 passed; parts_identity against main 282 of 282 byte-identical; **`ia_gates` unforced 79 runs all as expected (6797.7 s)**. Two uxi plant runs inside
`ia_gates` (`planans`, `planwait`) stalled at low CPU for 47 and 22 minutes (the browser stopped answering); I killed the browser each time, the gate recorded "got fail", so
those two are fails by crash, not by the plant's own assertion. A standalone `UXI_PLANT=planans` rerun completed normally in 10 m 34 s with 9 assertion FAILs (rc 1; `gates/uxi-planans.log`), so the stalls were browser flakes, not the plant or this round's code; `planwait` was not rerun alone. Fast check-all: **All 40 guards passed** (396 s wall, 276 s waiting for a slot; r2-lows rerun: All 40 guards passed, 142.5 s). Layout evidence (`tools/layout-evidence.mjs`): not run, needs a served URL (no server started); `ia_shots` measures.
