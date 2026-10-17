# W1-F3 fix round: independent re-review

Reviewer: a fresh Claude reviewer who is not the author. Revision: `db47efc2` (last code commit `8a6a294c`). Fix diff: `dcbbf181..db47efc2 -- frontend`.
Inputs:
- `.agent/W1-F3-review.md`
- the packet's fix-round sections
- the captures in `.agent/W1-F3-evidence-height3/`, compared with the `*-mock.png` files at 1440 and 390.

## Verdict: RETURN

Two Medium findings block. Both are on the Assumptions screen. Every other High and Medium finding from the prior review is fixed and confirmed in code and in the captures. Both fixes are small.

## Checks run (by me)

- `npx.cmd tsc --noEmit`: passed (exit 0).
- Focused run:
  - Command: `npx.cmd vitest run` over these 7 files: `w1f3PanelGuard`, `panelStructure`, `siteFinancials`, `siteFinding`, `siteFindingEvidence`, `siteFindingHistory` and `s404SiteFindingIndex`.
  - Result: 285 of 286 passed, 36.5 s.
  - The 1 failure was `siteFinancials.test.tsx:490`, "pins the selected version into the address when the link named none". The address still had no `revision_id` when the test checked it.
  - I reran `siteFinancials` alone 3 times: 82 of 82 passed each time.
  - The test dates from `07a96854` and the fix round did not change it. It is a timing flake under parallel load (see Low 5).
- Full suite: not rerun, as instructed. I cite the implementer's run at `8a6a294c`: 2015 of 2016 passed, 362 s, with the known `siteFoundationChange` flake. That revision is the last code commit under review.
- Layout evidence: not rerun. The captures I read are listed under each item below.

## Prior findings: status

| # | Prior | Status | What I saw |
| --- | --- | --- | --- |
| H1 | Limits hidden | Fixed | Every limit renders in the visible `ul[data-finding-limits]`: the bounded line, the record gap, the series limit, all groups, joined gaps, stops and recurrence. Only the access note and the SUPPORTED lifecycle sentence sit in `finding-limits-context`. A new test covers 9 visible limits. Seen in `finding-stale-1440-app`. |
| H2 | Priority / Confidence / Domain | Fixed | The sitefindings table has Domain, Priority and Confidence columns. The Finding strip has Priority and Confidence chips. Financials has a bridge Confidence column and a "Data confidence" chip. All unknowns show as muted dashed "Not assessed". Lens waits for F5, as allowed. |
| H3 | Price versions as a list | Fixed in form | The price versions are now a 5-column table. Per-row disclosures remain (Medium 1). |
| M4 | State line said more than once | Fixed | Finding: the panel keeps the sentence, the source clause and the as-of. Financials: "Modelled potential..." is gone, and "This is not zero" now appears 2 times (it was 4). History and Evidence: one line each. Sitefindings: the in-panel note, "Showing N of N" and the one-day strip are gone. |
| M5 | One disclosure per panel | Fixed except Interpretation history | Financials bridge: 1. Trade-offs: 0. Evidence: one in the bundle and none in lineage. Financial assumptions: 1, plus the "When each price applies" Show-all list expander. Interpretation history: see Medium 1. |
| M6 | Raw IDs | Fixed | The Source cells read "Source not named" or "3 sources, not named". The IDs moved into the disclosure. A test asserts there is no `code` in the Source cells. |
| M7 | Contradiction | Fixed | When there are no fuel-cost rows there is one state line: "No fuel cost version recorded by this moment; the price versions below are prices only." |
| M8 | Lineage cuts | Fixed | Lineage is a step line only, plus the reworded no-record line and one head link. It is now 1.26x. |
| M9 | Rows at 390 | Fixed | Sitefindings rows at 390 are about 80 px (they were about 170). Related now sits under the title. |
| L10 / L11 | | Fixed | A new cosmetic issue is in Low 4. |

## Regression check

- **Money gates unchanged.** `shown` and `gated` (`FindingConsequence.tsx:730-731`) are not in the diff. `drawn` (`:746`) is pinned-or-stepHead, and only feeds the one references disclosure. The pinned table still gets `current={false}`. NO_PRICE, CONFLICT and `recorded_amount.disposition` are untouched.
- **"Why no current amount".** It now renders only for QUANTITY_UNAVAILABLE and UNPRICED, because the state line already gives the reason in every other state. This is copy only; no amount condition changed.
- **No assertion weakened.** I read every removed `expect`. Each one is re-pointed to the new DOM home or replaced by a stronger check:
  - The "at most 3 limits" checks became "every limit visible".
  - The removed history row links are now asserted absent, and the same exact IDs are asserted on the head and evidence links.
  - Disclosure counts went from 2 to 1.
- **Panel coverage.** `expectV69Panels` still runs on every F3 route and state (76 call sites), and the guard's non-vacuity tests pass.

## Findings

1. **Medium (blocking): Interpretation history has one disclosure per row, which breaks the one-disclosure rule (prior M5). It is the main cause of the 2.28x height, which got worse.**
   - Where: `frontend/src/sites/SiteFinancials.tsx:766-771`, the per-row `ExactReferences name="price-history-N"`, plus the inline "How these times are read" at `:805`.
   - What is wrong:
     - The panel has 4 closed disclosures with 3 versions shown.
     - Each per-row disclosure is labelled "How this was worked out" but holds only a reference and a link.
     - It forces a second line in every row: about 82 px per row at 1440, against the mock's 50 px one-line rows. At 390 the off-screen Status cell makes each row about 80 px with blank cells, which is the same defect M9 fixed on sitefindings.
   - Decision: **adopt the proposed single panel-level reference disclosure.**
   - Fix:
     - (a) In each row's Status cell keep only the change badge and "Open version N", on one line (`white-space: nowrap`).
     - (b) Below the table, render one `ExactReferences name="price-history"` for the panel. List each shown version as "Version N: `<revision_id>` · Prices as recorded then (link)". Fold the "How these times are read" text into the same disclosure.
     - (c) Leave the fuel-cost rows (`ConsequenceHistory.tsx`) unchanged. When fuel-cost rows exist they are their own table, and this fix touches only the price-version part.
     - (d) Update the `siteFinancials` assertion "4 for the history table" to 1. Assert that every version's reference and "Prices as recorded then" href are still in that disclosure.
     - (e) Re-capture part11 at 1440 and 390. Expected result: about 1.4x or less, with rows on one line.

2. **Medium (blocking): on the version-1 page, the in-use dates and the selected version's dates contradict each other, because one label means two things.**
   - Where: `frontend/src/sites/SiteFinancials.tsx:247` (the `PriceFields` "Effective period" label), `:610` (the in-use line) and `:657` (the assignments, moved into the disclosure this round).
   - It is a real defect:
     - In the default view, "Effective period" shows the assignment that is actually in force (1 Jul 2026 until 1 Jan 2030).
     - On a pinned version it shows the authored validity (from 1 Jan 2026, no end date).
     - So the same field label shows different dates for the same price (1.25, version 1). The in-use line directly above names the other period, without naming a version.
     - This round also moved "where this version applied" (the real effective segments) into the closed disclosure. That removed the only visible text that reconciles the two.
     - These are the dates a money assumption covers, so this is a material fact, not method.
   - Fix:
     - (a) In `ExactVersion`, label the authored field "Entered as applying" rather than "Effective period".
     - (b) Bring the assignments back as one visible line under the fields: "Applied: 1 Jan 2026 until 1 Jun 2026; 1 Jul 2026 until 1 Jan 2030". Keep only the known-from and replaced-on times in the disclosure.
     - (c) When an address pins a version, make the in-use line name the version it describes: "In use today: version 1, 1.25 USD per litre, from 1 Jul 2026 until 1 Jan 2030".
     - (d) Add a `siteFinancials` test on the version-1 fixture. It should assert that the applied segments are visible outside any closed `details`, and that the authored field label is not "Effective period".

3. **Low: the "Open version N of the Finding" head link deviation is not justified as written.**
   - Where: `frontend/src/sites/SiteFindingHistory.tsx:307`.
   - The packet says the head link is "the only way to the Finding at a version". That is wrong:
     - The Finding section tab and the breadcrumb both carry `revisionId` (`SiteAnalyticsFrames.tsx:412-413`, and the `FindingSections` doc comment says each link keeps the exact selected version).
     - "Select version N" moves that selection.
   - The mock's Revision history panel has no head link.
   - It is a small link and not a panel-structure change, so it does not block. Recommended fix: drop it, and drop its `data-history-open-finding` assertion in favour of the Finding tab's href.

4. **Low: cosmetic leftovers from L10.**
   - Where: `frontend/src/ui/ProductStatus.tsx:39`, and the compact Finding state in `SiteFinding.tsx` around `:365`.
   - When the inline state wraps after a block child (the source-record `details`), the bound starts its line with a space. Visible cases:
     - " As of 16 Oct..." in `finding-stale-1440-app`
     - " Site KOBO-001..." and " Diesel price..." in part11
   - Fix: trim the leading space by putting it before the child rather than after it, or by using CSS `margin-left` on `.product-status__bound` when it is not first on its line. Also make the `SourceProvenanceNotice` disclosure `display: inline` inside inline status.

5. **Low: a pre-existing timing flake.**
   - Where: `frontend/src/sites/__tests__/siteFinancials.test.tsx:488-490`.
   - The address is read straight after `settledScreen()`. It failed once for me under the 7-file parallel run and passed 3 of 3 times alone.
   - Fix: wrap the check in `await waitFor(...)`. This can go to the test-speed backlog.

## Accepted overages (judged)

| Case | Ratio | Judgement |
| --- | --- | --- |
| Finding History | 1.63 / 1.87 | Accept. What remains is the state line, the honest headline, the no-replay line and two-line rows, all owned content. Dropping the head link (Low 3) helps slightly. |
| Evidence bundle | 1.43 | Accept. It holds the state line with the example-data clause, the 4-row table, one gap line and one disclosure. |
| Financials withheld | 1.45 | Accept. It holds the withheld state, the series-limit bullet and the recorded-version link, all required. |
| Financial assumptions | 1.38-1.43 | Accept. It holds the fields, the in-use line, the disabled edit with its reason and one disclosure. After Medium 2 it grows by one line, which is accepted. |
| Finding stale limits | 1.36 | Accept, because every limit must stay visible. |
| Sitefindings | 1.34 | Accept. The extra height comes from the Not-assessed columns and the Related links under titles. |
| Interpretation history | 1.38-2.28 | **Not accepted.** Medium 1 is the cut. Re-measure after it. |

## Residual risk not in the packet

- At 390, the finding-history Basis column and the price table scroll sideways inside their cards. Medium 1 shortens the price rows, but the sideways scroll stays.
- The interpretation-history description says "newest first", while the price table eyebrow says "oldest first". This is copy only and could be fixed in the W1 copy pass.
