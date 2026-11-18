# S4-05b phase 1 review - registered producers and exact stored source provenance on reads

Reviewer: fresh independent Claude reviewer (did not author). Revision reviewed: `e147b06d`
(`task/S4-05b-producers-reads-walkthrough` phase-1 head), diff `7a647ce5..e147b06d`. Worktree
`AssetOpsV1-review5`, `assetops_backend.__file__` confirmed to resolve in this worktree.

## Verdict: ACCEPT

No High or Medium findings. Three Lows below; none blocks. Open Architect questions (the `Simulated data`
label versus the vocabulary scan, partly sealed Lab runs now refused, Actions still on
`demonstration_label.py`) are not re-raised.

## Focus answers

- **Register before upload, refusal stops the run.** `tools/s4_finding_cases.py:200-221` runs
  `python -m assetops_backend.publish_source` on the exact sealed body before the POST at `:240` and raises
  `SystemExit` on any non-zero exit. All authored upload sites pass `fixture=`: `s402b_power_cases.py:88`
  (power and authored context), `s402c_late_power_walkthrough.py:263,519`, `s402d_tick_walkthrough.py:245`.
  P02 walkthroughs read the late spec (`s402c...:113`), so they register as `assetops.s4-power-late-demo-cases`
  v1, not P01. The remaining unfixtured `post()` calls (`s4_finding_cases.py:371,376`) are the ordinary F-cases,
  which correctly stay unbound. Lab: `host/lab_execution.py:2827-2833` publishes after the COMPLETED and gateway
  checks and before `gateway.release`; `RegisteredRunPublisher` maps every `PublicationRefused` and every other
  exception to `SOURCE_PUBLICATION_REFUSED`. Only the run ID, the server-computed run identity digest and the
  gateway's sealed bytes reach the publication. No private simulator truth is in the public path.
- **Exact revision provenance.** Finding detail and Evidence pass the selected revision's own ID
  (`analytics/finding_read.py:447,559`). The consequence read resolves the selected row and every history row
  separately by its own consequence revision ID (`financials/consequence_read.py:222-226`), plus the
  FindingRevision block. Both money routes pass these through unchanged (`finding_api.py:270-276,306-311`).
- **Missing or failing resolver.** `evidence/provenance_read.py` returns `UNKNOWN` with
  `PROVENANCE_NOT_WIRED`, `PROVENANCE_UNREADABLE` (exception type in the detail) or
  `PROVENANCE_REVISION_NOT_FOUND`, and claims no IDs. The frontend maps a missing block to UNKNOWN.
- **MIXED names exactly the unpublished IDs.** This is asserted in
  `test_s405b_an_ordinary_contextual_id_makes_the_finding_and_union_mixed`: `problematic == plain` for both the
  finding block and the union, and the bound power IDs are excluded.
- **Rule 8.** No writer or migration is touched. The designation call lives in non-route
  `runs/registered_release.py` and uses the existing ledger writer. `check-architecture.ps1` passes.
- **Lab release refusal.** The refusal is raised before `gateway.release`, so nothing is released.
  Registration is per batch (`publication.register_run`, "a refusal stops the rest"), so earlier batches
  can keep a publication row without any admission. That is harmless: an identical retry returns the same ID.
  The host test proves that a refusing publisher leaves every batch `STAGED`.
- **Heuristic retired from the money routes.** `finding_api.py` no longer imports `demonstration_label`.
  It remains only in `site_overview/read.py` and `actions/service.py`, which are phase 2 or the open question.
- **Phase-2 leakage.** Nothing is half-gated. `presented_as_current` and money eligibility are unchanged, and
  no `MIXED_OR_UNKNOWN_SOURCE` code exists yet. On this branch, Finding Financials can show
  `Source not confirmed` beside a current amount, while the S5 Overview still shows the heuristic
  `Demonstration data` for the same P01/P02 day. That state is inconsistent but declared in the handoff, and
  it is acceptable only because the slice is held until phase 2 (see residual risk 1).

## Findings

1. **Low - an unreadable gateway Stage skips registration but still attempts the release.**
   `backend/assetops_backend/runs/registered_release.py:47-49` and `host/lab_execution.py:2829-2834`.
   When `gateway.stage()` hits `GatewayUnavailable`, it returns `unavailable_stage` with `batches=()`
   (`host/gateway_publication.py:246-247`). `publish()` then returns `()` and `gateway.release()` runs anyway.
   If the gateway answers the release call after missing the stage read, the run's batches upload without a
   publication. Registration after admission is refused, so the run is then permanently UNKNOWN rather than
   `REGISTERED_SIMULATION`. Reads stay fail-closed, but this breaks "registration failure stops upload".
   Fix: refuse (`SOURCE_PUBLICATION_REFUSED` or `GATEWAY_RELEASE_UNAVAILABLE`) when the Stage read is
   `GATEWAY_UNAVAILABLE`, or more generally when `stage.status` is not one the publisher can attest. Return
   `()` only when the Stage is readable and holds no `STAGED` batch.
2. **Low - an unrecognised source state crashes the notice instead of reading as unknown.**
   `frontend/src/sites/sourceProvenance.tsx:104-106,128-129`. `sourceState` returns `p.state` verbatim, so a
   state outside the four keys, such as the contract's future `ATTESTED_REAL_SOURCE`, makes
   `SOURCE_WORDS[state]` undefined and `words.label` throws. Fix: map any state outside `SOURCE_WORDS` to
   `UNKNOWN`. This is a fail-closed preference until the attested class exists.
3. **Low - acceptance gap deferred: no layout evidence and no end-to-end producer run.** The packet's phase-1
   review lists desktop and narrow app-versus-v6.9 layout evidence for Finding, Evidence and Financials. The
   handoff records it as not run, with the precondition "no populated walkthrough DB", which is an honest
   `not run`. The walkthrough producers were also not executed end to end. These are acceptable for phase 1
   only because phase 2's `s405_provenance_walkthrough.py` must produce both. The phase-2 review should treat
   their absence as blocking.

## Checks run (this reviewer, revision `e147b06d`)

- Focused backend, Postgres `assetops_s405brev_test` (private, dropped afterwards), `-n 2`:
  `test_s405b_registered_release`, `test_s4_assumption_read_api`, `test_s4_power_demo_case_postgres`,
  `test_s4_consequence_read`, `test_s4_finding_api`, `test_s4_finding_evidence_history_api`, `test_s405_resolver`,
  `test_s405_resolver_postgres`, `test_s405_publication_postgres`, `test_s4_finding_read_postgres`,
  `test_lr01_money_eligibility_postgres`. JUnit: tests=112, failures=0, errors=0, skipped=0, 140.5 s.
- `host/tests/test_registered_gateway_delivery.py`: 3 passed (real gateway process).
- Adjacent: `host/tests/test_lab_execution.py`, `backend/tests/test_s2_registered_commit_api.py`,
  `backend/tests/test_simulator_lab_gate.py`: 122 passed.
- Scratch probe, not committed: a real gateway `RegisteredStageView` after `run_to_end` fed through
  `simulation_records(run_attestation(run, stage))` produced 5 `REGISTERED_SIMULATION` records. The real sealed
  bytes therefore pass the structural attestation; only the fake-stage tests covered this before.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Frontend: **not run.** `frontend/node_modules` is absent in this worktree, so `npx.cmd tsc --noEmit` and
  `npm.cmd test` are unverified by this reviewer. The handoff's 1577 passes and clean tsc at `dbc5f07b` are not
  independently confirmed.
- No full suite (per dispatch). The implementer ran none either (phase-1 brief).

## Residual risk not already named

1. The branch must not merge at phase 1. Between the phases the Finding Financials and S5 Overview disagree on
   the source of the same Finding, and UNKNOWN or MIXED still sits beside a current amount.
2. The ledger-side check that the gateway is a registered `SIMULATED` gateway has been exercised only with the
   test Kit's gateway. No test runs host, real gateway, publisher, upload and resolver end to end against
   Postgres. Phase 2's walkthrough is the first place that full chain runs.
3. The consequence route resolves provenance once per history row: two queries each, plus the finding block,
   for up to 50 rows per page. This is acceptable for W1 but has no bound beyond the page limit.
