# T028 phase 2 handoff (screens) -> phase 3

Branch `task/T028-dispatch-finding-and-evidence`. Phase 2 committed
(`74d6bc7..HEAD`). Task Status stays `active`; packet, CODE_STATE and
ACTIVE_CONTEXT belong to phase 3. Start phase 3 from this file and
`.agent/T028-phase-1-handoff.md`.

## Owner rulings recorded (2026-10-03)

`backend/tests/dispatch_decision_table.md`: Necessary intervals stay
assessments without a Finding, listed on Performance > Dispatch; stop-60 stays
as is with no policy record (T034 owns versioned policy-change records).

## What landed, per AC

| AC | Where | Proof |
| --- | --- | --- |
| 8 alternatives on screen with evidence links | `sites/FindingDetail.tsx` `FindingAlternatives`; links open the claim drawer | `t028Screens.test.tsx` "the Alternatives tab lists each explanation..." |
| 12 same object; Overview links, never recomputes | every screen reads `siteAnalyticsClient.ts` by `assessment_id`; Overview card links `lead_assessment_id` to the Finding (or to Dispatch `?interval=` when it raises none); Overview Findings panel lists `overview.findings` as links (`SiteOverview.tsx`) | `t028Screens.test.tsx` AC12 block; host `test_the_global_findings_index_lists_the_same_finding_with_its_site` |
| 15 context, window, classification, facts, gaps, confidence, alternatives, bounded fuel, no Lab | Finding detail Overview six-part hierarchy (recommendation 3), fuel as technical quantity only | `t028Screens.test.tsx` "renders Overview \| Evidence \| Alternatives and the recommendation's hierarchy" |
| 21 navigation | Site tabs Overview, Foundation, Performance, Findings, Evidence (`shell/operatorSiteTabs.tsx`); Performance > Dispatch only subtab; Finding `Overview \| Evidence \| Alternatives`; claim drawer = `ClaimDrawer` in `sites/findingPresentation.tsx` reusing T027 `RecordDetail` (now exported from `SiteEvidence.tsx`), open state `?record=&claim=`, path/root unchanged; Findings rail root `/findings` (global index, new backend `GET /api/findings` in `analytics_api.py`); Site > Findings scoped index with claim filter, no KPI strip, row click -> `/findings/:siteId/:assessmentId` | `t028Screens.test.tsx`; updated rail/tab pins in 8 test files (exact, not loosened); `navigation-truthfulness.ps1` rail rule replaced: exactly `/sites\|Sites\|OPERATE; /findings\|Findings\|INTELLIGENCE` (3 mutation probes CAUGHT: extra item, wrong group, missing Findings) |
| 18 Performance subtabs, Finding types | `presentationProfile.ts` `performanceSubtabs`, `findingTypeLabel`, `orphanFindingTypeIds`; profile `finding_types` in `presentationProfiles.json` | rules 1 and 2 frontend tests in `t028Screens.test.tsx`; rule 3 (gap from backend only) asserted on Finding detail `data-finding-gaps` |
| 19 orphan list | `EXPECTED_ORPHAN_FINDING_TYPES` beside `EXPECTED_ORPHANS` in `backend/tests/test_t028_presentation_profile.py`; `test_a_listed_planned_id_passes_and_an_unlisted_one_fails` | proved: adding `fuel-residual` to the profile fails `test_no_unexpected_orphan_finding_types`; reverted |

Rail: `ui/NavRail.tsx` items take an optional `group`; a header
(`.nav-rail__group-label`, `data-rail-group`) renders before each group, so a
one-item group is headed. `OperatorShellLayout.tsx` declares the two items.

Routes (`shell/operatorSiteRoutes.ts`): `SITE_PERFORMANCE_ROUTE_PATH`
(+`/:capabilityId`), `SITE_FINDINGS_ROUTE_PATH`, `FINDINGS_PATH`,
`FINDING_ROUTE_PATH` (+`/:findingTab`); frames in `shell/SiteAnalyticsFrames.tsx`;
App prop `siteAnalytics`. Loading sentences added to `test/settled.ts`.
Fixtures: `sites/__tests__/analyticsFixtures.ts` (`analyticsClient`,
`EMPTY_ANALYTICS_CLIENT`).

## Phase 3 anchors

- AC20 capability table goes above source health in `sites/SiteEvidence.tsx`
  (`SiteEvidence` body, ~:68-190); score from `getDeclaration` (requirements
  carry `available`, `usable_records`) - backend scoring belongs in
  `analytics/declaration.py` `site_declaration` (:119) if readiness is computed
  server-side (preferred: rule 3, gap only from backend state).
- Evidence capability rows use `servedCapabilities`/`capabilityPresentation`
  (rules 1-2) and must show gaps only from backend state (rule 3 test there).
- Layout evidence: T028 block in `tools/layout-evidence.mjs` (search
  `T028 phase 2`), before the RUNNING-draft readback block; add phase 3 claims
  beside it.

## Checks run (phase 2)

- backend `test_t028_presentation_profile.py`, `test_t027_overview.py`,
  `test_t028_dispatch_analytic.py`, `test_health.py`: 46 passed.
- host `test_t028_dispatch_finding.py`: 12 passed.
- frontend full suite (after test updates): 45 files, 1089 passed;
  `t028Screens.test.tsx` 15 passed, no act warnings; `tsc --noEmit` exit 0.
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed.
- Layout evidence: see "Layout evidence" below.
- Not run (phase 3): full backend/host suites, production build check, packet.

## Layout evidence

Isolated run on HEAD `11a5b9b` (T027 method: `git archive` copy in the
scratchpad, copy `var/` = sites (valid_from backdated) + scenarios +
`.demo/T025c` runs/stages, PYTHONPATH on the copy, `vite preview` on 4173):
`ASSETOPS_LAYOUT_SITE=MG-006 ASSETOPS_KOBO_SITE=SITET26 node tools/layout-evidence.mjs http://localhost:4173`.
Output `.agent/T028-phase-2-layout-evidence.txt`: **546 PASS, 7 FAIL**, run
completed.

- Every T028 claim passes: grouped rail (two one-item groups, headers 17 px,
  inside the rail column) at 1280/1000/640; Performance tabs and the single
  Dispatch subtab; interval table populated (1 Candidate row, strip drawn),
  contained, no page scroll; Finding detail tabs, six-part hierarchy, rail
  root Findings at 1280/640; Evidence tab 13 claims / 198 links, drawer opens
  the clicked record, path and root unchanged, drawer inside the viewport
  (380 px at 1280, 345 px at 640), no page scroll; Findings index lists the
  Finding, contained.
- Pre-existing (T027-recorded): 3 "blocked table" (MG-006 setup READY) and
  the T025e 50 ms p95 delta budget (106.6 ms).
- 3 x T027 "every card reads No assessment yet" failed (4 of 5): the Dispatch
  card now carries the T028 assessment. Claim updated in `adccde6` (four
  cards No assessment yet, Dispatch slot assessed); **not re-run** - phase 3's
  layout run covers it.
- Note: `tabLabels` reads every `.site-tabs__list li`, so on Performance it
  includes the subtab; the T028 claim compares `slice(0, 5)` plus the subtab
  row separately.

## Risks / open

- Global `/api/findings` reads every configured Site's assessments (each read
  runs `assess_site`); fine at demo scale, linear in Sites.
- Finding detail for a Necessary assessment is reachable by URL only and is
  titled "Assessment"; no screen links it and the Findings indexes never
  list it.
- `finding_id` is computed from the latest revision, so a lineage revised to
  Necessary leaves the Findings indexes (by design; worth naming in review).
- Phase 1 risk stands: the Dispatch card shows the whole-interval runtime
  metric beside an assessment with a different duration basis.
- An attempted non-isolated layout run against the working `var/` aborted in
  the T022 section (stale READY drafts) and created four MG-001 Draft runs in
  `var/runs`; they were deleted. Run layout evidence only on an isolated copy
  (T027 method).

## Owner UI check (after phase 3; phase 2 part)

Prereq: phase 1 steps 1-3 (KOBO-P prolonged committed, KOBO-H healthy
committed), backend with the Lab, frontend dev server.

1. Rail shows header OPERATE over Sites and INTELLIGENCE over Findings.
2. Sites > KOBO-P > Overview: Site tabs read Overview, Foundation,
   Performance, Findings, Evidence. Dispatch card shows "Candidate avoidable"
   and an "Open the Finding" link; the Findings panel lists the same Finding.
3. Performance: one subtab, "Dispatch assessment". The table lists each
   assessed interval with its claim, a segment strip, duration bounds,
   constraint or missing evidence, confidence. Click an interval time: the
   panel below shows the binding constraint or gap and load/PV/SOC/reserve/
   capability at the interval's start. Click "Open Finding".
4. Finding: tabs Overview | Evidence | Alternatives (no Recommendation or
   History). Overview reads 1-6: claim, observed facts then inference,
   confidence with basis and separate coverage, claim ceiling (override
   absence stated as not proof), indicative fuel L range with duration, kW
   and L/kWh inputs (no money), next steps. Rail current is Findings.
5. Evidence tab: each segment is a claim with record links. Click one: the
   "Claim evidence" drawer shows the claim, assessed window, algorithm
   version and the T027 record detail (source, mapping, Foundation version,
   three timestamps). The address path does not change; Close removes it.
6. Alternatives tab: override, PCS capability, policy, PV entries with status
   (Observed / Not excluded / Contradicted) and record links.
7. Rail > Findings: the global index lists the same Finding with its Site;
   clicking the row opens it. KOBO-H contributes no row (Necessary only).
8. Sites > KOBO-H > Performance lists its interval(s) as Necessary with
   "No Finding (Necessary)"; Sites > KOBO-H > Findings says the site has no
   active Finding; KOBO-P > Findings lists one row, the filter narrows it.
9. Optional: restart with the Lab off; steps 2-8 read the same.
