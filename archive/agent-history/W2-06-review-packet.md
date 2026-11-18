# W2-06 review packet (EV session assessment)

Branch `task/W2-06-ev-assessment`. Spec: `.agent/W2-06-build-spec.md` (`D-2026-10-18-w2-06-07-buildspec`), rulings q1-q4, r5, r6. Handoff: `.agent/W2-06-phase-handoff.md`. Not merged to main. **Fix round r7/r8/r9 built and verified at `c18acc34`** (r9 rulings in the build spec "Fix-round rulings (r9)"). Three interpretation notes are in `.agent/W2-06-pending-rulings.md` "fix round r9"; none blocks.

## Commits
1 `cb470909` `3af70964` `fc231615` migration 0025, EV probes; q1 `13c6ef33`; 2b `27ceef76`; 3a `0eeb57ef`; q3 `255ccbae` `a3138bfb` `3a48dc45` `0a8f5866`; 2 (R12 vectors) `ef408a1b`; 3b `d556b02c`; r5 `981830ea`; 4 `41f32db2`; r6 proofs `61b3c602`; 5 `0dcedf16` (UI routes, captures). Handoff/rulings-only commits omitted.

## Run 8 (this run)
- `61b3c602` r6 tests in `backend/tests/test_w206_ev_reads_postgres.py`: `test_exact_window_does_not_use_covering_selection` (narrower, shifted and wider windows over a selected one are 200 UNKNOWN, null counts, detail 404), `test_ev_source_age_never_emits_stale_source` (settled replay window more than 1 day older than the wall clock; list/detail/Finding reads CURRENT, no `STALE_SOURCE` in any body), `test_historical_cutoff_precedes_pending_job` (PENDING `ev_charging` job row asserted; current read PENDING_RECOMPUTE, first cutoff HISTORICAL on list, detail and Findings), `test_repeated_query_key_is_parameter_unknown` (each permitted key repeated, valid or malformed, on both lists and session detail), `test_only_cursor_basis_change_is_ev_read_409` (basis- and cutoff-changed cursors 409 `EV_CURSOR_BASIS_CHANGED` on both lists; no-selection 200, misses 404; `SELECTION_UNSETTLED` absent from the three EV read modules).
- `EV_SELECTION_UNSETTLED`: no product code ever contained it (commit 4); r6 removal is held by the last test's source check. Older spec/W2-07 mentions are Architect text and were left as written (r6 says superseded).
- Non-vacuity: precedence swapped (pending before historical) and exact-window predicate loosened to covering (`<=`/`>=`): both the exact-window and precedence tests FAILED; restored by `git checkout`.
- `0dcedf16` commit 5: `frontend/src/sites/evAssessmentClient.ts`, `EvAssessmentViews.tsx`, `w2-ev-assessment.css`; wired in `shell/SiteAnalyticsFrames.tsx` (EV_CHARGING Performance with no subtab or `sessions`; EV Finding Overview) and `App.tsx` (`evAssessment` prop); `UnavailableInline` added to `ui/UnavailableEntry.tsx` (same exempt const); `SITE_SCREEN_DESCRIPTIONS.sessions` (mock subtitle, no values); `test/settled.ts` learns the EV loading line.
- Copy: spec Commit 5 ledger with r5 state copy and r6 dry-read overrides (pending/historical/contradictory/no-session/orphan/simulation/refusal copy literal). Finding link turns on only from `links.finding`; evidence/analysis/financials stay in-place gaps. The Finding route follows `claim.session_id` at the Finding's own window for the connector name.

## Fix round (r7/r8)
| Finding | Commit | Test / proof |
| --- | --- | --- |
| r7 P5 withdrawn / unsupported BigClaim literals; stored limitations, lifecycle, cutoff in details | `0b06acfc` | `evAssessmentRoutes.test.tsx` "withdrawn Finding is history…" (extended), "supported Finding without the exact START/FAULT/ABORT claim…" |
| r7 P7 pending row keeps rows, `Open Finding · Not available yet` | `0b06acfc` | `pending_and_historical_currentness` (pending linked row, current link, historical own link / null) |
| r7 P8 W1-plus-W2 tab multiset; EV fixtures | `0b06acfc` | `navigation-rail-fixtures.ps1` five new EV mutations (drop EV Recommendation / Availability / Energy, duplicate, append) each fail; route test asserts both tab orders, inert entries. check-all 10/10 at `0b06acfc` |
| r8 H1 exact re-head, late terminal correlates | `3bdcabec` | `test_w206_ev_store_postgres.py::test_late_terminal_past_selected_end_reheads_exact_window`, `test_w206_ev_reads_postgres.py::test_wider_replacement_never_leaves_exact_window_current_on_stale_head`; both FAILED with the pre-H1 store restored, pass after |
| r8 M2 completeness from SUPPORT uses; chips | `37da7b0b` | `test_completeness_uses_selected_evidence_not_reason_absence` (complete, contradictory, missing-meter); `contradictory_row_has_no_terminal_chip` |
| r8 M3 backend match | `37da7b0b` | `test_finding_evidence_matches_selected_session_support` |
| r9 M3 wire: Finding detail `claim.start_evidence_id` / `abort_evidence_id` (read-time join of cited IDs to the selected session revision's SUPPORT/null-reason uses and literal kind; one per kind else null) | `26718e5d` (key set `c18acc34`) | `test_finding_evidence_matches_selected_session_support` extended: both fields equal the selected SUPPORT START/ABORT; missing case (revision outside the selected result, other session) gives null |
| r9 M3 UI: closed line `Record {8} · No analysis link` (accessible `Record {full}`) only with the full trio; `ev-finding-references` lists Start/Fault/Abort record IDs in order, then the analysis gap once; incomplete trio gives the unsupported conclusion and `Record Unknown` | `0b2e12cd` | `evAssessmentRoutes.test.tsx::finding_record_line_names_fault_and_discloses_all_support_ids` |
| r9 M1-a: whole-set `classify` before `assess`; MIXED/UNKNOWN non-empty set raises `EvConfigurationRefused` (S4-05 reasons + IDs in the job error), nothing written, job retryable; per-record gate is the record's own BOUND class + exact binding. Read: no head gives 200 UNKNOWN, null counts/basis, set `classification`, sorted `evidence_ids`/`source_ids`, the sentence in currentness/status/denominator/`limitations`; pending prior head keeps its facts with the current class public and the sentence in `limitations[]`; link-reader failure is 503 | `dd3b0b53` | `test_w206_ev_store_postgres.py::test_mixed_runs_refuse_successful_empty_projection`, `::test_bound_unbound_and_all_unbound_refuse_projection[bound-and-unbound,all-unbound]`; `test_w206_ev_reads_postgres.py::test_unassessable_source_has_unknown_status_and_limitation` (pending head, MIXED, all-unbound, empty set, failed link query, no assessment write); UI `unassessable_source_never_says_no_sessions` and the pending-head case |
| r9 M1-b: coherent class, every candidate START wrong-binding: one selected UNKNOWN assessment, all counts (orphan included) null, `as_of` = creation, the binding sentence; idempotent repeat | `dd3b0b53` | `::test_coherent_class_wrong_binding_does_not_claim_no_sessions`; UI `wrong_binding_records_have_exact_disclosure` (gap above disclosure, Unknown cards, no `0`) |
| r9 M1-c: `result.excluded_records` (wrong-binding records once, sorted by source time/ID); sessions list `excluded_records` required, full-window, page-independent; one closed line per ID after the session references | `dd3b0b53`, `0b2e12cd` (key set `2ae3da82`) | `test_w206_ev_reads_postgres.py::test_wrong_binding_records_survive_empty_and_paginated_lists` (M1-b empty list + `limit=1`; valid session with excluded END: first page, cursor page and detail `EXCLUDED`/`SOURCE_UNVERIFIED`); UI `wrong_binding_records_have_exact_disclosure`, "valid sessions list excluded records after the ordinary references" |
| r8 L1 | `a17026f1` | `test_non_ascii_limit_is_422_ev_limit_invalid` (both list routes, `²`, Arabic-Indic, fullwidth, `1²`) |
| r8 L2 | `a17026f1` | note below |

H1 test scenario: the registered late-record replay with an exact selection `[08:00,08:30)` written by the production EV writer, so the 08:31 END is past the selected end; no manifest or vector change. `ev_windows` subtracts every selected window near the aligned job hull from the remainder. Six W2-05b manifests and `ev-w206-vectors.json` byte-identical: `git diff --stat cd3a78d5 HEAD` over `contract-fixtures/w2/ev` and the vectors file is empty; vectors blob `99dc3921` at both revisions.

r9 test seams: `patch_links` rewrites the S4-05 link rows the scoped reader returns (run ID, `link=None`) after an ordinary registered replay; `rebind` gives selected records a member binding outside the selected set on the writer's own `ev_inputs`. Neither seeds an analytic result. Worker behaviour change: a job window with no accepted record (a configuration enqueue) completes with nothing written (r8 "do not fabricate a successful empty assessment"); `_failed_job_rolls_back` now skips those DONE-empty jobs to reach the writing one.

## Trigger fixtures vs ordinary replay (r8 L2)
The isolated SQL trigger tests in test_w206_ev_enqueue_postgres.py clone accepted_evidence rows and seed analytic_run_selection directly to exercise enqueue timing and bridge cases. They are trigger unit fixtures, not proof of an ordinary accepted replay. The replay, assessment-store and selected-read proofs use the registered Stage/Commit/Batch V2/S2 accepted chain; no production analytic result is test-seeded.

## Frontend tests (`evAssessmentRoutes.test.tsx`, 27 at `c18acc34`)
Stocked complete (panels, strip, card labels/notes/values, six headers, row cells, green tone, denominator and cause copy, one disclosure per panel, no mock IDs), interrupted (Fault-aborted amber, `Open Finding →` href with the same window), missing-meter, contradictory (red, competing end, r5 copy), empty/orphan, `pending_and_historical_currentness` (sessions pending + historical, Finding pending), `unknown_selection_has_no_zero_counts`, four rows then Show all, refusals 401/403/404/409/422/503 and malformed on sessions, ev-finding stocked/withdrawn/404/409/503. Every case asserts `expectV69Panels`; stocked cases also `expectPlantedPanelRejected`.

## Captures (`.agent/W2-06-evidence/`, `evidence.json`, `capture.mjs`, `seed.py`)
r9 refresh at `c18acc34`: interrupted replay reseeded into `w206i_test`, Finding `...025b` (the skipped empty windows shift the deterministic IDs; `capture.mjs` updated), claim start `...00d7`, fault `...013f`, abort `...013c`. All eight PNGs re-captured; they are byte-identical to the previous capture (the r9 additions are inside closed disclosures or absent in this state) and every height row below is unchanged. Earlier: seeded into `w206g_test` (registered path + EV worker), `EV-LAB-001`, window `2026-10-06T08:00:00Z`-`09:05:00Z`, `known_at` `09:00:00Z`. Real backend (uvicorn 9734) + vite 6134; mock `#/sessions`, `#/ev-finding`. Files `{sessions,ev-finding}-interrupted-{1440,390}-{app,mock}.png`. Viewed: sessions 1440/390 and ev-finding 1440.

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

## Checks at `c18acc34` (r9 final, serial, private `w206i_test`)
- Focused `backend/tests/test_w206_ev_*.py`: 137 at `0b2e12cd` = 131 passed + 6 failed (six-replay read key sets lacked the new fields); test-only fixes `2ae3da82`, `c18acc34`, then the six cases passed (6/6). 15.8 min.
- Frontend `npm.cmd test -- --run`: 90 files, 2322 passed. `npm.cmd run build` passed (existing chunk-size warning).
- `tools/check-all.ps1 -Python ...plan2\.venv`: **10/10**.
- Backend full real-Postgres suite, serial (`pytest backend/tests -q --junitxml`), keep-awake running: 3234 passed, JUnit tests 3234, failures 0, errors 0, skipped 0, 4097 s (1:08:17; cap 2x the 65 min previous run).
- Host suite (`pytest host/tests -q --junitxml`): 787 passed, JUnit skipped 0, failed 0, 609 s.
- DB: `w206i_test` dropped (`dropdb --force`). Harness `w206i_pt*` clones are dropped by each run's own session cleanup; not separately listed (listing needs a psql command the brief does not allow).

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

## User review (r9)
UI slice: hold the merge for the owner walkthrough. The r9 UI states (M1-a/b/c, M3 fallback) are jsdom-only; the browser capture is the interrupted state.

## User review
UI slice: build and review now, hold the merge for the owner walkthrough (W1/W2 practice). P8 must be ruled before merge.

## Closing round (r10, L3)
- r10 N2: `source_provenance.reasons: [{code, accepted_evidence_ids}]` on the EV envelope (`postgres_assessment_store.py` `_unassessable`/`_envelope`): classifier order, internal detail keys dropped, `[]` for empty and coherent sets; with a pending prior head `classification`, `evidence_ids`, `source_ids`, `reasons` describe the current accepted set, `basis_sha256` stays the prior stored basis. UI: one `Source reason: {sentence} Accepted record IDs: {ids|None}.` line per reason in the source detail (and the pending-rows disclosure), rendered as paragraphs in the disclosure's extra block, so they follow the Source class/ID rows rather than sitting between them (ExactReferences keys rows by label). Closes re-review L4.
- Tests: extended `test_unassessable_source_has_unknown_status_and_limitation` (mixed, all-unbound, pending, empty); added `test_empty_job_window_completes_without_assessment` (N1) and `unassessable_source_discloses_reasons_and_ids`.
- L3 (r7 P7): `NextStep` shows `Open Finding · Not available yet` on a pending row only when it has a Finding; a pending row without one renders as the non-pending no-Finding row (asserted in `pending_and_historical_currentness`).
- Scope: additive EV read and UI only; full backend and host suites NOT rerun. W2-05b manifests and R12 vectors untouched (see check below).
- N1/N3 need no further code (N3 deferred to W2-07).
- Verification at final revision: `test_w206_ev_*` 132 passed + 6 six-replay failures from the envelope key-set assertion (fixed, 6 passed rerun); frontend 90 files / 2323 passed; build ok; check-all 10/10; no `test_s4_05*` files exist; vectors/manifests untouched.
