# FIX-S4-DOMAIN Mini dispatch matcher reads only mini_grid / dispatch Findings

Status: in_review

`PostgresFindingStore.episodes` read every Finding on a Site, so a Site holding an open cold Finding (`episode_end`
NULL) broke the mini dispatch matcher pass (`plan_pass` TypeError) and stopped that Site's later tick stages.
Branch `task/FIX-S4-domain-filter`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-fixs4`, from main `ee678cbe5`.
Contract: ruling 1 of Addendum 3 in `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-DEMO-SPARSE.md`.
Packet `.agent/FIX-S4-DOMAIN-packet.md`.

## Gates (from the ruling)

- `episodes(tenant_id, site_id, domain=FINDING_DOMAIN, analytic_id=dispatch.ANALYTIC_ID)` with the
  `_index_snapshot` predicate `AND f.domain = :d AND f.analytic_id = :a`; every implementer of `episodes` updated.
- No special case for a NULL `episode_end` in the matcher: a NULL on a mini episode must keep failing loudly.
- Tests: a Postgres test (one open cold Finding and one mini Finding on the same Site; the pass completes and plans
  only the mini episode); a unit test that `episodes` passes the domain and analytic.
- Tier: scoped `test_s4_*`, `test_idx_gaps_*` and cold sets, check-all, then one `-Tier all` (an `analytics/` shared
  seam) on the coordinator's go.

USER_REVIEW_REQUIRED: false (a one-unit backend fix; merges on a fresh independent review ACCEPT, before DEMO-A is
rebuilt on it)
