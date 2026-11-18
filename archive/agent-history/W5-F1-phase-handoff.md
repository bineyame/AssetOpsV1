# W5-F1 phase handoff - D3 corrections R22, R37, R38

Branch `task/W5-F1-d3-corrections` (from main `2503a34d`). Spec `.agent/W5-F1-build-spec.md`.

## Pre-flight

Every card names its files, markup, tests and capture contract; the spec records "Decisions left open: none".
No open decision found; built as written. One choice the spec left to fixture use: the capture seed case is the W2-02
`excursion` replay (`opened("excursion", chain)` + `run(built)`), the case that gives the Excursion context and accepted records.

## Run 1 - 2026-10-23

- **F1-1 (R22)** `f0812934`: cold Health mounts only `ColdHealthDepth` (`SiteHealthFrames.tsx`); exported
  `SiteHealthSources` removed (`SiteHealth.tsx`, private source panel + non-cold read intact); Foundation Gateway status action
  is `Evidence › Data sources →` to `${evidenceHref}#cold-site-sources-heading` (`ColdFoundationViews.tsx`). Tests: cold
  Health title list `["Condition and evidence"]` + order for CURRENT/UNKNOWN, refused page; no `/source-health` or
  `/battery` request (`coldHealthDepth`, `siteHealthBoundary`); exact href and followed click lands on the cold-evidence panel (`coldFoundation`).
- **F1-2 (R37)** `42964500`: no source change (row already in mock order). Tests assert the seven labels in order,
  one `Loading / batch`, `Not established`, Door opening < Loading / batch < Defrost for selected/empty, no rows when refused
  (`coldSiteViews`, `coldRoutes`). Non-vacuous: swapping the row with Defrost failed 4 tests; reverted by checkout.
- **F1-3 (R38)** `89b88a40`: Record cell is the unconditional labelled reference + `Record page unavailable`
  (`coldSiteViews.tsx`). Tests: full `REC {id}`, no anchor (hostile PROVED/self-link row included), distinct IDs with shared
  prefix, six headings, Record details unchanged. Non-vacuous: the old component failed 2 tests; restored by checkout.
- **Producer + captures** `ff59b3cf`: `tools/w5f1-d3-evidence.mjs`; first evidence `run1/` (superseded and removed in Run 2). Method: private `assetops_w5f1_test` (`ASSETOPS_TEST_TEMPLATE=0`), throwaway seed test (deleted),
  host `lab_app` on 9781 with `DATABASE_URL` = that DB, Vite 6181 (`ASSETOPS_API_PORT=9781`, serves v69 same origin), own
  headless Chrome CDP 9861. App revision captured: `89b88a40` (producer-only commit followed). Result **PASS**:
  - reads: stocked 200 CURRENT, empty 200 UNKNOWN, refused 422 `COLD_WINDOW_INVALID` for health/temperature/analysis;
    `known_at` = `committed_watermark` = `2026-10-23T06:15:56.695105Z` (refused: none).
  - analysis first ids `...0b6`, `...0b8`, `...0ba`; target state `UNAVAILABLE`, 0 links; 50 record cells, 0 anchors.
  - cold Health titles `["Condition and evidence"]` = mock; Temperature and Analysis titles = mock on loaded states; refused
    shows the honest refusal (page refusal on Health, in-slot refusal sentence on W2 views).
  - Foundation click lands `/sites/COLD-LAB-001/evidence#cold-site-sources-heading` on the Data sources panel at 1440 and 390.
  - no document overflow at 1440/390; no clipped record ID (390 keeps the existing table scroller, like the mock).
  - Producer non-vacuous: swapping the Loading / batch and Defrost rows gave `result FAIL (4)`; reverted by checkout.
- Cleanup: API, Vite and Chrome stopped by PID; `assetops_w5f1_test` dropped (0 `w5f1` DBs).

## Run 2 - 2026-10-23

- Slice close: frontend `vitest run` 113 files / 2697 passed; `npm run build` OK; `check-all.ps1` 10/11 - the W1-UX-06
  evidence width guard (`tools/checks/test_evidence_checks.mjs`) failed: the new producer did not use the shared width check.
- Fix `8e7dd87e`: producer imports `widthGuard` from `tools/evidence-checks.mjs` and calls `requireWidth` after every
  resize/navigation and after the Foundation click; the guard test then passed 10/10. No guard edited.
- Recapture with the guarded producer: `.agent/W5-F1-evidence/run2/` (evidence.json + PNGs), revision `8e7dd87e`, same
  method (fresh `assetops_w5f1_test`, throwaway excursion seed deleted, `lab_app` 9781, Vite 6181, CDP 9861). Result **PASS**,
  28 width claims all ok; `known_at` = `committed_watermark` = `2026-10-23T06:32:55.659284Z`; analysis first ids `...0b6`,
  `...0b8`, `...0ba`, `UNAVAILABLE`, 0 links; Foundation click lands on `#cold-site-sources-heading` at 1440 and 390.
  `run1/` removed (same assertions, unguarded widths).
- Cleanup: API, Vite, Chrome stopped by PID; `assetops_w5f1_test` dropped (0 `w5f1` DBs).
- Register R22/R37/R38 set to `built: W5-F1 <commit>`. Next: independent review, then owner walkthrough before merge.
- Final `check-all.ps1` at `200f97ca`: 11/11 PASS.
