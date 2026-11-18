# S4-05b phase 1 handoff - producers register before upload; exact provenance on the reads

Branch `task/S4-05b-producers-reads-walkthrough` (worktree `AssetOpsV1-review2`), from main `7576ef9d`.
Commits: `7b7b020c` (reads + frontend), `5c49ee7d` (producers), `dbc5f07b` (tests), then mutation-proof and
handoff commits. No migration added (none needed); nothing merged.

## What landed

- Read block: `backend/assetops_backend/evidence/provenance_read.py` (`finding_provenance`,
  `consequence_provenance`, `unresolved`). Fail closed: resolver not composed / raising / revision not found ->
  `UNKNOWN` with `PROVENANCE_NOT_WIRED | PROVENANCE_UNREADABLE | PROVENANCE_REVISION_NOT_FOUND`, no IDs.
- Finding detail and Evidence: `FindingReadService(store, dispatch, provenance=None)` adds top-level
  `source_provenance` (selected revision's own cited set) - `analytics/finding_read.py` (`source_provenance`
  method; both returns). Composed in `analytics/composition.py:build_finding_read_service`.
- Consequence read: `ConsequenceReadService(..., provenance=None)` adds `source_provenance =
  {finding_revision, consequence_revision}` and per-row `source_provenance` on the selected consequence and every
  history row (`financials/consequence_read.py` read()). Composed in `financials/composition.py`.
- Money routes (`finding_api.py`): `demonstration` key and the `demonstration_label` import are gone. The
  consequences route passes the service's `source_provenance`; Financials returns
  `source_provenance = {finding_revision: <finding read block>, consequence_revision: <bridged head block>}`;
  `bridge()` now returns the raw read and `bridge_consequence(result)` is applied in the route.
- NOT gated yet (phase 2): MIXED/UNKNOWN does not yet withhold the current amount; no
  `MIXED_OR_UNKNOWN_SOURCE` reason. `demonstration_label.py` still used by `site_overview/read.py` and
  `actions/service.py` (S5/Action reads; phase 2 cutover for S5, Actions not named in the packet).
- Producers: `tools/s4_finding_cases.py` `Cases.publish_authored` + `post(..., fixture=)` runs
  `python -m assetops_backend.publish_source` per exact sealed batch before the upload; non-zero exit -> SystemExit,
  nothing uploaded. `PowerCases.authored_fixture()` (spec `schema.id/version`) used by `s402b_power_cases.py`
  (power + authored context batches), `s402c_late_power_walkthrough.py` (both late posts) and
  `s402d_tick_walkthrough.py` (late post). Run artifact records `publications` per case.
  `s402b_fuel_cost_walkthrough.py prepare` refuses a template without `batch_publication_link` rows.
- Lab release: `runs/registered_release.py` `RegisteredRunPublisher.publish(run, stage)` registers every
  still-`STAGED` batch via `run_attestation` + `register_run`; already-released batches are skipped (idempotent
  re-release); any refusal/ledger failure -> `LabControlRefused("SOURCE_PUBLICATION_REFUSED")` (new kind +
  statement in `contracts/assetops_contracts/lab_projection.py`). `host/lab_execution.py`
  `HostLabExecution(..., source_publisher=None)` calls it inside `release_registered` after the COMPLETED and
  gateway checks, before `gateway.release`. `host/lab_app.py` always composes `publisher_for(database_url())`
  (no DB -> every release refused). Gateway seal path (`gateway/service.py`) unchanged: the gateway's own sealed
  bytes are what get attested; live (READY-at-admission) gateway batches are never published -> UNKNOWN.
- Frontend: `frontend/src/sites/sourceProvenance.tsx` (types, `SOURCE_WORDS`, `reasonWords`,
  `SourceProvenanceNotice`, `data-source-provenance`, `data-source-reason`, IDs in a closed disclosure).
  Used in `FindingConsequence.tsx` (bridge: consequence block, else finding block), `SiteFinding.tsx` lead,
  `SiteFindingEvidence.tsx` Selection panel. `financialsClient.ts` / `findingClient.ts` types updated;
  `DemonstrationLabel` removed.

## Tests (phase 1)

- `backend/tests/test_s4_power_demo_case_postgres.py` +5: fresh P01 (every cited and power ID linked, AUTHORED,
  per-ID publication), one unbound context device -> Finding and union MIXED (`BOUND_AND_UNBOUND`, exact plain IDs),
  same-day unpublished P01 (old producer/host) -> UNKNOWN, fresh P02 on-time -> ELIGIBLE 15.8125 with AUTHORED
  union incl. the late ID, ordinary run through the composed Lab publisher -> REGISTERED_SIMULATION, plus a
  same-day unbound batch -> MIXED.
- `backend/tests/test_s405b_registered_release.py` (5), `host/tests/test_registered_gateway_delivery.py` +1
  (refusing publisher releases nothing; accepting one sees exactly the STAGED batches).
- `backend/tests/test_s4_assumption_read_api.py`: heuristic class replaced by same-day non-authorship tests.
- Frontend: `sourceProvenance.test.tsx` (3), `siteFinancials`, `siteFinding`, `siteFindingEvidence` updated.

## Next (phase 2)

Money gating (`MIXED_OR_UNKNOWN_SOURCE` beside every other typed gate in `bridge_consequence`, consequence
`presented_as_current`, S5 Overview) composed at `financials/money_eligibility.py` / `finding_api.py` bridge;
S5 cutover off `demonstration_label` (+ `tests/test_s5_overview_*` and `tools/s5_overview_walkthrough.py` which
still read `demonstration`); `tools/s402b-fuel-cost-evidence.mjs` still selects `data-financials-demonstration`
(now `data-source-provenance`); install gate; `tools/s405_provenance_walkthrough.py`; layout evidence; full suite.

## Open risks

- Vocabulary: the mandated label `Simulated data` contains the T028 banned term `simulated`; any vocabulary
  scan of a page in REGISTERED_SIMULATION state will flag it. Needs Architect/owner ruling (exempt or reword).
- A partially sealed registered run (`SEALING_REFUSED`/`SEALING_PENDING`) can no longer be released at all:
  `simulation_records` refuses a non-STAGED stage, so Commit returns `SOURCE_PUBLICATION_REFUSED`. Previously it
  released "as far as sealed".
- Layout evidence not run in phase 1 (no populated walkthrough DB; phase 2's walkthrough provides it).
- Walkthrough producers not executed end to end in phase 1 (memory limit); exercised via the same CLI in tests
  only indirectly (`publish_source` CLI itself is S4-05a-tested).

## Checks run (revision `dbc5f07b`)

- Focused backend/host (Postgres `assetops_s405b_test`, `-n 2`): 20 files, JUnit tests=324 failures=0 errors=0
  skipped=0, 267.7 s.
- Frontend: `npx.cmd tsc --noEmit` clean; `npm.cmd test` 67 files / 1577 tests passed.
- `tools/check-architecture.ps1` and `tools/check-agent-workflow.ps1` passed at `dbc5f07b`.
- Mutations (each failed its test, reverted with `git checkout --`): backend `unresolved()` state ->
  AUTHORED (`test_s4_assumption_read_api -k unwired` 1 failed); `RegisteredRunPublisher` swallowing a refusal
  (`test_s405b_registered_release` 2 failed); frontend `sourceState` default -> AUTHORED
  (`sourceProvenance.test.tsx` 1 failed).
- Rule-8 writer impact: no writer touched (`postgres_evidence_ledger.py` unchanged); `writer_guard_probes.py`
  not applicable. No full suite in phase 1 (brief).
