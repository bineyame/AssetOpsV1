# S6-01b phase 1 - implementer brief

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review3`, branch `task/S6-01b-action-ui` (stacked on reviewed, unmerged S6-01a `c341599b`). Other agents use other worktrees; touch none of them or the main checkout.

Environment: real `frontend/node_modules` here. Python: `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` with `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator` (confirm `assetops_backend.__file__`). Temporary `.venv` junction (guards) and `var/sites/*.yaml` copies from the main checkout as needed; remove afterwards. Private `_test` DBs only.

Packet `tasks/S6-01b-action-ui.md` (+ umbrella `tasks/S6-01-action-change.md`); Architect `.agent/architect-S6-01-answers.md` / `D-2026-10-15-s601-action-store-and-ui` (Q4 capability-guarded labelled demo controls; Q5 selectors); plan reviews `.agent/S6-01-plan-review.md`, `.agent/S6-01-plan-rereview.md`. Consume S6-01a's committed contract `backend/tests/fixtures/s6_action_api_contract.json` and its NOTES (`backend/tests/s6_action_records.py`): `ACTION_ACCEPTANCE_CONFLICT` with `action_id` = "already accepted"; `application_basis` covers the read time while the server checks the revision covering `effective_from`; money consequence is a labelled link with no amount. S6-01a's slice review `.agent/S6-01a-review.md` and fix handoff list what the UI must respect. Wording must not imply the Site now behaves differently (no Lab effect until S6-02) and must make no savings claim.

Build **phase 1 only** per the packet. Focused frontend tests, `npx.cmd tsc --noEmit`; backend only if the packet's phase 1 touches it. No full suite in phase 1. Keep-awake is running. Commit on the branch; do not merge; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. If an Architect ruling is unimplementable, stop and report.

Handoff `.agent/S6-01b-phase-1-handoff.md` (git add -f). Report concisely.
