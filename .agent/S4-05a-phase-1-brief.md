# S4-05a phase 1 - implementer brief

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review3`, branch `task/S4-05a-provenance-binding-resolver` (from main `fd7afd2c`). Other builds run in the main checkout and `AssetOpsV1-review2`; do not touch them.

Environment: Python `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe` with `PYTHONPATH=C:/Users/assef/Bineyame/AssetOpsV1-review3/backend;C:/Users/assef/Bineyame/AssetOpsV1-review3/contracts;C:/Users/assef/Bineyame/AssetOpsV1-review3/gateway;C:/Users/assef/Bineyame/AssetOpsV1-review3/simulator` (confirm `assetops_backend.__file__` is in this worktree). Private `_test` DB per `backend/TESTING.md`. For `tools/check-all.ps1`: temporary `.venv` junction to the main venv (remove afterwards) and `npm.cmd ci` in `frontend` if frontend guards need modules. Gitignored `var/sites/*.yaml` exist only in the main checkout; copy temporarily if needed, remove afterwards.

Packet `tasks/S4-05a-provenance-binding-resolver.md` (+ umbrella `tasks/S4-05-stored-demo-provenance.md`) - build **phase 1 only**. Authority: `D-2026-10-15-s405-stored-demo-provenance`, `.agent/architect-S4-05-answers.md` (Q1-Q3, rule-8 section, Follow-up M1: AUTHORED_DEMONSTRATION and REGISTERED_SIMULATION pre-admission bindings, truth table, MIXED/UNKNOWN precedence). Reviews `.agent/S4-05-plan-review.md`, `.agent/S4-05-plan-rereview.md`; coordinator note in the packet (N-L1 simulator registration anchor on the registered commit/release path; N-L2 several run IDs -> MIXED; residual: `ON CONFLICT DO NOTHING` batch insert vs rule 8 upsert rejection).

Migration note: other unmerged branches add migrations (LR-01 0014/0015, S6-01a 0014). Number yours after main's head (0013) and state the re-chain obligation in your handoff; do not re-chain now.

Process: focused tests only in phase 1; no full suite. Before any long run check for another `pytest ... -n 2` process and keep runs focused while one runs. Keep-awake is running; cap at 2x expected. Measure the admission-lock cost in phase-1 tests (residual risk in the plan review). Mutation checks for the resolver truth table, pre-admission lock/refusals and rule-8 additions. Commit on the branch; do not merge; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. If an Architect ruling is unimplementable as written, stop and report.

Handoff `.agent/S4-05a-phase-1-handoff.md` (git add -f). Report concisely.
