# UQ-FI-2 review (fresh Claude reviewer, 2026-11-13)

Branch `task/UQ-FI-1-2`, worktree `/opt/assetecon/AssetOpsV1-uqfi`, head `66ead2967`. Scope: UQ-FI-2 commits after `c66937b97` (`8acf207a5`, `fc2d007a3`, `ec7b22d56`, `82420ed3e`, `900925779`, `a56b29c70`) and the UQ-FI-3 merge resolution. Spec: rev 6 6.1/6.3, D-UQFI.4, .6, .8, .13-18.

## Verdict: ACCEPT WITH FINDINGS (M1 fixed on the branch or ruled held by the Architect before merge; Lows may ride)

## Checklist
- **Board row collapse (D-UQFI.4): OK.** `OutcomeBoard.tsx:196-216` groups only chip-less contributors whose whole line is the same gap string (exact match, so different reasons never merge). The fact is said once at the first contributor's place, every contributor is named in its own `li` with its `To` link, and nothing is dropped. The `outcomeBoard` test pins one group, both subjects, the link, the other-reason/chip/value lines, and every label.
- **Cold board untouched (D-UQFI.6): OK in practice.** The row collapse is not gated by Site type (Cold renders `OutcomeBoard`, `coldSiteViews.tsx:697`). Every Cold contributor in `site_outcomes/cold.py` carries a distinct fact, though, so nothing groups there. The six panels are untouched, and `coldSiteViews` pins no `GapGroup`.
- **One h1, P1-P8, per D-UQFI.13-17: OK** except the Kisiwa fuel Finding (M1). P2 keeps the Site name, P5 keeps "Productive-use headroom at {site}", P6 keeps "Findings", P7 keeps the Site name, and P1 asserts only the h1 (the card is not touched, D-UQFI.17).
- **P3 mini Finding (D-UQFI.18): OK.** The first sentence is now the header subtitle in both Finding frames, and `LifecycleSentence` keeps the rest plus the UNCONFIRMED cause. The test proves the sentence occurs exactly once and the h1 is the title, on SUPPORTED and UNCONFIRMED. The changed `siteFinding.test.tsx:696` assertion is faithful: SUPPORTED's lifecycle sentence is a single sentence, so after the move the body holds nothing and the disclosure item correctly goes.
- **`test/headline.ts` is non-vacuous.** It checks the count, exact text and position, and 15 of 16 callers pass exact text. The exception is `siteFuelFinding` with `/\S/` (M1).
- **`tools/uqfi-captures.mjs` is harmless.** It only spawns headless Chrome on a temporary profile and writes PNGs and `measure.json` to the given output directory. It makes no DB call and no POST. I did not run it.
- **Merge `66ead2967`: OK.** `OutcomeBoard.tsx` keeps the `GapGroup`/`groupGaps` imports and `contributorLines`, and also the `StatusPill` import and both `StatusPill` uses (lines 228 and 246). The register gains only R740, from UQ-FI-3.
- **No stray files.** UQ-FI-2's commits touch only the source and tests named above, `tools/uqfi-captures.mjs` and the packet. `v72/*` and `UQ-0-packet.md` are from the stacked UQ-0 lineage (already reviewed). The worktree is clean.

## Findings
- **M1 (Medium, acceptance gap): P3 is not built on the Kisiwa fuel Finding.**
  - Where: `shell/SiteAnalyticsFrames.tsx:2713` and `sites/__tests__/siteFuelFinding.test.tsx:189-196`.
  - Rev 6 6.1 P3 names "Kisiwa unexplained fuel (incl. `SiteFuelFindingFrame`)", demo step K. D-UQFI.18 lifts D-UQFI.8's hold ("Wire P3 now"). The fuel frame's h1 is still the Site name through `SitePageHeader`, although the read carries `lines.title`.
  - The test asserts `expectOneHeadline(/\S/)`, which any text passes, and its comment still says the work is "held by D-UQFI.8". The packet does not list this as not built.
  - Fix: move the fuel Finding's own title and first sentence into the header, with a test on the exact text. Alternatively, get an Architect ruling holding it and list it under "Not built".
- **L1 (Low): the P3 "gap set unchanged" assertion is vacuous.**
  - Where: `siteFinding.test.tsx:1241,1251`.
  - I ran a temporary copy of the test, since deleted: `bareGaps` is `[]` for both lifecycles, because the Finding page renders no `data-gap-id`. The test also compares the bare body with the frame, not before with after, and it never compares gap facts, which D-UQFI.18 asks for.
  - Low risk: the diff does not touch any gap line.
  - Fix: pin the gap-fact lines, for example the status strip's "not assessed" group and any `MissingClaim` text, against literal expected values.
- **L2 (Low): the packet is stale after `a56b29c70` and the merge.**
  - `.agent/UQ-FI-packet.md` still says that `SiteAnalyticsFrames.tsx` is untouched and that P3 is held.
  - Its checks are recorded at `82420ed3e`, not at the head.
  - It does not mention that the header subtitle on the Finding view is replaced.
  - Fix: update the P3 section, the "Not built" list (M1, captures) and the test evidence at the head.
- **L3 (Low): two register rows are stale, and the collapse has no row.**
  - R389: the `{Site} · generator support finding` subtitle no longer shows on the Finding view (`SiteAnalyticsFrames.tsx:1053`). The generic frame's `{Site} · finding` subtitle (`:865`) is also replaced.
  - R392: the disclosure no longer holds the lifecycle sentence. The `SiteFinding.tsx:980` branch `lifecycleRest(body) !== ""` is now always false for SUPPORTED.
  - The board-row collapse `MOCK DEVIATION` (`OutcomeBoard.tsx:280`) has no register row. The packet records this as a choice.
  - Fix: amend R389 and R392, and add the row or cite the rev 6 ruling that covers it.
- **L4 (Low): the generic frame's subtitle has no view guard.**
  - `SiteAnalyticsFrames.tsx:865` shows `headline?.sentence` on any view. The canonical frame (`:1053`) shows it on the Finding view only.
  - If that frame instance moves from the Finding view to a child view, the sentence stays in the header.
  - Fix: apply the same guard as `:1053`.
- **L5 (Low): stale comments.**
  - `miniDecisions.test.tsx:647` ("joins it once D-UQFI.8 lands"). That test still asserts only the title.
  - `siteFinding.test.tsx:630,698` ("the SUPPORTED lifecycle sentence" in the expander).

## Checks run (this reviewer, head `66ead2967`)
- vitest, 25 files: the 19 changed test files (estatePortfolio, estateRoots, s404SiteFindingIndex, siteDetailScreen, coldSiteViews, evSiteMoneyRoutes, fuelVerification, millVerification, miniDecisions, miniFuelRoutes, miniServiceRoutes, outcomeBoard, siteFinding, siteFuelFinding, sitePrices, gapGroup, statusPill, globalMaintenance, operationalRecords), of which 14 assert Site hrefs. I added 6 more Site-href files: sharedRange, rangeLink, overflowContainment, idxGapsFindingIndex, siteRangeTags, runCommitPanel. Result: 25 passed, 698 tests passed.
- `npx tsc --noEmit`: exit 0.
- Style ratchet: passed (rawHex 458). Style ratchet fixtures: 7/7.
- Missing-claim scan: passed (43 tagged, 10 baselined). Missing-claim fixtures: 26/26.
- Mock-deviation labels fixtures: 14/14.
- Not run, per the lane rules: check-all (for the coordinator), the captures and `measure.json` (layout evidence for the long-sentence header subtitle and the board group line is unverified), and the DB.

## Residual risk
- Whether any live board row actually repeats a gap line, and how a two-line sentence subtitle wraps at 1280 and 390 px, are unseen until the coordinator's captures.
