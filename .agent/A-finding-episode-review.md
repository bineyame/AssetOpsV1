# A-finding-episode review (fresh Claude reviewer)

Target: plan/A-finding-episode @ 513711b. Planning-record review only; no implementation reviewed.

## Verdict: ACCEPT (no block findings; 2 carry)

## Checks
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: all 6 guards passed (architecture, nav, agent workflow, registry, delivery fixtures, screen ledger).
- Registry diff: exactly one line (node A-finding-episode): status open->resolved, evidence set to the new decision anchor, decision text updated; JSON formatting preserved; no other node touched. Dependents (A-finding-index, A-S4-financial, A-S5-overview) remain open.
- Decision D-2026-10-12-finding-episode-and-revisions present in DECISIONS.md with answers file linked.

## Consistency
- Routes/revision selection match D-2026-10-09-pre-s3-claim-routes-and-actor (/sites/{site_code}/findings/{finding_id}, optional revision_id, tenant/Site scope).
- 20-minute continuity equals CONTINUITY_TOLERANCE_S in backend/assetops_backend/analytics/dispatch.py; six-hour bracket matches dispatch decisions.
- dispatch-3 results pinned as history and not CURRENT under dispatch-3.1 agrees with the phase-3a decision; Indeterminate never alone creates avoidability Finding (consistent with bounded claim limits); no fuel/money implied.
- Cross-domain reuse limited to identity/lineage/freshness; FindingIndex and money deferred to S4-04/S4-02. Nothing implies implementation exists (S4-01, fixture, panels stated open).
- Q14-Q22 rulings coherent: S3-01u scoped to Q17+Q22, not an S4-01 prerequisite; Q21 is a practice change.

## Findings
1. CARRY (low): S3-01u is named only in the decision/answers; no task file or registry node exists (grep finds none). Planner must create it, or it is lost.
2. CARRY (low): the decision says dispatch-3.1 "(or later reviewed dispatch-3.x)" creates Findings but the Foundation-pre-3.1 "pinned" history has no live fixture (Q18 accepts test-backed only); S4-01 refinement must make sure the multi-revision fixture covers model-upgrade revision explicitly. Also merge/split are required by the contract but the answers make bridge/merge fixture optional "if bounded" - Planner should record merge as tested-or-explicitly-deferred, not silently dropped.

Not verified: no code/tests run (planning record).
