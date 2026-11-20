# Review: UI wave 2c (Portfolio polish), round 1

Reviewer: independent Claude reviewer (did not author the wave). Branch `task/uiux-guide`, commit 602e3e378, base 6bdbd3329.
Brief: `owner/owner-portfolio-polish-wave2c-2026-11-19.md` (main), `owner/owner-african-design-identity-2026-11-19.md`.

## Summary

- **Verdict: REVISE** (one Medium, small fix; otherwise ready).
- Gaps 2, 3, 5 and 6 read as fixed at 1440 and 390 for all three operators. Gap 4 is fixed for Lakeside and Metro; it breaks for Harvest (M1).
- Gap 1 (trends) is honestly not fixed: there is no history, `uxHistory` returns null and every slot says "Trend not available yet". No invented values anywhere.
- Gap 7: East Africa is now distinguishable at a glance (serif headings, indigo title with a short rule, terracotta tab, 12 px textile band, rail lattice) and stays professional. The pushback holds (see below).
- M1: in the gap-as-scale chart, a run that overshoots the gap (offsetting steps) draws bars past the track and out of the card (Harvest: 46 px past the track, 29 px past the panel at 1440).
- Lows: a visible empty "Due:" on phone cards; rounded figures that do not add up on screen (Lakeside); offsetting shares sum to 141%; residual sign differs between tile and chart (Metro, pre-existing); rail lattice behind low-contrast rail text; dead `uxPlanCard`.
- Gates: all pass (check_manifest: the 5 known FAILs only). No page errors in 37 screenshots.

## Findings

### M1 (Medium, acceptance gap: gap 4) Gap-scale bars overflow the chart when the running total overshoots the gap
`interactive-mockup-vNEXT/loop-ux.js:184-186`. Position is `run` in percent of the gap and only the left edge is clamped (`Math.max(0, L)`). When a step moves past October and a later one comes back, `run` exceeds 100. Harvest: crate-days −$620 (81%), then electricity −$197 takes the run to 106%, and +$155 brings it back. Measured at 1440: both of those bars end 46 px past the track and 29 px past the panel edge, and the panel clips them. At 390 they end 2 px past the panel. Screenshots: `crop-harvest-1440-bridge.png` and `east-africa-portfolio-harvest-1440-light.png`. Metro overshoots too, by 4-5 px. This matters because it is the hero chart for one of three demo operators, and its claim is "the steps fill the width of the gap". The scale is drawn wrongly exactly where steps offset. The fix is to scale the track to `[min(0, min run), max(100, max run)]`, place the "Target" and "October" labels at their scaled positions, and add a containment assertion to `ux_interaction_check` (each bar's right edge ≤ the track's right edge, for every operator). The check passed only because it does not measure this.

### L1 (Low) An empty "Due:" label on phone
`loop-ux.js:132`. The blank cell is right at 1440, where the column header carries "Due". On a phone card the label is static, so rows without a deadline show a bare "Due:". See `east-africa-portfolio-harvest-390-light.png`, rows 1-2. To fix, omit the whole `.ux-q-due` line on phone when there is no date, and keep the screen-reader text.

### L2 (Low, honesty) Rounded figures do not add up on screen
Lakeside: the rows sum to −$851 against a gap of −$852. The Optimize rows sum to −$826 against a subtotal of −$827. The shares sum to 101%. The underlying values reconcile (they are rounding artefacts), but an executive adding the column finds $1. To fix, round with largest remainder so the rows sum to the shown subtotal, or add "figures rounded" to the scale caption.

### L3 (Low, honesty) Shares of a gap with offsetting steps
Harvest's shares are 81%, 26%, 20% and 14%, which sum to 141%. Calling the favourable +$155 "20% of the gap" is arithmetically defined but reads oddly. To fix, label the shares "% of gap size" or show shares only for steps that widen the gap, and give the offset as "offsets $155".

### L4 (Low, pre-existing) Residual sign differs between tile and chart (Metro)
The "Gap to target" tile reads "+$20 not attributed yet" (raw `G.residual`, `loop-ux.js:283`). The chart row reads "−$20" (`shown()` applies `dir`). The arithmetic in the chart (2,604 + 600 − 20 = 3,184) is right. To fix, use one sign convention for the same quantity on one page.

### L5 (Low) Rail lattice sits behind rail text, and one rail label fails contrast
The East Africa `.rail::before` pattern covers the lower 38% of the rail, so its diagonals run through "Simulator Lab" and "Demo workspace". The "WORKSPACE" section label computes to rgb(92,82,68) on #1d1b3a, about 2.2:1, below AA. It predates 2c, but the pattern makes it worse. See `crop-ea-rail-footer.png`. To fix, keep the pattern below the last rail item (or mask it behind the footer) and lift the section-label token. The "AA in both packs" claim evidently did not cover this label.

### L6 (Low) Dead code
`uxPlanCard` (`loop-ux.js:259`) is no longer called anywhere. Remove it, or note that it is kept for the plan tab.

## Pushback, judged on merit

- **Outcome strip kept on the Overview (OD-21): agreed.** The tiles are slim and even, have no counts and open their drawers. They are not the same thing as the gap: they show headline measures, including Protect and Assure, which the bridge cannot show. The page meets the budget anyway: 6 blocks; 2,222 / 1,966 / 1,982 px at 1440 (the claim was 2,230).
- **No pictorial illustration: agreed.** Textile band, beadwork rule and door lattice are abstract regional accents. Illustration on a finance overview reads as costume and carries stereotype risk. The serif plus terracotta and indigo are enough to tell the packs apart at a glance. The 12 px band is the busiest element, but it is acceptable.

## Gate results (run by the reviewer, worktree at 602e3e378, `node build.mjs` reproduces index.html byte-identically)

| Gate | Result |
|---|---|
| render_text | 205 renders, 0 script errors |
| vocab_check | 0 hits |
| copy_check | 12,838 segments, 0 hits; `COPY_PLANT=1`: planted, 4 hits, exit 1 (as intended) |
| plan_switch_check | 777 passed, 0 failed |
| design_lint | exit 0 (residual colour literals only, not failing) |
| ux_interaction_check | 87 PASS, 0 FAIL (overview budget, queue rules, brand switch +22 px ≤ 32) |
| check_manifest.py | 4,474 passed, 5 failed: the 5 known (factor-map brief readable, 4 × A1 owner-reference alignment) |

## Verified by the reviewer
- Gap chart sums: Lakeside −25 −412 −176 −166 −56 −16 = −851 ≈ −852 (rounding). Harvest −620 −197 +155 −108 = −770 ✓, Optimize subtotal −150 ✓. Metro 2,604 + 600 − 20 = 3,184 ✓.
- One primary Decide (on the first row) for each operator. No title repeats its Site. Chips sit on their own line.
- Moved content is reachable: "Where value leaks" is the first heading on Demand and capacity for all three operators, and the insight is appended to Outcomes by site (`loop-init.js:21`). The plan is reached through "Review the plan".
- Modelled tile: lighter, dashed, keeps its "Modelled" marker and the † design-estimate mark. Actuals are untouched.
- Dark mode in both packs and the phone layout (390) show no horizontal page scroll (`scrollWidth` = viewport on every shot).

## Not verified
- Real Iowan/Palatino rendering: this host falls back to DejaVu Serif. Pointer-hover underline on figures (the keyboard focus indicator was checked by the gate).

Screenshots: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-wave2c/` (scratch, not committed).

## Re-review (fix round + U7–U10 + Recalculate now)

Reviewer: a fresh independent Claude reviewer (wrote neither the wave nor round 1). Range b255131a5..853013d13 (85375a072, eb56b72d0, 853013d13). The gates ran on a `git archive` copy of 853013d13 in scratch; `node build.mjs` reproduced `index.html` byte for byte. The worktree was not touched.

### Summary

- **Verdict: ACCEPT with findings fixed on the branch**: M1 (a copy-only change to the Recalculate notice) before merge; the Lows can go with it or later.
- M1 and L1–L6 are fixed as classes. The new checks in `ux_interaction_check` caught each of 5 planted violations (below).
- The rulings hold on merit. Hand arithmetic for Lakeside, Harvest and Metro reconciles, and the signs agree across tile, chart, drawer and Site rows.
- U7–U10 are applied as the owner answered. East Africa is the default for the three demo operators; Neutral is the product default; the switch works.
- At 1280×720 the first queue row is above the fold in both packs for all three operators.
- M1 (new): after "Recalculate now" the notice contradicts itself and the top bar.
- Lows: the brand-height check no longer tests anything; the in-page MOCK DEVIATION chip has no category and is visible to clients; the U7 RULES text goes slightly past what was approved.

### Planted violations (scratch copies; nothing to revert in the worktree)

| Plant | What | Result |
|---|---|---|
| 1 | M1 reverted: `S = p => p`, no width clamp | FAIL harvest 1440/390 (46 / 19 px outside), metro 1440/390 |
| 2 | L2: rows rounded on their own | FAIL lakeside: rows −826 against subtotal −827 |
| 3 | L3: shares of the gap, rounded on their own | FAIL lakeside 101%, harvest 121%, metro 101% |
| 4 | L1: the CSS rule for `.ux-q-due.is-empty` removed | FAIL ×3 at 390: 2 empty due lines visible |
| 5 | Subtotals rounded on their own, +1 | FAIL ×6: subtotals against the gap (−850/−852, −768/−770, −3183/−3184) |

### The rulings, checked by hand

- **Lakeside.** Gap −852. Grow −25. Optimize steps −412.5, −176, −166.5, −56, −16; the floors sum to −828, so 1 is added back to the first .5 tie, giving −412, −176, −167, −56, −16 = −827. −827 − 25 = −852 ✓. Shares of 852: 48.42, 20.66, 19.54, 6.57, 2.93, 1.88. Largest remainder gives 48, 21, 19, 7, 3, 2 = 100 ✓. Note: the two .5 values round in opposite directions; the table view shows cents. That is a property of the method, not a defect.
- **Harvest.** −620 | −197, +155 (offset), −108 = −150 | −770 ✓. Shares of 925: 67.03, 21.30, 11.68, giving 67, 21, 12 = 100 ✓. +$155 reads "offsets" ✓.
- **Metro.** Gap −3,184.32, shown as −3,184. Steps −2,604, −600, +19.68: the floors sum to −3,185, so the .68 rounds up to +20. −3,184 ✓. Shares of 3,204: 81, 19 = 100 ✓.
- **Signs.** For Metro: tile −$3,184 and "+$20 not attributed yet"; chart −$2,604, −$600, +$20; drawer −$2,604, −$600, +$19.68; Site rows the same ✓. Lakeside and Harvest agree as well.
- **On merit.** Largest remainder (Hamilton) is the standard method for reconciling rounded parts. "Shares of what widens the gap", with offsets unshared, removes the 141% oddity without hiding the offset. One sign rule (effect on the headline result) is the right executive convention. Scaling the track to [min run, max run] is correct: for Harvest, October sits at 94% and the overshoot is visible inside the card.

### Findings

**M1 (Medium, honesty: Recalculate now).** `loop-ux.js:470`. After the press, the green notice reads: "Recalculated · figures as of 01:03, 6 Nov · asked for by Operator executive · Esther. Figures updated: this demo holds no recalculated values, so the numbers shown are unchanged." There are four problems:
- "Figures updated" contradicts "unchanged".
- The time comes from the wall clock on the demo date. It can come before the 06:00 snapshot and the 09:40 invoice, as it did here (01:03).
- The top bar still says "Figures as of 06:00, 6 Nov", so the page states two different as-of times.
- The green "Recalculated" tone implies the invoice is now reflected, and that it changed nothing.

The notice does say the numbers are unchanged, but the rest of it says the opposite. Fix: word it as a request, for example "Recalculation requested at <time> by <person>. This demo holds no recalculated values, so the figures still show 06:00." Keep a neutral or info tone, keep the top bar as it is, and drop "Figures updated". Shots: `harvest-*-recalc-after.png`.

**L1 (Low, gate regression).** `tools/ux_interaction_check.cjs:155-160`. Because the page now starts in East Africa, `before` and `after` are both East Africa, and the "height within 32 px" assertion compares 2264 with 2264. The 32 px pack budget (guide §4.7) is no longer asserted. Fix: measure the height in Neutral (after the switch to Neutral) against East Africa.

**L2 (Low, RULES §6 label).** `loop-core.js:412`. The chip reads "MOCK DEVIATION · addition". "addition" is not one of the D1–D6 categories that RULES §6 requires (this one is D2, an improvement the owner asked for). The chip also sits in the product content, not in the review bar, so it is system vocabulary on the client-facing surface (copy_check and vocab_check do not catch it). Fix: label it D2, and mark it as review tooling (like the review bar) or keep it in the code and the guide only.

**L3 (Low, U7 scope).** `.ai/RULES.md:130-133`. The diff is minimal and in the existing style. It says "gates G1-G5", where the approved U7 text says G2 to G4. It also adds a precedence rule ("the guide wins") that the owner's answer ("RULES §6 cites the UI/UX guide") did not state. Both are reasonable, but they are slightly more than was approved. Fix: match the U7 wording, or flag the two additions to the owner.

### Verified

- **Classes, not instances.** One rounding function serves rows, subtotals and shares. The scale is computed from every running total, so any operator with offsets is covered. The empty-due rule is a container rule on the class. The rail labels use one token in both packs. `uxPlanCard` is gone (0 references).
- **L5.** The rail labels now measure 8.25 to 10.56:1 in both packs, light and dark. The lattice starts below the last rail item (1,309–1,491 px against 710 px) and the footer has a solid backing.
- **U8.** The rail items and groups are unchanged; only colours changed.
- **U10.** With no override, all three operators load in `east-africa`. The switch to Neutral removes the attribute. Neutral is the fallback in `uxBrand()`.
- **U9.** A2 is a data contract only: the generator, the evaluator and the file shape. It invents no values, and it states correctly that the manifest declares the 2026-07..2026-10 span. `derived-values.json` has no `history`, so every slot reads "Trend not available yet" (seen in the shots).
- **Fold at 1280×720** (bottom of the first queue row):

  | Operator | Neutral, light/dark | East Africa, light | East Africa, dark |
  |---|---|---|---|
  | Lakeside | 650 | 668 | 674 |
  | Harvest | 687 | 705 | 711 |
  | Metro | 694 | 712 | 718 |

  Harvest after Recalculate now: 678 (Neutral), 696 (East Africa).
- **Recalculate now.** It is reachable by keyboard (gate) and has `role=status`. It names the person (the signed-in executive avatar). The Organisation settings copy reads "recalculated at the daily run, or at once when someone asks" ✓.
- **No horizontal scroll.** `scrollWidth` equals the viewport on all 36 Portfolio shots, with 0 page errors.

### Gates (reviewer-run, 853013d13)

| Gate | Result |
|---|---|
| render_text | 205 renders, 0 script errors |
| vocab_check | 0 hits |
| copy_check | 12,841 segments, 0 hits; COPY_PLANT=1: 4 hits, exit 1 |
| plan_switch_check | 777 passed, 0 failed |
| design_lint (rendered) | fails [], exit 0 |
| ux_interaction_check | 94 PASS, 0 FAIL |
| check_manifest.py | 4,474 passed, 5 failed (the known 5: brief readable, 4 × A1) |

### Residual risk

- Metro in East Africa dark at 1280×720 has 2 px of fold headroom, and the fold gate runs in light only.
- On a short page the lattice (30% of the rail, above a fixed 120 px fallback for `--rail-foot-h`) could reach the rail items; it is masked and faded.
- The Recalculate state is not persisted: a re-render returns the notice to pending. The Metro bridge title says cost and efficiency "explain" all $3,184 while $20 is "not attributed" (this predates the wave).

Shots: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/rereview-wave2c/` (scratch, not committed).
