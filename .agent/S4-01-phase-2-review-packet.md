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

## Fix round 1 (review `.agent/S4-01-phase-2-review.md`; Architect `.agent/architect-S4-01-answers-3.md`)

Code commit `254b843`; closeout commit follows. Diff: `git diff d2599de..HEAD`. New questions: `.agent/S4-01-questions-4.md`
(Q21-Q24, each with a built default). Producer output: `.agent/S4-01-phase-2-fix-finding-cases-run.txt`.

| Item | Fix | Test that fails before it (proven by mutation on the committed code) |
| --- | --- | --- |
| B1 Indeterminate window read as NO_FINDING | `window_state`: Indeterminate window without Findings = `NOT_DETERMINABLE`; body adds `window_claim_level`, `window_limitations`, `selected_run_id`, watermarks | Postgres: every day 10-05..10-23 pinned (`EXPECTED_DAYS`); 10-19 `NOT_DETERMINABLE` with `AMBIGUOUS_COHORT`; 10-15 LIMITED discloses 17 limitations. Branch removed -> `{'2026-10-19': 'NO_FINDING'} != {'2026-10-19': 'NOT_DETERMINABLE'}` |
| B1 "one complete no-Candidate day NO_FINDING" | the fixture has none (the old `in states.values()` hit was 10-19, the defect) | new `test_a_complete_day_without_candidate_is_no_finding` (10-25, Necessary-only run) |
| Q18 completed match before NO_FINDING | `finding_match_pass` row per committed pass (fenced `selection_seq`, matcher version); NO_FINDING needs a v2 pass at or after the window's current selection, else `FINDING_MATCH_PENDING` | same test: before the pass `FINDING_MATCH_PENDING`, after it `NO_FINDING`. Check removed -> `'NO_FINDING' == 'FINDING_MATCH_PENDING'` fails |
| B2 pinned old revision "match pending" | non-latest pin: currentness `SUPERSEDED_BY_LATER_REVISION` + `latest_revision_id` (windows kept); `state.claim_is_current_refers_to: LATEST_REVISION` | Postgres F04 r1 assertions. Mutated -> `'FINDING_MATCH_PENDING' == 'SUPERSEDED_BY_LATER_REVISION'` |
| C3 window-route matrix | (no code defect) | `TestWindowRouteMatrix`: 401 + `WWW-Authenticate` before lookup, 403 before lookup, 404, 503 x2 |
| Q17 stop proof | `FindingMatcher.bases` passes each CURRENT window's selected run input evidence (typed `StateReport`, one read per run) to the pure matcher. `_stop_proof` needs both OFF endpoints in that evidence and every report strictly between last ON and next first ON accepted, GOOD, in the window's cohort and OFF; windows CURRENT, not Indeterminate, no generator cohort limit over the stop. Refused = no bridge; the proof (evidence IDs, run/window IDs, `reports_sha256`) is cited on each bridging stop | `TestStopProof`: contradictory state between two valid OFFs, NOT_GOOD, wrong cohort, positive power, unread reports, series limit, Indeterminate window -> two Findings, empty continuity, recurrence `NOT_ESTABLISHED: SEPARATION_STOP_NOT_CONFIRMED: <reason>`. Bridging on unconfirmed stops -> 7 fail. Postgres F02: every bridging stop `CONFIRMED` with non-empty evidence |
| Q19 cutover gate | `build_finding_router(gate=)` uses `main.performance_gate` (comparison, lineage breaks, other-model heads). An unconfigured gate is closed, and an unreadable one is a typed 503. Closed gate: default detail and window reads are 409 `PERFORMANCE_CUTOVER_CLOSED`. A pinned `revision_id` returns 200 `audit_only`, `SOURCE_CLOSED`, with no S3 read; S3 links are withheld and `links.performance` gives the reason | `TestPerformanceCutoverGate` (6) + Postgres F04 closed-gate asserts. Window gate removed -> 2 fail |
| Q20 relations in the basis | `MATCHER_VERSION = finding-episode-2`. Normalized relation facts (gap bounds, bridged_by, stop OFF times and proof status, recurrence status/prior/OFF times) go into `support_sha256`, and the full continuity/recurrence records (evidence IDs, digests, assessment refs) into `basis_sha256`. The opening recurrence record is carried on `Episode.recurrence`, so replays stay idempotent | `TestRelationsInTheBasis`: one more checked OFF report -> `BASIS_REFRESHED` (basis moved, support equal); a refused proof changes support. Relations removed from basis -> fails |

Q20 existing rows: 0009 is unmerged and has reached only disposable databases. These are the isolated `_test`
databases and `assetops_s4cases`, which are dropped and recreated on every run. A `finding-episode-1` row would
be kept: the basis includes the matcher version, so the next pass appends a revision. Q16 is unchanged
(`DEVELOPMENT_TENANT_OPERATOR_CONTEXT`).

### Checks (fix round)

- Producer on `254b843`: `tools/s4_finding_cases.py run`: 0 check failures, produced in 238 s. F01-gateway: 198
  sealed batches, 329 readings, 1 Finding at 05:15Z, 102 cited IDs with 0 outside gateway batches. Verify: 8
  cases match, 11 Findings / 30 revisions match, replay planned 0, "verify reads: 11 Findings read;
  gateway-case Findings 1; problems 0", `VERIFY PASSED`. The script stopped tls-server, lab-api and gateway, and
  nothing listens on 8730/8763. `assetops_s4cases` dropped.
- S4 tests with Postgres (isolated `assetops_s4p2fix_test`): `57 passed` (read, store, episode, API).
- Backend with Postgres (isolated `assetops_s4p2fix_test`, dropped afterwards) on `254b843`: `1893 passed, 20 warnings in
  621.89s`.
- Host: `667 passed, 3 warnings in 545.72s`. Gateway: `164 passed in 55.09s`. Simulator: `265 passed in 4.17s`.
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: `All 6 guards passed.`; `check-architecture.ps1` passed;
  `check-agent-workflow.ps1` passed.
- Guard extension proof: dropping `finding_match_pass` from the Finding-store table list fails
  `check-architecture.ps1` ("The Finding store only inserts into ... postgres_finding_store.py:133: INSERT INTO
  finding_match_pass"). Reverted with `git checkout --`.
- No frontend change. Layout evidence: not applicable.

### Known deviations / residual risk (fix round)

- Recurrence now uses the stop proof too (Q21). A non-GOOD or contrary report in either separation stop leaves
  the two Findings unlinked.
- `finding_match_pass` was added to the unmerged 0009 rather than a 0010 (Q22). The operator `finding-reads` CLI
  is ungated (Q23).
- The matcher now reads each selected run's full input evidence once per run per pass. That is fine at fixture
  scale. S4-04 should bound it.
- C5 (one-hop canonical) and C6 (window read cost, midnight boundary) still carry.

USER_REVIEW_REQUIRED: owner checkpoint after phase 3. This fix round needs a fresh Claude re-review (no UI).
