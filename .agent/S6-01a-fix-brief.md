# S6-01a fix round (Sonnet) - slice review Lows L1, L2

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review`, branch `task/S6-01a-action-store-read`. Environment as in `.agent/S6-01a-phase-1-brief.md` but with this worktree's paths in PYTHONPATH (`C:/Users/assef/Bineyame/AssetOpsV1-review/...`); confirm `assetops_backend.__file__`. Private `_test` DB; drop it afterwards. Another build runs in `AssetOpsV1-review3`: keep test runs focused; NO full suite (it runs later at merge time after re-chaining).

From `.agent/S6-01a-review.md`:
1. L1 (`actions/service.py:274`): take the apply's server time after acquiring the Action and Site locks (or map S1 `FOUNDATION_CLOCK_BEHIND` in this path to `ACTION_FOUNDATION_STALE`), so a publish committed in the window yields the stale code and FAILED, and a `recorded_at` cutoff never gains an earlier-recorded event later. Add a test.
2. L2 (`service.py:379`): make `application_basis` honest: expose the Foundation revision covering `effective_from` (what the server actually checks), or relabel; update the API contract fixture `backend/tests/fixtures/s6_action_api_contract.json` (regenerate deterministically) and add a contract note for S6-01b.
3. Record L3 and L4 as accepted deviations in `.agent/S6-01a-review-packet.md`.

Proof: S6 focused tests + contract fixture equality; `check-architecture.ps1`. Commit small; write `.agent/S6-01a-fix-handoff.md` (git add -f). Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Report concisely.
