# PB-1a packet: Cold analysed periods (backend)

Branch `task/PB-1a-cold-periods` (wt `AssetOpsV1-pb1`), from main `fd9c88860`. Card: `.agent/architect-answer-non-kobo-sites-2026-11-10.md` PB-1a; rule D-E5.31.

## What changed

- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py`
  - New module helpers, reusable by PB-1b (EV): `analysed_periods_in(c, t, s, analytics, lo, hi, known)` (distinct stored selected windows wholly inside `[lo, hi]`, run known by `known`) and `shown_analysed_period(c, t, s, domain, periods, known)` (most recent period holding an open Finding of `domain`, else most recent; open = latest revision known at the cutoff is `SUPPORTED`, the frontend's own "open" test; most recent = latest `(window_end, window_start)`).
  - `ColdReadService._snapshot`: the per-analytic selection loop moved unchanged into `_select`. Default mode, explicit window, no covering selection (rule i failed) -> list periods inside; if any, the shown period becomes the snapshot's `lo`/`hi` and is reselected (rule ii); none -> today's empty selection (rule iii). Pinned mode and the no-window (latest) path are untouched. Snapshot carries `analysed_periods` (list of `(from, to)`) and `shown_period` (tuple or None).
  - New kwarg `analysed_periods=True`; the single-Finding read `finding()` passes `False` so a Finding link with a wider window still resolves by anchor (no 404 regression).
- `backend/assetops_backend/analytics/cold_site_reads.py`: `ColdSiteReadService._envelope` adds `analysed_periods: [{from, to, href}]` and `shown_period: {from, to} | null` to all five Site reads (overview, evidence, evidence/analysis, financials, financial-assumptions). `href` = overview API read of the period's exact window at the same `known_at` (same convention as the read's other `links`).
- No frontend change (PB-1c not built).

## Semantics carried

| Case | `analysed_periods` | `shown_period` | envelope `window` |
|---|---|---|---|
| (i) window equals / inside a stored selection, or no window | `[]` | null | as requested |
| (ii) periods inside | all, ordered by start | chosen period | the shown period (the read is about it) |
| (iii) none inside | `[]` | null | as requested; status UNKNOWN |

## Tests (Postgres on own `assetops_pb1a_test`)

| File | Before | After |
|---|---|---|
| `test_pb1a_cold_periods_postgres.py` (new: day over one period; week over four, failure day wins + most-recent fallback; none inside incl. straddling window; pinned unchanged) | 4 failed | 4 passed |
| `test_w204_cold_reads.py` (+1 router test: day window on all five reads, href follow, empty week) | 21 tests (not rerun on main) | 22 passed |
| `test_w301_cold_selection_on_postgres.py` (assertion `whole_day["selected"] == {}` updated to the new rule) | - | 4 passed |
| Importers of the changed modules, one at a time: `test_w203_cold_reads_postgres` 6, `test_polish_pa2a_server_copy` 14, `test_w302_evidence_api` 19, `test_w302_evidence_links_postgres` 3, `test_w302_financials_links_postgres` 3, `test_w302_pinned_facades` 21, `test_w302_pinned_facades_postgres` 8, `test_w501_cold_depth_postgres` 12, `test_w501_cold_depth_router` 4, `test_w501_cold_scenarios_postgres` 7 | - | all passed |

Week fixture: the three extra periods are inserted `analytic_run_selection` rows re-selecting the same stored runs on later days (append-only table; no hand-made assessment or Finding rows).

## Not done / notes

- PB-1c (window-bar literals, `No analysed period in this range` words) not built; the backend carries the fields only. Case (iii) keeps today's empty-state text.
- PB-1b (EV) not built; the two helpers take `analytics` and `domain` for it. PB-1b's "widest wins on shared start" is not in `analysed_periods_in`.
- Envelope `window` reports the shown period in case (ii); the frontend window bar should keep showing the requested range from the URL (PB-1c).
- Cold depth reads (`cold_depth.py` via `selection_on`) and the Findings list follow the shown period too (previously empty for a day/week window).
- Only the 12 files above were run; no full suite (per brief). Process slip: one test function was appended to `test_w204_cold_reads.py` with a shell `>>` instead of Edit.
