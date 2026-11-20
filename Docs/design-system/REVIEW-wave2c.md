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
