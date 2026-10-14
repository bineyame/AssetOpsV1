# S4-02c phase 1 handoff - transactional acceptance work

Implementer: fresh Claude, 2026-10-14. Branch `task/S4-02c-evidence-consequence-work` from `5af9f214`. Phase 1 only (packet table row 1; items 1, 2, 5 and the item 3 unknown-cause guard). No phase 2 drain/runner, no phase 3 walkthrough. Built state: `.ai/CODE_STATE.md` "S4-02c phase 1".

## Built

- `backend/migrations/versions/0012_evidence_consequence_work.py` (new head). See its docstring. Key names:
  - columns `financial_consequence_work.accepted_evidence_id`, `financial_consequence_work_attempt.no_op_reason`;
  - constraints `financial_consequence_work_cause_check` (three causes), `financial_consequence_work_cause_shape` (three arms), `financial_consequence_work_evidence_fk` (scoped), `financial_consequence_attempt_no_op_reason`;
  - indexes `financial_consequence_work_finding_revision_once` (partial, FRA), `financial_consequence_work_evidence_once` (partial, `(accepted_evidence_id, finding_revision_id)`), `financial_consequence_work_finding`, `financial_consequence_attempt_latest`;
  - functions/triggers `financial_consequence_dirty_on_evidence` (new, on `ingestion_disposition` WHEN ACCEPTED) and the replaced `financial_consequence_dirty_on_finding_revision`; both use the module constant `ENQUEUE_LOCK` verbatim (N6).
  - `NO_OP_REASONS` enum in the CHECK: `FINDING_REVISION_SUPERSEDED`, `EVIDENCE_ROLE_NOT_RELEVANT`, `EVIDENCE_ASSET_NOT_RELEVANT`, `EVIDENCE_OUTSIDE_CANDIDATE_TIME` (see Deviations).
- `financials/adapters/postgres_consequence_store.py` `chain()`: pending SQL matches `w.cause IN ('FINDING_REVISION_APPENDED', 'EVIDENCE_ACCEPTED') AND w.finding_id = :f`; selects `accepted_evidence_id`.
- `financials/consequence_read.py`: `NO_WORK_RECORDED` constant appended to STALE reasons when no pending work touches the read; `pending_work` items add `finding_revision_id`, `accepted_evidence_id` (diagnostics). No `REASONS` change; bridge still uses `REASONS["STALE"]`/`["STALE_QUEUED"]`.
- `financials/recompute.py`: `CAUSE_FINDING_REVISION`, `CAUSE_ASSUMPTION`, `CauseNotSupported`, `ERROR_CAUSE_NOT_SUPPORTED`; `targets()` dispatches the two 0011 causes explicitly and raises for anything else; `process()` records a typed FAILED attempt.
- `tools/checks/configuration-persistence.ps1`: rule 8 comment and failure message now name the 0011/0012 triggers (N8). Logic unchanged; this is not a rule amendment.

## Proofs (tests)

`backend/tests/test_s4_evidence_consequence_work_postgres.py` (12 tests) and `backend/tests/test_s4_consequence_cause_dispatch.py` (2, no DB):
committed acceptance -> one row with exact accepted/Finding/revision IDs and reading interval; trigger failure rolls back accepted evidence and disposition; exact replay, DUPLICATE, REJECTED, CONFLICT enqueue nothing; reading ending at `episode_start`, starting at `episode_end`, zero-width latest episode, non-power role (pv) enqueue nothing (C3); post-0012 FindingRevision append writes exactly one FRA row and coexists with evidence work for the same revision, superseded revision not selected, both partial unique indexes enforce (C1); three-arm shape, cause CHECK, scoped FK, `no_op_reason` CHECK; Site B (KOBO-002) reading at identical times enqueues nothing for Site A and its accepted ID cannot be named by Site A work (C4 enqueue half); identical lock text in both stored function bodies (N6); two-connection race (connection 1 holds an uncommitted FindingRevision append, acceptance waits on the advisory lock, then selects the new revision) (M4); 0011 bootstrap rows identical across 0011 -> 0012 upgrade; empty downgrade restores 0011 body/CHECK/UNIQUE and FRA enqueue still works; downgrade refuses while evidence work exists, version stays 0012, rows intact; `chain()` evidence match -> STALE + `STALE_QUEUED`, worker records `CAUSE_NOT_SUPPORTED` without appending, then STALE with no pending work -> `NO_WORK_RECORDED` and `REASONS["STALE"]`.

## Checks as observed

- Mutation proofs (scratchpad script, fresh `assetops_s402c_mut_test` per mutation, file restored by `git checkout`): 12/12 killed - evidence trigger without lock (2 failed), FindingRevision trigger without lock (1), zero-width episode allowed, `>=` overlap at episode_start, no stored-role filter, no Site filter, DUPLICATE also enqueues, not-latest-only, downgrade without refusal, `chain()` ignores evidence, no `NO_WORK_RECORDED`, unknown cause falls through (3 failed). The role and DUPLICATE mutations first SURVIVED; the tests were strengthened (non-power interval mean; duplicate after a new latest revision) and both then failed.
- Rule 8 (C2): appending `INSERT INTO financial_consequence_work` to `recompute.py` made `tools/check-architecture.ps1` fail ("A second product database writer ... recompute.py:148"); reverted.

- Focused: `test_s4_evidence_consequence_work_postgres.py` 12 passed; `test_s4_consequence_store_postgres.py` + `test_s4_consequence_recompute_postgres.py` 24 passed; `test_s4_consequence_cause_dispatch.py`, `test_s4_consequence_read.py`, `test_s4_assumption_read_api.py`, `test_s4_finding_api.py` 43 passed.
- Full backend (`assetops_s402c_p1_test`): 2 failed, 2064 passed in 12:15. Both failures were hard-coded head revisions (`test_s1_bindings_postgres.py:119`, `test_s2_evidence_ledger_postgres.py:445`, expected `0011_financial_consequences`); updated to `0012_evidence_consequence_work`, those two files then 40 passed. The full suite was not rerun after that test-only change.
- `tools/check-all.ps1`: All 9 guards passed.
- Frontend: not run (no frontend file changed; `pending_work` items gained two backend fields that no component reads).

## Deviations

- `no_op_reason` is a closed enum of four codes chosen from N1's safe no-op set (wrong Site is a FAILED attempt per item 3, so it has no no-op code). If phase 2 needs another code it must add a migration; a format-only CHECK was the alternative.
- Downgrade also refuses while any attempt has a `no_op_reason` (the packet names only evidence work rows); same never-delete rule.
- Phase 1 chose "typed failure" (not "skip") for unsupported causes: `EVIDENCE_ACCEPTED` work drained by today's CLI records `CAUSE_NOT_SUPPORTED` FAILED attempts and `run` exits 1 until phase 2. The work stays pending and visible (`last_error_code`), which keeps the read at STALE/`STALE_QUEUED`.
- Guard rule 8 message text changed along with the comment (N8), no logic change.

## Questions

None opened. No owner-facing text was added (USER_REVIEW_REQUIRED conditions (a)/(b) intact).

## What phase 2 needs

- Replace `CauseNotSupported` for `EVIDENCE_ACCEPTED` in `recompute.py` `targets()/process()` with the scoped recheck (item 3, N1: no-op only for role/asset/no-overlap/superseded; never on quality). Record no-ops via `record_attempt(..., succeeded=True, consequence_revision_ids=())` plus a new `no_op_reason` argument (the column exists; `record_attempt` does not write it yet).
- "Latest eligible revision": highest `revision_no` in the same tenant/Site, as the trigger SQL in 0012 does (`r.tenant_id/site_id` scoped subquery). Note `latest_revisions_overlapping` (0011-era) scopes the max subquery by `finding_id` only.
- Runner, Site claim on a dedicated connection (N3), injectable `now` (N4), retry schedule from the last FAILED attempt (`financial_consequence_attempt_latest` index), CLI `run --tenant --site --limit`. R2 bounded-batch test.
- `pending_work()` still lists all causes oldest first; phase 2 adds due/deferred filtering.

## Risks

- Every accepted generator-power mean with an overlapping Finding now takes the Site enqueue lock inside the ingestion chunk; it serializes with `match-findings` FindingRevision inserts on that Site (re-review residual risk). Not measured in phase 1; R2's test should log chunk latency.
- Owner/reviewer databases at 0011 are untouched until they run `alembic upgrade head`.
