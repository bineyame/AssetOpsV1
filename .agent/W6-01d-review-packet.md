# W6-01d review packet — C4 request History

Branch `task/W6-01d-request-history`, base `d798029e` (main with W6-01a/b/c merged). Spec: `.agent/W6-01-build-spec.md` "C4 pre-flight rulings" (P-C4-1..22), §2 `history` row, §3.1 F3–F5 (`wr-history`). Commits: `f756d86e` (Lane A), `f7122095` (Lane B), `09536c95` (By-cell layout), then the evidence/packet commit.

## Outcome

`/maintenance/requests/{case_id}/history?site_id={site_code}[&known_at=]` renders the v69 `wr-history` screen in the shared C2 frame: breadcrumb `Maintenance › {WR} › History · site: {Site}`, h1/subtitle with `Open site`, tab row (Overview, Maintenance record, Verification `Not available yet`, History current), date bar, mheader, then the one `History` panel with the mock's `Time | Event | By` table. Rows are `work_detail.events` plus successor `history.revisions` (revision 1 omitted), in exact `(recorded_at, lowercase id)` string order; five authored rows per page with an in-panel `History pages` pager; the last page ends with the two in-table gaps. A body without CREATED (or with a missing known payload) fails closed as the 503 sentence.

## Files

- `frontend/src/work/WorkRequestHistory.tsx` (new): `historyRows`, `historyUtc`, `historyReadable`, pager, `WorkRequestHistoryFrame`. Labels MOCK DEVIATION (D2, R19) Time and (D4, R39) By in the header comment.
- `frontend/src/work/workRequestShared.tsx`: `WorkRequestTab` adds `history`; `LiveTab` uses `body.links[tab]`; the History `UnavailableTab` became a `LiveTab`; `WorkRequestFrame` gains optional `accept` (rejected body reads as `WORK_STORE_UNAVAILABLE`). C2/C3 pages untouched.
- `frontend/src/work/globalWork.css`: `.global-work--history` scroll caps 430/480, min-width 750, cell wrap, time/by blocks.
- Tests: `__tests__/workRequestHistory.test.tsx` (new, 17); `workRequestOverview.test.tsx` and `workRequestRecord.test.tsx` History-tab assertions only (live `/history?site_id=` and `&known_at=`; Verification still unavailable).
- Lane A: `shell/operatorSiteRoutes.ts` (`WORK_REQUEST_HISTORY_ROUTE_PATH`), `App.tsx` route, `navigation-truthfulness.ps1` (`"History"` removed from `$expectedTabs`, dated comment), registry `wr-history:1` reason, ledger `wr-overview` interaction and `wr-history` F5 fields with the C4 interaction literal.
- Evidence: `.agent/W6-01-evidence/C4/` (manifest.json, mock_comparison.json, capture.mjs, run_state.sh, api_403.py copy, api_503.py, build_manifest.py, seeds, 11 states x 2 widths + mock pair).

## Acceptance (P-C4)

| P-ID | Status | Proof |
| --- | --- | --- |
| 1 | met | Imports only C2 exports and the `GlobalWorkDetailResult` union; `globalWorkClient.ts`, `globalWorkParts.tsx`, Overview/Record pages unchanged; `tsc` clean |
| 2 | met | Overview/Record tests assert live History href (with and without cutoff), Verification unavailable |
| 3 | met | `History pages` nav, hooks, `link-button`, `Showing 1–5 of 6` / `6–6 of 6`, hidden Previous/Next; no read on paging; Reload resets |
| 4 | met | `expectV69Panels("wr-history")` loaded/page 2/refused/missing-CREATED; panel 465/488 (page1), max collapsed 467/490 (stress) vs 600/690; pager 29/29 |
| 5 | met | six-row test, revision 1 absent |
| 6 | met | `history_labels_all_seven`; assignee/comment/reason/COMPLETE reference; `Full event text` with 128-char assignee and 500-char reason |
| 7 | met | `Raised from INC-000007` with href, plain text without href, `Created` without source; captured `linked-source` (INC-000004 href) |
| 8 | met | two gap rows on last page only, no disclosure, not counted |
| 9 | met | `historyUtc` seconds; same-second tie test |
| 10 | met | `Name not recorded` + `Stored actor` disclosure; 128-char actor test; doc width = viewport in all captures |
| 11 | met | `OPEN_VERIFICATION` row `Event OPEN_VERIFICATION · meaning not established`; typed CLOSE through `historyRows` |
| 12 | met | typed 200 without CREATED -> 503 sentence, no rows (fails when `accept` is removed: proven); fetched malformed 200 -> parser 503; backend `test_missing_created_is_503` passed |
| 13 | met | Occurrence disclosure on events and Correction; collapsed details max 16 px; expanded capture |
| 14 | met | loaded/loading/refused breadcrumb and shared shell tests |
| 15 | met | 390: table 750 scroll in 318, hint visible, columns 210/340/200 |
| 16 | met | microsecond-string then lowercase-ID order test |
| 17 | met | ledger literals exact; `check_v69_ledger.py` valid |
| 18 | met | registry reason, node `open`, panel `gap`, contract `Deferred`; registry checker exit 0 |
| 19 | met | manifest: current rev 2 IN_PROGRESS 6 rows vs `11:59:04Z` rev 1 COMPLETED 4 rows |
| 20 | met | 11 states at 1440/390 with R8 note; mock pair captured |
| 21 | met | stress CREATED/ASSIGN/Correction, no pager (test and capture) |
| 22 | met | guard proof: re-adding `"History"` fails the tab multiset; reverted |

## Checks

- Frontend focused: `workRequestHistory` 17, Overview+Record 38 passed. Wider `src/work src/shell src/sites src/estate src/ui` at `09536c95`: 111 files, 2645 passed, 1 failed: `s404SiteFindingIndex.test.tsx` "changing the dates writes a new window to the address and reads again". This slice does not touch that file, and it passes when run alone (37/37), so the failure looks load-sensitive. `tsc --noEmit` exit 0; `vite build` exit 0.
- Backend: `backend/tests/test_w601c_request_detail.py` 15 passed (163.9 s, private `assetops_w601d_c4f_test`, dropped). No backend code change; full suite not run (dispatch rule).
- `tools/check-all.ps1`: 11/11 PASS (with `.venv` junction to plan2's venv).
- Layout: captured with Vite dev + uvicorn on private DBs (all dropped); Vite stopped by PID.

## Known deviations

- MOCK DEVIATION D2 (R19) Time with year/seconds + occurrence disclosure; D4 (R39) By `Name not recorded` + stored actor. Both labelled in code; register rows exist.
- The two gap rows are ruled honest gaps; the register has no separate row for them (register is not on the C4 card). Architect may wish to add one.
- `Full event text` is shown for rows with stored free text (ASSIGN, COMMENT, CLOSE/REOPEN/CANCEL, Correction); CREATED, COMPLETE and unknown rows have none (builder reading of "preserve ... through the clamp").
- The dispatch summary said unknown kinds are read failures; the spec (C4 Mock mapping) renders them as authored rows `Event {code} · meaning not established`, and only missing CREATED or missing identity/payload fails. Built to the spec.

## Residual risk / review focus

- `accept` in the shared frame (new optional prop) — confirm it is within the C4 `workRequestShared.tsx` ownership.
- 390 tab row scrolls inside itself (C2 behaviour), so the current History tab may sit off-screen at 390.
- USER_REVIEW: W6 walkthrough after W6; this slice needs independent review before merge.
