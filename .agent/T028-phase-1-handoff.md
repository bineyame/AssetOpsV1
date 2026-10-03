# T028 phase 1 handoff

Branch `task/T028-dispatch-finding-and-evidence`. Phase 1 (analytic,
declaration, Finding, revision history, Overview Dispatch card) is committed.
Task Status stays `active`; packet, CODE_STATE and ACTIVE_CONTEXT are phase 3's.

## What landed, per AC

Analytic `backend/assetops_backend/analytics/dispatch.py` (model `dispatch-1`,
`assess()` at :865). Decision table (required by "Deliver", also answers the
carried question): `backend/tests/dispatch_decision_table.md`.

| AC | Where | Proof |
| --- | --- | --- |
| 1 intervals, gaps bound duration | dispatch.py `_states`/`_runs`/`_off_before`/`_off_after` (~:220-303) | `test_a_gap_bounds_duration_instead_of_assuming_operation`; host `test_delayed_soc_record_is_placed_at_its_source_time` |
| 2 load/PV/SOC/capability/reserve/gen/policy at t | dispatch.py segment evaluation; `_Evidence.effective` :193 | `test_reserve_and_capability_shortfall_make_runtime_necessary` |
| 3 no observed PV, no simulator truth | decision table "Never used" | `test_observed_pv_output_never_stands_in...`; host `test_candidate_evidence_links_are_accepted_records_and_never_observed_pv` |
| 4 binding constraint / bounded candidate | segment table rows 1-5 | host `test_prolonged_runtime_is_a_bounded_candidate_with_its_constraints` |
| 5 indeterminate names evidence; no hidden weak portion | `portions_hours` per level | `test_insufficient_capability...`, `test_one_missing_portion_is_listed_beside_the_candidate`, `test_conflicting_records_are_used_by_nothing`; host `test_missing_pcs_capability_segments_the_claim_and_names_the_gap` |
| 6 coverage vs confidence basis | decision table "Coverage, confidence" | analytic unit tests; host prolonged test asserts `confidence.basis` |
| 7 override none-observed; records constrain | dispatch.py override lookup | `test_an_override_record_is_a_constraint...`, `test_a_reserve_override...`, `test_override_absence_is_none_observed_not_proof`; host `test_override_absence_is_a_stated_limitation_not_proof` |
| 8 alternatives with evidence links (data) | assessment `alternatives` | host degraded `test_a_stop_the_published_policy_cannot_explain_is_said_so`; on screen is phase 2 |
| 9 prolonged -> candidate via ingestion; healthy no Finding | host `World` commits through the real Commit route | host prolonged + `test_healthy_reference_raises_no_finding` |
| 10/11 bounded modelled fuel or unavailable+reason | decision table "Indicative fuel"; `service.fuel_basis` :43 | `test_hand_calculated_candidate_interval_and_fuel_bound`, `test_fuel_is_unavailable_with_its_reason` |
| 12 (card only) Overview links, never recomputes | `AssessmentService.card_assessments` service.py:257; injected into `evidence/overview.py` `CardAssessments` (evidence never imports analytics) | host `test_overview_dispatch_card_links_the_finding_not_a_recomputation`; frontend `overviewDispatchAssessment.test.tsx` |
| 13 idempotent rerun; persisted revisions | `AssessmentService._reconcile` service.py:145; `analytics/adapters/json_assessment_store.py` (`var/assessments`) | `test_the_same_records_give_the_same_payload`, `test_changed_evidence_appends_a_revision_and_keeps_the_prior` (reloads JSON store), `test_an_interval_no_longer_found_is_retired_not_deleted`; host `test_rerun_on_the_same_evidence_adds_no_revision`, `test_a_second_commit_that_fills_a_gap_revises_and_keeps_the_prior` (new this session) |
| 14 private data removed, same result | - | host `test_removing_private_artifacts_leaves_the_same_assessment` (Lab off, evidence copy only) |
| 16 declaration read model | `analytics/declaration.py` (`DECLARATIONS` :87, `site_declaration` :119); route `GET /api/sites/{id}/analytics` in `analytics_api.py` | `test_the_declaration_names_finding_type_evidence_and_claim_levels`, `test_the_analytics_routes_are_served_with_the_lab_gated_off` |
| 17 guard | `tools/checks/analytic-declaration.ps1`; dependency-direction (evidence may not import analytics); configuration-persistence (analytics persistence domain) | 8/8 mutation probes CAUGHT via `.agent/T028-guard-probes.py` (rerun this session) |
| 18 (card slot) rules 1-3 | `frontend/src/sites/presentationProfile.ts` `capabilityPresentation`/`servedCapabilities`/`orphanCapabilityIds`; profile `capabilities` in `presentationProfiles.json`; card in `SiteOverview.tsx` `DomainCard` | frontend `overviewDispatchAssessment.test.tsx` (rules 1, 2, 3); backend `tests/test_t028_presentation_profile.py` flags orphans (proved: adding `renewable` to the profile fails it; reverted) |

AC19 shape is already in place for phase 2: `EXPECTED_ORPHANS` in
`backend/tests/test_t028_presentation_profile.py` (empty; stale entries fail
too). Phase 2 adds Finding-type and Performance-subtab ids there if it puts
planned ids in the profile.

Read-model routes (all ungated, `analytics_api.py`): `/api/sites/{id}/analytics`,
`/dispatch`, `/findings`, `/assessments/{aid}`, `/assessments/{aid}/revisions`.
Assessment runs on ingestion completion (`IngestionService.add_completed_listener`,
`evidence/service.py`) and on read (`_active` calls `assess_site`; writes only
when changed).

## Carried stop-60 question (needs owner answer, no change made)

Answered in `dispatch_decision_table.md` "Carried question". The analytic does
not need a stop-threshold record to classify; the stop threshold is context for
the policy alternative only, and when an observed stop happens below the
published (Foundation 90 %) threshold with no override record, the alternative
says the published policy does not explain the stop. **Owner question:** should
stop-60's change surface as a POLICY record (version, effective interval,
source) under publication profile 5? Under
`D-2026-10-02-scenario-states-override-issuer` it is a configuration fact with
no issuer, and publishing it needs a scenario or publication change (the record
source is the Foundation today), which T028 may not make.

## Generator-runtime carry (backlog "Generator running time is whole-interval")

Handled for the Finding: the analytic does not reuse the Overview's
whole-interval runtime; it reconstructs intervals from status transitions and
treats an output mean > 0 as running somewhere inside its span (decision table,
"Interval reconstruction"), with lower/upper bounds. The T027 Overview metric
"Generator running time, measured intervals" (`evidence/overview.py`) is
unchanged and still whole-interval; the backlog entry stays open for that
metric. Risk: the Dispatch card now shows that metric beside an assessment whose
duration bound comes from a different basis; the two numbers can differ.

## Open risks / notes for phase 2

- Necessary intervals are assessments without Findings (decision table, open
  for owner review). Findings index will list Candidate and Indeterminate only.
- Ingestion keeps the first accepted record at a (device, signal, time) and
  holds later distinct ones as conflicts outside `load_site().records`. So a
  second overlapping run of the same recipe does NOT revise an interval; only
  records at new keys do. Found while building the revision proof.
- Card lead selection: Candidate > Indeterminate > Necessary among active
  intervals overlapping the Overview window (`card_assessments`).
- Untracked `Docs/*` files in the tree are not this slice's; left alone.
- Frontend `capabilities` profile entries are presentation only; the
  T027 profile-shape test was relaxed to allow the key
  (`backend/tests/test_t027_overview.py` `test_the_profile_owns_no_card_state`).

## Checks run this session

- backend: `test_t028_presentation_profile.py`, `test_t027_overview.py`,
  `test_t028_dispatch_analytic.py`: 39 passed.
- host: `test_t028_dispatch_finding.py`: 11 passed.
- frontend: `overviewDispatchAssessment.test.tsx` + `src/sites`: 293 passed;
  `tsc --noEmit` exit 0.
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed;
  guard probes 8/8 CAUGHT, restored tree passes.
- Not run (phase 3): full suites, production build, layout evidence.

## Owner UI check (phase 1)

Use fresh Kobo Sites so earlier T027 evidence on KOBO-001/SITET26 does not
overlap (ingestion keeps the first record at a key). Create three Sites from
template `kobo-mini-grid-60kw` (e.g. KOBO-P, KOBO-H, KOBO-R).

1. Backend with the Lab: from `host/`,
   `..\.venv\Scripts\python.exe -m uvicorn lab_app:app --reload` (port 8000).
   Frontend: from `frontend/`, `npm.cmd run dev`.
2. Prolonged: in the Lab, Draft `kobo-mini-grid-prolonged` on KOBO-P,
   2026-09-22 03:00-11:00 UTC, 5-min step, model profile mini-grid v3,
   publication profile 5; run to end; Commit. Open Sites > KOBO-P > Overview
   (default window = the accepted evidence): the Dispatch card reads "Dispatch assessment:
   Candidate avoidable" with a one-line reason; Service, Battery, Fuel,
   Renewable read "No assessment yet".
3. Healthy: same on KOBO-H with `kobo-mini-grid-evening`, 09:00-17:00. The
   Dispatch card must NOT read Candidate avoidable (expected Necessary).
4. Declaration: `http://127.0.0.1:8000/api/sites/KOBO-P/analytics` shows id
   `dispatch`, site types, Finding type, required/optional evidence, claim
   levels Necessary / Candidate avoidable / Indeterminate.
5. Revisions: on KOBO-R commit `kobo-mini-grid-degraded-evidence`
   (03:00-11:00), note the assessment id from
   `http://127.0.0.1:8000/api/sites/KOBO-R/dispatch`; then commit
   `kobo-mini-grid-prolonged` over the same window on KOBO-R. Open
   `http://127.0.0.1:8000/api/sites/KOBO-R/assessments/<id>/revisions`:
   revisions 2 and 1 are listed, revision 1 unchanged (fewer evidence
   records, different digest). Restart the backend and reload: both remain.
6. Optional: restart with `simulator_lab.enabled` false
   (`..\.venv\Scripts\python.exe -m uvicorn assetops_backend.main:app` from
   `backend/`); the card and routes answer the same.

Phase 2 next: screens (Performance > Dispatch, Finding detail
`Overview | Evidence | Alternatives`, drawer reuse, Findings rail root, Site >
Findings), ACs 8, 12, 15, 21 on screen, 18/19 for subtabs and Finding types,
layout evidence including a one-item rail group.
