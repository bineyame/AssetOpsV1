# W1-F5b review packet: in-page tab rows, Site Findings chips, carries, all-26 audit

Branch `task/W1-F5b-tabs-audit`, built from main `e7a1f6a1` (F1-F5a merged). Brief: `.agent/W1-F5b-build-brief.md`. Ruling: `D-2026-10-17-f5-subtabs-and-contact` (F5 section of `.agent/architect-W1-fidelity.md`). Carries 7-11 of `.agent/W1-F5-carries.md`. Frontend and guards only; not merged.

Commits: `9ce710af` (carries 8-9), `f0b8878f` (rows, chips, headings, breadcrumb, guards), `69ceb4cf` (audit index tool), `6978d924` (audit fixes), plus the evidence/packet commit.

## Outcome delivered
- **Unbuilt entries** (`ui/UnavailableEntry.tsx`): `UnavailableTab` / `UnavailableChip` render muted text in a `li` with the visible and accessible status "Not available yet". They have no `href`/`to`, handler, tab stop, button, role, `disabled` or `aria-disabled`. This follows the rail's W1-UX-07 pattern.
- **Foundation row** (`sites/FoundationSubtabs.tsx`): Site model | Single line diagram | Readiness | **Change & effect**. Change & effect is a live link to the existing `/foundation/changes` route, and it is current on both Changes routes (`SiteAnalyticsFrames.tsx`). It is not a period view: `FOUNDATION_SUBTABS` is unchanged, so `foundationViewFor("changes")` is still null. The cold-room row keeps the mock's three views (`withChanges={false}`).
- **Rows following the v69 order:**
  - Work: Actions (live, current), then Incidents and Maintenance (not available yet).
  - Financials: Overview, Assumptions, then Scenarios (not available yet).
  - Finding: Finding, Evidence, Alternatives (not available yet), Recommendation, History. This is the mock's order. The old order was Finding, Evidence, History, Recommendation.
  - No placeholder routes were created, and no counts were copied from the mock.
- **Site Findings:** the single panel now holds, under its heading, one controls row:
  - Lens chips: All (live, `aria-current`), then Cost, Risks and Opportunities (not available yet).
  - The existing date window form, which is still the real scope control. The chips cannot change or discard the window.
  - Columns and Finding links are unchanged.
- **Bare Change & effect page** (`/foundation/changes`, found by the audit): it is now the changes screen's own structure. The page states "No change selected" once, then shows the two v69 panels, "Change and effect" and "Decision path", with the gap stated inside each (`NoChangeSelected` in `SiteFoundationChange.tsx`). It used to be a one-panel "No list of changes yet" card.
- **Carry 8:**
  - The Overview money panel now has one closed row. The cost's source record folds into "Cost range, money gate, source record and links" through `SourceProvenanceNotice record="elsewhere"` and `SourceProvenanceRecord`.
  - "the gaps below" was reworded to "for the rest of the period a reading it needs is missing or unreliable" (`EvidenceClaimLimit.tsx:110`).
  - Dispatch was recaptured (part07).
- **Carry 9:** the " · " separator before the source line now applies only when something precedes it (`w1ux02-finding.css`, `:not(:first-child)`).
- **Carry 10, headings:** Finding Evidence and History use the Finding's own name as the h1, as the mock does (`onTitle`). The fallback is "Generator support review".
- **Carry 10, tab rows:** `.site-tabs__list` no longer wraps. It scrolls inside itself, like the mock's `.tabs` (inset rule, so the underline is not clipped). `useCurrentTabInView` keeps the current tab visible in the Site row and the Finding row.
- **Carry 11:** every breadcrumb names the site (`display_name`), not the raw code:
  - all Site frames (Analytics, Health, Evidence, Foundation)
  - the legacy Site detail page
- **Carry 7:** not possible, see Known deviations.

## Files materially changed
- `frontend/src/ui/UnavailableEntry.tsx` (new), `ui/useCurrentTabInView.ts` (new), `ui/primitives.css` (tab row scroll, unavailable styles)
- `frontend/src/sites/FoundationSubtabs.tsx`, `ColdFoundationViews.tsx`, `SiteFindingEvidence.tsx` (FindingSections, onTitle), `SiteFindingHistory.tsx`, `SiteFindingIndex.tsx`, `SiteFoundationChange.tsx`, `SiteWindowOverview.tsx`, `sourceProvenance.tsx`, `EvidenceClaimLimit.tsx`, `SiteDetails.tsx`, `w1ux02-*.css`
- `frontend/src/shell/SiteAnalyticsFrames.tsx`, `SiteFoundationFrame.tsx`, `SiteHealthFrames.tsx`, `SiteEvidenceFrame.tsx`, `operatorSiteTabs.tsx`
- Tests: `test/unavailableEntry.ts` (new shared assertions), siteFinancials, siteFoundationRevision, foundationScreen, siteFoundationChange, s404SiteFindingIndex, siteFindingEvidence, siteFindingHistory, siteDetailScreen, w1f4ChangesWorkStructure, s5SiteWindowOverview
- `frontend/src/test/productVocabulary.json`: two exact-text glosses for "Scenarios · Not available yet" and "Scenarios, Not available yet"
- Guards:
  - `tools/checks/navigation-truthfulness.ps1`: the Foundation row allows Change & effect as its 4th entry, and the new `Get-InPageUnavailableEntryFailures` check
  - `navigation-rail-fixtures.ps1`: 9 new in-page cases
  - `missing-claim-scan.mjs`: a reviewed exemption for `IN_PAGE_UNAVAILABLE_STATUS`, with tests in `test_missing_claim_scan.mjs`
- `tools/w1-fidelity-audit-index.mjs` (new): builds the all-26 index from the per-part evidence

## Acceptance (brief items)
| Item | Status |
| --- | --- |
| 1. Named rows show live tabs plus "Not available yet" text entries that are not links | Met. Every row's order, status, missing destinations, current tab and keyboard behaviour (focus, Enter, Space, click) are tested through `expectUnavailableEntry` and `rowLabels`. |
| 1. Site Findings keeps its date scope; only backed lenses are interactive | Met. All is live; Cost, Risks and Opportunities are not available yet; the window form sits inside the panel. Test: s404 W1-F3 structure. |
| Navigation guard amended narrowly; other disabled Site tabs still rejected | Met. The Foundation row is exactly 4 labels; "Changes" and "Change and effect" stay forbidden. The in-page inventory is exactly Alternatives, Scenarios, Incidents and Maintenance (tabs) plus Cost, Risks and Opportunities (chips). The Site tab and rail guards are unchanged. |
| Carry 7 | Not met (see Known deviations). |
| Carries 8, 9, 10, 11 | Met. Carry 9 is CSS only and jsdom cannot see it; the part08 finding captures include that state line, but I did not inspect them closely, so carry 9 is visually unverified. |
| 3. All-26 audit | Met. Index `.agent/W1-F5b-evidence/index.html` and `audit.json`: **168 pairs, 26/26 screens at both widths, 0 failing, panel count matches everywhere, overflowX 0 everywhere**. 1 screen (sites) is within 1.3x; 25 have taller panels, and every one has a stated reason (`overages.json`, 43 panel reasons). |
| Structural mismatch fixed | The audit found one: the bare Changes page had 1 panel against the mock's 2. Fixed in `6978d924` and recaptured (part17). |

## Checks run
- `npx.cmd tsc --noEmit`: clean at `6978d924`.
- Full `npm.cmd test` (vitest): **82 files, 2140 passed, 0 failed** at `6978d924`. The same result at `f0b8878f`. No known flake fired.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`: **All 10 guards passed** at `f0b8878f` and again on the final revision.
- `node --test tools/checks/test_missing_claim_scan.mjs`: 24/24.
- Proof that the guards can fail, run on committed code and reverted with `git checkout`:
  - Adding `tabIndex={0}` to `UnavailableEntry.tsx` made the check fail with "carries tabIndex".
  - Reverting `$requiredViews` to 3 labels failed on the real tree ("declares 'Site model, …, Change & effect'").
  - The 9 fixture cases (tab stop, handler, button, an undeclared tab, a dropped tab, Alternatives promoted, a computed chip label, the component missing, baseline) all behave as expected inside check-architecture.
- Captures:
  - 15 walkthrough parts at `69ceb4cf`, 970/972 claims passed. The 2 failures are part13's, matching the `changes:list` panel-count mismatch (the audit's only red result); that pair was removed and superseded.
  - part17 at `6978d924` (changes:list, plus the tab-row cases for sitework, evidence and financials): 48/48.
  - All servers were stopped and every fixture database and work folder dropped.
- **Layout evidence after `6978d924`:** only part17 was recaptured. The other 390 captures were taken before the current-tab-in-view fix. Panel structure is unaffected; the only difference is the Site row's scroll position.

## Known deviations
1. **Carry 7, legacy-Site captures:** not possible. No walkthrough tool prepares a file-backed (LEGACY_FILE) Site; every part serves KOBO-001/002 from Postgres. Legacy paths stay covered by the structure tests only (t028, siteEvidenceScreen, S5 legacy). Capturing them would need a tool that serves `var/sites` YAML against a migrated database with no tenant.
2. **Finding row label:** the first entry stays "Finding", not the mock's "Overview". The Finding page keeps its own Overview | Analysis view row below, and two "Overview" entries would be ambiguous. The mock's separate Analysis tab is not added, because the ruling names only Alternatives.
3. **Recommendation heading:** superseded by the fix round (M2): the h1 is now the Finding's name.
4. **"Scenarios" vocabulary:** "scenarios" is on the product word list in its development-workflow sense. The ruling requires the mock label, so two exact-text glosses allow it only together with its status. The unbuilt tab's label and status are therefore one text node, "Scenarios · Not available yet".
5. **390 behaviour that matches the mock but is worth seeing:**
   - Tab rows scroll inside themselves, so the trailing unbuilt entries in the Work row are reached by scrolling, as in the mock.
   - The Site Findings chips wrap onto a second line (the mock's `.chips` also wrap).
   - The Finding row's money link sits on a short line under the row.
6. **Heights:** 139 capture rows are above 1.3x. They come down to 43 distinct panels, each with a reason in `overages.json`. Most come from real data or from material limits that must stay visible, and earlier reviews accepted them. Superseded by the fix round: the two placeholder reasons are replaced and the worst case is now the opened-reading capture at 3.59x/3.71x.

## Residual risk
- The Changes route has no change list, so Change & effect opened from Site model always lands on "No change selected". This is honest, but owners may expect a list.
- `useCurrentTabInView` is measured only in real Chrome (part17). jsdom does no layout, so no unit test covers it.

## User-review focus
- The walkthrough index `.agent/W1-F5b-evidence/index.html`: the summary table, then each screen's app beside the mock at 1440 and 390.
- The unbuilt tabs and chips: muted, with their status, not clickable.
- Change & effect in the Foundation row.
- The heading change on the Finding child views.

## Fix round (review RETURN: 1 High, 2 Medium, 3 Low)
Code at the fix-round commits after `13cf2477`; frontend only.
- **H1 Lens column:** `SiteFindingIndex.tsx` adds `Lens` after Main consequence (Period kept), each cell the muted "Not assessed" badge (`data-finding-index-lens`). The s404 W1-F3 test now asserts the header row `Finding, Domain, Priority, Confidence, State, Main consequence, Lens, Period` and each row's Lens badge. part09 recaptured.
- **M2 Recommendation heading:** `SiteRecommendation` takes `onTitle` and reports `FINDING_NAME` ("Generator support review": the recommendation read carries no lifecycle, so the lifecycle-specific title Finding/Evidence/History derive is not available there). `FINDING_VIEW_TITLES` removed; the frame always uses `title`. `w1f4RecommendationStructure` asserts the h1. part13 and part14 (recommendation guardrail-hold) recaptured. Residual: a current Finding titled "Generator support merits review" shows "Generator support review" on its Recommendation view.
- **M3 reading detail:** `RecordFacts` now shows plain words (reading by its configured name, Quality "Good", Decision "Accepted", times, delivery progress) and one closed "Exact references" disclosure with every ID, fingerprint, source/device code, the exact message and the repeat/conflict records. `v01bEvidenceVisual` asserts one closed disclosure, the message and IDs inside it, none outside, no GOOD/ACCEPTED. Audit: the opened-reading case is listed second and labelled "record (a reading opened)"; the overage reason is split per case (default 1.64x named by its real content). part04 recaptured; the opened state is 3.59x/3.71x (was 5.75x/7.86x).
- **Low 4:** `FactList` takes an optional `className`; the Analysis Coverage list stacks label over value below 480px (`periodStrip.css`), so 390 is 0.87x (was 1.38x). Asset ratio corrected to 1.20x at 1440 / 1.31x at 390 with its real cause.
- **Low 6:** every walkthrough part was retaken on the fix-round code (parts 01, 02, 04, 05, 06, 07, 08, 09, 10, 10b, 11, 13, 14, 15, 16; part17 already current). All 168 pairs and `audit.json` regenerated by `tools/w1-fidelity-audit-index.mjs` (`audit: 168 pairs, 2 match, 24 taller, 0 failing`; no panel above 1.3x lacks a reason).
- **Low 5 (carry 7):** accepted and backlogged by the coordinator; no action.
- Capture claims: all parts passed (part02, part14 had one first-load fail each under parallel load; rerun alone: 48/48 and 108/108). Servers on 9900-9950/6300-6350 stopped; fixture databases and work folders dropped (s3 shared template and `assetops_s4cases` untouched).
- Proof: `npx.cmd tsc --noEmit` clean; focused files (s404, s2LedgerEvidence, v01bEvidenceVisual, siteFindingEvidence, siteAction, t028, w1f4RecommendationStructure) pass; full `npm.cmd test` 82 files, 2140 passed, 0 failed (156 s); `tools/check-all.ps1`: All 10 guards passed.

USER_REVIEW_REQUIRED: yes. This index is the owner's repeat W1 walkthrough. Owner acceptance closes W1.

## Fix round 2 (re-review RETURN: 1 Medium, 1 Low)
- **M1 lost capture state:** parts 06 and 07 were recaptured against fresh private fixtures (s302 claim-limit and s3 dispatch walkthroughs) with the assessed revision restored in the URL. part06 supported (10/06) reads "avoidable for 30 min"; limited (10/11) reads "avoidable for at most 5 min; ... missing or unreliable" with "Clear selection". part07 analysis supported (10/02, block 1) shows the constraint table and "Low" confidence; limited (10/09) shows its own result. Images viewed at 1440 and 390. Capture tooling only; no code change for this item.
- **L2 part09 scroll:** `w1ux02-findings-index.css` lets non-first cells wrap and first column min-width 12rem at 900px and wider. The stocked 1440 capture shows all 8 columns with no scrollbar. part09 recaptured (72/72 claims).
- Audit index and `audit.json` regenerated: 168 pairs, 2 match, 24 taller, 0 failing.
- Proof: `npx.cmd tsc --noEmit` clean; `s404SiteFindingIndex` 37 passed. Full suite not rerun (CSS only). Ports 9900-9950/6300-6350 servers stopped; fixture DBs and work folders dropped.
