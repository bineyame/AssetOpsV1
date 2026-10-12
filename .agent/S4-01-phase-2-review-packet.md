# S4-01 phase 2 review packet - `I-finding-read`

Task: `tasks/S4-01-finding-identity.md`, phase 2 row and "Detail read and visible states" (Status stays `active`).
Branch `task/S4-01-finding-identity`; phase 2 = `1e24e4d` (read, routes, relation records, tests), `72aec76`
(producer R2/manifest/verify reads), `2d980db` (tightened test, R3, questions, run record), closeout commit.
Diff: `git diff 0484268..HEAD`. Authority: `D-2026-10-12-finding-episode-and-revisions`, phase-1 and phase-1-fix
clarifications (Q1-Q15), `D-2026-10-09-pre-s3-claim-routes-and-actor`. Questions: `.agent/S4-01-questions-3.md`.

## Outcome delivered

- `GET /api/sites/{site_code}/findings/{finding_id}` (optional exact `revision_id`; `after_revision_no`/`limit`
  paging): stable root (ID, key, anchor, cohort, matcher), `selection` (LATEST_RECORDED or EXACT_REVISION_ID,
  latest ID, `is_latest`, no-`knowledge_at`-replay statement), the selected revision (transition, lifecycle,
  claim, limitations, Candidate/Necessary/Indeterminate minutes, primary + every interval/window AssessmentRevision
  with run, model, cohort, window, Foundation/binding revisions, input evidence count, basis/support/cited/input
  digests, exact cited accepted evidence with batch/gateway/source/epoch/as-accepted revisions, OFF report
  evidence, previous revision ID), `state` (recorded lifecycle vs projection), `relations` (canonical, merged
  into/from, split from/parts, recurs after/recurred by, recurrence record), every revision summary,
  `revision_groups` hint, provenance by source plus manifest case labels, watermarks, typed unavailable
  money/Action/Evidence/History/list/control-route, and back-links (canonical, pinned revision, S3 revision/window).
- `GET /api/sites/{site_code}/finding-windows/{day}`: NOT_ASSESSED / PENDING / STALE / FAILED / NO_FINDING /
  FINDING_MATCH_PENDING / FINDINGS_RECORDED for one UTC day (Q18).
- Matcher records `claim.continuity` and `claim.recurrence` (Q2/Q3/Q11/Q13 phase-2 requirements; Q20).
- Producer: R2 assertion, case manifest (`fault_fixture` / opt-in `gateway_sealed`), `verify` through the read.

## Files materially changed

`backend/assetops_backend/analytics/finding_read.py` (new), `backend/assetops_backend/finding_api.py` (new),
`.../analytics/finding_episode.py`, `.../analytics/adapters/postgres_finding_store.py` (read methods),
`.../analytics/adapters/demo_manifest_file.py`, `.../analytics/composition.py`, `.../analytics/assess_dispatch.py`
(`finding-reads`), `backend/assetops_backend/main.py`, tests `test_s4_finding_api.py` (new),
`test_s4_finding_read_postgres.py` (new), `test_s4_finding_episode.py` (+5), `tools/s4_finding_cases.py`.

## Acceptance criteria (phase 2)

| Criterion | Status | Evidence |
| --- | --- | --- |
| Tenant/Site-scoped exact root read at the A-claim-work-routes API | Met | route resolves Site via `registry.ledger_scope`; store queries filter `tenant_id`/`site_id` |
| Omitted revision = latest; exact `revision_id` pins history | Met | Postgres test: every Finding latest == stored last; F04 r1 pinned (`is_latest` false, 08:30 start) after r2 |
| 401 / 403 / 404 / typed unavailable | Met (401/403 via seam, Q16) | `test_s4_finding_api.py`: 401 before lookup + `WWW-Authenticate`, 403, unknown Site 404, None 404, 503 x2; Postgres: random ID, other Finding's revision, unknown Site 404, malformed 422 |
| Selected S3 lineage: run/model/cohort/window/supporting revisions, digests | Met | per-revision window/interval IDs equal stored `finding_revision_assessment`; `runs` carry model/cohort/config/Foundation/binding |
| Cited accepted evidence vs full input set | Met | `cited_evidence` == stored `finding_revision_evidence`, all ACCEPTED; `input_evidence_count` per run + `input_evidence_sha256` |
| Currentness; "currently selected window" uses the basis window set (carry) | Met | `_currentness` uses the revision's own WINDOW citations; stale test: STALE -> FINDING_MATCH_PENDING -> CURRENT |
| Honest states: no Finding vs not assessed vs stale | Met | window_state NOT_ASSESSED (09-01), STALE with "not a no-Finding verdict", NO_FINDING on an assessed no-Candidate day, FINDING_MATCH_PENDING |
| BASIS_REFRESHED each selectable, `support_changed:false`, grouped only as hint | Met | Postgres + pure grouping test; `revisions` never squashed; group counts sum to revisions |
| Old/new pinned lineage | Met | F04 r1/r2 primary differ, r2 `prior_interval_*` == r1 IDs; F06 superseded and canonical both 200 |
| Q10 closure preserved | Met | F05: UNCONFIRMED and final NO_LONGER_SUPPORTED on one ID, `claim_is_current` false |
| Q11 stop bridge record | Partly (Q17) | F02 continuity: `bridged_by`, both OFF times, `candidate_minutes_added "0"`; intervening ON tested; contradictory-between-OFFs not visible |
| Q12 merge read | Met | `merged_into_finding_id`, `canonical_finding_id`, `merged_from`, `MERGED_INTO_CANONICAL` projection, canonical link |
| Q13 recurrence read | Met | LINKED: both OFF bounds resolved to accepted evidence IDs + covered window IDs; others NOT_ESTABLISHED + reason |
| Q15 gateway case distinct from fault fixtures | Met | producer verify: gateway Finding annotated only `DEMO_MANIFEST_GATEWAY_CASE`, others `..._FAULT_FIXTURE` |
| No arbitrary `knowledge_at` replay | Met | no such parameter; `selection.replay` states it |
| R2 gateway cited evidence subset | Met | producer: "102 IDs, 0 outside the gateway-sealed batches OK" |
| R3 stale packet text | Met | phase-1 packet residual risk rewritten |

## Producer run (`.agent/S4-01-phase-2-finding-cases-run.txt`, code `72aec76`)

`.venv/Scripts/python.exe tools/s4_finding_cases.py run`: 0 check failures, produced in 204 s; F01-gateway 198
sealed batches, 329 accepted readings under `s4-gateway-epoch-1`, 1 Finding OPENED at 05:15Z, cited 102 IDs all
from gateway batches. Verify: 8 case digests match; 11 Findings / 30 revisions reloaded match; replay planned 0;
"verify reads: 11 Findings read; gateway-case Findings 1; problems 0"; `VERIFY PASSED`, exit 0. DB
`assetops_s4cases` dropped; no listener on 8730/8763.

## Checks run

- Backend with Postgres (isolated `assetops_s4p2_test`, dropped afterwards) on `2d980db`: `1871 passed, 20 warnings
  in 598.03s` (includes 2 new Postgres read tests, 6 API matrix tests, 5 new pure matcher tests).
- Host: `667 passed, 3 warnings in 610.05s`. Gateway: `164 passed in 60.75s`. Simulator (from `simulator/`):
  `265 passed in 3.67s`.
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: `All 6 guards passed.`; `check-agent-workflow.ps1`: `Agent
  workflow check passed.`
- Guard coverage proof: an `INSERT INTO finding_revision` line appended to `finding_read.py` failed
  `check-architecture.ps1` ("A second product database writer in ...finding_read.py:269"); reverted with
  `git checkout --`. No new guard was added.
- Mutation proof (committed first): `cited_is_current_selection` forced true -> stale test failed
  `assert 'CURRENT' == 'FINDING_MATCH_PENDING'`; reverted, tree clean.
- No frontend change; frontend suites not run. Layout evidence: not applicable (no UI).

## Known deviations

- 401/403 are produced by an injectable `access` seam; the default admits the development tenant (parity with
  S3 Performance), labelled `access_basis` in every body (Q16).
- Contradictory report between stop OFFs is not detected (Q17); intervening ON is.
- Extra route `/api/sites/{site_code}/finding-windows/{day}` (Q18); ungated by the Performance cutover (Q19).
- Relation records live in `claim` jsonb, outside the basis digest (Q20).

## Residual risk

- Currentness calls the S3 window read once per cited window per request (a long cross-day Finding costs N reads).
- `revision_groups` is computed over all revisions while `revisions` is paged.
- OFF evidence is resolved by role + exact time inside the cited interval revision's evidence; two accepted
  reports at one instant would both be listed.

## User-review focus

USER_REVIEW_REQUIRED: true for S4-01 at the owner checkpoint after phase 3; phase 2 needs a fresh Claude review
(no UI). Reviewer: rerun the producer and `test_s4_finding_read_postgres.py`; check Q16-Q20 defaults; compare
returned IDs with stored relations for F01, F04, F05, F06 and the gateway case.
