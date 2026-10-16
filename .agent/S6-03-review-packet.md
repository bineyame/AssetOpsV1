# S6-03 review packet - Site Work Action list

Task `tasks/S6-03-site-work-list.md` (incl. plan fix round 1). Branch `task/S6-03-site-work-list` from main `cdb09767`.
Authority: `.agent/architect-W1-remaining-answers.md` (S6-03), `.agent/architect-W1-remaining-q-answers.md` (1),
`D-2026-10-16-a-action-index`. USER_REVIEW_REQUIRED: **true** - independent review, then owner walkthrough
`.agent/S6-03-owner-walkthrough.md`, then merge. Review diff: `git diff cdb09767..HEAD -- ':!.agent'`.

## Outcome delivered

Site > **Work** (new tab) > **Actions** lists persisted Actions created at one tenant/Site in a half-open UTC window of
at most 31 days, newest-created first, from one REPEATABLE READ snapshot, or an explicit zero. Each row shows code,
origin Finding version (exact link), creation time, the lifecycle reduced by the same `actions.lifecycle.reduce` as
Action detail, and the latest step selected by `(recorded_at, id)` with an exact history link. Paging uses an opaque
cursor bound to tenant/Site/window/fence/last key; a changed fence refuses page two and the UI restarts at page one.
Without a window the page asks for one and reads nothing. IDs, fence and rules sit in "What this list is based on".
No owner, due date, priority, success criterion or verdict; Incidents/Maintenance not rendered.

## Files materially changed

- Backend: `actions/site_index.py` (new: request parse, cursor, fence, rows), `action_index_api.py` (new route),
  `actions/adapters/postgres_action_store.py` (`site_window`, SELECT only), `actions/service.py`
  (`selected_action_links` extracted from `ActionService._links`, detail unchanged), `main.py` (composition).
- Tests/fixtures: `tests/test_s6_site_action_index.py`, `tests/test_s6_site_action_index_postgres.py` (new),
  `tests/s6_action_records.py` (`second_created_after=`; default keeps the S6-01a contract),
  `tests/fixtures/s6_site_action_index_contract.json` (new, recorded API bodies for the frontend tests).
- Frontend: `sites/actionIndexClient.ts`, `sites/SiteWorkActions.tsx`, `sites/__tests__/siteWorkActions.test.tsx`
  (new); `shell/SiteAnalyticsFrames.tsx` (`SiteWorkFrame`), `shell/operatorSiteRoutes.ts` (`SITE_WORK_ROUTE_PATH`,
  `siteWorkHref`), `shell/operatorSiteTabs.tsx` (Work capability true), `App.tsx`, `test/settled.ts` (loading
  sentence); tab expectations in `operatorSiteTabs.test.tsx`, `siteDetailRoute.test.tsx`,
  `overflowContainment.test.tsx`, `tools/layout-evidence.mjs`.
- Tools: `tools/s603_site_work_walkthrough.py` (prepare|serve|attest|drop), `tools/s603-site-work-evidence.mjs`.

## Acceptance criteria

| Criterion (task) | Status | Evidence |
| --- | --- | --- |
| One snapshot, `created_at` window membership, latest event by `(recorded_at,id)` | Met | `site_window` one `_read` (RR, READ ONLY); unit `test_order_selection_paging_and_fence` (later-recorded backdated event selected); PG test backdated observation keeps row position |
| Row key, code, creation, origin Finding/Revision IDs, event ID/recorded time, canonical + exact links | Met | PG test asserts `key`, origin, links equal Action detail's `links` |
| Lifecycle = Action detail at same fence | Met | `same_fence_parity` (latest and `?event_id=`) on every listed row, before/after a new event |
| S6-02a RESOLVED / RESOLUTION_WITHDRAWN shown as recorded events, no list verdict | Met | `test_resolution_events_are_listed_as_recorded_with_detail_lifecycle` (real evaluator path; parity at both); UI shows step words only, test asserts no "Verified" |
| Order `created_at DESC, action_id ASC`; bounded page; opaque cursor bound to tenant/Site/window/fence/key | Met | unit tie-break test; PG page 1/2 on one fence; cursor decode refusal |
| Fence over all Site/window Actions and events incl. off-page, with counts | Met | `fence` = max created, max recorded, Action count, event count; PG + unit: an event stamped before the fence's max still invalidates (count); evidence: real-clock FAILED step stamped before the fence refuses page 2 |
| Echo scope/timezone, `read_at`, fence or explicit zero fence, total, next cursor; `CURRENT` only on success | Met | body fields; zero window `zero_rows: true`, counts 0 |
| Zero means only "no persisted Actions created here/window" | Met | `ZERO_STATEMENT`; UI "No Actions created at this site in this window"; independent SQL count in PG test and `attest` |
| 401/403/404; invalid/unbounded window, changed cursor, unavailable store, inconsistent snapshot typed, never empty | Met | PG test (401, 403, unknown Site 404, 422 x5, 409 FENCE/SCOPE_CHANGED, 503 no store and unreachable store); unit inconsistent snapshot 409 |
| Choose-window state for an unparameterised entry | Met | UI test: no request until a window is chosen; evidence `choose-window` |
| UI: Site/window in URL, count/page basis, exact FindingRevision and ActionEvent links, Unknown/error distinct, keyboard, no invented verification | Met | `siteWorkActions.test.tsx` (20 tests); evidence 56/56 |
| Phase 1 fixture: two Actions at distinct creation times, backdated later event, paging, wrong Site, changed-fence cursor, assessed zero | Met | `build(..., second_created_after=5 min)`; PG test |
| Parity rerun against S6-02a event kinds (S6-02a merged first) | Met | evaluator RESOLVED/WITHDRAWN test above; adjacent `test_s6_action_records/store/apply_postgres.py`, `test_s6_verification_evaluator_postgres.py` passed (see checks) |
| Owner walkthrough tool and steps | Met | tool run end to end at `4d9a89ca`: prepare, attest OK (2/2, 0/0), serve, evidence 56/56, owner step-6 snippet checked, drop |
| Statement-level writer rule 8 for new SQL | Met (no writer) | new SQL is SELECT only in the existing Action store; `check-all` Architecture seams PASS. Probe corpus not completed, see deviations |

## Checks run

- Focused backend (private `assetops_s603_test`): `test_s6_site_action_index.py` 15 passed;
  `test_s6_site_action_index_postgres.py` 2 passed (contract check mode); adjacent run: `test_s6_site_action_index*`,
  `test_s6_action_records_postgres`, `test_s6_action_store_postgres`, `test_s6_action_apply_postgres`,
  `test_s6_verification_evaluator_postgres` 46 passed / 3 failed - the 3 were "too many clients already" (shared
  Postgres exhausted by other agents' suites at the time); `test_s6_action_apply_postgres.py` rerun alone with the
  index tests: 14 passed.
- Frontend: `npx.cmd tsc --noEmit` exit 0. Full `npm.cmd test` at `4d9a89ca`: 69 files, 1631 tests passed (an earlier
  full run at `9e8f2bdc` failed only `siteDetailRoute.test.tsx` on the new Work tab; fixed in `4d9a89ca`).
- `tools/check-all.ps1` at `4d9a89ca`: all 9 guards passed (architecture, navigation truthfulness, agent workflow,
  dependency registry, missing-claim scan, screen ledger, fixtures).
- Layout: `node tools/s603-site-work-evidence.mjs` against the walkthrough at `4d9a89ca`: **56/56 claims** at 1440 and
  390 (positive rows non-empty, exact links, reload, zero, choose-window, paging, changed-list refusal and restart,
  step link opens history at that step, no page-level horizontal overflow, mockup `#/sitework` captured).
  `node tools/layout-evidence.mjs http://localhost:5463 KOBO-001` on the private walkthrough DB: 327 PASS, 2 FAIL,
  both pre-existing preconditions (a Lab Site with a 430 L tank; a legacy file Kobo Site) unrelated to S6-03.
- Full backend suite at `0696e744` (code identical to `4d9a89ca`): `pytest backend/tests -n 2 --dist loadfile
  --no-loadscope-reorder -q -p no:cacheprovider --junitxml=<scratchpad>/s603-junit.xml` on private `assetops_s603_test`,
  `var/sites/*.yaml` copied in (removed after): **2535 passed** in 1446.7 s (wall 1450 s, under the 30-minute cap); JUnit
  tests 2535, failures 0, errors 0, skipped 0. No other pytest ran at start; free memory 4.0 GB.

## Known deviations

1. Ports: the packet reserves 8943/5443; the build brief assigns this worktree 8963/5463. The tool defaults to
   8963/5463 (`--port/--web-port` override).
2. A served-clock artefact found in the walkthrough: an apply attempt on today's clock (before the fixture's November
   times) records a FAILED step that sorts BEFORE ACCEPTED in `(recorded_at, id)`. The first consistency rule
   (ACCEPTED must sort first) wrongly refused the whole list; it now requires only that an ACCEPTED step exists
   (`848fc8d8`, unit test added). The list still shows the latest step in recorded order, as detail does.
3. `tools/writer_guard_probes.py` was started twice but not completed (about 5 minutes per probe under shared load;
   S6-03 adds no writer or DDL). Its first run overlapped my commits and two probe mutations
   (`scheduling/.../postgres_schedule_store.py`, `evidence/.../postgres_gateway_access.py`) were swept into
   `589d9258`..`e8ed0247`; `e473ba0c` restores both files to main exactly (`git diff cdb09767..HEAD` touches neither).
4. Owner wording copy: "not available yet" phrasing is avoided (the missing-claim scan has no catalogued `sitework`
   gap); missing owner/due/incidents are stated as "not recorded" / "not part of this list".
5. Each row's Action link reads "<code> · Battery reserve trial", as the Action page title does; it is the only
   Action kind in W1 and is not read from the index body.

## Residual risk

- The read loads every Action and event of the window into memory (31-day bound); fine at W1 volumes, would need SQL
  paging with the same fence for large Sites.
- The fence detects any change in counts or max times; an in-place mutation cannot occur (append-only writer).
- Registry nodes `I-site-action-index-read`, `I-sitework-ui`, `I-S6-03`, `sitework:1#a` are left open for review.

## User-review focus

Does the Work > Actions list show the right rows and links, state an empty window honestly, refuse rather than
mislead when the list changes, and keep IDs out of the default reading? Wording polish is for the W1-conclusion task.
