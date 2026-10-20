# W2-07 review packet (EV Site evidence and money)

Task: W2-07, five EV Site reads and routes with a gross tariff scenario (`.agent/W2-07-build-spec.md`, rulings q1-q6).
Branch `task/W2-07-ev-site-evidence-money`. USER_REVIEW: UI slice; hold the merge for the owner walkthrough (W1 rule).

## Commits
1 `601456bc` `a471f3f4` migration 0026, rule-8 EV probes; q1 R3/R4 `7cbe440c`; q2 R7 `69ea6aee`; 2 `94c1a2f2` `4f34e3e2`
`1ce20550` (money writer, runner, R5/R6, R8 pending retry); 3 `7fb66e17` (five reads, q4 selector); q5 `50c31605`;
q6 `cfd299f8`; 4-5 `eed6820b` (routes, client, views), `454a6a77` (tests), `e6de374f` (capture fixes), `5a26b74b`
(guard fixes: chart moved into `assessmentGraphics.tsx`, no read-model type in shell routes); captures `5d924f4b`.
Handoff / resume / ruling-request commits omitted.

## Files materially changed (commits 4-5)
- `frontend/src/sites/evSiteClient.ts` (five reads, cursor/limit on Analysis and Financials).
- `frontend/src/sites/EvSiteViews.tsx` (`EvSiteFrame`, five screens), `frontend/src/sites/w2-ev-site.css`
  (closure s4 fixed widths, 390 min widths 640/900/900/600, chip tones), `EvPowerChart` in `assessmentGraphics.tsx`.
- `frontend/src/shell/evSiteRoutes.tsx` (`SiteEvFrame`), `operatorSiteRoutes.ts` (`SITE_EV_*_ROUTE_PATH`,
  `siteEvHref`), `App.tsx` (five routes, `evSite` client).
- `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx` (five named tests).
Private DBs `w207i_test` and its run template dropped at the end. Backend commits 1-3/q5/q6: see `.agent/W2-07-phase-handoff.md` runs 1-8.

## Acceptance (commits 4-5)
| Requirement | Status / proof |
| --- | --- |
| Exactly `/sites/{code}/ev`, `/ev/evidence`, `/ev/evidence/analysis`, `/ev/financials`, `/ev/financial-assumptions`, `from/to/known_at` kept on every tab/link | Met. `all_five_routes...`, `ev_evidence_tabs...`, `financial_tabs...` assert exact hrefs; Assumptions tab built from route + window (no wire key) |
| q5 panel arrays per route, stocked/empty/unpriced/refused | Met. `expectV69Panels` on keys `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions` for all four states on all five routes; pending/historical on `ev`/`ev-financials`; planted-panel rejection on `ev` |
| r10 N3 `SOURCE_UNVERIFIED` per record | Met. `analysis_source_unverified_shows_full_id_and_sentence`: full UUID + exact sentence in `Record details`, Site/window/cutoff line, `No analysis link`, no banner, no link |
| q6 copy: objective three labels; Mixed chip, `Source contacts differ`, `Contact checked at {checked_at} UTC`; coverage units and null limitation; `Metered with complete coverage` only on gross `ratio:"1"` | Met. `all_five_routes...` (4 objective labels), `ev_evidence_tabs_and_record_limit`, `financial_tabs_and_price_gate` |
| Refusal copy 401/403/404/409/422/503 inside the same frame | Met (`all_five_routes...`) |
| Tab multiset +0 | Met. Route subtabs are live links only; no `UnavailableTab` added; navigation-truthfulness guard passes |
| Captures 1440/390 same state; height table; <=1.3x | Met (below) |

## Captures (`.agent/W2-07-evidence/`, `seed.py`, `capture.mjs`, `evidence.json`)
`interrupted` replay seeded into `w207i_test` (registered path, EV worker, tariff published through the store path,
EV consequence worker). `EV-LAB-001`, window `2026-10-06T08:00:00Z`-`09:05:00Z`, `known_at` `09:00:00Z`; real
backend (uvicorn 9736) + vite 6135; mock `#/ev`, `#/ev-evidence`, `#/ev-evidence-analysis`, `#/ev-financials`,
`#/ev-assumptions`. Captured money state is UNPRICED/`TARIFF_MISSING`: the seed tariff's default validity (`T0` from
the cold fixture) does not cover the window, so the read honestly says `Unpriced`; ESTIMATED is covered by jsdom only.
Files `{screen}-interrupted-{1440,390}-{app,mock}.png`. Viewed: `ev` 390, `ev-evidence` 1440.

## Panel heights (app / mock px, closed; limit 1.3x and closure ceiling)
| Screen · panel | 1440 | 390 (stacked) |
| --- | --- | --- |
| ev · What happened on the service day | 252 / 238 = 1.06 | 553 / 617 = 0.90 |
| ev · Charging activity and site power | 374 / 356 = 1.05 | 307 / 269 = 1.14 |
| ev · Needs attention | 374 / 356 = 1.05 | 251 / 336 = 0.75 |
| ev · Bounded money consequence | 211 / 193 = 1.09 | 231 / 233 = 0.99 |
| ev · Next step | 211 / 193 = 1.09 | 197 / 193 = 1.02 |
| ev-evidence · What we can conclude now | 356 / 336 = 1.06 | 417 / 449 = 0.93 |
| ev-evidence · Data sources | 421 / 336 = 1.25 | 478 / 416 = 1.15 |
| ev-evidence · Most useful next evidence | 421 / 336 = 1.25 | 333 / 319 = 1.04 |
| ev-evidence-analysis · Accepted records | 340 / 266 = 1.28 | 302 / 386 = 0.78 |
| ev-evidence-analysis · How a claim limit is set | 170 / 148 = 1.15 | 216 / 247 = 0.87 |
| ev-financials · What happened → money | 323 / 285 = 1.13 | 369 / 422 = 0.87 |
| ev-financials · Assumptions in use | 281 / 234 = 1.20 | 281 / 234 = 1.20 |
| ev-financials · Not included | 281 / 234 = 1.20 | 149 / 142 = 1.05 |
| ev-assumptions · Financial assumptions | 299 / 272 = 1.10 | 314 / 390 = 0.81 |

All within 1.3x and the closure ceilings (309/463/463/251/251; 437x3; 345/193; 371/304/304; 354). First capture had
Data sources pair at 1.32 (444) and the 390 chart panel at 1.89; fixed in `e6de374f` (panel sub-line dropped, the
contact footer is the note; chart keeps its aspect; SLD entry moved to a footer). 1440 document overflow none, clipped
cells 0; at 390 tables scroll in their region (sources 640, records/bridge 900, assumptions 600), no page overflow.

## Checks (serial, private base `w207i_test`)
- Focused W2-07 backend (`test_w207_ev_money.py`, `test_w207_ev_money_postgres.py`,
  `test_w207_ev_site_reads_postgres.py`) at `5d924f4b`: 29 passed, 551 s.
- Focused frontend `evSiteMoneyRoutes.test.tsx`: 5 passed (also at `5a26b74b`).
- `tools/check-all.ps1`: first run at `5d924f4b` failed 1/10 (site-substrate: `SiteEvView` type in shell routes;
  shell-overflow: svg outside chart modules); fixed in `5a26b74b`; rerun all 10 guards passed.
- Frontend `npm.cmd test`: at `5d924f4b` 91 files / 2328 passed (129 s). At `5a26b74b` 2327 passed, 1 failed:
  `siteFinancials.test.tsx` "reloads page one at the same moment when the basis changed (typed 409)" (unchanged
  S4-08 file); it passed in the earlier full run and 3/3 isolated reruns of the file (83 passed) - load flake.
- `npm.cmd run build` (tsc + vite): passed at `5a26b74b` (existing chunk-size warning).
- Backend full real-Postgres suite, serial (`pytest backend/tests -q --durations=30 --junitxml`) at `5a26b74b`, keep-awake running: 3264 passed, JUnit tests 3264, failures 0, errors 0, skipped 0, 4682 s (1:18; cap 160 min).
- Host suite (`pytest host/tests -q --junitxml`), serial after backend: 787 passed, JUnit skipped 0, failed 0, 638 s.

## Builder readings (not rulings; confirm at review)
- Run 5 (commit 2): line-77 `source_class` = selected stored `result.source_provenance.class`; `source_gate` = C5
  classified class; tariff fields enter the basis only when ESTIMATED; session/evidence links only for ESTIMATED;
  WITHHELD/INCOMPLETE quantity null; UNPRICED keeps eligible kWh. Contradiction = CONTRADICTORY session, EXCLUDED
  `METER_OVERLAP`, one evidence ID under two sessions, or overlapping SUPPORT intervals on one connector. No exact
  selection / no session -> empty SUCCEEDED attempt. Replay window is `[08:00, 09:05)`. C1-C5 in
  `.agent/W2-07-pending-rulings.md` R8.
- Run 6 (commit 3): wire additions beyond closure lists (consequence `revision_no,tariff_recorded_at,limitation`;
  summary `reason`; Financials `history[]`; Analysis `total_count,excluded_records`, item `session_id,note`;
  Assumptions `tariff_revision_count,publication_note,consequence_tariff`; overview finding record IDs) - ratified by
  q5 R5. Source `contact.state` and the replay example readings were superseded by q5/q6.
- Run 7: `service_schedule_declared` flag; `configured_service_windows` always a list; contact key set; coverage
  `unit`; SUPPORTED demoted to LIMITED unless `ratio=="1"`; null-coverage sentence appended once - all ratified by q6.
- Run 8: enabled connector = `ev-connector-enabled=ENABLED` per `ev_foundation.py:522`; a schedule on a disabled
  connector is not "declared".
- Run 9 (UI): evidence aggregate chip over all seven capabilities (empty or all UNAVAILABLE -> `Evidence unknown`;
  any CONTRADICTORY -> contradictory; all SUPPORTED -> supported; else limited); Evidence table rows map Session
  outcomes/Connector availability/Delivered energy/Cause to SESSION_OUTCOME/SERVICE_STATE/DELIVERED_ENERGY/
  FAULT_ASSOCIATION; Next step links Sessions (row 1) and Financials (row 3), others `Availability`/`Work · Not
  available yet`; chronology uses accepted START/FAULT/ABORT/END with `use != EXCLUDED`, `End record missing` from
  the `INCOMPLETE_SESSION` attention code; the chart reads every Analysis page (limit 200, cursor followed); Financials
  explanatory rows appear when `findings.count > 0`; `Delivered energy` card is overview `energy.complete_kwh`;
  strip line count = consequence with a stored `revision_id`; null consequence card is `Unpriced`; display rounding
  is half-up to 2 places on the Decimal string (`money2`); Assumptions screen has no status strip (mock has none) and
  carries provenance/state in the window bar; SLD entry is a static `Open single line diagram · Not available yet`.

## Known deviations / residual risk
- Captured browser state is UNPRICED (see Captures); ESTIMATED, pending, historical, empty and refused are jsdom only.
- Replay UUIDs share the `00000502` prefix, so closed `Record {8}` labels look alike (full IDs are accessible).
- The capture replay has no source diagnostics, so every contact chip is `Unknown` in the browser state.
- `.agent/W2-07-pending-rulings.md` R1-R8 headings still read "open"; each was closed by q1-q4 in the build spec.

## User review
UI slice: hold the merge for the owner walkthrough. Focus: the five EV routes against the mock side by side.

## Fix round r1 (rulings 2026-10-20; code `4fb6a401` + test-fix commit; captures at `4fb6a401`)
Maps each finding to fix / test / capture. Frontend tests: `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx`;
backend: `backend/tests/test_w207_*_postgres.py`.

| Finding | Fix | Test | Capture |
| --- | --- | --- | --- |
| M1 priced proof, basis words | `seed.py` uses `golden_tariff`; `basisText` maps `AUTHORED_ESTIMATE` -> `Authored estimate` (Financials/Assumptions rows and details); other basis -> `Basis not recognised` | `financial_tabs_and_price_gate` (real stored basis, both routes, no `AUTHORED_ESTIMATE`) | `ev*-interrupted-{1440,390}-app.png`: `KES 4.17`, bridge `15.000 kWh × 0.27775 KES/kWh`, `Scenario`, tariff `0.27775 KES/kWh · Authored estimate`; DB: ESTIMATED 15.000 kWh / 4.16625000 |
| M2 rounding | `money2` half even on the absolute value, every discarded digit | same test: 8.325->8.32, 8.335->8.34, 8.32500001->8.33, -8.325->-8.32 | - |
| M3 plain words | `EvSiteReads._row_words` + `SOURCE_SUFFIX` (8 roles), `STATE_TEXT` (7), `KIND_TEXT` (5), `State not recognised`, `EV reading`; state rows carry no unit; `role` unchanged | `test_analysis_intervals_and_publication_note`, `test_analysis_row_words_for_every_role_state_and_event`, `test_analysis_plain_mapping_tables_are_complete`; `ev_evidence_tabs_and_record_limit`, `claim_details_use_plain_capability_and_chip_words` (7 labels, 4 chips) | analysis captures |
| M4 two clocks | `publication_note` inside both `Assumption details` disclosures (after validity facts); Assumptions keeps its visible note | `financial_tabs_and_price_gate` (sentence on both, absent for null-note fixture; fixture `recorded_at` 09:30) | - |
| L1 null consequence | `No gross tariff scenario assessed` for null on card, bridge cell, `consequenceWord(null)`; stored UNPRICED stays `Unpriced` | `financial_tabs_and_price_gate` | - |
| L2 aggregate | `evidenceAggregate` and strip/overview count use the four mock rows only | `claim_details_use_plain_capability_and_chip_words` (four SUPPORTED + POWER_CONSTRAINT LIMITED -> `Evidence supported`; counts) | - |
| L3 next evidence | `_next_candidates` ranked list incl. `INDEPENDENT_POWER_GAP`, deduplicated, first three | `test_next_evidence_candidates_rank_and_first_three`; ranking check in `test_five_routes_...` | - |
| L4 chronology | `(source_time, kind_rank, evidence_id)` in Overview chronology only | `same_instant_fault_precedes_abort_in_chronology` | - |
| L5 downgrade | Empty downgrade moved to `test_0026_empty_downgrade_on_a_fresh_site_restores_diesel_only_checks` (7 guarded counts 0, reaches `0025_w2_ev_session`, diesel rows/checks survive); refusal probe keeps populated-state assertions | same | - |
| L5(old) capture revision | `evidence.json` revision `4fb6a401` (final code revision) | - | - |

Heights (app / mock px, same width; all <= 1.30): ev 252/238, 374/356, 374/356, 211/193, 211/193 at 1440; ev-evidence 356/336,
421/336, 421/336; analysis 340/266 (1.28), 170/148; financials 305/285, 269/234, 269/234; assumptions 314/272. At 390:
553/617, 307/269, 153/336, 231/233, 197/193; 417/449, 478/416, 267/319; 302/386, 216/247; 355/422, 285/234 (1.22),
149/142; 345/390. Worst 1.28. No page overflow, clipped cells 0.

Verification (scope: additive EV-only; full backend/host suites not rerun): focused backend on private DB `w207f_test`
(dropped after): `test_w207_ev_money.py`, `test_w207_ev_money_postgres.py`, `test_w207_ev_site_reads_postgres.py` at `4fb6a401`:
32 passed, 1 failed (549 s) - the failure was my test's own suffix map missing `ev_connector_power`; fixed in the next commit and
that test re-run alone: 1 passed. Frontend full: 91 files, 2330 passed. tsc exit 0. check-all: 10/10 guards passed.

Readings made (no ruling contradicted): (1) L5 names `test_r4_ev_currency_and_value_validation_is_ev_only`, a pure validator;
the downgrade probe is in `TestMigration0026`, so I split that. (2) `test_0026_trigger_only_work_...` still uses
`remove_money` for its backfill downgrade/upgrade (not the L5 test; needs a populated Site first); the refusal probes keep
`remove_money` only to clear state between probes. (3) State rows: `unit` set to null (state is not numeric). (4) Event with an
unknown kind: `value_display` null (`Not recorded`). (5) Overview Evidence card note now `4 capabilities` (same L2 rule).
(6) Captures include all five routes, not only the four money routes.
