# S6-01a change round - Architect ruling D-2026-10-15-s601-reopen

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review`, branch `task/S6-01a-action-store-read` (head `c341599b`). Environment as in `.agent/S6-01a-phase-1-brief.md` with this worktree's paths in PYTHONPATH (confirm `assetops_backend.__file__`). Other agents use other worktrees; touch none of them.

Ruling: `C:\Users\assef\Bineyame\AssetOpsV1-gap-planning\.agent\architect-S6-01-reopen-answers.md`. S6-01a owns:
1. The Site-scoped recommendation read for a selected revision returns prior Actions for the same canonical Finding (origin revision, application state, outcome state, exact Action link); never hidden by `FOUNDATION_BASIS_STALE`, a later revision or a failed live recomputation; selected revision and accepted snapshot labelled separately.
2. Accept guard for `reserve-trial-1` (same Finding, battery asset, reserve field): an earlier Action with application pending (incl. failed attempts awaiting retry) or applied with verification pending blocks a new acceptance with typed `PRIOR_ACTION_UNRESOLVED` (blocking Action ID, origin revision, link); live current-basis reasons shown separately; no Accept capability for the new key; identical retry of the existing accepted key still returns its Action.
3. Atomic recheck at acceptance: simultaneous accepts on different Finding revisions cannot create two unresolved trials (race proof on Postgres).
4. Regenerate the committed API contract fixture (`ASSETOPS_WRITE_S6_CONTRACT=1`) with both the recorded-clock AVAILABLE and served-clock stale cases, and add NOTES for S6-01b.

Proof: focused S6 tests + contract fixture equality; mutation checks for the guard and the atomic recheck; `check-architecture.ps1`. ONE full backend suite from PowerShell with `--junitxml` (`var/sites/*.yaml` copied in temporarily, 20-minute cap; first check no other `pytest -n 2` runs; wait if one does). Update `.agent/S6-01a-review-packet.md`. Commit small; handoff `.agent/S6-01a-reopen-handoff.md` (git add -f). Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Drop DBs. Report concisely.
