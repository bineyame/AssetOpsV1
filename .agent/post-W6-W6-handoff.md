# post-W6 W6-global-Work handoff (build phase; captures and full suites held)

Branch `task/post-W6-W6-global` (worktree `AssetOpsV1-review8`, from main `821ad6bf`). Binding: `.agent/post-W6-W6-rulings.md`
(Q1-Q21), the amended W6 card, `.agent/post-W6-W6-preflight.md`, `.agent/post-W6-R373-rulings.md`.

## Landed (commits)
- `fe52c862` backend: `site_domain` on all four global list rows and detail `selected` (stored `site_type`); `links.site` via
  `estate/evidence_money.site_home_href` (EV -> `/sites/{code}/ev`), Site Work tab links unchanged (R352/R353); incident
  `linked_requests` [{label, href}] with `linked_request_ids` in the basis only when non-empty (R359); Site
  incidents/maintenance fallbacks carry `known_at` only for an explicit cutoff, `select_incidents` now passes `cutoff` (R360);
  global Action labels = stored `ACT-` code from `action`/`domain_action`, read pairs enter the basis as `action_codes` only
  when Actions exist, no code keeps `Action {id8}` (R366). Files: `work/{global_index,global_detail,operational_index}.py`,
  `work/adapters/postgres_global_read.py` (`linked_requests`, `action_codes`, `site_type`). Tests: `test_w601{a,b,c,e}`,
  helper `test_w502_domain_work_links_postgres.assert_global_domain_parity` (ACT relabel), `tools/w601_seed.py` linked
  self-check (finds the Action link by href, not the old label).
- `5685abad` frontend + guard: all frontend D3s (R352, R354, R356, R357, R359, R361, R364, R366, R367, R368, R370, R371,
  R372), Q7 window and membership lines, Q17/Q18 labels/form/plural/asset words, R371 App route
  `/maintenance/requests/:caseId/*` -> `WorkRequestUnknownSectionFrame` (in `workRequestShared.tsx`), guard rule in
  `tools/checks/navigation-truthfulness.ps1` (Get-OperatorRailFailures) with two fixtures in `navigation-rail-fixtures.ps1`.
- Register (handoff commit): R396 row; R73 screen + `incidents`; R65/R74 screens +
  `incidents`, `maintenance`, `wr-overview`.

## Visible labels (all 12 px `.global-work-deviation`, `data-mock-deviation`)
R73 + R358 in the Incident cases panel; R355 + R358 in the Corrective work requests panel; R362 (D4) inside the manual
reading form; R396 inside the Context tabs `nav` under the row; R363 inside the WR date bar; R365 in the Work done panel
and the Maintenance record panel; R369 in the History panel. Labels sit in chrome or panels because
`frontend/src/test/panelStructure.ts` rejects free blocks between panels; the helper was not loosened.

## Proofs done
- Backend focused: `test_w601{a,b,c,e}` 65 passed (after `fe52c862`, real Postgres `assetops_test`).
- Backend non-vacuity (single-file revert to `821ad6bf`, 11 new/changed tests): postgres_global_read 9 fail; global_index
  collection error (global_detail imports `coded_actions`); global_detail 3 fail; operational_index 2 fail; mutations: R360
  fallback pins watermark -> 2 fail; R359 IDs dropped from basis -> 1 fail; restored HEAD 11 pass.
- `test_r373_request_access.py` on this branch: 10 passed.
- Frontend: work + related sites + shell + test-helper suites 70 files / 1556 tests pass; `tsc --noEmit` clean.
- Frontend non-vacuity (single-file revert to `821ad6bf`, W6 test files): globalWorkClient 64 fail; globalWorkParts 96;
  GlobalIncidents 5; GlobalMaintenance 3; GlobalPreventive 1; OperationalRecords 3; workRequestShared 34;
  WorkRequestOverview 2; WorkRequestRecord 1; WorkRequestHistory 6; App.tsx 4 (the four R371 sections); restored 150 pass.
  CSS (R356, R364) is layout-only and unproven until captured.
- Guard: two new navigation fixtures fail against mutated App lines by construction; `check-all.ps1 -Python <main .venv>`
  11/11 PASS at `5685abad` + register.

## Remaining (held or not started)
1. Full real-Postgres backend suite at final SHA (keep-awake, 2x cap, JUnit zero skips).
2. Full vitest and production build.
3. All captures: 380 indexed pairs + link landings, R353 EV Site, R359 WR landing, R360 current/historical, R371 four
   unknown-section landings, R373 mini/cold/EV 403/200 at 1440/390, B19 refusal cases, EV current-day default window.
4. Q15 caps: measure final-SHA five-row/160-char closed peaks (capture-only DOM probe) for oprecords panels, Incidents Case
   boundaries, WR panels at 390; Architect ratifies. Q16 R356 `scrollWidth <= clientWidth` at 1440 and R364 390 tab wrap are
   unverified layout claims until captured.
5. Q19 registry-chain evidence for the packet (A-work-cases <- A-maintenance-index <- A-cold-work-projections; EV left open).
6. Review packet, CODE_STATE/ACTIVE_CONTEXT updates after captures.

## Caps fix round (closed)
Rulings `.agent/post-W6-W6-caps-rulings.md`. Commits `cf4a06d9` (rulings), `fff67f3e` (Feeds 125 + CellDisclosure), `ffcf6e13` (correction lines), `6f54ad1b` (Work request Finding/Action line), `ee1a0546` (q15b probe), then closeout (packet, CODE_STATE, ACTIVE_CONTEXT, b18r/b19r). Product is final at 6f54ad1b. Packet `.agent/post-W6-W6-packet.md`. Next step: fresh independent review.
