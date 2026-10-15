# Planner brief - stored demonstration provenance (`I-stored-demo-provenance`)

You are the AssetOps Planner (Codex). Architect work order item 4 (`.agent/architect-autonomy-2026-10-15-answers.md`, `D-2026-10-15-owner-absence-work-order`). Write a new implementation-ready packet `tasks/S4-05-stored-demo-provenance.md` (pick the next free sensible ID if S4-05 is taken) on branch `plan/stored-demo-provenance` in worktree `C:\Users\assef\Bineyame\AssetOpsV1-plan2`. No code; the coordinator commits.

Read: registry node `I-stored-demo-provenance` (acceptance target) in `frontend/docs/architecture/v69-dependency-registry-pilot.json`; `.agent/architect-S4-02-batch-answers.md` "Q3 - demonstration provenance"; the S4-02b demonstration-label / date heuristic it retires (find it in `backend/assetops_backend/financials/` and the Finding read; cite exact lines); `.ai/MILESTONE_REVIEW_BACKLOG.md` items naming stored provenance/authorship (S4-02a/b carries, A-S5-overview carries P7, L2 at ~2195); S2 evidence ledger and gateway admission code; actor identity decision; S5-01 packet's note that unverified demonstration sources show no amount (`tasks/S5-01-site-overview.md`); `backend/TESTING.md`; exemplar `tasks/S4-02d-analytic-finding-worker-schedule.md`.

Requirements:
1. Code-reality check with `path:line` for every cited function/table/column/route/test/tool; new items marked new. Base on main (do not depend on unmerged LR-01/S5-01/S6-01 branches); state migration re-chaining if those merge first (LR-01 adds 0014/0015 on its branch).
2. Cover the acceptance target fully: server-authorized immutable tenant/Site-scoped publication designation with fixture/spec version and publication ID; binding to accepted evidence IDs; traced into Finding and consequence reads; mixed/unknown inputs stay cautious; date heuristic retired; wrong-Site and client-only/gateway-credential authorship refused. Name the writer (existing writer extended vs a new one) and the rule-8 guard impact; if a new writer is needed, raise it as an Architect question.
3. Non-UI if possible (mergeable after fresh review). If any owner-visible label changes, say so and set USER_REVIEW_REQUIRED accordingly.
4. Size: S or M (at most two phases); last phase review = slice review; focused tests per phase; one full suite at slice end per `backend/TESTING.md`.
5. Add a README queue row and set the registry node's `task` to the packet ID; keep registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). Status must start `implementation-ready`.
6. Open contract choices go in an "Architect questions" section with a recommendation each.

Keep it tight (under ~200 lines). Print a short summary.
