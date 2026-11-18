# S3-01 review packet (all phases: 1, 2, 3a, dispatch-3.1, R1, 3b)

Task: `tasks/S3-01-dispatch-assessment.md`. Branch `task/S3-01-dispatch-assessment`. USER_REVIEW_REQUIRED: true (owner checkpoint). Status: `in_review`.

## Outcome delivered

A typed, persisted dispatch assessment (`dispatch-3.1`): role vocabulary and fixture, durable runs/revisions and recompute worker, selected-window/interval read API with derived status, the file-backed comparison and cutover gate, and the Performance > Dispatch and Analysis UI for imported Sites. Earlier packets are cited, not restated.

## Review files

| Phase | Packet / handoff | Review |
| --- | --- | --- |
| 1 | `.agent/S3-01-phase-1-review-packet.md`, `S3-01-phase-1-handoff.md` | `S3-01-phase-1-review.md`, `S3-01-phase-1-fix-rereview.md` (accept) |
| 2 | `.agent/S3-01-phase-2-review-packet.md` | `S3-01-phase-2-review.md`, `S3-01-phase-2-fix-rereview.md` (accept) |
| 3a, dispatch-3.1, R1 | `.agent/S3-01-phase-3a-review-packet.md` (incl. "dispatch-3.1", "Fix round (R1)"), `S3-01-phase-3a-handoff.md`, `S3-01-dispatch-3-1-handoff.md` | `S3-01-phase-3a-review.md` (R1 block; R2-R5 carried), `S3-01-R1-rereview.md` (accept; C1, C2 carried) |
| 3b | `.agent/S3-01-phase-3b-handoff.md`, `S3-01-phase-3b-dispatch-evidence.txt`, `S3-01-phase-3b-shots/`, `S3-01-owner-walkthrough.md` | none yet |
| Questions | `.agent/S3-01-questions-1.md` to `S3-01-questions-5.md` | |

## Phase 3b: files materially changed

- Backend: `analytics/performance_comparison.py` (`comparison_summary`, `classified_revision_ids`, R2 recheck in `permits_performance_cutover`), `performance_api.py` (cutover route returns `comparison`; R3 closed 503 body), `main.py` (live `selected_intervals` and report wiring).
- Frontend: `sites/performanceDispatchClient.ts`, `sites/dispatchWords.ts`, `sites/PerformanceDispatch.tsx`, `SitePerformance.tsx` (renders it when the legacy declaration is AWAITING_EVIDENCE_MIGRATION), CSS at the end of `ui/primitives.css`.
- Tools: `tools/s3_dispatch_walkthrough.py` (prepare/serve/recover), `tools/s3-dispatch-evidence.mjs`.
- Tests: `backend/tests/test_s3_performance_cutover.py`, `test_s3_dispatch_read_postgres.py` (R1-C1 recovery test), `frontend/src/sites/__tests__/performanceDispatch.test.tsx` (12).

## Acceptance (task "Read states and acceptance")

| Criterion | Status | Evidence |
| --- | --- | --- |
| Read returns Site/window, cutoff, selected IDs, evidence, coverage, limitations, watermarks, derived status; `NO_PENDING_DISPATCH` is not CURRENT | Met | 3a packet; UI shows every status (test + evidence 32/32) |
| UI: interval list, bounded segment durations, selected interval/revision, AcceptedEvidence drill-down; honest states for missing role/config, contradiction, weak quality, ambiguous cohort, worker failure; selection and reload keep IDs | Met | `performanceDispatch.test.tsx`; evidence: keyboard Enter selects a block, reload keeps revision/block/records (390 and 1440) |
| Comparison before switching the Performance read; unproven keeps cutover closed | Met | 3a `TestComparison`/`TestGate`; 3b R2 (classified revisions rechecked), R3 (closed 503); live PASSED with an empty set, shown as "not a match" |
| Late evidence: new revision and job, old addressable; replay no duplicate; failed worker retries; race never CURRENT | Met in backend; UI history by tests only | Phase 2 and 3a Postgres tests; R1 recovery; pinned older revision on another day shown (evidence) |
| V-01 `dispatch:1-3` app versus mock at desktop, narrow, interaction; supported portions and omissions stated | Met with omissions | table below |
| `analysis:1,3` supported portions, `:2` fuel gated | Met | Analysis view: constraints, confidence/coverage/unavailable, stored record, history, comparison; fuel/money/Finding gated and typed unavailable |
| Reviewer path: manifest IDs, open Necessary/Candidate/Indeterminate after reload, follow a value to evidence, old/new revisions, overlap isolation, comparison gate | Met | `S3-01-owner-walkthrough.md`; `tools/s3_dispatch_cases.py run` then `verify` (isolated DB `assetops_s3cases`) |

V-01 (mock `dispatch:1-3` versus app):

| Mock panel | App | Deliberate omission |
| --- | --- | --- |
| 1 Overview | Status line, totals, periods and 15-minute blocks, limitations, coverage, comparison line | single-hour EAT window |
| 2 Selected period/block | Selected period/block and records drill-down (cap 60 per scope) | chart of power readings; fuel notice |
| 3 Evidence/outcome | Stored record and history (Analysis) | Finding link (gated) |

## Checks run (tree `4f56b89` plus closeout docs)

- Backend with Postgres (isolated DB `assetops_s3close_test`, dropped afterwards): `pytest backend/tests -q` 1836 passed, 18 warnings, 344s.
- Host `pytest host -q` 667 passed, 3 warnings. Gateway `pytest gateway -q` 164 passed. Simulator (from `simulator/`) 265 passed.
- Frontend: `npx vitest run` 54 files, 1282 passed; `npx tsc --noEmit -p .` clean; `npm run build` built (chunk-size warning only).
- `tools/check-all.ps1` (ExecutionPolicy Bypass): all 6 guards passed.
- Layout/interaction: `tools/s3-dispatch-evidence.mjs` 32/32 claims at 1440 and 390 (`S3-01-phase-3b-dispatch-evidence.txt`). It found a real narrow overflow, fixed with a `minmax(0, 1fr)` column. Gate-test mutations and reverts are recorded in the 3a packet and 3b R2/R3 commits.

## Known deviations

- No list of assessed days: `?day=` absent opens on today UTC (usually "Not assessed"). Q17.
- Older-rule label and late-evidence history proven by tests only; the fixture has no `dispatch-3` run. Q18.
- (Superseded by the fix round below: demonstration notes now show on the Overview. Q19 answered.)
- Staged FAILED/STALE days have no interval; "prior result kept" is the window assessment. Q20.
- `classified_revision_ids` rechecks are skipped for empty-set reports by design.
- The committed `.agent/S3-01-dispatch-cases-v1.manifest.json` was refreshed from the producer work-dir manifest at closeout. Evidence IDs are per run: a new producer run changes every ID and the committed copy goes stale. Q21.

## Residual risk and carries

- R1 carries: C1 closed by `test_comparison_classifies_a_recovered_interval_after_a_superseded_failed_job_r1_c1`; C2 (overlap-based supersession, low) still carried.
- 3a review carries: R2, R3 built in 3b; R4 (0008 does not backfill 0007 selections, theoretical) and R5 (producer first-run harness fragility) remain carried.
- A window read evaluates the full input basis per request; `run_pending` reconciles every assessed Site per pass.
- Cutover opens only on a PASSED report; the empty legacy inventory is a zero-inventory comparison, not classification parity.

## User-review focus

Run the walkthrough (`tools/s3_dispatch_walkthrough.py prepare`, `serve`; steps in `.agent/S3-01-owner-walkthrough.md`) and judge: plain wording, the "Not assessed" default day, the Analysis gating of fuel/money/Finding, and Q17-Q22.

## Fix round (3b)

Against `.agent/S3-01-phase-3b-review.md`. C3 and C4 not worked (carried).

- **B1** `PerformanceDispatch.tsx`: window `demo_annotations` render on the Overview/Analysis whenever non-empty (`WindowView`), independent of any selection; the records panel shows only per-result notes not already shown. Test: window with notes and no periods. Guide and Q19 corrected, known-deviation line superseded.
- **B2** coverage row relabelled "Reported battery reserve level (the reserve used comes from site settings)". Test added.
- **C1** `CAPABILITY_SHORTFALL`, `OPERATOR_OVERRIDE`, `MINIMUM_RUNTIME` and `NO_COHORT` have plain words; the never-emitted `LOAD_ABOVE_CAPABILITY` entry removed.
- **C2** selected block shows one plain "missing or limited" line (the exact strings stay in Analysis); quality "Good" and UTC stamps replace `GOOD`/raw ISO; "Stored result" id removed from the Overview (kept in Analysis); the closed-cutover default view is plain, with the class codes, lineage dump and backend reason only in the Analysis view.
- **C5** no-series day says records exist but none is used; MISSING_ROLE says "for part of the day".
- **C6** `prepare` now stops on a failed comparison and on missing prerequisites; the guide lists prerequisites and the stop behaviour.
- **C7** day-total cards and a note are marked not current on a stale or failed day.
- New/changed tests: 9 (8 failed before the change, as run; the Analysis-closed-path test is a guard). `performanceDispatch.test.tsx` 20 passed.
- Evidence: `tools/s3-dispatch-evidence.mjs` re-run on its own ports (8820/5320, stopped): 32/32, `.agent/S3-01-phase-3b-dispatch-evidence.txt`. `prepare` run once on HEAD: comparison PASSED, cutover permitted.
- Still needs a fresh re-review; Status stays `in_review`.

