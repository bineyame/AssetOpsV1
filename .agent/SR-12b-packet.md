# SR-12b packet: analytics readiness over the date range

- Task: SR-12b (sequence doc rev 10b/10c `architect-sequence-client-scope-2026-11-11.md:461-463`; D-SR.34, D-SR.39:
  "readiness only"). Lane G, branch `task/SR-12-warm-routes` (from main e8f2bdea5), commit f978798bb.
- USER_REVIEW_REQUIRED: no separate walkthrough; the copy in Q1 needs an Architect yes/no.

## Outcome
- `GET /api/sites/{site_id}/analytics` takes optional `from`/`to` (UTC instants `YYYY-MM-DDTHH:MM:SSZ`, both or
  neither, `from < to`; else 422 `INVALID_WINDOW`, the evidence routes' code). With a window, readiness counts only
  the active assessments whose assessed window meets `[from, to)` (`declaration.in_window`: closed `[start, end]`,
  `start < to and end >= from`; the interval's running bounds when no `assessed_window`). Which analytics apply,
  their evidence rows and the accepted-record check are unchanged. New body field `readiness_window`
  (`{from, to}` or null).
- Ranged reads change the readiness `statement` and `scope` words (`READINESS_STATEMENT_RANGED`,
  `plain.READINESS_SCOPE_RANGED`): the old words say "not the selected window", which a ranged read makes false.
- Page: `SiteEvidence` sends the address's `from`/`to` to `getDeclaration` (both or none); SR-4c's "All dates" line is
  removed from "How each limit is set" (rejections keeps it until SR-12a). `siteAnalyticsClient.getDeclaration(siteId,
  window?)`. `SitePerformance`'s declaration read is unchanged (not named by the spec).

## Files
- `backend/assetops_backend/analytics_api.py`, `analytics/declaration.py`, `analytics/plain.py`
- `frontend/src/sites/siteAnalyticsClient.ts`, `SiteEvidence.tsx`, `CapabilityReadiness.tsx` (comment)
- Tests: `backend/tests/test_sr12b_analytics_readiness_range.py` (new), `frontend/src/shell/__tests__/siteEvidenceScreen.test.tsx`

## Acceptance (rev 10c)
- Route takes optional from/to: MET (8 tests incl. 5 bad-window cases).
- Declaration unchanged: MET (every non-readiness key equal ranged vs unranged).
- Readiness counts only assessments meeting `[from, to)`: MET (1 inside, 0 outside, edges unit-tested).
- "All dates" line removed: MET (analytics panel; one line remains, under rejections).

## Checks (VPS, no DB)
- `test_sr12b_analytics_readiness_range.py` + `test_t028_dispatch_analytic.py`: 42 passed. Adjacent
  `test_sites_api.py`, `test_uq6a_message_seam.py`, `test_health.py`: 98 passed; `test_scenario_parsing.py`,
  `test_qw2_reuse.py`: 148 passed.
- vitest `siteEvidenceScreen.test.tsx` 17 passed. Range/link files touching evidence/analytics (63 files from the
  lane-rules grep, filtered to evidence/analytics): 1958 passed, 1 failed (`evEnergy.test.tsx` R347) under batch
  load; that file passes alone on the branch and on main (12/12): load flake, not this change.
- `tsc --noEmit`: clean. Mutations: page sends no window -> 2 failed; `in_window` always true -> 2 failed; reverted.
- check-all: for coordinator.

## Known deviations
- **Postgres test not run, and none written.** `/analytics` has no Postgres path: it is the file-backed declaration
  (`build_assessment_store` -> Json/Memory store) and `LegacySiteGate` refuses every imported Site (sequence doc
  :122). `assetops_sr12b_test` was not touched.
- Consequence: on the demo Sites (all imported) this panel never loads, so SR-12b is not visible in the demo.

## Questions (Architect)
- Q1: confirm the ranged copy - statement "...the coverage of its active assessments whose assessed window meets the
  selected date range."; scope "Assessed periods are those in the selected date range; whether each required input
  has a usable record is checked against all of this site's accepted records. It is not a rating of the site's
  health and not permission to act."
- Q2: intersection rule: an assessment whose assessed window ends exactly at `from` counts (closed window). OK?
- Q3: given the Known deviation, does SR-12b stay on the Saturday deferral list as is, or is it closed?
