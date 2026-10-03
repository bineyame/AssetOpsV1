# T028 phase 3a handoff (AC20 built) -> phase 3b (closeout)

Branch `task/T028-dispatch-finding-and-evidence`. Phase 3 build committed
(`20fbc58..HEAD`: 8518801 backend, 4411337 frontend, then the layout-evidence
commit). Stopped at the context budget. **Partial: build done, closeout not.**
Task Status still `active`.

## What landed

| AC | Where | Proof |
| --- | --- | --- |
| 20 scoring (backend) | `analytics/declaration.py`: `ReadinessBasis` (field `readiness` on every `AnalyticDeclaration`; DISPATCH basis `readiness-1`), `score_readiness`, `_coverage_gaps`; `site_declaration(site, evidence, assessments)` adds `readiness` per analytic. `analytics_api.py` `get_declaration` passes the active dispatch assessments (`service.dispatch`) when the site type has an applicable analytic. Rules written up in `backend/tests/dispatch_decision_table.md` "Capability readiness". | backend `test_t028_dispatch_analytic.py` 23 passed (5 new: Full, limiting gap -> Limited, non-limiting gap stays Full, capability never accepted -> ceiling Necessary, no generator -> None, basis roles declared); host `test_t028_dispatch_finding.py` 14 passed (2 new) |
| 20 screen | `sites/CapabilityReadiness.tsx` `CapabilityReadinessTable`, rendered first in `SiteEvidence` body (above source health); declaration read joins the evidence `Promise.all` (no new loading sentence). Props `analytics`/`profile` threaded via `SiteEvidenceFrame` and `App` (`analytics={siteAnalytics}`). Nothing renders for not_found or zero analytics; unavailable says so. | `shell/__tests__/t028EvidenceCapability.test.tsx` 8 passed |
| 18 Evidence rows | rules 1-2 via `servedCapabilities`; rule 3: readiness only from backend, `NOT_SCORED` row when the backend sends none | same file: rule 1, rule 2, two rule-3 tests |
| guard | `tools/checks/analytic-declaration.ps1` requires `readiness` in each declaration | probe: deleting DISPATCH `readiness=` -> "does not declare 'readiness'" CAUGHT; reverted |
| rule-3 probe | replacing the NOT_SCORED sentence with "Full" fails the rule-3 test | CAUGHT; reverted |

`siteEvidenceScreen.test.tsx` (T027) now passes `siteAnalytics={EMPTY_ANALYTICS_CLIENT}`; its "says nothing about capability readiness" test is kept exact (declaration not_found -> nothing).

Observed readiness through ingestion (host worlds): prolonged **Full** (SOC
gap 06:00-06:30 listed as not limiting - classification did not need it),
healthy **Full**, degraded **Limited** (Battery discharge capability gap,
5 of 13 segments, limiting; SOC gap listed too), ceiling Candidate avoidable.

## Design choices to state in the packet

- Readiness is site-wide (all accepted evidence + active assessments), not the
  page's selected window; the row says so (`READINESS_STATEMENT`).
- A coverage gap lowers Full to Limited only when it left a segment
  Indeterminate (a segment's `missing` names the input); non-limiting gaps are
  still listed (`limits_claim: false`). Owner may prefer any gap -> Limited.
- Absent optional evidence (overrides) is listed "Not observed ... absence is
  not proof" and never lowers readiness.
- `GET /api/sites/{id}/analytics` now runs `assess_site` (as Overview does).
- Phase 2 added `GET /api/findings` and changed `test_health` to allow it.

## Next (phase 3b closeout)

1. Full suites: backend (`backend/`), host (`host/`), simulator (from
   `simulator/`), frontend (`npx vitest run`), `npx tsc --noEmit`, `npm.cmd run
   build`; both `tools/check-*.ps1` (need `-ExecutionPolicy Bypass`).
2. Layout evidence, isolated copy (method: `.agent/T027-phase-2-review-packet.md`
   :88-97 and phase-2 handoff "Layout evidence"). New claim block "T028 Site >
   Evidence capability table" after the T028 Findings block in
   `tools/layout-evidence.mjs`; it must also re-run the updated T027 "No
   assessment yet" claim (`adccde6`). Known failures: 3 x blocked table
   (MG-006 READY), T025e p95 budget.
3. Packet `.agent/T028-review-packet.md` (all three phases; phase handoffs
   1, 2, 3a hold the AC tables and owner UI steps), CODE_STATE entry,
   ACTIVE_CONTEXT, task Status `in_review`.

## Owner UI check (phase 3 part)

10. Sites > KOBO-P > Evidence: "Capability readiness" table above Source
    health, one row "Dispatch assessment", readiness Full, ceiling Candidate
    avoidable, missing evidence listing the SOC gap as not limiting, "Not
    observed: Operator override. Absence is not proof that none existed."
11. A fresh Kobo site (e.g. KOBO-D) with only `kobo-mini-grid-degraded-evidence`
    committed (03:00-11:00): readiness Limited, missing evidence names Battery
    discharge capability (5 of 13 segments Indeterminate). Not KOBO-R: its
    later prolonged commit fills the gap, so it may read Full.
12. KOBO-H > Evidence: Full.
