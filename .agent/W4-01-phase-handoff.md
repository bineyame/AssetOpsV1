# W4-01 phase handoff - run 2 stopped before commit 2 (2026-10-20)

Branch `task/W4-01-work-case-core` (worktree `AssetOpsV1-review5`), head `f6fd3c4f`. Commit 1 is `4cb89c68`.
**Commit 2 is NOT committed**: it is saved as `.agent/W4-01-commit2-partial.patch` (apply with `git apply`),
stopped on pending rulings q2 items 4-5 in `.agent/W4-01-pending-rulings.md`.

## What landed in run 2

- `git merge main` (merge commit `c721ea28`), clean.
- W3-01 reviewed commit-1 unit cherry-picked per W3-01 q1 ruling 1, from `git rev-list --reverse --no-merges
  1c409a3d^..e0d7ab04`. Commits already ancestors of HEAD (main's planning commits in that range) were skipped, as
  were empty picks (684f685e, 1ca18cb9, 1ceb1299 whose review file arrived with later picks). `.agent` conflicts on
  731789e7 and b65564cd took the incoming version. No code conflict. Backend/frontend/contracts code now equals
  `e0d7ab04` except W4 commit 1 (verified with `git diff --stat e0d7ab04 HEAD -- backend frontend/src contracts`).
  Reviewed end SHA consumed: **`e0d7ab04`** (picked as `f6fd3c4f`).
- `tools/check-all.ps1` on this head: all 10 guards passed.

## Patch contents (commit 2 draft)

`work/{model,service,composition}.py`, `work/adapters/postgres_work_store.py` (one INSERT statement per table, all 11
tables, SERIALIZABLE per command, bounded 40001 retry), `tests/test_w401_work_service_postgres.py` (7 named nodes).
On `w401b_test` (created, dropped): request/transitions/idempotency/plan/operational nodes passed (5);
`test_incident_attestation_reload_and_exact_links` fails on q2-4; `test_foreign_asset_and_evidence_refuse` fails on
q2-5. Not yet in the patch: rule-8 `$workWriter` registration with per-table anti-vacuity counts and writer probes
(`tools/checks/configuration-persistence.ps1` near the `$actionWriter` block ~l.757, `$pgWriters`, `$pgWritesSeen`,
`$pgDriverSeen`; probes in `tools/writer_guard_probes.py` modelled on the EV consequence set, each table's INSERT
appears exactly once as `"INSERT INTO <table> (` so `_unseen`-style replace probes work).

## Readings in the patch (none chosen as product semantics; confirm at review)

1. Incident IN_PROGRESS --REOPEN--> OPEN is allowed: the state table names IN_PROGRESS as REOPEN's source and line 42
   refuses only outside named sources; the cell note "REOPEN from active state is 409" is read as OPEN (the only
   coherent reading). Confirm.
2. Refusal order: missing server principal 403 `WORK_WRITE_FORBIDDEN` -> closed shape 422 (incl.
   `actor.authorization_basis`) -> USER 403 `WORK_USER_AUTH_REQUIRED` -> attestation 422 -> idempotency -> bounds/links.
3. Event kinds `CREATED`/`OPEN_VERIFICATION` 409 `WORK_TRANSITION_INVALID`; `VERIFIED|INEFFECTIVE|INCONCLUSIVE` 409
   `WORK_OUTCOME_NOT_SUPPORTED`; other unknown kinds 422. Transition check precedes the COMPLETE record check.
4. Hash path identity uses the resolved `site_id` (Q6 "normalize site code by resolved Site ID"), plus `case_id`, or
   the canonical root ID on plan/op corrections. Decimals hash and store as normalized plain text (`250.50`->`250.5`).
5. Create keys: all wire keys required; `incident_id` optional and request-only. Revision: `occurred_at`, `title`,
   `narrative`, `reason` required; link/citation arrays optional (omitted copies, `[]` clears).
6. Non-head, unknown or non-root correction predecessor/root -> 409 `WORK_CORRECTION_CONFLICT` (S14 supersedes l.295's
   `WORK_BASIS_CHANGED`); concurrent successor unique violations map to the same code.
7. Event retry body: state reduced through that event, `revision_id` = latest revision recorded by then. Create retry
   rebuilds `work-case-1` from revision 1 and CREATED (state OPEN). Output times use six fractional digits + `Z`.
8. Case provenance (Q11) via `PublicProvenance.cited_set(..., detail=False)` over a `LinkRowsReads` bound to the
   command connection (`evidence.composition.build_link_rows_reader`).

## Next

Apply the patch after q2 rulings, adjust the two failing nodes, add rule-8 registration + probes, run focused
tests on a private `_test` DB, writer probes, check-all, commit. Then commit 3 (`work_api.py`).
