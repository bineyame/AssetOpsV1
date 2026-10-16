# S4-04 phase 2 handoff - Site Findings UI, walkthrough, closeout

Branch `task/S4-04-site-finding-index`; final code revision `38c61cfd`, closeout commits after it. Not merged.
Task status `in_review`; packet `.agent/S4-04-review-packet.md` (this phase's review is the slice review).

## Landed
- Phase-1 review H1 (index-side, defence in depth): `analytics/finding_index.py` `candidate_reach` + `discover(...,
  edge_reach=)`; `FindingIndexService.read` caches one `dispatch.window` read per day and feeds both discovery and
  `_day(read, ...)`. Test `TestContinuity::test_s3_candidate_near_an_edge_reaches_a_neighbour_the_matcher_skipped`
  (reviewer's probe: stale D+1 -> STALE no claim; injected cap 1 -> 409 via S3 edge only; reassessed before rematch
  -> PENDING; rematch -> CURRENT/1). Its stage-1 reason check is `any(... "2026-10-26")`, so it stays valid after the
  upstream deferred-match fix adds a D MATCH_PENDING reason. Mutation `edge_reach=None` caught, reverted. Matcher and
  `postgres_finding_store.apply` untouched (coordinator direction).
- UI: `frontend/src/sites/findingIndexClient.ts`, `frontend/src/sites/SiteFindingIndex.tsx`,
  `frontend/src/shell/SiteAnalyticsFrames.tsx` (`SiteFindingsFrame`, `findingIndexScopeQuery`), `App.tsx`
  `siteFindingIndex`. Tests `frontend/src/shell/__tests__/s404SiteFindingIndex.test.tsx` (15); mutation (non-current
  rendered as empty) caught by 4, reverted.
- Walkthrough `tools/s404_finding_index_walkthrough.py`, evidence `tools/s404-finding-index-evidence.mjs`, owner doc
  `.agent/S4-04-owner-walkthrough.md`, evidence `.agent/S4-04-browser-evidence/`.

## Next
- Fresh Claude slice review of the whole branch (phase 1 + 2).
- When `fix/S4-deferred-match` merges to main: merge main here, rerun the S4 Finding focused command
  (`backend/TESTING.md`), confirm the H1 test still passes.
- Owner walkthrough, then merge and `sitefindings:1#a/#b` promotion.

## Open risks
- Dirty-day fixture read a FAILED job staged for the adjacent day (job reasons seem to be read across the day
  margin); fixtures were separated, not investigated.
- Engineering wording in the basis disclosure and reasons: for the W1 plain-language task.
- Temporary `.venv` junction and `var/sites/*.yaml` copies are removed at the end of this phase; the walkthrough
  needs them again (`var/sites/kobo-001.yaml`, `.venv`).
