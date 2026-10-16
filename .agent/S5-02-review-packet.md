# S5-02 review packet - Finding list in the Site Overview

Task: `tasks/S5-02-overview-finding-list.md` (one build phase). Branch `task/S5-02-overview-finding-list` from main
`5c1d9d42`. Folded in: Architect `D-2026-10-16-s502-parity` (`.agent/architect-S5-02-answers.md`) and plan review
Lows L1-L4 (`.agent/S5-02-plan-review.md`). USER_REVIEW_REQUIRED: true (slice review, then owner walkthrough
`.agent/S5-02-owner-walkthrough.md`; merge and `mini:3#a/b` promotion wait for the owner record).

Commits: `261cf751` (frontend + tests + packet citation), `040204cd` (walkthrough wrapper + evidence script), and
the closeout commit (task status, ACTIVE_CONTEXT, CODE_STATE). Review range: `git diff a88d3e8a..HEAD -- ':!.agent'`.

## Outcome

The imported Site Overview's "Findings" panel now reads the S4-04 index for the served UTC day
(`GET /api/sites/{site_code}/finding-index?domain=mini-grid-dispatch&from=window.start&to=window.end&limit=2`) and
replaces the visible `finding_list: UNAVAILABLE` placeholder. CURRENT+is_current zero says "No Findings for this day"
with inspected days and token; non-current reads and every refusal say Not known/Not current with reasons and no
count; CURRENT rows list in index order with exact revision links, a first-page notice and a full-list link with
the identical window. The first row is compared with the Overview's known Finding only under the Architect rule.
No backend change.

## Files materially changed

- `frontend/src/sites/OverviewFindingList.tsx` (new): read, states, `compareParity`, `OVERVIEW_FINDING_PREVIEW_LIMIT = 2`.
- `frontend/src/sites/SiteWindowOverview.tsx`: `WindowOverviewLinks.findingList?`, props `findingIndex?`/`onReload?`;
  the list replaces the placeholder only when the shell supplies both.
- `frontend/src/sites/SiteOverview.tsx`: `findingIndex?` prop, reload counter (`reload()` clears `answered`).
- `frontend/src/shell/SiteDetailFrame.tsx`: injects the client (default `createFindingIndexClient()`) and
  `findingList` href via `siteFindingsHref` + `findingIndexScopeQuery` (L2); `App.tsx` passes `siteFindingIndex`.
- `frontend/src/sites/SiteFindingIndex.tsx`: exports `STATUS_WORDS` and `Basis` (shared vocabulary; no behaviour change).
- Tests: `frontend/src/shell/__tests__/s502OverviewFindingList.test.tsx` (new, 22 tests);
  `s5WindowFixtures.ts` (summary builders moved out of the S5-01 test); `s5SiteWindowOverview.test.tsx` uses them and a
  stub index client; its unassessed case now asserts the list's no-claim state.
- `tools/s502_overview_finding_list_walkthrough.py` (new, L1), `tools/s502-overview-finding-list-evidence.mjs` (new).
- `tasks/S5-02-overview-finding-list.md`: citation `read.py:214` (L4); status.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Request: canonical Site, domain, served `from/to`, first page, bounded limit; re-read on day change; older answer ignored; no request for legacy Overview | Met | tests "reads the index with the Overview's served day...", "a legacy ... issues no index request", "a date change ... late answer never appears"; live 2026-10-15 -> next day |
| URL keys and known Finding pin preserved; row link opens exact revision | Met | tests; live Back/reload claims keep `date`+pin |
| Current zero (#a) only on CURRENT, is_current, total 0, token, watermarks; basis incl. neighbour days; full-list link | Met | test "states the assessed zero..."; live 2026-10-25 `current-empty` both widths |
| Pending/unassessed/stale/failed, deferred matched window: Unknown with reasons, no zero/count | Met | `it.each` x4 + "CURRENT status that is not is_current"; live 10-30/10-27/11-05 |
| Positive (#b): rows in index order, title/period/lifecycle, version + revision ID, exact links, token, count, first-page statement, full-list link; no money/priority/action | Met | test "lists persisted rows..."; live order equals API, "Showing the first 2 of 3" |
| Parity (D-2026-10-16-s502-parity): positive, retained pin, differing basis, same-basis ID mismatch | Met | four UI tests; live positive `same` (manifest `positive_parity.equal: true`), and again after `settle` |
| Refusals 409 closed / continuity / basis changed, 401, 403, 422, unavailable: typed, no rows/count; Overview sections stay | Met | `it.each` x7; live `gate --close` 16/16 |
| Date change and reload do not resurrect old rows | Met | test + live date-change and reload claims |
| Native links/buttons, focus order, Enter opens revision, Back returns at 1440/390 | Met | test (focus + click); live CDP Enter key + `history.back()` both widths |
| Walkthrough wrapper: S2 comparison after prepare, imported Overview proven for every day | Met | prepare: `Evidence cutover: permitted`, `0 Overview check(s) failed` |
| 1440/390 app vs mock captures | Met | `s502-*-{desktop,narrow}-*.png`, `s502-mock-{desktop,narrow}-mini.png` in `%TEMP%\s502\evidence` (local, not committed) |

## Checks run (final code revision `040204cd`; closeout touches only docs)

- Focused: `npx.cmd vitest run` s502 (22 passed), s5SiteWindowOverview (28), s404SiteFindingIndex + siteOverviewScreen + overviewDispatchAssessment (with s5: 62 passed).
- `npx.cmd tsc --noEmit`: clean. `npm.cmd run build`: exit 0 (chunk-size warning only).
- Full frontend `npm.cmd test`: 67 files, 1594 tests passed, 117 s, no timeouts.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. `tools/check-all.ps1`: All 9 guards passed.
- Backend: no code change, so no full backend suite (packet phase 1).
- Walkthrough (DB `assetops_s404_owner_s502`, API 8952, web 5452): `prepare` exit 0 (S4-04 checks + S2 comparison + 5 Overview days); browser evidence `initial` 60/60, `late` 8/8, `settled` 8/8, `closed` 16/16; `gate --open`; `drop` done.
- Non-vacuity: the parity tests split outcomes (`same` vs `not-compared` vs `different`) on single-field changes; the date-change test resolves the old day last and asserts its rows are absent.

## Known deviations

1. Fixture prefix: the walkthrough uses `assetops_s404_owner_s502` / `var/s404_owner_s502` (the S4-04 tool refuses other prefixes), not `assetops_s502_*`.
2. Parity comparability is strict: the Architect's "where supplied" fields (run, assessment record, hashes, model, match pass, matched-through) must be present on both reads and equal, else no claim (fail closed).
3. The row shows the lifecycle label, not the raw `claim_level` code (the product-vocabulary scan rejects the code). Copy still says "window" in the shared S4-04 sentences; wording is for the W1-conclusion task.
4. The backend still emits `finding_list: UNAVAILABLE` and the client validator still requires it; the UI only stops showing it when the shell supplies the index client.
5. Live walkthrough shows only the `same` parity outcome; retained-pin, differing-basis and ID-mismatch are proven in component tests (the fixture has no natural way to produce them).
6. `var/sites/kobo-001.yaml` had to be copied into this worktree (gitignored precondition) before `prepare`.

## Residual risk

- The two reads are separately fenced; a reload between them can still show different bases (handled by the no-claim path, not prevented).
- "Reload both" re-reads the whole Overview (loading state flashes) rather than only the list.
- Preview limit 2 is fixed; a day with many Findings always needs the full-list link.

## User-review focus

The Findings panel on 2026-10-15 (rows, first-page notice, comparison line) and on 2026-10-25/10-30 (zero vs not
known), at desktop and phone width; follow `.agent/S5-02-owner-walkthrough.md`.
