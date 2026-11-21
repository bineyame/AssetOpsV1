# IA-2a review, round 2 (verification, W5/W6): fix round r1

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/IA-2a-plan`, head `12ab99a75`, diff
`d412f8202..12ab99a75` (vNEXT hunks: `ia-routes.js`, `ia-shapes.js`, `ia.css`, `loop-portfolio.js`, five tools; the rest is the
DS3 merge from `main` and docs). Evidence and logs: `/opt/assetecon/evidence/IA-2a/review2/`.

## Summary (round 2)

- **Verdict: ACCEPT WITH FIXES.** One Medium (M3, needs an Architect ruling), three Lows. Merge stays held for the owner's
  walkthrough (`USER_REVIEW_REQUIRED: true`). **Ready to show the owner: yes**, at 1440 and 1280 × 720 in every state; M3 (a phone
  in Lakeside's non-default case) should be named as open when the walkthrough is run.
- **M1 / D-IA.54 closed.** On all three operators the tile equals the release line plus the new clause ($3,750 = $3,660 + $90;
  $720 = $620 + $100; $1,590 = $1,500 + $90), on all four tabs. `qty_check` PASS (270 screens); `QTY_PLANT=clause` and `wait`
  each fail on all three operators (48 fails each).
- **M2 / D-IA.55 closed for the case the gate measures.** Tab set 81 switches, 0 bad; `tabnoscroll` 66 bad, `tabscrollall` 69 bad.
  At 1440 and 1280 nothing scrolls in the default case. Focus lands on the active tab, and a real mouse click shows no focus ring.
- **M3 (new, Medium).** At 390 in Lakeside's non-default case (6500 / No), a tab switch still shows only L1: the content starts 140 px
  below the fold on every tab. The rule cannot meet its aim when L1 is taller than the screen, and the gate measures only the default case.
- **D-IA.56 and D-IA.57 closed:** the rows fill (`tilefill` 48 of 72 bad); hand_typed count 0; `parts_identity` 282/282; the case-link
  `href` is asserted per tab.
- **"+$6,089" vs "Net +$6,088.50":** recommend one form per quantity on a screen and its drawers (a figure-format rule). Not a finding
  of this diff (both are reviewed bytes on `main`, and the Net sits in the tile's hidden definition). See "Honest numbers" below.

## Findings

### M3 (Medium, D-IA.55 aim not met; outside the gate's measured set): the phone tab switch in a non-default case

**Measured** (`ndfold.cjs` / `ndfold.log`, 3 operators × non-default / approved / sent back × 390 and 1280 × 720, after each tab
click). In Lakeside 6500 / No at 390 × 844 the strip moves to the top (`scrollY` 293), but the first box of the tab's content is
**140 px below the viewport on all four tabs** (`lakeside-nondefault-left-out-390-view.png`: the tabs, the stepper, four tiles,
Approve, the longer release line, the clause, then the "case shown is not the proposed version" notice, all on the first screen). Every
other combination passes (lowest: Lakeside approved 58 px, Metro non-default 86 px). At 1280 × 720 the non-default case scrolls the
strip to the top (Lakeside 245, Harvest 297), which is what the rule says, and Approve stays in view (bottom 273 and 214).

**Why it matters.** This is M2's symptom again, in the case the demo uses to show Left out (the `ia_shots` "Lakeside 6500/No on Left
out" shot). The builder made no mistake: "strip to the top" cannot work once L1 is taller than the viewport, and the Known Deviation (1)
margin tightening (8 px) shows how little headroom the default case has. The `ia_shots` tab set (`ia_shots.cjs:126-150`) measures only
the default case, so the gate cannot see the problem.

**Fix (Architect ruling; general, every tab group).** For example: on a switch whose content would start below the fold, make the tab
strip sticky at the viewport top below 760 px and scroll the content's first box to just under it. That keeps one header, one grammar,
and puts content in view at any L1 height. Gate: add the D-IA.50 non-default case and the approved state to the tab set; the existing
plants still fail.

### L5 (Low, packet claim / D-IA.54 sweep rule): `qty_check` guards one quantity; the packet says more are registered

`qty_check.cjs` `QTY` holds only `plan-spend` rows, and only `iaPlanReleased` declares `data-qty`. The packet says Items "$1,520 in
all", Harvest "$620 in all" and "+$6,089 / Net +$6,088.50" are "registered in `qty_check`'s QTY table". They are not. The Overview gap
pair ($852 = $827 + $25), which D-IA.54 says "gets a `QTY` row", has none. All of these screens are correct today (they sit in
collapsed or hidden content; my probe finds no visible "in all" or "Net" text on the plan or portfolio routes). Only regression cover
is missing. **Fix:** add the rows (the Overview gap as its own key; the Items sum as a separate key), or correct the packet sentence.

### L6 (Low, brief: deliberate hierarchy): the clause outweighs the line it completes

`.ia-plan-released` renders as body text (larger, darker) directly under the muted `.approval-releases` line. These are the two parts
of one total, but the smaller remainder reads as the more important statement (every shot, for example
`lakeside-plan-history-1440-view.png`). **Fix:** give `.ia-plan-released` the release line's type and colour. One `ia.css` rule; no copy
change.

### L7 (Low, packet completeness, D-IA.57 / spec §8 rev 6)

Packet line 65 still says the hand_typed hit is "pre-existing on `main` … not in this diff" (D-IA.57 L2 asked for the correction; the
code fix itself landed, count 0). The one-off count of typed dates inside templates (D-IA.57) is not reported. The D-IA.56 list of
changed rows names no shot. **Fix:** three packet lines.

## Honest numbers: "+$6,089" (tile) vs "Net +$6,088.50"

The tile and `planGroups` (`index.html:4290-4297`, used in the tile's definition `def`, `:4317`) show one quantity two ways: the
tile rounds to whole dollars, and the breakdown keeps cents because one valued option has cents. The two forms agree to the cent once
rounded, so this is not a wrong number. But the owner's brief puts honesty first, and an executive who opens the tile's explanation sees
two different figures. **Recommendation: one form, made a figure-format rule rather than a one-off fix.** Choose one rendered
precision per quantity, used everywhere that quantity appears on a screen and in its drawers and definitions. Whole dollars when every
part is whole; otherwise cents wherever it shows, tile included (or round the parts as well, and only where they then still add up).
`qty_check` can then compare rendered strings, not values. This changes reviewed bytes, so under D-IA.54 it is an Architect question,
best placed in the IA-2e reconciliation or the W1 copy pass. Not blocking IA-2a; name it at the walkthrough if the owner opens that
definition.

## ab3746a44 (copy_check lists the clause)

Fine, and it hides no text rule. The entry is exactly the §5.1.6 copy of D-IA.54 ("its Action was" / "their Actions were", "{item}
({$})" joined by "; "). Its `.+` item slot is the same width as the existing case-line entry. The doubled-word and spacing faults are
separate checks and are untouched. 36 strings matched; `COPY_PLANT=plan` still fails.

## Checks run (by me, head `12ab99a75`, heavy slot, pw env)

- `qty_check` PASS (270 screens, 210 figures); `QTY_PLANT=clause` FAIL and `wait` FAIL, each on all three operators (48 fails, rc=1).
- `ia_shots` `SHOTS_ONLY=tabs`: 81 switches, 0 bad (the Site group has one landed tab, so it is reported, not measured);
  `tabnoscroll` 66 bad (390 on Plan: content −241 px), `tabscrollall` 69 bad (1440 Plan: `scrollY 322, not 0`);
  `SHOTS_ONLY=plan SHOTS_PLANT=tilefill` 48 of 72 bad (Harvest and Metro 3-tile rows, 16 at each of 390, 1280 × 720 and 1440).
- `parts_identity` against `main`'s `index.html`: 282 cases, 282 byte-identical. `hand_typed_scan` count 0. `plan_shape_check` PASS
  (the per-tab `href` assert and `.ia-plan-released` once in L1). `copy_check` PASS, IA-2a block 4838 strings, clause 36;
  `COPY_PLANT=plan` FAIL.
- `check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON`, since the worktree has no `.venv`); `check-agent-workflow.ps1` passed.
- Browser (`look.cjs`, `ndfold.cjs`, `focusring.cjs`, `net.cjs`): the four tabs × 3 operators × 390 / 1280 × 720 / 1440, viewport and
  full-page shots (`shots/`): no sideways scroll, no page errors, distinct titles, tile rows end flush (gap 0), L1 text identical across
  tabs. Real mouse click: focus on the tab, `:focus-visible` false.

## Not verified by me

The full `ia_gates` (79 runs), the full `ia_shots` (611), uxi, G3, render_text, check_manifest and check-all: I cite the builder's run at
`ab3746a44`, and `git diff ab3746a44 12ab99a75` touches no vNEXT file. I did not look at dark mode beyond the gate's measures, and did not
run `layout-evidence.mjs` (the packet records it as not run).

## Residual risk not named in the packet

- L1 height at phone width grows with state (the case line, the notice, a longer release line), so D-IA.55's headroom is a few px in
  the default case (M3).
- `qty_check` knows one key. Any other total-beside-part pair on a live route is unguarded until it has a row (L5).

---

# IA-2a review, round 3 (verification, W5/W6): fix round r2

Reviewer: a fresh Claude reviewer who did not author the work. Branch `task/IA-2a-plan`, head `30d8b7b82`. The code is in `25decf048`, and main
was merged at `b2fb5de65`. I checked M3 and L5 to L7 against D-IA.58 and D-IA.60, and D-IA.59's deferral. Evidence:
`/opt/assetecon/evidence/IA-2a/r2-verify/` (`summary.txt`, per-run logs, `probe.cjs`, `shots/`).

## Summary (round 3)

- **Verdict: READY FOR WALKTHROUGH.** No High or Medium findings. There are three Lows (L8 to L10), none blocking; each can be fixed on the
  branch before the merge. The merge stays held for the owner's walkthrough.
- **M3 / D-IA.58 is closed.** I wrote my own probe with real mouse clicks on the visible tab: 3 operators × 390/1280/1440 × 3 states × the
  default and the non-default case, 216 switches, 0 bad, no page errors. At 390 in Lakeside 6500/No the content's first box is at 8 to 9 px
  from the top on Items, Left out and Review, in every state, and the bottom sticky bar covers none of it. History is short and its scroll is
  clamped, so its content is at about 455 to 475 px, still in view. At 1440 and 1280 the default proposed case stays at scroll 0.
  `ia_shots` tabs: 306 switches, 0 bad.
- **The plants fail on their own assertions**, which I checked line by line, not only by count. `tabstrip`: the content is at −116 px
  (proposed) and −26 px (approved) on all four tabs and Back, in Lakeside non-default at 390. `tabnoscroll`: 120 content failures.
  `tabscrollall`: 40 `scrollY` failures. See L9 for why the totals are inflated.
- **L5 is closed:** `overview-gap` and `plan-items` are in `QTY`, and `qty_check` passes (270 screens). `QTY_PLANT=gap` fails on Lakeside, the
  only operator with a Grow part. `items` fails on all three operators. `clause` and `wait` still fail.
- **L6 is closed:** 18 clauses are measured, with the same size, weight and colour as the release line in light and dark. The `releasedtype`
  plant fails all 18.
- **L7 is closed**, except for one leftover sentence (L8).
- **D-IA.59 is consistent:** the ruling puts it in IA-2e, and spec rev 7 (§5 note, line 584) says so.
- **Builder's caveat:** both plants complete on their own and fail on their own assertions, with no stall. `planwait`: rc 1 in 625 s,
  3 FAIL. `planans`: rc 1 in 593 s, 9 FAIL.

## Findings

### L8 (Low, packet accuracy, D-IA.60 L5): the r1 sentence still claims "+$6,089 / Net" is registered

`specs/IA-1-shape-rebuild/packet-IA-2a.md:123-124` still reads "Items '+$6,089' (tile) against 'Net +$6,088.50' … both registered, not
changed". It is not registered; it waits for D-IA.59 in IA-2e. Line 148 corrects this in the r2 section, but the original sentence stands
unmarked, and the ruling asked for the sentence itself to be corrected. **Fix:** a one-line edit at :123-124, for example "both waiting for
D-IA.59 (IA-2e)". This is an acceptance gap, though a trivial one.

### L9 (Low, gate signal): the three tab plants also remove the focus step, so most of their failures are the focus assertion

`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/tools/ia_shots.cjs:144-146` replaces `iaTabSwitch` wholesale. None of the
three replacements focuses the active tab, so almost every click fails "focus is not on the active tab". For example, `tabstrip` shows 245 bad,
but only 10 of those are content failures. A plant that only fails on focus would still "fail" if the content assertion broke, so the plant's
exit code does not prove the D-IA.58 assertion. I confirmed by reading the logs that it does fail today. The packet's "tabstrip 245 of 306
bad (Lakeside … content 116 px below the fold)" reads as if 245 were content failures. **Fix:** let each plant keep the focus line (copy it from
`iaTabSwitch`), so that each plant fails only on its target assertion, and restate the counts. This is gate quality, not product behaviour.

### L10 (Low, plant registry, W6): the new `qty_check` plants are not in `ia_gates`

`tools/ia_gates.cjs:18` registers `qty_check` plants `['clause', 'wait']` only. `gap` and `items` (D-IA.60) were run by hand, but the gate
runner that "runs every plant of every landed unit" does not run them, so a future change that makes them pass would go unseen. **Fix:**
add `'gap', 'items'` to that list (2 more runs, about 2 minutes).

## Checks run (by me, head `30d8b7b82`, heavy slot, pw env)

- `node build.mjs`: it rebuilds `index.html` byte-identical to the commit (no diff).
- `probe.cjs` (mine): 216 real-click switches, 0 bad. The screenshots of Lakeside non-default in all 3 states at 390, and each operator's
  default at 390, are in `shots/`.
- `ia_shots` with `SHOTS_ONLY=tabs`: 306 switches, 0 bad. `tabstrip` rc 1 (245 bad), `tabnoscroll` rc 1 (266), `tabscrollall` rc 1 (251).
- `qty_check`: PASS. `gap`, `items`, `clause` and `wait` each rc 1.
- `ia_shots` with `SHOTS_ONLY=plan`: 98 measured, 0 bad, 18 clauses. `releasedtype` rc 1, with 18 bad.
- uxi with `UXI_PLANT=planwait` alone: rc 1, 383 PASS and 3 FAIL ("plan/history after Approve … awaiting approval"). With `planans` alone: rc 1,
  377 PASS and 9 FAIL ("Left out … NOT all answered"). All other uxi assertions pass in both runs, including the in-page anchor paths that
  use the extracted `iaStickyH`, so the refactor of `iaInPage` shows no regression.
- `check-architecture.ps1` passed. `check-agent-workflow.ps1` passed.

## Not verified by me

I did not rerun the full `ia_shots` (612), the full `ia_gates` (79), G3, render_text, check_manifest, parts_identity or check-all. For those I
cite the builder's runs at `25decf048`; `30d8b7b82` touches only the packet. The builder's first G3 run (`gates/g3.log`) crashed when called
with no arguments, and the rerun with arguments (`g3b.log`) gives 36 of 36. I did not run `layout-evidence.mjs`, for the same reason as the
packet: it needs a served URL.

## Residual risk

- On a phone, a tab switch now lands about 1,000 to 1,250 px down the page, and the tab strip is out of sight above it. D-IA.58 accepts this
  and rejects a sticky strip. Name it at the walkthrough in case the owner finds the strip "lost" (the ruling's W1 reconsideration).
- The IA-2e row in spec §5 (table, line 580) does not list D-IA.59; only the rev 7 note carries it. The Architect should add it to IA-2e's
  scope when that unit is specced.
