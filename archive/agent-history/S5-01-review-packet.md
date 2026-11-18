# S5-01 review packet - selected-window Site Overview (slice review)

Task `tasks/S5-01-site-overview.md` (status `in_review`, USER_REVIEW_REQUIRED: owner visual acceptance before merge
or `mini:1#a/2#a/4#a` promotion). Branch `task/S5-01-site-overview`, stacked on LR-01 (merged in at `e8d555bc`, its
fix rounds 1 and 2). Phase 1 build `c21f279f`/`91415b18` (handoff `.agent/S5-01-phase-1-handoff.md`); phase 2 from
`440a2bad` to the head named under Checks. Slice diff: `git diff 394a9135..HEAD`; phase 2: `git diff 440a2bad..HEAD`
(includes the LR-01 merges; S5 files listed below).

## Outcome delivered

- Imported KOBO-001 at `/sites/KOBO-001?date=YYYY-MM-DD[&finding_id&finding_revision_id]` shows one UTC day: day
  freshness (Unknown/Pending/Out of date/Failed/Current, typed reasons, source gate), operating objective with an
  exact Dispatch link, a day timeline (assessed periods and reading spans, CSS bars), accepted-reading context with
  per-record links, one bounded Finding fuel-cost card, and "Unavailable until the Site Finding index is delivered."
- Amount only for server `PRICED` with both display bounds; every no-amount state is named, with the raw LR-01 money
  gate and upstream status shown separately. Demonstration label (P01 and, per the Architect M3 ruling, P02) shown.
- The served day and Finding version are written into the address (replace) and survive reload; a day change drops
  the pin. Legacy Sites keep the old Overview body unchanged.
- Repeatable owner walkthrough `tools/s5_overview_walkthrough.py prepare|serve|attest|tick|stop-schedule|start-schedule|gate --close|--open|drop`
  and owner doc `.agent/S5-01-owner-walkthrough.md`.

## Files materially changed (S5-01 phase 2)

- UI: `frontend/src/sites/SiteWindowOverview.tsx` (new), `SiteOverview.tsx` (URL selection, S5 branch),
  `siteOverviewClient.ts` (`site-window-summary-1` types/validator, date/pin query), `shell/SiteDetailFrame.tsx`
  (exact destinations), `ui/primitives.css`; test `shell/__tests__/s5SiteWindowOverview.test.tsx` (28 cases).
- Backend: `site_overview/read.py` (review M1/M2/L3/L7, `PinNotFound`, seam `current_amount_permitted` conjunct,
  interval spans), `route.py` (L1 typed 503, L2), `composition.py` (L4 one seam), `main.py` (startup fix, below);
  tests `test_s5_overview_read.py`, `test_s5_overview_postgres.py`.
- Tools: `tools/s5_overview_walkthrough.py`, `tools/s5-overview-evidence.mjs`.

## Acceptance (phase-2 row and owner walkthrough)

| Criterion | Status | Evidence |
| --- | --- | --- |
| URL-persisted UTC date selector; reload keeps date and IDs | Met | vitest "writes the server's default day...", "reloads with the day and the pinned Finding version", "changes the UTC day, drops the Finding pin"; browser `initial` reload and Next-day claims, both widths |
| Responsive objective/context/timeline/money at 1440/390 | Met | `s5-overview-evidence.mjs` no page overflow at every stage and width (90/90 claims); screenshots `var/s501-evidence/` (local, gitignored) |
| Explicit Unknown and all no-amount states | Met | vitest `it.each` over all 15 no-amount states; browser ordinary (QUANTITY_UNAVAILABLE), Unknown, Failed, withheld, pending (UPSTREAM_STALE + gate PENDING_REASSESSMENT), stopped (SCHEDULE_STOPPED), closed (SOURCE_CLOSED) |
| Exact drill-downs; Finding list unavailable, not empty | Met | vitest priced case checks Finding, Financials (`consequence_revision_id`), assumption, evidence record and Dispatch `revision` hrefs; browser checks list text on every page |
| React derives no status/amount | Met | UI reads `money.state`/`freshness.state`; mutation: dropping the `state === "PRICED"` test fails "never shows an amount the server did not price"; renaming the UNASSESSED word fails the Unknown test |
| No unsupported mock claims | Met | No totals, savings, battery/service health, renewable or recommendation panels; vocabulary scan passes |
| Owner walkthrough tool and doc, P01 settled neighbourhood, stops instead of promising | Met | `prepare` 0 failed checks (5 day checks through the served API); follow-ups exercised end to end (sequence below) |
| Legacy tests green | Met | `siteOverviewScreen`, `overviewDispatchAssessment`, `t028Screens`, `t028Vocabulary` 51/51; full vitest below |

Browser sequence (fresh `prepare`, HEAD `1dc1df1e` tree, then `05869379` for `initial`): initial 46/46, pending 8/8,
eligible 10/10, stopped 8/8, closed 8/8, eligible after reopen 10/10. Claims JSON and the step log with the final API record
(watermarks and IDs) are committed in `.agent/S5-01-evidence/`; screenshots stay local in `var/s501-evidence/`
(the `initial` screenshots there predate the day-navigation change from buttons to links; the `initial` claims were
re-run at `05869379`, 46/46, after it); P01 after `attest` read `STALE_PROJECTION`/`UPSTREAM_STALE` (N5), and after
`tick` `PRICED 15.82 P01-power`.

## Phase-1 review folded in (`.agent/S5-01-phase-1-review.md`)

M1 pin must intersect the day (`NOT_IN_SELECTED_DAY`); M2 closed source honours only an exact pin, no discovery
leakage (`excluded`/`several_intersect` blank when retained); L1 typed 503 `SITE_STORE_UNAVAILABLE`; L2 `PinNotFound`;
L3 distinct `previous_pin` reasons, also top-level; L4 S5 reuses the seam's consequence read and Finding store; L7
`FINDING_NOT_READABLE`; L6 route tests for no comparison reader, legacy `date=` through the route, a Site outside the
tenant's ledger scope. Mutations (each reverted with `git checkout`): M1 check removed 1 failed; M2 bare-pin rule
removed 1 failed; retained `excluded` blanking removed 1 failed; seam `current_amount_permitted` conjunct removed
1 failed; `add_event_handler` restored 1 failed (startup test).

## Checks run

- Full backend suite, revision `05869379` (final code revision; later commits are docs only), keep-awake running,
  cap 20 min: `$env:ASSETOPS_TEST_DATABASE_URL=".../assetops_s501_test"; .venv\Scripts\python.exe -m pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=.pytest-junit.xml`
  -> 2226 passed in 633.8 s (wall 634 s); JUnit tests 2226, failures 0, errors 0, skipped 0.

- `pytest test_s5_overview_read.py test_s5_overview_postgres.py test_s4_assumption_read_api.py -n 2`: 61 passed
  (after the LR-01 fix-2 merge); with `test_s4_schedule_upstream_unit.py test_lr01_money_eligibility_postgres.py`:
  39 passed (after fix-1 merge).
- Frontend: `npx.cmd tsc --noEmit` clean; `npm.cmd test` (vitest) 63 files, 1513 passed at `05869379`; `npm.cmd run build` passed.
- `tools/check-all.ps1`: all 9 guards passed at `05869379`.
- Layout: `node tools/layout-evidence.mjs http://localhost:5425 KOBO-001` on the private store: 327 PASS, 2 FAIL, both
  store preconditions unrelated to S5 (no 430 L Lab tank; no legacy file Kobo on a registered-KOBO store). A first run
  found "no enabled action renders" failing on the Site page (Previous/Next day buttons); day navigation became links
  and the claim passes. The default `MG-001` run is not meaningful on this store (Site absent).

## Known deviations

1. LR-01 seam fields: S5 keeps its own typed precedence (it needs the named state, and reads the gate from its own
   exact consequence read for the head fence) and adds the seam's `current_amount_permitted` as a further conjunct
   (`head_matches_seam`); a disagreement gives `CONSEQUENCE_STALE`. `seam_upstream_status`/`seam_current_amount_permitted`
   are reported in `money` for audit.
2. Phase-1 deviation 3 stands and is shown, not hidden: after `attest` and before `tick` the card says "Upstream out
   of date" (`UPSTREAM_STALE`) while "Money gate" says "Pending reassessment"; the walkthrough explains why.
3. N5: P01 loses its amount between `attest` and `tick` (P02 lies in P01's six-hour bracket); fail-closed, documented.
4. Schedule thresholds are production (300 s / 900 s). With no OS schedule installed, amounts disappear five minutes
   after the last `tick` (`SCHEDULE_STOPPED`); the walkthrough says so. `stop-schedule` ages the private heartbeat and
   Site head by SQL on the private database (walkthrough-only) so the stop is visible at once.
5. Review L5 not moved: the closing accepted-source fence is still taken before the Finding/money reads; the head
   fence and `is_latest` keep the amount consistent with the seam snapshot (reviewer: not a mixed-CURRENT hole).
6. Review L6 Postgres merge and exact-midnight cases are proved with fakes only (the LR-01 fixture has neither a merge
   nor a midnight-ending episode); the reviewer judged the risk low.
7. Phase-2 findings fixed in phase-1 code: `main.py` called `app.add_event_handler`, which FastAPI 0.141 lacks, so
   the app could not start with a database (now `app.router.on_shutdown`, with a start/shutdown test); timeline
   intervals carried the day window instead of their stored span (`result.interval.first_on/last_on`).
8. The S4 `UNPRICED` state remains unit-only (phase-1 deviation 7).

## Residual risk

- Ticks in the walkthrough use the `default` environment the app reads; LR-01's own walk ticks `lr01-walkthrough`.
- The timeline draws periods from `first_on/last_on`; an interval with no `last_on` draws to the day end.

## User-review focus

Run `.agent/S5-01-owner-walkthrough.md`: the no-amount wording for each state (especially step 6's two facts), the
P01/P02 demonstration labels and exact links, and the 390 px layout. Hold merge and registry promotion until the
owner record exists.
