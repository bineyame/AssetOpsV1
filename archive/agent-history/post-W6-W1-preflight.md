# Post-W6 W1-mini-Action-a / -b: builder pre-flight

Branch `task/post-W6-W1-a` at main `dcf5b086`. Pre-flight only; no product code. Sources: both W1 cards, the
sequencing rules, the Architect rulings and the cap docket in `.agent/post-W6-audit/fix-slices.md`; register rows
R156-R230; classification rows; batch-02 to batch-05 ledgers; v69 mock (`frontend/mockups/v69/index.html`, cited
as `mock:<line>`); diffs of `task/post-W6-shell`, `task/post-W6-W2-EV` and `task/post-W6-W2-cold` against main.
Each code anchor is relative to `frontend/src/`. 58 points (G1-G6, Q1-Q52; Q44-Q52 restate decisions for the docket). Each one gives a **default** that the builder takes
unless the Architect rules otherwise.

## 0. Global questions (both cards)

- **G1. Which part of a mixed ledger row is the D3.** Several rows mix (a), (b) and (c) proposals: B2-08, B2-10, B3-03 to B3-09, B3-12 to B3-18, B4-21, B4-22, B5-07 and B5-08. The classification lists only "D3". **Default:** follow shell Q3 precedent. Only the (c) parts are D3. The (a) height parts are governed by the cap docket. The (b) parts stay D1/D2 and are recorded in the register as those dispositions. The parts I treat as D3 are listed per ID below.
- **G2. Card file lists miss files the fixes live in.** **Default:** allow these extra files. Each is the only home of the defect.
  - `sites/SiteWindowOverview.tsx` and `sites/overviewSlots.tsx` (B2-08, B2-10, B2-15). `SiteOverview.tsx` only dispatches to `SiteWindowOverview` (SiteOverview.tsx:222-231).
  - `sites/SiteRecommendation.tsx` (B3-10/B4-10 title).
  - `sites/MiniAlternatives.tsx` (B3-10 tab label constant :32).
  - `sites/findingPresentation.tsx` (B3-01 LocalViews :384-411).
  - `sites/ConsequenceHistory.tsx` and `sites/FindingConsequence.tsx` (B3-15/16/17 strip, Trade-offs and history live there, not in SiteFinancials.tsx).
  - `shell/OperatorShellLayout.tsx` (B4-01 rail :70).
  - `sites/verificationCards.tsx` (B5-07 KPI note :143) and `sites/verificationWords.ts` (B4-22).
  - The B2-15 key fix may alternatively touch `ui/ProductStatus.tsx:198`. The default keeps it local (unique labels in SiteWindowOverview).
- **G3. Site-timezone helper.** B3-04 and B3-12 need Site-local time with UTC in a disclosure (Time-basis ruling). Shell (merges first) exports `usableZone`, `zoneAbbreviation`, `selectedLocalDay` and `measuredTime` from `sites/LedgerSiteEvidence.tsx`. W2-EV and W2-cold each add an identical `sites/siteTime.ts` (`siteTime`, `siteZoneLabel`), which lands after W1. W2-cold ruling 6 makes W2-EV the owner of "the shared signature". **Default:** W1 reuses shell's exported helpers from LedgerSiteEvidence and adds no third formatter. W2-EV may later fold both into `siteTime.ts`. The alternative is for W1 to create `siteTime.ts` now with W2's exact signature; that needs an Architect ruling because W2-EV owns it.
- **G4. Order and rebase.** W1-a starts only after shell merges. Both cards edit `shell/SiteAnalyticsFrames.tsx`.
  - Shell rewrites the SiteActionFrame breadcrumb hunk (:1656-1690). W1-b's tab-row and Open-site edits are adjacent to it.
  - W2-EV wraps the mini branch of `SiteFindingsFrame` in an EV ternary. W1-a's lens/strip/Manage edits are in that branch.
  - Both W2 branches export `LensChips` from `sites/SiteFindingIndex.tsx` and reuse it for cold/EV.
  - **Default:** W1 keeps the `LensChips` signature backward-compatible: an optional prop for live lens hrefs, defaulting to today's output. That way W2's reuse still compiles. I will name in the W1-a handoff exactly which hunks W2 must rebase over.
- **G5. Title format is a contract.** Shell's `w1ActionCode(title)` parses `{code} · Battery reserve trial` from SiteAction.tsx:170. **Default:** no W1 edit changes that string. A unit test pins it (siteAction.test.tsx :445/:1018/:1087 already do).
- **G6. Split of SiteFindingIndex between cards.** B3-13 (W1-a) covers lens chips, strip and Manage in Findings. B3-14 (W1-b) covers the table. W2-cold ruling 1 says "W1-b owns its mini Finding/index hunks". **Default:** W1-a edits only `View`/`LensChips`/the strip, and W1-b edits only the table rows.

## 1. W1-mini-Action-a (18 IDs)

### Mini Overview

- **Q1 B2-07 R156 breadcrumb.**
  - Today: `Sites › {site}` (SiteDetails.tsx:231 with SiteDetailFrame.tsx:140). Mock: `Sites › Kobo Mini-grid › Overview` (mock:1117-1124, section `Overview` at mock:409).
  - **Default:** append the current leaf `Overview` and make the site crumb a link. Is this mini only, or every Site type that shares `SiteDetails`? Default: every Site that renders SiteDetails, since shared code reaches it. Cold/EV overviews keep their own frames.
  - Test: one `sitesIndexRoute`/overview crumb assertion.
- **Q2 B2-08 R157 objective cards.** D3 parts: the link sits in the card footer slot on all cards that have a mounted destination, Dispatch gets a link, and the status-tone top border.
  - **Default:**
    - Move "View detail →" from `note` into `MetricCard link` (V69Layout.tsx:52) for Service, Fuel and Renewable.
    - Add a Dispatch link to `sitePerformanceHref(id,"dispatch")` with the selected `day`.
    - Battery has no condition read on the Overview, so it stays D1 with no link. The alternative is a link to `siteAssetsHref`; the mock links it to `asset`. I need a ruling on whether to link it even though there is no value.
    - Tone border: use `assessment` + tone **only from the stored dispatch classification the card already shows**: amber for "Needs attention"/possibly avoidable, gray otherwise. Cards with no read get no border.
    - Values ("Assessed"/"Not available") stay D1.
  - Copy: `View detail →`.
- **Q3 B2-10 R159 SLD link.** D3 part: only the missing panel-head link. The lanes stay D1 under the W1-F5b ruling.
  - **Default:** in the `actions` slot of the Operating context panel (overviewSlots.tsx:56-63, fed from SiteWindowOverview.tsx:1216-1224), add `Single line diagram →` to `siteFoundationViewHref(id,"sld", at)`.
  - Which `at`? Default: the selected window's end (`known_at` equivalent). If the helper has no time argument, use the bare route.
- **Q4 B2-15 R164 duplicate key.**
  - `status_reasons` (SiteWindowOverview.tsx:302) and `reasonReferences("Recorded reason", f.reasons)` (:304, :211-212) both produce `Recorded reason {n}`, and they are keyed by label (ProductStatus.tsx:198).
  - Rows can drop or duplicate. **Default:** prefix the second list's labels distinctly: `Recorded reason {n}` for the assessment and `Finding reason {n}` for the Finding. This changes copy. The alternative is to keep the labels and key by `${source}:${i}`. Which?
  - Add the failed-day key test the card asks for, asserting no React duplicate-key warning (spy `console.error`) and both rows present.

### Evidence Analysis

- **Q5 B2-22 R171 heights.** The docket caps are 400/800 for How each limit is set and 1200/1800 for Accepted records. The ledger peaks are 311 (refused, 1440), 542 (390) and 910/1235 (record opened). All of them fit.
  - **Default:** no layout change. B2-22 closes on a worst-case remeasure: selected + refused + five 160-character role rows (pure fixture) at both widths.
  - Lesson 15 flag: the selected state with 5 roles × open "n readings" disclosures is user-expanded, so it is exempt. The closed selected state at 390 with long role names is the miss risk. If it exceeds 800, the default is to wrap the role table in an inner scroll.
  - Overlap: shell rewrites `LedgerSiteEvidence.tsx` (R170 measured-time column). W1-a rebases on it.

### Dispatch

- **Q6 B2-29 R178 crash (Medium).**
  - `WindowView` reads `selected.result.segments[blockIndex]` (PerformanceDispatch.tsx:403). `getRevision` (:387) loads any revision, and `isRevision` (:219-224) never checks the shape. A window-assessment id has no `result.segments`, so `undefined[1]` throws, and there is no ErrorBoundary anywhere in `src`.
  - **Default:**
    - (a) Narrow `isRevision`, or add `isIntervalRevision`, requiring `Array.isArray(result.segments)`. Also check `scope` when present (performanceDispatchClient.ts:101). I need the exact scope literals; default is to rely on the segments shape only.
    - (b) Render the existing `DispatchRefused` with the title **"This assessment cannot be shown as 15-minute blocks"** and the sentence **"The address names a whole-window assessment, not a 15-minute interval result for this day. Open the day without a selected revision."** plus a link to the day.
    - (c) Do not add a global ErrorBoundary. That is out of card scope; flag it as residual risk.
  - Tests: a component test with a window-shaped revision gives the refusal and no throw. A second test covers a wrong-day revision. The card asks for "wrong-revision refusal" cases. Today a revision from another day shows as "stored" (`PinnedNotice`, :911). Is that a D3 refusal too, or is the stored-other-day note acceptable? Default: keep it. It is honest and labelled. Only shape mismatches refuse.
  - Recapture: the `window-id-as-revision` pair at both widths. The dispatch Selected-block cap (390) is 750.

### Finding (Overview / Evidence / History)

- **Q7 B3-01 R184 one section row; Analysis live.**
  - **Default:**
    - Remove `LocalViews` from SiteFinding.tsx:132/:144.
    - Change the `analysis` section at SiteAnalyticsFrames.tsx:846 from `unavailable: true` to a live link to the existing `?view=analysis` of the Finding root, carrying the selected revision.
    - Drop `ANALYSIS_HELPER_SECTION` from Evidence and History (:921-936) and from Recommendation (B4-10, W1-b).
  - The Analysis tab's `aria-current` is set when `view=analysis`.
  - Architect: narrow R21 (the "Not available yet" entries) so it no longer claims Finding Analysis. That is a register edit, done in the closeout.
  - Tests that break: miniDecisions.test.tsx :679, :698, :737, :743, :1078 (Analysis · Not available yet and helper counts), and the siteFinding LocalViews assertions. Update them to the live tab.
- **Q8 B3-02 R185 money link.** The classification chose D3, which means "move to the mock position".
  - **Default:**
    - Remove the 7th aside (SiteAnalyticsFrames.tsx:913-919) from all Finding sections.
    - Add `Inspect financial assumptions →` in What to do next after the recommendation button (mock:460), to `siteFinancialAssumptionsHref` (operatorSiteRoutes.ts:229).
  - Then is "What this finding means in money" (to Financials with findingId/revisionId) lost? The mock has no such link on the Finding; the money reaches the Finding through the cost card (Q12). Default: drop it.
  - Tests: `[data-finding-financials-link]` in miniDecisions :879/:899, siteFindingEvidence :584, siteFindingHistory :459 and w1f4RecommendationStructure :95 flip to absence assertions.
- **Q9 B3-03 R186 Open site.** D3 part: the header action only. Code is D1 (R65/R74) and the child subtitle is D2.
  - **Default:** extend the `actions` at SiteAnalyticsFrames.tsx:887-895 from Alternatives-only to every Finding section (overview, evidence, history, alternatives, recommendation). B4-05 needs the recommendation case.
  - Element: a `Link className="button"` like the domain Action (:1446-1455) and Alternatives. Copy: `Open site`.
- **Q10 B3-04 R187 status-strip time zone.**
  - `periodWords` (SiteFinding.tsx:540-546) gives `{day} HH:MM–HH:MM UTC`. **Default:** Site-local primary, e.g. `2026-10-15 15:00–16:30 EAT`, using `SiteSummary.timezone` (siteReadModel.ts:49). Exact UTC goes in a closed disclosure or a `title`.
  - Which? Default: a small `<details>` "UTC time", consistent with the Time-basis ruling's "UTC available in a disclosure". Helper per G3.
  - The chips stay D1.
- **Q11 B3-05 R188 Inspect evidence.**
  - **Default:** in the What happened panel head (SiteFinding.tsx:605-609 `actions`), add `Inspect evidence →` to the Finding Evidence section with the selected revision.
  - Height: at 390 the panel head may wrap. The cap is 600 against a peak of 534 at 390. Lesson 15: the late-stale case at 1.41x. I cannot tell from the ledger whether that peak is inside 534; the remeasure decides.
- **Q12 B3-06 R189 cost card (data source).**
  - The Finding read has no money. `FinancialsClient.getFindingFinancials(site, finding, revisionId)` (financialsClient.ts:491-493) returns `consequence {state, amount{low,high}, currency}` for the exact revision.
  - **Default:**
    - SiteFinding gets an optional `financials` client prop. The frame defaults it to the module `DEFAULT_FINANCIALS` (SiteAnalyticsFrames.tsx:1009), so no App edit is needed.
    - The cost card shows `range(low, high, currency)` labelled **"Cost exposure"**, with note **"Bounded for this Finding version; see Financials."**, but only when `state === "PRICED"` for the resolved revision.
    - Withheld, unpriced or failed reads keep "Not available" with the reason word from the consequence state.
    - The card link goes to the Financials overview for that finding and revision.
  - This adds one read per Finding page. Is that acceptable? The alternative is to leave the card D1 and register it. Default: build it, because classification says D3 (D-2026-10-04).
  - Tests: priced, withheld, read-failed and wrong-revision cases (pure fake client).
- **Q13 B3-07 R190.** This is the same link as Q8 (`Inspect financial assumptions →`). The heading is D1/D4. **Default:** Q8 closes both. Test it once.
- **Q14 B3-08 R191 limits link.**
  - **Default:** add the panel-head or foot link `See analysis and alternatives →` (mock:460) to the Alternatives section (`siteFindingAlternativesHref`, operatorSiteRoutes.ts:298).
  - What about the existing closed disclosure "Access and review context" (:784)? Default: keep it. It holds real dev-access/lifecycle text, so it is D2 extra content and not removed.
  - Alternatively, the link could point to the Analysis view. The mock wording names both; the default target is Alternatives, because Analysis gets its own live tab (Q7).
  - Cap 400/550 against peaks of 318/467. The ledger's 1.91x at 390 (s408 priced) is likely near 550. Lesson 15 flag: measure s408 priced first.
- **Q15 B3-09 R192 Alternatives item.**
  - **Default:** add a Where-to-look-next item `Alternatives` with the mock wording (mock:461) to `siteFindingAlternativesHref(site, finding, resolvedRevision)`. Order: Analysis, Evidence, Alternatives, History, Dispatch day, Related Findings.
  - Linked action stays D1. Copy for the item description: mock:461 text. Builder will quote it.
  - Cap flag (lesson 15): 390 cap 750, peak 628. One more item adds about 60-80 px, giving a predicted 690-710 with no margin for long related-Finding titles. If it exceeds 750, the default is to collapse Related Findings behind its existing disclosure count.
- **Q16 B3-10 R193 refused copy and tab label.**
  - **Default:**
    - On refused, not-found or loading reads, Evidence and History use the h1 `Finding` (same as root), not `FINDING_NAME` (SiteFindingEvidence.tsx:48/:241, SiteFindingHistory.tsx:29/:131).
    - The Alternatives tab, when `resolved === null` (SiteAnalyticsFrames.tsx:848-849), becomes the short disabled label `Alternatives · Not available yet` with the long sentence moved below the row (the existing body note :939-942).
    - Should `SiteRecommendation.tsx:117` `onTitle(FINDING_NAME)` also become record-driven? Default: yes, on refused only.
  - Tests: siteFindingEvidence.test.tsx:1041 and w1f4RecommendationStructure :79 ("Generator support review"); `ALTERNATIVES_FINDING_UNAVAILABLE` in miniDecisions :664/:946, siteFindingEvidence :594 and t028Screens :220.
- **Q17 B3-12 R195 history time.**
  - "Version recorded" uses `stamp()` (dispatchWords.ts:150-156), which is UTC with no label. Mock: column `Time`, `6 Oct · 16:00` (mock:721-722).
  - **Default:** rename the column to `Time ({zone})` and render Site-local `D Mon · HH:MM` (shell `measuredTime` style; seconds are not needed for revisions). The UTC instant goes in `title` and in the existing technical disclosure.
  - Is renaming the header to `Time` itself in scope (the ledger also lists the label)? Default: yes, as `Time (EAT)`.
  - Test: siteFindingHistory.test.tsx:338.
  - Cap flag: 1500 at 390 against a peak of 1329. The ledger had 4.25x (version 1). If that is the 1329, there is 171 px of margin, and five long related-Finding rows may exceed it. Measure the version-1 case first.
- **Q18 B3-13 R196 Site Findings strip.** D3 parts: `Manage in Findings →` (mock:330) and site lens chips.
  - **Default:**
    - Add `Manage in Findings →` to `/findings` in the scope strip.
    - Lens chips: render them **above** the strip, matching the mock order (mock:329-332). Chips/order was ruled (a) D2, but moving them is cheap and lowers the panel height. Do I move them, or keep the W1-F5b placement? Default: move.
    - Cost/Risks/Opportunities become links to `/findings/cost|risks|opportunities` (App.tsx:488-491) with a Site filter? The estate lens has no Site filter today. **Default: keep them "Not available yet" (D5)** and only add Manage in Findings. Linking to unfiltered estate lenses would misstate the scope. This is the classification's open "(b) D5 or (c) D3 if Site-scoped" choice, and I need the Architect to pick.
  - Overlap: G4, since W2 reuses LensChips.
  - Tests: s404SiteFindingIndex.test.tsx order assertions.

## 2. W1-mini-Action-b (18 IDs)

### Site Findings, Financials, Assumptions

- **Q19 B3-14 R197 table.** D3 parts: the Domain link and the opportunity-line link.
  - **Default:** the Domain cell (SiteFindingIndex.tsx:475, hard-coded `Dispatch`) links to `sitePerformanceHref(site,"dispatch")` with that row's day (and revision if present). Add `dispatch` to `FindingIndexLinks` (:98-103), wired at SiteAnalyticsFrames.tsx:491-500.
  - Panel description: should the mock's `Domain links back to the Performance view that produced the finding` (mock:331) be added? Default: yes, as the panel description.
  - Test: s404SiteFindingIndex.test.tsx:304.
- **Q20 B3-14 opportunity line.**
  - `siteOpportunityHref` needs an `opportunityId`, and the index has none. The helper text says "open the renewable evaluation". **Default:** link the words `open the renewable evaluation` to `sitePerformanceHref(site,"renewable")`, which is mounted and is the W4-02 page whose CTA leads to the Opportunity.
  - Overlap: W2 reuses the LensChips helper flag; keep `opportunityHelper` semantics.
  - Test: miniDecisions.test.tsx:1627-1629.
- **Q21 B3-15 R198 Portfolio roll-up.**
  - The mock link `Portfolio roll-up →` targets `globalfinancials` (mock:478), which is `/financials` (FINANCIALS_PATH), **not** `/portfolio` as the ledger says. **Default:** link to `/financials` in `FinancialsStatusBar` (FindingConsequence.tsx:498-514).
  - That bar is shared with `FindingConsequence.tsx:759`. Which pages reach that? I will confirm, and recapture them if they are outside the card.
  - KPI/rows stay D1.
- **Q22 B3-16 R199 Inspect technical basis.**
  - The mock's `claim('Inspect technical basis')` opens a claim-evidence drawer (mock:179/:481); the app has no drawer. **Default:** a route link `Inspect technical basis →` to the Dispatch analysis view (`/performance/dispatch?view=analysis&day=…&revision=…`) for the Finding revision's day, placed in TradeoffsPanel (FindingConsequence.tsx:565-594).
  - Cap 450 at 390 against a peak of 387. One link line, about 25 px, fits.
- **Q23 B3-17 R200 Interpretation history paging (Medium).**
  - The ruling says: at most three compact rows per default page, an accessible Next/Previous control, and the full selected record on demand. Caps 800/1400.
  - Today: `ConsequenceHistoryPanel` (ConsequenceHistory.tsx:162-262) has "Back to newest"/"Show earlier versions" with `history_limit` (server default 25; SiteFinancials.tsx:402-413). There is also a second `PriceHistory` table (SiteFinancials.tsx:733-833) with latest 3 + ShowAll + "Show later versions".
  - **Default:**
    - (a) The client requests `history_limit=3` when the URL has none.
    - (b) Rename the controls to `Previous versions` / `Next versions` (keep the data attributes).
    - (c) Each row shows only Version / Fuel price / Recorded amount / Status in one line. Source and multi-line details go into a per-row "Show this version" disclosure (on demand).
    - (d) The PriceHistory table moves into one closed disclosure, `Price versions recorded ({n})`, below the history table, so it does not count toward the closed height.
  - Is (d) acceptable, or must PriceHistory also be paged to 3? Default: (d), since its rows are already latest-3.
  - Lesson 15: five 160-character sources inside closed disclosures stay a single line. Predicted about 500/900. Measure the T3 7-row and mixed cases first.
  - Tests: siteFinancials.test.tsx :1110/:1118/:1259 change.
- **Q24 B3-18 R201 Return link.** **Default:** add `Return to financial overview` (a link to `siteFinancialsHref`) in the Financial assumptions form footer (mock:487), beside the disabled edit. The notice position is D2 and is not moved.

### Recommendation and Action frames ("all six")

- **Q25 B4-01 R202 rail.**
  - `railActiveLabel` (OperatorShellLayout.tsx:70) only maps `/sites/:id/actions/...` to Actions. **Default:** add `/sites/:id/findings/:fid(/...)` to `Findings` for all Finding sections, not only Recommendation, because the mock root is Findings for finding, evidence, history and recommendation.
  - Does this exceed B4-01 (Recommendation only)? Default: apply it to all Finding child routes, recapture batch-03 Finding screens, and ask whether W1-a should own it instead (G2 file). Also confirm cold/EV Finding routes get the same rail; they share the path pattern.
- **Q26 B4-04 R204 + B5-01 R223 Site tab row.**
  - **Default:** remove `<OperatorSiteTabs current="Findings">` from SiteActionFrame (SiteAnalyticsFrames.tsx:1675) and from the Recommendation view (:899, keep it on Finding overview, evidence, history and alternatives). The mock shows no Site tabs for non-Sites roots (mock:1091-1114).
  - Is the Finding section row (overview, evidence, history) also in B4-04's scope? No, B4 is "all six" = Recommendation + 5 Action. But the mock also drops Site tabs on finding screens (root Findings). Default: leave the Finding pages unchanged, since they are not in the card, and flag it for the Architect.
  - B5-01's breadcrumb part is shell R203 (already on the shell branch).
  - Tests: a no-Site-tabs assertion on all six views. Existing tests that find `[data-site-tab]` on Action pages will break; I will list them at build time.
- **Q27 B4-05 R205 Open site.**
  - **Default:** in the SiteActionFrame PageHeader (:1670-1674), `actions={<Link className="button" to={siteDetailHref(site)}>Open site</Link>}`. For Recommendation this is covered by Q9's extension.
  - Who owns the Recommendation Open site if W1-a ships Q9 for all Finding sections? Default: W1-a, and W1-b only tests it.
- **Q28 B4-10 R209 helper line.** **Default:** remove `ANALYSIS_HELPER_SECTION` (SiteAnalyticsFrames.tsx:612, passed at :930-936). After Q7 it has no users; delete the constant. Test: miniDecisions :737/:861-862.

### Action pages

- **Q29 B4-19 R218 RESOLVED fall-through (defect).**
  - `ActionEventKind` (actionClient.ts:212) omits `RESOLVED`/`RESOLUTION_WITHDRAWN`, though backend `lifecycle.py:25-26` emits them. `EventDetails` (SiteAction.tsx:1273-1339) falls through at :1338 to "Trial accepted; nothing on the Site changed." `EVENT_BADGE` (:697-702) and `EVENT_WORDS` (actionPresentation.tsx:55-60) lack them.
  - `EventTable` (:1134-1144) concatenates events, outcomes and `resolution_events`, so the same resolution renders twice (keys `event.id` and `r.id` collide).
  - **Default:**
    - (a) Widen the type and add words and badges:
      - RESOLVED: **"Resolved"**, meaning **"The evaluator settled the outcome for this Action."**
      - RESOLUTION_WITHDRAWN: **"Resolution withdrawn"**, meaning **"The evaluator withdrew an earlier outcome; the Action is open for a new outcome."**
      - An unknown kind gets the meaning **"Recorded event; its meaning is not shown in this build."** It never falls through to ACCEPTED.
    - (b) De-duplicate: drop an Action event of kind RESOLVED/RESOLUTION_WITHDRAWN when a `resolution_events` row has the same id. Keep the resolution row, which has more detail. Key all rows by `${source}:${id}`.
    - (c) Counts: see Q30.
  - Exact copy is needed from the Architect if the defaults are not accepted.
  - Test: the verified-replay fixture (3 events incl. RESOLVED + 1 resolution) renders 1 Resolved row, no duplicate-key warning, and consistent counts.
- **Q30 B4-20 R219 history count copy.**
  - The chip `Every recorded event` and the sentence "everything recorded … N of N events" (SiteAction.tsx:982-1004, :428/:434) sit beside the latest-3 rows. "Show all {total}" (:1023/:1033) counts events + outcomes + resolutions.
  - **Default:**
    - Chip: `Latest at read time`.
    - Sentence: **"Showing the latest {shown} of {total} recorded entries; show all to see every entry."**
    - `{total}` is the de-duplicated union used by "Show all {total} entries".
    - The server's "N of M events" note stays only inside the technical disclosure.
  - Tests: siteAction.test.tsx :749 (`events.length + 4`) and :931 change.
- **Q31 B4-21 R220 Success criteria typography.**
  - D3 part: the row-header weight and line-height only. Rows/notes stay D2.
  - **Default:** keep `<th scope="row">` for accessibility (SiteActionVerification.tsx:1343-1362) with a scoped class `font-weight: 400` and the table line-height token. CSS belongs in a W1 component stylesheet, not `ui/primitives.css`, which shell owns. Is it OK to add a scoped rule to the existing verification CSS file after shell merges? Default: yes.
- **Q32 B4-22 R221 Evidence requirements.**
  - D3 parts: the tone and the duplicate text.
  - **Default:**
    - `requirementTone(ok===true)` gives `info` (blue) instead of `pass` (SiteActionVerification.tsx:1657-1662), matching mock:727 `badge('Available','blue')`.
    - The source cell shows `sourceWords(x)` once (de-duplicate :1588/:1591/:1622 "Registered Lab trial data / Registered Lab trial data").
  - Does the tone change also apply to the verification screen's "Available" chips? Default: yes, wherever `requirementTone` is used.
  - Cap 450/800 against peaks of 373/615. Fine. The 390 >2x ratio is inside the cap.
- **Q33 B4-24 R222 unknown section and `/overview`.**
  - **Default:**
    - (a) `/actions/:id/overview` resolves to Overview (SiteAnalyticsFrames.tsx:1619-1625; drop the `!== "overview"` exclusion). Should the canonical link stay the bare path? Default: yes.
    - (b) Unknown section keeps the refusal. Title stays `Action` (no record asserted), but the Action sub-tab row is kept so the user can navigate.
    - Copy: **"This Action has no section called '{segment}'. Open the Action overview."** with a link.
  - The 14 px sentence and the 325 px header belong to shell (B1-07/B1-02); I will not touch them.
  - Test: siteAction.test.tsx:887.

### Verification and Site Work

- **Q34 B5-07 R228 selector conflict.**
  - **Default:** Outcome evidence renders the conflict sentence once. Pass `historyGap` only when it differs from `gap` (SiteActionVerification.tsx:410-416, :1176/:1215-1217).
  - The KPI note becomes **"Not read: the address names conflicting selections."** instead of "The verification read failed" (verificationCards.tsx:143). To do that, `VerificationMetricCards` gets a `reason` prop.
  - Tests: siteActionVerification :302/:310 and w1f4VerificationStructure :145.
- **Q35 B5-08 R229 unknown Action subtitle.** D3 part: the subtitle only. The three refusal panels stay D2.
  - **Default:** the PageHeader subtitle (SiteAnalyticsFrames.tsx:1673) is `{site} · an action raised from a finding` only when the Action read loaded. Otherwise it is `{site}`.
  - This needs an `onLoaded`/state flag from SiteAction. Default: derive it from the reported title, since shell's `w1ActionCode(title) !== null` signals a loaded record. That avoids a new callback.
  - Test: unknown Action shows no "raised from a finding" text.
- **Q36 B5-09 R230 Manage in Actions.**
  - **Default:** add `Manage in Actions →` to `/actions` in the SiteWorkActions scope strip (mock:341/:644). Delete the stale docblock (SiteWorkActions.tsx:22-23).
  - Flip the negative test w1f4ChangesWorkStructure.test.tsx:152-153 (mini). Keep evWorkActions.test.tsx:204 (EV, other card).
  - Overlap: shell edits `siteWorkCases.tsx` count strip, but SiteWorkActions is a separate file. W5/W6 Work cards may add the same link to cold/EV. Not in this card.

## 3. Cap docket check (lesson 15)

Likely misses and predictions, before any capture:

| Screen / panel | Width | Cap | Peak | Risk from W1 change | Default if over |
| --- | ---: | ---: | ---: | --- | --- |
| assumptions / Interpretation history | 1440 / 390 | 800 / 1400 | 1823 / 4572 | Q23 paging is the fix | per-row disclosure; Architect if still over |
| finding / Where to look next | 390 | 750 | 628 | +1 item (Q15) | Related Findings behind its disclosure |
| finding / What limits | 390 | 550 | 467 (ledger s408 1.91x) | +1 link (Q14) | wrap link inline with last bullet |
| finding-history / Revision history | 390 | 1500 | 1329 | time format longer; 5 long related rows | move Related Findings out of panel into closed disclosure |
| finding / What happened | 390 | 600 | 534 | head link wrap (Q11) | link into panel foot |
| evidence-analysis / How each limit | 390 | 800 | 542 | none (Q5), long role names | inner scroll on role table |
| sitefindings / Findings at this site | 390 | 900 | 763 | chips move out (lower), Domain links neutral | n/a |
| financials / Trade-offs | 390 | 450 | 387 | +1 link (Q22) | inline link |
| verification, action-* | both | per docket | within | Q31-Q34 neutral | n/a |

- **Q37.** Some docket rows have no closed-height cap: `mini` objective cards (Q2), the `finding` strip/header, `finding-evidence` Evidence bundle (W1-a only touches the header/tabs there), `action-history` 390 (cap 800 against a peak of 589, but Q29/Q30 change rows), and `dispatch` refusal (Q6). **Default:** treat cards and strips as uncapped. Measure `action-history` against its docket cap with five 160-character meanings.
- **Q38.** Worst-case fixtures need five 160-character rows. That is possible with pure render fixtures, but the producers cannot lengthen rows. **Default:** pure selected-DTO render tests plus measured jsdom-free layout via `tools/layout-evidence.mjs` on a fixture route? There is no fixture route. Default: use producer captures for the real cases. Record the five-long-row case as a capture gap covered by the pure test, as W2 did.

## 4. Tests expected to break (to be updated, not loosened)

- miniDecisions.test.tsx :664, :679, :698, :715-716, :737, :742-743, :861-862, :879, :899, :946, :1078, :1627-1629 (Q7, Q8, Q9, Q16, Q20, Q28)
- siteFinding.test.tsx LocalViews and :616/:686 (Q7, Q14)
- siteFindingEvidence.test.tsx :584, :594, :1041; siteFindingHistory.test.tsx :338, :459 (Q8, Q16, Q17)
- w1f4RecommendationStructure.test.tsx :79, :95; t028Screens.test.tsx :220 (Q8, Q16)
- s404SiteFindingIndex.test.tsx :304 and order assertions (Q18, Q19)
- siteFinancials.test.tsx :1110, :1118, :1259 (Q23)
- siteAction.test.tsx :749, :887, :931; w1f4ActionStructure.test.tsx :130, :163 (Q29, Q30, Q33)
- siteActionVerification.test.tsx :302, :310; w1f4VerificationStructure.test.tsx :145 (Q34)
- w1f4ChangesWorkStructure.test.tsx :152-153 (Q36)
- Any test that queries Site tabs on Action or Recommendation (Q26); listed at build time
- Shell's new siteAction.test.tsx R203 block must stay green (G5)

New tests: failed-day key (Q4), window-shaped revision refusal (Q6), wrong-revision cost card (Q12), unknown Action section (Q33), long history page (Q23), RESOLVED replay (Q29), verification conflict (Q34), work link (Q36).

## 5. Recapture set and capture gaps

- **Q39.** W1-a: the 88 indexed pairs (mini 12, evidence-analysis 16, dispatch 14, finding 12, finding-evidence 8, finding-history 10, sitefindings 16). W1-b: the 118 pairs (sitefindings 16, financials 14, assumptions 12, recommendation 10, action-overview 10, action-plan 8, action-execution 6, action-evidence 6, action-history 10, verification 16, sitework 10).
- **Q40. Shared-component reach outside the lists.** **Default:** recapture the representative pair of each of these.
  - The Finding section row/header (Q7-Q9, Q16): `alternatives`, `opportunity-finding` if it uses the row, and the cold/EV Finding frames, which pass their own tabs but share `FindingSections`.
  - The rail (Q25): cold/EV Finding routes.
  - `FinancialsStatusBar` (Q21): cold-financials if shared.
  - `SiteDetails` crumb (Q1).
  - `requirementTone` (Q32).
- **Q41. Producers.** Reuse the batch-02 to -05 producers: s404/s405/s408 Finding walkthroughs, s601b/s602b/s602b-guardrail, s603, and the W1-F5b mini mode. All need Postgres scratch DBs and run only on a quiet machine.
- **Q42. Capture gaps (default: record, cover with pure tests).**
  - (a) Five-long-row worst cases on every capped panel.
  - (b) A priced Finding with a withheld consequence (Q12), if no producer yields it.
  - (c) RESOLUTION_WITHDRAWN on the Action history. The s602b `withdrawn` case may yield it; check it before calling it a gap.
  - (d) The B5-08 unknown Action already has a capture. (e) A wrong-day dispatch revision is capturable from batch-02 ids.
- **Q43.** Capture-only clicks: the Q23 Previous/Next and the Q30 Show all are client-only GETs/viewer state. Previous/Next changes the URL `history_limit` and cursor, which is a GET read and not a mutation. Default: allowed under the capture-only ruling, recorded in pair metadata.

## 6. Remaining open points

- **Q44.** Card split. Q9 (Open site on all Finding sections, W1-a) and Q27 (Recommendation Open site) overlap, as do Q7 and Q28. Default: W1-a does the frame work and W1-b tests the Recommendation view. Alternatively the IDs could swap so that each lands in one card.
- **Q45.** Recommendation still reads "Finding code unavailable" in the crumb (B4-09, D1). Not touched.
- **Q46.** B4-21 rows and B4-22 rows/detail are recorded as D2. Should the closeout add register rows for them, or does the Architect add them? Default: the builder adds D2 rows citing this pre-flight's ruling.
- **Q47.** Dispatch ErrorBoundary (Q6c): register as residual risk or as a new backlog item? Default: residual risk in the packet.
- **Q48.** B2-08 Battery link (Q2): decide link or no link.
- **Q49.** B3-13 site lens chips (Q18): D5 or a Site-scoped estate lens.
- **Q50.** G3 helper ownership.
- **Q51.** Q12 extra read on the Finding page.
- **Q52.** Q26 Site tabs on Finding overview, evidence and history (mock drops them; out of card): leave them, or extend W1-b?

## Top five for the Architect

1. **Q12 / B3-06.** Should the Finding cost card get a new financials read for the exact revision (data source, extra request, copy)?
2. **Q23 / B3-17.** History paging shape: 3-row default via `history_limit`, Previous/Next labels, PriceHistory moved into a disclosure, against caps 800/1400.
3. **Q6 / B2-29.** Refusal copy and shape test for a non-interval revision; a wrong-day revision stays "stored"; no global ErrorBoundary.
4. **Q29-Q30 / B4-19-B4-20.** RESOLVED/RESOLUTION_WITHDRAWN words, de-duplication against resolution_events, and the unified count copy.
5. **G2/G3/G4.** Extra files outside the card lists (incl. `OperatorShellLayout.tsx` rail and `SiteWindowOverview.tsx`); Site-timezone helper reuse from shell vs W2's `siteTime.ts`; LensChips/SiteFindingsFrame rebase contract with W2.
