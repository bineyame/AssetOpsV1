# S4-02c review packet: consequence work on accepted evidence (all three phases)

Task: `tasks/S4-02c-evidence-consequence-work.md` (registry node `I-evidence-acceptance-consequence-work`).
Branch `task/S4-02c-evidence-consequence-work` from main `f9d6d1a5`; built `5af9f214..HEAD`. Status `in_review`.
USER_REVIEW_REQUIRED: **false** — both packet conditions hold: (a) the stale-without-work discrepancy is the typed
code `NO_WORK_RECORDED` with no new owner-facing sentence; (b) Leg A ends on the existing reviewed
`QUANTITY_UNAVAILABLE` + `POWER_NOT_IN_ASSESSMENT_INPUTS` copy. Independent implementation review is required.

## Outcome delivered

A genuinely accepted late generator-power mean that can alter an existing FindingRevision's `fuel-cost-1`
technical input now creates durable `EVIDENCE_ACCEPTED` work atomically with acceptance (migration 0012 trigger on
the ACCEPTED disposition, Site advisory lock shared with the FindingRevision trigger). The read shows
`STALE/TECHNICAL_INPUT_CHANGED` with the real queued work ID (bridge `STALE_QUEUED`). A Site-claimed, bounded,
one-shot runner drains it on the same FindingRevision to `CURRENT QUANTITY_UNAVAILABLE/
POWER_NOT_IN_ASSESSMENT_INPUTS`; S3 `process-jobs` + S4 `match-findings` then append a revised FindingRevision
whose own work drains to `CURRENT PRICED` (S5 money-eligible). All revisions remain inspectable. Shown end to end
on a new authored variant by `tools/s402c_late_power_walkthrough.py` (`.agent/S4-02c-walkthrough-evidence.md`).

## Files materially changed

- Phase 1: `backend/migrations/versions/0012_evidence_consequence_work.py`;
  `backend/assetops_backend/financials/{adapters/postgres_consequence_store.py,consequence_read.py,recompute.py}`;
  guard rule 8 comment (`tools/checks/configuration-persistence.ps1`, N8, logic unchanged);
  `backend/tests/test_s4_evidence_consequence_work_postgres.py`, `test_s4_consequence_cause_dispatch.py`.
- Phase 2: `recompute.py` (dispatch, `evidence_no_op`, `run`, retry schedule, `RunReport`),
  `postgres_consequence_store.py` (`evidence_target`, `claim_site`, `pending_work` last-attempt fields,
  `record_attempt(no_op_reason=)`), `backend/assetops_backend/recompute_consequences.py` (`run --tenant --site
  --limit`), `backend/README-db.md` runbook; `backend/tests/test_s4_evidence_drain_postgres.py`,
  `test_s4_evidence_drain.py`.
- Phase 3: `tools/s402b_fuel_cost_walkthrough.py`, `tools/s402b-fuel-cost-evidence.mjs`,
  `tools/s402b_power_cases.py` (docstring) — M1; `backend/tests/test_s4_evidence_drain_postgres.py` (L1/L2);
  `backend/README-db.md` (I1/I2); new `backend/conversions/s4-power-late-demo-cases-v1.json`,
  `tools/s402c_late_power_walkthrough.py`; `.agent/S4-02c-walkthrough-evidence.{md,json}`.

## Acceptance criteria

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Migration 0012 and constraints | Met (phase 1, reviewed) | `.agent/S4-02c-phase-1-review.md`; upgrade keeps 0011 rows; downgrade refuses on evidence work or `no_op_reason`, empty case restores 0011 |
| 2. Transactional enqueue | Met (phase 1, reviewed) | rollback atomicity, replay/duplicate/conflict/rejection, half-open edges (C3), Site B (C4), two-connection race, C1 coexistence; walkthrough: one row for the late ID and r1 |
| 3. Scoped drain | Met (phase 2, reviewed) | typed no-ops (superseded/role/asset/outside Candidate), FAILED locator refusals, no fallback, idempotent append; walkthrough Leg A same-revision n+1 |
| 4. Run plan and retry | Met (phase 2, reviewed; phase 3 carries) | Site claim, 1/2/4/8/16/16-minute schedule, injected clock, counts, runbook; L1 per-Site key and backlog-after-failure now asserted |
| 5. Reads and S5 gate | Met | `chain()` evidence match, `NO_WORK_RECORDED` typed only; walkthrough: STALE_QUEUED before drain, S5-eligible only for r2 CURRENT PRICED |
| Phase 3 walkthrough (two legs) | Met | `.agent/S4-02c-walkthrough-evidence.md`: 21/21 checks, exact IDs |
| C1-C4 | Met (phases 1-2) | phase 1/2 reviews |
| C5 exact IDs | Met | work, attempt, consequence, accepted IDs, examined digests and technical digests in the evidence |
| N2 price before Leg B | Met | price v1 `508b264a...` published first |
| N5 precondition asserted | Met | `[07:00, 07:05)` inside r1's observed Candidate `[06:05, 08:00)`; tool stops otherwise |
| N7 wrong-asset no-op | Met by tests, stated | evidence "Not shown by this fixture" |
| R2 bounded backlog | Measured (phase 2) | ~0.5-0.7 s per 48-mean chunk at 581 rows; drained in bounded runs |

## Phase 3 carries closed

- **M1 (merge gate):** the S4-02b walkthrough passes `--tenant demo`, loops bounded runs until the summary's
  backlog is 0, counts only lines with `work_id`; the evidence harness now claims the recompute exit status; the
  power-cases docstring is current. Proved end to end on private `assetops_s402bc3walk`/`assetops_s402bc3empty`
  from HEAD `c623b69b`: `prepare` (34 items, 0 failed, 31 appended, 12 replayed; P01 PRICED), `publish-v4` +
  `recompute` (1 appended, 11 replayed), `recompute --empty` (31 appended, P01 UNPRICED/NO_PRICE); then dropped.
  The `.mjs` browser harness itself was not run (no UI change; its only change is a claim on the exit status).
- **L1:** retry test asserts `failed 1, backlog 1` after the failing run; claim test asserts the held lock is
  `financial_consequence_runner:<site>` in `pg_locks` and that another Site's claim is not blocked. Non-vacuity:
  backlog mutation (`len(pending) - len(outcomes)`) and constant runner key each fail their test; restored by
  `git checkout`. Mutations 6/7 (redundant ACCEPTED term, tenant-only mismatch) left as the reviewer allowed.
- **L2:** R2 print label fixed. **I1/I2:** runbook now names repeated `skipped` ticks as the hung-runner alarm
  (no timeout added) and the permanent-failure retry volume (~90 attempts/day/row, no terminal state).

## Checks run (as observed)

- Focused: `test_s4_evidence_drain_postgres.py -k "retried or second_runner"` 2 passed (scratch
  `assetops_s402c3_focus_test`, dropped).
- Walkthrough: run 2 21 checks, 0 failed, exit 0 (`assetops_s402c3walk`, dropped).
- `tools/check-all.ps1`: All 9 guards passed (after the tool commits).
- Full backend (`assetops_s402c3_full_test`, at `b134984a`): **2090 passed** in 21:10 (exit 0).
- Frontend suites not run: no `frontend/` file changed; `tools/s402b-fuel-cost-evidence.mjs` is not covered by them.

## Known deviations

- **Walkthrough fixture sequence rule.** Run 1 appended the late mean after the epoch's last sequence; S3
  reported `SEQUENCE_ORDER_INVERTED`, and the revised Finding ended at 07:00 and did not count the late mean (one
  check failed). The variant now numbers every mean in source order (`sequence_rule: SOURCE_ORDER`, the late mean
  keeps sequence 14). This models a reading sequenced on time and uploaded late (not the project's own gateway numbering, see Residual risk); it
  does not change Leg A or N5 (both passed in run 1). Run 1 is recorded in the evidence. Reviewer: judge whether
  this is an acceptable authoring correction under the packet's "do not change the fixture to force the result".
- Reads pass `source_open=True` to the read service rather than running the file-backed Performance comparison.
- The superseded no-op branch did not arise in the walkthrough (evidence work drained before r2); proved in tests.
- Consequence 1 was appended by the price's ASSUMPTION_PUBLISHED work; r1's FRA work replayed it (same basis).
- Phase 2 deviations stand as reviewed (never-attempted work always due; skipped Site exits 0; test-written
  work rows for role/asset/outside-Candidate no-ops).

## Residual risk

- **R1:** S3 `process-jobs` and S4 `match-findings` remain one-shot and unscheduled; money after late evidence
  waits for them (Leg B ran them by hand). Architect may schedule them as a W1 follow-on.
- **Late-reading sequencing (from run 1, review F1):** the fixture models a reading *sequenced on time and uploaded late*. The project's own gateway assigns the next sequence on intake (`gateway/assetops_gateway/service.py:9-11`) and Lab-delayed readings get theirs on release, so the project's own late path is run 1's numbering. Measured: S3 INDETERMINATE (SEQUENCE_ORDER_INVERTED, GENERATOR_SERIES_AMBIGUOUS); revised Finding still SUPPORTED, episode shrunk to [06:05, 07:00), only limitation OPEN_BOUND; consequence CURRENT PRICED 7.5625 USD over 11 means, S5-eligible, versus 15.8125 USD in source order. Understated money arrives as current. Architect question (review Q1-Q3) before S5-01.
- **I1 (phase 2):** permanently failing rows accumulate attempts without a terminal state or alert (runbook).
- **I2:** a hung runner shows only as repeated `skipped`, exit 0 (runbook alarm, no timeout).
- **I3:** app/DB clock skew shifts retry timing only. **I4:** concurrent overlapping ingestion chunks under the
  Site enqueue lock remain unmeasured (phase 1 I1).
- Pre-0012 stale heads report `NO_WORK_RECORDED`; no backfill.

## Merge gate

Phases 1-3 must not merge or deploy before the independent review of this phase. M1 is closed on this branch.

## User-review focus

None required (flag false). If the owner looks: the evidence's Leg A/Leg B values, and the run-1 sequence finding.
