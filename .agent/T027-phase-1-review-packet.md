# T027 phase 1 review packet - Commit, ingestion and Site > Evidence

## Task

`tasks/T027-commit-ingestion-and-site-overview.md`, phase 1 (ACs 1-9, 12, 16-18,
20, 21, 23 in full; 10, 13, 14, 15, 19 for evidence and Site > Evidence).
Branch `task/T027-commit-ingestion-and-site-overview`. Plan
`.agent/T027-implementer-plan.md`. USER_REVIEW_REQUIRED: true. The task puts the
packet in phase 2; this phase-1 packet was asked for so the phase-1 owner check
has evidence to read.

## Outcome delivered

A completed, release-eligible Lab stage is sealed once into an immutable Commit
artifact and released as an ordinary ingestion batch through the one product
ingest path. Ingestion assigns `received_at`, keeps accepted records, rejections,
duplicates and conflicts durably, resumes an interrupted release, and serves a
Site evidence read model built from accepted content only. Operators get Site >
Evidence (source health, per-signal coverage of needed signals, accepted
mapping/configuration basis, rejections, and a record inspector with three
timestamps). The Lab run screen shows Commit and release as separate facts with
an Open in AssetOps link to Site > Evidence. Site tabs render per capability
(Overview | Foundation | Evidence; Foundation Definition | Topology | Controls);
`/` redirects to `/sites` and the rail shows Sites only.

## Files materially changed

- Contracts: `contracts/assetops_contracts/committed_artifact.py`,
  `ingestion_batch.py`, `source_stage.py`.
- Backend: `backend/assetops_backend/evidence/` (models, ports, service,
  read_model, composition, `adapters/json_evidence_store.py` -> `var/evidence`),
  `evidence_api.py`, `main.py`, `runs/commit_ports.py`, `runs/composition.py`,
  `runs/adapters/json_commit_store.py` (`var/commits`), `simulator_lab_api.py`
  (`RUN_COMMIT_ROUTE`).
- Host: no product code; proofs in `host/tests/test_t027_commit_ingestion.py`.
- Frontend: `sites/SiteEvidence.tsx`, `sites/siteEvidenceClient.ts`,
  `shell/SiteEvidenceFrame.tsx`, `shell/RunCommitPanel.tsx`, `shell/RunFrame.tsx`,
  `shell/RunSetupFrame.tsx`, `shell/operatorSiteTabs.tsx`,
  `shell/operatorSiteRoutes.ts`, `sites/FoundationSubtabs.tsx` (Readiness
  removed), `shell/OperatorShellLayout.tsx`, `shell/OperatorShellFrame.tsx`,
  `App.tsx` (`/` redirect), `ui/primitives.css` (dead tab-label styles removed;
  `.identity-heading`).
- Checks: `tools/checks/navigation-truthfulness.ps1`, `dependency-direction.ps1`
  (evidence rule), `configuration-persistence.ps1` (evidence and commit domains),
  `tools/layout-evidence.mjs` (T027 section; stale tab and run-control claims
  brought to the rendered-tab rule and the Commit control).

## Acceptance criteria (phase 1)

| AC | Status | Evidence |
| --- | --- | --- |
| 1 seal once, manifest, ineligible refused | met | ingestion::test_seal_round_trips_and_names_each_envelope, ::test_an_envelope_the_mapping_refuses_cannot_be_sealed; commit_api::test_commit_seals_once_releases_and_reports_commit_and_release_separately, ::test_an_ineligible_stage_is_refused_with_its_blockers_and_nothing_is_written |
| 2 immutable; resume, not edit | met | commit_api::test_a_filed_artifact_is_never_rewritten_and_a_changed_stage_is_refused, ::test_an_interrupted_release_reports_progress_and_a_retry_resumes, ::test_a_tampered_artifact_is_answered_as_unreadable |
| 3 strict schema, resolved mapping/config, inspectable rejection | met | ingestion::test_bad_siblings_are_rejected_and_valid_ones_accepted, ::test_an_unregistered_older_version_is_unresolved, ::test_a_source_mode_the_site_does_not_have_is_refused |
| 4 one path; SIMULATED provenance kept | met | ingestion::test_simulated_and_live_batches_cross_the_same_ingest, ::test_the_artifact_is_released_only_as_an_ordinary_batch |
| 5 received_at by ingestion; three timestamps | met | ingestion::test_received_at_is_ingestions_and_distinct_from_both_source_times; host::test_delayed_publication_shows_three_distinct_timestamps; layout: source 11:00:00Z, published 11:00:03Z, received 2026-10-02T21:11:33Z |
| 6 idempotent duplicate; conflict keeps original | met | ingestion::test_a_duplicate_after_restart_is_idempotent, ::test_same_id_other_content_is_a_conflict_and_the_original_stays, ::test_a_reused_batch_id_with_other_content_is_refused; host::test_duplicate_release_after_restart_counts_nothing_twice |
| 7 survives reload; interrupted batch honest | met | ingestion::test_an_interrupted_batch_resumes_without_duplicates; commit_api interrupted-release test; runCommitPanel "shows an interrupted release with how far it got..." |
| 8 read models accepted content only | met | ingestion::test_coverage_reads_accepted_content_only; host::test_stage_without_commit_changes_no_accepted_history |
| 9 overlap at identity/time grain | met | ingestion::test_distinct_ids_at_the_same_signal_and_time_are_both_kept |
| 10 missingness, needed-signal coverage (evidence part) | met for Evidence | ingestion::test_coverage_names_needed_signals_and_never_fills_a_gap; siteEvidenceScreen "names a signal no record reported as a coverage gap with no value"; layout: 17 coverage rows, 1 NOT_REPORTED, 1 gap. Overview cards: phase 2 |
| 11 Site Overview | phase 2 | - |
| 12 inspector fields, opens from rows, root unchanged | met for Evidence | siteEvidenceScreen "opens from a signal row and shows the record with three distinct timestamps", "opens from a source row...", "reopens a deep-linked record from the address alone"; layout inspector at 1280 and 640. Overview links: phase 2 |
| 13 gate off: Evidence stays, Lab goes | met for Evidence | commit_api::test_gate_closed_has_no_commit_routes_and_still_serves_accepted_evidence, ::test_a_closed_build_never_builds_the_commit_store; host::test_gate_closed_serves_the_same_accepted_evidence_and_no_lab; siteEvidenceScreen "stays available with the Simulator Lab gate open or closed"; HTTP check below |
| 14 rebuild in empty store matches | met for Evidence | ingestion::test_rebuild_from_artifact_texts_matches_the_original; host::test_rebuild_from_committed_artifact_text_alone_matches |
| 15 rebuild without simulator/runtime | partial | same host test rebuilds from artifact text only in a gate-closed `create_app`; does not prove host/simulator absent from `sys.path` (deviation 1) |
| 16 private payloads refused; dependency guards | met | ingestion::test_a_private_object_key_refuses_the_batch_whole, ::test_an_envelope_given_as_an_object_refuses_the_batch, ::test_a_private_payload_is_refused_whole_over_http; new evidence dependency rule proven failing (`evidence/service.py` importing `runs.models`) and non-vacuous |
| 17 historic basis unchanged by Foundation edit | met | ingestion::test_a_foundation_edit_leaves_accepted_basis_unchanged; host::test_changing_the_current_foundation_leaves_the_accepted_basis; siteEvidenceScreen basis test |
| 18 Commit vs acceptance separate; Open in AssetOps | met | commit_api::test_partial_rejection_is_reported_and_open_in_assetops_uses_the_accepted_window; host::test_partial_rejection_then_open_in_assetops_shows_actual_coverage; runCommitPanel "commits an eligible stage and shows Commit and release as two facts...", "never says every record was accepted..."; layout: link clicked, landed on `/sites/SITET26/evidence`, populated |
| 19 gate off: Lab routes/payloads gone; accepted evidence feeds views | met for Evidence | ingestion::test_evidence_routes_are_served_and_lab_routes_are_not; gate-closed tests above |
| 20 Evidence sections; nothing about capability/claims | met | siteEvidenceScreen populated block (5 tests) incl. "says nothing about capability readiness or claim ceilings"; layout 4 sections at 3 widths |
| 21 rendered tabs per capability | met | operatorSiteTabs.test.tsx, foundationScreen.test.tsx, overflowContainment.test.tsx; navigation-truthfulness rules proven with four mutations (1a); layout: Overview\|Foundation\|Evidence and Definition\|Topology\|Controls |
| 22 presentation profile | phase 2 | needed-signal substrate keyed by `site_type` MINIGRID exists for coverage only |
| 23 rail Sites only; `/` -> `/sites` | met | OperatorShellFrame.test.tsx, operatorRouteFrames, sitesIndexRoute, siteDetailRoute, siteFoundationRoute, simulatorLabWorkspaceEntryPoint; layout "/ lands on the Sites index" |

**AC18 lands on Site > Evidence in both phases.** The link's job is to show the
actual release and acceptance outcome for the committed window. Evidence is the
surface that states it record for record (source health per batch, coverage per
signal, rejections), so a partial rejection is visible where the link lands.
Overview (phase 2) summarises and cites evidence; landing there would put a
summary between the operator and the outcome AC18 says must not be overstated.

## Proof table

| Case | Test |
| --- | --- |
| Stage without Commit | host::test_stage_without_commit_changes_no_accepted_history |
| Valid Commit | host::test_commit_accepts_evidence_for_the_selected_site_window |
| Bad mapping or unit | ingestion::test_bad_siblings_are_rejected_and_valid_ones_accepted; host partial-rejection test (kWh on active-power) |
| Duplicate release after restart | host::test_duplicate_release_after_restart_counts_nothing_twice |
| Same id, changed content | ingestion::test_same_id_other_content_is_a_conflict_and_the_original_stays |
| Delayed publication | host::test_delayed_publication_shows_three_distinct_timestamps |
| Missing capability/report | ingestion::test_coverage_names_needed_signals_and_never_fills_a_gap; layout 1 NOT_REPORTED row |
| Disable Lab | host::test_gate_closed_serves_the_same_accepted_evidence_and_no_lab |
| Remove private artifacts and rebuild | host::test_rebuild_from_committed_artifact_text_alone_matches |
| Change current configuration | host::test_changing_the_current_foundation_leaves_the_accepted_basis |
| Partial rejection; Open in AssetOps | host::test_partial_rejection_then_open_in_assetops_shows_actual_coverage |

## Checks run (final tree, d26d6e2 + records)

- backend `pytest -q`: 1412 passed. host: 602 passed. simulator: 244 passed.
- frontend typecheck: clean. `npm test`: 42 files, 1055 tests passed. build: ok.
- `check-architecture.ps1`: "Architecture check passed." `check-agent-workflow.ps1`:
  "Agent workflow check passed." `navigation-truthfulness.ps1` alone prints
  nothing (a module; check-architecture runs it).

## Layout evidence

`ASSETOPS_LAYOUT_SITE=MG-006 ASSETOPS_KOBO_SITE=SITET26 node tools/layout-evidence.mjs http://localhost:4173`
(production build via `vite preview`; `host/lab_app:app` on 8000 from an isolated
`git archive HEAD` copy whose `var/` copies sites (valid_from backdated in the
copy only), scenarios and `.demo/T025c` runs - T026's method). Output:
`.agent/T027-phase-1-layout-evidence.txt`; 485 PASS, final line
`AT LEAST ONE CLAIM FAILED`. Every T027 claim passes: Commit panel COMMITTED with
a release; link clicked lands on populated Evidence; populated at 1280/1000/640
(1 source, 1 batch, 17 coverage rows, both tables overflow and scroll in their
regions, page never scrolls horizontally); inspector 33 records and three
timestamps at 1280 and 640; MG-006 empty at 1280 and 640 (8 needed signals, all
NOT_REPORTED). Failing, not T027: three "blocked table" claims (MG-006 setup is
READY, as in T026) and the T025e 50 ms p95 delta budget (97.2 ms; an A/B of the
same read gave p95 231-244 ms on this branch and 733-738 ms on main's code).
The layout run found a real defect, fixed in 5c19e90: the record heading's
64-character digest widened the page at 640 (844 vs 625).
Gate closed (product `assetops_backend.main:app`, copy with the gate off, HTTP):
`/api/sites/SITET26/evidence` 200 populated, MG-006 200 empty,
`/api/simulator-lab/runs` 404, POST commit 404. No browser gate-closed pass.

## Known deviations

1. AC15: the rebuild runs in-process; host/simulator are not proven absent from
   `sys.path`.
2. The profile-5 run stages no fuel-level-sensor envelopes, so Fuel coverage
   reads NOT_REPORTED (the layout run's one gap). Phase 2's Fuel card will show
   a coverage gap unless the profile publishes it.
3. `?batch=` only highlights the source-health batch; it does not filter.
4. Ingestion store: one JSON document per Site rewritten per 64-record chunk;
   single-process lock only (scope limit: simple and correct).
5. Before the isolated run, two dev-server layout runs against the working
   checkout added Drafts/executions under `var/runs`/`var/executions`
   (additive; `var/sites` untouched, no commit or evidence written there).
6. An unknown-Site batch is refused and not stored (no rejection record).

## Residual risk

Evidence store does not scale past a few Sites' worth of records; the T025e delta
budget miss is carried from T026; navigation-truthfulness has no Pester tests
(proven by mutation only).

## User-review focus

Phase-1 UI check: Lab run (Kobo v3 Site, `kobo-mini-grid-degraded-evidence`) ->
Run to the end -> Commit and release -> Open in AssetOps -> Site > Evidence:
source health, coverage (one gap), basis, rejections, then a coverage row's
record with source, published and received times. Then Lab off: Evidence stays.
