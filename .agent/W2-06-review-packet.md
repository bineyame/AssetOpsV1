# W2-06 review packet (EV session assessment)

Branch `task/W2-06-ev-assessment`. Spec: `.agent/W2-06-build-spec.md` (`D-2026-10-18-w2-06-07-buildspec`), rulings q1-q4, r5, r6. Handoff: `.agent/W2-06-phase-handoff.md`. Not merged to main. **Blocked on one ruling (P8) before merge: check-all is 8/10.**

## Commits
1 `cb470909` `3af70964` `fc231615` migration 0025, EV probes; q1 `13c6ef33`; 2b `27ceef76`; 3a `0eeb57ef`; q3 `255ccbae` `a3138bfb` `3a48dc45` `0a8f5866`; 2 (R12 vectors) `ef408a1b`; 3b `d556b02c`; r5 `981830ea`; 4 `41f32db2`; r6 proofs `61b3c602`; 5 `0dcedf16` (UI routes, captures). Handoff/rulings-only commits omitted.

## Run 8 (this run)
- `61b3c602` r6 tests in `backend/tests/test_w206_ev_reads_postgres.py`: `test_exact_window_does_not_use_covering_selection` (narrower, shifted and wider windows over a selected one are 200 UNKNOWN, null counts, detail 404), `test_ev_source_age_never_emits_stale_source` (settled replay window more than 1 day older than the wall clock; list/detail/Finding reads CURRENT, no `STALE_SOURCE` in any body), `test_historical_cutoff_precedes_pending_job` (PENDING `ev_charging` job row asserted; current read PENDING_RECOMPUTE, first cutoff HISTORICAL on list, detail and Findings), `test_repeated_query_key_is_parameter_unknown` (each permitted key repeated, valid or malformed, on both lists and session detail), `test_only_cursor_basis_change_is_ev_read_409` (basis- and cutoff-changed cursors 409 `EV_CURSOR_BASIS_CHANGED` on both lists; no-selection 200, misses 404; `SELECTION_UNSETTLED` absent from the three EV read modules).
- `EV_SELECTION_UNSETTLED`: no product code ever contained it (commit 4); r6 removal is held by the last test's source check. Older spec/W2-07 mentions are Architect text and were left as written (r6 says superseded).
- Non-vacuity: precedence swapped (pending before historical) and exact-window predicate loosened to covering (`<=`/`>=`): both the exact-window and precedence tests FAILED; restored by `git checkout`.
- `0dcedf16` commit 5: `frontend/src/sites/evAssessmentClient.ts`, `EvAssessmentViews.tsx`, `w2-ev-assessment.css`; wired in `shell/SiteAnalyticsFrames.tsx` (EV_CHARGING Performance with no subtab or `sessions`; EV Finding Overview) and `App.tsx` (`evAssessment` prop); `UnavailableInline` added to `ui/UnavailableEntry.tsx` (same exempt const); `SITE_SCREEN_DESCRIPTIONS.sessions` (mock subtitle, no values); `test/settled.ts` learns the EV loading line.
- Copy: spec Commit 5 ledger with r5 state copy and r6 dry-read overrides (pending/historical/contradictory/no-session/orphan/simulation/refusal copy literal). Finding link turns on only from `links.finding`; evidence/analysis/financials stay in-place gaps. The Finding route follows `claim.session_id` at the Finding's own window for the connector name.

## Trigger fixtures vs ordinary replay (r8 L2)
The isolated SQL trigger tests in test_w206_ev_enqueue_postgres.py clone accepted_evidence rows and seed analytic_run_selection directly to exercise enqueue timing and bridge cases. They are trigger unit fixtures, not proof of an ordinary accepted replay. The replay, assessment-store and selected-read proofs use the registered Stage/Commit/Batch V2/S2 accepted chain; no production analytic result is test-seeded.

## Frontend tests (`evAssessmentRoutes.test.tsx`, 20)
Stocked complete (panels, strip, card labels/notes/values, six headers, row cells, green tone, denominator and cause copy, one disclosure per panel, no mock IDs), interrupted (Fault-aborted amber, `Open Finding →` href with the same window), missing-meter, contradictory (red, competing end, r5 copy), empty/orphan, `pending_and_historical_currentness` (sessions pending + historical, Finding pending), `unknown_selection_has_no_zero_counts`, four rows then Show all, refusals 401/403/404/409/422/503 and malformed on sessions, ev-finding stocked/withdrawn/404/409/503. Every case asserts `expectV69Panels`; stocked cases also `expectPlantedPanelRejected`.

## Captures (`.agent/W2-06-evidence/`, `evidence.json`, `capture.mjs`, `seed.py`)
Same selected state both sides: interrupted W2-05b replay seeded into `w206g_test` (registered path + EV worker), `EV-LAB-001`, window `2026-10-06T08:00:00Z`-`09:05:00Z`, `known_at` `09:00:00Z`, Finding `...025d`. Real backend (uvicorn 9734) + vite 6134; mock `#/sessions`, `#/ev-finding`. Files `{sessions,ev-finding}-interrupted-{1440,390}-{app,mock}.png`. Viewed: sessions 1440/390 and ev-finding 1440.

## Panel heights (app / mock px; limit 1.3x)
| Screen · panel | 1440 | 390 (stacked) |
| --- | --- | --- |
| sessions · Session service records | 183 / 336 = 0.54 | 221 / 485 = 0.46 |
| sessions · How to read the denominator | 167 / 142 = 1.18 | 188 / 163 = 1.15 |
| sessions · Cause remains bounded | 167 / 142 = 1.18 | 150 / 163 = 0.92 |
| ev-finding · Bounded conclusion | 249 / 209 = 1.19 | 358 / 287 = 1.25 |
| ev-finding · Operational context | 254 / 232 = 1.09 | 254 / 232 = 1.09 |
| ev-finding · Recommended next step | 254 / 232 = 1.09 | 169 / 193 = 0.88 |

All under 1.3x and the spec ceilings (sessions 437/185/185, Finding 272/302/302). Panel 1 is short because the replay has one real session (no placeholder rows). First capture had the pair at 1.62 and Bounded conclusion at 1.39; fixed by one prose block for the denominator lines, 6 px prose spacing and the compact `tech` disclosure (scoped to `[data-ev-view]`). Columns at 1440: 224/179/134/146/246/190 px = 20/16/12/13/22/17%. 390: table scrolls in its region (client 303, scroll 640), document overflow none, clipped cells 0, all six columns kept.

## Checks at `0dcedf16`
- Backend full real-Postgres suite, serial (`pytest backend/tests -q --durations=30 --junitxml`), private `w206g_test`: 3221 passed, JUnit cases 3221, skipped 0, failed 0, 3927 s (1:05:27; serial run, under the 90 min cap).
- Host suite (`pytest host/tests -q`), serial after backend: 787 passed, JUnit skipped 0, failed 0, 638 s.
- Frontend `npm.cmd test`: 90 files, 2315 passed. `npm.cmd run build` (tsc + vite) passed (existing chunk-size warning).
- `tools/check-all.ps1`: **8/10. FAIL Navigation truthfulness and Architecture seams** (rail fixture baseline): the unbuilt in-page tab inventory is fixed at six W1 entries, and commit 5 adds `Availability`, `Energy / site power` and a second `Recommendation` in mock order. Under `D-2026-10-17-f5-subtabs-and-contact` this is a ruling, so the guard was not edited: pending ruling P8.
- DB: `w206g_test` dropped. The harness template clones `w206g_pt64e8ab15_tpl_test` (this run) and `w206q4_pt76380a96_{tpl,main}_test` (earlier run) remain; the brief allowed only `w206g_test`, so they were left for the coordinator.

## Deviations and open choices
`.agent/W2-06-pending-rulings.md` "run 8": P1 panel-1 subtitle gap, P2 strip lineage gap, P3 short-ID form, P4 r5 vs ledger conclusion order, P5 withdrawn big claim, P6 UNKNOWN body text, P7 pending rows/link, **P8 tab inventory (blocks check-all)**. Each was built with an interim answer. None touches the backend.
Short IDs use the prefix. The replay's deterministic UUIDs share the `00000502` prefix, so captured Finding/record IDs look alike. Real UUIDs do not do this.

## Residual risk
Only the interrupted state was captured in a browser; the other states are covered by jsdom only. The sessions list pages only the first server page (`next_cursor` is not followed); Show all reveals the loaded rows. After P8 is ruled, rerun only check-all and the frontend suite, unless the ruling changes the backend.

## User review
UI slice: build and review now, hold the merge for the owner walkthrough (W1/W2 practice). P8 must be ruled before merge.
