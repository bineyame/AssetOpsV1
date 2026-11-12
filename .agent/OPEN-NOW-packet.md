# OPEN-NOW review packet

Task: card OPEN-NOW, `.agent/architect-sequence-client-scope-2026-11-11.md` lines 36-41. Spec: portfolio-layout proposal ~581. Context: PB-1c packet (Work pages default to the last 7 full days).
Branch `task/OPEN-NOW-work-read` from main `8a4b4fe4d`. Build commit `df60697a1`. Worktree `C:\Users\assef\Bineyame\AssetOpsV1-opennow`.

## Outcome
- Backend: `open_now = {incidents, requests, line}` on the global `/api/work/incidents` and `/api/work/maintenance` responses and on both Site Work list responses (`/api/sites/{code}/work/incidents|maintenance`). Counted on the list's own snapshot, at the list's K (`known_at`, or the cursor's K on page two), over the list's admitted Sites, with no date filter (`eligible_cases` with the widest bounds, then `reduce_state` in OPEN / IN_PROGRESS). Not in the selection token, so cursors are unchanged.
- Words are server-side (`work/open_now.py`): "Open now: 2 incidents, 1 request, whatever the dates"; a kind with zero is left out; all zero is "Nothing open now".
- Contract: `contracts/assetops_contracts/work_open_now.py` (`OpenNowCounts`, `OPEN_STATES`, `OPEN_NOW_KEYS`); TS type `OpenNow` in `frontend/src/work/openNow.tsx`, optional on `GlobalIncidentsBody`, `GlobalMaintenanceBody` and `WorkIndexBody`.
- Frontend: `OpenNowLine` above the list in the cases panel on global Incidents, global Maintenance (Corrective) and Site Work Incidents/Maintenance (also above the empty-window card). It renders the server line only; with no `open_now` it renders nothing.

## Files
backend/assetops_backend/work/{open_now.py (new), site_index.py, global_index.py}; contracts/assetops_contracts/work_open_now.py (new); frontend/src/work/{openNow.tsx (new), globalWorkClient.ts, GlobalIncidents.tsx, GlobalMaintenance.tsx}; frontend/src/sites/{workClient.ts, siteWorkCases.tsx}; tests: backend/tests/test_open_now_postgres.py (new), test_w601a/test_w601b (envelope set + `open_now`), three frontend test files.

## Acceptance
- Counts on the existing list responses, no new endpoint: done.
- No date filter, same known_at and Site scope: done. The tests check it on Postgres, but only the first run passed (see Checks).
- Contract type in `contracts`: done (see deviation 3).
- One line above each Work list, zero reads "Nothing open now", words from the server: done.
- Backend test that the count ignores the range and obeys known_at: written (`test_site_open_now_...`, `test_global_open_now_...`).
- One frontend test per Work page: done (global Incidents, global Maintenance, Site Work). Proven non-vacuous: with the line disabled, all 3 fail; reverted with `git checkout`.
- Register R338/S17: R338 (`.agent/mock-departure-register.md:440`) is the cold-work window-fix row, closed in W5-cold-Work. It says nothing about "including today" or open items, so it is not revised. S17 is not found in the repo.

## Checks
- `test_open_now_postgres.py` on `assetops_opennow_test`: first it failed as expected (KeyError `open_now`, plus fixture errors I fixed). After wiring: **3 passed, 0 skipped** (27.6 s, 8 connections).
- STILL TO RUN on Postgres. The coordinator stopped DB use (D-ANY.6), so I stopped my sequential run during its first file and did not rerun it. Run one at a time: `test_open_now_postgres.py`, `test_w401_site_indexes_postgres.py`, `test_w601a_global_incidents.py`, `test_w601b_global_maintenance.py`, `test_w403_work_links_postgres.py`, `test_k6a_fuel_action_origin_postgres.py`, `test_w601c_request_detail.py`, `test_w601e_operational_index.py`.
- vitest: globalIncidents + globalMaintenance + siteWorkCases 91 passed; coldWorkCases + evWorkCases + globalWorkClient 74 passed.
- `tsc --noEmit`: clean (no output).
- Non-DB import and wording check: ok.
- `check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv): "Architecture check passed." `check-agent-workflow.ps1`: "Agent workflow check passed." (exit 0, on `df60697a1`).

## D-OPEN.1 follow-up and Postgres run (2026-11-12, after `git merge main`, merge d8733388b)
- Ruling items: (1) card wording "requests, actions" is not in the code or the packet; the line and the wording stay "incidents, requests" and "Nothing open now"; Actions subtab gets no line (unchanged). (2) `guarded_open_now` in `work/open_now.py`: a failed count omits `open_now`, logs `open_now_unavailable`, still serves the list; wired in `global_index.py` (~537) and `site_index.py` (~390). New no-DB `backend/tests/test_open_now_failure.py`, 2 tests (one per list); both fail when the guard re-raises, pass with it. (3) `test_open_now_postgres.py` now reads a real cursor page two on the Site list (wide window, limit 1, cursor, later read instant) and on the global list; counts equal on both pages.
- Postgres on `assetops_opennow_test`, one file at a time, all after the D-OPEN.1 changes: `test_open_now_postgres` 3, `test_w401_site_indexes_postgres` 5, `test_w601a_global_incidents` 20, `test_w601b_global_maintenance` 17, `test_w403_work_links_postgres` 3 (11:00), `test_k6a_fuel_action_origin_postgres` 7, `test_w601c_request_detail` 18, `test_w601e_operational_index` 12. 0 failed, 0 skipped.
- vitest (6 files: globalIncidents, globalMaintenance, siteWorkCases, coldWorkCases, evWorkCases, globalWorkClient) 165 passed; `tsc --noEmit` clean (run on the merge, frontend unchanged since).
- check-all (19 guards) on the merge before the D-OPEN.1 commit: all 19 passed; rerun on the final revision (after the D-OPEN.1 commit): All 19 guards passed.

## Known deviations
1. Actions are not counted. The card's example says "1 action", but the Action index has no `known_at` cutoff, and an Action has no "open" state (ACCEPTED → PENDING → APPLIED; resolution is separate). The Architect needs to define "open action" before actions can be counted. The Site Actions subtab and the global Preventive and Operational records pages get no line, because plans and records have no open state.
2. Every line counts both kinds (incidents and requests), whichever page it is on.
3. `assetops_contracts` is the cross-barrier neutral package. A Work read shape sits there only because the card asks for it.
4. No CSS: the line is a plain `<p class="work-open-now">`. Layout evidence: not run.

## Demo safety
`tools/demo_combined.py` `prebuilt_routes` has no Work route, so no pre-built response changes shape.

## Residual risk
Each open count runs one events query per case across every Site, on every list read. That is fine at demo sizes but scales with the total number of cases.

USER_REVIEW: none required by the card; a Reviewer gate applies.
