# W5-EV-Work handoff (PARTIAL: code and focused tests done; captures, caps, proofs, packet, state docs remain)

Branch `task/post-W6-W5-EV-work` from main 104e9c33. Binding: `.agent/post-W6-W5-rulings.md` 3-5, `.agent/post-W6-W5-EV-preflight.md`, UI guide. Register range R470-R479 (none used so far).

## Landed (4 commits, all frontend tests green on the touched files; `npx tsc --noEmit` clean at last edit)
1. R345 availability: `EvAvailability.tsx` `connectorHoursText` uses `plural` (imported from EvAssessmentViews) and hour/hours; cards render `{hoursText} connector-h` via `connectorHoursValue` (span `data-ev-connector-h`, `title` = exact `X h Y min`).
2. R244 depth refusals: `EvDepthRefusal` (EvAvailability.tsx) is now RefusedHead + RefusedGap + correction link `Read without a selected window` (`data-ev-depth-correction`, window refusals only, keeps known_at) + `Reload` (503, 409, unreachable; `data-ev-depth-retry`). Mounted by Availability (4 tiles), Energy (4 tiles), Health (panel "Condition and evidence"), Scenarios (`ScenariosRefusal` removed; panel "Financial scenarios"). CSS `.ev-depth-refusal__*` in `w2-ev-assessment.css`. Constants `EV_WINDOW_INVALID_TEXT/TOO_LONG_TEXT` exported from EvAssessmentViews.
3. R346: `bridgeRows` guarded (WITHHELD + null quantity) row 1 = metered kWh; stored null stays Unknown; visible `MOCK DEVIATION D1 (R06)` line (`data-mock-deviation="R06"`) under the Energy chart. Backend: `MONEY_COPY["STALE_BASIS"]` = "No stored gross tariff estimate matches the current evidence." (ruling 5) and `test_w207_ev_site_reads_postgres.py` expectation updated.
4. R347: `ReportSelected` context + `useReportSelectedWindow` in `sites/evSelectedWindow.ts`; `EvDepthPage` provides it (availability/energy), Scenarios and Health report. `SiteHealthFrames.tsx` EV uses `EvHealthWithTabs` (EV_SITE_TAB_HREFS + reported window). `evWorkTabHrefs`/`evWorkTabSearch` in `shell/evSiteRoutes.tsx` feed the two Work mounts in SAF (explicit valid URL window only; cold keeps `coldTabSearch`). ev-action keeps no Site tab row.
5. R348/R349/R350 in SAF `DomainActionShell`/`DomainActionRoute`/new `DomainActionUnknownSection`: `actionWindowRefusal` (evWorkPresentation.ts) gates EV windows (state `window_invalid`, no read, no link carries it, link `Open this Action without a window`); `evActionRefusal` + presentation fields `reloadLabel`, `technicalDetail`, `headings` (R349, EV only; cold unchanged); W1-only sections (plan/execution/evidence/history) on cold and EV render "Page not available / This address is not served" with `Open this Action's verification` (valid known_at and valid EV window kept), no read or redirect. Bare route still redirects (R222).
6. R373: `tools/w504_ev_work_walkthrough.py` Site Work router now passes `M.build_work_service(url)` and `details=M.build_work_detail_service(url)`. Backend scoped run (env: PYTHONPATH must include this worktree's contracts, backend, simulator, host, gateway; venv `../AssetOpsV1-plan2/.venv`; `ASSETOPS_TEST_DATABASE_URL=...assetops_test`): `test_w504_ev_work_cases.py` 18 passed; `test_w504_ev_intent_api.py` + `test_w207_ev_site_reads_postgres.py` 25 passed (8m12s). No route-list expectation needed changing.

Tests added/updated: evDepth (refusal matrix incl. one-sided, units, title, tabs), evEnergy (refusal, bridge, R06, tabs), evHealthDepth, evScenarios, evWorkActions and evWorkCases (Work tabs), domainActionVerification (R348 window 4 kinds, R349 matrix, R350 EV+cold), operatorRouteFrames (409).

## Remaining
1. Revert proofs (product file to HEAD~N, run its test, `git checkout --`): EvAvailability, EvEnergy, EvHealthDepth, EvScenarios, evSelectedWindow/EvAssessmentViews, SiteHealthFrames, evSiteRoutes, SAF (R348/R350), evWorkPresentation, ev_site_reads.py.
2. Caps (guide section 1; 5-row 160-char probe, 50*ceil(peak*1.15/50), ruled: ev-health Condition and evidence 400/800, ev-work Actions at this site 550/800; unruled panels provisional) on the real mounted page at 1440/390.
3. Captures with unmodified producers at 1440 and 390: `tools/w504_ev_work_walkthrough.py --work var/w504a_<tag> --tag <tag>` (fresh `ASSETOPS_WORK_CURSOR_KEY_HEX`; W6 Q20 R373 landing: EV case detail from ev-work-incidents/maintenance rows), batch-16/17 harness under `.agent/post-W6-audit/batch-16|17/tools` (mk_targets.py, capture-b16/b17.mjs; see `.agent/post-W6-W5-cold-recapture/tools/run_ev.sh` for the pattern: one Vite on a free port, `ASSETOPS_CDP_PORT`, stop by PID). Cover: 124 indexed pairs (depth 64, ev-work 24, ev-action 36), one-sided and >31-day URLs on the four depth pages and ev-action, R350 landings (bare, /verification, /overview, /execution, /history, /plan, /evidence) for EV and cold (w502 producer), EV case-detail landing, Energy/EV Overview/EV Financials stale-basis copy. Gaps (selected-DTO tests): unknown, pending, stale, missing-meter, historical depth, authored scenario, non-Open Action states.
4. Full vitest (long: run in background; flaky timeouts under load, rerun file), `npx tsc --noEmit -p .`, `npm run build`, `tools/check-all.ps1` via `powershell -ExecutionPolicy Bypass` with `-Python ..\AssetOpsV1-plan2\.venv\Scripts\python.exe`.
5. Packet `.agent/post-W6-W5-EV-packet.md` (Choices made below, capture gaps, provisional caps), register rows (R345-R350 closed in place after captures, R06 label noted; no new rows so far), `.ai/CODE_STATE.md`, `.ai/ACTIVE_CONTEXT.md`.
6. Clean up: PIDs, DBs created (`<prefix>_audit*`), var/ work folders. None created yet.

## Choices made so far (guide-covered; for the packet)
- C1 (sec 4): connector-h decimal value with exact `X h Y min` in title; reuse `plural`.
- C2 (sec 3): depth refusal mapped by code/status, one alert, raw code only in the `Technical detail`-style disclosure (existing `RefusedGap` disclosure); Reload also on 409 (its copy says reload), not 401/403/404/422.
- C3 (sec 3): window correction is a link `Read without a selected window` (same path, keeps `known_at`).
- C4 (sec 3/4): ev-action h1s `Loading Action…` / `Action not found` / `Action unavailable`; EV refusal panel keeps its bold `EV work unavailable` title except `Window cannot be read`.
- C5 (sec 5): R06 visible D1 label, no new row.
- C6: no Site tab row on ev-action (mock root is Actions).
- C7: Work tabs carry only a valid explicit URL window (not the implicit 7-day default).
- Health refusal has no tile labels (its tiles depend on the read); Scenarios/Health keep their single panel.
## Open risks
- SAF `window_invalid` also applies at the bare route (no redirect), a small extension of R348.
- evWorkPresentation now imports constants from EvAssessmentViews (heavier module); fine for tsc/tests, check build.
- Producer change (R373) is unverified by a live run until the capture.

## Update 2026-10-26: COMPLETE. Remaining steps 1-6 done; see `.agent/post-W6-W5-EV-packet.md`.
