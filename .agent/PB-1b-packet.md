# PB-1b packet: EV analysed periods (backend)

Branch `task/PB-1b-ev-periods` (wt `AssetOpsV1-pb1b`), rebased onto main `987d48c78` (PB-1a merged). Card: `.agent/architect-answer-non-kobo-sites-2026-11-10.md` PB-1b (lines 251-255); rule D-E5.31 (line 156); E4 (line 100). PB-1a review notes L1 (widest-wins / nested) and M1 (href is an API route, kept consistent with Cold; UI link is PB-1c) applied.

## What changed

- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py`
  - New helper `widest_periods(periods)`: drops every period lying wholly inside another listed one, so of two stored windows sharing a start only the widest is listed (08:00-09:05 over 08:00-09:00) and a nested window is never listed or shown (PB-1a review L1).
  - `EvReadService._snapshot`, default mode only: explicit window with no exact selected head (rule i failed; EV's W2 default selection is exact-window equality, kept) -> `widest_periods(analysed_periods_in(...))` (PB-1a helper); if any, `shown_analysed_period(..., ev.DOMAIN, ...)` (PB-1a helper) becomes `lo`/`hi` and the head is reselected (ii); none -> today's empty UNKNOWN (iii). Everything after (pending job, `_unassessable` source classification, notes) reads the shown period only, never the union: E4. Snapshot carries `analysed_periods` and `shown_period`. Pinned mode and no-window path untouched.
  - The exact-head SQL moved unchanged into `EvReadService._head` (used twice).
- `backend/assetops_backend/ev_site_reads.py`: `_ctx` adds `analysed_periods: [{from, to, href}]` and `shown_period: {from, to} | null` to the body of all five EV Site reads; `href` = `/api/sites/{code}/ev/overview?from&to&known_at` (same convention as Cold's).
- No frontend change (PB-1c not built).

## Tests (Postgres, own `assetops_pb1b_test`, one file at a time)

`test_pb1b_ev_periods_postgres.py` (new, 9): day over one period; week over several (open Finding wins, else most recent); shared start lists only the widest (late-record + exact 08:00-08:30 selection); nested window never listed/shown and status not UNKNOWN; `widest_periods` unit; none inside incl. straddling window; pinned unchanged; E4 provenance per period (fake classifier answers MIXED for any multi-period window, as `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS` does for a multi-day union; asserts the union is never judged and no unassessable note in envelope or Needs attention); Site reads/API (all five reads, href followed, empty week).
- Before the code: the first 7 tests: 7 failed (KeyError `analysed_periods`; E4 failed on the MIXED assertion). The nested and unit tests were added with the L1 change, so they have no before-code run.
- After, on the rebased head: 9 passed.
- Updated: `test_w207_ev_site_reads_postgres.py` `check_shape` (two new Site-read keys); `test_w301_ev_selection_on_postgres.py` (whole-day snapshot now reads its shown period, not `selected is None`).
- Importers of the changed modules: see the results table below.

| File | Result (rebased head) |
|---|---|
| `test_pb1b_ev_periods_postgres` | 9 passed |
| `test_w207_ev_site_reads_postgres` | 19 passed (after fix: its "empty" window 2026-10-07 08-16 held the replay period, now reads it; moved to 10-27) |
| `test_w206_ev_reads_postgres` | 23 passed (after fix: the wider-window case of `test_exact_window_does_not_use_covering_selection` now reads its period; asserted) |
| `test_w301_ev_selection_on_postgres` | 3 passed |
| `test_w206_ev_store_postgres` | 12 passed + 1 failed in the first run (`[missing-meter]`); rerun of `test_six_cases_persist_the_vectors`: 6 passed |
| `test_w207_ev_money_postgres` | 4 failed / 10 passed in the first run (0026 trigger, money vectors complete/interrupted/fault); rerun of the file: 14 passed. Neither file reads `EvReadService._snapshot`; the first-run failures did not reproduce (machine shared with other agents) |
| `test_polish_pa3_ev_tariff_copy` 2, `test_w301_provenance_dto_postgres` 7, `test_w302_evidence_links_postgres` 3, `test_w302_financials_links_postgres` 3, `test_w302_pinned_facades` 21, `test_w302_pinned_facades_postgres` 8, `test_w503_ev_availability_postgres` 15, `test_w503_ev_depth_postgres` 15, `test_w503_ev_scenarios_postgres` 15, `test_w504_ev_intent_api` 6, `test_w504_ev_intent_postgres` 15 | all passed |

## Notes / risks

- Rule (i) for EV stays exact-window equality (a window strictly inside a stored session is not "contained" -> no period inside -> empty, as today).
- A period wider than the window that shares a start with a narrower one inside it: the narrower one is listed (filter is inside-first).
- The E4 test uses a monkeypatched classifier; a real multi-run MIXED union is not built in a fixture.
- Single-Finding and session reads also follow the rule (EV Finding links already carry the exact window, so no change in practice; a wider window can now resolve instead of 404).
- No full suite (per brief).
