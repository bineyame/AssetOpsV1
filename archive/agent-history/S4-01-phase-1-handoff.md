# S4-01 phase 1 handoff (PARTIAL - stopped at the context budget)

Branch `task/S4-01-finding-identity`; core commit `bcbc3f4` on top of activation `5f7cd4c`. Status stays `active`.
Do not commit `.agent/coordinator-handoff.md` (owner's working change).

## Landed (committed, `bcbc3f4`)

- `backend/migrations/versions/0009_finding_store.py`: `finding` (immutable key `gen-support:<asset>:<anchor>:<uuid8>`,
  anchor + anchor assessment revision, cohort sha, matcher version, immutable `recurs_after_finding_id` /
  `split_from_finding_id`), `finding_revision` (transition, lifecycle, primary `assessment_revision_id` + run + window
  revision, episode bounds, candidate/necessary/indeterminate minutes, claim/limitations jsonb, basis/cited/input
  digests; UNIQUE `(finding_id, revision_no)` and `(finding_id, basis_sha256, transition)`),
  `finding_revision_assessment` (every interval + window revision with its run), `finding_revision_evidence` (cited
  accepted evidence only; full input set stays via `analytic_run_evidence` of the cited runs), `finding_merge`.
  All append-only (`ledger_append_only`). Head asserts moved to 0009 in `test_s1_bindings_postgres.py:119`,
  `test_s2_evidence_ledger_postgres.py:445`.
- `analytics/finding_episode.py` (pure, `MATCHER_VERSION = "finding-episode-1"`): `plan(windows, episodes, model)`.
  Only CURRENT windows under the current model count; clusters of CANDIDATE segments bridge over <=20 min only through
  observed Necessary or modelling-reason Indeterminate (`dispatch_v3._NOT_EVIDENCE_GAPS`) segments, and across a stop
  only with observed OFF bounds; recurrence link only when an observed OFF separates; component logic for
  open/extend/split/merge; UNCONFIRMED vs NO_LONGER_SUPPORTED for unsupported episodes; MODEL_REEVALUATED; basis hash =
  lifecycle + interval revision IDs + bounds + minutes + cited IDs (window revision cited but not in the basis).
- `analytics/adapters/postgres_finding_store.py`: fifth guarded writer (INSERT-only); `fence` (selection seq + job
  marker), advisory lock, re-check, `FindingFenceMoved`; `rows()` reload for verification/phase 2.
- `analytics/finding_service.py` `FindingMatcher.match(tenant, site)`: reads each assessed day through
  `DispatchReadService.window` (so CURRENT == the read's derived status), plans, applies; retries a moved fence.
- `tools/checks/configuration-persistence.ps1`: Finding store allowlisted, insert-only; other modules may not write
  Finding tables.
- `backend/conversions/s4-finding-cases-v1.json`: stable specification (setup controls; cases F01-F06, F08 with steps
  deliver / held+release / reserve / runtime / assess / match and expected transitions; F07 test-scoped note).
- `backend/tests/test_s4_finding_store_postgres.py`: 5 tests, all pass on isolated DB `assetops_s4p1_test`
  (`CaseRunner` executes the spec through `BatchIngestionService` Batch V2 ingestion, the S3 worker and the matcher;
  each expectation checked against a reload). F07 monkeypatches `dispatch_v3.MODEL_VERSION` to the labelled
  `dispatch-3.1-s4-test-upgrade` (no live upgraded claim).

Fixture learnings: minimum-runtime 30 is in the Kobo Foundation (setup publishes 0 from 10-03); backdated publications
only split the Foundation revision containing `effective_from` (bindings change at 10-02, so setup uses 10-03); late
reports must keep their earlier gateway sequence (`held`/`release`), otherwise `SEQUENCE_ORDER_INVERTED` makes the rest
of the day Indeterminate; a backdated control re-selects new control revision IDs for every later window, so unchanged
episodes append documented `collateral` SUPPORT_CHANGED revisions (F05 steps).

## Guard proof

Run after the commit: appending an `UPDATE finding_revision` line to the Finding store and an `INSERT INTO finding`
line to `finding_service.py` must each fail `tools/check-architecture.ps1`; both reverted with `git checkout --`.
Result on `bcbc3f4`: both failed ("The Finding store only inserts into ... postgres_finding_store.py:214" and "A second product database writer in ... finding_service.py:57"); reverted, tree clean. `tools/check-architecture.ps1` passes on the commit.

## Next (resume here)

1. `tools/s4_finding_cases.py run|verify` modelled on `tools/s3_dispatch_cases.py` (`class Cases(s2.Demo)`, DB
   `assetops_s4cases`, own ports, e.g. TLS 8763 / HTTP 8730; avoid 8000, 5173/5183/5199/5213/5291, 8610/8643, 8710/8743):
   import KOBO-001, `demo_configuration --steps properties,bindings`, F01 also as a gateway-sealed Lab run if cheap
   (S3 case 02 `prolonged` roles-2 yields a CANDIDATE interval), all spec steps as labelled authenticated Batch V2
   posts (`post_fixture`/`seal_batch_v2` precedent) to `/api/ingestion/batches`, controls through `FoundationService`
   CLI or a small `-m` entry, `assess_dispatch process-jobs`, then a `match-findings` CLI (add a subcommand to
   `analytics/assess_dispatch.py` calling `FindingMatcher`). Write the environment-bound run artifact (batch, evidence,
   run, Finding/revision IDs) under the work dir, not committed as "current"; `verify` reloads and compares.
2. Optional: pure unit tests for `finding_episode.plan` (no DB).
3. Full suites (backend with Postgres on an isolated `_test` DB, host, gateway, simulator from `simulator/`),
   `tools/check-all.ps1 -ExecutionPolicy Bypass`, drop `assetops_s4p1_test` and any producer DB.
4. `.agent/S4-01-questions-1.md` (batched, fail-closed defaults): Q1 technical design `UNIQUE(finding_id,
   assessment_revision_id)` replaced by `(finding_id, basis_sha256, transition)` (a cross-window episode can keep its
   primary interval while another changes); Q2 modelling-reason Indeterminate may bridge (<=20 min); Q3 recurrence link
   only with an observed OFF; Q4 window revision excluded from the basis; Q5 collateral revisions after a backdated
   control (Foundation split re-IDs controls); Q6 fixture is labelled authenticated (not gateway-sealed) except any Lab
   case; Q7 lifecycle has no mutable `closed_at` (derived from the latest revision).
5. Review packet `.agent/S4-01-phase-1-review-packet.md`, `.ai/CODE_STATE.md` entry (<40 lines),
   `.ai/ACTIVE_CONTEXT.md` pointer.

## Open risks

- The matcher reads every assessed day per pass (one window read each); fine for fixtures, linear in days.
- Merge with three or more episodes and mixed split+merge in one component is implemented but only the two-way cases
  are fixture-tested.
- `apply` raises `FindingFenceMoved` when a cited evidence ID is not accepted in the Site (defensive).
