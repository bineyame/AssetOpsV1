# T028 presentation correction - handoff (paused)

Status: **paused by the coordinator** on 2026-10-04. The owner widened the
direction (`.agent/owner-T028-presentation-direction-2026-10-04.md`, referenced
only, not acted on) and the Architect is revising scope. Built against
`D-2026-10-04-practitioner-first-finding-presentation` items 1-3. Branch
`task/T028-dispatch-finding-and-evidence`; code commits `dec4e52`, `17b8b97`,
`04c0d28`; packet section "Presentation correction (Architect, 2026-10-04)" in
`.agent/T028-review-packet.md` has the detail and the walk updates.

## What landed (all tests green at `04c0d28`)

- Backend: `dispatch.reading(assessment)` + `CLAIM_MEANINGS`,
  `NEXT_STEP_FRAMING` (`backend/assetops_backend/analytics/dispatch.py`, above
  `_digest`); attached as `reading` in `service.lineage_summary`
  (`analytics/service.py`), read time only, never persisted (no revision).
  Readiness `question`/`meaning`/`scope` (`READINESS_QUESTION`,
  `READINESS_MEANINGS`, `READINESS_SCOPE` in `analytics/declaration.py`,
  emitted by `score_readiness`).
- Frontend: types `NextStep`, `Reading`, readiness fields
  (`sites/siteAnalyticsClient.ts`); `readableTime`, `readablePeriod`,
  `NextSteps`, reordered `FindingsTable` (`sites/findingPresentation.tsx`);
  `FindingDetail.tsx` header + `AssessmentDetails` disclosure, plain six-part
  headings, coverage/duration/fuel-input disclosures, `alternativeAnchor` and
  hash scroll on Alternatives; `SitePerformance.tsx` question-first intro,
  "Method details" disclosure, Period/Reason columns, meaning + steps on
  selection; `CapabilityReadiness.tsx` question/scope lead, per-row meaning,
  "Strongest conclusion available", "How readiness is scored" disclosure.
- Tests: backend +5 (`test_t028_dispatch_analytic.py` tail), host +3
  (`host/tests/test_t028_dispatch_finding.py` tail), frontend assertions in
  `shell/__tests__/t028Screens.test.tsx`, `t028EvidenceCapability.test.tsx`,
  fixtures `sites/__tests__/analyticsFixtures.ts` (`reading()`).
- Layout claims added (`tools/layout-evidence.mjs`, `READ_T028_DISCLOSURES`,
  `OPEN_T028_DISCLOSURES`, "T028 Finding detail disclosures"); **not run to
  completion** (stopped). Any partial `.agent/T028-layout-evidence-presentation.txt`
  is not evidence (536 lines, 418 PASS, 3 FAIL - the 3 known "blocked table"; killed before any T028 Finding claim ran).
- Case dump: `.agent/T028-presentation-cases.txt` (candidate / healthy /
  degraded as served), produced from the host `World` fixtures.
- Checks at `04c0d28`: backend 1490, host 619, simulator 244, frontend 1099
  (46 files), tsc 0, build OK, both `tools/check-*.ps1` passed.

## What was planned next

1. Complete the isolated layout run (method: packet "Checks run"), write
   `.agent/T028-layout-evidence-presentation.txt`, confirm the disclosure claims
   and the 640 px digest wrap.
2. Independent review: shorter wording does not strengthen claims; disclosures
   usable; owner walk.

## Open choices (made minimally; revisit under the revised scope)

- Persisted `summary` and claim-limit texts unchanged (Necessary "4.5-open",
  `(dispatch-2)` in the Candidate limit) - rewording appends a revision per
  lineage.
- Site Overview unchanged; times in UTC, not Site-local; generator shown as the
  device id `generator-controller`.
- The owner's new direction (plain text with graphs, deeper analysis as its
  own tab, no simulator language such as "run" or "binding") is not addressed;
  e.g. "binding constraint" remains in persisted text and some labels.
