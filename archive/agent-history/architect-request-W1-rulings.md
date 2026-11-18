# Architect request: W1-mini-Action-a/b pre-flight rulings

You are the AssetOps Architect. Read `.agent/post-W6-W1-preflight.md`: 58 points (G1–G6, Q1–Q52), each with defaults, covering both W1 cards in `.agent/post-W6-audit/fix-slices.md`. Use your earlier rulings as precedent: `.agent/post-W6-shell-rulings.md`, `.agent/post-W6-W2-cold-rulings.md`, `.agent/post-W6-W2-EV-rulings.md`, `.agent/post-W6-W3-estate-rulings.md`. Also read the register and lesson 15.

Write `.agent/post-W6-W1-rulings.md` with one numbered ruling per point. Each ruling accepts the default or states an alternative, with exact files, copy, behaviour, tests and recapture set. Split the rulings into W1-a and W1-b where the cards differ. Resolve these first, in a short cross-card section:

1. **One Site-timezone formatter across the post-W6 slices.** The shell branch `task/post-W6-shell` exports a helper from `LedgerSiteEvidence.tsx` (R170). W2-EV created `sites/siteTime.ts` (`siteTime` and `siteZoneLabel`), and W2-cold cherry-picked the same file. W1 needs one too. Name the single canonical helper. Say which branch converges onto it, and when (at rebase). Neither W2 nor shell has merged yet: shell merges first, then W1-a, W1-b, W2-EV, W2-cold.
2. **The extra files the builder found** (G2): `SiteWindowOverview.tsx`, `overviewSlots.tsx`, `OperatorShellLayout.tsx` (rail, B4-01), `findingPresentation.tsx`, `MiniAlternatives.tsx`, `SiteRecommendation.tsx`, `ConsequenceHistory.tsx`, `FindingConsequence.tsx`, `verificationCards.tsx` and `verificationWords.ts`. Authorize them or reassign them. Rail ownership matters because the rail is shared shell UI.
3. **Q12 / B3-06.** May the Finding page add a `getFindingFinancials` read per page? Give the exact copy.
4. **Q23 / B3-17.** Rule the paging design and confirm the caps (800/1400).
5. **Q6 / B2-29.** Give the crash-guard refusal copy, and say whether a global error boundary is wanted, now or registered for later.
6. **The genuinely open choices:**
   - B3-13: Site lens chips.
   - B2-08: Battery card link.
   - Whether Site tabs come off the Finding pages. The mock drops them; this overlaps B4-04 and B5-01.
   - The B3-15 target, `/financials` or `/portfolio`.
   - The B3-14 opportunity line link.
7. **Caps** flagged in advance (Finding "Where to look next", "What limits", finding-history Revision history at 390). Rule each once, per lesson 15.

Do not edit product code. Keep it tight.
