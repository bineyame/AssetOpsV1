# post-W6 W1-mini-Action-a: build handoff (code + focused tests done; capture and closeout pending)

Branch `task/post-W6-W1-a`, worktree `AssetOpsV1-review4`. Base 091045ed. Rulings: `.agent/post-W6-W1-rulings.md` (cross-card 1-5, 6-29).

## Commits

- `575fc2ab`: Q6/R178 Dispatch whole-window refusal.
- `b09a5c07`: Q1-Q4 Overview crumb, card links/tone, SLD link, Finding reason labels.
- `cf4266f0`: Q7-Q18 Finding sections, local time, cost card, links, Site Findings lenses/Manage; adds `sites/siteTime.ts` (blob identical to W2-EV 3c533f0f, `2b390038`) and the delegating `sites/findingTime.ts`.
- `2afb0fcf`: literal lens chips; navigation inventory (`tools/checks/navigation-truthfulness.ps1` expected tabs: Analysis -> Alternatives) and rail fixtures follow Q7/Q16.

## What landed, by ruling

- Q1: `SiteDetails.tsx` `siteHref` prop; `SiteDetailFrame.tsx` passes `siteDetailHref` -> `Sites › {site} › Overview`.
- Q2/Q48: `SiteWindowOverview.tsx` `ObjectiveCards(links)`: mini cards use `MetricCard link`; Dispatch footer link `dispatchDay(day)` (no revision), `assessment` border only when CURRENT, amber for CANDIDATE_AVOIDABLE else gray (`data-objective-card-tone`); Battery footer link to `links.assets`. New optional `WindowOverviewLinks.assets`/`sld`.
- Q3: Operating context `actions` -> `links.sld(summary.window.end)`.
- Q4: Finding reasons labelled `Finding reason {n}`.
- Q5: no code (measure in capture; inner scroll only if closed roles > 800 at 390).
- Q6: `performanceDispatchClient.ts` `isIntervalRevision` (WINDOW scope refused; unknown scope needs `segments[]` + `interval`); `PerformanceDispatch.tsx` `WindowView` returns `DispatchRefused name="not-interval"` before indexing, link `Open this day` drops `revision`/`block`.
- Q7/Q9/Q16 (frame, `SiteAnalyticsFrames.tsx` `CanonicalMiniFinding`): Analysis tab live (`siteFindingHref(...)&view=analysis`, current when `?view=analysis`); `LocalViews` removed from `SiteFinding.tsx` (implementation kept: Dispatch uses it); helper only on Alternatives and Recommendation (W1-b retires the Recommendation one, Q28); `Open site` (`data-finding-open-site={view}`) on every section; refused selection -> `Alternatives · Not available yet` tab + `[data-alternatives-finding-unavailable]` line below the row (loading keeps a plain `Alternatives` gap); Alternatives/Recommendation h1 = selection title, `Finding` on refusal; `SiteRecommendation.tsx` no longer sets `FINDING_NAME`. Evidence/History h1 `Finding` while loading/refused.
- Q8/Q13: money aside removed; `Inspect financial assumptions →` after the recommendation button (`links.assumptions`).
- Q10: status-bar period via `findingLocalPeriod` (local, closed `UTC time` detail with both instants; `(site time zone not recorded)` on fallback). Prose periods stay labelled UTC (scope: status period only).
- Q11: `Inspect evidence →` in What happened panel head.
- Q12: `SiteFinding` `financials` prop (`FindingCostClient`); `SiteFindingFrame` optional `financials` defaulting to `DEFAULT_FINANCIALS`. Priced only for loaded, same-revision, `PRICED` + `currentness CURRENT` + amount + currency (the `FindingBridge` gate); else `Not available` with a state reason (`data-finding-cost`). Keyed by revision so a stale answer is never shown; no read without a resolved revision.
- Q14: foot link `See analysis and alternatives →` (`links.alternatives`). Q15: Where-to-look `Alternatives` item between Evidence and History.
- Q17: History `Time ({zone})`, cells `D Mon · HH:MM`, UTC in `title` and `Version recorded (UTC)` detail row; `timeZone` passed from the frame.
- Q18: `SiteFindingIndex.tsx` lens row above the strip (new `LensRow` context; opportunity helper stays in the panel controls, since moving it trips the leading-element guard), `Manage in Findings →` in the strip (`links.manage = FINDINGS_PATH`), `LensChips` optional `hrefs` (unused, literal unbuilt chips).
- Guard: `test/panelStructure.ts` LEADING_SELECTOR admits `[data-alternatives-finding-unavailable]` (Q16 ruled line).

## Hunks W2-EV / W2-cold rebase over (G4)

`SiteAnalyticsFrames.tsx`: `SiteFindingFrame` props (+`financials`), `CanonicalMiniFinding` (sections, title effect, header actions, `FindingSections` call, refused line, SiteFinding/History props), `SiteFindingsFrame` mini `links.manage`. `SiteFindingIndex.tsx`: `LensChips`/`LiveLens`/`OpportunityHelper`, `View` (lenses + Manage), provider block. W2 branches drop their own `siteTime.ts` (identical blob) and run mini regression (`miniDecisions`, `s404SiteFindingIndex`, `siteFinding*`).

## Tests (focused, all green at 2afb0fcf; each new test failed with its fix reverted)

performanceDispatch 44, s5SiteWindowOverview + siteDetailScreen + s502 166, siteFinding 67, siteFindingEvidence 46, siteFindingHistory, miniDecisions, w1f4RecommendationStructure, s404 37, t028Screens, evidenceClaimLimit, findingTime 5, estateRoots, evDepth. Proofs: Dispatch 2 fail without fix; Overview 9 fail; Finding/Index 33 fail. `tsc` clean; `check-architecture.ps1` passed; check-all at de2da2fc: all 11 guards passed.

## Remaining

1. DONE: main (shell 4fc39160, W3-estate d9a73b80) merged cleanly; `siteTime.ts` blob still `2b390038`. `de2da2fc`: shell's `usableZone`/`zoneAbbreviation`/`selectedLocalDay`/`measuredTime` in `LedgerSiteEvidence.tsx` now delegate to `siteTime.ts` (+ `findingTime.ts`); a 3-zone EAT label set (Asmara, Djibouti, Mogadishu) stays in the wrapper because `siteTime.ts` must stay verbatim; W2-EV may fold it into the canonical table. `measuredTime.test.ts` + delegation test, `siteAction.test.tsx` (title contract) green. New register rows, if any, start at R383. Backend suite: not required (coordinator).
2. Held for clearance: full vitest, production build, real-Postgres backend suite (frontend-only slice; confirm whether it is required), captures: all 88 indexed pairs (mini 12, evidence-analysis 16, dispatch 14, finding 12, finding-evidence 8, finding-history 10, sitefindings 16) + Q40 representatives (alternatives, SiteDetails crumb, cold/EV Finding representative), cap proofs (Where to look 650/1000, What limits 450/800, Revision history 850/2000, Dispatch Selected-block 390 750, Q5 400/800 and 1200/1800, What happened 600). Q11 link moves to the panel foot and Q15 Related Findings goes behind its count disclosure only if measured over cap.
3. Closeout: review packet, CODE_STATE entry, ACTIVE_CONTEXT, narrow R21 (Finding Analysis no longer unavailable), register the global error boundary follow-up (Q47) as a backlog item, register rows per G1.

## Known deviations / risks

- Q10 local time is the status period only; panel prose periods remain labelled UTC.
- Cost card also requires `currentness CURRENT` (FindingBridge's gate), so a historical PRICED version reads Not available.
- `void onTitle` in `SiteRecommendation.tsx` keeps the prop for callers.
