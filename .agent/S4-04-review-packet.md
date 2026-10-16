# S4-04 review packet - Site Finding index and list (slice review)

Task: `tasks/S4-04-site-finding-index.md` (status `in_review`). Branch `task/S4-04-site-finding-index`, base main
`f8a131e3`. Phase 1 handoff `.agent/S4-04-phase-1-handoff.md`; phase 2 handoff `.agent/S4-04-phase-2-handoff.md`.
USER_REVIEW_REQUIRED: true - merge and `sitefindings:1#a/#b` promotion held for the owner walkthrough
(`.agent/S4-04-owner-walkthrough.md`).

## Outcome delivered

- Phase 1: `GET /api/sites/{site_code}/finding-index` (see phase-1 handoff for contract and anchors).
- Phase-1 review H1 folded in: discovery now also crosses a UTC edge when the edge day's selected S3 Candidate
  segment lies within 20 min of it (`analytics/finding_index.py` `candidate_reach`, `discover(edge_reach=)`), to a
  fixed point under the same 62-day cap. Defence in depth only: the root fix (matcher pass recording a deferred
  window as matched) is on `fix/S4-deferred-match` and not touched here (coordinator direction).
- Phase 2: imported-Site Site > Findings over the index. Scope (`domain`, `from`, `to`, `limit`, `cursor`) lives in
  the URL; default is today's UTC day. States: loading; CURRENT empty ("No Findings in this window" + basis);
  CURRENT rows (period, Finding link to the exact `?revision_id=`, lifecycle/transition, version, relations,
  "No amount shown"); PENDING/UNASSESSED/STALE/FAILED, closed gate, continuity limit, changed basis (restart link),
  invalid scope, sign-in, forbidden, unavailable - all with no rows, no count and no "no Findings" claim.
  Pagination and every Finding are links (keyboard operable). A 404 (no imported Site) keeps the older T028
  summary unchanged as the fallback; it is not relabelled.
- Walkthrough tool and owner doc; browser evidence at 1440/390 in four stages.

## Files materially changed (phase 2)

- `backend/assetops_backend/analytics/finding_index.py` (H1), `backend/tests/test_s4_finding_index_postgres.py`
  (H1 probe test).
- `frontend/src/sites/findingIndexClient.ts` (new typed client), `frontend/src/sites/SiteFindingIndex.tsx` (new
  view), `frontend/src/shell/SiteAnalyticsFrames.tsx` (`SiteFindingsFrame` URL scope + fallback), `frontend/src/App.tsx`
  (`siteFindingIndex` prop).
- Tests: `frontend/src/shell/__tests__/s404SiteFindingIndex.test.tsx`, `frontend/src/sites/__tests__/findingIndexFixtures.ts`;
  `t028Screens`/`t028Vocabulary` now name a not-imported Site explicitly.
- `tools/s404_finding_index_walkthrough.py`, `tools/s404-finding-index-evidence.mjs`.
- Evidence: `.agent/S4-04-browser-evidence/` (screenshots, claims JSON, API responses, manifest).

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Read contract (scope, 422, gate 409, continuity 409, cursor 409/422, no-snapshot statuses, order, exact links, amount unavailable) | Met (phase 1) + H1 | phase-1 handoff; `test_s4_finding_index_postgres.py` 10 tests |
| H1: S3 Candidate near an edge pulls the neighbour; stale -> no claim; reassessed-before-rematch -> no claim; rematch -> CURRENT/1; injected cap via the new source | Met | `test_s3_candidate_near_an_edge_reaches_a_neighbour_the_matcher_skipped`; mutation `edge_reach=None` fails it (`['2026-10-25'] != ['2026-10-25','2026-10-26']`), reverted |
| UI URL-persisted scope, date change makes a new read, reload keeps page | Met | s404 tests "defaults", "changing the dates", "next page"; browser page 2 loaded from the address alone |
| Assessed empty (#a) with watermark | Met | test + browser `empty` 1440/390; `api-empty.json` |
| Positive rows (#b), order = API, exact revision links, relations, no amount | Met | test + browser `positive`; order claim vs manifest |
| Unknown/stale/failed/closed/continuity-limit/invalid: no rows, no count, no zero claim | Met | `it.each` (8 states); browser variants and `closed` stage; mutation (non-current rendered as empty) fails 4 tests, reverted |
| Cursor invalidation and restart | Met | test "changed basis"; browser `late` and `settled` old page-2 -> `basis-changed` |
| Pinned detail/history after a newer revision | Met | browser `settled`: `ef37d258` revision `0057e42e` opens after `47385b1b` exists; history opens |
| Legacy summary not relabelled | Met | test "no imported record" |
| Walkthrough prepare/serve/late/settle/gate/drop, private DB/ports | Met | prepare 178 s, 0 failed checks; all stages run (below) |
| S5-01 card parity | Met (phase 1 test) | phase-1 handoff |
| Owner visual/copy acceptance | Pending | owner walkthrough |

## Checks run (final code revision `38c61cfd`)

- `npx.cmd tsc --noEmit`: clean. `npm.cmd run build`: built.
- `npm.cmd test` (full frontend): see "Suites" below.
- `tools/check-architecture.ps1`: passed. Registry checker `node frontend/docs/architecture/check_v69_dependency_registry.cjs`:
  exit 0, "Registry valid: 228 nodes, 11 linked pilot panels".
- Focused backend: `test_s4_finding_index_postgres.py` 10 passed (58.8 s).
- Walkthrough `prepare` exit 0 (178 s): positive CURRENT 3, empty CURRENT 0, dirty STALE_PROJECTION, failed FAILED,
  unassessed UNASSESSED, page 1 = 2 rows + cursor, page 2 = 1 row; Performance gate OPEN.
- Layout/browser evidence `node tools/s404-finding-index-evidence.mjs http://localhost:5434 <stage> ...` at 1440x1000
  and 390x900: initial 54/54, late 12/12, settled 14/14, closed 14/14 claims passed; every page has zero
  page-level horizontal overflow; row claims measured non-empty sets (3 rows, then 4).

## Suites

SUITES_PLACEHOLDER

## Known deviations

- Row link text is the product lifecycle title (`LIFECYCLE_WORDS[...].title`), not the stored Finding title: the
  stored titles contain "running", which the product-vocabulary scan bans on product screens.
- Default window when the URL has none is today's UTC day; the URL is not rewritten until the owner changes it.
- The window form is whole UTC days; a non-midnight `from`/`to` in the URL is honoured and stated, but the form
  rounds to days on submit.
- Walkthrough fixtures: dirty 2026-10-27 and failed 2026-11-05 are kept apart because a failed job for an adjacent
  day was read for the dirty day (first attempt put failed on 2026-10-28 and the dirty day read FAILED). Worth a
  look by the reviewer: job reasons appear to be read across the day's tolerance margin.
- `late` adds a new Finding (16:00-16:40) rather than extending an existing one; the newer-revision proof uses the
  provenance revision the settle pass wrote for `ef37d258`.
- Phase-1 deviations stand (bridge from stored episodes plus now S3 segments; cap proven by injection; UTC display).

## Residual risk

- H1 guard is index-side only; correctness also depends on the upstream deferred-match fix merging to main
  (then merge main here and rerun the focused index tests).
- Copy is engineering-plain in places ("Selection token", per-day basis table, raw reason strings in the
  disclosure); log for the W1 plain-language task.

## User-review focus

Assessed-empty wording and basis disclosure; "Not known / Not current" pages; row columns (period, version,
related, "No amount shown"); restart message; omitted mock elements (lens chips, "N open", global link, badges,
sample money).
