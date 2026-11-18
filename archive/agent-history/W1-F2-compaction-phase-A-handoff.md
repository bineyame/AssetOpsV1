# W1-F2 compaction, phase A handoff

Branch `task/W1-F2-overview`, build commit `016ed942` (on `74148840`). Not merged. Heights not measured here (phase B runs captures).

## What moved, per panel
- **evidence-analysis panel 2 "How each limit is set"** (`EvidenceClaimLimit.tsx` `Loaded` ~512-580; `LedgerSiteEvidence.tsx` analysis branch ~193-215):
  visible: label, the mock paragraph (now a `ChartNote`), day chooser, assessed periods, question, `data-claim-limit-headline`, `ProductStatusLine` (`.claim-limit__when`), UNASSESSED day line (`ChartNote`), pinned Dispatch link, capacity note (`ChartNote`, was `.claim-limit__note`).
  closed `details[data-disclosure='claim-limit-detail']`: role strip, "What limits it" reasons, window level, earlier-version sentence and periods, interval links, role table, `claim-limit-technical`.
  The three analysis Advanced disclosures (status, comparison, gateway) now nest in one closed `evidence-analysis-technical` row; each keeps its own closed `details` and "Advanced details — " summary.
- **evidence-analysis panel 1 "Accepted records ..."** (`Inspector` ~1164-1350): rows past 3 get `hidden` (`RECORD_PREVIEW_ROWS`); "Show all N readings" / "... on this page" toggle in the paging row (`data-evidence-records-toggle`, `aria-expanded`); a selected record past row 3 shows the full page. Count/clock line is a `ChartNote` (`data-evidence-records-count`). Clocks/sources/deliveries/coverage Advanced nest in one closed `evidence-records-technical` row. Not-accepted line untouched (outside details).
- **evidence panel 2 "Data sources"** (`SourcesOverview` ~628-735): reporting facts + reporting note visible; source rows past 3 `hidden` (`SOURCE_PREVIEW_ROWS`), "Show all N sources" toggle (`data-evidence-sources-toggle`); `source-judgements` NotAvailableYet visible (moved above the disclosure). Closed `evidence-sources-detail`: `[data-evidence-source-clocks]`, `SourceStrip` (`data-period-strip='evidence-sources'`), gateway block, nested `evidence-earlier-store`.
- **evidence panel 1:** not trimmed (1.36-1.46x; no cheap safe cut — ExactReferences is already closed).
- **dispatch panel 3 "Accepted sample coverage"** (`PerformanceDispatch.tsx` third slot ~496-510, `CoverageDetail`/`CoverageBody` ~1015-1100): coverage rows past 3 `hidden` (`COVERAGE_PREVIEW_ROWS`), "Show all N inputs" (`data-coverage-toggle`); coverage note and `ComparisonLine` visible; "No limitation is recorded" stays a visible `ChartNote` (`data-dispatch-limitations="none"`, was `<p>`). Closed `dispatch-coverage-detail`: the grouped limitations list (panel 1's `LimitationSummary` line still states them), `dispatch-coverage-reading`, `dispatch-selected-records`.

## Changed assertions
None. All 184 targeted + 748 adjacent tests passed unchanged. Existing queries use `querySelector`/`textContent`, which still find content in closed `details` and `hidden` rows (rows are hidden, not removed, so e.g. `[data-coverage-role='battery_reserve']` in performanceDispatch.test.tsx:276 still resolves).

## New tests (each proven to fail under mutation, then reverted)
- `performanceDispatch.test.tsx` "W1-F2 compaction: coverage shows three inputs ..." (preview constant -> 30 fails it).
- `v01bEvidenceVisual.test.tsx` two "W1-F2 compaction" tests: records 3 + Show all + nested technical rows; sources 3 + Show all + detail contents + visible facts.
- `evidenceClaimLimit.test.tsx` "W1-F2 compaction: the headline and state line stay visible ..." (headline moved into the disclosure fails it).

## Open risks / for phase B
- Panel 2 of evidence-analysis keeps form controls (day chooser, periods nav) and five note lines; may still exceed 1.3x vs the mock's 148px paragraph. Measure; next cuts would be the label line (`CLAIM_LIMIT_HEADING_ID`, check aria references first) or folding the two panel ChartNotes.
- Gateway "switched off for this site" wording now lives only in the closed gateway block on the overview (the visible contact fact does not mention DISABLED).
- Dispatch refused path (`DispatchRefused`, third slot `gap`+`extra`, ~278) untouched; if the "failed" case uses it, its height is unchanged.
- PowerShell 5.1 mangles `"` inside `git commit -m @'...'@`; commit from a message file (`-F`).
