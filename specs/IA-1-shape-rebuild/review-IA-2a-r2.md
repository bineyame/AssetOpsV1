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
