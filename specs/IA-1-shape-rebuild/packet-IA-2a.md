# IA-2a packet: the plan shape (partial: clean stop at the end of 3(a))

**Stopped after 3(a) at the packet commit (after `dfaeef262`); resume at 3(b), the flip. `IA_LANDED` has no IA-2a: every
screen is as on `main`.** Stopped on the builder's context budget (standing brief), not on a coordinator stop. Not reviewable as
IA-2a yet: 3(b) and the discovery review remain.

Branch `task/IA-2a-plan` (worktree `/opt/assetecon/AssetOpsV1-ia2a`). Module path:
`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`. Evidence: `/opt/assetecon/evidence/IA-2a/` (`unit2/`, `3a/`).
Mid-build questions: **2** (Q3, Q4), both answered by the coordinator as naming only (`PS_PLANT`; a new block in `copy_check`); the
spec's "shape_check item 10" is item 14 (items 10 to 13 exist).

Commits: `554863783` unit 1 (splits, `parts_identity` states) · `c5af13ced` unit 2 (checks, stub, forced runs) · `ef7d098ad` 3(a)
builders, routes, `docTitle`, `ia.css` · `76b739121` uxi page default and M1 route order · `ce3d81d16` `ia_gates` names a crash's
error line · `dfaeef262` handoff.

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
- Not run at this stop: unforced `ia_gates`, full `ia_shots`, `parts_identity` against main's build, G3, shell_check, design_lint,
  render_text, vocab, hand_typed, check_manifest, check-architecture, check-agent-workflow; screenshots of the four tabs (3(b)).

## Notes for 3(b) and review
- `IA_FORCE_LANDED` re-renders after load (the bundle ends in `render();`, so "before the first render" needs a product change).
- D-IA.51: the Approve dialog has no case-label function; `iaPlanCaseLabel` uses the reviewed switches' own legends and checked
  options from `switches(op)`.
- `plan_shape_check` item 10 compares against `planScreen()` with `plainWords` applied, as `render()` applies it to the page.
- uxi needed two runner fixes: a default page path and no state shots without an out dir (`ia_gates` passes no arguments; the
  second is in the packet commit, after the gate run, which left a stray `undefined/` folder, deleted).
- Two forced uxi runs crashed with "Target crashed" during the /tmp quota incident (05:30 to 05:40 UTC); the rerun passed.
- 3(b) prep is saved, not committed: `/opt/assetecon/evidence/IA-2a/3a/3b-prep.patch` (walkthroughs.md, register R757 to R760,
  `.ai/state/demo.md` entry and index line 168) and `/opt/assetecon/evidence/IA-2a/3a/flip.py` (IA_LANDED gains IA-2a, plan renders
  `shapePlan`, `shapePlanInterim` deleted). Then build, unforced `ia_gates` (every IA-2a plant must fail; no "dormant"), the rest.

`MOCK DEVIATION`s (rows written in the patch, land in 3(b)): R757 D2 (no approval panel), R758 D2 (Approve in the band's act row),
R759 D1 (Review "Not yet"), R760 D5 (History: no per-version drawer, no address per entry).

`USER_REVIEW_REQUIRED`: not at this stop (nothing visible changed); the IA-2 walkthrough follows 3(b).
