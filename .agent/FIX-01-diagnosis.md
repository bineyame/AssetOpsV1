# FIX-01 step 1 diagnosis: 409 ESTATE_SELECTION_INCONSISTENT on the w504 EV build

Classification: **High, real product defect** (not a fixture artefact). The check works as written but is wrong for a
Finding that is legitimately revised per assessed window.

## Build and reproduction
- DB `assetops_fix01_ev_test` on 127.0.0.1:55432 (alembic head, then the EV_BUILD code from `test_out_b4_board_postgres.py`;
  builder status `ready`, 221 envelopes ACCEPTED, about 60 s). Dropped at the end of the run.
- Reproduced through the real app: `GET /api/estate/findings` and `/api/estate/evidence` for
  [2026-10-06, 2026-10-07) -> 409 `ESTATE_SELECTION_INCONSISTENT`; 5 Oct and 7 Oct -> 200.
  Message: `Finding e0a54f1e-f314-4610-8aab-b77a0b7d0bb9 has two selected revisions at one cutoff.`
  (Finding ids are random per build; `0ccdbf27...` in the earlier report is the same Finding in the earlier build.)
- Hour-sized estate windows are refused (422 INVALID_WINDOW, day-aligned), so no narrower read dodges it.

## Query results (this build)
Finding `e0a54f1e-...` (EV, session-anchored), two revisions:

| rev | no | transition | lifecycle | created_at | episode | assessment_revision |
|---|---|---|---|---|---|---|
| b0bbdbba-... | 1 | OPENED | SUPPORTED | 21:07:13.3593 | 06 Oct 08:01-08:16 | b268076a-... |
| e720ab83-... | 2 | BASIS_REFRESHED | SUPPORTED | 21:07:13.9165 | same | b2697801-... |

Assessment revisions (analytic `ev-session/1`) and selections (`analytic_run_selection`):

| seq | window | assessment | evidence ids | job_id | selected_at | run |
|---|---|---|---|---|---|---|
| 1 | [06 Oct 08:00, 09:05) | b268076a (rev_no 1, key ...T09:05) | 221 | 71235545-... (worker job) | 21:07:13.3593 | c019a60b |
| 2 | [06 Oct 08:00, 09:00) | b2697801 (rev_no 1, key ...T09:00) | 219 | NULL (DEFAULT selection) | 21:07:13.9165 | ff0ed97c |

`finding_revision_assessment`: one WINDOW/primary link per revision (rev1 -> b268076a, rev2 -> b2697801).

Answer: **two different selected windows** (different `window_end`: 09:05 vs 09:00; distinct selection keys), each
selected once, each with its own assessment revision. It is not one window selected twice. Selected EV windows for
6 Oct: exactly those two. Each window's own read is internally consistent (one revision per window).

## Root cause
- `backend/assetops_backend/estate/postgres_estate_read.py:283-319` (`_ev_window`): each selected window returns the
  Finding revision whose `assessment_revision_id` is that window's selected assessment (`_findings`,
  `analytics/adapters/postgres_assessment_store.py:3257-3267`, filter `fr.assessment_revision_id = :ar`). Two windows over
  one session -> the same `finding_id` carries two different `finding_revision_id`s.
- `backend/assetops_backend/estate/coverage.py:249-257` (`_windowed`): merges all windows of the day into `by_finding`;
  `held["finding_revision_id"] != row["finding_revision_id"]` raises `EstateSelectionInconsistent`. That is the firing
  condition: same finding_id, different revision id, from two windows. There is no same-window check; the guard is purely
  cross-window. Confirmed by traceback: raised at coverage.py:256 via `site_coverage` (coverage.py:50), from
  `index.py:115` (findings) and `evidence_money.py:470` (evidence).
- `postgres_estate_read.py:239` is not it: that is only the `except LookupError` (pinned-selection refusal) in
  `selected_windows`, and was not raised here.
- Window selection: `selected_windows_on` (`postgres_assessment_store.py:1923-1945`) returns the latest seq per *exact*
  `(window_start, window_end)` key, so two overlapping keys are both returned.

Verdict: works as written, but its assumption (one selected revision per Finding per day) is false for the EV model, where
a Finding is a lineage and BASIS_REFRESHED revisions are appended per assessed window. It is not catching bad data: both
selections are valid and append-only, and each revision is correctly pinned to its own selected assessment.

## Can real data trigger it? Yes
- `ev_windows` (`postgres_assessment_store.py:1480-1492`): every EV job re-assesses each already-selected overlapping
  window at its exact bounds and aligns the remainder outward to 5-minute brackets. Windows are never merged. The first
  window here is that product output ([08:00,09:05) from data ending about 09:01).
- A later job or reselection over the same session with a different span (more telemetry arriving, or a default or operator
  selection of another window) leaves both windows selected. Any session inside the overlap then gets one revision per
  window: same Finding id, new `basis_sha256` (evidence sets differ, 221 vs 219), so a `BASIS_REFRESHED` revision tied to
  the second window's assessment. An interrupted session spanning two windows is sufficient but not required.
- The test helper `select_exact` (`backend/tests/test_w206_ev_store_postgres.py:370`) documents itself as "the shape any
  earlier job's window would have left", so the fixture reproduces a realistic state, not an artefact.
- Impact: whole-request 409 for estate Findings and estate Evidence over that day, not a per-site degraded row.
- No existing test covers the raise (grep "two selected revisions" in backend/tests: none).
- Not verified: whether Cold can hit the same path (`_cold_window` also filters revisions to the window's chosen
  assessment, so overlapping cold windows may). The check is domain-agnostic; test COLD too.

## Proposed minimal fix
In `coverage.py::_windowed`, replace the raise with supersession within one Finding lineage:
- carry `revision_no` on each row (EV: already `r["revision_no"]` from `_findings`; cold: from the `revisions` rows) from
  `_ev_window` / `_cold_window`;
- when `held` has a different revision id for the same `finding_id`, keep the higher `revision_no` (tie -> later
  `selected_at`, then `seq`, then `selection_id`, the order already used for `latest` at coverage.py:237);
- still raise `EstateSelectionInconsistent` for genuinely bad data: equal `revision_no` with different ids (a fork), or
  two revisions from the same window.
- `selected_assessment_revision_ids` / `cited_accepted_evidence_ids` are currently unions over all windows. Keep as is, or
  restrict to the winning revision's assessment: an Architect decision about provenance.

Tests (backend):
1. Unit on `_windowed`: two windows, same finding, rev 1 vs rev 2 -> one row at rev 2; reversed window order -> same.
2. Unit: same revision_no, different ids -> still raises (prove non-vacuous: remove the guard, watch it fail).
3. Unit: one window yielding two revisions -> raises.
4. Postgres: this EV build (replay + `select_exact`), then `/api/estate/findings` and `/api/estate/evidence` over 6 Oct ->
   200 with exactly one row for the Finding at revision 2; 5 and 7 Oct unchanged.
5. Cold analogue with overlapping selected windows (confirm hit or no hit first).
6. Re-run the w504 outcome-board and portfolio tests that read the covering UTC day (`_covering_day_params`).

## Housekeeping
Only `assetops_fix01_ev_test` was created; dropped at the end. A targeted 3-file pytest from the outD worktree (no full
suite or browser capture) was running on other databases; I did not touch it.
