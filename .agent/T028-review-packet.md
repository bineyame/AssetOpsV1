# T028 review packet - First dispatch Finding with challengeable evidence

Branch `task/T028-dispatch-finding-and-evidence` (26 commits over `main`, 69
files, +8.4k/-0.1k). Task `tasks/T028-dispatch-finding-and-evidence.md`,
Status `in_review`. **USER_REVIEW_REQUIRED: yes** (owner UI walk below; two
open owner decisions). Phase handoffs hold the detail:
`.agent/T028-phase-1-handoff.md`, `-2-`, `-3a-`.

## Outcome delivered

A dispatch analytic (`dispatch-1`) reconstructs generator intervals from
accepted evidence and classifies each Necessary / Candidate avoidable /
Indeterminate, with segments, named gaps, confidence and coverage kept
separate, alternatives with evidence links, and a bounded modelled fuel
quantity. Assessments persist with revision history. Screens: Performance >
Dispatch, Finding detail (`Overview | Evidence | Alternatives`) with the
claim drawer, Findings rail root, Site > Findings, the Overview Dispatch card
linking the Finding, and a Site > Evidence capability-readiness table. The
backend serves the evaluated declaration; the frontend presentation profile
only labels/orders (3 rules, tested). A `tools/checks` guard enforces the
declaration.

## Files materially changed

Backend `analytics/` (dispatch.py, declaration.py, service.py, models.py,
ports.py, adapters/json_assessment_store.py, composition.py),
`analytics_api.py`, `evidence/overview.py` + `service.py` (listener), `main.py`;
decision table `backend/tests/dispatch_decision_table.md`. Frontend
`sites/` (SitePerformance, FindingDetail, FindingsIndexes, CapabilityReadiness,
findingPresentation, presentationProfile(.json), siteAnalyticsClient,
SiteOverview, SiteEvidence), `shell/` (routes, tabs, frames), `ui/NavRail.tsx`
(grouped rail). Tools: `tools/checks/analytic-declaration.ps1` (new),
`navigation-truthfulness.ps1`, `configuration-persistence.ps1`,
`dependency-direction` in `check-architecture.ps1`, `tools/layout-evidence.mjs`.

## Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| 1 intervals; gaps bound duration | met | dispatch.py `_states`/`_runs`; `test_a_gap_bounds_duration_instead_of_assuming_operation`; host `test_delayed_soc_record_is_placed_at_its_source_time` |
| 2 load/PV/SOC/reserve/generator/policy at time | met | `test_reserve_and_capability_shortfall_make_runtime_necessary`; decision table segment rows |
| 3 no observed-PV stand-in, no simulator truth | met | `test_observed_pv_output_never_stands_in...`; host `test_candidate_evidence_links_are_accepted_records_and_never_observed_pv` |
| 4 Necessary has binding constraint; Candidate bounded | met | host `test_prolonged_runtime_is_a_bounded_candidate_with_its_constraints` |
| 5 Indeterminate names evidence; no hidden weak portion | met | `test_insufficient_capability...`, `test_one_missing_portion_is_listed_beside_the_candidate`, `test_conflicting_records_are_used_by_nothing`; host missing-PCS test |
| 6 coverage vs confidence basis | met | decision table "Coverage, confidence"; host prolonged asserts `confidence.basis` |
| 7 override none-observed; records constrain | met | `test_an_override_record_is_a_constraint...`, `test_override_absence_is_none_observed_not_proof`; host override-absence test |
| 8 alternatives with evidence links | met | host degraded stop-policy test; `t028Screens.test.tsx` Alternatives tab |
| 9 prolonged via ingestion; healthy no Finding | met | host `World` through the real Commit route; `test_healthy_reference_raises_no_finding` |
| 10 bounded fuel or unavailable+reason | met | `test_hand_calculated_candidate_interval_and_fuel_bound`, `test_fuel_is_unavailable_with_its_reason` |
| 11 basis modelled; no loss/saving implied | met | decision table "Indicative fuel"; Finding Overview shows technical quantity only (no money) |
| 12 Finding and Dispatch same object; Overview links | met | `t028Screens.test.tsx` AC12; `overviewDispatchAssessment.test.tsx`; host `test_overview_dispatch_card_links_the_finding_not_a_recomputation`, `test_the_global_findings_index_lists_the_same_finding_with_its_site` |
| 13 idempotent rerun; persisted revisions | met | `test_the_same_records_give_the_same_payload`, `test_changed_evidence_appends_a_revision_and_keeps_the_prior` (reloads store); host rerun/second-commit tests |
| 14 private data removed, same result | met | host `test_removing_private_artifacts_leaves_the_same_assessment` |
| 15 screen path without Lab | met | Finding detail six-part hierarchy test; routes served with Lab gated off (`test_the_analytics_routes_are_served_with_the_lab_gated_off`) |
| 16 declaration read model | met | `analytics/declaration.py`; `GET /api/sites/{id}/analytics`; declaration test |
| 17 guard | met | `tools/checks/analytic-declaration.ps1`; 8/8 mutation probes CAUGHT (`.agent/T028-guard-probes.py`); readiness probe CAUGHT |
| 18 profile rules 1-3 (subtabs, card slot, Evidence rows, Finding types) | met | `overviewDispatchAssessment.test.tsx`, `t028Screens.test.tsx`, `t028EvidenceCapability.test.tsx` (rule 3 probe CAUGHT) |
| 19 expected-orphan list | met | `EXPECTED_ORPHANS`, `EXPECTED_ORPHAN_FINDING_TYPES` in `backend/tests/test_t028_presentation_profile.py`; adding `renewable`/`fuel-residual` fails, proved |
| 20 Evidence capability table above source health | met, with two owner questions | backend `score_readiness` (declaration.py), `CapabilityReadiness.tsx`; backend 23 + host 14 + frontend 8 tests; layout claims (below). Open decisions 1 and 2 |
| 21 navigation | met | `t028Screens.test.tsx`; Performance one subtab, Finding 3 tabs, drawer path/root unchanged, rail group headers; `navigation-truthfulness.ps1` rail rule (3 probes CAUGHT) |

## Proof table

| Evidence case | Result | Where |
| --- | --- | --- |
| Healthy supported-demand | Necessary, no false candidate, no Finding | host `test_healthy_reference_raises_no_finding` |
| Prolonged, adequate capability | Candidate Avoidable with reasons | host prolonged test |
| PCS capability missing in part | segmented/limited claim + named gap | host `test_missing_pcs_capability_segments_the_claim_and_names_the_gap` |
| Insufficient capability throughout | Indeterminate | `test_insufficient_capability...` |
| Time-valid reserve blocks battery support | Necessary, limit explained | `test_reserve_and_capability_shortfall_make_runtime_necessary`, `test_a_reserve_override...` |
| Override present | constraint included | `test_an_override_record_is_a_constraint...` |
| Override absent | limitation explicit | `test_override_absence_is_none_observed_not_proof`; host |
| Delayed/out-of-order | source-time reconstruction | host `test_delayed_soc_record_is_placed_at_its_source_time` |
| Private simulator data removed | same assessment | host `test_removing_private_artifacts...` |
| Hand-calculated fuel | matching range and basis | `test_hand_calculated_candidate_interval_and_fuel_bound` |
| Changed accepted evidence | new revision, prior retained | `test_changed_evidence_appends_a_revision_and_keeps_the_prior`; host `test_a_second_commit_that_fills_a_gap_revises_and_keeps_the_prior` |
| Profile drift | default render; orphan flagged | rule 1/2 frontend tests; backend orphan tests |

## Checks run (HEAD at closeout; code unchanged since phase 3 build)

- backend `pytest`: **1465 passed** (T027 merge: 1435).
- host `pytest`: **616 passed** (602).
- simulator `pytest` from `simulator/`: **244 passed** (244).
- frontend `vitest run`: **46 files, 1097 passed** (1071); `tsc --noEmit` exit 0;
  `npm.cmd run build` built (only the existing chunk-size warning).
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed.
- Layout evidence, isolated copy (`git archive HEAD`, copy `var/` sites with
  `valid_from` backdated + scenarios + T025c runs/stages, PYTHONPATH on the
  copy, `vite preview` 4173, `host/lab_app:app` 8000), SITET26/MG-006:
  `.agent/T028-layout-evidence.txt` **560 PASS, 5 FAIL**, run completed.
  Failures: the 3 known "blocked table" (MG-006 READY), the known T025e p95
  budget (179 ms vs 50 ms), and **one not on the known list**: T025b
  "profile 4 discloses the status as observed and not staged" (`unstaged none;
  status true value RUNNING`), a Lab run-detail claim. T028 touches no Lab run
  or stage code; T027 phase 2 saw the same claim fail once and not repeat. Not
  re-run to confirm; reviewer may treat as pre-existing flake or re-run.
  T028 claims all pass: updated T027 "No assessment yet" claim (Service,
  Battery, Fuel, Renewable; Dispatch assessed; 3 widths), grouped rail,
  Performance > Dispatch (table populated), Finding detail/Evidence/drawer,
  Findings root, and the Evidence capability table (one dispatch row, LIMITED,
  ceiling CANDIDATE_AVOIDABLE, 2 missing-evidence items; above Source health;
  contained at 1280/1000/640; at 640 it overflows and scrolls in its own region,
  non-vacuous).
- A first layout run was started concurrently with a second by mistake and both
  aborted/garbled; the recorded run is a clean single run after restoring a
  fresh `var/`.

## Known deviations

None against the ACs. Choices, stated for review:

- Readiness is site-wide (all accepted evidence plus active assessments), not
  the page's selected window; the row says so (`READINESS_STATEMENT`).
- Absent optional evidence (overrides) is listed "Not observed" and never lowers
  readiness.
- `GET /api/sites/{id}/analytics` now runs `assess_site` (as Overview does).

## Items for the reviewer

- Phase 2 added `GET /api/findings` (global index; reads every configured
  Site's assessments, each runs `assess_site`; linear in Sites) and changed
  `backend/tests/test_health.py` to allow the route.
- Existing tests changed (exact, not loosened): rail/tab pins in
  `operatorRouteFrames`, `operatorSiteTabs`, `siteDetailRoute`,
  `siteFoundationRoute`, `sitesIndexRoute`, `simulatorLabWorkspaceEntryPoint`,
  `overflowContainment`, `sharedVisualVocabulary`; `siteEvidenceScreen` passes
  `siteAnalytics={EMPTY_ANALYTICS_CLIENT}` and keeps its no-readiness test
  exact; backend `test_t027_overview` (profile owns no card state, allows the
  `capabilities` key), `test_sites_api`, `t027_isolated_probe`; T027 layout
  "every card reads No assessment yet" claim updated (`adccde6`) because the
  Dispatch card now carries an assessment; `navigation-truthfulness.ps1` rail
  rule replaced with the two grouped items.
- Necessary intervals are assessments without a Finding (owner ruling
  2026-10-03); a lineage revised to Necessary leaves the Findings indexes by
  design; its detail is reachable by URL only, titled "Assessment".
- Stop-60 stays as is, no policy record (owner ruling; T034 owns it).
- Ingestion keeps the first record at a (device, signal, time) key, so a second
  overlapping recipe run does not revise an interval; only new keys do.
- The Overview Dispatch card shows the whole-interval runtime metric beside an
  assessment on a different duration basis; the two can differ (backlog
  "Generator running time is whole-interval" stays open for that metric).

## Open owner decisions (phase 3a)

1. **Gap rule.** A coverage gap lowers readiness Full to Limited only when it
   left a segment Indeterminate (the segment's `missing` names the input).
   Non-limiting gaps are still listed with `limits_claim: false`. Observed:
   prolonged is Full with a non-limiting SOC gap listed. Alternative: any gap
   lowers to Limited. Which?
2. **Site-wide readiness window.** Readiness reads all accepted evidence for the
   Site, not the Evidence page's selected window. Alternative: score the
   selected window. Which? (Site-wide is what the table states today.)

## Residual risk

- Layout: one non-known failure named above; gate-closed browser pass not run
  (covered by tests).
- `/api/findings` and `/analytics` do analytic work on read; fine at demo scale.
- `finding_id` derives from the latest revision.
- Decision-table thresholds are demo-calibrated (documented in
  `dispatch_decision_table.md`).

## Owner UI check (one ordered walk)

Prereq: from `host/`, `..\.venv\Scripts\python.exe -m uvicorn lab_app:app --reload`
(port 8000); from `frontend/`, `npm.cmd run dev`. Create fresh Sites from
template `kobo-mini-grid-60kw`: KOBO-P, KOBO-H, KOBO-R, KOBO-D (fresh Sites
avoid overlap with earlier evidence; ingestion keeps the first record at a key).

1. KOBO-P: in the Lab, Draft `kobo-mini-grid-prolonged`, 2026-09-22
   03:00-11:00 UTC, 5-min step, model profile mini-grid v3, publication profile
   5; run to end; Commit.
2. KOBO-H: same with `kobo-mini-grid-evening`, 09:00-17:00; Commit.
3. KOBO-D: Draft `kobo-mini-grid-degraded-evidence` 03:00-11:00; Commit (only).
4. Rail: header OPERATE over Sites, INTELLIGENCE over Findings.
5. Sites > KOBO-P > Overview: tabs Overview, Foundation, Performance, Findings,
   Evidence. Dispatch card "Candidate avoidable" with "Open the Finding"; the
   Findings panel lists the same Finding; Service, Battery, Fuel, Renewable read
   "No assessment yet". KOBO-H's Dispatch card must not say Candidate avoidable.
6. `http://127.0.0.1:8000/api/sites/KOBO-P/analytics`: id `dispatch`, site
   types, Finding type, required/optional evidence, claim levels, and
   `readiness`.
7. KOBO-P > Performance: one subtab "Dispatch assessment"; interval table with
   claim, segment strip, duration bounds, constraint or missing evidence,
   confidence. Click an interval time: detail below. Click "Open Finding".
8. Finding: tabs Overview | Evidence | Alternatives only. Overview: claim,
   observed facts then inference, confidence with basis and separate coverage,
   claim ceiling (override absence "not proof"), indicative fuel litres range
   with duration, kW and L/kWh inputs (no money), next steps. Rail current is
   Findings.
9. Evidence tab: click a claim's record link; "Claim evidence" drawer shows the
   claim, window, algorithm version and the record detail; address path
   unchanged; Close removes it. Alternatives tab: override, PCS capability,
   policy, PV entries with status and record links.
10. Rail > Findings: global index lists that Finding with its Site; row click
    opens it. KOBO-H contributes no row.
11. KOBO-H > Performance: interval(s) Necessary, "No Finding (Necessary)";
    KOBO-H > Findings says no active Finding; KOBO-P > Findings lists one row and
    the filter narrows it.
12. KOBO-P > Evidence: "Capability readiness" table above Source health, one row
    "Dispatch assessment", readiness Full, ceiling Candidate avoidable, missing
    evidence lists the SOC gap as not limiting, "Not observed: Operator
    override. Absence is not proof that none existed." KOBO-H > Evidence: Full.
13. KOBO-D > Evidence: readiness Limited, missing evidence names Battery
    discharge capability (5 of 13 segments Indeterminate). (Not KOBO-R: its
    later prolonged commit fills the gap, so it may read Full.)
14. Revisions: on KOBO-R commit `kobo-mini-grid-degraded-evidence` 03:00-11:00,
    note the id at `http://127.0.0.1:8000/api/sites/KOBO-R/dispatch`; commit
    `kobo-mini-grid-prolonged` over the same window; open
    `http://127.0.0.1:8000/api/sites/KOBO-R/assessments/<id>/revisions`:
    revisions 2 and 1 listed, revision 1 unchanged. Restart the backend and
    reload: both remain.
15. Optional: restart with the Lab off (`..\.venv\Scripts\python.exe -m uvicorn
    assetops_backend.main:app` from `backend/`); steps 5-13 read the same.
16. Answer the two open decisions above.
