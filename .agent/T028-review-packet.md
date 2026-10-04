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
| 2 load/PV/SOC/reserve/generator/policy at time | met after fix round 1 (R2, R3, R4) | `test_reserve_and_capability_shortfall_make_runtime_necessary`; `test_t028_fix_round_1.py` `test_r2_*`, `test_r3_*`, `test_r4_*`; decision table segment rows |
| 3 no observed-PV stand-in, no simulator truth | met | `test_observed_pv_output_never_stands_in...`; host `test_candidate_evidence_links_are_accepted_records_and_never_observed_pv` |
| 4 Necessary has binding constraint; Candidate bounded | met after fix round 1 (R3) | host `test_prolonged_runtime_is_a_bounded_candidate_with_its_constraints` |
| 5 Indeterminate names evidence; no hidden weak portion | met after fix round 1 (R4: conflicting policy/override records named) | `test_insufficient_capability...`, `test_one_missing_portion_is_listed_beside_the_candidate`, `test_conflicting_records_are_used_by_nothing`; host missing-PCS test |
| 6 coverage vs confidence basis | met | decision table "Coverage, confidence"; host prolonged asserts `confidence.basis` |
| 7 override none-observed; records constrain | met after fix round 1 (R2: commands between reports and in edges) | `test_an_override_record_is_a_constraint...`, `test_override_absence_is_none_observed_not_proof`; host override-absence test |
| 8 alternatives with evidence links | met | host degraded stop-policy test; `t028Screens.test.tsx` Alternatives tab |
| 9 prolonged via ingestion; healthy no Finding | met | host `World` through the real Commit route; `test_healthy_reference_raises_no_finding` |
| 10 bounded fuel or unavailable+reason | met | `test_hand_calculated_candidate_interval_and_fuel_bound`, `test_fuel_is_unavailable_with_its_reason` |
| 11 basis modelled; no loss/saving implied | met | decision table "Indicative fuel"; Finding Overview shows technical quantity only (no money) |
| 12 Finding and Dispatch same object; Overview links | met | `t028Screens.test.tsx` AC12; `overviewDispatchAssessment.test.tsx`; host `test_overview_dispatch_card_links_the_finding_not_a_recomputation`, `test_the_global_findings_index_lists_the_same_finding_with_its_site` |
| 13 idempotent rerun; persisted revisions | met after fix round 1 (R1: `test_t028_fix_round_1.py` `test_r1_*`) | `test_the_same_records_give_the_same_payload`, `test_changed_evidence_appends_a_revision_and_keeps_the_prior` (reloads store); host rerun/second-commit tests |
| 14 private data removed, same result | met | host `test_removing_private_artifacts_leaves_the_same_assessment` |
| 15 screen path without Lab | met | Finding detail six-part hierarchy test; routes served with Lab gated off (`test_the_analytics_routes_are_served_with_the_lab_gated_off`) |
| 16 declaration read model | met | `analytics/declaration.py`; `GET /api/sites/{id}/analytics`; declaration test |
| 17 guard | met | `tools/checks/analytic-declaration.ps1`; 8/8 mutation probes CAUGHT (`.agent/T028-guard-probes.py`); readiness probe CAUGHT |
| 18 profile rules 1-3 (subtabs, card slot, Evidence rows, Finding types) | met | `overviewDispatchAssessment.test.tsx`, `t028Screens.test.tsx`, `t028EvidenceCapability.test.tsx` (rule 3 probe CAUGHT) |
| 19 expected-orphan list | met | `EXPECTED_ORPHANS`, `EXPECTED_ORPHAN_FINDING_TYPES` in `backend/tests/test_t028_presentation_profile.py`; adding `renewable`/`fuel-residual` fails, proved |
| 20 Evidence capability table above source health | met after fix round 1 (R5: generator-state gaps; `test_r5_*`, frontend R5 row test); owner questions closed (`D-2026-10-04-analytic-readiness-scope-and-gap-impact`) | backend `score_readiness` (declaration.py), `CapabilityReadiness.tsx`; backend 23 + host 14 + frontend 8 tests; layout claims (below). No open decisions: both are closed by that decision |
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

## Open owner decisions (phase 3a) - closed

Both are settled by the Architect record `.agent/T028-architect-readiness-decisions.md`
and `D-2026-10-04-analytic-readiness-scope-and-gap-impact` (`.ai/DECISIONS.md`):
the gap rule stays claim-dependent as T028's disclosed interim default, and
readiness stays site-wide (evidence sufficiency, not the selected window). The
configurable gap-impact type is carried as unscheduled follow-up **T028A -
Configurable analytic evidence-gap impact** (plan after T029 point-2 feedback;
gates nothing). The owner may still overrule; slice acceptance is separate.

## Correction round (Architect, 2026-10-04)

Items 1-3 of the record's section 3, no wider.

- Meaning and limits: `READINESS_STATEMENT` now says evidence sufficiency (not
  Site health), site-wide scope, the interim claim-dependent rule, and that Full
  is not health or uninterrupted/current/selected-window coverage. The table
  shows `assessed_intervals`: "No intervals assessed; signal availability only."
  at zero, else "N interval(s) assessed." The empty-gap text is now "All required
  signals have usable records; no claim-limiting gaps identified in assessed
  intervals." (at zero intervals: "...no intervals assessed, so coverage is not
  yet checked.").
- None aligned with reconstruction: `ReadinessBasis.no_claim_without` became
  `reconstruct_from_any` (alternatives). None only when neither generator status
  nor output has a usable record; one channel alone is Limited with the missing
  channel listed and the Candidate ceiling kept. `dispatch.py` unchanged.
- `basis_version` is `readiness-2` (`dispatch-1` and history untouched); decision
  table "Capability readiness" updated to match.
- New checks (backend `test_t028_dispatch_analytic.py`): status-only and
  power-only each reconstruct an interval (segments non-empty, 1 assessed) and
  score Limited, naming only the absent channel; neither-channel stays None with
  the "no accepted record of ... or ..." statement; statement names scope,
  meaning and limits; basis_version. Frontend `t028EvidenceCapability.test.tsx`:
  new Full wording and the zero-interval case.
- Counts after: backend 1468, host `test_t028_dispatch_finding` 14, frontend
  1098; tsc and both checks clean. Layout evidence not re-run: its capability
  claim reads attributes and counts, not the changed text (the table cell gained
  one short note line; row height is reported, not asserted).

## Fix round 1 (Codex review, 2026-10-04)

Fixes R1-R5 of `.agent/T028-codex-review.md`; carries (C1 and others) untouched.
Approved choices unchanged (Necessary without a Finding, stop-60 without a
policy record, site-wide readiness with the interim rule, T028A deferred).
Versions: model `dispatch-2` (R1-R4), readiness basis `readiness-3` (R5).
Thresholds unchanged. A stored `dispatch-1` revision is retained; reassessment
appends a `dispatch-2` revision to the same lineage
(`test_r1_a_model_version_change_is_a_retained_revision_not_a_rewrite`).
Decision table updated (`dispatch-2` change list; segment split; conflict rule;
row 6 wording; edge rule; "Evidence basis and revisions"; readiness-3 row).
Regressions in `backend/tests/test_t028_fix_round_1.py` (14 tests). Proof:
with `backend/assetops_backend/analytics` checked out at `af668a7`, 13 of 14
fail; the 14th (`identical records do not conflict`) guards against an
over-broad conflict rule and is meant to pass both ways.

- **R1 evidence basis.** `_off_before`/`_off_after` return the records placing
  each bound; `_alternatives` returns the records it read; `_digest(used, fuel)`
  covers those plus the fuel basis (dispatch.py `_digest`, `_interval`).
  `AssessmentService._reconcile` keeps the latest revision only when digest,
  model and payload all match (service.py). Tests: late stop at 02:15 appends
  revision 2 (open revision kept unchanged, reloaded from a fresh
  `JsonAssessmentStore`, rerun adds nothing); a stop-policy record (alternative
  only) and a changed fuel basis each change the digest.
- **R2 commands between reports.** Choice: **segment at effective boundaries**,
  not a conservative cap of the whole segment. `_observed_segments` splits a
  report segment at every effective start/end of a constraint record
  (`CONSTRAINT_RECORDS`: generator override, battery reserve override, reserve
  policy, minimum runtime policy) strictly inside it; each part uses the two
  reports' measurements (none invented) with the records effective in that part
  (`_evaluate(policy_at=, runtime_at=)`). Why: it is the smallest change that
  makes the "included at its effective time" statement true, it limits the
  effect to the time the command was effective rather than the whole 15 min,
  and a segment with no boundary inside is evaluated exactly as before. Edge
  (start/stop uncertainty) spans have no segment, so `_edge_allowance` removes
  generator-override time from the candidate upper bound there and the override
  alternative says such an override is outside the assessed segments. Tests:
  the review's 95 % override 01:05-01:10 (5 min Necessary, candidate 0.92 h), a
  reserve override between reports, an override in the stop edge (high bound
  1.07 h instead of 1.17 h). Stop-threshold policy records do not split: they
  are not a classification input (unchanged owner ruling).
- **R3 SOC headroom in 5b.** `_classify` returns Indeterminate before counting
  battery support when SOC <= reserve + 10 (pv at or above load, so not
  Necessary). Tests: the review's PV = load, SOC 30, reserve 30 case; PV 21 /
  21.9 / 20 with SOC 35 / 40 / 40 Indeterminate; SOC 41 Candidate (control).
- **R4 equal-rank conflicts.** `_Evidence.effective` returns every top-rank
  record; `_distinct` collapses identical content. `_evaluate` classifies under
  each alternative (`itertools.product`): agreement stands with the conflict
  named in its reasons; disagreement is Indeterminate with
  `<role>: conflicting records` in `missing`; a conflicting reserve shows as no
  reserve value. Choice: classify-under-each rather than always Indeterminate,
  so a conflict that cannot change the outcome (e.g. PV alone covers load)
  does not erase an independent result, as the review allows. Conflicting stop
  policies are not quoted in the policy alternative. Tests: the review's 30/70
  reserve case (Indeterminate, both records in the basis, readiness Limited),
  agreement case, identical duplicates, generator override and minimum-runtime
  conflicts, stop-policy conflict.
- **R5 generator gaps in readiness.** `declaration._generator_gaps` reads
  `coverage.unobserved_generator_state` and adds a limiting `COVERAGE_GAP` row
  ("Generator state: not observed for N min ..."). No frontend code change: the
  row renders through the existing list. Tests: backend `test_r5_*` on the AC1
  gap fixture (Limited, row named, basis readiness-3); frontend
  `t028EvidenceCapability.test.tsx` "a generator-state gap is a claim-limiting
  row" (Limited, limits=yes, no "no claim-limiting gaps" text).
- Frontend fixtures' version strings moved to `dispatch-2` / `readiness-3`.
- Checks after the fix: backend 1482 passed; frontend 1099 passed (46 files);
  host 616 passed (21 min, run alongside the other suites); `tsc --noEmit` exit 0; `check-architecture.ps1` and
  `check-agent-workflow.ps1` passed. Layout evidence not re-run: no layout claim
  reads anything changed (one more list item in an existing cell at most).
- Left open: a conflict in optional evidence (minimum runtime, generator
  override) that makes a segment Indeterminate does not lower readiness, because
  those inputs have no coverage row under the interim rule; it is named in the
  assessment's `missing_evidence`. Candidate for T028A's impact types.

## Fix round 2 (Claude re-review F1, F3)

- F1: the operator-override alternative text now follows what the analytic did
  (`_alternatives`, `dispatch.py`). An override counts as assessed only if it
  reaches a segment with observed generator state; one only in a generator-state
  gap says so and that time stays Indeterminate; in a stop/start edge, a
  generator stop-threshold override says the edge time it covers is not counted
  as candidate (and the rest is not assessed), while any other override (e.g.
  battery reserve) says it is not evaluated and does not change the upper bound.
  Classifications and fuel numbers are unchanged. No model-version bump: the text
  is in the persisted payload, and the payload-equality check in `service.py`
  already appends a revision when it changes, so previously stored assessments
  get a corrected revision on re-assessment.
- Tests: `test_f1_*` (3) in `backend/tests/test_t028_fix_round_1.py`, one per
  reproduced case; all three fail on the previous `dispatch.py` and pass now.
- F3: AC20 row and owner-walk step 16 corrected; walk notes the extra
  `dispatch-2` revision. F2 stays carried to the backlog, not fixed.

## Presentation correction (Architect, 2026-10-04)

`D-2026-10-04-practitioner-first-finding-presentation`, items 1-3 of
`.agent/T028-architect-audience.md`. Commits `dec4e52`, `17b8b97`, `04c0d28` and the handoff commit.
**Paused 2026-10-04 by the coordinator** (owner widened the direction,
`.agent/owner-T028-presentation-direction-2026-10-04.md`; Architect revising
scope); see `.agent/T028-presentation-handoff.md`. Emphasis and copy only:
classification, confidence, coverage, fuel bounds, readiness rules, thresholds,
navigation and the evidence contract are unchanged; no History tab; no money.

**Backend-owned reading (the one interpretation, served once).**
`dispatch.reading(assessment)` (`analytics/dispatch.py`) returns `meaning`
(per classification, `CLAIM_MEANINGS`), `generator`, `next_steps` (each with a
`target`: an alternative id, the Site's evidence page, or none) and `framing`
("checks to make before considering any change ... not an instruction to stop
the generator or to change a setting"). Steps are conditional on what the
assessment already states: Candidate + `UNOBSERVED_OVERRIDE` -> confirm the
operator instruction; an `OPERATOR_OVERRIDE` -> review it; PCS capability
`NOT_EXCLUDED` -> check the N min it was not reported; other missing inputs ->
the Site's evidence; conflicting/absent stop policy -> confirm the policy;
Necessary -> no avoidable runtime, check the constraint only if unexpected.
`service.lineage_summary` attaches it to every summary (dispatch rows, Finding,
Site and global indexes, Overview findings). **Revisions:** it is computed at
read time and is not in the persisted assessment, so it adds no revision and
the revision statement ("added only when the evidence basis or model changes")
stays true; an old revision would read identically because the function reads
only stored fields. Readiness (`declaration.py`, computed on read, not
persisted) gains `question`, per-level `meaning` and `scope` beside the full
`statement`.

**Item 1 - operational explanation leads.** Finding header: Assessment
(badge + type), Site, Generator, Period assessed as "22 Sep 2026, 03:00 to
11:00 UTC" (`readablePeriod`/`readableTime` in `findingPresentation.tsx`; ISO
kept in record detail and the drawer). Assessment ID, revision n of m with the
retained revision list, analytic/model, ISO window, record count and basis
digest moved to the closed "Assessment details" disclosure (inspectable; no
History tab). Performance intro now states the operational question and the
three classifications first; analytic/model sit in a closed "Method details"
disclosure. The same backend `summary` remains the text of the Overview card,
the indexes' link and the Finding's lead.

**Item 2 - six parts readable at a glance (order kept).** Headings: "1. What
the evidence suggests" (summary + classification meaning), "2. What was
observed, and what is inferred" (running period, running time, portions,
"Constraint requiring the generator"), "3. How confident, and how much was
measured" (confidence + basis visible; a one-line coverage summary naming
inputs not usable in every segment), "4. What limits this conclusion" (missing
evidence + claim limits, visible), "5. Estimated fuel associated with this
runtime" (range, "modelled", candidate duration bound and the consumption
uncertainty visible; Unavailable / Not applicable stated with the backend's
reason), "6. What to check next". Behind closed disclosures: "How the running
time is bounded", "Coverage of every input" (statement + per-input gaps), "How
the fuel estimate is calculated" (duration, kW, L/kWh inputs, formula).

**Item 3 - next step and evidence sufficiency.** Section 6 renders the
backend's steps; alternative targets link to
`.../alternatives#alternative-<ID>` (the Alternatives list items carry that id
and the tab scrolls to it); `site_evidence` links Site > Evidence. Supporting
links follow (records, other explanations not ruled out, Performance).
Performance's selected period shows the meaning and the steps (text only).
Site > Evidence: "What can we assess from this site's evidence?" with the
scope sentence ("not the selected window ... not site health and not
permission to act") leads; each row shows the level's meaning under
Full/Limited/None; column "Strongest conclusion available" (was "Claim
ceiling"); assessed-interval count, zero-interval wording, limiting gaps and
"not observed" stay visible; the scoring statement and model/basis versions
are in a closed "How readiness is scored" disclosure. Findings indexes: columns
Finding (summary link), Site, Period (readable), Assessment, Confidence, Type;
Revision moved to the Finding's Assessment details.

**Choices made (record did not settle).** (a) Reading served at read time, not
persisted (avoids revision churn; see above). (b) The persisted `summary` and
claim-limit texts are unchanged: changing them would append a revision to every
stored lineage with an unchanged evidence basis. Consequence: the Necessary
summary still reads "Generator runtime of 4.5-open was required: ..." and the
Candidate claim limit still names `(dispatch-2)`; carried, not fixed. (c) Site
Overview unchanged: its Dispatch card and Findings panel already use the shared
summary; the "No assessment yet" domains are the honest scope limit the
Architect named. (d) Times shown in UTC (explicit), not Site-local. (e)
Generator is the analytic's generator device id (`generator-controller`).

**Shorter wording never strengthens a claim.** Every new sentence restates a
served limit: "not proven waste", "not a judgement of optimal dispatch", "does
not judge whether that constraint was well set", "says neither that the runtime
was needed nor that it was avoidable", override absence "not proof", Full "not
whether the site is operating well, and not uninterrupted coverage". The
claim-limit list, missing evidence and unavailable fuel stay visible.

**The three cases after the change** (served payloads,
`.agent/T028-presentation-cases.txt`, built through the host Lab worlds):
- Candidate (prolonged): "4 h of generator runtime with PV and battery
  capability above load and no binding constraint evidenced (confidence
  medium)." Meaning "Potentially avoidable runtime ... not proven waste". Fuel
  21.6 to 35.8 L, modelled, for 4 to 4.17 h, +/-10 %. Next: confirm whether an
  operator instruction kept the generator running (-> Unobserved override).
  Readiness Full, with SOC gap listed as not limiting.
- Healthy (evening): Necessary, no Finding; meaning "Needed runtime ... does
  not judge whether that constraint was well set"; fuel Not applicable; next:
  "No avoidable runtime was identified. If the constraint shown is unexpected,
  check how it is set". Readiness Full.
- Evidence-limited (degraded): Candidate 0.5 h, confidence low, 1.25 h
  Indeterminate; fuel 3.5 to 4.3 L for 0.5 h; next: confirm operator
  instruction; check why battery discharge capability was not reported for 75
  min (-> PCS capability); check the Site's evidence for "Battery state of
  charge: no record". Readiness Limited: "Assessments are possible but limited
  ..." with both limiting gaps named.

**Tests.** Backend `test_t028_dispatch_analytic.py` +5 (candidate, capability
gap, Indeterminate/Necessary readings, served-not-persisted with one revision,
readiness question/meaning/scope). Host `test_t028_dispatch_finding.py` +3 (one
per case; the reading is identical on dispatch, Finding and Site index).
Frontend `t028Screens.test.tsx`: new heading order; readable period; meaning
visible; "Assessment details", coverage and fuel-input disclosures closed on
load, contents present, summary click opens; gaps and fuel range not inside a
disclosure; next-step links to the alternative anchors; framing; Performance
question before a closed "Method details"; index has no Revision column and
reads the period. `t028EvidenceCapability.test.tsx`: question + scope lead,
meaning per row, renamed column, closed scoring disclosure with versions, no
model version in the row.

**Checks (at `04c0d28`).** backend pytest 1490 passed; host 619 passed
(incl. `test_t028_dispatch_finding.py` 17); simulator 244 passed; frontend
vitest 46 files / 1099 passed; `tsc --noEmit` exit 0; `npm.cmd run build`
built (existing chunk-size warning only); `check-architecture.ps1` and
`check-agent-workflow.ps1` passed. **Layout evidence: not completed** - the
isolated run was stopped on the coordinator's instruction; the new Finding
disclosure claims (`READ_T028_DISCLOSURES`/`OPEN_T028_DISCLOSURES` in
`tools/layout-evidence.mjs`) are unverified, including whether the 64-char
digest in an opened "Assessment details" wraps at 640 px.


## Presentation checkpoint 1 (D-2026-10-04-plain-language-analysis-views)

Spec `.agent/T028-architect-presentation.md` section 5 item 1: default reading
and Analysis destinations, tabs and routes (section 3), vocabulary in all
copy touched (section 4). Graphics, card projection and the guard are
checkpoint 2 (`.agent/T028-presentation-cp1-handoff.md`). Supersedes the
disclosure layout of "Presentation correction" above. Commits `4d8f69b`,
`7736148`, `5704010`, `7f6cc37` and the closeout commit.

**Per surface.**

| Surface | Default view | Analysis |
| --- | --- | --- |
| Finding | Tabs `Overview, Analysis, Evidence, Alternatives` (`/analysis`). Outcome (Possibly avoidable / Needed / Cannot determine), site name, equipment, period UTC; "What happened" (headline + reason + meaning); recorded vs assessed portions (separate values); confidence word + principal limitation; missing records, limits, still-open explanations linked; fuel range or reason; next steps. No disclosures, IDs or method versions. Title `Finding: <outcome>`. Withdrawn/unknown assessment stated with a link to current results. | Shared `AssessmentAnalysis`: per assessed part the outcome, plain reason and values used at start and end ("Not reported", never zero), reasons needed, confidence explanation, coverage per input ("assessed parts", "not assessed" at zero), operating-time and fuel calculation, method version, references and revision history; links to Evidence and Alternatives instead of copying them. Evidence and Alternatives tabs reworded (plain outcome per part, "Other possible explanations", Supported by records / Still possible / Not supported by the available records). Drawer "Supporting record". |
| Performance > Dispatch | Dispatch still the only subtab; local `Overview, Analysis` (`?view=analysis`, `interval` kept). Periods in time order: outcome, operating time, main reason or missing info, strip, Finding link (Needed: none). Selected period: headline, meaning, confidence, fuel, limits, next steps, "View the analysis of this period". | Period chooser + the same `AssessmentAnalysis` for the selected period, including Needed periods; record links open the Site Evidence inspector. A selected id not in current results is stated, never substituted. |
| Site Overview card | Backend `plain.card`: outcome label + headline/reason (+ count of other periods). Findings panel shows `outcome: headline`. | "View analysis": Finding `/analysis`, or Dispatch `?interval=..&view=analysis` for a Needed lead. |
| Findings indexes | Columns Finding (headline + reason), Site, Period, Outcome, Confidence and main limitation, Analysis, Type; filter labels plain. Row opens Overview. | "View analysis" link per row opens the Finding's Analysis. No index-wide Analysis. |
| Site > Evidence | Local `Overview, Analysis`. "What can we assess from this site's records?", "Scope: whole site" apart from "Selected window"; per row Full/Limited/None + meaning, conclusion available, plain gaps (limiting or not), assessed-period count with the zero-period qualification; compact source summary ("Demonstration data"), coverage count, rejection count. | "How readiness is scored" (method, versions, required/optional records with references, gaps with references and assessed-period ids), full source status, input coverage, record interpretation and equipment details, rejected records. Record inspector reachable from both. |

**Backend.** `analytics/plain.py` generates every product sentence at read
time from the stored structured assessment (classification, constraint ids,
portions, input names, alternative ids/status/gaps, fuel status); fixed
stored templates (confidence basis, missing lines, policy statement) are read
by template, and unknown text becomes an explicit unavailable sentence.
Served as `reading` on every lineage summary, card label/reason, readiness
`question/meaning/scope/method/conclusion/gaps`, `plain_role` on requirement
rows. Nothing persisted, no new revision (tested), `dispatch-2`/`readiness-3`
unchanged; stored `summary`/`label`/`claim_limits` still served but rendered
nowhere on T028 product views. Site Overview metric/series labels and
statements reworded (`evidence/overview.py`); global Findings statement plain.

**Cases** (`.agent/T028-presentation-cases.txt`, as served from the host Kobo
worlds): candidate (prolonged) Possibly avoidable 4 h to 4 h 10 min, Medium,
21.6 to 35.8 litres; Necessary (evening) Needed, end open, no fuel estimate,
no Finding, shown via Dispatch Analysis; uncertain (degraded) Possibly
avoidable 30 min, Low, 1 h 15 min Cannot determine, missing battery records
named, Site Evidence Limited with two limiting gaps.

**Checks (closeout HEAD).** backend pytest 1491 passed; host pytest 619 passed
(incl. `test_t028_dispatch_finding.py` 17 passed); frontend vitest 46 files /
1104 passed; `tsc --noEmit` exit 0; `npm run build` built (chunk-size warning
only); `check-architecture.ps1` passed; `check-agent-workflow.ps1`
passed. Simulator suite not rerun (no simulator code touched). Layout
evidence: not run (checkpoint 2 by brief); `tools/layout-evidence.mjs`
T028 disclosure claims are now stale and must be rewritten in checkpoint 2.

**Tests changed.** Finding tab inventory now four; old six-heading and
closed-disclosure assertions replaced by default/Analysis split, absence of
method/ID/jargon on default views, Analysis content, Back/reload/direct
link and unknown-tab fallback, unknown assessment with current-results link;
Dispatch views, Needed-period Analysis, missing selection; card and index
Analysis links; Evidence Overview/Analysis split, window param kept; T027
Site Evidence tests moved to `?view=analysis` with new wording. Backend: plain
reading/readiness tests with a forbidden-word check over all reading text;
host reading/card/readiness assertions.

**Known deviations / choices.** Dispatch and index rows show the recorded
operating period, the Finding header the assessed window. Frontend
`INPUT_WORDS` maps stable input ids for coverage rows (presentation mapping).
Remaining jargon outside the touched copy (record drawer normalization text,
rejection details, Site Overview `interval_statement`, Foundation) is left
for the cp2 guard and the post-T029 follow-up. No owner walk yet.

## Presentation checkpoint 2a (graphics; D-2026-10-04-plain-language-analysis-views)

Spec `.agent/T028-architect-presentation.md` section 2 and the card projection
of section 5. Commits `a91764c`..`92b669e` plus this closeout. The guard,
remaining jargon and the layout-evidence rewrite/run are checkpoint 2b
(`.agent/T028-presentation-cp2a-handoff.md`).

**Graphics (all in `frontend/src/sites/assessmentGraphics.tsx`; frontend computes geometry only).**

| Graphic | Where | Contract delivered |
| --- | --- | --- |
| Assessed-period timeline | Finding Overview (full, part links `analysis?part=N`); each Dispatch row (compact); lead Overview Dispatch card (compact, from `lead_timeline`); Finding/Dispatch Analysis (full, selectable) | `timelineGeometry`: bands at supplied times on a period from the earliest to latest supplied time, no minimum width; bracketed start/stop (`last_stopped_before..first_running_observed`, `last_running_observed..first_stopped_after`) are separate dotted bands, never parts; unrecorded parts hatched with text; open start/end: marker plus explanation, axis ends at the last supplied time. Legend: Needed, Possibly avoidable, Cannot determine, Generator operation not recorded, Start or stop time uncertain (compact: kinds present only). Full form has a parts table (times UTC, outcome, served reason, select/link button); compact has the same as its `aria-label`. |
| Estimated fuel range | Finding Overview; Analysis; card (compact, BOUNDED only) | Low-to-high interval on a 0-based litre scale (round max), both numbers, caption "Estimated fuel associated with possibly avoidable operation (assessed result, litres)", served note ("an estimate, not confirmed fuel savings"). UNAVAILABLE/NOT_APPLICABLE: served reason, no bar. |
| Reported values for a selected part | Finding/Dispatch Analysis, "Values used for the selected part" | Separate kW bars (demand, available solar, available battery output, generator output) on one zero-based scale; battery charge and minimum reserve on 0-100 %. Switch "Values used at the start/end of the assessed part" (aria-pressed). Missing: "Not reported", no bar; zero: zero-width bar with "0 kW". Unrecorded part: no values. Part records listed under it. |
| Record coverage by input | Finding/Dispatch Analysis; Site Evidence > Analysis `?assessment=<id>` | Table: input, "N of M" assessed parts with a usable record, count bar, named gaps; zero evaluated reads "Not assessed" with no bar; unrecorded generator spans listed. Caption: counts of parts, not elapsed time. Site Evidence block is its own panel, scoped "Only the assessed period ..., not the whole site", below and apart from readiness; a missing id is stated, never substituted. |

**Backend.** `plain.card_timeline(a)` and `service.card_assessments` add
`lead_revision` and `lead_timeline` (window, interval bounds/open flags,
segments with outcome word, fuel status/bounds + served fuel wording) to the
Dispatch card. Read-time copy; nothing persisted, `dispatch-2`/`readiness-3`
unchanged.

**Choices (spec silent; minimal).**
- Part selection is `?part=N` (1-based) in the address; default part is the
  first recorded part with the period's outcome, else the first recorded part.
  An out-of-range part is stated and the default shown. Dispatch clears `part`
  when the period changes. Start/end switch is local state (defaults to start).
- Unrecorded parts are drawn hatched regardless of their classification; their
  outcome is in the table/label.
- Colours: Needed `#3d6fb0`, Possibly avoidable `#c2680a`, Cannot determine
  `#7e8796` (deliberately neutral; dataviz validator flags its chroma as "reads
  gray"; it is also cross-hatched and labelled), plus patterns. Light theme only, as the app.
- Card fuel: compact range only when BOUNDED; otherwise nothing on the card
  (the card reason carries the story; the Finding shows the reason).
- Coverage bar width is usable/evaluated (geometry); no percentage is shown.
- Analysis links "This period's record coverage on the Site Evidence page"
  (`siteEvidenceAssessmentHref`).
- The old per-part start/end values table in Analysis is replaced by the
  parts table plus the selected part's values.

**Guard extended, not loosened.** `tools/checks/shell-overflow.ps1` names
`assessmentGraphics.tsx` as the fifth svg module with region
`.assessment-graphic` (`overflow-x: auto`); tables go through `DataTable`.
Proven: removing the overflow declaration, removing the region class, and an
`<svg />` in `FindingDetail.tsx` each fail the architecture check; reverted.

**Tests.** `frontend/src/sites/__tests__/assessmentGraphics.test.tsx` (16):
geometry against supplied times incl. bracketed bands; a 1-min part keeps
1/480 width; unrecorded hatched/bracketed dotted with table rows; open ends
marked/explained, axis not extended; compact text equivalent; unreadable time
not drawn; fuel endpoints on the scale; UNAVAILABLE/NOT_APPLICABLE no bar, no
"0 litres"; missing vs zero inputs; common kW scale; start/end switch; part
without values; coverage Not assessed vs 0 of 4; selection by `?part`, button
(keyboard-usable, address updated) and out-of-range. `t028Screens` (+4):
Dispatch rows draw their own assessment; card timeline is the lead it links;
Dispatch Analysis coverage link to Site Evidence, scoped, apart from
readiness; missing selection stated. Mutation proofs: min band width, missing
as zero, fuel bar when unavailable, coverage always assessed: each fails.
Backend `test_the_overview_card_carries_the_lead_period_timeline_unchanged`.

**Checks.** Frontend 47 files / 1124 tests pass (run before and again after
the DataTable/guard commit `92b669e`); `tsc --noEmit` clean; production build
ok (rerun after `92b669e`); backend 1492 passed; host `tests/test_t028_dispatch_finding.py` 17
passed; `check-architecture.ps1` passed; `check-agent-workflow.ps1` passed.
Layout evidence: not run (checkpoint 2b; `tools/layout-evidence.mjs` still
measures `.segment-strip` and the old disclosures). Narrow-screen behaviour is
therefore unverified in a browser.

## Presentation checkpoint 2b (vocabulary guard, jargon, layout; D-2026-10-04-plain-language-analysis-views)

Spec `.agent/T028-architect-presentation.md` sections 4 and 5. Commits
`fd73418`, `36966c0`, `436f1dc` and the closeout. Last build step before review.

**Guard design (section 4).**
- Versioned list `frontend/src/test/productVocabulary.json` (version 1, the
  section 4 table: run/runtime/ran/running, binding/bound input, scenario,
  recipe, draft, commit, staged envelope, execution, world state, oracle,
  kernel, tick, projection, replay, model/publication profile,
  simulation/simulated/simulator, backend, frontend, read model, payload,
  analytic (declaration), basis digest, claim(s)/claim ceiling, candidate
  (avoidable), indeterminate, necessary, PV/SOC/PCS (case-sensitive),
  discharge capability, load, reserve policy, envelope, ingest(ion/ed),
  mapping (basis), receipt timestamp, normalization/normalized). Allowed
  glosses: "solar power (PV)", "battery charge (SOC)", "battery power
  converter (PCS)" (Analysis may add the abbreviation after its meaning).
- Scanner `frontend/src/test/productVocabulary.ts`: every rendered text node
  (incl. svg `<title>`, captions, legends, backend text, empty/error states)
  plus `aria-label`, `aria-description`, `aria-roledescription`, `title`,
  `alt`, `placeholder`; Unicode word boundaries; failures name page, phrase,
  where (text or attribute) and the text.
- Exclusions, only the three named, per element via
  `data-vocabulary-exempt="source-reference|user-owned|lab"` (justifications in
  the JSON). An exempt element must wrap a single value: one with element
  children, or an unknown reason, is itself a violation, so no panel or
  backend response can be exempted. Used on: record drawer message id,
  source/device/signal, record-interpretation id, delivery id; rejection
  delivery id; Site details foundation summary (the site's own configured
  document text, user-owned).
- Frontend suite `frontend/src/shell/__tests__/t028Vocabulary.test.tsx`, Lab
  off: 29 product states over the five surfaces, plus 2 Lab-on states (Site and Finding Overview) where the Lab entries are the only `lab` exemptions - Site Overview (populated, no
  evidence, unavailable); Dispatch Overview, selected period, Analysis of a
  Needed and a possibly avoidable period, unknown period, nothing assessed,
  unavailable; Finding Overview, Analysis, Evidence, Evidence with the record
  drawer open, Alternatives, unknown, unavailable; global and Site Findings
  (populated, none, unavailable); Site Evidence Overview, Analysis, Analysis
  with one assessed period, unknown period, record drawer, no evidence,
  unavailable. Each state must scan more than 5 pieces (not a loading screen).
- Live text: `tools/layout-evidence.mjs` `t028Journey` runs the same rule in
  the browser over the populated backend (Site Overview; Dispatch Overview,
  each period selected and its Analysis; unknown period; Finding Overview,
  Analysis, Evidence, drawer, Alternatives; unknown Finding; both indexes;
  Site Evidence Overview, Analysis, one period, record drawer) - this is the
  scan of text the fixtures cannot reach. Backend: 
  `test_served_evidence_explanations_use_the_product_vocabulary` scans the
  served evidence/overview statements and every rejection reason against the
  same JSON list.
- Failing-example proofs (in the suite): a forbidden phrase delivered by the
  backend (`reading.reason` "The binding constraint held for this run." through
  the analytics client) is caught with page and phrase (`binding`, `run`); an
  `aria-label` alone is caught; a source reference `sim-run-0042` renders
  verbatim and is not flagged, a Lab link is not flagged, a panel-wide
  exemption and an unknown reason are refused. Mutation proofs (reverted):
  "Run start or stop time uncertain" in the timeline legend fails the suite on
  4 states; "in its payload" in one rejection reason fails the backend test.
  Live: a planted backend-style sentence is caught in the browser.

**Jargon removed (what the guard found).**
- Record drawer: `NORMALIZATION_STATEMENT` now "AssetOps uses this value and
  unit exactly as the source sent them; it does not convert units." (same
  fact; constant, not stored).
- Rejected records: read-time `reason` per rejection from
  `evidence/read_model.py` `REJECTION_READINGS` (every envelope, batch and
  ingestion kind; unknown kind gets an unavailable sentence, never its code).
  The stored `kind`/`field`/`detail` are unchanged and still served; the
  product shows the reason and the delivery reference, no longer the kind code
  or the ingestion detail ("not in the mapping").
- Site Overview `INTERVAL_STATEMENT` rewritten in plain words (operating time,
  no "interval mean"/"sample carried forward").
- Source mode label "Simulated" -> "Demonstration data" (`siteViewModel.ts`,
  shared by the site header, details and Sites index; section 4's quiet
  origin disclosure).
- Frontend fixtures that had drifted from the served text (overview card
  reason, metric labels, findings statement, record statement, rejection
  kinds) synced to the backend.
- Not widened: Foundation and other non-T028 product pages keep their
  legacy copy (post-T029 follow-up). The shared shell did not force it; the
  only shared change is the source-mode label.

**Layout evidence rewrite.** The `.segment-strip`, six-heading and
closed-disclosure claims are replaced. New claims (non-empty sets proven by
counts): Dispatch rows each draw their own compact timeline >= 120 px in the
contained table, views `Overview|Analysis` (1280/1000/640/480); Finding
Overview tabs, full timeline geometry (each part's rendered width and offset
within 1.5 px of its `data-width`/`data-x`), caption and key inside the
graphic, fuel range or its stated reason (1280/640/480); Finding Analysis
parts, value and coverage tables each in a contained scroll region
(1280/640/480); Evidence tab drawer (1280/640); Dispatch Analysis (1280/480);
Site Evidence one-period coverage (1280/640); Overview card compact timeline
is the linked lead, inside the card (1280/640/480); Findings index with View
analysis links; the live vocabulary journey.

**Section 5 verification list, mapped.**

| Distinction or check | Where it is proven |
| --- | --- |
| Candidate and Necessary portions together | backend `test_one_missing_portion_is_listed_beside_the_candidate`, `test_reserve_and_capability_shortfall_make_runtime_necessary`; graphics "places every band at its supplied times"; `t028Screens` Dispatch rows (Possibly avoidable and Needed periods) |
| Evidence-limited and wholly Indeterminate | backend `test_insufficient_capability_evidence_throughout_is_indeterminate`, `test_indeterminate_and_necessary_readings_say_their_own_truth`; Cannot determine legend/label in the timeline tests |
| Unobserved time; open start/end | graphics "draws unrecorded operation hatched and bracketed time dotted", "marks and explains an open start and end without inventing a time" |
| Unavailable fuel; range endpoints | backend `test_fuel_is_unavailable_with_its_reason`, `test_hand_calculated_candidate_interval_and_fuel_bound`; graphics "draws the low-to-high interval at its endpoints"; layout "fuel graphic draws a range or states why" |
| Full readiness with a non-limiting gap | backend `test_a_gap_no_classification_needed_is_listed_but_stays_full`; `t028EvidenceCapability` "a Full row says no gap limited an assessed period" |
| Zero assessed periods; no evidence | `t028EvidenceCapability` "zero assessed periods say coverage is not yet checked"; graphics "zero assessed parts reads Not assessed"; vocabulary suite "no evidence"/"nothing assessed" states |
| Timeline geometry against supplied times | graphics geometry tests (incl. "a short part keeps its true width"); layout: each rendered part within 1.5 px of its supplied width and offset |
| Missing versus zero inputs | graphics "a missing input has no bar; a zero has a zero-width bar" |
| Selected assessment consistency | graphics "the selected part stays this assessment's part"; `t028Screens` card timeline is the lead it links, Dispatch rows draw their own assessment; layout card claim (drawn = linked lead) |
| Unchanged analytic outputs/revisions | backend `test_the_reading_is_served_and_not_persisted`, `test_the_overview_card_carries_the_lead_period_timeline_unchanged`; host `test_rerun_on_the_same_evidence_adds_no_revision`; `dispatch-2`/`readiness-3` unchanged |
| Direct links, Back/reload, keyboard | `t028Screens` "direct links, Back and reload keep each tab"; graphics "keyboard-usable buttons and keeps the choice in the address" |
| Narrow layouts | layout evidence at 640 and 480 px (above) |
| Product journey with Lab off | vocabulary suite renders all 29 product states with the Lab flag off; live Lab-off build and host: `.agent/T028-layout-evidence-lab-off.txt` (4 PASS, 0 FAIL: 17 pages found and scanned, 2900 pieces, no listed phrase, planted sentence caught, Lab address "Page not available") |
| Vocabulary | this section's guard and proofs |

**Layout evidence (run on HEAD `3fce4af`).** Isolated copy as earlier T028
runs (`git archive HEAD` in the scratchpad; copy `var/` = sites with
`valid_from` backdated to 2026-01-01 + scenarios + `.demo/T025c` runs/stages;
`host/lab_app:app` on 8000 with PYTHONPATH on the copy; `vite preview` 4173;
working-tree `var/` untouched):
`ASSETOPS_LAYOUT_SITE=MG-006 ASSETOPS_KOBO_SITE=SITET26 node tools/layout-evidence.mjs http://localhost:4173`
-> `.agent/T028-layout-evidence-final.txt` **615 PASS, 4 FAIL**, run completed.
The 4 failures are all on the known list: 3 "blocked table" (lines 124, 135,
146) and the T025e p95 delta budget (56.8 ms vs 50 ms, line 559). The T025b
"profile 4 discloses the status" claim passed this run. Every T028 claim
passes, including the live vocabulary journey (17 pages, 2917 pieces, no
listed phrase).

Lab-off journey: the copy's `config/app-config.json` set to Lab off, the
copy's frontend rebuilt, `assetops_backend.main:app` on the same populated
store, `vite preview` 4174,
`ASSETOPS_LAYOUT_T028_JOURNEY_ONLY=1 ASSETOPS_KOBO_SITE=SITET26 node tools/layout-evidence.mjs http://localhost:4174`
-> `.agent/T028-layout-evidence-lab-off.txt` **4 PASS, 0 FAIL** (Lab API 404).

What the first full run found, fixed before the run above (commit `3fce4af`):
- Live text the fixtures could not show: source identifiers inside authored
  text (`policy-minimum-runtime`, `simulator-lab-source`,
  `site-controller / policy-critical-load-priority`, delivery
  `commit-...`) and the Lab entries shown with the Lab on ("Open Simulator
  Lab", the Site quick actions). Identifiers are now marked by value with
  `data-vocabulary-reference` (`sites/vocabularyReference.ts`; the scanner
  removes exactly those values, still reads the authored words around them,
  and refuses a value that is not identifier-shaped); Lab entries carry
  `data-vocabulary-exempt="lab"`. Nothing was rewritten.
- Finding Analysis scrolled the page at 640 px (713 vs 625): a visually
  hidden table heading inside the value tables escaped its scroll region.
  `.assessment-graphic` and its `.data-table__scroll` are now positioned.
- Stale non-T028-named claims caused by T028 cp1: the T027 Site > Evidence
  claims read source health/coverage on `?view=analysis` and accept the
  Evidence local views after the five site tabs.
- At 480 px the shell gives the content column about 185 px and shared
  fact-list badges (site and Finding headers) overflow it; the shell is not
  committed below 640 px, so 480 px claims cover the graphics and their
  regions, not the whole page (named choice below).

**Checks.** Backend pytest **1493 passed**; host pytest **619 passed**;
simulator pytest (from `simulator/`) **244 passed**; frontend vitest **48
files, 1132 passed**; `tsc --noEmit` exit 0; `npm run build` built (chunk-size
warning only); `tools/check-architecture.ps1` passed;
`tools/check-agent-workflow.ps1` passed.

**Choices (spec silent; minimal).**
- The list lives with the frontend tests (JSON) and is read by the frontend
  suite, the browser scan and the backend test; the browser scanner restates
  the TS rule (no shared module across node/browser/TS); both are proven.
- "load", "necessary", "candidate", "claim" are banned as whole words on
  every T028 surface (the table's display-label rows), not only default views.
- 480 px claims are graphics-only (no whole-page claim): the shell column
  is ~185 px there and the overflow is in shared header fact lists, outside
  T028's graphics; 1280/1000/640 keep the whole-page claim.
- Source identifiers are excluded by exact value (`data-vocabulary-reference`)
  rather than by wrapping; the DOM text is unchanged.
- The foundation summary is treated as user-owned site content (shipped
  templates included) rather than rewritten: it is the site record's own
  document, immutable by revision.

## Residual risk

- Vocabulary: the guard is a word list; plain meaning, uncertainty and claim
  strength still need the owner's reading. Foundation and non-T028 product
  pages are not scanned (post-T029 inventory).
- Layout: one non-known failure named above; gate-closed browser pass not run
  (covered by tests).
- `/api/findings` and `/analytics` do analytic work on read; fine at demo scale.
- `finding_id` derives from the latest revision.
- Decision-table thresholds are demo-calibrated (documented in
  `dispatch_decision_table.md`).

## Owner UI check (one ordered walk; spec section 5)

Rewritten for the presentation revision. First read the default views only,
as a reader without an engineer beside you; only then open Analysis and one
supporting record to challenge the reason. Neither the checks above nor a
narrated walkthrough substitutes for this first reading.

**Setup.** From `host/`, `..\.venv\Scripts\python.exe -m uvicorn lab_app:app --reload`
(port 8000); from `frontend/`, `npm.cmd run dev`. Create fresh Sites from
template `kobo-mini-grid-60kw`: KOBO-P, KOBO-H, KOBO-D, KOBO-R (fresh Sites
avoid overlap with earlier evidence). In the Lab, for each: Draft, 2026-09-22,
5-min step, model profile mini-grid v3, publication profile 5, run to end,
Commit: KOBO-P `kobo-mini-grid-prolonged` 03:00-11:00; KOBO-H
`kobo-mini-grid-evening` 09:00-17:00; KOBO-D
`kobo-mini-grid-degraded-evidence` 03:00-11:00. (The Lab is only the way the
demonstration records are made; the walk below is the product.)

**A. Default views only - do not open Analysis yet.**

1. Rail > Findings. KOBO-P's row: a short headline and reason, the site, the
   period in UTC, "Possibly avoidable", confidence and its main limitation.
   Can you say what the Finding is about from the row alone?
2. Open the row (Finding Overview). Without help, explain: the outcome; the
   affected period (the timeline: coloured parts at their times, a key; any
   uncertain start/stop dotted and named); how much operating time is
   possibly avoidable vs recorded; the fuel estimate as a low-to-high range
   with its note that it is an estimate, not confirmed savings; how confident
   it is and what limits it; and the next information to confirm. Nothing
   should talk about runs, bindings, simulations or how AssetOps is built.
3. KOBO-P > Overview: the Dispatch card states one outcome and reason for the
   period it names (not the whole site), its compact timeline and fuel range,
   and "View analysis". Other cards keep their own meanings.
4. KOBO-H > Performance > Dispatch (Overview): "Was the generator needed?";
   its period reads Needed, has no Finding, and its open end is marked and
   explained rather than drawn as a stop.
5. KOBO-D's Finding Overview: a "Cannot determine" part stays visibly
   uncertain (grey, labelled), and the missing battery records are named as
   what to confirm next.
6. KOBO-P > Evidence (Overview): "What can we assess from this site's
   records?", Full with its meaning (not "the site is fine"), "Scope: whole
   site" kept apart from the selected window, the assessed-period count.
   KOBO-D reads Limited and names what limits it.

**B. Analysis and one supporting record - challenge the reason.**

7. KOBO-P Finding > Analysis: the parts table; select a part (button or the
   timeline) and see `?part=N` in the address; its values at the start and
   at the end (switch); a value that was not reported reads "Not reported",
   never 0; coverage by input as "N of M assessed parts"; the operating-time
   and fuel calculation; method version and references. Does the stated
   reason follow from the values shown?
8. One supporting record: Evidence tab, open a part's record. The "Supporting
   record" drawer shows the value as sent, source/sent/received times, origin
   "Demonstration data", and labelled references; the address path is
   unchanged; Close removes it. Alternatives: other possible explanations as
   Supported by records / Still possible / Not supported by the available
   records, none claimed as globally disproved.
9. KOBO-H > Dispatch > Analysis of the Needed period (no Finding needed): the
   reasons and values; a record link opens the Site Evidence record view.
   "This period's record coverage" leads to Site Evidence > Analysis scoped
   to that period, apart from site-wide readiness; rejected records (if any)
   give a plain reason.
10. Direct link, Back and reload on each Finding tab and on `?view=analysis`
    keep the view; at a narrow window (~640 px) graphics stay inside the
    page and wide tables scroll in place.
11. Optional, Lab off: stop the host, set `config/app-config.json`
    `simulator_lab.enabled` to false, start `..\.venv\Scripts\python.exe -m
    uvicorn assetops_backend.main:app` from `backend/` and restart the dev
    server; steps 1-10 read the same and the Lab address says "Page not
    available".
12. Optional, revisions: on KOBO-R commit `kobo-mini-grid-degraded-evidence`
    then `kobo-mini-grid-prolonged` over 03:00-11:00;
    `http://127.0.0.1:8000/api/sites/KOBO-R/assessments/<id>/revisions` lists
    revisions 2 and 1, revision 1 unchanged, and both survive a restart.
