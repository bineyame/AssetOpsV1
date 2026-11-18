# S4-04 - take main (deferred-match root fix) and close review Lows (Sonnet)

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review`, branch `task/S4-04-site-finding-index` (slice review ACCEPT). Main `7edbe396` now has the deferred-match root fix (migration `0018_finding_match_deferral`, `finding_match_pass.deferred_window_starts`, `match_state` reports deferred windows as not matched).

1. `git merge main`; expect a conflict in `backend/assetops_backend/analytics/adapters/postgres_finding_store.py` - keep both sides' read methods. Docs: keep both sides.
2. Root-fix review L1: S4-04's index computes `matched` from its own snapshot query (`finding_index.py:~240`) and ignores `deferred_window_starts`. Make the index treat a deferred window as not matched (read the column in `index_snapshot` or call `match_state`), keeping the S3 edge-reach guard as defence in depth. Add a real-Postgres assertion that a deferred day reads PENDING with no claim.
3. S4-04 slice review L1: add a unit test for `candidate_reach`/`discover` covering BOTH day edges (a cluster at 00:00-00:20 reaches the previous day); mutation-check by removing the lower-edge check.
4. Migration-head pins: update any S4-04 test expecting an older head to `0018_finding_match_deferral`.
5. Owner doc `.agent/S4-04-owner-walkthrough.md`: add one plain sentence that the two days either side of the failed day also read "Not known" (by design).
6. Focused tests (index, read, episode, deferred-match files), `npx.cmd tsc --noEmit`, the s404 frontend test file, then ONE full backend suite from PowerShell with `--junitxml` (`-n 2 --dist loadfile --no-loadscope-reorder`, `var/sites/*.yaml` copied in temporarily, 20-minute cap, keep-awake running) and `tools/check-all.ps1` (temporary `.venv` junction). Remove temporaries afterwards.

Commit small; do not merge to main; update the review packet with a "main merge" section and JUnit counts; handoff `.agent/S4-04-main-merge-handoff.md` (git add -f). Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Report concisely.
