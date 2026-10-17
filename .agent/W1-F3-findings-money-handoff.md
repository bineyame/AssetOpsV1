# W1-F3 handoff: height phase (resume point)

Branch `task/W1-F3-findings-money`, worktree `AssetOpsV1-review`. Head `23671e6a` plus the packet/evidence commit. Main (final W1-F1) is merged in, and the tightened guard passes on all six screens.

## Done and green

- The six screens render exactly their v69 panels. Tests: `expectV69Panels` in stocked, empty and refused states, plus `src/test/__tests__/w1f3PanelGuard.test.ts` (non-vacuity).
- tsc is clean. `check-all` passes 10/10.
- Full suite at `23671e6a`: 2004/2005. The one failure is the known `siteFoundationChange` flake, which passes alone.
- Captures are in `.agent/W1-F3-evidence/part{5,8,9,10,10-emptyprice,11}`, with fixture commands per the walkthrough Parts 5/8/9/10/11. The capture agent used API 9120+, web 5620+ and CDP 9573. `s405 prepare` took about 11 min under load.
- The packet `.agent/W1-F3-findings-money-review-packet.md` is complete apart from the height rule.

## Next: the coordinator's 1.3x rule

Each panel at 1440 must be at most about 1.3x the mock's height for the same content shape. The approach:
- Show what the mock shows, e.g. the latest 3 rows plus a plain "Show all N" link.
- Put full IDs, digests and merged text in the closed disclosure.
- Keep honest-state lines visible in compact mock form, one line where possible.

The height table is in the packet. Measure again with `node tools/w1-fidelity-evidence.mjs` plus the scratchpad-style script, which reads each `evidence.json` and compares app vs mock panel `h` at 1440.

Targets and the main excess, by screen. "Mock" is the mock's height.

### finding-evidence (`sites/SiteFindingEvidence.tsx`)
- **Bundle: 903 px against mock 287.** Keep the input table (header plus 4 rows) and one compact state line (state · version · "Prepared example data" · as of). Move the version box, the stats key-values, the summary sentence and the three disclosures into one closed disclosure. The Coverage and Use columns are all "Not available": consider one gap line instead of two.
- **Lineage: 332 px against mock 100.** Replace the 5-card step strip with one line ("Every cited record traces … · all steps done") and the links. The step detail goes in the disclosure. A broken trail must still show its broken steps visibly: tests in `siteFindingEvidence.test.tsx` cover "broken trail marks only the broken steps".

### assumptions (`sites/SiteFinancials.tsx` FinancialAssumptions, ImpactPreview, PriceHistory)
- **Pair: 913-1187 px against mock 368.** Impact preview stretches to the height of its neighbour: use `align-items: start` on this pair, or cap it. Trim Financial assumptions to the price fields plus a compact strip. Move the schedule beyond the latest 3 rows and the exact version detail behind "Show all" or the disclosure.
- **Interpretation history: 514 px against mock 211.** Show 3 rows plus "Show all N".
- Fix the contradictory line "No fuel cost version had been recorded … at this moment" while price versions are listed. This was seen in the price-in-effect capture.

### finding-history (`sites/SiteFindingHistory.tsx`)
- **600-713 px against mock 243.** Show the latest 3 rows plus "Show all N". Fold the version box into one line. The 205-row test case needs a "Show all" path that still exposes every version, because tests assert all 205 in order and an incomplete marker.

### finding (`sites/SiteFinding.tsx`)
- **What happened: 436-477 px against mock 279.** The block timeline caption and legend go in the disclosure or onto one line.
- **Limits and Next pair: 389-468 px against mock 233.** Shorten the limits list to the mock's 2-3 bullets; the rest goes in the disclosure. "What to do next" needs a primary button, as in the mock.

### financials (`FindingConsequence.tsx` bridge, `SiteFinancials.tsx` AssumptionsInUse)
- **Bridge: 477-632 px against mock 288.** In the withheld case, a bullet and the "Open the recorded fuel cost" line render at body size; bring them to 12 px.
- **Assumptions in use: 485 px against mock 306.** Six key-values: keep price, effective and set-by; the rest go in the disclosure.

### sitefindings (`sites/SiteFindingIndex.tsx`)
- **Stocked: 560 px against mock 288.** Show 3 rows plus "Show all N". The day strip goes into the disclosure or a caption. The repeated placeholder "Main consequence" line becomes a single gap note.

## Rules to keep

- Every money gate, honest-state and fail-closed assertion stays. Justify any test changed for "Show all" in the packet.
- Commit before any proof mutation. Re-run the captures at the end, refresh the packet's height table and drop the fixtures.

## Observations outside scope (from the capture agent, for the coordinator)

- Page titles are generic, where the mock shows the site or Finding name.
- The Finding tabs are two-level; the mock has one row, and Alternatives is missing.
- The Scenarios sub-tab is missing on Financials.
- The sitefindings index has a date form where the mock has lens chips, and its columns differ.
- At 390, the left menu stacks about 600 px above the content (F1 shell).
