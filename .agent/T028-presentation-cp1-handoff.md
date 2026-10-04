# T028 presentation checkpoint 1 - handoff to checkpoint 2

Spec `.agent/T028-architect-presentation.md` (`D-2026-10-04-plain-language-analysis-views`),
section 5 item 2 is what remains: the four graphics, compact card projection,
accessible interactions, the vocabulary guard, the Lab-off journey and layout
evidence. Checkpoint 1 is committed on `task/T028-dispatch-finding-and-evidence`
(commits `4d8f69b`..HEAD); packet section "Presentation checkpoint 1".

## What landed

- Backend read-time plain projection `backend/assetops_backend/analytics/plain.py`:
  `reading(assessment)` (outcome, headline, reason, meaning, operating_time,
  portions, reasons_needed, missing, confidence{word, explanation,
  principal_limitation}, limits, fuel{label,text,note}, duration_note,
  coverage_note, segments[] and alternatives[] index-aligned with the stored
  lists, next_steps, framing); `card()` for the Overview card label/reason;
  `readiness()` (question, meaning, scope, method, conclusion, gaps[] aligned
  with `missing_evidence`); `role()`. Attached in `service.lineage_summary`
  and `declaration.score_readiness`/`site_declaration` (`plain_role` on
  requirement and optional rows). Nothing persisted; `dispatch-2`/`readiness-3`
  unchanged. Stored template text (confidence basis, missing lines, policy
  statement) is read by template; unknown text becomes `plain.UNAVAILABLE`.
- Frontend: `sites/assessmentAnalysis.tsx` (shared Analysis, Finding and
  Dispatch); `findingPresentation.tsx` `OUTCOME_WORDS`, `AssessedPeriodStrip`,
  `LocalViews`/`localView`/`localViewSearch` (`?view=analysis`);
  `FindingDetail.tsx` tabs `overview|analysis|evidence|alternatives`;
  `SitePerformance.tsx` Dispatch Overview|Analysis; `SiteEvidence.tsx` and
  `CapabilityReadiness.tsx` (`CapabilityReadinessTable` overview,
  `CapabilityReadinessAnalysis`); `SiteOverview.tsx` card "View analysis"
  (`analysisHref` from `shell/SiteDetailFrame.tsx`); `FindingsTable`
  "View analysis" column. Route type `FindingTab` in `shell/operatorSiteRoutes.ts`.

## Anchors for checkpoint 2

- Assessed-period timeline: replace `AssessedPeriodStrip`
  (`findingPresentation.tsx`, `data-graphic-anchor="assessed-period-timeline"`).
  Used on Finding Overview, each Dispatch row, and Analysis. The compact form
  for the Overview card needs a backend projection of the lead assessment's
  segments on the card (`service.card_assessments`; the card currently has
  label/reason only) - spec 5 "compact timeline/fuel projection on the lead
  Overview card".
- Fuel range: Finding Overview `data-graphic-anchor="fuel-range"`
  (`FindingDetail.tsx`) and Analysis `data-analysis-fuel`.
- Reported values: `assessmentAnalysis.tsx` `data-graphic-anchor="reported-values"`
  wraps the per-part table; `InputValues` already shows "Not reported" for
  missing values (never zero). Needs selection of one part and the
  start/end switch.
- Coverage by input: `assessmentAnalysis.tsx` `data-graphic-anchor="coverage-by-input"`;
  "not assessed" when `evaluated_segments` is 0. Site Evidence Analysis has no
  selected-assessment coverage graphic yet (spec: label the scope, keep it
  apart from site-wide readiness).
- Guard: no guard built. Backend side is pinned by `_FORBIDDEN`/`_assert_plain`
  in `backend/tests/test_t028_dispatch_analytic.py` (reading and readiness
  only). Frontend tests assert absence of key words on Finding Overview,
  Finding Analysis, Dispatch Overview and the index row. The cp2 guard must
  scan rendered text and accessible names on all five surfaces, including
  drawers and empty/error states, with a failing-example proof.

## Open choices made (revisit if the reviewer disagrees)

- Dispatch and index rows show the recorded operating period
  (`interval.first/last_running_observed`); Finding header shows the assessed
  window. Both UTC.
- Dispatch Analysis record links go to the Site Evidence record inspector
  (`siteEvidenceRecordHref`); Finding Analysis links to its Evidence tab.
- Site Overview metric/series labels and statements in `evidence/overview.py`
  were reworded (running -> operating, PV -> solar, state of charge -> battery
  charge, "analytic" removed); other-domain meanings unchanged.
- "Simulated source" now reads "Demonstration data"; batch -> delivery;
  published -> sent; mapping -> record interpretation.
- Stored `summary`, `label`, `claim_limits`, `statement` fields are still
  served (API unchanged) but no T028 product view renders them.

## Risks and known gaps

- `tools/layout-evidence.mjs` `READ_T028_DISCLOSURES`/`OPEN_T028_DISCLOSURES`
  (about line 4229-4340) measure disclosures that no longer exist: rewrite to
  the new tabs/views before the cp2 layout run.
- Remaining jargon not yet removed (guard will find it): record drawer
  `normalization_statement` and rejection details from the T027 backend
  ("mapping", "Normalization"), `RecordDetail` source/device/signal ids
  (allowed as labelled references), `Status records ... RUNNING` source
  values in Site Overview metrics text, Site Overview `interval_statement`
  wording, Foundation and other non-T028 surfaces (post-T029 follow-up).
- `INPUT_WORDS` (frontend) duplicates backend input names for coverage rows;
  consider serving plain coverage labels from `plain.reading`.
- Case dump `.agent/T028-presentation-cases.txt` shows the three cases as
  served; the Necessary headline lists three reasons in one sentence (accurate,
  long).
